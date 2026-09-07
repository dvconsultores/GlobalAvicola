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
            area_id=await _area_del_lote(db, evento.lot_id),
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


async def _area_del_lote(db: AsyncSession, lot_id) -> int | None:
    """El área funcional del lote, o `None` si no la tiene o el evento no tiene lote.

    `GA-REM-039`: los seis avisos de `P-14` convergen en el lote para resolver su área. Sin
    ella no hay gerente ni supervisor a quien avisar, y eso no es un error: las inspecciones
    de granja tienen `lot_id` nulo desde `i9j0k1l2m3n4`.
    """
    if lot_id is None:
        return None
    from ..masters.models import Lot

    return (await db.execute(select(Lot.area_id).where(Lot.id == lot_id))).scalar_one_or_none()


#: `OD-08`: «faltan 3 días calendario para la fecha prevista de cierre». No es un parámetro
#: nuestro y no se deriva de la genética, ni de una edad fija, ni de la duración de fase.
DIAS_PARA_CIERRE = 3

LOT_NEAR_CLOSE = "lot_near_close"


async def evaluar_lotes_proximos_a_cierre(
    db: AsyncSession, hoy: "date | None" = None
) -> int:
    """Avisa de los lotes que entran en la ventana de cierre. `AC-C05`…`AC-C14`.

    La condición es una **ventana** y no una igualdad:

        0 <= días hasta la fecha prevista <= 3

    Con `== 3` el aviso solo saldría si esto corriera exactamente ese día; con el sistema
    apagado no saldría nunca, y un aviso que no sale es un aviso que no existe. La ventana lo
    detecta cuando vuelva a correr.

    No se avisa si la fecha prevista ya pasó —ya no significa «próximo»—, si el lote está
    cerrado, o si no hay fecha prevista: sin referencia no se inventa ninguna.

    La comparación es día de calendario contra día de calendario, con la convención que `R-75`
    fijó para las fechas de negocio del lote. `R-80` describe otra cosa —mezclar un instante
    UTC con un día local— y no interviene.
    """
    from datetime import date as _date

    from ..masters.models import Lot
    from .recipients import resolver_destinatarios
    from .service import LOT_NEAR_CLOSE as TIPO, crear_notificacion

    referencia = hoy or _date.today()

    lotes = (await db.execute(
        select(Lot).where(
            Lot.planned_close_date.isnot(None),
            Lot.status == "active",
        )
    )).scalars().all()

    creados = 0
    for lote in lotes:
        prevista = lote.planned_close_date
        dia = prevista.date() if hasattr(prevista, "date") else prevista
        faltan = (dia - referencia).days
        if not (0 <= faltan <= DIAS_PARA_CIERRE):
            continue

        # La ocurrencia se ata a la **fecha prevista**, no solo al lote: una replanificación
        # real es una situación nueva y merece aviso nuevo, mientras que reevaluar la misma
        # no debe repetirlo.
        ocurrencia = f"lot:{lote.id}:{dia.isoformat()}"

        destinatarios = await resolver_destinatarios(
            db,
            company_id=lote.company_id,
            area_id=lote.area_id,
            # Quien registró el lote, tomado del rastro de auditoría del alta. No de quien
            # ejecuta esto: el evaluador corre sin sesión de nadie.
            originadores=[await _quien_registro_el_lote(db, lote.id)],
        )
        for user_id in destinatarios:
            aviso = await crear_notificacion(
                db,
                company_id=lote.company_id,
                recipient_user_id=user_id,
                notification_type=TIPO,
                payload={
                    "lot_id": lote.id,
                    "lot_code": lote.lot_code,
                    "planned_close_date": dia.isoformat(),
                    "days_remaining": faltan,
                },
                related_entity_type="lot",
                related_entity_id=lote.id,
                ocurrencia=ocurrencia,
            )
            if aviso is not None:
                creados += 1
    return creados


async def _quien_registro_el_lote(db: AsyncSession, lot_id: int) -> int | None:
    """Quién dio de alta el lote, según la auditoría.

    `Lot` no guarda un campo de originador, pero el alta **sí** deja rastro: `create_lot`
    emite un `AuditLog` con `AuditAction.CREATED` y el usuario que la ejecutó. Ése es el dato
    persistido, y usarlo evita duplicar en una columna algo que ya está guardado.

    Es el mismo criterio que el aviso de las 24 horas: la auditoría es historia, y consultarla
    para computar una condición no la convierte en bandeja.
    """
    from ..audit.models import AuditAction, AuditLog

    return (await db.execute(
        select(AuditLog.user_id)
        .where(AuditLog.entity_type == "lot",
               AuditLog.entity_id == str(lot_id),
               AuditLog.action == AuditAction.CREATED)
        .order_by(AuditLog.created_at.asc())
        .limit(1)
    )).scalar_one_or_none()


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
                # Las dos condiciones temporales de `docs/02 §3.14` comparten evaluador: no
                # hacen falta dos tareas para mirar dos cosas cada hora.
                creados = await evaluar_revisiones_vencidas(sesion)
                creados += await evaluar_lotes_proximos_a_cierre(sesion)
                await sesion.commit()
            if creados:
                registro.info("Avisos temporales creados: %s", creados)
        except Exception:  # noqa: BLE001
            registro.exception("Fallo evaluando revisiones pendientes")
