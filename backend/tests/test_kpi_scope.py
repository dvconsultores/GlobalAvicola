"""Agregados e indicadores acotados por unidad — `GA-REM-040` fase 4 · `T-040-11` · `T-040-12`.

    LO QUE NO SE PUEDE VER COMO FILAS
    NO PUEDE REAPARECER COMO TOTAL

La fase 3 dejó `/lots` acotado. Un total calculado sobre la empresa entera devuelve por la
puerta de atrás lo que el listado acaba de ocultar: no enseña la fila, enseña que existe y
cuánto pesa. Y es la única fuga que **no deja rastro y nadie reporta**.

Al inventariar apareció que la forma del riesgo no es la que se suponía. Casi todos los `KPI`
son **por lote** —exigen `lot_id`—, de modo que no suman la empresa: filtran cuando alguien
nombra el lote de otra cadena. Los agregados de empresa de verdad son los del panel y los
indicadores sin lote.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.security import create_access_token
from tests.time_reference import days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "BUKPI-"

#: Valores discriminantes: si las dos cadenas tuvieran el mismo número, una fuga pasaría
#: inadvertida —el total sería idéntico con filtro y sin él— y la prueba no probaría nada.
MUERTES_REPRODUCTORA = 10
MUERTES_INCUBADORA = 7
POBLACION_INICIAL = 1000
#: Un registro pendiente de revisión. `P-15` **no** lo cuenta, y el filtro de seguridad de la
#: fase 4 no puede alterar esa regla: se añade encima, no en su lugar.
MUERTES_SIN_APROBAR = 500


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def kpi(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.lots.models import OpeningBalance
    from app.masters.models import BirdTypeEnum, Company, Lot, ProductivePhase
    from app.operations.models import (
        BirdMovement, EventStatus, EventType, OperationalEvent,
    )

    motor = create_async_engine(test_database_url)
    datos: dict = {}
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

        fase = (await s.execute(select(ProductivePhase).limit(1))).scalar_one_or_none()
        if fase is None:
            fase = ProductivePhase(name=f"{PREFIJO}F", code=f"{PREFIJO[:3]}{uuid.uuid4().hex[:4]}",
                                   order=1, duration_days=10)
            s.add(fase)
            await s.flush()

        rol = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        for modulo in ("lots", "reports", "dashboard"):
            s.add(Permission(role_id=rol.id, module=modulo,
                             action=PermissionAction.READ, scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, role_id=None):
            return User(first_name=marca, last_name="Kpi",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=role_id or rol.id, is_active=True)

        re_, amb, cero = _usuario(a.id, "RE"), _usuario(a.id, "AMB"), _usuario(a.id, "CERO")
        s.add_all([re_, amb, cero])
        await s.flush()
        await conceder_unidad(s, user=re_, company_business_unit=hab[(a.id, "breeder")])
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=amb, company_business_unit=hab[(a.id, code)])

        async def _lote_con_muertes(company_id, marca, tipo, muertes):
            lote = Lot(company_id=company_id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status="active")
            s.add(lote)
            await s.flush()
            s.add(OpeningBalance(
                lot_id=lote.id, activation_date=days_ago(60),
                phase_at_activation_id=fase.id,
                initial_male_count=POBLACION_INICIAL // 2,
                initial_female_count=POBLACION_INICIAL // 2,
                is_manual_activation=True, activated_by_id=amb.id))
            evento = OperationalEvent(
                company_id=company_id, lot_id=lote.id,
                event_type=EventType.MORTALITY_RECORDING,
                event_date=days_ago(10), status=EventStatus.APPROVED,
                registered_by_id=amb.id)
            s.add(evento)
            await s.flush()
            s.add(BirdMovement(event_id=evento.id, quantity=muertes))
            await s.flush()
            return lote

        lote_r = await _lote_con_muertes(a.id, "R", BirdTypeEnum.BREEDER, MUERTES_REPRODUCTORA)
        # Un registro **sin aprobar** sobre el mismo lote. `P-15` lo excluye, y esa regla
        # funcional tiene que sobrevivir al filtro de seguridad que la fase 4 añade.
        borrador = OperationalEvent(
            company_id=a.id, lot_id=lote_r.id, event_type=EventType.MORTALITY_RECORDING,
            event_date=days_ago(5), status=EventStatus.PENDING_REVIEW,
            registered_by_id=amb.id)
        s.add(borrador)
        await s.flush()
        s.add(BirdMovement(event_id=borrador.id, quantity=MUERTES_SIN_APROBAR))
        await s.flush()
        lote_h = await _lote_con_muertes(a.id, "H", BirdTypeEnum.HATCHERY, MUERTES_INCUBADORA)
        lote_b = await _lote_con_muertes(b.id, "B", BirdTypeEnum.BREEDER, 99)
        await s.commit()

        datos = {"empresa_a": a.id, "lote_r": lote_r.id, "lote_h": lote_h.id,
                 "lote_b": lote_b.id, "user_re": re_.id, "user_amb": amb.id,
                 "user_cero": cero.id, "hab_hatchery": hab[(a.id, "hatchery")].id,
                 "rol_id": rol.id}

    yield datos

    async with motor.begin() as c:
        for sql in (
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events "
            "WHERE lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p))",
            "DELETE FROM operational_events WHERE lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM opening_balances WHERE lot_id IN "
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


# ── El KPI por lote · nombrar el lote ajeno no debe bastar ───────────────────

async def test_el_kpi_del_lote_propio_funciona(http_client, kpi):
    """`CONTROL`. Y comprueba de paso que la fórmula de `P-15` no ha cambiado."""
    r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={kpi['lote_r']}",
                              headers=_token(kpi["user_re"]))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["total_deaths"] == MUERTES_REPRODUCTORA
    assert cuerpo["initial_population"] == POBLACION_INICIAL
    assert cuerpo["mortality_rate_pct"] == round(
        MUERTES_REPRODUCTORA / POBLACION_INICIAL * 100, 2)


async def test_el_kpi_de_un_lote_de_otra_cadena_es_inalcanzable(http_client, kpi):
    """`TRATAMIENTO`. Conocer el identificador del lote de incubadora no puede bastar.

    Si bastara, el indicador devolvería exactamente el dato que el listado oculta —y con más
    detalle: población inicial, muertes y tasa—.
    """
    r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={kpi['lote_h']}",
                              headers=_token(kpi["user_re"]))
    assert r.status_code == 404, r.text
    assert str(MUERTES_INCUBADORA) not in r.text


async def test_el_usuario_de_dos_cadenas_alcanza_los_dos_kpi(http_client, kpi):
    """Sin este control, un indicador que deniega siempre pasaría por seguro."""
    for lote, muertes in ((kpi["lote_r"], MUERTES_REPRODUCTORA),
                          (kpi["lote_h"], MUERTES_INCUBADORA)):
        r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={lote}",
                                  headers=_token(kpi["user_amb"]))
        assert r.status_code == 200, r.text
        assert r.json()["total_deaths"] == muertes


async def test_el_usuario_sin_unidades_no_alcanza_ningun_kpi(http_client, kpi):
    for lote in (kpi["lote_r"], kpi["lote_h"]):
        r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={lote}",
                                  headers=_token(kpi["user_cero"]))
        assert r.status_code == 404, r.text


async def test_el_kpi_de_otra_empresa_sigue_siendo_inalcanzable(http_client, kpi):
    r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={kpi['lote_b']}",
                              headers=_token(kpi["user_amb"]))
    assert r.status_code == 404, r.text


async def test_apagar_la_unidad_retira_su_kpi(http_client, kpi, test_database_url):
    from app.business_units.models import CompanyBusinessUnit

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor)() as s:
        h = await s.get(CompanyBusinessUnit, kpi["hab_hatchery"])
        h.is_enabled = False
        await s.commit()
    try:
        r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={kpi['lote_h']}",
                                  headers=_token(kpi["user_amb"]))
        assert r.status_code == 404, r.text
    finally:
        async with async_sessionmaker(motor)() as s:
            h = await s.get(CompanyBusinessUnit, kpi["hab_hatchery"])
            h.is_enabled = True
            await s.commit()
        await motor.dispose()


async def test_los_demas_kpi_por_lote_tambien_se_acotan(http_client, kpi):
    """Arreglar uno no arregla los otros once: cada uno tiene su método."""
    for camino in ("feed-conversion", "egg-production", "animal-welfare",
                   "vaccination-efficiency", "transfer-efficiency", "afcr",
                   "production-index"):
        r = await http_client.get(
            f"/api/v1/reports/kpis/{camino}?lot_id={kpi['lote_h']}",
            headers=_token(kpi["user_re"]))
        assert r.status_code == 404, f"{camino}: {r.status_code} {r.text}"


async def test_los_kpi_por_ruta_con_lote_tambien(http_client, kpi):
    for camino in (f"kpi/ipe/{kpi['lote_h']}", f"kpi/weight-uniformity/{kpi['lote_h']}",
                   f"lot/{kpi['lote_h']}"):
        r = await http_client.get(f"/api/v1/reports/{camino}",
                                  headers=_token(kpi["user_re"]))
        assert r.status_code == 404, f"{camino}: {r.status_code} {r.text}"


# ── El agregado de empresa · la fuga por diferencia ──────────────────────────

async def test_el_panel_no_revela_las_cadenas_ajenas_como_grupo(http_client, kpi):
    """`§46`. Un total acotado no basta si la **dimensión** nombra lo ajeno.

        {"breeder": 3, "hatchery": 5}

    no enseña ninguna fila de incubadora y sin embargo dice que existe y cuántos hay.
    """
    r = await http_client.get("/api/v1/dashboard/admin", headers=_token(kpi["user_re"]))
    assert r.status_code == 200, r.text
    por_tipo = r.json().get("lots_by_type") or {}
    # La clave llega como `BirdTypeEnum.HATCHERY`, no como `hatchery`: comparar por
    # igualdad exacta haría que esta prueba pasara sin comprobar nada.
    etiquetas = " ".join(str(k).lower() for k in por_tipo)
    assert "hatchery" not in etiquetas, (
        f"la cadena ajena aparece como grupo: {por_tipo}")


async def test_el_panel_del_usuario_de_dos_cadenas_las_muestra(http_client, kpi):
    r = await http_client.get("/api/v1/dashboard/admin", headers=_token(kpi["user_amb"]))
    assert r.status_code == 200, r.text
    # `R-216`: claves exactas del valor del enum (el substring dejaba pasar
    # `'BirdTypeEnum.BROILER'` sin detectar el defecto).
    claves = set(r.json().get("lots_by_type") or {})
    assert "breeder" in claves and "hatchery" in claves, claves


async def test_el_panel_del_usuario_sin_unidades_no_muestra_ninguna(http_client, kpi):
    r = await http_client.get("/api/v1/dashboard/admin", headers=_token(kpi["user_cero"]))
    assert r.status_code == 200, r.text
    assert not (r.json().get("lots_by_type") or {})


# ── Sin atajos ───────────────────────────────────────────────────────────────

async def test_llamarse_contralor_no_amplia_el_agregado(http_client, kpi, test_database_url):
    """`OD-09.a` da visibilidad de control por **política explícita**, no por el nombre.

    El rol se llama «Contralor Avícola» y tiene una sola cadena concedida. El agregado
    operacional sigue acotado: si el nombre bastara, la capacidad se saltaría desde la
    pantalla de roles.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import CompanyBusinessUnit
    from app.business_units.service import conceder_unidad

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            breeder = (await s.execute(select(CompanyBusinessUnit).where(
                CompanyBusinessUnit.company_id == kpi["empresa_a"],
                CompanyBusinessUnit.id != kpi["hab_hatchery"]))).scalars().first()
            rol = Role(name=f"{PREFIJO}Contralor Avícola-{uuid.uuid4().hex[:6]}",
                       company_id=kpi["empresa_a"], is_active=True)
            s.add(rol)
            await s.flush()
            for modulo in ("reports", "dashboard", "lots"):
                s.add(Permission(role_id=rol.id, module=modulo,
                                 action=PermissionAction.READ, scope_type="company"))
            u = User(first_name="Contra", last_name="Lor",
                     email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                     username=f"{PREFIJO}{uuid.uuid4().hex[:8]}",
                     hashed_password=hash_password("x"), company_id=kpi["empresa_a"],
                     role_id=rol.id, is_active=True)
            s.add(u)
            await s.flush()
            await conceder_unidad(s, user=u, company_business_unit=breeder)
            await s.commit()
            user_id = u.id
    finally:
        await motor.dispose()

    r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={kpi['lote_h']}",
                              headers=_token(user_id))
    assert r.status_code == 404, r.text

    panel = await http_client.get("/api/v1/dashboard/admin", headers=_token(user_id))
    assert panel.status_code == 200
    claves = set(panel.json().get("lots_by_type") or {})
    assert "hatchery" not in claves, claves


