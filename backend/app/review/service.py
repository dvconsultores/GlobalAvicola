"""Review & Approval service — business logic for review workflow."""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_accion, audit_approval_action, audit_state_transition
from ..audit.models import AuditAction, AuditModule
from ..operations.models import EventStatus, OperationalEvent
from . import models, schemas


class SegregacionMixin:
    """`BR-14` en un unico sitio, para todo el que apruebe.

    La auditoria encontro tres vias distintas de saltarse la regla: `complete_review` no
    la comprobaba, `approve` la aplicaba de forma incondicional ignorando la bandera de
    configuracion, y `PUT /operations/{id}` permitia fijar el estado sin pasar por
    ninguna de las dos (`R-32`, corregido en el Stage 1).

    Una regla de control interno aplicada en un sitio y ausente en otro no es un control:
    es una casualidad. De ahi que viva aqui y no incrustada en cada servicio.
    """

    async def _exigir_segregacion(self, event, accion: str = "aprobar") -> None:
        """Aplica `BR-14` en un unico sitio, consultando la configuracion del paso.

        Regla vigente `RR-03` (Wave 1.5): `BR-14` es **configurable por paso de
        aprobacion** mediante `ApprovalStep.require_segregation`, con valor por defecto
        `True`. La bandera existia en el modelo desde el principio, se sembraba con cada
        paso y **nunca se leia**: la comprobacion estaba incrustada en `approve()` y
        `complete_review()` la eludia por completo.

        Centralizarla importa porque la auditoria encontro tres vias distintas de
        saltarse la regla. Una regla de control interno aplicada en un sitio y ausente en
        otros no es un control: es una casualidad.
        """
        from ..operations.validators import BusinessRuleViolation, validate_segregation

        if not await self._segregacion_configurada():
            return
        try:
            validate_segregation(event.registered_by_id, self.current_user["id"], accion)
        except BusinessRuleViolation as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
        # `GA-REM-007-A` · `R-143` · `docs/12 R2` + `OD-17.b`: tampoco aprueba quien **corrigió**
        # el registro (`correction_logs.corrected_by_id`) ni quien lo **rechazó**
        # (`approval_actions.REJECTED`). Devolverlo no cuenta: observar no es rechazar
        # (`OD-17.a`), y el mismo supervisor revisa el reenvío (`docs/12 §2`). Mismo
        # identificador `BR-14` y mismo punto de control (`GA-REM-007 AC05`, `AC07`).
        from ..corrections.models import CorrectionLog

        implicados = set((await self.db.execute(
            select(CorrectionLog.corrected_by_id).where(CorrectionLog.event_id == event.id)
        )).scalars().all())
        implicados |= set((await self.db.execute(
            select(models.ApprovalAction.user_id).where(
                models.ApprovalAction.event_id == event.id,
                models.ApprovalAction.action_type == models.ActionType.REJECTED)
        )).scalars().all())
        if self.current_user["id"] in implicados:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quien corrigió o rechazó un registro no puede {accion}lo (segregación de funciones, BR-14)",
            )

    async def _segregacion_configurada(self) -> bool:
        """`True` salvo que la empresa la haya desactivado explicitamente.

        Sin pasos configurados se exige segregacion: el valor por defecto de la columna es
        `True` y una empresa que no ha configurado nada no puede haber renunciado a un
        control interno sin saberlo.
        """
        resultado = await self.db.execute(
            select(models.ApprovalStep.require_segregation)
            .where(
                models.ApprovalStep.company_id == self.company_id,
                models.ApprovalStep.can_approve.is_(True),
            )
            .order_by(models.ApprovalStep.step_order.desc())
        )
        configurado = resultado.scalars().first()
        return True if configurado is None else bool(configurado)



