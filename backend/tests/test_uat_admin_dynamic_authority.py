"""`SPEC 013` · UAT Administración — autoridad dinámica (`B4b1a`).

Cubre `AC-MX-02`: el rol y los permisos de un usuario se leen de la base en CADA
petición, de modo que revocar un permiso, cambiar el rol, dar de baja la cuenta o
desactivar el rol surten efecto de inmediato — sin esperar a que caduque el token.

Si la autoridad viajara dentro del token, el `403` no llegaría hasta el refresco y una
revocación dejaría una ventana de privilegio de la vida del access token.

PREFIJOS propios para poder limpiar sin tocar la siembra: roles `DA-TEST-`, usuarios
`da_test_` y empresas `DA-TEST-EMPRESA-`.
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
from app.auth.security import create_access_token

PREFIJO_ROL = "DA-TEST-"
PREFIJO_USUARIO = "da_test_"
PREFIJO_EMPRESA = "DA-TEST-EMPRESA-"

CLAVE = "ClaveDa2026x"


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
        # Los asientos de sesión y de cambio de permisos sobreviven al rechazo: se borran
        # explícitamente, en el mismo orden que las claves foráneas.
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
    """Una empresa con el administrador y los roles que estas pruebas necesitan.

    ```
    EMPRESA A
      ADMIN       users:read/create/update/delete + audit:read + lots:read

      ROL_AUDIT_LOTES  audit:read + lots:read   sujeto de `DA-01`
      ROL_AUDIT        audit:read               sujeto de `DA-02` (rol A) y `DA-03`/`DA-04`
      ROL_LOTES        lots:read                sujeto de `DA-02` (rol B)
    ```

    El `ADMIN` es de empresa y posee **explícitamente** cada permiso que reparte: nada de
    `("*", …)`, que lo convertiría en autoridad global y lo eximiría de `DR-3`.
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
            ("users", "delete"), ("audit", "read"), ("lots", "read")])
        rol_audit_lotes, perms_audit_lotes = _rol(
            "ROL-AUDIT-LOTES", [("audit", "read"), ("lots", "read")])
        rol_audit, perms_audit = _rol("ROL-AUDIT", [("audit", "read")])
        rol_lotes, perms_lotes = _rol("ROL-LOTES", [("lots", "read")])
        await s.flush()

        for rol, pares in ((rol_admin, perms_admin),
                           (rol_audit_lotes, perms_audit_lotes),
                           (rol_audit, perms_audit), (rol_lotes, perms_lotes)):
            for modulo, accion in pares:
                s.add(Permission(role_id=rol.id, module=modulo,
                                 action=PermissionAction(accion), scope_type="company"))

        admin = User(first_name="Admin", last_name="Dinámico",
                     email=f"{PREFIJO_USUARIO}admin-{sufijo}@example.com",
                     username=f"{PREFIJO_USUARIO}admin-{sufijo}",
                     hashed_password=hash_password(CLAVE),
                     company_id=a.id, role_id=rol_admin.id, is_active=True)
        s.add(admin)
        await s.flush()
        await s.commit()
        return {
            "empresa_a": a.id,
            "admin": admin.id,
            "rol_admin": rol_admin.id,
            "rol_audit_lotes": rol_audit_lotes.id,
            "rol_audit": rol_audit.id,
            "rol_lotes": rol_lotes.id,
            "sufijo": sufijo, "url": test_database_url,
        }

# ══════════════════════════════════════════════════════════════════════════════
#  Utilidades
# ══════════════════════════════════════════════════════════════════════════════

def _token(user_id: int, company_id: int | None = None) -> dict:
    """Cabecera del administrador; la empresa y los permisos salen de la base."""
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


