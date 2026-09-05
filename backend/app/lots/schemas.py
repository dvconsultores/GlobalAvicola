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
    """Alta de lote.

    `GA-REM-028` / `R-47`. `start_date` no figuraba en el contrato de creación, de modo que
    pydantic la descartaba **en la capa de esquema**: el cliente la enviaba, recibía un 201 y
    la fecha no llegaba a ninguna parte. Mismo patrón que `P0-14`, donde catorce campos de
    evento se aceptaban y se perdían en silencio.

    `docs/02 §3.5.1` la lista entre los campos del registro de lote, y `docs/02 §3.9.1` la
    exige —«fecha real de inicio»— al incorporar un lote ya en marcha. Sin ella, `P-11` no
    puede existir.
    """

    start_date: Optional[datetime] = None


class LotUpdate(BaseModel):
    """Edición de un lote. **No** incluye `status`.

    `R-51`, misma clase que `R-32`: con `status` en el contrato, un `PUT` podía cerrar un
    lote saltándose `close_lot` —sin la precondición de que estuviera activo, sin resumen
    final y sin fijar `end_date`— y también **reabrir** uno cerrado, con lo que volvían a
    admitirse movimientos contra él (`BR-07`).

    El estado del lote cambia por su transición: `POST /lots/{id}/close`.

    `extra="forbid"` para que enviarlo sea un error explícito y no un descarte silencioso.
    """

    model_config = {"extra": "forbid"}

    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    genetic_line_id: Optional[int] = None
    breed_id: Optional[int] = None
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


# ============================================================
# T-083: Generational Traceability
# ============================================================

class LotRef(BaseModel):
    """Minimal lot reference for traceability tree nodes."""
    id: int
    lot_code: str
    bird_type: Optional[str] = None
    status: str
    model_config = {"from_attributes": True}


class EggBatchRead(BaseModel):
    id: int
    source_lot_id: int
    hatchery_lot_id: Optional[int] = None
    generation: Optional[str] = None  # "grandparent" | "breeder"
    quantity_dispatched: int
    quantity_received: Optional[int] = None
    dispatch_date: date
    reception_date: Optional[date] = None
    source_lot: Optional[LotRef] = None
    hatchery_lot: Optional[LotRef] = None
    model_config = {"from_attributes": True}


class ChickBatchRead(BaseModel):
    id: int
    hatchery_lot_id: int
    destination_lot_id: Optional[int] = None  # Generalized: breeder or broiler
    broiler_lot_id: Optional[int] = None  # Legacy, synced with destination
    egg_batch_id: Optional[int] = None
    quantity_dispatched: int
    quantity_received: Optional[int] = None
    dispatch_date: date
    reception_date: Optional[date] = None
    hatchery_lot: Optional[LotRef] = None
    destination_lot: Optional[LotRef] = None
    broiler_lot: Optional[LotRef] = None
    model_config = {"from_attributes": True}


class EggBatchCreate(BaseModel):
    source_lot_id: int
    hatchery_lot_id: Optional[int] = None
    generation: Optional[str] = None  # "grandparent" | "breeder"
    dispatch_event_id: Optional[int] = None
    quantity_dispatched: int
    dispatch_date: date
    notes: Optional[str] = None


class ChickBatchCreate(BaseModel):
    hatchery_lot_id: int
    destination_lot_id: Optional[int] = None  # Generalized: breeder or broiler lot
    broiler_lot_id: Optional[int] = None  # Legacy, synced if destination not set
    dispatch_event_id: Optional[int] = None
    egg_batch_id: Optional[int] = None
    quantity_dispatched: int
    dispatch_date: date
    notes: Optional[str] = None


class TraceabilityNode(BaseModel):
    """Full generational traceability tree for a lot."""
    lot: LotRef
    egg_batches_sent: list[EggBatchRead] = []        # batches this lot sent upstream
    egg_batches_received: list[EggBatchRead] = []    # batches received (hatchery)
    chick_batches_sent: list[ChickBatchRead] = []    # chicks dispatched to broiler
    chick_batches_received: list[ChickBatchRead] = []  # chicks received (broiler)
