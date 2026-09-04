"""Frontera transaccional de la petición — `GA-REM-026`, hallazgo `R-68`.

Cubre `AC01`…`AC12`.

Una advertencia sobre el método, porque condiciona todo lo que sigue. Un test que use el
cliente en proceso **no puede** detectar `R-68`: `ASGITransport` ejecuta la aplicación
hasta el final —incluido el cierre de dependencias— antes de devolver la respuesta, de
modo que la carrera nunca se manifiesta y el test pasaría igual con el defecto presente.

Por eso `AC01` se comprueba a nivel ASGI: se envuelve `send` y, en el instante exacto en
que la aplicación emite `http.response.start`, se consulta la fila **desde otra conexión**.
Si el dato no está confirmado en ese momento, el cliente recibiría un éxito por algo que
todavía no existe. Ese test falla con el código anterior y pasa con el actual.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# SQLAlchemy configura todos los mappers de golpe: sin estos imports, las relaciones
# cruzadas de `Lot` fallan al inicializarse.
import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.database import get_db
from app.operations.validators import BusinessRuleViolation
from app.masters.models import Company
from tests.time_reference import reference_today
from app.transaction import (
    RutaTransaccional,
    TransactionCoverageError,
    rutas_sin_frontera,
    verificar,
)

PREFIJO = "TX-TEST-"


# ── Aplicación mínima bajo prueba ─────────────────────────────────────────────

def _app_de_prueba() -> FastAPI:
    """Aplicación reducida que usa la misma frontera y la misma dependencia reales."""
    app = FastAPI()
    router = APIRouter(route_class=RutaTransaccional)

    @router.post("/empresas")
    async def crear(nombre: str, db: AsyncSession = Depends(get_db)):
        empresa = Company(name=nombre, tax_id=nombre, country="Test", currency="USD")
        db.add(empresa)
        await db.flush()
        return {"id": empresa.id, "name": empresa.name}

    @router.put("/empresas/{empresa_id}")
    async def actualizar(empresa_id: int, pais: str, db: AsyncSession = Depends(get_db)):
        empresa = (
            await db.execute(select(Company).where(Company.id == empresa_id))
        ).scalar_one_or_none()
        if empresa is None:
            raise HTTPException(status_code=404, detail="no existe")
        empresa.country = pais
        await db.flush()
        return {"id": empresa.id, "country": empresa.country}

    @router.delete("/empresas/{empresa_id}")
    async def borrar(empresa_id: int, db: AsyncSession = Depends(get_db)):
        await db.execute(delete(Company).where(Company.id == empresa_id))
        return {"borrado": empresa_id}

    @router.post("/regla")
    async def regla(nombre: str, db: AsyncSession = Depends(get_db)):
        db.add(Company(name=nombre, tax_id=nombre, country="Test", currency="USD"))
        await db.flush()
        raise BusinessRuleViolation("no procede", "BR-99")

    @router.post("/crash")
    async def crash(nombre: str, db: AsyncSession = Depends(get_db)):
        db.add(Company(name=nombre, tax_id=nombre, country="Test", currency="USD"))
        await db.flush()
        raise ValueError("fallo inesperado")

    @router.post("/confirma-el-servicio")
    async def confirma_el_servicio(nombre: str, db: AsyncSession = Depends(get_db)):
        """Reproduce el camino de evidencias: el servicio confirma por su cuenta."""
        empresa = Company(name=nombre, tax_id=nombre, country="Test", currency="USD")
        db.add(empresa)
        await db.commit()
        await db.refresh(empresa)
        return {"id": empresa.id}

    @router.get("/solo-lectura")
    async def solo_lectura(db: AsyncSession = Depends(get_db)):
        """Depende de la base pero no la usa: no debe abrir ni confirmar transacción."""
        return {"ok": True}

    from app.operations.validators import BusinessRuleViolation as _BRV
    from starlette.responses import JSONResponse

    @app.exception_handler(_BRV)
    async def _manejador(request, exc):
        return JSONResponse(status_code=400, content={"detail": exc.message})

    app.include_router(router)
    return app


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    async with e.begin() as c:
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await e.dispose()


@pytest_asyncio.fixture
async def client_tx():
    """Cliente contra la aplicación mínima. Propaga lo que la aplicación no maneje."""
    from httpx import ASGITransport, AsyncClient

    app = _app_de_prueba()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://tx"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def client_tx_sin_excepciones():
    """Cliente que observa el código HTTP real en lugar de propagar la excepción.

    Necesario para `AC05` y `AC07`: lo que se quiere comprobar es qué recibe el cliente,
    no qué excepción salió.
    """
    from httpx import ASGITransport, AsyncClient

    app = _app_de_prueba()
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://tx"
    ) as ac:
        yield ac


def _nombre() -> str:
    return f"{PREFIJO}{uuid.uuid4().hex[:12]}"


async def _existe(motor, nombre: str) -> bool:
    """Consulta desde una conexión **independiente** de la de la petición."""
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return (
            await s.execute(select(Company.id).where(Company.name == nombre))
        ).scalar_one_or_none() is not None


# ── AC01 · ninguna respuesta de éxito antes de la confirmación ────────────────

async def test_t_026_01_no_hay_exito_antes_de_confirmar(motor):
    """`AC01` y `AC10` · en el instante de `http.response.start`, el dato ya está confirmado.

    Se comprueba a nivel ASGI y desde otra conexión, que es la única forma de observar la
    ordenación real. Con el código anterior —confirmación en el cierre de la dependencia—
    este test falla.
    """
    app = _app_de_prueba()
    nombre = _nombre()
    observado: dict = {}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(mensaje):
        if mensaje["type"] == "http.response.start":
            observado["estado"] = mensaje["status"]
            observado["visible"] = await _existe(motor, nombre)
        elif mensaje["type"] == "http.response.body":
            observado.setdefault("cuerpo", b"")
            observado["cuerpo"] += mensaje.get("body", b"")

    await app(
        {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "POST", "scheme": "http", "path": "/empresas", "raw_path": b"/empresas",
            "query_string": f"nombre={nombre}".encode(), "root_path": "",
            "headers": [(b"host", b"test")], "client": ("test", 1), "server": ("test", 80),
        },
        receive,
        send,
    )

    assert observado["estado"] == 200, observado
    assert observado["visible"], (
        "la respuesta de éxito se emitió antes de que la transacción estuviera confirmada"
    )

    import json

    cuerpo = json.loads(observado["cuerpo"])
    assert cuerpo["id"] is not None, "el identificador generado debe venir en la respuesta"


# ── AC02 / AC03 / AC04 · lectura inmediata determinista ───────────────────────

ITERACIONES = 30
"""Suficientes para que una carrera de milisegundos se manifieste: en la reproducción
original del defecto fallaban 3 de cada 5."""


async def test_t_026_02_lectura_inmediata_tras_crear(client_tx, motor):
    """`AC02` · un `GET` inmediato tras una creación con éxito ve el recurso. Sin esperas."""
    fallos = []
    for _ in range(ITERACIONES):
        nombre = _nombre()
        r = await client_tx.post("/empresas", params={"nombre": nombre})
        assert r.status_code == 200, r.text
        if not await _existe(motor, nombre):
            fallos.append(nombre)
    assert not fallos, f"{len(fallos)}/{ITERACIONES} creaciones no eran visibles al instante"


async def test_t_026_03_lectura_inmediata_tras_actualizar(client_tx, motor):
    """`AC03` · una actualización con éxito es observable de inmediato."""
    fallos = []
    for i in range(ITERACIONES):
        nombre = _nombre()
        creado = await client_tx.post("/empresas", params={"nombre": nombre})
        eid = creado.json()["id"]
        pais = f"PAIS-{i}"
        r = await client_tx.put(f"/empresas/{eid}", params={"pais": pais})
        assert r.status_code == 200, r.text

        fabrica = async_sessionmaker(motor, expire_on_commit=False)
        async with fabrica() as s:
            actual = (
                await s.execute(select(Company.country).where(Company.id == eid))
            ).scalar_one_or_none()
        if actual != pais:
            fallos.append((eid, actual, pais))
    assert not fallos, f"{len(fallos)}/{ITERACIONES} actualizaciones no eran visibles al instante"


async def test_t_026_04_lectura_inmediata_tras_borrar(client_tx, motor):
    """`AC04` · un borrado con éxito es observable de inmediato."""
    fallos = []
    for _ in range(ITERACIONES):
        nombre = _nombre()
        eid = (await client_tx.post("/empresas", params={"nombre": nombre})).json()["id"]
        r = await client_tx.delete(f"/empresas/{eid}")
        assert r.status_code == 200, r.text
        if await _existe(motor, nombre):
            fallos.append(nombre)
    assert not fallos, f"{len(fallos)}/{ITERACIONES} borrados no eran visibles al instante"


# ── AC05 · un fallo al confirmar no puede terminar en éxito ───────────────────

async def test_t_026_05_fallo_al_confirmar_no_devuelve_exito(client_tx_sin_excepciones, motor, monkeypatch):
    """`AC05` · si la confirmación falla, el cliente no recibe un HTTP de éxito."""
    nombre = _nombre()
    original = AsyncSession.commit
    llamadas = {"n": 0}

    async def commit_que_falla(self, *a, **k):
        llamadas["n"] += 1
        raise RuntimeError("fallo de confirmación inducido")

    monkeypatch.setattr(AsyncSession, "commit", commit_que_falla)
    try:
        r = await client_tx_sin_excepciones.post("/empresas", params={"nombre": nombre})
    finally:
        monkeypatch.setattr(AsyncSession, "commit", original)

    assert llamadas["n"] >= 1, "la frontera no intentó confirmar"
    assert r.status_code >= 500, f"un fallo de confirmación devolvió {r.status_code}"
    assert not await _existe(motor, nombre), "quedó dato pese al fallo de confirmación"


# ── AC06 / AC07 · reversión ───────────────────────────────────────────────────

async def test_t_026_06_error_de_dominio_revierte(client_tx_sin_excepciones, motor):
    """`AC06` · un error de regla de negocio revierte lo que la petición había preparado."""
    nombre = _nombre()
    r = await client_tx_sin_excepciones.post("/regla", params={"nombre": nombre})
    assert r.status_code == 400, r.text
    assert not await _existe(motor, nombre)


async def test_t_026_07_excepcion_inesperada_revierte(client_tx_sin_excepciones, motor):
    """`AC07` · una excepción no controlada revierte igualmente."""
    nombre = _nombre()
    r = await client_tx_sin_excepciones.post("/crash", params={"nombre": nombre})
    assert r.status_code >= 500
    assert not await _existe(motor, nombre)


# ── AC08 · las lecturas no confirman de más ───────────────────────────────────

async def test_t_026_08_solo_lectura_no_confirma(client_tx, monkeypatch):
    """`AC08` · una petición que no toca la base no abre ni confirma transacción."""
    original = AsyncSession.commit
    llamadas = {"n": 0}

    async def contar(self, *a, **k):
        llamadas["n"] += 1
        return await original(self, *a, **k)

    monkeypatch.setattr(AsyncSession, "commit", contar)
    r = await client_tx.get("/solo-lectura")
    monkeypatch.setattr(AsyncSession, "commit", original)

    assert r.status_code == 200
    assert llamadas["n"] == 0, "se confirmó una sesión que nunca abrió transacción"


# ── AC09 · convivencia con quien ya gestiona su transacción ───────────────────

async def test_t_026_09_servicio_que_confirma_no_regresa(client_tx, motor):
    """`AC09` · un servicio que confirma por su cuenta sigue funcionando, sin doble efecto.

    Reproduce el camino de evidencias (`operations/service.py:664`), la única excepción
    documentada al modelo. Confirmar una sesión ya confirmada es inocuo.
    """
    nombre = _nombre()
    r = await client_tx.post("/confirma-el-servicio", params={"nombre": nombre})
    assert r.status_code == 200, r.text
    assert await _existe(motor, nombre)

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        cuantas = (
            await s.execute(select(Company.id).where(Company.name == nombre))
        ).scalars().all()
    assert len(cuantas) == 1, "la doble confirmación duplicó la fila"


# ── AC11 · cobertura ──────────────────────────────────────────────────────────

def test_t_026_10_ninguna_ruta_fuera_de_la_frontera():
    """`AC11` · toda ruta que usa la base está bajo la frontera transaccional."""
    from app.main import app

    huerfanas = rutas_sin_frontera(app)
    assert not huerfanas, "rutas que usan la base fuera de la frontera:\n" + "\n".join(huerfanas)


def test_t_026_11_la_cobertura_detecta_un_router_olvidado():
    """`AC11` · la comprobación no es decorativa: detecta el olvido y aborta el arranque."""
    app = FastAPI()
    router = APIRouter()  # sin `route_class`: el olvido que se quiere detectar

    @router.post("/olvidada")
    async def olvidada(db: AsyncSession = Depends(get_db)):
        return {}

    app.include_router(router)

    assert rutas_sin_frontera(app) == ["POST /olvidada"]
    with pytest.raises(TransactionCoverageError, match="olvidada"):
        verificar(app)


# ── §22 · atomicidad de una escritura multi-entidad ───────────────────────────

async def test_t_026_12_evento_y_submovimientos_son_atomicos(
    http_client, auth_headers, seeded_ids, test_database_url
):
    """§22 · un evento y sus submovimientos se guardan juntos o no se guardan.

    `create_event` escribe en dos tandas: primero el evento —con su `flush()`, que ya envía
    el `INSERT`— y después los submovimientos. Si la segunda falla, el evento **no puede**
    quedarse. Se provoca con una referencia inexistente en el submovimiento, que rompe la
    clave foránea en el segundo `flush()`.

    Antes de `GA-REM-026` esto era además una vía para dejar basura confirmada: la
    dependencia confirmaba en su cierre y el orden de los efectos no estaba garantizado.
    """
    from sqlalchemy import func

    observaciones = f"{PREFIJO}atomicidad-{uuid.uuid4().hex[:8]}"
    motor = create_async_engine(test_database_url)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    try:
        from app.operations.models import BirdMovement, OperationalEvent

        async with fabrica() as s:
            antes_ev = (await s.execute(select(func.count(OperationalEvent.id)))).scalar_one()
            antes_bm = (await s.execute(select(func.count(BirdMovement.id)))).scalar_one()

        r = await http_client.post(
            "/api/v1/operations",
            headers=auth_headers,
            json={
                "lot_id": seeded_ids["lot_id"],
                "farm_id": seeded_ids["farm_id"],
                "house_id": seeded_ids["house_id"],
                "event_type": "bird_reception",
                # Fecha derivada, nunca literal: una fecha escrita a mano caduca
                # sola por BR-19 (R-28).
                "event_date": reference_today().isoformat(),
                "observations": observaciones,
                # `breed_id` inexistente: la clave foránea revienta en el segundo flush.
                "bird_movements": [
                    {"sex": "male", "quantity": 10, "breed_id": 987654321}
                ],
            },
        )
        assert r.status_code >= 400, (
            f"una referencia inexistente devolvió {r.status_code}; debía fallar"
        )

        async with fabrica() as s:
            despues_ev = (await s.execute(select(func.count(OperationalEvent.id)))).scalar_one()
            despues_bm = (await s.execute(select(func.count(BirdMovement.id)))).scalar_one()
            huerfano = (
                await s.execute(
                    select(OperationalEvent.id).where(
                        OperationalEvent.observations == observaciones
                    )
                )
            ).scalar_one_or_none()

        assert huerfano is None, "quedó el evento sin sus submovimientos"
        assert despues_ev == antes_ev, f"eventos {antes_ev} → {despues_ev}"
        assert despues_bm == antes_bm, f"submovimientos {antes_bm} → {despues_bm}"
    finally:
        await motor.dispose()
