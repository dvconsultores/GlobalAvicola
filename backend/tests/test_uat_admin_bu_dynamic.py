"""`SPEC 013` · UAT Administración — unidades de negocio con el mismo token (`B4b2`).

Cubre `AC-MX-03`: las **unidades de negocio** de un usuario se leen de la base en CADA
petición, igual que sus permisos (`AC-MX-02`). Conceder una unidad abre el acceso en la
petición siguiente y revocarla lo cierra, **sin esperar a que se emita otro token**.

Si las unidades viajaran dentro del token, revocar dejaría viva una ventana de privilegio
de la vida del access token: el usuario seguiría viendo lotes que ya no le pertenecen.
Aquí se mide el ciclo completo — permitir, revocar, denegar, restaurar, permitir — sobre
una sola sesión, y que la revocación de una unidad no arrastra a las demás.

PREFIJOS propios para limpiar sin tocar la siembra: roles `BD-TEST-`, usuarios `bd_test_`,
empresas `BD-TEST-EMPRESA-` y lotes `BD-TEST-LOTE-`.
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
from app.auth.security import create_access_token

PREFIJO_ROL = "BD-TEST-"
PREFIJO_USUARIO = "bd_test_"
PREFIJO_EMPRESA = "BD-TEST-EMPRESA-"
PREFIJO_LOTE = "BD-TEST-LOTE-"

CLAVE = "ClaveBd2026x"
# ══════════════════════════════════════════════════════════════════════════════
#  Limpieza — prefijos propios, nunca la siembra
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.auth.models import Permission, Role, User
    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit
    from app.masters.models import Company, Lot

    async with e.begin() as c:
        empresas = (await c.execute(
            select(Company.id).where(Company.name.like(f"{PREFIJO_EMPRESA}%")))).scalars().all()
        usuarios = (await c.execute(
            select(User.id).where(User.username.like(f"{PREFIJO_USUARIO}%")))).scalars().all()
        roles = (await c.execute(
            select(Role.id).where(Role.name.like(f"{PREFIJO_ROL}%")))).scalars().all()
        lotes = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO_LOTE}%")))).scalars().all()
        # `audit_logs` cuelga de empresa, de usuario y de lote: se borra antes que ellos.
        if empresas:
            await c.execute(delete(AuditLog).where(AuditLog.company_id.in_(empresas)))
        if usuarios:
            await c.execute(delete(AuditLog).where(AuditLog.user_id.in_(usuarios)))
        if lotes:
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lotes)))
            await c.execute(delete(Lot).where(Lot.id.in_(lotes)))
        habilitaciones = []
        if empresas:
            habilitaciones = (await c.execute(select(CompanyBusinessUnit.id).where(
                CompanyBusinessUnit.company_id.in_(empresas)))).scalars().all()
        if usuarios:
            await c.execute(delete(UserBusinessUnit).where(
                UserBusinessUnit.user_id.in_(usuarios)))
        if habilitaciones:
            await c.execute(delete(UserBusinessUnit).where(
                UserBusinessUnit.company_business_unit_id.in_(habilitaciones)))
        if empresas:
            await c.execute(delete(CompanyBusinessUnit).where(
                CompanyBusinessUnit.company_id.in_(empresas)))
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
    """Una empresa con `broiler` y `breeder` habilitadas, su administrador y el rol sujeto.

    ```
    EMPRESA A   broiler ✓ habilitada · breeder ✓ habilitada   (hatchery/grandparent no)
      ADMIN             business_units:read/create/update/delete · users:read/create/update
                        lots:read + lots:create   — y las dos unidades concedidas por SQL
      ROL_LOTES         lots:read                 — el sujeto, al que se concede por API
    ```

    Al `ADMIN` se le conceden las unidades por el camino sancionado (`conceder_unidad`)
    porque `OD-15` le prohíbe concederse a sí mismo por la API: quien reparte no recibe.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    sufijo = uuid.uuid4().hex[:8]
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO_EMPRESA}A-{sufijo}", is_active=True)
        s.add(a)
        await s.flush()

        rol_admin = Role(name=f"{PREFIJO_ROL}ADMIN-{sufijo}", company_id=a.id, is_active=True)
        rol_lotes = Role(name=f"{PREFIJO_ROL}LOTES-{sufijo}", company_id=a.id, is_active=True)
        s.add_all([rol_admin, rol_lotes])
        await s.flush()

        for modulo, accion in (
            ("business_units", "read"), ("business_units", "create"),
            ("business_units", "delete"), ("business_units", "update"),
            ("users", "read"), ("users", "create"), ("users", "update"),
            ("lots", "read"), ("lots", "create"),
        ):
            s.add(Permission(role_id=rol_admin.id, module=modulo,
                             action=PermissionAction(accion), scope_type="company"))
        s.add(Permission(role_id=rol_lotes.id, module="lots",
                         action=PermissionAction.READ, scope_type="company"))
        admin = User(first_name="Admin", last_name="Unidades",
                     email=f"{PREFIJO_USUARIO}admin-{sufijo}@example.com",
                     username=f"{PREFIJO_USUARIO}admin-{sufijo}",
                     hashed_password=hash_password(CLAVE),
                     company_id=a.id, role_id=rol_admin.id, is_active=True)
        s.add(admin)
        await s.flush()
        await s.commit()
        datos = {"empresa_a": a.id, "admin": admin.id, "rol_admin": rol_admin.id,
                 "rol_lotes": rol_lotes.id, "sufijo": sufijo, "url": test_database_url}

    await _habilitar_y_conceder(datos["url"], company_id=datos["empresa_a"],
                                codes=("broiler", "breeder"), user_ids=[datos["admin"]])
    return datos
