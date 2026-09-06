"""Aprobación obligatoria antes del cierre — `GA-REM-036`, hallazgo `R-76`.

Cubre `AC01`…`AC09`.

`docs/12 §6 R7`: «un lote no puede cerrarse si tiene registros sin aprobar». No estaba
implementado: `close_lot` comprobaba que el lote estuviera activo y que `BR-05` se cumpliera,
y nada más.

Los siete estados que bloquean y los seis que no salen de `docs/12 §4`, justificados uno a
uno en `R76_LOT_CLOSE_APPROVAL_MATRIX`. Aquí se comprueban **todos**, porque una regla que
bloquea de más es tan defectuosa como una que no bloquea.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from app.operations.models import EventStatus
from tests.time_reference import iso_days_ago

PREFIJO = "CA-TEST-"

#: `docs/12 §4`. Estados anteriores a la aprobación, más el rechazo — que no es terminal.
BLOQUEAN = [
    EventStatus.DRAFT, EventStatus.REGISTERED, EventStatus.PENDING_REVIEW,
    EventStatus.IN_REVIEW, EventStatus.RETURNED, EventStatus.CORRECTED,
    EventStatus.REJECTED,
]

#: La aprobación y todo lo posterior, más lo anulado.
NO_BLOQUEAN = [
    EventStatus.APPROVED, EventStatus.CONSOLIDATED, EventStatus.SENT_TO_SAP,
    EventStatus.SAP_CONFIRMED, EventStatus.SAP_ERROR, EventStatus.CANCELLED,
]


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, InspectionDetail, OperationalEvent,
    )
    from app.review.models import ApprovalAction

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(ids)))).scalars().all()
            if eventos:
                for sub in (BirdMovement, EggMovement, FeedMovement, InspectionDetail,
                            ApprovalAction):
                    await c.execute(delete(sub).where(sub.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
    await e.dispose()


async def _fijar_estado(motor, event_id, estado):
    """Coloca un evento en un estado concreto.

    Se hace por base y no por la API porque el objetivo es recorrer **los trece** estados de
    `docs/12 §4`, y varios —`sap_error`, `cancelled`— no son alcanzables por el flujo normal
    en una prueba. Lo que se está probando es la guarda del cierre, no el flujo de revisión,
    que tiene sus propias pruebas en `P-07`.
    """
    from app.operations.models import OperationalEvent
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        evento = (await s.execute(select(OperationalEvent).where(
            OperationalEvent.id == event_id))).scalar_one()
        evento.status = estado
        await s.commit()


@pytest_asyncio.fixture
async def lote_cerrable(client, auth_headers, seeded_ids, motor):
    """Un lote que satisface **todas** las demás condiciones de cierre.

    Está activo y cumple `BR-05` —pesaje y alimento—, de modo que cualquier rechazo posterior
    solo puede venir de `R7`. Los tres eventos quedan aprobados.

    El tercero, una inspección, es el que las pruebas mueven de estado. **No puede ser el
    pesaje ni el alimento**: anular cualquiera de esos dos rompería `BR-05` legítimamente y el
    rechazo llegaría por la causa equivocada, que es justo lo que hay que evitar para aislar
    `R7`.
    """
    r = await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    lot_id = r.json()["id"]

    ids = []
    for tipo, extra in (
        ("weight_recording", {"bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 2000}]}),
        ("feed_registration", {"feed_movements": [{"quantity_kg": 100.0}]}),
        ("farm_inspection", {"inspection_details": [
            {"parameter": "Bioseguridad", "value": "ok", "status": "ok"}]}),
    ):
        ev = await client.post("/api/v1/operations", headers=auth_headers, json={
            "lot_id": lot_id, "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"], "event_type": tipo,
            "event_date": iso_days_ago(0), **extra,
        })
        assert ev.status_code == 201, f"{tipo}: {ev.text}"
        ids.append(ev.json()["id"])
        await _fijar_estado(motor, ev.json()["id"], EventStatus.APPROVED)

    return {"lot_id": lot_id, "eventos": ids}


async def _cerrar(client, cab, lot_id):
    return await client.post(f"/api/v1/lots/{lot_id}/close", headers=cab)


async def _estado_del_lote(motor, lot_id):
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == lot_id))).scalar_one()
        return lote.status, lote.end_date


# ── AC01 · el CONTROL ─────────────────────────────────────────────────────────

async def test_t_076_01_con_todo_aprobado_el_lote_cierra(
    client, auth_headers, lote_cerrable, motor
):
    """`AC01` · sin este control, un rechazo posterior no probaría nada."""
    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, f"CONTROL falló: el lote debería ser cerrable — {r.text}"


# ── AC02 · AC03 · AC05 · AC06 · los siete estados que bloquean ────────────────

@pytest.mark.parametrize("estado", BLOQUEAN, ids=[e.value for e in BLOQUEAN])
async def test_t_076_02_un_registro_sin_aprobar_impide_el_cierre(
    client, auth_headers, lote_cerrable, motor, estado
):
    """`AC02`, `AC03`, `AC05`, `AC06` · `docs/12 R7`.

    TRATAMIENTO: el mismo lote y la misma llamada que el CONTROL; lo único que cambia es el
    estado de **un** registro. `BR-05` sigue satisfecho porque el pesaje y el alimento siguen aprobados.
    """
    await _fijar_estado(motor, lote_cerrable["eventos"][2], estado)

    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 400, (
        f"un registro en «{estado.value}» debe impedir el cierre: {r.status_code} {r.text}"
    )
    assert r.json().get("rule") == "R7", r.json()

    # `AC05` y `AC06` · la negativa precede a cualquier mutación.
    situacion, fecha = await _estado_del_lote(motor, lote_cerrable["lot_id"])
    assert situacion == "active", f"el lote cambió de estado pese al rechazo: {situacion}"
    assert fecha is None, "se fijó la fecha de cierre pese al rechazo"


# ── AC04 · los seis que no bloquean ───────────────────────────────────────────

@pytest.mark.parametrize("estado", NO_BLOQUEAN, ids=[e.value for e in NO_BLOQUEAN])
async def test_t_076_03_los_estados_no_gobernados_no_bloquean(
    client, auth_headers, lote_cerrable, motor, estado
):
    """`AC04` · una regla que bloquea de más es tan defectuosa como una que no bloquea.

    `sap_error` es el caso que más importa: solo se alcanza tras aprobar y consolidar, así
    que un fallo de integración no puede impedir cerrar un lote.
    """
    await _fijar_estado(motor, lote_cerrable["eventos"][2], estado)

    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, (
        f"«{estado.value}» no está entre los estados que R7 gobierna y no debe bloquear: "
        f"{r.status_code} {r.text}"
    )


# ── AC08 · aprobar desbloquea, sin esperas ────────────────────────────────────

async def test_t_076_04_aprobar_el_registro_desbloquea_el_cierre(
    client, auth_headers, lote_cerrable, motor
):
    """`AC08` · `R-68`. La guarda no deja el lote atrapado."""
    await _fijar_estado(motor, lote_cerrable["eventos"][2], EventStatus.REGISTERED)
    bloqueado = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert bloqueado.status_code == 400, bloqueado.text

    await _fijar_estado(motor, lote_cerrable["eventos"][2], EventStatus.APPROVED)

    # Lectura inmediata, sin esperas: la guarda debe ver el estado nuevo.
    liberado = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert liberado.status_code == 200, (
        f"tras aprobar, el mismo lote debe cerrarse: {liberado.text}"
    )


# ── AC07 · pertenencia ────────────────────────────────────────────────────────

async def test_t_076_05_un_registro_de_otro_lote_no_influye(
    client, auth_headers, seeded_ids, lote_cerrable, motor
):
    """`AC07` · solo cuentan los registros **de ese lote**.

    Un evento sin aprobar en otro lote de la misma empresa no puede impedir este cierre: si
    la consulta olvidara el `lot_id`, cualquier pendiente del sistema bloquearía todo.
    """
    otro = await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert otro.status_code == 201, otro.text
    pendiente = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": otro.json()["id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "feed_registration",
        "event_date": iso_days_ago(0), "feed_movements": [{"quantity_kg": 50.0}],
    })
    assert pendiente.status_code == 201, pendiente.text   # queda en `registered`

    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, (
        f"un pendiente de otro lote no debe bloquear este cierre: {r.text}"
    )


# ── AC09 · BR-05 sigue vigente ────────────────────────────────────────────────

async def test_t_076_06_br05_sigue_vigente(
    client, auth_headers, seeded_ids, motor
):
    """`AC09` · la guarda nueva no desplaza a la anterior."""
    r = await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert r.status_code == 201, r.text

    cierre = await _cerrar(client, auth_headers, r.json()["id"])
    assert cierre.status_code == 400, cierre.text
    assert cierre.json().get("rule") == "BR-05", (
        f"sin pesaje ni alimento el motivo sigue siendo BR-05: {cierre.json()}"
    )
