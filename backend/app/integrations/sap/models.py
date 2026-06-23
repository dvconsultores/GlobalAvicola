"""
SAP Integration models — SapReference, SapSyncJob, SapPayload, SapResponse, ConsolidatedMovement.
Follows the adapter pattern: domain never imports SAP concrete implementations.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey, Integer,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ...database import Base


# ============================================================
# Enums
# ============================================================

class SapReferenceType(str, enum.Enum):
    PURCHASE_ORDER = "purchase_order"
    TRANSFER_ORDER = "transfer_order"
    MATERIAL = "material"
    VENDOR = "vendor"
    PLANT = "plant"
    STORAGE_LOCATION = "storage_location"
    COST_CENTER = "cost_center"
    SAP_BATCH = "sap_batch"
    OTHER = "other"


class SyncDirection(str, enum.Enum):
    IMPORT = "import"
    EXPORT = "export"


class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PayloadStatus(str, enum.Enum):
    PREPARED = "prepared"
    SENDING = "sending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    RETRYING = "retrying"


# ============================================================
# SapReference
# ============================================================

class SapReference(Base):
    """Stores a reference to any SAP object (PO, material, vendor, etc.)."""
    __tablename__ = "sap_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    ref_type: Mapped[SapReferenceType] = mapped_column(Enum(SapReferenceType), index=True)
    sap_code: Mapped[str] = mapped_column(String(100), index=True)  # SAP document/material/order code
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # G-R05: OC/STO expected quantity
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # G-R05: unit of measure
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # flexible additional data
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    imported_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<SapReference {self.ref_type.value}:{self.sap_code}>"


# ============================================================
# ConsolidatedMovement
# ============================================================

class ConsolidatedMovement(Base):
    """Groups approved operational events ready for SAP export."""
    __tablename__ = "consolidated_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_ids: Mapped[list[int]] = mapped_column(JSONB, default=list)  # list of event IDs consolidated
    total_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # kg, units, eggs
    sap_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # SAP doc ref
    consolidated_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    sap_payload_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # soft ref, no FK (circular)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<ConsolidatedMovement lot={self.lot_id} type={self.event_type}>"


# ============================================================
# SapSyncJob
# ============================================================

class SapSyncJob(Base):
    """Tracks a complete sync operation (import or export batch)."""
    __tablename__ = "sap_sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    direction: Mapped[SyncDirection] = mapped_column(Enum(SyncDirection))
    status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus), default=SyncStatus.PENDING)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    file_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    initiated_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<SapSyncJob {self.direction.value} status={self.status.value}>"


# ============================================================
# SapPayload
# ============================================================

class SapPayload(Base):
    """Individual payload prepared for SAP export."""
    __tablename__ = "sap_payloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    sync_job_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # soft ref to sap_sync_jobs
    consolidated_movement_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # soft ref
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # SHA-256
    external_transaction_id: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True, index=True)  # G-R03: unique cross-system ID
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="APP_AVICOLA")  # G-R03
    sap_reference_item: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # G-R03: posición de documento SAP
    payload_data: Mapped[dict] = mapped_column(JSONB)  # the actual SAP-compatible JSON
    status: Mapped[PayloadStatus] = mapped_column(Enum(PayloadStatus), default=PayloadStatus.PREPARED)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sap_document_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # SAP confirmation ID
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<SapPayload status={self.status.value} retry={self.retry_count}>"


# ============================================================
# SapResponse
# ============================================================

class SapResponse(Base):
    """Response received from SAP for a payload."""
    __tablename__ = "sap_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payload_id: Mapped[int] = mapped_column(Integer, ForeignKey("sap_payloads.id"), index=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sap_document_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sap_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_success: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<SapResponse payload={self.payload_id} success={self.is_success}>"
