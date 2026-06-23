"""Correction service — creates immutable correction audit trail."""
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..operations.models import EventStatus, OperationalEvent
from . import models, schemas


class CorrectionService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def create_correction(self, data: schemas.CorrectionCreate) -> models.CorrectionLog:
        """Create a correction log entry and update the event status to CORRECTED."""
        # Validate event exists and belongs to company
        result = await self.db.execute(
            select(OperationalEvent).where(
                OperationalEvent.id == data.event_id,
                OperationalEvent.company_id == self.company_id,
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")

        # Event must be in a correctable state
        correctable = (EventStatus.REGISTERED, EventStatus.PENDING_REVIEW, EventStatus.IN_REVIEW, EventStatus.RETURNED)
        if event.status not in correctable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El evento no se puede corregir en estado '{event.status.value}'",
            )

        # Create immutable correction log
        correction = models.CorrectionLog(
            event_id=data.event_id,
            field_name=data.field_name,
            original_value=data.original_value,
            corrected_value=data.corrected_value,
            corrected_by_id=self.current_user["id"],
            correction_type_id=data.correction_type_id,
            reason=data.reason,
        )
        self.db.add(correction)

        # Update event status to CORRECTED
        event.status = EventStatus.CORRECTED
        await self.db.flush()
        await self.db.refresh(correction)
        return correction

    async def get_corrections_for_event(self, event_id: int) -> list[models.CorrectionLog]:
        """Get all corrections for a given event."""
        result = await self.db.execute(
            select(models.CorrectionLog)
            .join(OperationalEvent, models.CorrectionLog.event_id == OperationalEvent.id)
            .where(
                models.CorrectionLog.event_id == event_id,
                OperationalEvent.company_id == self.company_id,
            )
            .order_by(models.CorrectionLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_corrections(
        self,
        lot_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[models.CorrectionLog], int]:
        """List corrections with optional lot filter."""
        base = select(models.CorrectionLog).join(
            OperationalEvent, models.CorrectionLog.event_id == OperationalEvent.id
        ).where(OperationalEvent.company_id == self.company_id)
        cq = select(func_count()).select_from(models.CorrectionLog).join(
            OperationalEvent, models.CorrectionLog.event_id == OperationalEvent.id
        ).where(OperationalEvent.company_id == self.company_id)

        if lot_id:
            base = base.where(OperationalEvent.lot_id == lot_id)
            cq = cq.where(OperationalEvent.lot_id == lot_id)

        base = base.order_by(models.CorrectionLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(base)
        corrections = list(result.scalars().all())
        count_r = await self.db.execute(cq)
        total = count_r.scalar() or 0
        return corrections, total


def func_count():
    from sqlalchemy import func
    return func.count()
