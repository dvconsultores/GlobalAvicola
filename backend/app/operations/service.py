"""Operational events service — handles all 24 event types through unified API."""
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_event_created, audit_state_transition
from ..masters.service import MasterService
from . import models, schemas
from .validators import (
    BusinessRuleViolation,
    validate_chick_dispatch,
    validate_egg_dispatch,
    validate_event_date,
    validate_farm_house,
    validate_house_capacity,
    validate_incubation_load,
    validate_lot_active,
    validate_lot_closure,
    validate_mortality,
    validate_oc_limit,
    validate_period_open,
    validate_sap_document_unique,
    validate_sap_edit_lock,
    validate_segregation,
)


class OperationsService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    # ============================================================
    # Create Event
    # ============================================================

    async def create_event(self, data: schemas.OperationalEventCreate) -> models.OperationalEvent:
        # Validate event type
        event_type = models.EventType(data.event_type)

        # Idempotency: if client sent a key, check for duplicate submission
        if data.idempotency_key:
            existing = await self.db.execute(
                select(models.OperationalEvent).where(
                    models.OperationalEvent.idempotency_key == data.idempotency_key,
                    models.OperationalEvent.company_id == self.company_id,
                )
            )
            dup = existing.scalar_one_or_none()
            if dup:
                return dup  # Return existing event — no duplicate created

        # Business rules per event type
        await self._apply_business_rules(event_type, data)

        # Create event
        event = models.OperationalEvent(
            company_id=self.company_id,
            lot_id=data.lot_id,
            farm_id=data.farm_id,
            house_id=data.house_id,
            event_type=event_type,
            event_date=data.event_date,
            observations=data.observations,
            sap_document_ref=data.sap_document_ref,
            status=models.EventStatus.REGISTERED,
            registered_by_id=self.current_user["id"],
            idempotency_key=data.idempotency_key,
        )
        self.db.add(event)
        await self.db.flush()

        # Create sub-movements
        for bm in data.bird_movements:
            self.db.add(models.BirdMovement(event_id=event.id, **bm.model_dump()))
        for em in data.egg_movements:
            self.db.add(models.EggMovement(event_id=event.id, **em.model_dump()))
        for fm in data.feed_movements:
            self.db.add(models.FeedMovement(event_id=event.id, **fm.model_dump()))
        for hp in data.hatchery_params:
            self.db.add(models.HatcheryParams(event_id=event.id, **hp.model_dump()))
        for ins in data.inspection_details:
            self.db.add(models.InspectionDetail(event_id=event.id, **ins.model_dump()))
        for es in data.egg_storage_records:
            es_data = es.model_dump()
            es_data.setdefault("lot_id", data.lot_id)
            self.db.add(models.EggStorage(event_id=event.id, **es_data))

        await self.db.flush()
        await self.db.refresh(event)

        # Phase 3.2: auto-generate alerts for threshold violations
        await self._check_and_create_alerts(event, data)

        # Phase 5.4: auto-create generational traceability batches
        await self._auto_create_traceability_batches(event, data)

        # Audit: event created
        await audit_event_created(self.db, event, self.current_user)

        return event

    async def _auto_create_traceability_batches(
        self,
        event: models.OperationalEvent,
        data: schemas.OperationalEventCreate,
    ) -> None:
        """
        Auto-create EggBatch or ChickBatch when matching dispatch+reception events exist.
        
        EggBatch: egg_dispatch (breeder/grandparent prod → hatchery) matched with
                  egg_reception_hatchery for the same lot.
        ChickBatch: chick_dispatch (hatchery → breeder/broiler) matched with
                    bird_reception for the same lot.
        """
        from ..lots.models import EggBatch, ChickBatch
        from ..masters.models import Lot

        if event.event_type == models.EventType.EGG_DISPATCH:
            match = await self.db.execute(
                select(models.OperationalEvent).where(
                    models.OperationalEvent.lot_id == data.lot_id,
                    models.OperationalEvent.event_type == models.EventType.EGG_RECEPTION_HATCHERY,
                    models.OperationalEvent.status.not_in([models.EventStatus.CANCELLED]),
                    models.OperationalEvent.id != event.id,
                ).order_by(models.OperationalEvent.event_date.desc()).limit(1)
            )
            reception = match.scalar_one_or_none()
            if reception:
                src_lot_result = await self.db.execute(select(Lot).where(Lot.id == data.lot_id))
                src_lot = src_lot_result.scalar_one_or_none()
                generation = None
                if src_lot and src_lot.bird_type:
                    generation = src_lot.bird_type.value if hasattr(src_lot.bird_type, 'value') else str(src_lot.bird_type)
                total_qty = sum(em.quantity for em in data.egg_movements)
                batch = EggBatch(
                    source_lot_id=data.lot_id,
                    hatchery_lot_id=reception.lot_id,
                    generation=generation,
                    dispatch_event_id=event.id,
                    reception_event_id=reception.id,
                    quantity_dispatched=total_qty,
                    dispatch_date=event.event_date,
                )
                self.db.add(batch)

        elif event.event_type == models.EventType.EGG_RECEPTION_HATCHERY:
            match = await self.db.execute(
                select(models.OperationalEvent).where(
                    models.OperationalEvent.lot_id == data.lot_id,
                    models.OperationalEvent.event_type == models.EventType.EGG_DISPATCH,
                    models.OperationalEvent.status.not_in([models.EventStatus.CANCELLED]),
                    models.OperationalEvent.id != event.id,
                ).order_by(models.OperationalEvent.event_date.desc()).limit(1)
            )
            dispatch = match.scalar_one_or_none()
            if dispatch:
                batch_result = await self.db.execute(
                    select(EggBatch).where(EggBatch.dispatch_event_id == dispatch.id)
                )
                batch = batch_result.scalar_one_or_none()
                if batch:
                    total_qty = sum(em.quantity for em in data.egg_movements)
                    batch.quantity_received = total_qty
                    batch.reception_event_id = event.id
                    batch.reception_date = event.event_date

        elif event.event_type == models.EventType.CHICK_DISPATCH:
            match = await self.db.execute(
                select(models.OperationalEvent).where(
                    models.OperationalEvent.lot_id == data.lot_id,
                    models.OperationalEvent.event_type == models.EventType.BIRD_RECEPTION,
                    models.OperationalEvent.status.not_in([models.EventStatus.CANCELLED]),
                    models.OperationalEvent.id != event.id,
                ).order_by(models.OperationalEvent.event_date.desc()).limit(1)
            )
            reception = match.scalar_one_or_none()
            if reception:
                egg_batch_result = await self.db.execute(
                    select(EggBatch).where(EggBatch.hatchery_lot_id == data.lot_id)
                )
                egg_batch = egg_batch_result.scalars().first()
                total_qty = sum(bm.quantity for bm in data.bird_movements)
                batch = ChickBatch(
                    hatchery_lot_id=data.lot_id,
                    destination_lot_id=reception.lot_id,
                    broiler_lot_id=reception.lot_id,
                    dispatch_event_id=event.id,
                    reception_event_id=reception.id,
                    egg_batch_id=egg_batch.id if egg_batch else None,
                    quantity_dispatched=total_qty,
                    dispatch_date=event.event_date,
                )
                self.db.add(batch)

        elif event.event_type == models.EventType.BIRD_RECEPTION:
            match = await self.db.execute(
                select(models.OperationalEvent).where(
                    models.OperationalEvent.lot_id == data.lot_id,
                    models.OperationalEvent.event_type == models.EventType.CHICK_DISPATCH,
                    models.OperationalEvent.status.not_in([models.EventStatus.CANCELLED]),
                    models.OperationalEvent.id != event.id,
                ).order_by(models.OperationalEvent.event_date.desc()).limit(1)
            )
            dispatch = match.scalar_one_or_none()
            if dispatch:
                batch_result = await self.db.execute(
                    select(ChickBatch).where(ChickBatch.dispatch_event_id == dispatch.id)
                )
                batch = batch_result.scalar_one_or_none()
                if batch:
                    total_qty = sum(bm.quantity for bm in data.bird_movements)
                    batch.quantity_received = total_qty
                    batch.reception_event_id = event.id
                    batch.reception_date = event.event_date

    async def _check_and_create_alerts(
        self,
        event: models.OperationalEvent,
        data: schemas.OperationalEventCreate,
    ) -> None:
        """Auto-generate OperationalAlerts when operational thresholds are exceeded."""
        alerts: list[models.OperationalAlert] = []

        # Alert 1: High mortality (>= 3% of current bird balance triggers warning; >= 8% critical)
        if event.event_type == models.EventType.MORTALITY_RECORDING:
            total_mortality = sum(bm.quantity for bm in data.bird_movements)
            if total_mortality > 0:
                balance = await get_current_bird_balance(self.db, event.lot_id, self.company_id)
                # balance already includes this event's mortality (flushed above),
                # so add it back to get the pre-event balance
                pre_balance = balance + total_mortality
                if pre_balance > 0:
                    pct = total_mortality / pre_balance * 100
                    if pct >= 3.0:
                        severity = "critical" if pct >= 8.0 else "warning"
                        alerts.append(models.OperationalAlert(
                            company_id=event.company_id,
                            lot_id=event.lot_id,
                            event_id=event.id,
                            alert_type="high_mortality",
                            severity=severity,
                            message=(
                                f"Mortalidad del {pct:.1f}% del saldo "
                                f"({total_mortality} aves). "
                                f"Umbral: 3% advertencia / 8% crítico."
                            ),
                            threshold_value=3.0,
                            actual_value=round(pct, 2),
                        ))

        # Alert 2: Temperature / humidity extremes during farm inspection
        if event.event_type == models.EventType.FARM_INSPECTION:
            TEMP_MIN, TEMP_MAX = 18.0, 35.0
            HUMI_MIN, HUMI_MAX = 40.0, 90.0
            for ins in data.inspection_details:
                ins_data = ins.model_dump()
                temp = ins_data.get("temperature")
                humi = ins_data.get("humidity")
                house = ins_data.get("house_id", "?")
                if temp is not None and (temp < TEMP_MIN or temp > TEMP_MAX):
                    alerts.append(models.OperationalAlert(
                        company_id=event.company_id,
                        lot_id=event.lot_id,
                        event_id=event.id,
                        alert_type="temperature_out_of_range",
                        severity="warning",
                        message=(
                            f"Temperatura {temp}°C fuera del rango "
                            f"[{TEMP_MIN}–{TEMP_MAX}°C] en galpón {house}."
                        ),
                        threshold_value=TEMP_MAX,
                        actual_value=temp,
                    ))
                if humi is not None and (humi < HUMI_MIN or humi > HUMI_MAX):
                    alerts.append(models.OperationalAlert(
                        company_id=event.company_id,
                        lot_id=event.lot_id,
                        event_id=event.id,
                        alert_type="humidity_out_of_range",
                        severity="warning",
                        message=(
                            f"Humedad {humi}% fuera del rango "
                            f"[{HUMI_MIN}–{HUMI_MAX}%] en galpón {house}."
                        ),
                        threshold_value=HUMI_MAX,
                        actual_value=humi,
                    ))

        if alerts:
            self.db.add_all(alerts)
            await self.db.flush()

    async def _apply_business_rules(self, event_type: models.EventType, data: schemas.OperationalEventCreate):
        """Apply business rules based on event type."""
        # BR-07: Lot must be active
        await validate_lot_active(self.db, data.lot_id)
        # BR-06: Event date cannot be before lot activation date
        await validate_event_date(self.db, data.lot_id, data.event_date)
        # BR-08: Movements require farm/house when applicable
        await validate_farm_house(data.event_type.value if hasattr(data.event_type, 'value') else str(data.event_type), data.farm_id, data.house_id)
        # BR-19: Date not in closed period
        await validate_period_open(self.db, data.event_date)
        # BR-10: SAP document must not be duplicated
        if data.sap_document_ref:
            await validate_sap_document_unique(self.db, data.lot_id, event_type, data.sap_document_ref)

        total_qty = sum(bm.quantity for bm in data.bird_movements) + sum(em.quantity for em in data.egg_movements)

        # G-R04: Validate house capacity for reception/distribution events
        if event_type in (models.EventType.BIRD_RECEPTION, models.EventType.BIRD_DISTRIBUTION):
            if data.house_id and total_qty > 0:
                await validate_house_capacity(self.db, data.house_id, total_qty)
            # G-R05: Validate quantity ≤ OC
            await validate_oc_limit(self.db, data.sap_document_ref, total_qty)

        try:
            if event_type == models.EventType.MORTALITY_RECORDING:
                if total_qty > 0:
                    await validate_mortality(self.db, data.lot_id, total_qty)
            elif event_type == models.EventType.EGG_DISPATCH:
                total = sum(em.quantity for em in data.egg_movements)
                if total > 0:
                    await validate_egg_dispatch(self.db, data.lot_id, total)
            elif event_type == models.EventType.INCUBATION_LOAD:
                total = sum(hp.quantity_loaded or 0 for hp in data.hatchery_params)
                if total > 0:
                    await validate_incubation_load(self.db, data.lot_id, total)
            elif event_type == models.EventType.CHICK_DISPATCH:
                if total_qty > 0:
                    await validate_chick_dispatch(self.db, data.lot_id, total_qty)
            elif event_type == models.EventType.LOT_CLOSURE:
                await validate_lot_closure(self.db, data.lot_id)
        except BusinessRuleViolation as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    # ============================================================
    # Query Events
    # ============================================================

    async def get_alerts(
        self,
        lot_id: Optional[int] = None,
        is_resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[models.OperationalAlert]:
        query = select(models.OperationalAlert)
        if not self.current_user.get("is_super_admin") and self.company_id:
            query = query.where(models.OperationalAlert.company_id == self.company_id)
        if lot_id is not None:
            query = query.where(models.OperationalAlert.lot_id == lot_id)
        if is_resolved is not None:
            query = query.where(models.OperationalAlert.is_resolved == is_resolved)
        query = query.order_by(models.OperationalAlert.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def resolve_alert(self, alert_id: int) -> models.OperationalAlert:
        from datetime import datetime, timezone
        result = await self.db.execute(
            select(models.OperationalAlert).where(
                models.OperationalAlert.id == alert_id,
                models.OperationalAlert.company_id == self.company_id,
            )
        )
        alert = result.scalar_one_or_none()
        if alert is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        alert.is_resolved = True
        alert.resolved_by_id = self.current_user.get("id")
        alert.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def get_events(
        self,
        skip: int = 0,
        limit: int = 20,
        lot_id: Optional[int] = None,
        farm_id: Optional[int] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> tuple[list[models.OperationalEvent], int]:
        query = select(models.OperationalEvent)

        # Company isolation
        if not self.current_user.get("is_super_admin") and self.company_id:
            query = query.where(models.OperationalEvent.company_id == self.company_id)

        if lot_id:
            query = query.where(models.OperationalEvent.lot_id == lot_id)
        if farm_id:
            query = query.where(models.OperationalEvent.farm_id == farm_id)
        if event_type:
            query = query.where(models.OperationalEvent.event_type == event_type)
        if status:
            query = query.where(models.OperationalEvent.status == status)
        if date_from:
            query = query.where(models.OperationalEvent.event_date >= date_from)
        if date_to:
            query = query.where(models.OperationalEvent.event_date <= date_to)

        # Count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Order and paginate
        query = query.order_by(models.OperationalEvent.event_date.desc(), models.OperationalEvent.id.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_event(self, event_id: int) -> models.OperationalEvent:
        query = select(models.OperationalEvent).where(
            models.OperationalEvent.id == event_id,
            models.OperationalEvent.company_id == self.company_id,
        )
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
        return event

    # ============================================================
    # Update & State Transitions
    # ============================================================

    async def update_event(self, event_id: int, data: schemas.OperationalEventUpdate) -> models.OperationalEvent:
        event = await self.get_event(event_id)
        old_status = event.status.value if hasattr(event.status, 'value') else str(event.status)
        # BR-15: Records sent to SAP cannot be edited
        validate_sap_edit_lock(event.status.value)
        if event.status not in [models.EventStatus.DRAFT, models.EventStatus.REGISTERED, models.EventStatus.RETURNED]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden editar eventos en borrador, registrados o devueltos")
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(event, key, val)
        event.version += 1
        await self.db.flush()
        await self.db.refresh(event)
        # Audit
        await audit_state_transition(self.db, event, self.current_user, old_status, old_status, comments="Evento actualizado")
        return event

    async def submit_to_review(self, event_id: int) -> models.OperationalEvent:
        event = await self.get_event(event_id)
        if event.status != models.EventStatus.REGISTERED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo eventos registrados pueden enviarse a revisión")
        old_status = event.status.value if hasattr(event.status, 'value') else str(event.status)
        event.status = models.EventStatus.PENDING_REVIEW
        await self.db.flush()
        await self.db.refresh(event)
        # Audit: submitted to review
        new_status = event.status.value if hasattr(event.status, 'value') else str(event.status)
        await audit_state_transition(self.db, event, self.current_user, old_status, new_status, comments="Enviado a revisión")
        return event

    async def cancel_event(self, event_id: int) -> models.OperationalEvent:
        event = await self.get_event(event_id)
        if event.status in [models.EventStatus.APPROVED, models.EventStatus.CONSOLIDATED, models.EventStatus.SENT_TO_SAP]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede cancelar un evento ya aprobado o enviado a SAP")
        old_status = event.status.value if hasattr(event.status, 'value') else str(event.status)
        event.status = models.EventStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(event)
        # Audit: cancelled
        new_status = event.status.value if hasattr(event.status, 'value') else str(event.status)
        await audit_state_transition(self.db, event, self.current_user, old_status, new_status, comments="Evento cancelado")
        return event

    # ============================================================
    # Evidence / Attachments
    # ============================================================

    async def get_evidences(self, event_id: int) -> list[models.Evidence]:
        event = await self.get_event(event_id)
        if not self.current_user.get("is_super_admin") and event.company_id != self.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
        return list(event.evidences)

    async def create_evidence(
        self, event_id: int, file_name: str, file_path: str,
        file_size: int, mime_type: str, evidence_type: str, description: str | None,
    ) -> models.Evidence:
        event = await self.get_event(event_id)
        if not self.current_user.get("is_super_admin") and event.company_id != self.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
        evidence = models.Evidence(
            event_id=event_id,
            company_id=event.company_id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            evidence_type=evidence_type,
            description=description,
            uploaded_by_id=self.current_user["id"],
        )
        self.db.add(evidence)
        await self.db.commit()
        await self.db.refresh(evidence)
        return evidence

    async def delete_evidence(self, event_id: int, evidence_id: int) -> None:
        import os
        result = await self.db.execute(
            select(models.Evidence).where(
                models.Evidence.id == evidence_id,
                models.Evidence.event_id == event_id,
            )
        )
        evidence = result.scalar_one_or_none()
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")
        if not self.current_user.get("is_super_admin") and evidence.company_id != self.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
        try:
            os.remove(evidence.file_path)
        except OSError:
            pass
        await self.db.delete(evidence)
        await self.db.commit()

    async def get_evidence_for_download(self, event_id: int, evidence_id: int) -> models.Evidence:
        result = await self.db.execute(
            select(models.Evidence).where(
                models.Evidence.id == evidence_id,
                models.Evidence.event_id == event_id,
            )
        )
        evidence = result.scalar_one_or_none()
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidencia no encontrada")
        if not self.current_user.get("is_super_admin") and evidence.company_id != self.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
        return evidence

    # ============================================================
    # Event Types Reference
    # ============================================================

    def get_event_types(self) -> list[dict]:
        return schemas.ALL_EVENT_TYPES
