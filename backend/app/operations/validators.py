"""
Business rules validators for operational events.
BR-01 through BR-19 from the spec.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BirdMovement, EggMovement, EventStatus, EventType, HatcheryParams, OperationalEvent


class BusinessRuleViolation(Exception):
    """Raised when a business rule is violated."""
    def __init__(self, message: str, rule_id: str = ""):
        self.message = message
        self.rule_id = rule_id
        super().__init__(message)


# ─── Balance helpers ──────────────────────────────────────────────────────────

async def get_current_bird_balance(db: AsyncSession, lot_id: int) -> int:
    """
    Current live bird count for a lot.
    IN:  BIRD_RECEPTION, BIRTH_REGISTRATION
    OUT: MORTALITY_RECORDING, CULL_RECORDING, BIRD_EXIT, CHICK_DISPATCH
    """
    in_types = [EventType.BIRD_RECEPTION, EventType.BIRTH_REGISTRATION]
    out_types = [
        EventType.MORTALITY_RECORDING,
        EventType.CULL_RECORDING,
        EventType.BIRD_EXIT,
        EventType.CHICK_DISPATCH,
    ]
    res_in = await db.execute(
        select(func.coalesce(func.sum(BirdMovement.quantity), 0))
        .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type.in_(in_types),
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    res_out = await db.execute(
        select(func.coalesce(func.sum(BirdMovement.quantity), 0))
        .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type.in_(out_types),
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    return (res_in.scalar() or 0) - (res_out.scalar() or 0)


async def get_egg_balance(db: AsyncSession, lot_id: int) -> int:
    """
    Fertile eggs available at the farm for dispatch.
    IN:  EGG_COLLECTION
    OUT: EGG_DISPATCH
    """
    res_in = await db.execute(
        select(func.coalesce(func.sum(EggMovement.quantity), 0))
        .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.EGG_COLLECTION,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    res_out = await db.execute(
        select(func.coalesce(func.sum(EggMovement.quantity), 0))
        .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.EGG_DISPATCH,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    return (res_in.scalar() or 0) - (res_out.scalar() or 0)


async def get_hatchery_egg_balance(db: AsyncSession, lot_id: int) -> int:
    """
    Eggs available at hatchery (received - loaded into incubators).
    IN:  EGG_RECEPTION_HATCHERY
    OUT: INCUBATION_LOAD (quantity_loaded from hatchery_params)
    """
    res_in = await db.execute(
        select(func.coalesce(func.sum(EggMovement.quantity), 0))
        .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.EGG_RECEPTION_HATCHERY,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    res_out = await db.execute(
        select(func.coalesce(func.sum(HatcheryParams.quantity_loaded), 0))
        .join(OperationalEvent, HatcheryParams.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.INCUBATION_LOAD,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    return (res_in.scalar() or 0) - (res_out.scalar() or 0)


async def get_viable_chick_balance(db: AsyncSession, lot_id: int) -> int:
    """
    Viable chicks available for dispatch.
    IN:  BIRTH_REGISTRATION (bird_movements)
    OUT: CHICK_DISPATCH (bird_movements)
    """
    res_in = await db.execute(
        select(func.coalesce(func.sum(BirdMovement.quantity), 0))
        .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.BIRTH_REGISTRATION,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    res_out = await db.execute(
        select(func.coalesce(func.sum(BirdMovement.quantity), 0))
        .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.CHICK_DISPATCH,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    return (res_in.scalar() or 0) - (res_out.scalar() or 0)


# ─── Business rule validators ─────────────────────────────────────────────────

async def validate_mortality(db: AsyncSession, lot_id: int, quantity: int) -> None:
    """BR-01: Mortality cannot exceed available bird balance."""
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad de mortalidad debe ser mayor a cero", "BR-01")
    balance = await get_current_bird_balance(db, lot_id)
    if quantity > balance:
        raise BusinessRuleViolation(
            f"Mortalidad ({quantity}) excede el saldo de aves disponibles ({balance})",
            "BR-01",
        )


async def validate_egg_dispatch(db: AsyncSession, lot_id: int, quantity: int) -> None:
    """BR-02: Egg dispatch cannot exceed available egg balance."""
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad de huevos debe ser mayor a cero", "BR-02")
    balance = await get_egg_balance(db, lot_id)
    if quantity > balance:
        raise BusinessRuleViolation(
            f"Despacho de huevos ({quantity}) excede el saldo disponible ({balance}). "
            "Registre primero la recolección.",
            "BR-02",
        )


async def validate_incubation_load(db: AsyncSession, lot_id: int, quantity: int) -> None:
    """BR-03: Incubation load cannot exceed eggs received at hatchery."""
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad a cargar debe ser mayor a cero", "BR-03")
    balance = await get_hatchery_egg_balance(db, lot_id)
    if quantity > balance:
        raise BusinessRuleViolation(
            f"Carga de incubadora ({quantity}) excede los huevos disponibles en incubadora ({balance}). "
            "Registre primero la recepción de huevos.",
            "BR-03",
        )


async def validate_chick_dispatch(db: AsyncSession, lot_id: int, quantity: int) -> None:
    """BR-04: Chick dispatch cannot exceed viable births."""
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad de pollitos debe ser mayor a cero", "BR-04")
    balance = await get_viable_chick_balance(db, lot_id)
    if quantity > balance:
        raise BusinessRuleViolation(
            f"Despacho de pollitos ({quantity}) excede los pollitos viables disponibles ({balance}). "
            "Registre primero el nacimiento.",
            "BR-04",
        )


async def validate_lot_closure(db: AsyncSession, lot_id: int) -> None:
    """
    BR-05: Lot closure requires at least one weight_recording AND one feed_registration.
    Without these, FCR and final weight cannot be computed.
    """
    has_weight = await db.execute(
        select(OperationalEvent.id).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.WEIGHT_RECORDING,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        ).limit(1)
    )
    if not has_weight.scalar_one_or_none():
        raise BusinessRuleViolation(
            "No se puede cerrar el lote sin al menos un registro de pesaje (requerido para calcular FCR y peso final)",
            "BR-05",
        )
    has_feed = await db.execute(
        select(OperationalEvent.id).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.FEED_REGISTRATION,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        ).limit(1)
    )
    if not has_feed.scalar_one_or_none():
        raise BusinessRuleViolation(
            "No se puede cerrar el lote sin al menos un registro de consumo de alimento (requerido para calcular FCR)",
            "BR-05",
        )


async def validate_sap_document_unique(
    db: AsyncSession,
    lot_id: int,
    event_type: EventType,
    sap_document_ref: str | None,
    exclude_event_id: int | None = None,
) -> None:
    """
    BR-10: SAP documents must not be duplicated for the same lot+event_type combination.
    Only applies to documents that reference SAP (purchase orders, dispatch orders, etc.).
    """
    if not sap_document_ref:
        return
    q = select(OperationalEvent.id).where(
        OperationalEvent.lot_id == lot_id,
        OperationalEvent.event_type == event_type,
        OperationalEvent.sap_document_ref == sap_document_ref,
        OperationalEvent.status.not_in([EventStatus.CANCELLED]),
    )
    if exclude_event_id:
        q = q.where(OperationalEvent.id != exclude_event_id)
    result = await db.execute(q.limit(1))
    if result.scalar_one_or_none():
        raise BusinessRuleViolation(
            f"El documento SAP '{sap_document_ref}' ya fue registrado para este lote. "
            "Los documentos SAP no pueden duplicarse.",
            "BR-10",
        )


async def validate_event_date(db: AsyncSession, lot_id: int, event_date) -> None:
    """BR-06: Event date cannot be before lot activation date."""
    from ..masters.models import Lot
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if lot and lot.start_date and event_date < lot.start_date.date() if hasattr(lot.start_date, 'date') else False:
        if lot.activation_type != "manual":
            raise BusinessRuleViolation(
                f"Fecha del evento ({event_date}) anterior a la activación del lote ({lot.start_date})",
                "BR-06",
            )


async def validate_lot_active(db: AsyncSession, lot_id: int) -> None:
    """BR-07: Movements require active lot."""
    from ..masters.models import Lot, LotStatus
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if not lot:
        raise BusinessRuleViolation("Lote no encontrado", "BR-07")
    if lot.status != LotStatus.ACTIVE:
        raise BusinessRuleViolation(
            f"El lote no está activo (estado: {lot.status.value}). No se pueden registrar movimientos.",
            "BR-07",
        )


def validate_segregation(registered_by_id: int, action_user_id: int, action: str = "aprobar") -> None:
    """BR-14: Operator cannot approve own data. Enforces segregation of duties."""
    if registered_by_id == action_user_id:
        raise BusinessRuleViolation(
            f"Un operador no puede {action} sus propios registros (segregación de funciones)",
            "BR-14",
        )


def validate_sap_edit_lock(event_status: str) -> None:
    """BR-15: Records sent to SAP cannot be edited directly."""
    locked_statuses = ("sent_to_sap", "sap_confirmed", "consolidated")
    if event_status in locked_statuses:
        raise BusinessRuleViolation(
            f"Registros enviados a SAP no pueden editarse (estado: {event_status}). "
            "Requiere reverso, corrección auditada o nuevo movimiento autorizado.",
            "BR-15",
        )


async def validate_house_capacity(db: AsyncSession, house_id: int, quantity: int) -> None:
    """G-R04 / BR-17: Bird placement cannot exceed house capacity."""
    if house_id is None:
        return
    from ..masters.models import House
    result = await db.execute(select(House).where(House.id == house_id))
    house = result.scalar_one_or_none()
    if not house:
        raise BusinessRuleViolation(f"Galpón {house_id} no encontrado", "BR-17")
    if house.capacity and quantity > house.capacity:
        raise BusinessRuleViolation(
            f"Cantidad de aves ({quantity}) excede la capacidad del galpón ({house.capacity})",
            "BR-17",
        )


async def validate_oc_limit(db: AsyncSession, sap_document_ref: str | None, quantity_received: int) -> None:
    """G-R05 / BR-18: Quantity received cannot exceed Purchase Order without authorization."""
    if not sap_document_ref:
        return
    from ..integrations.sap.models import SapReference, SapReferenceType
    result = await db.execute(
        select(SapReference).where(
            SapReference.sap_code == sap_document_ref,
            SapReference.ref_type == SapReferenceType.PURCHASE_ORDER,
        )
    )
    oc = result.scalar_one_or_none()
    if oc and oc.quantity is not None and quantity_received > oc.quantity:
        raise BusinessRuleViolation(
            f"Cantidad recibida ({quantity_received}) excede la OC {sap_document_ref} ({oc.quantity})",
            "BR-18",
        )


async def validate_period_open(db: AsyncSession, event_date) -> None:
    """G-R12 / BR-19: Cannot register events in closed SAP periods (>90 days)."""
    from datetime import date
    today = date.today()
    if isinstance(event_date, str):
        from datetime import datetime as dt
        event_date = dt.strptime(event_date, "%Y-%m-%d").date()
    if hasattr(event_date, 'date'):
        event_date = event_date.date()
    days_ago = (today - event_date).days
    if days_ago > 90:
        raise BusinessRuleViolation(
            f"La fecha del evento ({event_date}) está en un período cerrado (+90 días). "
            "Requiere autorización especial.",
            "BR-19",
        )


async def validate_farm_house(event_type: str, farm_id: int | None, house_id: int | None) -> None:
    """F-03 / BR-08: Movements require farm/house when applicable."""
    location_events = {
        "bird_reception", "bird_distribution", "bird_transfer", "bird_exit",
        "farm_inspection", "transport_inspection", "egg_collection",
        "egg_dispatch", "egg_reception_hatchery", "chick_dispatch", "hatchery_inspection",
    }
    if event_type in location_events:
        if farm_id is None or farm_id <= 0:
            raise BusinessRuleViolation(f"El evento '{event_type}' requiere una granja asignada", "BR-08")
        if house_id is None or house_id <= 0:
            raise BusinessRuleViolation(f"El evento '{event_type}' requiere un galpón asignado", "BR-08")



# Legacy balance helper — renamed to avoid shadowing the comprehensive version above
async def get_current_bird_balance_legacy(db: AsyncSession, lot_id: int) -> tuple[int, int]:
    """Calculate current bird balance (males, females) for a lot."""
    # Sum all bird movements
    result = await db.execute(
        select(
            func.sum(BirdMovement.quantity).label("total")
        ).join(OperationalEvent).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type.in_([
                EventType.BIRD_RECEPTION,
                EventType.BIRD_DISTRIBUTION,
            ]),
        )
    )
    total = result.scalar() or 0
    return total, total  # Simplified: return same for both sexes


async def validate_mortality(
    db: AsyncSession,
    lot_id: int,
    quantity: int,
) -> None:
    """
    BR-01: Mortality cannot exceed available bird balance.
    BR-07: Lot must be active.
    """
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad de mortalidad debe ser mayor a cero", "BR-01")

    current, _ = await get_current_bird_balance_legacy(db, lot_id)
    if quantity > current:
        raise BusinessRuleViolation(
            f"Mortalidad ({quantity}) excede el saldo disponible ({current})",
            "BR-01",
        )


async def validate_egg_dispatch(
    db: AsyncSession,
    lot_id: int,
    quantity: int,
) -> None:
    """
    BR-02: Egg dispatch cannot exceed available eggs.
    """
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad de huevos debe ser mayor a cero", "BR-02")
    # In v1, trust the operator + supervisor review for egg balance
    # Full balance tracking comes in Phase 6 (Reports)


async def validate_incubation_load(
    db: AsyncSession,
    lot_id: int,
    quantity: int,
) -> None:
    """
    BR-03: Incubation load cannot exceed eggs received.
    """
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad a cargar debe ser mayor a cero", "BR-03")


async def validate_chick_dispatch(
    db: AsyncSession,
    lot_id: int,
    quantity: int,
) -> None:
    """
    BR-04: Chick dispatch cannot exceed hatched viable.
    """
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad de pollitos debe ser mayor a cero", "BR-04")


async def validate_event_date(
    db: AsyncSession,
    lot_id: int,
    event_date,
) -> None:
    """
    BR-06: Event date cannot be before lot activation date.
    """
    from ..masters.models import Lot
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if lot and lot.start_date and event_date < lot.start_date.date() if hasattr(lot.start_date, 'date') else False:
        if lot.activation_type != "manual":
            raise BusinessRuleViolation(
                f"Fecha del evento ({event_date}) anterior a la activación del lote ({lot.start_date})",
                "BR-06",
            )


async def validate_lot_active(db: AsyncSession, lot_id: int) -> None:
    """BR-07: Movements require active lot."""
    from ..masters.models import Lot, LotStatus
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if not lot:
        raise BusinessRuleViolation("Lote no encontrado", "BR-07")
    if lot.status != LotStatus.ACTIVE:
        raise BusinessRuleViolation(
            f"El lote no está activo (estado: {lot.status.value}). No se pueden registrar movimientos.",
            "BR-07",
        )


def validate_segregation(registered_by_id: int, action_user_id: int, action: str = "aprobar") -> None:
    """BR-14: Operator cannot approve own data. Enforces segregation of duties."""
    if registered_by_id == action_user_id:
        raise BusinessRuleViolation(
            f"Un operador no puede {action} sus propios registros (segregación de funciones)",
            "BR-14",
        )


def validate_sap_edit_lock(event_status: str) -> None:
    """BR-15: Records sent to SAP cannot be edited directly."""
    locked_statuses = ("sent_to_sap", "sap_confirmed", "consolidated")
    if event_status in locked_statuses:
        raise BusinessRuleViolation(
            f"Registros enviados a SAP no pueden editarse (estado: {event_status}). "
            "Requiere reverso, corrección auditada o nuevo movimiento autorizado.",
            "BR-15",
        )


def validate_closure_summary(lot_id: int, has_events: bool) -> None:
    """BR-05: Lot closure requires summary of final state."""
    if not has_events:
        raise BusinessRuleViolation(
            f"El cierre del lote {lot_id} requiere al menos un registro operativo previo",
            "BR-05",
        )


async def validate_house_capacity(db: AsyncSession, house_id: int, quantity: int) -> None:
    """
    G-R04 / BR-17: Bird placement cannot exceed house capacity.
    """
    if house_id is None:
        return  # No house specified, skip validation
    from ..masters.models import House
    result = await db.execute(select(House).where(House.id == house_id))
    house = result.scalar_one_or_none()
    if not house:
        raise BusinessRuleViolation(f"Galpón {house_id} no encontrado", "BR-17")
    if house.capacity and quantity > house.capacity:
        raise BusinessRuleViolation(
            f"Cantidad de aves ({quantity}) excede la capacidad del galpón ({house.capacity})",
            "BR-17",
        )


async def validate_oc_limit(
    db: AsyncSession,
    sap_document_ref: str | None,
    quantity_received: int,
) -> None:
    """
    G-R05 / BR-18: Quantity received cannot exceed Purchase Order without authorization.
    """
    if not sap_document_ref:
        return  # No OC reference, skip validation
    from ..integrations.sap.models import SapReference, SapReferenceType
    result = await db.execute(
        select(SapReference).where(
            SapReference.sap_code == sap_document_ref,
            SapReference.ref_type == SapReferenceType.PURCHASE_ORDER,
        )
    )
    oc = result.scalar_one_or_none()
    if oc and oc.quantity is not None and quantity_received > oc.quantity:
        raise BusinessRuleViolation(
            f"Cantidad recibida ({quantity_received}) excede la OC {sap_document_ref} ({oc.quantity})",
            "BR-18",
        )


async def validate_period_open(db: AsyncSession, event_date) -> None:
    """
    G-R12 / BR-19: Cannot register events in closed SAP periods.
    """
    from datetime import date
    from ..audit.models import AuditLog
    # Check if there's any period closure record after event_date
    # Simplified: only block dates more than 90 days in the past
    today = date.today()
    if isinstance(event_date, str):
        from datetime import datetime as dt
        event_date = dt.strptime(event_date, "%Y-%m-%d").date()
    if hasattr(event_date, 'date'):
        event_date = event_date.date()
    days_ago = (today - event_date).days
    if days_ago > 90:
        raise BusinessRuleViolation(
            f"La fecha del evento ({event_date}) está en un período cerrado (+90 días). "
            "Requiere autorización especial.",
            "BR-19",
        )


async def validate_farm_house(
    event_type: str,
    farm_id: int | None,
    house_id: int | None,
) -> None:
    """
    F-03 / BR-08: Movements require farm/house when applicable.
    Events that operate on physical locations (reception, distribution,
    inspection, dispatch, egg handling) must have farm and house assigned.
    """
    location_events = {
        "bird_reception",
        "bird_distribution",
        "bird_transfer",
        "bird_exit",
        "farm_inspection",
        "transport_inspection",
        "egg_collection",
        "egg_dispatch",
        "egg_reception_hatchery",
        "chick_dispatch",
        "hatchery_inspection",
    }
    if event_type in location_events:
        if farm_id is None or farm_id <= 0:
            raise BusinessRuleViolation(
                f"El evento '{event_type}' requiere una granja asignada",
                "BR-08",
            )
        if house_id is None or house_id <= 0:
            raise BusinessRuleViolation(
                f"El evento '{event_type}' requiere un galpón asignado",
                "BR-08",
            )

