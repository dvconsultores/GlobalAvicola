"""Review & Approval service — business logic for review workflow."""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_approval_action, audit_state_transition
from ..operations.models import EventStatus, OperationalEvent
from . import models, schemas


class ReviewService:
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
            # Single level: review = approval
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


class ApprovalService:
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

        # BR-14: Operator cannot approve own data (segregation of duties)
        from ..operations.validators import validate_segregation, BusinessRuleViolation
        from fastapi import HTTPException, status as http_status
        try:
            validate_segregation(event.registered_by_id, self.current_user["id"], "aprobar")
        except BusinessRuleViolation as e:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=e.message)

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rol '{name}' no encontrado en el sistema",
            )
        return role
