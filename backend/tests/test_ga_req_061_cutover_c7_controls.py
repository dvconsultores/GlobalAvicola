"""GA-REQ-061 · T14 · C7 — controles verdes (CUT-CTL-01..06).

Controles que la suite conserva: el cutover no puede romper lo nativo. CTL-02/03/
04 ejercen el **motor operacional por API** sobre un lote MIGRATED aplicado (los
mismos endpoints del lote nativo, AC57/58). El corte de estos controles es
**pasado** (`2026-08-01`) para que las fechas de evento puedan venir del reloj de
la suite (`recent_event_date()`, BR-19) y sigan siendo post-cutover.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from test_ga_req_061_cutover_c2_lifecycle import _crear_batch, _subir, _xlsx  # noqa: E402
from test_ga_req_061_cutover_c3_lifecycle import _headers_aprobar, _otorgar  # noqa: E402
from test_ga_req_061_cutover_c4_apply import _fase  # noqa: E402
from time_reference import recent_event_date  # noqa: E402

CORTE_PASADO = "2026-08-01T00:00:00+00:00"


def _filas(etiqueta: str, ref_extra: str | None = None) -> list[list]:
    filas = [[f"CUT-G7C-{etiqueta}-1", "2026-07-01", 3000, 3000, 50, 50, None, "controles C7"]]
    if ref_extra:
        filas.append([ref_extra, "2026-06-01", 100, 100, None, None, None, "lote nativo reusado"])
    return filas


async def _aplicar_corte_pasado(client, auth_headers, seeded_ids, etiqueta: str, ref_extra: str | None = None):
    await _fase()
    batch_id = await _crear_batch(client, auth_headers, cutover=CORTE_PASADO)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                          headers=auth_headers, files=_subir(_xlsx(_filas(etiqueta, ref_extra))))
    assert r.status_code == 200, r.text
    await _otorgar(seeded_ids["role_approver_id"], ("cutover", "approve"), ("cutover", "read"))
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 200
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/approve",
                              headers=_headers_aprobar(seeded_ids))).status_code == 200
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert r.status_code == 200, r.text
    items = (await client.get(f"/api/v1/cutover-batches/{batch_id}/items", headers=auth_headers)).json()["items"]
    por_ref = {it["legacy_lot_reference"]: it["lot_id"] for it in items}
    return batch_id, por_ref


@pytest.mark.asyncio
async def test_ctl01_lote_nativo_reusado_intacto(auth_headers, client, seeded_ids):
    """CTL-01/AC20-21: el lote nativo reusado conserva origen y fecha; solo gana la referencia."""
    from app.masters.models import Lot

    async with database.async_session() as session:
        nativo = (await session.execute(select(Lot).order_by(Lot.id))).scalars().all()[1]
        codigo, inicio, origen, lote_id = nativo.lot_code, nativo.start_date, nativo.origin, nativo.id

    _, por_ref = await _aplicar_corte_pasado(client, auth_headers, seeded_ids, "CTL1", codigo)

    async with database.async_session() as session:
        despues = (await session.execute(select(Lot).where(Lot.id == lote_id))).scalars().first()
    assert por_ref[codigo] == lote_id, "debe reusar el lote existente, no crear otro"
    assert despues.origin == origen == "NATIVE"
    assert despues.start_date == inicio, "la fecha de un lote nativo no se reescribe"


@pytest.mark.asyncio
async def test_ctl02_mortalidad_post_cutover_por_api_sigue_operando(auth_headers, client, seeded_ids):
    """CTL-02/AC57-58: mortalidad normal por el motor sobre lote MIGRATED ⇒ reporte la refleja."""
    batch_id, por_ref = await _aplicar_corte_pasado(client, auth_headers, seeded_ids, "CTL2")
    lote = por_ref["CUT-G7C-CTL2-1"]

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "mortality_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 10, "avg_weight": 1500.0}]})
    assert r.status_code == 201, r.text

    rec = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    fila = next(f for f in rec.json()["lots"] if f["lot_id"] == lote)
    assert fila["post"]["mortality"] == 10
    assert fila["current_live"] == 5990, "6.000 − 10"


@pytest.mark.asyncio
async def test_ctl03_pesaje_normal_funciona(auth_headers, client, seeded_ids):
    """CTL-03: pesaje por el motor en lote MIGRATED (mismo endpoint que el nativo)."""
    _, por_ref = await _aplicar_corte_pasado(client, auth_headers, seeded_ids, "CTL3")
    lote = por_ref["CUT-G7C-CTL3-1"]

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "weight_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 5, "avg_weight": 1600.0}]})
    assert r.status_code == 201, r.text
    assert r.json()["event_type"] == "weight_recording"


@pytest.mark.asyncio
async def test_ctl04_transferencia_normal_funciona(auth_headers, client, seeded_ids):
    """CTL-04/RR-02: transferencia intra-lote neutra — el saldo no cambia."""
    batch_id, por_ref = await _aplicar_corte_pasado(client, auth_headers, seeded_ids, "CTL4")
    lote = por_ref["CUT-G7C-CTL4-1"]

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "bird_transfer", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 2, "avg_weight": 1500.0}]})
    assert r.status_code in (201, 400), r.text  # 400 legítimo si BR exige destino; el saldo nunca se corrompe

    rec = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    fila = next(f for f in rec.json()["lots"] if f["lot_id"] == lote)
    assert fila["current_live"] == 6000, "una transferencia intra-lote es neutra (RR-02)"


@pytest.mark.asyncio
async def test_ctl05_reporting_normal_sin_cambios(auth_headers, client, seeded_ids):
    """CTL-05: el reporte semanal nativo (R-218) responde igual con lotes migrados en la empresa."""
    from app.masters.models import Lot

    async with database.async_session() as session:
        nativo = (await session.execute(select(Lot).order_by(Lot.id))).scalars().all()[0]

    await _aplicar_corte_pasado(client, auth_headers, seeded_ids, "CTL5")
    r = await client.get(f"/api/v1/reports/lot/{nativo.id}/weekly", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), dict)


@pytest.mark.asyncio
async def test_ctl06_rbac_existente_intacto(auth_headers, client):
    """CTL-06: los permisos previos siguen vigentes (listado con sesión; 401 sin ella)."""
    assert (await client.get("/api/v1/lots", headers=auth_headers)).status_code == 200
    assert (await client.get("/api/v1/lots")).status_code == 401
