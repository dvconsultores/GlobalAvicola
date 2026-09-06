"""SAP Integration schemas — Pydantic models."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================
# SapReference
# ============================================================

class SapReferenceCreate(BaseModel):
    """`R-95` / `GA-REM-035`. `quantity` faltaba.

    `SapReference.quantity` existe en el modelo con el comentario «`G-R05`: OC/STO expected
    quantity», pero el esquema de importación no la declaraba: Pydantic la descartaba en
    silencio y toda orden importada quedaba sin cantidad ordenada. Con ella nula,
    `validate_oc_limit` sale por su primera línea, de modo que **`BR-18` no podía dispararse
    nunca**, poblado o no el campo tipado.

    Es el mismo patrón de `R-47` y `P0-14`: el cliente envía, el esquema descarta, la
    respuesta es `2xx` y el dominio nunca se entera.
    """
    ref_type: str = Field(..., examples=["purchase_order"])
    sap_code: str = Field(..., max_length=100)
    description: Optional[str] = None
    quantity: Optional[float] = None
    extra_data: Optional[dict[str, Any]] = None


class SapReferenceRead(BaseModel):
    id: int
    company_id: int
    ref_type: str
    sap_code: str
    description: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None
    is_active: bool
    imported_by_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SapReferenceImportRequest(BaseModel):
    """Bulk import SAP references from CSV/JSON data."""
    references: list[SapReferenceCreate] = Field(..., min_length=1, max_length=1000)


# ============================================================
# Consolidation
# ============================================================

class ConsolidateRequest(BaseModel):
    lot_id: Optional[int] = None
    event_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class ConsolidatedMovementRead(BaseModel):
    id: int
    company_id: int
    lot_id: int
    event_type: str
    period_start: datetime
    period_end: datetime
    event_ids: list[int]
    total_quantity: float
    unit: Optional[str] = None
    sap_reference: Optional[str] = None
    consolidated_by_id: int
    sap_payload_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Sync Job
# ============================================================

class SyncJobRead(BaseModel):
    id: int
    company_id: int
    direction: str
    status: str
    total_records: int
    success_count: int
    error_count: int
    file_name: Optional[str] = None
    initiated_by_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# SAP Export
# ============================================================

class SapExportRequest(BaseModel):
    """Trigger export of consolidated movements to SAP."""
    consolidated_ids: Optional[list[int]] = None  # specific IDs, or all pending
    file_name: Optional[str] = None


class SapExportResponse(BaseModel):
    sync_job_id: int
    payloads_created: int
    status: str
    message: str


class SapRetryRequest(BaseModel):
    """Retry failed SAP payloads."""
    payload_ids: Optional[list[int]] = None  # specific payloads, or all failed
    max_retries: int = Field(default=3, ge=1, le=5)


# ============================================================
# Payload / Response
# ============================================================

class SapPayloadRead(BaseModel):
    id: int
    company_id: int
    sync_job_id: Optional[int] = None
    consolidated_movement_id: Optional[int] = None
    idempotency_key: str
    status: str
    retry_count: int
    sap_document_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SapResponseRead(BaseModel):
    id: int
    payload_id: int
    status_code: Optional[int] = None
    sap_document_id: Optional[str] = None
    sap_message: Optional[str] = None
    is_success: bool
    received_at: datetime

    model_config = {"from_attributes": True}


class SapErrorItem(BaseModel):
    payload_id: int
    error_message: Optional[str] = None
    retry_count: int
    sap_document_id: Optional[str] = None
    created_at: datetime
