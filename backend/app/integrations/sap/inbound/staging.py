"""Validación y STAGING — SPEC 005 `§23`, `§47`.

De la fila cruda (nombres de campo SAP) al DTO de negocio tipado que el resto del pipeline usa.
Nada de aquí consulta la base ni decide a qué empresa pertenece una fila: eso es `mapping`.

    estructura    los campos obligatorios vienen con valor
    tipos         fechas `YYYYMMDD` → ISO, cantidades → número no negativo
    clave         la clave de origen es reconstruible

Una fila que no pasa queda `INVALID` y visible: no se descarta en silencio ni se repara.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from .registry import HanaObject, QueryDefinition

#: `VGABE` del historial de compras: entrada de mercancías (dominio estándar de SAP).
GOODS_RECEIPT = "1"
DEBIT, CREDIT = "S", "H"


@dataclass
class Staged:
    dto: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    #: Centros que la fila referencia: todos deben estar mapeados para promoverla.
    plants: tuple[str, ...] = ()


def canonical_hash(payload: dict[str, Any]) -> str:
    """Hash estable del payload: orden canónico de campos, sin depender de la serialización."""
    canonico = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def source_key(definition: QueryDefinition, fila: dict[str, Any]) -> str:
    return "|".join(_txt(fila.get(c)) for c in definition.source_key_fields)


# ── Conversores ──────────────────────────────────────────────────────────────

def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _marca(valor: Any) -> bool:
    return _txt(valor) != ""


class _Lector:
    """Lee una fila acumulando los errores en lugar de detenerse en el primero."""

    def __init__(self, fila: dict[str, Any]) -> None:
        self.fila = fila
        self.errores: list[str] = []

    def req(self, campo: str) -> str:
        valor = _txt(self.fila.get(campo))
        if not valor:
            self.errores.append(f"{campo} obligatorio sin valor")
        return valor

    def opt(self, campo: str) -> str | None:
        return _txt(self.fila.get(campo)) or None

    def fecha(self, campo: str, obligatoria: bool = False) -> str | None:
        valor = _txt(self.fila.get(campo)).replace("-", "")
        if not valor or set(valor) == {"0"}:
            if obligatoria:
                self.errores.append(f"{campo} obligatorio sin valor")
            return None
        if len(valor) != 8 or not valor.isdigit():
            self.errores.append(f"{campo} no es una fecha AAAAMMDD")
            return None
        return f"{valor[:4]}-{valor[4:6]}-{valor[6:]}"

    def cantidad(self, campo: str, obligatoria: bool = True) -> float | int | None:
        bruto = self.fila.get(campo)
        if bruto is None or _txt(bruto) == "":
            if obligatoria:
                self.errores.append(f"{campo} obligatorio sin valor")
            return None
        try:
            numero = float(bruto)
        except (TypeError, ValueError):
            self.errores.append(f"{campo} no es numérico")
            return None
        if numero < 0:
            self.errores.append(f"{campo} negativo")
            return None
        return int(numero) if numero == int(numero) else numero


# ── Un constructor por objeto ────────────────────────────────────────────────

def _company(r: _Lector):
    return {"company_code": r.req("BUKRS"), "name": r.req("BUTXT"), "city": r.opt("ORT01"),
            "country": r.opt("LAND1"), "currency": r.opt("WAERS")}, ()


def _plant(r: _Lector):
    planta = r.req("WERKS")
    return {"plant": planta, "name": r.req("NAME1"), "name2": r.opt("NAME2"),
            "city": r.opt("ORT01"), "country": r.opt("LAND1"),
            "company_code": r.req("BUKRS")}, (planta,)


def _storage_location(r: _Lector):
    planta = r.req("WERKS")
    return {"plant": planta, "storage_location": r.req("LGORT"), "name": r.opt("LGOBE"),
            "company_code": r.req("BUKRS")}, (planta,)


def _vendor(r: _Lector):
    return {"vendor": r.req("LIFNR"), "name": r.req("NAME1"), "tax_id": r.opt("STCD1"),
            "country": r.opt("LAND1"), "blocked": _marca(r.fila.get("SPERR")),
            "deleted": _marca(r.fila.get("LOEVM")), "company_code": r.opt("BUKRS")}, ()


def _material(r: _Lector):
    return {"material": r.req("MATNR"), "description": r.opt("MAKTX"),
            "material_type": r.req("MTART"), "material_group": r.opt("MATKL"),
            "base_unit": r.req("MEINS"), "deleted": _marca(r.fila.get("LVORM")),
            "changed_at": r.fecha("LAEDA")}, ()


def _batch(r: _Lector):
    planta = r.req("WERKS")
    return {"material": r.req("MATNR"), "plant": planta, "batch": r.req("CHARG"),
            "production_date": r.fecha("HSDAT"), "expiry_date": r.fecha("VFDAT"),
            "created_at": r.fecha("ERSDA"), "changed_at": r.fecha("LAEDA"),
            "deleted": _marca(r.fila.get("LVORM")), "company_code": r.req("BUKRS")}, (planta,)


def _movement_type(r: _Lector):
    return {"movement_type": r.req("BWART"), "description": r.opt("BTEXT")}, ()


def _purchase_order(r: _Lector):
    borrada = _marca(r.fila.get("LOEKZ"))
    return {"po_number": r.req("EBELN"), "company_code": r.req("BUKRS"),
            "document_category": r.opt("BSTYP"), "document_type": r.opt("BSART"),
            "vendor": r.req("LIFNR"), "purchasing_org": r.opt("EKORG"),
            "document_date": r.fecha("BEDAT", obligatoria=True),
            "created_at": r.fecha("AEDAT"), "currency": r.opt("WAERS"), "deleted": borrada,
            "status": "CANCELLED" if borrada else "OPEN"}, ()


def _purchase_order_item(r: _Lector):
    planta = r.req("WERKS")
    return {"po_number": r.req("EBELN"), "item": r.req("EBELP"), "material": r.req("MATNR"),
            "description": r.opt("TXZ01"), "plant": planta,
            "storage_location": r.opt("LGORT"), "quantity": r.cantidad("MENGE"),
            "unit": r.req("MEINS"), "delivery_date": r.fecha("EINDT"),
            "deleted": _marca(r.fila.get("LOEKZ")),
            "delivery_completed": _marca(r.fila.get("ELIKZ")),
            "company_code": r.req("BUKRS")}, (planta,)


def _purchase_order_history(r: _Lector):
    signo = r.req("SHKZG")
    if signo and signo not in (DEBIT, CREDIT):
        r.errores.append("SHKZG fuera de dominio (S/H)")
    planta = r.opt("WERKS")
    return {"po_number": r.req("EBELN"), "item": r.req("EBELP"),
            "account_assignment": r.opt("ZEKKN"), "event_type": r.req("VGABE"),
            "year": r.req("GJAHR"), "document": r.req("BELNR"), "document_item": r.opt("BUZEI"),
            "category": r.opt("BEWTP"), "movement_type": r.opt("BWART"),
            "posting_date": r.fecha("BUDAT", obligatoria=True),
            "quantity": r.cantidad("MENGE"), "debit_credit": signo,
            "reversal": signo == CREDIT, "material": r.opt("MATNR"), "plant": planta,
            "reference_document": r.opt("LFBNR"),
            "company_code": r.req("BUKRS")}, ((planta,) if planta else ())


def _production_order(r: _Lector):
    planta = r.req("WERKS")
    if _marca(r.fila.get("LOEKZ")):
        estado = "DELETED"
    elif _marca(r.fila.get("PHAS3")):
        estado = "CLOSED"
    elif _marca(r.fila.get("PHAS2")):
        estado = "COMPLETED"
    elif _marca(r.fila.get("PHAS1")):
        estado = "RELEASED"
    else:
        estado = "CREATED"
    return {"order_number": r.req("AUFNR"), "order_type": r.opt("AUART"),
            "company_code": r.req("BUKRS"), "plant": planta, "material": r.req("MATNR"),
            "batch": r.opt("CHARG"), "storage_location": r.opt("LGORT"),
            "start_date": r.fecha("GSTRP"), "end_date": r.fecha("GLTRP"),
            "planned_quantity": r.cantidad("GAMNG"), "unit": r.req("GMEIN"), "status": estado,
            "created_at": r.fecha("ERDAT", obligatoria=True),
            "changed_at": r.fecha("AEDAT")}, (planta,)


def _transfer_order(r: _Lector):
    origen, destino = r.req("RESWK"), r.req("WERKS")
    borrada = _marca(r.fila.get("LOEKZ"))
    completa = _marca(r.fila.get("ELIKZ"))
    return {"document": r.req("EBELN"), "item": r.req("EBELP"), "company_code": r.req("BUKRS"),
            "document_type": r.opt("BSART"), "source_plant": origen,
            "source_storage": r.opt("RESLO"), "destination_plant": destino,
            "destination_storage": r.opt("LGORT") or "", "material": r.req("MATNR"),
            "description": r.opt("TXZ01"), "quantity": r.cantidad("MENGE"),
            "unit": r.req("MEINS"), "document_date": r.fecha("BEDAT"),
            "created_at": r.fecha("AEDAT"), "deleted": borrada, "delivery_completed": completa,
            "status": "CANCELLED" if borrada else ("DELIVERY_COMPLETED" if completa else "OPEN"),
            }, tuple(p for p in (origen, destino) if p)


def _outbound_order(r: _Lector):
    planta = r.req("WERKS")
    salida_real = r.fecha("WADAT_IST")
    return {"order_number": r.req("VBELN"), "item": r.req("POSNR"),
            "delivery_type": r.opt("LFART"), "shipping_point": r.opt("VSTEL"),
            "customer": r.opt("KUNNR"), "planned_goods_issue_date": r.fecha("WADAT"),
            "actual_goods_issue_date": salida_real,
            "created_at": r.fecha("ERDAT", obligatoria=True), "material": r.req("MATNR"),
            "description": r.opt("ARKTX"), "plant": planta, "storage_location": r.opt("LGORT"),
            "batch": r.opt("CHARG"), "quantity": r.cantidad("LFIMG"), "unit": r.req("VRKME"),
            "reference_document": r.opt("VGBEL"), "reference_item": r.opt("VGPOS"),
            "company_code": r.req("BUKRS"),
            "status": "GOODS_ISSUED" if salida_real else "OPEN"}, (planta,)


def _material_movement(r: _Lector):
    planta = r.req("WERKS")
    destino = r.opt("UMWRK")
    signo = r.req("SHKZG")
    if signo and signo not in (DEBIT, CREDIT):
        r.errores.append("SHKZG fuera de dominio (S/H)")
    anulado = r.opt("SMBLN")
    referencia = None
    if anulado:
        referencia = "/".join(p for p in (anulado, r.opt("SJAHR"), r.opt("SMBLP")) if p)
    orden_compra = r.opt("EBELN")
    return {"material_document": r.req("MBLNR"), "year": r.req("MJAHR"), "item": r.req("ZEILE"),
            "movement_type": r.req("BWART"), "material": r.req("MATNR"), "plant": planta,
            "storage_location": r.opt("LGORT"), "destination_plant": destino,
            "destination_storage": r.opt("UMLGO"), "batch": r.opt("CHARG"),
            "quantity": r.cantidad("ERFMG"), "unit": r.req("ERFME"),
            "quantity_base": r.cantidad("MENGE", obligatoria=False),
            "base_unit": r.opt("MEINS"), "debit_credit": signo,
            "posting_date": r.fecha("BUDAT", obligatoria=True),
            "document_date": r.fecha("BLDAT"), "entry_date": r.fecha("CPUDT"),
            "purchase_order": orden_compra,
            "purchase_order_item": r.opt("EBELP") if orden_compra else None,
            "production_order": r.opt("AUFNR"), "company_code": r.req("BUKRS"),
            "reversal_flag": bool(anulado), "original_document": anulado,
            "reversal_reference": referencia,
            }, tuple(p for p in (planta, destino) if p)


_CONSTRUCTORES: dict[HanaObject, Callable[[_Lector], tuple[dict, tuple]]] = {
    HanaObject.COMPANY: _company,
    HanaObject.PLANT: _plant,
    HanaObject.STORAGE_LOCATION: _storage_location,
    HanaObject.VENDOR: _vendor,
    HanaObject.MATERIAL: _material,
    HanaObject.BATCH: _batch,
    HanaObject.MOVEMENT_TYPE: _movement_type,
    HanaObject.PURCHASE_ORDER: _purchase_order,
    HanaObject.PURCHASE_ORDER_ITEM: _purchase_order_item,
    HanaObject.PURCHASE_ORDER_HISTORY: _purchase_order_history,
    HanaObject.PRODUCTION_ORDER: _production_order,
    HanaObject.TRANSFER_ORDER: _transfer_order,
    HanaObject.OUTBOUND_ORDER: _outbound_order,
    HanaObject.MATERIAL_MOVEMENT: _material_movement,
}
assert set(_CONSTRUCTORES) == set(HanaObject)


def stage(objeto: HanaObject, fila: dict[str, Any]) -> Staged:
    lector = _Lector(fila)
    dto, plantas = _CONSTRUCTORES[objeto](lector)
    return Staged(dto=dto, errors=lector.errores, plants=tuple(dict.fromkeys(plantas)))
