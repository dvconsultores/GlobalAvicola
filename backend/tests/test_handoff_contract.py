"""Contrato de traspaso entre unidades — `GA-REM-040` fase 5 · `OD-10.a` · `OD-10.b`.

    VISIBILIDAD DE TRASPASO   ≠   ACCESO A LA UNIDAD AJENA

Participar en un traspaso da lo que el traspaso necesita —identificar, despachar, recibir,
confirmar, auditar y trazar— y nada más. No da el objeto completo del otro lado, ni sus
internos, ni sus agregados, ni la concesión de su cadena.

    A  propio            B  contrato de traspaso
    C  interno ajeno     D  agregado
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.security import create_access_token
from tests.time_reference import iso_days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "BUHAND-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def flujo(test_database_url):
    """Reproductora despacha huevo a **una** incubadora concreta, y hay otra que no participa.

    ```
    Empresa A   Reproductora · Incubadora · Engorde
        lote RE      breeder     el origen
        lote INC_A   hatchery    el destino elegido
        lote INC_B   hatchery    otra incubadora, que NO participa
        lote ENG     broiler     destino inválido para huevo fértil
        usuario RE   solo Reproductora
        usuario IA   solo Incubadora
    Empresa B   Reproductora · lote ajeno
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
        for empresa, codes in ((a, ("breeder", "hatchery", "broiler")), (b, ("breeder",))):
            for code in codes:
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id, is_enabled=True)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila

        def _lote(company_id, marca, tipo):
            return Lot(company_id=company_id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status="active")

        re_lote = _lote(a.id, "RE", BirdTypeEnum.BREEDER)
        inc_a = _lote(a.id, "INCA", BirdTypeEnum.HATCHERY)
        inc_b = _lote(a.id, "INCB", BirdTypeEnum.HATCHERY)
        eng = _lote(a.id, "ENG", BirdTypeEnum.BROILER)
        ajeno = _lote(b.id, "AJENO", BirdTypeEnum.HATCHERY)
        s.add_all([re_lote, inc_a, inc_b, eng, ajeno])
        await s.flush()

        rol = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        for accion in (PermissionAction.READ, PermissionAction.CREATE):
            s.add(Permission(role_id=rol.id, module="lots", action=accion,
                             scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca):
            return User(first_name=marca, last_name="Han",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        u_re, u_ia = _usuario(a.id, "RE"), _usuario(a.id, "IA")
        s.add_all([u_re, u_ia])
        await s.flush()
        await conceder_unidad(s, user=u_re, company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=u_ia, company_business_unit=hab[(a.id, "hatchery")])
        await s.commit()

        datos = {"empresa_a": a.id, "lote_re": re_lote.id, "lote_inc_a": inc_a.id,
                 "lote_inc_b": inc_b.id, "lote_eng": eng.id, "lote_ajeno": ajeno.id,
                 "user_re": u_re.id, "user_ia": u_ia.id}

    yield datos

    async with motor.begin() as c:
        for sql in (
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM egg_batches WHERE source_lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p) OR hatchery_lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM chick_batches WHERE hatchery_lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p)",
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


def _despacho(flujo, destino=None, origen=None, **extra):
    cuerpo = {"source_lot_id": origen or flujo["lote_re"],
              "quantity_dispatched": 40000, "dispatch_date": iso_days_ago(3),
              "generation": "breeder"}
    if destino is not None:
        cuerpo["hatchery_lot_id"] = destino
    cuerpo.update(extra)
    return cuerpo


# ── `OD-10.b` · el destino se declara al crear ───────────────────────────────

async def test_od10b_un_despacho_sin_destino_se_rechaza(http_client, flujo):
    """Sin destino, la incubadora no puede saber que un despacho es para ella antes de
    recibirlo, y la alternativa —enseñarle todos los pendientes de la empresa— anularía el
    aislamiento justo donde se quería proteger."""
    r = await http_client.post("/api/v1/lots/egg-batches",
                               headers=_token(flujo["user_re"]),
                               json=_despacho(flujo, destino=None))
    assert r.status_code == 422, r.text


async def test_od10b_con_destino_declarado_se_crea(http_client, flujo):
    """`CONTROL`. Si nada pudiera crearse, la prueba anterior no demostraría nada."""
    r = await http_client.post("/api/v1/lots/egg-batches",
                               headers=_token(flujo["user_re"]),
                               json=_despacho(flujo, destino=flujo["lote_inc_a"]))
    assert r.status_code == 201, r.text
    assert r.json()["hatchery_lot_id"] == flujo["lote_inc_a"]


# ── El origen tiene que ser del despachante ──────────────────────────────────

async def test_no_se_despacha_desde_un_lote_de_otra_cadena(http_client, flujo):
    """Despachar es una operación **sobre el lote origen**: exige tenerlo al alcance.

    Sin esta comprobación, el usuario de reproductora podía crear un traspaso saliendo de un
    lote de incubadora — operar sobre la cadena ajena por la puerta del contrato.
    """
    r = await http_client.post("/api/v1/lots/egg-batches",
                               headers=_token(flujo["user_re"]),
                               json=_despacho(flujo, destino=flujo["lote_inc_a"],
                                              origen=flujo["lote_inc_b"]))
    assert r.status_code in (403, 404), r.text


async def test_el_destino_no_exige_tener_su_cadena(http_client, flujo):
    """Y esto es lo que hace que sea un **contrato** y no un permiso.

    Quien despacha no tiene incubadora concedida y aun así puede dirigirle el traspaso: para
    eso existe el contrato. Lo que no obtiene es acceso a la cadena de destino.
    """
    r = await http_client.post("/api/v1/lots/egg-batches",
                               headers=_token(flujo["user_re"]),
                               json=_despacho(flujo, destino=flujo["lote_inc_a"]))
    assert r.status_code == 201, r.text


# ── El destino tiene que ser válido para el flujo ────────────────────────────

async def test_el_huevo_fertil_no_se_despacha_a_un_lote_de_engorde(http_client, flujo):
    """El flujo 2 va de Reproductora a Incubadora. Un lote de engorde no es destino válido,
    y aceptarlo escribiría una cadena que `P-10` no puede reconstruir."""
    r = await http_client.post("/api/v1/lots/egg-batches",
                               headers=_token(flujo["user_re"]),
                               json=_despacho(flujo, destino=flujo["lote_eng"]))
    assert r.status_code in (400, 422), r.text


async def test_no_se_despacha_a_otra_empresa(http_client, flujo):
    r = await http_client.post("/api/v1/lots/egg-batches",
                               headers=_token(flujo["user_re"]),
                               json=_despacho(flujo, destino=flujo["lote_ajeno"]))
    assert r.status_code in (400, 403, 404, 422), r.text


# ── La proyección · lo que cruza y lo que no ─────────────────────────────────

async def test_la_proyeccion_no_lleva_datos_internos_del_otro_lado(http_client, flujo):
    """Categoría `C`. `notes` es una anotación interna y no forma parte del contrato.

    Se comprueba sobre la respuesta real, no sobre la intención: devolver la entidad entera
    y confiar en que el frontend use tres campos no es una proyección.
    """
    creado = await http_client.post(
        "/api/v1/lots/egg-batches", headers=_token(flujo["user_re"]),
        json=_despacho(flujo, destino=flujo["lote_inc_a"], notes="interno de reproductora"))
    assert creado.status_code == 201, creado.text
    assert "notes" not in creado.json(), (
        f"la anotación interna cruzó el contrato: {creado.json()}")

    traza = await http_client.get(f"/api/v1/lots/{flujo['lote_inc_a']}/traceability",
                                  headers=_token(flujo["user_ia"]))
    assert traza.status_code == 200, traza.text
    assert "interno de reproductora" not in traza.text


async def test_el_destino_ve_el_traspaso_dirigido_a_el(http_client, flujo):
    """Categoría `B`. Identidad, cantidad y fecha: lo que hace falta para recibir."""
    await http_client.post("/api/v1/lots/egg-batches", headers=_token(flujo["user_re"]),
                           json=_despacho(flujo, destino=flujo["lote_inc_a"]))
    r = await http_client.get(f"/api/v1/lots/{flujo['lote_inc_a']}/traceability",
                              headers=_token(flujo["user_ia"]))
    assert r.status_code == 200, r.text
    recibidos = r.json()["egg_batches_received"]
    assert len(recibidos) == 1
    assert recibidos[0]["quantity_dispatched"] == 40000


async def test_la_otra_incubadora_no_ve_el_traspaso(http_client, flujo):
    """`§24`. Dirigido a una incubadora concreta, no a «las incubadoras»."""
    await http_client.post("/api/v1/lots/egg-batches", headers=_token(flujo["user_re"]),
                           json=_despacho(flujo, destino=flujo["lote_inc_a"]))
    r = await http_client.get(f"/api/v1/lots/{flujo['lote_inc_b']}/traceability",
                              headers=_token(flujo["user_ia"]))
    assert r.status_code == 200, r.text
    assert r.json()["egg_batches_received"] == []


async def test_conocer_el_lote_del_otro_lado_no_abre_su_detalle(http_client, flujo):
    """`§43`. El identificador ajeno puede ser `B` para trazar, y **no** es una llave.

    La cadena completa: se crea el traspaso, el destino lee su traza, obtiene el
    identificador del lote de reproductora, y al pedir su detalle la fase 3 sigue negándolo.
    """
    await http_client.post("/api/v1/lots/egg-batches", headers=_token(flujo["user_re"]),
                           json=_despacho(flujo, destino=flujo["lote_inc_a"]))
    traza = await http_client.get(f"/api/v1/lots/{flujo['lote_inc_a']}/traceability",
                                  headers=_token(flujo["user_ia"]))
    origen = traza.json()["egg_batches_received"][0]["source_lot_id"]
    assert origen == flujo["lote_re"]

    detalle = await http_client.get(f"/api/v1/lots/{origen}",
                                    headers=_token(flujo["user_ia"]))
    assert detalle.status_code == 404, detalle.text


# ── El traspaso no concede cadena ────────────────────────────────────────────

async def test_participar_en_un_traspaso_no_concede_la_cadena_ajena(
        http_client, flujo, test_database_url):
    """`§36` y `§37`. Se mide el conjunto efectivo antes y después."""
    from app.auth.models import User
    from app.business_units.service import unidades_efectivas

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            u = (await s.execute(
                select(User).where(User.id == flujo["user_re"]))).scalar_one()
            antes = await unidades_efectivas(s, u)

        await http_client.post("/api/v1/lots/egg-batches", headers=_token(flujo["user_re"]),
                               json=_despacho(flujo, destino=flujo["lote_inc_a"]))

        async with async_sessionmaker(motor)() as s:
            u = (await s.execute(
                select(User).where(User.id == flujo["user_re"]))).scalar_one()
            despues = await unidades_efectivas(s, u)
    finally:
        await motor.dispose()

    assert antes == despues == ["breeder"], f"{antes} → {despues}"


async def test_el_destino_tampoco_gana_la_cadena_del_origen(
        http_client, flujo, test_database_url):
    from app.auth.models import User
    from app.business_units.service import unidades_efectivas

    await http_client.post("/api/v1/lots/egg-batches", headers=_token(flujo["user_re"]),
                           json=_despacho(flujo, destino=flujo["lote_inc_a"]))
    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            u = (await s.execute(
                select(User).where(User.id == flujo["user_ia"]))).scalar_one()
            assert await unidades_efectivas(s, u) == ["hatchery"]
    finally:
        await motor.dispose()


async def test_el_nombre_del_rol_no_abre_el_traspaso_ajeno(http_client, flujo):
    """Ni siquiera para leer la traza de un lote que no se alcanza."""
    r = await http_client.get(f"/api/v1/lots/{flujo['lote_inc_a']}/traceability",
                              headers=_token(flujo["user_re"]))
    assert r.status_code == 404, r.text
