"""`R-209` · control (verde en HEAD) — el comparativo SAP reporta las referencias **verbatim**.

El endpoint `/reports/sap-comparison` lista los eventos con `sap_document_ref` y su `status`
decide `matched`/`pending`; la normalización del valor es responsabilidad del **cliente**
(`R-189 §2` / `R-209`). Este control fija el contrato de lectura: lo que el asistente
guarde es lo que el comparativo muestra — código, no id (`C-03`: los históricos con id no
se reescriben aquí; inventario de lectura aparte).
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

pytestmark = pytest.mark.asyncio

PREFIJO = "R209-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company
    from app.operations.models import EventStatus, EventType, OperationalEvent

    motor = create_async_engine(test_database_url)
    datos: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()

        rol = Role(name=f"{PREFIJO}R-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        s.add(Permission(role_id=rol.id, module="reports", action=PermissionAction.READ,
                         scope_type="company"))
        usuario = User(first_name="L", last_name="R209",
                       email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                       username=f"{PREFIJO}U-{uuid.uuid4().hex[:6]}",
                       hashed_password=hash_password("x"), company_id=a.id,
                       role_id=rol.id, is_active=True)
        s.add(usuario)
        await s.flush()

        from tests.time_reference import days_ago

        confirmado = OperationalEvent(company_id=a.id, event_type=EventType.BIRD_EXIT,
                                      event_date=days_ago(2),
                                      status=EventStatus.SAP_CONFIRMED,
                                      sap_document_ref="4500001234",
                                      registered_by_id=usuario.id)
        aprobado = OperationalEvent(company_id=a.id, event_type=EventType.FEED_REGISTRATION,
                                    event_date=days_ago(1),
                                    status=EventStatus.APPROVED,
                                    sap_document_ref="4500009",
                                    registered_by_id=usuario.id)
        historico = OperationalEvent(company_id=a.id, event_type=EventType.BIRD_EXIT,
                                     event_date=days_ago(30),
                                     status=EventStatus.SAP_CONFIRMED,
                                     sap_document_ref="12",
                                     registered_by_id=usuario.id)
        s.add_all([confirmado, aprobado, historico])
        await s.commit()

        datos = {"operador": usuario.id}
    yield datos

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
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


async def test_r209_01_el_comparativo_reporta_las_referencias_verbatim(http_client, esc):
    r = await http_client.get("/api/v1/reports/sap-comparison",
                              headers=_token(esc["operador"]))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["total_with_sap_ref"] == 3
    refs = {e["sap_ref"] for e in cuerpo["events"]}
    assert {"4500001234", "4500009", "12"} <= refs, refs


async def test_r209_02_matched_por_estado_pending_por_aprobado(http_client, esc):
    r = await http_client.get("/api/v1/reports/sap-comparison",
                              headers=_token(esc["operador"]))
    cuerpo = r.json()
    assert cuerpo["matched_with_sap"] == 2
    assert cuerpo["pending_sap_sync"] == 1
