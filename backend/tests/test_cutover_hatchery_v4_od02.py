"""SPEC 018 §9 · OD-HATCH-V4-02 RATIFIED — `fertile_eggs_to_pit` es PRE-CARGA.

Sustituye a la suite de OD-HATCH-V4-01 (fosa POST-CARGA, SUPERSEDED). Evidencia de la usuaria
funcional: la fosa se descuenta de los huevos **recibidos**; cuando se cargan, ya se descontó.

- **D-21** `eggs_set + oversized + dirty + broken + fertile_eggs_to_pit ≤ eggs_received` (con `≤`,
  igualdad válida); cada salida pre-carga KNOWN `≤ eggs_received`; con UNKNOWN solo la suma conocida.
- **D-22** sin `pit ≤ set` ni `transferred + pit ≤ set`; se conserva `transferred ≤ set`.
- **D-23** `eggs_in_process = eggs_set − eggs_transferred` (no resta la fosa).
- **D-24** saldo disponible para cargar = `received − set − Σ no incubables − fosa` solo si todo es KNOWN.
- **D-25** BR-03 operativo resta la fosa KNOWN (un UNKNOWN no se resta: cota superior).
- **D-27** V3 histórica intacta.

Casos del mandato: PIT-PRELOAD-01..06, PIT-POST-01..03, doble conteo y O-15.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    aplicar, aprobar, corte, crear_batch, fila_incubadora,
    headers_aprobador, items_por_referencia, preparar, subir, xlsx_v2,
)

EMPRESA = 1

#: Salidas pre-carga a cero: cada caso declara las suyas (el fixture trae 500/300/200 y fosa 0).
CEROS = dict(eggs_non_incubable_oversized=0, eggs_non_incubable_dirty=0, eggs_non_incubable_broken=0,
             fertile_eggs_to_pit=0)


def _fila(ref: str, **valores) -> list:
    """Fila V4 con todas las salidas pre-carga explícitas (sin heredar los 500/300/200 del fixture)."""
    return fila_incubadora(ref, **{**CEROS, **valores})


async def _subir_para_validar(client, headers, filas: list, dias: int) -> int:
    batch_id = await crear_batch(client, headers, "hatchery", corte(dias))
    r = await subir(client, headers, batch_id, xlsx_v2("hatchery", filas, company_id=EMPRESA))
    assert r.status_code == 200, r.text
    return batch_id


async def _errores(client, headers, filas: list, dias: int) -> tuple[dict, list[tuple]]:
    batch_id = await _subir_para_validar(client, headers, filas, dias)
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    return v, sorted((e["row_number"], e["field"], e["error_code"]) for e in v["errors"])


async def _aplicar_batch(client, headers, headers_apr, filas: list, dias: int) -> int:
    """Pipeline completo staging → validate → preview → approve → apply."""
    batch_id = await _subir_para_validar(client, headers, filas, dias)
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    assert v["invalid_rows"] == 0, v["errors"]
    await aprobar(client, headers, headers_apr, batch_id)
    r = await aplicar(client, headers, batch_id)
    assert r.status_code == 200, r.text
    return batch_id


async def _preview(client, headers, batch_id: int) -> dict:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/preview", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _filas(preview: dict) -> dict[str, dict]:
    return {f["legacy_lot_code"]: f for f in preview["rows"]}


async def _reconciliacion(client, headers, batch_id: int) -> dict[str, dict]:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=headers)
    assert r.status_code == 200, r.text
    return {f["legacy_lot_code"]: f for f in r.json()["lots"]}


async def _saldos_br03(lotes: dict[str, int]) -> dict[str, int]:
    """Saldo operativo de huevo por cargar (BR-03) de cada lote aplicado."""
    from app.operations.validators import get_hatchery_egg_balance

    async with database.async_session() as s:
        return {ref: await get_hatchery_egg_balance(s, lot_id) for ref, lot_id in lotes.items()}


# ── PIT-PRELOAD-01 · saldo disponible con fosa pre-carga ─────────────────────

@pytest.mark.asyncio
async def test_pit_preload_01_saldo_disponible_resta_la_fosa(auth_headers, http_client, seeded_ids):
    """10000 / 8500 / 200 / 200 / 100 / fosa 200 ⇒ válido y saldo disponible 800 (AC-V4-21)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _fila("PIT-PRE-01", eggs_received=10000, eggs_set=8500, eggs_non_incubable_oversized=200,
              eggs_non_incubable_dirty=200, eggs_non_incubable_broken=100, fertile_eggs_to_pit=200),
    ], 100)

    fila = _filas(await _preview(http_client, auth_headers, batch_id))["PIT-PRE-01"]
    assert fila["derived"]["eggs_available_to_set"] == 800
    assert fila["values"]["fertile_eggs_to_pit"] == {"value": 200, "status": "KNOWN"}

    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["PIT-PRE-01"]
    assert rec["current"]["eggs_available_hatchery"] == 800
    assert rec["opening"]["hatchery"]["fertile_eggs_to_pit"] == 200
    assert rec["opening"]["hatchery"]["eggs_non_incubable_total"] == 500   # la fosa no es un no incubable

    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    assert (await _saldos_br03(lotes))["PIT-PRE-01"] == 800                 # D-25: BR-03 resta la fosa


