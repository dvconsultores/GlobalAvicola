"""GA-REQ-061 · Cutover — servicio del ciclo crear→subir→validar (C2).

Reglas duras del checkpoint: el Excel pasa por staging (AC43/44); los errores son
estructurados con `error_code`/`received_value` (AC46); `template_version` se
valida (AC45); el re-upload del mismo archivo no duplica filas (AC50); el
`source_checksum_sha256` se conserva como evidencia de la carga (AC49).
"""
from __future__ import annotations

import hashlib
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_accion
from ..audit.models import AuditAction, AuditModule
from ..masters.models import Farm
from .models import CutoverBatch, CutoverBatchStatus, CutoverItem, CutoverItemStatus, CutoverStagingRow
from .parser import CutoverParseError, parse_cutover_workbook
from .schemas import CutoverBatchCreate

_ESTADOS_CARGABLES = {
    CutoverBatchStatus.DRAFT.value,
    CutoverBatchStatus.VALIDATING.value,
    CutoverBatchStatus.VALIDATED.value,
}


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

    async def crear_batch(self, data: CutoverBatchCreate) -> CutoverBatch:
        """`POST /cutover-batches` — nace en DRAFT con actor y empresa efectiva."""
        batch = CutoverBatch(
            company_id=self._empresa(),
            business_unit=data.business_unit,
            cutover_datetime=data.cutover_datetime,
            source_type="EXCEL",
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

    async def subir_y_validar(self, batch_id: int, filename: str, content: bytes) -> CutoverBatch:
        """Upload → parse → staging → validación. Sin efectos operacionales."""
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status not in _ESTADOS_CARGABLES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El batch está en estado {batch.status}: ya no admite cargas.",
            )

        checksum = hashlib.sha256(content).hexdigest()
        try:
            parsed = parse_cutover_workbook(content)
        except CutoverParseError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"{exc.code}: {exc.message}") from exc

        if parsed["business_unit"] != batch.business_unit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(f"BUSINESS_UNIT_MISMATCH: la plantilla es de {parsed['business_unit']} "
                        f"y el batch es de {batch.business_unit}."),
            )

        # ── Validación contra maestros (solo referencia NUEVA: OD-21) ──────────
        codigos = {f["normalized"].get("farm_code") for f in parsed["rows"] if f["normalized"].get("farm_code")}
        granjas: dict[str, Farm] = {}
        if codigos:
            resultado = await self.db.execute(
                select(Farm).where(Farm.company_id == batch.company_id, Farm.code.in_(codigos)))
            granjas = {g.code: g for g in resultado.scalars().all() if g.code}

        # ── Staging re-creado (idempotente: re-subir el mismo archivo no duplica) ──
        await self.db.execute(delete(CutoverItem).where(CutoverItem.batch_id == batch.id))
        await self.db.execute(delete(CutoverStagingRow).where(CutoverStagingRow.batch_id == batch.id))

        validas = invalidas = 0
        for fila in parsed["rows"]:
            errores = list(fila["errors"])
            normalizado = dict(fila["normalized"])
            codigo_granja = normalizado.get("farm_code")
            if codigo_granja:
                granja = granjas.get(codigo_granja)
                if granja is None:
                    errores.append({
                        "row_number": fila["row_number"], "column": "farm_code", "field": "farm_code",
                        "error_code": "MASTER_NOT_FOUND",
                        "message": "Granja no existe o no pertenece a la empresa.",
                        "received_value": codigo_granja,
                    })
                else:
                    normalizado["farm_id"] = granja.id

            estado = CutoverItemStatus.VALID.value if not errores else CutoverItemStatus.INVALID.value
            validas += estado == CutoverItemStatus.VALID.value
            invalidas += estado == CutoverItemStatus.INVALID.value

            self.db.add(CutoverStagingRow(
                batch_id=batch.id, row_number=fila["row_number"], raw=fila["raw"],
                normalized=normalizado, validation_status=estado,
                validation_errors=errores or None,
            ))
            self.db.add(CutoverItem(
                batch_id=batch.id, company_id=batch.company_id, business_unit=batch.business_unit,
                legacy_lot_reference=normalizado.get("legacy_lot_code"),
                real_start_date=(__import__("datetime").date.fromisoformat(normalizado["real_start_date"])
                                 if normalizado.get("real_start_date") else None),
                cutover_datetime=batch.cutover_datetime,
                opening_state=normalizado,
                source_row_number=fila["row_number"],
                validation_status=estado, validation_errors=errores or None,
            ))

        batch.source_filename = filename
        batch.source_checksum_sha256 = checksum
        batch.template_version = parsed["template_version"]
        batch.total_rows = len(parsed["rows"])
        batch.valid_rows = validas
        batch.invalid_rows = invalidas
        if invalidas == 0:
            batch.status = CutoverBatchStatus.VALIDATED.value
            batch.validated_by_id = int(self.current_user["id"])
            from datetime import datetime, timezone
            batch.validated_at = datetime.now(timezone.utc)
        else:
            batch.status = CutoverBatchStatus.VALIDATING.value

        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.UPLOAD, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id,
            comments=filename,
            new_values={"checksum": checksum, "size_bytes": len(content),
                        "business_unit": batch.business_unit},
        )
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.VALIDATE, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id,
            new_values={"total": batch.total_rows, "valid": validas, "invalid": invalidas,
                        "business_unit": batch.business_unit},
        )
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def validacion(self, batch_id: int) -> dict:
        batch = await self._batch_propio(batch_id)
        resultado = await self.db.execute(
            select(CutoverItem).where(CutoverItem.batch_id == batch.id).order_by(CutoverItem.source_row_number))
        errores: list[dict] = []
        for item in resultado.scalars().all():
            for err in (item.validation_errors or []):
                errores.append(err)
        return {
            "batch_id": batch.id, "status": batch.status,
            "total_rows": batch.total_rows, "valid_rows": batch.valid_rows,
            "invalid_rows": batch.invalid_rows, "errors": errores,
        }

    async def items(self, batch_id: int) -> list[CutoverItem]:
        batch = await self._batch_propio(batch_id)
        resultado = await self.db.execute(
            select(CutoverItem).where(CutoverItem.batch_id == batch.id).order_by(CutoverItem.source_row_number))
        return list(resultado.scalars().all())
