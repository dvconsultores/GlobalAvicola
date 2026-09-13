"""`R-190` · control (verde en HEAD) — `BR-08` intacto tras generalizar la derivación
de ubicación del evento.

La regla no cambia (`C-09`): los `location_events` siguen exigiendo granja y galpón
 en el
backend. Estos casos prueban que el contrato servidor permanece — el RED de
 `R-190` vive en
el frontend (payload sin `house_id`); aquí sólo se fija la frontera que la
 implementación FE
**no** debe debilitar.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import days_ago, recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "BR08R190-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


def _es_br(r, regla: str) -> bool:
    return r.status_code == 400 and r.json().get("rule") == regla


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.lots.models import OpeningBalance
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House,
                                    Lot, LotStatus, ProductivePhase)

    motor = create_async_engine(test_database_url)
    datos: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for code in ("grandparent",):
            fila = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades[code].id,
                                       is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[code] = fila

        rol = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        for accion in (PermissionAction.CREATE, PermissionAction.READ,
                       PermissionAction.UPDATE):
            s.add(Permission(role_id=rol.id, module="operations", action=accion,
                             scope_type="company"))
        s.add(Permission(role_id=rol.id, module="lots", action=PermissionAction.READ,
                         scope_type="company"))
        await s.flush()

        operador = User(first_name="OP", last_name="Br08",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}OP-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=a.id,
                        role_id=rol.id, is_active=True)
        s.add(operador)
        await s.flush()
        await conceder_unidad(s, user=operador, company_business_unit=hab["grandparent"])

        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA",
                      code=f"{PREFIJO}G-{uuid.uuid4().hex[:4]}",
                      farm_type=FarmType.BREEDING, is_active=True)
        s.add(granja)
        await s.flush()
        galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON", capacity=5000,
                       is_active=True)
        s.add(galpon)
        await s.flush()

        fase = (await s.execute(select(ProductivePhase).limit(1))).scalar_one_or_none()
        if fase is None:
            fase = ProductivePhase(name=f"{PREFIJO}F", code=f"{PREFIJO[:3]}{uuid.uuid4().hex[:4]}",
                                   order=1, duration_days=10)
            s.add(fase)
            await s.flush()

        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}L-{uuid.uuid4().hex[:6]}",
                   bird_type=BirdTypeEnum.GRANDPARENT, status=LotStatus.ACTIVE,
                   farm_id=granja.id, house_id=None)
        s.add(lote)
        await s.flush()
        s.add(OpeningBalance(lot_id=lote.id, activation_date=days_ago(60),
                             phase_at_activation_id=fase.id,
                             initial_male_count=500, initial_female_count=500,
                             is_manual_activation=True, activated_by_id=operador.id))
        await s.commit()

        datos = {"lote": lote.id, "granja": granja.id, "galpon": galpon.id,
                 "operador": operador.id, "url": test_database_url}
    yield datos

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM operational_alerts WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM evidences WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM hatchery_params WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM inspection_details WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM opening_balances WHERE lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN "
            "(SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN "
            "(SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def _crear(http_client, esc, cuerpo):
    return await http_client.post("/api/v1/operations",
                                  headers=_token(esc["operador"]), json=cuerpo)


async def _eventos(esc) -> int:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return int((await s.execute(text(
                "SELECT count(*) FROM operational_events WHERE lot_id = :l"),
                {"l": esc["lote"]})).scalar() or 0)
    finally:
        await motor.dispose()


async def test_r190_01_distribucion_sin_house_id_es_400_br08(http_client, esc):
    antes = await _eventos(esc)
    r = await _crear(http_client, esc, {
        "event_type": "bird_distribution", "event_date": recent_event_date(),
        "lot_id": esc["lote"], "farm_id": esc["granja"],
        "bird_movements": [{"sex": "male", "quantity": 40}],
    })
    assert _es_br(r, "BR-08"), r.text
    assert await _eventos(esc) == antes, "una denegación no deja fila"


async def test_r190_02_salida_sin_house_id_es_400_br08(http_client, esc):
    antes = await _eventos(esc)
    r = await _crear(http_client, esc, {
        "event_type": "bird_exit", "event_date": recent_event_date(),
        "lot_id": esc["lote"], "farm_id": esc["granja"],
        "bird_movements": [{"sex": "male", "quantity": 10}],
    })
    assert _es_br(r, "BR-08"), r.text
    assert await _eventos(esc) == antes


async def test_r190_03_recoleccion_sin_house_id_es_400_br08(http_client, esc):
    antes = await _eventos(esc)
    r = await _crear(http_client, esc, {
        "event_type": "egg_collection", "event_date": recent_event_date(),
        "lot_id": esc["lote"], "farm_id": esc["granja"],
        "egg_movements": [{"egg_type": "fertile", "quantity": 100}],
    })
    assert _es_br(r, "BR-08"), r.text
    assert await _eventos(esc) == antes


async def test_r190_04_con_ubicacion_declarada_es_201(http_client, esc):
    """Con `farm_id` y `house_id` declarados, la puerta `BR-08` se abre (control)."""
    r = await _crear(http_client, esc, {
        "event_type": "bird_distribution", "event_date": recent_event_date(),
        "lot_id": esc["lote"], "farm_id": esc["granja"], "house_id": esc["galpon"],
        "bird_movements": [{"sex": "male", "quantity": 40}],
    })
    assert r.status_code == 201, r.text
