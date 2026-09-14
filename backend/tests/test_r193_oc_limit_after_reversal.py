"""`R-193` · RED — acumulado `BR-18` **neto** de reversos (`OD-19`).

`BR-18` (`G-R05`/`OD-04`): la cantidad acumulada recibida contra una orden de compra no puede
exceder `SapReference.quantity`; el acumulado suma `bird_movements.quantity` de las recepciones
con la misma `sap_document_ref` y `status != CANCELLED`. `OD-19` añadió el reverso: la
contrapartida copia el original (incluida la referencia) y al aprobarse **ambos** quedan
`REVERSED`. Los saldos de aves ya restan la contrapartida efectiva (`_suma_neta`); `BR-18` no:
tras un reverso, la OC «pierde» 2n de capacidad — entregas reales rechazadas y conciliación
inflada.

Acumulado esperado: Σ de recepciones `≠ CANCELLED` que **no** son contrapartidas
− contrapartidas efectivas ⇒ equivalente a excluir `REVERSED` y `id ∈ reversals.reversal_event_id`.
Una contrapartida **pendiente o rechazada** no resta; el original mientras no sea `REVERSED`
sí cuenta.

RED esperado en HEAD: 01 (400 «ya recibidas: 800»), 02 (segundo 700 ⇒ 400), 03 (600 ⇒ 400),
04 (1000 ⇒ 400), 05 («ya recibidas: 1200»). Controles verdes: par efectivo, pendiente bloquea,
mensaje sin reverso.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from app.operations.models import EventStatus, OperationalEvent, Reversal
from tests.time_reference import iso_days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "R193-"
ORDENADO = 1000


def _cabecera(user_id: int) -> dict:
    from app.auth.security import create_access_token
    return {"Authorization": "Bearer " + create_access_token(data={"sub": str(user_id)})}


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.integrations.sap.models import SapReference
    from app.lots.models import LotPhase, OpeningBalance
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, InspectionDetail, OperationalAlert,
    )
    from app.review.models import ApprovalAction

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(ids)))).scalars().all()
            if eventos:
                await c.execute(delete(OperationalAlert).where(
                    OperationalAlert.event_id.in_(eventos)))
                await c.execute(text(
                    "DELETE FROM notifications WHERE related_entity_id = ANY(:e)"
                ), {"e": eventos})
                await c.execute(delete(Reversal).where(
                    Reversal.original_event_id.in_(eventos)
                    | Reversal.reversal_event_id.in_(eventos)))
                for sub in (BirdMovement, EggMovement, FeedMovement, InspectionDetail,
                            ApprovalAction):
                    await c.execute(delete(sub).where(sub.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
        await c.execute(delete(SapReference).where(SapReference.sap_code.like(f"{PREFIJO}%")))
    await e.dispose()


async def _fijar_estado(motor, event_id, estado):
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        evento = (await s.execute(select(OperationalEvent).where(
            OperationalEvent.id == event_id))).scalar_one()
        evento.status = estado
        await s.commit()


async def _estado(motor, event_id) -> str:
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        estado = (await s.execute(select(OperationalEvent.status).where(
            OperationalEvent.id == event_id))).scalar_one()
        return estado.value


async def _contrapartida(motor, event_id) -> int:
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return (await s.execute(select(Reversal.reversal_event_id).where(
            Reversal.original_event_id == event_id))).scalar_one()


async def _orden(client, cab, cantidad: int = ORDENADO) -> str:
    codigo = f"{PREFIJO}OC-{uuid.uuid4().hex[:8].upper()}"
    r = await client.post("/api/v1/sap/references/import", headers=cab, json={
        "references": [{
            "ref_type": "purchase_order", "sap_code": codigo,
            "description": "OC de prueba R-193", "quantity": cantidad,
        }],
    })
    assert r.status_code in (200, 201), r.text
    return codigo


async def _lote(client, cab, ids) -> int:
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": ids["company_id"], "farm_id": ids["farm_id"],
        "house_id": ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _recepcion(client, cab, ids, lote, n, oc):
    return await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": lote, "farm_id": ids["farm_id"], "house_id": ids["house_id"],
        "event_type": "bird_reception", "event_date": iso_days_ago(0),
        "sap_document_ref": oc,
        "bird_movements": [{"sex": "mixed", "quantity": n, "house_id": ids["house_id"]}],
    })


async def _recepcion_aprobada(client, cab, ids, motor, lote, n, oc) -> int:
    r = await _recepcion(client, cab, ids, lote, n, oc)
    assert r.status_code == 201, r.text
    await _fijar_estado(motor, r.json()["id"], EventStatus.APPROVED)
    return r.json()["id"]


async def _solicitar_reverso(client, cab, event_id):
    return await client.post("/api/v1/reversals", headers=cab,
                             json={"event_id": event_id, "reason": f"{PREFIJO}prueba"})


async def _aprobar_contrapartida(client, cab_aprobador, cp_id):
    r = await client.post(f"/api/v1/review/start/{cp_id}", headers=cab_aprobador)
    assert r.status_code in (200, 201), r.text
    r = await client.post("/api/v1/approvals/approve", headers=cab_aprobador,
                          json={"event_id": cp_id})
    assert r.status_code in (200, 201), r.text
    return r


async def _reverso_efectivo(client, motor, cab, cab_aprobador, event_id) -> int:
    r = await _solicitar_reverso(client, cab, event_id)
    assert r.status_code == 201, r.text
    cp = await _contrapartida(motor, event_id)
    await _aprobar_contrapartida(client, cab_aprobador, cp)
    return cp


async def _rechazar_contrapartida(client, cab_aprobador, cp_id):
    r = await client.post(f"/api/v1/review/start/{cp_id}", headers=cab_aprobador)
    assert r.status_code in (200, 201), r.text
    r = await client.post("/api/v1/approvals/reject", headers=cab_aprobador,
                          json={"event_id": cp_id, "observations": f"{PREFIJO}no procede"})
    assert r.status_code in (200, 201), r.text
    return r


# ── R193-01 · el reverso efectivo devuelve la capacidad a la OC ───────────────

async def test_r193_01_tras_un_reverso_efectivo_la_oc_recupera_su_capacidad(
    client, auth_headers, seeded_ids, motor
):
    """`AC01` · A=400 aprobada, reverso efectivo, B=400 ⇒ **201** (hoy 400 «ya recibidas: 800»)."""
    oc = await _orden(client, auth_headers)
    lote = await _lote(client, auth_headers, seeded_ids)
    a = await _recepcion_aprobada(client, auth_headers, seeded_ids, motor, lote, 400, oc)

    aprobador = _cabecera(seeded_ids["user_approver_id"])
    cp = await _reverso_efectivo(client, motor, auth_headers, aprobador, a)
    assert await _estado(motor, a) == "reversed"  # CONTROL
    assert await _estado(motor, cp) == "reversed"

    b = await _recepcion(client, auth_headers, seeded_ids, lote, 400, oc)
    assert b.status_code == 201, (
        f"tras el reverso efectivo la OC debe admitir de nuevo su capacidad: {b.status_code} {b.text}"
    )


# ── R193-02 · el reverso pendiente no libera la OC ────────────────────────────

async def test_r193_02_el_reverso_pendiente_no_libera_la_oc(
    client, auth_headers, seeded_ids, motor
):
    """`AC02` · con la contrapartida sin decidir, B=700 sigue bloqueada; al aprobarla, pasa."""
    oc = await _orden(client, auth_headers)
    lote = await _lote(client, auth_headers, seeded_ids)
    a = await _recepcion_aprobada(client, auth_headers, seeded_ids, motor, lote, 400, oc)

    r = await _solicitar_reverso(client, auth_headers, a)
    assert r.status_code == 201, r.text
    cp = await _contrapartida(motor, a)
    assert await _estado(motor, cp) == "pending_review"  # CONTROL

    bloqueada = await _recepcion(client, auth_headers, seeded_ids, lote, 700, oc)
    assert bloqueada.status_code == 400, (
        f"un reverso sin decidir no libera la OC: {bloqueada.text}"
    )

    aprobador = _cabecera(seeded_ids["user_approver_id"])
    await _aprobar_contrapartida(client, aprobador, cp)

    admitida = await _recepcion(client, auth_headers, seeded_ids, lote, 700, oc)
    assert admitida.status_code == 201, (
        f"aprobado el reverso, la OC vuelve a estar íntegra: {admitida.status_code} {admitida.text}"
    )


# ── R193-03 · la contrapartida rechazada no cuenta ────────────────────────────

async def test_r193_03_la_contrapartida_rechazada_no_cuenta(
    client, auth_headers, seeded_ids, motor
):
    """`AC03` · A=400 contada, reverso rechazado (no efectivo) · empresa ajena no influye."""
    assert seeded_ids.get("company_id_2"), "la semilla debe tener la segunda empresa"
    # CONTROL de inquilino: misma `sap_code` en otra empresa — no puede aportar acumulado.
    from app.integrations.sap.models import SapReference, SapReferenceType

    oc = await _orden(client, auth_headers)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        s.add(SapReference(company_id=seeded_ids["company_id_2"], sap_code=oc,
                           ref_type=SapReferenceType.PURCHASE_ORDER, quantity=ORDENADO,
                           description="OC gemela de otra empresa", is_active=True))
        await s.commit()

    lote = await _lote(client, auth_headers, seeded_ids)
    a = await _recepcion_aprobada(client, auth_headers, seeded_ids, motor, lote, 400, oc)

    r = await _solicitar_reverso(client, auth_headers, a)
    assert r.status_code == 201, r.text
    cp = await _contrapartida(motor, a)
    aprobador = _cabecera(seeded_ids["user_approver_id"])
    await _rechazar_contrapartida(client, aprobador, cp)
    assert await _estado(motor, cp) == "rejected"  # CONTROL

    b = await _recepcion(client, auth_headers, seeded_ids, lote, 600, oc)
    assert b.status_code == 201, (
        f"una contrapartida rechazada no es una recepción: {b.status_code} {b.text}"
    )
    b2 = await _recepcion(client, auth_headers, seeded_ids, lote, 1, oc)
    assert b2.status_code == 400 and "ya recibidas: 1000" in b2.text, (
        f"el mensaje debe reportar el neto (1000): {b2.status_code} {b2.text}"
    )


# ── R193-04 · dos reversos dejan el acumulado en cero ─────────────────────────

async def test_r193_04_dos_reversos_dejan_el_acumulado_en_cero(
    client, auth_headers, seeded_ids, motor
):
    """`AC04` · 400+400 revertidas ⇒ C=1000 pasa; D=1001 excede."""
    oc = await _orden(client, auth_headers)
    lote = await _lote(client, auth_headers, seeded_ids)
    a1 = await _recepcion_aprobada(client, auth_headers, seeded_ids, motor, lote, 400, oc)
    a2 = await _recepcion_aprobada(client, auth_headers, seeded_ids, motor, lote, 400, oc)

    aprobador = _cabecera(seeded_ids["user_approver_id"])
    await _reverso_efectivo(client, motor, auth_headers, aprobador, a1)
    await _reverso_efectivo(client, motor, auth_headers, aprobador, a2)

    c = await _recepcion(client, auth_headers, seeded_ids, lote, 1000, oc)
    assert c.status_code == 201, (
        f"con dos reversos el acumulado es 0 y la OC admite 1000: {c.status_code} {c.text}"
    )
    d = await _recepcion(client, auth_headers, seeded_ids, lote, 1, oc)
    assert d.status_code == 400 and "ya recibidas: 1000" in d.text, (
        f"un exceso real debe reportar el neto: {d.status_code} {d.text}"
    )


# ── R193-05 · el mensaje reporta el neto ──────────────────────────────────────

async def test_r193_05_el_mensaje_reporta_el_neto(
    client, auth_headers, seeded_ids, motor
):
    """`AC01`/`AC05` · A=400 revertida + B=400 vigente ⇒ C=700 reporta «ya recibidas: 400»."""
    oc = await _orden(client, auth_headers)
    lote = await _lote(client, auth_headers, seeded_ids)
    a = await _recepcion_aprobada(client, auth_headers, seeded_ids, motor, lote, 400, oc)

    aprobador = _cabecera(seeded_ids["user_approver_id"])
    await _reverso_efectivo(client, motor, auth_headers, aprobador, a)
    await _recepcion_aprobada(client, auth_headers, seeded_ids, motor, lote, 400, oc)

    c = await _recepcion(client, auth_headers, seeded_ids, lote, 700, oc)
    assert c.status_code == 400, c.text
    assert "ya recibidas: 400" in c.text, (
        f"el acumulado del mensaje es el **neto** (solo la recepción vigente): {c.text}"
    )
