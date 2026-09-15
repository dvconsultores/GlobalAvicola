"""GA-REQ-061 · T14 · C3 — lifecycle del batch con segregación (RED).

Rojo en HEAD (`3e138a1`): no existen `submit/approve/reject` (404). La
Implementación añade la máquina de estados DRAFT→…→VALIDATED→PENDING_APPROVAL→
APPROVED|REJECTED con **segregación de funciones** (creador ≠ aprobador; espejo
de BR-14), rechazo MOTIVADO y auditoría SUBMIT/APPROVED/REJECTED (AC70-75).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

# Helpers de construcción del Excel/batch del checkpoint C2 (mismo paquete de tests).
sys.path.insert(0, str(Path(__file__).parent))
from test_ga_req_061_cutover_c2_lifecycle import _crear_batch, _subir, _xlsx  # noqa: E402
from time_reference import days_ago, iso_days_ago  # noqa: E402

#: Cortes propios por test (la unicidad company/BU/checksum/corte es del contrato).
CORTE_C3_A = days_ago(48).isoformat() + "T00:00:00+00:00"
CORTE_C3_B = days_ago(47).isoformat() + "T00:00:00+00:00"
CORTE_C3_C = days_ago(46).isoformat() + "T00:00:00+00:00"
CORTE_C3_D = days_ago(44).isoformat() + "T00:00:00+00:00"

FILAS_VALIDAS = [
    ["CUT-BR-010", iso_days_ago(60), 4000, 4000, 100, 80, None, ""],
]


async def _batch_validado(client, headers, cutover: str) -> int:
    batch_id = await _crear_batch(client, headers, cutover=cutover)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                          headers=headers, files=_subir(_xlsx(FILAS_VALIDAS)))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "validated", r.text
    return batch_id


async def _otorgar(role_id: int, *pares: tuple[str, str]) -> None:
    """Otorga permisos a un rol sembrado (patrón R-199; la matriz de permisos es un dato)."""
    from app.auth.models import Permission, PermissionAction

    async with database.async_session() as session:
        for modulo, accion in pares:
            session.add(Permission(role_id=role_id, module=modulo,
                                   action=PermissionAction(accion), scope_type="company"))
        await session.commit()


def _headers_aprobar(seeded_ids: dict) -> dict:
    from app.auth.security import create_access_token

    return {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_approver_id"])})}


@pytest.mark.asyncio
async def test_c3_submit_solo_desde_validated(auth_headers, client):
    """`submit` exige VALIDATED; después el batch queda inmóvil a cargas (409 determinista)."""
    # Un borrador no puede enviarse.
    borrador = await _crear_batch(client, auth_headers, cutover=CORTE_C3_A)
    r0 = await client.post(f"/api/v1/cutover-batches/{borrador}/submit", headers=auth_headers)
    assert r0.status_code == 409, r0.text

    batch_id = await _batch_validado(client, auth_headers, CORTE_C3_A)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/submit", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "pending_approval"

    # Reenviar ⇒ 409; recargar plantilla ⇒ 409 (ya no admite cargas).
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 409
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                              headers=auth_headers,
                              files=_subir(_xlsx(FILAS_VALIDAS)))).status_code == 409


@pytest.mark.asyncio
async def test_c3_creador_no_aprueba_su_batch(auth_headers, client):
    """Segregación (espejo de BR-14): quien creó el batch no lo aprueba, ni siendo super admin."""
    batch_id = await _batch_validado(client, auth_headers, CORTE_C3_B)
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 200
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/approve", headers=auth_headers)
    assert r.status_code == 403, r.text
    assert "segregaci" in r.text.lower() or "creador" in r.text.lower()


@pytest.mark.asyncio
async def test_c3_aprobar_con_otro_actor(auth_headers, client, seeded_ids):
    """Un actor distinto con `cutover:approve` aprueba; queda auditoría SUBMIT/APPROVED."""
    await _otorgar(seeded_ids["role_approver_id"], ("cutover", "approve"), ("cutover", "read"))
    batch_id = await _batch_validado(client, auth_headers, CORTE_C3_C)
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 200

    headers_aprob = _headers_aprobar(seeded_ids)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/approve", headers=headers_aprob)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"

    # Auditoría del ciclo (AC70-75): SUBMIT y APPROVED registrados para el batch.
    from app.audit.models import AuditLog

    async with database.async_session() as session:
        acciones = (await session.execute(
            select(AuditLog.action).where(AuditLog.entity_id == str(batch_id),
                                          AuditLog.entity_type == "cutover_batch"))).scalars().all()
    nombres = {str(getattr(a, "name", a)) for a in acciones}
    assert {"SUBMIT", "APPROVED"} <= nombres, nombres


@pytest.mark.asyncio
async def test_c3_rechazo_requiere_razon(auth_headers, client, seeded_ids):
    """`REJECTED` exige razón; sin ella ⇒ 422; con ella ⇒ terminal (re-submit ⇒ 409)."""
    await _otorgar(seeded_ids["role_approver_id"], ("cutover", "approve"))
    batch_id = await _batch_validado(client, auth_headers, CORTE_C3_D)
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 200

    headers_aprob = _headers_aprobar(seeded_ids)
    sin_razon = await client.post(f"/api/v1/cutover-batches/{batch_id}/reject",
                                  headers=headers_aprob, json={"reason": ""})
    assert sin_razon.status_code == 422, sin_razon.text

    con_razon = await client.post(f"/api/v1/cutover-batches/{batch_id}/reject",
                                  headers=headers_aprob,
                                  json={"reason": "Documento de respaldo inconsistente"})
    assert con_razon.status_code == 200, con_razon.text
    assert con_razon.json()["status"] == "rejected"

    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit",
                              headers=auth_headers)).status_code == 409
