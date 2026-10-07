"""SPEC 005 · Promoción controlada a `sap_references` — `AC-HANA-31…33`.

La orden de compra sincronizada tiene que alimentar el contrato que la recepción ya usa:
una referencia por OC y empresa, con `quantity` funcionalmente correcta, para que `BR-18`
siga siendo aplicable **sin tocar la regla**.

Dataset (`fake_hana.default_dataset`), sociedad 1000:

    OC …0001  pos 00010  hembras  1000 UN  centro 1100
              pos 00020  machos    150 UN  centro 1100      → ordenado 1150 UN
              historial: entrada 300 (S) · reverso 100 (H)  → recibido en SAP 200
    OC …0002  pos 00010  alimento 20000 KG centro 1100
    STO …0001 pos 00010  alimento  5000 KG 1100 → 1200
"""
from __future__ import annotations

import copy
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.integrations.sap.inbound.errors import ErrorCode
from app.integrations.sap.inbound.fake_hana import FakeHana, default_dataset
from app.integrations.sap.inbound.registry import HanaObject
from app.integrations.sap.inbound.service import SapInboundService
from app.masters.models import Lot
from tests.sap_hana_fixtures import (  # noqa: F401  (`esc` es una fixture)
    adaptador_de_prueba,
    cfg_de_prueba,
    esc,
    filas,
    mapear,
    referencias,
    registros,
    sincronizar,
    ventana_amplia,
)
from tests.time_reference import iso_days_ago

pytestmark = pytest.mark.asyncio

VENTANA = ventana_amplia()
OC = [HanaObject.PURCHASE_ORDER]


async def _oc(esc, codigo, empresa="a"):
    refs = [r for r in await referencias(esc, "PURCHASE_ORDER", empresa) if r["sap_code"] == codigo]
    assert len(refs) <= 1, "nunca dos referencias para la misma OC en una empresa"
    return refs[0] if refs else None


async def _cabecera(esc, codigo, empresa="a"):
    return next(r for r in await registros(esc, "purchase_order", empresa)
                if r["payload_json"]["EBELN"] == codigo)


def _posiciones(datos, codigo):
    return [f for f in datos["purchase_order_item"] if f["EBELN"] == codigo]


# ── Cantidad y desglose ─────────────────────────────────────────────────────

async def test_purchase_order_promotes_quantity(esc):
    """`AC-HANA-32`. Σ de posiciones activas de unidad homogénea, con su desglose."""
    await sincronizar(esc, objetos=OC, **VENTANA)
    ref = await _oc(esc, esc["oc"])

    assert ref is not None and ref["is_active"] is True
    assert ref["quantity"] == 1150 and ref["unit"] == "UN"
    extra = ref["extra_data"]
    assert extra["source"] == "SAP_HANA_CLOUD" and extra["company_code"] == "1000"
    assert extra["ordered_quantity"] == 1150
    assert [(i["item"], i["quantity"], i["unit"], i["plant"]) for i in extra["items"]] == [
        ("00010", 1000, "UN", "1100"), ("00020", 150, "UN", "1100")]
    assert all(i["material"] and i["description"] for i in extra["items"])
    assert extra["vendor"] and extra["document_date"] and extra["document_type"]
    assert ref["description"]
    assert ref["imported_by_id"] == esc["ids"]["analista_a"]

    cab = await _cabecera(esc, esc["oc"])
    assert cab["promotion_status"] == "PROMOTED" and cab["promoted_reference_id"] == ref["id"]
    assert extra["inbound_record_id"] == cab["id"] and extra["payload_hash"] == cab["payload_hash"]


async def test_purchase_order_other_unit_keeps_its_own_total(esc):
    await sincronizar(esc, objetos=OC, **VENTANA)
    ref = await _oc(esc, esc["oc_alimento"])
    assert (ref["quantity"], ref["unit"]) == (20000, "KG")


async def test_purchase_order_received_quantity_nets_reversals(esc):
    """El reverso en SAP resta de lo recibido; lo ordenado no cambia."""
    await sincronizar(esc, objetos=OC, **VENTANA)
    extra = (await _oc(esc, esc["oc"]))["extra_data"]
    assert extra["received_quantity"] == 200, "300 de entrada − 100 de reverso"
    assert extra["history_summary"]["receipts"] == 300
    assert extra["history_summary"]["reversals"] == 100
    assert extra["ordered_quantity"] == 1150


