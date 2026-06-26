"""
Master data models for Global Avícola.
Companies, farms, houses, hatcheries, genetic lines, suppliers, etc.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


# ============================================================
# Enums
# ============================================================

class FarmType(str, enum.Enum):
    BREEDING = "breeding"
    PRODUCTION = "production"
    FATTENING = "fattening"
    MIXED = "mixed"


class HouseType(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    TUNNEL = "tunnel"


class BirdTypeEnum(str, enum.Enum):
    GRANDPARENT = "grandparent"
    BREEDER = "breeder"
    BROILER = "broiler"
    HATCHERY = "hatchery"


class SexEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    MIXED = "mixed"


class LotStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# ============================================================
# Core Entities
# ============================================================

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="USD")
    sap_config: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # JSON stored as text
    approval_levels: Mapped[int] = mapped_column(Integer, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farms: Mapped[list["Farm"]] = relationship("Farm", back_populates="company", lazy="selectin")
    hatcheries: Mapped[list["Hatchery"]] = relationship("Hatchery", back_populates="company", lazy="selectin")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    farm_type: Mapped[FarmType] = mapped_column(Enum(FarmType), default=FarmType.BREEDING)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship("Company", back_populates="farms")
    houses: Mapped[list["House"]] = relationship("House", back_populates="farm", lazy="selectin")
    lots: Mapped[list["Lot"]] = relationship("Lot", back_populates="farm", lazy="selectin")


class House(Base):
    __tablename__ = "houses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"))
    name: Mapped[str] = mapped_column(String(200))
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    house_type: Mapped[Optional[HouseType]] = mapped_column(Enum(HouseType), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm: Mapped["Farm"] = relationship("Farm", back_populates="houses")


class Hatchery(Base):
    __tablename__ = "hatcheries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship("Company", back_populates="hatcheries")
    incubators: Mapped[list["Incubator"]] = relationship("Incubator", back_populates="hatchery", lazy="selectin")
    hatchers: Mapped[list["Hatcher"]] = relationship("Hatcher", back_populates="hatchery", lazy="selectin")


class Incubator(Base):
    __tablename__ = "incubators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hatchery_id: Mapped[int] = mapped_column(Integer, ForeignKey("hatcheries.id"))
    name: Mapped[str] = mapped_column(String(200))
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hatchery: Mapped["Hatchery"] = relationship("Hatchery", back_populates="incubators")


class Hatcher(Base):
    __tablename__ = "hatchers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hatchery_id: Mapped[int] = mapped_column(Integer, ForeignKey("hatcheries.id"))
    name: Mapped[str] = mapped_column(String(200))
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hatchery: Mapped["Hatchery"] = relationship("Hatchery", back_populates="hatchers")


class GeneticLine(Base):
    __tablename__ = "genetic_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Breed(Base):
    __tablename__ = "breeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    genetic_line_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("genetic_lines.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    bird_type: Mapped[Optional[BirdTypeEnum]] = mapped_column(Enum(BirdTypeEnum), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    genetic_line: Mapped[Optional["GeneticLine"]] = relationship("GeneticLine", lazy="selectin")


class ProductivePhase(Base):
    __tablename__ = "productive_phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# Lot (Placeholder for FK references)
# ============================================================

class Lot(Base):
    """Minimal Lot model for FK references. Full model in lots module."""
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    farm_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("farms.id"), nullable=True)
    house_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("houses.id"), nullable=True)
    genetic_line_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("genetic_lines.id"), nullable=True)
    breed_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("breeds.id"), nullable=True)
    lot_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    bird_type: Mapped[Optional[BirdTypeEnum]] = mapped_column(Enum(BirdTypeEnum), nullable=True)
    sex: Mapped[Optional[SexEnum]] = mapped_column(Enum(SexEnum), nullable=True)
    status: Mapped[LotStatus] = mapped_column(Enum(LotStatus), default=LotStatus.ACTIVE)
    activation_type: Mapped[Optional[str]] = mapped_column(String(50), default="normal")
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farm: Mapped[Optional["Farm"]] = relationship("Farm", back_populates="lots")
    phases: Mapped[list["LotPhase"]] = relationship("LotPhase", back_populates="lot", lazy="selectin")
    opening_balance: Mapped[Optional["OpeningBalance"]] = relationship("OpeningBalance", back_populates="lot", uselist=False, lazy="selectin")


# ============================================================
# Catalogs (Suppliers, Feed Types, Vaccines, etc.)
# ============================================================

class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    sap_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supplier_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeedType(Base):
    __tablename__ = "feed_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    presentation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Vaccine(Base):
    __tablename__ = "vaccines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    laboratory: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vaccine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    standard_dosage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    application_route: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    laboratory: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    presentation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MortalityCause(Base):
    __tablename__ = "mortality_causes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CullCause(Base):
    __tablename__ = "cull_causes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Transport(Base):
    __tablename__ = "transports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    plate: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transport_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessingPlant(Base):
    __tablename__ = "processing_plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RejectionReason(Base):
    __tablename__ = "rejection_reasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CorrectionType(Base):
    __tablename__ = "correction_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
