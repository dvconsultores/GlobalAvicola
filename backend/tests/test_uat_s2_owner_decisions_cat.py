"""`SPEC 020 §6` · `RR-32` — la causa compartida «Desconocida» y su listado por empresa.

`mortality_causes` y `cull_causes` son catálogos con valor de plataforma: la fila con
`company_id` nulo se comparte. La migración `i4d5e6f7a8b9` siembra **una** por tabla y el
listado la muestra junto a las propias. Seis comprobaciones, una por riesgo:

```
T-CAT-1  la migración deja **una** fila compartida por tabla — ni dos ni ninguna
T-CAT-2  el listado de la empresa trae la compartida **y** las propias
T-CAT-3  la compartida se ve desde cualquier empresa; las propias, solo desde la suya
T-CAT-4  la compartida **no** se edita ni se da de baja desde una empresa (404/403)
T-CAT-5  el resto de catálogos sigue sin listar filas con `company_id` nulo
T-CAT-6  la siembra es idempotente: correrla otra vez no duplica
```

`T-CAT-3` es la que impide que el arreglo se pase de largo: compartir la causa «Desconocida»
no puede convertirse en compartir el catálogo. `T-CAT-4` cierra el otro extremo — leer sí,
escribir no.
"""
from __future__ import annotations

import importlib.util
import pathlib
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "UATS2C-"

#: Nombre que siembra la migración, y su categoría. Se citan como constantes para que un
#: cambio de dato no deje las pruebas midiendo el nombre viejo.
COMPARTIDA = "Desconocida"
CATEGORIA_COMPARTIDA = "unknown"

#: La misma normalización que usa la migración (minúsculas y sin acentos) y los alias que
#: significan «no se conoce la causa».
NORMALIZAR = "lower(translate(name, 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'))"
ALIAS_DESCONOCIDA = ("desconocida", "desconocido", "por determinar", "sin determinar")

TABLAS_DE_CAUSA = ("mortality_causes", "cull_causes")


def _token(user_id: int) -> dict:
    """Cabecera de un actor. `OD-11`: sin reclamar empresa; manda la del usuario en la base."""
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


def _causas_compartidas(tabla: str):
    """Filas compartidas cuyo nombre ya significa «desconocida»."""
    return text(
        f"SELECT id, name, category, is_active FROM {tabla} "
        f"WHERE company_id IS NULL AND {NORMALIZAR} IN :alias"
    ).bindparams(bindparam("alias", expanding=True))


async def _filas(url: str, clausula, **parametros):
    motor = create_async_engine(url)
    try:
        async with motor.connect() as c:
            return (await c.execute(clausula, parametros)).all()
    finally:
        await motor.dispose()


async def _ejecutar(url: str, clausula, **parametros) -> int:
    motor = create_async_engine(url)
    try:
        async with motor.begin() as c:
            return (await c.execute(clausula, parametros)).rowcount
    finally:
        await motor.dispose()


