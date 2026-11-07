"""SPEC 014 · Cutover — transferencias históricas: apply, UNKNOWN y reconciliación (RED).

El apply real persiste los 4 componentes de transferencias en `opening_balances` (v3), la
reconciliación y el informe del lote los exponen por sexo y con estado, UNKNOWN nunca se
convierte en 0 y lo histórico no se vuelve a contar como evento post-corte.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select, text

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    aplicar, aprobar, corte, crear_batch, fila_reproductoras, headers_aprobador,
    items_por_referencia, preparar, subir, xlsx_v2,
)
from time_reference import recent_event_date  # noqa: E402

from app.lots.models import OpeningBalance  # noqa: E402
from app.operations.models import OperationalEvent  # noqa: E402

DIAS_CORTE = 30
#: SPEC 014 §3: lote origen (entrega 300 machos) y receptor (los recibe).
ORIGEN = dict(birds_placed_males=1300, historical_mortality_males=165, historical_culls_males=0,
              historical_transfers_in_males=0, historical_transfers_out_males=300, live_males=835,
              birds_placed_females=9500, historical_mortality_females=450,
              historical_culls_females=50, historical_transfers_in_females=0,
              historical_transfers_out_females=0, live_females=9000)
RECEPTOR = dict(birds_placed_males=1000, historical_transfers_in_males=300,
                historical_mortality_males=100, historical_culls_males=20,
                historical_transfers_out_males=0, live_males=1180,
                birds_placed_females=9000, historical_transfers_in_females=0,
                historical_mortality_females=450, historical_culls_females=0,
                historical_transfers_out_females=0, live_females=8550)


def _ref(base: str) -> str:
    """Referencia única por test: la BD es compartida en la sesión de pytest."""
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _row(ref: str, **valores) -> list:
    """Fila de reproductoras con los 6 componentes del balance por sexo."""
    return fila_reproductoras("breeder", ref, **valores)


async def _lote_aplicado(client, headers, seeded_ids, filas: list) -> tuple[int, dict[str, int]]:
    b = await crear_batch(client, headers, "breeder", corte(DIAS_CORTE))
    r = await subir(client, headers, b, xlsx_v2("breeder", filas, company_id=seeded_ids["company_id"]))
    assert r.status_code == 200 and r.json()["status"] == "validated", r.text
    await aprobar(client, headers, headers_aprobador(seeded_ids), b)
    assert (await aplicar(client, headers, b)).status_code == 200
    return b, await items_por_referencia(client, headers, b)


async def _opening(lot_id: int) -> OpeningBalance:
    async with database.async_session() as s:
        q = select(OpeningBalance).where(OpeningBalance.lot_id == lot_id)
        return (await s.execute(q)).scalars().one()


async def _fila(client, headers, batch_id: int, lot_id: int) -> dict:
    rec = (await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=headers)).json()
    return next(f for f in rec["lots"] if f["lot_id"] == lot_id)


@pytest.mark.asyncio
async def test_ht_apply_origen_y_receptor(auth_headers, http_client, seeded_ids):
    """El apply persiste las transferencias por sexo: alojadas y mortalidad no se contaminan."""
    await preparar(seeded_ids)
    ori, rec = _ref("HT-AP-ORI"), _ref("HT-AP-REC")
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids,
                                      [_row(ori, **ORIGEN), _row(rec, **RECEPTOR)])
    casos = {ori: (0, 0, 300, 0, 835, 9000, 1300, 9500, 165, 0),
             rec: (300, 0, 0, 0, 1180, 8550, 1000, 9000, 100, 20)}
    for ref, esperado in casos.items():
        ob = await _opening(por_ref[ref])
        assert (ob.accumulated_transfers_in_male, ob.accumulated_transfers_in_female,
                ob.accumulated_transfers_out_male, ob.accumulated_transfers_out_female) == esperado[:4], ref
        assert (ob.transfers_in_status, ob.transfers_out_status) == ("KNOWN", "KNOWN"), ref
        assert (ob.initial_male_count, ob.initial_female_count) == esperado[4:6], ref
        assert (ob.placed_male_count, ob.placed_female_count) == esperado[6:8], ref
        assert (ob.accumulated_mortality_male, ob.accumulated_culls_male) == esperado[8:10], ref
        assert ob.template_version == "v3", ref
        async with database.async_session() as s:
            q = select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.lot_id == por_ref[ref])
            assert await s.scalar(q) == 0, ref


@pytest.mark.asyncio
async def test_ht_unknown_no_es_cero(auth_headers, http_client, seeded_ids):
    """`out_males` UNKNOWN se aplica sin inventar cero; un `0` explícito sí es KNOWN."""
    await preparar(seeded_ids)
    unknown = {k: v for k, v in ORIGEN.items() if k != "historical_transfers_out_males"}
    cero = {**ORIGEN, "birds_placed_males": 1135, "live_males": 970,
            "historical_transfers_out_males": 0}
    ori, cero_ref = _ref("HT-AP-ORI"), _ref("HT-AP-CERO")
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids,
                                      [_row(ori, **unknown), _row(cero_ref, **cero)])
    ob = await _opening(por_ref[ori])
    assert ob.accumulated_transfers_out_male is None
    assert ob.transfers_out_status == "UNKNOWN"
    f = (await _fila(http_client, auth_headers, b, por_ref[ori]))["opening"]
    assert f["historical_transfers_out"] is None
    assert f["transfers_out_status"] == "UNKNOWN"
    ob0 = await _opening(por_ref[cero_ref])
    assert (ob0.accumulated_transfers_out_male, ob0.transfers_out_status) == (0, "KNOWN")
    f0 = (await _fila(http_client, auth_headers, b, por_ref[cero_ref]))["opening"]
    assert (f0["historical_transfers_out"], f0["transfers_out_status"]) == (0, "KNOWN")


@pytest.mark.asyncio
async def test_ht_reconciliacion_expone_transferencias(auth_headers, http_client, seeded_ids):
    """La reconciliación suma machos+hembras por sentido y publica el estado de cada uno."""
    await preparar(seeded_ids)
    ori_ref, rec_ref = _ref("HT-AP-ORI"), _ref("HT-AP-REC")
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids,
                                      [_row(ori_ref, **ORIGEN), _row(rec_ref, **RECEPTOR)])
    ori = (await _fila(http_client, auth_headers, b, por_ref[ori_ref]))["opening"]
    rec = (await _fila(http_client, auth_headers, b, por_ref[rec_ref]))["opening"]
    assert (ori["historical_transfers_in"], ori["historical_transfers_out"]) == (0, 300)
    assert (rec["historical_transfers_in"], rec["historical_transfers_out"]) == (300, 0)
    for opening in (ori, rec):
        assert (opening["transfers_in_status"], opening["transfers_out_status"]) == ("KNOWN", "KNOWN")


@pytest.mark.asyncio
async def test_ht_sin_doble_conteo(auth_headers, http_client, seeded_ids):
    """Las transferencias históricas viven solo en el opening: el evento post no las re-suma."""
    await preparar(seeded_ids)
    ori_ref = _ref("HT-AP-ORI")
    b, por_ref = await _lote_aplicado(http_client, auth_headers, seeded_ids, [_row(ori_ref, **ORIGEN)])
    lote = por_ref[ori_ref]
    r = await http_client.post("/api/v1/operations", headers=auth_headers,
                               json={"lot_id": lote, "event_type": "mortality_recording",
                                     "event_date": recent_event_date(),
                                     "bird_movements": [{"sex": "male", "quantity": 15, "avg_weight": 3600.0}]})
    assert r.status_code == 201, r.text
    f = await _fila(http_client, auth_headers, b, lote)
    assert f["opening"]["live"] == 835 + 9000 == 9835
    assert f["post"]["mortality"] == 15
    assert f["current_live"] == 9835 - 15
    assert f["current_live"] == f["opening"]["live"] + f["post"]["entradas"] - f["post"]["salidas"]
    detalle = await http_client.get(f"/api/v1/lots/{lote}", headers=auth_headers)
    assert detalle.status_code == 200, detalle.text
    ob = detalle.json()["opening_balance"]
    assert (ob["accumulated_transfers_out_male"], ob["transfers_out_status"]) == (300, "KNOWN")


@pytest.mark.asyncio
async def test_ht_migracion_columnas():
    """Las 6 columnas existen, las 4 de cantidad son nullable y los estados defaultean UNKNOWN."""
    esperadas = {
        "accumulated_transfers_in_male", "accumulated_transfers_in_female",
        "accumulated_transfers_out_male", "accumulated_transfers_out_female",
        "transfers_in_status", "transfers_out_status",
    }
    async with database.async_session() as s:
        q = text("SELECT column_name, is_nullable, column_default FROM information_schema.columns "
                 "WHERE table_name = 'opening_balances' AND table_schema = current_schema()")
        filas = (await s.execute(q)).all()
    columnas = {f[0]: (f[1], f[2]) for f in filas}
    assert esperadas <= set(columnas), sorted(esperadas - set(columnas))
    for nombre in sorted(esperadas):
        es_nullable, default = columnas[nombre]
        if nombre.startswith("accumulated_"):
            assert es_nullable == "YES", nombre
            assert default is None, nombre
        else:
            assert "UNKNOWN" in str(default), nombre
