"""Propiedad de roles y permisos — `OD-13` · `R-121` · `AC-R01`…`AC-R07`.

```
PERMISO  =  capacidad de producto        · global · excepción explícita de `RQ-03`
ROL      =  permisos + alcance           · `company_id NULL` sistema · concreto inquilino
VISIBLE  ≠  ASIGNABLE
```

El sujeto es un administrador de empresa **real**: tiene `users:read/create/update` explícitos
y **no** es Super Administrador. Es el actor que `R-113` creará.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "RTEN-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """Dos empresas, dos roles de inquilino y dos de sistema.

    ```
    ROL_A       company_id = A          rol de inquilino
    ROL_B       company_id = B          rol de inquilino — invisible para el actor de A
    SISTEMA     company_id = NULL       plantilla de producto, sin autoridad global
    GLOBAL      company_id = NULL       `("*", …, "all")` — autoridad global
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
        rol_a = _rol("InquilinoA", a.id)
        rol_b = _rol("InquilinoB", b.id)
        rol_sistema = _rol("Sistema", None)
        rol_global = _rol("Global", None)
        await s.flush()

        for accion in (PermissionAction.READ, PermissionAction.CREATE,
                       PermissionAction.UPDATE, PermissionAction.DELETE):
            s.add(Permission(role_id=rol_admin_a.id, module="users", action=accion,
                             scope_type="company"))
        for r in (rol_a, rol_b, rol_sistema):
            s.add(Permission(role_id=r.id, module="operations",
                             action=PermissionAction.READ, scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Rol",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        admin_a = _usuario(a.id, "ADMINA", rol_admin_a)
        user_a = _usuario(a.id, "USERA", rol_a)
        user_b = _usuario(b.id, "USERB", rol_b)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([admin_a, user_a, user_b, superadmin])
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "b": b.id, "admin_a": admin_a.id, "user_a": user_a.id,
                 "user_b": user_b.id, "super": superadmin.id,
                 "rol_a": rol_a.id, "rol_b": rol_b.id, "rol_sistema": rol_sistema.id,
                 "rol_global": rol_global.id, "rol_admin_a": rol_admin_a.id,
                 "nombre_a": rol_a.name, "nombre_b": rol_b.name,
                 "nombre_sistema": rol_sistema.name, "url": test_database_url}
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


async def _rol_en_base(esc, role_id: int) -> dict:
    from app.auth.models import Role

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            r = (await s.execute(select(Role).where(Role.id == role_id))).scalar_one()
            return {"name": r.name, "company_id": r.company_id,
                    "description": r.description, "is_active": r.is_active}
    finally:
        await motor.dispose()


async def _rol_de_usuario(esc, user_id: int) -> int | None:
    from app.auth.models import User

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return (await s.execute(
                select(User.role_id).where(User.id == user_id))).scalar_one()
    finally:
        await motor.dispose()


# ── `AC-R01` · listar ─────────────────────────────────────────────────────────

async def test_r01_el_listado_no_muestra_roles_de_otra_empresa(http_client, esc):
    r = await http_client.get("/api/v1/roles", headers=_token(esc["admin_a"]))
    assert r.status_code == 200, r.text
    nombres = {x["name"] for x in r.json()}

    assert esc["nombre_a"] in nombres, "debe ver los roles de su empresa"
    assert esc["nombre_b"] not in nombres, "fuga: apareció un rol de la empresa B"


async def test_r01_las_plantillas_de_sistema_si_se_ven(http_client, esc):
    """`OD-13.c`: verlas es necesario para elegir. Asignarlas es otra pregunta."""
    r = await http_client.get("/api/v1/roles", headers=_token(esc["admin_a"]))
    assert r.status_code == 200, r.text
    assert esc["nombre_sistema"] in {x["name"] for x in r.json()}


# ── `AC-R02` · crear ──────────────────────────────────────────────────────────

async def test_r02_el_rol_nace_en_la_empresa_del_actor(http_client, esc):
    marca = f"{PREFIJO}NUEVO-{uuid.uuid4().hex[:6]}"
    r = await http_client.post("/api/v1/roles", headers=_token(esc["admin_a"]),
                               json={"name": marca, "description": "d", "permissions": []})
    assert r.status_code in (200, 201), r.text
    assert (await _rol_en_base(esc, r.json()["id"]))["company_id"] == esc["a"], (
        "el rol no quedó en la empresa del actor")


async def test_r02_la_autoridad_global_crea_plantillas_de_sistema(http_client, esc):
    marca = f"{PREFIJO}PLANTILLA-{uuid.uuid4().hex[:6]}"
    r = await http_client.post("/api/v1/roles", headers=_token(esc["super"]),
                               json={"name": marca, "description": "d", "permissions": []})
    assert r.status_code in (200, 201), r.text
    assert (await _rol_en_base(esc, r.json()["id"]))["company_id"] is None


# ── `AC-R03` · `AC-R04` · editar ──────────────────────────────────────────────

async def test_r03_no_se_edita_el_rol_de_otra_empresa(http_client, esc):
    antes = await _rol_en_base(esc, esc["rol_b"])
    r = await http_client.put(f"/api/v1/roles/{esc['rol_b']}",
                              headers=_token(esc["admin_a"]),
                              json={"name": "TOMADO"})
    assert r.status_code == 404, r.text
    assert await _rol_en_base(esc, esc["rol_b"]) == antes


async def test_r04_un_actor_de_empresa_no_edita_una_plantilla_de_sistema(http_client, esc):
    """`OD-13.e`. Verla no basta."""
    antes = await _rol_en_base(esc, esc["rol_sistema"])
    r = await http_client.put(f"/api/v1/roles/{esc['rol_sistema']}",
                              headers=_token(esc["admin_a"]),
                              json={"name": "TOMADA"})
    assert r.status_code in (403, 404), r.text
    assert await _rol_en_base(esc, esc["rol_sistema"]) == antes


async def test_r03_el_rol_propio_si_se_edita(http_client, esc):
    r = await http_client.put(f"/api/v1/roles/{esc['rol_a']}",
                              headers=_token(esc["admin_a"]),
                              json={"description": "editada"})
    assert r.status_code == 200, r.text
    assert (await _rol_en_base(esc, esc["rol_a"]))["description"] == "editada"


# ── `AC-R05` · `AC-R06` · asignar ─────────────────────────────────────────────

async def test_r05_se_asigna_el_rol_propio_a_un_usuario_propio(http_client, esc):
    r = await http_client.put(f"/api/v1/users/{esc['user_a']}",
                              headers=_token(esc["admin_a"]),
                              json={"role_id": esc["rol_admin_a"]})
    assert r.status_code == 200, r.text
    assert await _rol_de_usuario(esc, esc["user_a"]) == esc["rol_admin_a"]


async def test_r05_no_se_asigna_un_rol_de_otra_empresa(http_client, esc):
    antes = await _rol_de_usuario(esc, esc["user_a"])
    r = await http_client.put(f"/api/v1/users/{esc['user_a']}",
                              headers=_token(esc["admin_a"]),
                              json={"role_id": esc["rol_b"]})
    assert r.status_code in (403, 404, 422), r.text
    assert await _rol_de_usuario(esc, esc["user_a"]) == antes, "el rol ajeno se asignó"


async def test_r05_la_plantilla_de_sistema_ordinaria_si_se_asigna(http_client, esc):
    """`OD-13.c`. Sin esta, «no se asigna la global» sería compatible con «no se asigna nada»."""
    r = await http_client.put(f"/api/v1/users/{esc['user_a']}",
                              headers=_token(esc["admin_a"]),
                              json={"role_id": esc["rol_sistema"]})
    assert r.status_code == 200, r.text
    assert await _rol_de_usuario(esc, esc["user_a"]) == esc["rol_sistema"]


async def test_r06_la_autoridad_global_no_se_reparte_desde_una_empresa(http_client, esc):
    antes = await _rol_de_usuario(esc, esc["user_a"])
    r = await http_client.put(f"/api/v1/users/{esc['user_a']}",
                              headers=_token(esc["admin_a"]),
                              json={"role_id": esc["rol_global"]})
    assert r.status_code == 403, r.text
    assert await _rol_de_usuario(esc, esc["user_a"]) == antes


# ── `AC-R07` · el permiso es de producto ──────────────────────────────────────

async def test_r07_el_catalogo_de_permisos_es_global(http_client, esc):
    """No hay catálogo por inquilino: el mismo para todos, porque describe el producto."""
    a = await http_client.get("/api/v1/roles/permissions-catalog",
                              headers=_token(esc["admin_a"]))
    g = await http_client.get("/api/v1/roles/permissions-catalog",
                              headers=_token(esc["super"]))
    assert a.status_code == 200 and g.status_code == 200, (a.text, g.text)
    assert a.json() == g.json(), "el catálogo de capacidades difiere por inquilino"
    assert "business_units" in a.json()["modules"]
