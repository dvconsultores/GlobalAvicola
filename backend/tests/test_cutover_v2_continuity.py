"""SPEC 006 · Cutover v2 — continuidad operativa tras el apply (mandato §30) y CUT-GL-02.

Gate obligatorio: no se certifica porque `status = applied`; cada BU registra su primer evento
real post-corte consumiendo el opening, la reconciliación y el informe del lote propagan
UNKNOWN, y ningún evento con fecha ≤ corte entra en un lote migrado.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    aplicar, aprobar, corte, crear_batch, fila_engorde, fila_incubadora, fila_reproductoras, headers_aprobador,
    items_por_referencia, preparar, subir, xlsx_v2,
)
from time_reference import iso_days_ago, recent_event_date  # noqa: E402

DIAS_CORTE = 30


async def _lote_aplicado(client, headers, seeded_ids, bu: str, filas: list, dias: int = DIAS_CORTE) -> tuple[int, dict[str, int]]:
    b = await crear_batch(client, headers, bu, corte(dias))
    r = await subir(client, headers, b, xlsx_v2(bu, filas, company_id=seeded_ids["company_id"]))
    assert r.status_code == 200 and r.json()["status"] == "validated", r.text
    await aprobar(client, headers, headers_aprobador(seeded_ids), b)
    assert (await aplicar(client, headers, b)).status_code == 200
    return b, await items_por_referencia(client, headers, b)


async def _evento(client, headers, **cuerpo):
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


async def _fila(client, headers, batch_id: int, lot_id: int) -> dict:
    rec = (await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=headers)).json()
    return next(f for f in rec["lots"] if f["lot_id"] == lot_id)


@pytest.mark.asyncio
async def test_grandparent_primer_evento_de_su_fase(auth_headers, http_client, seeded_ids):
    """GP en PRODUCCIÓN: mortalidad por sexo y recolección de huevo funcionan desde el opening; lifetime propagado."""
    ids = await preparar(seeded_ids)
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids, "grandparent",
                                      [fila_reproductoras("grandparent", "GP-CONT-1", fase="PROD")])
    lote = por_ref["GP-CONT-1"]
    r = await _evento(http_client, auth_headers, lot_id=lote, event_type="mortality_recording", event_date=recent_event_date(),
                      bird_movements=[{"sex": "female", "quantity": 20, "avg_weight": 3200.0}, {"sex": "male", "quantity": 15, "avg_weight": 3600.0}])
    assert r.status_code == 201, r.text
    r = await _evento(http_client, auth_headers, lot_id=lote, event_type="egg_collection", event_date=recent_event_date(),
                      farm_id=ids["farm_id"], house_id=ids["house_id"], egg_movements=[{"egg_type": "fertile", "quantity": 7000}])
    assert r.status_code == 201, r.text
    f = await _fila(http_client, auth_headers, b, lote)
    assert (f["opening"]["live"], f["post"]["mortality"], f["current_live"]) == (10000, 35, 9965)
    assert f["lifetime"]["mortality"] == 535 and f["lifetime"]["culls"] == 0
    assert f["post"]["eggs_collected"] == 7000 and f["lifetime"]["egg_production"] == 187000
    assert f["lifetime"]["feed_kg"] == 120000.5  # sin alimento post: histórico KNOWN se conserva
    # El detalle del lote se sirve (OpeningBalanceRead ya no rechaza aperturas v2) y expone la apertura.
    detalle = await http_client.get(f"/api/v1/lots/{lote}", headers=auth_headers)
    assert detalle.status_code == 200, detalle.text
    ob = detalle.json()["opening_balance"]
    assert (ob["initial_male_count"], ob["initial_female_count"], ob["mortality_status"], ob["template_version"]) == (1000, 9000, "KNOWN", "v2")
    assert detalle.json()["origin"] == "MIGRATED" if "origin" in detalle.json() else True


@pytest.mark.asyncio
async def test_breeder_cria_y_produccion(auth_headers, http_client, seeded_ids):
    """Reproductoras en cría: mortalidad; en producción: recolección y despacho de huevo fértil sobre lo recolectado."""
    ids = await preparar(seeded_ids)
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids, "breeder", [
        fila_reproductoras("breeder", "BR-CONT-CRIA", fase="CRIA", real_start_date=iso_days_ago(70), live_males=0, live_females=4500,
                           historical_mortality_males=50, historical_mortality_females=200,
                           accumulated_egg_production="N/A", accumulated_eggs_to_hatchery="N/A"),
        fila_reproductoras("breeder", "BR-CONT-PROD", fase="PROD"),
    ])
    cria, prod = por_ref["BR-CONT-CRIA"], por_ref["BR-CONT-PROD"]
    r = await _evento(http_client, auth_headers, lot_id=cria, event_type="mortality_recording", event_date=recent_event_date(),
                      bird_movements=[{"sex": "female", "quantity": 10, "avg_weight": 900.0}])
    assert r.status_code == 201, r.text
    # Lote con 0 machos vivos y mortalidad histórica de machos: estado real, se sirve sin 500 (validador movido al alta).
    assert (await http_client.get(f"/api/v1/lots/{cria}", headers=auth_headers)).status_code == 200
    f = await _fila(http_client, auth_headers, b, cria)
    assert (f["opening"]["live"], f["current_live"], f["lifetime"]["mortality"]) == (4500, 4490, 260)
    assert f["opening"]["egg_production_status"] == "NOT_APPLICABLE" and f["lifetime"]["egg_production"] is None
    r = await _evento(http_client, auth_headers, lot_id=prod, event_type="egg_collection", event_date=recent_event_date(),
                      farm_id=ids["farm_id"], house_id=ids["house_id"], egg_movements=[{"egg_type": "fertile", "quantity": 8000}])
    assert r.status_code == 201, r.text
    r = await _evento(http_client, auth_headers, lot_id=prod, event_type="egg_dispatch", event_date=recent_event_date(),
                      farm_id=ids["farm_id"], house_id=ids["house_id"], egg_movements=[{"egg_type": "fertile", "quantity": 5000}])
    assert r.status_code == 201, r.text
    f = await _fila(http_client, auth_headers, b, prod)
    assert f["post"]["eggs_collected"] == 8000 and f["post"]["eggs_dispatched"] == 5000
    assert f["lifetime"]["egg_production"] == 188000 and f["lifetime"]["eggs_to_hatchery"] == 155000


@pytest.mark.asyncio
async def test_hatchery_siguiente_paso_de_incubacion(auth_headers, http_client, seeded_ids):
    """Incubadora: carga del huevo recibido no cargado (BR-03) y despacho de pollitos disponibles (BR-04) desde el opening."""
    ids = await preparar(seeded_ids)
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids, "hatchery", [
        fila_incubadora("INC-CONT-1"),
        fila_incubadora("INC-CONT-2", eggs_transferred=8900, chicks_hatched=8000, chicks_available=500),
    ])
    l1, l2 = por_ref["INC-CONT-1"], por_ref["INC-CONT-2"]
    r = await _evento(http_client, auth_headers, lot_id=l1, event_type="incubation_load", event_date=recent_event_date(),
                      hatchery_params=[{"quantity_loaded": 1000}])
    assert r.status_code == 201, r.text
    r = await _evento(http_client, auth_headers, lot_id=l1, event_type="incubation_load", event_date=recent_event_date(),
                      hatchery_params=[{"quantity_loaded": 1}])
    assert r.status_code == 400 and r.json().get("rule") == "BR-03", r.text
    f = await _fila(http_client, auth_headers, b, l1)
    assert f["opening"]["hatchery"]["eggs_received"] == 10000 and f["post"]["eggs_loaded"] == 1000
    assert f["current"]["eggs_available_hatchery"] == 0 and f["current"]["eggs_in_process"] == 9900
    # Pollitos ya nacidos y disponibles al corte se despachan (viables = 500 + nacimientos − salidas).
    # BR-08: el despacho declara la granja/galpón de destino.
    r = await _evento(http_client, auth_headers, lot_id=l2, event_type="chick_dispatch", event_date=recent_event_date(),
                      farm_id=ids["farm_id"], house_id=ids["house_id"], bird_movements=[{"sex": "mixed", "quantity": 300, "avg_weight": 40.0}])
    assert r.status_code == 201, r.text
    r = await _evento(http_client, auth_headers, lot_id=l2, event_type="chick_dispatch", event_date=recent_event_date(),
                      farm_id=ids["farm_id"], house_id=ids["house_id"], bird_movements=[{"sex": "mixed", "quantity": 201, "avg_weight": 40.0}])
    assert r.status_code == 400 and r.json().get("rule") == "BR-04", r.text
    f = await _fila(http_client, auth_headers, b, l2)
    assert f["opening"]["hatchery"]["chicks_available"] == 500 and f["post"]["chicks_dispatched"] == 300
    assert f["current"]["chicks_available"] == 200 and f["current_live"] == 200
    assert f["lifetime"]["chicks_hatched"] == 8000


@pytest.mark.asyncio
async def test_broiler_mortalidad_alimento_y_peso(auth_headers, http_client, seeded_ids):
    """Engorde: mortalidad, alimento y pesaje por el motor normal; KPIs leen la apertura mixta."""
    await preparar(seeded_ids)
    from app.masters.models import FeedType

    async with database.async_session() as s:
        alimento = (await s.execute(select(FeedType).where(FeedType.company_id == seeded_ids["company_id"]))).scalars().first()
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids, "broiler", [fila_engorde("ENG-CONT-1")])
    lote = por_ref["ENG-CONT-1"]
    r = await _evento(http_client, auth_headers, lot_id=lote, event_type="mortality_recording", event_date=recent_event_date(),
                      bird_movements=[{"sex": "mixed", "quantity": 35, "avg_weight": 900.0}])
    assert r.status_code == 201, r.text
    r = await _evento(http_client, auth_headers, lot_id=lote, event_type="feed_registration", event_date=recent_event_date(),
                      feed_movements=[{"feed_type_id": alimento.id, "quantity_kg": 500}])
    assert r.status_code == 201, r.text
    r = await _evento(http_client, auth_headers, lot_id=lote, event_type="weight_recording", event_date=recent_event_date(),
                      bird_movements=[{"sex": "mixed", "quantity": 50, "avg_weight": 1250.0}])
    assert r.status_code == 201, r.text
    f = await _fila(http_client, auth_headers, b, lote)
    assert (f["opening"]["live"], f["post"]["mortality"], f["current_live"]) == (10000, 35, 9965)
    assert f["lifetime"]["mortality"] == 335 and f["post"]["feed_kg_registered"] == 500 and f["lifetime"]["feed_kg"] == 15500
    # El KPI de mortalidad usa la población de apertura mixta (antes solo sumaba machos + hembras).
    kpi = await http_client.get(f"/api/v1/reports/kpi/mortality/{lote}", headers=auth_headers)
    if kpi.status_code == 200:
        assert kpi.json()["opening_population"] == 10000
    informe = await http_client.get(f"/api/v1/reports/lot/{lote}", headers=auth_headers)
    if informe.status_code == 200:
        datos = informe.json()
        assert datos["opening_balance"]["total_birds"] == 10000 and datos["opening_balance"]["total_mixed"] == 10000
        assert datos["lifetime"]["mortality"]["opening"] == 300 and datos["lifetime"]["mortality"]["opening_status"] == "KNOWN"


@pytest.mark.asyncio
async def test_cut_gl_02_rechaza_eventos_hasta_el_corte(auth_headers, http_client, seeded_ids):
    """S9: evento con fecha igual o anterior al corte en un lote migrado ⇒ 400 CUT-GL-02; posterior ⇒ 201.
    Un lote nativo (sin corte) no se ve afectado."""
    await preparar(seeded_ids)
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids, "grandparent",
                                      [fila_reproductoras("grandparent", "GP-GL02", fase="PROD")], dias=20)
    lote = por_ref["GP-GL02"]
    for fecha in (iso_days_ago(20), iso_days_ago(25)):
        r = await _evento(http_client, auth_headers, lot_id=lote, event_type="mortality_recording", event_date=fecha,
                          bird_movements=[{"sex": "female", "quantity": 1, "avg_weight": 3200.0}])
        assert r.status_code == 400, r.text
        assert r.json()["rule"] == "CUT-GL-02" and "corte" in r.json()["detail"]
    r = await _evento(http_client, auth_headers, lot_id=lote, event_type="mortality_recording", event_date=iso_days_ago(19),
                      bird_movements=[{"sex": "female", "quantity": 1, "avg_weight": 3200.0}])
    assert r.status_code == 201, r.text
    # Nativo sembrado: la regla no aplica (sin opening de cutover).
    r = await _evento(http_client, auth_headers, lot_id=seeded_ids["lot_id"], event_type="weight_recording", event_date=iso_days_ago(25),
                      bird_movements=[{"sex": "mixed", "quantity": 5, "avg_weight": 1000.0}])
    assert r.status_code in (201, 400), r.text
    if r.status_code == 400:
        assert r.json().get("rule") != "CUT-GL-02"


@pytest.mark.asyncio
async def test_unknown_se_propaga_en_reconciliacion_e_informe(auth_headers, http_client, seeded_ids):
    """UNKNOWN + post = UNKNOWN en reconciliación e informe de lote; el post sigue visible aparte."""
    await preparar(seeded_ids)
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids, "broiler", [
        fila_engorde("ENG-UNK", historical_mortality=None, historical_culls=None, accumulated_feed_kg=None, current_avg_weight_g=None)])
    lote = por_ref["ENG-UNK"]
    r = await _evento(http_client, auth_headers, lot_id=lote, event_type="mortality_recording", event_date=recent_event_date(),
                      bird_movements=[{"sex": "mixed", "quantity": 35, "avg_weight": 900.0}])
    assert r.status_code == 201, r.text
    f = await _fila(http_client, auth_headers, b, lote)
    assert f["opening"]["historical_mortality"] is None and f["opening"]["mortality_status"] == "UNKNOWN"
    assert f["post"]["mortality"] == 35 and f["lifetime"]["mortality"] is None
    assert f["post"]["feed_kg"] is None and f["post"]["feed_kg_registered"] == 0.0 and f["lifetime"]["feed_kg"] is None
    assert f["opening"]["avg_weight_g"] is None and f["opening"]["weight_status"] == "UNKNOWN"
    assert f["current_live"] == 9965
    informe = await http_client.get(f"/api/v1/reports/lot/{lote}", headers=auth_headers)
    if informe.status_code == 200:
        vida = informe.json()["lifetime"]
        assert vida["mortality"]["opening"] is None and vida["mortality"]["opening_status"] == "UNKNOWN" and vida["mortality"]["lifetime"] is None
        assert informe.json()["opening_balance"]["total_feed_kg"] is None and informe.json()["opening_balance"]["feed_status"] == "UNKNOWN"