# ══════════════════════════════════════════════════════════════════════════════
#  Utilidades
# ══════════════════════════════════════════════════════════════════════════════

async def _habilitar_y_conceder(url: str, *, company_id: int, codes, user_ids) -> None:
    """Habilita esas cadenas a la empresa y las concede a esos usuarios.

    Idempotente y por el camino de escritura sancionado —`conceder_unidad`—, de modo que la
    concesión queda acotada a la empresa igual que la haría la administración por la API.
    Es lo que permite al `ADMIN` crear lotes de cada cadena sin poder concederse a sí mismo
    (`OD-15`).
    """
    from app.auth.models import User
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit
    from app.business_units.service import conceder_unidad

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            filas = {}
            for code in codes:
                unidad = (await s.execute(select(BusinessUnit).where(
                    BusinessUnit.code == code))).scalar_one()
                fila = (await s.execute(select(CompanyBusinessUnit).where(
                    CompanyBusinessUnit.company_id == company_id,
                    CompanyBusinessUnit.business_unit_id == unidad.id))).scalar_one_or_none()
                if fila is None:
                    fila = CompanyBusinessUnit(company_id=company_id,
                                               business_unit_id=unidad.id, is_enabled=True)
                    s.add(fila)
                    await s.flush()
                else:
                    fila.is_enabled = True
                filas[code] = fila

            for user_id in user_ids:
                usuario = (await s.execute(
                    select(User).where(User.id == user_id))).scalar_one()
                for fila in filas.values():
                    viva = (await s.execute(select(UserBusinessUnit).where(
                        UserBusinessUnit.user_id == user_id,
                        UserBusinessUnit.company_business_unit_id == fila.id,
                        UserBusinessUnit.revoked_at.is_(None)))).scalar_one_or_none()
                    if viva is None:
                        await conceder_unidad(s, user=usuario, company_business_unit=fila)
            await s.commit()
    finally:
        await motor.dispose()
def _token(user_id: int, company_id: int | None = None) -> dict:
    """Cabecera del administrador; la empresa, los permisos y las unidades salen de la BD."""
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


