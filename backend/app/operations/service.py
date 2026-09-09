"""Operational events service — handles all 25 event types through unified API."""
import logging
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException
from fastapi import status
from fastapi import status as status_mod
from sqlalchemy import func, select
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
    validate_bird_decrement,
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

# `GA-REM-006-A` §A.2 · mapa de transiciones de `P-07` (`R-135`, `R-140` PARTE A, `R-154`):
# estados **desde** los que cada acto es válido. `OD-17.a`: `RETURNED` y `REJECTED` son
# devoluciones internas, vivas; `CANCELLED` y el ciclo SAP son terminales o diferidos.
EDITABLES = (models.EventStatus.DRAFT, models.EventStatus.REGISTERED,
             models.EventStatus.RETURNED, models.EventStatus.REJECTED)
REENVIABLES = (models.EventStatus.REGISTERED, models.EventStatus.RETURNED, models.EventStatus.REJECTED)
NO_CANCELABLES = (models.EventStatus.APPROVED, models.EventStatus.CONSOLIDATED, models.EventStatus.SENT_TO_SAP,
                  models.EventStatus.SAP_CONFIRMED, models.EventStatus.SAP_ERROR, models.EventStatus.CANCELLED,
                  models.EventStatus.REVERSED)  # `OD-19`: lo revertido es terminal


