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
from test_ga_req_061_cutover_c2_lifecycle import BU_FIXTURE, _crear_batch, _subir, _xlsx  # noqa: E402
from test_ga_req_061_cutover_c3_lifecycle import _headers_aprobar, _otorgar  # noqa: E402
from time_reference import days_ago, iso_days_ago  # noqa: E402

#: Corte del checkpoint (fecha civil, computada: sin literales que caduquen).
CORTE = days_ago(40).isoformat() + "T00:00:00+00:00"

FILAS = [
    ["CUT-MG-001", iso_days_ago(60), 5000, 5000, 300, 200, None, "histórico conocido"],
    ["CUT-MG-002", iso_days_ago(45), 2000, 2000, None, None, None, "histórico desconocido"],
]


async def _fase() -> int:
    """Fase productiva del opening.

    SPEC 006: el contrato v2 declara la fase por código (`PROD` para la fixture de
    reproductoras), así que aquí se garantiza el catálogo `CRIA/PROD/INCUB/ENGORDE` (una fila
    por código: la siembra de la suite completa los localiza con `scalar_one_or_none`).
    """
    from cutover_v2_fixtures import asegurar_fases

    return (await asegurar_fases())["PROD"]


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
        ["CUT-MG-101", iso_days_ago(60), 5000, 5000, 300, 200, None, ""],
        ["CUT-MG-102", iso_days_ago(45), 2000, 2000, None, None, None, ""],
    ]
    batch_id = await _crear_batch(client, auth_headers, cutover=days_ago(39).isoformat() + "T00:00:00+00:00")
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
    """Referencia repetida ⇒ `LOT_DUPLICATE` y **nada** aplicado (atomicidad AC27/28).

    SPEC 006 adelanta la detección al staging: la fila repetida queda inválida, el batch no
    llega a APPROVED y ningún lote se crea. La guarda del apply (`LOT_DUPLICATE` → rollback +
    `FAILED_APPLY`) se conserva como defensa en profundidad y se ejercita en
    `test_cutover_v2_apply.py`.
    """
    await _fase()
    filas = [
        ["CUT-DUP-1", iso_days_ago(60), 1000, 1000, None, None, None, ""],
        ["CUT-DUP-1", iso_days_ago(59), 500, 500, None, None, None, ""],
    ]
    batch_id = await _crear_batch(client, auth_headers, cutover=CORTE)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/upload", headers=auth_headers, files=_subir(_xlsx(filas)))
    assert r.status_code == 200, r.text
    assert (r.json()["status"], r.json()["valid_rows"], r.json()["invalid_rows"]) == ("validating", 1, 1), r.text
    v = await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    assert [(e["row_number"], e["error_code"]) for e in v.json()["errors"]] == [(3, "LOT_DUPLICATE")], v.text
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit", headers=auth_headers)).status_code == 409
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)).status_code == 409

    from app.masters.models import Lot

    async with database.async_session() as session:
        lotes = (await session.execute(
            select(Lot).where(Lot.legacy_lot_code == "CUT-DUP-1"))).scalars().all()
        assert lotes == []  # nada aplicado: ni un lote a medias
    items = (await client.get(f"/api/v1/cutover-batches/{batch_id}/items", headers=auth_headers)).json()["items"]
    assert all(it["lot_id"] is None for it in items)


@pytest.mark.asyncio
async def test_c4_lote_existente_se_reusa_sin_duplicar(auth_headers, client, seeded_ids):
    """AC20: un lote existente se relaciona (no se duplica); su origen NATIVE se conserva."""
    await _fase()
    from app.masters.models import BirdTypeEnum, Lot

    empresa = seeded_ids["company_id"]
    async with database.async_session() as session:
        # SPEC 006: el lote a reutilizar es de la misma BU y se declara con `existing_lot_code`.
        previo = Lot(company_id=empresa, lot_code="CUT-REUSE-1", origin="NATIVE",
                     bird_type=BirdTypeEnum(BU_FIXTURE), activation_type="normal")
        session.add(previo)
        await session.commit()
        await session.refresh(previo)
        previo_id = previo.id

    filas = [["CUT-REUSE-1", iso_days_ago(60), 1200, 1300, 10, 20, None, "", {"existing_lot_code": "CUT-REUSE-1"}]]
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
