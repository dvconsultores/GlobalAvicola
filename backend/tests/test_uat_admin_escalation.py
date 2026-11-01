"""`SPEC 013` · UAT Administración — escalada de privilegios y auto-acciones (`B3a`).

Cubre `AC-ES-01`…`AC-ES-03`, `AC-ID-05` y `AC-ID-06` con la decisión vinculante del
Owner:

```
DR-3   NADIE asigna un rol ni concede permisos que él mismo no posea — la autoridad
       global queda exenta;
       NADIE cambia su PROPIO rol ni se desactiva a sí mismo — tampoco la autoridad
       global.
```

```
AC-ES-01  subconjunto en la ASIGNACIÓN de rol (alta y cambio): si el rol destino
          reparte un `(módulo, acción)` que el actor no tiene ⇒ `403` + asiento
AC-ES-02  subconjunto en el ALTA/EDICIÓN de rol: solo lo AÑADIDO exige poseerlo;
          retirar siempre se puede y reenviar el mismo conjunto no exige nada
AC-ES-03  `403` al cambiar el propio `role_id` o al desactivarse (`PUT`/`DELETE`),
          autoridad global incluida
AC-ID-05  `PUT is_active=false` exige además `users:delete`; reactivar sigue siendo
          `users:update`
AC-ID-06  la nueva contraseña igual a la vigente ⇒ `422`, propio o restablecimiento
```

Todo esto se decide en el backend: ocultar un botón en la interfaz no impide que un
`POST /users` directo se asigne el rol de auditoría, ni que un administrador de empresa
se conceda a sí mismo un permiso que no tiene.

PREFIJOS propios para poder limpiar sin tocar la siembra: roles `ES-TEST-`, usuarios
`es_test_` y empresas `ES-TEST-EMPRESA-`.
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
from app.auth.security import create_access_token

PREFIJO_ROL = "ES-TEST-"
PREFIJO_USUARIO = "es_test_"
PREFIJO_EMPRESA = "ES-TEST-EMPRESA-"

CLAVE = "ClaveEs2026x"


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
        # El asiento de una petición rechazada se confirma dentro de la petición, de modo
        # que sobrevive al rechazo: hay que borrarlo explícitamente.
        condiciones = []
        if usuarios:
            condiciones.append(AuditLog.user_id.in_(usuarios))
        if ids_usuarios:
            condiciones.append(and_(AuditLog.entity_type == "user",
                                    AuditLog.entity_id.in_(ids_usuarios)))
        if condiciones:
            await c.execute(delete(AuditLog).where(or_(*condiciones)))
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
    """Una empresa con los actores y los roles que estas reglas necesitan.

    ```
    EMPRESA A
      ADMIN       users:read/create/update/delete + lots:read      (el administrador)
      SIN_BORRAR  users:read/update + lots:read                    (sin `users:delete`)
      CON_COMODIN users:read/create/update/delete + ("*", "read")  (sí tiene el comodín)

      ROL_AUDIT      audit:read                permiso que ADMIN **no** posee
      ROL_LOTES      lots:read                 subconjunto de ADMIN
      ROL_HEREDADO   audit:read + lots:read    rol anterior a la regla, con un permiso ajeno
      ROL_COMODIN    ("*", "read", company)    el comodín exige comodín
    ```

    Los permisos de los actores son **explícitos**: nada de `("*", …)` salvo en el actor
    que existe justamente para probar el comodín. Un escenario con autoridad global no
    mediría la regla, porque `DR-3` la exime.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    sufijo = uuid.uuid4().hex[:8]
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO_EMPRESA}A-{sufijo}", is_active=True)
        s.add(a)
        await s.flush()

        def _rol(nombre, permisos):
            r = Role(name=f"{PREFIJO_ROL}{nombre}-{sufijo}", company_id=a.id, is_active=True)
            s.add(r)
            return r, permisos

        rol_admin, perms_admin = _rol("ADMIN", [
            ("users", "read"), ("users", "create"), ("users", "update"),
            ("users", "delete"), ("lots", "read")])
        rol_sin_borrar, perms_sin_borrar = _rol("SIN-BORRAR", [
            ("users", "read"), ("users", "update"), ("lots", "read")])
        rol_actor_comodin, perms_actor_comodin = _rol("ACTOR-COMODIN", [
            ("users", "read"), ("users", "create"), ("users", "update"),
            ("users", "delete"), ("*", "read")])
        rol_audit, perms_audit = _rol("ROL-AUDIT", [("audit", "read")])
        rol_lotes, perms_lotes = _rol("ROL-LOTES", [("lots", "read")])
        rol_heredado, perms_heredado = _rol(
            "ROL-HEREDADO", [("audit", "read"), ("lots", "read")])
        rol_comodin, perms_comodin = _rol("ROL-COMODIN", [("*", "read")])
        await s.flush()

        for rol, pares in (
                (rol_admin, perms_admin), (rol_sin_borrar, perms_sin_borrar),
                (rol_actor_comodin, perms_actor_comodin), (rol_audit, perms_audit),
                (rol_lotes, perms_lotes), (rol_heredado, perms_heredado),
                (rol_comodin, perms_comodin)):
            for modulo, accion in pares:
                s.add(Permission(role_id=rol.id, module=modulo,
                                 action=PermissionAction(accion), scope_type="company"))

        def _usuario(marca, rol):
            return User(first_name=marca, last_name="Escalada",
                        email=f"{PREFIJO_USUARIO}{marca.lower()}-{sufijo}@example.com",
                        username=f"{PREFIJO_USUARIO}{marca.lower()}-{sufijo}",
                        hashed_password=hash_password(CLAVE),
                        company_id=a.id, role_id=rol.id, is_active=True)

        admin = _usuario("ADMIN", rol_admin)
        sin_borrar = _usuario("SINBORRAR", rol_sin_borrar)
        con_comodin = _usuario("COMODIN", rol_actor_comodin)
        s.add_all([admin, sin_borrar, con_comodin])
        await s.flush()
        await s.commit()
        return {
            "empresa_a": a.id,
            "admin": admin.id, "sin_borrar": sin_borrar.id,
            "con_comodin": con_comodin.id,
            "rol_admin": rol_admin.id, "rol_sin_borrar": rol_sin_borrar.id,
            "rol_audit": rol_audit.id, "rol_lotes": rol_lotes.id,
            "rol_heredado": rol_heredado.id, "rol_comodin": rol_comodin.id,
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
        "name": nombre, "description": "Escalada de privilegios",
        "permissions": [_permiso("lots")] if permisos is None else permisos,
    })


