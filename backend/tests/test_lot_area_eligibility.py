"""Elegibilidad de Área por estado en referencias nuevas de lote — `GA-FE-07` (OD-21, R-185).

Cubre `GA07-AC06`…`GA07-AC17` (semántica de dominio) del lado backend:

    UN RECURSO MAESTRO DADO DE BAJA LÓGICA NO PUEDE USARSE PARA NUEVAS REFERENCIAS.
    LA DESACTIVACIÓN LÓGICA NO BORRA NI INVALIDA LA HISTORIA.

Matriz:
    Alta:     activa propia ALLOW · inactiva propia DENY («Área inactiva») ·
              ajena DENY («no encontrado») · inexistente DENY · NULL ALLOW.
    Edición:  H1 sin cambio + histórica inactiva ALLOW · H2 mismo ID inactivo ALLOW ·
              H3/H5 cambio a inactiva DENY · H4 cambio a activa ALLOW · ajena DENY.

Nota de ejecución: requiere PostgreSQL (familia de lotes). En local sin PG queda
`skipped`; corre en CI. La evidencia RED/GREEN runtime vive en `audit/ga-fe-07/`.
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago

PREFIJO = "AREA-ELIG-TEST-"
PREFIJO_AREA = "AREA-ELIG-A-"


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            existe = (await c.execute(text("SELECT to_regclass('public.notifications')"))).scalar()
            if existe:
                await c.execute(text(
                    "DELETE FROM notifications WHERE related_entity_type = 'lot' "
                    "AND related_entity_id = ANY(:ids)"), {"ids": ids})
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
        areas = (await c.execute(text(
            "SELECT id FROM areas WHERE code LIKE :p"), {"p": f"{PREFIJO_AREA}%"})).scalars().all()
        if areas:
            await c.execute(text(
                "UPDATE lots SET area_id = NULL WHERE area_id = ANY(:ids)"), {"ids": areas})
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "area",
                AuditLog.entity_id.in_([str(i) for i in areas])))
            await c.execute(text("DELETE FROM areas WHERE id = ANY(:ids)"), {"ids": areas})
    await e.dispose()


@pytest_asyncio.fixture
async def unidades(test_database_url, seeded_ids):
    from tests.business_unit_fixtures import habilitar_y_conceder_todo

    await habilitar_y_conceder_todo(
        test_database_url, company_id=seeded_ids["company_id"],
        user_ids=[seeded_ids["user_admin_id"]])


async def _area(client, cab, company_id, sufijo):
    return await client.post("/api/v1/masters/areas", headers=cab, json={
        "company_id": company_id, "name": f"{PREFIJO_AREA}{sufijo}",
        "code": f"{PREFIJO_AREA}{sufijo}", "description": "Fixture GA-FE-07"})


async def _baja(client, cab, area_id):
    r = await client.delete(f"/api/v1/masters/areas/{area_id}", headers=cab)
    assert r.status_code == 204, r.text


async def _cab_otra_empresa(client, cab, company_id_2):
    """`R-196`. Token del mismo actor con el contexto en la empresa 2: los
    maestros se crean para la empresa del contexto — el `company_id` del cuerpo
    ya no impone empresa."""
    r = await client.post("/api/v1/switch-company", headers=cab,
                          json={"company_id": company_id_2})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _lote(client, cab, seeded_ids, **extra):
    cuerpo = {
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/lots", headers=cab, json=cuerpo)


# ── Alta ──────────────────────────────────────────────────────────────────────


async def test_g07_01_alta_inactiva_denegada(client, auth_headers, seeded_ids, motor, unidades):
    x = (await _area(client, auth_headers, seeded_ids["company_id"], "X1")).json()
    await _baja(client, auth_headers, x["id"])
    codigo = f"{PREFIJO}{uuid.uuid4().hex[:10]}"

    r = await _lote(client, auth_headers, seeded_ids, lot_code=codigo, area_id=x["id"])

    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Área inactiva", r.text
    assert r.json().get("rule") == "BR-07", r.text
    async with motor.connect() as c:
        filas = (await c.execute(select(Lot.id).where(Lot.lot_code == codigo))).scalars().all()
    assert filas == [], "el lote se persistió pese a la denegación"


async def test_g07_02_alta_activa_permitida(client, auth_headers, seeded_ids, motor, unidades):
    a = (await _area(client, auth_headers, seeded_ids["company_id"], "A1")).json()
    r = await _lote(client, auth_headers, seeded_ids, area_id=a["id"])
    assert r.status_code == 201, r.text
    assert r.json().get("area_id") == a["id"], r.text


async def test_g07_03_alta_ajena_denegada_sin_enumerar(
    client, auth_headers, seeded_ids, motor, unidades
):
    # `R-196`: el área «ajena» se crea con el contexto de la empresa 2.
    cab2 = await _cab_otra_empresa(client, auth_headers, seeded_ids["company_id_2"])
    y = (await _area(client, cab2, seeded_ids["company_id_2"], "Y1")).json()
    assert y["company_id"] == seeded_ids["company_id_2"], y
    r = await _lote(client, auth_headers, seeded_ids, area_id=y["id"])
    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Área no encontrado", r.text


async def test_g07_04_alta_inexistente_denegada(client, auth_headers, seeded_ids, motor, unidades):
    r = await _lote(client, auth_headers, seeded_ids, area_id=999999)
    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Área no encontrado", r.text


async def test_g07_05_alta_null_sin_cambio(client, auth_headers, seeded_ids, motor, unidades):
    r = await _lote(client, auth_headers, seeded_ids)
    assert r.status_code == 201, r.text
    assert r.json().get("area_id") is None, r.text


# ── Edición ───────────────────────────────────────────────────────────────────


async def test_g07_06_cambio_a_inactiva_denegado(client, auth_headers, seeded_ids, motor, unidades):
    a = (await _area(client, auth_headers, seeded_ids["company_id"], "A2")).json()
    x = (await _area(client, auth_headers, seeded_ids["company_id"], "X2")).json()
    await _baja(client, auth_headers, x["id"])
    lote = (await _lote(client, auth_headers, seeded_ids, area_id=a["id"])).json()

    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"area_id": x["id"]})
    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Área inactiva", r.text
    leido = (await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)).json()
    assert leido["area_id"] == a["id"], leido


async def test_g07_07_historica_sin_cambio_update_permitido(
    client, auth_headers, seeded_ids, motor, unidades
):
    """H1 · la baja lógica del área no invalida la historia ni bloquea ediciones ajenas al área."""
    x = (await _area(client, auth_headers, seeded_ids["company_id"], "H1")).json()
    lote = (await _lote(client, auth_headers, seeded_ids, area_id=x["id"],
                        planned_close_date=iso_days_ago(-10))).json()
    await _baja(client, auth_headers, x["id"])

    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"planned_close_date": iso_days_ago(-5)})
    assert r.status_code == 200, r.text
    leido = (await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)).json()
    assert leido["area_id"] == x["id"], "la referencia histórica cambió o se perdió"


async def test_g07_08_mismo_id_inactivo_explicito_permitido(
    client, auth_headers, seeded_ids, motor, unidades
):
    """H2 · reenviar el área actual (no es referencia nueva) no invalida la historia."""
    x = (await _area(client, auth_headers, seeded_ids["company_id"], "H2")).json()
    lote = (await _lote(client, auth_headers, seeded_ids, area_id=x["id"])).json()
    await _baja(client, auth_headers, x["id"])

    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"area_id": x["id"], "planned_close_date": iso_days_ago(-3)})
    assert r.status_code == 200, r.text
    leido = (await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)).json()
    assert leido["area_id"] == x["id"], leido


async def test_g07_09_historica_a_activa_permitido(
    client, auth_headers, seeded_ids, motor, unidades
):
    """H4 · cambiar a un área activa válida es una referencia nueva legítima."""
    x = (await _area(client, auth_headers, seeded_ids["company_id"], "H4")).json()
    a = (await _area(client, auth_headers, seeded_ids["company_id"], "A4")).json()
    lote = (await _lote(client, auth_headers, seeded_ids, area_id=x["id"])).json()
    await _baja(client, auth_headers, x["id"])

    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"area_id": a["id"]})
    assert r.status_code == 200, r.text
    leido = (await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)).json()
    assert leido["area_id"] == a["id"], leido


async def test_g07_10_inactiva_a_inactiva_denegado(
    client, auth_headers, seeded_ids, motor, unidades
):
    """H3 · la referencia histórica inactiva no puede moverse a otra inactiva."""
    x = (await _area(client, auth_headers, seeded_ids["company_id"], "H3a")).json()
    y = (await _area(client, auth_headers, seeded_ids["company_id"], "H3b")).json()
    lote = (await _lote(client, auth_headers, seeded_ids, area_id=x["id"])).json()
    await _baja(client, auth_headers, x["id"])
    await _baja(client, auth_headers, y["id"])

    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"area_id": y["id"]})
    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Área inactiva", r.text
    leido = (await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)).json()
    assert leido["area_id"] == x["id"], leido


async def test_g07_11_cambio_a_ajena_denegado(client, auth_headers, seeded_ids, motor, unidades):
    a = (await _area(client, auth_headers, seeded_ids["company_id"], "A5")).json()
    # `R-196`: contexto de la empresa 2 para la creación del área ajena.
    cab2 = await _cab_otra_empresa(client, auth_headers, seeded_ids["company_id_2"])
    y = (await _area(client, cab2, seeded_ids["company_id_2"], "Y5")).json()
    assert y["company_id"] == seeded_ids["company_id_2"], y
    lote = (await _lote(client, auth_headers, seeded_ids, area_id=a["id"])).json()

    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"area_id": y["id"]})
    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Área no encontrado", r.text
