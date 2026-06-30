"""
Operational Events — Unified model for all poultry operational records.
Replaces 12+ legacy tables with a single event_type discriminator.
"""
import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


# ============================================================
# Enums
# ============================================================

class EventType(str, enum.Enum):
    BIRD_RECEPTION = "bird_reception"
    BIRD_DISTRIBUTION = "bird_distribution"
    BIRD_TRANSFER = "bird_transfer"
    BIRD_EXIT = "bird_exit"
    FEED_REGISTRATION = "feed_registration"
    WEIGHT_RECORDING = "weight_recording"
    MORTALITY_RECORDING = "mortality_recording"
    CULL_RECORDING = "cull_recording"
    VACCINATION = "vaccination"
    MEDICATION = "medication"
    FARM_INSPECTION = "farm_inspection"
    TRANSPORT_INSPECTION = "transport_inspection"
    HATCHERY_INSPECTION = "hatchery_inspection"
    EGG_COLLECTION = "egg_collection"
    EGG_CLASSIFICATION = "egg_classification"
    EGG_RECEPTION_CLASSIFICATION = "egg_reception_classification"  # Hatchery: classify received eggs
    EGG_DISPATCH = "egg_dispatch"
    EGG_RECEPTION_HATCHERY = "egg_reception_hatchery"
    INCUBATION_LOAD = "incubation_load"
    OVOSCOPY = "ovoscopy"
    TRANSFER_TO_HATCHER = "transfer_to_hatcher"
    BIRTH_REGISTRATION = "birth_registration"
    CHICK_DISPATCH = "chick_dispatch"
    LOT_CLOSURE = "lot_closure"
    GRANDPARENT_IMPORT = "grandparent_import"


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    RETURNED = "returned"
    CORRECTED = "corrected"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONSOLIDATED = "consolidated"
    SENT_TO_SAP = "sent_to_sap"
    SAP_CONFIRMED = "sap_confirmed"
    SAP_ERROR = "sap_error"
    CANCELLED = "cancelled"


# ============================================================
# OperationalEvent (Unified Model)
# ============================================================

class OperationalEvent(Base):
    """
    Central event model. One table for all 20+ event types,
    replacing crias_pesaje, produccion_mortalidad, engorde_alimento, etc.
    """
    __tablename__ = "operational_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lots.id"), nullable=True, index=True)
    farm_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("farms.id"), nullable=True)
    house_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("houses.id"), nullable=True)

    event_type: Mapped[EventType] = mapped_column(Enum(EventType), index=True)
    event_date: Mapped[date] = mapped_column(Date, default=func.current_date())
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status workflow
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.DRAFT)
    version: Mapped[int] = mapped_column(Integer, default=1)  # optimistic locking

    # Idempotency — client-generated UUID to prevent duplicate submissions
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)

    # Audit
    registered_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # SAP reference
    sap_document_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Operation-specific catalog references (nullable — only populated for the relevant event type)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True)
    cause_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mortality_causes.id"), nullable=True)
    cull_cause_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cull_causes.id"), nullable=True)
    vaccine_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vaccines.id"), nullable=True)
    vaccination_route: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vaccine_lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    medication_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("medications.id"), nullable=True)
    dosage_per_bird: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    treatment_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    destination_farm_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("farms.id"), nullable=True)
    destination_plant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("processing_plants.id"), nullable=True)
    transport_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transports.id"), nullable=True)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Notes
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    bird_movements: Mapped[list["BirdMovement"]] = relationship("BirdMovement", back_populates="event", lazy="selectin")
    egg_movements: Mapped[list["EggMovement"]] = relationship("EggMovement", back_populates="event", lazy="selectin")
    feed_movements: Mapped[list["FeedMovement"]] = relationship("FeedMovement", back_populates="event", lazy="selectin")
    hatchery_params: Mapped[list["HatcheryParams"]] = relationship("HatcheryParams", back_populates="event", lazy="selectin")
    inspection_details: Mapped[list["InspectionDetail"]] = relationship("InspectionDetail", back_populates="event", lazy="selectin")
    egg_storage_records: Mapped[list["EggStorage"]] = relationship("EggStorage", back_populates="event", lazy="selectin")
    evidences: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="event", lazy="selectin")
    alerts: Mapped[list["OperationalAlert"]] = relationship("OperationalAlert", back_populates="event", lazy="selectin")

    def __repr__(self) -> str:
        return f"<OperationalEvent {self.event_type.value} lot={self.lot_id} date={self.event_date}>"


