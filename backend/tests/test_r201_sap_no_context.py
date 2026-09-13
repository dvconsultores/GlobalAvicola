"""`R-201` · Predicado SAP **fail-closed** sin contexto de empresa.

Diseño: `audit/ga-claude-final-audit/specs/R-201/R-201_RED_E2E_UAT_DESIGN.md §1`.

El módulo SAP usa `_company_filter` con rama comodín `true()` para la autoridad
global **sin contexto**: ve referencias, jobs, consolidados, errores y payloads de
todas las empresas; `retry` reenvía las ajenas; `consolidate` lee todas antes de
fallar. El resto del producto ya es fail-closed (patrón `_acotar_a_empresa`).

```
Global SIN contexto   → lecturas ∅ · consolidate/export/retry ⇒ 4xx cerrado
Global SITUADA en A   → ve y opera solo A (control)
Actor de empresa A    → comportamiento intacto (control)
```

Nota de diseño (verificada contra el código antes de ejecutar el RED): en HEAD,
`consolidate` **sin contexto y sin eventos aprobados** retorna `201 []` — la
guarda `_require_company_id` solo se alcanza dentro del bucle de grupos. Por eso
`test_r201_03` vacía los eventos aprobados de A en su propio paso: el criterio
«falla cerrado **sin leer**» se observa como `4xx` donde HEAD responde éxito. El
control `test_r201_03b` (evento aprobado presente) documenta que, con eventos,
HEAD ya fallaba tarde y sin transicionar — tras el fix falla **antes** de leer.

PREFIJO `R201-`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, time, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R201-"
CUATROXX = (400, 403, 409)


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc201(test_database_url):
    """Empresas A/B con referencias, jobs, consolidados, payloads y un evento aprobado.

    ```
    rol_global   company_id=NULL · ("*", …, "all")   → autoridad global (R-199)
    rol_a        company_id=A    · sap:read + sap:send_sap
    u_global     sin contexto  ·  u_a  actor de empresa A
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.integrations.sap.models import (
        ConsolidatedMovement, PayloadStatus, SapPayload, SapReference,
        SapReferenceType, SapSyncJob, SyncDirection,
    )
    from app.masters.models import BirdTypeEnum, Company, Lot
    from app.operations.models import EventStatus, EventType, OperationalEvent

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        def _rol(nombre, company_id):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_global = _rol("Global", None)
        rol_a = _rol("A", a.id)
        await s.flush()
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        for modulo, accion in (("sap", PermissionAction.READ),
                               ("sap", PermissionAction.SEND_SAP)):
            s.add(Permission(role_id=rol_a.id, module=modulo, action=accion,
                             scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca[:8], last_name="R201",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        u_global = _usuario(None, "GLOBAL", rol_global)
        u_a = _usuario(a.id, "EMPRESA", rol_a)
        s.add_all([u_global, u_a])
        await s.flush()

        def _referencia(company_id, marca):
            ref = SapReference(company_id=company_id,
                               ref_type=SapReferenceType.PURCHASE_ORDER,
                               sap_code=f"{PREFIJO}OC-{marca}-{uuid.uuid4().hex[:6]}",
                               description=marca, is_active=True)
            s.add(ref)
            return ref

        ref_a1 = _referencia(a.id, "A1")
        ref_a2 = _referencia(a.id, "A2")
        ref_b1 = _referencia(b.id, "B1")

        lote_a = Lot(company_id=a.id, lot_code=f"{PREFIJO}LA-{uuid.uuid4().hex[:6]}",
                     bird_type=BirdTypeEnum.BROILER, status="active")
        lote_b = Lot(company_id=b.id, lot_code=f"{PREFIJO}LB-{uuid.uuid4().hex[:6]}",
                     bird_type=BirdTypeEnum.BROILER, status="active")
        s.add_all([lote_a, lote_b])
        await s.flush()

        def _instante():
            return datetime.combine(datetime.now(timezone.utc).date(), time.min,
                                    tzinfo=timezone.utc)

        cm_a = ConsolidatedMovement(
            company_id=a.id, lot_id=lote_a.id, event_type="mortality_recording",
            period_start=_instante(), period_end=_instante(), event_ids=[],
            total_quantity=10.0, unit="units", consolidated_by_id=u_a.id)
        cm_b = ConsolidatedMovement(
            company_id=b.id, lot_id=lote_b.id, event_type="mortality_recording",
            period_start=_instante(), period_end=_instante(), event_ids=[],
            total_quantity=20.0, unit="units", consolidated_by_id=u_a.id)
        s.add_all([cm_a, cm_b])

        job_a = SapSyncJob(company_id=a.id, direction=SyncDirection.EXPORT,
                           initiated_by_id=u_a.id)
        job_b = SapSyncJob(company_id=b.id, direction=SyncDirection.EXPORT,
                           initiated_by_id=u_a.id)
        s.add_all([job_a, job_b])

        def _payload(company_id, marca, lot_id):
            # `SapExportPayload` exige la forma completa: el retry la valida al
            # construir el payload del adaptador.
            p = SapPayload(company_id=company_id, idempotency_key=uuid.uuid4().hex,
                           payload_data={
                               "idempotency_key": uuid.uuid4().hex,
                               "event_type": "mortality_recording",
                               "lot_id": lot_id, "company_id": company_id,
                               "event_date": "2026-09-12", "quantity": 1.0,
                               "unit": "units",
                           },
                           status=PayloadStatus.FAILED,
                           retry_count=0, error_message=f"{PREFIJO}fallo {marca}")
            s.add(p)
            return p

        p_a = _payload(a.id, "PA", lote_a.id)
        p_b = _payload(b.id, "PB", lote_b.id)

        ev_a = OperationalEvent(company_id=a.id, lot_id=lote_a.id,
                                event_type=EventType.MORTALITY_RECORDING,
                                event_date=_instante().date(),
                                status=EventStatus.APPROVED,
                                registered_by_id=u_a.id, version=1,
                                observations=f"{PREFIJO}evento aprobado A")
        s.add(ev_a)
        await s.flush()
        await s.commit()

        d = {"url": test_database_url, "a": a.id, "b": b.id,
             "u_global": u_global.id, "u_a": u_a.id, "ev_a": ev_a.id,
             "ref_a1": ref_a1.id, "ref_b1": ref_b1.id,
             "p_a": p_a.id, "p_b": p_b.id}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM sap_responses WHERE payload_id IN (SELECT id FROM sap_payloads WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM sap_payloads WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM sap_sync_jobs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM consolidated_movements WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM sap_references WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def _escalar(esc, sql, **params):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(sql), params)).scalar()
    finally:
        await motor.dispose()


async def test_r201_01_referencias_sin_contexto_es_vacio(http_client, esc201):
    """`AC-R201-01`. RED en HEAD: devuelve las referencias de A y B."""
    r = await http_client.get("/api/v1/sap/references",
                              headers=_token(esc201["u_global"]))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["references"] == [], cuerpo["total"]
    assert cuerpo["total"] == 0


async def test_r201_02_payloads_sin_contexto_es_vacio(http_client, esc201):
    """`AC-R201-02`. RED en HEAD: jobs/consolidados/errores/payloads de todas."""
    cab = _token(esc201["u_global"])
    r = await http_client.get("/api/v1/sap/payloads", headers=cab)
    assert r.status_code == 200 and r.json()["payloads"] == [], r.text
    r = await http_client.get("/api/v1/sap/errors", headers=cab)
    assert r.status_code == 200 and r.json() == [], r.text
    r = await http_client.get("/api/v1/sap/sync/jobs", headers=cab)
    assert r.status_code == 200 and r.json()["jobs"] == [], r.text
    r = await http_client.get("/api/v1/sap/consolidated", headers=cab)
    assert r.status_code == 200 and r.json()["consolidated"] == [], r.text


async def test_r201_03_consolidate_sin_contexto_falla_cerrado(http_client, esc201):
    """`AC-R201-03`. RED en HEAD: sin eventos aprobados responde **201 []**.

    La guarda de empresa solo se alcanza dentro del bucle de grupos; sin filas
    que agrupar no hay falla. Debe fallar **antes de leer**, siempre.
    """
    motor = create_async_engine(esc201["url"])
    async with motor.begin() as c:
        await c.execute(text(
            "DELETE FROM operational_events WHERE company_id = :a"),
            {"a": esc201["a"]})
    await motor.dispose()

    r = await http_client.post("/api/v1/sap/consolidate",
                               headers=_token(esc201["u_global"]), json={})
    assert r.status_code in CUATROXX, r.text
    n = await _escalar(esc201,
                       "SELECT count(*) FROM consolidated_movements WHERE company_id = :a",
                       a=esc201["a"])
    assert n == 1, "sin consolidados nuevos"  # el del fixture (A) sigue siendo el único


async def test_r201_03b_control_con_evento_aprobado_no_transiciona(http_client, esc201):
    """Control: con evento aprobado, HEAD ya fallaba tarde; tras el fix, antes.

    En ambos: 4xx y el evento sigue `approved` (criterio de «sin transiciones»).
    """
    r = await http_client.post("/api/v1/sap/consolidate",
                               headers=_token(esc201["u_global"]), json={})
    assert r.status_code in CUATROXX, r.text
    estado = await _escalar(esc201,
                            "SELECT status FROM operational_events WHERE id = :e",
                            e=esc201["ev_a"])
    assert str(estado).lower().split(".")[-1] == "approved"


async def test_r201_04_retry_sin_contexto_no_reenvia(http_client, esc201,
                                                   monkeypatch, tmp_path):
    """`AC-R201-04`. RED en HEAD: reenvía payloads `FAILED` de A **y** de B.

    `SAP_EXPORT_DIR` temporal: el adaptador `manual` (por defecto) escribe un
    artefacto por payload; sin directorio escribible devolvería 500 de entorno,
    no el comportamiento del servidor que esta prueba mide.
    """
    monkeypatch.setenv("SAP_EXPORT_DIR", str(tmp_path))
    r = await http_client.post("/api/v1/sap/retry",
                               headers=_token(esc201["u_global"]), json={})
    assert r.status_code in CUATROXX, r.text
    for clave, marca in (("p_a", "A"), ("p_b", "B")):
        fila = await _escalar(esc201,
                              "SELECT retry_count || ':' || status::text FROM sap_payloads WHERE id = :p",
                              p=esc201[clave])
        assert str(fila).lower() == "0:failed", f"payload {marca} intacto: {fila}"


async def test_r201_05_global_situada_opera_su_empresa(http_client, esc201,
                                                     monkeypatch, tmp_path):
    """`AC-R201-05` (control): situada en A ve y reintenta solo lo de A."""
    monkeypatch.setenv("SAP_EXPORT_DIR", str(tmp_path))
    cab = _token(esc201["u_global"], company_id=esc201["a"])
    r = await http_client.get("/api/v1/sap/references", headers=cab)
    assert r.status_code == 200 and r.json()["total"] == 2, r.text
    r = await http_client.get("/api/v1/sap/consolidated", headers=cab)
    assert r.status_code == 200 and r.json()["total"] == 1, r.text
    r = await http_client.post("/api/v1/sap/retry", headers=cab, json={})
    assert r.status_code == 200, r.text
    assert r.json()["retried"] == 1, r.text
    fila_b = await _escalar(esc201,
                            "SELECT retry_count FROM sap_payloads WHERE id = :p",
                            p=esc201["p_b"])
    assert fila_b == 0, "B intacta"


async def test_r201_06_actor_de_empresa_intacto(http_client, esc201,
                                              monkeypatch, tmp_path):
    """`AC-R201-06` (control): el actor de empresa A conserva su comportamiento."""
    monkeypatch.setenv("SAP_EXPORT_DIR", str(tmp_path))
    cab = _token(esc201["u_a"])
    r = await http_client.get("/api/v1/sap/references", headers=cab)
    assert r.status_code == 200 and r.json()["total"] == 2, r.text
    r = await http_client.post("/api/v1/sap/retry", headers=cab, json={})
    assert r.status_code == 200 and r.json()["retried"] == 1, r.text