def _cab(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


async def _login(http, usuario: str, clave: str = CLAVE):
    return await http.post("/api/v1/login", json={"username": usuario, "password": clave})


async def _alta_sujeto(http, cabeceras, *, role_id: int, quien: str):
    """El usuario sujeto se da de alta por API: contraseña conocida y rol elegido."""
    marca = f"{quien}-{uuid.uuid4().hex[:8]}"
    usuario = f"{PREFIJO_USUARIO}{marca}"
    alta = await http.post("/api/v1/users", headers=cabeceras, json={
        "first_name": "Unidades", "last_name": "Dinámicas",
        "email": f"{usuario}@example.com", "username": usuario,
        "password": CLAVE, "role_id": role_id})
    return alta, usuario


async def _crear_lote(http, cabeceras, tipo: str) -> int:
    """Un lote de esa cadena; la unidad del lote se deriva de `bird_type`."""
    r = await http.post("/api/v1/lots", headers=cabeceras, json={
        "lot_code": f"{PREFIJO_LOTE}{tipo.upper()}-{uuid.uuid4().hex[:8]}",
        "bird_type": tipo, "sex": "mixed"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _listado(http, cabeceras) -> set[int]:
    """Los identificadores de lote que ese actor alcanza, acotado a los lotes de la prueba."""
    r = await http.get(f"/api/v1/lots?limit=100&search={PREFIJO_LOTE}", headers=cabeceras)
    assert r.status_code == 200, (
        f"el listado de lotes falló: {r.status_code} {r.text[:300]}")
    return {lote["id"] for lote in r.json()}


async def _me(http, cabeceras) -> dict:
    r = await http.get("/api/v1/me", headers=cabeceras)
    assert r.status_code == 200, r.text
    return r.json()


async def _concesiones(http, cabeceras, user_id: int) -> list[dict]:
    r = await http.get(f"/api/v1/users/{user_id}/business-units", headers=cabeceras)
    assert r.status_code == 200, r.text
    return r.json()
# ══════════════════════════════════════════════════════════════════════════════
#  `AC-MX-03` · las unidades se leen en cada petición
# ══════════════════════════════════════════════════════════════════════════════

async def test_bd_01_allow_revoke_deny_restore_allow_mismo_token(http_client, escenario):
    """`AC-MX-03` · concedida ⇒ el sujeto ve su lote; revocada ⇒ el **mismo** access token
    deja de verlo y `/me` lo confiesa; re-concedida ⇒ el mismo token lo vuelve a ver.

    Una sola sesión para todo el ciclo. Si las unidades viajaran en el token, la revocación
    no se notaría hasta emitir otro y la re-concesión tampoco: la ventana de privilegio
    duraría la vida del token. Al final se comprueba la historia: revocar no borra, deja el
    rastro, y volver a conceder añade una fila viva sin resucitar la revocada.
    """
    admin = _token(escenario["admin"])

    unidades = await http_client.get("/api/v1/business-units", headers=admin)
    assert unidades.status_code == 200, unidades.text
    estados = {u["code"]: u["is_enabled"] for u in unidades.json()}
    assert len(estados) == 4, estados
    assert estados["broiler"] and estados["breeder"], estados

    lote_broiler = await _crear_lote(http_client, admin, "broiler")
    lote_breeder = await _crear_lote(http_client, admin, "breeder")
    alta, usuario = await _alta_sujeto(http_client, admin, role_id=escenario["rol_lotes"],
                                       quien="bd01")
    assert alta.status_code == 201, alta.text
    uid = alta.json()["id"]

    conceder = await http_client.post(f"/api/v1/users/{uid}/business-units", headers=admin,
                                      json={"code": "broiler"})
    assert conceder.status_code == 201, (
        f"conceder una unidad habilitada no devolvió 201: {conceder.status_code} "
        f"{conceder.text[:300]}")
    otorgada = conceder.json()
    assert otorgada["code"] == "broiler", otorgada
    assert otorgada["revoked_at"] is None, otorgada
    assert otorgada["is_effective"] is True, otorgada

    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab = _cab(sesion.json()["access_token"])

    # ── permitir: el sujeto ve broiler y no breeder, con su propio token ──────
    lista = await _listado(http_client, cab)
    assert lote_broiler in lista, lista
    assert lote_breeder not in lista, f"un lote de una cadena no concedida apareció: {lista}"
    assert (await http_client.get(f"/api/v1/lots/{lote_broiler}",
                                  headers=cab)).status_code == 200
    ajeno = await http_client.get(f"/api/v1/lots/{lote_breeder}", headers=cab)
    assert ajeno.status_code == 404, (
        f"el detalle de un lote no concedido no devolvió 404 (anti-enumeración): "
        f"{ajeno.status_code} {ajeno.text[:300]}")
    me = await _me(http_client, cab)
    assert me["effective_business_units"] == ["broiler"], me
    assert me["granted_business_units"] == ["broiler"], me
    # ── revocar: el MISMO access token deja de ver la cadena ──────────────────
    revocar = await http_client.delete(f"/api/v1/users/{uid}/business-units/broiler",
                                       headers=admin)
    assert revocar.status_code == 200, (
        f"la revocación no devolvió la concesión: {revocar.status_code} "
        f"{revocar.text[:300]}")
    assert revocar.json()["revoked_at"] is not None, revocar.json()

    negado = await http_client.get(f"/api/v1/lots/{lote_broiler}", headers=cab)
    assert negado.status_code == 404, (
        f"el mismo token siguió viendo el lote tras revocar su unidad: {negado.status_code} "
        f"{negado.text[:300]}")
    lista = await _listado(http_client, cab)
    assert lote_broiler not in lista, f"el lote revocado siguió en el listado: {lista}"
    me = await _me(http_client, cab)
    assert me["effective_business_units"] == [], me
    assert me["granted_business_units"] == [], me

    # ── restaurar: la misma concesión nueva, sin tocar la sesión ──────────────
    reconceder = await http_client.post(f"/api/v1/users/{uid}/business-units", headers=admin,
                                        json={"code": "broiler"})
    assert reconceder.status_code == 201, reconceder.text
    assert reconceder.json()["revoked_at"] is None, reconceder.json()

    assert (await http_client.get(f"/api/v1/lots/{lote_broiler}",
                                  headers=cab)).status_code == 200, (
        "el mismo token no recuperó el lote al re-conceder la unidad")
    assert lote_broiler in await _listado(http_client, cab)
    me = await _me(http_client, cab)
    assert me["effective_business_units"] == ["broiler"], me
    # ── la historia: 2 filas de broiler, una revocada y exactamente una viva ──
    filas = await _concesiones(http_client, admin, uid)
    de_broiler = [f for f in filas if f["code"] == "broiler"]
    assert len(de_broiler) == 2, (
        f"revocar y re-conceder debía dejar 2 filas de broiler: {de_broiler}")
    vivas = [f for f in de_broiler if f["revoked_at"] is None]
    revocadas = [f for f in de_broiler if f["revoked_at"] is not None]
    assert len(vivas) == 1, f"el índice parcial único admite una sola viva: {de_broiler}"
    assert len(revocadas) == 1, de_broiler
    assert vivas[0]["is_effective"] is True, vivas[0]
    assert revocadas[0]["is_effective"] is False, revocadas[0]
    # orden (code, id): la revocada se escribió antes y por eso va primero
    assert de_broiler[0]["revoked_at"] is not None, (
        f"las concesiones no vienen ordenadas por (code, id): {de_broiler}")
    codigos = [f["code"] for f in filas]
    assert codigos == sorted(codigos), f"orden por código incumplido: {filas}"
async def test_bd_02_revocar_una_entre_varias_no_afecta_a_las_demas(http_client, escenario):
    """`AC-MX-03` · con dos unidades concedidas, revocar una deja la otra intacta — en el
    mismo token, tras refrescar y tras volver a entrar.

    Quien tiene incubadora y engorde y pierde engorde sigue trabajando en incubadora. Si la
    revocación se llevara por delante el resto —o si el token congelara la lista vieja—, el
    usuario quedaría sin acceso a lo que nadie le quitó.
    """
    admin = _token(escenario["admin"])
    lote_broiler = await _crear_lote(http_client, admin, "broiler")
    lote_breeder = await _crear_lote(http_client, admin, "breeder")

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=escenario["rol_lotes"],
                                       quien="bd02")
    assert alta.status_code == 201, alta.text
    uid = alta.json()["id"]

    for code in ("broiler", "breeder"):
        r = await http_client.post(f"/api/v1/users/{uid}/business-units", headers=admin,
                                   json={"code": code})
        assert r.status_code == 201, (code, r.status_code, r.text[:300])

    sesion = await _login(http_client, usuario)
    assert sesion.status_code == 200, sesion.text
    cab = _cab(sesion.json()["access_token"])

    me = await _me(http_client, cab)
    assert sorted(me["effective_business_units"]) == ["breeder", "broiler"], me
    assert (await http_client.get(f"/api/v1/lots/{lote_broiler}",
                                  headers=cab)).status_code == 200
    assert (await http_client.get(f"/api/v1/lots/{lote_breeder}",
                                  headers=cab)).status_code == 200
    # ── revocar SOLO broiler ─────────────────────────────────────────────────
    revocar = await http_client.delete(f"/api/v1/users/{uid}/business-units/broiler",
                                       headers=admin)
    assert revocar.status_code == 200, (
        f"la revocación no devolvió la concesión: {revocar.status_code} "
        f"{revocar.text[:300]}")

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
        me = await _me(http_client, cabeceras)
        assert me["effective_business_units"] == ["breeder"], (etiqueta, me)
        assert me["granted_business_units"] == ["breeder"], (etiqueta, me)
        assert (await http_client.get(f"/api/v1/lots/{lote_breeder}", headers=cabeceras)
                ).status_code == 200, (
            f"[{etiqueta}] se perdió el acceso a la unidad que nadie revocó")
        quitado = await http_client.get(f"/api/v1/lots/{lote_broiler}", headers=cabeceras)
        assert quitado.status_code == 404, (
            f"[{etiqueta}] el lote revocado siguió visible: {quitado.status_code} "
            f"{quitado.text[:300]}")
        lista = await _listado(http_client, cabeceras)
        assert lote_breeder in lista and lote_broiler not in lista, (etiqueta, lista)


async def test_bd_03_re_concesion_es_idempotente_y_sin_vivos_duplicados(
    http_client, escenario
):
    """`AC-MX-03` · conceder dos veces no crea una segunda fila viva, y revocar más volver
    a conceder deja **dos** filas con **una sola** viva.

    La idempotencia protege de dos errores a la vez: una pantalla que reintenta no puede
    inflar el historial con concesiones que no ocurrieron, y el índice parcial único
    —una viva por usuario y unidad— no puede quedar a merced de la carrera entre dos
    peticiones. La segunda fila, en cambio, **debe** existir cuando hubo revocación: la
    historia de «se le quitó» no se borra al devolvérselo.
    """
    admin = _token(escenario["admin"])

    alta, usuario = await _alta_sujeto(http_client, admin, role_id=escenario["rol_lotes"],
                                       quien="bd03")
    assert alta.status_code == 201, alta.text
    uid = alta.json()["id"]

    primera = await http_client.post(f"/api/v1/users/{uid}/business-units", headers=admin,
                                     json={"code": "broiler"})
    assert primera.status_code == 201, primera.text
    segunda = await http_client.post(f"/api/v1/users/{uid}/business-units", headers=admin,
                                     json={"code": "broiler"})
    assert segunda.status_code in (200, 201), (
        f"repetir la concesión no devolvió la existente: {segunda.status_code} "
        f"{segunda.text[:300]}")
    assert segunda.json()["revoked_at"] is None, segunda.json()
    assert segunda.json()["is_effective"] is True, segunda.json()

    filas = await _concesiones(http_client, admin, uid)
    de_broiler = [f for f in filas if f["code"] == "broiler"]
    assert len(de_broiler) == 1, (
        f"conceder dos veces creó una segunda fila viva: {de_broiler}")
    assert de_broiler[0]["revoked_at"] is None, de_broiler

    # ── revocar y volver a conceder: 2 filas, exactamente 1 viva ─────────────
    revocar = await http_client.delete(f"/api/v1/users/{uid}/business-units/broiler",
                                       headers=admin)
    assert revocar.status_code == 200, revocar.text
    otra_vez = await http_client.post(f"/api/v1/users/{uid}/business-units", headers=admin,
                                      json={"code": "broiler"})
    assert otra_vez.status_code == 201, otra_vez.text

    filas = await _concesiones(http_client, admin, uid)
    de_broiler = [f for f in filas if f["code"] == "broiler"]
    assert len(de_broiler) == 2, (
        f"revocar y re-conceder debía dejar 2 filas: {de_broiler}")
    vivas = [f for f in de_broiler if f["revoked_at"] is None]
    assert len(vivas) == 1, f"más de una fila viva para la misma unidad: {de_broiler}"
    assert vivas[0]["is_effective"] is True, vivas[0]

    # revocar sin concesión viva no inventa historia: 404 sobre la ya revocada
    de_mas = await http_client.delete(f"/api/v1/users/{uid}/business-units/breeder",
                                      headers=admin)
    assert de_mas.status_code == 404, (
        f"revocar una unidad sin concesión viva no devolvió 404: {de_mas.status_code} "
        f"{de_mas.text[:300]}")