def _cab(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


async def _login(http, usuario: str, clave: str = CLAVE):
    return await http.post("/api/v1/login", json={"username": usuario, "password": clave})


async def _alta_sujeto(http, cabeceras, *, role_id: int, quien: str):
    """El usuario sujeto se da de alta por API: contraseña conocida, rol elegido.

    El administrador de empresa **no** manda `company_id`: se resuelve por contexto.
    """
    marca = f"{quien}-{uuid.uuid4().hex[:8]}"
    usuario = f"{PREFIJO_USUARIO}{marca}"
    alta = await http.post("/api/v1/users", headers=cabeceras, json={
        "first_name": "Autoridad", "last_name": "Dinámica",
        "email": f"{usuario}@example.com", "username": usuario,
        "password": CLAVE, "role_id": role_id})
    return alta, usuario


async def _desactivar_rol_por_sql(escenario, role_id: int) -> None:
    """Apaga el rol saltándose la API: nadie pasa por aquí salvo esta prueba.

    Modela el rol que un `UPDATE` administrativo o una migración deja inactivo mientras
    alguien ya tiene sesión abierta.
    """
    from app.auth.models import Role

    e = create_async_engine(escenario["url"])
    try:
        async with e.begin() as c:
            await c.execute(update(Role).where(Role.id == role_id).values(is_active=False))
    finally:
        await e.dispose()

# ══════════════════════════════════════════════════════════════════════════════
#  `AC-MX-02` · la autoridad se lee en cada petición
# ══════════════════════════════════════════════════════════════════════════════

async def test_da_01_permiso_allow_revoke_deny_restore_allow_mismo_token(
    http_client, escenario
):
    """`AC-MX-02` · concedido ⇒ responde; revocado ⇒ el **mismo** access token deja de
    pasar; restaurado ⇒ el mismo token vuelve a pasar.

    El ciclo completo con una sola sesión: si los permisos viajaran dentro del token, la
    revocación no se notaría hasta emitir otro y la restauración tampoco. Refresco y
    relogin se comprueban al final, sobre el estado vigente.
    """
    admin = _token(escenario["admin"])
    rol = escenario["rol_audit_lotes"]

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=rol, quien="da01")
    assert alta.status_code == 201, alta.text
    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab = _cab(sesion.json()["access_token"])

    assert (await http_client.get("/api/v1/audit", headers=cab)).status_code == 200
    me = await http_client.get("/api/v1/me", headers=cab)
    assert me.status_code == 200, me.text
    assert me.json()["permissions"] == ["audit:read", "lots:read"], me.json()

    # ── revocación: solo queda `lots:read` ────────────────────────────────────
    revocar = await http_client.put(f"/api/v1/roles/{rol}", headers=admin,
                                    json={"permissions": [_permiso("lots")]})
    assert revocar.status_code == 200, (
        f"retirar un permiso del rol falló: {revocar.status_code} {revocar.text[:300]}")

    negado = await http_client.get("/api/v1/audit", headers=cab)
    assert negado.status_code == 403, (
        f"el mismo token siguió pasando tras revocar el permiso: {negado.status_code} "
        f"{negado.text[:300]}")
    assert negado.json()["detail"] == "Permiso requerido: audit:read", negado.json()
    me = await http_client.get("/api/v1/me", headers=cab)
    assert me.json()["permissions"] == ["lots:read"], me.json()
    assert (await http_client.get("/api/v1/lots", headers=cab)).status_code == 200

    # ── restauración: el permiso vuelve sin tocar la sesión ───────────────────
    restaurar = await http_client.put(f"/api/v1/roles/{rol}", headers=admin, json={
        "permissions": [_permiso("audit"), _permiso("lots")]})
    assert restaurar.status_code == 200, restaurar.text

    assert (await http_client.get("/api/v1/audit", headers=cab)).status_code == 200
    me = await http_client.get("/api/v1/me", headers=cab)
    assert me.json()["permissions"] == ["audit:read", "lots:read"], me.json()

    # ── refresco y relogin reflejan el estado vigente ─────────────────────────
    nuevo = await http_client.post("/api/v1/refresh",
                                   json={"refresh_token": sesion.json()["refresh_token"]})
    assert nuevo.status_code == 200, nuevo.text
    cab_refresco = _cab(nuevo.json()["access_token"])
    assert (await http_client.get("/api/v1/audit", headers=cab_refresco)).status_code == 200
    assert (await http_client.get("/api/v1/me", headers=cab_refresco)).json()[
        "permissions"] == ["audit:read", "lots:read"]

    otra = await _login(http_client, usuario)
    assert otra.status_code == 200, otra.text
    cab_relogin = _cab(otra.json()["access_token"])
    assert (await http_client.get("/api/v1/audit", headers=cab_relogin)).status_code == 200
    assert (await http_client.get("/api/v1/me", headers=cab_relogin)).json()[
        "permissions"] == ["audit:read", "lots:read"]

