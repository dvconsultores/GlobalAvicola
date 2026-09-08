"""Las tres tablas del fundamento — `GA-REM-040 §6`.

    business_units           qué unidades existen EN EL PRODUCTO
    company_business_units   cuáles tiene HABILITADAS una empresa
    user_business_units      cuáles se le han CONCEDIDO a un usuario

Separar las tres no es ceremonia. El catálogo no puede depender de una empresa —si lo hiciera,
cada cliente inventaría sus propias unidades y el producto dejaría de saber qué es una
incubadora—; y la habilitación no puede confundirse con la concesión, porque son decisiones de
personas distintas: una es comercial y la otra operativa.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class BusinessUnit(Base):
    """El catálogo de plataforma. Cuatro filas, y **ninguna empresa las crea**.

    `GA-REM-034` permite que una empresa cree roles, pero no unidades: una unidad de negocio
    es una capacidad conocida del producto, con procesos certificados detrás. Por eso este
    catálogo se siembra y no tiene `CRUD` de cliente.

    **`bird_type` es una correspondencia registrada, no la autoridad.** El acceso lo deciden
    estas tres tablas; el enum de dominio solo dice qué lote pertenece a qué cadena. La
    dirección importa: si mandara el enum, cambiar un valor de dominio cambiaría quién ve qué.
    """

    __tablename__ = "business_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #: Identificador estable. Es el que usarán los filtros de fases posteriores.
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    #: Clave de traducción, no una traducción. El producto habla dos lenguas.
    name_key: Mapped[str] = mapped_column(String(100))
    #: Correspondencia con `BirdTypeEnum`. Nulable: una unidad futura podría no tenerla.
    bird_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    #: Disponibilidad de plataforma. Retirar una unidad del producto no borra su historia.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<BusinessUnit {self.code}>"


class CompanyBusinessUnit(Base):
    """Qué unidades tiene habilitadas una empresa. Decisión comercial.

    `is_enabled` es un campo y no la ausencia de la fila **a propósito**: apagar una unidad
    tiene que ser distinguible de no haberla configurado nunca, y tiene que poder deshacerse
    sin perder cuándo se decidió.
    """

    __tablename__ = "company_business_units"
    __table_args__ = (
        # Dos filas para el mismo par harían que «habilitada» dependiese de cuál se leyera.
        UniqueConstraint("company_id", "business_unit_id", name="uq_company_business_unit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id"), index=True
    )
    business_unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_units.id"), index=True
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return (f"<CompanyBusinessUnit company={self.company_id} "
                f"unit={self.business_unit_id} enabled={self.is_enabled}>")


class UserBusinessUnit(Base):
    """Qué unidades se le han concedido a un usuario. Decisión operativa.

    **Apunta al catálogo, no a la habilitación de una empresa.** Es deliberado: si apuntara a
    `company_business_units`, se podría escribir la fila inválida «usuario de la empresa A
    sobre la habilitación de la empresa B», y habría que prohibirla con una validación. Al
    apuntar al catálogo esa combinación **no se puede ni expresar**, y la empresa del usuario
    sigue siendo la única fuente de a qué inquilino pertenece.

    Sin `company_id` propio por la misma razón: duplicarlo aquí crearía una segunda fuente que
    quedaría obsoleta el día que alguien mueva un usuario de empresa.

    Y **no hay borrado en cascada desde la habilitación de empresa**: `BU-D10` sigue pendiente
    de ratificación, de modo que apagar una unidad no puede destruir concesiones que el
    propietario quizá quiera conservar. La concesión sobrevive; simplemente deja de ser
    efectiva.
    """

    __tablename__ = "user_business_units"
    __table_args__ = (
        UniqueConstraint("user_id", "business_unit_id", name="uq_user_business_unit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    business_unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_units.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<UserBusinessUnit user={self.user_id} unit={self.business_unit_id}>"
