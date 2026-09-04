"""
SAP Integration Service — consolidation, import/export, idempotency, retries.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...operations.models import EventStatus, OperationalEvent
from . import models, schemas
from .adapter import (
    ManualSapAdapter,
    MockSapAdapter,
    SapExportPayload,
    SapExportResult,
    SapIntegrationAdapter,
    generate_idempotency_key,
)


class SapService:
    """Handles SAP references import, consolidation, and export."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")
        # Default: Manual adapter. Can be swapped via config.
        self._adapter: Optional[SapIntegrationAdapter] = None

    #: GA-REM-010 — adaptadores disponibles, seleccionables por configuración.
    #: "real" queda registrado y aún no implementado (GA-REM-017, BLOCKED_EXTERNAL).
    _ADAPTERS = {
        "manual": ManualSapAdapter,
        "mock": MockSapAdapter,
    }

    def get_adapter(self) -> SapIntegrationAdapter:
        """GA-REM-010: el adaptador se elige por configuración, no por código."""
        if self._adapter is None:
            from ...config import settings

            name = (getattr(settings, "SAP_ADAPTER", None) or "manual").strip().lower()
            if name == "real":
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=(
                        "El adaptador SAP real no está implementado (GA-REM-017). "
                        "Configure SAP_ADAPTER=manual mientras tanto."
                    ),
                )
            adapter_cls = self._ADAPTERS.get(name)
            if adapter_cls is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"SAP_ADAPTER='{name}' no es un adaptador válido. "
                           f"Válidos: {', '.join(self._ADAPTERS)}.",
                )
            self._adapter = adapter_cls()
        return self._adapter

    def _require_company_id(self) -> int:
        """Return the company_id, raising an error if None (e.g. for write operations)."""
        if self.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operación requiere una empresa asignada. Los super administradores deben seleccionar una empresa.",
            )
        return self.company_id

    def _company_filter(self, model_column):
        """Return a where clause for company_id, or a no-op (True) for super admins."""
        if self.company_id is not None:
            return model_column == self.company_id
        from sqlalchemy import true
        return true()  # No filter for super admins — sees all companies

    # ============================================================
    # SAP References Import
    # ============================================================

    async def import_references(self, data: schemas.SapReferenceImportRequest) -> list[models.SapReference]:
        """Bulk import SAP references."""
        cid = self._require_company_id()
        refs = []
        for item in data.references:
            ref = models.SapReference(
                company_id=cid,
                ref_type=models.SapReferenceType(item.ref_type),
                sap_code=item.sap_code,
                description=item.description,
                extra_data=item.extra_data,
                imported_by_id=self.current_user["id"],
            )
            self.db.add(ref)
            refs.append(ref)

        # Create sync job for audit
        job = models.SapSyncJob(
            company_id=cid,
            direction=models.SyncDirection.IMPORT,
            status=models.SyncStatus.COMPLETED,
            total_records=len(refs),
            success_count=len(refs),
            initiated_by_id=self.current_user["id"],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()
        return refs

    async def list_references(
        self, ref_type: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[models.SapReference], int]:
        base = select(models.SapReference).where(
            self._company_filter(models.SapReference.company_id),
            models.SapReference.is_active == True,
        )
        cq = select(func_count()).select_from(models.SapReference).where(
            self._company_filter(models.SapReference.company_id),
            models.SapReference.is_active == True,
        )
        if ref_type:
            base = base.where(models.SapReference.ref_type == ref_type)
            cq = cq.where(models.SapReference.ref_type == ref_type)

        base = base.order_by(models.SapReference.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(base)
        refs = list(result.scalars().all())
        cr = await self.db.execute(cq)
        total = cr.scalar() or 0
        return refs, total

    # ============================================================
    # Consolidation
    # ============================================================

    async def consolidate_approved(
        self, lot_id: Optional[int] = None, event_type: Optional[str] = None,
        date_from: Optional[str] = None, date_to: Optional[str] = None,
    ) -> list[models.ConsolidatedMovement]:
        """Group approved events into consolidated movements ready for SAP export."""

        # Find approved events not yet consolidated
        base = select(OperationalEvent).where(
            self._company_filter(OperationalEvent.company_id),
            OperationalEvent.status == EventStatus.APPROVED,
        )
        if lot_id:
            base = base.where(OperationalEvent.lot_id == lot_id)
        if event_type:
            base = base.where(OperationalEvent.event_type == event_type)
        if date_from:
            base = base.where(OperationalEvent.event_date >= date_from)
        if date_to:
            base = base.where(OperationalEvent.event_date <= date_to)

        base = base.order_by(OperationalEvent.lot_id, OperationalEvent.event_type, OperationalEvent.event_date)

        result = await self.db.execute(base)
        events = list(result.scalars().all())

        if not events:
            return []

        # Group by (lot_id, event_type)
        groups: dict[tuple[int, str], list[OperationalEvent]] = {}
        for ev in events:
            key = (ev.lot_id, ev.event_type.value)
            groups.setdefault(key, []).append(ev)

        consolidated = []
        for (lot_id_key, ev_type), evs in groups.items():
            # Calculate totals from sub-movements
            total_qty = 0.0
            unit = "units"
            # Load sub-movements to sum quantities
            for ev in evs:
                for bm in ev.bird_movements:
                    total_qty += bm.quantity
                    unit = "aves"
                for em in ev.egg_movements:
                    total_qty += em.quantity
                    unit = "huevos"
                for fm in ev.feed_movements:
                    total_qty += fm.quantity_kg
                    unit = "kg"

            # Find date range
            dates = [ev.event_date for ev in evs]
            period_start = min(dates) if dates else datetime.now(timezone.utc)
            period_end = max(dates) if dates else datetime.now(timezone.utc)

            cm = models.ConsolidatedMovement(
                company_id=self._require_company_id(),
                lot_id=lot_id_key,
                event_type=ev_type,
                period_start=period_start,
                period_end=period_end,
                event_ids=[ev.id for ev in evs],
                total_quantity=total_qty,
                unit=unit,
                sap_reference=evs[0].sap_document_ref,
                consolidated_by_id=self.current_user["id"],
            )
            self.db.add(cm)
            consolidated.append(cm)

            # Mark events as CONSOLIDATED
            for ev in evs:
                ev.status = EventStatus.CONSOLIDATED

        await self.db.flush()
        return consolidated

    # ============================================================
    # SAP Export
    # ============================================================

    async def export_to_sap(
        self, consolidated_ids: Optional[list[int]] = None, file_name: Optional[str] = None,
    ) -> schemas.SapExportResponse:
        """Export consolidated movements to SAP via the active adapter."""

        # Find consolidated movements not yet exported
        base = select(models.ConsolidatedMovement).where(
            self._company_filter(models.ConsolidatedMovement.company_id),
            models.ConsolidatedMovement.sap_payload_id == None,  # not yet exported
        )
        if consolidated_ids:
            base = base.where(models.ConsolidatedMovement.id.in_(consolidated_ids))
        base = base.order_by(models.ConsolidatedMovement.created_at)

        result = await self.db.execute(base)
        movements = list(result.scalars().all())

        if not movements:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay movimientos consolidados pendientes de exportación",
            )

        # Create sync job
        job = models.SapSyncJob(
            company_id=self._require_company_id(),
            direction=models.SyncDirection.EXPORT,
            status=models.SyncStatus.IN_PROGRESS,
            total_records=len(movements),
            file_name=file_name,
            initiated_by_id=self.current_user["id"],
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()

        adapter = self.get_adapter()
        payloads_created = 0
        success_count = 0
        error_count = 0

        for cm in movements:
            # Generate idempotency key
            data_str = json.dumps(cm.event_ids, sort_keys=True)
            idem_key = generate_idempotency_key(
                cm.lot_id, cm.event_type,
                cm.period_start.isoformat(), cm.sap_reference or "", data_str
            )

            # Check for existing confirmed payload (idempotency)
            existing = await self.db.execute(
                select(models.SapPayload).where(
                    models.SapPayload.idempotency_key == idem_key,
                    models.SapPayload.status == models.PayloadStatus.CONFIRMED,
                )
            )
            if existing.scalar_one_or_none():
                # Already sent, just link
                cm.sap_payload_id = existing.scalar_one_or_none().id
                success_count += 1
                continue

            # Build payload for adapter
            export_payload = SapExportPayload(
                idempotency_key=idem_key,
                event_type=cm.event_type,
                lot_id=cm.lot_id,
                company_id=cm.company_id,
                event_date=cm.period_start.isoformat(),
                quantity=cm.total_quantity,
                unit=cm.unit or "units",
                sap_reference=cm.sap_reference,
                extra_data={"event_ids": cm.event_ids, "period_end": cm.period_end.isoformat()},
            )

            # Create SapPayload record
            sap_payload = models.SapPayload(
                company_id=self._require_company_id(),
                sync_job_id=job.id,
                consolidated_movement_id=cm.id,
                idempotency_key=idem_key,
                payload_data=export_payload.model_dump(),
                status=models.PayloadStatus.SENDING,
            )
            self.db.add(sap_payload)
            await self.db.flush()

            # Send via adapter
            result: SapExportResult = await adapter.export_consolidated(export_payload)

            # Record response
            response = models.SapResponse(
                payload_id=sap_payload.id,
                status_code=result.status_code,
                sap_document_id=result.sap_document_id,
                sap_message=result.message,
                raw_response=result.raw_response,
                is_success=result.success,
            )
            self.db.add(response)

            if result.success:
                # GA-REM-059 / R-21: identificación externa exigida por el cliente
                # (Recomendación central §19) para evitar duplicados en SAP.
                sap_payload.external_transaction_id = (
                    f"AVICOLA-{cm.event_type.upper()}-{idem_key[:16]}"
                )
                sap_payload.source_system = "APP_AVICOLA"
                sap_payload.sap_document_id = result.sap_document_id
                cm.sap_payload_id = sap_payload.id

                # ── GA-REM-010 · REGLA ABSOLUTA ──────────────────────────────
                #   NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap
                # Un adaptador manual o simulado genera un artefacto, no una
                # entrega. Los eventos permanecen en CONSOLIDATED —listos para
                # SAP— y siguen siendo corregibles, porque BR-15 no debe
                # bloquear registros que nunca llegaron a SAP.
                if adapter.delivers_to_sap and result.sap_document_id:
                    sap_payload.status = models.PayloadStatus.CONFIRMED
                    for ev_id in cm.event_ids:
                        await self.db.execute(
                            update(OperationalEvent)
                            .where(OperationalEvent.id == ev_id)
                            .values(
                                status=EventStatus.SENT_TO_SAP,
                                sap_document_ref=result.sap_document_id,
                            )
                        )
                else:
                    # Artefacto preparado, pendiente de carga y confirmación.
                    sap_payload.status = models.PayloadStatus.PREPARED
                    # Los eventos NO cambian de estado y NO reciben referencia SAP.
                success_count += 1
            else:
                sap_payload.status = models.PayloadStatus.FAILED
                sap_payload.error_message = result.message
                sap_payload.retry_count = 1
                # Exponential backoff: 1 min
                # GA-REM-010: retroceso con timedelta. La aritmética anterior
                # ((minuto + n) % 60) podía producir una fecha en el pasado.
                sap_payload.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=1)
                error_count += 1

            payloads_created += 1
            await self.db.flush()

        # Update job
        job.status = models.SyncStatus.COMPLETED if error_count == 0 else models.SyncStatus.FAILED
        job.success_count = success_count
        job.error_count = error_count
        job.completed_at = datetime.now(timezone.utc)
        await self.db.flush()

        return schemas.SapExportResponse(
            sync_job_id=job.id,
            payloads_created=payloads_created,
            status=job.status.value,
            message=f"Exportado: {success_count} éxito, {error_count} errores",
        )

    # ============================================================
    # Retry Failed Payloads
    # ============================================================

    async def retry_failed(self, payload_ids: Optional[list[int]] = None, max_retries: int = 3) -> dict:
        """Retry failed SAP payloads with exponential backoff."""
        base = select(models.SapPayload).where(
            self._company_filter(models.SapPayload.company_id),
            models.SapPayload.status == models.PayloadStatus.FAILED,
            models.SapPayload.retry_count < max_retries,
        )
        if payload_ids:
            base = base.where(models.SapPayload.id.in_(payload_ids))

        result = await self.db.execute(base)
        payloads = list(result.scalars().all())

        retried = 0
        for sp in payloads:
            # Check backoff
            if sp.next_retry_at and sp.next_retry_at > datetime.now(timezone.utc):
                continue

            adapter = self.get_adapter()
            export_payload = SapExportPayload(**sp.payload_data)

            sp.status = models.PayloadStatus.RETRYING
            sp.retry_count += 1
            await self.db.flush()

            sap_result = await adapter.export_consolidated(export_payload)
            response = models.SapResponse(
                payload_id=sp.id,
                status_code=sap_result.status_code,
                sap_document_id=sap_result.sap_document_id,
                sap_message=sap_result.message,
                raw_response=sap_result.raw_response,
                is_success=sap_result.success,
            )
            self.db.add(response)

            if sap_result.success:
                sp.status = models.PayloadStatus.CONFIRMED
                sp.sap_document_id = sap_result.sap_document_id
                # Update events
                cm = await self.db.get(models.ConsolidatedMovement, sp.consolidated_movement_id)
                if cm:
                    for ev_id in (cm.event_ids or []):
                        await self.db.execute(
                            update(OperationalEvent)
                            .where(OperationalEvent.id == ev_id)
                            .values(status=EventStatus.SAP_CONFIRMED)
                        )
            else:
                sp.status = models.PayloadStatus.FAILED
                sp.error_message = sap_result.message
                # Exponential backoff: 1min, 5min, 15min
                minutes = {1: 1, 2: 5, 3: 15}.get(sp.retry_count, 15)
                sp.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

            retried += 1
            await self.db.flush()

        return {"retried": retried, "message": f"{retried} payloads reintentados"}

    # ============================================================
    # Query
    # ============================================================

    async def list_sync_jobs(self, limit: int = 20, offset: int = 0) -> tuple[list[models.SapSyncJob], int]:
        q = select(models.SapSyncJob).where(
            self._company_filter(models.SapSyncJob.company_id)
        ).order_by(models.SapSyncJob.created_at.desc()).offset(offset).limit(limit)
        cq = select(func_count()).select_from(models.SapSyncJob).where(
            self._company_filter(models.SapSyncJob.company_id)
        )
        result = await self.db.execute(q)
        jobs = list(result.scalars().all())
        cr = await self.db.execute(cq)
        total = cr.scalar() or 0
        return jobs, total

    async def list_consolidated(
        self, lot_id: Optional[int] = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[models.ConsolidatedMovement], int]:
        base = select(models.ConsolidatedMovement).where(
            self._company_filter(models.ConsolidatedMovement.company_id)
        )
        cq = select(func_count()).select_from(models.ConsolidatedMovement).where(
            self._company_filter(models.ConsolidatedMovement.company_id)
        )
        if lot_id:
            base = base.where(models.ConsolidatedMovement.lot_id == lot_id)
            cq = cq.where(models.ConsolidatedMovement.lot_id == lot_id)
        base = base.order_by(models.ConsolidatedMovement.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(base)
        items = list(result.scalars().all())
        cr = await self.db.execute(cq)
        total = cr.scalar() or 0
        return items, total

    async def list_errors(self, limit: int = 50, offset: int = 0) -> list[schemas.SapErrorItem]:
        q = select(models.SapPayload).where(
            self._company_filter(models.SapPayload.company_id),
            models.SapPayload.status == models.PayloadStatus.FAILED,
        ).order_by(models.SapPayload.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(q)
        payloads = list(result.scalars().all())
        return [
            schemas.SapErrorItem(
                payload_id=sp.id,
                error_message=sp.error_message,
                retry_count=sp.retry_count,
                sap_document_id=sp.sap_document_id,
                created_at=sp.created_at,
            )
            for sp in payloads
        ]

    async def list_payloads(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> tuple[list[models.SapPayload], int]:
        base = select(models.SapPayload).where(self._company_filter(models.SapPayload.company_id))
        cq = select(func_count()).select_from(models.SapPayload).where(self._company_filter(models.SapPayload.company_id))
        if status:
            base = base.where(models.SapPayload.status == status)
            cq = cq.where(models.SapPayload.status == status)
        base = base.order_by(models.SapPayload.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(base)
        items = list(result.scalars().all())
        cr = await self.db.execute(cq)
        total = cr.scalar() or 0
        return items, total


def func_count():
    from sqlalchemy import func
    return func.count()
