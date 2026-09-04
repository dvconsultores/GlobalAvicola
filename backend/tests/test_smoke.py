"""Suite de humo — para ejecutar inmediatamente después de un despliegue.

Cubre el mínimo que demuestra que una instalación está viva y coherente: salud,
autenticación, renovación, contexto de empresa, catálogos, alta de lote, mortalidad,
permisos y evidencias.

**No está pensada para producción.** Escribe datos: un lote, una operación y un fichero de
evidencia. Ejecutarla contra una instalación real dejaría registros artificiales en el
inventario y en la auditoría. Se ejecuta contra un entorno de pruebas o de preproducción
equivalente. Si alguna vez se autorizara contra producción, habría que rediseñarla para que
solo leyera.

Se lanza con `bash backend/scripts/run_tests.sh tests/test_smoke.py -q`.
"""

from __future__ import annotations

import io
import uuid

import pytest

from tests.time_reference import iso_days_ago

pytestmark = pytest.mark.asyncio

SUFIJO = uuid.uuid4().hex[:8]


async def test_humo_01_salud(http_client):
    r = await http_client.get("/health")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"


async def test_humo_02_login(client, test_credentials):
    usuario, password = test_credentials
    r = await client.post("/api/v1/login", json={"username": usuario, "password": password})
    assert r.status_code == 200, r.text
    assert {"access_token", "refresh_token"} <= set(r.json())


async def test_humo_03_refresh(client, test_credentials):
    usuario, password = test_credentials
    login = await client.post("/api/v1/login", json={"username": usuario, "password": password})
    r = await client.post("/api/v1/refresh",
                          json={"refresh_token": login.json()["refresh_token"]})
    assert r.status_code == 200, r.text
    yo = await client.get("/api/v1/me",
                          headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert yo.status_code == 200


async def test_humo_04_switch_company(client, auth_headers, seeded_ids):
    r = await client.post("/api/v1/switch-company", headers=auth_headers,
                          json={"company_id": seeded_ids["company_id"]})
    assert r.status_code == 200, r.text


async def test_humo_05_masters_read(client, auth_headers):
    for ruta in ("/api/v1/masters/farms", "/api/v1/masters/houses",
                 "/api/v1/masters/vaccines", "/api/v1/masters/mortality-causes"):
        r = await client.get(ruta, headers=auth_headers)
        assert r.status_code == 200, f"{ruta}: {r.text[:150]}"


async def test_humo_06_crear_lote(client, auth_headers, seeded_ids):
    r = await client.post("/api/v1/lots", headers=auth_headers, json={
        "lot_code": f"SMOKE-{SUFIJO}", "farm_id": seeded_ids["farm_id"],
        "bird_type": "broiler", "sex": "mixed"})
    assert r.status_code in (200, 201), r.text


async def test_humo_07_crear_mortalidad(client, auth_headers, seeded_ids):
    lot = seeded_ids["lot_id"]
    recepcion = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lot, "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "event_type": "bird_reception", "event_date": iso_days_ago(0),
        "bird_movements": [{"sex": "mixed", "quantity": 200}]})
    assert recepcion.status_code == 201, recepcion.text

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lot, "event_type": "mortality_recording", "event_date": iso_days_ago(0),
        "cause_id": 1, "bird_movements": [{"sex": "mixed", "quantity": 1}]})
    assert r.status_code == 201, r.text
    assert r.json()["cause_id"] == 1, "La causa debe persistirse"


async def test_humo_08_permisos(http_client, seeded_ids):
    """Un permiso concedido pasa; uno denegado no."""
    from app.auth.security import create_access_token

    operador = {"Authorization":
                f"Bearer {create_access_token(data={'sub': str(seeded_ids['user_operator_id'])})}"}
    permitido = await http_client.get("/api/v1/masters/farms", headers=operador)
    assert permitido.status_code == 200, "El operador debe poder leer maestros"

    denegado = await http_client.post("/api/v1/approvals/approve", headers=operador,
                                      json={"event_id": 1})
    assert denegado.status_code == 403, "El operador no debe poder aprobar"


async def test_humo_09_evidencia_subida_y_lectura(client, auth_headers, seeded_ids):
    """`GA-REM-009`: la evidencia debe escribirse y poder recuperarse."""
    evento = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": seeded_ids["lot_id"], "event_type": "feed_registration",
        "event_date": iso_days_ago(0), "feed_movements": [{"quantity_kg": 1.0}]})
    assert evento.status_code == 201, evento.text
    eid = evento.json()["id"]

    # PNG mínimo válido: el endpoint solo admite imágenes y PDF, y probar la persistencia
    # con un tipo rechazado no probaría nada.
    contenido = bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001080600000"
        "01f15c4890000000a49444154789c6360000002000100" "05fe02fe" "dccc59e70000000049454e44ae426082")
    subida = await client.post(
        f"/api/v1/operations/{eid}/evidences", headers=auth_headers,
        files={"file": (f"smoke-{SUFIJO}.png", io.BytesIO(contenido), "image/png")})
    assert subida.status_code == 201, f"subida: {subida.text[:200]}"

    listado = await client.get(f"/api/v1/operations/{eid}/evidences", headers=auth_headers)
    assert listado.status_code == 200
    assert listado.json(), "La evidencia debe aparecer en el listado"

    descarga = await client.get(
        f"/api/v1/operations/{eid}/evidences/{listado.json()[0]['id']}/download",
        headers=auth_headers)
    assert descarga.status_code == 200, f"descarga: {descarga.text[:150]}"
    assert descarga.content == contenido, "El contenido recuperado debe ser el mismo"


async def test_humo_10_esquema_al_dia():
    """La base debe estar en el `head` que el código espera."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import text

    import app.database as database

    esperado = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    async with database.engine.connect() as conexion:
        actual = (await conexion.execute(text("SELECT version_num FROM alembic_version"))).scalar()
    assert actual == esperado[0], f"La base está en {actual}, el código espera {esperado[0]}"
