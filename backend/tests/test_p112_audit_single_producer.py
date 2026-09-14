"""P1-12 (REAPERTURA) · RED — un productor por acción y cobertura completa.

Diseño: `audit/ga-claude-final-audit/specs/P1-12-REOPEN/P1-12-REOPEN_RED_E2E_UAT_DESIGN.md §1.2`.

El `lifespan` de uvicorn registra el listener `after_flush`; el transporte ASGI del
arnés de tests no, y por eso la duplicación listener+helpers quedaba oculta
(`FINDING §1.2`). Estos tests registran el listener durante su ejecución para
reproducir el runtime real: con él, HEAD escribe 2-3 filas por acción y 0 filas en
las acciones sin productor.

Fallos esperados en HEAD (rojos exactos):
  01 alta          ⇒ `created`=2 (listener + helper `audit_event_created`).
  02 aprobación    ⇒ `review_started`=3; `approved`=2; `corrected` espuria=1.
  03 cierre de lote ⇒ 0 filas de lote (sin productor).
  04 usuarios      ⇒ 0 filas en alta/edición/baja.
  05 evidencias/curvas ⇒ 0 filas en subir/borrar y crear/activar.
  06 batch         ⇒ 0 transiciones `pending_review` (update masivo invisible).

Fechas relativas al reloj (`R-28`); ids de siembra por `seeded_ids` (nunca literales).
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
from app.audit.models import AuditAction, AuditLog, AuditModule
from tests.time_reference import iso_days_ago

PREFIJO = "P112-"

#: Un PNG mínimo válido: el contrato de evidencias exige imagen real.
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16

#: Tabla de curva de peso: dos edades bastan al contrato del maestro.
TABLA = [
    {"age_days": 10, "min_weight": 90.0, "target_weight": 100.0, "max_weight": 110.0},
    {"age_days": 20, "min_weight": 180.0, "target_weight": 200.0, "max_weight": 220.0},
]

ALIMENTO_KG = 42.5


@pytest.fixture(autouse=True)
def _listener_como_runtime():
    """Registra el listener de auditoría durante el test (equivalente al `lifespan`).

    Sin él la duplicación no existe y el RED sería ciego: los tests de este módulo
    comprueban el comportamiento **en runtime**.
    """
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    from app.audit import listeners as audit_listeners

    presente = event.contains(Session, "after_flush", audit_listeners.audit_after_flush)
    if not presente:
        event.listen(Session, "after_flush", audit_listeners.audit_after_flush)
    yield
    event.remove(Session, "after_flush", audit_listeners.audit_after_flush)


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e

    from app.corrections.models import CorrectionLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.masters.models import (
        GeneticLine,
        GeneticWeightCurve,
        GeneticWeightCurvePoint,
        Lot,
    )
    from app.operations.models import (
        BirdMovement,
        EggMovement,
        Evidence,
        FeedMovement,
        InspectionDetail,
        OperationalAlert,
        OperationalEvent,
    )
    from app.review.models import ApprovalAction, ReviewBatch

    async with e.begin() as c:
        lot_ids = (
            await c.execute(select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))
        ).scalars().all()
        event_ids: list[int] = []
        if lot_ids:
            event_ids = (
                await c.execute(
                    select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(lot_ids))
                )
            ).scalars().all()
        if event_ids:
            for tabla in (BirdMovement, EggMovement, FeedMovement, InspectionDetail,
                          Evidence, OperationalAlert, ApprovalAction, CorrectionLog):
                await c.execute(delete(tabla).where(tabla.event_id.in_(event_ids)))
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_id.in_([str(i) for i in event_ids])))
        if lot_ids:
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lot_ids)))
            await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(event_ids)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(lot_ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(lot_ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(lot_ids)))

        await c.execute(delete(ReviewBatch).where(ReviewBatch.batch_name.like(f"{PREFIJO}%")))

        lineas = (
            await c.execute(select(GeneticLine.id).where(GeneticLine.name.like(f"{PREFIJO}%")))
        ).scalars().all()
        if lineas:
            curvas = (
                await c.execute(
                    select(GeneticWeightCurve.id).where(
                        GeneticWeightCurve.genetic_line_id.in_(lineas))
                )
            ).scalars().all()
            if curvas:
                await c.execute(delete(GeneticWeightCurvePoint).where(
                    GeneticWeightCurvePoint.curve_id.in_(curvas)))
                await c.execute(delete(GeneticWeightCurve).where(
                    GeneticWeightCurve.id.in_(curvas)))
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_id.in_([str(i) for i in [*lineas, *curvas]])))
            await c.execute(delete(GeneticLine).where(GeneticLine.id.in_(lineas)))
    await e.dispose()


async def _registros(motor, accion: AuditAction, **filtros):
    """Filas de auditoría de una acción, leídas de la base en sesión limpia."""
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        q = select(AuditLog).where(AuditLog.action == accion)
        for campo, valor in filtros.items():
            q = q.where(getattr(AuditLog, campo) == valor)
        return (await s.execute(q)).scalars().all()


async def _lote(client, cabecera, ids) -> int:
    r = await client.post("/api/v1/lots", headers=cabecera, json={
        "company_id": ids["company_id"],
        "farm_id": ids["farm_id"],
        "house_id": ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder",
        "sex": "mixed",
        "start_date": iso_days_ago(90),
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _evento(client, cabecera, ids, lot_id, tipo, **extra) -> int:
    r = await client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": lot_id,
        "farm_id": ids["farm_id"],
        "house_id": ids["house_id"],
        "event_type": tipo,
        "event_date": iso_days_ago(7),
        **extra,
    })
    assert r.status_code == 201, f"{tipo}: {r.text}"
    return r.json()["id"]


async def _requisitos_br05(client, cabecera, ids, lot_id) -> None:
    """Pesaje y alimento: lo mínimo que `BR-05` exige para poder cerrar."""
    await _evento(client, cabecera, ids, lot_id, "weight_recording",
                  bird_movements=[{"sex": "mixed", "quantity": 10, "avg_weight": 2000}])
    await _evento(client, cabecera, ids, lot_id, "feed_registration",
                  feed_movements=[{"quantity_kg": ALIMENTO_KG}])


async def _aprobar_todo(motor, lot_id) -> None:
    """Deja los eventos del lote en `approved` (R7: sin registros sin aprobar no cierra)."""
    from app.operations.models import EventStatus, OperationalEvent

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        eventos = (await s.execute(select(OperationalEvent).where(
            OperationalEvent.lot_id == lot_id))).scalars().all()
        for e in eventos:
            e.status = EventStatus.APPROVED
        await s.commit()


# ── 01 · alta de evento: exactamente una fila `created` ───────────────────────

async def test_p112_01_alta_una_fila(client, auth_headers, seeded_ids, motor):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id, "weight_recording",
                             bird_movements=[{"sex": "mixed", "quantity": 10, "avg_weight": 2000}])

    filas = await _registros(motor, AuditAction.CREATED,
                             module=AuditModule.OPERATIONS,
                             entity_type="operational_event", entity_id=str(event_id))
    assert len(filas) == 1, (
        f"el alta escribió {len(filas)} filas `created` (runtime con listener: "
        "listener + helper `audit_event_created`)"
    )


# ── 02 · flujo de aprobación: una fila por acción y cero espurias ─────────────

async def test_p112_02_aprobacion_una_fila(client, auth_headers, seeded_ids, motor):
    from app.auth.security import create_access_token

    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id, "weight_recording",
                             bird_movements=[{"sex": "mixed", "quantity": 10, "avg_weight": 2000}])

    envio = await client.post(f"/api/v1/operations/{event_id}/submit", headers=auth_headers)
    assert envio.status_code == 200, envio.text

    # `BR-14` (segregación): quien registra no aprueba; la revisión la hace el aprobador.
    revisor = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_approver_id"])})}
    inicio = await client.post(f"/api/v1/review/start/{event_id}", headers=revisor)
    assert inicio.status_code == 200, inicio.text
    fin = await client.post("/api/v1/review/complete", headers=revisor,
                            json={"event_id": event_id, "observations": "sin hallazgos"})
    assert fin.status_code == 200, fin.text
    assert fin.json()["status"] == "approved", "la empresa de siembra tiene un nivel de aprobación"

    iniciadas = await _registros(motor, AuditAction.REVIEW_STARTED,
                                 entity_type="operational_event", entity_id=str(event_id))
    assert len(iniciadas) == 1, f"`review_started` escribió {len(iniciadas)} filas"

    aprobadas = await _registros(motor, AuditAction.APPROVED,
                                 entity_type="operational_event", entity_id=str(event_id))
    assert len(aprobadas) == 1, f"`approved` escribió {len(aprobadas)} filas"

    espurias = await _registros(motor, AuditAction.CORRECTED,
                                entity_type="operational_event", entity_id=str(event_id))
    assert len(espurias) == 0, (
        "`complete_review` escribió una fila `corrected` al aprobar "
        "(`review/service.py` usa `ActionType.CORRECTED` en ambas ramas)"
    )


# ── 03 · cierre de lote: una fila con el resumen ──────────────────────────────

async def test_p112_03_cierre_auditado(client, auth_headers, seeded_ids, motor):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    await _requisitos_br05(client, auth_headers, seeded_ids, lot_id)
    await _aprobar_todo(motor, lot_id)

    cierre = await client.post(f"/api/v1/lots/{lot_id}/close", headers=auth_headers)
    assert cierre.status_code == 200, cierre.text

    filas = await _registros(motor, AuditAction.UPDATED,
                             module=AuditModule.LOTS, entity_id=str(lot_id))
    assert len(filas) == 1, f"el cierre escribió {len(filas)} filas (sin productor: 0)"
    assert filas[0].new_values, "la fila del cierre no registró el resumen del lote"


# ── 04 · usuarios: alta, edición y baja con rastro ────────────────────────────

async def test_p112_04_usuarios_auditados(client, auth_headers, seeded_ids, motor):
    sufijo = uuid.uuid4().hex[:8]
    alta = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": f"{PREFIJO}{sufijo}",
        "first_name": "Uno", "last_name": "Auditado",
        "email": f"{PREFIJO}{sufijo}@example.com".lower(),
        "password": uuid.uuid4().hex,
        "role_id": seeded_ids["role_operator_id"],
        "company_id": seeded_ids["company_id"],
        "view_type": "web",
    })
    assert alta.status_code == 201, alta.text
    user_id = alta.json()["id"]

    creadas = await _registros(motor, AuditAction.CREATED,
                               module=AuditModule.USERS, entity_id=str(user_id))
    assert len(creadas) == 1, "el alta de usuario no dejó una fila de auditoría"

    edicion = await client.put(f"/api/v1/users/{user_id}", headers=auth_headers,
                               json={"first_name": "Editado"})
    assert edicion.status_code == 200, edicion.text
    ediciones = await _registros(motor, AuditAction.UPDATED,
                                 module=AuditModule.USERS, entity_id=str(user_id))
    assert len(ediciones) == 1, "la edición de usuario no dejó una fila de auditoría"

    baja = await client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert baja.status_code == 204, baja.text
    bajas = await _registros(motor, AuditAction.DELETED,
                             module=AuditModule.USERS, entity_id=str(user_id))
    assert len(bajas) == 1, "la baja de usuario no dejó una fila de auditoría"


# ── 05 · evidencias y curvas: subir/borrar; crear/activar ─────────────────────

async def test_p112_05_evidencias_curvas(client, auth_headers, seeded_ids, motor):
    # Evidencias: subir y borrar dejan fila cada uno.
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id, "weight_recording",
                             bird_movements=[{"sex": "mixed", "quantity": 10, "avg_weight": 2000}])

    subida = await client.post(
        f"/api/v1/operations/{event_id}/evidences", headers=auth_headers,
        files={"file": (f"{PREFIJO}{uuid.uuid4().hex[:6]}.png", PNG, "image/png")})
    assert subida.status_code == 201, subida.text
    ev_id = subida.json()["id"]

    alta_ev = await _registros(motor, AuditAction.CREATED,
                               module=AuditModule.OPERATIONS,
                               entity_type="evidence", entity_id=str(ev_id))
    assert len(alta_ev) == 1, "subir una evidencia no dejó fila de auditoría"

    borrado = await client.delete(
        f"/api/v1/operations/{event_id}/evidences/{ev_id}", headers=auth_headers)
    assert borrado.status_code == 204, borrado.text
    baja_ev = await _registros(motor, AuditAction.DELETED,
                               module=AuditModule.OPERATIONS,
                               entity_type="evidence", entity_id=str(ev_id))
    assert len(baja_ev) == 1, "borrar una evidencia no dejó fila de auditoría"

    # Curvas: crear y activar dejan fila cada uno.
    linea = await client.post("/api/v1/masters/genetic-lines", headers=auth_headers,
                              json={"company_id": seeded_ids["company_id"],
                                    "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}"})
    assert linea.status_code in (200, 201), linea.text
    linea_id = linea.json()["id"]

    curva = await client.post("/api/v1/masters/weight-curves", headers=auth_headers,
                              json={"genetic_line_id": linea_id, "version_label": "v1",
                                    "is_active": False, "points": TABLA})
    assert curva.status_code in (200, 201), curva.text
    curva_id = curva.json()["id"]

    alta_curva = await _registros(motor, AuditAction.CREATED,
                                  module=AuditModule.MASTERS,
                                  entity_type="weight_curve", entity_id=str(curva_id))
    assert len(alta_curva) == 1, "crear una curva no dejó fila de auditoría"

    activacion = await client.put(f"/api/v1/masters/weight-curves/{curva_id}/activate",
                                  headers=auth_headers)
    assert activacion.status_code == 200, activacion.text
    act_curva = await _registros(motor, AuditAction.UPDATED,
                                 module=AuditModule.MASTERS,
                                 entity_type="weight_curve", entity_id=str(curva_id))
    assert len(act_curva) == 1, "activar una curva no dejó fila de auditoría"


# ── 06 · batch de revisión: la transición a `pending_review` deja fila ────────

async def test_p112_06_batch_transicion(client, auth_headers, seeded_ids, motor):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id, "weight_recording",
                             bird_movements=[{"sex": "mixed", "quantity": 10, "avg_weight": 2000}])

    batch = await client.post("/api/v1/review/batches", headers=auth_headers, json={
        "batch_name": f"{PREFIJO}batch-{uuid.uuid4().hex[:6]}",
        "event_ids": [event_id],
        "notes": "P1-12",
    })
    assert batch.status_code == 201, batch.text

    filas = await _registros(motor, AuditAction.UPDATED,
                             entity_type="operational_event", entity_id=str(event_id))
    transiciones = [f for f in filas if f.new_state == "pending_review"]
    assert len(transiciones) == 1, (
        f"el batch escribió {len(transiciones)} transiciones `pending_review` "
        "(el update masivo no pasa por el listener: sin productor son 0)"
    )
