"""Fundamento del acceso por unidad de negocio — `GA-REM-040` fase 1.

Cubre `AC-A01`…`AC-A07` y `AC-B01`…`AC-B06`, y solo eso: la fase 1 construye catálogo,
habilitación, concesión y resolutor. No hay guardas de ruta, ni filtro por fila, ni API de
administración; esas son fases posteriores y estos tests no las suponen.

La distinción que estos tests existen para proteger:

    MISMA EMPRESA          no implica    MISMO ACCESO A UNIDAD
    SIN CONCESIÓN          no implica    TODAS LAS UNIDADES
    ROL LLAMADO «ADMIN»    no implica    ATRAVESAR NADA

Se prueban contra el servicio y el modelo, no por HTTP, porque en esta fase no existe ningún
endpoint nuevo: inventar uno para poder probar sería adelantar la fase 7.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401

PREFIJO = "BU-TEST-"


@pytest_asyncio.fixture
async def sesion_bu(test_database_url):
    """Sesión propia con limpieza por SQL.

    Por SQL y no por ORM porque esta suite se escribió **antes** de que las tablas
    existieran, y un error de importación al recolectar no es un rojo que demuestre nada.
    """
    motor = create_async_engine(test_database_url)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        yield s

    from app.auth.models import Role, User
    from app.masters.models import Company

    async with motor.begin() as c:
        for tabla, columna in (("user_business_units", "user_id"),):
            existe = (await c.execute(
                text(f"SELECT to_regclass('public.{tabla}')"))).scalar()
            if existe:
                await c.execute(text(
                    f"DELETE FROM {tabla} WHERE {columna} IN "
                    "(SELECT id FROM users WHERE username LIKE :p)"), {"p": f"{PREFIJO}%"})
        existe = (await c.execute(
            text("SELECT to_regclass('public.company_business_units')"))).scalar()
        if existe:
            await c.execute(text(
                "DELETE FROM company_business_units WHERE company_id IN "
                "(SELECT id FROM companies WHERE name LIKE :p)"), {"p": f"{PREFIJO}%"})
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
        await c.execute(delete(Role).where(Role.name.like(f"{PREFIJO}%")))
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await motor.dispose()


async def _empresa(s, sufijo=""):
    from app.masters.models import Company

    e = Company(name=f"{PREFIJO}{sufijo}{uuid.uuid4().hex[:8]}", is_active=True)
    s.add(e)
    await s.flush()
    return e


async def _usuario(s, company_id, rol_nombre="Operario"):
    from app.auth.models import Role, User

    rol = Role(name=f"{PREFIJO}{rol_nombre}-{uuid.uuid4().hex[:6]}",
               company_id=company_id, is_active=True)
    s.add(rol)
    await s.flush()
    u = User(
        first_name="Prueba", last_name="Unidad",
        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@example.test",
        username=f"{PREFIJO}{uuid.uuid4().hex[:8]}",
        hashed_password="x", company_id=company_id, role_id=rol.id, is_active=True,
    )
    s.add(u)
    await s.flush()
    return u


async def _unidad(s, code):
    from app.business_units.models import BusinessUnit

    return (await s.execute(
        select(BusinessUnit).where(BusinessUnit.code == code))).scalar_one()


async def _habilitar(s, company_id, code, habilitada=True):
    from app.business_units.models import CompanyBusinessUnit

    unidad = await _unidad(s, code)
    fila = CompanyBusinessUnit(
        company_id=company_id, business_unit_id=unidad.id, is_enabled=habilitada)
    s.add(fila)
    await s.flush()
    return fila


async def _conceder(s, user_id, code):
    """Concede por el camino que usará la administración: la habilitación de **su** empresa."""
    from app.auth.models import User
    from app.business_units.models import CompanyBusinessUnit
    from app.business_units.service import conceder_unidad

    usuario = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
    unidad = await _unidad(s, code)
    habilitacion = (await s.execute(
        select(CompanyBusinessUnit).where(
            CompanyBusinessUnit.company_id == usuario.company_id,
            CompanyBusinessUnit.business_unit_id == unidad.id)
    )).scalar_one()
    return await conceder_unidad(s, user=usuario, company_business_unit=habilitacion)


# ── El catálogo · AC-A01 ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_a01_el_catalogo_tiene_las_cuatro_unidades(sesion_bu):
    """Las cuatro cadenas productivas existen como catálogo de plataforma."""
    from app.business_units.models import BusinessUnit

    codigos = set((await sesion_bu.execute(select(BusinessUnit.code))).scalars().all())
    assert codigos == {"grandparent", "breeder", "hatchery", "broiler"}


@pytest.mark.asyncio
async def test_ac_a01_los_codigos_son_unicos(sesion_bu):
    """Un código repetido haría ambiguo el catálogo entero."""
    from app.business_units.models import BusinessUnit

    with pytest.raises(IntegrityError):
        sesion_bu.add(BusinessUnit(code="breeder", name_key="x", bird_type="breeder"))
        await sesion_bu.flush()
    await sesion_bu.rollback()


@pytest.mark.asyncio
async def test_ac_a01_el_nombre_visible_es_una_clave_de_i18n(sesion_bu):
    """El catálogo guarda una clave, no una traducción: el producto habla dos lenguas."""
    from app.business_units.models import BusinessUnit

    for unidad in (await sesion_bu.execute(select(BusinessUnit))).scalars():
        assert unidad.name_key.startswith("businessUnits."), unidad.name_key
        assert unidad.name_key.endswith(unidad.code)


@pytest.mark.asyncio
async def test_ac_a01_la_correspondencia_con_bird_type_esta_registrada(sesion_bu):
    """`BirdTypeEnum` **no** es la autoridad: el catálogo registra a qué código corresponde.

    La dirección importa. Si el enum mandara, cambiar un valor de dominio cambiaría quién ve
    qué, y eso es exactamente lo que `GA-REM-040 §2` prohíbe.
    """
    from app.business_units.models import BusinessUnit

    filas = {u.code: u.bird_type for u in
             (await sesion_bu.execute(select(BusinessUnit))).scalars()}
    assert filas == {"grandparent": "grandparent", "breeder": "breeder",
                     "hatchery": "hatchery", "broiler": "broiler"}


# ── Habilitación por empresa · AC-A02, AC-A03, AC-A07 ─────────────────────────

@pytest.mark.asyncio
async def test_ac_a02_la_habilitacion_distingue_encendida_de_apagada(sesion_bu):
    """`Breeder ON` y `Hatchery OFF` en la misma empresa son estados distintos y persistidos."""
    from app.business_units.service import unidades_habilitadas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    await _habilitar(sesion_bu, empresa.id, "hatchery", False)

    assert await unidades_habilitadas(sesion_bu, empresa.id) == ["breeder"]


@pytest.mark.asyncio
async def test_ac_a07_la_habilitacion_no_cruza_empresas(sesion_bu):
    """Habilitar una unidad en una empresa no la habilita en otra."""
    from app.business_units.service import unidades_habilitadas

    a = await _empresa(sesion_bu, "A-")
    b = await _empresa(sesion_bu, "B-")
    await _habilitar(sesion_bu, a.id, "breeder", True)

    assert await unidades_habilitadas(sesion_bu, a.id) == ["breeder"]
    assert await unidades_habilitadas(sesion_bu, b.id) == []


@pytest.mark.asyncio
async def test_ac_a02_una_empresa_no_puede_habilitar_dos_veces_la_misma_unidad(sesion_bu):
    """Dos filas para el mismo par harían que «habilitada» dependiese de cuál se lea."""
    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    with pytest.raises(IntegrityError):
        await _habilitar(sesion_bu, empresa.id, "breeder", False)
    await sesion_bu.rollback()


# ── Concesión por usuario · AC-B01, AC-B02 ────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_b01_el_usuario_recibe_un_subconjunto(sesion_bu):
    """La empresa tiene dos; al usuario se le concede una. Efectivas: una."""
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    await _habilitar(sesion_bu, empresa.id, "hatchery", True)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "breeder")

    assert await unidades_efectivas(sesion_bu, u) == ["breeder"]


@pytest.mark.asyncio
async def test_ac_b02_la_empresa_apagada_manda_sobre_la_concesion(sesion_bu):
    """Concesión viva sobre unidad que la empresa apagó: **no** es efectiva.

    Es el caso que protege contra el olvido: revocar la unidad a la empresa no obliga a
    recorrer usuario por usuario.
    """
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "hatchery", False)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "hatchery")

    assert await unidades_efectivas(sesion_bu, u) == []


@pytest.mark.asyncio
async def test_ac_b02_una_unidad_que_la_empresa_no_declaro_no_se_puede_ni_conceder(sesion_bu):
    """Ausencia de fila no es habilitación implícita — y desde `OD-09.d`, ni siquiera es
    concedible.

    Antes de la enmienda esta prueba concedía la unidad y comprobaba que no era efectiva.
    Ahora la concesión apunta a la habilitación de la empresa, y si la empresa nunca declaró
    la unidad **no hay a qué apuntar**: la fila inválida no llega a existir. Se comprueba la
    propiedad más fuerte, no la anterior.
    """
    from app.business_units.models import CompanyBusinessUnit
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    u = await _usuario(sesion_bu, empresa.id)
    unidad = await _unidad(sesion_bu, "broiler")

    habilitacion = (await sesion_bu.execute(
        select(CompanyBusinessUnit).where(
            CompanyBusinessUnit.company_id == empresa.id,
            CompanyBusinessUnit.business_unit_id == unidad.id)
    )).scalar_one_or_none()
    assert habilitacion is None, "la empresa no declaró la unidad: no hay nada que conceder"
    assert await unidades_efectivas(sesion_bu, u) == []


@pytest.mark.asyncio
async def test_ac_b01_no_se_puede_conceder_dos_veces_la_misma_unidad(sesion_bu):
    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "breeder")
    with pytest.raises(IntegrityError):
        await _conceder(sesion_bu, u.id, "breeder")
    await sesion_bu.rollback()


# ── El usuario sin unidades · AC-B03, AC-B04 · OD-09.c ────────────────────────

@pytest.mark.asyncio
async def test_ac_b04_sin_concesiones_el_conjunto_efectivo_esta_vacio(sesion_bu):
    """Y **vacío** quiere decir vacío: nunca «toda la empresa».

    Es la regla que impide que la capacidad entera sea opcional en la práctica. Si no
    conceder nada equivaliera a concederlo todo, nadie concedería nunca.
    """
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    await _habilitar(sesion_bu, empresa.id, "hatchery", True)
    await _habilitar(sesion_bu, empresa.id, "broiler", True)
    u = await _usuario(sesion_bu, empresa.id)

    assert await unidades_efectivas(sesion_bu, u) == []


@pytest.mark.asyncio
async def test_ac_b03_el_usuario_sin_unidades_sigue_siendo_valido(sesion_bu):
    """`OD-09.c`: no tener unidades no es un problema de credenciales.

    El resolutor devuelve un conjunto vacío; no lanza, no niega la identidad y no
    convierte la ausencia de configuración en cuenta inválida.
    """
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    u = await _usuario(sesion_bu, empresa.id)

    assert await unidades_efectivas(sesion_bu, u) == []
    assert u.is_active is True


# ── Aislamiento de empresa · AC-A07 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_a07_no_se_aprovecha_lo_habilitado_en_otra_empresa(sesion_bu):
    """Un usuario de la empresa A no se beneficia de que la empresa B tenga `breeder`.

    La habilitación de B se le ofrece explícitamente al servicio y se rechaza; y el conjunto
    efectivo sigue vacío. Dos comprobaciones, porque protegen cosas distintas: que no se
    escriba, y que no se lea.
    """
    from app.business_units.service import ConcesionInvalida, conceder_unidad, unidades_efectivas

    a = await _empresa(sesion_bu, "A-")
    b = await _empresa(sesion_bu, "B-")
    habilitacion_de_b = await _habilitar(sesion_bu, b.id, "breeder", True)
    u = await _usuario(sesion_bu, a.id)

    with pytest.raises(ConcesionInvalida):
        await conceder_unidad(sesion_bu, user=u, company_business_unit=habilitacion_de_b)

    assert await unidades_efectivas(sesion_bu, u) == []


@pytest.mark.asyncio
async def test_ac_a07_un_usuario_sin_empresa_no_resuelve_nada(sesion_bu):
    """El Super Administrador global se siembra sin empresa. No obtiene acceso operativo
    a ninguna por esta capacidad: el modelo de inquilino se preserva."""
    from app.auth.models import Role, User
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    rol = Role(name=f"{PREFIJO}Global-{uuid.uuid4().hex[:6]}", company_id=None, is_active=True)
    sesion_bu.add(rol)
    await sesion_bu.flush()
    sin_empresa = User(
        first_name="Super", last_name="Global",
        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@example.test",
        username=f"{PREFIJO}{uuid.uuid4().hex[:8]}",
        hashed_password="x", company_id=None, role_id=rol.id, is_active=True)
    sesion_bu.add(sin_empresa)
    await sesion_bu.flush()

    assert await unidades_efectivas(sesion_bu, sin_empresa) == []


# ── Sin atajos · AC-F05 en su parte de fundamento ─────────────────────────────

@pytest.mark.asyncio
async def test_el_nombre_del_rol_no_concede_nada(sesion_bu):
    """Un rol cuyo nombre contiene «admin» no atraviesa el filtro.

    `GA-REM-034` permite crear roles y el nombre es texto editable: si bastara con
    llamarse de cierta forma, la capacidad se saltaría desde la pantalla de roles.
    """
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    await _habilitar(sesion_bu, empresa.id, "hatchery", True)
    u = await _usuario(sesion_bu, empresa.id, rol_nombre="Administrador de Empresa")

    assert await unidades_efectivas(sesion_bu, u) == []


@pytest.mark.asyncio
async def test_el_nombre_del_rol_de_control_tampoco(sesion_bu):
    """`OD-09.a` da visibilidad de control a contraloría, y **no** autoridad operativa.

    Ese es otro resolutor, que la fase 1 no construye. El operativo no debe conocer
    excepciones de control: mezclarlos convertiría una visibilidad de lectura en permiso
    de escritura sobre las cuatro unidades.
    """
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    u = await _usuario(sesion_bu, empresa.id, rol_nombre="Contralor Avícola")

    assert await unidades_efectivas(sesion_bu, u) == []


# ── La unidad retirada del producto · AC-A01 ──────────────────────────────────

@pytest.mark.asyncio
async def test_una_unidad_inactiva_en_el_producto_no_es_efectiva(sesion_bu):
    """El catálogo tiene disponibilidad de plataforma. Si una unidad se retira del producto,
    ninguna empresa la obtiene, por mucho que tenga filas antiguas."""
    from app.business_units.models import BusinessUnit
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "broiler", True)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "broiler")
    assert await unidades_efectivas(sesion_bu, u) == ["broiler"]

    unidad = await _unidad(sesion_bu, "broiler")
    unidad.is_active = False
    await sesion_bu.flush()
    try:
        assert await unidades_efectivas(sesion_bu, u) == []
    finally:
        unidad.is_active = True
        await sesion_bu.flush()


# ── La consulta puntual · AC-C01 en su parte de fundamento ────────────────────

@pytest.mark.asyncio
async def test_la_pregunta_puntual_coincide_con_el_conjunto(sesion_bu):
    """`tiene_acceso` y `unidades_efectivas` no pueden discrepar: son la misma regla.

    Dos caminos con dos respuestas serían dos políticas, y con el tiempo una de las dos
    se quedaría atrás.
    """
    from app.business_units.service import tiene_acceso, unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    await _habilitar(sesion_bu, empresa.id, "hatchery", True)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "breeder")

    efectivas = await unidades_efectivas(sesion_bu, u)
    for code in ("grandparent", "breeder", "hatchery", "broiler"):
        assert await tiene_acceso(sesion_bu, u, code) is (code in efectivas), code


@pytest.mark.asyncio
async def test_la_revocacion_surte_efecto_de_inmediato(sesion_bu):
    """`AC-B05`: se lee de la base en cada evaluación, no de un token ni de una caché.

    Si la concesión viviera solo en el `JWT`, revocar tardaría lo que durase la sesión.
    """
    from app.business_units.models import UserBusinessUnit
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    u = await _usuario(sesion_bu, empresa.id)
    concesion = await _conceder(sesion_bu, u.id, "breeder")
    assert await unidades_efectivas(sesion_bu, u) == ["breeder"]

    await sesion_bu.delete(concesion)
    await sesion_bu.flush()
    assert await unidades_efectivas(sesion_bu, u) == []


@pytest.mark.asyncio
async def test_el_resolutor_no_necesita_una_peticion_http(sesion_bu):
    """`AC-C07`: se invoca con sesión y usuario, sin `Request`.

    Las tareas de fondo y los informes no tienen petición, y si el resolutor la exigiera
    tendrían que reimplementar la regla —que es como se acaba con dos políticas—.
    """
    import inspect

    from app.business_units import service

    for nombre in ("unidades_habilitadas", "unidades_efectivas", "tiene_acceso"):
        firma = inspect.signature(getattr(service, nombre))
        assert "request" not in firma.parameters, nombre


# ── Apagar y volver a encender · AC-A04, AC-A06 · BU-D10 ──────────────────────

@pytest.mark.asyncio
async def test_ac_a04_apagar_una_unidad_no_borra_las_concesiones(sesion_bu):
    """`BU-D10` sigue pendiente de ratificación, así que apagar tiene que ser reversible.

    Si apagar borrase las concesiones, el propietario ya no podría elegir: la opción
    «conservar el histórico» habría desaparecido de hecho el día que alguien apagó una
    unidad. Se conserva la fila y se pierde la efectividad, que sí es reversible.
    """
    from sqlalchemy import func

    from app.business_units.models import UserBusinessUnit
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    habilitacion = await _habilitar(sesion_bu, empresa.id, "hatchery", True)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "hatchery")
    assert await unidades_efectivas(sesion_bu, u) == ["hatchery"]

    habilitacion.is_enabled = False
    await sesion_bu.flush()

    assert await unidades_efectivas(sesion_bu, u) == []
    vivas = (await sesion_bu.execute(
        select(func.count(UserBusinessUnit.id))
        .where(UserBusinessUnit.user_id == u.id)
    )).scalar_one()
    assert vivas == 1, "la concesión debe sobrevivir al apagado"


@pytest.mark.asyncio
async def test_ac_a06_rehabilitar_devuelve_la_efectividad_a_la_concesion_previa(sesion_bu):
    """Encender de nuevo no obliga a recorrer usuario por usuario reconcediendo."""
    from app.business_units.service import unidades_efectivas

    empresa = await _empresa(sesion_bu)
    habilitacion = await _habilitar(sesion_bu, empresa.id, "breeder", True)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "breeder")

    habilitacion.is_enabled = False
    await sesion_bu.flush()
    assert await unidades_efectivas(sesion_bu, u) == []

    habilitacion.is_enabled = True
    await sesion_bu.flush()
    assert await unidades_efectivas(sesion_bu, u) == ["breeder"]


# ── La concesión pertenece a una empresa · AC-B07…AC-B11 · OD-09.d ────────────

async def _mover_de_empresa(s, user, company_id):
    """Mueve al usuario. Hoy ninguna API lo permite —`UserUpdate` no acepta `company_id`—,
    pero el modelo tiene que ser correcto frente a un cambio directo futuro: la ausencia de
    una pantalla no es una garantía de seguridad."""
    user.company_id = company_id
    await s.flush()


@pytest.mark.asyncio
async def test_ac_b07_la_concesion_dice_bajo_que_empresa_se_otorgo(sesion_bu):
    """La fila responde por sí sola, sin mirar la empresa actual del usuario.

    Es la diferencia entre un dato que **contiene** la respuesta y uno del que hay que
    deducirla: si hay que deducirla, el día que la premisa cambie la respuesta cambia sola.
    """
    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit

    empresa = await _empresa(sesion_bu)
    await _habilitar(sesion_bu, empresa.id, "breeder", True)
    u = await _usuario(sesion_bu, empresa.id)
    await _conceder(sesion_bu, u.id, "breeder")

    otorgante = (await sesion_bu.execute(
        select(CompanyBusinessUnit.company_id)
        .join(UserBusinessUnit,
              UserBusinessUnit.company_business_unit_id == CompanyBusinessUnit.id)
        .where(UserBusinessUnit.user_id == u.id)
    )).scalar_one()
    assert otorgante == empresa.id


@pytest.mark.asyncio
async def test_ac_b08_la_concesion_no_viaja_con_el_usuario(sesion_bu):
    """El caso que motivó la enmienda `OD-09.d`.

    Las dos empresas tienen `breeder`. El usuario se mueve de A a B **sin que nadie le conceda
    nada en B**. Antes de la corrección el resolutor devolvía `['breeder']`: la fila no decía
    de qué empresa venía, y las dos eran indistinguibles para ella.
    """
    from app.business_units.service import unidades_efectivas

    a = await _empresa(sesion_bu, "A-")
    b = await _empresa(sesion_bu, "B-")
    await _habilitar(sesion_bu, a.id, "breeder", True)
    await _habilitar(sesion_bu, b.id, "breeder", True)
    u = await _usuario(sesion_bu, a.id)
    await _conceder(sesion_bu, u.id, "breeder")
    assert await unidades_efectivas(sesion_bu, u) == ["breeder"]

    await _mover_de_empresa(sesion_bu, u, b.id)

    assert await unidades_efectivas(sesion_bu, u) == [], (
        "la concesión de la empresa A no puede volverse efectiva en la B")


@pytest.mark.asyncio
async def test_ac_b08_en_la_empresa_nueva_hace_falta_conceder_de_nuevo(sesion_bu):
    """Y al concederla explícitamente, funciona. Sin ese segundo paso no habría corrección,
    solo una puerta cerrada."""
    from app.business_units.service import unidades_efectivas

    a = await _empresa(sesion_bu, "A-")
    b = await _empresa(sesion_bu, "B-")
    await _habilitar(sesion_bu, a.id, "breeder", True)
    await _habilitar(sesion_bu, b.id, "breeder", True)
    u = await _usuario(sesion_bu, a.id)
    await _conceder(sesion_bu, u.id, "breeder")
    await _mover_de_empresa(sesion_bu, u, b.id)
    assert await unidades_efectivas(sesion_bu, u) == []

    await _conceder(sesion_bu, u.id, "breeder")
    assert await unidades_efectivas(sesion_bu, u) == ["breeder"]


@pytest.mark.asyncio
async def test_ac_b11_mover_de_empresa_no_borra_la_concesion_anterior(sesion_bu):
    """`OD-09.d`: la historia se conserva; lo que se pierde es la efectividad.

    Borrarla haría imposible reconstruir quién tuvo acceso a qué y cuándo, que es justo lo
    que un control de acceso tiene que poder responder.
    """
    from sqlalchemy import func

    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit

    a = await _empresa(sesion_bu, "A-")
    b = await _empresa(sesion_bu, "B-")
    await _habilitar(sesion_bu, a.id, "breeder", True)
    await _habilitar(sesion_bu, b.id, "breeder", True)
    u = await _usuario(sesion_bu, a.id)
    await _conceder(sesion_bu, u.id, "breeder")
    await _mover_de_empresa(sesion_bu, u, b.id)
    # Y se le concede en la empresa nueva: es el momento en que alguien podría sentir la
    # tentación de «limpiar» lo anterior. No se limpia.
    await _conceder(sesion_bu, u.id, "breeder")

    de_a = (await sesion_bu.execute(
        select(func.count(UserBusinessUnit.id))
        .join(CompanyBusinessUnit,
              CompanyBusinessUnit.id == UserBusinessUnit.company_business_unit_id)
        .where(UserBusinessUnit.user_id == u.id,
               CompanyBusinessUnit.company_id == a.id)
    )).scalar_one()
    assert de_a == 1, "la concesión de la empresa A debe seguir registrada"


@pytest.mark.asyncio
async def test_ac_b09_el_mismo_codigo_en_dos_empresas_son_dos_contextos(sesion_bu):
    """`breeder` de A y `breeder` de B no son la misma autorización.

    Es la prueba central de la enmienda: sin ella, «unidad de negocio» sería un permiso
    global con nombre de cadena productiva.
    """
    from app.business_units.service import tiene_acceso, unidades_efectivas

    a = await _empresa(sesion_bu, "A-")
    b = await _empresa(sesion_bu, "B-")
    await _habilitar(sesion_bu, a.id, "breeder", True)
    await _habilitar(sesion_bu, b.id, "breeder", True)

    de_a = await _usuario(sesion_bu, a.id)
    de_b = await _usuario(sesion_bu, b.id)
    await _conceder(sesion_bu, de_a.id, "breeder")

    assert await unidades_efectivas(sesion_bu, de_a) == ["breeder"]
    assert await unidades_efectivas(sesion_bu, de_b) == []
    assert await tiene_acceso(sesion_bu, de_b, "breeder") is False


@pytest.mark.asyncio
async def test_ac_b10_conceder_cruzando_empresas_se_rechaza(sesion_bu):
    """Un usuario de la empresa A no puede recibir la habilitación de la empresa B.

    Se rechaza en el límite de servicio y **no queda escrita**: una fila inválida que
    existe acaba encontrando el camino a una consulta que la lea mal.
    """
    from sqlalchemy import func

    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit
    from app.business_units.service import ConcesionInvalida, conceder_unidad

    a = await _empresa(sesion_bu, "A-")
    b = await _empresa(sesion_bu, "B-")
    await _habilitar(sesion_bu, a.id, "breeder", True)
    habilitacion_de_b = await _habilitar(sesion_bu, b.id, "breeder", True)
    u = await _usuario(sesion_bu, a.id)

    with pytest.raises(ConcesionInvalida):
        await conceder_unidad(sesion_bu, user=u, company_business_unit=habilitacion_de_b)

    escritas = (await sesion_bu.execute(
        select(func.count(UserBusinessUnit.id))
        .join(CompanyBusinessUnit,
              CompanyBusinessUnit.id == UserBusinessUnit.company_business_unit_id)
        .where(UserBusinessUnit.user_id == u.id)
    )).scalar_one()
    assert escritas == 0, "no debe quedar escrita ninguna concesión"


@pytest.mark.asyncio
async def test_ac_b10_conceder_a_un_usuario_sin_empresa_se_rechaza(sesion_bu):
    """Sin empresa no hay empresa que conceda. El super administrador global entra por aquí."""
    from app.auth.models import Role, User
    from app.business_units.service import ConcesionInvalida, conceder_unidad

    empresa = await _empresa(sesion_bu)
    habilitacion = await _habilitar(sesion_bu, empresa.id, "breeder", True)
    rol = Role(name=f"{PREFIJO}Global-{uuid.uuid4().hex[:6]}", company_id=None, is_active=True)
    sesion_bu.add(rol)
    await sesion_bu.flush()
    sin_empresa = User(
        first_name="Super", last_name="Global",
        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@example.test",
        username=f"{PREFIJO}{uuid.uuid4().hex[:8]}",
        hashed_password="x", company_id=None, role_id=rol.id, is_active=True)
    sesion_bu.add(sin_empresa)
    await sesion_bu.flush()

    with pytest.raises(ConcesionInvalida):
        await conceder_unidad(sesion_bu, user=sin_empresa, company_business_unit=habilitacion)


@pytest.mark.asyncio
async def test_ac_b07_conceder_por_el_servicio_produce_la_misma_efectividad(sesion_bu):
    """El camino de escritura y el de lectura tienen que casar."""
    from app.business_units.models import CompanyBusinessUnit
    from app.business_units.service import conceder_unidad, unidades_efectivas

    empresa = await _empresa(sesion_bu)
    habilitacion = await _habilitar(sesion_bu, empresa.id, "hatchery", True)
    assert isinstance(habilitacion, CompanyBusinessUnit)
    u = await _usuario(sesion_bu, empresa.id)

    await conceder_unidad(sesion_bu, user=u, company_business_unit=habilitacion)
    assert await unidades_efectivas(sesion_bu, u) == ["hatchery"]
