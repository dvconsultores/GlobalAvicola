"""Administración de roles y permisos — `GA-REM-034`, hallazgos `R-92`, `R-93` y `R-94`.

Cubre `AC01`…`AC03` y `AC06`…`AC09`.

`docs/02 §3.1.3` pide «CRUD de roles **con permisos granulares**». Un rol nacía con sus
permisos y no podía cambiarlos nunca: `RoleUpdate` solo admitía `name`, `description` e
`is_active`. Y ningún endpoint decía qué módulos y acciones existen.

No se toca el enforcement: `GA-REM-002` lo certificó. Esto es administración.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401

PREFIJO = "RA-TEST-"


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.auth.models import Permission, Role, User

    async with e.begin() as c:
        roles = (await c.execute(
            select(Role.id).where(Role.name.like(f"{PREFIJO}%")))).scalars().all()
        usuarios = (await c.execute(
            select(User.id).where(User.username.like("ra_test_%")))).scalars().all()
        if usuarios:
            await c.execute(delete(AuditLog).where(AuditLog.user_id.in_(usuarios)))
            await c.execute(delete(User).where(User.id.in_(usuarios)))
        if roles:
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "role",
                AuditLog.entity_id.in_([str(r) for r in roles])))
            await c.execute(delete(Permission).where(Permission.role_id.in_(roles)))
            await c.execute(delete(Role).where(Role.id.in_(roles)))
    await e.dispose()


async def _rol(client, cab, permisos):
    r = await client.post("/api/v1/roles", headers=cab, json={
        "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}", "description": "Prueba de administración",
        "permissions": permisos,
    })
    assert r.status_code in (200, 201), r.text
    return r.json()


def _conjunto(rol):
    """Los permisos de un rol, como pares comparables."""
    return sorted((p["module"], p["action"]) for p in rol.get("permissions", []))


# ── AC01 · el catálogo de permisos ────────────────────────────────────────────

async def test_t_094_01_el_catalogo_de_permisos_es_consultable(client, auth_headers):
    """`AC01` · sin esto, una interfaz de roles tendría que adivinar módulos y acciones."""
    r = await client.get("/api/v1/roles/permissions-catalog", headers=auth_headers)
    assert r.status_code == 200, r.text
    catalogo = r.json()

    assert "modules" in catalogo and "actions" in catalogo, catalogo
    # Las acciones vienen del enum, no de una lista escrita a mano.
    assert set(catalogo["actions"]) >= {
        "read", "create", "update", "delete", "approve", "reject", "send_sap"
    }, catalogo["actions"]
    assert {"lots", "operations", "masters", "users", "audit"} <= set(catalogo["modules"]), (
        catalogo["modules"]
    )


# ── AC02 · los permisos de un rol se pueden editar ────────────────────────────

async def test_t_093_02_editar_permisos_sustituye_el_conjunto(
    client, auth_headers, motor
):
    """`AC02` y `AC06` · sustituye, no acumula.

    Se comprueba el **conjunto exacto**: si sumara en vez de sustituir, el resultado tendría
    tres pares en lugar de dos y no habría forma de revocar nada.
    """
    rol = await _rol(client, auth_headers, [
        {"module": "lots", "action": "read"},
        {"module": "operations", "action": "create"},
    ])
    assert _conjunto(rol) == [("lots", "read"), ("operations", "create")], rol

    r = await client.put(f"/api/v1/roles/{rol['id']}", headers=auth_headers, json={
        "permissions": [
            {"module": "lots", "action": "read"},
            {"module": "masters", "action": "update"},
        ],
    })
    assert r.status_code == 200, f"los permisos de un rol no se pueden editar: {r.text}"

    # `AC06` · `R-68`: lectura posterior e independiente.
    leidos = await client.get("/api/v1/roles", headers=auth_headers)
    actual = next(x for x in leidos.json() if x["id"] == rol["id"])
    assert _conjunto(actual) == [("lots", "read"), ("masters", "update")], (
        f"el conjunto debe sustituirse, no acumularse: {_conjunto(actual)}"
    )


async def test_t_093_03_retirar_un_permiso_retira_ese_y_no_otro(
    client, auth_headers, motor
):
    """`AC02` · la mitad de administrar permisos es poder revocarlos."""
    rol = await _rol(client, auth_headers, [
        {"module": "lots", "action": "read"},
        {"module": "lots", "action": "create"},
        {"module": "audit", "action": "read"},
    ])

    r = await client.put(f"/api/v1/roles/{rol['id']}", headers=auth_headers, json={
        "permissions": [
            {"module": "lots", "action": "read"},
            {"module": "audit", "action": "read"},
        ],
    })
    assert r.status_code == 200, r.text

    leidos = await client.get("/api/v1/roles", headers=auth_headers)
    actual = next(x for x in leidos.json() if x["id"] == rol["id"])
    assert ("lots", "create") not in _conjunto(actual), "no se retiró el permiso indicado"
    assert ("lots", "read") in _conjunto(actual), "se retiró un permiso que no tocaba"
    assert ("audit", "read") in _conjunto(actual)


# ── AC03 · el cambio se audita ────────────────────────────────────────────────

async def test_t_092_04_el_cambio_de_permisos_se_audita(
    client, auth_headers, seeded_ids, motor
):
    """`AC03` · reutiliza `GA-REM-032`; no se duplica lógica de auditoría."""
    from app.audit.models import AuditAction, AuditLog

    rol = await _rol(client, auth_headers, [{"module": "lots", "action": "read"}])
    r = await client.put(f"/api/v1/roles/{rol['id']}", headers=auth_headers, json={
        "permissions": [{"module": "lots", "action": "create"}]})
    assert r.status_code == 200, r.text

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        registros = (await s.execute(select(AuditLog).where(
            AuditLog.action == AuditAction.PERMISSION_CHANGE,
            AuditLog.entity_id == str(rol["id"])))).scalars().all()
    assert len(registros) >= 2, (
        f"el alta y la edición deben dejar rastro: {len(registros)}"
    )
    assert registros[0].user_id == seeded_ids["user_admin_id"]


# ── AC07 · el permiso concedido surte efecto ──────────────────────────────────

async def test_t_092_05_el_permiso_concedido_surte_efecto(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC07` · une la administración con el enforcement ya certificado.

    CONTROL y TRATAMIENTO sobre **el mismo usuario y la misma llamada**: lo único que cambia
    es el permiso del rol. Un `403` genérico no bastaría — se comprueba que antes pasaba.
    """
    rol = await _rol(client, auth_headers, [
        {"module": "audit", "action": "read"},
        {"module": "masters", "action": "read"},
    ])

    clave = f"Ra-{uuid.uuid4().hex[:12]}!"
    sufijo = uuid.uuid4().hex[:8]
    u = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": f"ra_test_{sufijo}", "email": f"ra_test_{sufijo}@example.com",
        "password": clave, "first_name": "Rol", "last_name": "Efectivo",
        "company_id": seeded_ids["company_id"], "role_id": rol["id"], "view_type": "web",
    })
    assert u.status_code in (200, 201), u.text
    entrada = await client.post("/api/v1/login",
                                json={"username": f"ra_test_{sufijo}", "password": clave})
    assert entrada.status_code == 200, entrada.text
    sujeto = {"Authorization": f"Bearer {entrada.json()['access_token']}"}

    # CONTROL · con `audit:read` concedido, la consulta pasa.
    antes = await http_client.get("/api/v1/audit?limit=1", headers=sujeto)
    assert antes.status_code == 200, f"CONTROL falló: {antes.status_code} {antes.text}"

    # Se retira ese permiso y solo ese.
    r = await client.put(f"/api/v1/roles/{rol['id']}", headers=auth_headers, json={
        "permissions": [{"module": "masters", "action": "read"}]})
    assert r.status_code == 200, r.text

    # TRATAMIENTO · el mismo usuario, la misma llamada, sin el permiso.
    entrada2 = await client.post("/api/v1/login",
                                 json={"username": f"ra_test_{sufijo}", "password": clave})
    sujeto2 = {"Authorization": f"Bearer {entrada2.json()['access_token']}"}
    despues = await http_client.get("/api/v1/audit?limit=1", headers=sujeto2)
    assert despues.status_code == 403, (
        f"retirar el permiso no surtió efecto: {despues.status_code}"
    )


