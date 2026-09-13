"""`R-202` · Restablecimiento de contraseña por administrador **con contexto de empresa**.

Diseño: `audit/ga-claude-final-audit/specs/R-202/R-202_AC_RED_E2E_UAT.md §2`.

```
Super admin SIN contexto  → objetivo de una empresa ⇒ 4xx fail-closed (hoy 200)
Admin de empresa (users:update) → objetivo de su empresa ⇒ 204 (hoy 403)
Admin de empresa → objetivo de otra empresa ⇒ 403/404 (sin cambio)
Auditoría: empresa efectiva del actor + objetivo
```

Rojos en HEAD: 01 (200⇒4xx), 03 (403⇒204), 06 (sin asiento con empresa del actor).
Controles: 02 (super situado) y 04 (cross-company) verdes antes y después.
PREFIJO `R202-`.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R202-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc202(test_database_url):
    """Empresas A y B · super sin contexto · super situado · admin de empresa A.

    ```
    rol_admin_a   company_id=A   users:read/create/update/delete (company)
    rol_ops       company_id=A/B operations:read (para u_a/u_b)
    rol_global    company_id=NULL ("*", …, "all")  — plantilla de sistema
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        def _rol(nombre, company_id):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_admin_a = _rol("AdminA", a.id)
        rol_ops_a = _rol("OpsA", a.id)
        rol_ops_b = _rol("OpsB", b.id)
        rol_global = _rol("Global", None)
        await s.flush()

        for accion in (PermissionAction.READ, PermissionAction.CREATE,
                       PermissionAction.UPDATE, PermissionAction.DELETE):
            s.add(Permission(role_id=rol_admin_a.id, module="users", action=accion,
                             scope_type="company"))
        s.add(Permission(role_id=rol_ops_a.id, module="operations",
                         action=PermissionAction.READ, scope_type="company"))
        s.add(Permission(role_id=rol_ops_b.id, module="operations",
                         action=PermissionAction.READ, scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="R202",
                        email=f"{PREFIJO}{marca.lower()}-{uuid.uuid4().hex[:6]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        super_ = _usuario(None, "SUPER", rol_global)
        admin_a = _usuario(a.id, "ADMINA", rol_admin_a)
        u_a = _usuario(a.id, "UA", rol_ops_a)
        u_b = _usuario(b.id, "UB", rol_ops_b)
        s.add_all([super_, admin_a, u_a, u_b])
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "b": b.id, "super": super_.id, "admin_a": admin_a.id,
                 "u_a": u_a.id, "u_b": u_b.id, "url": test_database_url}
    yield datos

    async with motor.begin() as c:
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN "
                             "(SELECT id FROM users WHERE username LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        from app.auth.models import Permission, Role, User
        from app.masters.models import Company
        ids = (await c.execute(text("SELECT id FROM roles WHERE name LIKE :p"),
                               {"p": f"{PREFIJO}%"})).scalars().all()
        if ids:
            await c.execute(delete(Permission).where(Permission.role_id.in_(ids)))
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
        await c.execute(delete(Role).where(Role.name.like(f"{PREFIJO}%")))
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await motor.dispose()


async def _hash_en_base(esc202, user_id: int) -> str:
    from app.auth.models import User

    motor = create_async_engine(esc202["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return (await s.execute(
                select(User.hashed_password).where(User.id == user_id))).scalar_one()
    finally:
        await motor.dispose()


async def _ultimo_asiento(esc202, user_id: int):
    from app.audit.models import AuditLog

    motor = create_async_engine(esc202["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return (await s.execute(
                select(AuditLog).where(AuditLog.entity_type == "user_password",
                                       AuditLog.entity_id == str(user_id))
                .order_by(AuditLog.id.desc()).limit(1))).scalar_one_or_none()
    finally:
        await motor.dispose()


# ── RED-01 · RED-03 · RED-06 (rojas en HEAD) · CTL-02 · CTL-04 ───────────────

async def test_r202_01_super_sin_contexto_no_restablece_fuera_de_ambito(http_client, esc202):
    """`AC-R202-01` — sin empresa efectiva no hay ámbito: 4xx fail-closed y sin cambio."""
    antes = await _hash_en_base(esc202, esc202["u_a"])
    r = await http_client.post(f"/api/v1/users/{esc202['u_a']}/password",
                               headers=_token(esc202["super"]),
                               json={"new_password": "R202-nueva-123"})
    assert r.status_code in (400, 403, 404), r.text
    assert await _hash_en_base(esc202, esc202["u_a"]) == antes, (
        "la contraseña cambió a pesar de la denegación")


async def test_r202_02_super_situado_restablece_en_su_empresa(http_client, esc202):
    """`AC-R202-02` (control) — la vía legítima del administrador global situado."""
    r = await http_client.post(f"/api/v1/users/{esc202['u_a']}/password",
                               headers=_token(esc202["super"], esc202["a"]),
                               json={"new_password": "R202-nueva-123"})
    assert r.status_code == 204, r.text


async def test_r202_03_admin_de_empresa_restablece_en_su_empresa(http_client, esc202):
    """`AC-R202-03` — `users:update` de la empresa es autoridad suficiente (hoy 403)."""
    r = await http_client.post(f"/api/v1/users/{esc202['u_a']}/password",
                               headers=_token(esc202["admin_a"]),
                               json={"new_password": "R202-nueva-123"})
    assert r.status_code == 204, r.text


async def test_r202_04_admin_de_empresa_no_cruza_el_inquilino(http_client, esc202):
    """`AC-R202-04` — cross-company sigue fail-closed (403/404)."""
    antes = await _hash_en_base(esc202, esc202["u_b"])
    r = await http_client.post(f"/api/v1/users/{esc202['u_b']}/password",
                               headers=_token(esc202["admin_a"]),
                               json={"new_password": "R202-nueva-123"})
    assert r.status_code in (403, 404), r.text
    assert await _hash_en_base(esc202, esc202["u_b"]) == antes


async def test_r202_06_la_auditoria_lleva_la_empresa_efectiva_del_actor(http_client, esc202):
    """`AC-R202-06` — el asiento del restablecimiento queda con la empresa del actor."""
    r = await http_client.post(f"/api/v1/users/{esc202['u_a']}/password",
                               headers=_token(esc202["admin_a"]),
                               json={"new_password": "R202-nueva-123"})
    assert r.status_code == 204, r.text
    asiento = await _ultimo_asiento(esc202, esc202["u_a"])
    assert asiento is not None, "el restablecimiento no dejó asiento"
    assert asiento.company_id == esc202["a"], (
        "la auditoría no lleva la empresa efectiva del actor")
    assert asiento.user_id == esc202["admin_a"]
