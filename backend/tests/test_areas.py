"""Áreas funcionales — `GA-REM-039`, decisión `OD-08`.

Cubre `AC-A01`, `AC-A02`, `AC-A03` y `AC-A12`.

El área es **dónde pertenece** un usuario, no **qué puede hacer**. Esa distinción es la razón de
que exista una tabla en vez de deducirla del nombre del rol: con dos supervisores de áreas
distintas, deducirla haría que cada uno recibiera lo del otro.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401

PREFIJO = "AREA-TEST-"


@pytest_asyncio.fixture
async def motor(test_database_url):
    """Limpieza por SQL: esta suite se escribió antes de que la tabla existiera, y un error
    de importación al recolectar no es un rojo que demuestre nada."""
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.auth.models import User

    async with e.begin() as c:
        existe = (await c.execute(text("SELECT to_regclass('public.areas')"))).scalar()
        if existe:
            ids = (await c.execute(text(
                "SELECT id FROM areas WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})).scalars().all()
            if ids:
                await c.execute(text(
                    "UPDATE users SET area_id = NULL WHERE area_id = ANY(:ids)"), {"ids": ids})
                await c.execute(text(
                    "UPDATE lots SET area_id = NULL WHERE area_id = ANY(:ids)"), {"ids": ids})
                await c.execute(delete(AuditLog).where(
                    AuditLog.entity_type == "area",
                    AuditLog.entity_id.in_([str(i) for i in ids])))
                await c.execute(text("DELETE FROM areas WHERE id = ANY(:ids)"), {"ids": ids})
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
    await e.dispose()


def _cabecera(user_id: int) -> dict:
    from app.auth.security import create_access_token
    return {"Authorization": "Bearer " + create_access_token(data={"sub": str(user_id)})}


async def _area(client, cab, company_id, nombre=None):
    return await client.post("/api/v1/masters/areas", headers=cab, json={
        "company_id": company_id,
        "name": nombre or f"{PREFIJO}{uuid.uuid4().hex[:8]}",
    })


# ── AC-A01 · el área es dato maestro configurable ─────────────────────────────

async def test_t_039_01_el_area_se_administra_como_maestro(
    client, auth_headers, seeded_ids, motor
):
    """`AC-A01` · alta, lectura, edición y baja lógica, con el patrón de los otros maestros."""
    r = await _area(client, auth_headers, seeded_ids["company_id"])
    assert r.status_code in (200, 201), r.text
    creada = r.json()
    assert creada["is_active"] is True, creada

    leida = await client.get(f"/api/v1/masters/areas/{creada['id']}", headers=auth_headers)
    assert leida.status_code == 200, leida.text
    assert leida.json()["name"] == creada["name"]

    editada = await client.put(f"/api/v1/masters/areas/{creada['id']}", headers=auth_headers,
                               json={"description": "Área de producción avícola"})
    assert editada.status_code == 200, editada.text
    assert editada.json()["description"] == "Área de producción avícola"

    # Baja lógica: el histórico de notificaciones y lotes que la citan debe sobrevivir.
    baja = await client.put(f"/api/v1/masters/areas/{creada['id']}", headers=auth_headers,
                            json={"is_active": False})
    assert baja.status_code == 200, baja.text
    assert baja.json()["is_active"] is False


async def test_t_039_02_el_listado_expone_el_total(client, auth_headers, seeded_ids, motor):
    """`AC-A01` · mismo contrato de paginación que el resto de maestros (`R-89`)."""
    for _ in range(3):
        await _area(client, auth_headers, seeded_ids["company_id"])

    r = await client.get("/api/v1/masters/areas?limit=2", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert len(r.json()) <= 2
    assert r.headers.get("x-total-count") is not None, "el listado no expone el total"


# ── AC-A02 · sin nombres codificados ──────────────────────────────────────────

async def test_t_039_03_los_nombres_no_estan_codificados(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-A02` · el cliente pone los nombres. No hay enum, ni lista fija, ni siembra.

    Sembrar «Producción», «Administración» y «Ventas» habría fijado el organigrama de un
    cliente que aún no lo ha dicho.
    """
    inventado = f"{PREFIJO}Fábrica de Alimento Balanceado"
    r = await _area(client, auth_headers, seeded_ids["company_id"], nombre=inventado)
    assert r.status_code in (200, 201), r.text
    assert r.json()["name"] == inventado

    # Y la siembra no crea ninguna.
    from seeds.baseline_seeds import sembrar_baseline
    from sqlalchemy.ext.asyncio import async_sessionmaker

    e = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            await sembrar_baseline(s)
        async with e.connect() as c:
            sembradas = (await c.execute(text(
                "SELECT count(*) FROM areas WHERE name NOT LIKE :p"),
                {"p": f"{PREFIJO}%"})).scalar()
        assert sembradas == 0, f"la siembra creó {sembradas} áreas; `OD-08` no lo autoriza"
    finally:
        await e.dispose()


# ── AC-A03 · el usuario se asigna a un área ───────────────────────────────────

async def test_t_039_04_el_usuario_puede_asignarse_a_un_area(
    client, auth_headers, seeded_ids, motor
):
    """`AC-A03` · y puede no tenerla: los usuarios anteriores a esta spec no la tienen."""
    area = (await _area(client, auth_headers, seeded_ids["company_id"])).json()
    nombre = f"{PREFIJO}{uuid.uuid4().hex[:8]}"

    sin_area = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": nombre, "first_name": "Test", "last_name": "SinÁrea",
        "email": f"{nombre}@example.com", "password": uuid.uuid4().hex,
        "role_id": seeded_ids["role_operator_id"], "company_id": seeded_ids["company_id"],
        "view_type": "web"})
    assert sin_area.status_code == 201, sin_area.text
    assert sin_area.json().get("area_id") is None, "un usuario nace sin área asignada"

    asignado = await client.put(f"/api/v1/users/{sin_area.json()['id']}", headers=auth_headers,
                                json={"area_id": area["id"]})
    assert asignado.status_code == 200, asignado.text
    assert asignado.json()["area_id"] == area["id"], asignado.json()


# ── AC-A12 · aislamiento entre empresas ───────────────────────────────────────

async def test_t_039_05_las_areas_no_cruzan_de_empresa(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC-A12` · con control y tratamiento, y sin usar al Super Administrador como negativo.

    Su exención de tenencia haría pasar la prueba sin comprobar nada.
    """
    from app.auth.security import create_access_token

    propia = (await _area(client, auth_headers, seeded_ids["company_id"])).json()
    ajena = (await _area(client, auth_headers, seeded_ids["company_id_2"])).json()

    operador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_other_company_id"])})}

    # CONTROL · el operador de la empresa 2 ve el área de la empresa 2.
    suya = await http_client.get(f"/api/v1/masters/areas/{ajena['id']}", headers=operador)
    assert suya.status_code == 200, suya.text

    # TRATAMIENTO · la de la empresa 1 no existe para él.
    cruzada = await http_client.get(f"/api/v1/masters/areas/{propia['id']}", headers=operador)
    assert cruzada.status_code == 404, (
        f"un operador leyó el área de otra empresa: {cruzada.text}"
    )

    lista = await http_client.get("/api/v1/masters/areas?limit=100", headers=operador)
    assert lista.status_code == 200, lista.text
    assert all(a["id"] != propia["id"] for a in lista.json())
