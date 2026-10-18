"""BR-23 · una orden de compra de otra cadena productiva no puede usarse en la recepción.

La cadena de una OC se deriva de `business_unit_code` del mapping `PLANT` de **todos** sus
items: si la cadena es única y no coincide con el `bird_type` del lote, la recepción se
rechaza (`400`, `rule == "BR-23"`). Cuando no es derivable —sin items, item sin mapping o
items de cadenas distintas— la regla no aplica y la recepción se acepta.

Datos pequeños: la OC se carga en modo manual, sin tocar SAP real; los centros llevan un
`sap_key` aleatorio por prueba porque el mapping es único por (sistema, mandante, tipo,
clave).
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.inbound.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.integrations.sap.inbound.models import SOURCE_SYSTEM, SapEntityMapping
from app.masters.models import Lot
from tests.time_reference import iso_days_ago

PREFIJO = "BR23-"
CENTRO = "BR23P"
CLIENTE = "100"
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
        await c.execute(delete(SapEntityMapping).where(
            SapEntityMapping.sap_key.like(f"{CENTRO}%")))
    await e.dispose()


def _centro() -> str:
    """Centro SAP único por prueba: el mapping no se hereda entre pruebas."""
    return f"{CENTRO}{uuid.uuid4().hex[:4].upper()}"


async def _mapear_centro(motor, company_id, sap_key, business_unit_code):
    """Declara el centro SAP con su cadena productiva (`business_unit_code`)."""
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        s.add(SapEntityMapping(
            source_system=SOURCE_SYSTEM, client=CLIENTE, entity_type="PLANT",
            sap_key=sap_key, company_id=company_id,
            business_unit_code=business_unit_code, is_active=True))
        await s.commit()


async def _orden(client, cab, *, plant=None, items=None, cantidad=ORDENADO):
    """Una orden de compra cargada en modo manual, sin tocar SAP real."""
    codigo = f"{PREFIJO}{uuid.uuid4().hex[:8].upper()}"
    extra: dict = {"vendor": "BR23-V"}
    if items is not None:
        extra["items"] = items
    elif plant is not None:
        extra["items"] = [{"plant": plant, "quantity": cantidad, "unit": "UN"}]
    r = await client.post("/api/v1/sap/references/import", headers=cab, json={
        "references": [{
            "ref_type": "purchase_order", "sap_code": codigo,
            "description": "Orden de prueba BR-23", "quantity": cantidad,
            "unit": "UN", "extra_data": extra,
        }],
    })
    assert r.status_code in (200, 201), r.text
    return codigo


async def _lote(client, cab, ids, bird_type="broiler"):
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": ids["company_id"], "farm_id": ids["farm_id"],
        "house_id": ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": bird_type, "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _recibir(client, cab, ids, lot_id, orden, cantidad=100, bird_type="broiler"):
    cuerpo = {
        "lot_id": lot_id, "farm_id": ids["farm_id"], "house_id": ids["house_id"],
        "event_type": "bird_reception", "event_date": iso_days_ago(0),
        "sap_document_ref": orden,
        "bird_movements": [{"sex": "mixed", "quantity": cantidad}],
    }
    if bird_type == "breeder":
        # `BR-20`: la recepción de reproductoras declara el cuadre explícitamente.
        cuerpo.update({"received_total": cantidad, "dead_on_arrival": 0,
                       "rejected_on_arrival": 0})
    return await client.post("/api/v1/operations", headers=cab, json=cuerpo)


# ── la regla ─────────────────────────────────────────────────────────────────

async def test_br23_oc_de_engorde_rechazada_en_lote_reproductoras(
    client, auth_headers, seeded_ids, motor
):
    """Una OC de la cadena de engorde no se recibe en un lote de reproductoras."""
    centro = _centro()
    await _mapear_centro(motor, seeded_ids["company_id"], centro, "broiler")
    orden = await _orden(client, auth_headers, plant=centro)
    lote = await _lote(client, auth_headers, seeded_ids, bird_type="breeder")

    r = await _recibir(client, auth_headers, seeded_ids, lote, orden, bird_type="breeder")

    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "BR-23", r.text


async def test_br23_oc_de_la_misma_cadena_aceptada(
    client, auth_headers, seeded_ids, motor
):
    """La misma cadena productiva: la recepción pasa."""
    centro = _centro()
    await _mapear_centro(motor, seeded_ids["company_id"], centro, "breeder")
    orden = await _orden(client, auth_headers, plant=centro)
    lote = await _lote(client, auth_headers, seeded_ids, bird_type="breeder")

    r = await _recibir(client, auth_headers, seeded_ids, lote, orden, bird_type="breeder")

    assert r.status_code == 201, r.text


# ── el selector de órdenes ───────────────────────────────────────────────────

async def test_br23_listado_filtra_por_cadena_derivada(
    client, auth_headers, seeded_ids, motor
):
    """El listado filtra por la cadena derivada y expone `business_unit_code`.

    Se piden las OC de `breeder`: entran la mapeada a esa cadena y la que no tiene cadena
    derivable (sin mapping), y queda fuera la mapeada a `broiler`. La respuesta trae el
    atributo derivado para cada orden.
    """
    centro_breeder, centro_broiler = _centro(), _centro()
    await _mapear_centro(motor, seeded_ids["company_id"], centro_breeder, "breeder")
    await _mapear_centro(motor, seeded_ids["company_id"], centro_broiler, "broiler")
    orden_breeder = await _orden(client, auth_headers, plant=centro_breeder)
    orden_broiler = await _orden(client, auth_headers, plant=centro_broiler)
    orden_sin_mapping = await _orden(client, auth_headers, plant=_centro())

    r = await client.get(
        "/api/v1/sap/references?ref_type=purchase_order&business_unit=breeder&limit=200",
        headers=auth_headers)
    assert r.status_code == 200, r.text
    filas = {f["sap_code"]: f for f in r.json()["references"]}

    assert orden_breeder in filas and orden_sin_mapping in filas, sorted(filas)
    assert orden_broiler not in filas, "la OC de otra cadena no se ofrece"

    assert filas[orden_breeder]["business_unit_code"] == "breeder"
    assert filas[orden_sin_mapping]["business_unit_code"] is None

    # Sin el parámetro, el listado conserva su comportamiento: aparecen las tres.
    completo = await client.get("/api/v1/sap/references?ref_type=purchase_order&limit=200",
                                headers=auth_headers)
    assert completo.status_code == 200, completo.text
    codigos = {f["sap_code"] for f in completo.json()["references"]}
    assert {orden_breeder, orden_broiler, orden_sin_mapping} <= codigos
    broiler_fila = next(f for f in completo.json()["references"]
                        if f["sap_code"] == orden_broiler)
    assert broiler_fila["business_unit_code"] == "broiler"


async def test_br23_oc_sin_mapping_se_permite(
    client, auth_headers, seeded_ids, motor
):
    """Sin mapping no hay cadena derivable: la regla no aplica."""
    centro = _centro()  # declarado pero nunca mapeado
    orden_sin_mapping = await _orden(client, auth_headers, plant=centro)
    lote = await _lote(client, auth_headers, seeded_ids, bird_type="breeder")

    primera = await _recibir(client, auth_headers, seeded_ids, lote, orden_sin_mapping,
                            bird_type="breeder")
    assert primera.status_code == 201, primera.text

    orden_sin_items = await _orden(client, auth_headers)
    segunda = await _recibir(client, auth_headers, seeded_ids, lote, orden_sin_items,
                             bird_type="breeder")
    assert segunda.status_code == 201, segunda.text


async def test_br23_cadenas_mixtas_se_permiten(
    client, auth_headers, seeded_ids, motor
):
    """Items de dos cadenas distintas: no hay cadena única, no hay rechazo."""
    centro_breeder, centro_broiler = _centro(), _centro()
    await _mapear_centro(motor, seeded_ids["company_id"], centro_breeder, "breeder")
    await _mapear_centro(motor, seeded_ids["company_id"], centro_broiler, "broiler")
    orden = await _orden(client, auth_headers, items=[
        {"plant": centro_breeder, "quantity": 600, "unit": "UN"},
        {"plant": centro_broiler, "quantity": 400, "unit": "UN"},
    ])
    lote = await _lote(client, auth_headers, seeded_ids, bird_type="breeder")

    r = await _recibir(client, auth_headers, seeded_ids, lote, orden, bird_type="breeder")

    assert r.status_code == 201, r.text

