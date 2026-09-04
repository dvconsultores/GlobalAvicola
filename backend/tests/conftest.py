"""
Configuración de pytest y fixtures compartidas.

GA-REM-014 — Entorno de test aislado.

La guarda FAIL-CLOSED de `tests/environment_guard.py` se aplica **antes** de
cualquier fixture y antes de que se abra ninguna conexión. Si el entorno no es
inequívocamente de pruebas, la sesión se aborta sin tocar ninguna base de datos.
"""
from __future__ import annotations

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.environment_guard import (
    TEST_DB_URL_ENV,
    UnsafeTestEnvironment,
    require_safe_test_environment,
)
from tests.simulated_clock import install as install_simulated_clock


# ═══════════════════════════════════════════════════════════════════════════
# GUARDA — se ejecuta en el arranque de pytest, antes de importar la app
# ═══════════════════════════════════════════════════════════════════════════

def pytest_configure(config: pytest.Config) -> None:
    """Aplica la guarda de entorno antes de recolectar o ejecutar nada.

    `--collect-only` queda exento: la recolección no abre conexiones ni escribe.
    """
    if config.getoption("--collect-only"):
        return
    try:
        decision = require_safe_test_environment()
    except UnsafeTestEnvironment as exc:
        pytest.exit(str(exc), returncode=3)
        return

    # La aplicación debe apuntar a la base desechable, nunca a la suya.
    os.environ["DATABASE_URL"] = decision.database_url or ""
    config.stash["ga_test_db"] = decision.database_name

    # R-28: simulación del avance del calendario, si se ha pedido. Adelanta el reloj de
    # todo el proceso —aplicación incluida— para que `BR-19` y los tests midan contra la
    # misma fecha. Sin la variable de entorno no hace nada.
    simulada = install_simulated_clock()
    if simulada is not None:
        print(f"\n[R-28] calendario simulado: hoy = {simulada}")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


# ═══════════════════════════════════════════════════════════════════════════
# Aislamiento entre tests (GA-REM-014 · AC04)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def _use_null_pool():
    """Sustituye el pool de conexiones por `NullPool` durante las pruebas.

    `app/database.py` crea un motor asíncrono con pool a nivel de módulo.
    pytest-asyncio ejecuta cada test en su propio bucle de eventos, y las
    conexiones de asyncpg quedan ligadas al bucle en que se crearon. Al
    reutilizarse desde otro bucle, SQLAlchemy falla con `InterfaceError` o
    `RuntimeError: got Future attached to a different loop`.

    `NullPool` abre y cierra una conexión por uso, de modo que ninguna
    conexión sobrevive a su bucle. Es configuración **de pruebas**: no altera
    el comportamiento de la aplicación en ejecución real.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    import app.database as database

    original_engine, original_session = database.engine, database.async_session
    database.engine = create_async_engine(
        os.environ["DATABASE_URL"], echo=False, poolclass=NullPool
    )
    database.async_session = async_sessionmaker(
        database.engine, class_=AsyncSession, expire_on_commit=False
    )
    yield
    database.engine, database.async_session = original_engine, original_session


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_between_tests():
    """Cierra cualquier conexión residual al terminar cada test."""
    yield
    import app.database as database

    await database.engine.dispose()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """URL de la base desechable, ya validada por la guarda."""
    return os.environ[TEST_DB_URL_ENV]


# ═══════════════════════════════════════════════════════════════════════════
# Cliente HTTP
# ═══════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator:
    """Cliente HTTPX asíncrono contra la aplicación FastAPI."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app  # import diferido: después de la guarda

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def http_client() -> AsyncGenerator:
    """Cliente que observa el código HTTP real en lugar de propagar la excepción.

    `ASGITransport` re-lanza por defecto lo que la aplicación no maneja, de modo que un
    fallo no controlado llega al test como excepción y no como respuesta. Para verificar
    el *contrato de error* —qué código ve realmente el cliente— hace falta el
    comportamiento de un servidor real, que es lo que da `raise_app_exceptions=False`.
    """
    from httpx import ASGITransport, AsyncClient

    from app.main import app  # import diferido: después de la guarda

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ═══════════════════════════════════════════════════════════════════════════
# Credenciales de prueba — nunca literales en el código (GA-REM-004)
# ═══════════════════════════════════════════════════════════════════════════

def _test_credentials() -> tuple[str, str]:
    """Credenciales del usuario administrador de pruebas.

    Se leen del entorno; los seeds de test crean el usuario con esos mismos
    valores. No hay contraseñas literales en el código versionado.
    """
    from seeds.test_seeds import TEST_ADMIN_PASSWORD_ENV, TEST_ADMIN_USERNAME

    password = os.environ.get(TEST_ADMIN_PASSWORD_ENV)
    if not password:
        pytest.skip(
            f"{TEST_ADMIN_PASSWORD_ENV} no definida: ejecute la suite con "
            "backend/scripts/run_tests.sh, que la genera y siembra."
        )
    return TEST_ADMIN_USERNAME, password


