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

async def _suma_neta(db: AsyncSession, lot_id: int, columna, columna_evento, tipos,
                     sexo: str | None = None) -> int:
    """Σ natural de los eventos del lote de esos tipos, **menos** las contrapartidas efectivas.

    `GA-REM-041 §3.4` · `OD-19 §3, §5`. El original revertido sigue sumando en su signo (la
    historia dice que ocurrió); su contrapartida —mismo tipo, mismas cantidades— resta
    exactamente lo mismo cuando es **efectiva** (`REVERSED`). Una contrapartida pendiente,
    rechazada o cancelada no cuenta: ni suma como movimiento (no lo es) ni resta todavía.
    No hay exclusión retroactiva: las dos filas están y las dos suman.
    """
    from .models import Reversal

    contrapartidas = select(Reversal.reversal_event_id).where(Reversal.reversal_event_id.is_not(None))
    base = (
        select(func.coalesce(func.sum(columna), 0))
        .join(OperationalEvent, columna_evento == OperationalEvent.id)
        .where(OperationalEvent.lot_id == lot_id, OperationalEvent.event_type.in_(list(tipos)))
    )
    if sexo is not None:  # `R-191`: saldo por sexo (misma semántica de contrapartidas)
        base = base.where(BirdMovement.sex == sexo)
    natural = (await db.execute(base.where(
        OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        OperationalEvent.id.not_in(contrapartidas),
    ))).scalar() or 0
    efectivas = (await db.execute(base.where(
        OperationalEvent.status == EventStatus.REVERSED,
        OperationalEvent.id.in_(contrapartidas),
    ))).scalar() or 0
    return int(natural) - int(efectivas)


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
    entradas = await _suma_neta(db, lot_id, BirdMovement.quantity, BirdMovement.event_id, in_types)
    salidas = await _suma_neta(db, lot_id, BirdMovement.quantity, BirdMovement.event_id, out_types)
    from ..lots.models import OpeningBalance

    apertura = await db.execute(
        select(
            func.coalesce(OpeningBalance.initial_male_count, 0)
            + func.coalesce(OpeningBalance.initial_female_count, 0)
        ).where(OpeningBalance.lot_id == lot_id)
    )

    return (apertura.scalar() or 0) + entradas - salidas


async def get_current_bird_balance_by_sex(db: AsyncSession, lot_id: int) -> tuple[int, int]:
    """Saldo vivo por sexo `(machos, hembras)` — `R-191` (poblaciones de una transición).

    Misma taxonomía, contrapartidas y apertura que `get_current_bird_balance`. Las filas
    `mixed` no se reparten (no se inventa): solo cuenta cada sexo declarado; un lote con
    filas mixtas sigue teniendo su saldo total en el helper original.
    """
    in_types = [EventType.BIRD_RECEPTION, EventType.BIRTH_REGISTRATION]
    out_types = [
        EventType.MORTALITY_RECORDING,
        EventType.CULL_RECORDING,
        EventType.BIRD_EXIT,
        EventType.CHICK_DISPATCH,
    ]
    from ..lots.models import OpeningBalance

    saldos = []
    for sexo in ("male", "female"):
        entradas = await _suma_neta(db, lot_id, BirdMovement.quantity,
                                    BirdMovement.event_id, in_types, sexo=sexo)
        salidas = await _suma_neta(db, lot_id, BirdMovement.quantity,
                                   BirdMovement.event_id, out_types, sexo=sexo)
        apertura = (await db.execute(
            select(func.coalesce(
                OpeningBalance.initial_male_count if sexo == "male" else OpeningBalance.initial_female_count,
                0,
            )).where(OpeningBalance.lot_id == lot_id)
        )).scalar() or 0
        saldos.append((apertura or 0) + entradas - salidas)
    return int(saldos[0]), int(saldos[1])


TIPO_DISPONIBLE = "fertile"


