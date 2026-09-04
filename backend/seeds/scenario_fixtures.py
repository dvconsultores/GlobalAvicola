"""Fixtures de escenario deterministas. Entregable de `GA-REM-025` (`AC06`, `AC10`, `AC14`).

Sustituye a la práctica anterior: que un test diese por supuesto que en la base compartida
ya existía «el lote 123» o «la granja demo». Eso no probaba el código, probaba que nadie
hubiera borrado el registro.

Aquí cada escenario **crea sus propias precondiciones** y puede retirarlas después.

Ciclo de vida (encargo §48). Cada escenario declara el suyo:

    EPHEMERAL              se crea y se destruye dentro de la prueba
    REUSABLE_FIXTURE       se conserva mientras dure una campaña de certificación
    MANUAL_TEST_TEMPORARY  lo pide una persona para probar a mano; caducable

Todo lo que se crea aquí lleva el prefijo `FX-`, de modo que cualquier registro del
entorno compartido puede identificarse como dato de prueba de un vistazo.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.models import Role, User
from app.auth.security import hash_password
from app.lots.models import LotPhase
from app.masters.models import Breed, Company, Farm, GeneticLine, House, Lot, ProductivePhase

#: Prefijo obligatorio de todo registro creado por un fixture.
PREFIJO = "FX-"


def password_fixture() -> str:
    """Contraseña de los usuarios de fixture.

    No es literal (`GA-REM-004` §54): se toma del entorno o se genera por ejecución. Los
    usuarios que la llevan se crean y se retiran dentro de la propia prueba, así que no
    hay nada que recordar entre ejecuciones.
    """
    return os.environ.get("GA_FIXTURE_PASSWORD") or secrets.token_urlsafe(16)


class CicloDeVida(str, Enum):
    EPHEMERAL = "EPHEMERAL"
    REUSABLE_FIXTURE = "REUSABLE_FIXTURE"
    MANUAL_TEST_TEMPORARY = "MANUAL_TEST_TEMPORARY"


@dataclass
class ContextoTenant:
    """Un tenant completo y utilizable: empresa, granja, galpón, lote y usuario."""

    company_id: int
    farm_id: int
    house_id: int
    lot_id: int
    user_id: int
    etiqueta: str

    @property
    def lot_code(self) -> str:
        return f"{PREFIJO}{self.etiqueta}-LOTE-01"


async def _obtener_o_crear(session: AsyncSession, modelo, filtro, **campos):
    fila = (await session.execute(select(modelo).where(filtro))).scalar_one_or_none()
    if fila is None:
        fila = modelo(**campos)
        session.add(fila)
        await session.flush()
    return fila


async def crear_tenant(
    session: AsyncSession,
    etiqueta: str,
    *,
    rol: str = "Operador de Granja",
    ciclo: CicloDeVida = CicloDeVida.EPHEMERAL,
    password: str | None = None,
) -> ContextoTenant:
    """Crea un tenant completo y determinista. Idempotente por `etiqueta`.

    `etiqueta` debe ser corta y única en la prueba: `A`, `B`, `AISLAMIENTO`…
    """
    password = password or password_fixture()
    nombre_empresa = f"{PREFIJO}COMPANY-{etiqueta}"
    empresa = await _obtener_o_crear(
        session, Company, Company.name == nombre_empresa,
        name=nombre_empresa, tax_id=f"{PREFIJO}{etiqueta}-TAXID",
        country="Test", currency="USD",
    )

    granja = await _obtener_o_crear(
        session, Farm, Farm.name == f"{PREFIJO}{etiqueta}-GRANJA",
        company_id=empresa.id, name=f"{PREFIJO}{etiqueta}-GRANJA",
        code=f"{PREFIJO}{etiqueta}-G1", location="Escenario de prueba",
    )

    galpon = await _obtener_o_crear(
        session, House, House.name == f"{PREFIJO}{etiqueta}-GALPON",
        farm_id=granja.id, name=f"{PREFIJO}{etiqueta}-GALPON", capacity=10_000,
    )

    linea = await _obtener_o_crear(
        session, GeneticLine, GeneticLine.name == f"{PREFIJO}{etiqueta}-LINEA",
        company_id=empresa.id, name=f"{PREFIJO}{etiqueta}-LINEA", code=f"{PREFIJO}{etiqueta}-L1",
    )
    raza = await _obtener_o_crear(
        session, Breed, Breed.name == f"{PREFIJO}{etiqueta}-RAZA",
        genetic_line_id=linea.id, name=f"{PREFIJO}{etiqueta}-RAZA",
    )

    codigo = f"{PREFIJO}{etiqueta}-LOTE-01"
    lote = await _obtener_o_crear(
        session, Lot, Lot.lot_code == codigo,
        company_id=empresa.id, farm_id=granja.id, house_id=galpon.id,
        genetic_line_id=linea.id, breed_id=raza.id, lot_code=codigo,
        start_date=datetime.now(timezone.utc),
    )

    fase = (
        await session.execute(select(ProductivePhase).where(ProductivePhase.is_initial.is_(True)))
    ).scalars().first()
    if fase is not None:
        await _obtener_o_crear(
            session, LotPhase, LotPhase.lot_id == lote.id,
            lot_id=lote.id, phase_id=fase.id, start_date=date.today(),
            start_population_male=5_000, start_population_female=5_000,
        )

    rol_fila = (await session.execute(select(Role).where(Role.name == rol))).scalar_one_or_none()
    usuario_nombre = f"{PREFIJO}{etiqueta}-user".lower()
    usuario = await _obtener_o_crear(
        session, User, User.username == usuario_nombre,
        first_name="Fixture", last_name=etiqueta,
        email=f"{usuario_nombre}@fixtures.globalavicola.com", username=usuario_nombre,
        hashed_password=hash_password(password),
        role_id=rol_fila.id if rol_fila else None,
        company_id=empresa.id, view_type="web",
    )

    await session.flush()
    return ContextoTenant(
        company_id=empresa.id, farm_id=granja.id, house_id=galpon.id,
        lot_id=lote.id, user_id=usuario.id, etiqueta=etiqueta,
    )


async def crear_par_multitenant(session: AsyncSession) -> tuple[ContextoTenant, ContextoTenant]:
    """Dos tenants aislados. Base de las regresiones `R-42`, `R-48`, `R-54` y `R-59`.

    Que los cree la prueba, y no un seed permanente, es justamente lo que hace que la
    prueba de aislamiento signifique algo: los identificadores son nuevos y no pueden
    coincidir por casualidad con datos que alguien dejó ahí.
    """
    return await crear_tenant(session, "A"), await crear_tenant(session, "B")


async def retirar_fixtures(session: AsyncSession) -> int:
    """Elimina todo lo creado por fixtures. Orden inverso al de dependencias."""
    borradas = 0
    for modelo, columna in (
        (LotPhase, None), (Lot, Lot.lot_code), (Breed, Breed.name),
        (GeneticLine, GeneticLine.name), (House, House.name), (Farm, Farm.name),
        (User, User.username), (Company, Company.name),
    ):
        if columna is None:
            codigos = (
                await session.execute(select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))
            ).scalars().all()
            if codigos:
                resultado = await session.execute(delete(LotPhase).where(LotPhase.lot_id.in_(codigos)))
                borradas += resultado.rowcount or 0
            continue
        patron = PREFIJO.lower() if modelo is User else PREFIJO
        resultado = await session.execute(delete(modelo).where(columna.like(f"{patron}%")))
        borradas += resultado.rowcount or 0
    await session.commit()
    return borradas