async def test_da_02_cambio_de_rol_reemplaza_no_une(http_client, escenario):
    """`AC-MX-02` · cambiar de rol **sustituye** el conjunto de permisos; no lo une.

    Si el cambio se acumulara, ascender a alguien de `audit:read` a `lots:read` lo dejaría
    con los dos permisos y la administración no podría retirar nada moviendo de rol. El
    mismo access token tiene que notarlo en la petición siguiente.
    """
    admin = _token(escenario["admin"])
    rol_a = escenario["rol_audit"]          # audit:read
    rol_b = escenario["rol_lotes"]          # lots:read

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=rol_a, quien="da02")
    assert alta.status_code == 201, alta.text
    uid = alta.json()["id"]
    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab = _cab(sesion.json()["access_token"])

    assert (await http_client.get("/api/v1/audit", headers=cab)).status_code == 200
    assert (await http_client.get("/api/v1/me", headers=cab)).json()["permissions"] == [
        "audit:read"]

    cambio = await http_client.put(f"/api/v1/users/{uid}", headers=admin,
                                   json={"role_id": rol_b})
    assert cambio.status_code == 200, (
        f"el cambio de rol falló: {cambio.status_code} {cambio.text[:300]}")

    nuevo = await http_client.post("/api/v1/refresh",
                                   json={"refresh_token": sesion.json()["refresh_token"]})
    assert nuevo.status_code == 200, nuevo.text
    otra = await _login(http_client, usuario)
    assert otra.status_code == 200, otra.text

    casos = (
        ("mismo token", cab),
        ("tras refresh", _cab(nuevo.json()["access_token"])),
        ("tras relogin", _cab(otra.json()["access_token"])),
    )
    for etiqueta, cabeceras in casos:
        negado = await http_client.get("/api/v1/audit", headers=cabeceras)
        assert negado.status_code == 403, (
            f"[{etiqueta}] el rol anterior siguió vigente: {negado.status_code} "
            f"{negado.text[:300]}")
        assert negado.json()["detail"] == "Permiso requerido: audit:read", (etiqueta,
                                                                          negado.json())
        propio = await http_client.get("/api/v1/lots", headers=cabeceras)
        assert propio.status_code == 200, (etiqueta, propio.status_code, propio.text[:300])
        me = await http_client.get("/api/v1/me", headers=cabeceras)
        assert me.json()["permissions"] == ["lots:read"], (etiqueta, me.json())