@pytest_asyncio.fixture
async def esc(test_database_url):
    """Dos empresas con su catálogo de causas y un actor de cada una.

    ```
    Empresa A   MORT-A, CULL-A  ·  ACTOR_A  masters:read/create/update/delete
    Empresa B   MORT-B, CULL-B  ·  ACTOR_B  masters:read/create/update/delete
    ```

    Los actores **no** son Super Administradores: la autoridad global ya tiene su propia
    prueba (`test_master_tenant_isolation.py`), y aquí lo que se mide es el inquilino.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company, CullCause, MortalityCause

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        roles = {}
        for marca, empresa in (("A", a), ("B", b)):
            rol = Role(name=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", is_active=True)
            s.add(rol)
            await s.flush()
            for accion in (PermissionAction.READ, PermissionAction.CREATE,
                           PermissionAction.UPDATE, PermissionAction.DELETE):
                s.add(Permission(role_id=rol.id, module="masters", action=accion,
                                 scope_type="company"))
            roles[marca] = rol
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Cat",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        actor_a = _usuario(a.id, "ACTORA", roles["A"])
        actor_b = _usuario(b.id, "ACTORB", roles["B"])
        s.add_all([actor_a, actor_b])
        await s.flush()

        def _causa(modelo, company_id, marca):
            fila = modelo(company_id=company_id, is_active=True,
                          name=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", category="prueba")
            s.add(fila)
            return fila

        mort_a = _causa(MortalityCause, a.id, "MORT-A")
        cull_a = _causa(CullCause, a.id, "CULL-A")
        mort_b = _causa(MortalityCause, b.id, "MORT-B")
        cull_b = _causa(CullCause, b.id, "CULL-B")
        await s.flush()
        await s.commit()

        datos = {
            "url": test_database_url, "a": a.id, "b": b.id,
            "actor_a": actor_a.id, "actor_b": actor_b.id,
            "mort_a": mort_a.name, "cull_a": cull_a.name,
            "mort_b": mort_b.name, "cull_b": cull_b.name,
        }
    yield datos

    async with motor.begin() as c:
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN "
                             "(SELECT id FROM users WHERE username LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM audit_logs WHERE company_id IN "
                             "(SELECT id FROM companies WHERE name LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM mortality_causes WHERE name LIKE :p"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM cull_causes WHERE name LIKE :p"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM permissions WHERE role_id IN "
                             "(SELECT id FROM roles WHERE name LIKE :p)"), {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM users WHERE username LIKE :p"), {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM roles WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM companies WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})
    await motor.dispose()




# ── Pruebas ──────────────────────────────────────────────────────────────────

RECURSOS = (("mortality-causes", "mortality_causes", "mort"),
            ("cull-causes", "cull_causes", "cull"))


async def _listar(http_client, actor_id: int, recurso: str, buscar: str) -> list[dict]:
    r = await http_client.get(f"/api/v1/masters/{recurso}", headers=_token(actor_id),
                              params={"search": buscar, "limit": 100})
    assert r.status_code == 200, r.text
    return r.json()


async def test_t_cat_1_la_migracion_deja_una_compartida_por_tabla(esc):
    """`T-CAT-1`: ni dos ni ninguna."""
    for tabla in TABLAS_DE_CAUSA:
        filas = await _filas(esc["url"], _causas_compartidas(tabla), alias=list(ALIAS_DESCONOCIDA))
        assert len(filas) == 1, (tabla, filas)
        assert filas[0].name == COMPARTIDA and filas[0].category == CATEGORIA_COMPARTIDA
        assert filas[0].is_active is True


async def test_t_cat_2_el_listado_trae_la_compartida_y_las_propias(esc, http_client):
    """`T-CAT-2`."""
    for recurso, _tabla, clave in RECURSOS:
        compartida = await _listar(http_client, esc["actor_a"], recurso, COMPARTIDA)
        assert any(f["name"] == COMPARTIDA and f.get("company_id") is None for f in compartida), compartida
        propia = await _listar(http_client, esc["actor_a"], recurso, esc[f"{clave}_a"])
        assert [f["name"] for f in propia] == [esc[f"{clave}_a"]], propia


async def test_t_cat_3_la_compartida_se_ve_desde_cualquier_empresa_las_propias_no(esc, http_client):
    """`T-CAT-3`: compartir «Desconocida» no es compartir el catálogo."""
    for recurso, _tabla, clave in RECURSOS:
        compartida_b = await _listar(http_client, esc["actor_b"], recurso, COMPARTIDA)
        assert any(f["name"] == COMPARTIDA for f in compartida_b), compartida_b
        ajena = await _listar(http_client, esc["actor_b"], recurso, esc[f"{clave}_a"])
        assert ajena == [], f"la empresa B no puede ver la causa de A: {ajena}"
        propia_b = await _listar(http_client, esc["actor_b"], recurso, esc[f"{clave}_b"])
        assert [f["name"] for f in propia_b] == [esc[f"{clave}_b"]]


async def test_t_cat_4_la_compartida_no_se_edita_ni_se_da_de_baja_desde_una_empresa(esc, http_client):
    """`T-CAT-4`: leer sí, escribir no."""
    for recurso, tabla, _clave in RECURSOS:
        fila = (await _filas(esc["url"], _causas_compartidas(tabla), alias=list(ALIAS_DESCONOCIDA)))[0]
        cab = _token(esc["actor_a"])
        put = await http_client.put(f"/api/v1/masters/{recurso}/{fila.id}", headers=cab,
                                    json={"name": "Renombrada por una empresa"})
        assert put.status_code in (403, 404), put.text
        borrar = await http_client.delete(f"/api/v1/masters/{recurso}/{fila.id}", headers=cab)
        assert borrar.status_code in (403, 404, 405), borrar.text
        despues = await _filas(esc["url"], text(f"SELECT name, is_active FROM {tabla} WHERE id = :i"), i=fila.id)
        assert (despues[0].name, despues[0].is_active) == (COMPARTIDA, True)


async def test_t_cat_5_los_demas_catalogos_no_listan_filas_sin_empresa(esc, http_client):
    """`T-CAT-5`: el cambio se limita a las dos causas."""
    marca = f"{PREFIJO}SINEMP-{uuid.uuid4().hex[:6]}"
    await _ejecutar(esc["url"], text("INSERT INTO vaccines (company_id, name, is_active) VALUES (NULL, :n, TRUE)"), n=marca)
    try:
        r = await http_client.get("/api/v1/masters/vaccines", headers=_token(esc["actor_a"]),
                                  params={"search": marca, "limit": 100})
        assert r.status_code == 200, r.text
        assert r.json() == [], "un catálogo que no es de causas no comparte filas sin empresa"
    finally:
        await _ejecutar(esc["url"], text("DELETE FROM vaccines WHERE name = :n"), n=marca)


async def test_t_cat_6_la_siembra_es_idempotente(esc):
    """`T-CAT-6`: correr la siembra otra vez no duplica."""
    ruta = pathlib.Path(__file__).resolve().parents[1] / "alembic" / "versions" / "i4d5e6f7a8b9_spec020_owner_decisions.py"
    espec = importlib.util.spec_from_file_location("mig_i4d5", ruta)
    mig = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(mig)
    motor = create_async_engine(esc["url"])
    try:
        async with motor.begin() as c:
            creadas = await c.run_sync(lambda sync_conn: mig._sembrar(sync_conn))
        assert creadas == [], f"ya estaban sembradas, no se crea otra: {creadas}"
    finally:
        await motor.dispose()
    for tabla in TABLAS_DE_CAUSA:
        filas = await _filas(esc["url"], _causas_compartidas(tabla), alias=list(ALIAS_DESCONOCIDA))
        assert len(filas) == 1, (tabla, filas)