async def _alta_usuario(http, cabeceras, *, role_id: int | None = None,
                        quien: str | None = None):
    marca = f"{quien or 'u'}-{uuid.uuid4().hex[:8]}"
    cuerpo = {"first_name": "Escalada", "last_name": "Privilegios",
              "email": f"{PREFIJO_USUARIO}u-{marca}@example.com",
              "username": f"{PREFIJO_USUARIO}u-{marca}", "password": CLAVE}
    if role_id is not None:
        cuerpo["role_id"] = role_id
    return await http.post("/api/v1/users", headers=cabeceras, json=cuerpo)


# ── lectura directa de la base: la verdad, no lo que la API quiso contar ──────

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


async def _activo_en_base(escenario, user_id: int) -> bool:
    from app.auth.models import User

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            return (await s.execute(
                select(User.is_active).where(User.id == user_id))).scalar_one()
    finally:
        await e.dispose()


async def _hash_en_base(escenario, user_id: int) -> str:
    from app.auth.models import User

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            return (await s.execute(
                select(User.hashed_password).where(User.id == user_id))).scalar_one()
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


async def _rechazos(escenario, *, role_id: int | None = None) -> list[str]:
    """Comentarios de los rechazos de autoridad dejados en la empresa del escenario.

    `C-05`: un intento denegado de repartir autoridad tiene que dejar rastro. Se lee en la
    tabla de auditoría —no en la respuesta HTTP— porque el asiento es lo que sobrevive al
    rechazo y lo que un auditor puede revisar después.
    """
    from app.audit.models import AuditAction, AuditLog

    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            consulta = select(AuditLog.comments).where(
                AuditLog.action == AuditAction.PERMISSION_CHANGE,
                AuditLog.entity_type == "role",
                AuditLog.company_id == escenario["empresa_a"])
            if role_id is not None:
                consulta = consulta.where(AuditLog.entity_id == str(role_id))
            filas = (await s.execute(consulta)).scalars().all()
            return [c for c in filas if c and "rechazado" in c]
    finally:
        await e.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ES-01` · subconjunto al ASIGNAR un rol
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_es_01_el_alta_no_asigna_un_rol_con_permisos_que_el_actor_no_posee(
    http_client, escenario
):
    """`AR-02` · `DR-3`. `POST /users` con un rol que reparte `audit:read` a quien solo
    administra usuarios es la escalada más corta que existe: el actor crea a alguien —o se
    crea a sí mismo— con la capacidad que no tiene.

    En HEAD el alta devolvía `201`: bastaba `users:create` para conceder cualquier permiso
    de la empresa.
    """
    cab = _token(escenario["admin"])
    ajeno = escenario["rol_audit"]              # audit:read — `ADMIN` no lo posee

    antes = await _contar_usuarios(escenario)
    alta = await _alta_usuario(http_client, cab, role_id=ajeno, quien="escalada-alta")
    assert alta.status_code == 403, (
        f"se creó un usuario con un rol que reparte permisos ajenos: "
        f"{alta.status_code} {alta.text[:300]}")
    assert "posee" in alta.json()["detail"], alta.json()["detail"]
    assert "audit:read" in alta.json()["detail"], alta.json()["detail"]
    assert await _contar_usuarios(escenario) == antes, (
        "una petición rechazada creó una fila")

    # `C-05` · el rechazo deja asiento.
    rechazos = await _rechazos(escenario, role_id=ajeno)
    assert rechazos, "el intento de escalada no dejó asiento de auditoría"
    assert any("escalada" in c for c in rechazos), rechazos

    # El CAMBIO de rol pasa por la misma regla: un `PUT` directo no es una puerta trasera.
    otro = (await _alta_usuario(http_client, cab, quien="escalada-otro")).json()
    cambio = await http_client.put(f"/api/v1/users/{otro['id']}", headers=cab,
                                   json={"role_id": ajeno})
    assert cambio.status_code == 403, (
        f"se cambió el rol a uno con permisos ajenos: {cambio.status_code} "
        f"{cambio.text[:300]}")
    assert await _rol_de_usuario(escenario, otro["id"]) is None, (
        "el rol ajeno se asignó de todos modos")

    # CONTROL · un rol **subconjunto** de lo que el actor posee sigue siendo asignable, en
    # alta y en cambio. Sin esto, el `403` de arriba no distinguiría «la regla funciona»
    # de «nadie puede asignar nada».
    propio = escenario["rol_lotes"]             # lots:read — sí lo posee
    alta_ok = await _alta_usuario(http_client, cab, role_id=propio, quien="subconjunto")
    assert alta_ok.status_code == 201, (
        f"un rol con permisos que el actor sí posee no se pudo asignar: "
        f"{alta_ok.status_code} {alta_ok.text[:300]}")
    cambio_ok = await http_client.put(f"/api/v1/users/{otro['id']}", headers=cab,
                                      json={"role_id": propio})
    assert cambio_ok.status_code == 200, (
        f"el cambio a un rol propio falló: {cambio_ok.status_code} {cambio_ok.text[:300]}")



async def test_ac_es_01_el_comodin_exige_comodin(http_client, escenario):
    """`AC-ES-01` · «el comodín exige comodín».

    Un rol que reparte `("*", "read")` alcanza **todos** los módulos: solo puede asignarlo
    quien ya tiene el comodín. La comprobación usa `tiene_permiso`, la misma función que
    decide cada ruta, de modo que no hay una segunda definición de la regla que pueda
    divergir de la que autoriza.
    """
    comodin = escenario["rol_comodin"]          # ("*", "read", company)

    # El administrador de empresa tiene `users:*` y `lots:read`, pero no el comodín.
    sin_comodin = await _alta_usuario(http_client, _token(escenario["admin"]),
                                      role_id=comodin, quien="comodin-negado")
    assert sin_comodin.status_code == 403, (
        f"se asignó un rol con comodín de módulo sin tenerlo: {sin_comodin.status_code} "
        f"{sin_comodin.text[:300]}")
    assert "*:read" in sin_comodin.json()["detail"], sin_comodin.json()["detail"]

    # CONTROL · quien sí tiene `("*", "read")` puede asignarlo.
    con_comodin = await _alta_usuario(http_client, _token(escenario["con_comodin"]),
                                      role_id=comodin, quien="comodin-permitido")
    assert con_comodin.status_code == 201, (
        f"el comodín no se pudo asignar teniéndolo: {con_comodin.status_code} "
        f"{con_comodin.text[:300]}")


async def test_ac_es_01_la_autoridad_global_queda_exenta(http_client, auth_headers, escenario):
    """CONTROL de `DR-3`: la regla de subconjunto **no** alcanza a la autoridad global.

    Sin este control, un `403` universal pasaría por implementación correcta y dejaría al
    Super Administrador sin poder asignar ningún rol del producto.
    """
    alta = await _alta_usuario(http_client, auth_headers,
                               role_id=escenario["rol_audit"], quien="global")
    assert alta.status_code == 201, (
        f"la autoridad global no pudo asignar un rol de la empresa: {alta.status_code} "
        f"{alta.text[:300]}")

    cambio = await http_client.put(f"/api/v1/users/{alta.json()['id']}",
                                   headers=auth_headers,
                                   json={"role_id": escenario["rol_comodin"]})
    assert cambio.status_code == 200, (
        f"la autoridad global no pudo cambiar el rol: {cambio.status_code} "
        f"{cambio.text[:300]}")



# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ES-02` · subconjunto al CONCEDER permisos (alta y edición de rol)
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_es_02_un_rol_no_concede_lo_que_su_autor_no_posee(http_client, escenario):
    """`AR-02` · `DR-3`. Crear un rol es la otra mitad de la escalada: no hace falta
    asignárselo a nadie, basta dejarlo en el catálogo y dárselo después a quien convenga.

    En HEAD el alta devolvía `201` con `audit:read` para un actor que solo administra
    usuarios.
    """
    cab = _token(escenario["admin"])

    marca = _marca("CON-AUDIT")
    alta = await _alta_rol(http_client, cab, marca, permisos=[_permiso("audit")])
    assert alta.status_code == 403, (
        f"se creó un rol con un permiso que su autor no posee: {alta.status_code} "
        f"{alta.text[:300]}")
    assert "posee" in alta.json()["detail"], alta.json()["detail"]
    assert await _rol_por_nombre(escenario, marca) is None, (
        "la petición rechazada dejó fila")
    assert await _rechazos(escenario), "el rechazo no dejó asiento de auditoría"

    # CONTROL · con permisos que sí posee, el alta sigue siendo un alta.
    mio = await _alta_rol(http_client, cab, _marca("CON-LOTES"), permisos=[_permiso("lots")])
    assert mio.status_code == 201, (
        f"no se pudo crear un rol con permisos propios: {mio.status_code} "
        f"{mio.text[:300]}")



