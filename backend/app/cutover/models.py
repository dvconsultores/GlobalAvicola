"""GA-REQ-061 · Cutover operacional — modelos (`C1`).

Fundación de datos del cutover: batches, items, staging y correcciones de
opening. La **pieza canónica del opening** es `OpeningBalance` (R-67 ·
`PARTIAL_REUSE`): estas tablas la referencian, no la reemplazan.

Semántica de estados de datos por métrica (`KNOWN|UNKNOWN|NOT_APPLICABLE`) —
`UNKNOWN` **nunca** es `0`. Los estados viajan como columnas tipadas en
`opening_balances`; las máquinas de estado de batch/item usan `String` +
`CHECK` (migración) para no acoplar el esquema a enums nativos.
"""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (JSON, Date, DateTime, ForeignKey, Integer, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class CutoverBatchStatus(str, enum.Enum):
    """Lifecycle del batch: `APPLIED` es terminal (AC24/AC25)."""

    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"


class CutoverItemStatus(str, enum.Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    APPLIED = "applied"


class DataStatus(str, enum.Enum):
    """`0` = conocido y cero · `UNKNOWN` = no disponible · `NOT_APPLICABLE` = no corresponde."""

    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CutoverBatch(Base):
    """Batch de cutover por empresa+BU con trazabilidad completa de actores."""

    __tablename__ = "cutover_batches"
    __table_args__ = (
        UniqueConstraint("company_id", "business_unit", "source_checksum_sha256",
                         "cutover_datetime", name="uq_cutover_batches_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    business_unit: Mapped[str] = mapped_column(String(20), index=True)
    cutover_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(20), default="EXCEL")
    source_system: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_filename: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    source_checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    template_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=CutoverBatchStatus.DRAFT.value, index=True)

    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)

    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    validated_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CutoverItem(Base):
    """Fila de lote/proceso del batch (staging normalizado → item)."""

    __tablename__ = "cutover_items"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_row_number", name="uq_cutover_items_row"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("cutover_batches.id"), index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    business_unit: Mapped[str] = mapped_column(String(20))
    #: Lote existente O creado en el apply (nullable hasta el apply).
    lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lots.id"), nullable=True, index=True)
    legacy_lot_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    real_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cutover_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Complemento **descriptivo** del opening; las métricas con reglas viven tipadas en `opening_balances`.
    opening_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_row_number: Mapped[int] = mapped_column(Integer)
    validation_status: Mapped[str] = mapped_column(String(20), default=CutoverItemStatus.PENDING.value)
    validation_errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CutoverStagingRow(Base):
    """Staging crudo del archivo — el Excel **nunca** escribe tablas operacionales (AC43/44)."""

    __tablename__ = "cutover_staging_rows"
    __table_args__ = (
        UniqueConstraint("batch_id", "row_number", name="uq_cutover_staging_row"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("cutover_batches.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    normalized: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(20), default=CutoverItemStatus.PENDING.value)
    validation_errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OpeningBalanceCorrection(Base):
    """Corrección formal de un opening APPLIED (AC59-65): conserva el original."""

    __tablename__ = "opening_balance_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opening_id: Mapped[int] = mapped_column(Integer, ForeignKey("opening_balances.id"), index=True)
    field: Mapped[str] = mapped_column(String(60))
    old_value: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    delta: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    reason: Mapped[str] = mapped_column(Text)  # obligatoria (AC62)
    requested_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
