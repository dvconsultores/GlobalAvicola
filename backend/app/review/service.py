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



class ReviewService(SegregacionMixin):
    """Handles review workflow: batch creation, start/return/complete review."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

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
        base = select(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.status.in_([EventStatus.REGISTERED, EventStatus.PENDING_REVIEW]),
        )
        count_q = select(func_count()).select_from(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
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
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
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
        base = select(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.status == EventStatus.CORRECTED,
        )
        cq = select(func_count()).select_from(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
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

        event.status = EventStatus.APPROVED
        event.approved_by_id = self.current_user["id"]
        if observations:
            event.observations = observations
        await self.db.flush()

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
                                     "corrected", "approved",
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
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
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
