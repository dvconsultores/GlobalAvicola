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
    """Saldo vivo de aves del lote.

        SALDO = saldo de apertura + Σ(entradas) − Σ(salidas)

        Apertura : `initial_male_count` + `initial_female_count` del `OpeningBalance`
        Entradas : BIRD_RECEPTION, BIRTH_REGISTRATION
        Salidas  : MORTALITY_RECORDING, CULL_RECORDING, BIRD_EXIT, CHICK_DISPATCH
        Neutros  : BIRD_TRANSFER, BIRD_DISTRIBUTION  (intra-lote, `RR-02`)

    El saldo de apertura es `R-67`. Sin él, un lote incorporado con
    `POST /lots/activate-manual` tenía saldo 0 y `BR-01` rechazaba toda mortalidad,
    descarte y salida: quedaba inoperable. Y ese es justamente el mecanismo previsto para
    incorporar lotes ya en marcha cuando el sistema se instala en un cliente
    (`docs/02 §3.9`, prioridad «Crítica (para implantación)»).

    Los campos `accumulated_mortality_*` y `accumulated_culls_*` **no se restan**: son
    histórico previo a la implantación, capturado para continuidad de indicadores.
    Restarlos sería el doble conteo que `docs/02 §3.9.2` prohíbe. Resuelto como `RC-08`
    por evidencia de nivel 3, regla `RR-08` (`GA-REM-005`, enmienda `R-67`).
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
    from ..lots.models import OpeningBalance

    apertura = await db.execute(
        select(
            func.coalesce(OpeningBalance.initial_male_count, 0)
            + func.coalesce(OpeningBalance.initial_female_count, 0)
        ).where(OpeningBalance.lot_id == lot_id)
    )

    return (apertura.scalar() or 0) + (res_in.scalar() or 0) - (res_out.scalar() or 0)


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


#: `docs/12 §4`. Estados en los que un registro **ya fue aprobado**: la aprobación es el
#: séptimo del ciclo y todo lo posterior la presupone. `sap_error` entra aquí porque solo se
#: alcanza desde `sent_to_sap`, que solo se alcanza desde `consolidated`, que solo se alcanza
#: desde `approved`: un fallo de integración no vuelve el registro «sin aprobar».
#:
#: Se aparta del conjunto que usan los indicadores de `P-15` —que omite `sap_error`— y a
#: propósito: aquél cuenta eventos para mostrar; éste decide si algo está aprobado.
ESTADOS_APROBADOS = (
    EventStatus.APPROVED,
    EventStatus.CONSOLIDATED,
    EventStatus.SENT_TO_SAP,
    EventStatus.SAP_CONFIRMED,
    EventStatus.SAP_ERROR,
)


async def validate_lot_records_approved(
    db: AsyncSession, lot_id: int, company_id: int | None = None,
) -> None:
    """`docs/12 §6 R7`: un lote no puede cerrarse si tiene registros sin aprobar.

    `R-76`. La regla estaba escrita en la documentación del ciclo de revisión y no existía en
    el código: `close_lot` comprobaba que el lote estuviera activo y que `BR-05` se cumpliera,
    y nada más. Un lote podía cerrarse con todos sus eventos en `registered`.

    **Registro** es el `OperationalEvent` del lote: `docs/12 §4` se titula «Estados del
    registro operativo» y el documento entero trata de esa entidad. No se generaliza a otras
    tablas —correcciones y aprobaciones son artefactos del propio flujo, y los lotes de
    trazabilidad o las fases no tienen estado que aprobar—.

    **`cancelled` no cuenta**: un registro anulado no representa operación alguna, y es lo que
    excluyen los ocho saldos de este mismo fichero.

    **`rejected` sí cuenta**: no está aprobado. Y no atrapa el lote, porque `docs/12 §4`
    muestra que no es terminal — el operador lo reenvía corregido.

    Es una regla distinta de `BR-05`, con la que solo comparte el momento de ejecución: aquélla
    pregunta si hay base para el resumen final; ésta, si todo está aprobado.
    """
    consulta = (
        select(OperationalEvent.status, func.count(OperationalEvent.id))
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.status.not_in(
                (*ESTADOS_APROBADOS, EventStatus.CANCELLED)
            ),
        )
        .group_by(OperationalEvent.status)
    )
    if company_id is not None:
        consulta = consulta.where(OperationalEvent.company_id == company_id)

    pendientes = (await db.execute(consulta)).all()
    if not pendientes:
        return

    total = sum(n for _, n in pendientes)
    detalle = ", ".join(f"{n} en «{estado.value}»" for estado, n in pendientes)
    raise BusinessRuleViolation(
        f"No se puede cerrar el lote: {total} registro(s) sin aprobar ({detalle}). "
        "Apruébelos o anúlelos antes de cerrar.",
        "R7",
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


async def validate_lot_active(db: AsyncSession, lot_id: int, company_id: int | None = None) -> None:
    """BR-07: Movements require active lot, and the lot must belong to the caller.

    `R-42`: la consulta no filtraba por compañía. Como `create_event` fija
    `company_id = self.company_id` —la de quien pide— y el `lot_id` no se comprobaba, un
    usuario de la empresa A podía **registrar operaciones contra un lote de la empresa
    B**. El evento quedaba archivado bajo A pero ligado a un lote de B, y como el saldo de
    aves se calcula por `lot_id` sin filtro de compañía, contaminaba los balances de B.

    No era una fuga de lectura sino una **escritura entre inquilinos**, que es peor: los
    filtros de listado protegían la consulta y nadie comprobaba la referencia.

    `company_id` es opcional para no romper a los llamadores que aún no lo aportan; cuando
    llega, un lote ajeno se comporta como inexistente, que es lo que debe parecerle a
    quien no tiene derecho a verlo.
    """
    from ..masters.models import Lot, LotStatus
    consulta = select(Lot).where(Lot.id == lot_id)
    if company_id is not None:
        consulta = consulta.where(Lot.company_id == company_id)
    result = await db.execute(consulta)
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


async def validate_oc_limit(
    db: AsyncSession,
    sap_document_ref: str | None,
    quantity_received: int,
    company_id: int | None = None,
    exclude_event_id: int | None = None,
) -> None:
    """`G-R05` / `BR-18`. La cantidad **acumulada** no puede exceder la orden de compra.

    `OD-04`, resuelta por el propietario: *una misma orden de compra puede recibirse mediante
    múltiples entregas parciales*. De ahí que repetir la referencia no sea un error y que la
    protección recaiga sobre el acumulado.

    Antes se comparaba **solo la recepción en curso**, de modo que tres entregas de 400 contra
    una orden de 1000 pasaban las tres y sumaban 1200: el límite nunca llegó a comprobarse.

    Qué cuenta para el acumulado no se decide aquí por criterio. Los ocho saldos de este mismo
    fichero excluyen exactamente `CANCELLED` y nada más, y se sigue ese precedente. **No** se
    traslada la semántica de los indicadores de `P-15`, que solo cuentan lo aprobado: un
    control de recepción no puede esperar a la aprobación, porque si tres entregas sin aprobar
    suman más que la orden el exceso ya ocurrió físicamente.

    Sin tolerancia: ninguna fuente normativa la establece. Y sin cierre automático de la
    orden: `OD-04` respondió si caben entregas parciales, no qué ocurre al completarla.
    """
    if not sap_document_ref:
        return
    from ..integrations.sap.models import SapReference, SapReferenceType

    consulta = select(SapReference).where(
        SapReference.sap_code == sap_document_ref,
        SapReference.ref_type == SapReferenceType.PURCHASE_ORDER,
    )
    # La orden se busca **dentro de la compañía del actor**: una referencia ajena se comporta
    # como inexistente, en lugar de imponer su cantidad sobre una recepción que no le toca.
    if company_id is not None:
        consulta = consulta.where(SapReference.company_id == company_id)
    oc = (await db.execute(consulta)).scalar_one_or_none()
    if oc is None or oc.quantity is None:
        return

    acumulado_q = (
        select(func.coalesce(func.sum(BirdMovement.quantity), 0))
        .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.sap_document_ref == sap_document_ref,
            OperationalEvent.event_type == EventType.BIRD_RECEPTION,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    if company_id is not None:
        acumulado_q = acumulado_q.where(OperationalEvent.company_id == company_id)
    if exclude_event_id is not None:
        acumulado_q = acumulado_q.where(OperationalEvent.id != exclude_event_id)

    acumulado = int((await db.execute(acumulado_q)).scalar() or 0)
    total = acumulado + quantity_received
    if total > oc.quantity:
        raise BusinessRuleViolation(
            f"La recepción de {quantity_received} elevaría lo recibido contra la OC "
            f"{sap_document_ref} a {total}, por encima de las {int(oc.quantity)} ordenadas "
            f"(ya recibidas: {acumulado}).",
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
    # R-30: la comparación `> 90` dejaba pasar cualquier fecha futura, porque `days_ago`
    # se vuelve negativo. Un evento operativo que todavía no ha ocurrido no puede
    # registrarse. Se admite un día de holgura porque el servidor mide en su propia zona
    # horaria y un operador al este puede estar viviendo ya el día siguiente.
    if days_ago < -1:
        raise BusinessRuleViolation(
            f"La fecha del evento ({event_date}) es futura. "
            "Solo pueden registrarse operaciones ya ocurridas.",
            "BR-19",
        )


async def validate_farm_house(event_type: str, farm_id: int | None, house_id: int | None) -> None:
    """F-03 / BR-08: Movements require farm/house when applicable."""
    # Hatchery inspections are machine-scoped and can be recorded without lot/farm/house.
    if event_type == "hatchery_inspection":
        return

    location_events = {
        "bird_reception", "bird_distribution", "bird_transfer", "bird_exit",
        "farm_inspection", "transport_inspection", "egg_collection",
        "egg_dispatch", "egg_reception_hatchery", "chick_dispatch",
    }
    if event_type in location_events:
        if farm_id is None or farm_id <= 0:
            raise BusinessRuleViolation(f"El evento '{event_type}' requiere una granja asignada", "BR-08")
        if house_id is None or house_id <= 0:
            if event_type == "farm_inspection":
                raise BusinessRuleViolation("La inspección de granja requiere al menos un galpón", "BR-08")
            raise BusinessRuleViolation(f"El evento '{event_type}' requiere un galpón asignado", "BR-08")

