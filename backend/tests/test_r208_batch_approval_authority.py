"""`R-208` · Autoridad de aprobación **por lote** alineada con la unitaria.

Diseño: `audit/ga-claude-final-audit/specs/R-208/R-208_RED_E2E_UAT_DESIGN.md §1`.

Las rutas unitarias (`/approvals/approve|reject`) exigen `approvals:approve|reject`;
las de lote piden `review:review` (`review/router.py:143-160`) — un revisor sin la
capacidad de aprobar **aprueba** por lote (200) mientras la unitaria le da 403.

```
R1 (review:review, sin approvals:*)  → batch-approve ⇒ 403 y estados intactos (hoy 200)
A1 (approvals:approve/reject)        → batch-approve ⇒ 200 (control)
R1                                   → batch-reject  ⇒ 403 (hoy 200)
A1 que rechazó e1                    → batch-approve [e1,e2] ⇒ denegación por evento,
                                       e2 intacto (control BR-14/R-143)
```

PREFIJO `R208-`.
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
import app.notifications.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R208-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc208(test_database_url):
    """Empresa A (broiler ON) · lotes LR · eventos CORRECTED ×2 (registrados por OP).

    ```
    revisor    review:review/read · operations:read            (sin approvals:*)
    aprobador  review:review/read · approvals:approve/reject · operations:read
    operador   operations:create/read                          (tercero: BR-14)
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Lot, LotStatus
    from app.operations.models import EventStatus, EventType, OperationalEvent

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True,
                    approval_levels=2)
        s.add(a)
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades["broiler"].id,
                                  is_enabled=True)
        s.add(hab)
        await s.flush()
        PA = PermissionAction

        def _rol(nombre, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=a.id, is_active=True)
            s.add(r)
            return r, permisos

        roles = {
            "revisor": _rol("Rev", [("review", PA.REVIEW), ("review", PA.READ),
                                    ("operations", PA.READ)]),
            "aprobador": _rol("Apr", [("review", PA.REVIEW), ("review", PA.READ),
                                      ("approvals", PA.APPROVE), ("approvals", PA.REJECT),
                                      ("operations", PA.READ)]),
            "operador": _rol("Op", [("operations", PA.CREATE), ("operations", PA.READ)]),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion,
                                 scope_type="company"))
        await s.flush()

        def _usuario(marca, rol):
            return User(first_name=marca, last_name="R208",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=a.id, role_id=rol.id, is_active=True)

        u = {"revisor": _usuario("REV", roles["revisor"][0]),
             "aprobador": _usuario("APR", roles["aprobador"][0]),
             "operador": _usuario("OP", roles["operador"][0])}
        s.add_all(u.values())
        await s.flush()
        for k in ("revisor", "aprobador", "operador"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab)

        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}L-{uuid.uuid4().hex[:6]}",
                   bird_type=BirdTypeEnum.BROILER, status=LotStatus.ACTIVE)
        s.add(lote)
        await s.flush()
        ev = {}
        for clave in ("e1", "e2"):
            e = OperationalEvent(company_id=a.id, lot_id=lote.id,
                                 event_type=EventType.FARM_INSPECTION,
                                 event_date=date.today(),
                                 status=EventStatus.CORRECTED,
                                 registered_by_id=u["operador"].id, version=1,
                                 observations=f"{PREFIJO}{clave}")
            s.add(e)
            ev[clave] = e
        await s.flush()
        await s.commit()
        d = {"a": a.id, "url": test_database_url}
        d.update({f"u_{k}": v.id for k, v in u.items()})
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
            return str((await s.execute(
                text("SELECT status FROM operational_events WHERE id = :e"),
                {"e": ev})).scalar()).lower().split(".")[-1]
    finally:
        await motor.dispose()


async def test_r208_01_revisor_sin_permiso_no_aprueba_en_lote(http_client, esc208):
    """`AC-R208-01`: `review:review` sin `approvals:approve` ⇒ 403 y cero cambios.

    RED en HEAD: 200 — la puerta de lote no exige la capacidad de aprobar.
    """
    resp = await http_client.post(
        "/api/v1/approvals/batch-approve",
        headers=_token(esc208["u_revisor"]),
        json={"event_ids": [esc208["ev_e1"], esc208["ev_e2"]]},
    )
    assert resp.status_code == 403, resp.text
    assert "approvals:approve" in resp.text
    assert await _estado(esc208, esc208["ev_e1"]) == "corrected"
    assert await _estado(esc208, esc208["ev_e2"]) == "corrected"


async def test_r208_02_aprobador_aprueba_en_lote(http_client, esc208):
    """`AC-R208-02` (control): con `approvals:approve` el lote aprueba (verde hoy)."""
    resp = await http_client.post(
        "/api/v1/approvals/batch-approve",
        headers=_token(esc208["u_aprobador"]),
        json={"event_ids": [esc208["ev_e1"], esc208["ev_e2"]]},
    )
    assert resp.status_code == 200, resp.text
    assert await _estado(esc208, esc208["ev_e1"]) == "approved"
    assert await _estado(esc208, esc208["ev_e2"]) == "approved"


async def test_r208_03_reject_simetrico(http_client, esc208):
    """`AC-R208-03`: `batch-reject` exige `approvals:reject` (RED en HEAD: 200)."""
    resp = await http_client.post(
        "/api/v1/approvals/batch-reject",
        headers=_token(esc208["u_revisor"]),
        json={"event_ids": [esc208["ev_e1"]],
              "observations": f"{PREFIJO}motivo suficientemente largo"},
    )
    assert resp.status_code == 403, resp.text
    assert "approvals:reject" in resp.text
    assert await _estado(esc208, esc208["ev_e1"]) == "corrected"


async def test_r208_04_br14_por_evento(http_client, esc208):
    """`AC-R208-04` (control): BR-14/R-143 por evento intactas tras la puerta.

    A1 rechaza e1 en lote (permitido) y después no puede aprobarlo; la denegación
    es por evento y e2 queda intacto.
    """
    cab = _token(esc208["u_aprobador"])
    r1 = await http_client.post(
        "/api/v1/approvals/batch-reject", headers=cab,
        json={"event_ids": [esc208["ev_e1"]],
              "observations": f"{PREFIJO}motivo suficientemente largo"},
    )
    assert r1.status_code == 200, r1.text
    assert await _estado(esc208, esc208["ev_e1"]) == "rejected"

    r2 = await http_client.post(
        "/api/v1/approvals/batch-approve", headers=cab,
        json={"event_ids": [esc208["ev_e1"], esc208["ev_e2"]]},
    )
    assert r2.status_code in (400, 403), r2.text
    assert await _estado(esc208, esc208["ev_e1"]) == "rejected"
    assert await _estado(esc208, esc208["ev_e2"]) == "corrected"
