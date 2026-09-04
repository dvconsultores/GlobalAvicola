"""Certificación del baseline limpio — `GA-REM-025`.

Cubre `AC01`…`AC15`. Se ejecuta contra la base de test aislada de `GA-REM-014`; nunca
contra el entorno compartido desplegado (§17 del encargo).

Los identificadores `T-025-NN` son los de la matriz de certificación.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import Permission, Role, User
from app.masters.models import Company, ProductivePhase
from scripts.data_classification import Categoria, clasificar
from scripts.reset_guard import ResetBloqueado, verificar
from seeds.baseline_seeds import _matriz_de_la_migracion, sembrar_baseline
from seeds.scenario_fixtures import PREFIJO, crear_par_multitenant, retirar_fixtures

# El modo asyncio de la suite es automático (`pyproject.toml`); no hace falta marca global.


@pytest_asyncio.fixture
async def sesion(test_database_url):
    motor = create_async_engine(test_database_url, poolclass=None)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        yield s
    await motor.dispose()


# ── AC02 — Alembic en cabeza, una sola cabeza ─────────────────────────────────

def _alembic(*args: str, url: str) -> str:
    entorno = {**os.environ, "DATABASE_URL": url}
    salida = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True, text=True, env=entorno, cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    return salida.stdout + salida.stderr


async def test_t_025_01_alembic_en_cabeza(test_database_url):
    """`AC02` · la base está en `head` y la cadena tiene una sola cabeza."""
    url = test_database_url
    actual = _alembic("current", url=url)
    cabezas = [l for l in _alembic("heads", url=url).splitlines() if "(head)" in l]
    assert "(head)" in actual, f"la base no está en head:\n{actual}"
    assert len(cabezas) == 1, f"se esperaba una sola cabeza, hay {len(cabezas)}:\n{cabezas}"


# ── AC03 — Roles y permisos ───────────────────────────────────────────────────

async def test_t_025_02_matriz_rbac_completa(sesion):
    """`AC03` · existen los 6 roles y sus 46 asociaciones operativas, permiso a permiso.

    Se comprueba la matriz entera y no solo el total: dos roles con permisos cruzados
    darían el mismo 46 y una autorización equivocada (§38 del encargo).
    """
    await sembrar_baseline(sesion)
    matriz = _matriz_de_la_migracion()

    for nombre, esperados in matriz.items():
        rol = (await sesion.execute(select(Role).where(Role.name == nombre))).scalar_one_or_none()
        assert rol is not None, f"falta el rol {nombre!r}"
        reales = {
            (p.module, p.action.value)
            for p in (
                await sesion.execute(select(Permission).where(Permission.role_id == rol.id))
            ).scalars()
        }
        faltan = set(esperados) - reales
        assert not faltan, f"{nombre}: faltan permisos {sorted(faltan)}"

    # Solo los roles de la matriz documentada. La base de la suite contiene además roles
    # `TEST *` creados por los fixtures de GA-REM-015: contarlos daría un total mayor y
    # no diría nada sobre la corrección de la matriz.
    operativos = (
        await sesion.execute(
            select(func.count(Permission.id))
            .join(Role, Role.id == Permission.role_id)
            .where(Role.name.in_(list(matriz)))
        )
    ).scalar_one()
    assert operativos == 46, f"se esperaban 46 asociaciones operativas, hay {operativos}"

    # Y ninguna de más: un permiso concedido fuera de `docs/12 §3` es una autorización
    # que nadie decidió.
    for nombre, esperados in matriz.items():
        rol = (await sesion.execute(select(Role).where(Role.name == nombre))).scalar_one()
        reales = {
            (p.module, p.action.value)
            for p in (
                await sesion.execute(select(Permission).where(Permission.role_id == rol.id))
            ).scalars()
        }
        sobran = reales - set(esperados)
        assert not sobran, f"{nombre}: permisos no documentados {sorted(sobran)}"

    admin = (
        await sesion.execute(select(Role).where(Role.name == "Super Administrador"))
    ).scalar_one()
    comodines = (
        await sesion.execute(
            select(func.count(Permission.id)).where(
                Permission.role_id == admin.id, Permission.module == "*"
            )
        )
    ).scalar_one()
    assert comodines == 9, f"el Super Administrador debe tener 9 comodines, tiene {comodines}"


# ── AC04 / AC05 — Configuración y autenticación ───────────────────────────────

async def test_t_025_03_settings_y_admin(sesion):
    """`AC04` y `AC05` · los Settings requeridos existen y hay un administrador."""
    from app.config import settings

    assert settings.MORTALITY_ALERT_WARNING_PCT == 3.0
    assert settings.MORTALITY_ALERT_CRITICAL_PCT == 8.0

    await sembrar_baseline(sesion)
    admin = (await sesion.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
    assert admin is not None and admin.hashed_password
    assert admin.company_id is None, "el Super Administrador no debe quedar atado a un tenant"


# ── AC01 / AC07 — Nada de historia ficticia ───────────────────────────────────

async def test_t_025_04_la_purga_cubre_toda_la_historia(sesion):
    """`AC01` y `AC07` · el conjunto a borrar cubre toda la historia de negocio y SAP.

    La prueba de que la base queda vacía es el ciclo completo de
    `scripts/certify_baseline.sh`, que no cabe aquí: vaciar la base de la suite dejaría
    sin datos al resto de pruebas. Lo que sí se comprueba aquí es la propiedad de la que
    depende aquel resultado: que ninguna tabla de historia quede fuera del borrado, y que
    ninguna tabla conservada dependa de una borrada —si dependiera, el `TRUNCATE CASCADE`
    la vaciaría en silencio.
    """
    from scripts.data_classification import borrable

    tablas = (
        await sesion.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()")
        )
    ).scalars().all()

    olvidadas = [
        t
        for t in tablas
        if clasificar(t)[0] in {Categoria.TEST_BUSINESS_DATA, Categoria.SIMULATED_SAP_DATA}
        and not borrable(t)
    ]
    assert not olvidadas, f"historia ficticia fuera del borrado: {olvidadas}"

    a_borrar = {t for t in tablas if borrable(t)}
    filas = await sesion.execute(
        text(
            """
            SELECT tc.table_name, ccu.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
             AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = current_schema()
            """
        )
    )
    arrastradas = sorted(
        {(o, d) for o, d in filas if o not in a_borrar and d in a_borrar}
    )
    assert not arrastradas, (
        f"tablas conservadas que el CASCADE vaciaría: {arrastradas}"
    )


# ── AC06 / AC10 — Fixtures deterministas ──────────────────────────────────────

async def test_t_025_05_fixtures_crean_dos_tenants(sesion):
    """`AC06` y `AC10` · el escenario crea sus precondiciones, sin depender de nada previo."""
    await sembrar_baseline(sesion)
    try:
        a, b = await crear_par_multitenant(sesion)
        await sesion.commit()

        assert a.company_id != b.company_id
        assert a.farm_id != b.farm_id and a.house_id != b.house_id and a.lot_id != b.lot_id

        nombres = (
            await sesion.execute(
                select(Company.name).where(Company.id.in_([a.company_id, b.company_id]))
            )
        ).scalars().all()
        assert all(n.startswith(PREFIJO) for n in nombres), (
            "todo dato de fixture debe ser identificable como tal"
        )
    finally:
        await retirar_fixtures(sesion)


async def test_t_025_06_fixtures_se_retiran(sesion):
    """`AC10` · el escenario se limpia por completo; no deja residuo."""
    await sembrar_baseline(sesion)
    await crear_par_multitenant(sesion)
    await sesion.commit()
    await retirar_fixtures(sesion)

    restantes = (
        await sesion.execute(select(func.count(Company.id)).where(Company.name.like(f"{PREFIJO}%")))
    ).scalar_one()
    assert restantes == 0, f"quedaron {restantes} empresas de fixture"


# ── AC11 — Reproducibilidad ───────────────────────────────────────────────────

async def test_t_025_07_baseline_idempotente(sesion):
    """`AC11` · sembrar dos veces produce exactamente el mismo estado."""
    primero = await sembrar_baseline(sesion)
    segundo = await sembrar_baseline(sesion)
    assert primero == segundo, f"el baseline no es reproducible: {primero} vs {segundo}"

    fases = (await sesion.execute(select(func.count(ProductivePhase.id)))).scalar_one()
    assert fases == 4, f"las fases se duplicaron: {fases}"


# ── AC15 — La guarda destructiva ──────────────────────────────────────────────

@pytest.mark.parametrize(
    "descripcion,entorno,marcador,lista,confirmar",
    [
        ("entorno productivo", "production", "1", "h/b", "b"),
        ("entorno desconocido", "qa-nueva", "1", "h/b", "b"),
        ("entorno sin declarar", "", "1", "h/b", "b"),
        ("sin marcador de intención", "development", None, "h/b", "b"),
        ("destino fuera de la lista blanca", "development", "1", "otro/otra", "b"),
        ("lista blanca vacía", "development", "1", "", "b"),
        ("confirmación equivocada", "development", "1", "h/b", "otra"),
        ("sin confirmación", "development", "1", "h/b", None),
    ],
)
def test_t_025_08_guarda_rechaza(monkeypatch, descripcion, entorno, marcador, lista, confirmar):
    """`AC15` · la guarda es fail-closed ante cada señal ausente o ambigua."""
    monkeypatch.delenv("GA_ALLOW_DESTRUCTIVE_RESET", raising=False)
    if marcador is not None:
        monkeypatch.setenv("GA_ALLOW_DESTRUCTIVE_RESET", marcador)
    monkeypatch.setenv("GA_RESET_ALLOWED_TARGETS", lista)
    with pytest.raises(ResetBloqueado):
        verificar("postgresql://u:p@h/b", base_confirmada=confirmar, entorno=entorno)


def test_t_025_09_guarda_rechaza_base_autodeclarada_productiva(monkeypatch):
    """`AC15` · una base que se declara real de cliente no se borra aunque todo lo demás cuadre."""
    monkeypatch.setenv("GA_ALLOW_DESTRUCTIVE_RESET", "1")
    monkeypatch.setenv("GA_RESET_ALLOWED_TARGETS", "h/b")
    with pytest.raises(ResetBloqueado, match="REAL_PRODUCTION"):
        verificar(
            "postgresql://u:p@h/b", base_confirmada="b", entorno="development",
            comentario_base="Instalación REAL_PRODUCTION del cliente X",
        )


def test_t_025_10_guarda_acepta_destino_autorizado(monkeypatch):
    """`AC15` · con las cinco señales favorables, y solo entonces, la guarda deja pasar."""
    monkeypatch.setenv("GA_ALLOW_DESTRUCTIVE_RESET", "1")
    monkeypatch.setenv("GA_RESET_ALLOWED_TARGETS", "h/b")
    destino = verificar("postgresql://u:p@h/b", base_confirmada="b", entorno="development")
    assert destino.identidad == "h/b"


# ── Clasificación de datos ────────────────────────────────────────────────────

async def test_t_025_11_toda_tabla_real_esta_clasificada(sesion):
    """Ninguna tabla puede quedar `UNKNOWN`: lo desconocido no se borra, pero debe verse."""
    tablas = (
        await sesion.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()")
        )
    ).scalars().all()
    desconocidas = [t for t in tablas if clasificar(t)[0] is Categoria.UNKNOWN]
    assert not desconocidas, f"tablas sin clasificar: {desconocidas}"
