"""
Lot service with business rules for lot lifecycle management.
"""
from datetime import date, datetime, time, timezone


def _dia(valor: datetime | date) -> date:
    """Día del calendario de un valor que puede venir como fecha o como instante."""
    return valor.date() if isinstance(valor, datetime) else valor


def _fecha_de_negocio(valor: datetime | date) -> datetime:
    """Un día del calendario anclado a medianoche UTC, listo para una columna con zona.

    `R-75`. Vale para cualquier fecha de negocio del lote, no solo la de inicio: `end_date`
    es la misma columna `DateTime(timezone=True)` y arrastraba el mismo desfase.
    """
    return datetime.combine(_dia(valor), time.min, tzinfo=timezone.utc)


def _inicio_declarado(valor: datetime | date | None) -> datetime:
    """Inicio del ciclo, anclado a medianoche UTC.

    `GA-REM-028 AC01/AC02`. La columna es `DateTime(timezone=True)` y la base corre en
    `CET`, de modo que una fecha sin zona se guardaba a medianoche local y volvía como el
    **día anterior** en UTC. Afectaba también al valor por omisión: un lote creado hoy se
    leía como iniciado ayer.

    Anclar el día declarado a medianoche UTC hace que la petición, la persistencia y la
    respuesta hablen del mismo día del calendario, que es lo que `§46` exige. No se cambia
    el tipo de la columna: eso sería una migración que `R-47` no necesita.
    """
    if valor is None:
        valor = date.today()
    return _fecha_de_negocio(valor)
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..masters.models import Lot
from ..tenancy import verificar_pertenencia
from ..operations.validators import validate_lot_closure, validate_lot_records_approved
from ..operations.models import (
    OperationalEvent, EventType, EventStatus,
    BirdMovement, FeedMovement, EggMovement,
)
from . import models, schemas
from ..masters.service import MasterService


