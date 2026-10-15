"""SPEC 006 · Cutover v2 — validación de dominio sobre el DTO normalizado.

Resuelve códigos/nombres contra los maestros de la **empresa efectiva** (nunca ids del
usuario), comprueba relaciones padre-hijo, compatibilidad de fase con la BU, lote y opening
existentes, orden de fechas e invariantes de consistencia **solo cuando todas las piezas son
KNOWN** (sin tolerancias, sin inventar certeza). Deja en cada fila las referencias resueltas
(`_refs`) y los derivados (`_derived`) que el apply necesita.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..lots.models import OpeningBalance
from ..masters.models import (Area, Breed, Farm, GeneticLine, Hatcher, Hatchery, House, Incubator, Lot,
                              LotStatus, ProductivePhase)
from ..operations.models import OperationalEvent
from .contracts import KNOWN, NOT_APPLICABLE, UNKNOWN, TemplateContract
from .parser import error_de_fila

_MENSAJES = {
    "MASTER_NOT_FOUND": "{entidad} no existe, está fuera de la empresa o no coincide con el catálogo.",
    "MASTER_INACTIVE": "{entidad} está inactivo: no admite referencias nuevas (OD-21).",
    "MASTER_AMBIGUOUS": "{entidad} es ambiguo: hay más de un registro con ese código/nombre.",
    "PARENT_MISMATCH": "{entidad} existe pero no pertenece a {padre}.",
    "PHASE_INCOMPATIBLE": "La fase no es compatible con la unidad de negocio (permitidas: {permitidas}).",
    "METRIC_NOT_APPLICABLE_IN_PHASE": "Métrica de producción con valor en fase CRIA: use N/A o déjela vacía.",
    "LOT_DUPLICATE": "Código de lote repetido en el batch o ya usado en otra empresa.",
    "LOT_EXISTS_REUSE_REJECTED": "Ya existe un lote con ese código en la empresa: indique existing_lot_code para reutilizarlo o cambie el código.",
    "OPENING_ALREADY_EXISTS": "El lote ya tiene un saldo de apertura: no se carga dos veces.",
    "CONSISTENCY_MISMATCH": "La ecuación de consistencia no cuadra: {detalle}.",
    "DATE_ORDER_INVALID": "Orden de fechas inválido: {detalle}.",
}


def _val(fila: dict, campo: str) -> Any:
    celda = fila["normalized"].get(campo)
    return celda["value"] if celda else None


def _st(fila: dict, campo: str) -> str:
    celda = fila["normalized"].get(campo)
    return celda["status"] if celda else UNKNOWN


def _known(fila: dict, *campos: str) -> bool:
    return all(_st(fila, c) == KNOWN for c in campos)


def _fecha(v: Optional[str]) -> Optional[date]:
    return date.fromisoformat(v) if v else None


class ValidadorDeDominio:
    def __init__(self, db: AsyncSession, *, company_id: int, contrato: TemplateContract, cutover_date: date):
        self.db = db
        self.company_id = company_id
        self.contrato = contrato
        self.corte = cutover_date
        self._cache: dict[tuple, Any] = {}

    # ── utilidades ───────────────────────────────────────────────────────────

    def _error(self, fila: dict, campo: str, code: str, **fmt: Any) -> None:
        mensaje = _MENSAJES[code].format(**fmt) if fmt else _MENSAJES[code]
        fila["errors"].append(error_de_fila(fila["row_number"], campo, campo, code, mensaje, _val(fila, campo)))

    async def _uno(self, clave: tuple, consulta):
        if clave not in self._cache:
            self._cache[clave] = list((await self.db.execute(consulta)).scalars().all())
        return self._cache[clave]

    async def _resolver(self, fila: dict, campo: str, entidad: str, consulta, *, clave: tuple,
                        padre: Optional[str] = None, consulta_en_empresa=None) -> Optional[Any]:
        """Devuelve el maestro resuelto o registra el error; `None` si no hay valor."""
        if not _known(fila, campo):
            return None
        filas = await self._uno(clave, consulta)
        if not filas:
            if padre and consulta_en_empresa is not None:
                en_empresa = await self._uno(clave + ("empresa",), consulta_en_empresa)
                if en_empresa:
                    self._error(fila, campo, "PARENT_MISMATCH", entidad=entidad, padre=padre)
                    return None
            self._error(fila, campo, "MASTER_NOT_FOUND", entidad=entidad)
            return None
        if len(filas) > 1:
            self._error(fila, campo, "MASTER_AMBIGUOUS", entidad=entidad)
            return None
        maestro = filas[0]
        if getattr(maestro, "is_active", True) is False and not fila["_refs"].get("existing_lot_id"):
            self._error(fila, campo, "MASTER_INACTIVE", entidad=entidad)
            return None
        return maestro

    # ── maestros ─────────────────────────────────────────────────────────────

    async def _lote_existente(self, fila: dict) -> None:
        codigo = _val(fila, "existing_lot_code")
        if not codigo:
            return
        lotes = await self._uno(("lot", codigo), select(Lot).where(Lot.company_id == self.company_id, Lot.lot_code == codigo))
        if not lotes:
            self._error(fila, "existing_lot_code", "MASTER_NOT_FOUND", entidad="El lote existente")
            return
        lote = lotes[0]
        if (lote.bird_type.value if lote.bird_type else None) != self.contrato.bird_type:
            self._error(fila, "existing_lot_code", "PARENT_MISMATCH", entidad="El lote existente", padre=f"la unidad {self.contrato.business_unit}")
            return
        if lote.status != LotStatus.ACTIVE:
            self._error(fila, "existing_lot_code", "MASTER_INACTIVE", entidad="El lote existente")
            return
        tiene_opening = (await self.db.execute(select(func.count()).select_from(OpeningBalance)
                                               .where(OpeningBalance.lot_id == lote.id))).scalar() or 0
        if tiene_opening:
            self._error(fila, "existing_lot_code", "OPENING_ALREADY_EXISTS")
            return
        eventos = (await self.db.execute(select(func.count()).select_from(OperationalEvent)
                                         .where(OperationalEvent.lot_id == lote.id))).scalar() or 0
        if eventos:
            self._error(fila, "existing_lot_code", "LOT_EXISTS_REUSE_REJECTED")
            return
        fila["_refs"]["existing_lot_id"] = lote.id

    async def _codigo_legado(self, fila: dict, vistos: dict[str, int]) -> None:
        codigo = _val(fila, "legacy_lot_code")
        if not codigo:
            return
        if codigo in vistos:
            self._error(fila, "legacy_lot_code", "LOT_DUPLICATE")
            return
        vistos[codigo] = fila["row_number"]
        existentes = await self._uno(("legacy", codigo), select(Lot).where(
            (Lot.lot_code == codigo) | ((Lot.company_id == self.company_id) & (Lot.legacy_lot_code == codigo))))
        reutilizado = fila["_refs"].get("existing_lot_id")
        for lote in existentes:
            if reutilizado and lote.id == reutilizado:
                continue
            if lote.company_id != self.company_id:
                self._error(fila, "legacy_lot_code", "LOT_DUPLICATE")
            else:
                self._error(fila, "legacy_lot_code", "LOT_EXISTS_REUSE_REJECTED")
            return

    async def _maestros_aves(self, fila: dict) -> None:
        refs = fila["_refs"]
        granja = await self._resolver(
            fila, "farm_code", "La granja", select(Farm).where(Farm.company_id == self.company_id, Farm.code == _val(fila, "farm_code")),
            clave=("farm", _val(fila, "farm_code")))
        if granja is not None:
            refs["farm_id"] = granja.id
        if _known(fila, "house_name"):
            nombre = _val(fila, "house_name")
            if granja is not None:
                galpon = await self._resolver(
                    fila, "house_name", "El galpón",
                    select(House).where(House.farm_id == granja.id, House.name == nombre),
                    clave=("house", granja.id, nombre), padre=f"la granja {granja.code}",
                    consulta_en_empresa=select(House).join(Farm, House.farm_id == Farm.id).where(
                        Farm.company_id == self.company_id, House.name == nombre))
                if galpon is not None:
                    refs["house_id"] = galpon.id
        if _known(fila, "area_code"):
            area = await self._resolver(
                fila, "area_code", "El área", select(Area).where(
                    (Area.company_id == self.company_id) | (Area.company_id.is_(None)), Area.code == _val(fila, "area_code")),
                clave=("area", _val(fila, "area_code")))
            if area is not None:
                refs["area_id"] = area.id
        if _known(fila, "productive_phase_code"):
            codigo = _val(fila, "productive_phase_code")
            fase = await self._resolver(fila, "productive_phase_code", "La fase productiva",
                                        select(ProductivePhase).where(ProductivePhase.code == codigo), clave=("phase", codigo))
            if fase is not None:
                if codigo not in self.contrato.phases:
                    self._error(fila, "productive_phase_code", "PHASE_INCOMPATIBLE", permitidas=", ".join(self.contrato.phases))
                else:
                    refs["phase_id"] = fase.id
                    refs["phase_code"] = codigo
        linea = None
        if _known(fila, "genetic_line_code"):
            linea = await self._resolver(
                fila, "genetic_line_code", "La línea genética", select(GeneticLine).where(
                    (GeneticLine.company_id == self.company_id) | (GeneticLine.company_id.is_(None)),
                    GeneticLine.code == _val(fila, "genetic_line_code")),
                clave=("line", _val(fila, "genetic_line_code")))
            if linea is not None:
                refs["genetic_line_id"] = linea.id
        if _known(fila, "breed_name"):
            nombre = _val(fila, "breed_name")
            base = select(Breed).where(Breed.name == nombre)
            if linea is not None:
                raza = await self._resolver(
                    fila, "breed_name", "La raza", base.where(Breed.genetic_line_id == linea.id),
                    clave=("breed", linea.id, nombre), padre=f"la línea {linea.code}", consulta_en_empresa=base)
            else:
                raza = await self._resolver(fila, "breed_name", "La raza", base, clave=("breed", None, nombre))
            if raza is not None:
                if raza.bird_type is not None and raza.bird_type.value != self.contrato.bird_type:
                    self._error(fila, "breed_name", "PARENT_MISMATCH", entidad="La raza", padre=f"la unidad {self.contrato.business_unit}")
                else:
                    refs["breed_id"] = raza.id

    async def _maestros_incubadora(self, fila: dict) -> None:
        refs = fila["_refs"]
        planta = await self._resolver(
            fila, "hatchery_code", "La planta de incubación",
            select(Hatchery).where(Hatchery.company_id == self.company_id, Hatchery.code == _val(fila, "hatchery_code")),
            clave=("hatchery", _val(fila, "hatchery_code")))
        if planta is not None:
            refs["hatchery_id"] = planta.id
        for campo, modelo, entidad, clave in (("incubator_name", Incubator, "La incubadora", "incubator_id"),
                                              ("hatcher_name", Hatcher, "La nacedora", "hatcher_id")):
            if not _known(fila, campo) or planta is None:
                continue
            nombre = _val(fila, campo)
            equipo = await self._resolver(
                fila, campo, entidad, select(modelo).where(modelo.hatchery_id == planta.id, modelo.name == nombre),
                clave=(clave, planta.id, nombre), padre=f"la planta {planta.code}",
                consulta_en_empresa=select(modelo).join(Hatchery, modelo.hatchery_id == Hatchery.id).where(
                    Hatchery.company_id == self.company_id, modelo.name == nombre))
            if equipo is not None:
                refs[clave] = equipo.id
        if _known(fila, "source_lot_code"):
            codigo = _val(fila, "source_lot_code")
            lotes = await self._uno(("source", codigo), select(Lot).where(
                Lot.company_id == self.company_id, (Lot.lot_code == codigo) | (Lot.legacy_lot_code == codigo)))
            if not lotes:
                self._error(fila, "source_lot_code", "MASTER_NOT_FOUND", entidad="El lote fuente")
            else:
                fuente = lotes[0]
                tipo = fuente.bird_type.value if fuente.bird_type else None
                generacion = _val(fila, "generation")
                if tipo not in ("grandparent", "breeder") or (generacion and tipo != generacion):
                    self._error(fila, "source_lot_code", "PARENT_MISMATCH", entidad="El lote fuente",
                                padre=f"la generación {generacion or 'grandparent|breeder'}")
                else:
                    refs["source_lot_id"] = fuente.id

    # ── fechas, fase y consistencia ───────────────────────────────────────────

    def _fechas_aves(self, fila: dict) -> None:
        inicio = _fecha(_val(fila, "real_start_date"))
        if inicio and inicio > self.corte:
            self._error(fila, "real_start_date", "DATE_ORDER_INVALID", detalle="la fecha real de inicio es posterior al corte")
        if _known(fila, "phase_start_date"):
            inicio_fase = _fecha(_val(fila, "phase_start_date"))
            if inicio and inicio_fase < inicio:
                self._error(fila, "phase_start_date", "DATE_ORDER_INVALID", detalle="la fase empieza antes que el lote")
            elif inicio_fase > self.corte:
                self._error(fila, "phase_start_date", "DATE_ORDER_INVALID", detalle="la fase empieza después del corte")

    def _fechas_incubadora(self, fila: dict) -> None:
        recepcion = _fecha(_val(fila, "reception_date"))
        if recepcion and recepcion > self.corte:
            self._error(fila, "reception_date", "DATE_ORDER_INVALID", detalle="la recepción es posterior al corte")
        carga = _fecha(_val(fila, "set_date")) if _known(fila, "set_date") else None
        if carga:
            if recepcion and carga < recepcion:
                self._error(fila, "set_date", "DATE_ORDER_INVALID", detalle="la carga es anterior a la recepción")
            elif carga > self.corte:
                self._error(fila, "set_date", "DATE_ORDER_INVALID", detalle="la carga es posterior al corte")
        if _known(fila, "expected_hatch_date") and carga:
            if _fecha(_val(fila, "expected_hatch_date")) < carga:
                self._error(fila, "expected_hatch_date", "DATE_ORDER_INVALID", detalle="el nacimiento previsto es anterior a la carga")

    def _consistencia_reproductoras(self, fila: dict) -> None:
        if fila["_refs"].get("phase_code") == "CRIA":
            for campo in ("accumulated_egg_production", "accumulated_eggs_to_hatchery"):
                if _st(fila, campo) == KNOWN:
                    self._error(fila, campo, "METRIC_NOT_APPLICABLE_IN_PHASE")
        for sexo, vivas, alojadas, mort, desc in (
                ("machos", "live_males", "birds_placed_males", "historical_mortality_males", "historical_culls_males"),
                ("hembras", "live_females", "birds_placed_females", "historical_mortality_females", "historical_culls_females")):
            if _known(fila, vivas, alojadas, mort, desc):
                esperado = _val(fila, alojadas) - _val(fila, mort) - _val(fila, desc)
                if esperado != _val(fila, vivas):
                    self._error(fila, vivas, "CONSISTENCY_MISMATCH",
                                detalle=f"{sexo}: alojadas − mortalidad − descartes = {esperado} ≠ vivas {_val(fila, vivas)}")
        if _known(fila, "accumulated_egg_production", "accumulated_eggs_to_hatchery") and \
                _val(fila, "accumulated_eggs_to_hatchery") > _val(fila, "accumulated_egg_production"):
            self._error(fila, "accumulated_eggs_to_hatchery", "CONSISTENCY_MISMATCH",
                        detalle="huevos a incubadora > huevos producidos")

    def _consistencia_engorde(self, fila: dict) -> None:
        if _known(fila, "live_birds", "accumulated_birds_received", "historical_mortality", "historical_culls", "partial_outbound_birds"):
            esperado = (_val(fila, "accumulated_birds_received") - _val(fila, "historical_mortality")
                        - _val(fila, "historical_culls") - _val(fila, "partial_outbound_birds"))
            if esperado != _val(fila, "live_birds"):
                self._error(fila, "live_birds", "CONSISTENCY_MISMATCH",
                            detalle=f"recibidas − mortalidad − descartes − salidas = {esperado} ≠ vivas {_val(fila, 'live_birds')}")

    def _consistencia_incubadora(self, fila: dict) -> None:
        if _known(fila, "eggs_received", "eggs_set") and _val(fila, "eggs_set") > _val(fila, "eggs_received"):
            self._error(fila, "eggs_set", "CONSISTENCY_MISMATCH", detalle="huevos cargados > huevos recibidos")
        if _known(fila, "eggs_set"):
            cargados = _val(fila, "eggs_set")
            excedidas = []
            for campo in ("eggs_transferred", "eggs_discarded"):
                if _known(fila, campo) and _val(fila, campo) > cargados:
                    self._error(fila, campo, "CONSISTENCY_MISMATCH", detalle=f"{campo} > huevos cargados")
                    excedidas.append(campo)
            if not excedidas and _known(fila, "eggs_transferred", "eggs_discarded") and \
                    _val(fila, "eggs_transferred") + _val(fila, "eggs_discarded") > cargados:
                self._error(fila, "eggs_discarded", "CONSISTENCY_MISMATCH", detalle="transferidos + descartados > cargados")
            if _known(fila, "chicks_hatched"):
                tope_campo = "eggs_transferred" if _known(fila, "eggs_transferred") else "eggs_set"
                if _val(fila, "chicks_hatched") > _val(fila, tope_campo):
                    self._error(fila, "chicks_hatched", "CONSISTENCY_MISMATCH", detalle=f"pollitos nacidos > {tope_campo}")
        if _known(fila, "chicks_hatched", "chicks_available") and _val(fila, "chicks_available") > _val(fila, "chicks_hatched"):
            self._error(fila, "chicks_available", "CONSISTENCY_MISMATCH", detalle="pollitos disponibles > nacidos")

    def _derivados(self, fila: dict) -> None:
        derivados = fila["_derived"]
        bu = self.contrato.business_unit
        if bu == "hatchery":
            recepcion = _fecha(_val(fila, "reception_date"))
            carga = _fecha(_val(fila, "set_date")) if _known(fila, "set_date") else None
            derivados["incubation_day"] = (self.corte - carga).days if carga else None
            derivados["age_days"] = (self.corte - recepcion).days if recepcion else None
            if _known(fila, "eggs_set", "eggs_transferred", "eggs_discarded"):
                derivados["eggs_in_process"] = _val(fila, "eggs_set") - _val(fila, "eggs_transferred") - _val(fila, "eggs_discarded")
            else:
                derivados["eggs_in_process"] = None
            return
        inicio = _fecha(_val(fila, "real_start_date"))
        edad_declarada = _val(fila, "age_days") if bu == "broiler" and _known(fila, "age_days") else None
        if edad_declarada is not None:
            derivados["age_days"] = edad_declarada
            derivados["age_source"] = "declared"
        elif inicio:
            derivados["age_days"] = max(0, (self.corte - inicio).days)
            derivados["age_source"] = "derived"
        else:
            derivados["age_days"] = None
        if bu == "broiler":
            derivados["live_total"] = _val(fila, "live_birds")
        else:
            m, f = _val(fila, "live_males"), _val(fila, "live_females")
            derivados["live_total"] = (m or 0) + (f or 0) if (m is not None and f is not None) else None

    # ── punto de entrada ─────────────────────────────────────────────────────

    async def validar(self, filas: list[dict]) -> None:
        vistos: dict[str, int] = {}
        for fila in filas:
            fila.setdefault("_refs", {})
            fila.setdefault("_derived", {})
            await self._lote_existente(fila)
            await self._codigo_legado(fila, vistos)
            if self.contrato.business_unit == "hatchery":
                await self._maestros_incubadora(fila)
                self._fechas_incubadora(fila)
                self._consistencia_incubadora(fila)
            else:
                await self._maestros_aves(fila)
                self._fechas_aves(fila)
                if self.contrato.business_unit == "broiler":
                    self._consistencia_engorde(fila)
                else:
                    self._consistencia_reproductoras(fila)
            self._derivados(fila)
