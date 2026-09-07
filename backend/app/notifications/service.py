"""Creación y lectura de notificaciones internas — `GA-REM-038` / `OD-07`.

Un único punto de creación. Repartir `INSERT` por los módulos que disparan avisos habría
hecho que cada uno decidiera por su cuenta la empresa, el destinatario y la forma del
`payload`, y con el tiempo discreparían.

No hay bus de eventos, ni cola, ni tarea en segundo plano: el canal es interno y la
arquitectura vigente basta. Introducir infraestructura externa sin requisito es exactamente lo
que este programa evita.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Notification

#: Los cinco tipos accionables. El sexto de `docs/02 §3.14` —«lote próximo a cierre»— no
#: figura: «próximo» no está definido en ninguna fuente y `OD-08` sigue abierta en esa mitad.
RECORD_REJECTED = "record_rejected"
SAP_SEND_FAILED = "sap_send_failed"
MORTALITY_OVER_THRESHOLD = "mortality_over_threshold"
WEIGHT_OUT_OF_STANDARD = "weight_out_of_standard"
REVIEW_PENDING_24H = "review_pending_24h"


async def crear_notificacion(
    db: AsyncSession,
    *,
    company_id: int,
    recipient_user_id: int,
    notification_type: str,
    payload: Optional[dict] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    evitar_duplicado_sin_leer: bool = False,
) -> Optional[Notification]:
    """Crea un aviso para una persona. Devuelve `None` si se omitió por duplicado.

    Va en la **misma transacción** que el evento del negocio: si aquél revierte, esto revierte
    con él. Una notificación de algo que no llegó a ocurrir es una mentira, y `GA-REM-026`
    ya fijó que la confirmación ocurre en la capa de ruta, con lo que las dos cosas salen o no
    salen juntas.

    `evitar_duplicado_sin_leer` sirve al envío SAP, que reintenta hasta tres veces: si el mismo
    problema sigue sin leerse, no se anuncia otra vez. La bandeja informa de problemas, no
    cuenta reintentos.
    """
    if evitar_duplicado_sin_leer:
        ya_avisado = (await db.execute(
            select(Notification.id).where(
                Notification.recipient_user_id == recipient_user_id,
                Notification.notification_type == notification_type,
                Notification.related_entity_type == related_entity_type,
                Notification.related_entity_id == related_entity_id,
                Notification.read_at.is_(None),
            ).limit(1)
        )).scalar_one_or_none()
        if ya_avisado is not None:
            return None

    aviso = Notification(
        company_id=company_id,
        recipient_user_id=recipient_user_id,
        notification_type=notification_type,
        payload=payload or {},
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(aviso)
    await db.flush()
    return aviso


async def usuarios_con_rol(
    db: AsyncSession, nombre_rol: str, company_id: int
) -> Sequence[int]:
    """Los usuarios activos de una empresa que tienen un rol, por su **nombre**.

    `docs/10 §6.2` nombra el destinatario así —«Notificar al rol "Analista SAP"»— y el rol
    existe: lo crea la migración `l2m3n4o5p6q7`. Se resuelve por nombre y no por id porque es
    lo que dice la fuente, igual que ya hace `review/service.py` al armar los pasos de
    aprobación.

    Si la empresa no tiene a nadie con ese rol, devuelve vacío y **no falla**: el envío a SAP
    no puede depender de que la plantilla esté completa.
    """
    from ..auth.models import Role, User

    return (await db.execute(
        select(User.id)
        .join(Role, Role.id == User.role_id)
        .where(Role.name == nombre_rol,
               User.company_id == company_id,
               User.is_active.is_(True))
    )).scalars().all()


# ── Lectura ───────────────────────────────────────────────────────────────────

def _mias(consulta, current_user: dict):
    """La puerta de la bandeja: ser el destinatario.

    Filtrar solo por `company_id` devolvería las notificaciones de los compañeros de empresa,
    que es una fuga con toda la apariencia de un filtro correcto. El alcance de empresa se
    suma, no sustituye.
    """
    consulta = consulta.where(Notification.recipient_user_id == current_user["id"])
    if current_user.get("company_id"):
        consulta = consulta.where(Notification.company_id == current_user["company_id"])
    return consulta


async def listar(
    db: AsyncSession, current_user: dict, skip: int = 0, limit: int = 20
) -> tuple[Sequence[Notification], int]:
    total = (await db.execute(
        _mias(select(func.count(Notification.id)), current_user))).scalar_one()
    filas = (await db.execute(
        _mias(select(Notification), current_user)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip).limit(limit)
    )).scalars().all()
    return filas, total


async def contar_sin_leer(db: AsyncSession, current_user: dict) -> int:
    """El contador lo calcula el servidor. Contar en el cliente daría el número de la primera
    página, que es el mismo defecto que `R-89` costó en los maestros."""
    return (await db.execute(
        _mias(select(func.count(Notification.id)), current_user)
        .where(Notification.read_at.is_(None))
    )).scalar_one()


async def obtener(
    db: AsyncSession, current_user: dict, notification_id: int
) -> Optional[Notification]:
    return (await db.execute(
        _mias(select(Notification).where(Notification.id == notification_id), current_user)
    )).scalar_one_or_none()


async def marcar_leida(aviso: Notification, db: AsyncSession) -> Notification:
    """Fija `read_at` una sola vez.

    Repetir la llamada deja el mismo estado final: si se reescribiera la marca, el momento de
    lectura pasaría a ser el de la última vez que alguien pulsó, que no es lo que significa.
    """
    if aviso.read_at is None:
        aviso.read_at = datetime.now(timezone.utc)
        await db.flush()
    return aviso
