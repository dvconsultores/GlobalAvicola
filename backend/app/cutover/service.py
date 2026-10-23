"""SPEC 006 · Cutover v2 — servicio del ciclo crear → subir → validar → aprobar → aplicar → reconciliar.

Reglas duras que se conservan de GA-REQ-061: el archivo pasa por **staging** y jamás toca
tablas operacionales (AC43/44); errores estructurados con `error_code`/`received_value`
(AC46); `template_version` validada (AC45); re-upload idempotente por checksum (AC50);
segregación creador ≠ aprobador; apply **todo-o-nada**; UNKNOWN nunca se muestra como 0.

Lo nuevo (SPEC 006): un contrato por BU (`contracts.py`), XLSX + CSV al mismo DTO
(`parser.py`), validación de dominio con maestros de la empresa (`validation.py`), listado y
detalle de batches, preview por BU, informe de errores descargable, apply con destino por
campo (lote migrado + `LotPhase` + `OpeningBalance` extendido + `HatcheryOpening`) y
reconciliación Opening/Post/Lifetime/Current por métrica con propagación de UNKNOWN.
"""
from __future__ import annotations

import csv
import hashlib
import io
from datetime import date, datetime, time, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_accion
from ..audit.models import AuditAction, AuditModule
from ..business_units.service import unidades_habilitadas
from ..lots.models import LotPhase, OpeningBalance
from ..masters.models import BirdTypeEnum, Lot, LotStatus, ProductivePhase, SexEnum
from .contracts import KNOWN, NOT_APPLICABLE, UNKNOWN, TemplateContract, contrato
from .models import (CutoverBatch, CutoverBatchStatus, CutoverItem, CutoverItemStatus, CutoverStagingRow,
                     HatcheryOpening)
from .parser import CutoverParseError, parse_cutover_file
from .schemas import CutoverBatchCreate
from .validation import ValidadorDeDominio

#: Estados por métrica del opening (`UNKNOWN` nunca se muestra como `0`).
_METRICAS_DE_OPENING = (
    "mortality_status", "culls_status", "feed_status",
    "egg_production_status", "chicks_hatched_status", "broiler_received_status",
)
_ESTADOS_V2 = _METRICAS_DE_OPENING + (
    "placed_status", "weight_status", "eggs_to_hatchery_status", "outbound_status", "age_status", "initial_mixed_status",
)

_ESTADOS_CARGABLES = {
    CutoverBatchStatus.DRAFT.value,
    CutoverBatchStatus.VALIDATING.value,
    CutoverBatchStatus.VALIDATED.value,
}

COLUMNAS_INFORME_ERRORES = ("row_number", "field", "error_code", "message", "received_value", "column")

#: Columnas destacadas del preview por BU (mandato §22); el detalle expandido trae todas.
PREVIEW_DESTACADAS = {
    "grandparent": ("legacy_lot_code", "productive_phase_code", "farm_code", "house_name", "live_males", "live_females",
                    "historical_mortality_males", "historical_mortality_females", "accumulated_feed_kg",
                    "current_avg_weight_g", "accumulated_egg_production"),
    "breeder": ("legacy_lot_code", "productive_phase_code", "farm_code", "house_name", "live_males", "live_females",
                "historical_mortality_males", "historical_mortality_females", "accumulated_feed_kg",
                "current_avg_weight_g", "accumulated_egg_production"),
    "broiler": ("legacy_lot_code", "farm_code", "house_name", "real_start_date", "age_days", "live_birds",
                "historical_mortality", "historical_culls", "accumulated_feed_kg", "current_avg_weight_g"),
    "hatchery": ("legacy_lot_code", "hatchery_code", "incubator_name", "set_date", "eggs_received", "eggs_set",
                 "eggs_transferred", "eggs_discarded", "chicks_hatched", "chicks_available", "expected_hatch_date"),
}


