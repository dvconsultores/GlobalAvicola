"""Reverso interno: la solicitud es una contrapartida; la aprobación aplica la compensación.

`GA-REM-041` · `OD-19`. Tres ideas, en el orden en que importan:

    LA HISTORIA NO SE BORRA      el original queda íntegro y termina `REVERSED`; la contrapartida
                                 —mismo tipo, mismas cantidades, `reversals` vinculada— dice que fue
                                 neutralizado. Los saldos suman las dos: neto cero (`validators`).
    NADA ES EFECTIVO SIN APROBAR la contrapartida entra en la cola de revisión y la decide el
                                 motor existente (`OD-19 §6`); quien solicita no aprueba (`BR-14`
                                 sobre `registered_by_id`, que aquí es el solicitante).
    EXACTAMENTE UNA VEZ          el original se bloquea (`FOR UPDATE`) al solicitar y al aplicar;
                                 una contrapartida activa o efectiva impide otra (`OD-19 §5, §19`).
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import false as sa_false
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_accion, audit_state_transition
from ..audit.models import AuditAction, AuditModule
from ..operations.models import (BirdMovement, EventStatus, EventType, FeedMovement, HatcheryParams,
                                 InspectionDetail, OperationalEvent, Reversal)
from ..operations.validators import (BusinessRuleViolation, bloquear_saldo_del_lote,
                                     get_current_bird_balance, get_viable_chick_balance)
from . import schemas

# `GA-REM-041 §3.5` · `OD-19 §10, §17, §18`
ELEGIBLES_CON_SALDO_DE_AVES = {
    EventType.BIRD_RECEPTION, EventType.MORTALITY_RECORDING, EventType.CULL_RECORDING,
    EventType.BIRD_EXIT, EventType.CHICK_DISPATCH, EventType.BIRTH_REGISTRATION,
}
ELEGIBLES_SIN_SALDO = {
    EventType.FEED_REGISTRATION, EventType.WEIGHT_RECORDING, EventType.VACCINATION, EventType.MEDICATION,
    EventType.FARM_INSPECTION, EventType.TRANSPORT_INSPECTION, EventType.HATCHERY_INSPECTION,
    EventType.BIRD_TRANSFER, EventType.BIRD_DISTRIBUTION,
}
BLOQUEADOS_POR_R161 = {
    EventType.EGG_COLLECTION, EventType.EGG_CLASSIFICATION, EventType.EGG_RECEPTION_CLASSIFICATION,
    EventType.EGG_DISPATCH, EventType.EGG_RECEPTION_HATCHERY, EventType.INCUBATION_LOAD,
    EventType.OVOSCOPY, EventType.TRANSFER_TO_HATCHER,
}
#: Estados de una contrapartida que **bloquean** otra solicitud sobre el mismo original.
CONTRAPARTIDA_ACTIVA = (EventStatus.PENDING_REVIEW, EventStatus.IN_REVIEW, EventStatus.CORRECTED,
                        EventStatus.REGISTERED, EventStatus.RETURNED, EventStatus.REJECTED,
                        EventStatus.APPROVED, EventStatus.REVERSED)
ENTRADAS_DE_AVES = {EventType.BIRD_RECEPTION, EventType.BIRTH_REGISTRATION}
SALIDAS_DE_AVES = {EventType.MORTALITY_RECORDING, EventType.CULL_RECORDING, EventType.BIRD_EXIT, EventType.CHICK_DISPATCH}


def _plano(valor: Any) -> Any:
    if isinstance(valor, (int, float, str, bool)) or valor is None:
        return valor
    return getattr(valor, "value", str(valor))


def _instantanea(event: OperationalEvent, movimientos: dict[str, list[dict]]) -> dict:
    campos = {c.name: _plano(getattr(event, c.name)) for c in OperationalEvent.__table__.columns}
    campos["movimientos"] = movimientos
    return campos


async def es_contrapartida(db: AsyncSession, event_id: int) -> bool:
    """¿Este evento es la contrapartida de un reverso? (`AC-RV06`: no se edita ni corrige)."""
    return (await db.execute(
        select(func.count()).select_from(Reversal).where(Reversal.reversal_event_id == event_id)
    )).scalar() > 0


async def _bloquear_original(db: AsyncSession, event_id: int) -> OperationalEvent:
    """El original bajo `FOR UPDATE`, releído: es lo que serializa dos solicitudes o dos aprobaciones."""
    return (await db.execute(
        select(OperationalEvent).where(OperationalEvent.id == event_id)
        .with_for_update().execution_options(populate_existing=True)
    )).scalar_one()


class ReversalService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def solicitar(self, data: schemas.ReversalCreate) -> Reversal:
        from ..operations.service import OperationsService

        operaciones = OperationsService(self.db, self.current_user)
        # Empresa y unidad efectiva (`404` fuera de alcance) y habilitación (`403`), como toda
        # escritura productiva (`OD-19 §13-14`, `GA-REM-040-G/H`).
        original = await operaciones.get_event(data.event_id)
        await operaciones.exigir_unidad_operativa(event=original)
        original = await _bloquear_original(self.db, original.id)

        # Elegibilidad (`OD-19 §10-11, §18` · `AC-RV02…07`).
        if original.status == EventStatus.REVERSED:
            raise BusinessRuleViolation("El registro ya fue revertido", "BR-16")
        if original.status == EventStatus.CONSOLIDATED:
            raise BusinessRuleViolation(
                "Un registro consolidado no se reversa internamente (diferido, OD-19 §11)", "BR-16")
        if original.status != EventStatus.APPROVED:
            raise BusinessRuleViolation(
                f"Solo un registro aprobado y no enviado a SAP se reversa (estado actual: {original.status.value})", "BR-16")
        if original.event_type in BLOQUEADOS_POR_R161:
            raise BusinessRuleViolation(
                "El reverso de huevos e incubación queda bloqueado por R-161 (OD-19 §18)", "BR-16")
        if original.event_type not in ELEGIBLES_CON_SALDO_DE_AVES | ELEGIBLES_SIN_SALDO:
            raise BusinessRuleViolation(
                f"El tipo de evento {original.event_type.value!r} no es reversible", "BR-16")
        if await es_contrapartida(self.db, original.id):
            raise BusinessRuleViolation("Una contrapartida de reverso no se reversa", "BR-16")
        activa = (await self.db.execute(
            select(func.count()).select_from(Reversal)
            .join(OperationalEvent, OperationalEvent.id == Reversal.reversal_event_id)
            .where(Reversal.original_event_id == original.id,
                   OperationalEvent.status.in_(CONTRAPARTIDA_ACTIVA))
        )).scalar()
        if activa:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="El registro ya tiene una solicitud de reverso activa o efectiva")

        # La contrapartida: mismo tipo y mismas cantidades, derivadas del original (`OD-19 §4`).
        copia = {c.name: getattr(original, c.name) for c in OperationalEvent.__table__.columns
                 if c.name not in ("id", "status", "version", "idempotency_key", "registered_by_id",
                                   "reviewed_by_id", "approved_by_id", "event_date", "event_time",
                                   "observations", "classified_at", "created_at", "updated_at")}
        contrapartida = OperationalEvent(
            **copia, event_date=date.today(), status=EventStatus.PENDING_REVIEW, version=1,
            registered_by_id=self.current_user["id"],
            observations=f"Reverso de #{original.id}: {data.reason}",
        )
        self.db.add(contrapartida)
        await self.db.flush()
        movimientos: dict[str, list[dict]] = {}
        for modelo, clave in ((BirdMovement, "bird_movements"), (FeedMovement, "feed_movements"),
                              (InspectionDetail, "inspection_details"), (HatcheryParams, "hatchery_params")):
            filas = (await self.db.execute(select(modelo).where(modelo.event_id == original.id))).scalars().all()
            movimientos[clave] = []
            for fila in filas:
                datos = {c.name: getattr(fila, c.name) for c in modelo.__table__.columns if c.name not in ("id", "event_id")}
                movimientos[clave].append({k: _plano(v) for k, v in datos.items()})
                self.db.add(modelo(event_id=contrapartida.id, **datos))
        aves = sum(m.get("quantity") or 0 for m in movimientos["bird_movements"])
        reverso = Reversal(
            original_event_id=original.id, reversal_event_id=contrapartida.id, company_id=original.company_id,
            reason=data.reason, reversed_by_id=self.current_user["id"],
            original_data_snapshot=_instantanea(original, movimientos),
            reversal_data={"event_type": original.event_type.value, "bird_quantity": aves,
                           "feed_kg": sum(m.get("quantity_kg") or 0 for m in movimientos["feed_movements"])},
        )
        self.db.add(reverso)
        await self.db.flush()
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CREATED, modulo=AuditModule.OPERATIONS,
            entity_type="reversal", entity_id=str(reverso.id), company_id=original.company_id,
            lot_id=original.lot_id, comments=data.reason,
            new_values={"original_event_id": original.id, "reversal_event_id": contrapartida.id},
        )
        await self.db.refresh(reverso)
        return reverso

    async def listar(self, limit: int = 50, offset: int = 0) -> tuple[list[Reversal], int]:
        base = select(Reversal)
        base = base.where(sa_false()) if self.company_id is None else base.where(Reversal.company_id == self.company_id)
        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        filas = (await self.db.execute(base.order_by(Reversal.created_at.desc()).offset(offset).limit(limit))).scalars().all()
        return list(filas), int(total)

    async def por_evento(self, event_id: int) -> list[Reversal]:
        from ..operations.service import OperationsService

        await OperationsService(self.db, self.current_user).get_event(event_id)  # `404` fuera de alcance
        return list((await self.db.execute(
            select(Reversal).where(Reversal.original_event_id == event_id).order_by(Reversal.created_at.desc())
        )).scalars().all())


async def efectuar_reverso_si_procede(db: AsyncSession, contrapartida: OperationalEvent, current_user: dict) -> bool:
    """La aprobación de una contrapartida aplica el reverso (`OD-19 §6, §17, §20` · `AC-EF*`).

    Devuelve `False` si el evento aprobado no es una contrapartida (aprobación ordinaria). Si lo es:
    bloquea el original, comprueba que sigue `APPROVED`, valida que los saldos resultantes no
    quedan negativos (`BR-01`/`BR-04`, `R-130`) y marca **ambos** `REVERSED` en la misma
    transacción. Una excepción deja todo como estaba (`RutaTransaccional` hace `rollback`).
    """
    reverso = (await db.execute(
        select(Reversal).where(Reversal.reversal_event_id == contrapartida.id)
    )).scalar_one_or_none()
    if reverso is None:
        return False
    original = await _bloquear_original(db, reverso.original_event_id)
    if original.status != EventStatus.APPROVED:
        raise BusinessRuleViolation(
            f"El original ya no es reversible (estado: {original.status.value})", "BR-16")
    if original.lot_id is not None and original.event_type in ELEGIBLES_CON_SALDO_DE_AVES:
        await bloquear_saldo_del_lote(db, original.lot_id)
        aves = (await db.execute(
            select(func.coalesce(func.sum(BirdMovement.quantity), 0)).where(BirdMovement.event_id == original.id)
        )).scalar() or 0
        signo = 1 if original.event_type in ENTRADAS_DE_AVES else -1
        saldo = await get_current_bird_balance(db, original.lot_id)
        if saldo - signo * aves < 0:
            raise BusinessRuleViolation(
                f"El reverso dejaría el saldo de aves en {saldo - signo * aves} (actual {saldo})", "BR-01")
        if original.event_type in (EventType.BIRTH_REGISTRATION, EventType.CHICK_DISPATCH,
                                   EventType.MORTALITY_RECORDING, EventType.CULL_RECORDING):
            viable = await get_viable_chick_balance(db, original.lot_id)
            signo_viable = 1 if original.event_type == EventType.BIRTH_REGISTRATION else -1
            if viable - signo_viable * aves < 0:
                raise BusinessRuleViolation(
                    f"El reverso dejaría los pollitos viables en {viable - signo_viable * aves}", "BR-04")
    original.status = EventStatus.REVERSED
    contrapartida.status = EventStatus.REVERSED
    await db.flush()
    await audit_state_transition(db, original, current_user, "approved", "reversed", comments=reverso.reason)
    return True
