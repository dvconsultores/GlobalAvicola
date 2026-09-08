"""Segregación en la administración de acceso — `OD-15` · `R-128` · `R-113`.

```
ADMINISTRAR EL ACCESO  ≠  ELEVAR EL PROPIO
`business_units:create` autoriza a REPARTIR, no a RECIBIR
```

El sujeto es el **Administrador de Accesos** que `R-113` crea: cuatro permisos de
`business_units` y nada más. Sin comodín, sin `users:*`, sin ninguna cadena productiva
concedida. Es el actor cuya existencia mantuvo congelada esta figura durante tres tandas.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "ACCADM-"

#: Los cuatro permisos que `OD-15 §6` fija para la figura. Se enumeran aquí y se comparan
#: contra la siembra: si alguien añade un quinto, la prueba lo dice.
PERMISOS_DEL_ROL = {("business_units", "read"), ("business_units", "update"),
                    ("business_units", "create"), ("business_units", "delete")}


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """El escenario de la segregación.

    ```
    Empresa A   Incubadora HABILITADA · un lote de incubadora
        ADMIN     4 permisos de `business_units` + `lots:read` · CERO concesiones
        OTRO      segundo Administrador de Accesos — la vía de arranque de `OD-15.c`
        A2        usuario objetivo, sin concesiones
        SUPER_A   supervisor con acceso productivo y SIN permisos de administración
    Empresa B   Incubadora habilitada · un usuario
    SUPER       autoridad global
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
        hab = {}
        for empresa in (a, b):
            fila = CompanyBusinessUnit(company_id=empresa.id,
                                       business_unit_id=unidades["hatchery"].id,
                                       is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[empresa.id] = fila

        def _rol(nombre, company_id=None):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_acceso = _rol("AdminAccesos")
        rol_supervisor = _rol("Supervisor")
        rol_llano = _rol("Llano")
        rol_global = _rol("Global")
        await s.flush()

        for modulo, accion in PERMISOS_DEL_ROL:
            s.add(Permission(role_id=rol_acceso.id, module=modulo,
                             action=PermissionAction(accion), scope_type="company"))
        # `lots:read` para poder demostrar `OD-09.b`: sin él, el 404 del lote llegaría por
        # RBAC y no por ausencia de concesión, y la prueba no mediría nada.
        s.add(Permission(role_id=rol_acceso.id, module="lots",
                         action=PermissionAction.READ, scope_type="company"))
        # El supervisor tiene producción y **ningún** permiso de administración de acceso.
        for modulo in ("lots", "operations"):
            s.add(Permission(role_id=rol_supervisor.id, module=modulo,
                             action=PermissionAction.READ, scope_type="company"))
        s.add(Permission(role_id=rol_llano.id, module="lots",
                         action=PermissionAction.READ, scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Acc",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        admin = _usuario(a.id, "ADMIN", rol_acceso)
        otro = _usuario(a.id, "OTRO", rol_acceso)
        a2 = _usuario(a.id, "A2", rol_llano)
        supervisor = _usuario(a.id, "SUPERVISOR", rol_supervisor)
        user_b = _usuario(b.id, "USERB", rol_llano)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([admin, otro, a2, supervisor, user_b, superadmin])
        await s.flush()

        # El supervisor **sí** opera incubadora: su negativa debe venir de la falta de
        # permiso administrativo, no de no tener nada.
        await conceder_unidad(s, user=supervisor, company_business_unit=hab[a.id])

        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}INC-{uuid.uuid4().hex[:6]}",
                   bird_type=BirdTypeEnum.HATCHERY, status="active")
        s.add(lote)
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "b": b.id, "admin": admin.id, "otro": otro.id, "a2": a2.id,
                 "supervisor": supervisor.id, "user_b": user_b.id, "super": superadmin.id,
                 "lote": lote.id, "url": test_database_url}
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


async def _efectivas(esc, user_id: int, company_id: int | None = None) -> list[str]:
    from app.business_units.service import unidades_efectivas_por_id

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return await unidades_efectivas_por_id(
                s, user_id=user_id, company_id=company_id or esc["a"])
    finally:
        await motor.dispose()


async def _concesiones(esc, user_id: int) -> int:
    from app.business_units.models import UserBusinessUnit

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return (await s.execute(
                select(func.count()).select_from(UserBusinessUnit)
                .where(UserBusinessUnit.user_id == user_id))).scalar_one()
    finally:
        await motor.dispose()


async def _auditorias_de_concesion(esc) -> int:
    from app.audit.models import AuditLog

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return (await s.execute(
                select(func.count()).select_from(AuditLog)
                .where(AuditLog.entity_type == "user_business_unit"))).scalar_one()
    finally:
        await motor.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-S01`…`AC-S05` · la segregación
# ══════════════════════════════════════════════════════════════════════════════

