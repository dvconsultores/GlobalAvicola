"""
Pydantic schemas for master data entities.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# Company
# ============================================================

class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tax_id: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = "USD"
    approval_levels: int = Field(default=2, ge=1, le=3)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    approval_levels: Optional[int] = None
    is_active: Optional[bool] = None


class CompanyRead(CompanyBase):
    id: int
    is_active: bool
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