async def _bloquear_evento(db: AsyncSession, event: OperationalEvent) -> None:
    """`GA-REM-007` enmienda B · `R-166`: serializa las decisiones de revisión sobre el mismo evento.

    La fila autoritativa de la decisión es `operational_events` —`status` **es** la decisión efectiva; los
    `approval_actions` son historia—. Sin bloqueo, dos peticiones concurrentes leían `CORRECTED`, ambas
    superaban la comprobación de estado y ambas escribían: dos decisiones efectivas, dos auditorías de éxito
    y —el rechazo— una notificación de un evento que quedaba aprobado.

    `SELECT … FOR UPDATE` sobre esa fila y **relectura** del estado: el segundo espera al `commit` del primero
    y ve el estado terminal, de modo que su transición ya no es legal (`GA-REM-006-A §A.2`). Misma primitiva que
    `reversals._bloquear_original` y que `bloquear_saldo_del_lote` (`R-130`), sobre otra fila y otro invariante:
    revisar **no** serializa el saldo del lote (`R-166` ≠ `R-161`).

    Va **después** de la cadena de inquilino/unidad: bloquear antes revelaría la existencia de un evento ajeno.
    """
    await db.execute(
        select(OperationalEvent.id).where(OperationalEvent.id == event.id).with_for_update()
    )
    await db.refresh(event, attribute_names=["status"])


async def _exigir_habilitacion(db, current_user, event) -> None:
    """`GA-REM-041 §1.2` · `R-165` · `OD-19 §13`: revisar, devolver, completar, aprobar o rechazar
    es operar dato productivo. El actor de empresa ya queda fuera por `unidades_efectivas`
    (`404`); a la autoridad global, exenta de concesión, se le exige la **habilitación** de la
    unidad como en `operations`, `lots` y `corrections` (`403`). Misma guarda compartida."""
    from ..operations.service import OperationsService

    await OperationsService(db, current_user).exigir_unidad_operativa(event=event)


