"""`GA-REM-007` enmienda A · `R-143` · quien corrige (o rechaza) no aprueba el mismo registro (`docs/12 R2`, `OD-17.b`).

Se siembra la historia (`correction_logs`, `approval_actions`) para medir la regla del aprobador sin depender de la
continuidad de `R-135`. `require_segregation` se deja por defecto (`True`) salvo en la prueba de `RR-03`.

    Empresa A (approval_levels=2)  breeder ON · lote LR
    OP        registra (operations:create/read/update)
    C1        corrige y aprueba (corrections:correct · approvals:approve/reject · review:review)
    D         aprueba (approvals:approve · review:review)
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

PREFIJO = "SEGR-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.corrections.models import CorrectionLog
    from app.masters.models import BirdTypeEnum, Company, Lot, LotStatus
    from app.operations.models import EventStatus, EventType, OperationalEvent
    from app.review.models import ActionType, ApprovalAction

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True, approval_levels=2)
        s.add(a)
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades["breeder"].id, is_enabled=True)
        s.add(hab)
        await s.flush()
        PA = PermissionAction

        def _rol(nombre, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
            s.add(r)
            return r, permisos

        roles = {
            "op": _rol("Op", [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE)]),
            "c1": _rol("C1", [("corrections", PA.CORRECT), ("corrections", PA.READ), ("approvals", PA.APPROVE), ("approvals", PA.REJECT), ("review", PA.REVIEW), ("review", PA.READ), ("operations", PA.READ)]),
            "d": _rol("D", [("approvals", PA.APPROVE), ("review", PA.REVIEW), ("operations", PA.READ)]),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        await s.flush()

        def _usuario(marca, rol):
            return User(first_name=marca, last_name="Segr", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=a.id, role_id=rol.id, is_active=True)

        u = {"op": _usuario("OP", roles["op"][0]), "c1": _usuario("C1", roles["c1"][0]), "d": _usuario("D", roles["d"][0])}
        s.add_all(u.values())
        await s.flush()
        for usuario in u.values():
            await conceder_unidad(s, user=usuario, company_business_unit=hab)
        lr = Lot(company_id=a.id, lot_code=f"{PREFIJO}LR-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER, status=LotStatus.ACTIVE)
        s.add(lr)
        await s.flush()

        def _evento(estado):
            return OperationalEvent(company_id=a.id, lot_id=lr.id, event_type=EventType.FARM_INSPECTION, event_date=date.today(),
                                    status=estado, registered_by_id=u["op"].id, version=1, observations=f"{PREFIJO}{estado.value}")

        ev = {"g01": _evento(EventStatus.CORRECTED), "g02": _evento(EventStatus.IN_REVIEW), "g03": _evento(EventStatus.IN_REVIEW),
              "g04": _evento(EventStatus.CORRECTED), "g05": _evento(EventStatus.IN_REVIEW), "g06": _evento(EventStatus.IN_REVIEW)}
        s.add_all(ev.values())
        await s.flush()
        # g04: rechazado por C1 en el pasado, corregido después por D → hoy CORRECTED
        s.add(ApprovalAction(event_id=ev["g04"].id, user_id=u["c1"].id, action_type=ActionType.REJECTED, observations=f"{PREFIJO}rechazo previo de C1"))
        s.add(CorrectionLog(event_id=ev["g04"].id, field_name="observations", original_value="x", corrected_value="y",
                            corrected_by_id=u["d"].id, reason=f"{PREFIJO}corrección de D"))
        # g06: corregido por C1 (historia) y aún en revisión; la empresa de un nivel se configura en la prueba
        s.add(CorrectionLog(event_id=ev["g06"].id, field_name="observations", original_value="x", corrected_value="y",
                            corrected_by_id=u["c1"].id, reason=f"{PREFIJO}corrección de C1"))
        await s.flush()
        await s.commit()
        d = {"a": a.id, "lr": lr.id, "rol_c1": roles["c1"][0].id, "url": test_database_url}
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
            "DELETE FROM approval_steps WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
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


async def _sql(esc, sql, **params):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(sql), params)).all()
    finally:
        await motor.dispose()


async def _estado(esc, ev):
    return str((await _sql(esc, "SELECT status FROM operational_events WHERE id = :e", e=ev))[0][0]).lower().split(".")[-1]


async def _aprobar(http_client, esc, actor, ev):
    return await http_client.post("/api/v1/approvals/approve", headers=_token(esc[actor]), json={"event_id": esc[ev]})


async def _corregir(http_client, esc, actor, ev):
    return await http_client.post("/api/v1/corrections", headers=_token(esc[actor]),
                                  json={"event_id": esc[ev], "field_name": "observations", "corrected_value": f"{PREFIJO}v2",
                                        "reason": f"{PREFIJO}error de digitación"})


async def _es_br14(r):
    return r.status_code == 403 and "BR-14" in r.text


async def test_g01_control_un_tercero_aprueba(http_client, esc):
    r = await _aprobar(http_client, esc, "d", "ev_g01")
    assert r.status_code == 200, r.text
    assert await _estado(esc, esc["ev_g01"]) == "approved"


async def test_g02_quien_corrige_no_aprueba_el_mismo_registro(http_client, esc):
    assert (await _corregir(http_client, esc, "c1", "ev_g02")).status_code == 201
    r = await _aprobar(http_client, esc, "c1", "ev_g02")
    assert await _es_br14(r), r.text
    assert await _estado(esc, esc["ev_g02"]) == "corrected"
    assert (await _sql(esc, "SELECT approved_by_id FROM operational_events WHERE id = :e", e=esc["ev_g02"]))[0][0] is None


async def test_g03_control_corrige_uno_y_aprueba_otro(http_client, esc):
    assert (await _corregir(http_client, esc, "c1", "ev_g03")).status_code == 201
    r = await _aprobar(http_client, esc, "d", "ev_g03")
    assert r.status_code == 200, r.text


async def test_g04_quien_rechazo_no_aprueba_el_reenvio(http_client, esc):
    r = await _aprobar(http_client, esc, "c1", "ev_g04")
    assert await _es_br14(r), r.text
    assert await _estado(esc, esc["ev_g04"]) == "corrected"
    # D corrigió ese registro: tampoco (R2). Un tercero limpio sí.
    r = await _aprobar(http_client, esc, "d", "ev_g04")
    assert await _es_br14(r), r.text


async def test_g05_rr03_sin_segregacion_configurada_el_corrector_aprueba(http_client, esc):
    from app.review.models import ApprovalStep
    motor = create_async_engine(esc["url"])
    async with async_sessionmaker(motor)() as s:
        s.add(ApprovalStep(company_id=esc["a"], step_order=1, name=f"{PREFIJO}Aprobación", role_id=esc["rol_c1"],
                           can_correct=True, can_approve=True, can_reject=True, require_segregation=False))
        await s.commit()
    await motor.dispose()
    assert (await _corregir(http_client, esc, "c1", "ev_g05")).status_code == 201
    r = await _aprobar(http_client, esc, "c1", "ev_g05")
    assert r.status_code == 200, r.text


async def test_g06_completar_la_revision_con_un_nivel_tampoco_lo_aprueba_quien_corrigio(http_client, esc):
    motor = create_async_engine(esc["url"])
    async with motor.begin() as c:
        await c.execute(text("UPDATE companies SET approval_levels = 1 WHERE id = :a"), {"a": esc["a"]})
    await motor.dispose()
    r = await http_client.post("/api/v1/review/complete", headers=_token(esc["c1"]), json={"event_id": esc["ev_g06"]})
    assert await _es_br14(r), r.text
    assert await _estado(esc, esc["ev_g06"]) == "in_review", "AC-G07: cero cambios"
