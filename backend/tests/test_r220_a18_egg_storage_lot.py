"""R-220 · A18 (B-40) — `egg_storage` sin lote resoluble ⇒ 4xx, nunca 500.

Contexto: `R-194` reparó la herencia del lote del evento cuando el schema emite
`lot_id: None`; el residual es el caso en que **ni el hijo ni el evento** aportan
lote: el INSERT quedaría en NULL sobre una columna no nulable (500 de motor).
Este paquete exige una respuesta 4xx legible (hardening).
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

PREFIJO = "R220A18-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc_a18(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus

    motor = create_async_engine(test_database_url)
    s = async_sessionmaker(motor, expire_on_commit=False)()
    empresa = Company(name=f"{PREFIJO}{uuid.uuid4().hex[:6]}", is_active=True)
    s.add(empresa)
    await s.flush()
    unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
    hab = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades["hatchery"].id, is_enabled=True)
    s.add(hab)
    await s.flush()

    rol = Role(name=f"{PREFIJO}op-{uuid.uuid4().hex[:6]}", company_id=empresa.id, is_active=True)
    s.add(rol)
    await s.flush()
    for accion in (PermissionAction.CREATE, PermissionAction.READ):
        s.add(Permission(role_id=rol.id, module="operations", action=accion, scope_type="company"))
    await s.flush()
    user = User(first_name="OP", last_name="A18", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                username=f"{PREFIJO}op-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                company_id=empresa.id, role_id=rol.id, is_active=True)
    s.add(user)
    await s.flush()
    await conceder_unidad(s, user=user, company_business_unit=hab)

    granja = Farm(company_id=empresa.id, name=f"{PREFIJO}planta", code=f"{PREFIJO}P-{uuid.uuid4().hex[:4]}",
                  farm_type=FarmType.BREEDING, is_active=True)
    s.add(granja)
    await s.flush()
    galpon = House(farm_id=granja.id, name=f"{PREFIJO}gp", capacity=1000, is_active=True)
    s.add(galpon)
    await s.flush()
    lote = Lot(company_id=empresa.id, lot_code=f"{PREFIJO}L-{uuid.uuid4().hex[:6]}", status=LotStatus.ACTIVE,
               farm_id=granja.id, house_id=galpon.id, bird_type=BirdTypeEnum.HATCHERY)
    s.add(lote)
    await s.commit()

    yield {"empresa": empresa.id, "operador": user.id, "planta": granja.id, "galpon": galpon.id,
           "lote": lote.id, "token": _token(user.id), "url": test_database_url}

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM egg_storage WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
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


async def test_a18_egg_storage_sin_lote_resoluble_es_4xx(client, esc_a18):
    """Sin lote en el evento ni en el registro: 4xx legible (hoy: 500 del motor)."""
    cuerpo = {
        "event_type": "egg_reception_hatchery",
        "event_date": (date.today() - timedelta(days=1)).isoformat(),
        "farm_id": esc_a18["planta"], "house_id": esc_a18["galpon"],
        "egg_storage_records": [{
            "lot_id": None,
            "arrival_date": (date.today() - timedelta(days=1)).isoformat(),
            "eggs_received": 100,
        }],
    }
    r = await client.post("/api/v1/operations", headers=esc_a18["token"], json=cuerpo)
    assert r.status_code != 500, f"500 del motor: {r.text[:200]}"
    assert r.status_code in (400, 422), r.text


async def test_a18_control_con_lote_hijo_hereda_y_crea(client, esc_a18):
    """Control `R-194`: el hijo sin lote hereda el del evento ⇒ 201 (no regresión)."""
    cuerpo = {
        "lot_id": esc_a18["lote"], "event_type": "egg_reception_hatchery",
        "event_date": (date.today() - timedelta(days=1)).isoformat(),
        "farm_id": esc_a18["planta"], "house_id": esc_a18["galpon"],
        "egg_storage_records": [{
            "arrival_date": (date.today() - timedelta(days=1)).isoformat(),
            "eggs_received": 100,
        }],
        "egg_movements": [{"egg_type": "fertile", "quantity": 100}],
    }
    r = await client.post("/api/v1/operations", headers=esc_a18["token"], json=cuerpo)
    assert r.status_code == 201, r.text
