"""`SPEC 013` · UAT Administración — `GA-UAT-USERS-S2-01` · `AC-S2-04`.

La contraseña se cambia **solo** por `POST /api/v1/users/{id}/password`. Este archivo fija
ese contrato contra el BACKEND tal como está en HEAD —no se modifica `app/`—:

```
BE-01  PUT /users/{id} con {"role_id": B}     200 y el hash queda IDÉNTICO
BE-02  tras el cambio el rol es B; /me da B sin unir A, y la clave original sirve
BE-03  PUT con `password` en el cuerpo        422 (`extra=forbid`); nada cambia
BE-04  restablecimiento por un administrador  204; el hash cambia y la clave vieja muere
BE-05  la nueva igual a la actual             422 «distinta de la actual»; hash intacto
BE-06  sin `users:update` 403 · objetivo de otra empresa 404; el rol no cambia
BE-07  auditoría: `user` sí, `user_password` solo si se cambió; ningún secreto dentro
```

`PUT` es la vía del rol y `POST .../password` la de la credencial: son superficies
distintas y el interés de estos casos es que no se cruzan. Un `200` que dijera «guardado»
sin haber cambiado el hash volvería a ser el silencio de `P0-13`, y una segunda vía de
clave dentro del `PUT` sería una toma de cuentas con `users:update`.

PREFIJOS propios para poder limpiar sin tocar la siembra: roles `S2-ROL-`, usuarios
`s2_user_`.
"""
from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401

PREFIJO_ROL = "S2-ROL-"
PREFIJO_USUARIO = "s2_user_"
PREFIJO_EMPRESA = "S2-EMP-"

#: La credencial de los usuarios de estas pruebas y la que el administrador impone después.
CLAVE = "ClaveS2Original"
CLAVE_NUEVA = "Otra-Clave-123"

#: A y B reparten módulos **distintos**: es lo único que permite afirmar que el `PUT`
#: sustituye capacidades en vez de acumularlas.
PERMISOS_A = [{"module": "lots", "action": "read", "scope_type": "company"}]
PERMISOS_B = [{"module": "audit", "action": "read", "scope_type": "company"}]
#: El actor de `BE-06` administra sin poder modificar: `users:update` es lo que falta.
PERMISOS_LECTOR = [{"module": "users", "action": "read", "scope_type": "company"}]

# ══════════════════════════════════════════════════════════════════════════════
#  Limpieza — prefijos propios, nunca la siembra
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def motor(test_database_url):
    """Motor de la prueba y limpieza de lo que **esta** prueba escribió.

    La auditoría se borra por `entity_id` de estas filas, no por `user_id`: el actor es la
    siembra y borrar por ahí se llevaría por delante asientos de otras pruebas.
    """
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.auth.models import Permission, Role, User
    from app.masters.models import Company

    async with e.begin() as c:
        usuarios = (await c.execute(
            select(User.id).where(User.username.like(f"{PREFIJO_USUARIO}%")))).scalars().all()
        roles = (await c.execute(
            select(Role.id).where(Role.name.like(f"{PREFIJO_ROL}%")))).scalars().all()
        ids = [str(u) for u in usuarios]
        if ids:
            await c.execute(delete(AuditLog).where(and_(
                AuditLog.entity_type.in_(("user", "user_password")),
                AuditLog.entity_id.in_(ids))))
        if roles:
            await c.execute(delete(AuditLog).where(and_(
                AuditLog.entity_type == "role",
                AuditLog.entity_id.in_([str(r) for r in roles]))))
            await c.execute(delete(Permission).where(Permission.role_id.in_(roles)))
        if usuarios:
            await c.execute(delete(User).where(User.id.in_(usuarios)))
        if roles:
            await c.execute(delete(Role).where(Role.id.in_(roles)))
        empresas = (await c.execute(
            select(Company.id).where(Company.name.like(f"{PREFIJO_EMPRESA}%")))).scalars().all()
        if empresas:
            await c.execute(delete(Company).where(Company.id.in_(empresas)))
    await e.dispose()

