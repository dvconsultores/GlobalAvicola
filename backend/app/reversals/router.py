"""Rutas del reverso interno. `GA-REM-041 §5`: tres rutas, justificadas en la spec."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import require_permission
from ..transaction import RutaTransaccional
from . import schemas
from .service import ReversalService

router = APIRouter(route_class=RutaTransaccional, prefix="/reversals", tags=["Reversals"])


@router.post("", response_model=schemas.ReversalRead, status_code=201)
async def solicitar_reverso(
    data: schemas.ReversalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reversals", "create")),
):
    """Solicita el reverso de un registro aprobado: crea la contrapartida en la cola de revisión."""
    return await ReversalService(db, current_user).solicitar(data)


@router.get("", response_model=schemas.ReversalListResponse)
async def listar_reversos(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reversals", "read")),
):
    reversos, total = await ReversalService(db, current_user).listar(limit=limit, offset=offset)
    return {"reversals": reversos, "total": total}


@router.get("/event/{event_id}", response_model=list[schemas.ReversalRead])
async def reversos_de_un_evento(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reversals", "read")),
):
    return await ReversalService(db, current_user).por_evento(event_id)