async def test_ac_es_02_la_edicion_solo_exige_poseer_lo_que_se_anade(http_client, escenario):
    """`AC-ES-02` · **añadir** exige poseerlo; **retirar** siempre se puede, y reenviar el
    mismo conjunto no exige nada.

    La distinción no es un adorno: la interfaz reenvía **todos** los permisos al guardar, y
    si se validara el conjunto entero, un rol heredado con un permiso que su administrador
    no tiene quedaría imposible de renombrar — ni siquiera podría quitarse ese permiso.
    """
    cab = _token(escenario["admin"])

    # Añadir a un rol propio un permiso ajeno ⇒ 403 y los permisos quedan intactos.
    mio = (await _alta_rol(http_client, cab, _marca("EDITABLE"),
                           permisos=[_permiso("lots")])).json()
    antes = await _permisos_en_base(escenario, mio["id"])
    anadir = await http_client.put(f"/api/v1/roles/{mio['id']}", headers=cab, json={
        "permissions": [_permiso("lots"), _permiso("audit")]})
    assert anadir.status_code == 403, (
        f"se añadió un permiso que el actor no posee: {anadir.status_code} "
        f"{anadir.text[:300]}")
    assert await _permisos_en_base(escenario, mio["id"]) == antes, (
        "una edición rechazada mutó los permisos del rol")

    # Rol heredado: contiene `audit:read`, que `ADMIN` no posee.
    heredado = escenario["rol_heredado"]
    assert await _permisos_en_base(escenario, heredado) == [
        ("audit", "read", "company"), ("lots", "read", "company")]

    renombrar = await http_client.put(f"/api/v1/roles/{heredado}", headers=cab, json={
        "name": _marca("HEREDADO-RENOMBRADO"),
        "permissions": [_permiso("audit"), _permiso("lots")]})
    assert renombrar.status_code == 200, (
        f"renombrar reenviando los permisos heredados quedó bloqueado: "
        f"{renombrar.status_code} {renombrar.text[:300]}")

    # Retirar —incluso el permiso que el actor no posee— siempre es posible.
    retirar = await http_client.put(f"/api/v1/roles/{heredado}", headers=cab, json={
        "permissions": [_permiso("lots")]})
    assert retirar.status_code == 200, (
        f"no se pudo retirar un permiso del rol: {retirar.status_code} "
        f"{retirar.text[:300]}")
    assert await _permisos_en_base(escenario, heredado) == [("lots", "read", "company")]