# ══════════════════════════════════════════════════════════════════════════════
#  Utilidades — todo por la API real, salvo la lectura de la base
# ══════════════════════════════════════════════════════════════════════════════

async def _rol(http, cabeceras, nombre: str, permisos) -> int:
    r = await http.post("/api/v1/roles", headers=cabeceras,
                        json={"name": nombre, "description": "Prueba AC-S2-04",
                              "permissions": permisos})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _usuario(http, cabeceras, *, sufijo: str, etiqueta: str, rol_id: int) -> dict:
    username = f"{PREFIJO_USUARIO}{etiqueta}-{sufijo}"
    r = await http.post("/api/v1/users", headers=cabeceras, json={
        "first_name": "S2", "last_name": etiqueta,
        "email": f"{username}@example.com", "username": username,
        "password": CLAVE, "role_id": rol_id})
    assert r.status_code == 201, r.text
    return {"id": r.json()["id"], "username": username}


async def _login(http, username: str, password: str):
    return await http.post("/api/v1/login",
                            json={"username": username, "password": password})


async def _escenario(http, cabeceras) -> dict:
    """Rol A, rol B y un usuario que nace con A — todo en la empresa del actor."""
    sufijo = uuid.uuid4().hex[:8]
    rol_a = await _rol(http, cabeceras, f"{PREFIJO_ROL}A-{sufijo}", PERMISOS_A)
    rol_b = await _rol(http, cabeceras, f"{PREFIJO_ROL}B-{sufijo}", PERMISOS_B)
    usuario = await _usuario(http, cabeceras, sufijo=sufijo, etiqueta="u", rol_id=rol_a)
    return {"sufijo": sufijo, "rol_a": rol_a, "rol_b": rol_b, **usuario}


async def _fila(motor, user_id: int) -> dict:
    """Lo que la base guarda de la credencial y del rol, sin exponerlo en la salida."""
    from app.auth.models import User

    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        u = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
        return {"role_id": u.role_id, "hashed_password": u.hashed_password}


async def _asientos(motor, entity_type: str, user_id: int) -> list[dict]:
    """Los registros de auditoría de esa entidad, como datos planos."""
    from app.audit.models import AuditLog

    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        filas = (await s.execute(
            select(AuditLog.action, AuditLog.previous_values, AuditLog.new_values,
                   AuditLog.comments)
            .where(AuditLog.entity_type == entity_type,
                   AuditLog.entity_id == str(user_id)))).all()
    return [{"action": getattr(a, "value", a), "previous_values": p, "new_values": n,
             "comments": c} for a, p, n, c in filas]
# ══════════════════════════════════════════════════════════════════════════════
#  Actores — un administrador y un lector de empresa **propia**
# ══════════════════════════════════════════════════════════════════════════════

#: `DR-3`. Solo se asigna un rol cuyos permisos se **poseen**, así que el actor lleva los
#: de A y los de B —si no, `BE-01` no llegaría a correr— además de `users:*`.
PERMISOS_ACTOR = PERMISOS_A + PERMISOS_B + [
    {"module": "users", "action": "read", "scope_type": "company"},
    {"module": "users", "action": "create", "scope_type": "company"},
    {"module": "users", "action": "update", "scope_type": "company"},
]
#: El actor de `BE-06`: lectura de usuarios y nada más.
PERMISOS_SOLO_LECTURA = PERMISOS_A + PERMISOS_B + PERMISOS_LECTOR


def _cabeceras_de(user_id: int) -> dict:
    """Token de un usuario real; la empresa y los permisos los resuelve el backend."""
    from app.auth.security import create_access_token

    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


