"""Persistencia inbound — SPEC 005 `§19`, `§20`, `§21`. Detalle en `specs/005-…/data-model.md`.

    sap_inbound_sync_jobs    un job por (petición, objeto): la sincronización reconstruible
    sap_inbound_records      RAW inmutable + capa STAGING (`staged_json` y los tres estados)
    sap_inbound_watermarks   hasta dónde se leyó con éxito; nunca avanza si el batch falla
    sap_entity_mappings      MANDT → BUKRS → WERKS → empresa GA, fail-closed

Los estados son cadenas, no enums de PostgreSQL: son tablas nuevas y así la migración y su
`downgrade` no dejan tipos huérfanos.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ....database import Base

SOURCE_SYSTEM = "SAP_HANA_CLOUD"

# ── Estados ──────────────────────────────────────────────────────────────────
JOB_IN_PROGRESS, JOB_COMPLETED, JOB_PARTIAL = "in_progress", "completed", "partial"
JOB_FAILED, JOB_SKIPPED = "failed", "skipped"

V_PENDING, V_VALID, V_INVALID = "PENDING", "VALID", "INVALID"
M_PENDING, M_MAPPED, M_PENDING_MAPPING = "PENDING", "MAPPED", "PENDING_MAPPING"
P_PENDING, P_READY, P_PROMOTED = "PENDING", "READY_FOR_PROMOTION", "PROMOTED"
P_STAGED_ONLY, P_BLOCKED, P_SUPERSEDED = "STAGED_ONLY", "BLOCKED", "SUPERSEDED"

ENTITY_COMPANY_CODE, ENTITY_PLANT = "COMPANY_CODE", "PLANT"
ENTITY_STORAGE_LOCATION = "STORAGE_LOCATION"
ENTITY_TYPES = (ENTITY_COMPANY_CODE, ENTITY_PLANT, ENTITY_STORAGE_LOCATION)


class SapInboundSyncJob(Base):
    __tablename__ = "sap_inbound_sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_request_id: Mapped[str] = mapped_column(String(36), index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    source_system: Mapped[str] = mapped_column(String(30), default=SOURCE_SYSTEM)
    object_type: Mapped[str] = mapped_column(String(40), index=True)
    query_id: Mapped[str] = mapped_column(String(60))
    trigger: Mapped[str] = mapped_column(String(20), default="manual")
    status: Mapped[str] = mapped_column(String(20), default=JOB_IN_PROGRESS, index=True)
    filters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    watermark_from: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    watermark_to: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    rows_read: Mapped[int] = mapped_column(Integer, default=0)
    rows_raw: Mapped[int] = mapped_column(Integer, default=0)
    rows_noop: Mapped[int] = mapped_column(Integer, default=0)
    rows_valid: Mapped[int] = mapped_column(Integer, default=0)
    rows_invalid: Mapped[int] = mapped_column(Integer, default=0)
    rows_pending_mapping: Mapped[int] = mapped_column(Integer, default=0)
    rows_promoted: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    #: Nulo cuando lo lanza el scheduler: no hay actor humano.
    initiated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<SapInboundSyncJob {self.object_type} {self.status}>"


class SapInboundRecord(Base):
    __tablename__ = "sap_inbound_records"
    __table_args__ = (
        UniqueConstraint("company_id", "source_system", "object_type", "source_key", "version",
                         name="uq_sap_inbound_records_version"),
        Index("uq_sap_inbound_records_current", "company_id", "source_system", "object_type",
              "source_key", unique=True, postgresql_where=text("is_current")),
        Index("ix_sap_inbound_records_promotion", "company_id", "object_type",
              "promotion_status"),
        Index("ix_sap_inbound_records_mapping", "company_id", "object_type", "mapping_status"),
        Index("ix_sap_inbound_records_error", "company_id", "error_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sap_inbound_sync_jobs.id"), index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    source_system: Mapped[str] = mapped_column(String(30), default=SOURCE_SYSTEM)
    object_type: Mapped[str] = mapped_column(String(40))
    source_key: Mapped[str] = mapped_column(String(200))
    client: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    company_code: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    plant_code: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    #: La fila tal como llegó, normalizada a JSON. No se modifica nunca.
    payload_json: Mapped[dict] = mapped_column(JSONB)
    payload_hash: Mapped[str] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    source_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    validation_status: Mapped[str] = mapped_column(String(20), default=V_PENDING)
    mapping_status: Mapped[str] = mapped_column(String(20), default=M_PENDING)
    promotion_status: Mapped[str] = mapped_column(String(30), default=P_PENDING)
    #: STAGING: el DTO de negocio tipado. Nulo mientras la fila no sea válida.
    staged_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    promoted_reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<SapInboundRecord {self.object_type}:{self.source_key} v{self.version}>"


class SapInboundWatermark(Base):
    __tablename__ = "sap_inbound_watermarks"
    __table_args__ = (
        UniqueConstraint("company_id", "source_system", "object_type", "scope_key",
                         name="uq_sap_inbound_watermarks_scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    source_system: Mapped[str] = mapped_column(String(30), default=SOURCE_SYSTEM)
    object_type: Mapped[str] = mapped_column(String(40))
    scope_key: Mapped[str] = mapped_column(String(120))
    watermark_value: Mapped[str] = mapped_column(String(40))
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    last_record_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SapEntityMapping(Base):
    """`SAP SYSTEM → MANDT → BUKRS → WERKS → GA COMPANY`. Una clave SAP, una sola empresa."""
    __tablename__ = "sap_entity_mappings"
    __table_args__ = (
        UniqueConstraint("source_system", "client", "entity_type", "sap_key",
                         name="uq_sap_entity_mappings_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_system: Mapped[str] = mapped_column(String(30), default=SOURCE_SYSTEM)
    client: Mapped[str] = mapped_column(String(3))
    entity_type: Mapped[str] = mapped_column(String(30))
    sap_key: Mapped[str] = mapped_column(String(40))
    parent_sap_key: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    #: `OD-24`: Plant ↔ Farm, solo cuando alguien lo declara. Nunca por heurística.
    farm_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("farms.id"), nullable=True)
    #: LGORT no es un galpón. Este vínculo existe únicamente por decisión expresa.
    house_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("houses.id"), nullable=True)
    #: Informativo. No habilita unidades ni concede acceso (`OD-16.c`).
    business_unit_code: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<SapEntityMapping {self.entity_type}:{self.client}/{self.sap_key}>"
