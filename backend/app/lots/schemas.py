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
    # `GA-REM-037 AC07`. La **versión concreta** de la curva estándar, no solo la línea:
    # publicar una revisión no puede cambiar la referencia contra la que ya se juzgó a
    # este lote. Si se omite, el alta toma la versión activa de su línea (`AC09`).
    weight_curve_id: Optional[int] = None
    #: `GA-REM-039` / `OD-08`. Ámbito funcional del lote; por él resuelven su área los seis
    #: avisos de `P-14`.
    area_id: Optional[int] = None
    #: `GA-REM-038` enmienda B / `OD-08`. Cuándo se **prevé** cerrar. No es `end_date`, que es
    #: la fecha real y la fija `close_lot`: usar aquélla para pronosticar avisaría de algo que
    #: ya ocurrió. Va en la base para que el alta la acepte y la lectura la devuelva.
    planned_close_date: Optional[datetime] = None
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
    area_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    #: Replanificar es legítimo y no reescribe la historia: los avisos ya emitidos se
    #: conservan como evidencia de lo que se sabía entonces.
    planned_close_date: Optional[datetime] = None


class LotRead(LotBase):
    id: int
    status: str
    activation_type: Optional[str] = None
    start_date: Optional[datetime] = None
    #: La real. No se confunde con `planned_close_date`, que viaja en `LotBase`.
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
    # `R-191`: la lectura incluye la fase maestra (código y nombre) — la UI distingue
    # producción de cría sin una segunda consulta.
    phase: Optional["ProductivePhaseRead"] = None
    model_config = {"from_attributes": True}


from ..masters.schemas import ProductivePhaseRead  # noqa: E402  (evita ciclo al importar)
LotPhaseRead.model_rebuild()


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
    """Despacho de huevo fértil. `OD-10.b`: el destino se declara **al crear**.

    Era opcional, y con destino nulo la incubadora no podía saber que un despacho era para
    ella antes de recibirlo. La alternativa —enseñarle todos los pendientes de la empresa
    para que encontrara el suyo— anularía el aislamiento justo en el punto que se quería
    proteger.
    """

    source_lot_id: int
    hatchery_lot_id: int
    generation: Optional[str] = None  # "grandparent" | "breeder"
    dispatch_event_id: Optional[int] = None
    quantity_dispatched: int
    dispatch_date: date
    notes: Optional[str] = None


class ChickBatchCreate(BaseModel):
    """Despacho de pollito. `OD-10.b`: el destino se declara al crear.

    Se admiten los dos nombres —`destination_lot_id` es el general y `broiler_lot_id` el
    heredado— pero **uno de los dos es obligatorio**: sin destino no hay contrato.
    """

    hatchery_lot_id: int
    destination_lot_id: Optional[int] = None  # general: cría o engorde
    broiler_lot_id: Optional[int] = None  # heredado, se sincroniza con el anterior

    @model_validator(mode="after")
    def _exige_destino(self):
        if self.destination_lot_id is None and self.broiler_lot_id is None:
            raise ValueError(
                "el destino del despacho es obligatorio: indique `destination_lot_id`")
        return self
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


# ============================================================
# Cierre de lote
# ============================================================

class LotClosureSummary(BaseModel):
    """
    `GA-REM-029 AC02`. El resumen final que exige `BR-05`, declarado.

    La ruta no tenía `response_model`, así que nadie fijó nunca el contrato: el servicio
    devolvía este resumen y la ruta lo validaba como `LotRead`, de modo que **el cierre
    respondía 500 siempre** (`R-73`). Tipado aquí, cualquier divergencia futura entre
    servicio y ruta rompe en validación en vez de pasar inadvertida.
    """
    lot_id: int
    lot_code: str
    age_days: int
    total_mortality: int
    total_feed_kg: float
    total_eggs: int
    total_events: int
    approved_events: int
    status: str
    end_date: date
