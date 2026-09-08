#!/usr/bin/env python
"""Cuentas temporales para la revisión integral de la aplicación.

    ADMINISTRADOR    Super Administrador · ve y administra todo
    OPERADOR MÓVIL   Operador de Granja · vista móvil · con las cuatro cadenas concedidas

No son cuentas definitivas. Antes de producción se vacía y se crean como corresponde;
esto existe para poder recorrer la aplicación de extremo a extremo mientras tanto.

    # ver el estado sin tocar nada
    PYTHONPATH=. python3 seeds/usuarios_de_revision.py --inventario

    # crear o actualizar las dos cuentas
    GA_REVIEW_PASSWORD='...' PYTHONPATH=. python3 seeds/usuarios_de_revision.py --crear

    # además, retirar las cuentas anteriores (reversible: solo las desactiva)
    GA_REVIEW_PASSWORD='...' PYTHONPATH=. python3 seeds/usuarios_de_revision.py --crear --retirar-anteriores

**La contraseña no se escribe aquí.** `GA-REM-004` retiró las credenciales literales del
repositorio y esa remediación está certificada; volver a ponerlas la desharía. Se lee del
entorno y no queda en ningún fichero versionado.

**Retirar no es borrar.** `--retirar-anteriores` pone `is_active = False`, que es lo que el
propio producto entiende por dar de baja una cuenta (`AuthService.deactivate_user`) y basta
para que nadie pueda entrar con ella: `get_current_user` rechaza al usuario inactivo. Borrar
las filas exigiría destruir además eventos, revisiones, aprobaciones, correcciones,
evidencias, notificaciones y registros `SAP` —once claves foráneas obligatorias apuntan a
`users`—, es decir, justo el dato que hace posible revisar la aplicación. Y contradiría el
criterio ya escrito en `GA-REM-025`: «las cuentas obsoletas se retiran con criterio, no en
bloque». Si de verdad se quiere partir de cero, la herramienta es
`scripts/environment_reset.py`, que tiene su propia guarda de cinco señales.

**Vive en `seeds/` y no en `scripts/` a propósito.** El `Dockerfile` copia `app/` y `seeds/`
a la imagen, y **no** `scripts/`: un fichero ahí no existiría dentro del contenedor
desplegado, que es justo donde hay que ejecutarlo.

**Configura la empresa, no solo las cuentas.** Desde `GA-REM-040` un usuario sin unidades de
negocio concedidas no ve dato productivo: es lo que `OD-09.c` decidió. Un operador recién
creado vería la aplicación vacía y parecería rota. Por eso esto habilita las cuatro cadenas a
la empresa y se las concede al operador, por el camino de escritura sancionado.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy import select, update  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

# Registrar los mapeadores antes de consultar nada. `Lot` declara relaciones hacia
# `LotPhase` y `OpeningBalance`, y `SQLAlchemy` resuelve esos nombres al configurar el
# primer mapeador: sin estos imports, la primera consulta —aunque sea a `companies`—
# falla con «failed to locate a name 'LotPhase'». `dev_seeds.py` lleva el mismo import
# por la misma razón.
import app.lots.models  # noqa: E402,F401
import app.business_units.models  # noqa: E402,F401
import app.operations.models  # noqa: E402,F401

ADMINISTRADOR = {
    "username": "administrador",
    "first_name": "Administrador",
    "last_name": "de Revisión",
    "email": "administrador@globalavicola.com",
    "role_name": "Super Administrador",
    "view_type": "web",
}

OPERADOR = {
    "username": "operador.movil",
    "first_name": "Operador",
    "last_name": "Móvil",
    "email": "operador.movil@globalavicola.com",
    "role_name": "Operador de Granja",
    "view_type": "mobile",
}


def _dsn() -> str:
    valor = os.environ.get("DATABASE_URL")
    if not valor:
        sys.exit("[revisión] Falta DATABASE_URL.")
    return valor.replace("postgresql://", "postgresql+asyncpg://", 1)


def _password() -> str:
    valor = os.environ.get("GA_REVIEW_PASSWORD")
    if not valor:
        sys.exit(
            "[revisión] Falta GA_REVIEW_PASSWORD.\n"
            "           `GA-REM-004`: no se escriben credenciales literales en el repositorio."
        )
    return valor


async def _empresa_destino(s, pedida: int | None):
    from app.masters.models import Company

    if pedida is not None:
        empresa = (await s.execute(
            select(Company).where(Company.id == pedida))).scalar_one_or_none()
        if empresa is None:
            sys.exit(f"[revisión] La empresa {pedida} no existe.")
        return empresa
    empresa = (await s.execute(
        select(Company).where(Company.is_active.is_(True))
        .order_by(Company.id).limit(1))).scalar_one_or_none()
    if empresa is None:
        sys.exit("[revisión] No hay ninguna empresa activa. Siembre una antes.")
    return empresa


async def _rol(s, nombre: str):
    from app.auth.models import Role

    rol = (await s.execute(select(Role).where(Role.name == nombre))).scalar_one_or_none()
    if rol is None:
        sys.exit(
            f"[revisión] No existe el rol {nombre!r}.\n"
            "           Ejecute antes `seeds/baseline_seeds.py`: los roles se siembran, "
            "no se inventan aquí."
        )
    return rol


async def _crear_o_actualizar(s, definicion: dict, *, company_id: int, clave: str):
    """Idempotente: repetirlo actualiza la cuenta en vez de duplicarla."""
    from app.auth.models import User
    from app.auth.security import hash_password

    rol = await _rol(s, definicion["role_name"])
    usuario = (await s.execute(
        select(User).where(User.username == definicion["username"]))).scalar_one_or_none()

    if usuario is None:
        usuario = User(
            username=definicion["username"], first_name=definicion["first_name"],
            last_name=definicion["last_name"], email=definicion["email"],
            hashed_password=hash_password(clave), role_id=rol.id,
            company_id=company_id, view_type=definicion["view_type"], is_active=True,
        )
        s.add(usuario)
        await s.flush()
        print(f"  ✅ creado    {usuario.username:<18} {definicion['role_name']}")
    else:
        usuario.hashed_password = hash_password(clave)
        usuario.role_id = rol.id
        usuario.company_id = company_id
        usuario.view_type = definicion["view_type"]
        usuario.is_active = True
        await s.flush()
        print(f"  🔄 actualizado {usuario.username:<16} {definicion['role_name']}")
    return usuario


async def _configurar_unidades(s, *, company_id: int, usuario):
    """Habilita las cuatro cadenas a la empresa y se las concede al usuario.

    Son **dos** decisiones distintas y aquí se toman las dos a conciencia: habilitar es de la
    empresa y conceder es del usuario. Se hace por `conceder_unidad`, el camino sancionado,
    que rechaza una concesión que cruce empresas.
    """
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit
    from app.business_units.service import conceder_unidad

    unidades = (await s.execute(
        select(BusinessUnit).where(BusinessUnit.is_active.is_(True))
        .order_by(BusinessUnit.code))).scalars().all()
    if not unidades:
        sys.exit("[revisión] El catálogo de unidades está vacío. Ejecute `baseline_seeds.py`.")

    for unidad in unidades:
        fila = (await s.execute(select(CompanyBusinessUnit).where(
            CompanyBusinessUnit.company_id == company_id,
            CompanyBusinessUnit.business_unit_id == unidad.id))).scalar_one_or_none()
        if fila is None:
            fila = CompanyBusinessUnit(company_id=company_id,
                                       business_unit_id=unidad.id, is_enabled=True)
            s.add(fila)
            await s.flush()
        elif not fila.is_enabled:
            fila.is_enabled = True
            await s.flush()

        viva = (await s.execute(select(UserBusinessUnit).where(
            UserBusinessUnit.user_id == usuario.id,
            UserBusinessUnit.company_business_unit_id == fila.id,
            UserBusinessUnit.revoked_at.is_(None)))).scalar_one_or_none()
        if viva is None:
            await conceder_unidad(s, user=usuario, company_business_unit=fila)
        print(f"     └─ {unidad.code:<12} habilitada y concedida")


async def _retirar_anteriores(s, conservar: list[int]) -> int:
    """Da de baja las cuentas que no son las de revisión. **No borra ninguna fila.**"""
    from app.auth.models import User

    resultado = await s.execute(
        update(User).where(User.id.notin_(conservar), User.is_active.is_(True))
        .values(is_active=False))
    return resultado.rowcount or 0


async def _inventario(s):
    from app.auth.models import Role, User
    from app.masters.models import Company

    print("\n── EMPRESAS ────────────────────────────────────────────")
    for e in (await s.execute(select(Company).order_by(Company.id))).scalars():
        print(f"  {e.id:<4} {e.name:<34} activa={e.is_active}")

    print("\n── USUARIOS ────────────────────────────────────────────")
    filas = (await s.execute(
        select(User, Role.name).outerjoin(Role, Role.id == User.role_id)
        .order_by(User.id))).all()
    for u, rol in filas:
        estado = "activo  " if u.is_active else "INACTIVO"
        print(f"  {u.id:<4} {u.username:<24} {estado} empresa={u.company_id} rol={rol}")
    print(f"\n  total {len(filas)} · activos {sum(1 for u, _ in filas if u.is_active)}")


async def main() -> None:
    p = argparse.ArgumentParser(description="Cuentas temporales de revisión integral.")
    p.add_argument("--inventario", action="store_true", help="mostrar el estado, sin tocar nada")
    p.add_argument("--crear", action="store_true", help="crear o actualizar las dos cuentas")
    p.add_argument("--retirar-anteriores", action="store_true",
                   help="dar de baja el resto de cuentas (reversible; no borra)")
    p.add_argument("--empresa", type=int, default=None,
                   help="id de la empresa; por defecto, la primera activa")
    args = p.parse_args()

    if not (args.inventario or args.crear):
        p.error("indique --inventario o --crear")

    motor = create_async_engine(_dsn())
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            if args.inventario and not args.crear:
                await _inventario(s)
                return

            clave = _password()
            empresa = await _empresa_destino(s, args.empresa)
            print(f"\n── EMPRESA DE REVISIÓN · {empresa.id} · {empresa.name} ──")

            admin = await _crear_o_actualizar(s, ADMINISTRADOR,
                                              company_id=empresa.id, clave=clave)
            operador = await _crear_o_actualizar(s, OPERADOR,
                                                 company_id=empresa.id, clave=clave)

            print("\n── UNIDADES DE NEGOCIO ─────────────────────────────────")
            await _configurar_unidades(s, company_id=empresa.id, usuario=operador)

            if args.retirar_anteriores:
                n = await _retirar_anteriores(s, [admin.id, operador.id])
                print(f"\n  🔻 {n} cuentas anteriores dadas de baja (is_active = False)")
                print("     Reversible: no se ha borrado ninguna fila ni ningún dato.")

            await s.commit()
            print("\n✅ Listo.")
            await _inventario(s)
    finally:
        await motor.dispose()


if __name__ == "__main__":
    asyncio.run(main())