async def test_da_03_usuario_activo_inactivo_deny_y_reactivacion(http_client, escenario):
    """`AC-MX-02` · la baja corta la sesión viva y el refresco; la reactivación la reabre.

    Un token emitido antes de la baja no puede seguir valiendo —ni servir para renovarse—,
    y un usuario inactivo no puede volver a entrar hasta que un administrador lo reactive.
    La baja por `DELETE` y por `PUT is_active=false` tienen que surtir idéntico efecto.
    """
    admin = _token(escenario["admin"])
    rol = escenario["rol_audit"]            # audit:read

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=rol, quien="da03")
    assert alta.status_code == 201, alta.text
    uid = alta.json()["id"]
    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab = _cab(sesion.json()["access_token"])
    assert (await http_client.get("/api/v1/audit", headers=cab)).status_code == 200

    baja = await http_client.delete(f"/api/v1/users/{uid}", headers=admin)
    assert baja.status_code == 204, (
        f"la baja no devolvió 204: {baja.status_code} {baja.text[:300]}")

    assert (await http_client.get("/api/v1/me", headers=cab)).status_code == 401, (
        "el token de un usuario dado de baja siguió sirviendo")
    assert (await http_client.get("/api/v1/audit", headers=cab)).status_code == 401
    renovar = await http_client.post("/api/v1/refresh",
                                     json={"refresh_token": sesion.json()["refresh_token"]})
    assert renovar.status_code == 401, (
        f"un usuario inactivo pudo refrescar: {renovar.status_code} {renovar.text[:300]}")
    negado = await _login(http_client, usuario)
    assert negado.status_code == 403, (
        f"un usuario inactivo pudo entrar: {negado.status_code} {negado.text[:300]}")
    assert negado.json()["detail"] == "Cuenta desactivada. Contacte al administrador.", (
        negado.json())

    # ── reactivación: vuelve a entrar y el permiso vuelve con él ──────────────
    reactivar = await http_client.put(f"/api/v1/users/{uid}", headers=admin,
                                      json={"is_active": True})
    assert reactivar.status_code == 200, (
        f"la reactivación falló: {reactivar.status_code} {reactivar.text[:300]}")
    vuelta = await _login(http_client, usuario)
    assert vuelta.status_code == 200, vuelta.text
    cab_vuelta = _cab(vuelta.json()["access_token"])
    assert (await http_client.get("/api/v1/audit", headers=cab_vuelta)).status_code == 200

    # ── misma baja, por la otra puerta: `PUT is_active=false` ────────────────
    otra_baja = await http_client.put(f"/api/v1/users/{uid}", headers=admin,
                                      json={"is_active": False})
    assert otra_baja.status_code == 200, (
        f"la baja por PUT falló: {otra_baja.status_code} {otra_baja.text[:300]}")

    assert (await http_client.get("/api/v1/me", headers=cab_vuelta)).status_code == 401
    assert (await http_client.get("/api/v1/audit", headers=cab_vuelta)).status_code == 401
    renovar_2 = await http_client.post(
        "/api/v1/refresh", json={"refresh_token": vuelta.json()["refresh_token"]})
    assert renovar_2.status_code == 401, renovar_2.text
    negado_2 = await _login(http_client, usuario)
    assert negado_2.status_code == 403, negado_2.text
    assert negado_2.json()["detail"] == "Cuenta desactivada. Contacte al administrador."

async def test_da_04_rol_inactivo_por_sql_no_confiere_y_se_recupera_al_reactivar(
    http_client, escenario
):
    """`AC-MX-02` · un rol inactivo no confiere nada, aunque esté asignado y la sesión
    siga abierta; al reactivarlo, el **mismo** token vuelve a mandar.

    El caso real: un administrador apaga un rol desde otra vía —o una migración lo deja
    inactivo— mientras alguien ya tiene sesión. `get_current_user` tiene que leer el
    `is_active` del rol en la base, no confiar en lo que hubiera al emitir el token.
    """
    admin = _token(escenario["admin"])
    rol = escenario["rol_audit"]            # audit:read

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=rol, quien="da04")
    assert alta.status_code == 201, alta.text
    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab = _cab(sesion.json()["access_token"])
    assert (await http_client.get("/api/v1/audit", headers=cab)).status_code == 200

    await _desactivar_rol_por_sql(escenario, rol)

    negado = await http_client.get("/api/v1/audit", headers=cab)
    assert negado.status_code == 403, (
        f"un rol inactivo siguió confiriendo permisos: {negado.status_code} "
        f"{negado.text[:300]}")
    me = await http_client.get("/api/v1/me", headers=cab)
    assert me.status_code == 200, me.text
    assert me.json()["permissions"] == [], me.json()

    reactivar = await http_client.put(f"/api/v1/roles/{rol}", headers=admin,
                                      json={"is_active": True})
    assert reactivar.status_code == 200, (
        f"la reactivación del rol falló: {reactivar.status_code} {reactivar.text[:300]}")
    assert (await http_client.get("/api/v1/audit", headers=cab)).status_code == 200, (
        "el mismo token no recuperó el permiso al reactivar el rol")

