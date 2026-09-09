"""Pydantic schemas for operational events and movements."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================
# Movement Schemas
# ============================================================

class BirdMovementSchema(BaseModel):
    model_config = {"from_attributes": True}
    sex: Optional[str] = None
    quantity: int = Field(default=0, ge=0)
    avg_weight: Optional[float] = None
    week_number: Optional[int] = None
    breed_id: Optional[int] = None
    source_house_id: Optional[int] = None
    target_house_id: Optional[int] = None


class EggMovementSchema(BaseModel):
    model_config = {"from_attributes": True}
    egg_type: str  # fertile, dirty, broken, infertile, discarded, commercial
    quantity: int = Field(default=0, ge=0)
    avg_weight: Optional[float] = None
    classification_date: Optional[date] = None
    storage_start_date: Optional[date] = None
    storage_temp_c: Optional[float] = None
    storage_humidity_pct: Optional[float] = None


class FeedMovementSchema(BaseModel):
    model_config = {"from_attributes": True}
    feed_type_id: Optional[int] = None
    quantity_kg: float = Field(default=0.0, gt=0)
    sacks_count: Optional[int] = None
    week_number: Optional[int] = None
    sap_order_id: Optional[str] = None


class EggStorageSchema(BaseModel):
    model_config = {"from_attributes": True}
    arrival_date: date
    eggs_received: int = Field(default=0, ge=0)
    storage_temp_c: Optional[float] = None
    storage_humidity_pct: Optional[float] = None
    storage_start_date: Optional[date] = None
    storage_end_date: Optional[date] = None
    transport_temp_c: Optional[float] = None
    transport_duration_min: Optional[int] = None
    lot_id: Optional[int] = None
    notes: Optional[str] = None


class HatcheryParamsSchema(BaseModel):
    model_config = {"from_attributes": True}
    hatchery_id: Optional[int] = None
    incubator_id: Optional[int] = None
    hatcher_id: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[float] = None
    turning: Optional[bool] = None
    quantity_loaded: Optional[int] = None
    quantity_transferred: Optional[int] = None


class InspectionDetailSchema(BaseModel):
    model_config = {"from_attributes": True}
    house_id: Optional[int] = None  # Scopes record to a specific house; NULL = farm-level
    parameter: str
    value: Optional[str] = None
    value_numeric: Optional[float] = None  # Numeric counterpart for aggregations (T°, H%, etc.)
    status: Optional[str] = None


# ============================================================
# OperationalEvent Schemas
# ============================================================

class OperationalEventBase(BaseModel):
    lot_id: Optional[int] = None
    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    event_type: str
    event_date: date = Field(default_factory=date.today)
    observations: Optional[str] = None
    sap_document_ref: Optional[str] = None
    # Operation-specific catalog references
    supplier_id: Optional[int] = None
    cause_id: Optional[int] = None
    cull_cause_id: Optional[int] = None
    vaccine_id: Optional[int] = None
    vaccination_route: Optional[str] = None
    vaccine_lot_number: Optional[str] = None
    medication_id: Optional[int] = None
    dosage_per_bird: Optional[float] = None
    treatment_days: Optional[int] = None
    destination_farm_id: Optional[int] = None
    destination_plant_id: Optional[int] = None
    transport_id: Optional[int] = None
    sample_size: Optional[int] = None
    extra_data: Optional[dict] = None
    #: `GA-REM-021-A` · `B05`: litros del día; obligatorio en `water_consumption`, prohibido en el resto.
    water_liters: Optional[float] = None
    idempotency_key: Optional[str] = None  # Client-generated UUID to prevent duplicate submissions


# Submovimientos: viajan en el mismo cuerpo pero no son columnas del evento.
SUBMOVEMENT_FIELDS: frozenset[str] = frozenset({
    "bird_movements",
    "egg_movements",
    "feed_movements",
    "hatchery_params",
    "inspection_details",
    "egg_storage_records",
})

# Campos que identifican el envío y no pueden cambiar una vez creado el evento:
# alterar el tipo invalidaría las reglas que se le aplicaron al registrarlo, y la clave
# de idempotencia identifica el envío original (BR-12).
IMMUTABLE_AFTER_CREATE: frozenset[str] = frozenset({"event_type", "idempotency_key"})


class OperationalEventCreate(OperationalEventBase):
    bird_movements: list[BirdMovementSchema] = []
    egg_movements: list[EggMovementSchema] = []
    feed_movements: list[FeedMovementSchema] = []
    hatchery_params: list[HatcheryParamsSchema] = []
    inspection_details: list[InspectionDetailSchema] = []
    egg_storage_records: list[EggStorageSchema] = []


class OperationalEventUpdate(BaseModel):
    """Edición del evento antes de enviarlo a revisión.

    Admite los mismos campos operativos que la creación (`R-34`): hasta ahora solo dejaba
    tocar `event_date` y `observations`, de modo que un operador que erraba la vacuna tenía
    que cancelar y volver a registrar, pese a que `docs/12 §3` le reconoce la edición
    mientras el registro no ha salido de sus manos.

    Dos ausencias son deliberadas:

    * **`status`**. El estado solo cambia por las transiciones del flujo. Aceptarlo aquí
      permitía aprobar un evento con un `PUT`, sin revisión, sin segregación y sin dejar
      aprobador (`R-32`).
    * **`event_type` e `idempotency_key`**. Cambiar el tipo invalidaría las reglas que se
      aplicaron al registrar; la clave identifica el envío original (`BR-12`).

    Las restricciones de estado que hacen cumplir `BR-15`, `BR-16` y `RR-01` viven en
    `update_event` y no se relajan: solo se edita en `DRAFT`, `REGISTERED` y `RETURNED`.

    `extra="forbid"` es la diferencia entre rechazar y descartar en silencio: quien envíe
    `status` recibe un 422 explícito, no un 200 que no hizo nada. Es la clase de fallo de
    `P0-13` y `P0-14`, y aquí se cierra por contrato.

    El conjunto de campos se mantiene alineado con `OperationalEventBase` mediante
    `test_p014_persistence.py::test_update_cubre_el_contrato_operativo`.
    """

    model_config = {"extra": "forbid"}

    lot_id: Optional[int] = None
    farm_id: Optional[int] = None
    house_id: Optional[int] = None
    event_date: Optional[date] = None
    observations: Optional[str] = None
    sap_document_ref: Optional[str] = None
    supplier_id: Optional[int] = None
    cause_id: Optional[int] = None
    cull_cause_id: Optional[int] = None
    vaccine_id: Optional[int] = None
    vaccination_route: Optional[str] = None
    vaccine_lot_number: Optional[str] = None
    medication_id: Optional[int] = None
    dosage_per_bird: Optional[float] = None
    treatment_days: Optional[int] = None
    destination_farm_id: Optional[int] = None
    destination_plant_id: Optional[int] = None
    transport_id: Optional[int] = None
    sample_size: Optional[int] = None
    extra_data: Optional[dict] = None
    #: `GA-REM-021-A`: editable y **corregible** (`campos_corregibles` deriva de este contrato).
    water_liters: Optional[float] = None


class OperationalEventRead(OperationalEventBase):
    id: int
    company_id: int
    status: str
    version: int
    registered_by_id: int
    reviewed_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class EvidenceRead(BaseModel):
    id: int
    event_id: int
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    evidence_type: str
    description: Optional[str] = None
    uploaded_by_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class OperationalAlertRead(BaseModel):
    id: int
    company_id: int
    lot_id: int
    event_id: Optional[int] = None
    alert_type: str
    severity: str
    message: str
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class OperationalEventDetailRead(OperationalEventRead):
    bird_movements: list[BirdMovementSchema] = []
    egg_movements: list[EggMovementSchema] = []
    feed_movements: list[FeedMovementSchema] = []
    hatchery_params: list[HatcheryParamsSchema] = []
    inspection_details: list[InspectionDetailSchema] = []
    egg_storage_records: list[EggStorageSchema] = []
    evidences: list[EvidenceRead] = []


# ============================================================
# List of all event types for documentation/reference
# ============================================================

ALL_EVENT_TYPES = [
    {"type": "bird_reception", "label": "Recepción de Aves"},
    {"type": "bird_distribution", "label": "Distribución de Aves"},
    {"type": "bird_transfer", "label": "Transferencia de Aves"},
    {"type": "bird_exit", "label": "Salida de Aves"},
    {"type": "feed_registration", "label": "Registro de Alimento"},
    {"type": "weight_recording", "label": "Registro de Pesaje"},
    {"type": "mortality_recording", "label": "Registro de Mortalidad"},
    {"type": "cull_recording", "label": "Registro de Descarte"},
    {"type": "vaccination", "label": "Vacunación"},
    {"type": "medication", "label": "Medicación"},
    {"type": "farm_inspection", "label": "Inspección de Granja"},
    {"type": "transport_inspection", "label": "Inspección de Transporte"},
    {"type": "hatchery_inspection", "label": "Inspección de Incubadora"},
    {"type": "egg_collection", "label": "Recolección de Huevos"},
    {"type": "egg_classification", "label": "Clasificación de Huevos"},
    {"type": "egg_reception_classification", "label": "Clasificación de Huevos Recibidos (Incubadora)"},
    {"type": "egg_dispatch", "label": "Despacho de Huevos"},
    {"type": "egg_reception_hatchery", "label": "Recepción de Huevos (Incubadora)"},
    {"type": "incubation_load", "label": "Carga de Incubación"},
    {"type": "ovoscopy", "label": "Ovoscopia"},
    {"type": "transfer_to_hatcher", "label": "Transferencia a Nacedora"},
    {"type": "birth_registration", "label": "Registro de Nacimiento"},
    {"type": "chick_dispatch", "label": "Despacho de Pollitos"},
    {"type": "lot_closure", "label": "Cierre de Lote"},
    {"type": "grandparent_import", "label": "Importación de Abuelas"},
]


# ============================================================
# Evaluación de peso contra la curva estándar · `GA-REM-037` enmienda A · `R-97`
# ============================================================

class WeightEvaluationRow(BaseModel):
    """Un peso juzgado contra el rango que le corresponde por edad."""
    avg_weight: float
    #: `below_standard` · `within_standard` · `above_standard` · `no_reference`
    status: str
    #: `None` cuando no hay referencia. **No** es cero: cero sería un rango de verdad.
    expected_min: Optional[float] = None
    expected_target: Optional[float] = None
    expected_max: Optional[float] = None


class WeightEvaluationRead(BaseModel):
    """Lo que el motor de curva concluyó sobre los pesos de un evento.

    `AC26`. Existe porque el cálculo no era observable: su único consumidor emitía alerta
    solo al salirse del rango, de modo que «dentro de norma» y «sin referencia» eran
    indistinguibles desde fuera. `reason` nombra por qué falta la referencia cuando falta.
    """
    event_id: int
    lot_id: Optional[int] = None
    age_days: Optional[int] = None
    curve_version_label: Optional[str] = None
    reason: Optional[str] = None
    evaluations: list[WeightEvaluationRow] = []


class ClassificationRequest(BaseModel):
    """`GA-REM-040` fase 6. La cadena se elige por su **habilitación de empresa**.

    No por el catálogo global: así el destino queda atado a una empresa concreta y la
    combinación entre empresas no se puede ni escribir — el mismo criterio de `OD-09.d`.
    """

    model_config = {"extra": "forbid"}

    company_business_unit_id: int


class ReclassificationRequest(BaseModel):
    """`OD-10.d`. Corregir una atribución exige decir **por qué**.

    Un motivo vacío convierte la trazabilidad en un sello: quedaría constancia de que alguien
    cambió la cadena y ninguna de la razón, que es justo lo que hará falta el día que se
    revise.
    """

    model_config = {"extra": "forbid"}

    company_business_unit_id: int
    reason: str = Field(..., min_length=1)

    @field_validator("reason")
    @classmethod
    def _no_en_blanco(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("el motivo no puede estar en blanco")
        return v.strip()
