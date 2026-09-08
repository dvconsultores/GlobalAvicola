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
    """Qué unidades le ha concedido **su empresa** a un usuario. Decisión operativa.

    **Apunta a la habilitación de una empresa concreta, no al catálogo** — `OD-09.d`. Una
    concesión no dice «este usuario puede ver reproductora»: dice «la empresa A le concedió
    reproductora **dentro de A**». La fila responde por sí sola a de quién viene, sin que
    haya que deducirlo de dónde esté hoy el usuario.

    La fase 1 lo hizo al revés —apuntaba al catálogo— por una razón que parecía buena:
    apuntando a la habilitación se podía escribir «usuario de A sobre habilitación de B», y
    apuntando al catálogo esa fila no se podía ni expresar. El error fue tratar **una**
    combinación inválida como si fueran todas: al quitar la empresa desapareció la fila
    imposible y, con ella, lo que distingue un contexto de otro. `breeder` de A y `breeder` de
    B pasaban a ser indistinguibles, y una concesión viajaba con el usuario al cambiar de
    empresa.

    Ahora la combinación entre empresas vuelve a ser representable, y se cierra por los dos
    lados: `conceder_unidad` la rechaza al escribir, y el resolutor exige al leer que la
    empresa de la habilitación sea la **actual** del usuario. Las dos hacen falta — la primera
    sola dejaría efectiva una concesión legítima de ayer cuando el usuario se mueve hoy.

    Sin borrado en cascada. `BU-D10` sigue pendiente de ratificación, y una concesión de una
    empresa anterior es **historia**: pierde la efectividad, no la existencia.
    """

    __tablename__ = "user_business_units"
    __table_args__ = (
        UniqueConstraint("user_id", "company_business_unit_id",
                         name="uq_user_company_business_unit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    company_business_unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("company_business_units.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<UserBusinessUnit user={self.user_id} cbu={self.company_business_unit_id}>"
