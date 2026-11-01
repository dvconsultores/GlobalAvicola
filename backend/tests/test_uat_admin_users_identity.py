"""`SPEC 013` · UAT Administración — identidad y unicidad de usuarios y roles.

Cubre `AC-ID-01`…`AC-ID-04` (lote `B1`): los hallazgos `AR-03`, `AR-04`, `AR-05` y
`AR-06` de la sesión de UAT del 30-10-2026.

```
UNICIDAD DE USUARIO   global, insensible a mayúsculas, con `strip()`
UNICIDAD DE ROL       por empresa (más las plantillas de sistema visibles), también
                      insensible a mayúsculas y espacios, incluidos los inactivos
NULL EN `PUT /users`  422, nunca `500` por `NOT NULL`
```

Nada de esto es cosmético: un alta con el `username` de uno y el `email` de otro
reventaba con `MultipleResultsFound` (500) en vez de explicar qué estaba ocupado, y dos
cuentas `PA_X` / `pa_x` convivían como identidades distintas en un producto donde el
login se escribe a mano. El `409` y la normalización son la superficie que el
administrador ve; los índices de la base no cambian (`sin migración`).

PREFIJOS propios para poder limpiar sin tocar la siembra: roles `UI-TEST-`, usuarios
`ui_test_` y empresas `UI-TEST-EMPRESA-`.
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
from app.auth.security import create_access_token

PREFIJO_ROL = "UI-TEST-"
PREFIJO_USUARIO = "ui_test_"
PREFIJO_EMPRESA = "UI-TEST-EMPRESA-"

CLAVE = "ClaveUi2026x"
#: `user:read` es un permiso que **cualquier** administrador de empresa de estas pruebas
#: posee, de modo que los roles de inquilino que se crean aquí no dependen de que el actor
#: tenga o no el catálogo entero (relevante para `AC-ES-02`, que es de otro lote).
PERMISO_DE_ROL = [{"module": "users", "action": "read", "scope_type": "company"}]


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
async def empresa_admin(motor):
    """Un administrador de empresa **real**: `users:*` en la suya y sin comodín.

    Es el actor de `AC-ID-04`: un rol de empresa tampoco puede repetir el nombre de una
    plantilla de sistema que ve. Se siembra aquí y no con la siembra compartida porque un
    rol de inquilino necesita empresa propia.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    sufijo = uuid.uuid4().hex[:8]
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        empresa = Company(name=f"{PREFIJO_EMPRESA}{sufijo}", is_active=True)
        s.add(empresa)
        await s.flush()

        rol = Role(name=f"{PREFIJO_ROL}ADMIN-{sufijo}", company_id=empresa.id, is_active=True)
        s.add(rol)
        await s.flush()
        for accion in (PermissionAction.READ, PermissionAction.CREATE,
                       PermissionAction.UPDATE, PermissionAction.DELETE):
            s.add(Permission(role_id=rol.id, module="users", action=accion,
                             scope_type="company"))
        admin = User(first_name="Admin", last_name="Empresa",
                     email=f"{PREFIJO_USUARIO}admin-{sufijo}@example.com",
                     username=f"{PREFIJO_USUARIO}admin-{sufijo}",
                     hashed_password=hash_password("x1234567"),
                     company_id=empresa.id, role_id=rol.id, is_active=True)
        s.add(admin)
        await s.flush()
        await s.commit()
        return {"empresa": empresa.id, "rol": rol.id, "admin": admin.id}


# ══════════════════════════════════════════════════════════════════════════════
#  Utilidades
# ══════════════════════════════════════════════════════════════════════════════

def _cabeceras_de(user_id: int) -> dict:
    """Token de un usuario real; la empresa y los permisos salen de la base."""
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


async def _alta_usuario(http, cabeceras, *, username: str, email: str, **extra):
    cuerpo = {"first_name": "Ui", "last_name": "Identidad", "email": email,
              "username": username, "password": CLAVE}
    cuerpo.update(extra)
    return await http.post("/api/v1/users", headers=cabeceras, json=cuerpo)


async def _alta_rol(http, cabeceras, nombre: str):
    return await http.post("/api/v1/roles", headers=cabeceras,
                           json={"name": nombre, "description": "Prueba de identidad",
                                 "permissions": PERMISO_DE_ROL})


async def _contar_usuarios(motor) -> int:
    from app.auth.models import User

    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        return (await s.execute(select(func.count()).select_from(User))).scalar_one()


async def _usuario_en_base(motor, user_id: int) -> dict:
    from app.auth.models import User

    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        u = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
        return {"username": u.username, "email": u.email, "first_name": u.first_name}


