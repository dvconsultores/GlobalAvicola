"""Wave 2.75 — el ciclo de negocio sobre la base que migró **el arranque real**.

```
MIGRATION EXISTS  ≠  MIGRATION DEPLOYED
CODE PASS         ≠  RUNTIME STARTUP PASS
```

`scripts/startup_test.sh` demuestra que el entrypoint migra y reconcilia antes de ceder el
control. Esta suite comprueba lo siguiente: que la base **que ese arranque dejó** sostiene
el ciclo completo, sin que nadie haya ejecutado `alembic` a mano.

Se lanza con `bash backend/scripts/runtime_test.sh`, que prepara el estado anterior a la
Wave 2 y arranca por el entrypoint, sin migrar por su cuenta.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from tests.time_reference import iso_days_ago, recent_event_date

_BASE_DE_ACTUALIZACION = "global_avicola_upgrade_test"

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.upgrade,
    pytest.mark.skipif(
        _BASE_DE_ACTUALIZACION not in os.environ.get("DATABASE_URL", ""),
        reason="Ciclo de arranque real: ejecútelo con `bash backend/scripts/runtime_test.sh`",
    ),
]


# ── El arranque dejó la base al día ──────────────────────────────────────────

async def test_el_arranque_dejo_la_base_en_head():
    """Nadie ejecutó `alembic` a mano: lo hizo el entrypoint."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    import app.database as database

    esperado = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    async with database.engine.connect() as conexion:
        actual = (await conexion.execute(text("SELECT version_num FROM alembic_version"))).scalar()

    assert len(esperado) == 1
    assert actual == esperado[0], f"La base quedó en {actual}, no en {esperado[0]}"


# ── §14 · el ciclo completo tras el arranque ─────────────────────────────────

async def test_ciclo_completo_de_negocio_tras_el_arranque(client, legacy_ids):
    """`login → refresh → switch-company → crear lote → leer maestros → operación`.

    Es la secuencia que el encargo exige demostrar sobre el arranque real, no sobre una
    base preparada a mano.
    """
    from seeds.legacy_state_seeds import PASSWORD_ENV

    clave = os.environ[PASSWORD_ENV]

    # 1 · login
    login = await client.post("/api/v1/login",
                              json={"username": "legacy_admin", "password": clave})
    assert login.status_code == 200, f"login: {login.text}"

    # 2 · refresh
    renovado = await client.post("/api/v1/refresh",
                                 json={"refresh_token": login.json()["refresh_token"]})
    assert renovado.status_code == 200, f"refresh: {renovado.text}"
    cabecera = {"Authorization": f"Bearer {renovado.json()['access_token']}"}

    # 3 · switch-company
    cambio = await client.post("/api/v1/switch-company", headers=cabecera,
                               json={"company_id": legacy_ids["company_id"]})
    assert cambio.status_code == 200, f"switch-company: {cambio.text}"
    cabecera = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    # 4 · leer maestros
    maestros = await client.get("/api/v1/masters/farms", headers=cabecera)
    assert maestros.status_code == 200, f"masters: {maestros.text}"

    # 5 · crear lote
    lote = await client.post("/api/v1/lots", headers=cabecera, json={
        "lot_code": "RUNTIME-LOT-01", "farm_id": legacy_ids["farm_id"],
        "bird_type": "broiler", "sex": "mixed"})
    assert lote.status_code in (200, 201), f"crear lote: {lote.text}"
    assert lote.json()["company_id"] == legacy_ids["company_id"], (
        "El lote debe pertenecer a la empresa seleccionada en el cambio de contexto")

    # 6 · crear y leer una operación.
    #
    # Con fecha de hoy, no retroactiva: `POST /lots` ignora el `start_date` recibido y
    # activa el lote en el momento de la creación (`R-47`), de modo que `BR-06` rechaza
    # cualquier evento anterior. La regla actúa bien; lo que falla es el alta del lote.
    # Se registra, no se corrige aquí: `R-47` pertenece a `GA-REM-019`.
    operacion = await client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": lote.json()["id"], "farm_id": legacy_ids["farm_id"],
        "house_id": legacy_ids["house_id"], "event_type": "bird_reception",
        "event_date": iso_days_ago(0),
        "bird_movements": [{"sex": "mixed", "quantity": 500}]})
    assert operacion.status_code == 201, f"crear operación: {operacion.text}"

    leida = await client.get(f"/api/v1/operations/{operacion.json()['id']}", headers=cabecera)
    assert leida.status_code == 200
    assert leida.json()["company_id"] == legacy_ids["company_id"]


