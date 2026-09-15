"""GA-REQ-061 · T14 · C5 — fotografía post-cutover por lote (motor operacional).

Solo cuentan los eventos con `event_date` **estrictamente posterior** a la fecha
civil del corte. El histórico anterior vive en el Opening (`R-67`); restarlo otra
vez sería el doble descuento que `docs/02 §3.9.2` prohíbe (golden: 9.965, nunca
9.465).

Semántica de contrapartidas idéntica a `_suma_neta` (`GA-REM-041 §3.4`): el
original revertido sigue sumando en su signo; su contrapartida **efectiva**
(`REVERSED`) resta exactamente lo mismo. Una contrapartida pendiente, rechazada
o cancelada no cuenta.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..operations.models import (
    BirdMovement,
    EventStatus,
    EventType,
    FeedMovement,
    OperationalEvent,
    Reversal,
)

#: Taxonomía `R-67`/`RR-08` (los mismos tipos que el saldo canónico).
ENTRADAS = (EventType.BIRD_RECEPTION, EventType.BIRTH_REGISTRATION)
SALIDAS = (
    EventType.MORTALITY_RECORDING,
    EventType.CULL_RECORDING,
    EventType.BIRD_EXIT,
    EventType.CHICK_DISPATCH,
)


async def suma_post_corte(
    db: AsyncSession,
    lot_id: int,
    columna,
    columna_evento,
    tipos,
    corte: date,
) -> float:
    """Σ neta post-cutover de los tipos dados (`event_date > corte`), con contrapartidas."""
    contrapartidas = select(Reversal.reversal_event_id).where(
        Reversal.reversal_event_id.is_not(None))
    base = (
        select(func.coalesce(func.sum(columna), 0))
        .join(OperationalEvent, columna_evento == OperationalEvent.id)
        .where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.event_type.in_(list(tipos)),
            OperationalEvent.event_date > corte,
        )
    )
    natural = (await db.execute(base.where(
        OperationalEvent.status.not_in([EventStatus.CANCELLED]),
        OperationalEvent.id.not_in(contrapartidas),
    ))).scalar() or 0
    efectivas = (await db.execute(base.where(
        OperationalEvent.status == EventStatus.REVERSED,
        OperationalEvent.id.in_(contrapartidas),
    ))).scalar() or 0
    return float(natural) - float(efectivas)


async def post_corte_del_lote(db: AsyncSession, lot_id: int, corte: date) -> dict:
    """Salidas post-cutover del lote: mortalidad, descarte, salidas, kg de alimento."""
    return {
        "mortality": int(await suma_post_corte(
            db, lot_id, BirdMovement.quantity, BirdMovement.event_id,
            (EventType.MORTALITY_RECORDING,), corte)),
        "culls": int(await suma_post_corte(
            db, lot_id, BirdMovement.quantity, BirdMovement.event_id,
            (EventType.CULL_RECORDING,), corte)),
        "salidas": int(await suma_post_corte(
            db, lot_id, BirdMovement.quantity, BirdMovement.event_id, SALIDAS, corte)),
        "feed_kg": float(await suma_post_corte(
            db, lot_id, FeedMovement.quantity_kg, FeedMovement.event_id,
            (EventType.FEED_REGISTRATION,), corte)),
    }