class ReviewService(SegregacionMixin):
    """Handles review workflow: batch creation, start/return/complete review."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def _ambito_de_unidad(self):
        """Predicado de cadena productiva para las colas de revisión. `GA-REM-040` fase 6.

        El flujo 6 —revisión y aprobación— quedó aplazado en la fase 5 porque su cadena se
        deriva del evento, y el evento podía no tenerla. Con la clasificación pendiente en
        pie, ya se puede: lo derivable se deriva, lo clasificado se lee, y lo que no tiene
        ninguna de las dos **no entra en la cola** — su superficie es la bandeja.

        Una cola de revisión que muestre eventos de cadenas ajenas revela su volumen y su
        ritmo aunque no se abra ninguno.
        """
        from ..business_units.classification import predicado_de_evento
        from ..business_units.service import unidades_de_alcance_productivo

        # `GA-FE-02-D` · `OD-16`: sin atajo para la autoridad global — su alcance son las
        # unidades habilitadas de la empresa (la concesión no se le exige; la habilitación
        # jamás se salta).
        unidades = await unidades_de_alcance_productivo(
            self.db, current_user=self.current_user, company_id=self.company_id)
        return [predicado_de_evento(unidades, self.company_id)]

    # ============================================================
    # Query pending events
    # ============================================================

    async def get_pending_review_events(
        self,
        farm_id: Optional[int] = None,
        lot_id: Optional[int] = None,
        event_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OperationalEvent], int]:
        """Get events pending review (status=registered or pending_review)."""
        _ambito = await self._ambito_de_unidad()
        base = select(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
            *_ambito,
            OperationalEvent.status.in_([EventStatus.REGISTERED, EventStatus.PENDING_REVIEW]),
        )
        count_q = select(func_count()).select_from(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
            *_ambito,
            OperationalEvent.status.in_([EventStatus.REGISTERED, EventStatus.PENDING_REVIEW]),
        )

        if farm_id:
            base = base.where(OperationalEvent.farm_id == farm_id)
            count_q = count_q.where(OperationalEvent.farm_id == farm_id)
        if lot_id:
            base = base.where(OperationalEvent.lot_id == lot_id)
            count_q = count_q.where(OperationalEvent.lot_id == lot_id)
        if event_type:
            base = base.where(OperationalEvent.event_type == event_type)
            count_q = count_q.where(OperationalEvent.event_type == event_type)
        if date_from:
            base = base.where(OperationalEvent.event_date >= date_from)
            count_q = count_q.where(OperationalEvent.event_date >= date_from)
        if date_to:
            base = base.where(OperationalEvent.event_date <= date_to)
            count_q = count_q.where(OperationalEvent.event_date <= date_to)

        base = base.order_by(OperationalEvent.event_date.desc()).offset(offset).limit(limit)

        result = await self.db.execute(base)
        events = list(result.scalars().all())

        count_result = await self.db.execute(count_q)
        total = count_result.scalar() or 0

        return events, total

    # ============================================================
    # Review batches
    # ============================================================

    async def create_review_batch(self, data: schemas.ReviewBatchCreate) -> models.ReviewBatch:
        """Create a review batch from a list of event IDs."""
        # Validate all events exist, belong to company, and are in reviewable status
        for event_id in data.event_ids:
            event = await self._get_event(event_id)
            if event.status not in (EventStatus.REGISTERED, EventStatus.PENDING_REVIEW):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Evento #{event_id} no está en estado revisable (actual: {event.status.value})",
                )

        batch = models.ReviewBatch(
            company_id=self.company_id,
            batch_name=data.batch_name,
            total_events=len(data.event_ids),
            created_by_id=self.current_user["id"],
            notes=data.notes,
        )
        self.db.add(batch)
        await self.db.flush()

        # Mark all events as pending_review and create actions
        for event_id in data.event_ids:
            await self.db.execute(
                update(OperationalEvent)
                .where(OperationalEvent.id == event_id)
                .values(status=EventStatus.PENDING_REVIEW, reviewed_by_id=self.current_user["id"])
            )
            self.db.add(models.ApprovalAction(
                event_id=event_id,
                batch_id=batch.id,
                user_id=self.current_user["id"],
                action_type=models.ActionType.STARTED_REVIEW,
            ))

        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def get_batches(self, limit: int = 20, offset: int = 0) -> tuple[list[models.ReviewBatch], int]:
        """List review batches for current company."""
        q = select(models.ReviewBatch).where(
            models.ReviewBatch.company_id == self.company_id
        ).order_by(models.ReviewBatch.created_at.desc()).offset(offset).limit(limit)
        cq = select(func_count()).select_from(models.ReviewBatch).where(
            models.ReviewBatch.company_id == self.company_id
        )
        result = await self.db.execute(q)
        batches = list(result.scalars().all())
        count_r = await self.db.execute(cq)
        total = count_r.scalar() or 0
        return batches, total

    # ============================================================
    # Review actions
    # ============================================================

    async def start_review(self, event_id: int) -> OperationalEvent:
        """Start reviewing a single event."""
        event = await self._get_event(event_id)
        if event.status != EventStatus.PENDING_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El evento debe estar en 'pending_review' (actual: {event.status.value})",
            )

        event.status = EventStatus.IN_REVIEW
        event.reviewed_by_id = self.current_user["id"]
        await self.db.flush()

        self.db.add(models.ApprovalAction(
            event_id=event_id,
            user_id=self.current_user["id"],
            action_type=models.ActionType.STARTED_REVIEW,
        ))
        await self.db.flush()
        await self.db.refresh(event)

        # Audit
        await audit_state_transition(self.db, event, self.current_user,
                                     "pending_review", "in_review",
                                     comments="Revisión iniciada por supervisor")

        return event

    async def return_to_operator(self, event_id: int, observations: str) -> OperationalEvent:
        """Return event to operator with observations."""
        event = await self._get_event(event_id)
        if event.status != EventStatus.IN_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El evento debe estar en 'in_review' (actual: {event.status.value})",
            )

        event.status = EventStatus.RETURNED
        event.observations = observations
        await self.db.flush()

        self.db.add(models.ApprovalAction(
            event_id=event_id,
            user_id=self.current_user["id"],
            action_type=models.ActionType.RETURNED,
            observations=observations,
        ))
        await self.db.flush()
        await self.db.refresh(event)

        # Audit
        await audit_state_transition(self.db, event, self.current_user,
                                     "in_review", "returned",
                                     comments=observations)

        return event

    async def complete_review(self, event_id: int, observations: Optional[str] = None) -> OperationalEvent:
        """Complete review. If single-level approval → auto-approve. Else → move to approval step."""
        event = await self._get_event(event_id)
        if event.status != EventStatus.IN_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El evento debe estar en 'in_review' (actual: {event.status.value})",
            )

        # Check company approval configuration
        approval_levels = await self._get_company_approval_levels()
        old_status = "in_review"

        if approval_levels <= 1:
            # Nivel unico: completar la revision equivale a aprobar. Y si equivale a
            # aprobar, `BR-14` rige igual: esta ruta fijaba `APPROVED` y `approved_by_id`
            # **sin comprobar la segregacion** (`R-23`), de modo que bastaba configurar un
            # solo nivel para que quien registraba aprobara lo suyo.
            await self._exigir_segregacion(event, "aprobar")
            event.status = EventStatus.APPROVED
            event.approved_by_id = self.current_user["id"]
            new_status = "approved"
            await self.db.flush()
            from ..reversals.service import efectuar_reverso_si_procede  # `GA-REM-041`

            if await efectuar_reverso_si_procede(self.db, event, self.current_user):
                new_status = "reversed"
            # `R-153` · `OD-25 (B)`: el nivel único de `complete_review` también **es** aprobar;
            # la creación del lote va aquí, tras el reverso, en la misma transacción.
            from ..lots.service import crear_lote_de_importacion_si_procede

            await crear_lote_de_importacion_si_procede(self.db, event, self.current_user)
        else:
            # Multi-level: mark as corrected (awaiting approval step)
            event.status = EventStatus.CORRECTED
            new_status = "corrected"

        event.observations = observations or event.observations
        await self.db.flush()

        self.db.add(models.ApprovalAction(
            event_id=event_id,
            user_id=self.current_user["id"],
            action_type=models.ActionType.CORRECTED,
            observations=observations,
        ))
        await self.db.flush()
        await self.db.refresh(event)

        # Audit
        await audit_state_transition(self.db, event, self.current_user,
                                     old_status, new_status,
                                     comments=observations)

        # `GA-REM-032 AC05`. `REVIEW_COMPLETED` estaba declarada y no la escribía nadie, de
        # modo que el cierre de la revisión era el único paso del ciclo sin rastro propio.
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.REVIEW_COMPLETED,
            modulo=AuditModule.REVIEW, entity_type="operational_event",
            entity_id=event.id, lot_id=event.lot_id, comments=observations,
        )
        return event

    # ============================================================
    # Helpers
    # ============================================================

    async def _get_event(self, event_id: int) -> OperationalEvent:
        result = await self.db.execute(
            select(OperationalEvent).where(
                OperationalEvent.id == event_id,
                OperationalEvent.company_id == self.company_id,
                *(await self._ambito_de_unidad()),
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
        await _exigir_habilitacion(self.db, self.current_user, event)  # `R-165` · `OD-19 §13`
        # `GA-REM-007-B` · `R-166`: todos los escritores de decisión convergen en la misma primitiva —
        # `start_review`, `return_to_operator` y `complete_review` transitan la misma fila que `approve`/`reject`.
        await _bloquear_evento(self.db, event)
        return event

    async def _get_company_approval_levels(self) -> int:
        from ..masters.models import Company
        result = await self.db.execute(
            select(Company.approval_levels).where(Company.id == self.company_id)
        )
        levels = result.scalar()
        return levels or 1


def func_count():
    from sqlalchemy import func
    return func.count()


class ApprovalService(SegregacionMixin):
    """Handles approval workflow: approve, reject, batch operations."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def _ambito_de_unidad(self):
        """Predicado de cadena productiva para las colas de revisión. `GA-REM-040` fase 6.

        El flujo 6 —revisión y aprobación— quedó aplazado en la fase 5 porque su cadena se
        deriva del evento, y el evento podía no tenerla. Con la clasificación pendiente en
        pie, ya se puede: lo derivable se deriva, lo clasificado se lee, y lo que no tiene
        ninguna de las dos **no entra en la cola** — su superficie es la bandeja.

        Una cola de revisión que muestre eventos de cadenas ajenas revela su volumen y su
        ritmo aunque no se abra ninguno.
        """
        from ..business_units.classification import predicado_de_evento
        from ..business_units.service import unidades_de_alcance_productivo

        # `GA-FE-02-D` · `OD-16`: sin atajo para la autoridad global — su alcance son las
        # unidades habilitadas de la empresa (la concesión no se le exige; la habilitación
        # jamás se salta).
        unidades = await unidades_de_alcance_productivo(
            self.db, current_user=self.current_user, company_id=self.company_id)
        return [predicado_de_evento(unidades, self.company_id)]

    # ============================================================
    # Pending approvals
    # ============================================================

    async def get_pending_approvals(
        self,
        farm_id: Optional[int] = None,
        lot_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OperationalEvent], int]:
        """Get events pending approval (status=corrected)."""
        _ambito = await self._ambito_de_unidad()
        base = select(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
            *_ambito,
            OperationalEvent.status == EventStatus.CORRECTED,
        )
        cq = select(func_count()).select_from(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
            *_ambito,
            OperationalEvent.status == EventStatus.CORRECTED,
        )

        if farm_id:
            base = base.where(OperationalEvent.farm_id == farm_id)
            cq = cq.where(OperationalEvent.farm_id == farm_id)
        if lot_id:
            base = base.where(OperationalEvent.lot_id == lot_id)
            cq = cq.where(OperationalEvent.lot_id == lot_id)

        base = base.order_by(OperationalEvent.event_date.desc()).offset(offset).limit(limit)

        result = await self.db.execute(base)
        events = list(result.scalars().all())
        count_r = await self.db.execute(cq)
        total = count_r.scalar() or 0
        return events, total

    # ============================================================
    # Approval actions
    # ============================================================

    async def approve(self, event_id: int, observations: Optional[str] = None) -> OperationalEvent:
        """Approve a single event."""
        event = await self._get_event_for_approval(event_id)

        # BR-14 (RR-03): segregacion de funciones, configurable por paso.
        await self._exigir_segregacion(event, "aprobar")

        old_status = event.status.value if hasattr(event.status, "value") else str(event.status)
        event.status = EventStatus.APPROVED
        event.approved_by_id = self.current_user["id"]
        if observations:
            event.observations = observations
        await self.db.flush()
        # `GA-REM-041` · `OD-19 §6, §20`: si lo aprobado es la contrapartida de un reverso, la
        # aprobación **aplica** la compensación en esta misma transacción (original y
        # contrapartida terminan `REVERSED`); si algo falla, nada de esto se confirma.
        from ..reversals.service import efectuar_reverso_si_procede

        new_status = "reversed" if await efectuar_reverso_si_procede(self.db, event, self.current_user) else "approved"
        # `R-153` · `OD-25 (B)`: aprobar una importación de abuelas **sin lote** lo crea aquí
        # mismo (`L-GP-{año}-{nn}`, sin poblar). No-op para el legado con lote y para los demás
        # tipos. Si el lote no puede nacer (p. ej. plan ilegible), la `BR-22` revierte con la
        # aprobación: no hay aprobación sin lote ni lote sin aprobación.
        from ..lots.service import crear_lote_de_importacion_si_procede

        await crear_lote_de_importacion_si_procede(self.db, event, self.current_user)

        self.db.add(models.ApprovalAction(
            event_id=event_id,
            user_id=self.current_user["id"],
            action_type=models.ActionType.APPROVED,
            observations=observations,
        ))
        await self.db.flush()
        await self.db.refresh(event)

        # Audit
        await audit_state_transition(self.db, event, self.current_user,
                                     old_status, new_status,
                                     comments=observations)

        return event

    async def reject(self, event_id: int, observations: str) -> OperationalEvent:
        """Reject a single event (reason mandatory)."""
        event = await self._get_event_for_approval(event_id)

        event.status = EventStatus.REJECTED
        event.observations = observations
        await self.db.flush()

        self.db.add(models.ApprovalAction(
            event_id=event_id,
            user_id=self.current_user["id"],
            action_type=models.ActionType.REJECTED,
            observations=observations,
        ))
        await self.db.flush()
        await self.db.refresh(event)

        # Audit
        await audit_state_transition(self.db, event, self.current_user,
                                     "corrected", "rejected",
                                     comments=observations)

        # `GA-REM-038` / `OD-07`. `docs/02 §3.14`: «Registro rechazado (notificar al
        # operador)». El destinatario es quien **registró**, no quien rechaza: `BR-14` exige
        # segregación, de modo que son personas distintas por diseño.
        #
        # Va dentro de la misma transacción: si el rechazo revierte, el aviso revierte con
        # él. Notificar algo que no llegó a ocurrir es peor que no notificar.
        #
        # `OD-08` amplía los destinatarios: además del operador, los administradores, la
        # contraloría y los supervisores de esa empresa. **El operador no se pierde**: entra
        # como originador y su fuente sigue exigiéndolo. Una decisión que amplía no retira.
        from ..notifications.recipients import resolver_destinatarios
        from ..notifications.service import RECORD_REJECTED, crear_notificacion

        from ..notifications.sla import _area_del_lote

        destinatarios = await resolver_destinatarios(
            self.db,
            company_id=event.company_id,
            area_id=await _area_del_lote(self.db, event.lot_id),
            originadores=[event.registered_by_id],
            explicitos=[event.registered_by_id],   # `docs/02 §3.14`, literal
        )
        for user_id in destinatarios:
            await crear_notificacion(
                self.db,
                company_id=event.company_id,
                recipient_user_id=user_id,
                notification_type=RECORD_REJECTED,
                payload={
                    "event_type": str(getattr(event.event_type, "value", event.event_type)),
                    "lot_id": event.lot_id,
                    "observations": observations,
                },
                related_entity_type="operational_event",
                related_entity_id=event.id,
            )

        return event

    async def batch_approve(self, event_ids: list[int], observations: Optional[str] = None) -> list[OperationalEvent]:
        """Approve multiple events."""
        events = []
        for event_id in event_ids:
            event = await self.approve(event_id, observations)
            events.append(event)
        return events

    async def batch_reject(self, event_ids: list[int], observations: str) -> list[OperationalEvent]:
        """Reject multiple events."""
        events = []
        for event_id in event_ids:
            event = await self.reject(event_id, observations)
            events.append(event)
        return events

    # ============================================================
    # Helpers
    # ============================================================

    async def _get_event_for_approval(self, event_id: int) -> OperationalEvent:
        result = await self.db.execute(
            select(OperationalEvent).where(
                OperationalEvent.id == event_id,
                OperationalEvent.company_id == self.company_id,
                *(await self._ambito_de_unidad()),
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
        await _exigir_habilitacion(self.db, self.current_user, event)  # `R-165` · `OD-19 §13`
        # `GA-REM-007-B` · `R-166`: la fila se bloquea y el estado se relee **antes** de validar la transición.
        await _bloquear_evento(self.db, event)
        # Can approve from CORRECTED or IN_REVIEW (single-level)
        if event.status not in (EventStatus.CORRECTED, EventStatus.IN_REVIEW):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El evento no está en estado aprobable (actual: {event.status.value})",
            )
        return event


class ApprovalStepService:
    """Manages approval step configuration per company."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def _ambito_de_unidad(self):
        """Predicado de cadena productiva para las colas de revisión. `GA-REM-040` fase 6.

        El flujo 6 —revisión y aprobación— quedó aplazado en la fase 5 porque su cadena se
        deriva del evento, y el evento podía no tenerla. Con la clasificación pendiente en
        pie, ya se puede: lo derivable se deriva, lo clasificado se lee, y lo que no tiene
        ninguna de las dos **no entra en la cola** — su superficie es la bandeja.

        Una cola de revisión que muestre eventos de cadenas ajenas revela su volumen y su
        ritmo aunque no se abra ninguno.
        """
        from ..business_units.classification import predicado_de_evento
        from ..business_units.service import unidades_de_alcance_productivo

        # `GA-FE-02-D` · `OD-16`: sin atajo para la autoridad global — su alcance son las
        # unidades habilitadas de la empresa (la concesión no se le exige; la habilitación
        # jamás se salta).
        unidades = await unidades_de_alcance_productivo(
            self.db, current_user=self.current_user, company_id=self.company_id)
        return [predicado_de_evento(unidades, self.company_id)]

    async def get_steps(self) -> list[models.ApprovalStep]:
        result = await self.db.execute(
            select(models.ApprovalStep)
            .where(models.ApprovalStep.company_id == self.company_id)
            .order_by(models.ApprovalStep.step_order)
        )
        return list(result.scalars().all())

    async def create_step(self, data: schemas.ApprovalStepCreate) -> models.ApprovalStep:
        step = models.ApprovalStep(company_id=self.company_id, **data.model_dump())
        self.db.add(step)
        await self.db.flush()
        await self.db.refresh(step)
        return step

    async def update_step(self, step_id: int, data: schemas.ApprovalStepUpdate) -> models.ApprovalStep:
        result = await self.db.execute(
            select(models.ApprovalStep).where(
                models.ApprovalStep.id == step_id,
                models.ApprovalStep.company_id == self.company_id,
            )
        )
        step = result.scalar_one_or_none()
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paso de aprobación no encontrado")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(step, field, value)
        await self.db.flush()
        await self.db.refresh(step)
        return step

    async def delete_step(self, step_id: int) -> None:
        result = await self.db.execute(
            select(models.ApprovalStep).where(
                models.ApprovalStep.id == step_id,
                models.ApprovalStep.company_id == self.company_id,
            )
        )
        step = result.scalar_one_or_none()
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paso de aprobación no encontrado")
        await self.db.delete(step)
        await self.db.flush()

    async def seed_default_steps(self, approval_levels: int) -> list[models.ApprovalStep]:
        """Seed default approval steps for a company based on levels."""
        # Delete existing
        existing = await self.db.execute(
            select(models.ApprovalStep).where(models.ApprovalStep.company_id == self.company_id)
        )
        for s in existing.scalars().all():
            await self.db.delete(s)

        from ..auth.models import Role
        steps = []
        if approval_levels >= 1:
            # Step 1: Review
            reviewer_role = await self._get_role_by_name("Supervisor Avícola")
            steps.append(models.ApprovalStep(
                company_id=self.company_id, step_order=1, name="Revisión",
                role_id=reviewer_role.id, can_correct=True, can_approve=(approval_levels == 1),
                can_reject=False, require_segregation=True,
            ))
        if approval_levels >= 2:
            # Step 2: Approval
            approver_role = await self._get_role_by_name("Aprobador")
            steps.append(models.ApprovalStep(
                company_id=self.company_id, step_order=2, name="Aprobación",
                role_id=approver_role.id, can_correct=True, can_approve=True,
                can_reject=True, require_segregation=True,
            ))
        if approval_levels >= 3:
            # Step 3: Confirmation
            sap_role = await self._get_role_by_name("Analista SAP")
            steps.append(models.ApprovalStep(
                company_id=self.company_id, step_order=3, name="Confirmación",
                role_id=sap_role.id, can_correct=False, can_approve=True,
                can_reject=True, require_segregation=True,
            ))

        for s in steps:
            self.db.add(s)
        await self.db.flush()
        return steps

    async def _get_role_by_name(self, name: str):
        from ..auth.models import Role
        result = await self.db.execute(select(Role).where(Role.name == name))
        role = result.scalar_one_or_none()
        if not role:
            # R-27: un requisito de configuración no satisfecho no es un fallo del
            # servidor. El 500 impedía distinguir «falta configurar los roles» de «algo
            # se ha roto», y no decía qué hacer.
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"El rol '{name}' no existe en el sistema. Cree los roles del flujo "
                    "de aprobación antes de sembrar los pasos por defecto."
                ),
            )
        return role
