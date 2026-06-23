"""Audit schemas — read-only, no create/update/delete."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: str
    company_id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    module: str
    lot_id: Optional[int] = None
    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    previous_values: Optional[dict] = None
    new_values: Optional[dict] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    change_reason: Optional[str] = None
    comments: Optional[str] = None
    sap_reference_id: Optional[int] = None
    ip_address: Optional[str] = None
    is_sensitive: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditTimelineItem(BaseModel):
    """Single item in an entity's audit timeline."""
    id: str
    action: str
    user_id: Optional[int] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    change_reason: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditFilterParams(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    module: Optional[str] = None
    lot_id: Optional[int] = None
    farm_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 50
    offset: int = 0