async def test_mortalidad_completa_tras_el_arranque(client, legacy_ids):
    """La operación crítica del dominio, sobre la base que migró el arranque."""
    from seeds.legacy_state_seeds import PASSWORD_ENV

    login = await client.post("/api/v1/login", json={
        "username": "legacy_admin", "password": os.environ[PASSWORD_ENV]})
    cambio = await client.post(
        "/api/v1/switch-company",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"company_id": legacy_ids["company_id"]})
    cabecera = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    await client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": legacy_ids["lot_id"], "farm_id": legacy_ids["farm_id"],
        "house_id": legacy_ids["house_id"], "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1000}]})

    causa = await client.get("/api/v1/masters/mortality-causes", headers=cabecera)
    assert causa.status_code == 200, causa.text
    cause_id = causa.json()[0]["id"] if causa.json() else None

    cuerpo = {
        "lot_id": legacy_ids["lot_id"], "event_type": "mortality_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 10}],
    }
    if cause_id:
        cuerpo["cause_id"] = cause_id
    r = await client.post("/api/v1/operations", headers=cabecera, json=cuerpo)
    assert r.status_code == 201, f"mortalidad: {r.text}"
    if cause_id:
        assert r.json()["cause_id"] == cause_id, "La causa debe conservarse"


# ── R-40 / R-41 sobre el arranque real ───────────────────────────────────────

async def test_r40_el_25o_tipo_funciona_tras_el_arranque(client, legacy_ids):
    from seeds.legacy_state_seeds import PASSWORD_ENV

    login = await client.post("/api/v1/login", json={
        "username": "legacy_admin", "password": os.environ[PASSWORD_ENV]})
    cambio = await client.post(
        "/api/v1/switch-company",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"company_id": legacy_ids["company_id"]})
    cabecera = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    r = await client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": legacy_ids["lot_id"], "event_type": "egg_reception_classification",
        "event_date": recent_event_date()})
    assert r.status_code == 201, f"El 25.º tipo debe funcionar: {r.text}"

    leido = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=cabecera)
    assert leido.json()["event_type"] == "egg_reception_classification"


async def test_r41_lote_de_incubadora_tras_el_arranque(client, legacy_ids):
    from seeds.legacy_state_seeds import PASSWORD_ENV

    login = await client.post("/api/v1/login", json={
        "username": "legacy_admin", "password": os.environ[PASSWORD_ENV]})
    cambio = await client.post(
        "/api/v1/switch-company",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"company_id": legacy_ids["company_id"]})
    cabecera = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    r = await client.post("/api/v1/lots", headers=cabecera, json={
        "lot_code": "RUNTIME-HATCHERY-01", "farm_id": legacy_ids["farm_id"],
        "bird_type": "hatchery", "sex": "mixed"})
    assert r.status_code in (200, 201), f"Lote de incubadora: {r.text}"

    leido = await client.get(f"/api/v1/lots/{r.json()['id']}", headers=cabecera)
    assert leido.json()["bird_type"] == "hatchery"


# ── R-44 sobre el arranque real ──────────────────────────────────────────────

@pytest.mark.parametrize("rol,ruta", [
    ("operador", "/api/v1/masters/farms"),
    ("operador", "/api/v1/lots"),
    ("supervisor", "/api/v1/review/pending"),
    ("aprobador", "/api/v1/approvals/pending"),
    ("sap", "/api/v1/sap/references"),
    ("auditor", "/api/v1/audit"),
])
async def test_r44_los_roles_funcionan_tras_el_arranque(cabecera_de_rol, http_client, rol, ruta):
    """La reconciliación la ejecutó el entrypoint, no un operador."""
    cabecera = await cabecera_de_rol(rol)
    r = await http_client.get(ruta, headers=cabecera)
    assert r.status_code != 403, f"'{rol}' perdió {ruta} tras el arranque: {r.text[:150]}"


@pytest.mark.parametrize("rol,metodo,ruta,cuerpo", [
    ("operador", "post", "/api/v1/approvals/approve", {"event_id": 1}),
    ("auditor", "post", "/api/v1/operations", {}),
    ("sap", "delete", "/api/v1/masters/farms/1", None),
])
async def test_r44_minimo_privilegio_tras_el_arranque(
    cabecera_de_rol, http_client, rol, metodo, ruta, cuerpo
):
    cabecera = await cabecera_de_rol(rol)
    llamada = getattr(http_client, metodo)
    r = await (llamada(ruta, headers=cabecera, json=cuerpo) if cuerpo is not None
               else llamada(ruta, headers=cabecera))
    assert r.status_code == 403, f"'{rol}' no debería poder {metodo.upper()} {ruta}: {r.status_code}"
