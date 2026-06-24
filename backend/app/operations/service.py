"""Operational events service — handles all 24 event types through unified API."""
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..masters.service import MasterService
from . import models, schemas
from .validators import (
    BusinessRuleViolation,
    validate_chick_dispatch,
    validate_egg_dispatch,
    validate_event_date,
    validate_farm_house,
    validate_house_capacity,
    validate_incubation_load,
    validate_lot_active,
    validate_mortality,
    validate_oc_limit,
    validate_period_open,
    validate_sap_edit_lock,
    validate_segregation,
)


class OperationsService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    # ============================================================
    # Create Event
    # ============================================================

    async def create_event(self, data: schemas.OperationalEventCreate) -> models.OperationalEvent:
        # Validate event type
        event_type = models.EventType(data.event_type)

        # Business rules per event type
        await self._apply_business_rules(event_type, data)

        # Create event
        event = models.OperationalEvent(
            company_id=self.company_id,
            lot_id=data.lot_id,
            farm_id=data.farm_id,
            house_id=data.house_id,
            event_type=event_type,
            event_date=data.event_date,
            observations=data.observations,
            sap_document_ref=data.sap_document_ref,
            status=models.EventStatus.REGISTERED,
            registered_by_id=self.current_user["id"],
        )
        self.db.add(event)
        await self.db.flush()

        # Create sub-movements
        for bm in data.bird_movements:
            self.db.add(models.BirdMovement(event_id=event.id, **bm.model_dump()))
        for em in data.egg_movements:
            self.db.add(models.EggMovement(event_id=event.id, **em.model_dump()))
        for fm in data.feed_movements:
            self.db.add(models.FeedMovement(event_id=event.id, **fm.model_dump()))
        for hp in data.hatchery_params:
            self.db.add(models.HatcheryParams(event_id=event.id, **hp.model_dump()))
        for ins in data.inspection_details:
            self.db.add(models.InspectionDetail(event_id=event.id, **ins.model_dump()))
        for es in data.egg_storage_records:
            es_data = es.model_dump()
            es_data.setdefault("lot_id", data.lot_id)
            self.db.add(models.EggStorage(event_id=event.id, **es_data))

        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def _apply_business_rules(self, event_type: models.EventType, data: schemas.OperationalEventCreate):
        """Apply business rules based on event type."""
        # BR-07: Lot must be active
        await validate_lot_active(self.db, data.lot_id)
        # BR-06: Event date cannot be before lot activation date
        await validate_event_date(self.db, data.lot_id, data.event_date)
        # BR-08: Movements require farm/house when applicable
        await validate_farm_house(data.event_type.value if hasattr(data.event_type, 'value') else str(data.event_type), data.farm_id, data.house_id)
        # BR-19: Date not in closed period
        await validate_period_open(self.db, data.event_date)

        total_qty = sum(bm.quantity for bm in data.bird_movements) + sum(em.quantity for em in data.egg_movements)

        # G-R04: Validate house capacity for reception/distribution events
        if event_type in (models.EventType.BIRD_RECEPTION, models.EventType.BIRD_DISTRIBUTION):
            if data.house_id and total_qty > 0:
                await validate_house_capacity(self.db, data.house_id, total_qty)
            # G-R05: Validate quantity ≤ OC
            await validate_oc_limit(self.db, data.sap_document_ref, total_qty)

        try:
            if event_type == models.EventType.MORTALITY_RECORDING:
                if total_qty > 0:
                    await validate_mortality(self.db, data.lot_id, total_qty)
            elif event_type == models.EventType.EGG_DISPATCH:
                total = sum(em.quantity for em in data.egg_movements)
                if total > 0:
                    await validate_egg_dispatch(self.db, data.lot_id, total)
            elif event_type == models.EventType.INCUBATION_LOAD:
                total = sum(hp.quantity_loaded or 0 for hp in data.hatchery_params)
                if total > 0:
                    await validate_incubation_load(self.db, data.lot_id, total)
            elif event_type == models.EventType.CHICK_DISPATCH:
                if total_qty > 0:
                    await validate_chick_dispatch(self.db, data.lot_id, total_qty)
        except BusinessRuleViolation as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    # ============================================================
    # Query Events
    # ============================================================

    async def get_events(
        self,
        skip: int = 0,
        limit: int = 20,
        lot_id: Optional[int] = None,
        farm_id: Optional[int] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> tuple[list[models.OperationalEvent], int]:
        query = select(models.OperationalEvent)

        # Company isolation
        if not self.current_user.get("is_super_admin") and self.company_id:
            query = query.where(models.OperationalEvent.company_id == self.company_id)

        if lot_id:
            query = query.where(models.OperationalEvent.lot_id == lot_id)
        if farm_id:
            query = query.where(models.OperationalEvent.farm_id == farm_id)
        if event_type:
            query = query.where(models.OperationalEvent.event_type == event_type)
        if status:
            query = query.where(models.OperationalEvent.status == status)
        if date_from:
            query = query.where(models.OperationalEvent.event_date >= date_from)
        if date_to:
            query = query.where(models.OperationalEvent.event_date <= date_to)

        # Count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Order and paginate
        query = query.order_by(models.OperationalEvent.event_date.desc(), models.OperationalEvent.id.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_event(self, event_id: int) -> models.OperationalEvent:
        result = await self.db.execute(
            select(models.OperationalEvent).where(models.OperationalEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
        return event

    # ============================================================
    # Update & State Transitions
    # ============================================================

    async def update_event(self, event_id: int, data: schemas.OperationalEventUpdate) -> models.OperationalEvent:
        event = await self.get_event(event_id)
        # BR-15: Records sent to SAP cannot be edited
        validate_sap_edit_lock(event.status.value)
        if event.status not in [models.EventStatus.DRAFT, models.EventStatus.REGISTERED, models.EventStatus.RETURNED]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden editar eventos en borrador, registrados o devueltos")
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(event, key, val)
        event.version += 1
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def submit_to_review(self, event_id: int) -> models.OperationalEvent:
        event = await self.get_event(event_id)
        if event.status != models.EventStatus.REGISTERED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo eventos registrados pueden enviarse a revisión")
        event.status = models.EventStatus.PENDING_REVIEW
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def cancel_event(self, event_id: int) -> models.OperationalEvent:
        event = await self.get_event(event_id)
        if event.status in [models.EventStatus.APPROVED, models.EventStatus.CONSOLIDATED, models.EventStatus.SENT_TO_SAP]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede cancelar un evento ya aprobado o enviado a SAP")
        event.status = models.EventStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(event)
        return event

    # ============================================================
    # Event Types Reference
    # ============================================================

    def get_event_types(self) -> list[dict]:
        return schemas.ALL_EVENT_TYPES
