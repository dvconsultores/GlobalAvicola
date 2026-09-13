"""`GA-REM-041 §1.2` · `R-165` · el plano de revisión exige la habilitación de la unidad a la autoridad global (`OD-19 §13`).

    Empresa A   breeder ON · hatchery OFF · lote LR (breeder) · LH (hatchery)
                eventos en LH: PENDING_REVIEW · IN_REVIEW ×2 · CORRECTED ×2 (y sus gemelos en LR como control)
    REVISOR     review:review/read · approvals:approve/reject · operations:read · breeder + hatchery (histórica)
    ACCESO      Administrador de Accesos        GLOBAL ("*", all)
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "RBU-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Lot, LotStatus
    from app.operations.models import EventStatus, EventType, OperationalEvent

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True, approval_levels=2)
        s.add(a)
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for code, on in (("breeder", True), ("hatchery", False)):
            fila = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[code] = fila
        PA = PermissionAction

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        roles = {
            "revisor": _rol("Rev", a.id, [("review", PA.REVIEW), ("review", PA.READ), ("approvals", PA.APPROVE), ("approvals", PA.REJECT), ("operations", PA.READ)]),
            "operador": _rol("Op", a.id, [("operations", PA.CREATE), ("operations", PA.READ)]),
            "acceso": _rol("Acceso", a.id, [("business_units", PA.READ), ("business_units", PA.CREATE), ("business_units", PA.UPDATE), ("business_units", PA.DELETE)]),
            "global": _rol("Global", None, []),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Rbu", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {"revisor": _usuario(a.id, "REV", roles["revisor"][0]), "operador": _usuario(a.id, "OP", roles["operador"][0]),
             "acceso": _usuario(a.id, "ACC", roles["acceso"][0]), "global": _usuario(None, "GLOBAL", roles["global"][0])}
        s.add_all(u.values())
        await s.flush()
        for k in ("revisor", "operador"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab["breeder"])
            await conceder_unidad(s, user=u[k], company_business_unit=hab["hatchery"])
        lr = Lot(company_id=a.id, lot_code=f"{PREFIJO}LR-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER, status=LotStatus.ACTIVE)
        lh = Lot(company_id=a.id, lot_code=f"{PREFIJO}LH-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.HATCHERY, status=LotStatus.ACTIVE)
        s.add_all([lr, lh])
        await s.flush()
        ev = {}
        for lote, marca in ((lr, "r"), (lh, "h")):
            for clave, estado in (("pend", EventStatus.PENDING_REVIEW), ("rev1", EventStatus.IN_REVIEW), ("rev2", EventStatus.IN_REVIEW),
                                  ("corr1", EventStatus.CORRECTED), ("corr2", EventStatus.CORRECTED)):
                e = OperationalEvent(company_id=a.id, lot_id=lote.id, event_type=EventType.FARM_INSPECTION, event_date=date.today(),
                                     status=estado, registered_by_id=u["operador"].id, version=1, observations=f"{PREFIJO}{marca}-{clave}")
                s.add(e)
                ev[f"{marca}_{clave}"] = e
        await s.flush()
        await s.commit()
        d = {"a": a.id, "url": test_database_url}
        d.update({k: v.id for k, v in u.items()})
        d.update({f"ev_{k}": v.id for k, v in ev.items()})
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def _estado(esc, ev):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return str((await s.execute(text("SELECT status FROM operational_events WHERE id = :e"), {"e": ev})).scalar()).lower().split(".")[-1]
    finally:
        await motor.dispose()


async def _acciones(http_client, esc, cab, marca):
    obs = f"{PREFIJO}observación suficientemente larga"
    return {
        "start": await http_client.post(f"/api/v1/review/start/{esc[f'ev_{marca}_pend']}", headers=cab),
        "return": await http_client.post("/api/v1/review/return", headers=cab, json={"event_id": esc[f"ev_{marca}_rev1"], "observations": obs}),
        "complete": await http_client.post("/api/v1/review/complete", headers=cab, json={"event_id": esc[f"ev_{marca}_rev2"]}),
        "approve": await http_client.post("/api/v1/approvals/approve", headers=cab, json={"event_id": esc[f"ev_{marca}_corr1"]}),
        "reject": await http_client.post("/api/v1/approvals/reject", headers=cab, json={"event_id": esc[f"ev_{marca}_corr2"], "observations": obs}),
    }


async def test_165_01_la_autoridad_global_situada_no_revisa_ni_decide_sobre_unidad_apagada(http_client, esc):
    r = await _acciones(http_client, esc, _token(esc["global"], esc["a"]), "h")
    for accion, resp in r.items():
        # `OD-16` (`9ffc5ec`): frontera productiva fail-closed — 404 sin enumerar el recurso.
        assert resp.status_code == 404, (accion, resp.text)
    for clave, estado in (("pend", "pending_review"), ("rev1", "in_review"), ("rev2", "in_review"), ("corr1", "corrected"), ("corr2", "corrected")):
        assert await _estado(esc, esc[f"ev_h_{clave}"]) == estado, "cero cambios"


async def test_165_02_control_la_autoridad_global_situada_sigue_operando_la_unidad_habilitada(http_client, esc):
    r = await _acciones(http_client, esc, _token(esc["global"], esc["a"]), "r")
    for accion, resp in r.items():
        assert resp.status_code == 200, (accion, resp.text)


async def test_165_03_control_el_actor_de_empresa_con_concesion_historica_no_alcanza_la_unidad_apagada(http_client, esc):
    r = await _acciones(http_client, esc, _token(esc["revisor"]), "h")
    for accion, resp in r.items():
        assert resp.status_code == 404, (accion, resp.text)
    r = await _acciones(http_client, esc, _token(esc["revisor"]), "r")
    assert r["start"].status_code == 200 and r["approve"].status_code == 200, "control positivo"


async def test_165_04_control_la_autoridad_global_sin_contexto_falla_cerrada(http_client, esc):
    r = await _acciones(http_client, esc, _token(esc["global"]), "h")
    for accion, resp in r.items():
        assert resp.status_code == 404, (accion, resp.text)


async def test_165_05_control_el_plano_de_control_sigue_administrando_la_unidad_apagada(http_client, esc):
    cab = _token(esc["acceso"])
    r = await http_client.get("/api/v1/business-units", headers=cab)
    assert r.status_code == 200 and {f["code"]: f["is_enabled"] for f in r.json()}["hatchery"] is False
    r = await http_client.patch("/api/v1/business-units/breeder/disable", headers=cab)
    assert r.status_code == 200 and r.json()["is_enabled"] is False
