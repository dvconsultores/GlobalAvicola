"""
Lot service with business rules for lot lifecycle management.
"""
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..masters.models import Lot
from ..operations.models import (
    OperationalEvent, EventType, EventStatus,
    BirdMovement, FeedMovement, EggMovement,
)
from . import models, schemas
from ..masters.service import MasterService


class LotService:
    """Handles lot CRUD, activation, closure, and balance queries."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")
        self.is_super_admin = current_user.get("is_super_admin", False)

    async def get_lots(
        self, skip: int = 0, limit: int = 20, search: str = "",
        farm_id: Optional[int] = None, status: Optional[str] = None,
    ) -> tuple[list[Lot], int]:
        """List lots with filters and company isolation."""
        master_service = MasterService(self.db, Lot, self.current_user)
        filters = {}
        if farm_id:
            filters["farm_id"] = farm_id
        if status:
            filters["status"] = status
        return await master_service.get_all(
            skip=skip, limit=limit, search=search,
            search_fields=["lot_code"],
            filters=filters,
            order_by="lot_code",
        )

    async def get_lot(self, lot_id: int) -> Lot:
        """Get single lot with phases and opening balance eager loaded."""
        master_service = MasterService(self.db, Lot, self.current_user)
        return await master_service.get_by_id(lot_id)

    async def create_lot(self, data: schemas.LotCreate) -> Lot:
        """Create a new lot."""
        existing = await self.db.execute(
            select(Lot).where(Lot.lot_code == data.lot_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un lote con ese código",
            )

        lot = Lot(
            company_id=self.company_id,
            lot_code=data.lot_code,
            farm_id=data.farm_id,
            house_id=data.house_id,
            genetic_line_id=data.genetic_line_id,
            breed_id=data.breed_id,
            bird_type=data.bird_type,
            sex=data.sex,
            status="active",
            activation_type="normal",
            start_date=date.today(),
        )
        self.db.add(lot)
        await self.db.flush()
        await self.db.refresh(lot)
        return lot

    async def update_lot(self, lot_id: int, data: schemas.LotUpdate) -> Lot:
        """Update lot fields."""
        master_service = MasterService(self.db, Lot, self.current_user)
        return await master_service.update(lot_id, data)

    async def close_lot(self, lot_id: int) -> dict:
        """G-09: Close a lot with final summary (BR-05)."""
        master_service = MasterService(self.db, Lot, self.current_user)
        lot = await master_service.get_by_id(lot_id)

        if lot.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden cerrar lotes activos",
            )

        # Calculate final summary
        # Total mortality
        mort_q = select(func.coalesce(func.sum(BirdMovement.quantity), 0)).join(
            OperationalEvent, BirdMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.MORTALITY_RECORDING,
        )
        mort_result = await self.db.execute(mort_q)
        total_mortality = mort_result.scalar() or 0

        # Total feed consumed
        feed_q = select(func.coalesce(func.sum(FeedMovement.quantity_kg), 0.0)).join(
            OperationalEvent, FeedMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
        )
        feed_result = await self.db.execute(feed_q)
        total_feed_kg = round(feed_result.scalar() or 0.0, 2)

        # Total eggs produced (if breeder)
        egg_q = select(func.coalesce(func.sum(EggMovement.quantity), 0)).join(
            OperationalEvent, EggMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.EGG_COLLECTION,
        )
        egg_result = await self.db.execute(egg_q)
        total_eggs = egg_result.scalar() or 0

        # Approved events count
        events_q = select(func.count(OperationalEvent.id)).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
        )
        events_result = await self.db.execute(events_q)
        total_events = events_result.scalar() or 0

        approved_q = select(func.count(OperationalEvent.id)).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.status.in_([
                EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
            ]),
        )
        approved_result = await self.db.execute(approved_q)
        approved_events = approved_result.scalar() or 0

        # Age in days
        age_days = (date.today() - lot.start_date).days if lot.start_date else 0

        summary = {
            "lot_id": lot_id,
            "lot_code": lot.lot_code if hasattr(lot, 'lot_code') else f"L-{lot_id}",
            "age_days": age_days,
            "total_mortality": total_mortality,
            "total_feed_kg": total_feed_kg,
            "total_eggs": total_eggs,
            "total_events": total_events,
            "approved_events": approved_events,
            "status": "closed",
            "end_date": str(date.today()),
        }

        lot.status = "closed"
        lot.end_date = date.today()
        await self.db.flush()
        await self.db.refresh(lot)

        return summary

    # ============================================================
    # Manual Activation (Opening Balance)
    # ============================================================

    async def activate_manual(self, data: schemas.OpeningBalanceCreate) -> models.OpeningBalance:
        """
        Activate a lot manually with opening balances.
        Used for lots that already exist before system adoption.
        """
        # Validate lot exists
        lot = await self.db.execute(select(Lot).where(Lot.id == data.lot_id))
        lot = lot.scalar_one_or_none()
        if not lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

        # Validate no existing opening balance
        existing = await self.db.execute(
            select(models.OpeningBalance).where(models.OpeningBalance.lot_id == data.lot_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este lote ya tiene un balance de apertura registrado",
            )

        # Business rules for opening balance
        if data.accumulated_mortality_male > data.initial_male_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mortalidad acumulada machos no puede exceder población inicial",
            )
        if data.accumulated_mortality_female > data.initial_female_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mortalidad acumulada hembras no puede exceder población inicial",
            )

        ob = models.OpeningBalance(
            lot_id=data.lot_id,
            activation_date=data.activation_date,
            phase_at_activation_id=data.phase_at_activation_id,
            age_days=data.age_days,
            initial_male_count=data.initial_male_count,
            initial_female_count=data.initial_female_count,
            accumulated_mortality_male=data.accumulated_mortality_male,
            accumulated_mortality_female=data.accumulated_mortality_female,
            accumulated_culls_male=data.accumulated_culls_male,
            accumulated_culls_female=data.accumulated_culls_female,
            accumulated_feed_kg=data.accumulated_feed_kg,
            current_avg_weight=data.current_avg_weight,
            accumulated_egg_production=data.accumulated_egg_production,
            accumulated_eggs_to_hatchery=data.accumulated_eggs_to_hatchery,
            accumulated_chicks_hatched=data.accumulated_chicks_hatched,
            accumulated_broiler_received=data.accumulated_broiler_received,
            activation_reason=data.activation_reason,
            support_document_url=data.support_document_url,
            is_manual_activation=True,
            activated_by_id=self.current_user["id"],
        )
        self.db.add(ob)

        # Mark lot as manually activated
        lot.activation_type = "manual"
        lot.start_date = data.activation_date

        await self.db.flush()
        await self.db.refresh(ob)
        return ob

    async def get_opening_balance(self, lot_id: int) -> Optional[models.OpeningBalance]:
        """Get opening balance for a lot."""
        result = await self.db.execute(
            select(models.OpeningBalance).where(models.OpeningBalance.lot_id == lot_id)
        )
        return result.scalar_one_or_none()

    async def get_lot_phases(self, lot_id: int) -> list[models.LotPhase]:
        """Get all phases for a lot."""
        result = await self.db.execute(
            select(models.LotPhase)
            .where(models.LotPhase.lot_id == lot_id)
            .order_by(models.LotPhase.start_date)
        )
        return list(result.scalars().all())

    async def add_phase(self, data: schemas.LotPhaseCreate) -> models.LotPhase:
        """Add a new phase to a lot."""
        phase = models.LotPhase(**data.model_dump())
        self.db.add(phase)
        await self.db.flush()
        await self.db.refresh(phase)
        return phase