# ============================================================
# Movement Sub-Models (specific data per event type)
# ============================================================

class BirdMovement(Base):
    """Birds received, distributed, transferred, or shipped."""
    __tablename__ = "bird_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    sex: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # male, female, mixed
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    avg_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    week_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # G-11: semana productiva
    breed_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("breeds.id"), nullable=True)
    source_house_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("houses.id"), nullable=True)
    target_house_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("houses.id"), nullable=True)

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="bird_movements")


class EggMovement(Base):
    """Eggs collected, classified, dispatched, received at hatchery, or stored."""
    __tablename__ = "egg_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    egg_type: Mapped[str] = mapped_column(String(30))  # fertile, dirty, broken, infertile, discarded, commercial
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    avg_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # G-07: Pre-incubation storage fields
    storage_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    storage_temp_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    storage_humidity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="egg_movements")


class FeedMovement(Base):
    """Feed consumption records."""
    __tablename__ = "feed_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    feed_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("feed_types.id"), nullable=True)
    quantity_kg: Mapped[float] = mapped_column(Float, default=0.0)
    sacks_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # G-08: número de bultos/sacos
    week_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # G-11: semana productiva
    sap_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # orden de transferencia SAP

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="feed_movements")


class HatcheryParams(Base):
    """Incubation parameters (temperature, humidity, CO2, etc.)."""
    __tablename__ = "hatchery_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    hatchery_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("hatcheries.id"), nullable=True)
    incubator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("incubators.id"), nullable=True)
    hatcher_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("hatchers.id"), nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    co2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turning: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    quantity_loaded: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity_transferred: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="hatchery_params")


class InspectionDetail(Base):
    """Farm, transport, or hatchery inspection details.
    house_id scopes the record to a specific house (galpón) when set.
    Existing records with house_id=NULL represent farm-level data.
    """
    __tablename__ = "inspection_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    house_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("houses.id"), nullable=True, index=True)
    parameter: Mapped[str] = mapped_column(String(200))  # e.g. "temperature", "humidity", "litter_condition"
    value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    value_numeric: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)  # numeric counterpart for aggregations
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # good, regular, bad

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="inspection_details")


class EggStorage(Base):
    """G-07: Pre-incubation egg storage tracking."""
    __tablename__ = "egg_storage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id"), index=True)
    arrival_date: Mapped[date] = mapped_column(Date)
    eggs_received: Mapped[int] = mapped_column(Integer, default=0)
    storage_temp_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    storage_humidity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    storage_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    storage_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    transport_temp_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transport_duration_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="egg_storage_records")


# ============================================================
# G-R06: Evidence / Attachments
# ============================================================

class Evidence(Base):
    """Photos, documents, or files attached to operational events."""
    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))  # local path or S3 URL
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(50))  # photo, document, signature, audio
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="evidences")


# ============================================================
# G-R07: Operational Alerts / Flags
# ============================================================

class OperationalAlert(Base):
    """Automatic alerts triggered when operational thresholds are exceeded."""
    __tablename__ = "operational_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id"), index=True)
    event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("operational_events.id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50))  # high_mortality, capacity_exceeded, weight_deviation, etc.
    severity: Mapped[str] = mapped_column(String(20), default="warning")  # info, warning, critical
    message: Mapped[str] = mapped_column(Text)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped["OperationalEvent"] = relationship("OperationalEvent", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<OperationalAlert {self.alert_type} severity={self.severity}>"


# ============================================================
# G-R09: Reversal / Compensating Entry
# ============================================================

class Reversal(Base):
    """Audit-trailed reversal of an approved/sent event."""
    __tablename__ = "reversals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    reversal_event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("operational_events.id"), nullable=True)  # compensating event
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    reversed_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    original_data_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # frozen state of original
    reversal_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # compensating data
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    original_event: Mapped["OperationalEvent"] = relationship("OperationalEvent", foreign_keys=[original_event_id], backref="reversals_as_original")