async def test_s02_el_administrador_concede_a_otro_usuario_de_su_empresa(client, esc):
    """CONTROL. Sin esta, «no puede concederse» sería compatible con «no puede conceder»."""
    r = await client.post(f"/api/v1/users/{esc['a2']}/business-units",
                          headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 201, r.text
    assert await _efectivas(esc, esc["a2"]) == ["hatchery"]


async def test_s01_el_administrador_no_se_concede_a_si_mismo(http_client, esc):
    """`OD-15.a`. El permiso autoriza a repartir, no a recibir.

    Todo lo demás está bien: tiene `business_units:create`, la empresa es la suya, la unidad
    está habilitada. La única razón de la negativa es que el objetivo es él.
    """
    r = await http_client.post(f"/api/v1/users/{esc['admin']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 403, f"{r.status_code}: {r.text[:200]}"


async def test_s03_la_auto_concesion_denegada_no_deja_rastro(http_client, esc):
    """`AC-S03`. Ni fila, ni alcance, ni auditoría de éxito."""
    antes_filas = await _concesiones(esc, esc["admin"])
    antes_audit = await _auditorias_de_concesion(esc)

    r = await http_client.post(f"/api/v1/users/{esc['admin']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 403, r.text

    assert await _concesiones(esc, esc["admin"]) == antes_filas == 0
    assert await _efectivas(esc, esc["admin"]) == []
    assert await _auditorias_de_concesion(esc) == antes_audit


async def test_s04_no_hay_excepcion_por_ser_el_unico_administrador(http_client, esc):
    """`OD-15.c`. La regla no cede aunque el actor se quede solo.

    Se retira al segundo administrador dejando a `ADMIN` como único de su empresa. Si
    existiera una excepción de arranque, aquí se activaría.
    """
    from app.auth.models import User

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            u = (await s.execute(select(User).where(User.id == esc["otro"]))).scalar_one()
            u.is_active = False
            await s.commit()
    finally:
        await motor.dispose()

    r = await http_client.post(f"/api/v1/users/{esc['admin']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 403, "apareció una excepción por quedarse solo"
    assert await _efectivas(esc, esc["admin"]) == []


async def test_s04_otro_administrador_si_puede_concederle(client, esc):
    """`OD-15.c`, primera vía de arranque. La regla no crea un callejón sin salida."""
    r = await client.post(f"/api/v1/users/{esc['admin']}/business-units",
                          headers=_token(esc["otro"]), json={"code": "hatchery"})
    assert r.status_code == 201, r.text
    assert await _efectivas(esc, esc["admin"]) == ["hatchery"]


async def test_s05_el_super_administrador_situado_puede_concederle(client, esc):
    """`OD-15.c`, segunda vía. `OD-14`: situado en la empresa, opera en ella."""
    r = await client.post(f"/api/v1/users/{esc['admin']}/business-units",
                          headers=_token(esc["super"], company_id=esc["a"]),
                          json={"code": "hatchery"})
    assert r.status_code == 201, r.text
    assert r.json()["company_id"] == esc["a"]
    assert await _efectivas(esc, esc["admin"]) == ["hatchery"]


async def test_el_super_administrador_situado_en_a_no_toca_la_empresa_b(http_client, esc):
    """`OD-14` sigue mandando: el contexto acota también a la autoridad global."""
    r = await http_client.post(f"/api/v1/users/{esc['user_b']}/business-units",
                               headers=_token(esc["super"], company_id=esc["a"]),
                               json={"code": "hatchery"})
    assert r.status_code == 404, r.text
    assert await _concesiones(esc, esc["user_b"]) == 0


async def test_el_super_administrador_sin_contexto_no_administra(http_client, esc):
    """`OD-14.d`. Sin empresa elegida no se opera sobre ningún inquilino."""
    r = await http_client.post(f"/api/v1/users/{esc['a2']}/business-units",
                               headers=_token(esc["super"]), json={"code": "hatchery"})
    assert r.status_code == 403, r.text


async def test_el_administrador_no_concede_a_un_usuario_de_otra_empresa(http_client, esc):
    r = await http_client.post(f"/api/v1/users/{esc['user_b']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 404, r.text
    assert await _concesiones(esc, esc["user_b"]) == 0


async def test_la_auto_revocacion_no_entra_en_od15(client, esc):
    """`OD-15.b`. Revocarse **reduce** privilegio: la política vigente no se toca.

    Se le concede primero por la vía legítima, y después se quita a sí mismo. Si algún día se
    decide restringirlo, será un hallazgo nuevo y no una extensión silenciosa de éste.
    """
    await client.post(f"/api/v1/users/{esc['admin']}/business-units",
                      headers=_token(esc["otro"]), json={"code": "hatchery"})
    assert await _efectivas(esc, esc["admin"]) == ["hatchery"]

    r = await client.delete(f"/api/v1/users/{esc['admin']}/business-units/hatchery",
                            headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    assert await _efectivas(esc, esc["admin"]) == []


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-S06`…`AC-S09` · la figura
# ══════════════════════════════════════════════════════════════════════════════

def test_s06_el_rol_sembrado_tiene_exactamente_los_cuatro_permisos():
    """`AC-S06` · `AC-S09`. Contra la **siembra**, no contra la base de pruebas.

    Se comprueba el conjunto **exacto**: un quinto permiso lo rompe. Un `>=` habría dejado
    pasar precisamente el error que esta figura existe para no cometer.
    """
    import pathlib
    import re

    texto = pathlib.Path(__file__).resolve().parents[1].joinpath(
        "seeds", "baseline_seeds.py").read_text(encoding="utf-8")
    bloque = re.search(
        r'PERMISOS_ADMINISTRADOR_DE_ACCESOS\s*=\s*\[(.*?)\]', texto, re.S)
    assert bloque, "no existe la definición del rol en `baseline_seeds.py`"
    pares = set(re.findall(r'\("(\w+)",\s*PermissionAction\.(\w+)\)', bloque.group(1)))
    pares = {(m, a.lower()) for m, a in pares}

    assert pares == PERMISOS_DEL_ROL, f"el conjunto de permisos cambió: {pares}"
    assert not [p for p in pares if p[0] == "*"], "el rol recibió autoridad comodín"
    assert not [p for p in pares if p[0] == "users"], "el rol recibió `users:*`"


def test_s07_el_supervisor_no_recibe_permisos_de_administracion_de_acceso():
    """`AC-S07`. `Supervisor Avícola` supervisa producción."""
    import pathlib
    import re

    texto = pathlib.Path(__file__).resolve().parents[1].joinpath(
        "seeds", "dev_seeds.py").read_text(encoding="utf-8")
    bloque = re.search(r'"name": "Supervisor Avícola".*?\],', texto, re.S)
    assert bloque, "no se encuentra el rol Supervisor Avícola en las semillas"
    assert "business_units" not in bloque.group(0), (
        "`Supervisor Avícola` recibió permisos de administración de acceso")


async def test_s07_el_supervisor_no_administra_aunque_opere_la_cadena(http_client, esc):
    """`AC-S07` en ejecución, no solo en la semilla.

    El supervisor **sí** tiene Incubadora concedida: su negativa viene de no tener autoridad
    administrativa, no de no tener nada. Esa es la diferencia que la prueba mide.
    """
    assert await _efectivas(esc, esc["supervisor"]) == ["hatchery"]

    for metodo, url, cuerpo in (
        ("get", "/api/v1/business-units", None),
        ("patch", "/api/v1/business-units/hatchery/disable", None),
        ("post", f"/api/v1/users/{esc['a2']}/business-units", {"code": "hatchery"}),
        ("post", f"/api/v1/users/{esc['supervisor']}/business-units", {"code": "hatchery"}),
    ):
        kwargs = {"headers": _token(esc["supervisor"])}
        if cuerpo is not None:
            kwargs["json"] = cuerpo
        r = await getattr(http_client, metodo)(url, **kwargs)
        assert r.status_code == 403, f"{metodo} {url} → {r.status_code}"


async def test_s08_tener_el_rol_no_concede_ninguna_unidad(esc):
    """`AC-S08` · `OD-15.d`. El rol es autoridad, no acceso."""
    assert await _concesiones(esc, esc["admin"]) == 0
    assert await _efectivas(esc, esc["admin"]) == [], (
        "el rol de administración trajo acceso productivo consigo")


# ══════════════════════════════════════════════════════════════════════════════
#  `OD-09.b` · administrar no es acceder · el par completo
# ══════════════════════════════════════════════════════════════════════════════

async def test_od09b_control_administra_la_cadena_que_no_puede_operar(client, esc):
    """CONTROL. Sin concesión de Incubadora, administra Incubadora."""
    assert await _efectivas(esc, esc["admin"]) == []

    listado = await client.get("/api/v1/business-units", headers=_token(esc["admin"]))
    assert listado.status_code == 200, listado.text

    apagar = await client.patch("/api/v1/business-units/hatchery/disable",
                                headers=_token(esc["admin"]))
    assert apagar.status_code == 200, apagar.text
    encender = await client.patch("/api/v1/business-units/hatchery/enable",
                                  headers=_token(esc["admin"]))
    assert encender.status_code == 200, encender.text

    conceder = await client.post(f"/api/v1/users/{esc['a2']}/business-units",
                                 headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert conceder.status_code == 201, conceder.text
    revocar = await client.delete(f"/api/v1/users/{esc['a2']}/business-units/hatchery",
                                  headers=_token(esc["admin"]))
    assert revocar.status_code == 200, revocar.text


async def test_od09b_tratamiento_ese_mismo_actor_no_abre_el_lote(http_client, esc):
    """TRATAMIENTO. El mismo actor, la misma sesión, un lote de la cadena que administra.

    Tiene `lots:read`, así que el `404` no puede venir de `RBAC`: viene de no tener la cadena
    concedida. Es `OD-09.b` entero, y con `OD-15` encima: ni siquiera puede concedérsela.
    """
    r = await http_client.get(f"/api/v1/lots/{esc['lote']}", headers=_token(esc["admin"]))
    assert r.status_code == 404, f"{r.status_code}: {r.text[:200]}"

    listado = await http_client.get("/api/v1/lots?limit=100", headers=_token(esc["admin"]))
    assert listado.status_code == 200, listado.text
    assert not [l for l in listado.json() if l["lot_code"].startswith(f"{PREFIJO}INC")]