@pytest_asyncio.fixture
async def seeded_ids() -> dict:
    """Identificadores reales de la siembra, leídos de la base.

    Los tests no deben inventar `user_id=3`: los ids dependen del orden de inserción y
    una suposición equivocada convierte un test de aislamiento en un test de nada.
    """
    from sqlalchemy import select

    import app.database as database
    from app.auth.models import User
    from app.masters.models import Company, Farm, House, Lot
    from seeds.test_seeds import (
        TEST_ADMIN_USERNAME,
        TEST_APPROVER_USERNAME,
        TEST_COMPANY_2_NAME,
        TEST_OPERATOR_USERNAME,
        TEST_OTHER_COMPANY_USERNAME,
    )

    from app.auth.models import Role

    async with database.async_session() as session:
        usuarios = {
            u.username: u for u in (await session.execute(select(User))).scalars().all()
        }
        roles = {r.name: r.id for r in (await session.execute(select(Role))).scalars().all()}
        lotes = (await session.execute(select(Lot).order_by(Lot.id))).scalars().all()
        granjas = (await session.execute(select(Farm).order_by(Farm.id))).scalars().all()
        galpones = (await session.execute(select(House).order_by(House.id))).scalars().all()
        empresa_2 = (
            await session.execute(select(Company).where(Company.name == TEST_COMPANY_2_NAME))
        ).scalar_one_or_none()

    return {
        "user_admin_id": usuarios[TEST_ADMIN_USERNAME].id,
        "user_operator_id": usuarios[TEST_OPERATOR_USERNAME].id,
        "user_approver_id": usuarios[TEST_APPROVER_USERNAME].id,
        "user_other_company_id": usuarios[TEST_OTHER_COMPANY_USERNAME].id,
        "company_id": usuarios[TEST_ADMIN_USERNAME].company_id,
        "company_id_2": empresa_2.id if empresa_2 else None,
        "farm_id": granjas[0].id if granjas else None,
        "house_id": galpones[0].id if galpones else None,
        "lot_id": lotes[0].id if lotes else None,
        "lot_id_2": (lotes[1].id if len(lotes) > 1 else lotes[0].id) if lotes else None,
        "role_admin_id": roles.get("TEST Super Admin"),
        "role_operator_id": roles.get("TEST Operador"),
        "role_approver_id": roles.get("TEST Aprobador"),
    }


@pytest.fixture(scope="function")
def test_credentials() -> tuple[str, str]:
    """Usuario y contraseña de prueba, generados por ejecución (`GA-REM-004`)."""
    return _test_credentials()


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client) -> dict:
    """Autentica al administrador de pruebas y devuelve la cabecera Bearer."""
    username, password = _test_credentials()
    resp = await client.post(
        "/api/v1/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, f"Login de pruebas falló: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ═══════════════════════════════════════════════════════════════════════════
# Camino de ACTUALIZACION (Wave 2.5) — fixtures del estado heredado
#
# Solo tienen sentido contra `global_avicola_upgrade_test`, la base que reproduce una
# instalacion anterior a la Wave 2. Se lanzan con `scripts/upgrade_test.sh`.
# ═══════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def legacy_ids() -> dict:
    """Identificadores del estado heredado, leidos de la base."""
    from sqlalchemy import select

    import app.database as database
    from app.auth.models import User
    from app.masters.models import Company, Farm, House, Lot
    from seeds.legacy_state_seeds import EMPRESA, GRANJA_CODIGO, LOTE_CODIGO

    async with database.async_session() as sesion:
        empresa = (await sesion.execute(
            select(Company).where(Company.name == EMPRESA))).scalar_one()
        granja = (await sesion.execute(
            select(Farm).where(Farm.code == GRANJA_CODIGO))).scalar_one()
        lote = (await sesion.execute(
            select(Lot).where(Lot.lot_code == LOTE_CODIGO))).scalar_one()
        galpon = (await sesion.execute(
            select(House).where(House.farm_id == granja.id))).scalars().first()
        usuarios = {
            u.username: u.id
            for u in (await sesion.execute(select(User))).scalars().all()
        }

    return {
        "company_id": empresa.id,
        "farm_id": granja.id,
        "house_id": galpon.id if galpon else None,
        "lot_id": lote.id,
        "users": usuarios,
    }


async def _cabecera_legacy(client, usuario: str) -> dict:
    """Autentica a un usuario heredado y devuelve su cabecera Bearer."""
    import os

    from seeds.legacy_state_seeds import PASSWORD_ENV

    respuesta = await client.post("/api/v1/login", json={
        "username": usuario, "password": os.environ[PASSWORD_ENV],
    })
    assert respuesta.status_code == 200, f"Login de {usuario}: {respuesta.text}"
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth_headers_legacy(client) -> dict:
    """Super Admin heredado."""
    return await _cabecera_legacy(client, "legacy_admin")


@pytest_asyncio.fixture
async def cabecera_de_rol(client):
    """Devuelve una funcion que autentica a cualquier usuario heredado por su rol."""
    usuarios = {
        "operador": "legacy_operador",
        "supervisor": "legacy_supervisor",
        "aprobador": "legacy_aprobador",
        "sap": "legacy_sap",
        "auditor": "legacy_auditor",
        "admin": "legacy_admin",
    }

    async def _obtener(rol: str) -> dict:
        return await _cabecera_legacy(client, usuarios[rol])

    return _obtener


@pytest_asyncio.fixture
async def auth_headers_legacy_en_empresa(client, legacy_ids) -> dict:
    """Super Admin heredado, con el contexto puesto en la empresa heredada.

    El Super Admin no pertenece a ninguna empresa (`company_id = None`), que es como lo
    sembraba la instalación original. Para operar sobre datos de una empresa concreta el
    producto ofrece `switch-company`, y es el camino que un administrador real recorre.
    """
    cabecera = await _cabecera_legacy(client, "legacy_admin")
    respuesta = await client.post(
        "/api/v1/switch-company",
        headers=cabecera,
        json={"company_id": legacy_ids["company_id"]},
    )
    assert respuesta.status_code == 200, f"switch-company: {respuesta.text}"
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}
