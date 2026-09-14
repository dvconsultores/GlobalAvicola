"""R-218 · `GET /reports/lot/{id}/weekly` — agregado por semana (opción A).

RED en HEAD: la ruta no existe ⇒ 404. La lista de `/operations` no expone
sublistas (`OperationalEventRead` aligerado), de modo que la vista semanal del
lote y las series de reportes quedan vacías/planas (C#4).
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

PREFIJO = "R218-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc_r218(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import Company, Farm, FarmType, House, Lot, LotStatus
    from app.operations.models import BirdMovement, EventStatus, FeedMovement, OperationalEvent

    motor = create_async_engine(test_database_url)
    s = async_sessionmaker(motor, expire_on_commit=False)()

    def _rol(company_id, modulo_acciones):
        r = Role(name=f"{PREFIJO}{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
        s.add(r)
        return r

    unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}

    empresa = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
    empresa_b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
    s.add_all([empresa, empresa_b])
    await s.flush()

    hab_a = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades["breeder"].id, is_enabled=True)
    hab_b = CompanyBusinessUnit(company_id=empresa_b.id, business_unit_id=unidades["breeder"].id, is_enabled=True)
    s.add_all([hab_a, hab_b])
    await s.flush()

    PA = PermissionAction
    rol_rev = _rol(empresa.id, None)
    rol_lect = _rol(empresa.id, None)
    rol_rev_b = _rol(empresa_b.id, None)
    await s.flush()
    for modulo, accion in (("reports", PA.READ), ("operations", PA.READ)):
        s.add(Permission(role_id=rol_rev.id, module=modulo, action=accion, scope_type="company"))
    s.add(Permission(role_id=rol_lect.id, module="operations", action=PA.READ, scope_type="company"))
    for modulo, accion in (("reports", PA.READ), ("operations", PA.READ)):
        s.add(Permission(role_id=rol_rev_b.id, module=modulo, action=accion, scope_type="company"))
    await s.flush()

    def _usuario(marca, rol, company_id):
        return User(first_name=marca, last_name="R218", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                    username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                    company_id=company_id, role_id=rol.id, is_active=True)

    rev = _usuario("REV", rol_rev, empresa.id)
    lect = _usuario("LECT", rol_lect, empresa.id)
    rev_b = _usuario("REVB", rol_rev_b, empresa_b.id)
    s.add_all([rev, lect, rev_b])
    await s.flush()
    await conceder_unidad(s, user=rev, company_business_unit=hab_a)
    await conceder_unidad(s, user=lect, company_business_unit=hab_a)
    await conceder_unidad(s, user=rev_b, company_business_unit=hab_b)

    granja = Farm(company_id=empresa.id, name=f"{PREFIJO}granja", code=f"{PREFIJO}G-{uuid.uuid4().hex[:4]}",
                  farm_type=FarmType.BREEDING, is_active=True)
    granja_b = Farm(company_id=empresa_b.id, name=f"{PREFIJO}granjaB", code=f"{PREFIJO}GB-{uuid.uuid4().hex[:4]}",
                    farm_type=FarmType.BREEDING, is_active=True)
    s.add_all([granja, granja_b])
    await s.flush()
    galpon = House(farm_id=granja.id, name=f"{PREFIJO}galpon", capacity=1000, is_active=True)
    galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}galponB", capacity=1000, is_active=True)
    s.add_all([galpon, galpon_b])
    await s.flush()
    lote = Lot(company_id=empresa.id, lot_code=f"{PREFIJO}L-{uuid.uuid4().hex[:6]}", status=LotStatus.ACTIVE,
               farm_id=granja.id, house_id=galpon.id, bird_type="breeder")
    lote_b = Lot(company_id=empresa_b.id, lot_code=f"{PREFIJO}LB-{uuid.uuid4().hex[:6]}", status=LotStatus.ACTIVE,
                 farm_id=granja_b.id, house_id=galpon_b.id, bird_type="breeder")
    s.add_all([lote, lote_b])
    await s.flush()

    def _evento(lot, farm, house, bu, tipo, agua=None, dias=7):
        return OperationalEvent(company_id=lot.company_id, event_type=tipo,
                                event_date=date.today() - timedelta(days=dias),
                                lot_id=lot.id, farm_id=farm.id, house_id=house.id,
                                business_unit_id=bu.id, registered_by_id=rev.id,
                                status=EventStatus.APPROVED, water_liters=agua)

    e_mort = _evento(lote, granja, galpon, hab_a, "mortality_recording", agua=500.0)
    e_feed = _evento(lote, granja, galpon, hab_a, "feed_registration", agua=200.0)
    e_peso = _evento(lote, granja, galpon, hab_a, "weight_recording")
    s.add_all([e_mort, e_feed, e_peso])
    await s.flush()
    s.add_all([
        BirdMovement(event_id=e_mort.id, sex="mixed", quantity=30, week_number=1),
        FeedMovement(event_id=e_feed.id, quantity_kg=100.0, week_number=1),
        BirdMovement(event_id=e_peso.id, sex="mixed", quantity=0, avg_weight=1500.0, week_number=2),
    ])
    await s.commit()

    yield {
        "url": test_database_url, "lote": lote, "lote_b": lote_b,
        "token_rev": _token(rev.id), "token_lect": _token(lect.id), "token_rev_b": _token(rev_b.id),
    }

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM feed_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
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


async def test_r218_01_serie_semanal_del_lote(client, esc_r218):
    r = await client.get(f"/api/v1/reports/lot/{esc_r218['lote'].id}/weekly", headers=esc_r218["token_rev"])
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    body = r.json()
    semanas = {s["week"]: s for s in body["weeks"]}
    assert semanas[1]["mortality"] == 30, semanas
    assert float(semanas[1]["feed_kg"]) == 100.0, semanas
    assert float(semanas[1]["water_l"]) == 700.0, semanas
    assert float(semanas[2]["weight_g"]) == 1500.0, semanas


async def test_r218_02_lote_ajeno_404(client, esc_r218):
    r = await client.get(f"/api/v1/reports/lot/{esc_r218['lote'].id}/weekly", headers=esc_r218["token_rev_b"])
    assert r.status_code == 404, r.text


async def test_r218_03_sin_reports_read_403(client, esc_r218):
    r = await client.get(f"/api/v1/reports/lot/{esc_r218['lote'].id}/weekly", headers=esc_r218["token_lect"])
    assert r.status_code == 403, r.text