async def test_da_05_politica_de_sesion_tras_cambio_de_clave_dr4(http_client, escenario):
    """`DR-4` · el cambio de clave **no** revoca los tokens ya emitidos.

    Contrato vigente `GA-REM-012` AC08: el access y el refresh previos al cambio siguen
    valiendo; si el cambio debiera revocarlos es la decisión `OD-01`, todavía abierta. Lo
    que sí cambia de inmediato es la entrada: la clave vieja deja de abrir sesión.
    """
    admin = _token(escenario["admin"])
    rol = escenario["rol_lotes"]            # lots:read
    nueva = "ClaveDa2026nueva"

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=rol, quien="da05")
    assert alta.status_code == 201, alta.text
    uid = alta.json()["id"]
    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    access_previo = _cab(sesion.json()["access_token"])
    refresh_previo = sesion.json()["refresh_token"]
    assert (await http_client.get("/api/v1/lots", headers=access_previo)).status_code == 200

    cambio = await http_client.post(f"/api/v1/users/{uid}/password", headers=access_previo,
                                    json={"current_password": CLAVE, "new_password": nueva})
    assert cambio.status_code == 204, (
        f"el cambio de clave no devolvió 204: {cambio.status_code} {cambio.text[:300]}")

    # ── DR-4 · contrato vigente `GA-REM-012` AC08 (`OD-01` ABIERTA) ───────────
    # El cambio de clave NO revoca los tokens previos: el access sigue sirviendo y el
    # refresh previo se puede canjear. Si `OD-01` se resuelve por revocar, esto cambia.
    me = await http_client.get("/api/v1/me", headers=access_previo)
    assert me.status_code == 200, (
        f"el access previo al cambio de clave dejó de valer: {me.status_code} {me.text[:300]}")
    renovar = await http_client.post("/api/v1/refresh",
                                     json={"refresh_token": refresh_previo})
    assert renovar.status_code == 200, (
        f"el refresh previo al cambio de clave dejó de valer: {renovar.status_code} "
        f"{renovar.text[:300]}")

    vieja = await _login(http_client, usuario)
    assert vieja.status_code == 401, (
        f"la clave vieja siguió abriendo sesión: {vieja.status_code} {vieja.text[:300]}")
    buena = await _login(http_client, usuario, nueva)
    assert buena.status_code == 200, (
        f"la clave nueva no abre sesión: {buena.status_code} {buena.text[:300]}")

    corta = await http_client.post(f"/api/v1/users/{uid}/password", headers=access_previo,
                                  json={"current_password": nueva, "new_password": "ClaveDa"})
    assert corta.status_code == 422, (
        f"una clave de 7 caracteres no fue rechazada: {corta.status_code} {corta.text[:300]}")
    errada = await http_client.post(f"/api/v1/users/{uid}/password", headers=access_previo,
                                    json={"current_password": "IncorrectaDa2026x",
                                          "new_password": "OtraClave2026x"})
    assert errada.status_code == 400, (
        f"una clave actual incorrecta no devolvió 400: {errada.status_code} "
        f"{errada.text[:300]}")

    # la clave sigue siendo la nueva: los rechazos no la tocaron
    assert (await _login(http_client, usuario, nueva)).status_code == 200

async def test_da_06_scope_type_se_ignora_pin_r123(http_client, escenario):
    """`R-123` (ABIERTA) · hoy el `scope_type`/`scope_id` del permiso **no** se evalúa.

    Se concede `lots:read` con alcance `farm`/`999999` —una granja ajena e inexistente— y el
    sujeto pasa igual en `GET /lots`. Este test **fija la política VIGENTE**: cuando `R-123`
    se implemente habrá que revisarlo, porque entonces ese permiso debería alcanzar solo esa
    granja y no el listado completo.
    """
    from app.auth.models import Permission, PermissionAction, Role

    sufijo = uuid.uuid4().hex[:8]
    e = create_async_engine(escenario["url"])
    try:
        async with async_sessionmaker(e, expire_on_commit=False)() as s:
            rol = Role(name=f"{PREFIJO_ROL}SCOPE-FARM-{sufijo}",
                       company_id=escenario["empresa_a"], is_active=True)
            s.add(rol)
            await s.flush()
            s.add(Permission(role_id=rol.id, module="lots", action=PermissionAction.READ,
                             scope_type="farm", scope_id=999999))
            await s.commit()
            rol_id = rol.id
    finally:
        await e.dispose()

    admin = _token(escenario["admin"])
    alta, usuario = await _alta_sujeto(http_client, admin, role_id=rol_id, quien="da06")
    assert alta.status_code == 201, alta.text
    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab = _cab(sesion.json()["access_token"])

    listado = await http_client.get("/api/v1/lots", headers=cab)
    assert listado.status_code == 200, (
        f"el alcance `farm` bloqueó el listado: el comportamiento cambió, revisar R-123: "
        f"{listado.status_code} {listado.text[:300]}")

