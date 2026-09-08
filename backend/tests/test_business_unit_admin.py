"""Administración del acceso por unidad — `GA-REM-040` fase 7 · `T-040-18` · `T-040-19`.

Lo que esta suite existe para sostener, y que ninguna prueba suelta demuestra:

```
AUTORIDAD ADMINISTRATIVA      ≠  ACCESO OPERATIVO A LA UNIDAD
HABILITAR A LA EMPRESA        ≠  CONCEDER A SUS USUARIOS
CONCEDER A UN USUARIO         ≠  HABILITAR A SU EMPRESA
SIN CONCESIÓN                 =  SIN DATO PRODUCTIVO
EL ADMINISTRADOR DE A         NUNCA ADMINISTRA B
```

La evidencia central de `OD-09.b` es un **par**, no una prueba: el mismo actor, con la misma
sesión, administra Incubadora y no puede leer un lote de Incubadora. Por separado ninguna de
las dos mitades prueba nada — «puede administrar» sería compatible con un permiso que lo abre
todo, y «no puede leer» sería compatible con un actor sin ninguna autoridad. Es la
simultaneidad lo que se mide, y por eso las dos usan el mismo `ADMIN` (`R-72`).
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "BUADM-"

#: Las cuatro acciones del plano de control. Se enumeran aquí y no se importan del router a
#: propósito: si alguien cambiara el módulo `RBAC` de las rutas, estas pruebas tienen que
#: romper en vez de seguirle la corriente.
ADMIN_TOTAL = [("business_units", "read"), ("business_units", "update"),
               ("business_units", "create"), ("business_units", "delete")]


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """El escenario.

    ```
    Empresa A    breeder ON · hatchery ON · broiler OFF (fila explícita)
                 grandparent SIN FILA — «nunca configurada» ≠ «apagada»
        ADMIN        business_units:* + lots:read   ·  CERO concesiones de unidad
        RARO         rol «Peón de patio» CON el permiso
        FALSOADMIN   rol «Administrador» SIN el permiso
        OPERARIO     lots:read · concesión breeder · sin autoridad administrativa
        SUJETO       objetivo de las concesiones, sin ninguna
        lote de INCUBADORA, que ADMIN nunca debe poder leer
    Empresa B    hatchery ON
        ADMIN_B      business_units:* en B
        SUJETO_B     usuario de B, que ADMIN nunca debe poder tocar
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Lot

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab: dict[tuple[int, str], CompanyBusinessUnit] = {}
        for empresa, estados in ((a, {"breeder": True, "hatchery": True, "broiler": False}),
                                 (b, {"hatchery": True})):
            for code, on in estados.items():
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id,
                                           is_enabled=on)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila

        def _rol(nombre, company_id):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_admin = _rol("Coordinacion", a.id)
        rol_raro = _rol("Peon de patio", a.id)
        rol_falso = _rol("Administrador", a.id)
        rol_op = _rol("Operario", a.id)
        rol_admin_b = _rol("CoordinacionB", b.id)
        await s.flush()

        for rol, permisos in (
            (rol_admin, ADMIN_TOTAL + [("lots", "read"), ("operations", "read")]),
            (rol_raro, ADMIN_TOTAL),
            # El nombre dice «Administrador» y los permisos no lo respaldan. `AC-F05`.
            (rol_falso, [("lots", "read")]),
            (rol_op, [("lots", "read"), ("operations", "read")]),
            (rol_admin_b, ADMIN_TOTAL),
        ):
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo,
                                 action=PermissionAction(accion), scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Adm",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        admin = _usuario(a.id, "ADMIN", rol_admin)
        raro = _usuario(a.id, "RARO", rol_raro)
        falso = _usuario(a.id, "FALSOADMIN", rol_falso)
        operario = _usuario(a.id, "OPERARIO", rol_op)
        sujeto = _usuario(a.id, "SUJETO", rol_op)
        admin_b = _usuario(b.id, "ADMINB", rol_admin_b)
        sujeto_b = _usuario(b.id, "SUJETOB", rol_admin_b)
        s.add_all([admin, raro, falso, operario, sujeto, admin_b, sujeto_b])
        await s.flush()

        # `OPERARIO` tiene Reproductora; `ADMIN` **no tiene ninguna**, y ahí está el par.
        await conceder_unidad(s, user=operario,
                              company_business_unit=hab[(a.id, "breeder")])

        lote_inc = Lot(company_id=a.id, lot_code=f"{PREFIJO}INC-{uuid.uuid4().hex[:6]}",
                       bird_type=BirdTypeEnum.HATCHERY, status="active")
        s.add(lote_inc)
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "b": b.id, "admin": admin.id, "raro": raro.id,
                 "falso": falso.id, "operario": operario.id, "sujeto": sujeto.id,
                 "admin_b": admin_b.id, "sujeto_b": sujeto_b.id,
                 "lote_inc": lote_inc.id,
                 "hab_a_breeder": hab[(a.id, "breeder")].id,
                 "hab_a_hatchery": hab[(a.id, "hatchery")].id,
                 "hab_b_hatchery": hab[(b.id, "hatchery")].id,
                 "url": test_database_url}

    yield datos

    async with motor.begin() as c:
        for sql in (
            "DELETE FROM audit_logs WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM user_business_units WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
        ):
            await c.execute(text(sql), {"p": f"{PREFIJO}%"})
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


# ── Utilidades que consultan la base directamente ─────────────────────────────

async def _sesion(esc):
    motor = create_async_engine(esc["url"])
    return motor, async_sessionmaker(motor, expire_on_commit=False)()


async def _efectivas(esc, user_id: int) -> list[str]:
    """El alcance operativo real, leído por el resolutor central y no por la API."""
    from app.business_units.service import unidades_efectivas_por_id

    motor, s = await _sesion(esc)
    try:
        async with s:
            return await unidades_efectivas_por_id(s, user_id=user_id,
                                                   company_id=esc["a"])
    finally:
        await motor.dispose()


async def _concesiones_en_base(esc, user_id: int, *, vivas=None) -> int:
    from app.business_units.models import UserBusinessUnit

    motor, s = await _sesion(esc)
    try:
        async with s:
            q = select(func.count()).select_from(UserBusinessUnit).where(
                UserBusinessUnit.user_id == user_id)
            if vivas is True:
                q = q.where(UserBusinessUnit.revoked_at.is_(None))
            elif vivas is False:
                q = q.where(UserBusinessUnit.revoked_at.is_not(None))
            return (await s.execute(q)).scalar_one()
    finally:
        await motor.dispose()


async def _habilitada(esc, company_id: int, code: str) -> bool | None:
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit

    motor, s = await _sesion(esc)
    try:
        async with s:
            fila = (await s.execute(
                select(CompanyBusinessUnit.is_enabled)
                .join(BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id)
                .where(CompanyBusinessUnit.company_id == company_id,
                       BusinessUnit.code == code))).scalar_one_or_none()
            return fila
    finally:
        await motor.dispose()


async def _auditoria(esc, *, entity_type: str, user_id: int | None = None) -> list[dict]:
    from app.audit.models import AuditLog

    motor, s = await _sesion(esc)
    try:
        async with s:
            q = select(AuditLog).where(AuditLog.entity_type == entity_type)
            if user_id is not None:
                q = q.where(AuditLog.user_id == user_id)
            filas = (await s.execute(q)).scalars().all()
            return [{"action": f.action, "company_id": f.company_id,
                     "previous_state": f.previous_state, "new_state": f.new_state,
                     "new_values": f.new_values, "user_id": f.user_id} for f in filas]
    finally:
        await motor.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  `A` · la empresa y sus unidades
# ══════════════════════════════════════════════════════════════════════════════

async def test_el_listado_muestra_el_catalogo_con_el_estado_de_la_empresa(http_client, esc):
    """`AC-A02`. Las cuatro siempre: hay que ver lo que se puede encender, no lo encendido."""
    r = await http_client.get("/api/v1/business-units", headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    estado = {u["code"]: u["is_enabled"] for u in r.json()}

    assert set(estado) == {"grandparent", "breeder", "hatchery", "broiler"}, estado
    assert estado["breeder"] is True and estado["hatchery"] is True
    assert estado["broiler"] is False, "apagada explícitamente"
    assert estado["grandparent"] is False, (
        "sin fila de configuración NO es acceso: la ausencia nunca se lee como permiso")


async def test_el_listado_no_deja_ver_la_configuracion_de_otra_empresa(http_client, esc):
    """`AC-A07`. La empresa `B` tiene Incubadora encendida y Reproductora apagada.

    Si el listado no estuviera acotado, `ADMIN` vería el estado del vecino mezclado con el
    suyo. Se comprueba comparando los dos listados: el de `B` es distinto del de `A`.
    """
    a = {u["code"]: u["is_enabled"]
         for u in (await http_client.get("/api/v1/business-units",
                                         headers=_token(esc["admin"]))).json()}
    b = {u["code"]: u["is_enabled"]
         for u in (await http_client.get("/api/v1/business-units",
                                         headers=_token(esc["admin_b"]))).json()}
    assert a["breeder"] is True and b["breeder"] is False
    assert a["broiler"] is False and b["broiler"] is False


async def test_habilitar_una_unidad_apagada_la_enciende(client, esc):
    """`AC-A03`. Engorde estaba apagada."""
    r = await client.patch("/api/v1/business-units/broiler/enable",
                           headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    assert r.json() == {"code": "broiler", "name_key": r.json()["name_key"],
                        "is_enabled": True}
    assert await _habilitada(esc, esc["a"], "broiler") is True


async def test_habilitar_no_concede_la_unidad_a_nadie(client, esc):
    """`§18`. El error clásico: encender la línea y repartirla sola.

    Es la mutación 2 de la fase. Si habilitar concediera, nadie decidiría nunca quién opera
    una cadena — habilitarla se la daría a toda la plantilla.
    """
    antes = await _concesiones_en_base(esc, esc["sujeto"])
    await client.patch("/api/v1/business-units/broiler/enable", headers=_token(esc["admin"]))

    assert await _concesiones_en_base(esc, esc["sujeto"]) == antes == 0
    assert await _efectivas(esc, esc["sujeto"]) == []
    assert "broiler" not in await _efectivas(esc, esc["operario"]), (
        "el operario tenía Reproductora y sigue teniendo solo Reproductora")


async def test_deshabilitar_apaga_la_unidad(client, esc):
    r = await client.patch("/api/v1/business-units/hatchery/disable",
                           headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    assert r.json()["is_enabled"] is False
    assert await _habilitada(esc, esc["a"], "hatchery") is False


async def test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve(client, esc):
    """`AC-A04` · `AC-A05` · `AC-A06`, y la razón de que `BU-D10` siga abierta.

    Deshabilitar apaga la **efectividad** sin destruir la concesión. Que el ciclo completo
    —apagar, comprobar que no es efectiva, encender, comprobar que vuelve— funcione sin
    volver a conceder es lo que demuestra que no se ha borrado nada, y por tanto que ninguna
    respuesta futura de `BU-D10` ha quedado cerrada por omisión.
    """
    assert await _efectivas(esc, esc["operario"]) == ["breeder"]
    vivas = await _concesiones_en_base(esc, esc["operario"], vivas=True)

    await client.patch("/api/v1/business-units/breeder/disable", headers=_token(esc["admin"]))
    assert await _efectivas(esc, esc["operario"]) == [], "deja de ser efectiva"
    assert await _concesiones_en_base(esc, esc["operario"], vivas=True) == vivas, (
        "y sigue escrita: deshabilitar no revoca")

    await client.patch("/api/v1/business-units/breeder/enable", headers=_token(esc["admin"]))
    assert await _efectivas(esc, esc["operario"]) == ["breeder"], (
        "`AC-A06`: vuelve sin volver a concederla")


async def test_habilitar_dos_veces_es_idempotente(client, esc):
    """`§41`. Y no crea una segunda fila: dos filas harían que «habilitada» dependiera de
    cuál se leyera."""
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit

    for _ in range(2):
        r = await client.patch("/api/v1/business-units/broiler/enable",
                               headers=_token(esc["admin"]))
        assert r.status_code == 200, r.text

    motor, s = await _sesion(esc)
    try:
        async with s:
            n = (await s.execute(
                select(func.count()).select_from(CompanyBusinessUnit)
                .join(BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id)
                .where(CompanyBusinessUnit.company_id == esc["a"],
                       BusinessUnit.code == "broiler"))).scalar_one()
    finally:
        await motor.dispose()
    assert n == 1


async def test_habilitar_una_unidad_inexistente_es_404(http_client, esc):
    r = await http_client.patch("/api/v1/business-units/pescado/enable",
                                headers=_token(esc["admin"]))
    assert r.status_code == 404, r.text


async def test_una_unidad_nunca_configurada_se_puede_habilitar(client, esc):
    """Progenitoras no tenía fila. Habilitarla la crea, en lugar de fallar por no existir."""
    assert await _habilitada(esc, esc["a"], "grandparent") is None
    r = await client.patch("/api/v1/business-units/grandparent/enable",
                           headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    assert await _habilitada(esc, esc["a"], "grandparent") is True


# ══════════════════════════════════════════════════════════════════════════════
#  `B` · el usuario y sus unidades
# ══════════════════════════════════════════════════════════════════════════════

async def test_conceder_una_unidad_habilitada(client, esc):
    """`AC-B01`. Y el resolutor central lo confirma: la API y la autoridad coinciden."""
    r = await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                          headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["code"] == "hatchery" and cuerpo["company_id"] == esc["a"]
    assert cuerpo["revoked_at"] is None and cuerpo["is_effective"] is True

    assert await _efectivas(esc, esc["sujeto"]) == ["hatchery"]


async def test_conceder_no_habilita_la_unidad_para_la_empresa(client, esc):
    """`§29`. Engorde está apagada: conceder no la enciende, la rechaza.

    Es la mutación 3. Contratar una línea es una decisión comercial, y no se toma de paso
    mientras se reparten accesos.
    """
    r = await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                          headers=_token(esc["admin"]), json={"code": "broiler"})
    assert r.status_code == 409, r.text
    assert await _habilitada(esc, esc["a"], "broiler") is False, "sigue apagada"
    assert await _concesiones_en_base(esc, esc["sujeto"]) == 0, "y no quedó escrita"


async def test_conceder_dos_veces_no_duplica(client, esc):
    """`§43`. El índice único parcial lo impediría en la base; la API no debe llegar allí."""
    for _ in range(2):
        r = await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                              headers=_token(esc["admin"]), json={"code": "hatchery"})
        assert r.status_code == 201, r.text
    assert await _concesiones_en_base(esc, esc["sujeto"], vivas=True) == 1


async def test_revocar_retira_el_acceso_de_inmediato_y_conserva_la_historia(client, esc):
    """`AC-B05` · `AC-B11`. Marca, no borra."""
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert await _efectivas(esc, esc["sujeto"]) == ["hatchery"]

    r = await client.delete(f"/api/v1/users/{esc['sujeto']}/business-units/hatchery",
                            headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    assert r.json()["revoked_at"] is not None
    assert r.json()["is_effective"] is False

    assert await _efectivas(esc, esc["sujeto"]) == []
    assert await _concesiones_en_base(esc, esc["sujeto"], vivas=False) == 1, (
        "la fila sigue ahí, fechada")


async def test_revocar_lo_ya_revocado_es_404_y_no_inventa_un_exito(client, esc):
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    await client.delete(f"/api/v1/users/{esc['sujeto']}/business-units/hatchery",
                        headers=_token(esc["admin"]))
    r = await client.delete(f"/api/v1/users/{esc['sujeto']}/business-units/hatchery",
                            headers=_token(esc["admin"]))
    assert r.status_code == 404, r.text


async def test_una_concesion_revocada_se_puede_volver_a_otorgar(client, esc):
    """El índice único es **parcial** justo para esto: revocar no puede ser irreversible."""
    for _ in range(2):
        assert (await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                                  headers=_token(esc["admin"]),
                                  json={"code": "hatchery"})).status_code == 201
        assert (await client.delete(
            f"/api/v1/users/{esc['sujeto']}/business-units/hatchery",
            headers=_token(esc["admin"]))).status_code == 200
    assert await _efectivas(esc, esc["sujeto"]) == []
    assert await _concesiones_en_base(esc, esc["sujeto"], vivas=False) == 2


async def test_el_listado_separa_otorgada_de_efectiva(client, esc):
    """`§65` · `AC-A05`. Una concesión viva sobre una unidad apagada **no** es efectiva.

    Una pantalla que solo dijera «tiene Incubadora» mentiría, y quien administra decidiría
    a ciegas.
    """
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    await client.patch("/api/v1/business-units/hatchery/disable",
                       headers=_token(esc["admin"]))

    r = await client.get(f"/api/v1/users/{esc['sujeto']}/business-units",
                         headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    fila = [c for c in r.json() if c["code"] == "hatchery"][0]
    assert fila["revoked_at"] is None, "otorgada: no se ha revocado"
    assert fila["is_effective"] is False, "y no efectiva: la empresa la tiene apagada"
    assert await _efectivas(esc, esc["sujeto"]) == [], "el resolutor dice lo mismo"


async def test_la_efectividad_del_listado_coincide_con_el_resolutor_central(client, esc):
    """Dos caminos, una sola política.

    El listado recompone la efectividad con las filas en la mano y el resolutor la consulta
    contra la base. Que coincidan no es redundante: si divergieran, la pantalla enseñaría un
    acceso que el backend deniega, o al revés — y una de las dos estaría concediendo de más.
    """
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "breeder"})
    await client.patch("/api/v1/business-units/breeder/disable", headers=_token(esc["admin"]))

    r = await client.get(f"/api/v1/users/{esc['sujeto']}/business-units",
                         headers=_token(esc["admin"]))
    segun_api = sorted(c["code"] for c in r.json() if c["is_effective"])
    assert segun_api == await _efectivas(esc, esc["sujeto"]) == ["hatchery"]


# ══════════════════════════════════════════════════════════════════════════════
#  `OD-09.b` · el par que separa administrar de acceder
# ══════════════════════════════════════════════════════════════════════════════

async def test_control_el_administrador_sin_la_unidad_puede_administrarla(client, esc):
    """CONTROL de `AC-F03`. `ADMIN` no tiene **ninguna** concesión de unidad.

    Sin esta mitad, la mitad siguiente pasaría con un actor que simplemente no puede nada.
    """
    assert await _efectivas(esc, esc["admin"]) == [], "el sujeto no tiene ninguna cadena"

    assert (await client.patch("/api/v1/business-units/broiler/enable",
                               headers=_token(esc["admin"]))).status_code == 200
    assert (await client.patch("/api/v1/business-units/broiler/disable",
                               headers=_token(esc["admin"]))).status_code == 200
    assert (await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                              headers=_token(esc["admin"]),
                              json={"code": "hatchery"})).status_code == 201
    assert (await client.delete(f"/api/v1/users/{esc['sujeto']}/business-units/hatchery",
                                headers=_token(esc["admin"]))).status_code == 200


async def test_tratamiento_ese_mismo_administrador_no_ve_dato_productivo(http_client, esc):
    """TRATAMIENTO de `AC-F04`. El mismo actor, la misma sesión, el dato de Incubadora.

    Administrar Incubadora para toda la empresa **no** le deja leer un lote de Incubadora.
    Es la propiedad entera de `OD-09.b` en dos líneas.
    """
    r = await http_client.get("/api/v1/lots?limit=100", headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    codigos = [l["lot_code"] for l in r.json()]
    assert not [c for c in codigos if c.startswith(f"{PREFIJO}INC")], codigos

    directo = await http_client.get(f"/api/v1/lots/{esc['lote_inc']}",
                                    headers=_token(esc["admin"]))
    assert directo.status_code == 404, (
        f"conocer el identificador tampoco abre el lote: {directo.status_code}")


async def test_administrar_no_cambia_el_alcance_operativo_del_administrador(client, esc):
    """`§9`. Después de administrarlo todo, `ADMIN` sigue con cero cadenas.

    Que no exista un `if admin: todas las unidades` no se demuestra leyendo el código: se
    demuestra ejerciendo la autoridad y comprobando que el alcance no se movió.
    """
    await client.patch("/api/v1/business-units/broiler/enable", headers=_token(esc["admin"]))
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert await _efectivas(esc, esc["admin"]) == []


# ══════════════════════════════════════════════════════════════════════════════
#  El inquilino
# ══════════════════════════════════════════════════════════════════════════════

async def test_no_se_concede_a_un_usuario_de_otra_empresa(http_client, esc):
    """`§44` · `AC-B10`. Y con `404`, que no distingue «no es tuyo» de «no existe»."""
    r = await http_client.post(f"/api/v1/users/{esc['sujeto_b']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 404, r.text
    assert await _concesiones_en_base(esc, esc["sujeto_b"]) == 0


async def test_no_se_listan_las_concesiones_de_un_usuario_de_otra_empresa(http_client, esc):
    r = await http_client.get(f"/api/v1/users/{esc['sujeto_b']}/business-units",
                              headers=_token(esc["admin"]))
    assert r.status_code == 404, r.text


async def test_habilitar_toca_la_fila_de_la_empresa_propia_y_no_la_del_vecino(client, esc):
    """`§45`. Las dos empresas tienen Incubadora: solo puede moverse una.

    La ruta direcciona por **código**, de modo que «la incubadora de la empresa vecina» no es
    expresable. Esta prueba comprueba lo que se sigue de ello: que el filtro por empresa del
    servicio elige la fila correcta y deja la otra intacta.
    """
    assert await _habilitada(esc, esc["b"], "hatchery") is True

    r = await client.patch("/api/v1/business-units/hatchery/disable",
                           headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text

    assert await _habilitada(esc, esc["a"], "hatchery") is False, "la propia, apagada"
    assert await _habilitada(esc, esc["b"], "hatchery") is True, (
        "la del vecino, intacta: administrar `A` nunca administra `B`")


async def test_el_administrador_no_puede_darse_acceso_a_otra_empresa(http_client, esc):
    """`§50`. No hay parámetro de empresa que manipular, y el cuerpo tampoco la acepta.

    Se envía igualmente para dejarlo probado: un campo de más se ignora, no amplía nada.
    """
    # El vehículo era una auto-concesión hasta `OD-15`. Se cambia el objetivo a otro usuario
    # de la misma empresa: lo que esta prueba mide es el **campo de empresa**, no quién
    # recibe, y con el objetivo antiguo mediría la regla de segregación por accidente.
    r = await http_client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                               headers=_token(esc["admin"]),
                               json={"code": "hatchery", "company_id": esc["b"]})
    assert r.status_code == 201, r.text
    assert r.json()["company_id"] == esc["a"], "la concesión es de su propia empresa"


async def test_el_denegado_no_deja_ni_escritura_ni_registro_de_exito(http_client, esc):
    """`§55` · `§91`. Un intento entre empresas: cero filas, cero auditoría de éxito."""
    antes = await _auditoria(esc, entity_type="user_business_unit")
    r = await http_client.post(f"/api/v1/users/{esc['sujeto_b']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 404

    assert await _concesiones_en_base(esc, esc["sujeto_b"]) == 0
    assert await _auditoria(esc, entity_type="user_business_unit") == antes


# ══════════════════════════════════════════════════════════════════════════════
#  La autoridad es el permiso, no el nombre
# ══════════════════════════════════════════════════════════════════════════════

async def test_llamarse_administrador_no_administra_nada(http_client, esc):
    """`AC-F05` · `§85`. El rol se llama «Administrador» y no tiene el permiso."""
    for metodo, url, cuerpo in (
        ("patch", "/api/v1/business-units/broiler/enable", None),
        ("patch", "/api/v1/business-units/hatchery/disable", None),
        ("get", "/api/v1/business-units", None),
        ("post", f"/api/v1/users/{esc['sujeto']}/business-units", {"code": "hatchery"}),
        ("delete", f"/api/v1/users/{esc['sujeto']}/business-units/breeder", None),
    ):
        kwargs = {"headers": _token(esc["falso"])}
        if cuerpo is not None:
            kwargs["json"] = cuerpo
        r = await getattr(http_client, metodo)(url, **kwargs)
        assert r.status_code == 403, f"{metodo} {url} → {r.status_code}"

    assert await _habilitada(esc, esc["a"], "broiler") is False
    assert await _concesiones_en_base(esc, esc["sujeto"]) == 0


async def test_un_rol_con_nombre_inesperado_y_el_permiso_si_administra(client, esc):
    """`§86`. «Peón de patio» con `business_units:*` administra.

    Es la contraparte imprescindible: sin ella, la prueba anterior pasaría también si las
    rutas estuvieran denegando a todo el mundo (`R-72`).
    """
    r = await client.patch("/api/v1/business-units/broiler/enable", headers=_token(esc["raro"]))
    assert r.status_code == 200, r.text
    assert await _habilitada(esc, esc["a"], "broiler") is True


async def test_un_usuario_operativo_no_concede_ni_a_otros_ni_a_si_mismo(http_client, esc):
    """`§48` · `§49`. `OPERARIO` opera Reproductora y no reparte accesos."""
    otro = await http_client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                                  headers=_token(esc["operario"]), json={"code": "hatchery"})
    assert otro.status_code == 403, otro.text

    propio = await http_client.post(f"/api/v1/users/{esc['operario']}/business-units",
                                    headers=_token(esc["operario"]),
                                    json={"code": "hatchery"})
    assert propio.status_code == 403, propio.text
    assert await _efectivas(esc, esc["operario"]) == ["breeder"], "sin cambios"


async def test_od15_quien_puede_conceder_no_puede_concederse(client, esc):
    """`OD-15.a` · **supersede la política que esta misma prueba documentaba**.

    Hasta `OD-15`, esta prueba afirmaba lo contrario: que `business_units:create` autorizaba a
    conceder a cualquier usuario de la empresa **incluido uno mismo**, y lo dejaba escrito
    como política vigente porque ninguna spec la separaba. Aquella lectura era correcta
    entonces — `§51` de la fase 7 pedía documentar lo que había y no inventar una excepción.

    El propietario la separó al resolver `R-128`. El permiso autoriza a **repartir**, no a
    **recibir**, y la negativa llega con todo lo demás correcto: permiso válido, empresa
    propia, unidad habilitada.

    El registro histórico de la política anterior vive en `OD-15 §1` y en
    `GA_REM_040_PHASE_7_EVIDENCE.md`; aquí no se borra, se supera.
    """
    assert await _efectivas(esc, esc["admin"]) == []

    r = await client.post(f"/api/v1/users/{esc['admin']}/business-units",
                          headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 403, r.text
    assert await _efectivas(esc, esc["admin"]) == [], "se concedió a sí mismo"

    # Y la contraparte, para que «no puede concederse» no se confunda con «no puede conceder».
    otro = await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                             headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert otro.status_code == 201, otro.text


# ══════════════════════════════════════════════════════════════════════════════
#  Cero concesiones · `OD-09.c`
# ══════════════════════════════════════════════════════════════════════════════

async def test_con_las_cuatro_habilitadas_y_cero_concesiones_el_alcance_es_vacio(client, esc):
    """`§95` · `AC-B04`. El `fail open` que esta capacidad existe para impedir."""
    for code in ("grandparent", "breeder", "hatchery", "broiler"):
        await client.patch(f"/api/v1/business-units/{code}/enable",
                           headers=_token(esc["admin"]))

    assert await _efectivas(esc, esc["sujeto"]) == [], (
        "habilitar a la empresa no es conceder: sin concesión, nada")


async def test_el_usuario_sin_unidades_conserva_lo_de_CORE(http_client, esc):
    """`AC-B03` · `BU-D09`. Entra, y `/me` le contesta. No es un `401`."""
    r = await http_client.get("/api/v1/me", headers=_token(esc["sujeto"]))
    assert r.status_code == 200, r.text
    assert await _efectivas(esc, esc["sujeto"]) == []


# ══════════════════════════════════════════════════════════════════════════════
#  Historia entre empresas · `AC-B08` · `AC-B12`
# ══════════════════════════════════════════════════════════════════════════════

async def test_una_concesion_de_la_empresa_anterior_no_se_lista_como_actual(client, esc):
    """`§92` · `§64`. El usuario se mueve de `A` a `B`; sus concesiones de `A` son historia.

    Administrarlo en `B` no debe mostrarlas. El filtro es sobre la habilitación, que ya lleva
    la empresa dentro — y sin él, una concesión de `A` aparecería junto a las de `B` y se
    leería como vigente.
    """
    from app.auth.models import User
    from app.business_units.service import revocar_concesiones

    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})

    motor, s = await _sesion(esc)
    try:
        async with s:
            u = (await s.execute(select(User).where(User.id == esc["sujeto"]))).scalar_one()
            await revocar_concesiones(s, user=u)   # lo que hace mover de empresa
            u.company_id = esc["b"]
            await s.commit()
    finally:
        await motor.dispose()

    r = await client.get(f"/api/v1/users/{esc['sujeto']}/business-units",
                         headers=_token(esc["admin_b"]))
    assert r.status_code == 200, r.text
    assert r.json() == [], "en `B` no tiene ninguna, y las de `A` no se asoman"


async def test_volver_a_la_empresa_anterior_no_reactiva_la_concesion(client, esc):
    """`AC-B12` · `OD-09.e` · `§93`. Vuelve a `A` y sigue sin acceso: hace falta otorgar de nuevo."""
    from app.auth.models import User
    from app.business_units.service import revocar_concesiones

    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert await _efectivas(esc, esc["sujeto"]) == ["hatchery"]

    motor, s = await _sesion(esc)
    try:
        async with s:
            u = (await s.execute(select(User).where(User.id == esc["sujeto"]))).scalar_one()
            await revocar_concesiones(s, user=u)
            u.company_id = esc["b"]
            await s.commit()
        async with async_sessionmaker(motor, expire_on_commit=False)() as s2:
            u = (await s2.execute(select(User).where(User.id == esc["sujeto"]))).scalar_one()
            u.company_id = esc["a"]        # vuelve
            await s2.commit()
    finally:
        await motor.dispose()

    assert await _efectivas(esc, esc["sujeto"]) == [], (
        "volver no prueba el mismo cargo ni la misma necesidad operativa")

    r = await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                          headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 201, r.text
    assert await _efectivas(esc, esc["sujeto"]) == ["hatchery"], "con una concesión nueva, sí"


# ══════════════════════════════════════════════════════════════════════════════
#  `P-09` · auditoría
# ══════════════════════════════════════════════════════════════════════════════

async def test_habilitar_y_deshabilitar_quedan_auditados(client, esc):
    """`AC-I03` · `§53`. Con actor, empresa, unidad y los dos estados."""
    await client.patch("/api/v1/business-units/broiler/enable", headers=_token(esc["admin"]))
    await client.patch("/api/v1/business-units/broiler/disable", headers=_token(esc["admin"]))

    registros = [x for x in await _auditoria(esc, entity_type="company_business_unit")
                 if x["user_id"] == esc["admin"]]
    assert len(registros) >= 2, registros
    encendido = [x for x in registros if x["new_state"] == "enabled"]
    apagado = [x for x in registros if x["new_state"] == "disabled"]
    assert encendido and apagado, registros
    assert encendido[0]["previous_state"] == "disabled"
    assert encendido[0]["company_id"] == esc["a"]
    assert encendido[0]["new_values"]["business_unit"] == "broiler"


async def test_conceder_y_revocar_quedan_auditados(client, esc):
    """`AC-I03` · `§54`. Y dicen **a quién**, que es lo que distingue este registro."""
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    await client.delete(f"/api/v1/users/{esc['sujeto']}/business-units/hatchery",
                        headers=_token(esc["admin"]))

    registros = [x for x in await _auditoria(esc, entity_type="user_business_unit")
                 if x["user_id"] == esc["admin"]]
    estados = {x["new_state"] for x in registros}
    assert {"granted", "revoked"} <= estados, registros
    for x in registros:
        assert x["new_values"]["target_user_id"] == esc["sujeto"]
        assert x["new_values"]["business_unit"] == "hatchery"
        assert x["company_id"] == esc["a"]


async def test_repetir_una_concesion_no_infla_la_auditoria(client, esc):
    """Un registro de cambio por un acto que no ocurrió sería ruido en `P-09`."""
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    tras_una = len(await _auditoria(esc, entity_type="user_business_unit"))
    await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                      headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert len(await _auditoria(esc, entity_type="user_business_unit")) == tras_una


# ══════════════════════════════════════════════════════════════════════════════
#  Contrato de respuesta · la lección de `R-112`
# ══════════════════════════════════════════════════════════════════════════════

async def test_las_rutas_nuevas_declaran_todas_su_contrato_de_respuesta(esc):
    """`§58`. `R-112` fue exactamente esto: la proyección existía y no se aplicaba.

    Se comprueba sobre la aplicación montada y no leyendo el fichero: lo que protege al
    cliente es el `response_model` que `FastAPI` tiene registrado, no el que esté escrito.
    """
    from app.authorization_coverage import enumerar_rutas, permiso_declarado
    from app.main import app

    rutas = [(camino, metodos, ruta) for camino, metodos, ruta in enumerar_rutas(app)
             if "business-units" in camino]
    assert len(rutas) == 6, [c for c, _, _ in rutas]

    sin_contrato = [f"{'/'.join(m)} {c}" for c, m, r in rutas
                    if getattr(r, "response_model", None) is None]
    assert sin_contrato == [], sin_contrato

    # Y la otra mitad del contrato: ninguna se sirve sin permiso declarado (`AC08`).
    sin_permiso = [f"{'/'.join(m)} {c}" for c, m, r in rutas
                   if permiso_declarado(r) is None]
    assert sin_permiso == [], sin_permiso


async def test_la_respuesta_no_arrastra_la_fila_del_orm(client, esc):
    """`§96` · `§61`. La proyección acota, y lo que no está declarado no viaja.

    Importa más aquí que en ningún otro sitio: estas entidades cuelgan de `users`, de modo
    que devolver la fila entera arrastraría credenciales y metadatos de sesión.
    """
    r = await client.post(f"/api/v1/users/{esc['sujeto']}/business-units",
                          headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 201, r.text
    assert set(r.json()) == {"user_id", "code", "company_id", "granted_at",
                             "revoked_at", "is_effective"}, r.json()

    lista = await client.get("/api/v1/business-units", headers=_token(esc["admin"]))
    for fila in lista.json():
        assert set(fila) == {"code", "name_key", "is_enabled"}, fila
        assert "id" not in fila, (
            "el identificador de la habilitación no se expone: no debe poder volver como "
            "entrada, que es por donde se colaría la de otro inquilino")


async def test_no_existe_una_puerta_generica_de_administracion(esc):
    """Lo que `OD-12` enseñó en la fase 5, aplicado aquí.

    No debe existir una función reutilizable que conceda unidades «porque el actor es
    administrador». Una excepción con nombre genérico la hereda cualquier ruta futura sin que
    nadie lo decida — y esta capacidad se sostiene sobre que administrar no conceda nada.
    """
    import ast
    from pathlib import Path

    # Se analiza el **árbol sintáctico** y no el texto del fichero: los comentarios y las
    # cadenas de documentación nombran estas cosas justamente para explicar que no se usan,
    # y una búsqueda literal confundiría la explicación con el defecto.
    arbol = ast.parse(Path("app/business_units/admin.py").read_text(encoding="utf-8"))
    usados = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
    usados |= {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
    usados |= {a.name for n in ast.walk(arbol)
               if isinstance(n, ast.ImportFrom) for a in n.names}

    for prohibido in ("is_super_admin", "role_name", "unidades_efectivas",
                      "unidades_habilitadas", "tiene_acceso"):
        assert prohibido not in usados, (
            f"`admin.py` usa {prohibido!r}: administrar no consulta ni amplía el "
            "alcance operativo de nadie")