# ── PIT-PRELOAD-02 · suma pre-carga = recibidos ──────────────────────────────

@pytest.mark.asyncio
async def test_pit_preload_02_suma_igual_a_recibidos_es_valida(auth_headers, http_client, seeded_ids):
    """9000 + 300 + 300 + 200 + 200 = 10000 ⇒ válido (igualdad, `≤`) y saldo 0 (AC-V4-22)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _fila("PIT-PRE-02", eggs_received=10000, eggs_set=9000, eggs_non_incubable_oversized=300,
              eggs_non_incubable_dirty=300, eggs_non_incubable_broken=200, fertile_eggs_to_pit=200),
    ], 101)

    assert _filas(await _preview(http_client, auth_headers, batch_id))["PIT-PRE-02"]["derived"]["eggs_available_to_set"] == 0
    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["PIT-PRE-02"]
    assert rec["current"]["eggs_available_hatchery"] == 0
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    assert (await _saldos_br03(lotes))["PIT-PRE-02"] == 0


# ── PIT-PRELOAD-03 · suma pre-carga > recibidos ──────────────────────────────

@pytest.mark.asyncio
async def test_pit_preload_03_suma_mayor_que_recibidos_se_rechaza(auth_headers, http_client, seeded_ids):
    """AC-V4-23: la suma pre-carga que supera lo recibido se rechaza, también si solo la fosa la rompe.

    - fila 2: 9000 + 500 + 400 + 200 + 100 = 10200 (ya 10100 en `broken`) ⇒ error en `broken`.
    - fila 3: 9000 + 300 + 300 + 200 = 9800 cuadra; con fosa 300 ⇒ 10100 ⇒ error en la fosa.
    - fila 4: `dirty` UNKNOWN; la suma conocida 9000 + 500 + 200 + 400 = 10100 ya supera ⇒ DENY.
    - fila 5: control, 9000 + 300 + 300 + 200 + 200 = 10000 ⇒ válida.
    """
    await preparar(seeded_ids)
    cuerpo, errores = await _errores(http_client, auth_headers, [
        _fila("PIT-PRE-03A", eggs_received=10000, eggs_set=9000, eggs_non_incubable_oversized=500,
              eggs_non_incubable_dirty=400, eggs_non_incubable_broken=200, fertile_eggs_to_pit=100),
        _fila("PIT-PRE-03B", eggs_received=10000, eggs_set=9000, eggs_non_incubable_oversized=300,
              eggs_non_incubable_dirty=300, eggs_non_incubable_broken=200, fertile_eggs_to_pit=300),
        _fila("PIT-PRE-03C", eggs_received=10000, eggs_set=9000, eggs_non_incubable_oversized=500,
              eggs_non_incubable_dirty=None, eggs_non_incubable_broken=200, fertile_eggs_to_pit=400),
        _fila("PIT-PRE-03D", eggs_received=10000, eggs_set=9000, eggs_non_incubable_oversized=300,
              eggs_non_incubable_dirty=300, eggs_non_incubable_broken=200, fertile_eggs_to_pit=200),
    ], 102)
    assert errores == [(2, "eggs_non_incubable_broken", "CONSISTENCY_MISMATCH"),
                       (3, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH"),
                       (4, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (1, 3)


# ── PIT-PRELOAD-04 · fosa > recibidos ────────────────────────────────────────

@pytest.mark.asyncio
async def test_pit_preload_04_fosa_mayor_que_recibidos(auth_headers, http_client, seeded_ids):
    """AC-V4-24: fosa 10001 > recibidos 10000 ⇒ un solo error, en la fosa (sin doble reporte)."""
    await preparar(seeded_ids)
    cuerpo, errores = await _errores(http_client, auth_headers, [
        _fila("PIT-PRE-04", eggs_received=10000, eggs_set=0, fertile_eggs_to_pit=10001),
        _fila("PIT-PRE-04B", eggs_received=10000, eggs_set=0, fertile_eggs_to_pit=10000),   # = recibidos: válida
    ], 103)
    assert errores == [(2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (1, 1)


# ── PIT-PRELOAD-05 · fosa UNKNOWN ⇒ saldo UNKNOWN ─────────────────────────────

@pytest.mark.asyncio
async def test_pit_preload_05_fosa_unknown_saldo_unknown(auth_headers, http_client, seeded_ids):
    """AC-V4-25: fosa vacía ⇒ saldo disponible UNKNOWN (nunca 1000); `dirty` UNKNOWN igual.

    En proceso no depende de la fosa: 8500 − 0. BR-03 operativo comparte el UNKNOWN (§10 · D-28/D-30:
    la suma conocida es una cota, no un saldo; reemplaza a D-25).
    """
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _fila("PIT-PRE-05", eggs_received=10000, eggs_set=8500, eggs_non_incubable_oversized=200,
              eggs_non_incubable_dirty=200, eggs_non_incubable_broken=100, fertile_eggs_to_pit=None),
        _fila("PIT-PRE-05B", eggs_received=10000, eggs_set=8500, eggs_non_incubable_oversized=200,
              eggs_non_incubable_dirty=None, eggs_non_incubable_broken=100, fertile_eggs_to_pit=200),
    ], 104)

    filas = _filas(await _preview(http_client, auth_headers, batch_id))
    assert filas["PIT-PRE-05"]["derived"]["eggs_available_to_set"] is None
    assert filas["PIT-PRE-05"]["derived"]["eggs_in_process"] == 8500
    assert filas["PIT-PRE-05B"]["derived"]["eggs_available_to_set"] is None

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    assert rec["PIT-PRE-05"]["current"]["eggs_available_hatchery"] is None
    assert rec["PIT-PRE-05"]["opening"]["hatchery"]["fertile_eggs_to_pit_status"] == "UNKNOWN"
    assert rec["PIT-PRE-05B"]["current"]["eggs_available_hatchery"] is None

    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    saldos = await _saldos_br03(lotes)
    assert saldos["PIT-PRE-05"] is None                          # fosa UNKNOWN ⇒ saldo UNKNOWN (§10)
    assert saldos["PIT-PRE-05B"] is None                         # dirty UNKNOWN ⇒ saldo UNKNOWN (§10)


# ── PIT-PRELOAD-06 · fosa 0 conocida ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_pit_preload_06_fosa_cero_conocida(auth_headers, http_client, seeded_ids):
    """AC-V4-25: fosa 0 conocida ⇒ válida y saldo numérico 10000 − 8500 − 500 = 1000."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _fila("PIT-PRE-06", eggs_received=10000, eggs_set=8500, eggs_non_incubable_oversized=200,
              eggs_non_incubable_dirty=200, eggs_non_incubable_broken=100, fertile_eggs_to_pit=0),
    ], 105)
    fila = _filas(await _preview(http_client, auth_headers, batch_id))["PIT-PRE-06"]
    assert fila["values"]["fertile_eggs_to_pit"] == {"value": 0, "status": "KNOWN"}
    assert fila["derived"]["eggs_available_to_set"] == 1000
    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["PIT-PRE-06"]
    assert rec["current"]["eggs_available_hatchery"] == 1000


