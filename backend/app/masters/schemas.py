"""
Pydantic schemas for master data entities.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================
# Company
# ============================================================

class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tax_id: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = "USD"
    sap_config: Optional[dict] = None
    approval_levels: int = Field(default=2, ge=1, le=3)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    sap_config: Optional[dict] = None
    approval_levels: Optional[int] = None
    is_active: Optional[bool] = None


class CompanyRead(CompanyBase):
    id: int
    is_active: bool
    sap_config: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# Farm
# ============================================================

class FarmBase(BaseModel):
    company_id: int
    name: str = Field(..., min_length=1, max_length=200)
    code: Optional[str] = None
    location: Optional[str] = None
    farm_type: Optional[str] = "breeding"


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    location: Optional[str] = None
    farm_type: Optional[str] = None
    is_active: Optional[bool] = None


class FarmRead(FarmBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# House
# ============================================================

class HouseBase(BaseModel):
    farm_id: int
    name: str = Field(..., min_length=1, max_length=200)
    capacity: Optional[int] = None
    house_type: Optional[str] = None


class HouseCreate(HouseBase):
    pass


class HouseUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    house_type: Optional[str] = None
    is_active: Optional[bool] = None


class HouseRead(HouseBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# Hatchery, Incubator, Hatcher
# ============================================================

class HatcheryBase(BaseModel):
    company_id: int
    name: str = Field(..., min_length=1, max_length=200)
    code: Optional[str] = None
    location: Optional[str] = None


class HatcheryCreate(HatcheryBase):
    pass


class HatcheryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class HatcheryRead(HatcheryBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class IncubatorBase(BaseModel):
    hatchery_id: int
    name: str = Field(..., min_length=1, max_length=200)
    capacity: Optional[int] = None


class IncubatorCreate(IncubatorBase):
    pass


class IncubatorRead(IncubatorBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class HatcherBase(BaseModel):
    hatchery_id: int
    name: str = Field(..., min_length=1, max_length=200)
    capacity: Optional[int] = None


class HatcherCreate(HatcherBase):
    pass


class HatcherRead(HatcherBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# Genetic Line & Breed & Productive Phase
# ============================================================

class GeneticLineBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    code: Optional[str] = None
    supplier: Optional[str] = None
    description: Optional[str] = None


class GeneticLineCreate(GeneticLineBase):
    pass


class GeneticLineRead(GeneticLineBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BreedBase(BaseModel):
    genetic_line_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    bird_type: Optional[str] = None
    description: Optional[str] = None


class BreedCreate(BreedBase):
    pass


class BreedRead(BreedBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ProductivePhaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = None
    order: Optional[int] = None
    duration_days: Optional[int] = None
    is_initial: bool = False
    is_final: bool = False


class ProductivePhaseCreate(ProductivePhaseBase):
    pass


class ProductivePhaseRead(ProductivePhaseBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# Catalogs (Supplier, FeedType, Vaccine, etc.)
# ============================================================

class SupplierBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    sap_code: Optional[str] = None
    country: Optional[str] = None
    supplier_type: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class FeedTypeBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    code: Optional[str] = None
    presentation: Optional[str] = None


class FeedTypeCreate(FeedTypeBase):
    pass


class FeedTypeRead(FeedTypeBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class VaccineBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    laboratory: Optional[str] = None
    vaccine_type: Optional[str] = None
    standard_dosage: Optional[str] = None
    application_route: Optional[str] = None


class VaccineCreate(VaccineBase):
    pass


class VaccineRead(VaccineBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class MedicationBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    laboratory: Optional[str] = None
    presentation: Optional[str] = None


class MedicationCreate(MedicationBase):
    pass


class MedicationRead(MedicationBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class MortalityCauseBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None


class MortalityCauseCreate(MortalityCauseBase):
    pass


class MortalityCauseRead(MortalityCauseBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class CullCauseBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None


class CullCauseCreate(CullCauseBase):
    pass


class CullCauseRead(CullCauseBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class TransportBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    plate: Optional[str] = None
    transport_type: Optional[str] = None
    capacity: Optional[int] = None


class TransportCreate(TransportBase):
    pass


class TransportRead(TransportBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ProcessingPlantBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = None


class ProcessingPlantCreate(ProcessingPlantBase):
    pass


class ProcessingPlantRead(ProcessingPlantBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class RejectionReasonBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None


class RejectionReasonCreate(RejectionReasonBase):
    pass


class RejectionReasonRead(RejectionReasonBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class CorrectionTypeBase(BaseModel):
    company_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class CorrectionTypeCreate(CorrectionTypeBase):
    pass


class CorrectionTypeRead(CorrectionTypeBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# GA-REM-011 C-17 — Esquemas de actualización de catálogos maestros
# ============================================================
# El frontend ofrece 'Editar' en 12 catálogos y el backend solo había
# registrado PUT para 4, devolviendo 405 en las otras 8 pantallas.

class SupplierUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    company_id: Optional[Any] = None
    name: Optional[Any] = None
    sap_code: Optional[Any] = None
    country: Optional[Any] = None
    supplier_type: Optional[Any] = None
    is_active: Optional[bool] = None


class GeneticLineUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    company_id: Optional[Any] = None
    name: Optional[Any] = None
    code: Optional[Any] = None
    supplier: Optional[Any] = None
    description: Optional[Any] = None
    is_active: Optional[bool] = None


class BreedUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    genetic_line_id: Optional[Any] = None
    name: Optional[Any] = None
    bird_type: Optional[Any] = None
    description: Optional[Any] = None
    is_active: Optional[bool] = None


class FeedTypeUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    company_id: Optional[Any] = None
    name: Optional[Any] = None
    code: Optional[Any] = None
    presentation: Optional[Any] = None
    is_active: Optional[bool] = None


class VaccineUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    company_id: Optional[Any] = None
    name: Optional[Any] = None
    laboratory: Optional[Any] = None
    vaccine_type: Optional[Any] = None
    standard_dosage: Optional[Any] = None
    application_route: Optional[Any] = None
    is_active: Optional[bool] = None


class MortalityCauseUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    company_id: Optional[Any] = None
    name: Optional[Any] = None
    category: Optional[Any] = None
    is_active: Optional[bool] = None


class TransportUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    company_id: Optional[Any] = None
    name: Optional[Any] = None
    plate: Optional[Any] = None
    transport_type: Optional[Any] = None
    capacity: Optional[Any] = None
    is_active: Optional[bool] = None


class ProcessingPlantUpdate(BaseModel):
    """GA-REM-011 C-17: la UI ofrece editar este catálogo; faltaba el método PUT."""
    company_id: Optional[Any] = None
    name: Optional[Any] = None
    location: Optional[Any] = None
    is_active: Optional[bool] = None


# ============================================================
# Esquemas de actualización — `GA-REM-033 AC05` / `R-91`
# ============================================================
#
# `register_crud` registra la ruta `PUT` **solo si se le pasa un esquema de actualización**.
# Estos siete maestros pasaban `None`, de modo que respondían `405`: podían crearse y darse
# de baja, pero no corregirse. Una errata obligaba a duplicar el registro.
#
# Ninguno expone `company_id`, `hatchery_id` ni `id`: `UPDATE_SCHEMA_SECURITY_MATRIX` los
# clasifica como `ADMIN_ONLY` o estructurales, y mover un maestro de empresa —o de planta—
# por la puerta de la edición es la escritura entre inquilinos que `R-42` y `R-59`
# describieron. Cambiar de padre es un traslado, no una corrección de datos.


class IncubatorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


class HatcherUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


class ProductivePhaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    order: Optional[int] = None
    duration_days: Optional[int] = None
    is_initial: Optional[bool] = None
    is_final: Optional[bool] = None
    is_active: Optional[bool] = None


class MedicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    laboratory: Optional[str] = None
    presentation: Optional[str] = None
    is_active: Optional[bool] = None


class CullCauseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    is_active: Optional[bool] = None


class RejectionReasonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class CorrectionTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================
# Curvas estándar de peso por línea genética · `GA-REM-037` / `OD-06`
# ============================================================

class WeightCurvePointIn(BaseModel):
    """Una fila de la tabla del proveedor.

    `target_weight` es opcional porque no todas las tablas publican el peso objetivo; el
    rango sí es obligatorio, porque sin él no hay nada contra lo que juzgar un pesaje.
    """
    age_days: int = Field(..., ge=0)
    min_weight: float = Field(..., gt=0)
    max_weight: float = Field(..., gt=0)
    target_weight: Optional[float] = Field(default=None, gt=0)


class WeightCurvePointRead(BaseModel):
    id: int
    age_days: int
    min_weight: float
    max_weight: float
    target_weight: Optional[float] = None
    model_config = {"from_attributes": True}


class WeightCurveCreate(BaseModel):
    """Alta de una versión de curva junto con su tabla completa.

    La tabla viaja en el alta y no por endpoint aparte a propósito: `AC06` exige que una
    tabla inválida no deje **nada** persistido, y una versión vacía a la espera de puntos
    sería exactamente ese residuo.
    """
    genetic_line_id: int
    # Ver `GeneticWeightCurve.version_label`: es la etiqueta que publica el proveedor, no
    # un contador del servidor.
    version_label: str = Field(..., min_length=1, max_length=50)
    source: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = False
    points: list[WeightCurvePointIn] = Field(..., min_length=1)


class WeightCurveRead(BaseModel):
    id: int
    genetic_line_id: int
    version_label: str
    is_active: bool
    source: Optional[str] = None
    created_at: datetime
    points: list[WeightCurvePointRead] = []
    model_config = {"from_attributes": True}


class WeightCurveActivate(BaseModel):
    is_active: bool
