"""Pydantic schemas for operational events and movements."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# Movement Schemas
# ============================================================

class BirdMovementSchema(BaseModel):
    sex: Optional[str] = None
    quantity: int = Field(default=0, ge=0)
    avg_weight: Optional[float] = None
    week_number: Optional[int] = None
    breed_id: Optional[int] = None
    source_house_id: Optional[int] = None
    target_house_id: Optional[int] = None


class EggMovementSchema(BaseModel):
    egg_type: str  # fertile, dirty, broken, infertile, discarded, commercial
    quantity: int = Field(default=0, ge=0)
    avg_weight: Optional[float] = None
    classification_date: Optional[date] = None
    storage_start_date: Optional[date] = None
    storage_temp_c: Optional[float] = None
    storage_humidity_pct: Optional[float] = None


class FeedMovementSchema(BaseModel):
    feed_type_id: Optional[int] = None
    quantity_kg: float = Field(default=0.0, gt=0)
    sacks_count: Optional[int] = None
    week_number: Optional[int] = None
    sap_order_id: Optional[str] = None


class EggStorageSchema(BaseModel):
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
    house_id: Optional[int] = None  # Scopes record to a specific house; NULL = farm-level
    parameter: str
    value: Optional[str] = None
    status: Optional[str] = None


# ============================================================
# OperationalEvent Schemas
# ============================================================

class OperationalEventBase(BaseModel):
    lot_id: int
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


class OperationalEventCreate(OperationalEventBase):
    bird_movements: list[BirdMovementSchema] = []
    egg_movements: list[EggMovementSchema] = []
    feed_movements: list[FeedMovementSchema] = []
    hatchery_params: list[HatcheryParamsSchema] = []
    inspection_details: list[InspectionDetailSchema] = []
    egg_storage_records: list[EggStorageSchema] = []


class OperationalEventUpdate(BaseModel):
    event_date: Optional[date] = None
    observations: Optional[str] = None
    status: Optional[str] = None


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