async def test_purchase_order_deleted_item_is_excluded(esc):
    datos = copy.deepcopy(esc["datos"])
    next(p for p in _posiciones(datos, esc["oc"]) if p["EBELP"] == "00020")["LOEKZ"] = "L"
    await sincronizar(esc, objetos=OC, fake=FakeHana(datos), **VENTANA)
    ref = await _oc(esc, esc["oc"])
    assert ref["quantity"] == 1000
    borrada = next(i for i in ref["extra_data"]["items"] if i["item"] == "00020")
    assert borrada["deleted"] is True, "se conserva en el desglose, marcada"


async def test_purchase_order_fully_deleted_becomes_inactive(esc):
    await sincronizar(esc, objetos=OC, **VENTANA)
    datos = copy.deepcopy(esc["datos"])
    next(c for c in datos["purchase_order"] if c["EBELN"] == esc["oc"])["LOEKZ"] = "L"
    await sincronizar(esc, objetos=OC, fake=FakeHana(datos), **VENTANA)
    ref = await _oc(esc, esc["oc"])
    assert ref["is_active"] is False, "una OC anulada deja de ofrecerse"
    assert ref["extra_data"]["status"] == "CANCELLED"
    assert ref["quantity"] == 1150, "el límite histórico no se borra"


async def test_purchase_order_mixed_units_blocks_promotion(esc):
    """`Q4`. No se suman unidades incompatibles ni se promueve una OC sin cantidad."""
    datos = copy.deepcopy(esc["datos"])
    next(p for p in _posiciones(datos, esc["oc"]) if p["EBELP"] == "00020")["MEINS"] = "KG"
    await sincronizar(esc, objetos=OC, fake=FakeHana(datos), **VENTANA)

    assert await _oc(esc, esc["oc"]) is None
    cab = await _cabecera(esc, esc["oc"])
    assert cab["promotion_status"] == "BLOCKED"
    assert cab["error_code"] == ErrorCode.SAP_VALIDATION_ERROR.value
    assert await _oc(esc, esc["oc_alimento"]) is not None, "la otra OC no se ve afectada"


async def test_purchase_order_with_item_on_unmapped_plant_is_blocked(esc):
    datos = copy.deepcopy(esc["datos"])
    next(p for p in _posiciones(datos, esc["oc"]) if p["EBELP"] == "00020")["WERKS"] = "1200"
    await sincronizar(esc, objetos=OC, fake=FakeHana(datos), **VENTANA)

    assert await _oc(esc, esc["oc"]) is None, "promover solo la mitad dejaría un límite falso"
    cab = await _cabecera(esc, esc["oc"])
    assert cab["promotion_status"] == "BLOCKED"
    assert cab["error_code"] == ErrorCode.SAP_MAPPING_PENDING.value


async def test_purchase_order_without_items_is_not_promoted(esc):
    datos = copy.deepcopy(esc["datos"])
    datos["purchase_order_item"] = [p for p in datos["purchase_order_item"] if p["EBELN"] != esc["oc"]]
    await sincronizar(esc, objetos=OC, fake=FakeHana(datos), **VENTANA)
    assert await _oc(esc, esc["oc"]) is None
    assert (await _cabecera(esc, esc["oc"]))["promotion_status"] == "READY_FOR_PROMOTION"


# ── Upsert ──────────────────────────────────────────────────────────────────

async def test_purchase_order_resync_updates_the_same_reference(esc):
    await sincronizar(esc, objetos=OC, **VENTANA)
    antes = await _oc(esc, esc["oc"])
    datos = copy.deepcopy(esc["datos"])
    next(p for p in _posiciones(datos, esc["oc"]) if p["EBELP"] == "00010")["MENGE"] = 1200
    await sincronizar(esc, objetos=OC, fake=FakeHana(datos), **VENTANA)
    despues = await _oc(esc, esc["oc"])
    assert despues["id"] == antes["id"] and despues["quantity"] == 1350


