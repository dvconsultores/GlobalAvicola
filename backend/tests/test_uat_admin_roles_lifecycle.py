"""`SPEC 013` · UAT Administración — ciclo de vida de roles (`AC-RL-01`…`AC-RL-06`).

Cubre el lote `B2`: los hallazgos `AR-01`, `AR-01b`, `AR-09`, `AR-18` y `AR-20` de la
sesión de UAT del 30-10-2026, con las decisiones vinculantes del Owner:

```
DR-1  un rol con usuarios ACTIVOS no se puede dar de baja (409); un rol inactivo
      NUNCA confiere permisos ni es asignable, y se puede reactivar
DR-2  un rol exige >= 1 permiso al crear y al editar (422)
```

```
AC-RL-01  baja bloqueada con usuarios activos asignados, con el número en el mensaje
AC-RL-02  un rol inactivo no confiere permisos ni autoridad global, con el MISMO token
AC-RL-03  un rol inactivo no es asignable; re-guardar el mismo rol ya asignado sí
AC-RL-04  `GET /roles?include_inactive=true` y reactivación, sin mezclar empresas
AC-RL-05  `422` por conjunto de permisos vacío, en alta y en edición, sin mutar nada
AC-RL-06  la edición de rol deja el diff en auditoría (sin secretos)
```

Todo esto se decide en el backend: ocultar un botón en la interfaz no impide que un `PUT`
directo desactive un rol en uso, ni que un rol inactivo siga autorizando.

PREFIJOS propios para poder limpiar sin tocar la siembra: roles `RL-TEST-`, usuarios
`rl_test_` y empresas `RL-TEST-EMPRESA-`.
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
from app.auth.security import create_access_token

PREFIJO_ROL = "RL-TEST-"
PREFIJO_USUARIO = "rl_test_"
PREFIJO_EMPRESA = "RL-TEST-EMPRESA-"

CLAVE = "ClaveRl2026x"

#: Permisos del actor de empresa que administra roles en estas pruebas.
#:
#: `users:*` es lo que exige la administración de acceso; `audit:read` y `lots:read` están
#: además para que los roles que estas pruebas crean y asignan no dependan de nada que el
#: actor no posea — la regla de subconjunto es de otro lote, pero no se escribe un
#: escenario que la contradiga.
PERMISOS_DEL_ACTOR = [
    {"module": "users", "action": "read", "scope_type": "company"},
    {"module": "users", "action": "create", "scope_type": "company"},
    {"module": "users", "action": "update", "scope_type": "company"},
    {"module": "users", "action": "delete", "scope_type": "company"},
    {"module": "audit", "action": "read", "scope_type": "company"},
    {"module": "lots", "action": "read", "scope_type": "company"},
]


def _permiso(module: str, action: str = "read", scope_type: str = "company") -> dict:
    return {"module": module, "action": action, "scope_type": scope_type}


# ══════════════════════════════════════════════════════════════════════════════
#  Limpieza — prefijos propios, nunca la siembra
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.auth.models import Permission, Role, User
    from app.masters.models import Company

    async with e.begin() as c:
        empresas = (await c.execute(
            select(Company.id).where(Company.name.like(f"{PREFIJO_EMPRESA}%")))).scalars().all()
        usuarios = (await c.execute(
            select(User.id).where(User.username.like(f"{PREFIJO_USUARIO}%")))).scalars().all()
        roles = (await c.execute(
            select(Role.id).where(Role.name.like(f"{PREFIJO_ROL}%")))).scalars().all()
        ids_usuarios = [str(u) for u in usuarios]
        if usuarios or ids_usuarios:
            await c.execute(delete(AuditLog).where(or_(
                AuditLog.user_id.in_(usuarios) if usuarios else False,
                and_(AuditLog.entity_type == "user", AuditLog.entity_id.in_(ids_usuarios)),
            )))
        if roles:
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "role",
                AuditLog.entity_id.in_([str(r) for r in roles])))
        if empresas:
            # `audit_logs.company_id` es clave foránea: nada de la empresa sobrevive.
            await c.execute(delete(AuditLog).where(AuditLog.company_id.in_(empresas)))
        if usuarios:
            await c.execute(delete(User).where(User.id.in_(usuarios)))
        if roles:
            await c.execute(delete(Permission).where(Permission.role_id.in_(roles)))
            await c.execute(delete(Role).where(Role.id.in_(roles)))
        if empresas:
            await c.execute(delete(Company).where(Company.id.in_(empresas)))
    await e.dispose()


@pytest_asyncio.fixture
async def escenario(motor, test_database_url):
    """Dos empresas con su administrador de acceso (`users:*` en la suya, sin comodín).

    ```
    EMPRESA A   admin A  · `users:*` + `audit:read` + `lots:read`   (el actor)
    EMPRESA B   admin B  · lo mismo, en la suya
                ROL_SOLO_B — rol de B que el actor de A no debe ver ni con el flag
    ```

    La empresa B existe por `AC-RL-04`: el flag de inactivos no puede convertirse en una
    puerta lateral que mezcle inquilinos.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    sufijo = uuid.uuid4().hex[:8]
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO_EMPRESA}A-{sufijo}", is_active=True)
        b = Company(name=f"{PREFIJO_EMPRESA}B-{sufijo}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        rol_admin_a = Role(name=f"{PREFIJO_ROL}ADMIN-A-{sufijo}", company_id=a.id, is_active=True)
        rol_admin_b = Role(name=f"{PREFIJO_ROL}ADMIN-B-{sufijo}", company_id=b.id, is_active=True)
        rol_solo_b = Role(name=f"{PREFIJO_ROL}SOLO-B-{sufijo}", company_id=b.id, is_active=True)
        s.add_all([rol_admin_a, rol_admin_b, rol_solo_b])
        await s.flush()

        for rol_admin in (rol_admin_a, rol_admin_b):
            for perm in PERMISOS_DEL_ACTOR:
                s.add(Permission(role_id=rol_admin.id, module=perm["module"],
                                 action=PermissionAction(perm["action"]),
                                 scope_type=perm["scope_type"]))
        s.add(Permission(role_id=rol_solo_b.id, module="lots",
                         action=PermissionAction.READ, scope_type="company"))

        def _admin(company_id, marca, role_id):
            return User(first_name=marca, last_name="Ciclo",
                        email=f"{PREFIJO_USUARIO}{marca.lower()}-{sufijo}@example.com",
                        username=f"{PREFIJO_USUARIO}{marca.lower()}-{sufijo}",
                        hashed_password=hash_password(CLAVE),
                        company_id=company_id, role_id=role_id, is_active=True)

        admin_a = _admin(a.id, "ADMINA", rol_admin_a.id)
        admin_b = _admin(b.id, "ADMINB", rol_admin_b.id)
        s.add_all([admin_a, admin_b])
        await s.flush()
        await s.commit()
        return {
            "empresa_a": a.id, "empresa_b": b.id,
            "admin_a": admin_a.id, "admin_b": admin_b.id,
            "rol_solo_b": rol_solo_b.id, "nombre_solo_b": rol_solo_b.name,
            "sufijo": sufijo, "url": test_database_url,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  Utilidades
# ══════════════════════════════════════════════════════════════════════════════

def _token(user_id: int, company_id: int | None = None) -> dict:
    """Cabecera de un usuario real; la empresa y los permisos salen de la base."""
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


def _marca(texto: str) -> str:
    return f"{PREFIJO_ROL}{texto}-{uuid.uuid4().hex[:8]}"


async def _alta_rol(http, cabeceras, nombre: str, *, permisos=None):
    return await http.post("/api/v1/roles", headers=cabeceras, json={
        "name": nombre, "description": "Ciclo de vida de roles",
        "permissions": [_permiso("lots")] if permisos is None else permisos,
    })


async def _alta_usuario(http, cabeceras, *, role_id: int | None = None,
                        quien: str | None = None):
    marca = quien or uuid.uuid4().hex[:8]
    cuerpo = {"first_name": "Ciclo", "last_name": "Vida",
              "email": f"{PREFIJO_USUARIO}u-{marca}@example.com",
              "username": f"{PREFIJO_USUARIO}u-{marca}", "password": CLAVE}
    if role_id is not None:
        cuerpo["role_id"] = role_id
    return await http.post("/api/v1/users", headers=cabeceras, json=cuerpo)


async def _nombres_de_roles(http, cabeceras, *, include_inactive: bool = False) -> set[str]:
    consulta = "/api/v1/roles" + ("?include_inactive=true" if include_inactive else "")
    r = await http.get(consulta, headers=cabeceras)
    assert r.status_code == 200, r.text
    return {x["name"] for x in r.json()}


# ── lectura directa de la base: la verdad, no lo que la API quiso contar ──────

async def _rol_en_base(escenario, role_id: int) -> dict:
    from app.auth.models import Role

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            r = (await s.execute(select(Role).where(Role.id == role_id))).scalar_one()
            return {"name": r.name, "is_active": r.is_active, "company_id": r.company_id}
    finally:
        await e.dispose()


async def _permisos_en_base(escenario, role_id: int) -> list[tuple[str, str, str]]:
    from app.auth.models import Permission

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            filas = (await s.execute(
                select(Permission).where(Permission.role_id == role_id))).scalars().all()
            return sorted((p.module, getattr(p.action, "value", str(p.action)), p.scope_type)
                          for p in filas)
    finally:
        await e.dispose()


async def _rol_por_nombre(escenario, nombre: str) -> dict | None:
    from app.auth.models import Role

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            fila = (await s.execute(
                select(Role).where(Role.name == nombre))).scalar_one_or_none()
            return None if fila is None else {"id": fila.id, "is_active": fila.is_active}
    finally:
        await e.dispose()


async def _rol_de_usuario(escenario, user_id: int) -> int | None:
    from app.auth.models import User

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            return (await s.execute(
                select(User.role_id).where(User.id == user_id))).scalar_one()
    finally:
        await e.dispose()


async def _contar_usuarios(escenario) -> int:
    from app.auth.models import User

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            return (await s.execute(select(func.count()).select_from(User))).scalar_one()
    finally:
        await e.dispose()


# ── mutaciones por SQL: fuerzan estados que la API (a propósito) ya no permite ─

async def _desactivar_rol_por_sql(escenario, role_id: int) -> None:
    """`AC-RL-02` · el rol se apaga **sin** pasar por la API.

    Es el escenario real del hallazgo: un rol desactivado en el pasado, o por otra vía, con
    usuarios todavía asignados. La defensa en profundidad se prueba sobre el estado, no
    sobre cómo se llegó a él.
    """
    from app.auth.models import Role

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            await s.execute(update(Role).where(Role.id == role_id).values(is_active=False))
            await s.commit()
    finally:
        await e.dispose()


async def _asignar_rol_por_sql(escenario, user_id: int, role_id: int) -> None:
    """Deja a un usuario con un rol inactivo ya asignado (estado heredado)."""
    from app.auth.models import User

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            await s.execute(update(User).where(User.id == user_id).values(role_id=role_id))
            await s.commit()
    finally:
        await e.dispose()


async def _conceder_permiso_al_actor_por_sql(escenario, module: str,
                                             action: str = "read") -> None:
    """Amplía el rol del **actor** con un permiso, solo para la prueba que lo pide.

    `DR-3` exige que quien reparte posea. Se concede sobre el rol del propio actuante y
    dentro del test —no en `escenario`— para no cambiar la autoridad del escenario que
    comparten las demás pruebas de `AC-RL-01`…`AC-RL-05`.
    """
    from app.auth.models import Permission, PermissionAction, User

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            rol_id = (await s.execute(
                select(User.role_id).where(User.id == escenario["admin_a"]))).scalar_one()
            s.add(Permission(role_id=rol_id, module=module,
                             action=PermissionAction(action), scope_type="company"))
            await s.commit()
    finally:
        await e.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-RL-01` · no se da de baja un rol que alguien está usando
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_rl_01_la_baja_de_un_rol_con_usuarios_activos_es_409(
    http_client, escenario
):
    """`AR-01` · DR-1. En HEAD el rol se desactivaba en silencio y su gente quedaba con un
    rol muerto: seguía entrando, pero sin ninguna capacidad y sin saber por qué.

    El mensaje lleva el número de usuarios porque es lo que el administrador necesita para
    actuar; un `409` mudo lo obligaría a adivinar.
    """
    cab = _token(escenario["admin_a"])
    rol = (await _alta_rol(http_client, cab, _marca("CON-USUARIOS"))).json()
    usuario = await _alta_usuario(http_client, cab, role_id=rol["id"])
    assert usuario.status_code == 201, usuario.text

    r = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab,
                              json={"is_active": False})
    assert r.status_code == 409, (
        f"se desactivó un rol con un usuario activo asignado: {r.status_code} {r.text[:300]}")
    assert "1" in r.json()["detail"], r.json()["detail"]

    # Y no hay mutación parcial: el rol sigue vivo.
    assert (await _rol_en_base(escenario, rol["id"]))["is_active"] is True

    # Dado de baja el usuario, la baja del rol ya es legítima.
    baja_usuario = await http_client.delete(
        f"/api/v1/users/{usuario.json()['id']}", headers=cab)
    assert baja_usuario.status_code == 204, baja_usuario.text

    r2 = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab,
                               json={"is_active": False})
    assert r2.status_code == 200, (
        f"sin usuarios activos la baja debe pasar: {r2.status_code} {r2.text[:300]}")
    assert (await _rol_en_base(escenario, rol["id"]))["is_active"] is False


async def test_ac_rl_01_un_rol_sin_usuarios_o_solo_con_inactivos_si_se_da_de_baja(
    http_client, escenario
):
    """El control de `AC-RL-01`: la regla no puede cerrar la baja legítima.

    «Sin usuarios» y «solo con inactivos» son los dos casos con los que un administrador
    retira de verdad un rol del catálogo.
    """
    cab = _token(escenario["admin_a"])

    vacio = (await _alta_rol(http_client, cab, _marca("SIN-USUARIOS"))).json()
    baja = await http_client.put(f"/api/v1/roles/{vacio['id']}", headers=cab,
                                 json={"is_active": False})
    assert baja.status_code == 200, (
        f"un rol sin usuarios no se pudo dar de baja: {baja.status_code} {baja.text[:200]}")

    solo_inactivos = (await _alta_rol(http_client, cab, _marca("SOLO-INACTIVOS"))).json()
    usuario = (await _alta_usuario(http_client, cab, role_id=solo_inactivos["id"])).json()
    baja_usuario = await http_client.put(f"/api/v1/users/{usuario['id']}", headers=cab,
                                         json={"is_active": False})
    assert baja_usuario.status_code == 200, baja_usuario.text

    baja_rol = await http_client.put(f"/api/v1/roles/{solo_inactivos['id']}", headers=cab,
                                     json={"is_active": False})
    assert baja_rol.status_code == 200, (
        f"un usuario inactivo bloqueó la baja del rol: {baja_rol.status_code} "
        f"{baja_rol.text[:300]}")


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-RL-02` · un rol inactivo no confiere nada
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_rl_02_un_rol_inactivo_no_confiere_permisos_ni_autoridad(
    http_client, escenario
):
    """`AR-01` · `AC-RL-02`. Con el MISMO token y la MISMA fila de usuario.

    CONTROL y TRATAMIENTO sobre la misma llamada: lo único que cambia es `roles.is_active`.
    Un `403` sin control no distinguiría «el rol inactivo dejó de autorizar» de «ese permiso
    nunca funcionó». Se apaga por SQL porque la API ya lo impide (`AC-RL-01`), y el estado
    heredado es justo el que hay que volver inofensivo.
    """
    cab = _token(escenario["admin_a"])
    rol = (await _alta_rol(http_client, cab, _marca("AUDIT-Y-LOTES"),
                           permisos=[_permiso("audit"), _permiso("lots")])).json()
    usuario = (await _alta_usuario(http_client, cab, role_id=rol["id"])).json()
    sujeto = _token(usuario["id"])

    rutas = ("/api/v1/audit?limit=1", "/api/v1/lots")

    # CONTROL · con el rol activo, los permisos surten efecto.
    me = await http_client.get("/api/v1/me", headers=sujeto)
    assert me.status_code == 200, me.text
    assert "audit:read" in me.json()["permissions"], me.json()["permissions"]
    assert me.json()["is_super_admin"] is False
    for ruta in rutas:
        control = await http_client.get(ruta, headers=sujeto)
        assert control.status_code == 200, (
            f"CONTROL roto en {ruta}: {control.status_code} {control.text[:200]}")

    # TRATAMIENTO · el rol se apaga.
    await _desactivar_rol_por_sql(escenario, rol["id"])

    despues = await http_client.get("/api/v1/me", headers=sujeto)
    assert despues.status_code == 200, despues.text
    assert despues.json()["permissions"] == [], (
        f"un rol inactivo sigue confiriendo permisos: {despues.json()['permissions']}")
    assert despues.json()["is_super_admin"] is False

    for ruta in rutas:
        negado = await http_client.get(ruta, headers=sujeto)
        assert negado.status_code == 403, (
            f"un rol inactivo sigue autorizando {ruta}: {negado.status_code} "
            f"{negado.text[:200]}")


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-RL-03` · un rol inactivo no es asignable
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_rl_03_un_rol_inactivo_no_se_asigna(http_client, escenario):
    """`AR-01b` · DR-1. Asignarlo reintroduciría por la puerta de atrás el usuario sin
    capacidades que `AC-RL-01` acaba de evitar.
    """
    cab = _token(escenario["admin_a"])
    rol = (await _alta_rol(http_client, cab, _marca("INACTIVO-ASIGNABLE"))).json()
    baja = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab,
                                 json={"is_active": False})
    assert baja.status_code == 200, baja.text

    # Alta con ese rol ⇒ 409 y sin fila.
    antes = await _contar_usuarios(escenario)
    alta = await _alta_usuario(http_client, cab, role_id=rol["id"])
    assert alta.status_code == 409, (
        f"se creó un usuario con un rol inactivo: {alta.status_code} {alta.text[:300]}")
    assert "inactivo" in alta.json()["detail"].lower(), alta.json()["detail"]
    assert await _contar_usuarios(escenario) == antes, "una petición rechazada creó una fila"

    # Cambio de `role_id` a uno inactivo ⇒ 409 y conserva el que tenía (ninguno).
    otro = (await _alta_usuario(http_client, cab)).json()
    cambio = await http_client.put(f"/api/v1/users/{otro['id']}", headers=cab,
                                  json={"role_id": rol["id"]})
    assert cambio.status_code == 409, (
        f"se asignó un rol inactivo en la edición: {cambio.status_code} {cambio.text[:300]}")
    assert await _rol_de_usuario(escenario, otro["id"]) is None, "el rol inactivo se asignó"

    # Re-guardar el MISMO rol ya asignado no se re-valida: si no, la fila quedaría
    # imposible de editar (un usuario heredado no podría ni cambiar su nombre).
    await _asignar_rol_por_sql(escenario, otro["id"], rol["id"])
    reguardado = await http_client.put(
        f"/api/v1/users/{otro['id']}", headers=cab,
        json={"role_id": rol["id"], "first_name": "Reguardado"})
    assert reguardado.status_code == 200, (
        f"re-guardar el rol ya asignado se re-validó y bloqueó la edición: "
        f"{reguardado.status_code} {reguardado.text[:300]}")
    assert reguardado.json()["first_name"] == "Reguardado"


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-RL-04` · ver los inactivos y reactivarlos
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_rl_04_los_inactivos_se_listan_solo_bajo_peticion_y_se_reactivan(
    http_client, escenario
):
    """`AR-20` · un rol desactivado desaparecía de la única lista que existe, de modo que
    el administrador no podía volver a encontrarlo para reactivarlo (`DR-1`).
    """
    cab = _token(escenario["admin_a"])
    marca = _marca("REACTIVABLE")
    rol = (await _alta_rol(http_client, cab, marca)).json()

    assert marca in await _nombres_de_roles(http_client, cab), (
        "un rol recién creado no aparece en el listado por defecto")

    baja = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab,
                                 json={"is_active": False})
    assert baja.status_code == 200, baja.text
    assert marca not in await _nombres_de_roles(http_client, cab), (
        "el listado por defecto incluye inactivos")
    assert marca in await _nombres_de_roles(http_client, cab, include_inactive=True), (
        "el listado no ofrece los inactivos ni bajo petición: el rol queda irrecuperable")

    reactivar = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab,
                                      json={"is_active": True})
    assert reactivar.status_code == 200, (
        f"un rol inactivo no se pudo reactivar: {reactivar.status_code} {reactivar.text[:300]}")
    assert marca in await _nombres_de_roles(http_client, cab), (
        "tras reactivarlo no vuelve al listado por defecto")


