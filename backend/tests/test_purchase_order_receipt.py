"""Recepción contra orden de compra — `GA-REM-035`, deuda `GA-TD-014`.

Cubre `AC01`…`AC12`.

`OD-04`, resuelta por el propietario: **una misma orden de compra puede recibirse mediante
múltiples entregas parciales**. De ahí que repetir la referencia no sea un error y que la
protección recaiga sobre la **cantidad acumulada**.

`validate_oc_limit` comparaba solo la recepción en curso: tres entregas de 400 contra una
orden de 1000 pasaban las tres y sumaban 1200.

Cifras pequeñas y redondas, calculadas a mano.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago

PREFIJO = "OC-TEST-"
ORDENADO = 1_000


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.integrations.sap.models import SapReference
    from app.lots.models import LotPhase, OpeningBalance
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, InspectionDetail, OperationalEvent,
    )

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(ids)))).scalars().all()
            if eventos:
                for sub in (BirdMovement, EggMovement, FeedMovement, InspectionDetail):
                    await c.execute(delete(sub).where(sub.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
        await c.execute(delete(SapReference).where(SapReference.sap_code.like(f"{PREFIJO}%")))
    await e.dispose()


async def _orden(client, cab, company_id, cantidad=ORDENADO):
    """Una orden de compra cargada en modo manual, sin tocar SAP real."""
    codigo = f"{PREFIJO}{uuid.uuid4().hex[:8].upper()}"
    r = await client.post("/api/v1/sap/references/import", headers=cab, json={
        "references": [{
            "ref_type": "purchase_order", "sap_code": codigo,
            "description": "Orden de prueba", "quantity": cantidad,
        }],
    })
    assert r.status_code in (200, 201), r.text
    return codigo


async def _lote(client, cab, ids):
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": ids["company_id"], "farm_id": ids["farm_id"],
        "house_id": ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _recibir(client, cab, ids, lot_id, orden, cantidad):
    return await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": lot_id, "farm_id": ids["farm_id"], "house_id": ids["house_id"],
        "event_type": "bird_reception", "event_date": iso_days_ago(0),
        "sap_document_ref": orden,
        "bird_movements": [{"sex": "mixed", "quantity": cantidad}],
    })


async def _recepciones(motor, orden):
    from app.operations.models import OperationalEvent
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return (await s.execute(select(OperationalEvent).where(
            OperationalEvent.sap_document_ref == orden))).scalars().all()


# ── AC01 · AC02 · AC10 · las entregas parciales ───────────────────────────────

async def test_t_014_01_varias_entregas_parciales_contra_la_misma_orden(
    client, auth_headers, seeded_ids, motor
):
    """`AC01`, `AC02`, `AC10` · `OD-04` hecha prueba.

    La segunda recepción con la **misma** referencia debe aceptarse: repetirla no es un
    error. Antes la rechazaba la regla de no duplicar documentos SAP.
    """
    orden = await _orden(client, auth_headers, seeded_ids["company_id"])
    lote = await _lote(client, auth_headers, seeded_ids)

    primera = await _recibir(client, auth_headers, seeded_ids, lote, orden, 300)
    assert primera.status_code == 201, f"la primera parcial debe aceptarse: {primera.text}"

    segunda = await _recibir(client, auth_headers, seeded_ids, lote, orden, 250)
    assert segunda.status_code == 201, (
        f"OD-04: la segunda parcial contra la misma OC debe aceptarse: {segunda.text}"
    )

    tercera = await _recibir(client, auth_headers, seeded_ids, lote, orden, 200)
    assert tercera.status_code == 201, tercera.text

    # `AC10` · la referencia queda guardada en el campo tipado, que es lo que `GA-TD-014` pedía.
    eventos = await _recepciones(motor, orden)
    assert len(eventos) == 3, f"deben quedar las tres recepciones: {len(eventos)}"
    assert all(e.sap_document_ref == orden for e in eventos)


# ── AC06 · el resto exacto ────────────────────────────────────────────────────

async def test_t_014_02_el_resto_exacto_se_acepta(
    client, auth_headers, seeded_ids, motor
):
    """`AC06` · `acumulado + nueva = ordenada` cabe.

    Distingue un `>` de un `>=` mal puesto: con `>=` esta recepción se rechazaría.
    """
    orden = await _orden(client, auth_headers, seeded_ids["company_id"])
    lote = await _lote(client, auth_headers, seeded_ids)

    assert (await _recibir(client, auth_headers, seeded_ids, lote, orden, 750)).status_code == 201
    exacta = await _recibir(client, auth_headers, seeded_ids, lote, orden, 250)
    assert exacta.status_code == 201, (
        f"completar la orden exactamente debe aceptarse: {exacta.text}"
    )


# ── AC05 · AC07 · AC08 · AC11 · el exceso ─────────────────────────────────────

async def test_t_014_03_el_exceso_repartido_se_rechaza(
    client, auth_headers, seeded_ids, motor
):
    """`AC05`, `AC07`, `AC08`, `AC11` · el caso que la regla anterior no atrapaba.

    900 recibidos y 200 nuevos superan 1000, **aunque cada recepción por separado quepa**.
    """
    orden = await _orden(client, auth_headers, seeded_ids["company_id"])
    lote = await _lote(client, auth_headers, seeded_ids)

    assert (await _recibir(client, auth_headers, seeded_ids, lote, orden, 900)).status_code == 201

    excedida = await _recibir(client, auth_headers, seeded_ids, lote, orden, 200)
    assert excedida.status_code == 400, (
        f"900 + 200 supera la orden de 1000 y debe rechazarse: {excedida.status_code}"
    )
    assert excedida.json().get("rule") == "BR-18", excedida.json()
    # El motivo es la **cantidad**, no la duplicidad de la referencia.
    assert "duplic" not in excedida.json()["detail"].lower(), excedida.json()

    # `AC08` · sin efectos: la recepción rechazada no existe.
    eventos = await _recepciones(motor, orden)
    assert len(eventos) == 1, f"el rechazo dejó un evento: {len(eventos)}"


async def test_t_014_04_una_unidad_de_mas_se_rechaza(
    client, auth_headers, seeded_ids, motor
):
    """`AC11` · sin tolerancia. Una unidad por encima basta."""
    orden = await _orden(client, auth_headers, seeded_ids["company_id"])
    lote = await _lote(client, auth_headers, seeded_ids)

    assert (await _recibir(client, auth_headers, seeded_ids, lote, orden,
                           ORDENADO)).status_code == 201
    una_mas = await _recibir(client, auth_headers, seeded_ids, lote, orden, 1)
    assert una_mas.status_code == 400, (
        f"no hay tolerancia: una unidad de más se rechaza ({una_mas.status_code})"
    )


# ── AC03 · lo cancelado no cuenta ─────────────────────────────────────────────

async def test_t_014_05_una_recepcion_cancelada_deja_de_contar(
    client, auth_headers, seeded_ids, motor
):
    """`AC03` · el acumulado sigue el precedente de los ocho saldos: excluye `CANCELLED`."""
    from app.operations.models import EventStatus, OperationalEvent

    orden = await _orden(client, auth_headers, seeded_ids["company_id"])
    lote = await _lote(client, auth_headers, seeded_ids)

    a_cancelar = await _recibir(client, auth_headers, seeded_ids, lote, orden, 400)
    assert a_cancelar.status_code == 201, a_cancelar.text
    assert (await _recibir(client, auth_headers, seeded_ids, lote, orden, 300)).status_code == 201

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        evento = (await s.execute(select(OperationalEvent).where(
            OperationalEvent.id == a_cancelar.json()["id"]))).scalar_one()
        evento.status = EventStatus.CANCELLED
        await s.commit()

    # Acumulado vigente = 300. Caben 700, y con los 400 cancelados contando no cabrían.
    r = await _recibir(client, auth_headers, seeded_ids, lote, orden, 700)
    assert r.status_code == 201, (
        f"lo cancelado no debe contar en el acumulado: {r.text}"
    )


# ── AC09 · pertenencia ────────────────────────────────────────────────────────

async def test_t_014_06_la_orden_de_otra_empresa_no_se_encuentra(
    client, auth_headers, seeded_ids, motor
):
    """`AC09` · CONTROL y TRATAMIENTO sobre la misma petición.

    Lo único que cambia es de quién es la orden: si el límite se aplicara sin filtrar por
    compañía, la ajena impondría su cantidad sobre una recepción que no le corresponde.
    """
    lote = await _lote(client, auth_headers, seeded_ids)

    # Una orden pequeña en la **otra** compañía.
    cambio = await client.post("/api/v1/switch-company", headers=auth_headers,
                               json={"company_id": seeded_ids["company_id_2"]})
    assert cambio.status_code == 200, cambio.text
    admin_2 = {"Authorization": f"Bearer {cambio.json()['access_token']}"}
    ajena = await _orden(client, admin_2, seeded_ids["company_id_2"], cantidad=10)

    # CONTROL · una orden propia y amplia acepta la recepción.
    propia = await _orden(client, auth_headers, seeded_ids["company_id"])
    ok = await _recibir(client, auth_headers, seeded_ids, lote, propia, 500)
    assert ok.status_code == 201, f"CONTROL falló: {ok.text}"

    # TRATAMIENTO · la orden ajena, de solo 10, no debe imponer su límite aquí.
    cruzada = await _recibir(client, auth_headers, seeded_ids, lote, ajena, 500)
    assert cruzada.status_code == 201, (
        "una orden de otra compañía no debe encontrarse ni aplicar su límite: "
        f"{cruzada.status_code} {cruzada.text}"
    )


# ── AC12 · sin cierre automático ──────────────────────────────────────────────

async def test_t_014_07_completar_la_orden_no_la_cierra(
    client, auth_headers, seeded_ids, motor
):
    """`AC12` · alcanzar el 100 % no cambia el estado de la referencia.

    Se comprueba explícitamente para que nadie añada un cierre sin requisito: `OD-04`
    respondió si caben entregas parciales, no qué ocurre al completar.
    """
    from app.integrations.sap.models import SapReference

    orden = await _orden(client, auth_headers, seeded_ids["company_id"])
    lote = await _lote(client, auth_headers, seeded_ids)

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        antes = (await s.execute(select(SapReference).where(
            SapReference.sap_code == orden))).scalar_one()
        estado_antes = getattr(antes, "status", None)

    assert (await _recibir(client, auth_headers, seeded_ids, lote, orden,
                           ORDENADO)).status_code == 201

    async with fabrica() as s:
        despues = (await s.execute(select(SapReference).where(
            SapReference.sap_code == orden))).scalar_one()
        assert getattr(despues, "status", None) == estado_antes, (
            "completar la orden no debe cambiar su estado: no hay requisito de cierre"
        )