async def test_purchase_order_adopts_existing_manual_reference(esc):
    """Una referencia cargada a mano con la misma clave se actualiza: no se duplica."""
    await filas_insertar_referencia(esc, esc["oc"], cantidad=5)
    await sincronizar(esc, objetos=OC, **VENTANA)
    ref = await _oc(esc, esc["oc"])
    assert ref["quantity"] == 1150 and ref["extra_data"]["source"] == "SAP_HANA_CLOUD"


async def test_purchase_order_duplicate_manual_references_block_promotion(esc):
    await filas_insertar_referencia(esc, esc["oc"], cantidad=5)
    await filas_insertar_referencia(esc, esc["oc"], cantidad=7)
    await sincronizar(esc, objetos=OC, **VENTANA)
    cab = await _cabecera(esc, esc["oc"])
    assert cab["promotion_status"] == "BLOCKED"
    assert cab["error_code"] == ErrorCode.SAP_VALIDATION_ERROR.value
    cantidades = sorted(r["quantity"] for r in await referencias(esc, "PURCHASE_ORDER")
                        if r["sap_code"] == esc["oc"])
    assert cantidades == [5, 7], "ante un duplicado no se elige uno ni se sobrescribe"


async def filas_insertar_referencia(esc, codigo, cantidad):
    from app.integrations.sap.models import SapReference, SapReferenceType

    async with esc["fabrica"]() as s:
        s.add(SapReference(company_id=esc["a"], ref_type=SapReferenceType.PURCHASE_ORDER,
                           sap_code=codigo, description="manual", quantity=cantidad,
                           is_active=True))
        await s.commit()


# ── Aislamiento entre empresas ──────────────────────────────────────────────

async def test_purchase_order_cross_company_isolation(esc):
    """El mismo `EBELN` en dos sociedades son dos órdenes: cada empresa ve la suya."""
    datos = copy.deepcopy(esc["datos"])
    cab_a = next(c for c in datos["purchase_order"] if c["EBELN"] == esc["oc"])
    datos["purchase_order"].append({**cab_a, "BUKRS": "2000"})
    datos["purchase_order_item"].append(
        {**_posiciones(datos, esc["oc"])[0], "BUKRS": "2000", "WERKS": "2100", "MENGE": 77})

    await sincronizar(esc, objetos=OC, fake=FakeHana(datos), **VENTANA)
    assert (await _oc(esc, esc["oc"]))["quantity"] == 1150
    assert await _oc(esc, esc["oc"], "b") is None, "sincronizar A no crea nada en B"

    await sincronizar(esc, actor="actor_b", objetos=OC, fake=FakeHana(datos), **VENTANA)
    assert (await _oc(esc, esc["oc"], "b"))["quantity"] == 77
    assert (await _oc(esc, esc["oc"]))["quantity"] == 1150, "y B no pisa la de A"
    assert await _oc(esc, esc["oc_b"], "a") is None


# ── Órdenes de traslado ─────────────────────────────────────────────────────

async def test_transfer_order_promotes_reference(esc):
    """`AC-HANA-32`. La STO queda disponible con el mismo contrato de referencia."""
    await sincronizar(esc, objetos=[HanaObject.PLANT], **VENTANA)
    async with esc["fabrica"]() as s:
        await mapear(s, client=esc["client"], company_id=esc["a"], entity_type="PLANT",
                     sap_key="1200", parent="1000")
        await s.commit()
    await sincronizar(esc, objetos=[HanaObject.TRANSFER_ORDER], **VENTANA)

    refs = [r for r in await referencias(esc, "TRANSFER_ORDER") if r["sap_code"] == esc["sto"]]
    assert len(refs) == 1
    assert (refs[0]["quantity"], refs[0]["unit"]) == (5000, "KG")
    extra = refs[0]["extra_data"]
    assert extra["source_plant"] == "1100" and extra["destination_plant"] == "1200"
    assert extra["items"][0]["material"] and extra["items"][0]["destination_storage"] is not None
    assert not [r for r in await referencias(esc, "PURCHASE_ORDER") if r["sap_code"] == esc["sto"]], (
        "una STO no es una orden de compra")


async def test_purchase_orders_do_not_include_transfer_orders(esc):
    await sincronizar(esc, objetos=OC, **VENTANA)
    assert esc["sto"] not in [r["sap_code"] for r in await referencias(esc, "PURCHASE_ORDER")]