async def test_el_filtro_de_seguridad_no_altera_la_regla_de_aprobacion(http_client, kpi):
    """`§6` · `P-15` sigue excluyendo lo que no está aprobado.

    El lote tiene 10 muertes aprobadas y 500 pendientes de revisión. El indicador debe
    seguir diciendo 10: el alcance por unidad se aplica **además** de la semántica de
    aprobación, no en su lugar.

    Sin esta prueba, una implementación que reemplazara el filtro de estado por el de unidad
    pasaría desapercibida y el indicador multiplicaría por cincuenta.
    """
    r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={kpi['lote_r']}",
                              headers=_token(kpi["user_re"]))
    assert r.status_code == 200, r.text
    assert r.json()["total_deaths"] == MUERTES_REPRODUCTORA, (
        "el registro sin aprobar no puede contar")


async def test_los_contadores_del_panel_no_cuentan_eventos_ajenos(http_client, kpi):
    """`§3` · un `COUNT` filtra igual que una fila.

    El panel cuenta eventos de la empresa. Si no se acota, el usuario de reproductora ve
    cuántos eventos tiene incubadora — y con dos consultas separadas por el tiempo, cuándo
    los registra.

    Esta prueba nació de una mutación que **no** rompió nada: el acotamiento estaba, pero
    ninguna prueba lo sujetaba.
    """
    de_re = await http_client.get("/api/v1/dashboard/admin", headers=_token(kpi["user_re"]))
    de_amb = await http_client.get("/api/v1/dashboard/admin", headers=_token(kpi["user_amb"]))
    assert de_re.status_code == 200 and de_amb.status_code == 200

    total_re = de_re.json()["total_events"]
    total_amb = de_amb.json()["total_events"]
    assert total_amb > total_re, (
        f"quien alcanza dos cadenas debe contar más que quien alcanza una: "
        f"{total_amb} vs {total_re}")


async def test_el_panel_del_usuario_sin_unidades_no_cuenta_eventos(http_client, kpi):
    r = await http_client.get("/api/v1/dashboard/admin", headers=_token(kpi["user_cero"]))
    assert r.status_code == 200, r.text
    assert r.json()["total_events"] == 0