async def test_ac_rl_04_el_flag_de_inactivos_no_mezcla_empresas(http_client, escenario):
    """`AC-RL-04` · el alcance de empresa no cambia con el flag.

    Sin esta prueba, `include_inactive` podría implementarse como «quitar el filtro» y
    llevarse por delante el aislamiento multiempresa.
    """
    cab_a = _token(escenario["admin_a"])
    cab_b = _token(escenario["admin_b"])

    baja = await http_client.put(f"/api/v1/roles/{escenario['rol_solo_b']}",
                                 headers=cab_b, json={"is_active": False})
    assert baja.status_code == 200, baja.text

    de_a = await _nombres_de_roles(http_client, cab_a, include_inactive=True)
    assert escenario["nombre_solo_b"] not in de_a, (
        "el flag de inactivos reveló un rol de otra empresa")

    # CONTROL: su dueño sí lo ve — el rol existe y está inactivo, no borrado.
    de_b = await _nombres_de_roles(http_client, cab_b, include_inactive=True)
    assert escenario["nombre_solo_b"] in de_b


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-RL-05` · un rol exige al menos un permiso
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_rl_05_un_rol_exige_al_menos_un_permiso(http_client, escenario):
    """`AR-18` · DR-2. Un rol sin permisos no es un rol: es una entrada de catálogo que
    solo sirve para dejar a alguien dentro del sistema sin poder hacer nada.
    """
    cab = _token(escenario["admin_a"])

    # Alta con el conjunto vacío ⇒ 422 y sin fila.
    marca = _marca("VACIO")
    alta = await http_client.post("/api/v1/roles", headers=cab, json={
        "name": marca, "description": "sin permisos", "permissions": []})
    assert alta.status_code == 422, (
        f"se creó un rol sin permisos: {alta.status_code} {alta.text[:300]}")
    assert "al menos un permiso" in alta.json()["detail"].lower(), alta.json()["detail"]
    assert await _rol_por_nombre(escenario, marca) is None, (
        "la petición rechazada dejó fila")

    # Edición que vacía el conjunto ⇒ 422 y los permisos quedan intactos.
    rol = (await _alta_rol(http_client, cab, _marca("CON-PERMISOS"),
                           permisos=[_permiso("audit"), _permiso("lots")])).json()
    antes = await _permisos_en_base(escenario, rol["id"])
    assert antes, "el rol de control debe nacer con permisos"

    vaciar = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab,
                                   json={"permissions": []})
    assert vaciar.status_code == 422, (
        f"se vació el conjunto de permisos: {vaciar.status_code} {vaciar.text[:300]}")
    assert "al menos un permiso" in vaciar.json()["detail"].lower(), vaciar.json()["detail"]
    assert await _permisos_en_base(escenario, rol["id"]) == antes, (
        "una edición rechazada mutó los permisos del rol")

    # Omitir `permissions` sigue siendo legítimo: renombrar no borra los permisos.
    renombrar = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab,
                                      json={"name": _marca("RENOMBRADO")})
    assert renombrar.status_code == 200, (
        f"editar el nombre sin enviar permisos falló: {renombrar.status_code} "
        f"{renombrar.text[:300]}")
    assert await _permisos_en_base(escenario, rol["id"]) == antes


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-RL-06` · la edición del rol deja el diff en auditoría
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_rl_06_la_edicion_de_rol_audita_el_diff_sin_secretos(
    http_client, escenario
):
    """`AR-09` · `GA-REM-032 AC03`. Antes se anotaba solo el nombre nuevo: no quedaba
    rastro de qué permiso se concedió ni de cuál se retiró, que es lo único que un auditor
    puede revisar después.
    """
    from app.audit.models import AuditAction, AuditLog

    cab = _token(escenario["admin_a"])
    marca = _marca("AUDITABLE")
    rol = (await _alta_rol(http_client, cab, marca,
                           permisos=[_permiso("audit"), _permiso("lots")])).json()

    # UAT-ADMIN-RBAC DR-3: el actor debe poseer lo que reparte (subconjunto); se le concede
    # en el escenario, la intención del test no cambia. Lo que se mide aquí es el diff que
    # deja la edición en auditoría (`AR-09`), no la escalada: el actor reparte `lots:create`
    # y para repartirlo tiene que tenerlo.
    await _conceder_permiso_al_actor_por_sql(escenario, "lots", "create")

    nuevo_nombre = f"{marca}-RENOMBRADO"
    edicion = await http_client.put(f"/api/v1/roles/{rol['id']}", headers=cab, json={
        "name": nuevo_nombre,
        "description": "descripción nueva",
        "permissions": [_permiso("lots"), _permiso("lots", "create")],
    })
    assert edicion.status_code == 200, edicion.text

    # El asiento es consultable por la API de auditoría, que es por donde lo verá un
    # auditor (`test_role_administration.py::test_t_092_04` fija el mismo productor).
    consulta = await http_client.get("/api/v1/audit", headers=cab, params={
        "entity_type": "role", "entity_id": str(rol["id"]),
        "action": AuditAction.PERMISSION_CHANGE.value, "limit": 50})
    assert consulta.status_code == 200, consulta.text
    visibles = [x for x in consulta.json()["logs"]
                if isinstance(x, dict) and x.get("entity_type") == "role"]
    assert visibles, "la edición del rol no dejó asiento consultable"

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            registros = (await s.execute(select(AuditLog).where(
                AuditLog.action == AuditAction.PERMISSION_CHANGE,
                AuditLog.entity_type == "role",
                AuditLog.entity_id == str(rol["id"])))).scalars().all()
    finally:
        await e.dispose()

    con_diff = [x for x in registros if x.previous_values and x.new_values]
    assert con_diff, (
        f"la edición del rol no dejó diff: {len(registros)} registro(s) de permiso")
    fila = con_diff[-1]
    previo, nuevo = fila.previous_values, fila.new_values

    for clave in ("nombre", "activo", "permisos"):
        assert clave in previo, f"falta {clave!r} en previous_values: {previo}"
        assert clave in nuevo, f"falta {clave!r} en new_values: {nuevo}"
    assert previo["nombre"] == marca, previo
    assert nuevo["nombre"] == nuevo_nombre, nuevo
    assert previo["activo"] is True and nuevo["activo"] is True, (previo, nuevo)
    assert previo["permisos"] == ["audit:read:company", "lots:read:company"], previo
    assert nuevo["permisos"] == ["lots:create:company", "lots:read:company"], nuevo
    assert nuevo["permisos_agregados"] == ["lots:create:company"], nuevo
    assert nuevo["permisos_retirados"] == ["audit:read:company"], nuevo

    # `AC-RL-06` · ningún secreto en el asiento.
    crudo = str([(x.previous_values, x.new_values) for x in registros]).lower()
    assert "password" not in crudo and "hashed" not in crudo and "$2b$" not in crudo, (
        "la auditoría del rol contiene material sensible")