def cuenta_como_disponible(egg_type: str | None) -> bool:
    """`GA-REM-005-F` / `R-172` / `RR-17`: solo el huevo **fértil** es disponibilidad.

    Lo que se traslada a la incubadora es huevo fértil (`Bases` p.7-8 «Traslado de huevos
    fértiles»; p.9 «Número de Huevos Recibidos: cantidad de huevos fértiles recibidos»;
    `docs/02 §3.6.4/§3.7.1`; `spec.md :166/:187`). Sucios, rotos, infértiles, descartados y
    comerciales son hechos capturados —producción, roturas, indicadores— y no cuentan para
    despachar (`BR-02`) ni para cargar (`BR-03`): `CAPTURADO ≠ DISPONIBLE`. Un solo predicado,
    en un solo sitio, para los dos saldos; los dos saldos siguen siendo distintos.
    """
    return egg_type == TIPO_DISPONIBLE


def validate_egg_dispatch_types(egg_types) -> None:
    """`GA-REM-005-F` `AC-R172-04`: el despacho a incubadora solo lleva huevo fértil."""
    ajenos = sorted({t for t in egg_types if not cuenta_como_disponible(t)})
    if ajenos:
        raise BusinessRuleViolation(
            f"El despacho a incubadora es de huevo fértil; tipo(s) no despachable(s): {', '.join(str(t) for t in ajenos)}",
            "BR-02",
        )


async def get_egg_balance(db: AsyncSession, lot_id: int) -> int:
    """
    Fertile eggs available at the farm for dispatch.
    IN:  EGG_COLLECTION   (solo filas que cuentan como disponibles: `cuenta_como_disponible`)
    OUT: EGG_DISPATCH     (ídem; las filas históricas de otro tipo nunca fueron disponibilidad)

    `GA-REM-005-F` / `R-172`: hasta esta enmienda sumaba todas las `egg_type` y una recolección
    de 100 fértiles + 60 de otros tipos admitía despachar 160.
    """
    res_in = await db.execute(
        select(func.coalesce(func.sum(EggMovement.quantity), 0))
        .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.EGG_COLLECTION,
            EggMovement.egg_type == TIPO_DISPONIBLE,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    res_out = await db.execute(
        select(func.coalesce(func.sum(EggMovement.quantity), 0))
        .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.EGG_DISPATCH,
            EggMovement.egg_type == TIPO_DISPONIBLE,
            OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        )
    )
    return (res_in.scalar() or 0) - (res_out.scalar() or 0)


