"""GA-REQ-061 · Cutover — esquemas de API (C2: ciclo crear→subir→validar)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

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