# ── PIT-POST-01 · en proceso no resta la fosa ────────────────────────────────

@pytest.mark.asyncio
async def test_pit_post_01_en_proceso_no_resta_la_fosa(auth_headers, http_client, seeded_ids):
    """AC-V4-26: set 9000, transferidos 8000, fosa 500 ⇒ en proceso 1000 (nunca 500)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _fila("PIT-POST-01", eggs_received=10000, eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=500),
    ], 106)

    fila = _filas(await _preview(http_client, auth_headers, batch_id))["PIT-POST-01"]
    assert fila["derived"]["eggs_in_process"] == 1000
    assert fila["derived"]["eggs_in_process"] != 500
    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["PIT-POST-01"]
    assert rec["opening"]["hatchery"]["eggs_in_process"] == 1000
    assert rec["current"]["eggs_in_process"] == 1000                  # sin eventos post-corte
    assert rec["current"]["eggs_available_hatchery"] == 500            # 10000 − 9000 − 0 − 500


# ── PIT-POST-02 / 03 · transferidos ≤ cargados, sin la fosa ──────────────────

@pytest.mark.asyncio
async def test_pit_post_02_03_transferidos_contra_cargados_sin_fosa(auth_headers, http_client, seeded_ids):
    """AC-V4-26: transferidos > cargados ⇒ DENY en `eggs_transferred`; la fosa no participa.

    - fila 2 (POST-02): transferidos 9001 > cargados 9000 ⇒ un único error en `eggs_transferred`.
    - fila 3 (POST-03): transferidos = cargados = 9000 con fosa 500 (9000 + 500 ≤ 10000) ⇒ válida;
      con la regla superada `transferred + pit ≤ set` habría sido rechazada.
    """
    await preparar(seeded_ids)
    cuerpo, errores = await _errores(http_client, auth_headers, [
        _fila("PIT-POST-02", eggs_received=10000, eggs_set=9000, eggs_transferred=9001, fertile_eggs_to_pit=0),
        _fila("PIT-POST-03", eggs_received=10000, eggs_set=9000, eggs_transferred=9000, fertile_eggs_to_pit=500),
    ], 107)
    assert errores == [(2, "eggs_transferred", "CONSISTENCY_MISMATCH")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (1, 1)


@pytest.mark.asyncio
async def test_pit_post_03_fosa_grande_con_todo_transferido_en_proceso_cero(auth_headers, http_client, seeded_ids):
    """PIT-POST-03 / caso 3 del mandato: set 9000 = transferidos 9000 (fosa 500) ⇒ en proceso 0."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _fila("PIT-POST-03B", eggs_received=10000, eggs_set=9000, eggs_transferred=9000, fertile_eggs_to_pit=500),
        _fila("PIT-POST-03C", eggs_received=10000, eggs_set=9000, eggs_transferred=None, fertile_eggs_to_pit=500),
    ], 108)
    filas = _filas(await _preview(http_client, auth_headers, batch_id))
    assert filas["PIT-POST-03B"]["derived"]["eggs_in_process"] == 0
    assert filas["PIT-POST-03C"]["derived"]["eggs_in_process"] is None   # transferidos UNKNOWN ⇒ UNKNOWN


