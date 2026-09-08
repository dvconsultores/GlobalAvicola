"""Seguridad central — `GA-REM-040` fase 2 · `OD-11` · `OD-09.e`.

Tres dimensiones que esta suite existe para mantener separadas:

    CONTEXTO DE INQUILINO   ¿en qué empresa se evalúa esta petición?
    ACCESO A UNIDAD         ¿qué cadenas productivas puede ver?
    PERMISO RBAC            ¿qué acción puede ejecutar?

Y una advertencia que la fase 2 **no** levanta: clasificar una ruta no es proteger sus filas.
Nada de lo que se prueba aquí hace que `/lots` devuelva menos lotes.
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

PREFIJO = "BUG2-"


@pytest_asyncio.fixture
async def s(test_database_url):
    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as sesion:
        yield sesion
    from app.auth.models import Role, User
    from app.masters.models import Company

    async with motor.begin() as c:
        for tabla in ("user_business_units",):
            if (await c.execute(text(f"SELECT to_regclass('public.{tabla}')"))).scalar():
                await c.execute(text(
                    f"DELETE FROM {tabla} WHERE user_id IN "
                    "(SELECT id FROM users WHERE username LIKE :p)"), {"p": f"{PREFIJO}%"})
        if (await c.execute(
                text("SELECT to_regclass('public.company_business_units')"))).scalar():
            await c.execute(text(
                "DELETE FROM company_business_units WHERE company_id IN "
                "(SELECT id FROM companies WHERE name LIKE :p)"), {"p": f"{PREFIJO}%"})
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
        await c.execute(delete(Role).where(Role.name.like(f"{PREFIJO}%")))
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await motor.dispose()


async def _empresa(s, activa=True, sufijo=""):
    from app.masters.models import Company

    e = Company(name=f"{PREFIJO}{sufijo}{uuid.uuid4().hex[:8]}", is_active=activa)
    s.add(e)
    await s.flush()
    return e


async def _usuario(s, company_id, rol="Operario"):
    from app.auth.models import Role, User

    r = Role(name=f"{PREFIJO}{rol}-{uuid.uuid4().hex[:6]}", company_id=company_id,
             is_active=True)
    s.add(r)
    await s.flush()
    u = User(first_name="P", last_name="U",
             email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
             username=f"{PREFIJO}{uuid.uuid4().hex[:8]}", hashed_password="x",
             company_id=company_id, role_id=r.id, is_active=True)
    s.add(u)
    await s.flush()
    return u


async def _habilitar(s, company_id, code, on=True):
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit

    unidad = (await s.execute(
        select(BusinessUnit).where(BusinessUnit.code == code))).scalar_one()
    fila = CompanyBusinessUnit(company_id=company_id, business_unit_id=unidad.id,
                              is_enabled=on)
    s.add(fila)
    await s.flush()
    return fila


async def _mover(s, user, company_id):
    """Mueve al usuario **por la operación sancionada**: revocar y después cambiar.

    Ninguna API hace esto hoy —`UserUpdate` no acepta `company_id`—, pero es la forma que la
    fase 7 tendrá que respetar. Empujar el campo a mano sin revocar deja el modelo en un
    estado que ninguna operación produce, igual que escribir `role_id` a mano se salta el
    `RBAC`.
    """
    from app.business_units.service import revocar_concesiones

    await revocar_concesiones(s, user=user)
    user.company_id = company_id
    await s.flush()


async def _conceder(s, user, code):
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad

    unidad = (await s.execute(
        select(BusinessUnit).where(BusinessUnit.code == code))).scalar_one()
    hab = (await s.execute(select(CompanyBusinessUnit).where(
        CompanyBusinessUnit.company_id == user.company_id,
        CompanyBusinessUnit.business_unit_id == unidad.id))).scalar_one()
    return await conceder_unidad(s, user=user, company_business_unit=hab)


# ═══ La empresa efectiva · AC-C09 … AC-C14 · OD-11 ═══════════════════════════

@pytest.mark.asyncio
async def test_ac_c09_para_un_usuario_normal_manda_la_base(s):
    """`OD-11.a`. La empresa persistida, sin más."""
    from app.tenancy import resolver_empresa_efectiva

    empresa = await _empresa(s)
    u = await _usuario(s, empresa.id)

    assert await resolver_empresa_efectiva(
        s, user=u, reclamada=None, puede_cambiar=False) == empresa.id


@pytest.mark.asyncio
async def test_ac_c10_una_reclamacion_ajena_no_desplaza_el_inquilino(s):
    """El aislamiento multiempresa se sostiene sobre esto: un token **no** reclama
    compañías ajenas. Si bastara con pedirlo, no habría aislamiento."""
    from app.tenancy import resolver_empresa_efectiva

    a = await _empresa(s, sufijo="A-")
    b = await _empresa(s, sufijo="B-")
    u = await _usuario(s, a.id)

    efectiva = await resolver_empresa_efectiva(
        s, user=u, reclamada=b.id, puede_cambiar=False)
    assert efectiva == a.id, "la reclamación se ignora, no se honra"


@pytest.mark.asyncio
async def test_ac_c11_un_actor_autorizado_si_desplaza_el_contexto(s):
    """`OD-11.b`. El Super Administrador se sitúa en una empresa: para eso existe."""
    from app.tenancy import resolver_empresa_efectiva

    empresa = await _empresa(s)
    u = await _usuario(s, None)

    assert await resolver_empresa_efectiva(
        s, user=u, reclamada=empresa.id, puede_cambiar=True) == empresa.id


@pytest.mark.asyncio
async def test_ac_c11_una_empresa_inexistente_no_da_contexto(s):
    from app.tenancy import resolver_empresa_efectiva

    u = await _usuario(s, None)
    assert await resolver_empresa_efectiva(
        s, user=u, reclamada=9_999_999, puede_cambiar=True) is None


@pytest.mark.asyncio
async def test_ac_c12_una_empresa_desactivada_deja_de_dar_contexto(s):
    """Y esto es lo que obliga a validar **en cada petición**.

    `switch-company` comprueba al emitir el token. El token vive treinta minutos y la
    renovación lo reemite. Si la empresa se desactiva entretanto, un contexto validado hace
    media hora no prueba nada sobre ahora.
    """
    from app.tenancy import resolver_empresa_efectiva

    empresa = await _empresa(s)
    u = await _usuario(s, None)
    assert await resolver_empresa_efectiva(
        s, user=u, reclamada=empresa.id, puede_cambiar=True) == empresa.id

    empresa.is_active = False
    await s.flush()

    assert await resolver_empresa_efectiva(
        s, user=u, reclamada=empresa.id, puede_cambiar=True) is None


@pytest.mark.asyncio
async def test_ac_c13_sin_empresa_y_sin_contexto_no_hay_empresa_efectiva(s):
    """`OD-11.c`. No se resuelve «todas las empresas»: elegir es un acto."""
    from app.tenancy import resolver_empresa_efectiva

    await _empresa(s)
    u = await _usuario(s, None)

    assert await resolver_empresa_efectiva(
        s, user=u, reclamada=None, puede_cambiar=True) is None


@pytest.mark.asyncio
async def test_ac_c14_cambiar_de_empresa_no_concede_ninguna_unidad(s):
    """El punto donde un atajo sería más tentador y más grave.

    El actor autorizado se sitúa en una empresa con las cuatro unidades habilitadas. Obtiene
    **contexto**, no autoridad: nadie le concedió nada allí.
    """
    from app.business_units.service import unidades_efectivas
    from app.tenancy import resolver_empresa_efectiva

    empresa = await _empresa(s)
    for code in ("grandparent", "breeder", "hatchery", "broiler"):
        await _habilitar(s, empresa.id, code, True)
    u = await _usuario(s, None)

    efectiva = await resolver_empresa_efectiva(
        s, user=u, reclamada=empresa.id, puede_cambiar=True)
    assert efectiva == empresa.id
    assert await unidades_efectivas(s, u, company_id=efectiva) == []


# ═══ La guarda de unidad · AC-C08, AC-C16 ════════════════════════════════════

@pytest.mark.asyncio
async def test_la_guarda_deja_pasar_una_concesion_viva(s):
    """El caso positivo. Sin él, una guarda que deniega todo pasaría por segura."""
    from app.business_units.service import exigir_acceso_a_unidad

    empresa = await _empresa(s)
    await _habilitar(s, empresa.id, "breeder", True)
    u = await _usuario(s, empresa.id)
    await _conceder(s, u, "breeder")

    await exigir_acceso_a_unidad(s, user=u, code="breeder")


@pytest.mark.asyncio
async def test_la_guarda_deniega_sin_concesion(s):
    from app.business_units.service import AccesoDeUnidadDenegado, exigir_acceso_a_unidad

    empresa = await _empresa(s)
    await _habilitar(s, empresa.id, "breeder", True)
    u = await _usuario(s, empresa.id)

    with pytest.raises(AccesoDeUnidadDenegado):
        await exigir_acceso_a_unidad(s, user=u, code="breeder")


@pytest.mark.asyncio
async def test_la_guarda_deniega_si_la_empresa_apago_la_unidad(s):
    from app.business_units.service import AccesoDeUnidadDenegado, exigir_acceso_a_unidad

    empresa = await _empresa(s)
    habilitacion = await _habilitar(s, empresa.id, "breeder", True)
    u = await _usuario(s, empresa.id)
    await _conceder(s, u, "breeder")
    await exigir_acceso_a_unidad(s, user=u, code="breeder")

    habilitacion.is_enabled = False
    await s.flush()

    with pytest.raises(AccesoDeUnidadDenegado):
        await exigir_acceso_a_unidad(s, user=u, code="breeder")


@pytest.mark.asyncio
async def test_la_guarda_no_cruza_empresas_con_el_mismo_codigo(s):
    """`breeder` de A no satisface a `breeder` de B."""
    from app.business_units.service import AccesoDeUnidadDenegado, exigir_acceso_a_unidad

    a = await _empresa(s, sufijo="A-")
    b = await _empresa(s, sufijo="B-")
    await _habilitar(s, a.id, "breeder", True)
    await _habilitar(s, b.id, "breeder", True)
    de_a = await _usuario(s, a.id)
    await _conceder(s, de_a, "breeder")

    await exigir_acceso_a_unidad(s, user=de_a, code="breeder")
    with pytest.raises(AccesoDeUnidadDenegado):
        await exigir_acceso_a_unidad(s, user=de_a, code="breeder", company_id=b.id)


@pytest.mark.asyncio
async def test_la_guarda_deniega_al_usuario_sin_unidades(s):
    """`BU-D09` desde el otro lado: entra, y la operación productiva le queda cerrada."""
    from app.business_units.service import AccesoDeUnidadDenegado, exigir_acceso_a_unidad

    empresa = await _empresa(s)
    for code in ("breeder", "hatchery"):
        await _habilitar(s, empresa.id, code, True)
    u = await _usuario(s, empresa.id)

    for code in ("grandparent", "breeder", "hatchery", "broiler"):
        with pytest.raises(AccesoDeUnidadDenegado):
            await exigir_acceso_a_unidad(s, user=u, code=code)


@pytest.mark.asyncio
async def test_el_nombre_del_rol_no_atraviesa_la_guarda(s):
    """Ni «Administrador», ni «Contralor», ni «Super Administrador».

    `GA-REM-034` permite crear roles y el nombre es texto editable: si bastara con llamarse
    de cierta forma, la capacidad se saltaría desde la pantalla de roles.
    """
    from app.business_units.service import AccesoDeUnidadDenegado, exigir_acceso_a_unidad

    empresa = await _empresa(s)
    await _habilitar(s, empresa.id, "breeder", True)
    for nombre in ("Administrador de Empresa", "Contralor Avícola", "Super Administrador"):
        u = await _usuario(s, empresa.id, rol=nombre)
        with pytest.raises(AccesoDeUnidadDenegado):
            await exigir_acceso_a_unidad(s, user=u, code="breeder")


@pytest.mark.asyncio
async def test_la_guarda_no_necesita_una_peticion_http(s):
    """`AC-C16`. Las tareas de fondo y los informes no tienen `Request`."""
    import inspect

    from app.business_units import service
    from app import tenancy

    for fn in (service.exigir_acceso_a_unidad, tenancy.resolver_empresa_efectiva):
        assert "request" not in inspect.signature(fn).parameters, fn.__name__


# ═══ Volver a una empresa anterior · AC-B12 · OD-09.e ════════════════════════

@pytest.mark.asyncio
async def test_ac_b12_volver_no_reactiva_la_concesion(s):
    """`OD-09.e`. Volver no prueba el mismo cargo ni la misma necesidad operativa.

    Una autorización que revive sola es una autorización que nadie concedió.
    """
    from app.business_units.service import unidades_efectivas

    a = await _empresa(s, sufijo="A-")
    b = await _empresa(s, sufijo="B-")
    await _habilitar(s, a.id, "breeder", True)
    await _habilitar(s, b.id, "breeder", True)
    u = await _usuario(s, a.id)
    await _conceder(s, u, "breeder")
    assert await unidades_efectivas(s, u) == ["breeder"]

    await _mover(s, u, b.id)      # se va
    assert await unidades_efectivas(s, u) == []

    await _mover(s, u, a.id)      # y vuelve
    assert await unidades_efectivas(s, u) == [], (
        "la concesión anterior no puede revivir por regresar")


@pytest.mark.asyncio
async def test_ac_b12_al_volver_hace_falta_una_concesion_nueva(s):
    from app.business_units.service import unidades_efectivas

    a = await _empresa(s, sufijo="A-")
    b = await _empresa(s, sufijo="B-")
    await _habilitar(s, a.id, "breeder", True)
    await _habilitar(s, b.id, "breeder", True)
    u = await _usuario(s, a.id)
    await _conceder(s, u, "breeder")
    await _mover(s, u, b.id)
    await _mover(s, u, a.id)
    assert await unidades_efectivas(s, u) == []

    await _conceder(s, u, "breeder")
    assert await unidades_efectivas(s, u) == ["breeder"]


@pytest.mark.asyncio
async def test_ac_b12_la_concesion_anterior_sigue_registrada_tras_volver(s):
    """Historia sí; autorización no."""
    from sqlalchemy import func

    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit

    a = await _empresa(s, sufijo="A-")
    b = await _empresa(s, sufijo="B-")
    await _habilitar(s, a.id, "breeder", True)
    await _habilitar(s, b.id, "breeder", True)
    u = await _usuario(s, a.id)
    await _conceder(s, u, "breeder")
    await _mover(s, u, b.id)
    await _mover(s, u, a.id)

    vivas = (await s.execute(
        select(func.count(UserBusinessUnit.id))
        .join(CompanyBusinessUnit,
              CompanyBusinessUnit.id == UserBusinessUnit.company_business_unit_id)
        .where(UserBusinessUnit.user_id == u.id, CompanyBusinessUnit.company_id == a.id)
    )).scalar_one()
    assert vivas == 1


# ═══ Clasificación de rutas · AC-C15 · T-040-06, T-040-07 ═══════════════════

def test_ac_c15_toda_ruta_esta_clasificada():
    """La guarda de arranque falla si alguna no lo está, igual que ya falla si alguna no
    declara permiso. Un olvido es un fallo de arranque, no un agujero silencioso."""
    from app.business_units.route_scope import rutas_sin_clasificar
    from app.main import app

    sin_clasificar = rutas_sin_clasificar(app)
    assert sin_clasificar == [], f"rutas sin alcance declarado: {sin_clasificar}"


def test_ac_c15_una_ruta_nueva_sin_clasificar_rompe_el_arranque():
    """Sin este control, la clasificación se degradaría sola: cada ruta nueva la olvidaría.

    Se prueba contra una aplicación de mentira, no ensuciando la real con una ruta de
    prueba que después habría que acordarse de quitar.
    """
    from fastapi import FastAPI

    from app.business_units.route_scope import (
        AlcanceNoDeclarado, rutas_sin_clasificar, verificar,
    )

    falsa = FastAPI()

    @falsa.get("/api/v1/inventada")
    def _inventada():  # pragma: no cover - nunca se sirve
        return {}

    assert rutas_sin_clasificar(falsa) == ["GET /api/v1/inventada"]
    with pytest.raises(AlcanceNoDeclarado):
        verificar(falsa)


def test_las_cinco_clases_estan_representadas():
    """Si una clase no se usa, o sobra en el vocabulario o hay rutas mal clasificadas."""
    from app.business_units.route_scope import Alcance, inventario
    from app.main import app

    por_clase = inventario(app)
    for clase in (Alcance.CORE, Alcance.CONTROL, Alcance.UNIDAD_UNICA,
                  Alcance.MULTI_UNIDAD, Alcance.CONTRATO):
        assert por_clase.get(clase), f"ninguna ruta clasificada como {clase.value}"


def test_lots_es_multi_unidad_y_eso_no_la_hace_segura():
    """`GA-REM-040` enmienda B: clasificar una ruta **no** es proteger sus filas.

    Esta prueba existe para que nadie lea la clasificación como una certificación. `/lots`
    sigue devolviendo lotes de todas las unidades de la empresa hasta la fase 3.
    """
    from app.business_units.route_scope import Alcance, clasificar

    alcance, _ = clasificar("/api/v1/lots")
    assert alcance is Alcance.MULTI_UNIDAD


def test_las_rutas_de_control_no_exigen_unidad_productiva():
    """`OD-09.b`: administrar el acceso es plano de control, no operación."""
    from app.business_units.route_scope import Alcance, clasificar

    for camino in ("/api/v1/users", "/api/v1/roles", "/api/v1/masters/areas"):
        alcance, _ = clasificar(camino)
        assert alcance is Alcance.CONTROL, camino


def test_la_incubadora_declara_su_unidad():
    """Una ruta inherentemente de una cadena lo dice, y no hace falta un `if` en cada una."""
    from app.business_units.route_scope import Alcance, clasificar, unidad_requerida

    for camino in ("/api/v1/masters/hatcheries", "/api/v1/masters/incubators",
                   "/api/v1/masters/hatchers"):
        alcance, _ = clasificar(camino)
        assert alcance is Alcance.UNIDAD_UNICA, camino
        assert unidad_requerida(camino) == "hatchery", camino
    assert unidad_requerida("/api/v1/masters/processing-plants") == "broiler"


@pytest.mark.asyncio
async def test_una_concesion_revocada_no_es_efectiva_ni_en_su_propia_empresa(s):
    """Revocar es revocar: no depende de que el usuario se haya movido.

    Sin esta prueba, `revocar_concesiones` solo estaría probada como efecto lateral de un
    cambio de empresa, y una regla probada de refilón es una regla a medio probar.
    """
    from app.business_units.service import revocar_concesiones, unidades_efectivas

    empresa = await _empresa(s)
    await _habilitar(s, empresa.id, "breeder", True)
    u = await _usuario(s, empresa.id)
    await _conceder(s, u, "breeder")
    assert await unidades_efectivas(s, u) == ["breeder"]

    revocadas = await revocar_concesiones(s, user=u)
    assert revocadas == 1
    assert await unidades_efectivas(s, u) == []


@pytest.mark.asyncio
async def test_una_concesion_revocada_se_puede_volver_a_otorgar(s):
    """La unicidad es entre las **vivas**. Si fuera total, revocar sería irreversible y eso
    no es lo que revocar significa."""
    from app.business_units.service import revocar_concesiones, unidades_efectivas

    empresa = await _empresa(s)
    await _habilitar(s, empresa.id, "breeder", True)
    u = await _usuario(s, empresa.id)
    await _conceder(s, u, "breeder")
    await revocar_concesiones(s, user=u)

    await _conceder(s, u, "breeder")
    assert await unidades_efectivas(s, u) == ["breeder"]
