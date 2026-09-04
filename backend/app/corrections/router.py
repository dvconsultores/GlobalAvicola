"""Corrections REST API router."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user, require_permission
from . import schemas
from .service import CorrectionService

router = APIRouter(prefix="/corrections", tags=["Corrections"])


@router.post("", response_model=schemas.CorrectionRead, status_code=201)
async def create_correction(
    data: schemas.CorrectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("corrections", "correct")),
):
    """Create a correction log entry (audit trail)."""
    return await CorrectionService(db, current_user).create_correction(data)


@router.get("/event/{event_id}", response_model=list[schemas.CorrectionRead])
async def get_event_corrections(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("corrections", "read")),
):
    """Get all corrections for a given event."""
    return await CorrectionService(db, current_user).get_corrections_for_event(event_id)


@router.get("")
async def list_corrections(
    lot_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("corrections", "read")),
):
    """List corrections with optional lot filter."""
    corrections, total = await CorrectionService(db, current_user).get_corrections(
        lot_id=lot_id, limit=limit, offset=offset,
    )
    return {"corrections": corrections, "total": total}
