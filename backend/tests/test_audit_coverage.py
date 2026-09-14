"""Cobertura de auditoría — `GA-REM-032`, hallazgo `R-81`.

Cubre `AC01`…`AC08`.

`docs/02 §3.11.1` exige que **cada acción del sistema** genere un registro inmutable. Los
listeners vigilaban tres tipos de modelo, de modo que seis de los once módulos declarados
—`auth`, `masters`, `lots`, `users`, `config`, `reports`— no producían ni un registro.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.audit.models import AuditAction, AuditLog, AuditModule
from tests.audit_harness import listener_auditoria_como_runtime  # noqa: F401

# `P1-12-REOPEN` (§1.3): los conteos «exactamente 1» se verifican en runtime (con listener).
pytestmark = pytest.mark.usefixtures("listener_auditoria_como_runtime")

PREFIJO = "AC-TEST-"


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    await e.dispose()


async def _registros(motor, accion: AuditAction, **filtros):
    """Registros de auditoría de una acción, leídos de la base."""
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        q = select(AuditLog).where(AuditLog.action == accion)
        for campo, valor in filtros.items():
            q = q.where(getattr(AuditLog, campo) == valor)
        return (await s.execute(q.order_by(AuditLog.created_at.desc()))).scalars().all()


# ── AC01 · el acceso al sistema deja rastro ───────────────────────────────────

async def test_t_081_01_el_login_correcto_se_audita(
    client, seeded_ids, test_credentials, motor
):
    """`AC01` y `AC06` · quién entró, cuándo y desde qué módulo."""
    usuario, clave = test_credentials

    previos = len(await _registros(motor, AuditAction.LOGIN))
    r = await client.post("/api/v1/login", json={"username": usuario, "password": clave})
    assert r.status_code == 200, r.text

    registros = await _registros(motor, AuditAction.LOGIN)
    assert len(registros) == previos + 1, "el inicio de sesión no dejó rastro"

    log = registros[0]
    assert log.user_id == seeded_ids["user_admin_id"], "el registro no identifica al actor"
    assert log.module == AuditModule.AUTH
    assert log.company_id == seeded_ids["company_id"]
    assert log.created_at is not None


async def test_t_081_02_el_login_fallido_se_audita(
    client, seeded_ids, test_credentials, motor
):
    """`AC01` · el intento fallido sobre una cuenta existente es lo que un auditor busca.

    Se comprueba además que el registro **no** filtra la contraseña intentada: auditar un
    fallo de acceso guardando la credencial sería peor que no auditarlo.
    """
    usuario, _ = test_credentials

    previos = len(await _registros(motor, AuditAction.LOGIN_FAILED))
    r = await client.post("/api/v1/login",
                          json={"username": usuario, "password": "clave-equivocada-XYZ"})
    assert r.status_code == 401, r.text

    registros = await _registros(motor, AuditAction.LOGIN_FAILED)
    assert len(registros) == previos + 1, "el intento fallido no dejó rastro"

    log = registros[0]
    assert log.user_id == seeded_ids["user_admin_id"]
    assert log.module == AuditModule.AUTH
    volcado = f"{log.new_values} {log.previous_values} {log.comments} {log.change_reason}"
    assert "clave-equivocada-XYZ" not in volcado, (
        "el registro de auditoría guardó la contraseña intentada"
    )


# ── AC02 · maestros y lotes ───────────────────────────────────────────────────

async def test_t_081_03_el_alta_y_la_edicion_de_un_maestro_se_auditan(
    client, auth_headers, seeded_ids, motor
):
    """`AC02` y `AC06` · crear y editar un maestro deja rastro con su entidad."""
    s = uuid.uuid4().hex[:8]
    creado = await client.post("/api/v1/masters/farms", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"],
        "name": f"{PREFIJO}granja-{s}", "code": f"ACT{s[:6]}"})
    assert creado.status_code in (200, 201), creado.text
    farm_id = creado.json()["id"]

    altas = await _registros(motor, AuditAction.CREATED,
                             module=AuditModule.MASTERS, entity_id=str(farm_id))
    assert len(altas) == 1, "el alta del maestro no dejó rastro"
    assert altas[0].user_id == seeded_ids["user_admin_id"]
    assert altas[0].entity_type == "farm", altas[0].entity_type

    editado = await client.put(f"/api/v1/masters/farms/{farm_id}", headers=auth_headers,
                               json={"name": f"{PREFIJO}granja-{s}-editada"})
    assert editado.status_code == 200, editado.text

    ediciones = await _registros(motor, AuditAction.UPDATED,
                                 module=AuditModule.MASTERS, entity_id=str(farm_id))
    assert len(ediciones) == 1, "la edición del maestro no dejó rastro"


# ── AC03 · permisos ───────────────────────────────────────────────────────────

async def test_t_081_04_el_cambio_de_permisos_se_audita(
    client, auth_headers, seeded_ids, motor
):
    """`AC03` · «quién concedió esto y cuándo» debe tener respuesta."""
    s = uuid.uuid4().hex[:8]
    rol = await client.post("/api/v1/roles", headers=auth_headers, json={
        "name": f"{PREFIJO}rol-{s}", "description": "Rol de prueba de auditoría",
        "permissions": [{"module": "lots", "action": "read"}],
    })
    assert rol.status_code in (200, 201), rol.text

    registros = await _registros(motor, AuditAction.PERMISSION_CHANGE,
                                 entity_id=str(rol.json()["id"]))
    assert len(registros) == 1, "el alta del rol no dejó rastro de permisos"
    assert registros[0].module == AuditModule.USERS
    assert registros[0].user_id == seeded_ids["user_admin_id"]


# ── AC05 · cierre de revisión ─────────────────────────────────────────────────

async def test_t_081_05_el_cierre_de_revision_se_audita(
    client, auth_headers, seeded_ids, motor
):
    """`AC05` · `REVIEW_COMPLETED` estaba declarada y no la escribía nadie."""
    from app.auth.security import create_access_token

    evento = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": seeded_ids["lot_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "feed_registration",
        "event_date": __import__("tests.time_reference", fromlist=["x"]).iso_days_ago(0),
        "feed_movements": [{"quantity_kg": 10.0}],
    })
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]

    enviado = await client.post(f"/api/v1/operations/{event_id}/submit", headers=auth_headers)
    assert enviado.status_code in (200, 201), enviado.text

    revisor = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_approver_id"])})}
    iniciada = await client.post(f"/api/v1/review/start/{event_id}", headers=revisor)
    assert iniciada.status_code in (200, 201), iniciada.text

    completada = await client.post("/api/v1/review/complete", headers=revisor,
                                   json={"event_id": event_id, "observations": "Revisado"})
    assert completada.status_code in (200, 201), completada.text

    registros = await _registros(motor, AuditAction.REVIEW_COMPLETED,
                                 entity_id=str(event_id))
    assert len(registros) == 1, "el cierre de revisión no dejó rastro"
    assert registros[0].module == AuditModule.REVIEW


# ── AC04 · importación ────────────────────────────────────────────────────────

async def test_t_081_06_la_importacion_de_referencias_se_audita(
    client, auth_headers, seeded_ids, motor
):
    """`AC04` · importar referencias SAP es una acción del sistema."""
    s = uuid.uuid4().hex[:6].upper()
    r = await client.post("/api/v1/sap/references/import", headers=auth_headers, json={
        "references": [{
            "ref_type": "purchase_order", "sap_code": f"PO-{PREFIJO}{s}",
            "description": "Importación de prueba", "quantity": 100,
        }],
    })
    assert r.status_code in (200, 201), r.text

    registros = await _registros(motor, AuditAction.IMPORT)
    assert len(registros) >= 1, "la importación no dejó rastro"
    assert registros[0].module == AuditModule.SAP
    assert registros[0].user_id == seeded_ids["user_admin_id"]
