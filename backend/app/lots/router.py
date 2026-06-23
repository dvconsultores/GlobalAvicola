"""REST API router for Lot management."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from . import schemas
from .service import LotService

router = APIRouter(prefix="/lots", tags=["Lots"])


def _service(db: AsyncSession, user: dict):
    return LotService(db, user)


# ============================================================
# Lot CRUD
# ============================================================

@router.get("", response_model=list[schemas.LotRead])
async def list_lots(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    farm_id: int | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = await _service(db, current_user).get_lots(
        skip=skip, limit=limit, search=search, farm_id=farm_id, status=status,
    )
    return [schemas.LotRead.model_validate(item) for item in items]


@router.post("", response_model=schemas.LotRead, status_code=201)
async def create_lot(
    data: schemas.LotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    lot = await _service(db, current_user).create_lot(data)
    return schemas.LotRead.model_validate(lot)


@router.get("/{lot_id}", response_model=schemas.LotDetailRead)
async def get_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = _service(db, current_user)
    lot = await service.get_lot(lot_id)
    result = schemas.LotDetailRead.model_validate(lot)
    # Eager load phases and opening balance
    result.phases = [
        schemas.LotPhaseRead.model_validate(p)
        for p in (await service.get_lot_phases(lot_id))
    ]
    ob = await service.get_opening_balance(lot_id)
    if ob:
        result.opening_balance = schemas.OpeningBalanceRead.model_validate(ob)
    return result


@router.put("/{lot_id}", response_model=schemas.LotRead)
async def update_lot(
    lot_id: int,
    data: schemas.LotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    lot = await _service(db, current_user).update_lot(lot_id, data)
    return schemas.LotRead.model_validate(lot)


@router.post("/{lot_id}/close")
async def close_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    lot = await _service(db, current_user).close_lot(lot_id)
    return schemas.LotRead.model_validate(lot)


# ============================================================
# Manual Activation (Opening Balance)
# ============================================================

@router.post("/activate-manual", response_model=schemas.OpeningBalanceRead, status_code=201)
async def activate_manual(
    data: schemas.OpeningBalanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ob = await _service(db, current_user).activate_manual(data)
    return schemas.OpeningBalanceRead.model_validate(ob)


@router.get("/{lot_id}/opening-balance", response_model=schemas.OpeningBalanceRead)
async def get_opening_balance(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ob = await _service(db, current_user).get_opening_balance(lot_id)
    if not ob:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Balance de apertura no encontrado")
    return schemas.OpeningBalanceRead.model_validate(ob)


# ============================================================
# Lot Phases
# ============================================================

@router.get("/{lot_id}/phases", response_model=list[schemas.LotPhaseRead])
async def get_lot_phases(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    phases = await _service(db, current_user).get_lot_phases(lot_id)
    return [schemas.LotPhaseRead.model_validate(p) for p in phases]


@router.post("/{lot_id}/phases", response_model=schemas.LotPhaseRead, status_code=201)
async def add_lot_phase(
    lot_id: int,
    data: schemas.LotPhaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if data.lot_id != lot_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="lot_id mismatch")
    phase = await _service(db, current_user).add_phase(data)
    return schemas.LotPhaseRead.model_validate(phase)