class OperationsService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")
        self._unidades_cache = None

    def _acotar_a_empresa(self, query, columna):
        """`OD-14.c/d` en una sola línea: con empresa efectiva, sus filas; sin ella, ninguna.

        `sa_false()` y no `columna == None`: la segunda también cierra —`IS NULL` sobre una
        columna no nula— pero solo por accidente del esquema (`R-116`, lección `M6`).
        """
        from sqlalchemy import false as sa_false
        if self.company_id is None:
            return query.where(sa_false())
        return query.where(columna == self.company_id)

    async def _unidades(self) -> list[str]:
        """Las cadenas efectivas de quien pregunta. Una vez por servicio."""
        if self._unidades_cache is None:
            from ..business_units.service import unidades_efectivas_por_id

            self._unidades_cache = await unidades_efectivas_por_id(
                self.db, user_id=self.current_user.get("id"), company_id=self.company_id
            )
        return self._unidades_cache

    # ============================================================
    # `GA-REM-040` enmienda G · `R-160` / `R-159` · la unidad se exige al operar
    # ============================================================

    async def _unidad_del_lote(self, lot_id: int) -> str | None:
        """La unidad canónica de un lote de la empresa efectiva: `lot.bird_type` → código.

        Un lote ajeno —o cualquiera sin empresa efectiva, `OD-14.d`— **no existe** para quien
        pregunta (`BR-07`, la misma respuesta que `validate_lot_active`): distinguir «no es
        tuyo» de «no está» ya enumera. `None` es un lote sin cadena declarada: pendiente
        (`OD-10.c`), no una quinta unidad.
        """
        from ..masters.models import Lot

        consulta = select(Lot.bird_type).where(Lot.id == lot_id)
        consulta = self._acotar_a_empresa(consulta, Lot.company_id)
        fila = (await self.db.execute(consulta)).one_or_none()
        if fila is None:
            raise BusinessRuleViolation("Lote no encontrado", "BR-07")
        tipo = fila[0]
        return tipo.value if tipo is not None else None

    async def _unidad_clasificada(self, company_business_unit_id: int) -> str | None:
        """El código de la habilitación que el plano de control fijó en el evento (fase 6)."""
        from ..business_units.models import BusinessUnit, CompanyBusinessUnit

        return (await self.db.execute(
            select(BusinessUnit.code)
            .join(CompanyBusinessUnit, CompanyBusinessUnit.business_unit_id == BusinessUnit.id)
            .where(CompanyBusinessUnit.id == company_business_unit_id,
                   CompanyBusinessUnit.company_id == self.company_id)
        )).scalar_one_or_none()

    async def exigir_unidad_operativa(self, *, lot_id: int | None = None, event=None) -> None:
        """La guarda de escritura. `GA-REM-040-G §G.3` · `AC-C05` · `AC-W02…W05, W13, W14`.

        La unidad se **deriva en el servidor** —del lote destino, o de la clasificación que el
        plano de control fijó en el evento— y nunca del cuerpo de la petición, que no la
        declara. Con eso resuelto:

            actor de empresa      la unidad está en su alcance efectivo (habilitada ∧ concedida),
                                  o el lote no existe para él (`BR-07`, anti-enumeración)
            dato pendiente        sin unidad derivable; se exige al menos una unidad efectiva
                                  (`OD-09.c`: cero unidades → ningún dato productivo)
            autoridad global      situada (`OD-14.d`) y sobre una unidad **habilitada** para esa
                                  empresa (`AC-A05`, `OD-16.e`: apagada = operativamente
                                  inaccesible, también para ella); la concesión no se le exige,
                                  como en la fase 3 (`R-139 §6`): su autoridad es la capacidad
                                  comodín, no una fila de `user_business_units`

        Sin lógica por nombre de rol: `is_super_admin` es la capacidad `("*", …, "all")`
        resuelta en la sesión, no una cadena. Todo ocurre antes de `db.add`: una denegación
        no deja fila, ni movimiento, ni auditoría (`AC-W11`).
        """
        if event is not None:
            if event.lot_id is not None:
                unidad = await self._unidad_del_lote(event.lot_id)
            elif event.business_unit_id is not None:
                unidad = await self._unidad_clasificada(event.business_unit_id)
            else:
                unidad = None
        elif lot_id is not None:
            unidad = await self._unidad_del_lote(lot_id)
        else:
            unidad = None

        # `GA-REM-040-H §H.5`: la decisión vive en un solo sitio, compartido con `lots`. Aquí
        # solo se deriva la unidad (arriba) y se traduce el motivo al contrato de esta
        # superficie: lo no concedido se comporta como lote inexistente (anti-enumeración,
        # `BR-07`); lo demás es `403`.
        from ..business_units.service import (AccesoDeUnidadDenegado,
                                              exigir_unidad_operativa as _guarda)

        try:
            await _guarda(self.db, current_user=self.current_user, company_id=self.company_id,
                          unidad=unidad, efectivas=await self._unidades())
        except AccesoDeUnidadDenegado as exc:
            if exc.motivo == "no_concedida":
                raise BusinessRuleViolation("Lote no encontrado", "BR-07") from exc
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

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

        # `GA-REM-040-G` · `R-160`: empresa y unidad del lote destino, antes de las reglas y
        # de cualquier `db.add`. El cuerpo no declara la unidad; se deriva del lote.
        await self.exigir_unidad_operativa(lot_id=data.lot_id)

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

    async def _cantidad_movida(self, event_id: int, modelo, campo: str = "quantity") -> int:
        """Suma los movimientos de un evento ya persistido.

        `GA-REM-031`. La rama del despacho conoce las cantidades porque tiene la carga de
        la petición delante; la de la recepción solo tiene la fila del despacho, así que
        las lee de sus movimientos. Es la única diferencia real de información entre las
        dos, y por eso vive aquí y no duplicada.
        """
        resultado = await self.db.execute(
            select(func.coalesce(func.sum(getattr(modelo, campo)), 0))
            .where(modelo.event_id == event_id)
        )
        return int(resultado.scalar() or 0)

    async def _generacion_del_lote(self, lot_id: int) -> str | None:
        from ..masters.models import Lot

        lote = (await self.db.execute(select(Lot).where(Lot.id == lot_id))).scalar_one_or_none()
        if lote is None or not lote.bird_type:
            return None
        return lote.bird_type.value if hasattr(lote.bird_type, "value") else str(lote.bird_type)

    async def _vincular_generaciones(
        self, modelo, despacho, recepcion, cantidad_despachada: int, **campos,
    ):
        """Crea el vínculo generacional de un par despacho/recepción.

        `GA-REM-031`. Un solo sitio para el mapeo de campos, invocado desde las dos ramas.
        Tenerlo duplicado era el riesgo real de extender la creación a la recepción: dos
        implementaciones del mismo vínculo divergen a la primera corrección que solo se
        aplique a una.

        `dispatch_event_id` es la clave del par, y por eso quien llama comprueba antes si
        el vínculo ya existe: **exactamente uno** por envío, cree quien cree.
        """
        vinculo = modelo(
            dispatch_event_id=despacho.id,
            reception_event_id=recepcion.id,
            quantity_dispatched=cantidad_despachada,
            dispatch_date=despacho.event_date,
            **campos,
        )
        self.db.add(vinculo)
        return vinculo

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
                # `R-78`. Antes esta rama **solo actualizaba**: si el vínculo no existía se
                # ignoraba en silencio. Como la creación vivía únicamente en la rama del
                # despacho —que busca una recepción ya registrada—, en el orden natural de
                # la operación, que despacha antes de recibir, no se creaba ninguno nunca.
                # `spec.md §4.9` no impone orden: la conjunción es simétrica.
                if batch is None:
                    batch = await self._vincular_generaciones(
                        EggBatch, dispatch, event,
                        await self._cantidad_movida(dispatch.id, models.EggMovement),
                        source_lot_id=dispatch.lot_id,
                        hatchery_lot_id=event.lot_id,
                        generation=await self._generacion_del_lote(dispatch.lot_id),
                    )
                batch.quantity_received = sum(em.quantity for em in data.egg_movements)
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
                if batch is None:                                          # `R-78`
                    egg_batch = (await self.db.execute(
                        select(EggBatch).where(EggBatch.hatchery_lot_id == dispatch.lot_id)
                    )).scalars().first()
                    batch = await self._vincular_generaciones(
                        ChickBatch, dispatch, event,
                        await self._cantidad_movida(dispatch.id, models.BirdMovement),
                        hatchery_lot_id=dispatch.lot_id,
                        destination_lot_id=event.lot_id,
                        broiler_lot_id=event.lot_id,
                        egg_batch_id=egg_batch.id if egg_batch else None,
                    )
                batch.quantity_received = sum(bm.quantity for bm in data.bird_movements)
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

        # Alerta 3: peso fuera de la curva estándar de la línea genética.
        # `GA-REM-037` / `OD-06`, que resuelve de dónde sale el rango: la tabla del
        # proveedor que el administrador cargó, en la versión que este lote tiene fijada.
        # `docs/03 spec.md §4.5` pedía esta alerta desde el principio; lo que faltaba no
        # era el aviso sino la referencia contra la que emitirlo.
        if event.event_type == models.EventType.WEIGHT_RECORDING and event.lot_id is not None:
            alerts.extend(await self._alertas_de_peso(event, data))

        if alerts:
            self.db.add_all(alerts)
            await self.db.flush()
            await self._notificar_alertas(event, alerts)

    #: Las dos alertas que `docs/02 §3.14` enumera como tipos de notificación. Las otras
    #: —temperatura y humedad fuera de rango— **no figuran ahí**, de modo que siguen siendo
    #: alertas del lote y nada más: convertirlas sería inventar requisito.
    ALERTAS_NOTIFICABLES = {
        "high_mortality": "mortality_over_threshold",     # «Mortalidad > umbral configurable»
        "weight_deviation": "weight_out_of_standard",     # «Peso fuera de estándar»
    }

    async def _notificar_alertas(self, event, alerts) -> None:
        """Convierte en notificación las alertas que `§3.14` nombra. `GA-REM-038` / `OD-08`.

        Una alerta pertenece al **lote**; una notificación, a **una persona**. No toda alerta
        se convierte: solo las dos que la fuente normativa enumera, y solo cuando la alerta se
        emitió de verdad —dentro de norma y sin referencia no la hay, y `GA-REM-037` sigue
        gobernando eso—.

        Los destinatarios salen de `OD-08`: quien registró el evento, los administradores, la
        contraloría y los supervisores de esa empresa, deduplicados.
        """
        from ..notifications.recipients import resolver_destinatarios
        from ..notifications.service import crear_notificacion

        notificables = [a for a in alerts if a.alert_type in self.ALERTAS_NOTIFICABLES]
        if not notificables:
            return

        from ..notifications.sla import _area_del_lote

        destinatarios = await resolver_destinatarios(
            self.db,
            company_id=event.company_id,
            area_id=await _area_del_lote(self.db, event.lot_id),
            originadores=[event.registered_by_id],
        )
        if not destinatarios:
            return

        for alerta in notificables:
            tipo = self.ALERTAS_NOTIFICABLES[alerta.alert_type]
            for user_id in destinatarios:
                await crear_notificacion(
                    self.db,
                    company_id=event.company_id,
                    recipient_user_id=user_id,
                    notification_type=tipo,
                    payload={
                        "lot_id": event.lot_id,
                        "message": alerta.message,
                        "threshold_value": alerta.threshold_value,
                        "actual_value": alerta.actual_value,
                    },
                    related_entity_type="operational_event",
                    related_entity_id=event.id,
                    evitar_duplicado_sin_leer=True,
                )

    async def _alertas_de_peso(
        self,
        event: models.OperationalEvent,
        data: schemas.OperationalEventCreate,
    ) -> list[models.OperationalAlert]:
        """Una alerta por cada pesaje fuera del rango esperado. `AC20`, `AC21`.

        Sin curva asignada, sin línea genética o con una edad que la tabla no cubre, el
        motor responde `NO_REFERENCE` y **no se emite nada**: avisar sin referencia sería
        inventarse un veredicto (`AC19`).

        `AC22`: esto crea un registro `OperationalAlert` y nada más. No hay correo, ni
        push, ni centro de notificaciones — eso es `P-14`, y sigue sin implementarse.
        """
        from .weight_curve import WeightStatus

        lectura = await self.evaluar_pesajes(
            event, [getattr(m, "avg_weight", None) for m in data.bird_movements]
        )
        age_days = lectura["age_days"]
        version = lectura["curve_version_label"]

        alertas: list[models.OperationalAlert] = []
        for fila in lectura["evaluations"]:
            estado = fila["status"]
            if estado in (WeightStatus.WITHIN_STANDARD.value, WeightStatus.NO_REFERENCE.value):
                continue
            peso = fila["avg_weight"]
            debajo = estado == WeightStatus.BELOW_STANDARD.value
            alertas.append(models.OperationalAlert(
                company_id=event.company_id,
                lot_id=event.lot_id,
                event_id=event.id,
                alert_type="weight_deviation",
                severity="warning",
                message=(
                    f"Peso {peso} g "
                    f"{'por debajo del' if debajo else 'por encima del'} rango estándar "
                    f"[{fila['expected_min']:g}–{fila['expected_max']:g} g] "
                    f"a {age_days} días "
                    f"(curva {version})."
                ),
                # El umbral que se cruzó, que es el que explica la alerta.
                threshold_value=(fila["expected_min"] if debajo else fila["expected_max"]),
                actual_value=peso,
            ))
        return alertas

    async def evaluar_pesajes(self, event, pesos: list) -> dict:
        """La evaluación de unos pesos contra la curva del lote. `AC26`, `AC27`.

        `R-97`. Este cálculo existía desde `GA-REM-037` pero **no era observable**: su único
        consumidor era el generador de alertas, que solo actúa cuando el peso queda fuera de
        rango. Desde fuera, «dentro de norma» y «sin referencia» se veían igual —sin alerta—,
        y una interfaz no puede distinguir dos cosas opuestas por la ausencia de una señal.

        No recalcula nada: llama al mismo motor (`weight_curve.evaluar`) que la alerta. Es la
        misma lectura vista dos veces, no dos implementaciones.
        """
        from datetime import date as _date, datetime as _datetime

        from ..masters.models import GeneticWeightCurve, Lot
        from .weight_curve import WeightStatus, evaluar

        def _sin_referencia(motivo: str) -> dict:
            """`AC27`. La ausencia de referencia se declara; callar sería afirmar normalidad."""
            return {
                "event_id": event.id,
                "lot_id": event.lot_id,
                "age_days": None,
                "curve_version_label": None,
                "reason": motivo,
                "evaluations": [
                    {"avg_weight": p, "status": WeightStatus.NO_REFERENCE.value,
                     "expected_min": None, "expected_target": None, "expected_max": None}
                    for p in pesos if p is not None and p > 0
                ],
            }

        lot = (await self.db.execute(
            select(Lot).where(Lot.id == event.lot_id)
        )).scalar_one_or_none()
        if lot is None or lot.start_date is None:
            return _sin_referencia("lot_without_start_date")
        if lot.genetic_line_id is None:
            return _sin_referencia("lot_without_genetic_line")
        if lot.weight_curve_id is None:
            return _sin_referencia("no_curve_assigned")

        curva = (await self.db.execute(
            select(GeneticWeightCurve).where(GeneticWeightCurve.id == lot.weight_curve_id)
        )).scalar_one_or_none()
        if curva is None or not curva.points:
            return _sin_referencia("curve_without_points")

        def _dia(valor):
            return valor.date() if isinstance(valor, _datetime) else valor

        # La edad del lote **el día del pesaje**, no hoy: un registro retroactivo debe
        # juzgarse contra el tramo de curva que le tocaba entonces.
        referencia = _dia(event.event_date) if event.event_date else _date.today()
        age_days = (referencia - _dia(lot.start_date)).days
        if age_days < 0:
            return _sin_referencia("event_before_lot_start")

        evaluaciones = []
        for peso in pesos:
            if peso is None or peso <= 0:
                continue
            e = evaluar(curva.points, age_days, peso)
            evaluaciones.append({
                "avg_weight": peso,
                "status": e.status.value,
                "expected_min": e.rango.min_weight if e.rango else None,
                "expected_target": e.rango.target_weight if e.rango else None,
                "expected_max": e.rango.max_weight if e.rango else None,
            })

        return {
            "event_id": event.id,
            "lot_id": event.lot_id,
            "age_days": age_days,
            "curve_version_label": curva.version_label,
            # Fuera del rango de edades de la tabla no hay extrapolación: el motor ya
            # devolvió `NO_REFERENCE` por fila, y aquí se nombra el porqué.
            "reason": None if any(f["expected_min"] is not None for f in evaluaciones)
                      else "age_outside_curve_table",
            "evaluations": evaluaciones,
        }

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
        # `BR-10`/`BR-11`: un documento SAP no se duplica — **salvo en la recepción de aves**.
        #
        # `OD-04`, decidida por el propietario: una misma orden de compra puede recibirse en
        # varias entregas parciales. Aplicar aquí la unicidad prohibiría exactamente eso. La
        # protección de la recepción es el límite **acumulado** (`BR-18`), unas líneas abajo.
        #
        # Se deja intacta para los demás tipos de evento: `OD-04` responde sobre órdenes de
        # compra y recepciones, y extender su alcance sería inventar política.
        if (
            data.sap_document_ref
            and data.lot_id is not None
            and event_type != models.EventType.BIRD_RECEPTION
        ):
            await validate_sap_document_unique(self.db, data.lot_id, event_type, data.sap_document_ref)

        total_qty = sum(bm.quantity for bm in data.bird_movements) + sum(em.quantity for em in data.egg_movements)

        # G-R04: Validate house capacity for reception/distribution events
        if event_type in (models.EventType.BIRD_RECEPTION, models.EventType.BIRD_DISTRIBUTION):
            if data.house_id and total_qty > 0:
                await validate_house_capacity(self.db, data.house_id, total_qty)
            # G-R05: Validate quantity ≤ OC
            await validate_oc_limit(
                self.db, data.sap_document_ref, total_qty, company_id=self.company_id,
            )

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
        elif event_type in (models.EventType.CULL_RECORDING, models.EventType.BIRD_EXIT):
            # `GA-REM-005-B` / `R-130`. Descarte y salida son salidas del saldo (`E.3`) y no
            # tenían rama: se registraban por encima del saldo, o con cero aves, con `201`.
            # Misma regla que la mortalidad, en el mismo sitio, bajo el mismo bloqueo.
            if data.lot_id is None:
                raise BusinessRuleViolation("El evento requiere lote", "BR-07")
            etiqueta = "descarte" if event_type == models.EventType.CULL_RECORDING else "salida"
            await validate_bird_decrement(self.db, data.lot_id, total_qty, etiqueta)
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
        # `GA-REM-002-C` / `R-139` · `OD-14.c`: dato productivo = `INQUILINO`. El predicado
        # de empresa es **incondicional**: antes, `if not is_super_admin` lo retiraba y la
        # autoridad global sin contexto listaba las alertas de todas las empresas.
        query = self._acotar_a_empresa(query, models.OperationalAlert.company_id)
        query = await self._acotar_alertas_a_unidades(query)
        if lot_id is not None:
            query = query.where(models.OperationalAlert.lot_id == lot_id)
        if is_resolved is not None:
            query = query.where(models.OperationalAlert.is_resolved == is_resolved)
        query = query.order_by(models.OperationalAlert.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _acotar_alertas_a_unidades(self, query):
        """`GA-REM-040-G` · `R-159` · `AC-A01…A07`: la alerta es de su lote, y el lote de su cadena.

        Predicado **en la consulta**, antes de contar, ordenar o paginar: `lot_id IN
        lotes_alcanzables(empresa, unidades efectivas)`; cero unidades → `false()` → `[]`
        (`OD-09.c`). La autoridad global conserva la visibilidad de control certificada en la
        fase 3 (toda la empresa situada, unidades apagadas incluidas), igual que `get_events`.
        """
        if self.current_user.get("is_super_admin"):
            return query
        from ..business_units.scope import lotes_alcanzables

        return query.where(models.OperationalAlert.lot_id.in_(
            lotes_alcanzables(self.company_id, await self._unidades())))

    async def resolve_alert(self, alert_id: int) -> models.OperationalAlert:
        from datetime import datetime, timezone
        query = select(models.OperationalAlert).where(models.OperationalAlert.id == alert_id)
        query = self._acotar_a_empresa(query, models.OperationalAlert.company_id)
        query = await self._acotar_alertas_a_unidades(query)  # `AC-A13`: ajena por unidad = 404
        alert = (await self.db.execute(query)).scalar_one_or_none()
        if alert is None:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        await self.exigir_unidad_operativa(lot_id=alert.lot_id)  # global sobre unidad apagada = 403
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
        #
        # `GA-REM-002-C` / `R-139` · `OD-14.c/d`: el predicado de empresa se aplica a
        # **todos**, autoridad global incluida; sin empresa efectiva, cero filas. Lo único
        # que sigue condicionado a no ser global es el predicado de **unidad**: la exención
        # de visibilidad certificada en la fase 3 se preserva tal cual.
        query = self._acotar_a_empresa(query, models.OperationalEvent.company_id)
        if not self.current_user.get("is_super_admin"):
            # `GA-REM-040` fase 6. La cadena del evento se deriva de su lote o se fijó a
            # mano; lo que no tiene ninguna de las dos **no aparece aquí**: su superficie es
            # la bandeja de pendientes, aparte. Mezclarlo en el listado normal obligaría a
            # que cada consulta recordara la excepción del creador, y la que la olvidara
            # abriría el sistema en silencio.
            from ..business_units.classification import predicado_de_evento

            query = query.where(
                predicado_de_evento(await self._unidades(), self.company_id))

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
        if not self.current_user.get("is_super_admin"):
            from ..business_units.classification import predicado_de_evento

            query = query.where(
                predicado_de_evento(await self._unidades(), self.company_id))
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
        # `GA-REM-006-A` · `OD-17.a`: un rechazo corregible no es terminal. `REJECTED` es
        # editable como `RETURNED`; el estado no cambia por editar (`AC-U02`).
        if event.status not in EDITABLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden editar eventos en borrador, registrados, devueltos o rechazados")
        # `GA-REM-041` · `AC-RV06`: la contrapartida de un reverso lleva las cantidades del
        # original; editarla rompería la compensación exacta (`OD-19 §4`).
        from ..reversals.service import es_contrapartida

        if await es_contrapartida(self.db, event.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Una contrapartida de reverso no se edita")
        # `exclude_unset` es lo que hace que una edición parcial no borre lo que no
        # menciona. El esquema ya excluye `status`, `event_type` e `idempotency_key`, de
        # modo que aquí no puede llegar ninguno: el estado solo cambia por las
        # transiciones del flujo (R-32).
        cambios = data.model_dump(exclude_unset=True)
        # `GA-REM-040-G` · `R-160` · `AC-W09`: el destino de una edición se verifica como el
        # de un alta. Antes, `lot_id`, `farm_id` y `house_id` se asignaban tal cual llegaban,
        # de modo que un evento podía repuntarse a un lote de otra unidad **o de otra empresa**
        # (`R-42` cubría el alta, no la edición). Si el lote no cambia, la guarda mira el
        # actual: para el actor de empresa ya lo garantizó `get_event`; para la autoridad
        # global bloquea la unidad apagada.
        lote_destino = cambios["lot_id"] if "lot_id" in cambios else event.lot_id
        if "lot_id" in cambios and lote_destino is not None:
            await validate_lot_active(self.db, lote_destino, self.company_id)
            await validate_event_date(self.db, lote_destino, cambios.get("event_date", event.event_date))
        if any(k in cambios for k in ("farm_id", "house_id", "destination_farm_id")):
            from ..tenancy import verificar_ubicacion

            await verificar_ubicacion(
                self.db, self.company_id,
                farm_id=cambios.get("farm_id"), house_id=cambios.get("house_id"),
                destination_farm_id=cambios.get("destination_farm_id"),
            )
        if lote_destino is not None:
            await self.exigir_unidad_operativa(lot_id=lote_destino)
        else:
            await self.exigir_unidad_operativa(event=event)
        for key, val in cambios.items():
            setattr(event, key, val)
        event.version += 1
        await self.db.flush()
        await self.db.refresh(event)
        # Audit
        await audit_state_transition(self.db, event, self.current_user, old_status, old_status, comments="Evento actualizado")
        return event

    async def submit_to_review(self, event_id: int) -> models.OperationalEvent:
        event = await self.get_event(event_id)
        await self.exigir_unidad_operativa(event=event)  # `AC-W13`: unidad apagada = 403
        # `GA-REM-006-A` · `R-135` · `OD-17.b` · `docs/12 §2`: el devuelto y el rechazado se
        # **reenvían** con este mismo acto explícito y vuelven a la cola de revisión; el
        # corregido espera al aprobador y el aprobado no vuelve. Mapa explícito, sin `setattr`
        # de estado desde el cliente.
        if event.status not in REENVIABLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo eventos registrados, devueltos o rechazados pueden enviarse a revisión")
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
        await self.exigir_unidad_operativa(event=event)  # `AC-W13`
        # `GA-REM-006-A` · `R-140` PARTE A: lo aprobado, lo consolidado, lo enviado o confirmado
        # por SAP, lo que SAP rechazó y lo ya anulado no se cancelan por aquí (`OD-17.a`:
        # terminales y ciclo SAP; `BR-15`/`BR-16`: solo reverso). Motivo y permiso: fuera.
        if event.status in NO_CANCELABLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede cancelar un evento aprobado, consolidado, enviado o confirmado por SAP, con error de SAP o ya anulado")
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
        await self.exigir_unidad_operativa(event=event)  # `AC-W13`
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
        # `R-139` · `OD-14.c`: la comparación de empresa es para todos; sin empresa efectiva
        # (`None`) nunca coincide, y la autoridad global borra solo desde una empresa situada.
        if evidence.company_id != self.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
        # `GA-REM-040-G` · `AC-W06`: ya dentro de la empresa, el evento se resuelve con el mismo
        # alcance de unidad que el resto de sus superficies (`404` para el actor de empresa
        # sobre unidad no alcanzable) y después la guarda de escritura (`403` para la
        # autoridad global sobre unidad apagada). Antes solo se comparaba la empresa. El
        # orden preserva el contrato certificado de `R-139` (`403` entre inquilinos).
        event = await self.get_event(event_id)
        await self.exigir_unidad_operativa(event=event)
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
        # `R-139` · `OD-14.c`: ídem `delete_evidence`; el fichero solo se sirve desde la
        # empresa efectiva de la evidencia.
        if evidence.company_id != self.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
        # `GA-REM-040-H` · `R-162` · `AC-E02…E04`: ya dentro de la empresa, el evento se resuelve
        # con el mismo alcance de unidad que su listado (`404` para el actor de empresa; la
        # autoridad global situada conserva la visibilidad de control). Antes, el fichero de
        # otra cadena de la propia empresa se servía con solo comparar la empresa.
        await self.get_event(event_id)
        return evidence

    # ============================================================
    # Event Types Reference
    # ============================================================

    def get_event_types(self) -> list[dict]:
        return schemas.ALL_EVENT_TYPES