class CutoverApplyError(Exception):
    """Fallo de dominio durante el apply — viaja como `error_code` y dispara rollback."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _v(estado: dict, campo: str) -> Any:
    celda = estado.get(campo)
    return celda.get("value") if isinstance(celda, dict) else None


def _s(estado: dict, campo: str) -> str:
    celda = estado.get(campo)
    return celda.get("status", UNKNOWN) if isinstance(celda, dict) else UNKNOWN


def _combinado(estado: dict, *campos: str) -> str:
    """Estado de una métrica con varias piezas: KNOWN si todas lo son; N/A si todas; si no, UNKNOWN."""
    estados = [_s(estado, c) for c in campos]
    if all(e == KNOWN for e in estados):
        return KNOWN
    if all(e == NOT_APPLICABLE for e in estados):
        return NOT_APPLICABLE
    return UNKNOWN


def _entero(estado: dict, campo: str) -> int:
    valor = _v(estado, campo)
    return int(valor) if valor is not None else 0


def _opcional(estado: dict, campo: str) -> Optional[Any]:
    return _v(estado, campo) if _s(estado, campo) == KNOWN else None


def _fecha(valor: Optional[str]) -> Optional[date]:
    return date.fromisoformat(valor) if valor else None


def _medianoche(valor: Optional[str]) -> Optional[datetime]:
    d = _fecha(valor)
    return datetime.combine(d, time.min, tzinfo=timezone.utc) if d else None


class CutoverService:
    def __init__(self, db: AsyncSession, current_user: dict):
        self.db = db
        self.current_user = current_user

    def _empresa(self) -> int:
        empresa = self.current_user.get("effective_company_id") or self.current_user.get("company_id")
        if not empresa:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Se requiere una empresa efectiva para operar el cutover.")
        return int(empresa)

    async def _batch_propio(self, batch_id: int, *, bloquear: bool = False) -> CutoverBatch:
        consulta = select(CutoverBatch).where(CutoverBatch.id == batch_id)
        if bloquear:
            consulta = consulta.with_for_update()
        batch = (await self.db.execute(consulta)).scalar_one_or_none()
        # Fail-closed: un batch ajeno se comporta como inexistente (patrón tenancy).
        if batch is None or batch.company_id != self._empresa():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch de cutover no encontrado")
        return batch

    # ── listado / detalle ────────────────────────────────────────────────────

    async def listar(self, *, estado: Optional[str] = None, business_unit: Optional[str] = None,
                     limit: int = 50, offset: int = 0) -> dict:
        base = select(CutoverBatch).where(CutoverBatch.company_id == self._empresa())
        if estado:
            base = base.where(CutoverBatch.status == estado)
        if business_unit:
            base = base.where(CutoverBatch.business_unit == business_unit)
        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        filas = (await self.db.execute(base.order_by(CutoverBatch.id.desc()).limit(limit).offset(offset))).scalars().all()
        return {"items": list(filas), "total": int(total)}

    async def detalle(self, batch_id: int) -> CutoverBatch:
        return await self._batch_propio(batch_id)

    # ── crear / subir ────────────────────────────────────────────────────────

    async def crear_batch(self, data: CutoverBatchCreate) -> CutoverBatch:
        """`POST /cutover-batches` — nace en DRAFT con actor y empresa efectiva."""
        batch = CutoverBatch(
            company_id=self._empresa(),
            business_unit=data.business_unit,
            cutover_datetime=data.cutover_datetime,
            source_type="XLSX",
            source_system=data.source_system,
            source_reference=data.source_reference,
            observations=data.observations,
            status=CutoverBatchStatus.DRAFT.value,
            created_by_id=int(self.current_user["id"]),
        )
        self.db.add(batch)
        await self.db.flush()
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CREATE_BATCH,
            modulo=AuditModule.CUTOVER, entity_type="cutover_batch", entity_id=str(batch.id),
            company_id=batch.company_id,
            new_values={"business_unit": batch.business_unit, "cutover_datetime": str(batch.cutover_datetime)},
        )
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def subir_y_validar(self, batch_id: int, filename: str, content: bytes,
                              template_version: Optional[str] = None) -> CutoverBatch:
        """Upload → parse (XLSX|CSV) → normalización → validación de dominio → staging. Sin efectos operacionales."""
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status not in _ESTADOS_CARGABLES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"BATCH_STATE_INVALID: el batch está en estado {batch.status}: ya no admite cargas.")

        checksum = hashlib.sha256(content).hexdigest()
        otro = (await self.db.execute(select(CutoverBatch).where(
            CutoverBatch.company_id == batch.company_id,
            CutoverBatch.business_unit == batch.business_unit,
            CutoverBatch.cutover_datetime == batch.cutover_datetime,
            CutoverBatch.source_checksum_sha256 == checksum,
            CutoverBatch.id != batch.id,
        ))).scalar_one_or_none()
        if otro is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"DUPLICATE_UPLOAD: el mismo archivo ya fue cargado en el batch {otro.id} (mismo corte).")

        c = contrato(batch.business_unit)
        try:
            parsed = parse_cutover_file(content, filename, contrato=c, template_version=template_version)
        except CutoverParseError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"{exc.code}: {exc.message}") from exc
        if parsed["company"] is not None and parsed["company"] != batch.company_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="COMPANY_MISMATCH: la plantilla fue generada para otra empresa.")

        corte = batch.cutover_datetime.date()
        await ValidadorDeDominio(self.db, company_id=batch.company_id, contrato=c, cutover_date=corte).validar(parsed["rows"])

        # Staging re-creado (idempotente: re-subir el mismo archivo no duplica).
        await self.db.execute(delete(CutoverItem).where(CutoverItem.batch_id == batch.id))
        await self.db.execute(delete(CutoverStagingRow).where(CutoverStagingRow.batch_id == batch.id))

        validas = invalidas = 0
        for fila in parsed["rows"]:
            errores = list(fila["errors"])
            normalizado = dict(fila["normalized"])
            normalizado["_refs"] = fila.get("_refs", {})
            normalizado["_derived"] = fila.get("_derived", {})
            estado = CutoverItemStatus.VALID.value if not errores else CutoverItemStatus.INVALID.value
            validas += estado == CutoverItemStatus.VALID.value
            invalidas += estado == CutoverItemStatus.INVALID.value
            self.db.add(CutoverStagingRow(
                batch_id=batch.id, row_number=fila["row_number"], raw=fila["raw"],
                normalized=normalizado, validation_status=estado, validation_errors=errores or None,
            ))
            self.db.add(CutoverItem(
                batch_id=batch.id, company_id=batch.company_id, business_unit=batch.business_unit,
                legacy_lot_reference=_v(normalizado, "legacy_lot_code"),
                real_start_date=_fecha(_v(normalizado, c.lot_date_field)),
                cutover_datetime=batch.cutover_datetime, opening_state=normalizado,
                source_row_number=fila["row_number"], validation_status=estado, validation_errors=errores or None,
            ))

        batch.source_filename = filename
        batch.source_type = parsed["source_type"]
        batch.source_checksum_sha256 = checksum
        batch.template_version = parsed["template_version"]
        batch.total_rows = len(parsed["rows"])
        batch.valid_rows = validas
        batch.invalid_rows = invalidas
        if invalidas == 0:
            batch.status = CutoverBatchStatus.VALIDATED.value
            batch.validated_by_id = int(self.current_user["id"])
            batch.validated_at = datetime.now(timezone.utc)
        else:
            batch.status = CutoverBatchStatus.VALIDATING.value

        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.UPLOAD, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id, comments=filename,
            new_values={"checksum": checksum, "size_bytes": len(content), "business_unit": batch.business_unit,
                        "source_type": batch.source_type, "template_version": batch.template_version},
        )
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.VALIDATE, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id,
            new_values={"total": batch.total_rows, "valid": validas, "invalid": invalidas, "business_unit": batch.business_unit},
        )
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    # ── lectura del staging ──────────────────────────────────────────────────

    async def _items(self, batch: CutoverBatch) -> list[CutoverItem]:
        return list((await self.db.execute(
            select(CutoverItem).where(CutoverItem.batch_id == batch.id).order_by(CutoverItem.source_row_number))).scalars().all())

    async def validacion(self, batch_id: int) -> dict:
        batch = await self._batch_propio(batch_id)
        errores: list[dict] = []
        for item in await self._items(batch):
            errores.extend(item.validation_errors or [])
        return {"batch_id": batch.id, "status": batch.status, "total_rows": batch.total_rows,
                "valid_rows": batch.valid_rows, "invalid_rows": batch.invalid_rows, "errors": errores}

    async def items(self, batch_id: int) -> list[CutoverItem]:
        return await self._items(await self._batch_propio(batch_id))

    async def informe_de_errores(self, batch_id: int, formato: str) -> tuple[bytes, str, str]:
        """Informe descargable (CSV `;` UTF-8 BOM | XLSX) con `row_number, field, error_code, message, received_value`."""
        validacion = await self.validacion(batch_id)
        filas = [[e.get(col) for col in COLUMNAS_INFORME_ERRORES] for e in validacion["errors"]]
        nombre = f"cutover_batch_{batch_id}_errores"
        if formato == "xlsx":
            from openpyxl import Workbook

            wb = Workbook()
            hoja = wb.active
            hoja.title = "Errores"
            hoja.append(list(COLUMNAS_INFORME_ERRORES))
            for fila in filas:
                hoja.append(["" if v is None else v for v in fila])
            buf = io.BytesIO()
            wb.save(buf)
            return buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f"{nombre}.xlsx"
        texto = io.StringIO()
        escritor = csv.writer(texto, delimiter=";", lineterminator="\n")
        escritor.writerow(COLUMNAS_INFORME_ERRORES)
        for fila in filas:
            escritor.writerow(["" if v is None else v for v in fila])
        return ("﻿" + texto.getvalue()).encode("utf-8"), "text/csv; charset=utf-8", f"{nombre}.csv"

    async def preview(self, batch_id: int) -> dict:
        """Preview funcional por BU (mandato §22): resumen + filas con valor/estado por campo."""
        batch = await self._batch_propio(batch_id)
        c = contrato(batch.business_unit)
        metricas = [f.name for f in c.fields if f.metric]
        filas: list[dict] = []
        resumen: dict[str, Any] = {
            "lots": 0, "valid_rows": 0, "invalid_rows": 0, "unknown_metrics": 0, "not_applicable_metrics": 0,
            "live_birds": 0, "live_males": 0, "live_females": 0, "by_phase": {}, "farms": [], "hatcheries": [],
            "historical_mortality": 0, "historical_mortality_unknown_rows": 0, "accumulated_feed_kg": 0.0,
            "eggs_received": 0, "eggs_set": 0, "eggs_in_process": 0, "chicks_available": 0,
        }
        granjas: set[str] = set()
        plantas: set[str] = set()
        for item in await self._items(batch):
            estado = item.opening_state or {}
            derivados = estado.get("_derived", {})
            valores = {campo: estado.get(campo) for campo in c.columns if campo in estado}
            desconocidas = sum(1 for m in metricas if _s(estado, m) == UNKNOWN)
            no_aplica = sum(1 for m in metricas if _s(estado, m) == NOT_APPLICABLE)
            filas.append({
                "row_number": item.source_row_number, "legacy_lot_code": item.legacy_lot_reference, "lot_id": item.lot_id,
                "status": item.validation_status, "errors": len(item.validation_errors or []),
                "values": valores, "derived": derivados, "unknown_metrics": desconocidas, "not_applicable_metrics": no_aplica,
            })
            resumen["lots"] += 1
            valida = item.validation_status in (CutoverItemStatus.VALID.value, CutoverItemStatus.APPLIED.value)
            resumen["valid_rows" if valida else "invalid_rows"] += 1
            resumen["unknown_metrics"] += desconocidas
            resumen["not_applicable_metrics"] += no_aplica
            if not valida:
                continue
            if c.business_unit == "hatchery":
                resumen["eggs_received"] += _entero(estado, "eggs_received")
                resumen["eggs_set"] += _entero(estado, "eggs_set")
                resumen["eggs_in_process"] += derivados.get("eggs_in_process") or 0
                resumen["chicks_available"] += _entero(estado, "chicks_available")
                resumen["live_birds"] += _entero(estado, "chicks_available")
                if _v(estado, "hatchery_code"):
                    plantas.add(_v(estado, "hatchery_code"))
            else:
                vivas = derivados.get("live_total") or 0
                resumen["live_birds"] += vivas
                if c.business_unit == "broiler":
                    if _s(estado, "historical_mortality") == KNOWN:
                        resumen["historical_mortality"] += _entero(estado, "historical_mortality")
                    else:
                        resumen["historical_mortality_unknown_rows"] += 1
                else:
                    resumen["live_males"] += _entero(estado, "live_males")
                    resumen["live_females"] += _entero(estado, "live_females")
                    if _combinado(estado, "historical_mortality_males", "historical_mortality_females") == KNOWN:
                        resumen["historical_mortality"] += (_entero(estado, "historical_mortality_males")
                                                            + _entero(estado, "historical_mortality_females"))
                    else:
                        resumen["historical_mortality_unknown_rows"] += 1
                if _s(estado, "accumulated_feed_kg") == KNOWN:
                    resumen["accumulated_feed_kg"] += float(_v(estado, "accumulated_feed_kg"))
                fase = estado.get("_refs", {}).get("phase_code") or _v(estado, "productive_phase_code")
                if fase:
                    resumen["by_phase"][fase] = resumen["by_phase"].get(fase, 0) + 1
                if _v(estado, "farm_code"):
                    granjas.add(_v(estado, "farm_code"))
        resumen["farms"] = sorted(granjas)
        resumen["hatcheries"] = sorted(plantas)
        if resumen["historical_mortality_unknown_rows"]:
            resumen["historical_mortality_status"] = UNKNOWN
        else:
            resumen["historical_mortality_status"] = KNOWN
        return {"batch_id": batch.id, "business_unit": batch.business_unit, "status": batch.status,
                "template_version": batch.template_version, "schema_id": c.schema_id,
                "columns": list(c.columns), "highlight": list(PREVIEW_DESTACADAS[batch.business_unit]),
                "summary": resumen, "rows": filas}

    # ── ciclo de aprobación ──────────────────────────────────────────────────

    async def enviar_a_aprobacion(self, batch_id: int) -> CutoverBatch:
        """VALIDATED → PENDING_APPROVAL (un batch sin filas válidas no se envía)."""
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status != CutoverBatchStatus.VALIDATED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"BATCH_STATE_INVALID: el batch está en estado {batch.status}: solo uno VALIDATED se envía.")
        if batch.valid_rows < 1 or batch.invalid_rows > 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="BATCH_STATE_INVALID: el batch no tiene filas válidas suficientes para enviarse.")
        batch.status = CutoverBatchStatus.PENDING_APPROVAL.value
        batch.submitted_by_id = int(self.current_user["id"])
        batch.submitted_at = datetime.now(timezone.utc)
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.SUBMIT, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id,
            new_values={"valid": batch.valid_rows, "business_unit": batch.business_unit},
        )
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    def _exigir_segregacion(self, batch: CutoverBatch) -> None:
        """Espejo de BR-14: quien creó el batch no lo aprueba ni lo rechaza (ni el super admin)."""
        if batch.created_by_id == int(self.current_user["id"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="SEGREGATION_VIOLATION: el creador no puede aprobar ni rechazar su propio batch.")

    async def aprobar(self, batch_id: int) -> CutoverBatch:
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status != CutoverBatchStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"BATCH_STATE_INVALID: el batch está en estado {batch.status}: solo uno PENDING_APPROVAL se aprueba.")
        self._exigir_segregacion(batch)
        batch.status = CutoverBatchStatus.APPROVED.value
        batch.approved_by_id = int(self.current_user["id"])
        batch.approved_at = datetime.now(timezone.utc)
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.APPROVED, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id, new_state=batch.status,
        )
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def rechazar(self, batch_id: int, reason: str) -> CutoverBatch:
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status != CutoverBatchStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"BATCH_STATE_INVALID: el batch está en estado {batch.status}: solo uno PENDING_APPROVAL se rechaza.")
        self._exigir_segregacion(batch)
        batch.status = CutoverBatchStatus.REJECTED.value  # terminal
        batch.rejected_by_id = int(self.current_user["id"])
        batch.rejected_at = datetime.now(timezone.utc)
        batch.rejection_reason = reason
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.REJECTED, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id,
            new_state=batch.status, change_reason=reason,
        )
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    # ── apply atómico por BU ─────────────────────────────────────────────────

    async def _fase_implicita(self, codigo: str) -> int:
        fase = (await self.db.execute(select(ProductivePhase).where(
            ProductivePhase.code == codigo, ProductivePhase.is_active == True))).scalars().first()  # noqa: E712
        if fase is None:
            raise CutoverApplyError("PHASE_REQUIRED", f"No existe la fase productiva activa '{codigo}' para anclar el opening.")
        return fase.id

    async def _lote(self, batch: CutoverBatch, item: CutoverItem, c: TemplateContract, estado: dict,
                    refs: dict, vistos: set[str]) -> tuple[Lot, bool]:
        """REUSE explícito del lote existente (sin duplicar) o creación del lote MIGRATED con su procedencia."""
        ref = _v(estado, "legacy_lot_code") or f"CUT-ITEM-{item.id}"
        if ref in vistos:
            raise CutoverApplyError("LOT_DUPLICATE", f"referencia de lote repetida en el batch: {ref}")
        vistos.add(ref)
        procedencia = _v(estado, "source_system") or batch.source_system or batch.source_type
        referencia = _v(estado, "source_reference") or batch.source_reference

        existente_id = refs.get("existing_lot_id")
        if existente_id:
            lote = (await self.db.execute(select(Lot).where(Lot.id == existente_id))).scalar_one_or_none()
            if lote is None or lote.company_id != batch.company_id:
                raise CutoverApplyError("LOT_DUPLICATE", f"el lote existente de la fila {item.source_row_number} no pertenece a la empresa")
            if not lote.legacy_lot_code:
                lote.legacy_lot_code = ref
            lote.source_system = lote.source_system or procedencia
            lote.source_reference = lote.source_reference or referencia
            for atributo, clave in (("farm_id", "farm_id"), ("house_id", "house_id"), ("area_id", "area_id"),
                                    ("genetic_line_id", "genetic_line_id"), ("breed_id", "breed_id")):
                if getattr(lote, atributo) is None and refs.get(clave):
                    setattr(lote, atributo, refs[clave])
            if lote.start_date is None:
                lote.start_date = _medianoche(_v(estado, c.lot_date_field))
            return lote, False

        if (await self.db.execute(select(Lot.id).where(Lot.lot_code == ref))).scalar_one_or_none() is not None:
            raise CutoverApplyError("LOT_DUPLICATE", f"el código {ref} ya existe como lote")
        sexo = _v(estado, "sex")
        if sexo is None and c.business_unit in ("broiler", "hatchery"):
            sexo = "mixed"
        lote = Lot(
            company_id=batch.company_id, lot_code=ref, origin="MIGRATED", legacy_lot_code=ref,
            bird_type=BirdTypeEnum(c.bird_type), farm_id=refs.get("farm_id"), house_id=refs.get("house_id"),
            area_id=refs.get("area_id"), genetic_line_id=refs.get("genetic_line_id"), breed_id=refs.get("breed_id"),
            sex=SexEnum(sexo) if sexo else None, hatchery_purpose=_v(estado, "generation") if c.business_unit == "hatchery" else None,
            start_date=_medianoche(_v(estado, c.lot_date_field)), status=LotStatus.ACTIVE, activation_type="normal",
            source_system=procedencia, source_reference=referencia,
        )
        self.db.add(lote)
        await self.db.flush()
        return lote, True

    def _opening_base(self, batch: CutoverBatch, item: CutoverItem, lote: Lot, fase_id: int, estado: dict,
                      derivados: dict) -> dict:
        edad = derivados.get("age_days")
        return dict(
            lot_id=lote.id, activation_date=batch.cutover_datetime.date(), phase_at_activation_id=fase_id,
            age_days=int(edad) if edad is not None else 0, age_status=KNOWN if edad is not None else UNKNOWN,
            is_manual_activation=False, activated_by_id=int(self.current_user["id"]),
            activation_reason="Cutover operacional v2 (SPEC 006)", cutover_item_id=item.id,
            cutover_datetime=batch.cutover_datetime, template_version=batch.template_version or "v2",
            source_system=_v(estado, "source_system") or batch.source_system or batch.source_type,
            source_reference=_v(estado, "source_reference") or batch.source_reference,
            legacy_lot_code=item.legacy_lot_reference,
            accumulated_feed_kg=_opcional(estado, "accumulated_feed_kg"), feed_status=_s(estado, "accumulated_feed_kg"),
            current_avg_weight=_opcional(estado, "current_avg_weight_g"), weight_status=_s(estado, "current_avg_weight_g"),
        )

    def _opening_reproductoras(self, batch, item, lote, fase_id, estado, derivados) -> OpeningBalance:
        base = self._opening_base(batch, item, lote, fase_id, estado, derivados)
        return OpeningBalance(
            **base,
            initial_male_count=_entero(estado, "live_males"), initial_female_count=_entero(estado, "live_females"),
            initial_mixed_count=0, initial_mixed_status=NOT_APPLICABLE,
            placed_male_count=_opcional(estado, "birds_placed_males"), placed_female_count=_opcional(estado, "birds_placed_females"),
            placed_status=_combinado(estado, "birds_placed_males", "birds_placed_females"),
            accumulated_mortality_male=_entero(estado, "historical_mortality_males"),
            accumulated_mortality_female=_entero(estado, "historical_mortality_females"),
            mortality_status=_combinado(estado, "historical_mortality_males", "historical_mortality_females"),
            accumulated_culls_male=_entero(estado, "historical_culls_males"),
            accumulated_culls_female=_entero(estado, "historical_culls_females"),
            culls_status=_combinado(estado, "historical_culls_males", "historical_culls_females"),
            accumulated_egg_production=_opcional(estado, "accumulated_egg_production"),
            egg_production_status=_s(estado, "accumulated_egg_production"),
            accumulated_eggs_to_hatchery=_opcional(estado, "accumulated_eggs_to_hatchery"),
            eggs_to_hatchery_status=_s(estado, "accumulated_eggs_to_hatchery"),
            chicks_hatched_status=NOT_APPLICABLE, broiler_received_status=NOT_APPLICABLE, outbound_status=NOT_APPLICABLE,
        )

    def _opening_engorde(self, batch, item, lote, fase_id, estado, derivados) -> OpeningBalance:
        base = self._opening_base(batch, item, lote, fase_id, estado, derivados)
        return OpeningBalance(
            **base,
            initial_male_count=0, initial_female_count=0,
            initial_mixed_count=_entero(estado, "live_birds"), initial_mixed_status=KNOWN,
            placed_mixed_count=None, placed_status=NOT_APPLICABLE,
            accumulated_broiler_received=_opcional(estado, "accumulated_birds_received"),
            broiler_received_status=_s(estado, "accumulated_birds_received"),
            accumulated_mortality_mixed=_entero(estado, "historical_mortality"), mortality_status=_s(estado, "historical_mortality"),
            accumulated_culls_mixed=_entero(estado, "historical_culls"), culls_status=_s(estado, "historical_culls"),
            accumulated_outbound_birds=_opcional(estado, "partial_outbound_birds"), outbound_status=_s(estado, "partial_outbound_birds"),
            egg_production_status=NOT_APPLICABLE, eggs_to_hatchery_status=NOT_APPLICABLE, chicks_hatched_status=NOT_APPLICABLE,
        )

    def _opening_incubadora(self, batch, item, lote, fase_id, estado, derivados) -> OpeningBalance:
        base = self._opening_base(batch, item, lote, fase_id, estado, derivados)
        base.update(accumulated_feed_kg=None, feed_status=NOT_APPLICABLE, current_avg_weight=None, weight_status=NOT_APPLICABLE)
        return OpeningBalance(
            **base,
            initial_male_count=0, initial_female_count=0,
            initial_mixed_count=_entero(estado, "chicks_available"), initial_mixed_status=_s(estado, "chicks_available"),
            accumulated_chicks_hatched=_opcional(estado, "chicks_hatched"), chicks_hatched_status=_s(estado, "chicks_hatched"),
            mortality_status=NOT_APPLICABLE, culls_status=NOT_APPLICABLE, placed_status=NOT_APPLICABLE,
            egg_production_status=NOT_APPLICABLE, eggs_to_hatchery_status=NOT_APPLICABLE,
            broiler_received_status=NOT_APPLICABLE, outbound_status=NOT_APPLICABLE,
        )

    def _hatchery_opening(self, opening: OpeningBalance, lote: Lot, estado: dict, refs: dict) -> HatcheryOpening:
        return HatcheryOpening(
            opening_id=opening.id, lot_id=lote.id, hatchery_id=refs["hatchery_id"],
            incubator_id=refs.get("incubator_id"), hatcher_id=refs.get("hatcher_id"),
            source_lot_id=refs.get("source_lot_id"), source_lot_reference=_v(estado, "source_lot_code"),
            generation=_v(estado, "generation"), egg_origin=_v(estado, "egg_origin"),
            reception_date=_fecha(_v(estado, "reception_date")),
            set_date=_fecha(_opcional(estado, "set_date")), set_date_status=_s(estado, "set_date"),
            expected_hatch_date=_fecha(_opcional(estado, "expected_hatch_date")),
            expected_hatch_date_status=_s(estado, "expected_hatch_date"),
            eggs_received=_opcional(estado, "eggs_received"), eggs_received_status=_s(estado, "eggs_received"),
            eggs_set=_opcional(estado, "eggs_set"), eggs_set_status=_s(estado, "eggs_set"),
            eggs_transferred=_opcional(estado, "eggs_transferred"), eggs_transferred_status=_s(estado, "eggs_transferred"),
            eggs_discarded=_opcional(estado, "eggs_discarded"), eggs_discarded_status=_s(estado, "eggs_discarded"),
        )

    def _lot_phase(self, lote: Lot, fase_id: int, c: TemplateContract, estado: dict, opening: OpeningBalance) -> LotPhase:
        inicio = _fecha(_opcional(estado, "phase_start_date")) if c.business_unit != "hatchery" else None
        inicio = inicio or _fecha(_v(estado, c.lot_date_field)) or opening.activation_date
        return LotPhase(
            lot_id=lote.id, phase_id=fase_id, start_date=inicio,
            start_population_male=opening.initial_male_count, start_population_female=opening.initial_female_count,
            start_weight_avg=opening.current_avg_weight, is_active=True,
        )

    async def _auditar_fallo_de_apply(self, batch_id: int, company_id: int, error: CutoverApplyError) -> None:
        """`FAILED_APPLY` sobrevive al rollback (patrón `LOGIN_FAILED`): transacción propia."""
        try:
            await audit_accion(
                self.db, usuario=self.current_user, accion=AuditAction.FAILED_APPLY,
                modulo=AuditModule.CUTOVER, entity_type="cutover_batch", entity_id=str(batch_id),
                company_id=company_id, comments=f"{error.code}: {error.message}"[:500],
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()

    async def aplicar(self, batch_id: int) -> CutoverBatch:
        """APPROVED → APPLIED en UNA transacción: lotes + fases + openings (+ incubadora) o nada."""
        batch = await self._batch_propio(batch_id, bloquear=True)
        empresa = batch.company_id
        if batch.status != CutoverBatchStatus.APPROVED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"BATCH_STATE_INVALID: el batch está en estado {batch.status}: solo uno APPROVED se aplica.")

        # OD-16: la BU de la empresa debe estar habilitada y el actor tener alcance.
        habilitadas = await unidades_habilitadas(self.db, empresa)
        if batch.business_unit not in habilitadas:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"BU_DISABLED: la unidad {batch.business_unit} no está habilitada para la empresa.")
        if not self.current_user.get("is_super_admin"):
            from ..business_units.service import unidades_concedidas, unidades_efectivas_por_id

            alcance = set(await unidades_efectivas_por_id(
                self.db, user_id=int(self.current_user["id"]), company_id=empresa)) | \
                set(await unidades_concedidas(
                    self.db, user_id=int(self.current_user["id"]), company_id=empresa))
            if batch.business_unit not in alcance:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"BU_NOT_GRANTED: la unidad {batch.business_unit} no está concedida al actor.")

        items = await self._items(batch)
        if any(item.validation_status != CutoverItemStatus.VALID.value for item in items):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="BATCH_STATE_INVALID: el batch tiene filas inválidas o pendientes: no se aplica.")

        c = contrato(batch.business_unit)
        try:
            fase_implicita = await self._fase_implicita(c.implicit_phase) if c.implicit_phase else None
            vistos: set[str] = set()
            creados = reusados = 0
            for item in items:
                estado = item.opening_state or {}
                refs = estado.get("_refs", {})
                derivados = estado.get("_derived", {})
                fase_id = fase_implicita or refs.get("phase_id")
                if fase_id is None:
                    raise CutoverApplyError("PHASE_REQUIRED", f"la fila {item.source_row_number} no tiene fase productiva resuelta")
                lote, nuevo = await self._lote(batch, item, c, estado, refs, vistos)
                ya = (await self.db.execute(select(OpeningBalance).where(OpeningBalance.lot_id == lote.id))).scalar_one_or_none()
                if ya is not None:
                    raise CutoverApplyError("OPENING_ALREADY_EXISTS", f"el lote {lote.lot_code} ya tiene un saldo de apertura vigente")
                if c.business_unit == "hatchery":
                    opening = self._opening_incubadora(batch, item, lote, fase_id, estado, derivados)
                elif c.business_unit == "broiler":
                    opening = self._opening_engorde(batch, item, lote, fase_id, estado, derivados)
                else:
                    opening = self._opening_reproductoras(batch, item, lote, fase_id, estado, derivados)
                self.db.add(opening)
                await self.db.flush()
                if c.business_unit == "hatchery":
                    if not refs.get("hatchery_id"):
                        raise CutoverApplyError("MASTER_NOT_FOUND", f"la fila {item.source_row_number} no tiene planta resuelta")
                    self.db.add(self._hatchery_opening(opening, lote, estado, refs))
                self.db.add(self._lot_phase(lote, fase_id, c, estado, opening))
                item.lot_id = lote.id
                item.validation_status = CutoverItemStatus.APPLIED.value
                item.applied_at = datetime.now(timezone.utc)
                creados += int(nuevo)
                reusados += int(not nuevo)

            batch.status = CutoverBatchStatus.APPLIED.value  # terminal (AC25)
            batch.applied_by_id = int(self.current_user["id"])
            batch.applied_at = datetime.now(timezone.utc)
            await audit_accion(
                self.db, usuario=self.current_user, accion=AuditAction.APPLY, modulo=AuditModule.CUTOVER,
                entity_type="cutover_batch", entity_id=str(batch.id), company_id=empresa,
                new_state=batch.status, new_values={"lots_created": creados, "lots_reused": reusados,
                                                    "template_version": batch.template_version},
            )
            await self.db.commit()
            await self.db.refresh(batch)
            return batch
        except CutoverApplyError as exc:
            await self.db.rollback()
            await self._auditar_fallo_de_apply(batch_id, empresa, exc)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{exc.code}: {exc.message}") from exc
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as exc:  # rollback total + rastro FAILED_APPLY
            await self.db.rollback()
            await self._auditar_fallo_de_apply(batch_id, empresa, CutoverApplyError("APPLY_FAILED", str(exc)[:300]))
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"APPLY_FAILED: {exc}") from exc

    # ── reconciliación ───────────────────────────────────────────────────────

    @staticmethod
    def _lifetime(opening_valor: Optional[Any], estado: str, post: Any) -> Optional[Any]:
        """UNKNOWN + post = UNKNOWN (jamás se convierte en el post)."""
        if estado != KNOWN or opening_valor is None:
            return None
        return type(post)(opening_valor) + post if isinstance(post, (int, float)) else opening_valor

    async def reconciliacion(self, batch_id: int) -> dict:
        """Opening / Post (`event_date > corte`) / Lifetime / Current por métrica y lote, con UNKNOWN propagado."""
        from .reporting import post_corte_del_lote, post_corte_incubadora

        batch = await self._batch_propio(batch_id)
        corte = batch.cutover_datetime.date()
        items = await self._items(batch)
        lots: list[dict] = []
        unknown_total = 0
        for item in items:
            if item.lot_id is None:
                continue
            opening = (await self.db.execute(
                select(OpeningBalance).where(OpeningBalance.cutover_item_id == item.id))).scalars().first()
            if opening is None:
                continue
            lote = (await self.db.execute(select(Lot).where(Lot.id == item.lot_id))).scalars().first()
            post = await post_corte_del_lote(self.db, item.lot_id, corte)
            unknown_total += sum(1 for campo in _ESTADOS_V2 if getattr(opening, campo, None) == UNKNOWN)

            live = int(opening.initial_male_count or 0) + int(opening.initial_female_count or 0) + int(opening.initial_mixed_count or 0)
            historico_mort = ((int(opening.accumulated_mortality_male or 0) + int(opening.accumulated_mortality_female or 0)
                               + int(opening.accumulated_mortality_mixed or 0)) if opening.mortality_status == KNOWN else None)
            historico_culls = ((int(opening.accumulated_culls_male or 0) + int(opening.accumulated_culls_female or 0)
                                + int(opening.accumulated_culls_mixed or 0)) if opening.culls_status == KNOWN else None)
            feed_opening = float(opening.accumulated_feed_kg) if (opening.feed_status == KNOWN and opening.accumulated_feed_kg is not None) else None

            fila: dict[str, Any] = {
                "lot_id": item.lot_id, "lot_code": lote.lot_code if lote else None,
                "legacy_lot_code": (lote.legacy_lot_code if lote else None) or item.legacy_lot_reference,
                "origin": lote.origin if lote else None, "business_unit": batch.business_unit,
                "opening": {
                    "live": live, "live_males": int(opening.initial_male_count or 0),
                    "live_females": int(opening.initial_female_count or 0), "live_mixed": int(opening.initial_mixed_count or 0),
                    "live_mixed_status": opening.initial_mixed_status,
                    "historical_mortality": historico_mort, "mortality_status": opening.mortality_status,
                    "historical_culls": historico_culls, "culls_status": opening.culls_status,
                    "feed_kg": feed_opening, "feed_status": opening.feed_status,
                    "avg_weight_g": opening.current_avg_weight if opening.weight_status == KNOWN else None,
                    "weight_status": opening.weight_status,
                    "egg_production": opening.accumulated_egg_production if opening.egg_production_status == KNOWN else None,
                    "egg_production_status": opening.egg_production_status,
                    "eggs_to_hatchery": opening.accumulated_eggs_to_hatchery if opening.eggs_to_hatchery_status == KNOWN else None,
                    "eggs_to_hatchery_status": opening.eggs_to_hatchery_status,
                    "birds_received": opening.accumulated_broiler_received if opening.broiler_received_status == KNOWN else None,
                    "broiler_received_status": opening.broiler_received_status,
                    "outbound_birds": opening.accumulated_outbound_birds if opening.outbound_status == KNOWN else None,
                    "outbound_status": opening.outbound_status,
                    "chicks_hatched": opening.accumulated_chicks_hatched if opening.chicks_hatched_status == KNOWN else None,
                    "chicks_hatched_status": opening.chicks_hatched_status,
                    "age_days": opening.age_days if opening.age_status == KNOWN else None, "age_status": opening.age_status,
                    "hatchery": None,
                },
                "post": {
                    "mortality": post["mortality"], "culls": post["culls"], "salidas": post["salidas"], "entradas": post["entradas"],
                    # Compatibilidad GA-REQ-061 (AC77): con alimento UNKNOWN el total mixto no se presenta; el post real va aparte.
                    "feed_kg": post["feed_kg"] if opening.feed_status == KNOWN else None,
                    "feed_kg_registered": post["feed_kg"],
                    "eggs_collected": post["eggs_collected"], "eggs_dispatched": post["eggs_dispatched"],
                },
                "lifetime": {
                    "mortality": self._lifetime(historico_mort, opening.mortality_status, post["mortality"]),
                    "culls": self._lifetime(historico_culls, opening.culls_status, post["culls"]),
                    "feed_kg": self._lifetime(feed_opening, opening.feed_status, post["feed_kg"]),
                    "egg_production": self._lifetime(opening.accumulated_egg_production, opening.egg_production_status, post["eggs_collected"]),
                    "eggs_to_hatchery": self._lifetime(opening.accumulated_eggs_to_hatchery, opening.eggs_to_hatchery_status, post["eggs_dispatched"]),
                },
                "current_live": live + post["entradas"] - post["salidas"],
                "current": {"live": live + post["entradas"] - post["salidas"]},
            }
            if batch.business_unit == "hatchery":
                ho = (await self.db.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == item.lot_id))).scalars().first()
                post_inc = await post_corte_incubadora(self.db, item.lot_id, corte)
                if ho is not None:
                    recibidos = ho.eggs_received if ho.eggs_received_status == KNOWN else None
                    cargados = ho.eggs_set if ho.eggs_set_status == KNOWN else None
                    transferidos = ho.eggs_transferred if ho.eggs_transferred_status == KNOWN else None
                    descartados = ho.eggs_discarded if ho.eggs_discarded_status == KNOWN else None
                    en_proceso = (cargados - transferidos - descartados) if None not in (cargados, transferidos, descartados) else None
                    fila["opening"]["hatchery"] = {
                        "hatchery_id": ho.hatchery_id, "incubator_id": ho.incubator_id, "hatcher_id": ho.hatcher_id,
                        "source_lot_id": ho.source_lot_id, "source_lot_reference": ho.source_lot_reference, "generation": ho.generation,
                        "reception_date": ho.reception_date.isoformat() if ho.reception_date else None,
                        "set_date": ho.set_date.isoformat() if (ho.set_date and ho.set_date_status == KNOWN) else None,
                        "set_date_status": ho.set_date_status,
                        "expected_hatch_date": ho.expected_hatch_date.isoformat() if (ho.expected_hatch_date and ho.expected_hatch_date_status == KNOWN) else None,
                        "expected_hatch_date_status": ho.expected_hatch_date_status,
                        "eggs_received": recibidos, "eggs_received_status": ho.eggs_received_status,
                        "eggs_set": cargados, "eggs_set_status": ho.eggs_set_status,
                        "eggs_transferred": transferidos, "eggs_transferred_status": ho.eggs_transferred_status,
                        "eggs_discarded": descartados, "eggs_discarded_status": ho.eggs_discarded_status,
                        "eggs_in_process": en_proceso,
                        "chicks_available": opening.initial_mixed_count if opening.initial_mixed_status == KNOWN else None,
                        "chicks_available_status": opening.initial_mixed_status,
                    }
                    fila["post"].update(post_inc)
                    fila["lifetime"]["chicks_hatched"] = self._lifetime(
                        opening.accumulated_chicks_hatched, opening.chicks_hatched_status, post_inc["chicks_hatched"])
                    fila["lifetime"]["eggs_set"] = self._lifetime(cargados, ho.eggs_set_status, post_inc["eggs_loaded"])
                    fila["current"].update({
                        "eggs_available_hatchery": ((recibidos - cargados) if None not in (recibidos, cargados) else None),
                        "eggs_in_process": ((en_proceso + post_inc["eggs_loaded"] - post_inc["eggs_transferred"]) if en_proceso is not None else None),
                        "chicks_available": ((opening.initial_mixed_count + post_inc["chicks_hatched"] - post_inc["chicks_dispatched"]
                                              - post["mortality"] - post["culls"]) if opening.initial_mixed_status == KNOWN else None),
                    })
                    if fila["current"]["eggs_available_hatchery"] is not None:
                        fila["current"]["eggs_available_hatchery"] += post_inc["eggs_received_hatchery"] - post_inc["eggs_loaded"]
            lots.append(fila)

        return {
            "batch_id": batch.id, "company_id": batch.company_id, "business_unit": batch.business_unit,
            "cutover_datetime": batch.cutover_datetime, "status": batch.status,
            "source": {"type": batch.source_type, "system": batch.source_system, "reference": batch.source_reference,
                       "filename": batch.source_filename, "checksum": batch.source_checksum_sha256,
                       "template_version": batch.template_version},
            "items": len(items), "openings": len(lots), "unknown_metrics": unknown_total,
            "applied_by_id": batch.applied_by_id, "applied_at": batch.applied_at, "lots": lots,
        }