async def get_hatchery_egg_balance(db: AsyncSession, lot_id: int) -> int:
    """
    Eggs available at hatchery (received - loaded into incubators).
    IN:  EGG_RECEPTION_HATCHERY  (solo el fértil recibido: `Bases` p.9, `GA-REM-005-F`; las demás filas
                                  —diferencias vs enviado— se capturan y no cuentan)
    OUT: INCUBATION_LOAD (quantity_loaded from hatchery_params)
    """
    res_in = await db.execute(
        select(func.coalesce(func.sum(EggMovement.quantity), 0))
        .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.EGG_RECEPTION_HATCHERY,
            EggMovement.egg_type == TIPO_DISPONIBLE,
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
    OUT: CHICK_DISPATCH · MORTALITY_RECORDING · CULL_RECORDING (bird_movements)

    `GA-REM-005-B` / `R-130`: «viable» descontaba solo lo despachado, de modo que un lote con
    100 nacidos, 10 muertos y 5 descartados admitía despachar 100 y dejaba el saldo de aves en
    −15 pese a `BR-04`. Viable = nacidos − muertos − descartados − ya despachados, que es lo que
    «viable» significa (`Bases` p.9: sanos frente a débiles) y coincide con el saldo del lote.
    """
    nacidos = await _suma_neta(db, lot_id, BirdMovement.quantity, BirdMovement.event_id, [EventType.BIRTH_REGISTRATION])
    salidas = await _suma_neta(db, lot_id, BirdMovement.quantity, BirdMovement.event_id,
                               [EventType.CHICK_DISPATCH, EventType.MORTALITY_RECORDING, EventType.CULL_RECORDING])
    return nacidos - salidas


# ─── Business rule validators ─────────────────────────────────────────────────

async def bloquear_saldo_del_lote(db: AsyncSession, lot_id: int) -> None:
    """`GA-REM-005-B` / `R-130` `AC-R130-10`: serializa los decrementos de un mismo lote.

    El saldo se calcula leyendo eventos y la sesión es por petición (`READ COMMITTED`): dos
    decrementos concurrentes leían el mismo saldo y se aprobaban ambos. `SELECT … FOR UPDATE`
    sobre la fila del lote hace que el segundo espere a que el primero confirme y lea el
    saldo ya reducido. El bloqueo vive lo que la transacción de la petición
    (`RutaTransaccional`) y solo toca la fila de **ese** lote: sin cadena de bloqueos, sin
    interbloqueo posible.
    """
    from ..masters.models import Lot
    await db.execute(select(Lot.id).where(Lot.id == lot_id).with_for_update())


async def validate_bird_decrement(
    db: AsyncSession, lot_id: int, quantity: int, etiqueta: str
) -> None:
    """`BR-01` para toda salida humana del saldo de aves: mortalidad, descarte y salida.

    `GA-REM-005 E.3` enumera las cuatro salidas del saldo y hasta `R-130` solo la mortalidad
    se validaba contra él: un descarte o una salida a planta mayor que el saldo se registraba
    y `get_current_bird_balance` quedaba negativo. La regla es una sola, en un solo sitio:
    cantidad > 0 y cantidad ≤ saldo, leído bajo el bloqueo de la fila del lote.
    """
    if quantity <= 0:
        raise BusinessRuleViolation(
            f"La cantidad de {etiqueta} debe ser mayor a cero", "BR-01"
        )
    await bloquear_saldo_del_lote(db, lot_id)
    balance = await get_current_bird_balance(db, lot_id)
    if quantity > balance:
        raise BusinessRuleViolation(
            f"{etiqueta.capitalize()} ({quantity}) excede el saldo de aves disponibles ({balance})",
            "BR-01",
        )


async def validate_mortality(db: AsyncSession, lot_id: int, quantity: int) -> None:
    """BR-01: Mortality cannot exceed available bird balance."""
    await validate_bird_decrement(db, lot_id, quantity, "mortalidad")


async def validate_egg_dispatch(db: AsyncSession, lot_id: int, quantity: int) -> None:
    """BR-02: Egg dispatch cannot exceed available egg balance.

    `GA-REM-005-D` / `R-161`: el saldo se lee **bajo el bloqueo de la fila del lote**, como
    el de aves (`validate_bird_decrement`): dos despachos concurrentes leían el mismo saldo y
    ambos confirmaban. Bloquear antes de leer hace que el segundo espere y lea el saldo ya
    reducido. Cantidad > 0: el servicio ya no salta esta regla con cantidad 0.
    """
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad de huevos debe ser mayor a cero", "BR-02")
    await bloquear_saldo_del_lote(db, lot_id)
    balance = await get_egg_balance(db, lot_id)
    if quantity > balance:
        raise BusinessRuleViolation(
            f"Despacho de huevos ({quantity}) excede el saldo disponible ({balance}). "
            "Registre primero la recolección.",
            "BR-02",
        )


async def validate_incubation_load(db: AsyncSession, lot_id: int, quantity: int) -> None:
    """BR-03: Incubation load cannot exceed eggs received at hatchery.

    `GA-REM-005-D` / `R-161`: misma primitiva que `BR-02` — bloqueo de la fila del lote antes de
    leer los huevos disponibles en incubadora.
    """
    if quantity <= 0:
        raise BusinessRuleViolation("La cantidad a cargar debe ser mayor a cero", "BR-03")
    await bloquear_saldo_del_lote(db, lot_id)
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
    await bloquear_saldo_del_lote(db, lot_id)
    balance = await get_viable_chick_balance(db, lot_id)
    if quantity > balance:
        raise BusinessRuleViolation(
            f"Despacho de pollitos ({quantity}) excede los pollitos viables disponibles ({balance}). "
            "Registre primero el nacimiento.",
            "BR-04",
        )


# ─── `GA-REM-005-E` · `R-173` · mutaciones posteriores al alta ───────────────────────────
#
# Los cuatro saldos son agregados dinámicos por `lot_id` y `status ≠ CANCELLED`: cambiar el lote
# de un evento mueve su efecto entero y cancelar una entrada lo resta. El invariante `saldo ≥ 0`
# (`B.2`, `D.1.4`) gobierna esas dos mutaciones igual que al alta (`RR-18`).

ENTRADAS_DE_SALDO = frozenset({EventType.BIRD_RECEPTION, EventType.BIRTH_REGISTRATION,
                               EventType.EGG_COLLECTION, EventType.EGG_RECEPTION_HATCHERY})
SALIDAS_DE_SALDO = frozenset({EventType.MORTALITY_RECORDING, EventType.CULL_RECORDING, EventType.BIRD_EXIT,
                              EventType.CHICK_DISPATCH, EventType.EGG_DISPATCH, EventType.INCUBATION_LOAD})


def tiene_efecto_en_saldo(event_type) -> bool:
    return event_type in ENTRADAS_DE_SALDO or event_type in SALIDAS_DE_SALDO


def efecto_persistido(event) -> int:
    """`n` del evento, derivado de sus filas persistidas; el cliente nunca lo aporta (`§E.2.5`)."""
    if event.event_type == EventType.INCUBATION_LOAD:
        return sum(hp.quantity_loaded or 0 for hp in event.hatchery_params)
    if event.event_type in (EventType.EGG_COLLECTION, EventType.EGG_DISPATCH, EventType.EGG_RECEPTION_HATCHERY):
        return sum(em.quantity for em in event.egg_movements if cuenta_como_disponible(em.egg_type))
    return sum(bm.quantity for bm in event.bird_movements)


async def bloquear_saldos_de_lotes(db: AsyncSession, *lot_ids) -> None:
    """Las filas de los lotes implicados, en orden ascendente de clave primaria (`§E.2.11`).

    Una sola convención para todos los escritores: sin interbloqueo A→B/B→A. Los validadores
    del alta vuelven a bloquear el destino dentro de la misma transacción (reentrante).
    """
    for lot_id in sorted({lote for lote in lot_ids if lote is not None}):
        await bloquear_saldo_del_lote(db, lot_id)


async def validate_retiro_de_entrada(db: AsyncSession, event, n: int, motivo: str) -> None:
    """La entrada deja de contar en su lote (anulación o reasignación): el lote queda `≥ 0`.

    Se lee **bajo el bloqueo** ya tomado por quien llama. Familia por tipo de evento; para el
    nacimiento se comprueban viables (`BR-04`) y aves (`BR-01`).
    """
    lot_id = event.lot_id
    reglas = {
        EventType.BIRD_RECEPTION: [("aves", "BR-01", get_current_bird_balance)],
        EventType.BIRTH_REGISTRATION: [("pollitos viables", "BR-04", get_viable_chick_balance), ("aves", "BR-01", get_current_bird_balance)],
        EventType.EGG_COLLECTION: [("huevos", "BR-02", get_egg_balance)],
        EventType.EGG_RECEPTION_HATCHERY: [("huevos en incubadora", "BR-03", get_hatchery_egg_balance)],
    }
    for etiqueta, regla, saldo_de in reglas.get(event.event_type, []):
        saldo = await saldo_de(db, lot_id)
        if saldo - n < 0:
            raise BusinessRuleViolation(
                f"{motivo} dejaría el saldo de {etiqueta} del lote en {saldo - n} (saldo {saldo}, entrada {n})", regla,
            )


async def validate_salida_en_destino(db: AsyncSession, event, n: int, lote_destino: int) -> None:
    """La salida reasignada se valida en el destino **como un alta** (`AC-W09`, `B.2`): mismo validador."""
    tipo = event.event_type
    if tipo == EventType.MORTALITY_RECORDING:
        await validate_mortality(db, lote_destino, n)
    elif tipo in (EventType.CULL_RECORDING, EventType.BIRD_EXIT):
        await validate_bird_decrement(db, lote_destino, n, "descarte" if tipo == EventType.CULL_RECORDING else "salida")
    elif tipo == EventType.CHICK_DISPATCH:
        await validate_chick_dispatch(db, lote_destino, n)
    elif tipo == EventType.EGG_DISPATCH:
        await validate_egg_dispatch(db, lote_destino, n)
    elif tipo == EventType.INCUBATION_LOAD:
        await validate_incubation_load(db, lote_destino, n)


async def validate_lot_closure(db: AsyncSession, lot_id: int) -> None:
    """
    BR-05: Lot closure requires at least one weight_recording AND one feed_registration.
    Without these, FCR and final weight cannot be computed.

    `R-192` · `OD-19 §3.3`: un pesaje o alimento con el par `REVERSED` **no está vigente**
    — su efecto neto es cero y no puede ser la base del FCR/peso final.
    """
    has_weight = await db.execute(
        select(OperationalEvent.id).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type == EventType.WEIGHT_RECORDING,
            OperationalEvent.status.not_in([EventStatus.CANCELLED, EventStatus.REVERSED]),
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
            OperationalEvent.status.not_in([EventStatus.CANCELLED, EventStatus.REVERSED]),
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

    **`reversed` cuenta como decidido** (`R-192` · `OD-19 §6`): el par original+contrapartida
    se decide por el motor de aprobación; `REVERSED` es terminal y no admite acción, luego
    bloquear por él dejaría el lote cerrable solo por intervención en datos.

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
                (*ESTADOS_APROBADOS, EventStatus.CANCELLED, EventStatus.REVERSED)
            ),
        )
        .group_by(OperationalEvent.status)
    )
    if company_id is not None:
        consulta = consulta.where(OperationalEvent.company_id == company_id)

    pendientes = (await db.execute(consulta)).all()
    if not pendientes:
        return

    # `R-192` · `C-07` (`OD-19 §6`): cuando lo vivo son **contrapartidas de reverso**, el
    # detalle lo dice: la acción posible no es «aprobar el registro» sino decidir el reverso.
    from .models import Reversal

    vivos = (*ESTADOS_APROBADOS, EventStatus.CANCELLED, EventStatus.REVERSED)
    cuenta_reversos = (
        select(func.count(OperationalEvent.id))
        .join(Reversal, Reversal.reversal_event_id == OperationalEvent.id)
        .where(OperationalEvent.lot_id == lot_id, OperationalEvent.status.not_in(vivos))
    )
    if company_id is not None:
        cuenta_reversos = cuenta_reversos.where(OperationalEvent.company_id == company_id)
    reversos_pendientes = (await db.execute(cuenta_reversos)).scalar() or 0

    total = sum(n for _, n in pendientes)
    detalle = ", ".join(f"{n} en «{estado.value}»" for estado, n in pendientes)
    aviso = ""
    if reversos_pendientes:
        aviso = (
            f" {reversos_pendientes} reverso pendiente de decisión."
            if reversos_pendientes == 1
            else f" {reversos_pendientes} reversos pendientes de decisión."
        )
    raise BusinessRuleViolation(
        f"No se puede cerrar el lote: {total} registro(s) sin aprobar ({detalle}).{aviso} "
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


#: `GA-REM-021-A` · `B05`: etapas del cliente que exigen el consumo de agua (`Bases` p.2, 4, 12).
UNIDADES_CON_CONSUMO_DE_AGUA = {"breeder", "broiler"}


def validate_reception_reconciliation(event_type, bird_type, received_total, dead_on_arrival, rejected_on_arrival, alojadas: int) -> None:
    """`GA-REM-021` enmienda B · `B01` · `RR-12` · `BR-20` (`Recomendación central §6`).

    Recepción de reproductoras: `recibidas == alojadas + muertas al arribo + rechazadas`, con los tres
    datos declarados explícitamente (la ausencia no es `0`) y sin tolerancia. Las **alojadas** las
    calcula el servidor (Σ `bird_movements.quantity`): nunca vienen del cuerpo. Engorde declara solo la
    mortalidad inicial (`spec.md §4.8`); ningún otro tipo de evento ni otra cadena lleva estos datos.
    """
    tipo = getattr(event_type, "value", event_type)
    cadena = getattr(bird_type, "value", bird_type)
    declarados = [n for n, v in (("received_total", received_total), ("dead_on_arrival", dead_on_arrival),
                                 ("rejected_on_arrival", rejected_on_arrival)) if v is not None]
    if tipo != EventType.BIRD_RECEPTION.value:
        if declarados:
            raise BusinessRuleViolation(
                f"{', '.join(declarados)} solo se registra en una recepción de aves", "BR-20")
        return
    if cadena == "breeder":
        faltan = [n for n, v in (("received_total", received_total), ("dead_on_arrival", dead_on_arrival),
                                 ("rejected_on_arrival", rejected_on_arrival)) if v is None]
        if faltan:
            raise BusinessRuleViolation(
                "La recepción de reproductoras declara recibidas, mortalidad al arribo y rechazo "
                f"(falta: {', '.join(faltan)})", "BR-20")
        suma = alojadas + dead_on_arrival + rejected_on_arrival
        if received_total != suma:
            raise BusinessRuleViolation(
                f"El cuadre de la recepción no cierra: recibidas {received_total} ≠ alojadas {alojadas} + "
                f"mortalidad al arribo {dead_on_arrival} + rechazo {rejected_on_arrival} = {suma}", "BR-20")
        return
    if cadena == "broiler":
        sobran = [n for n in declarados if n != "dead_on_arrival"]
        if sobran:
            raise BusinessRuleViolation(
                f"{', '.join(sobran)} solo se registra en la recepción de reproductoras (Rec. §6)", "BR-20")
        return
    if declarados:
        raise BusinessRuleViolation(
            f"{', '.join(declarados)} solo se registra en la recepción de reproductoras o de engorde", "BR-20")


def validate_birth_registration(event_type, bird_type, chicks_healthy, chicks_weak, filas) -> None:
    """`GA-REM-005` enmienda C (`R-170`, `RR-14`) + `GA-REM-021` enmienda C (`B13`, `RR-15`) · `BR-21`.

    Una sola contabilidad de nacimientos: los nacidos son Σ `quantity` de las filas, con una fila por
    sexo y `mixed` (sin sexar) excluyente con las filas sexadas; el total no se declara, se deriva.
    Sanos y débiles (`Bases` p.9) son atributos disjuntos de los nacidos: obligatorios y explícitos en
    el nacimiento de incubadora, `sanos + débiles ≤ nacidos`, y nunca un saldo. `filas` son pares
    `(sex, quantity)`; se aplica en el alta, la edición y la corrección.
    """
    tipo = getattr(event_type, "value", event_type)
    cadena = getattr(bird_type, "value", bird_type)
    declarados = [n for n, v in (("chicks_healthy", chicks_healthy), ("chicks_weak", chicks_weak)) if v is not None]
    if tipo != EventType.BIRTH_REGISTRATION.value:
        if declarados:
            raise BusinessRuleViolation(f"{', '.join(declarados)} solo se registra en un nacimiento", "BR-21")
        return
    sexos = [(s.value if hasattr(s, "value") else s) or "mixed" for s, _ in filas]
    nacidos = sum(int(q or 0) for _, q in filas)
    if nacidos < 1:
        raise BusinessRuleViolation("Un nacimiento declara al menos un pollito nacido", "BR-21")
    if len(sexos) != len(set(sexos)):
        raise BusinessRuleViolation(
            "Los nacidos se declaran con una sola fila por sexo (el total se deriva; no se repite como fila)", "BR-21")
    if "mixed" in sexos and len(sexos) > 1:
        raise BusinessRuleViolation(
            "Los nacidos sin sexar (mixed) no se combinan con filas sexadas: el total no es una fila más", "BR-21")
    if cadena != "hatchery":
        if declarados:
            raise BusinessRuleViolation(f"{', '.join(declarados)} solo se registra en la incubadora (Bases p.9)", "BR-21")
        return
    faltan = [n for n, v in (("chicks_healthy", chicks_healthy), ("chicks_weak", chicks_weak)) if v is None]
    if faltan:
        raise BusinessRuleViolation(
            f"El nacimiento declara los pollitos sanos y los débiles (falta: {', '.join(faltan)})", "BR-21")
    if chicks_healthy + chicks_weak > nacidos:
        raise BusinessRuleViolation(
            f"Sanos {chicks_healthy} + débiles {chicks_weak} = {chicks_healthy + chicks_weak} superan los nacidos {nacidos}", "BR-21")


CLASES_DE_ADJUNTO_DE_IMPORTACION = ("sanitary_document", "import_permit", "customs_document", "vaccination_certificate", "origin_certificate")
CLASES_DE_ADJUNTO = ("photo", "document", "signature", "audio") + CLASES_DE_ADJUNTO_DE_IMPORTACION


def _cadena(bird_type) -> str | None:
    return getattr(bird_type, "value", bird_type) if bird_type is not None else None


def validate_import_plan(event_type, bird_type, plan, filas, sap_document_ref, supplier_id) -> None:
    """`GA-REM-042` · `R-152` · `BR-22` · `RR-19`: el plan de importación de abuelas (`docs/02 §3.4.1`).

    Solo sobre un lote de Progenitoras (`spec.md §4.4`: `grandparent_import` es un evento exclusivo de esa
    unidad). El plan viaja en `extra_data["import_plan"]` con tipo (`PlanDeImportacion`) y sus identidades
    son exactas y sin tolerancia, como el cuadre de `RR-12`: `embarcada = recibida + mortalidad en traslado`,
    `recibida = Σ ♂/♀`, `llegada ≥ salida`, `fin de cuarentena ≥ llegada`. La OC y el proveedor se declaran.
    Comprada frente a embarcada **no** se regula (`OD-04`: entregas parciales). Es un evento documental: no
    puebla el lote ni acumula contra la OC (la población y `BR-18` siguen en `bird_reception`).
    """
    tipo = getattr(event_type, "value", event_type)
    if tipo != EventType.GRANDPARENT_IMPORT.value:
        return
    if _cadena(bird_type) != "grandparent":
        raise BusinessRuleViolation("La importación de abuelas solo se registra sobre un lote de Progenitoras", "BR-22")
    if not isinstance(plan, dict) or not plan:
        raise BusinessRuleViolation("El plan de importación es obligatorio (país, cantidades comprada, embarcada y recibida, mortalidad en traslado, fechas)", "BR-22")
    from pydantic import ValidationError

    from .schemas import PlanDeImportacion

    try:
        p = PlanDeImportacion.model_validate(plan)
    except ValidationError as exc:
        detalle = "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors()[:6])
        raise BusinessRuleViolation(f"Plan de importación inválido: {detalle}", "BR-22") from None
    if not sap_document_ref:
        raise BusinessRuleViolation("La importación de abuelas declara la orden de compra SAP", "BR-22")
    if supplier_id is None:
        raise BusinessRuleViolation("La importación de abuelas declara el proveedor internacional", "BR-22")
    if not filas:
        raise BusinessRuleViolation("La importación de abuelas declara las aves recibidas por sexo (machos y hembras)", "BR-22")
    recibidas = sum(int(q or 0) for _, q in filas)
    if p.received_total != recibidas:
        raise BusinessRuleViolation(
            f"La cantidad recibida ({p.received_total}) no cuadra con las aves recibidas por sexo ({recibidas})", "BR-22")
    if p.shipped_total != p.received_total + p.transit_mortality:
        raise BusinessRuleViolation(
            f"La cantidad embarcada ({p.shipped_total}) no cuadra con recibida {p.received_total} + mortalidad en traslado "
            f"{p.transit_mortality} = {p.received_total + p.transit_mortality}", "BR-22")
    if p.arrival_date < p.departure_date:
        raise BusinessRuleViolation(f"La fecha de llegada ({p.arrival_date}) es anterior a la de salida ({p.departure_date})", "BR-22")
    if p.quarantine_end_date is not None and p.quarantine_end_date < p.arrival_date:
        raise BusinessRuleViolation(f"El fin de la cuarentena ({p.quarantine_end_date}) es anterior a la llegada ({p.arrival_date})", "BR-22")


def validate_water_consumption(event_type, water_liters, bird_type) -> None:
    """`GA-REM-021` enmienda A · `B05` · `RR-10` (litros) · `RR-11` (> 0).

    Un dato, un registro: `water_liters` solo viaja en `water_consumption`, es obligatorio allí,
    estrictamente positivo (la ausencia de dato es ausencia, nunca `0`) y solo se registra sobre
    lotes de Reproductoras o Engorde; Incubadora no lo pide y Progenitoras no es etapa del
    documento del cliente. Se aplica en el alta, la edición y la corrección.
    """
    tipo = getattr(event_type, "value", event_type)
    if tipo == EventType.WATER_CONSUMPTION.value:
        if water_liters is None:
            raise BusinessRuleViolation("El consumo de agua requiere `water_liters` (litros)", "B05")
        if water_liters <= 0:
            raise BusinessRuleViolation("El consumo de agua debe ser mayor que cero (RR-11)", "RR-11")
        cadena = getattr(bird_type, "value", bird_type)
        if cadena not in UNIDADES_CON_CONSUMO_DE_AGUA:
            raise BusinessRuleViolation(
                "El consumo de agua solo se registra en Reproductoras y Engorde (Bases p.2/4/12)", "B05")
    elif water_liters is not None:
        raise BusinessRuleViolation("`water_liters` solo se registra en un evento de consumo de agua", "B05")


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

    Qué cuenta para el acumulado sigue el precedente de `_suma_neta` (`OD-19`): la suma es
    **neta**. El original revertido sigue contando en su signo (la historia dice que ocurrió)
    y su contrapartida efectiva resta exactamente lo mismo: por eso basta excluir `REVERSED`
    —ambos miembros del par comparten estado— y, además, toda contrapartida
    (`id ∈ reversals.reversal_event_id`): una contrapartida pendiente o rechazada **no es**
    una recepción y no puede sumar. El original mientras no sea `REVERSED` sí cuenta: la
    entrega ocurrió hasta que el reverso sea efectivo (`OD-19 §2`).

    Sin tolerancia: ninguna fuente normativa la establece. Y sin cierre automático de la
    orden: `OD-04` respondió si caben entregas parciales, no qué ocurre al completarla.
    """
    if not sap_document_ref:
        return
    from ..integrations.sap.models import SapReference, SapReferenceType
    from .models import Reversal

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
            OperationalEvent.status.not_in([EventStatus.CANCELLED, EventStatus.REVERSED]),
            # `R-193` · `OD-19 §2`: una contrapartida —pendiente o rechazada— no es una
            # recepción; solo suma el original vigente, y el par efectivo ya queda fuera
            # por estado.
            OperationalEvent.id.not_in(
                select(Reversal.reversal_event_id).where(
                    Reversal.reversal_event_id.is_not(None))),
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

