"""R-220 · A8 (C#33) — los listados exponen `X-Total-Count` (paginación real).

RED en HEAD: `/lots` y `/operations` calculan el total y lo **descartan**; el
cliente solo puede pedir «los primeros 100» sin saber cuántos hay.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R220A8-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc_a8(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus
    from app.operations.models import EventStatus, OperationalEvent

    motor = create_async_engine(test_database_url)
    s = async_sessionmaker(motor, expire_on_commit=False)()
    empresa = Company(name=f"{PREFIJO}{uuid.uuid4().hex[:6]}", is_active=True)
    s.add(empresa)
    await s.flush()
    unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
    hab = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades["broiler"].id, is_enabled=True)
    s.add(hab)
    await s.flush()

    rol = Role(name=f"{PREFIJO}op-{uuid.uuid4().hex[:6]}", company_id=empresa.id, is_active=True)
    s.add(rol)
    await s.flush()
    for modulo in ("lots", "operations"):
        s.add(Permission(role_id=rol.id, module=modulo, action=PermissionAction.READ, scope_type="company"))
    await s.flush()
    user = User(first_name="OP", last_name="A8", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                username=f"{PREFIJO}op-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                company_id=empresa.id, role_id=rol.id, is_active=True)
    s.add(user)
    await s.flush()
    await conceder_unidad(s, user=user, company_business_unit=hab)

    granja = Farm(company_id=empresa.id, name=f"{PREFIJO}granja", code=f"{PREFIJO}G-{uuid.uuid4().hex[:4]}",
                  farm_type=FarmType.BREEDING, is_active=True)
    s.add(granja)
    await s.flush()
    galpon = House(farm_id=granja.id, name=f"{PREFIJO}galpon", capacity=1000, is_active=True)
    s.add(galpon)
    await s.flush()
    lote1 = Lot(company_id=empresa.id, lot_code=f"{PREFIJO}L1-{uuid.uuid4().hex[:6]}", status=LotStatus.ACTIVE,
                farm_id=granja.id, house_id=galpon.id, bird_type=BirdTypeEnum.BROILER)
    lote2 = Lot(company_id=empresa.id, lot_code=f"{PREFIJO}L2-{uuid.uuid4().hex[:6]}", status=LotStatus.ACTIVE,
                farm_id=granja.id, house_id=galpon.id, bird_type=BirdTypeEnum.BROILER)
    s.add_all([lote1, lote2])
    await s.flush()
    for i in range(3):
        s.add(OperationalEvent(company_id=empresa.id, event_type="mortality_recording",
                               event_date=date.today() - timedelta(days=5 - i),
                               lot_id=lote1.id, farm_id=granja.id, house_id=galpon.id,
                               business_unit_id=hab.id, registered_by_id=user.id,
                               status=EventStatus.APPROVED))
    await s.commit()

    yield {"lote1": lote1.id, "lote2": lote2.id, "token": _token(user.id), "url": test_database_url}

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def test_a8_lots_expone_x_total_count(client, esc_a8):
    r = await client.get("/api/v1/lots?limit=1", headers=esc_a8["token"])
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1
    assert r.headers.get("x-total-count") == "2", dict(r.headers)


async def test_a8_operations_expone_x_total_count(client, esc_a8):
    r = await client.get(f"/api/v1/operations?lot_id={esc_a8['lote1']}&limit=2", headers=esc_a8["token"])
    assert r.status_code == 200, r.text
    assert len(r.json()) == 2
    assert r.headers.get("x-total-count") == "3", dict(r.headers)
