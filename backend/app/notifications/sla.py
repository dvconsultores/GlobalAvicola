"""«Registro pendiente de revisión > 24h» — `GA-REM-038` enmienda A, `AC-T01`…`AC-T04`.

El umbral **está en el nombre del evento** (`docs/02 §3.14`), de modo que no hace falta
decidirlo: son 24 horas. Lo que sí hubo que resolver es desde cuándo se cuentan.

    updated_at   NO sirve: cambia con cualquier edición posterior, y un evento tocado a las
                 23 horas reiniciaría su cuenta y no avisaría nunca.
    AuditLog     SÍ: guarda la transición a `pending_review` con su instante exacto.

Leer la auditoría para computar una condición no es convertirla en bandeja —eso sería
escribir avisos en ella—: es consultar historia, que es para lo que existe.

**La recurrencia no está definida en ninguna fuente.** Se emite **una vez** por evento y
destinatario. Inventar una repetición diaria añadiría ruido que nadie pidió; queda registrado
como hueco de requisito en `P14_NOTIFICATION_EVENT_MATRIX.md §6`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

#: `docs/02 §3.14`: «Registro pendiente de revisión **> 24h**». No es un parámetro nuestro.
HORAS_DE_REVISION = 24

REVIEW_PENDING = "review_pending_24h"


async def eventos_vencidos(db: AsyncSession, ahora: datetime | None = None):
    """Eventos que llevan más de 24 h en `pending_review`, con su instante de entrada.

    La condición es objetiva y se computa entera en la base: no depende de que nadie mire.
    """
    from ..audit.models import AuditLog
    from ..operations.models import EventStatus, OperationalEvent

    referencia = ahora or datetime.now(timezone.utc)
    limite = referencia - timedelta(hours=HORAS_DE_REVISION)

    # El instante en que **este** evento entró en revisión. Si volvió a entrar tras una
    # devolución, manda la última vez: la cuenta se reinicia con la nueva espera, no con la
    # primera de todas.
    entrada = (
        select(
            AuditLog.entity_id.label("entity_id"),
            func.max(AuditLog.created_at).label("desde"),
        )
        .where(AuditLog.entity_type == "operational_event",
               AuditLog.new_state == "pending_review")
        .group_by(AuditLog.entity_id)
        .subquery()
    )

    return (await db.execute(
        select(OperationalEvent, entrada.c.desde)
        .join(entrada, entrada.c.entity_id == func.cast(OperationalEvent.id, AuditLog.entity_id.type))
        .where(OperationalEvent.status == EventStatus.PENDING_REVIEW,
               entrada.c.desde < limite)
    )).all()


async def evaluar_revisiones_vencidas(
    db: AsyncSession, ahora: datetime | None = None
) -> int:
    """Crea los avisos que correspondan y devuelve cuántos. Idempotente.

    Reevaluar no duplica: `crear_notificacion` compara contra los avisos **sin leer** del mismo
    evento y destinatario. Si alguien ya fue avisado y no lo ha leído, el problema sigue siendo
    el mismo y no se anuncia otra vez.
    """
    from .recipients import resolver_destinatarios
    from .service import crear_notificacion

    creados = 0
    for evento, desde in await eventos_vencidos(db, ahora):
        destinatarios = await resolver_destinatarios(
            db,
            company_id=evento.company_id,
            originadores=[evento.registered_by_id],
        )
        for user_id in destinatarios:
            aviso = await crear_notificacion(
                db,
                company_id=evento.company_id,
                recipient_user_id=user_id,
                notification_type=REVIEW_PENDING,
                payload={
                    "event_type": str(getattr(evento.event_type, "value",
                                              evento.event_type)),
                    "lot_id": evento.lot_id,
                    "pending_since": desde.isoformat() if desde else None,
                    "threshold_hours": HORAS_DE_REVISION,
                },
                related_entity_type="operational_event",
                related_entity_id=evento.id,
                evitar_duplicado_sin_leer=True,
            )
            if aviso is not None:
                creados += 1
    return creados


async def vigilar_revisiones_pendientes(cada_segundos: int) -> None:
    """Evalúa la condición periódicamente. `AC-T02`.

    Vive aquí y no en `app/main.py` por dos razones. La primera es de sitio: el arranque de la
    aplicación no debe contener lógica de notificaciones. La segunda la impuso una guarda del
    proyecto —`R-26`— que prohíbe `except Exception` en `main.py`, porque el contrato de error
    no puede apoyarse en una captura genérica. Aquí sí procede: un fallo al evaluar no puede
    tumbar la aplicación, y el siguiente ciclo lo reintenta.

    Es una tarea del propio proceso, no un planificador externo: `docs/02 §3.14` pide el
    aviso, no una arquitectura. Y la evaluación es idempotente, así que varios trabajadores
    mirándola a la vez no duplican nada.
    """
    import asyncio
    import logging

    from ..database import async_session

    registro = logging.getLogger(__name__)
    while True:
        await asyncio.sleep(cada_segundos)
        try:
            async with async_session() as sesion:
                creados = await evaluar_revisiones_vencidas(sesion)
                await sesion.commit()
            if creados:
                registro.info("Avisos de revisión pendiente creados: %s", creados)
        except Exception:  # noqa: BLE001
            registro.exception("Fallo evaluando revisiones pendientes")
