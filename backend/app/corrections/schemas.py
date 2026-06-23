"""Correction schemas — Pydantic models for field-level corrections."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CorrectionCreate(BaseModel):
    """Create a correction for a specific field."""
    event_id: int
    field_name: str = Field(..., max_length=100, examples=["quantity", "event_date"])
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    correction_type_id: Optional[int] = None
    reason: str = Field(..., min_length=5, max_length=2000)


class CorrectionRead(BaseModel):
    id: int
    event_id: int
    field_name: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    corrected_by_id: int
    correction_type_id: Optional[int] = None
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CorrectionListResponse(BaseModel):
    corrections: list[CorrectionRead]
    total: int
