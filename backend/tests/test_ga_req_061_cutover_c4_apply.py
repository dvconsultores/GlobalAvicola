"""GA-REQ-061 · T14 · C4 — apply atómico con snapshots de opening (RED).

Rojo en HEAD (`3e3f2cb`): no existe `apply` (404). La Implementación añade el
apply transaccional: `APPROVED → APPLIED`, lotes MIGRATED (reusando el existente
sin duplicar, AC20-22), snapshots `OpeningBalance` con **saldo vivo al corte**
(no se resta lo histórico: 10.000→9.965/535 se verifica en C5 sobre esta base),
semántica UNKNOWN visible, auditoría APPLY/FAILED_APPLY y rollback TOTAL
(todo-o-nada, AC26-28).
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

CORTE = "2026-10-06T00:00:00+00:00"

FILAS = [
    ["CUT-MG-001", "2026-08-15", 5000, 5000, 300, 200, None, "histórico conocido"],
    ["CUT-MG-002", "2026-09-01", 2000, 2000, None, None, None, "histórico desconocido"],
]


async def _fase() -> int:
    """Fase productiva para el opening (los tests crean las suyas, patrón del repo)."""
    from app.masters.models import ProductivePhase

    async with database.async_session() as session:
        fase = ProductivePhase(name="Producción", code="PROD", is_initial=True, order=1)
        session.add(fase)
        await session.commit()
        await session.refresh(fase)
        return fase.id


async def _batch_aprobado(client, auth_headers, seeded_ids, filas=FILAS) -> int:
    await _otorgar(seeded_ids["role_approver_id"], ("cutover", "approve"), ("cutover", "read"))
    batch_id = await _crear_batch(client, auth_headers, cutover=CORTE)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                          headers=auth_headers, files=_subir(_xlsx(filas)))
    assert r.status_code == 200 and r.json()["status"] == "validated", r.text
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 200
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/approve",
                              headers=_headers_aprobar(seeded_ids))).status_code == 200
    return batch_id


@pytest.mark.asyncio
async def test_c4_apply_snapshots_saldo_vivo(auth_headers, client, seeded_ids):
    """Apply feliz: lotes MIGRATED + openings con saldo vivo y UNKNOWN visible."""
    await _fase()
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids)

    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "applied"

    from app.lots.models import OpeningBalance
    from app.masters.models import Lot

    async with database.async_session() as session:
        lotes = (await session.execute(
            select(Lot).where(Lot.legacy_lot_code.in_(["CUT-MG-001", "CUT-MG-002"])))).scalars().all()
        assert len(lotes) == 2
        assert {lote.origin for lote in lotes} == {"MIGRATED"}
        por_codigo = {lote.lot_code: lote for lote in lotes}

        openings = (await session.execute(
            select(OpeningBalance).where(OpeningBalance.lot_id.in_([l.id for l in lotes])))
        ).scalars().all()
        assert len(openings) == 2
        por_lote = {o.lot_id: o for o in openings}

        o1 = por_lote[por_codigo["CUT-MG-001"].id]
        # El saldo inicial ES el saldo vivo al corte (NO se le resta lo histórico).
        assert (o1.initial_male_count, o1.initial_female_count) == (5000, 5000)
        assert (o1.accumulated_mortality_male, o1.accumulated_mortality_female) == (300, 200)
        assert o1.mortality_status == "KNOWN"
        assert o1.feed_status == "UNKNOWN"          # UNKNOWN visible, jamás fabricado 0
        assert o1.is_manual_activation is False
        assert o1.cutover_datetime is not None
        assert o1.cutover_item_id is not None
        assert o1.source_system == "EXCEL"
        assert o1.legacy_lot_code == "CUT-MG-001"

        o2 = por_lote[por_codigo["CUT-MG-002"].id]
        assert (o2.initial_male_count, o2.initial_female_count) == (2000, 2000)
        assert o2.mortality_status == "UNKNOWN"     # celda vacía ⇒ UNKNOWN ≠ 0

    # Los items quedaron ligados a sus lotes.
    items = (await client.get(f"/api/v1/cutover-batches/{batch_id}/items", headers=auth_headers)).json()["items"]
    assert all(it["lot_id"] for it in items)
    assert {it["validation_status"] for it in items} == {"applied"}


@pytest.mark.asyncio
async def test_c4_apply_solo_desde_approved_y_una_vez(auth_headers, client, seeded_ids):
    """Un VALIDATED no se aplica; un APPLIED es terminal (re-apply ⇒ 409)."""
    await _fase()
    await _otorgar(seeded_ids["role_approver_id"], ("cutover", "approve"))
    # Referencias propias de este test: los lotes persisten entre tests del módulo.
    filas_propias = [
        ["CUT-MG-101", "2026-08-15", 5000, 5000, 300, 200, None, ""],
        ["CUT-MG-102", "2026-09-01", 2000, 2000, None, None, None, ""],
    ]
    batch_id = await _crear_batch(client, auth_headers, cutover="2026-10-07T00:00:00+00:00")
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                          headers=auth_headers, files=_subir(_xlsx(filas_propias)))
    assert r.status_code == 200

    no_aprobado = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert no_aprobado.status_code == 409, no_aprobado.text

    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 200
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/approve",
                              headers=_headers_aprobar(seeded_ids))).status_code == 200
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/apply",
                              headers=auth_headers)).status_code == 200
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/apply",
                              headers=auth_headers)).status_code == 409


@pytest.mark.asyncio
async def test_c4_duplicado_en_lote_rollback_total(auth_headers, client, seeded_ids):
    """Referencia repetida ⇒ LOT_DUPLICATE y **nada** aplicado (atomicidad AC27/28) + FAILED_APPLY."""
    await _fase()
    filas = [
        ["CUT-DUP-1", "2026-08-15", 1000, 1000, None, None, None, ""],
        ["CUT-DUP-1", "2026-08-16", 500, 500, None, None, None, ""],
    ]
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=filas)

    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert r.status_code == 422, r.text
    assert "LOT_DUPLICATE" in r.text

    from app.audit.models import AuditLog
    from app.lots.models import OpeningBalance
    from app.masters.models import Lot

    async with database.async_session() as session:
        lotes = (await session.execute(
            select(Lot).where(Lot.legacy_lot_code == "CUT-DUP-1"))).scalars().all()
        assert lotes == []  # rollback total: ni un lote a medias

        items = (await client.get(f"/api/v1/cutover-batches/{batch_id}/items",
                                  headers=auth_headers)).json()["items"]
        assert all(it["lot_id"] is None for it in items)

        # El batch sigue aprobado (no APPLIED) y con rastro FAILED_APPLY.
        acciones = (await session.execute(
            select(AuditLog.action).where(AuditLog.entity_id == str(batch_id),
                                          AuditLog.entity_type == "cutover_batch"))).scalars().all()
        nombres = {getattr(a, "name", str(a)) for a in acciones}
        assert "FAILED_APPLY" in nombres, nombres


@pytest.mark.asyncio
async def test_c4_lote_existente_se_reusa_sin_duplicar(auth_headers, client, seeded_ids):
    """AC20: un lote existente se relaciona (no se duplica); su origen NATIVE se conserva."""
    await _fase()
    from app.masters.models import Lot

    empresa = seeded_ids["company_id"]
    async with database.async_session() as session:
        previo = Lot(company_id=empresa, lot_code="CUT-REUSE-1", origin="NATIVE",
                     bird_type=None, activation_type="normal")
        session.add(previo)
        await session.commit()
        await session.refresh(previo)
        previo_id = previo.id

    filas = [["CUT-REUSE-1", "2026-08-15", 1200, 1300, 10, 20, None, ""]]
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=filas)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert r.status_code == 200, r.text

    from app.lots.models import OpeningBalance

    async with database.async_session() as session:
        iguales = (await session.execute(
            select(Lot).where(Lot.lot_code == "CUT-REUSE-1"))).scalars().all()
        assert len(iguales) == 1 and iguales[0].id == previo_id
        assert iguales[0].origin == "NATIVE"  # no se reescribe el origen histórico

        opening = (await session.execute(
            select(OpeningBalance).where(OpeningBalance.lot_id == previo_id))).scalar_one_or_none()
        assert opening is not None and opening.legacy_lot_code == "CUT-REUSE-1"
