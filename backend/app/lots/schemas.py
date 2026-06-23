"""Pydantic schemas for Lot, LotPhase, and OpeningBalance."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ============================================================
# Lot
# ============================================================

class LotBase(BaseModel):
    company_id: Optional[int] = None
    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    genetic_line_id: Optional[int] = None
    breed_id: Optional[int] = None
    lot_code: str = Field(..., min_length=1, max_length=100)
    bird_type: Optional[str] = None
    sex: Optional[str] = None


class LotCreate(LotBase):
    pass


class LotUpdate(BaseModel):
    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    genetic_line_id: Optional[int] = None
    breed_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class LotRead(LotBase):
    id: int
    status: str
    activation_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class LotDetailRead(LotRead):
    phases: list["LotPhaseRead"] = []
    opening_balance: Optional["OpeningBalanceRead"] = None


# ============================================================
# LotPhase
# ============================================================

class LotPhaseBase(BaseModel):
    lot_id: int
    phase_id: int
    start_date: date
    end_date: Optional[date] = None
    start_population_male: int = 0
    start_population_female: int = 0
    start_weight_avg: Optional[float] = None


class LotPhaseCreate(LotPhaseBase):
    pass


class LotPhaseRead(LotPhaseBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# OpeningBalance
# ============================================================

class OpeningBalanceBase(BaseModel):
    lot_id: int
    activation_date: date
    phase_at_activation_id: int
    age_days: int = 0
    initial_male_count: int = 0
    initial_female_count: int = 0
    accumulated_mortality_male: int = 0
    accumulated_mortality_female: int = 0
    accumulated_culls_male: int = 0
    accumulated_culls_female: int = 0
    accumulated_feed_kg: Optional[float] = None
    current_avg_weight: Optional[float] = None
    accumulated_egg_production: Optional[int] = None
    accumulated_eggs_to_hatchery: Optional[int] = None
    accumulated_chicks_hatched: Optional[int] = None
    accumulated_broiler_received: Optional[int] = None
    activation_reason: str = "Lote existente antes de la implantación del sistema"
    support_document_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_positive(self):
        if self.initial_male_count < 0 or self.initial_female_count < 0:
            raise ValueError("Población inicial no puede ser negativa")
        if self.accumulated_mortality_male > self.initial_male_count:
            raise ValueError("Mortalidad acumulada machos excede población inicial")
        if self.accumulated_mortality_female > self.initial_female_count:
            raise ValueError("Mortalidad acumulada hembras excede población inicial")
        return self


class OpeningBalanceCreate(OpeningBalanceBase):
    pass


class OpeningBalanceRead(OpeningBalanceBase):
    id: int
    is_manual_activation: bool
    activated_by_id: int
    created_at: datetime
    model_config = {"from_attributes": True}
