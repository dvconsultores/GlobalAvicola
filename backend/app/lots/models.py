"""
Lot phases and opening balance models.
Lot base model is in masters/models.py for FK consistency.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class LotPhase(Base):
    """Tracks each productive phase of a lot (cría → producción → engorde)."""
    __tablename__ = "lot_phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id"), index=True)
    phase_id: Mapped[int] = mapped_column(Integer, ForeignKey("productive_phases.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_population_male: Mapped[int] = mapped_column(Integer, default=0)
    start_population_female: Mapped[int] = mapped_column(Integer, default=0)
    start_weight_avg: Mapped[Optional[float]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lot: Mapped["Lot"] = relationship("Lot", back_populates="phases", lazy="selectin")
    phase: Mapped["ProductivePhase"] = relationship("ProductivePhase", lazy="selectin")

    def __repr__(self) -> str:
        return f"<LotPhase lot={self.lot_id} phase={self.phase_id}>"


class OpeningBalance(Base):
    """
    Manual activation of a lot that was already in progress before system adoption.
    Stores all initial balances needed to continue operations from a mid-point.
    """
    __tablename__ = "opening_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id"), unique=True, index=True)
    activation_date: Mapped[date] = mapped_column(Date)
    phase_at_activation_id: Mapped[int] = mapped_column(Integer, ForeignKey("productive_phases.id"))
    age_days: Mapped[int] = mapped_column(Integer, default=0)

    # Bird counts
    initial_male_count: Mapped[int] = mapped_column(Integer, default=0)
    initial_female_count: Mapped[int] = mapped_column(Integer, default=0)

    # Accumulated historical data
    accumulated_mortality_male: Mapped[int] = mapped_column(Integer, default=0)
    accumulated_mortality_female: Mapped[int] = mapped_column(Integer, default=0)
    accumulated_culls_male: Mapped[int] = mapped_column(Integer, default=0)
    accumulated_culls_female: Mapped[int] = mapped_column(Integer, default=0)
    accumulated_feed_kg: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Current status
    current_avg_weight: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Production phase specific
    accumulated_egg_production: Mapped[Optional[int]] = mapped_column(nullable=True)
    accumulated_eggs_to_hatchery: Mapped[Optional[int]] = mapped_column(nullable=True)
    accumulated_chicks_hatched: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Broiler phase specific
    accumulated_broiler_received: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Audit
    is_manual_activation: Mapped[bool] = mapped_column(Boolean, default=True)
    activated_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    activation_reason: Mapped[str] = mapped_column(Text, default="Lote existente antes de la implantación del sistema")
    support_document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lot: Mapped["Lot"] = relationship("Lot", back_populates="opening_balance", lazy="selectin")
    activated_by: Mapped["User"] = relationship("User", lazy="selectin")
    phase_at_activation: Mapped["ProductivePhase"] = relationship("ProductivePhase", lazy="selectin")

    def __repr__(self) -> str:
        return f"<OpeningBalance lot={self.lot_id} date={self.activation_date}>"


# Import after class definition to resolve forward references
from ..masters.models import Lot  # noqa: E402, F811
from ..auth.models import User  # noqa: E402, F811
from ..masters.models import ProductivePhase  # noqa: E402, F811


# ============================================================
# T-083: Generational Traceability
# ============================================================

class EggBatch(Base):
    """
    Tracks fertilized egg batches from breeder/grandparent lot → hatchery lot.
    Bridges the production chain: REPRODUCTORAS → INCUBADORA.
    """
    __tablename__ = "egg_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Source: breeder or grandparent production lot
    source_lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id"), index=True)
    # Destination: hatchery lot that receives these eggs
    hatchery_lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lots.id"), nullable=True, index=True)
    # Reference to the egg_dispatch operational event
    dispatch_event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("operational_events.id"), nullable=True)
    # Reference to the egg_reception_hatchery operational event
    reception_event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("operational_events.id"), nullable=True)

    quantity_dispatched: Mapped[int] = mapped_column(Integer, default=0)
    quantity_received: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dispatch_date: Mapped[date] = mapped_column(Date)
    reception_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source_lot: Mapped["Lot"] = relationship("Lot", foreign_keys=[source_lot_id], lazy="selectin")
    hatchery_lot: Mapped[Optional["Lot"]] = relationship("Lot", foreign_keys=[hatchery_lot_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<EggBatch id={self.id} source={self.source_lot_id} → hatchery={self.hatchery_lot_id}>"


class ChickBatch(Base):
    """
    Tracks chick batches from hatchery lot → broiler lot.
    Bridges the production chain: INCUBADORA → ENGORDE.
    """
    __tablename__ = "chick_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Source: hatchery lot
    hatchery_lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id"), index=True)
    # Destination: broiler lot that receives these chicks
    broiler_lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lots.id"), nullable=True, index=True)
    # Reference to the chick_dispatch operational event
    dispatch_event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("operational_events.id"), nullable=True)
    # Reference to the bird_reception (broiler) operational event
    reception_event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("operational_events.id"), nullable=True)
    # Back-link to the egg batch that produced these chicks
    egg_batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("egg_batches.id"), nullable=True)

    quantity_dispatched: Mapped[int] = mapped_column(Integer, default=0)
    quantity_received: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dispatch_date: Mapped[date] = mapped_column(Date)
    reception_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    hatchery_lot: Mapped["Lot"] = relationship("Lot", foreign_keys=[hatchery_lot_id], lazy="selectin")
    broiler_lot: Mapped[Optional["Lot"]] = relationship("Lot", foreign_keys=[broiler_lot_id], lazy="selectin")
    egg_batch: Mapped[Optional["EggBatch"]] = relationship("EggBatch", lazy="selectin")