class LotService:
    """Handles lot CRUD, activation, closure, and balance queries."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")
        self.is_super_admin = current_user.get("is_super_admin", False)

    async def get_lots(
        self, skip: int = 0, limit: int = 20, search: str = "",
        farm_id: Optional[int] = None, status: Optional[str] = None,
    ) -> tuple[list[Lot], int]:
        """List lots with filters and company isolation."""
        master_service = MasterService(self.db, Lot, self.current_user)
        filters = {}
        if farm_id:
            filters["farm_id"] = farm_id
        if status:
            filters["status"] = status
        return await master_service.get_all(
            skip=skip, limit=limit, search=search,
            search_fields=["lot_code"],
            filters=filters,
            order_by="lot_code",
        )

    async def get_lot(self, lot_id: int) -> Lot:
        """Get single lot with phases and opening balance eager loaded."""
        master_service = MasterService(self.db, Lot, self.current_user)
        return await master_service.get_by_id(lot_id)

    async def _curva_del_lote(
        self, genetic_line_id: Optional[int], weight_curve_id: Optional[int]
    ) -> Optional[int]:
        """La versión de curva que le corresponde a un lote nuevo. `AC09`, `AC10`.

        Sin línea genética no hay curva posible, y no se inventa ninguna: el motor
        devolverá `NO_REFERENCE`, que es la respuesta honesta (`AC19`).
        """
        from ..masters.curves import version_activa
        from ..masters.models import GeneticWeightCurve

        if weight_curve_id is None:
            if genetic_line_id is None:
                return None
            activa = await version_activa(self.db, genetic_line_id)
            return activa.id if activa else None

        curva = (await self.db.execute(
            select(GeneticWeightCurve).where(GeneticWeightCurve.id == weight_curve_id)
        )).scalar_one_or_none()
        if curva is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curva de peso no encontrada",
            )
        # `AC10`. Juzgar un Ross 308 contra la tabla de un Cobb 500 produce un veredicto
        # con toda la apariencia de ser correcto y ninguna de las garantías.
        if curva.genetic_line_id != genetic_line_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La curva de peso pertenece a otra línea genética",
            )
        return curva.id

    async def create_lot(self, data: schemas.LotCreate) -> Lot:
        """Create a new lot."""
        existing = await self.db.execute(
            select(Lot).where(Lot.lot_code == data.lot_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un lote con ese código",
            )

        # Validate farm belongs to user's company (or is global)
        if data.farm_id:
            from ..masters.models import Farm
            farm_result = await self.db.execute(select(Farm).where(Farm.id == data.farm_id))
            farm = farm_result.scalar_one_or_none()
            if farm and farm.company_id is not None and farm.company_id != self.company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="La granja no pertenece a su compañía",
                )

        # `GA-REM-037` / `OD-06`. La curva estándar contra la que se juzgará este lote se
        # fija ahora y no se recalcula: es lo que separa una referencia histórica de una
        # que cambia bajo los pies del dato ya registrado (`AC07`, `AC08`).
        weight_curve_id = await self._curva_del_lote(
            data.genetic_line_id, getattr(data, "weight_curve_id", None)
        )

        lot = Lot(
            company_id=self.company_id,
            lot_code=data.lot_code,
            farm_id=data.farm_id,
            house_id=data.house_id,
            genetic_line_id=data.genetic_line_id,
            weight_curve_id=weight_curve_id,
            breed_id=data.breed_id,
            bird_type=data.bird_type,
            sex=data.sex,
            status="active",
            activation_type="normal",
            # `GA-REM-028` / `R-47`. La fecha que envía quien registra el lote se
            # descartaba y se ponía la de hoy, de modo que un lote ya en marcha nacía con
            # edad cero: `age_days`, el índice productivo y la ganancia diaria salían mal,
            # y `BR-06` rechazaba cualquier evento retroactivo. Es lo que bloqueaba `P-11`.
            #
            # `RR-09`: `start_date` es el inicio del ciclo según el negocio y lo aporta el
            # usuario; `created_at` —que el servidor sigue fijando— es el alta en el
            # software. Para un lote incorporado, las dos difieren legítimamente.
            #
            # Omitirla mantiene el comportamiento de siempre: hoy.
            start_date=_inicio_declarado(data.start_date),
        )
        self.db.add(lot)
        await self.db.flush()
        await self.db.refresh(lot)
        # `GA-REM-032 AC02`. El alta de un lote no pasa por `MasterService`, así que la
        # instrumentación de los maestros no la alcanzaba: sin esto, crear un lote seguiría
        # sin dejar rastro.
        from ..audit.helpers import audit_accion
        from ..audit.models import AuditAction, AuditModule

        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CREATED,
            modulo=AuditModule.LOTS, entity_type="lot", entity_id=lot.id,
            company_id=lot.company_id, lot_id=lot.id,
            new_values={"lot_code": lot.lot_code,
                        "bird_type": str(getattr(lot.bird_type, "value", lot.bird_type))},
        )
        return lot

    async def update_lot(self, lot_id: int, data: schemas.LotUpdate) -> Lot:
        """Update lot fields."""
        master_service = MasterService(self.db, Lot, self.current_user)
        return await master_service.update(lot_id, data)

    async def close_lot(self, lot_id: int) -> dict:
        """G-09: Close a lot with final summary (BR-05)."""
        master_service = MasterService(self.db, Lot, self.current_user)
        lot = await master_service.get_by_id(lot_id)

        if lot.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden cerrar lotes activos",
            )

        # `R-74` / `GA-REM-029 AC05`. `BR-05` exige pesaje y alimento antes de cerrar, sin
        # los cuales el resumen final no tiene base para el FCR. La guarda existía, pero
        # colgaba del evento `lot_closure`, que **no cierra el lote**: este endpoint es el
        # único sitio del backend que asigna `status = "closed"`. Vigilaba la puerta
        # equivocada, y el audit la daba por vigente justamente aquí.
        await validate_lot_closure(self.db, lot_id)

        # `R-76` / `GA-REM-036`. `docs/12 §6 R7`: un lote no puede cerrarse con registros sin
        # aprobar. Estaba escrita en la documentación del ciclo de revisión y no existía aquí,
        # de modo que un lote se cerraba con todos sus eventos en `registered`.
        #
        # Va **antes** de tocar `status` y `end_date`: una negativa no puede dejar el cierre a
        # medias. Es una regla distinta de `BR-05` y se cita como `R7`, que es como la norma
        # la llama; no se amplía `BR-05` ni se inventa un `BR-` nuevo.
        await validate_lot_records_approved(self.db, lot_id, self.company_id)

        # Calculate final summary
        # Total mortality
        mort_q = select(func.coalesce(func.sum(BirdMovement.quantity), 0)).join(
            OperationalEvent, BirdMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.MORTALITY_RECORDING,
        )
        mort_result = await self.db.execute(mort_q)
        total_mortality = mort_result.scalar() or 0

        # Total feed consumed
        feed_q = select(func.coalesce(func.sum(FeedMovement.quantity_kg), 0.0)).join(
            OperationalEvent, FeedMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
        )
        feed_result = await self.db.execute(feed_q)
        total_feed_kg = round(feed_result.scalar() or 0.0, 2)

        # Total eggs produced (if breeder)
        egg_q = select(func.coalesce(func.sum(EggMovement.quantity), 0)).join(
            OperationalEvent, EggMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.EGG_COLLECTION,
        )
        egg_result = await self.db.execute(egg_q)
        total_eggs = egg_result.scalar() or 0

        # Approved events count
        events_q = select(func.count(OperationalEvent.id)).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
        )
        events_result = await self.db.execute(events_q)
        total_events = events_result.scalar() or 0

        approved_q = select(func.count(OperationalEvent.id)).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.status.in_([
                EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
            ]),
        )
        approved_result = await self.db.execute(approved_q)
        approved_events = approved_result.scalar() or 0

        # Age in days
        # `R-73`. Restaba un `datetime` de un `date` y reventaba con `TypeError`, de modo
        # que **el cierre de lote respondía 500 siempre**: `start_date` nunca es nulo. Es la
        # misma confusión entre fecha de negocio y marca temporal que originó `R-47`, y por
        # eso se resuelve con él (`GA-REM-028 AC07`): la edad es la única consumidora
        # alcanzable de `start_date`, y sin esto el criterio no puede comprobarse.
        age_days = (date.today() - _dia(lot.start_date)).days if lot.start_date else 0

        summary = {
            "lot_id": lot_id,
            "lot_code": lot.lot_code if hasattr(lot, 'lot_code') else f"L-{lot_id}",
            "age_days": age_days,
            "total_mortality": total_mortality,
            "total_feed_kg": total_feed_kg,
            "total_eggs": total_eggs,
            "total_events": total_events,
            "approved_events": approved_events,
            "status": "closed",
            "end_date": str(date.today()),
        }

        lot.status = "closed"
        # `R-75`. Escribir `date.today()` en una columna con zona lo guardaba a medianoche
        # **local**, de modo que el lote cerrado hoy se releía como cerrado ayer: el resumen
        # decía una fecha y el registro otra. Es el mismo desfase que `GA-REM-028` corrigió
        # en `start_date`, que quedó sin aplicar al campo hermano.
        lot.end_date = _fecha_de_negocio(date.today())
        await self.db.flush()
        await self.db.refresh(lot)

        return summary

    # ============================================================
    # Manual Activation (Opening Balance)
    # ============================================================

    async def activate_manual(self, data: schemas.OpeningBalanceCreate) -> models.OpeningBalance:
        """
        Activate a lot manually with opening balances.
        Used for lots that already exist before system adoption.
        """
        # Validate lot exists
        lot = await self.db.execute(select(Lot).where(Lot.id == data.lot_id))
        lot = lot.scalar_one_or_none()
        if not lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

        # `AC-R67-11`. Hasta aquí lo único que impedía activar el lote de otra empresa era
        # carecer del permiso `lots:create`; quien lo tuviera en su propia empresa podía
        # fijar el saldo de apertura de un lote ajeno. Existir no es pertenecer: se usa la
        # misma comprobación que el resto del sistema (`GA-REM-002 AC10`).
        if not self.is_super_admin:
            await verificar_pertenencia(self.db, Lot, data.lot_id, self.company_id, "Lote")

        # Validate no existing opening balance
        existing = await self.db.execute(
            select(models.OpeningBalance).where(models.OpeningBalance.lot_id == data.lot_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este lote ya tiene un balance de apertura registrado",
            )

        # `docs/02 §3.9.2` exige «Se evita doble conteo» y nada lo implementaba: un lote
        # que ya tuviera eventos de recepción y recibiera además un saldo de apertura
        # contaría dos veces las mismas aves. La activación manual sirve para lotes que
        # existían **antes** de la implantación, no para corregir lotes ya operando.
        con_historia = await self.db.execute(
            select(OperationalEvent.id)
            .where(
                OperationalEvent.lot_id == data.lot_id,
                OperationalEvent.status != EventStatus.CANCELLED,
            )
            .limit(1)
        )
        if con_historia.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El lote ya tiene operaciones registradas: activarlo manualmente "
                    "contaría dos veces las mismas aves"
                ),
            )

        # Business rules for opening balance
        if data.accumulated_mortality_male > data.initial_male_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mortalidad acumulada machos no puede exceder población inicial",
            )
        if data.accumulated_mortality_female > data.initial_female_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mortalidad acumulada hembras no puede exceder población inicial",
            )

        ob = models.OpeningBalance(
            lot_id=data.lot_id,
            activation_date=data.activation_date,
            phase_at_activation_id=data.phase_at_activation_id,
            age_days=data.age_days,
            initial_male_count=data.initial_male_count,
            initial_female_count=data.initial_female_count,
            accumulated_mortality_male=data.accumulated_mortality_male,
            accumulated_mortality_female=data.accumulated_mortality_female,
            accumulated_culls_male=data.accumulated_culls_male,
            accumulated_culls_female=data.accumulated_culls_female,
            accumulated_feed_kg=data.accumulated_feed_kg,
            current_avg_weight=data.current_avg_weight,
            accumulated_egg_production=data.accumulated_egg_production,
            accumulated_eggs_to_hatchery=data.accumulated_eggs_to_hatchery,
            accumulated_chicks_hatched=data.accumulated_chicks_hatched,
            accumulated_broiler_received=data.accumulated_broiler_received,
            activation_reason=data.activation_reason,
            support_document_url=data.support_document_url,
            is_manual_activation=True,
            activated_by_id=self.current_user["id"],
        )
        self.db.add(ob)

        # Mark lot as manually activated
        lot.activation_type = "manual"
        # Misma normalización que en el alta: la columna es `DateTime(timezone=True)` y la
        # base corre en `CET`, de modo que una fecha sin zona se guardaba a medianoche local
        # y volvía como el día anterior. La semántica no cambia —`docs/02 §3.9` pide la
        # «fecha real de inicio» y eso es lo que se guarda—, solo deja de derivar un día.
        lot.start_date = _inicio_declarado(data.activation_date)

        await self.db.flush()
        await self.db.refresh(ob)
        return ob

    async def get_opening_balance(self, lot_id: int) -> Optional[models.OpeningBalance]:
        """Get opening balance for a lot."""
        result = await self.db.execute(
            select(models.OpeningBalance).where(models.OpeningBalance.lot_id == lot_id)
        )
        return result.scalar_one_or_none()

    async def get_lot_phases(self, lot_id: int) -> list[models.LotPhase]:
        """Get all phases for a lot."""
        result = await self.db.execute(
            select(models.LotPhase)
            .where(models.LotPhase.lot_id == lot_id)
            .order_by(models.LotPhase.start_date)
        )
        return list(result.scalars().all())

    async def add_phase(self, data: schemas.LotPhaseCreate) -> models.LotPhase:
        """Add a new phase to a lot."""
        phase = models.LotPhase(**data.model_dump())
        self.db.add(phase)
        await self.db.flush()
        await self.db.refresh(phase)
        return phase
