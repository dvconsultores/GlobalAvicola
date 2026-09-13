"""`GA-REM-003` · AC04 — **el logout revoca el refresh token** (denylist de `jti`).

Diseño: `specs/remediation/GA-REM-003-AUTH-CONTEXT-AND-TOKEN-LIFECYCLE.md §AC04`.

Rojos en HEAD:
- 01: `POST /api/v1/logout` no existe (404) ⇒ «204 + refresh 401» no se cumple.
- 03: idempotencia no observada sin endpoint.
- 05: no hay asiento LOGOUT en auditoría.
- 07: el refresh emitido no lleva `jti` (no hay nada que revocar).

Controles (verdes antes y después):
- 02: el refresh normal sigue renovando.
- 04: el logout de una sesión no anula otra sesión del mismo usuario (revocación
  por `jti`, no por usuario).
- 06: un logout con token inválido no rompe ni revoca nada.
PREFIJO `GR3-`.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
from app.auth.security import decode_token

pytestmark = pytest.mark.asyncio

PREFIJO = "GR3-"


@pytest_asyncio.fixture
async def esc003(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()
        rol = Role(name=f"{PREFIJO}Rol-{uuid.uuid4().hex[:6]}", company_id=a.id,
                   is_active=True)
        s.add(rol)
        await s.flush()
        s.add(Permission(role_id=rol.id, module="operations",
                         action=PermissionAction.READ, scope_type="company"))
        u = User(first_name="GR3", last_name="Sesion",
                 email=f"{PREFIJO}{uuid.uuid4().hex[:6]}@e.test",
                 username=f"{PREFIJO}u-{uuid.uuid4().hex[:6]}",
                 hashed_password=hash_password("x1234567"),
                 company_id=a.id, role_id=rol.id, is_active=True)
        s.add(u)
        await s.flush()
        await s.commit()
        datos = {"url": test_database_url, "a": a.id, "u": u.id,
                 "username": u.username}
    yield datos
    # La tabla `revoked_tokens` puede no existir en la fase RED (pre-migración):
    # borrado en su propia transacción para que el fallo no aborte el resto.
    try:
        async with motor.begin() as c:
            await c.execute(text(
                "DELETE FROM revoked_tokens WHERE user_id IN "
                "(SELECT id FROM users WHERE username LIKE :p)"), {"p": f"{PREFIJO}%"})
    except Exception:  # noqa: BLE001
        pass
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def _login(http_client, esc):
    r = await http_client.post("/api/v1/login", json={
        "username": esc["username"], "password": "x1234567"})
    assert r.status_code == 200, r.text
    return r.json()


async def _refresh(http_client, token):
    return await http_client.post("/api/v1/refresh", json={"refresh_token": token})


def _auth(sesion):
    """`logout` es ruta de titularidad (`AC08b`): exige sesión del propio titular."""
    return {"Authorization": f"Bearer {sesion['access_token']}"}


async def _cuenta(esc, sql, **params):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(sql), params)).scalar()
    finally:
        await motor.dispose()


async def test_ac04_01_logout_revoca_el_refresh(http_client, esc003):
    """RED en HEAD: sin endpoint, el refresh sigue emitiendo (y el logout es 404)."""
    sesion = await _login(http_client, esc003)
    r = await http_client.post("/api/v1/logout", headers=_auth(sesion),
                               json={"refresh_token": sesion["refresh_token"]})
    assert r.status_code == 204, r.text
    r2 = await _refresh(http_client, sesion["refresh_token"])
    assert r2.status_code == 401, r2.text


async def test_ac04_02_control_el_refresh_normal_sigue_renovando(http_client, esc003):
    sesion = await _login(http_client, esc003)
    r = await _refresh(http_client, sesion["refresh_token"])
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]


async def test_ac04_03_logout_es_idempotente(http_client, esc003):
    sesion = await _login(http_client, esc003)
    r1 = await http_client.post("/api/v1/logout", headers=_auth(sesion),
                                json={"refresh_token": sesion["refresh_token"]})
    assert r1.status_code == 204, r1.text
    r2 = await http_client.post("/api/v1/logout", headers=_auth(sesion),
                                json={"refresh_token": sesion["refresh_token"]})
    assert r2.status_code == 204, r2.text
    r3 = await _refresh(http_client, sesion["refresh_token"])
    assert r3.status_code == 401, r3.text


async def test_ac04_04_control_el_logout_de_una_sesion_no_anula_otra(http_client, esc003):
    s1 = await _login(http_client, esc003)
    s2 = await _login(http_client, esc003)
    await http_client.post("/api/v1/logout", headers=_auth(s1),
                           json={"refresh_token": s1["refresh_token"]})
    r = await _refresh(http_client, s2["refresh_token"])
    assert r.status_code == 200, r.text


async def test_ac04_05_auditoria_del_logout(http_client, esc003):
    """RED en HEAD: no hay asiento LOGOUT (ni endpoint que lo produzca)."""
    sesion = await _login(http_client, esc003)
    r = await http_client.post("/api/v1/logout", headers=_auth(sesion),
                               json={"refresh_token": sesion["refresh_token"]})
    assert r.status_code == 204, r.text
    n = await _cuenta(esc003,
                      "SELECT count(*) FROM audit_logs WHERE user_id = :u "
                      "AND action::text ILIKE 'logout'", u=esc003["u"])
    assert n == 1, f"asientos LOGOUT: {n}"


async def test_ac04_06_control_logout_con_token_invalido_no_afecta(http_client, esc003):
    sesion = await _login(http_client, esc003)
    await http_client.post("/api/v1/logout", headers=_auth(sesion),
                           json={"refresh_token": "no-es-un-jwt"})
    r = await _refresh(http_client, sesion["refresh_token"])
    assert r.status_code == 200, r.text


async def test_ac04_07_el_refresh_lleva_jti(http_client, esc003):
    """RED en HEAD: sin `jti` no hay nada que revocar por token."""
    sesion = await _login(http_client, esc003)
    claims = decode_token(sesion["refresh_token"])
    assert claims.get("type") == "refresh"
    assert "jti" in claims and claims["jti"]
