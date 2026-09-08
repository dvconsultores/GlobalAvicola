"""Clasificación pendiente — `GA-REM-040` fase 6 · `OD-10.c` · `T-040-16` · `T-040-17`.

    SIN CLASIFICAR  ≠  DE TODA LA EMPRESA
    SIN CLASIFICAR  ≠  UNA QUINTA CADENA
    SIN CLASIFICAR  ≠  BORRADO

El registro existe, conserva trazabilidad, y su acceso productivo queda cerrado hasta que
alguien autorizado diga a qué cadena pertenece. Lo ven quien lo registró y el control
autorizado — dos partes nombradas, no «todos».

Y una vez clasificado, **manda el alcance normal**: haber creado el registro no es un
salvoconducto permanente.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "BUPEND-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def pend(test_database_url):
    """Una inspección de granja **sin lote** —el caso permanente de `OD-10.c`— y sus actores.

    ```
    Empresa A   Reproductora ON · Incubadora ON
        evento SIN LOTE   registrado por CREADOR (solo Reproductora)
        evento CON LOTE   de reproductora, clasificable por derivación
        CREADOR    solo Reproductora · sin permiso de clasificar
        AJENO      solo Reproductora · no lo registró
        INCUB      solo Incubadora
        CLASIF     control autorizado · `masters:update`
    Empresa B   otro control autorizado, que nunca debe verlo
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Lot
    from app.operations.models import EventStatus, EventType, OperationalEvent

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, codes in ((a, ("breeder", "hatchery")), (b, ("breeder",))):
            for code in codes:
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id, is_enabled=True)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila

        lote_re = Lot(company_id=a.id, lot_code=f"{PREFIJO}RE-{uuid.uuid4().hex[:6]}",
                      bird_type=BirdTypeEnum.BREEDER, status="active")
        s.add(lote_re)
        await s.flush()

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_op = _rol("Op", a.id, None)
        rol_ctrl = _rol("Ctrl", a.id, None)
        rol_ctrl_b = _rol("CtrlB", b.id, None)
        await s.flush()
        for rol, permisos in ((rol_op, [("operations", PermissionAction.READ),
                                        ("operations", PermissionAction.CREATE)]),
                              (rol_ctrl, [("operations", PermissionAction.READ),
                                          ("masters", PermissionAction.UPDATE)]),
                              (rol_ctrl_b, [("operations", PermissionAction.READ),
                                            ("masters", PermissionAction.UPDATE)])):
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion,
                                 scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Pen",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        creador = _usuario(a.id, "CREADOR", rol_op)
        ajeno = _usuario(a.id, "AJENO", rol_op)
        incub = _usuario(a.id, "INCUB", rol_op)
        clasif = _usuario(a.id, "CLASIF", rol_ctrl)
        clasif_b = _usuario(b.id, "CLASIFB", rol_ctrl_b)
        s.add_all([creador, ajeno, incub, clasif, clasif_b])
        await s.flush()
        for u in (creador, ajeno, clasif):
            await conceder_unidad(s, user=u, company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=incub, company_business_unit=hab[(a.id, "hatchery")])

        # La inspección de granja: `lot_id` nulo por decisión de esquema desde `i9j0k1l2m3n4`.
        sin_lote = OperationalEvent(
            company_id=a.id, lot_id=None, event_type=EventType.FARM_INSPECTION,
            event_date=days_ago(4), status=EventStatus.REGISTERED,
            registered_by_id=creador.id)
        con_lote = OperationalEvent(
            company_id=a.id, lot_id=lote_re.id, event_type=EventType.FARM_INSPECTION,
            event_date=days_ago(4), status=EventStatus.REGISTERED,
            registered_by_id=creador.id)
        s.add_all([sin_lote, con_lote])
        await s.flush()
        await s.commit()

        datos = {"empresa_a": a.id, "empresa_b": b.id, "lote_re": lote_re.id,
                 "sin_lote": sin_lote.id, "con_lote": con_lote.id,
                 "creador": creador.id, "ajeno": ajeno.id, "incub": incub.id,
                 "clasif": clasif.id, "clasif_b": clasif_b.id,
                 "hab_breeder": hab[(a.id, "breeder")].id,
                 "hab_hatchery": hab[(a.id, "hatchery")].id,
                 "hab_b_breeder": hab[(b.id, "breeder")].id}

    yield datos

    async with motor.begin() as c:
        for sql in (
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM operational_events WHERE registered_by_id IN "
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


async def _pendientes(http_client, user_id):
    r = await http_client.get("/api/v1/operations/pending-classification",
                              headers=_token(user_id))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else cuerpo.get("items", [])
    return {f["id"] for f in filas}


# ── El registro entra en pendiente, no en ninguna cadena ─────────────────────

async def test_un_evento_sin_lote_queda_pendiente_y_no_en_una_cadena(pend, test_database_url):
    """`OD-10.c`. Y **no** se le inventa unidad desde quien lo registró.

    Adivinar la cadena por el creador sería la forma más silenciosa de equivocarse: el
    registro quedaría atribuido a una cadena que nadie decidió y con toda la apariencia de
    estar bien clasificado.
    """
    from app.business_units.classification import estado_de_clasificacion
    from app.operations.models import OperationalEvent

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            evento = await s.get(OperationalEvent, pend["sin_lote"])
            assert evento.business_unit_id is None
            assert await estado_de_clasificacion(s, evento) == "pending"

            con_lote = await s.get(OperationalEvent, pend["con_lote"])
            assert await estado_de_clasificacion(s, con_lote) == "derived"
    finally:
        await motor.dispose()


async def test_no_existe_una_quinta_unidad(test_database_url):
    """`§22`. `PENDING` es un estado, no una cadena productiva."""
    from app.business_units.models import BusinessUnit

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            codigos = set((await s.execute(select(BusinessUnit.code))).scalars().all())
    finally:
        await motor.dispose()
    assert codigos == {"grandparent", "breeder", "hatchery", "broiler"}


# ── Quién lo ve mientras está pendiente ─────────────────────────────────────

async def test_el_creador_ve_su_pendiente(http_client, pend):
    assert pend["sin_lote"] in await _pendientes(http_client, pend["creador"])


async def test_otro_usuario_de_la_misma_empresa_no_lo_ve(http_client, pend):
    """Misma empresa, misma cadena concedida, y aun así no: no lo registró él."""
    assert pend["sin_lote"] not in await _pendientes(http_client, pend["ajeno"])


async def test_un_usuario_de_otra_cadena_tampoco(http_client, pend):
    assert pend["sin_lote"] not in await _pendientes(http_client, pend["incub"])


async def test_el_control_autorizado_lo_ve(http_client, pend):
    assert pend["sin_lote"] in await _pendientes(http_client, pend["clasif"])


async def test_el_control_de_otra_empresa_no_lo_ve(http_client, pend):
    assert pend["sin_lote"] not in await _pendientes(http_client, pend["clasif_b"])


async def test_conocer_el_identificador_no_abre_el_pendiente(http_client, pend):
    """`§41`. El detalle operativo normal sigue denegando lo no clasificado."""
    r = await http_client.get(f"/api/v1/operations/{pend['sin_lote']}",
                              headers=_token(pend["ajeno"]))
    assert r.status_code == 404, r.text


async def test_el_pendiente_no_aparece_en_el_listado_operativo_normal(http_client, pend):
    """`§58`. La bandeja es una superficie aparte, no una excepción dentro de la normal."""
    r = await http_client.get("/api/v1/operations?limit=100",
                              headers=_token(pend["creador"]))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else cuerpo.get("items", [])
    assert pend["sin_lote"] not in {f["id"] for f in filas}


# ── Quién puede clasificar ───────────────────────────────────────────────────

async def test_el_creador_no_puede_clasificar_por_haberlo_creado(http_client, pend):
    """`§4`. Ver no es decidir: `CREATOR VISIBILITY ≠ CLASSIFICATION AUTHORITY`."""
    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["creador"]),
        json={"company_business_unit_id": pend["hab_breeder"]})
    assert r.status_code == 403, r.text


async def test_el_control_autorizado_clasifica(http_client, pend, client):
    r = await client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"company_business_unit_id": pend["hab_hatchery"]})
    assert r.status_code == 200, r.text


async def test_no_se_clasifica_con_la_habilitacion_de_otra_empresa(http_client, pend):
    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"company_business_unit_id": pend["hab_b_breeder"]})
    assert r.status_code in (400, 404), r.text


async def test_el_control_de_otra_empresa_no_clasifica(http_client, pend):
    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif_b"]),
        json={"company_business_unit_id": pend["hab_breeder"]})
    assert r.status_code in (400, 403, 404), r.text


# ── Clasificar no concede nada ───────────────────────────────────────────────

async def test_clasificar_no_concede_la_cadena_a_nadie(http_client, pend, test_database_url):
    """`§30`. Ni al creador, ni al que clasifica."""
    from app.auth.models import User
    from app.business_units.service import unidades_efectivas

    motor = create_async_engine(test_database_url)
    try:
        async def _efectivas(uid):
            async with async_sessionmaker(motor)() as s:
                u = (await s.execute(select(User).where(User.id == uid))).scalar_one()
                return await unidades_efectivas(s, u)

        antes = {uid: await _efectivas(uid) for uid in (pend["creador"], pend["clasif"])}
        r = await http_client.post(
            f"/api/v1/operations/{pend['sin_lote']}/classify",
            headers=_token(pend["clasif"]),
            json={"company_business_unit_id": pend["hab_hatchery"]})
        assert r.status_code == 200, r.text
        despues = {uid: await _efectivas(uid) for uid in (pend["creador"], pend["clasif"])}
    finally:
        await motor.dispose()
    assert antes == despues, f"{antes} → {despues}"


async def test_clasificar_no_habilita_ninguna_unidad(http_client, pend, test_database_url):
    """`§31`. La configuración comercial de la empresa no cambia por clasificar un registro."""
    from app.business_units.service import unidades_habilitadas

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            antes = await unidades_habilitadas(s, pend["empresa_a"])
        await http_client.post(
            f"/api/v1/operations/{pend['sin_lote']}/classify",
            headers=_token(pend["clasif"]),
            json={"company_business_unit_id": pend["hab_hatchery"]})
        async with async_sessionmaker(motor)() as s:
            despues = await unidades_habilitadas(s, pend["empresa_a"])
    finally:
        await motor.dispose()
    assert antes == despues


async def test_clasificar_deja_rastro_en_p09(http_client, pend, test_database_url):
    """`§32`. En `P-09`, con el mecanismo que ya existe, no en un registro paralelo."""
    from app.audit.models import AuditLog

    await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"company_business_unit_id": pend["hab_hatchery"]})

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            filas = (await s.execute(select(AuditLog).where(
                AuditLog.entity_type == "operational_event",
                AuditLog.entity_id == str(pend["sin_lote"])))).scalars().all()
    finally:
        await motor.dispose()
    assert filas, "la clasificación no dejó rastro"
    ultimo = filas[-1]
    assert ultimo.user_id == pend["clasif"]
    assert ultimo.company_id == pend["empresa_a"]
    assert ultimo.new_state


# ── Después de clasificar manda el alcance normal ────────────────────────────

async def test_tras_clasificar_el_creador_pierde_su_excepcion(http_client, pend):
    """`§7` y `§62`. Haber creado el registro **no** es un salvoconducto permanente.

    Se clasifica como incubadora, y el creador solo tiene reproductora: deja de verlo.
    """
    assert pend["sin_lote"] in await _pendientes(http_client, pend["creador"])
    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"company_business_unit_id": pend["hab_hatchery"]})
    assert r.status_code == 200, r.text

    assert pend["sin_lote"] not in await _pendientes(http_client, pend["creador"])
    detalle = await http_client.get(f"/api/v1/operations/{pend['sin_lote']}",
                                    headers=_token(pend["creador"]))
    assert detalle.status_code == 404, detalle.text


async def test_tras_clasificar_lo_ve_quien_tiene_esa_cadena(http_client, pend):
    """El control de la transición: si nadie lo viera después, clasificar no serviría."""
    await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"company_business_unit_id": pend["hab_hatchery"]})
    r = await http_client.get(f"/api/v1/operations/{pend['sin_lote']}",
                              headers=_token(pend["incub"]))
    assert r.status_code == 200, r.text


async def test_tras_clasificar_sigue_denegado_a_otra_cadena(http_client, pend):
    await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"company_business_unit_id": pend["hab_hatchery"]})
    r = await http_client.get(f"/api/v1/operations/{pend['sin_lote']}",
                              headers=_token(pend["ajeno"]))
    assert r.status_code == 404, r.text


async def test_ya_no_esta_pendiente_para_el_control(http_client, pend):
    await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"company_business_unit_id": pend["hab_hatchery"]})
    assert pend["sin_lote"] not in await _pendientes(http_client, pend["clasif"])


# ── El evento derivable no pasa por la bandeja ──────────────────────────────

async def test_el_evento_con_lote_no_necesita_clasificarse(http_client, pend):
    """`§11` y `§13`. Un campo nulable no implica pendiente: primero se deriva.

    El evento con lote de reproductora se ve por derivación, sin que nadie lo clasifique.
    """
    assert pend["con_lote"] not in await _pendientes(http_client, pend["clasif"])
    r = await http_client.get(f"/api/v1/operations/{pend['con_lote']}",
                              headers=_token(pend["creador"]))
    assert r.status_code == 200, r.text


async def test_el_evento_derivado_no_lo_ve_la_otra_cadena(http_client, pend):
    r = await http_client.get(f"/api/v1/operations/{pend['con_lote']}",
                              headers=_token(pend["incub"]))
    assert r.status_code == 404, r.text


async def test_el_nombre_del_rol_no_abre_la_bandeja(http_client, pend, test_database_url):
    """Sin `masters:update`, llamarse «Contralor» no basta."""
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import CompanyBusinessUnit
    from app.business_units.service import conceder_unidad

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            rol = Role(name=f"{PREFIJO}Contralor Avícola-{uuid.uuid4().hex[:6]}",
                       company_id=pend["empresa_a"], is_active=True)
            s.add(rol)
            await s.flush()
            s.add(Permission(role_id=rol.id, module="operations",
                             action=PermissionAction.READ, scope_type="company"))
            u = User(first_name="Con", last_name="Tra",
                     email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                     username=f"{PREFIJO}{uuid.uuid4().hex[:8]}",
                     hashed_password=hash_password("x"), company_id=pend["empresa_a"],
                     role_id=rol.id, is_active=True)
            s.add(u)
            await s.flush()
            hab = await s.get(CompanyBusinessUnit, pend["hab_breeder"])
            await conceder_unidad(s, user=u, company_business_unit=hab)
            await s.commit()
            uid = u.id
    finally:
        await motor.dispose()

    assert pend["sin_lote"] not in await _pendientes(http_client, uid)
