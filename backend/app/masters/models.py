"""
Master data models for Global Avícola.
Companies, farms, houses, hatcheries, genetic lines, suppliers, etc.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func,
)
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


class Area(Base):
    """Área funcional de la empresa — `GA-REM-039`, decisión `OD-08`.

    **Dónde pertenece** un usuario, que es distinto de **qué puede hacer**: eso lo dice su rol.
    Con dos supervisores de áreas distintas, deducir el área del nombre del rol haría que cada
    uno recibiera los avisos del otro.

    No se guarda aquí el gerente. Tenerlo en `Area.manager_user_id` **y** poder deducirlo del
    rol crearía dos fuentes que acabarían discrepando: la pertenencia vive en `User.area_id` y
    la capacidad en el rol.
    """

    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    #: Baja lógica. Un área con usuarios, lotes o avisos históricos no se borra.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())


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


class GeneticWeightCurve(Base):
    """Una versión de la curva estándar de peso de una línea genética.

    `GA-REM-037` / `OD-06`. Versionada a propósito: una curva nueva **no** puede cambiar la
    referencia de los lotes existentes, o se destruiría la trazabilidad histórica. El lote
    guarda la versión con la que nació (`Lot.weight_curve_id`) y la conserva.

    El alcance de inquilino lo hereda de la línea, igual que `Incubator` de `Hatchery`.
    """
    __tablename__ = "genetic_weight_curves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    genetic_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("genetic_lines.id"), index=True)
    # `version_label` y no `version`: lo escribe el administrador —«2019», «rev. B»— y es
    # el identificador que el proveedor le da a su tabla publicada. `version` está
    # reservado en este proyecto para los campos que fija el servidor
    # (`UPDATE_SCHEMA_SECURITY_MATRIX`), y `R-32` barre los esquemas de escritura buscando
    # justamente ese nombre. Dos conceptos opuestos no pueden compartir palabra.
    version_label: Mapped[str] = mapped_column(String(50))
    #: Sirve de referencia por defecto para los lotes nuevos. Los ya asignados no se mueven.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    genetic_line: Mapped["GeneticLine"] = relationship("GeneticLine", lazy="selectin")
    points: Mapped[list["GeneticWeightCurvePoint"]] = relationship(
        "GeneticWeightCurvePoint", lazy="selectin",
        order_by="GeneticWeightCurvePoint.age_days", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("genetic_line_id", "version_label", name="uq_curve_line_version"),
    )


class GeneticWeightCurvePoint(Base):
    """Un punto de la curva: la edad y el rango esperado a esa edad.

    Los pesos van en **gramos**, la unidad canónica del sistema (`mean_weight_g`,
    `avg_weight_g`). `min_weight` y `max_weight` son la fuente de la alerta;
    `target_weight` es referencia y no decide nada.
    """
    __tablename__ = "genetic_weight_curve_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    curve_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("genetic_weight_curves.id", ondelete="CASCADE"), index=True)
    age_days: Mapped[int] = mapped_column(Integer)
    target_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_weight: Mapped[float] = mapped_column(Float)
    max_weight: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        #: Dos valores contradictorios para el mismo día harían la curva ambigua.
        UniqueConstraint("curve_id", "age_days", name="uq_curve_point_age"),
    )


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
    #: `GA-REM-037` / `OD-06`. La **versión concreta** de curva con la que se evalúa este
    #: lote, no la activa del momento: publicar una curva nueva no puede reescribir la
    #: referencia histórica de los lotes ya en marcha. Nulable porque hay lotes anteriores a
    #: esta capacidad y no se les inventa genética.
    weight_curve_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("genetic_weight_curves.id"), nullable=True)
    lot_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    bird_type: Mapped[Optional[BirdTypeEnum]] = mapped_column(Enum(BirdTypeEnum), nullable=True)
    # For hatchery-type lots: distinguishes grandparent-egg incubation (→ breeder chicks)
    # from breeder-egg incubation (→ broiler chicks). Values: "grandparent" | "breeder"
    hatchery_purpose: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sex: Mapped[Optional[SexEnum]] = mapped_column(Enum(SexEnum), nullable=True)
    status: Mapped[LotStatus] = mapped_column(Enum(LotStatus), default=LotStatus.ACTIVE)
    activation_type: Mapped[Optional[str]] = mapped_column(String(50), default="normal")
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    #: `GA-REM-038` enmienda B / `OD-08`. Cuándo se **prevé** cerrar, que no es `end_date`:
    #: aquélla es la fecha **real** y para cuando existe el lote ya cerró. Nulable porque hay
    #: lotes anteriores a esta spec y no hay fuente segura para completarlos.
    planned_close_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    #: `GA-REM-039`. El ámbito funcional del lote y, por él, el de sus eventos: es donde los
    #: seis avisos de `P-14` convergen para resolver gerente y supervisores.
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("areas.id"), nullable=True, index=True)
    # ── GA-REQ-061 · T14 (C1): NATIVE vs MIGRATED + provenance (el PK interno manda) ──
    origin: Mapped[str] = mapped_column(String(15), default="NATIVE")
    legacy_lot_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

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