async def test_ac_es_02_la_autoridad_global_queda_exenta_al_conceder(
    http_client, auth_headers, escenario
):
    """CONTROL de `DR-3`: crear y editar plantillas de sistema no exige subconjunto."""
    alta = await _alta_rol(http_client, auth_headers, _marca("SISTEMA"),
                           permisos=[_permiso("audit"), _permiso("lots")])
    assert alta.status_code == 201, (
        f"la autoridad global no pudo crear un rol: {alta.status_code} {alta.text[:300]}")

    edicion = await http_client.put(
        f"/api/v1/roles/{alta.json()['id']}", headers=auth_headers,
        json={"permissions": [_permiso("audit"), _permiso("lots"),
                              _permiso("users", "delete")]})
    assert edicion.status_code == 200, (
        f"la autoridad global no pudo ampliar un rol: {edicion.status_code} "
        f"{edicion.text[:300]}")



# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ES-03` · nadie cambia su propio rol ni se desactiva a sí mismo
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_es_03_nadie_cambia_su_propio_rol_ni_se_desactiva(http_client, escenario):
    """`AR-02` / `AR-08` · `DR-3`.

    Reenviar el **mismo** `role_id` —lo que la interfaz hace siempre al guardar— no es un
    cambio y sigue permitido; lo que se deniega es modificar el propio rol y darse de baja
    a uno mismo, por `PUT` o por `DELETE`. En HEAD las tres acciones pasaban.
    """
    admin = escenario["admin"]
    cab = _token(admin)
    su_rol = escenario["rol_admin"]
    pretendido = escenario["rol_lotes"]

    # (a) cambiar el propio rol ⇒ 403 y sin cambio.
    cambio = await http_client.put(f"/api/v1/users/{admin}", headers=cab,
                                   json={"role_id": pretendido})
    assert cambio.status_code == 403, (
        f"el actor se cambió su propio rol: {cambio.status_code} {cambio.text[:300]}")
    assert "propio rol" in cambio.json()["detail"], cambio.json()["detail"]
    assert await _rol_de_usuario(escenario, admin) == su_rol, (
        "el rol propio cambió pese al rechazo")
    assert any("auto-cambio" in c for c in await _rechazos(escenario, role_id=pretendido)), (
        await _rechazos(escenario, role_id=pretendido))

    # CONTROL · reenviar el mismo rol no es un cambio (la UI lo envía siempre).
    mismo = await http_client.put(f"/api/v1/users/{admin}", headers=cab,
                                  json={"role_id": su_rol, "first_name": "Admin"})
    assert mismo.status_code == 200, (
        f"reenviar el propio rol quedó bloqueado: {mismo.status_code} {mismo.text[:300]}")
    assert mismo.json()["first_name"] == "Admin"
    assert await _rol_de_usuario(escenario, admin) == su_rol

    # (b) desactivarse por `PUT` ⇒ 403 y la cuenta sigue viva (el token sigue valiendo).
    baja = await http_client.put(f"/api/v1/users/{admin}", headers=cab,
                                json={"is_active": False})
    assert baja.status_code == 403, (
        f"el actor se desactivó a sí mismo: {baja.status_code} {baja.text[:300]}")
    assert "desactivarse" in baja.json()["detail"], baja.json()["detail"]
    assert await _activo_en_base(escenario, admin) is True
    assert (await http_client.get("/api/v1/me", headers=cab)).status_code == 200

    # (c) darse de baja por `DELETE` ⇒ 403, con `users:delete` en la mano.
    borrado = await http_client.delete(f"/api/v1/users/{admin}", headers=cab)
    assert borrado.status_code == 403, (
        f"el actor se dio de baja a sí mismo: {borrado.status_code} {borrado.text[:300]}")
    assert await _activo_en_base(escenario, admin) is True
    assert (await http_client.get("/api/v1/me", headers=cab)).status_code == 200