# ── BR-18 con una OC sincronizada (`AC-HANA-33`) ─────────────────────────────

PREFIJO_LOTE = "HANA5-OC-"


@pytest_asyncio.fixture
async def oc_sincronizada(test_database_url, seeded_ids):
    """Una OC llegada por sync a la empresa sembrada, lista para recibir contra ella."""
    import random

    from app.integrations.sap.inbound.models import SOURCE_SYSTEM  # noqa: F401

    client = "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(3))
    serie = f"{random.randint(0, 9999):04d}"
    cid = seeded_ids["company_id"]
    motor = create_async_engine(test_database_url)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    cfg = cfg_de_prueba(client)

    async with fabrica() as s:
        await mapear(s, client=client, company_id=cid, entity_type="COMPANY_CODE", sap_key="1000")
        await mapear(s, client=client, company_id=cid, entity_type="PLANT", sap_key="1100",
                     parent="1000")
        await s.commit()
    async with fabrica() as s:
        actor = {"id": seeded_ids["user_admin_id"], "company_id": cid, "is_super_admin": True}
        fake = FakeHana(default_dataset(client=client, serie=serie))
        jobs = await SapInboundService(
            s, actor, adapter=adaptador_de_prueba(fake, cfg), cfg=cfg,
        ).sync([HanaObject.PURCHASE_ORDER], **VENTANA)
        await s.commit()
        assert all(j.status == "completed" for j in jobs), [(j.object_type, j.error_message) for j in jobs]

    yield {"codigo": f"45{serie}0001", "ordenado": 1150, "motor": motor}

    from app.audit.models import AuditLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.operations.models import BirdMovement, OperationalEvent

    async with motor.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO_LOTE}%")))).scalars().all()
        if ids:
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(ids)))).scalars().all()
            if eventos:
                await c.execute(delete(BirdMovement).where(BirdMovement.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
        p = {"m": client}
        for sql in (
            "DELETE FROM sap_inbound_records WHERE client = :m",
            "DELETE FROM sap_inbound_watermarks WHERE scope_key LIKE 'client:' || :m || '|%'",
            "DELETE FROM sap_inbound_sync_jobs WHERE id NOT IN "
            "(SELECT sync_job_id FROM sap_inbound_records) AND filters->>'client' = :m",
            "DELETE FROM sap_entity_mappings WHERE client = :m",
            "DELETE FROM sap_references WHERE extra_data->>'client' = :m",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def _lote(client, cab, ids):
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": ids["company_id"], "farm_id": ids["farm_id"],
        "house_id": ids["house_id"], "lot_code": f"{PREFIJO_LOTE}{uuid.uuid4().hex[:10]}",
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


async def test_purchase_order_br18_limit(client, auth_headers, seeded_ids, oc_sincronizada):
    """Recepción parcial, recepción hasta el límite e intento de exceder — con la regla intacta."""
    orden = oc_sincronizada["codigo"]
    lote = await _lote(client, auth_headers, seeded_ids)

    parcial = await _recibir(client, auth_headers, seeded_ids, lote, orden, 300)
    assert parcial.status_code == 201, parcial.text

    hasta_el_limite = await _recibir(client, auth_headers, seeded_ids, lote, orden, 850)
    assert hasta_el_limite.status_code == 201, (
        f"300 + 850 = 1150 = lo ordenado: debe caber. {hasta_el_limite.text}")

    exceso = await _recibir(client, auth_headers, seeded_ids, lote, orden, 1)
    assert exceso.status_code == 400, exceso.text
    assert exceso.json()["rule"] == "BR-18"
    assert "1150" in exceso.json()["detail"]


async def test_synced_purchase_order_is_listed_for_the_reception_selector(
    client, auth_headers, oc_sincronizada
):
    r = await client.get("/api/v1/sap/references?ref_type=purchase_order&limit=200",
                         headers=auth_headers)
    assert r.status_code == 200, r.text
    fila = next(x for x in r.json()["references"] if x["sap_code"] == oc_sincronizada["codigo"])
    assert fila["quantity"] == 1150 and fila["description"]
    assert fila["extra_data"]["items"], "el selector recibe el desglose"