# ══════════════════════════════════════════════════════════════════════════════
#  `AC-MX-04` · alta de usuarios y auditoría con antes/después
# ══════════════════════════════════════════════════════════════════════════════

async def test_da_07_campos_obligatorios_del_alta(http_client, escenario):
    """`AC-MX-04` · el alta exige `first_name`, `last_name`, `username`, `email` válido y
    `password` de 8 o más: omitir cualquiera —o mandarlo mal— se rechaza con `422`.

    Sin esa puerta un usuario podría nacer sin nombre, sin identificador de entrada o con
    una clave de un carácter, y la administración no tendría con qué rastrearlo.
    """
    admin = _token(escenario["admin"])
    rol = escenario["rol_audit"]            # audit:read
    marca = uuid.uuid4().hex[:8]
    valido = {
        "first_name": "Obligatorio", "last_name": "Campo",
        "username": f"{PREFIJO_USUARIO}da07-{marca}",
        "email": f"{PREFIJO_USUARIO}da07-{marca}@example.com",
        "password": CLAVE, "role_id": rol,
    }

    async def _alta(cuerpo):
        return await http_client.post("/api/v1/users", headers=admin, json=cuerpo)

    for campo in ("first_name", "last_name", "username", "email", "password"):
        falta = await _alta({k: v for k, v in valido.items() if k != campo})
        assert falta.status_code == 422, (
            f"omitir `{campo}` no devolvió 422: {falta.status_code} {falta.text[:300]}")

    for etiqueta, cuerpo in (
            ("email mal formado", {**valido, "email": "no-es-un-correo"}),
            ("password de 7 caracteres", {**valido, "password": "ClaveDa"})):
        malo = await _alta(cuerpo)
        assert malo.status_code == 422, (
            f"{etiqueta} no devolvió 422: {malo.status_code} {malo.text[:300]}")

    # control: el cuerpo completo sí crea (los rechazos no dejaron basura a medias)
    bueno = await _alta(valido)
    assert bueno.status_code == 201, bueno.text


async def test_da_07b_role_id_es_opcional_en_el_alta(http_client, escenario):
    """`AC-MX-04` · contrato VIGENTE: `role_id` es **opcional** en el alta.

    Un usuario puede nacer sin rol —pendiente de asignación, p. ej. para altas masivas o
    cuentas creadas antes de decidir el puesto—. Queda entonces sin permiso alguno: tras
    entrar, `/me.permissions` viene vacío y `GET /lots` responde `403`. Cuando la política
    cambie a «rol obligatorio», este test habrá que revisarlo.
    """
    admin = _token(escenario["admin"])
    usuario = f"{PREFIJO_USUARIO}da07b-{uuid.uuid4().hex[:8]}"

    alta = await http_client.post("/api/v1/users", headers=admin, json={
        "first_name": "Sin", "last_name": "Rol",
        "email": f"{usuario}@example.com", "username": usuario,
        "password": CLAVE})
    assert alta.status_code == 201, (
        f"omitir `role_id` no devolvió 201: {alta.status_code} {alta.text[:300]}")
    assert alta.json().get("role_id") is None, alta.json()

    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, (
        f"un usuario sin rol no pudo entrar: {sesion.status_code} {sesion.text[:300]}")
    cab = _cab(sesion.json()["access_token"])

    me = await http_client.get("/api/v1/me", headers=cab)
    assert me.status_code == 200, me.text
    assert me.json()["permissions"] == [], me.json()

    negado = await http_client.get("/api/v1/lots", headers=cab)
    assert negado.status_code == 403, (
        f"un usuario sin rol pasó `GET /lots`: {negado.status_code} {negado.text[:300]}")
    assert negado.json()["detail"] == "Permiso requerido: lots:read", negado.json()


