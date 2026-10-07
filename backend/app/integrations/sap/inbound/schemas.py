"""Esquemas de la API inbound — SPEC 005 `§33`.

Las peticiones prohíben campos extra: no hay hueco por el que colar un SQL, un schema o un
filtro libre. Las respuestas son proyecciones declaradas, no las entidades.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .registry import HanaObject


class _Peticion(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SyncWindow(_Peticion):
    """Ventana opcional de los objetos documentales. Acotada a 366 días por el servicio."""
    date_from: Optional[_dt.date] = None
    date_to: Optional[_dt.date] = None


class SyncRequest(SyncWindow):
    object_types: Optional[list[HanaObject]] = Field(default=None, max_length=20)


class MappingUpsert(_Peticion):
    entity_type: Literal["COMPANY_CODE", "PLANT", "STORAGE_LOCATION"]
    sap_key: str = Field(..., min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_/-]+$")
    parent_sap_key: Optional[str] = Field(default=None, max_length=40,
                                          pattern=r"^[A-Za-z0-9_/-]+$")
    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    business_unit_code: Optional[str] = Field(default=None, max_length=30)


class _Lectura(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class JobRead(_Lectura):
    id: int
    sync_request_id: str
    company_id: int
    object_type: str
    query_id: str
    trigger: str
    status: str
    filters: Optional[dict[str, Any]] = None
    watermark_from: Optional[str] = None
    watermark_to: Optional[str] = None
    rows_read: int
    rows_raw: int
    rows_noop: int
    rows_valid: int
    rows_invalid: int
    rows_pending_mapping: int
    rows_promoted: int
    rows_rejected: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    initiated_by_id: Optional[int] = None
    started_at: Optional[_dt.datetime] = None
    completed_at: Optional[_dt.datetime] = None


class RecordRead(_Lectura):
    id: int
    sync_job_id: int
    object_type: str
    source_key: str
    client: Optional[str] = None
    company_code: Optional[str] = None
    plant_code: Optional[str] = None
    version: int
    payload_hash: str
    validation_status: str
    mapping_status: str
    promotion_status: str
    staged_json: Optional[dict[str, Any]] = None
    promoted_reference_id: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    extracted_at: Optional[_dt.datetime] = None


class MappingRead(_Lectura):
    id: int
    client: str
    entity_type: str
    sap_key: str
    parent_sap_key: Optional[str] = None
    company_id: int
    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    business_unit_code: Optional[str] = None
    is_active: bool


class SyncResponse(BaseModel):
    sync_request_id: Optional[str] = None
    jobs: list[JobRead]