# ── AC08 · sin permiso no se administra ───────────────────────────────────────

async def test_t_092_06_sin_permiso_no_se_administran_roles(
    client, http_client, seeded_ids, motor
):
    """`AC08` · el operador no tiene `users:create`."""
    from app.auth.security import create_access_token

    operador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_operator_id"])})}
    r = await http_client.post("/api/v1/roles", headers=operador, json={
        "name": f"{PREFIJO}sin-permiso", "permissions": []})
    assert r.status_code == 403, r.text


# ── AC09 · baja lógica ────────────────────────────────────────────────────────

async def test_t_092_07_la_baja_de_rol_es_logica(client, auth_headers, motor):
    """`AC09` · desaparece del listado activo sin borrarse."""
    from app.auth.models import Role

    rol = await _rol(client, auth_headers, [{"module": "lots", "action": "read"}])

    r = await client.put(f"/api/v1/roles/{rol['id']}", headers=auth_headers,
                         json={"is_active": False})
    assert r.status_code == 200, r.text

    listados = await client.get("/api/v1/roles", headers=auth_headers)
    assert rol["id"] not in [x["id"] for x in listados.json()], (
        "el rol desactivado sigue en el listado activo"
    )

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        fila = (await s.execute(select(Role).where(Role.id == rol["id"]))).scalar_one_or_none()
    assert fila is not None, "la baja borró el rol físicamente"
    assert fila.is_active is False