async def test_ac_es_03_la_autoridad_global_tampoco_se_desactiva(
    http_client, auth_headers, escenario
):
    """`AC-ES-03` · «tampoco la autoridad global».

    Un usuario con un rol de sistema que porta `("*", …, "all")` es indistinguible de un
    Super Administrador para `get_current_user`. En HEAD podía darse de baja a sí mismo por
    `PUT`, y la única cuenta que puede administrarlo todo se apagaba sola.
    """
    rol = await http_client.post("/api/v1/roles", headers=auth_headers, json={
        "name": _marca("SISTEMA-BORRADO"), "description": "plantilla de sistema",
        "permissions": [{"module": "*", "action": "delete", "scope_type": "all"}]})
    assert rol.status_code == 201, rol.text

    marca = uuid.uuid4().hex[:8]
    alta = await http_client.post("/api/v1/users", headers=auth_headers, json={
        "first_name": "Global", "last_name": "Escalada",
        "email": f"{PREFIJO_USUARIO}global-{marca}@example.com",
        "username": f"{PREFIJO_USUARIO}global-{marca}",
        "password": CLAVE, "role_id": rol.json()["id"]})
    assert alta.status_code == 201, alta.text
    g = alta.json()["id"]
    cab_g = _token(g)

    me = await http_client.get("/api/v1/me", headers=cab_g)
    assert me.status_code == 200, me.text
    assert me.json()["is_super_admin"] is True, me.json()

    baja = await http_client.put(f"/api/v1/users/{g}", headers=cab_g,
                                json={"is_active": False})
    assert baja.status_code == 403, (
        f"la autoridad global se desactivó a sí misma: {baja.status_code} "
        f"{baja.text[:300]}")
    assert "desactivarse" in baja.json()["detail"], baja.json()["detail"]
    assert await _activo_en_base(escenario, g) is True
    assert (await http_client.get("/api/v1/me", headers=cab_g)).status_code == 200



# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-05` · desactivar no es editar
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_05_desactivar_exige_el_permiso_de_baja(http_client, escenario):
    """`AR-07` · `AC-ID-05`.

    `PUT is_active=false` es la mitad destructiva de la administración y en HEAD la
    ejecutaba cualquiera con `users:update` — el mismo permiso que renombrar. La baja ya
    tenía su propio permiso en `DELETE /users/{id}`; ahora el `PUT` no es una puerta que lo
    esquive. Reactivar sigue siendo `users:update`: no destruye nada.
    """
    cab = _token(escenario["admin"])            # users:* + lots:read
    cab_sin_baja = _token(escenario["sin_borrar"])  # users:read/update, sin users:delete

    objetivo = (await _alta_usuario(http_client, cab, quien="objetivo-id05")).json()

    negado = await http_client.put(f"/api/v1/users/{objetivo['id']}", headers=cab_sin_baja,
                                   json={"is_active": False})
    assert negado.status_code == 403, (
        f"se desactivó un usuario sin users:delete: {negado.status_code} "
        f"{negado.text[:300]}")
    assert "users:delete" in negado.json()["detail"], negado.json()["detail"]
    assert await _activo_en_base(escenario, objetivo["id"]) is True, (
        "el usuario quedó inactivo pese al rechazo")

    # CONTROL · con `users:delete` la baja pasa.
    baja = await http_client.put(f"/api/v1/users/{objetivo['id']}", headers=cab,
                                json={"is_active": False})
    assert baja.status_code == 200, (
        f"la baja legítima falló: {baja.status_code} {baja.text[:300]}")
    assert await _activo_en_base(escenario, objetivo["id"]) is False

    # CONTROL · reactivar solo exige `users:update`.
    reactivar = await http_client.put(f"/api/v1/users/{objetivo['id']}", headers=cab_sin_baja,
                                      json={"is_active": True})
    assert reactivar.status_code == 200, (
        f"reactivar exigió más que users:update: {reactivar.status_code} "
        f"{reactivar.text[:300]}")
    assert await _activo_en_base(escenario, objetivo["id"]) is True