async def _dos_usuarios(http, cabeceras, motor) -> dict:
    """Dos usuarios reales de la empresa del actor, con sus datos de identidad."""
    sufijo = uuid.uuid4().hex[:8]
    a = {"username": f"{PREFIJO_USUARIO}a-{sufijo}",
         "email": f"{PREFIJO_USUARIO}a-{sufijo}@example.com"}
    b = {"username": f"{PREFIJO_USUARIO}b-{sufijo}",
         "email": f"{PREFIJO_USUARIO}b-{sufijo}@example.com"}
    for datos in (a, b):
        r = await _alta_usuario(http, cabeceras, username=datos["username"],
                                email=datos["email"])
        assert r.status_code == 201, r.text
        datos["id"] = r.json()["id"]
    return {"a": a, "b": b, "sufijo": sufijo}


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-01` · username de uno + email de otro
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_01_username_de_uno_y_email_de_otro_da_409_y_no_crea_nada(
    http_client, auth_headers, motor
):
    """`AR-03`. La consulta anterior traía dos filas y `scalar_one_or_none` reventaba.

    El resultado en HEAD era un `500` con `MultipleResultsFound`: el administrador no
    sabía qué estaba ocupado y la petición no dejaba rastro útil. Debe ser un `409`
    accionable, y sin fila nueva.
    """
    datos = await _dos_usuarios(http_client, auth_headers, motor)
    antes = await _contar_usuarios(motor)

    r = await _alta_usuario(http_client, auth_headers,
                            username=datos["a"]["username"], email=datos["b"]["email"])

    assert r.status_code == 409, (
        f"esperado 409 y llegó {r.status_code}: {r.text[:300]}")
    assert "ya está en uso" in r.json()["detail"].lower(), r.json()["detail"]
    assert await _contar_usuarios(motor) == antes, (
        "una petición rechazada creó una fila")


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-01b` · los dos duplicados simples, cada uno con su mensaje
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_01b_duplicado_de_username_y_de_email_se_distinguen(
    http_client, auth_headers, motor
):
    """Un `409` genérico obligaría al administrador a adivinar qué corregir."""
    datos = await _dos_usuarios(http_client, auth_headers, motor)
    sufijo = datos["sufijo"]

    por_username = await _alta_usuario(
        http_client, auth_headers, username=datos["a"]["username"],
        email=f"{PREFIJO_USUARIO}nuevo-{sufijo}@example.com")
    assert por_username.status_code == 409, por_username.text
    assert "nombre de usuario" in por_username.json()["detail"].lower(), (
        por_username.json()["detail"])

    por_email = await _alta_usuario(
        http_client, auth_headers, username=f"{PREFIJO_USUARIO}nuevo2-{sufijo}",
        email=datos["a"]["email"])
    assert por_email.status_code == 409, por_email.text
    assert "correo" in por_email.json()["detail"].lower(), por_email.json()["detail"]


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-02` · editar con un email ajeno
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_02_editar_con_un_email_ajeno_da_409_y_no_cambia(
    http_client, auth_headers, motor
):
    """`AR-04`. Antes: `IntegrityError` sin capturar ⇒ `500`, o peor, cambio parcial."""
    datos = await _dos_usuarios(http_client, auth_headers, motor)
    antes = await _usuario_en_base(motor, datos["b"]["id"])

    r = await http_client.put(f"/api/v1/users/{datos['b']['id']}", headers=auth_headers,
                              json={"email": datos["a"]["email"]})
    assert r.status_code == 409, f"esperado 409 y llegó {r.status_code}: {r.text[:300]}"
    assert "ya está en uso" in r.json()["detail"].lower(), r.json()["detail"]

    # La unicidad se evalúa insensible a mayúsculas: los índices de la base no.
    r2 = await http_client.put(f"/api/v1/users/{datos['b']['id']}", headers=auth_headers,
                               json={"email": datos["a"]["email"].upper()})
    assert r2.status_code == 409, (
        f"la comprobación de unicidad distingue mayúsculas: {r2.status_code} {r2.text[:200]}")

    despues = await _usuario_en_base(motor, datos["b"]["id"])
    assert despues["email"].lower() == antes["email"].lower(), (
        f"el correo del usuario editado cambió: {antes['email']!r} → {despues['email']!r}")


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-02b` · un `null` en la edición es 422, no un 500 por `NOT NULL`
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_02b_los_campos_obligatorios_nulos_son_422(
    http_client, auth_headers, motor
):
    """`AR-04`. `PUT` con `null` llegaba hasta la base y moría en el `NOT NULL`."""
    datos = await _dos_usuarios(http_client, auth_headers, motor)
    objetivo = datos["b"]["id"]

    for campo in ("email", "first_name", "last_name", "view_type", "is_active"):
        r = await http_client.put(f"/api/v1/users/{objetivo}", headers=auth_headers,
                                  json={campo: None})
        assert r.status_code == 422, (
            f"`{campo}=null` debe ser 422 y fue {r.status_code}: {r.text[:200]}")

    # Y nada cambió: los cinco rechazos dejaron la fila intacta.
    despues = await _usuario_en_base(motor, objetivo)
    assert despues["email"].lower() == datos["b"]["email"].lower()
    assert despues["username"] == datos["b"]["username"]


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-02c` · un par histórico que solo difiere en mayúsculas no autochoca
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_02c_reenviar_el_propio_correo_no_choca_con_el_par_historico(
    http_client, auth_headers, motor
):
    """`AC-ID-02`. `A` con `correo` y `B` con `CORREO` convivían en la base —dato anterior a
    la regla de unicidad insensible—. Al editar cualquier otro campo de `B` reenviando su
    correo tal cual, la comprobación `lower(email)` encontraba a `A` y devolvía `409`: la
    fila quedaba imposible de guardar aunque su correo no cambiara.

    La comprobación solo aplica cuando el correo cambia de verdad; el `409` por un correo
    ajeno sigue en pie (`AC-ID-02`).
    """
    from app.auth.models import User

    datos = await _dos_usuarios(http_client, auth_headers, motor)
    a_id, b_id = datos["a"]["id"], datos["b"]["id"]

    # El índice de la base distingue mayúsculas, así que el par histórico cabe por SQL.
    # Se pone en mayúsculas solo la parte local: el esquema de entrada ya normaliza el
    # dominio, de modo que el valor reenviado es idéntico al que quedó en la fila.
    local, _, dominio = datos["a"]["email"].partition("@")
    par_historico = f"{local.upper()}@{dominio}"
    assert par_historico != datos["a"]["email"], "el par debe diferir para caber en el índice"
    assert par_historico.lower() == datos["a"]["email"].lower(), "para el producto es el mismo correo"
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        b = (await s.execute(select(User).where(User.id == b_id))).scalar_one()
        b.email = par_historico
        await s.commit()
    assert (await _usuario_en_base(motor, a_id))["email"] == datos["a"]["email"]

    r = await http_client.put(f"/api/v1/users/{b_id}", headers=auth_headers,
                              json={"first_name": "Nuevo", "email": par_historico})
    assert r.status_code == 200, (
        f"reenviar el propio correo con el par histórico dio {r.status_code}: "
        f"{r.text[:300]}")

    despues = await _usuario_en_base(motor, b_id)
    assert despues["first_name"] == "Nuevo", despues
    assert despues["email"] == par_historico, despues


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-03` · normalización con `strip()` y unicidad insensible
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_03_unicidad_insensible_a_mayusculas_y_sin_espacios(
    http_client, auth_headers, motor
):
    """`AR-05`. `PA_X` y `pa_x` convivían; el login, en cambio, se escribe a mano."""
    datos = await _dos_usuarios(http_client, auth_headers, motor)
    sufijo = datos["sufijo"]

    por_username = await _alta_usuario(
        http_client, auth_headers, username=datos["a"]["username"].upper(),
        email=f"{PREFIJO_USUARIO}mayus-{sufijo}@example.com")
    assert por_username.status_code == 409, (
        f"`PA_X` y `pa_x` siguen coexistiendo: {por_username.status_code} "
        f"{por_username.text[:200]}")

    por_email = await _alta_usuario(
        http_client, auth_headers, username=f"{PREFIJO_USUARIO}mayus2-{sufijo}",
        email=datos["a"]["email"].upper())
    assert por_email.status_code == 409, (
        f"el correo duplicado en mayúsculas se aceptó: {por_email.status_code}")

    # Un valor con espacios se persiste **sin** espacios.
    marca = f"{PREFIJO_USUARIO}nuevo-{sufijo}"
    con_espacios = await _alta_usuario(
        http_client, auth_headers, username=f"  {marca}  ",
        email=f"{marca}@example.com")
    assert con_espacios.status_code == 201, con_espacios.text
    leido = await http_client.get(f"/api/v1/users/{con_espacios.json()['id']}",
                                  headers=auth_headers)
    assert leido.status_code == 200, leido.text
    assert leido.json()["username"] == marca, (
        f"el username se guardó con espacios: {leido.json()['username']!r}")

    # Tras `strip()` el username deja de cumplir la longitud mínima ⇒ 422, no 500.
    corto = await _alta_usuario(
        http_client, auth_headers, username="  ab  ",
        email=f"{PREFIJO_USUARIO}corto-{sufijo}@example.com")
    assert corto.status_code == 422, (
        f"un username de dos caracteres tras `strip()` debe ser 422: "
        f"{corto.status_code} {corto.text[:200]}")


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-04` · el nombre de rol es único por empresa
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_04_nombre_de_rol_unico_insensible_e_incluido_el_inactivo(
    http_client, auth_headers, motor
):
    """`AR-06`. Alta y renombrado, con espacios, con otra capitalización y con inactivos.

    El último tramo —renombrar un rol a su propio nombre con otra capitalización— es el
    control que impide que la comprobación se convierta en «todo nombre está ocupado»:
    sin excluir al propio rol, el administrador no podría ni reescribir su nombre.
    """
    sufijo = uuid.uuid4().hex[:8]
    nombre = f"{PREFIJO_ROL}{sufijo}"

    alta = await _alta_rol(http_client, auth_headers, nombre)
    assert alta.status_code == 201, alta.text
    rol_id = alta.json()["id"]

    repetido = await _alta_rol(http_client, auth_headers, nombre)
    assert repetido.status_code == 409, (
        f"el mismo nombre de rol se aceptó dos veces: {repetido.status_code}")
    assert "ya existe un rol con ese nombre" in repetido.json()["detail"].lower(), (
        repetido.json()["detail"])

    en_mayusculas = await _alta_rol(http_client, auth_headers, nombre.upper())
    assert en_mayusculas.status_code == 409, (
        f"`{nombre.upper()}` convive con `{nombre}`: {en_mayusculas.status_code}")

    con_espacios = await _alta_rol(http_client, auth_headers, f"  {nombre}  ")
    assert con_espacios.status_code == 409, (
        f"el nombre con espacios esquiva la unicidad: {con_espacios.status_code}")

    otro = f"{PREFIJO_ROL}OTRO-{sufijo}"
    alta_otro = await _alta_rol(http_client, auth_headers, otro)
    assert alta_otro.status_code == 201, alta_otro.text
    otro_id = alta_otro.json()["id"]

    renombrado = await http_client.put(f"/api/v1/roles/{otro_id}", headers=auth_headers,
                                       json={"name": nombre})
    assert renombrado.status_code == 409, (
        f"renombrar a un nombre ocupado devolvió {renombrado.status_code}")

    # Control: su propio nombre, con otra capitalización, no se autochoca.
    propio = await http_client.put(f"/api/v1/roles/{otro_id}", headers=auth_headers,
                                   json={"name": otro.upper()})
    assert propio.status_code == 200, (
        f"renombrar un rol a su propio nombre falló: {propio.status_code} {propio.text[:200]}")
    assert propio.json()["name"] == otro.upper()

    # Un rol inactivo sigue reservando su nombre.
    baja = await http_client.put(f"/api/v1/roles/{rol_id}", headers=auth_headers,
                                 json={"is_active": False})
    assert baja.status_code == 200, baja.text
    tras_la_baja = await _alta_rol(http_client, auth_headers, nombre)
    assert tras_la_baja.status_code == 409, (
        f"el nombre de un rol inactivo quedó libre: {tras_la_baja.status_code}")


async def test_ac_id_04_un_rol_de_empresa_no_repite_el_nombre_de_una_plantilla(
    http_client, empresa_admin
):
    """`AR-06` · «incluye las plantillas de sistema **visibles**».

    Un administrador de empresa ve las plantillas de producto para poder elegirlas. Si
    pudiera crear un rol propio con el mismo nombre, el listado ofrecería dos entradas
    indistinguibles y el nombre dejaría de identificar nada.
    """
    cabeceras = _cabeceras_de(empresa_admin["admin"])

    visibles = await http_client.get("/api/v1/roles", headers=cabeceras)
    assert visibles.status_code == 200, visibles.text
    plantillas = [r for r in visibles.json() if r["company_id"] is None]
    assert plantillas, "el actor de empresa debe ver las plantillas de sistema"
    plantilla = plantillas[0]["name"]

    # Control: un nombre libre **sí** se crea en su empresa (la regla no bloquea todo).
    libre = f"{PREFIJO_ROL}LIBRE-{uuid.uuid4().hex[:8]}"
    alta = await _alta_rol(http_client, cabeceras, libre)
    assert alta.status_code == 201, alta.text
    assert alta.json()["company_id"] == empresa_admin["empresa"]

    repetida = await _alta_rol(http_client, cabeceras, plantilla.upper())
    assert repetida.status_code == 409, (
        f"un rol de empresa repitió el nombre de la plantilla {plantilla!r}: "
        f"{repetida.status_code} {repetida.text[:200]}")
    assert "ya existe un rol con ese nombre" in repetida.json()["detail"].lower(), (
        repetida.json()["detail"])
