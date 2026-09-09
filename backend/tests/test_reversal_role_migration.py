"""`GA-REM-041` enmienda B · `OD-19` Aclaración A · la capacidad de reverso llega a las
instalaciones existentes (`REV-R09`, `REV-R11`) y al baseline (`REV-R10`).

La suite se construye con `alembic upgrade head` **antes** de sembrar roles, así que la
migración de datos `v2w3x4y5z6a7` no encuentra ningún rol y no hace nada en ese momento.
Aquí se ejerce su lógica sobre una instalación que ya tiene el rol: se retiran los dos
permisos sembrados, se aplica la migración y se comprueba que los repone sin duplicar; la
bajada los retira sin tocar nada más. El estado final es el sembrado.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import Permission, Role
from seeds.baseline_seeds import _matriz_de_la_migracion

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ROL = "Supervisor Avícola"
DELTA = {("reversals", "CREATE"), ("reversals", "READ")}


def _migracion():
    rutas = list((RAIZ / "alembic" / "versions").glob("v2w3x4y5z6a7*.py"))
    assert rutas, "REV-R09: falta la migración de datos v2w3x4y5z6a7 (GA-REM-041-B)"
    spec = importlib.util.spec_from_file_location("mig_od19_acl_a", rutas[0])
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest_asyncio.fixture
async def sesion(test_database_url):
    motor = create_async_engine(test_database_url, poolclass=None)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        yield s
    await motor.dispose()


async def _rol(s) -> Role:
    return (await s.execute(select(Role).where(Role.name == ROL))).scalar_one()


async def _reverso(s, rol_id) -> set[tuple[str, str]]:
    filas = (await s.execute(select(Permission.module, Permission.action).where(
        Permission.role_id == rol_id, Permission.module == "reversals"))).all()
    return {(m, a.value.upper() if hasattr(a, "value") else str(a).upper()) for m, a in filas}


async def _total(s, rol_id) -> int:
    return (await s.execute(select(func.count(Permission.id)).where(Permission.role_id == rol_id))).scalar_one()


async def _reponer(s, rol_id):
    """Estado final = sembrado: los dos permisos presentes, una vez cada uno."""
    for modulo, accion in DELTA:
        existe = (await s.execute(text(
            "SELECT 1 FROM permissions WHERE role_id = :r AND module = :m AND action::text = :a"),
            {"r": rol_id, "m": modulo, "a": accion})).first()
        if existe is None:
            await s.execute(text(
                "INSERT INTO permissions (role_id, module, action, scope_type) "
                "VALUES (:r, :m, CAST(:a AS permissionaction), 'all')"), {"r": rol_id, "m": modulo, "a": accion})
    await s.commit()


async def test_rev_r09_la_migracion_concede_a_una_instalacion_existente_sin_duplicar(sesion):
    modulo = _migracion()
    rol = await _rol(sesion)
    try:
        await sesion.execute(text("DELETE FROM permissions WHERE role_id = :r AND module = 'reversals'"), {"r": rol.id})
        await sesion.commit()
        assert await _reverso(sesion, rol.id) == set(), "instalación existente sin la capacidad"
        antes = await _total(sesion, rol.id)

        await sesion.run_sync(lambda ss: modulo.aplicar(ss.connection()))
        await sesion.commit()
        assert await _reverso(sesion, rol.id) == DELTA, "REV-R09: la migración concede create + read"
        assert await _total(sesion, rol.id) == antes + 2, "REV-R09: exactamente dos asociaciones nuevas"

        await sesion.run_sync(lambda ss: modulo.aplicar(ss.connection()))
        await sesion.commit()
        assert await _total(sesion, rol.id) == antes + 2, "REV-R09: idempotente (segunda pasada no duplica)"
        assert await _reverso(sesion, rol.id) == DELTA
    finally:
        await _reponer(sesion, rol.id)


async def test_rev_r11_la_bajada_retira_exactamente_el_delta(sesion):
    modulo = _migracion()
    rol = await _rol(sesion)
    try:
        assert await _reverso(sesion, rol.id) == DELTA, "estado sembrado"
        total = await _total(sesion, rol.id)
        otros = total - 2

        await sesion.run_sync(lambda ss: modulo.retirar(ss.connection()))
        await sesion.commit()
        assert await _reverso(sesion, rol.id) == set(), "REV-R11: el delta se retira"
        assert await _total(sesion, rol.id) == otros, "REV-R11: ninguna otra asociación se toca"

        await sesion.run_sync(lambda ss: modulo.aplicar(ss.connection()))
        await sesion.commit()
        assert await _reverso(sesion, rol.id) == DELTA and await _total(sesion, rol.id) == total, "volver a subir repone"
    finally:
        await _reponer(sesion, rol.id)


async def test_rev_r10_la_matriz_compuesta_del_baseline_lleva_el_delta():
    matriz = _matriz_de_la_migracion()
    supervisor = {(m, a.lower()) for m, a in matriz[ROL]}
    assert {("reversals", "create"), ("reversals", "read")} <= supervisor, "REV-R10: el baseline concede el reverso al Supervisor"
    assert "Contralor Avícola" not in matriz, "REV-R10: el baseline no inventa roles (OD-19 Acl. A)"
    assert len(matriz) == 5, sorted(matriz)
    assert sum(len(v) for v in matriz.values()) == 48, "REV-R10 / GA-REM-025 AC03: 46 + 2"
    for rol, pares in matriz.items():
        assert len(pares) == len(set(pares)), f"{rol}: pares duplicados en la matriz compuesta"