# ── Doble conteo ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pit_doble_conteo_fosa_solo_en_la_etapa_pre_carga(auth_headers, http_client, seeded_ids):
    """AC-V4-27: 10000 / 8500 / 200 / 200 / 100 / fosa 200 y transferidos 8000.

    Saldo disponible 800 (la fosa resta una vez, antes de la carga) y en proceso 500 = 8500 − 8000.
    Si alguien vuelve a restar la fosa en proceso saldría 300: este test lo detecta.
    """
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _fila("PIT-DOBLE", eggs_received=10000, eggs_set=8500, eggs_non_incubable_oversized=200,
              eggs_non_incubable_dirty=200, eggs_non_incubable_broken=100, fertile_eggs_to_pit=200,
              eggs_transferred=8000),
    ], 109)

    fila = _filas(await _preview(http_client, auth_headers, batch_id))["PIT-DOBLE"]
    assert fila["derived"]["eggs_available_to_set"] == 800
    assert fila["derived"]["eggs_in_process"] == 500
    assert fila["derived"]["eggs_in_process"] != 300

    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["PIT-DOBLE"]
    assert rec["opening"]["hatchery"]["eggs_in_process"] == 500
    assert rec["current"]["eggs_in_process"] == 500
    assert rec["current"]["eggs_available_hatchery"] == 800
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    assert (await _saldos_br03(lotes))["PIT-DOBLE"] == 800