# ══════════════════════════════════════════════════════════════════════════════
#  `AC-ID-06` · la nueva contraseña tiene que ser nueva
# ══════════════════════════════════════════════════════════════════════════════

async def test_ac_id_06_la_nueva_contrasena_no_puede_ser_la_vigente(http_client, escenario):
    """`AR-10` · `AC-ID-06`. Aceptar la contraseña vigente como «nueva» deja creer al
    usuario que cambió algo que no cambió — el mismo silencio de `P0-13`, por otra puerta.

    Vale para los dos caminos: el titular y el restablecimiento por un administrador.
    """
    from app.auth.security import verify_password

    admin = escenario["admin"]
    cab = _token(admin)

    # Titular: la actual correcta y la nueva IGUAL ⇒ 422, y el hash no se toca.
    hash_antes = await _hash_en_base(escenario, admin)
    igual = await http_client.post(f"/api/v1/users/{admin}/password", headers=cab, json={
        "current_password": CLAVE, "new_password": CLAVE})
    assert igual.status_code == 422, (
        f"se aceptó como nueva la contraseña vigente del titular: {igual.status_code} "
        f"{igual.text[:300]}")
    assert "distinta" in igual.json()["detail"], igual.json()["detail"]
    assert await _hash_en_base(escenario, admin) == hash_antes, "la contraseña cambió igual"

    # Administrador que restablece a la contraseña que el usuario ya tiene ⇒ 422.
    objetivo = (await _alta_usuario(http_client, cab, quien="objetivo-id06")).json()
    hash_objetivo = await _hash_en_base(escenario, objetivo["id"])
    restablecer_igual = await http_client.post(
        f"/api/v1/users/{objetivo['id']}/password", headers=cab,
        json={"new_password": CLAVE})
    assert restablecer_igual.status_code == 422, (
        f"el restablecimiento aceptó la contraseña vigente: "
        f"{restablecer_igual.status_code} {restablecer_igual.text[:300]}")
    assert "distinta" in restablecer_igual.json()["detail"], restablecer_igual.json()["detail"]
    assert await _hash_en_base(escenario, objetivo["id"]) == hash_objetivo

    # CONTROL · una contraseña distinta sí se cambia (204) y es la que queda guardada.
    nueva = "NuevaClaveEs2026"
    cambio = await http_client.post(f"/api/v1/users/{objetivo['id']}/password", headers=cab,
                                    json={"new_password": nueva})
    assert cambio.status_code == 204, (
        f"no se pudo cambiar a una contraseña distinta: {cambio.status_code} "
        f"{cambio.text[:300]}")
    assert verify_password(nueva, await _hash_en_base(escenario, objetivo["id"])), (
        "la contraseña guardada no es la nueva")

    # Y el titular con una distinta: 204.
    propio = await http_client.post(f"/api/v1/users/{admin}/password", headers=cab, json={
        "current_password": CLAVE, "new_password": nueva})
    assert propio.status_code == 204, (
        f"el titular no pudo cambiar a una contraseña distinta: {propio.status_code} "
        f"{propio.text[:300]}")
    assert verify_password(nueva, await _hash_en_base(escenario, admin))

