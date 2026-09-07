"""Bandeja de notificaciones — `GA-REM-038` / `OD-07`.

**No hay endpoint de creación.** Las notificaciones las crea el backend cuando ocurre el
evento del negocio; que el cliente pudiera fabricarlas convertiría la bandeja en un tablón.

**No hay `read-all` ni borrado.** Ninguna fuente los pide, y las notificaciones son historial
operativo.

La autorización es la **propiedad**, no un permiso de módulo: es el mismo criterio que `/me` o
el cambio de contraseña. Añadir un módulo `notifications` al catálogo obligaría a reconciliar
la matriz `RBAC` de la migración con sus seis roles —el trabajo que `R-44` costó— para no
proteger nada que la propiedad no proteja mejor.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..transaction import RutaTransaccional
from . import schemas, service

router = APIRouter(route_class=RutaTransaccional, prefix="/notifications",
                   tags=["Notifications"])


@router.get("", response_model=list[schemas.NotificationRead])
async def list_notifications(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Las notificaciones **propias**, la más reciente primero.

    Consultarla no crea nada: solo los eventos del negocio crean notificaciones.
    """
    filas, total = await service.listar(db, current_user, skip=skip, limit=limit)
    # Mismo contrato que los maestros (`R-89`): el total en cabecera, para que el cliente no
    # tenga que confundir el tamaño de la página con el número de resultados.
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return [schemas.NotificationRead.model_validate(f) for f in filas]


@router.get("/unread-count", response_model=schemas.UnreadCountRead)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cuántas sin leer. Se cuenta en el servidor, no trayendo la bandeja entera."""
    return schemas.UnreadCountRead(unread=await service.contar_sin_leer(db, current_user))


@router.get("/{notification_id}", response_model=schemas.NotificationRead)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    aviso = await service.obtener(db, current_user, notification_id)
    if aviso is None:
        # `404` y no `403`: para quien no es el destinatario, la notificación no existe.
        # Un `403` confirmaría que hay algo ahí.
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return schemas.NotificationRead.model_validate(aviso)


@router.patch("/{notification_id}/read", response_model=schemas.NotificationRead)
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Solo el destinatario marca la suya. Repetirlo deja el mismo estado final."""
    aviso = await service.obtener(db, current_user, notification_id)
    if aviso is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return schemas.NotificationRead.model_validate(
        await service.marcar_leida(aviso, db))