async def test_da_08_auditoria_con_before_after_y_sin_secretos(http_client, escenario):
    """`AC-MX-04` · la auditoría de un usuario cuenta la vida entera del registro —alta,
    cambio de rol, cambio de clave y baja— con **antes y después**, y sin filtrar secretos.

    Es la traza con la que se responde «¿quién le dio este permiso y cuándo se lo quitó?».
    También se comprueba lo que **no** puede aparecer: ni la clave en claro, ni un `$2b$`
    de bcrypt, ni el nombre de un campo de hash, en ninguna fila de la respuesta.
    """
    admin = _token(escenario["admin"])
    rol_a = escenario["rol_audit"]          # audit:read
    rol_b = escenario["rol_lotes"]          # lots:read
    nueva = "ClaveDa2026nueva"

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=rol_a, quien="da08")
    assert alta.status_code == 201, alta.text
    uid = alta.json()["id"]

    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab_u = _cab(sesion.json()["access_token"])

    cambio_rol = await http_client.put(f"/api/v1/users/{uid}", headers=admin,
                                       json={"role_id": rol_b})
    assert cambio_rol.status_code == 200, (
        f"el cambio de rol falló: {cambio_rol.status_code} {cambio_rol.text[:300]}")

    clave = await http_client.post(f"/api/v1/users/{uid}/password", headers=cab_u,
                                   json={"current_password": CLAVE, "new_password": nueva})
    assert clave.status_code == 204, (
        f"el cambio de clave propia falló: {clave.status_code} {clave.text[:300]}")

    baja = await http_client.delete(f"/api/v1/users/{uid}", headers=admin)
    assert baja.status_code == 204, (
        f"la baja no devolvió 204: {baja.status_code} {baja.text[:300]}")

    auditoria = await http_client.get("/api/v1/audit?limit=100", headers=admin)
    assert auditoria.status_code == 200, auditoria.text
    cuerpo = auditoria.json()
    assert "total" in cuerpo and isinstance(cuerpo["logs"], list), cuerpo.keys()

    def _antes_despues(valor):
        """`previous_values`/`new_values` llegan como JSON ya decodificado o como texto."""
        import json

        if isinstance(valor, str):
            return json.loads(valor)
        return valor or {}

    filas = [f for f in cuerpo["logs"]
             if f["entity_id"] == str(uid)
             and f["entity_type"] in ("user", "user_password")]
    altas = [f for f in filas if f["action"] == "created"]
    cambios = [f for f in filas if f["entity_type"] == "user" and f["action"] == "updated"]
    claves = [f for f in filas if f["entity_type"] == "user_password"]
    bajas = [f for f in filas if f["action"] == "deleted"]
    for etiqueta, grupo in (("alta", altas), ("cambio de rol", cambios),
                            ("cambio de clave", claves), ("baja", bajas)):
        assert len(grupo) == 1, (etiqueta, len(grupo), filas)

    # ── alta: `created` con los campos que identifican al usuario creado ──────
    nuevos = _antes_despues(altas[0]["new_values"])
    for campo in ("username", "role_id", "company_id", "view_type"):
        assert campo in nuevos, (campo, nuevos)
    assert nuevos["username"] == usuario, nuevos
    assert altas[0]["entity_type"] == "user", altas[0]

    # ── cambio de rol: `updated` con el `role_id` de antes y el de después ────
    previo = _antes_despues(cambios[0]["previous_values"])
    posterior = _antes_despues(cambios[0]["new_values"])
    assert "role_id" in previo and "role_id" in posterior, (previo, posterior)
    assert previo["role_id"] == rol_a, previo
    assert posterior["role_id"] == rol_b, posterior
    assert previo["role_id"] != posterior["role_id"], (previo, posterior)

    # ── baja: `deleted` con el rastro de la desactivación ─────────────────────
    assert _antes_despues(bajas[0]["new_values"]) == {"is_active": False}, bajas[0]

    # ── cambio de clave propia: fila propia y con su comentario ───────────────
    assert claves[0]["action"] == "updated", claves[0]
    assert claves[0]["comments"] == "Cambio de contraseña propia", claves[0]

    # ── ninguna fila de TODA la respuesta puede llevar un secreto ─────────────
    import json

    volcado = json.dumps(cuerpo["logs"], ensure_ascii=False)
    for prohibido in (CLAVE, nueva, "$2b$"):
        assert prohibido not in volcado, (
            f"la auditoría filtró `{prohibido}`: {volcado[:400]}")
    assert "hashed" not in volcado.lower(), (
        f"la auditoría expuso un campo de hash: {volcado[:400]}")


