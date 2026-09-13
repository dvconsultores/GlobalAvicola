"""`R-204` · Predicado de unidad en agregados sin lote y alertas del panel.

Diseño: `specs/R-204/R-204_RED_E2E_UAT_DESIGN.md §1`.

En HEAD, los agregados **sin lote** (`/reports/kpis` bloque incubadora,
`/reports/kpis/hatchery`) suman toda la empresa — incluidas unidades no concedidas
o apagadas — y `dashboard/admin.active_alerts` calcula `_ambito` **y no lo aplica**
(`dashboard/service.py:206-242`). La doctrina `OD-16` exige `lot_id ∈ alcanzables`
en toda lectura productiva (ya vigente en operaciones, lotes y KPI por lote).

```
A: hatchery+breeder ON · lote_h(hatchery) con carga/nacimiento/descarte · lote_b(breeder)
   alerta activa en lote_h
   u_breeder: solo breeder concedida · u_all: ambas · (u_b en B con sus propios datos)
```

PREFIJO `R204-`.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R204-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc204(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Lot
    from app.operations.models import (
        BirdMovement, EggMovement, EventStatus, EventType, HatcheryParams,
        OperationalAlert, OperationalEvent,
    )

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, codes in ((a, ("hatchery", "breeder")), (b, ("hatchery", "breeder"))):
            for code in codes:
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id,
                                           is_enabled=True)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila

        def _rol(nombre, company_id):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_a = _rol("Panel", a.id)
        rol_b = _rol("PanelB", b.id)
        await s.flush()
        for rol in (rol_a, rol_b):
            for modulo in ("reports", "dashboard"):
                s.add(Permission(role_id=rol.id, module=modulo,
                                 action=PermissionAction.READ,
                                 scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca[:8], last_name="R204",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        u_breeder = _usuario(a.id, "BREEDER", rol_a)
        u_all = _usuario(a.id, "ALL", rol_a)
        u_b = _usuario(b.id, "B", rol_b)
        s.add_all([u_breeder, u_all, u_b])
        await s.flush()
        await conceder_unidad(s, user=u_breeder, company_business_unit=hab[(a.id, "breeder")])
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=u_all, company_business_unit=hab[(a.id, code)])
            await conceder_unidad(s, user=u_b, company_business_unit=hab[(b.id, code)])

        lote_h = Lot(company_id=a.id, lot_code=f"{PREFIJO}LH-{uuid.uuid4().hex[:6]}",
                     bird_type=BirdTypeEnum.HATCHERY, status="active")
        lote_b = Lot(company_id=a.id, lot_code=f"{PREFIJO}LB-{uuid.uuid4().hex[:6]}",
                     bird_type=BirdTypeEnum.BREEDER, status="active")
        lote_b2 = Lot(company_id=b.id, lot_code=f"{PREFIJO}LB2-{uuid.uuid4().hex[:6]}",
                      bird_type=BirdTypeEnum.BREEDER, status="active")
        s.add_all([lote_h, lote_b, lote_b2])
        await s.flush()

        def _evento(company_id, lote_id, tipo):
            e = OperationalEvent(company_id=company_id, lot_id=lote_id,
                                 event_type=tipo, event_date=date.today(),
                                 status=EventStatus.APPROVED,
                                 registered_by_id=(u_all.id if company_id == a.id else u_b.id),
                                 version=1, observations=f"{PREFIJO}{tipo.value}")
            s.add(e)
            return e

        e_load = _evento(a.id, lote_h.id, EventType.INCUBATION_LOAD)
        e_recv = _evento(a.id, lote_h.id, EventType.EGG_RECEPTION_HATCHERY)
        e_birth = _evento(a.id, lote_h.id, EventType.BIRTH_REGISTRATION)
        e_cull = _evento(a.id, lote_h.id, EventType.CULL_RECORDING)
        e_load_b = _evento(b.id, lote_b2.id, EventType.INCUBATION_LOAD)
        e_birth_b = _evento(b.id, lote_b2.id, EventType.BIRTH_REGISTRATION)
        await s.flush()
        s.add_all([
            HatcheryParams(event_id=e_load.id, quantity_loaded=1000),
            EggMovement(event_id=e_recv.id, egg_type="fertile", quantity=900),
            BirdMovement(event_id=e_birth.id, quantity=800),
            BirdMovement(event_id=e_cull.id, quantity=50),
            HatcheryParams(event_id=e_load_b.id, quantity_loaded=500),
            BirdMovement(event_id=e_birth_b.id, quantity=400),
        ])
        s.add(OperationalAlert(company_id=a.id, lot_id=lote_h.id,
                               alert_type="high_mortality", severity="warning",
                               message=f"{PREFIJO}alerta hatchery"))
        s.add(OperationalAlert(company_id=b.id, lot_id=lote_b2.id,
                               alert_type="high_mortality", severity="warning",
                               message=f"{PREFIJO}alerta B"))
        await s.flush()
        await s.commit()

        d = {"url": test_database_url, "a": a.id, "b": b.id,
             "u_breeder": u_breeder.id, "u_all": u_all.id, "u_b": u_b.id,
             "hab_a_hatchery": hab[(a.id, "hatchery")].id,
             "alerta_a": None}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM hatchery_params WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def test_r204_01_kpi_global_sin_hatchery_es_cero(http_client, esc204):
    """`AC-R204-01`. RED en HEAD: el bloque incubadora trae los valores del lote ajeno."""
    r = await http_client.get("/api/v1/reports/kpis", headers=_token(esc204["u_breeder"]))
    assert r.status_code == 200, r.text
    salida = r.json()["hatchery_yield"]
    assert salida["total_chicks_born"] == 0, salida
    assert salida["eggs_loaded"] == 0, salida
    assert salida["fertile_eggs"] == 0, salida


async def test_r204_02_kpi_hatchery_sin_unidad_es_vacio(http_client, esc204):
    """`AC-R204-02`. RED en HEAD: datos completos de una unidad no concedida."""
    r = await http_client.get("/api/v1/reports/kpis/hatchery",
                              headers=_token(esc204["u_breeder"]))
    assert r.status_code == 200, r.text
    salida = r.json()
    assert salida["total_chicks_born"] == 0, salida
    assert salida["eggs_loaded"] == 0, salida
    assert salida["fertile_eggs"] == 0, salida


async def test_r204_03_alertas_panel_acotadas(http_client, esc204):
    """`AC-R204-03`. RED en HEAD: la alerta del lote de hatchery aparece igualmente."""
    r = await http_client.get("/api/v1/dashboard/admin", headers=_token(esc204["u_breeder"]))
    assert r.status_code == 200, r.text
    alertas = r.json().get("active_alerts") or []
    assert alertas == [], alertas


async def test_r204_04_unidad_apagada_no_agrega(http_client, esc204):
    """`AC-R204-04`. RED en HEAD: con la unidad apagada, el agregado sigue sumando."""
    motor = create_async_engine(esc204["url"])
    async with motor.begin() as c:
        await c.execute(text(
            "UPDATE company_business_units SET is_enabled = false WHERE id = :i"),
            {"i": esc204["hab_a_hatchery"]})
    await motor.dispose()

    r = await http_client.get("/api/v1/reports/kpis/hatchery",
                              headers=_token(esc204["u_all"]))
    assert r.status_code == 200, r.text
    salida = r.json()
    assert salida["total_chicks_born"] == 0, salida
    assert salida["eggs_loaded"] == 0, salida


async def test_r204_05_control_con_unidad(http_client, esc204):
    """Control: con su unidad viva y concedida, los valores son los de hoy (verde)."""
    r = await http_client.get("/api/v1/reports/kpis/hatchery",
                              headers=_token(esc204["u_all"]))
    assert r.status_code == 200, r.text
    salida = r.json()
    assert salida["total_chicks_born"] == 800, salida
    assert salida["eggs_loaded"] == 1000, salida
    assert salida["fertile_eggs"] == 900, salida


async def test_r204_06_control_otra_empresa(http_client, esc204):
    """Control: la empresa B conserva sus propios valores (sin cruce)."""
    r = await http_client.get("/api/v1/reports/kpis/hatchery",
                              headers=_token(esc204["u_b"]))
    assert r.status_code == 200, r.text
    salida = r.json()
    assert salida["total_chicks_born"] == 400, salida
    assert salida["eggs_loaded"] == 500, salida