async def _sembrar_actor(motor, *, etiqueta: str, permisos, empresa_id: int | None = None) -> dict:
    """Rol + usuario actor, en empresa propia o en la que se le indique. Id y cabeceras.

    Se siembra en la base y no por la API —igual que en `test_uat_admin_users_identity`—
    porque hace falta un inquilino: los roles de estos casos necesitan empresa.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    sufijo = uuid.uuid4().hex[:8]
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        if empresa_id is None:
            empresa = Company(name=f"{PREFIJO_EMPRESA}{etiqueta}-{sufijo}", is_active=True)
            s.add(empresa)
            await s.flush()
            empresa_id = empresa.id
        rol = Role(name=f"{PREFIJO_ROL}ACTOR-{etiqueta}-{sufijo}", company_id=empresa_id,
                   is_active=True)
        s.add(rol)
        await s.flush()
        for permiso in permisos:
            s.add(Permission(role_id=rol.id, module=permiso["module"],
                             action=PermissionAction(permiso["action"]),
                             scope_type=permiso["scope_type"]))
        actor = User(first_name="Actor", last_name=etiqueta,
                     email=f"{PREFIJO_USUARIO}actor-{etiqueta}-{sufijo}@example.com",
                     username=f"{PREFIJO_USUARIO}actor-{etiqueta}-{sufijo}",
                     hashed_password=hash_password(CLAVE), company_id=empresa_id,
                     role_id=rol.id, is_active=True)
        s.add(actor)
        await s.commit()
        return {"empresa": empresa_id, "usuario": actor.id,
                "cabeceras": _cabeceras_de(actor.id)}


@pytest_asyncio.fixture
async def empresa_admin(motor):
    """Actor de `BE-01…BE-05` y `BE-07`: `users:*` y los permisos de A y B, en su empresa."""
    return await _sembrar_actor(motor, etiqueta="admin", permisos=PERMISOS_ACTOR)


@pytest_asyncio.fixture
async def empresa_lector(motor, empresa_admin):
    """Actor de `BE-06`: **misma** empresa, con `users:read` y sin `users:update`.

    Comparte la empresa del administrador para que el objetivo de la prueba sí esté a su
    alcance: lo que se mide es la falta de permiso (403), no la opacidad entre inquilinos.
    """
    return await _sembrar_actor(motor, etiqueta="lector", permisos=PERMISOS_SOLO_LECTURA,
                                empresa_id=empresa_admin["empresa"])


async def test_be_01_put_del_rol_da_200_y_deja_el_hash_identico(http_client, motor,
                                                               empresa_admin):
    """`PUT /users/{id}` con `role_id` es la vía del rol: no toca la credencial."""
    datos = await _escenario(http_client, empresa_admin["cabeceras"])
    antes = await _fila(motor, datos["id"])

    r = await http_client.put(f"/api/v1/users/{datos['id']}",
                              headers=empresa_admin["cabeceras"],
                              json={"role_id": datos["rol_b"]})
    assert r.status_code == 200, r.text

    despues = await _fila(motor, datos["id"])
    assert despues["hashed_password"] == antes["hashed_password"]

async def test_be_02_el_rol_queda_en_b_y_me_devuelve_sus_permisos(http_client, motor,
                                                                   empresa_admin):
    """El `PUT` **sustituye** capacidades: `audit:read` entra y `lots:read` sale."""
    datos = await _escenario(http_client, empresa_admin["cabeceras"])
    r = await http_client.put(f"/api/v1/users/{datos['id']}",
                              headers=empresa_admin["cabeceras"],
                              json={"role_id": datos["rol_b"]})
    assert r.status_code == 200, r.text
    assert (await _fila(motor, datos["id"]))["role_id"] == datos["rol_b"]

    login = await _login(http_client, datos["username"], CLAVE)
    assert login.status_code == 200, login.text
    me = await http_client.get("/api/v1/me", headers={
        "Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200, me.text
    permisos = me.json()["permissions"]
    assert "audit:read" in permisos, permisos
    assert "lots:read" not in permisos, permisos

async def test_be_03_el_put_no_acepta_password_y_nada_cambia(http_client, motor,
                                                             empresa_admin):
    """`UserUpdate` es `extra="forbid"`: una segunda vía de clave sería toma de cuentas."""
    datos = await _escenario(http_client, empresa_admin["cabeceras"])
    antes = await _fila(motor, datos["id"])

    r = await http_client.put(f"/api/v1/users/{datos['id']}",
                              headers=empresa_admin["cabeceras"],
                              json={"role_id": datos["rol_b"], "password": CLAVE_NUEVA})
    assert r.status_code == 422, r.text

    despues = await _fila(motor, datos["id"])
    assert despues["role_id"] == antes["role_id"]
    assert despues["hashed_password"] == antes["hashed_password"]
    assert (await _login(http_client, datos["username"], CLAVE)).status_code == 200

async def test_be_04_el_restablecimiento_cambia_el_hash_y_mata_la_clave_vieja(
        http_client, motor, empresa_admin):
    """El administrador restablece por `POST .../password`; la clave anterior muere."""
    datos = await _escenario(http_client, empresa_admin["cabeceras"])
    antes = await _fila(motor, datos["id"])

    r = await http_client.post(f"/api/v1/users/{datos['id']}/password",
                               headers=empresa_admin["cabeceras"],
                               json={"new_password": CLAVE_NUEVA})
    assert r.status_code == 204, r.text

    assert (await _fila(motor, datos["id"]))["hashed_password"] != antes["hashed_password"]
    assert (await _login(http_client, datos["username"], CLAVE)).status_code == 401
    assert (await _login(http_client, datos["username"], CLAVE_NUEVA)).status_code == 200

async def test_be_05_repetir_la_clave_actual_es_422_y_no_toca_el_hash(http_client, motor,
                                                                      empresa_admin):
    """Aceptar la vigente como «nueva» haría creer que cambió algo: es el silencio de `P0-13`."""
    datos = await _escenario(http_client, empresa_admin["cabeceras"])
    antes = await _fila(motor, datos["id"])

    r = await http_client.post(f"/api/v1/users/{datos['id']}/password",
                               headers=empresa_admin["cabeceras"],
                               json={"new_password": CLAVE})
    assert r.status_code == 422, r.text
    assert "distinta de la actual" in r.json()["detail"], r.json()
    assert (await _fila(motor, datos["id"]))["hashed_password"] == antes["hashed_password"]

async def test_be_06_sin_users_update_el_put_del_rol_es_403(http_client, motor,
                                                            empresa_admin, empresa_lector):
    """Leer usuarios no faculta a cambiarlos: el rol del objetivo queda donde estaba."""
    datos = await _escenario(http_client, empresa_admin["cabeceras"])
    antes = await _fila(motor, datos["id"])
    assert antes["role_id"] == datos["rol_a"]

    r = await http_client.put(f"/api/v1/users/{datos['id']}",
                              headers=empresa_lector["cabeceras"],
                              json={"role_id": datos["rol_b"]})
    assert r.status_code == 403, r.text
    assert (await _fila(motor, datos["id"]))["role_id"] == antes["role_id"]
    assert antes["role_id"] == datos["rol_a"]

async def test_be_07_la_auditoria_separa_rol_de_credencial_y_no_filtra_secretos(
        http_client, motor, empresa_admin):
    """`user` para el rol y `user_password` solo cuando la clave cambió; ni clave ni hash."""
    datos = await _escenario(http_client, empresa_admin["cabeceras"])
    assert (await http_client.put(f"/api/v1/users/{datos['id']}",
                                  headers=empresa_admin["cabeceras"],
                                  json={"role_id": datos["rol_b"]})).status_code == 200
    asientos_rol = await _asientos(motor, "user", datos["id"])
    assert asientos_rol, "el cambio de rol tiene que dejar asiento"
    assert await _asientos(motor, "user_password", datos["id"]) == []

    assert (await http_client.post(f"/api/v1/users/{datos['id']}/password",
                                   headers=empresa_admin["cabeceras"],
                                   json={"new_password": CLAVE_NUEVA})).status_code == 204
    asientos_clave = await _asientos(motor, "user_password", datos["id"])
    assert asientos_clave, "el restablecimiento tiene que dejar asiento"

    volcado = json.dumps(asientos_rol + asientos_clave, default=str)
    assert CLAVE not in volcado
    assert CLAVE_NUEVA not in volcado
    assert (await _fila(motor, datos["id"]))["hashed_password"][:20] not in volcado

