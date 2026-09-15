"""GA-REQ-061 · T14 · C6 — correcciones formales del opening (RED).

Rojo en HEAD (`4b8bc74`): no existe `POST/GET /opening-balances/{id}/corrections`
(404). Contrato: AC59-65 — APPLIED no editable/eliminable directamente,
corrección **conserva el original** (fila before/after/delta), **razón
obligatoria** (CUT-RED-17), auditoría completa, y **nunca borra eventos
post-cutover** (CUT-RED-18: 10.000 → corrección 9.900 ⇒ current 9.865 con la
mortalidad 35 intacta). Permiso de correcciones existente (`corrections`).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from test_ga_req_061_cutover_c4_apply import _batch_aprobado, _fase  # noqa: E402
from test_ga_req_061_cutover_c5_reporting import _evento_mortalidad  # noqa: E402


def _filas(etiqueta: str) -> list[list]:
    return [
        [f"CUT-G6-{etiqueta}-1", "2026-08-15", 5000, 5000, 300, 200, None, "golden correcciones"],
        [f"CUT-G6-{etiqueta}-2", "2026-09-01", 2000, 2000, None, None, None, "histórico desconocido"],
    ]


async def _opening_de(lot_id: int):
    from app.lots.models import OpeningBalance

    async with database.async_session() as session:
        fila = (await session.execute(
            select(OpeningBalance).where(OpeningBalance.lot_id == lot_id))).scalars().first()
    assert fila is not None
    return fila


async def _escenario(client, auth_headers, seeded_ids, etiqueta: str):
    """Batch aplicado + evento post (35); devuelve (batch_id, lote1, opening)."""
    await _fase()
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=_filas(etiqueta))
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert r.status_code == 200, r.text
    items = (await client.get(f"/api/v1/cutover-batches/{batch_id}/items", headers=auth_headers)).json()["items"]
    lote1 = next(it["lot_id"] for it in items if it["legacy_lot_reference"] == f"CUT-G6-{etiqueta}-1")
    await _evento_mortalidad(lote1, seeded_ids["company_id"], seeded_ids["user_admin_id"], "2026-09-30", 999, 0)
    await _evento_mortalidad(lote1, seeded_ids["company_id"], seeded_ids["user_admin_id"], "2026-10-09", 20, 15)
    return batch_id, lote1, await _opening_de(lote1)


def _correccion(opening_id: int, **overrides) -> dict:
    payload = {
        "field": "initial_female_count",
        "new_value": 4900,
        "reason": "ajuste por conteo físico del cierre",
    }
    payload.update(overrides)
    return payload


async def _corregir(client, headers, opening_id: int, **overrides):
    return await client.post(f"/api/v1/opening-balances/{opening_id}/corrections",
                             headers=headers, json=_correccion(opening_id, **overrides))


@pytest.mark.asyncio
async def test_c6_applied_no_editable_ni_eliminable(auth_headers, client, seeded_ids):
    """AC59/60: sin rutas de edición/borrado directo; la única vía es la corrección."""
    _, _, opening = await _escenario(client, auth_headers, seeded_ids, "G1")
    base = f"/api/v1/opening-balances/{opening.id}"
    assert (await client.patch(base, headers=auth_headers, json={"initial_male_count": 1})).status_code in (404, 405)
    assert (await client.put(base, headers=auth_headers, json={"initial_male_count": 1})).status_code in (404, 405)
    assert (await client.delete(base, headers=auth_headers)).status_code in (404, 405)
    # …y la vía formal SÍ existe (201).
    assert (await _corregir(client, auth_headers, opening.id)).status_code == 201


@pytest.mark.asyncio
async def test_c6_correccion_requiere_razon(auth_headers, client, seeded_ids):
    """CUT-RED-17/AC62: sin razón (o demasiado corta) ⇒ rechazada."""
    _, _, opening = await _escenario(client, auth_headers, seeded_ids, "G2")
    sin_razon = _correccion(opening.id)
    sin_razon.pop("reason")
    r = await client.post(f"/api/v1/opening-balances/{opening.id}/corrections",
                          headers=auth_headers, json=sin_razon)
    assert r.status_code == 422, r.text
    r = await _corregir(client, auth_headers, opening.id, reason="abc")
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_c6_before_after_delta_y_auditoria(auth_headers, client, seeded_ids):
    """AC61-64: conserva el original, registra before/after/delta, audita y actualiza el opening."""
    _, _, opening = await _escenario(client, auth_headers, seeded_ids, "G3")
    assert opening.initial_female_count == 5000

    r = await _corregir(client, auth_headers, opening.id)
    assert r.status_code == 201, r.text
    fila = r.json()
    assert fila["field"] == "initial_female_count"
    assert fila["old_value"] == "5000" and fila["new_value"] == "4900" and fila["delta"] == "-100"
    assert fila["reason"] and fila["requested_by_id"] == seeded_ids["user_admin_id"]
    assert fila["applied_at"]

    # La lista devuelve la corrección; el opening quedó actualizado (original conservado en la fila).
    lista = await client.get(f"/api/v1/opening-balances/{opening.id}/corrections", headers=auth_headers)
    assert lista.status_code == 200 and len(lista.json()["items"]) == 1
    assert (await _opening_de(opening.lot_id)).initial_female_count == 4900

    # Auditoría CORRECT con actor/empresa/antes/después.
    from app.audit.models import AuditLog

    async with database.async_session() as session:
        auditoria = (await session.execute(
            select(AuditLog).where(AuditLog.entity_type == "opening_balance",
                                   AuditLog.entity_id == str(opening.id)))).scalars().all()
    assert any(str(a.action).lower().endswith("correct") for a in auditoria), [a.action for a in auditoria]


@pytest.mark.asyncio
async def test_c6_correccion_no_borra_post_9865(auth_headers, client, seeded_ids):
    """CUT-RED-18/AC65: 10.000 → corrección 9.900 ⇒ current 9.865 con post 35 intacto."""
    batch_id, lote1, opening = await _escenario(client, auth_headers, seeded_ids, "G4")
    assert (await _corregir(client, auth_headers, opening.id)).status_code == 201

    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    fila = next(f for f in r.json()["lots"] if f["lot_id"] == lote1)
    assert fila["current_live"] == 9865, "9.900 − 35 (nunca se recalcula borrando el evento)"
    assert fila["post"]["mortality"] == 35, "la corrección JAMÁS borra eventos post-cutover"
    assert fila["lifetime"]["mortality"] == 535

    # Los dos eventos siguen en la base (pre + post): nada se eliminó.
    from app.operations.models import OperationalEvent

    async with database.async_session() as session:
        eventos = (await session.execute(
            select(OperationalEvent).where(OperationalEvent.lot_id == lote1))).scalars().all()
    assert len(eventos) == 2


@pytest.mark.asyncio
async def test_c6_correccion_cross_tenant_denegada(auth_headers, client, seeded_ids):
    """Seguridad: opening de otra empresa ⇒ 404 fail-closed (POST y GET)."""
    from sqlalchemy import select as _select

    from app.auth.models import User
    from app.auth.security import create_access_token
    from test_ga_req_061_cutover_c3_lifecycle import _otorgar

    _, _, opening = await _escenario(client, auth_headers, seeded_ids, "G5")

    # El rol del usuario ajeno necesita el permiso para que el gate RBAC no oculte
    # la comprobación de tenancy que es lo que aquí se verifica (fallo 404, no 403).
    async with database.async_session() as session:
        ajeno = (await session.execute(
            _select(User).where(User.id == seeded_ids["user_other_company_id"]))).scalars().first()
    await _otorgar(ajeno.role_id, ("corrections", "correct"), ("corrections", "read"))

    headers_ajenos = {"Authorization": "Bearer " + create_access_token(data={
        "sub": str(seeded_ids["user_other_company_id"]), "role": "operator"})}

    r = await _corregir(client, headers_ajenos, opening.id)
    assert r.status_code == 404, r.text
    r = await client.get(f"/api/v1/opening-balances/{opening.id}/corrections", headers=headers_ajenos)
    assert r.status_code == 404, r.text
