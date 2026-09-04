"""Operational events service — handles all 25 event types through unified API."""
import logging
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException
from fastapi import status
from fastapi import status as status_mod
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_event_created, audit_state_transition
from ..config import settings
from ..masters.service import MasterService

logger = logging.getLogger(__name__)

# Umbrales de la alerta de mortalidad, en porcentaje del saldo de aves previo al evento.
#
# `docs/02-functional-spec.md:516` exige que el umbral sea **configurable**; estaba fijo en
# el código y la auditoría lo registró como hueco (`audit/06:259`). Se lee de la
# configuración de la aplicación, el mismo mecanismo que gobierna el resto de parámetros
# del sistema. La configurabilidad **por empresa** es otra cosa, que ninguna fuente pide:
# vive como mejora opcional en `GA-REM-019`.
MORTALITY_WARNING_PCT = settings.MORTALITY_ALERT_WARNING_PCT
MORTALITY_CRITICAL_PCT = settings.MORTALITY_ALERT_CRITICAL_PCT
from . import models, schemas
from .validators import (
    BusinessRuleViolation,
    get_current_bird_balance,
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


LOT_OPTIONAL_EVENTS = {
    models.EventType.FARM_INSPECTION,
    models.EventType.HATCHERY_INSPECTION,
}


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

        # Create event.
        #
        # Los campos del evento se derivan del propio contrato de entrada en lugar de
        # enumerarse a mano. La lista escrita a mano que había aquí cubría 11 de los 22
        # campos declarados: los otros 14 —entre ellos `cause_id`, la causa de la
        # mortalidad— se aceptaban, se devolvían como `null` y nunca se guardaban (P0-14).
        # El defecto no era que faltaran 14 asignaciones, sino que fuera posible que
        # faltaran: cualquier campo añadido después se habría perdido igual y en silencio.
        event_fields = data.model_dump(exclude=set(schemas.SUBMOVEMENT_FIELDS))
        event_fields["event_type"] = event_type  # el enum ya validado, no la cadena
        event = models.OperationalEvent(
            **event_fields,
            company_id=self.company_id,
            status=models.EventStatus.REGISTERED,
            registered_by_id=self.current_user["id"],
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

        # Phase 3.2: auto-generate alerts for threshold violations.
        #
        # Las alertas son un artefacto derivado: perder una alerta es molesto, perder el
        # registro operativo que la originó es inadmisible. Un fallo aquí no puede
        # arrastrar la operación. Se registra en el log —nunca en silencio— para que el
        # defecto siga siendo visible: fue exactamente esta ruta la que ocultó `P0-1`
        # durante meses detrás de un 500.
        try:
            await self._check_and_create_alerts(event, data)
        except Exception:  # noqa: BLE001 - deliberado y acotado a la generación de alertas
            logger.exception(
                "Fallo al generar alertas para el evento %s (%s); el evento se conserva",
                event.id, event.event_type,
            )

        # Phase 5.4: auto-create generational traceability batches
        await self._auto_create_traceability_batches(event, data)

        # Audit: event created
        await audit_event_created(self.db, event, self.current_user)

        return event

    async def _despacho_dirigido_a_este_lote(self, recepcion_evento, tipo_despacho):
        """Busca el despacho cuyo destino declarado es la granja de este lote.

        Contrapartida de `_recepcion_en_el_destino_declarado`: cuando la recepcion llega
        despues del despacho, es ella quien tiene que encontrarlo. El criterio es el
        mismo —el destino que el operador declaro— y por eso ambas direcciones producen
        el mismo vinculo.
        """
        from ..masters.models import Lot

        lote = (await self.db.execute(
            select(Lot).where(Lot.id == recepcion_evento.lot_id))).scalar_one_or_none()
        if lote is None or lote.farm_id is None:
            return None

        consulta = (
            select(models.OperationalEvent)
            .where(
                models.OperationalEvent.event_type == tipo_despacho,
                models.OperationalEvent.company_id == self.company_id,
                models.OperationalEvent.status.not_in([models.EventStatus.CANCELLED]),
                models.OperationalEvent.id != recepcion_evento.id,
                models.OperationalEvent.lot_id != recepcion_evento.lot_id,
                models.OperationalEvent.destination_farm_id == lote.farm_id,
            )
            .order_by(models.OperationalEvent.event_date.desc())
            .limit(1)
        )
        return (await self.db.execute(consulta)).scalar_one_or_none()

    async def _recepcion_en_el_destino_declarado(
        self,
        despacho_evento,
        datos,
        tipo_recepcion,
    ):
        """Busca la recepcion que corresponde a un despacho, por el destino declarado.

        `RC-04` — resuelto por evidencia. La spec dice que el vinculo se crea «para el
        mismo lote de huevos», y la implementacion lo leyo como «el mismo `lot_id`». Es
        estructuralmente imposible: el despacho se registra en el lote origen y la
        recepcion en el lote destino, y `EggBatch` tiene por eso **dos** columnas de lote
        (`source_lot_id`, `hatchery_lot_id`). «El mismo lote de huevos» designa el mismo
        lote fisico de huevos viajando de uno a otro, no un identificador compartido. Con
        el filtro anterior no se creaba **ningun** vinculo, y de coincidir habria creado un
        lote enlazado consigo mismo.

        El emparejamiento usa la unica señal inequivoca disponible: **el destino que el
        operador declaro** (`destination_farm_id` / `destination_plant_id`), que solo es
        utilizable desde que `P0-14` lo persiste. Si el despacho no declara destino no se
        crea vinculo automatico: la spec §4.9 ya contempla el enlace manual para cuando la
        correspondencia automatica no es posible, y adivinarla seria peor que no hacerla.
        """
        from ..masters.models import Lot

        destino_granja = getattr(despacho_evento, "destination_farm_id", None)
        if destino_granja is None:
            return None

        consulta = (
            select(models.OperationalEvent)
            .join(Lot, Lot.id == models.OperationalEvent.lot_id)
            .where(
                models.OperationalEvent.event_type == tipo_recepcion,
                models.OperationalEvent.company_id == self.company_id,
                models.OperationalEvent.status.not_in([models.EventStatus.CANCELLED]),
                models.OperationalEvent.id != despacho_evento.id,
                # Lotes distintos: un lote no se despacha a si mismo.
                models.OperationalEvent.lot_id != despacho_evento.lot_id,
                Lot.farm_id == destino_granja,
            )
            .order_by(models.OperationalEvent.event_date.desc())
            .limit(1)
        )
        return (await self.db.execute(consulta)).scalar_one_or_none()

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
        if data.lot_id is None:
            return

        from ..lots.models import EggBatch, ChickBatch
        from ..masters.models import Lot

        if event.event_type == models.EventType.EGG_DISPATCH:
            reception = await self._recepcion_en_el_destino_declarado(
                event, data, models.EventType.EGG_RECEPTION_HATCHERY)
            if reception and reception.lot_id != data.lot_id:
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
            dispatch = await self._despacho_dirigido_a_este_lote(
                event, models.EventType.EGG_DISPATCH)
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
            reception = await self._recepcion_en_el_destino_declarado(
                event, data, models.EventType.BIRD_RECEPTION)
            if reception and reception.lot_id != data.lot_id:
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
            dispatch = await self._despacho_dirigido_a_este_lote(
                event, models.EventType.CHICK_DISPATCH)
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
        if event.event_type == models.EventType.MORTALITY_RECORDING and event.lot_id is not None:
            total_mortality = sum(bm.quantity for bm in data.bird_movements)
            if total_mortality > 0:
                # P0-1: la función no estaba importada y se la llamaba con tres
                # argumentos cuando acepta dos (`validators.py:21`). Ninguna mortalidad
                # válida podía registrarse: el `NameError` salía como 500 después de
                # haber persistido el evento.
                balance = await get_current_bird_balance(self.db, event.lot_id)
                # balance already includes this event's mortality (flushed above),
                # so add it back to get the pre-event balance
                pre_balance = balance + total_mortality
                if pre_balance > 0:
                    pct = total_mortality / pre_balance * 100
                    if pct >= MORTALITY_WARNING_PCT:
                        severity = ("critical" if pct >= MORTALITY_CRITICAL_PCT
                                    else "warning")
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
                            threshold_value=MORTALITY_WARNING_PCT,
                            actual_value=round(pct, 2),
                        ))

        # Alert 2: Temperature / humidity extremes during farm inspection
        if event.event_type == models.EventType.FARM_INSPECTION and event.lot_id is not None:
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
        lot_required = event_type not in LOT_OPTIONAL_EVENTS
        if lot_required and data.lot_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El evento requiere lote")

        # BR-07 / BR-06: Validate lot status/date when event is lot-scoped.
        if data.lot_id is not None:
            # R-42: el lote debe ser de quien registra. Sin este filtro, la empresa A
            # podía escribir operaciones contra lotes de la empresa B.
            await validate_lot_active(self.db, data.lot_id, self.company_id)
            await validate_event_date(self.db, data.lot_id, data.event_date)
        # GA-REM-002 AC10: las referencias de ubicación deben pertenecer a la compañía.
        # `R-42` cubrió `lot_id`; el gate de la Wave 3 encontró que `farm_id` y `house_id`
        # seguían aceptando recursos de otra empresa.
        from ..tenancy import verificar_ubicacion

        await verificar_ubicacion(
            self.db, self.company_id,
            farm_id=data.farm_id, house_id=data.house_id,
            destination_farm_id=data.destination_farm_id,
        )
        # BR-08: Movements require farm/house when applicable
        await validate_farm_house(data.event_type.value if hasattr(data.event_type, 'value') else str(data.event_type), data.farm_id, data.house_id)
        # BR-19: Date not in closed period
        await validate_period_open(self.db, data.event_date)
        # BR-10: SAP document must not be duplicated
        if data.sap_document_ref and data.lot_id is not None:
            await validate_sap_document_unique(self.db, data.lot_id, event_type, data.sap_document_ref)

        total_qty = sum(bm.quantity for bm in data.bird_movements) + sum(em.quantity for em in data.egg_movements)

        # G-R04: Validate house capacity for reception/distribution events
        if event_type in (models.EventType.BIRD_RECEPTION, models.EventType.BIRD_DISTRIBUTION):
            if data.house_id and total_qty > 0:
                await validate_house_capacity(self.db, data.house_id, total_qty)
            # G-R05: Validate quantity ≤ OC
            await validate_oc_limit(self.db, data.sap_document_ref, total_qty)

        # Reglas por tipo de evento. No hay `try/except` local: el manejador tipado de
        # `BusinessRuleViolation` registrado en `app/main.py` da un único contrato de
        # error a las 23 reglas. El bloque que había aquí solo cubría estas cinco, y era
        # justamente por eso que las otras ocho salían como 500 (R-26).
        if event_type == models.EventType.MORTALITY_RECORDING:
            # Sin la guarda `total_qty > 0`: `validate_mortality` es precisamente quien
            # rechaza el cero y los negativos (`BR-01`), y saltársela dejaba pasar un
            # registro de mortalidad de cero aves —un dato sin significado que además
            # contamina los indicadores— con un 201.
            if data.lot_id is None:
                raise BusinessRuleViolation("El evento requiere lote", "BR-07")
            await validate_mortality(self.db, data.lot_id, total_qty)
        elif event_type == models.EventType.EGG_DISPATCH:
            total = sum(em.quantity for em in data.egg_movements)
            if total > 0:
                if data.lot_id is None:
                    raise BusinessRuleViolation("El evento requiere lote", "BR-07")
                await validate_egg_dispatch(self.db, data.lot_id, total)
        elif event_type == models.EventType.INCUBATION_LOAD:
            total = sum(hp.quantity_loaded or 0 for hp in data.hatchery_params)
            if total > 0:
                if data.lot_id is None:
                    raise BusinessRuleViolation("El evento requiere lote", "BR-07")
                await validate_incubation_load(self.db, data.lot_id, total)
        elif event_type == models.EventType.CHICK_DISPATCH:
            if total_qty > 0:
                if data.lot_id is None:
                    raise BusinessRuleViolation("El evento requiere lote", "BR-07")
                await validate_chick_dispatch(self.db, data.lot_id, total_qty)
        elif event_type == models.EventType.LOT_CLOSURE:
            if data.lot_id is None:
                raise BusinessRuleViolation("El evento requiere lote", "BR-07")
            await validate_lot_closure(self.db, data.lot_id)

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
        # R-36, mismo patrón fail-open que en `get_events`.
        if not self.current_user.get("is_super_admin"):
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
        registered_by_me: bool = False,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> tuple[list[models.OperationalEvent], int]:
        query = select(models.OperationalEvent)

        # Company isolation
        # R-36: el filtro era `and self.company_id`, de modo que un usuario **sin**
        # compañía no recibía filtro alguno y veía los eventos de todas. Fail-open sobre
        # el aislamiento multiempresa. Ahora la ausencia de compañía no da acceso
        # universal: da acceso a nada.
        if not self.current_user.get("is_super_admin"):
            query = query.where(models.OperationalEvent.company_id == self.company_id)

        if lot_id:
            query = query.where(models.OperationalEvent.lot_id == lot_id)
        if farm_id:
            query = query.where(models.OperationalEvent.farm_id == farm_id)
        if event_type:
            query = query.where(models.OperationalEvent.event_type == event_type)
        if status:
            # GA-REM-011 C-09: se admite una lista de estados separada por coma.
            # Antes, un valor como "draft,registered" no era un miembro válido
            # del enum y la consulta fallaba con HTTP 500.
            raw = [s.strip() for s in str(status).split(",") if s.strip()]
            valid = {e.value for e in models.EventStatus}
            unknown = [s for s in raw if s not in valid]
            if unknown:
                raise HTTPException(
                    status_code=status_mod.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Estado no válido: {', '.join(unknown)}. "
                        f"Válidos: {', '.join(sorted(valid))}."
                    ),
                )
            if len(raw) == 1:
                query = query.where(models.OperationalEvent.status == raw[0])
            elif raw:
                query = query.where(models.OperationalEvent.status.in_(raw))
        if registered_by_me:
            # GA-REM-011 C-08: "Mis Pendientes" debe mostrar solo lo propio.
            query = query.where(
                models.OperationalEvent.registered_by_id == self.current_user["id"]
            )
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
        # `exclude_unset` es lo que hace que una edición parcial no borre lo que no
        # menciona. El esquema ya excluye `status`, `event_type` e `idempotency_key`, de
        # modo que aquí no puede llegar ninguno: el estado solo cambia por las
        # transiciones del flujo (R-32).
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
