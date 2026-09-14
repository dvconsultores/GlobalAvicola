"""R-197 · Bandeja por estado, acciones por evento (contract tests).

RED en HEAD:
- `/review/pending` ignora `status` (fijo registered|pending_review) y no acepta
  `registered_by_id`; un `status` inválido no es 422.
- `GET /review/events/{id}/actions` no existe (404 de ruta).

Fixture calcada del patrón probado de review (`test_review_decision_concurrency`):
roles con `Permission(role_id, module, action, scope_type)`, usuarios con
`hashed_password`, grants de BU vía `conceder_unidad`, eventos sembrados por
inserción directa con estados distinguibles.
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
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R197-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc_r197(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import Company, Farm, FarmType, House, Lot, LotStatus
    from app.operations.models import EventStatus, OperationalEvent
    from app.review.models import ApprovalAction

    motor = create_async_engine(test_database_url)
    s = async_sessionmaker(motor, expire_on_commit=False)()
    empresa = Company(name=f"{PREFIJO}{uuid.uuid4().hex[:6]}", is_active=True)
    s.add(empresa)
    await s.flush()
    unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
    hab = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades["breeder"].id, is_enabled=True)
    s.add(hab)
    await s.flush()

    PA = PermissionAction
    revisar = [("review", PA.REVIEW), ("review", PA.READ), ("operations", PA.READ)]

    role_rev = Role(name=f"{PREFIJO}rev-{uuid.uuid4().hex[:6]}", company_id=empresa.id, is_active=True)
    role_vacio = Role(name=f"{PREFIJO}vacio-{uuid.uuid4().hex[:6]}", company_id=empresa.id, is_active=True)
    s.add_all([role_rev, role_vacio])
    await s.flush()
    for modulo, accion in revisar:
        s.add(Permission(role_id=role_rev.id, module=modulo, action=accion, scope_type="company"))
    await s.flush()

    def _usuario(marca: str, rol: Role) -> User:
        return User(first_name=marca, last_name="R197", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                    username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                    company_id=empresa.id, role_id=rol.id, is_active=True)

    op = _usuario("OP", role_rev)
    rev = _usuario("REV", role_rev)
    np = _usuario("NP", role_vacio)
    s.add_all([op, rev, np])
    await s.flush()
    for u in (op, rev, np):
        await conceder_unidad(s, user=u, company_business_unit=hab)

    granja = Farm(company_id=empresa.id, name=f"{PREFIJO}granja", code=f"{PREFIJO}G-{uuid.uuid4().hex[:4]}",
                  farm_type=FarmType.BREEDING, is_active=True)
    s.add(granja)
    await s.flush()
    galpon = House(farm_id=granja.id, name=f"{PREFIJO}galpon", capacity=1000, is_active=True)
    s.add(galpon)
    await s.flush()
    lote = Lot(company_id=empresa.id, lot_code=f"{PREFIJO}L-{uuid.uuid4().hex[:6]}", status=LotStatus.ACTIVE,
               farm_id=granja.id, house_id=galpon.id)
    s.add(lote)
    await s.flush()

    eventos: dict[str, OperationalEvent] = {}
    for estado in (EventStatus.REGISTERED, EventStatus.PENDING_REVIEW,
                   EventStatus.IN_REVIEW, EventStatus.RETURNED):
        ev = OperationalEvent(company_id=empresa.id, event_type="mortality_recording", event_date=date.today() - timedelta(days=7),
                              lot_id=lote.id, farm_id=granja.id, house_id=galpon.id,
                              business_unit_id=hab.id,
                              registered_by_id=op.id, status=estado)
        s.add(ev)
        await s.flush()
        eventos[estado.value] = ev

    s.add(ApprovalAction(event_id=eventos["in_review"].id, action_type="started_review",
                         user_id=rev.id))
    await s.flush()
    await s.commit()

    yield {
        "url": test_database_url, "empresa": empresa, "op": op, "rev": rev, "np": np,
        "eventos": eventos, "lote": lote, "token_rev": _token(rev.id), "token_np": _token(np.id),
    }

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
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


async def test_r197_01_status_in_review_devuelve_solo_in_review(client, esc_r197):
    r = await client.get("/api/v1/review/pending?status=in_review", headers=esc_r197["token_rev"])
    assert r.status_code == 200, r.text
    ids = {e["id"] for e in r.json()["events"]}
    assert ids == {esc_r197["eventos"]["in_review"].id}, ids


async def test_r197_02_sin_status_conserva_el_defecto(client, esc_r197):
    r = await client.get("/api/v1/review/pending", headers=esc_r197["token_rev"])
    assert r.status_code == 200, r.text
    ids = {e["id"] for e in r.json()["events"]}
    assert ids == {esc_r197["eventos"]["registered"].id, esc_r197["eventos"]["pending_review"].id}, ids


async def test_r197_03_status_invalido_es_422(client, esc_r197):
    r = await client.get("/api/v1/review/pending?status=foo", headers=esc_r197["token_rev"])
    assert r.status_code == 422, r.text


async def test_r197_04_registered_by_id_filtra(client, esc_r197):
    r = await client.get(
        f"/api/v1/review/pending?status=in_review,returned&registered_by_id={esc_r197['op'].id}",
        headers=esc_r197["token_rev"])
    assert r.status_code == 200, r.text
    ids = {e["id"] for e in r.json()["events"]}
    assert ids == {esc_r197["eventos"]["in_review"].id, esc_r197["eventos"]["returned"].id}, ids


async def test_r197_05_acciones_por_evento(client, esc_r197):
    ev = esc_r197["eventos"]["in_review"]
    r = await client.get(f"/api/v1/review/events/{ev.id}/actions", headers=esc_r197["token_rev"])
    assert r.status_code == 200, r.text
    acciones = r.json()
    assert any(a["action_type"] == "started_review" and a.get("batch_id") is None for a in acciones), acciones


async def test_r197_06_acciones_sin_review_read_403(client, esc_r197):
    ev = esc_r197["eventos"]["in_review"]
    r = await client.get(f"/api/v1/review/events/{ev.id}/actions", headers=esc_r197["token_np"])
    assert r.status_code == 403, r.text