# ── O-15 · el agregado sigue propagando UNKNOWN ──────────────────────────────

@pytest.mark.asyncio
async def test_pit_o15_agregado_en_proceso_sigue_unknown(auth_headers, http_client, seeded_ids):
    """AC-V4-28: una fila con en proceso UNKNOWN (transferidos vacío) ⇒ summary UNKNOWN, nunca 0 ni 1000.

    La fosa UNKNOWN ya NO vuelve UNKNOWN el en proceso (D-23): la fila B tiene fosa vacía y en
    proceso 1000; la C tiene transferidos vacío y es la que vuelve UNKNOWN el agregado.
    """
    await preparar(seeded_ids)
    batch_id = await _subir_para_validar(http_client, auth_headers, [
        _fila("PIT-O15-A", eggs_received=10000, eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=100),
        _fila("PIT-O15-B", eggs_received=10000, eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=None),
        _fila("PIT-O15-C", eggs_received=10000, eggs_set=9000, eggs_transferred=None, fertile_eggs_to_pit=0),
    ], 110)
    preview = await _preview(http_client, auth_headers, batch_id)
    filas = _filas(preview)
    assert filas["PIT-O15-A"]["derived"]["eggs_in_process"] == 1000
    assert filas["PIT-O15-B"]["derived"]["eggs_in_process"] == 1000
    assert filas["PIT-O15-C"]["derived"]["eggs_in_process"] is None
    resumen = preview["summary"]
    assert resumen["eggs_in_process"] is None
    assert resumen["eggs_in_process_status"] == "UNKNOWN"
    assert resumen["eggs_in_process_unknown_rows"] == 1


# ── V3 histórica intacta (D-27) ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pit_v3_historica_no_cambia(auth_headers, http_client, seeded_ids):
    """V3: `eggs_in_process = set − transferred − eggs_discarded` y saldo `received − set`, sin fosa."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [fila_incubadora("PIT-V3", eggs_transferred=8000, fertile_eggs_to_pit=None)],
                                    111)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)

    from app.cutover.models import CutoverBatch, HatcheryOpening

    async with database.async_session() as s:
        ho = (await s.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == lotes["PIT-V3"]))).scalar_one()
        ho.eggs_discarded, ho.eggs_discarded_status = 100, "KNOWN"
        ho.fertile_eggs_to_pit, ho.fertile_eggs_to_pit_status = None, "UNKNOWN"
        batch = (await s.execute(select(CutoverBatch).where(CutoverBatch.id == batch_id))).scalar_one()
        batch.template_version = "v3"
        await s.commit()

    h = (await _reconciliacion(http_client, auth_headers, batch_id))["PIT-V3"]
    assert h["opening"]["hatchery"]["eggs_in_process"] == 9000 - 8000 - 100   # fórmula V3
    assert h["current"]["eggs_available_hatchery"] == 10000 - 9000            # V3: received − set
