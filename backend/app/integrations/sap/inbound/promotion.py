"""Promoción controlada a `sap_references` — SPEC 005 `§25`…`§27`, `FR-11`, `FR-12`.

Es el único punto donde el inbound toca algo que el dominio lee, y lo hace por una sola
puerta: un upsert por `(empresa, tipo, código SAP)`.

    una clave, una referencia   `validate_oc_limit` (BR-18) busca la OC con `scalar_one_or_none`
    duplicado previo            no se elige uno ni se sobrescribe: se bloquea y se informa
    sin tipo de referencia      el objeto se queda en staging; nunca se guarda como `OTHER`
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import SapReference, SapReferenceType
from .mapping import MappingContext
from .models import (
    M_MAPPED, P_BLOCKED, P_PROMOTED, P_READY, SOURCE_SYSTEM, V_INVALID, V_VALID,
    SapInboundRecord,
)
from .errors import ErrorCode
from .registry import HanaObject
from .staging import CREDIT, DEBIT, GOODS_RECEIPT

#: Objetos que se promueven fila a fila.
SIMPLE = {
    HanaObject.PLANT: SapReferenceType.PLANT,
    HanaObject.STORAGE_LOCATION: SapReferenceType.STORAGE_LOCATION,
    HanaObject.VENDOR: SapReferenceType.VENDOR,
    HanaObject.MATERIAL: SapReferenceType.MATERIAL,
    HanaObject.BATCH: SapReferenceType.SAP_BATCH,
}
#: Objetos sin tipo de referencia hoy: permanecen en staging (`Q3`).
STAGED_ONLY = frozenset({
    HanaObject.COMPANY, HanaObject.MOVEMENT_TYPE, HanaObject.PURCHASE_ORDER_HISTORY,
    HanaObject.PRODUCTION_ORDER, HanaObject.OUTBOUND_ORDER, HanaObject.MATERIAL_MOVEMENT,
})
#: Objetos cuya referencia se compone a partir de varias filas.
COMPOSED = frozenset({HanaObject.PURCHASE_ORDER, HanaObject.PURCHASE_ORDER_ITEM,
                      HanaObject.TRANSFER_ORDER})


def _traza(rec: SapInboundRecord) -> dict[str, Any]:
    return {"source": SOURCE_SYSTEM, "client": rec.client, "company_code": rec.company_code,
            "inbound_record_id": rec.id, "payload_hash": rec.payload_hash,
            "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


async def upsert_reference(
    db: AsyncSession, *, company_id: int, ref_type: SapReferenceType, sap_code: str,
    description: str | None, quantity: float | None, unit: str | None,
    extra: dict[str, Any], actor_id: int | None, is_active: bool = True,
) -> tuple[SapReference | None, str | None]:
    """Crea o actualiza la referencia. Devuelve `(referencia, None)` o `(None, motivo)`."""
    existentes = (await db.execute(
        select(SapReference).where(
            SapReference.company_id == company_id, SapReference.ref_type == ref_type,
            SapReference.sap_code == sap_code,
        ).order_by(SapReference.id))).scalars().all()
    if len(existentes) > 1:
        return None, (f"existen {len(existentes)} referencias {ref_type.value} con código "
                      f"{sap_code}; requiere revisión manual")

    descripcion = (description or "")[:500] or None
    if not existentes:
        ref = SapReference(
            company_id=company_id, ref_type=ref_type, sap_code=sap_code,
            description=descripcion, quantity=quantity, unit=unit, extra_data=extra,
            is_active=is_active, imported_by_id=actor_id)
        db.add(ref)
        await db.flush()
        return ref, None

    ref = existentes[0]
    previo = dict(ref.extra_data or {})
    # `synced_at` no cuenta como cambio: una pasada sin novedades no toca la referencia.
    sin_reloj = {k: v for k, v in extra.items() if k != "synced_at"}
    if {k: previo.get(k) for k in sin_reloj} != sin_reloj:
        ref.extra_data = {**previo, **extra}
    for campo, valor in (("description", descripcion), ("quantity", quantity), ("unit", unit),
                         ("is_active", is_active)):
        if getattr(ref, campo) != valor:
            setattr(ref, campo, valor)
    if ref.imported_by_id is None and actor_id is not None:
        ref.imported_by_id = actor_id
    await db.flush()
    return ref, None


def _marcar(rec: SapInboundRecord, estado: str, *, ref_id: int | None = None,
            codigo: ErrorCode | None = None, mensaje: str | None = None) -> None:
    cambios = {"promotion_status": estado, "promoted_reference_id": ref_id,
               "error_code": codigo.value if codigo else None, "error_message": mensaje}
    for campo, valor in cambios.items():
        if getattr(rec, campo) != valor:
            setattr(rec, campo, valor)


# ── Objetos simples ──────────────────────────────────────────────────────────

async def promote_simple(db: AsyncSession, objeto: HanaObject, rec: SapInboundRecord,
                         ctx: MappingContext, actor_id: int | None) -> bool:
    s = rec.staged_json or {}
    extra = _traza(rec)
    cantidad = unidad = None
    if objeto is HanaObject.PLANT:
        codigo, descripcion = s["plant"], s["name"]
        extra.update(name2=s.get("name2"), city=s.get("city"), country=s.get("country"))
        mapeo = ctx.plants.get(s["plant"]) or {}
        if mapeo.get("farm_id") is not None:
            extra["farm_id"] = mapeo["farm_id"]
        if mapeo.get("business_unit_code"):
            extra["business_unit_code"] = mapeo["business_unit_code"]
    elif objeto is HanaObject.STORAGE_LOCATION:
        codigo = f"{s['plant']}-{s['storage_location']}"
        descripcion = s.get("name") or codigo
        extra.update(plant=s["plant"], storage_location=s["storage_location"])
        mapeo = ctx.storage_locations.get(f"{s['plant']}/{s['storage_location']}") or {}
        if mapeo.get("house_id") is not None:
            extra["house_id"] = mapeo["house_id"]   # solo por mapping expreso: LGORT no es galpón
    elif objeto is HanaObject.VENDOR:
        codigo, descripcion = s["vendor"], s["name"]
        extra.update(tax_id=s.get("tax_id"), country=s.get("country"),
                     blocked=s.get("blocked"), deleted=s.get("deleted"),
                     vendor_name=s["name"])
    elif objeto is HanaObject.MATERIAL:
        codigo, descripcion = s["material"], s.get("description") or s["material"]
        unidad = s["base_unit"]
        extra.update(material_type=s.get("material_type"),
                     material_group=s.get("material_group"), deleted=s.get("deleted"))
    else:  # BATCH
        codigo = f"{s['material']}/{s['plant']}/{s['batch']}"
        descripcion = f"Lote {s['batch']} · {s['plant']}"
        extra.update(material=s["material"], plant=s["plant"], batch=s["batch"],
                     production_date=s.get("production_date"),
                     expiry_date=s.get("expiry_date"), deleted=s.get("deleted"))

    activo = not bool(s.get("deleted"))
    ref, motivo = await upsert_reference(
        db, company_id=rec.company_id, ref_type=SIMPLE[objeto], sap_code=codigo,
        description=descripcion, quantity=cantidad, unit=unidad, extra=extra,
        actor_id=actor_id, is_active=activo)
    if ref is None:
        _marcar(rec, P_BLOCKED, codigo=ErrorCode.SAP_VALIDATION_ERROR, mensaje=motivo)
        return False
    _marcar(rec, P_PROMOTED, ref_id=ref.id)
    return True


# ── Órdenes de compra ────────────────────────────────────────────────────────

async def _vigentes(db: AsyncSession, company_id: int, objeto: HanaObject,
                    prefijo: str) -> list[SapInboundRecord]:
    return list((await db.execute(
        select(SapInboundRecord).where(
            SapInboundRecord.company_id == company_id,
            SapInboundRecord.object_type == objeto.value,
            SapInboundRecord.is_current.is_(True),
            SapInboundRecord.source_key.like(prefijo + "|%"),
        ).order_by(SapInboundRecord.source_key))).scalars().all())


def _total(posiciones: list[dict]) -> tuple[float | int | None, str | None, bool]:
    """Σ de cantidades si la unidad es homogénea. `(total, unidad, homogénea)`."""
    unidades = {p["unit"] for p in posiciones}
    if len(unidades) != 1:
        return None, None, not posiciones
    total = sum(p["quantity"] or 0 for p in posiciones)
    return (int(total) if total == int(total) else total), unidades.pop(), True


async def promote_purchase_order(db: AsyncSession, cabecera: SapInboundRecord,
                                 actor_id: int | None) -> bool:
    """Compone la referencia de una OC desde su cabecera, sus posiciones y su historial.

    `quantity` es lo que `BR-18` comparará contra lo recibido en GA: por eso no se promueve una
    OC a medias (posición sin mapping) ni una cuya cantidad no pueda afirmarse (unidades
    mezcladas). Fail-closed: mejor una OC ausente del selector que un límite falso.
    """
    c = cabecera.staged_json or {}
    ebeln = c["po_number"]
    prefijo = f"{cabecera.client}|{ebeln}"
    posiciones = await _vigentes(db, cabecera.company_id, HanaObject.PURCHASE_ORDER_ITEM, prefijo)
    if not posiciones:
        _marcar(cabecera, P_READY)      # espera a sus posiciones; todavía no es un error
        return False

    if any(p.validation_status == V_INVALID for p in posiciones):
        _marcar(cabecera, P_BLOCKED, codigo=ErrorCode.SAP_VALIDATION_ERROR,
                mensaje=f"la OC {ebeln} tiene posiciones inválidas")
        return False
    activas = [p for p in posiciones if not (p.staged_json or {}).get("deleted")]
    if any(p.mapping_status != M_MAPPED or p.validation_status != V_VALID for p in activas):
        _marcar(cabecera, P_BLOCKED, codigo=ErrorCode.SAP_MAPPING_PENDING,
                mensaje=f"la OC {ebeln} tiene posiciones en centros sin mapping")
        return False

    total, unidad, homogenea = _total([p.staged_json for p in activas])
    if not homogenea:
        _marcar(cabecera, P_BLOCKED, codigo=ErrorCode.SAP_VALIDATION_ERROR,
                mensaje=f"la OC {ebeln} mezcla unidades de medida; no se agregan cantidades "
                        "incompatibles")
        return False
    anulada = bool(c.get("deleted")) or not activas
    if not activas:
        # Todas las posiciones borradas: se conserva el total histórico si puede afirmarse.
        total, unidad, _ = _total([p.staged_json for p in posiciones])

    historial = await _vigentes(db, cabecera.company_id, HanaObject.PURCHASE_ORDER_HISTORY,
                                prefijo)
    entradas = reversos = 0
    for h in historial:
        hs = h.staged_json or {}
        if h.validation_status != V_VALID or hs.get("event_type") != GOODS_RECEIPT:
            continue
        if hs.get("debit_credit") == DEBIT:
            entradas += hs.get("quantity") or 0
        elif hs.get("debit_credit") == CREDIT:
            reversos += hs.get("quantity") or 0

    proveedor = (await db.execute(
        select(SapInboundRecord.staged_json).where(
            SapInboundRecord.company_id == cabecera.company_id,
            SapInboundRecord.object_type == HanaObject.VENDOR.value,
            SapInboundRecord.is_current.is_(True),
            SapInboundRecord.source_key == f"{cabecera.client}|{c['vendor']}",
        ))).scalar_one_or_none() or {}

    desglose = [{
        "item": p.staged_json["item"], "material": p.staged_json["material"],
        "description": p.staged_json.get("description") or p.staged_json["material"],
        "plant": p.staged_json["plant"],
        "storage_location": p.staged_json.get("storage_location"),
        "quantity": p.staged_json["quantity"], "unit": p.staged_json["unit"],
        "delivery_date": p.staged_json.get("delivery_date"),
        "deleted": bool(p.staged_json.get("deleted")),
        "delivery_completed": bool(p.staged_json.get("delivery_completed")),
    } for p in posiciones]
    completa = bool(activas) and all(p.staged_json.get("delivery_completed") for p in activas)
    extra = _traza(cabecera)
    extra.update(
        vendor=c["vendor"], vendor_name=proveedor.get("name"),
        document_type=c.get("document_type"), document_date=c.get("document_date"),
        purchasing_org=c.get("purchasing_org"), currency=c.get("currency"),
        status="CANCELLED" if anulada else ("DELIVERY_COMPLETED" if completa else "OPEN"),
        ordered_quantity=total, received_quantity=entradas - reversos,
        history_summary={"receipts": entradas, "reversals": reversos,
                         "documents": len(historial)},
        items=desglose)
    descripcion = ", ".join(dict.fromkeys(d["description"] for d in desglose
                                          if not d["deleted"])) or f"OC {ebeln}"

    ref, motivo = await upsert_reference(
        db, company_id=cabecera.company_id, ref_type=SapReferenceType.PURCHASE_ORDER,
        sap_code=ebeln, description=descripcion, quantity=total, unit=unidad, extra=extra,
        actor_id=actor_id, is_active=not anulada)
    if ref is None:
        _marcar(cabecera, P_BLOCKED, codigo=ErrorCode.SAP_VALIDATION_ERROR, mensaje=motivo)
        return False
    _marcar(cabecera, P_PROMOTED, ref_id=ref.id)
    for p in posiciones:
        if p.validation_status == V_VALID and p.mapping_status == M_MAPPED:
            _marcar(p, P_PROMOTED, ref_id=ref.id)
    return True


# ── Órdenes de traslado ──────────────────────────────────────────────────────

async def promote_transfer_order(db: AsyncSession, company_id: int, client: str, ebeln: str,
                                 actor_id: int | None) -> int:
    """Compone la referencia de una STO a partir de sus posiciones. Devuelve filas promovidas."""
    posiciones = await _vigentes(db, company_id, HanaObject.TRANSFER_ORDER, f"{client}|{ebeln}")
    if not posiciones or any(p.validation_status != V_VALID for p in posiciones):
        return 0
    activas = [p for p in posiciones if not (p.staged_json or {}).get("deleted")]
    if any(p.mapping_status != M_MAPPED for p in activas):
        return 0                         # se retiene entera: ni origen ni destino a medias

    base = activas or posiciones
    total, unidad, homogenea = _total([p.staged_json for p in base])
    comun = lambda campo: (  # noqa: E731
        vals.pop() if len(vals := {p.staged_json.get(campo) for p in base}) == 1 else None)
    primera = posiciones[0]
    extra = _traza(primera)
    extra.update(
        document_type=primera.staged_json.get("document_type"),
        document_date=primera.staged_json.get("document_date"),
        source_plant=comun("source_plant"), destination_plant=comun("destination_plant"),
        status="CANCELLED" if not activas else (
            "DELIVERY_COMPLETED" if all(p.staged_json.get("delivery_completed") for p in activas)
            else "OPEN"),
        quantity_status="OK" if homogenea else "MIXED_UNITS_NOT_AGGREGATED",
        items=[{
            "item": p.staged_json["item"], "material": p.staged_json["material"],
            "description": p.staged_json.get("description") or p.staged_json["material"],
            "source_plant": p.staged_json["source_plant"],
            "source_storage": p.staged_json.get("source_storage"),
            "destination_plant": p.staged_json["destination_plant"],
            "destination_storage": p.staged_json.get("destination_storage"),
            "quantity": p.staged_json["quantity"], "unit": p.staged_json["unit"],
            "deleted": bool(p.staged_json.get("deleted")),
        } for p in posiciones])
    descripcion = ", ".join(dict.fromkeys(i["description"] for i in extra["items"])) \
        or f"Traslado {ebeln}"

    ref, motivo = await upsert_reference(
        db, company_id=company_id, ref_type=SapReferenceType.TRANSFER_ORDER, sap_code=ebeln,
        description=descripcion, quantity=total if homogenea else None,
        unit=unidad if homogenea else None, extra=extra, actor_id=actor_id,
        is_active=bool(activas))
    if ref is None:
        for p in posiciones:
            _marcar(p, P_BLOCKED, codigo=ErrorCode.SAP_VALIDATION_ERROR, mensaje=motivo)
        return 0
    promovidas = 0
    for p in posiciones:
        if p.mapping_status == M_MAPPED:
            promovidas += p.promotion_status != P_PROMOTED
            _marcar(p, P_PROMOTED, ref_id=ref.id)
    return promovidas
