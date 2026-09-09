"""Contratos del reverso interno. `GA-REM-041 §3` · `OD-19 §4, §9`."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ReversalCreate(BaseModel):
    """La solicitud solo dice **qué** se reversa y **por qué**.

    Cantidades, unidad, empresa, estado objetivo y efecto inverso los deriva el servidor del
    original (`OD-19 §4`); `extra="forbid"` para que un cuerpo que pretenda fijarlos sea un
    error explícito y no un descarte silencioso (`AC-S08`).
    """
    model_config = {"extra": "forbid"}

    event_id: int
    reason: str = Field(..., min_length=5, max_length=2000)

    @field_validator("reason")
    @classmethod
    def _motivo_no_vacio(cls, valor: str) -> str:
        # `OD-19 §9` · `AC-AU02`: ni vacío, ni espacios.
        if len(valor.strip()) < 5:
            raise ValueError("El motivo del reverso no puede estar en blanco")
        return valor


class ReversalRead(BaseModel):
    id: int
    original_event_id: int
    reversal_event_id: Optional[int] = None
    company_id: int
    reason: str
    reversed_by_id: int
    original_data_snapshot: Optional[dict] = None
    reversal_data: Optional[dict] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ReversalListResponse(BaseModel):
    reversals: list[ReversalRead]
    total: int
