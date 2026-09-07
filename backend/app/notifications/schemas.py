"""Contrato de la bandeja — `GA-REM-038`."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: int
    company_id: int
    recipient_user_id: int
    notification_type: str
    payload: dict = {}
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: datetime
    #: `None` es sin leer. La interfaz compone el texto con `notification_type` y `payload`,
    #: de modo que cambiar de idioma cambia lo que se lee, también en los avisos viejos.
    read_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class UnreadCountRead(BaseModel):
    unread: int
