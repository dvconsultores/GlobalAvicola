"""REST API router for operational events — unified endpoint for 24 event types."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from . import schemas
from .service import OperationsService

router = APIRouter(prefix="/operations", tags=["Operations"])


def _service(db: AsyncSession, user: dict):
    return OperationsService(db, user)


# ============================================================
# Event Types Reference
# ============================================================

@router.get("/event-types", tags=["Operations"])
async def list_event_types():
    return schemas.ALL_EVENT_TYPES


# ============================================================
# CRUD
# ============================================================

@router.get("", response_model=list[schemas.OperationalEventRead])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    lot_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = await _service(db, current_user).get_events(
        skip=skip, limit=limit, lot_id=lot_id, farm_id=farm_id,
        event_type=event_type, status=status,
        date_from=date_from, date_to=date_to,
    )
    return [schemas.OperationalEventRead.model_validate(item) for item in items]


@router.post("", response_model=schemas.OperationalEventRead, status_code=201)
async def create_event(
    data: schemas.OperationalEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    event = await _service(db, current_user).create_event(data)
    return schemas.OperationalEventRead.model_validate(event)


@router.get("/{event_id}", response_model=schemas.OperationalEventDetailRead)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    event = await _service(db, current_user).get_event(event_id)
    result = schemas.OperationalEventDetailRead.model_validate(event)
    result.bird_movements = [schemas.BirdMovementSchema.model_validate(bm) for bm in event.bird_movements]
    result.egg_movements = [schemas.EggMovementSchema.model_validate(em) for em in event.egg_movements]
    result.feed_movements = [schemas.FeedMovementSchema.model_validate(fm) for fm in event.feed_movements]
    result.hatchery_params = [schemas.HatcheryParamsSchema.model_validate(hp) for hp in event.hatchery_params]
    result.inspection_details = [schemas.InspectionDetailSchema.model_validate(id) for id in event.inspection_details]
    return result


@router.put("/{event_id}", response_model=schemas.OperationalEventRead)
async def update_event(
    event_id: int,
    data: schemas.OperationalEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    event = await _service(db, current_user).update_event(event_id, data)
    return schemas.OperationalEventRead.model_validate(event)


# ============================================================
# State Transitions
# ============================================================

@router.post("/{event_id}/submit", response_model=schemas.OperationalEventRead)
async def submit_to_review(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    event = await _service(db, current_user).submit_to_review(event_id)
    return schemas.OperationalEventRead.model_validate(event)


@router.post("/{event_id}/cancel", response_model=schemas.OperationalEventRead)
async def cancel_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    event = await _service(db, current_user).cancel_event(event_id)
    return schemas.OperationalEventRead.model_validate(event)
