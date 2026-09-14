"""R-196 · Create de maestros con `company_id` resuelto en el servidor.

Cubre `AC-R196-01/02/03` en su mitad de backend:

- Hoy `FarmCreate`/`HatcheryCreate` **exigen** `company_id` en el cuerpo: la
  interfaz no lo envía (ni debe) ⇒ 422 y maestro estructural imposible de crear.
- La resolución de contexto debe vivir en el servidor, y el valor del cliente
  **no** puede imponerse al contexto del actor (coordinación R-50/C-02).

Los padres (house→farm, incubator→hatchery) ya se verifican entre inquilinos: se
conserva como control.
"""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

PREFIJO = "R196-TEST-"


@pytest_asyncio.fixture
async def motor_r196(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.masters.models import Farm, Hatchery

    async with e.begin() as c:
        await c.execute(delete(Farm).where(Farm.name.like(f"{PREFIJO}%")))
        await c.execute(delete(Hatchery).where(Hatchery.name.like(f"{PREFIJO}%")))
    await e.dispose()


async def test_r196_01_create_farm_sin_company_en_cuerpo(
        client, auth_headers, seeded_ids):
    """AC-01: el Create de granja no declara empresa; la resuelve el contexto."""
    r = await client.post("/api/v1/masters/farms", headers=auth_headers, json={
        "name": f"{PREFIJO}granja-contexto", "code": "R196A"})
    assert r.status_code in (200, 201), r.text
    assert r.json()["company_id"] == seeded_ids["company_id"]


async def test_r196_02_create_farm_ignora_company_ajena(
        client, auth_headers, seeded_ids):
    """AC-02: una empresa del cliente no puede imponerse al contexto del actor."""
    ajena = seeded_ids.get("company_id_2")
    assert ajena, "la fixture requiere empresa 2 para este caso"
    r = await client.post("/api/v1/masters/farms", headers=auth_headers, json={
        "company_id": ajena, "name": f"{PREFIJO}granja-ajena", "code": "R196B"})
    assert r.status_code in (200, 201), r.text
    assert r.json()["company_id"] == seeded_ids["company_id"]


async def test_r196_03_create_house_verifica_padre(
        client, auth_headers, seeded_ids):
    """Control ya verde: un galpón no puede colgar de una granja ajena."""
    ajena = seeded_ids.get("company_id_2")
    assert ajena, "la fixture requiere empresa 2 para este caso"

    desde_la_ajena = await client.post("/api/v1/switch-company", headers=auth_headers,
                                       json={"company_id": ajena})
    assert desde_la_ajena.status_code == 200, desde_la_ajena.text
    cab_ajena = {"Authorization": f"Bearer {desde_la_ajena.json()['access_token']}"}

    granja_ajena = await client.post("/api/v1/masters/farms", headers=cab_ajena, json={
        "company_id": ajena, "name": f"{PREFIJO}granja-de-la-2", "code": "R196C"})
    assert granja_ajena.status_code in (200, 201), granja_ajena.text

    r = await client.post("/api/v1/masters/houses", headers=auth_headers, json={
        "farm_id": granja_ajena.json()["id"],
        "name": f"{PREFIJO}galpon-de-ajena"})
    # Contrato vigente del validador canónico (`app/tenancy.py`): 400 BR-07.
    assert r.status_code == 400, r.text
    assert "BR-07" in r.text
