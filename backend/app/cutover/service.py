"""GA-REQ-061 · Cutover — servicio del ciclo crear→subir→validar (C2).

Reglas duras del checkpoint: el Excel pasa por staging (AC43/44); los errores son
estructurados con `error_code`/`received_value` (AC46); `template_version` se
valida (AC45); el re-upload del mismo archivo no duplica filas (AC50); el
`source_checksum_sha256` se conserva como evidencia de la carga (AC49).
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_accion
from ..audit.models import AuditAction, AuditModule
from ..business_units.service import unidades_habilitadas
from ..lots.models import OpeningBalance
from ..masters.models import BirdTypeEnum, Farm, Lot, LotStatus, ProductivePhase
from .models import CutoverBatch, CutoverBatchStatus, CutoverItem, CutoverItemStatus, CutoverStagingRow
from .parser import CutoverParseError, parse_cutover_workbook
from .schemas import CutoverBatchCreate

#: Estados por métrica del opening (`UNKNOWN` nunca se muestra como `0`).
_METRICAS_DE_OPENING = (
    "mortality_status", "culls_status", "feed_status",
    "egg_production_status", "chicks_hatched_status", "broiler_received_status",
)

_ESTADOS_CARGABLES = {
    CutoverBatchStatus.DRAFT.value,
    CutoverBatchStatus.VALIDATING.value,
    CutoverBatchStatus.VALIDATED.value,
}


class CutoverApplyError(Exception):
    """Fallo de dominio durante el apply — viaja como `error_code` y dispara rollback."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


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
        # Idempotencia de BD (constraint único company/BU/checksum/corte): un archivo
        # idéntico ya cargado en OTRO batch del mismo corte ⇒ 409 determinista, no 500.
        otro = (await self.db.execute(select(CutoverBatch).where(
            CutoverBatch.company_id == batch.company_id,
            CutoverBatch.business_unit == batch.business_unit,
            CutoverBatch.cutover_datetime == batch.cutover_datetime,
            CutoverBatch.source_checksum_sha256 == checksum,
            CutoverBatch.id != batch.id,
        ))).scalar_one_or_none()
        if otro is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"DUPLICATE_UPLOAD: el mismo archivo ya fue cargado en el batch {otro.id} (mismo corte).",
            )
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
                    if not granja.is_active:
                        # OD-21/AC52: un maestro inactivo no admite referencias NUEVAS.
                        # AC53: la referencia histórica de un lote existente se conserva.
                        referencia = normalizado.get("legacy_lot_code")
                        existente = None
                        if referencia:
                            existente = (await self.db.execute(select(Lot).where(
                                Lot.company_id == batch.company_id,
                                (Lot.lot_code == referencia) | (Lot.legacy_lot_code == referencia),
                            ))).scalars().first()
                        if existente is None:
                            errores.append({
                                "row_number": fila["row_number"], "column": "farm_code", "field": "farm_code",
                                "error_code": "MASTER_INACTIVE",
                                "message": "La granja está inactiva: no admite referencias nuevas (OD-21).",
                                "received_value": codigo_granja,
                            })

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

    async def enviar_a_aprobacion(self, batch_id: int) -> CutoverBatch:
        """VALIDATED → PENDING_APPROVAL (un batch sin filas válidas no se envía)."""
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status != CutoverBatchStatus.VALIDATED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"El batch está en estado {batch.status}: solo uno VALIDATED se envía.")
        if batch.valid_rows < 1 or batch.invalid_rows > 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="El batch no tiene filas válidas suficientes para enviarse.")
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Segregación de funciones: el creador no puede aprobar ni rechazar su propio batch.",
            )

    async def aprobar(self, batch_id: int) -> CutoverBatch:
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status != CutoverBatchStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"El batch está en estado {batch.status}: solo uno PENDING_APPROVAL se aprueba.")
        self._exigir_segregacion(batch)
        batch.status = CutoverBatchStatus.APPROVED.value
        batch.approved_by_id = int(self.current_user["id"])
        batch.approved_at = datetime.now(timezone.utc)
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.APPROVED, modulo=AuditModule.CUTOVER,
            entity_type="cutover_batch", entity_id=str(batch.id), company_id=batch.company_id,
            new_state=batch.status,
        )
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def rechazar(self, batch_id: int, reason: str) -> CutoverBatch:
        batch = await self._batch_propio(batch_id, bloquear=True)
        if batch.status != CutoverBatchStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"El batch está en estado {batch.status}: solo uno PENDING_APPROVAL se rechaza.")
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

    # ── C4 · apply atómico ────────────────────────────────────────────────────

    async def _resolver_fase(self) -> int:
        fase = (await self.db.execute(
            select(ProductivePhase).where(ProductivePhase.is_active == True)  # noqa: E712
            .order_by(ProductivePhase.order, ProductivePhase.id).limit(1))).scalar_one_or_none()
        if fase is None:
            raise CutoverApplyError("PHASE_REQUIRED",
                                    "No hay fases productivas activas para anclar el opening.")
        return fase.id

    async def _crear_o_reusar_lote(self, batch: CutoverBatch, item: CutoverItem, ref: str,
                                   vistos: set[str]) -> tuple[Lot, bool]:
        """AC20-22: reusa el lote existente (no duplica); crea el migrado si no existe."""
        if ref in vistos:
            raise CutoverApplyError("LOT_DUPLICATE", f"referencia de lote repetida en el batch: {ref}")
        vistos.add(ref)
        existente = (await self.db.execute(select(Lot).where(Lot.lot_code == ref))).scalar_one_or_none()
        if existente is not None:
            if existente.company_id != batch.company_id:
                raise CutoverApplyError("LOT_DUPLICATE", f"el código {ref} pertenece a otra empresa")
            if not existente.legacy_lot_code:
                existente.legacy_lot_code = ref
            return existente, False
        estado = item.opening_state or {}
        arranque = estado.get("real_start_date")
        lote = Lot(
            company_id=batch.company_id, lot_code=ref, origin="MIGRATED", legacy_lot_code=ref,
            bird_type=BirdTypeEnum(batch.business_unit),
            start_date=(datetime.combine(date.fromisoformat(arranque), time.min, tzinfo=timezone.utc)
                        if arranque else None),
            status=LotStatus.ACTIVE, activation_type="normal", farm_id=estado.get("farm_id"),
        )
        self.db.add(lote)
        await self.db.flush()
        return lote, True

    def _construir_opening(self, batch: CutoverBatch, item: CutoverItem, lote: Lot, fase_id: int) -> OpeningBalance:
        """`initial_*` = **saldo vivo al corte** (lo histórico NO se resta otra vez, RC-08)."""
        estado = item.opening_state or {}
        fecha_corte = batch.cutover_datetime.date() if batch.cutover_datetime else date.today()
        arranque = estado.get("real_start_date")
        try:
            age = max(0, (fecha_corte - date.fromisoformat(arranque)).days) if arranque else 0
        except (ValueError, TypeError):
            age = 0
        hm, hf = estado.get("historical_mortality_males"), estado.get("historical_mortality_females")
        bu = batch.business_unit
        return OpeningBalance(
            lot_id=lote.id, activation_date=fecha_corte, phase_at_activation_id=fase_id, age_days=age,
            initial_male_count=estado.get("live_males") or 0,
            initial_female_count=estado.get("live_females") or 0,
            accumulated_mortality_male=hm or 0, accumulated_mortality_female=hf or 0,
            accumulated_culls_male=0, accumulated_culls_female=0,
            is_manual_activation=False, activated_by_id=int(self.current_user["id"]),
            activation_reason="Cutover operacional (GA-REQ-061)",
            cutover_item_id=item.id, cutover_datetime=batch.cutover_datetime,
            mortality_status="KNOWN" if (hm is not None and hf is not None) else "UNKNOWN",
            culls_status="UNKNOWN", feed_status="UNKNOWN",
            egg_production_status="NOT_APPLICABLE" if bu in ("hatchery", "broiler") else "UNKNOWN",
            chicks_hatched_status="NOT_APPLICABLE" if bu == "broiler" else "UNKNOWN",
            broiler_received_status="UNKNOWN" if bu == "broiler" else "NOT_APPLICABLE",
            source_system=batch.source_system or "EXCEL", source_reference=batch.source_reference,
            legacy_lot_code=item.legacy_lot_reference,
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
        """APPROVED → APPLIED en UNA transacción: lotes + openings o nada (AC26-30)."""
        batch = await self._batch_propio(batch_id, bloquear=True)
        empresa = batch.company_id
        if batch.status != CutoverBatchStatus.APPROVED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"El batch está en estado {batch.status}: solo uno APPROVED se aplica.")

        # OD-16: la BU de la empresa debe estar habilitada y el actor tener alcance.
        habilitadas = await unidades_habilitadas(self.db, empresa)
        if batch.business_unit not in habilitadas:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"BU_DISABLED: la unidad {batch.business_unit} no está habilitada para la empresa.")
        if not self.current_user.get("is_super_admin"):
            # El alcance del actor se resuelve contra la base (patrón de `/me`):
            # `current_user` de sesión no trae las listas de unidades.
            from ..business_units.service import unidades_concedidas, unidades_efectivas_por_id

            alcance = set(await unidades_efectivas_por_id(
                self.db, user_id=int(self.current_user["id"]), company_id=empresa)) | \
                set(await unidades_concedidas(
                    self.db, user_id=int(self.current_user["id"]), company_id=empresa))
            if batch.business_unit not in alcance:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"La unidad {batch.business_unit} no está concedida al actor.")

        items = list((await self.db.execute(
            select(CutoverItem).where(CutoverItem.batch_id == batch.id)
            .order_by(CutoverItem.source_row_number))).scalars().all())
        if any(item.validation_status != CutoverItemStatus.VALID.value for item in items):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="El batch tiene filas inválidas o pendientes: no se aplica.")

        try:
            fase_id = await self._resolver_fase()
            vistos: set[str] = set()
            creados = reusados = 0
            for item in items:
                ref = item.legacy_lot_reference or f"CUT-ITEM-{item.id}"
                lote, nuevo = await self._crear_o_reusar_lote(batch, item, ref, vistos)
                ya = (await self.db.execute(
                    select(OpeningBalance).where(OpeningBalance.lot_id == lote.id))).scalar_one_or_none()
                if ya is not None:
                    raise CutoverApplyError("OPENING_ALREADY_EXISTS",
                                            f"el lote {ref} ya tiene un saldo de apertura vigente")
                self.db.add(self._construir_opening(batch, item, lote, fase_id))
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
                new_state=batch.status, new_values={"lots_created": creados, "lots_reused": reusados},
            )
            await self.db.commit()
            await self.db.refresh(batch)
            return batch
        except CutoverApplyError as exc:
            await self.db.rollback()
            await self._auditar_fallo_de_apply(batch_id, empresa, exc)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"{exc.code}: {exc.message}") from exc
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as exc:  # rollback total + rastro FAILED_APPLY
            await self.db.rollback()
            await self._auditar_fallo_de_apply(batch_id, empresa,
                                               CutoverApplyError("APPLY_FAILED", str(exc)[:300]))
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"APPLY_FAILED: {exc}") from exc

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

    async def reconciliacion(self, batch_id: int) -> dict:
        """C5: Opening + Post (motor, `event_date > corte`) + Lifetime, por lote.

        El saldo vivo es `apertura − salidas post-cutover`; el histórico **no** se
        vuelve a restar (el doble descuento 10.000−500−35=9.465 está prohibido,
        golden 9.965 — `docs/02 §3.9.2`). Toda métrica sin dato queda `null` con
        su estado `UNKNOWN`, jamás un `0` fabricado.
        """
        from .reporting import post_corte_del_lote

        batch = await self._batch_propio(batch_id)
        corte = batch.cutover_datetime.date() if batch.cutover_datetime else None
        resultado = await self.db.execute(select(CutoverItem)
                                          .where(CutoverItem.batch_id == batch.id)
                                          .order_by(CutoverItem.source_row_number))
        items = list(resultado.scalars().all())

        lots: list[dict] = []
        unknown_total = 0
        for item in items:
            if item.lot_id is None:
                continue
            opening = (await self.db.execute(
                select(OpeningBalance).where(OpeningBalance.cutover_item_id == item.id))).scalars().first()
            if opening is None:
                continue
            lote = (await self.db.execute(
                select(Lot).where(Lot.id == item.lot_id))).scalars().first()
            post = await post_corte_del_lote(self.db, item.lot_id, corte) if corte else {
                "mortality": 0, "culls": 0, "salidas": 0, "feed_kg": 0.0}

            live = int(opening.initial_male_count or 0) + int(opening.initial_female_count or 0)
            conocido = opening.mortality_status == "KNOWN"
            historico = None
            if conocido:
                historico = (int(opening.accumulated_mortality_male or 0)
                             + int(opening.accumulated_mortality_female or 0))
            lifetime = (historico + post["mortality"]) if conocido else None
            feed_kg = post["feed_kg"] if opening.feed_status == "KNOWN" else None

            unknown_total += sum(
                1 for campo in _METRICAS_DE_OPENING if getattr(opening, campo) == "UNKNOWN")

            lots.append({
                "lot_id": item.lot_id,
                "legacy_lot_code": (lote.legacy_lot_code if lote else None) or item.legacy_lot_reference,
                "origin": lote.origin if lote else None,
                "opening": {
                    "live": live,
                    "historical_mortality": historico,
                    "mortality_status": opening.mortality_status,
                    "feed_status": opening.feed_status,
                },
                "post": {
                    "mortality": post["mortality"],
                    "culls": post["culls"],
                    "feed_kg": feed_kg,
                },
                "lifetime": {"mortality": lifetime},
                "current_live": live - post["salidas"],
            })

        return {
            "batch_id": batch.id,
            "company_id": batch.company_id,
            "business_unit": batch.business_unit,
            "cutover_datetime": batch.cutover_datetime,
            "status": batch.status,
            "source": {
                "type": batch.source_type,
                "system": batch.source_system,
                "reference": batch.source_reference,
                "filename": batch.source_filename,
                "checksum": batch.source_checksum_sha256,
                "template_version": batch.template_version,
            },
            "items": len(items),
            "openings": len(lots),
            "unknown_metrics": unknown_total,
            "applied_by_id": batch.applied_by_id,
            "applied_at": batch.applied_at,
            "lots": lots,
        }
