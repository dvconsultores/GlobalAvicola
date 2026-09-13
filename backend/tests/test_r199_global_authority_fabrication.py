"""`R-199` · La autoridad global no se fabrica desde un rol de inquilino.

Diseño: `audit/ga-claude-final-audit/specs/R-199/R-199_RED_E2E_UAT_DESIGN.md §1`.

```
ROL DE SISTEMA     company_id NULL   · plantilla de producto
ROL DE INQUILINO   company_id = X    · nunca porta ("*", scope_type="all")
AUTORIDAD GLOBAL   ("*", …, "all") EN UN ROL DE SISTEMA — no basta el permiso suelto
```

`RED-01…06` fijan el defecto (rojas en HEAD); `CTL-07…09` son controles que ya
pasan y deben seguir pasando; `CTL-10` es la RED de higiene (`C-07`,
`get_company_filter` muerto). PREFIJO de escenario `R199-`.
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
from app.auth.security import create_access_token, create_refresh_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R199-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc199(test_database_url):
    """Empresas A y B · rol de sistema global · rol de inquilino **envenenado**.

    ```
    rol_admin_a   company_id=A     users:read/create/update/delete (company)
    rol_a         company_id=A     operations:read
    rol_env       company_id=A     ("*", …, "all")  ← insertado directo: resultado de RED-01 o dato heredado
    rol_global    company_id=NULL  ("*", …, "all")  ← autoridad global legítima
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
        rol_a = _rol("OperA", a.id)
        rol_env = _rol("EnvA", a.id)
        rol_global = _rol("Global", None)
        await s.flush()

        for accion in (PermissionAction.READ, PermissionAction.CREATE,
                       PermissionAction.UPDATE, PermissionAction.DELETE):
            s.add(Permission(role_id=rol_admin_a.id, module="users", action=accion,
                             scope_type="company"))
        s.add(Permission(role_id=rol_a.id, module="operations",
                         action=PermissionAction.READ, scope_type="company"))
        for r in (rol_env, rol_global):
            for accion in PermissionAction:
                s.add(Permission(role_id=r.id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="R199",
                        email=f"{PREFIJO}{marca.lower()}-{uuid.uuid4().hex[:6]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        admin_a = _usuario(a.id, "ADMINA", rol_admin_a)
        user_a = _usuario(a.id, "USERA", rol_a)
        user_env = _usuario(a.id, "ENVA", rol_env)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([admin_a, user_a, user_env, superadmin])
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "b": b.id,
                 "admin_a": admin_a.id, "user_a": user_a.id,
                 "user_env": user_env.id, "super": superadmin.id,
                 "rol_a": rol_a.id, "rol_env": rol_env.id,
                 "rol_global": rol_global.id, "rol_admin_a": rol_admin_a.id,
                 "url": test_database_url}
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


async def _rol_en_base(esc199, role_id: int) -> dict:
    from app.auth.models import Role

    motor = create_async_engine(esc199["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            r = (await s.execute(select(Role).where(Role.id == role_id))).scalar_one()
            return {"name": r.name, "company_id": r.company_id, "is_active": r.is_active}
    finally:
        await motor.dispose()


async def _permisos_en_base(esc199, role_id: int) -> set[tuple[str, str, str]]:
    from app.auth.models import Permission

    motor = create_async_engine(esc199["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            filas = (await s.execute(
                select(Permission).where(Permission.role_id == role_id))).scalars().all()
            return {(p.module, getattr(p.action, "value", p.action), p.scope_type)
                    for p in filas}
    finally:
        await motor.dispose()


async def _rol_de_usuario(esc199, user_id: int) -> int | None:
    from app.auth.models import User

    motor = create_async_engine(esc199["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return (await s.execute(
                select(User.role_id).where(User.id == user_id))).scalar_one()
    finally:
        await motor.dispose()


async def _recuentos(esc199) -> tuple[int, int]:
    """`AC13`: recuento global de `roles` y `permissions` — nada parcial."""
    motor = create_async_engine(esc199["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            roles = (await s.execute(text("SELECT count(*) FROM roles"))).scalar_one()
            permisos = (await s.execute(text("SELECT count(*) FROM permissions"))).scalar_one()
            return int(roles), int(permisos)
    finally:
        await motor.dispose()


async def _auditorias_de_rechazo(esc199, company_id: int) -> int:
    """`AC12` · `C-05`: el intento denegado deja asiento que sobrevive al `403`."""
    from app.audit.models import AuditAction, AuditLog

    motor = create_async_engine(esc199["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            filas = (await s.execute(select(AuditLog).where(
                AuditLog.action == AuditAction.PERMISSION_CHANGE,
                AuditLog.company_id == company_id,
                AuditLog.comments.ilike("%rechazado%")))).scalars().all()
            return len(filas)
    finally:
        await motor.dispose()


# ── RED-01 … RED-06 · el defecto (rojas en HEAD) ─────────────────────────────

async def test_r199_01_crear_rol_de_inquilino_con_comodin_global_se_rechaza(http_client, esc199):
    """`AC01` · `AC12` · `AC13` — `OD-13.c`/`GAP-01`."""
    antes = await _recuentos(esc199)
    marca = f"{PREFIJO}X-{uuid.uuid4().hex[:6]}"
    r = await http_client.post("/api/v1/roles", headers=_token(esc199["admin_a"]),
                               json={"name": marca,
                                     "permissions": [{"module": "*", "action": "read",
                                                      "scope_type": "all"}]})
    assert r.status_code == 403, r.text
    assert await _recuentos(esc199) == antes, "una denegación no deja fila parcial"
    assert await _auditorias_de_rechazo(esc199, esc199["a"]) >= 1, (
        "el intento denegado debe quedar registrado (C-05)")


async def test_r199_02_editar_rol_de_inquilino_para_inyectar_el_comodin_se_rechaza(http_client, esc199):
    """`AC02` — la edición no es una puerta trasera del alta."""
    antes = await _permisos_en_base(esc199, esc199["rol_a"])
    r = await http_client.put(f"/api/v1/roles/{esc199['rol_a']}",
                              headers=_token(esc199["admin_a"]),
                              json={"permissions": [{"module": "*", "action": "update",
                                                     "scope_type": "all"}]})
    assert r.status_code == 403, r.text
    assert await _permisos_en_base(esc199, esc199["rol_a"]) == antes, (
        "los permisos del rol quedaron alterados")


async def test_r199_03_un_rol_de_inquilino_envenenado_no_es_asignable(http_client, esc199):
    """`AC03` — asignable ≠ visible: la rama de inquilino también pregunta por el comodín."""
    r = await http_client.put(f"/api/v1/users/{esc199['user_a']}",
                              headers=_token(esc199["admin_a"]),
                              json={"role_id": esc199["rol_env"]})
    assert r.status_code == 403, r.text
    assert await _rol_de_usuario(esc199, esc199["user_a"]) == esc199["rol_a"], (
        "el rol envenenado se asignó")

    marca = f"{PREFIJO}NEW-{uuid.uuid4().hex[:6]}"
    r2 = await http_client.post("/api/v1/users", headers=_token(esc199["admin_a"]),
                                json={"first_name": "N", "last_name": "R199",
                                      "email": f"{marca.lower()}@globalavicola.com",
                                      "username": marca, "password": "x1234567",
                                      "role_id": esc199["rol_env"]})
    assert r2.status_code == 403, r2.text


async def test_r199_04_un_rol_de_inquilino_envenenado_no_confiere_autoridad_global(http_client, esc199):
    """`AC04` — la capacidad global se computa del permiso **en un rol de sistema**."""
    me = await http_client.get("/api/v1/me", headers=_token(esc199["user_env"]))
    assert me.status_code == 200, me.text
    assert me.json()["is_super_admin"] is False, (
        "un rol de inquilino con el comodín concedió is_super_admin")

    sw = await http_client.post("/api/v1/switch-company", headers=_token(esc199["user_env"]),
                                json={"company_id": esc199["b"]})
    assert sw.status_code == 403, sw.text

    lst = await http_client.get("/api/v1/users", headers=_token(esc199["user_env"]))
    assert lst.status_code == 200, lst.text
    assert {u["company_id"] for u in lst.json()} == {esc199["a"]}, (
        "el listado de usuarios cruzó el inquilino")


async def test_r199_05_la_renovacion_no_honra_un_contexto_ajeno_con_rol_envenenado(http_client, esc199):
    """`AC05` — la renovación recalcula: manda la empresa persistida, no el claim."""
    refresh = create_refresh_token({"sub": str(esc199["user_env"]),
                                    "company_id": esc199["b"]})
    r = await http_client.post("/api/v1/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]
    me = await http_client.get("/api/v1/me",
                               headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200, me.text
    assert me.json()["effective_company_id"] == esc199["a"], (
        "la renovación honró un contexto ajeno reclamado")


async def test_r199_06_modulo_fuera_de_catalogo_es_422(http_client, esc199):
    """`AC06` · `GAP-16` — el catálogo del producto es cerrado (`MODULOS ∪ {"*"}`)."""
    antes = await _recuentos(esc199)
    r = await http_client.post("/api/v1/roles", headers=_token(esc199["admin_a"]),
                               json={"name": f"{PREFIJO}H-{uuid.uuid4().hex[:6]}",
                                     "permissions": [{"module": "hacking", "action": "read",
                                                      "scope_type": "company"}]})
    assert r.status_code == 422, r.text
    assert await _recuentos(esc199) == antes


async def test_r199_06_accion_invalida_es_422_y_no_500(http_client, esc199):
    """`AC07` — hoy `PermissionAction("fly")` revienta en `500`."""
    r = await http_client.post("/api/v1/roles", headers=_token(esc199["admin_a"]),
                               json={"name": f"{PREFIJO}F-{uuid.uuid4().hex[:6]}",
                                     "permissions": [{"module": "lots", "action": "fly",
                                                      "scope_type": "company"}]})
    assert r.status_code == 422, r.text


async def test_r199_06_alcance_invalido_es_422(http_client, esc199):
    """`AC08` — `scope_type` sólo `{all, company, farm}`."""
    r = await http_client.post("/api/v1/roles", headers=_token(esc199["admin_a"]),
                               json={"name": f"{PREFIJO}G-{uuid.uuid4().hex[:6]}",
                                     "permissions": [{"module": "lots", "action": "read",
                                                      "scope_type": "galaxy"}]})
    assert r.status_code == 422, r.text


# ── CTL-07 … CTL-09 · controles (verdes en HEAD y después) ───────────────────

async def test_r199_07_la_autoridad_global_sigue_creando_plantillas_con_comodin(http_client, esc199):
    """`AC09` — la puerta legítima no se cierra."""
    marca = f"{PREFIJO}Plantilla-{uuid.uuid4().hex[:6]}"
    r = await http_client.post("/api/v1/roles", headers=_token(esc199["super"]),
                               json={"name": marca,
                                     "permissions": [{"module": "*", "action": "read",
                                                      "scope_type": "all"}]})
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    assert (await _rol_en_base(esc199, rid))["company_id"] is None

    # El actor global **sin contexto** no crea usuarios por API («No hay empresa
    # efectiva en la que crear el usuario») — aquí se prueba la CAPACIDAD del rol,
    # así que el usuario del control se inserta directo, como dato real de plantel.
    from app.auth.models import User
    from app.auth.security import hash_password
    motor = create_async_engine(esc199["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            nuevo = User(first_name="G", last_name="R199",
                         email=f"{PREFIJO.lower()}g-{uuid.uuid4().hex[:6]}@globalavicola.com",
                         username=f"{PREFIJO}G-{uuid.uuid4().hex[:6]}",
                         hashed_password=hash_password("x1234567"),
                         company_id=None, role_id=rid, is_active=True)
            s.add(nuevo)
            await s.commit()
            nuevo_id = nuevo.id
    finally:
        await motor.dispose()

    me = await http_client.get("/api/v1/me", headers=_token(nuevo_id))
    assert me.status_code == 200, me.text
    assert me.json()["is_super_admin"] is True


async def test_r199_08_el_rol_de_inquilino_ordinario_se_crea_asigna_y_no_es_global(http_client, esc199):
    """`AC10` — el actor de empresa no pierde nada (lo que envía `RolesPage`)."""
    marca = f"{PREFIJO}Ord-{uuid.uuid4().hex[:6]}"
    r = await http_client.post("/api/v1/roles", headers=_token(esc199["admin_a"]),
                               json={"name": marca,
                                     "permissions": [{"module": "lots", "action": "read",
                                                      "scope_type": "all"},
                                                     {"module": "operations", "action": "create",
                                                      "scope_type": "all"}]})
    assert r.status_code in (200, 201), r.text
    rid = r.json()["id"]

    r2 = await http_client.put(f"/api/v1/users/{esc199['user_a']}",
                               headers=_token(esc199["admin_a"]),
                               json={"role_id": rid})
    assert r2.status_code == 200, r2.text

    me = await http_client.get("/api/v1/me", headers=_token(esc199["user_a"]))
    assert me.json()["is_super_admin"] is False
    assert "lots:read" in me.json()["permissions"]


async def test_r199_09_el_comodin_de_modulo_con_alcance_de_empresa_sigue_admitido(http_client, esc199):
    """`AC11` · `C-03` — `("*", read, company)` es atajo de catálogo, no autoridad global."""
    marca = f"{PREFIJO}Comodin-{uuid.uuid4().hex[:6]}"
    r = await http_client.post("/api/v1/roles", headers=_token(esc199["admin_a"]),
                               json={"name": marca,
                                     "permissions": [{"module": "*", "action": "read",
                                                      "scope_type": "company"}]})
    assert r.status_code in (200, 201), r.text
    rid = r.json()["id"]

    r2 = await http_client.put(f"/api/v1/users/{esc199['user_a']}",
                               headers=_token(esc199["admin_a"]),
                               json={"role_id": rid})
    assert r2.status_code == 200, r2.text

    me = await http_client.get("/api/v1/me", headers=_token(esc199["user_a"]))
    assert me.json()["is_super_admin"] is False
    lots = await http_client.get("/api/v1/lots", headers=_token(esc199["user_a"]))
    assert lots.status_code == 200, lots.text


# ── CTL-10 · higiene `C-07` (RED aceptada: se corrige en C2) ─────────────────

async def test_r199_10_no_queda_atajo_legado_sin_filtro():
    """`AC17` · `C-07` — `get_company_filter` (fail-open, muerto) se retira en C2."""
    import app.auth.security as s
    import app.dependencies as d

    assert not hasattr(s, "get_company_filter"), "security.py aún expone get_company_filter"
    assert not hasattr(d, "get_company_filter"), "dependencies.py aún re-exporta get_company_filter"
