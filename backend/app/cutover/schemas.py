"""GA-REQ-061 · Cutover — esquemas de API (C2: ciclo crear→subir→validar)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

BusinessUnit = Literal["grandparent", "breeder", "hatchery", "broiler"]


class CutoverBatchCreate(BaseModel):
    business_unit: BusinessUnit
    cutover_datetime: datetime
    source_system: Optional[str] = None
    source_reference: Optional[str] = None
    observations: Optional[str] = None


class CutoverBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    business_unit: str
    cutover_datetime: datetime
    source_type: str
    source_filename: Optional[str] = None
    source_checksum_sha256: Optional[str] = None
    template_version: Optional[str] = None
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int


class CutoverRejectRequest(BaseModel):
    #: El rechazo exige razón (AC62-style para batch): ≥5 caracteres.
    reason: str = Field(min_length=5, max_length=500)


class CutoverValidationError(BaseModel):
    row_number: int
    column: Optional[str] = None
    field: Optional[str] = None
    error_code: str
    message: str
    received_value: Optional[str] = None


class CutoverValidationRead(BaseModel):
    batch_id: int
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[CutoverValidationError]


class CutoverItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_row_number: int
    legacy_lot_reference: Optional[str] = None
    lot_id: Optional[int] = None
    real_start_date: Optional[date] = None
    validation_status: str
    validation_errors: Optional[list] = None


class CutoverItemsResponse(BaseModel):
    items: list[CutoverItemRead]


# ── C5: reconciliación Opening / Post / Lifetime (goldens de la spec) ──────────


class CutoverReconciliationSource(BaseModel):
    type: str
    system: Optional[str] = None
    reference: Optional[str] = None
    filename: Optional[str] = None
    checksum: Optional[str] = None
    template_version: Optional[str] = None


class CutoverOpeningRead(BaseModel):
    live: int
    historical_mortality: Optional[int] = None
    mortality_status: str
    feed_status: str


class CutoverPostRead(BaseModel):
    mortality: int
    culls: int
    feed_kg: Optional[float] = None


class CutoverLifetimeRead(BaseModel):
    #: `null` cuando alguna pieza es UNKNOWN (jamás un número fabricado).
    mortality: Optional[int] = None


class CutoverReconciliationLot(BaseModel):
    lot_id: int
    legacy_lot_code: Optional[str] = None
    origin: Optional[str] = None
    opening: CutoverOpeningRead
    post: CutoverPostRead
    lifetime: CutoverLifetimeRead
    current_live: int


class CutoverReconciliationRead(BaseModel):
    batch_id: int
    company_id: int
    business_unit: str
    cutover_datetime: datetime
    status: str
    source: CutoverReconciliationSource
    items: int
    openings: int
    unknown_metrics: int
    applied_by_id: Optional[int] = None
    applied_at: Optional[datetime] = None
    lots: list[CutoverReconciliationLot]


# ── C6: correcciones formales del Opening (AC59-65) ────────────────────────────


class OpeningCorrectionCreate(BaseModel):
    #: Campo corregible del opening (lista blanca del servicio).
    field: str
    new_value: int
    #: Razón obligatoria (AC62 / CUT-RED-17): ≥5 caracteres.
    reason: str = Field(min_length=5, max_length=500)


class OpeningCorrectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opening_id: int
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    delta: Optional[str] = None
    reason: str
    requested_by_id: int
    approved_by_id: Optional[int] = None
    created_at: datetime
    applied_at: Optional[datetime] = None


class OpeningCorrectionList(BaseModel):
    items: list[OpeningCorrectionRead]
