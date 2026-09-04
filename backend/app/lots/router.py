"""REST API router for Lot management."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..transaction import RutaTransaccional
from ..dependencies import get_current_user, require_permission
from . import schemas
from .service import LotService

router = APIRouter(route_class=RutaTransaccional, prefix="/lots", tags=["Lots"])


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
    current_user: dict = Depends(require_permission("lots", "read")),
):
    items, total = await _service(db, current_user).get_lots(
        skip=skip, limit=limit, search=search, farm_id=farm_id, status=status,
    )
    return [schemas.LotRead.model_validate(item) for item in items]


@router.post("", response_model=schemas.LotRead, status_code=201)
async def create_lot(
    data: schemas.LotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    lot = await _service(db, current_user).create_lot(data)
    return schemas.LotRead.model_validate(lot)


@router.get("/{lot_id}", response_model=schemas.LotDetailRead)
async def get_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
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
    current_user: dict = Depends(require_permission("lots", "update")),
):
    lot = await _service(db, current_user).update_lot(lot_id, data)
    return schemas.LotRead.model_validate(lot)


@router.post("/{lot_id}/close")
async def close_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
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
    current_user: dict = Depends(require_permission("lots", "create")),
):
    ob = await _service(db, current_user).activate_manual(data)
    return schemas.OpeningBalanceRead.model_validate(ob)


@router.get("/{lot_id}/opening-balance", response_model=schemas.OpeningBalanceRead)
async def get_opening_balance(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
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
    current_user: dict = Depends(require_permission("lots", "read")),
):
    phases = await _service(db, current_user).get_lot_phases(lot_id)
    return [schemas.LotPhaseRead.model_validate(p) for p in phases]


@router.post("/{lot_id}/phases", response_model=schemas.LotPhaseRead, status_code=201)
async def add_lot_phase(
    lot_id: int,
    data: schemas.LotPhaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    if data.lot_id != lot_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="lot_id mismatch")
    phase = await _service(db, current_user).add_phase(data)
    return schemas.LotPhaseRead.model_validate(phase)


# ============================================================
# T-083: Generational Traceability
# ============================================================

@router.get("/{lot_id}/traceability", response_model=schemas.TraceabilityNode)
async def get_lot_traceability(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
):
    """Return full generational traceability tree for a lot (egg batches + chick batches)."""
    from sqlalchemy import select
    from .models import EggBatch, ChickBatch

    # Use LotService to validate company isolation
    svc = _service(db, current_user)
    lot = await svc.get_lot(lot_id)

    egg_sent_r = await db.execute(select(EggBatch).where(EggBatch.source_lot_id == lot_id))
    egg_sent = egg_sent_r.scalars().all()
    egg_recv_r = await db.execute(select(EggBatch).where(EggBatch.hatchery_lot_id == lot_id))
    egg_recv = egg_recv_r.scalars().all()
    chick_sent_r = await db.execute(select(ChickBatch).where(ChickBatch.hatchery_lot_id == lot_id))
    chick_sent = chick_sent_r.scalars().all()
    # Received chicks: destination_lot_id (generalized) OR legacy broiler_lot_id
    from sqlalchemy import or_
    chick_recv_r = await db.execute(
        select(ChickBatch).where(
            or_(
                ChickBatch.destination_lot_id == lot_id,
                ChickBatch.broiler_lot_id == lot_id,
            )
        )
    )
    chick_recv = chick_recv_r.scalars().all()

    lot_ref = schemas.LotRef(
        id=lot.id, lot_code=lot.lot_code or f"L-{lot.id}",
        bird_type=lot.bird_type.value if lot.bird_type else None,
        status=lot.status.value if hasattr(lot.status, "value") else str(lot.status),
    )
    return schemas.TraceabilityNode(
        lot=lot_ref,
        egg_batches_sent=[schemas.EggBatchRead.model_validate(b) for b in egg_sent],
        egg_batches_received=[schemas.EggBatchRead.model_validate(b) for b in egg_recv],
        chick_batches_sent=[schemas.ChickBatchRead.model_validate(b) for b in chick_sent],
        chick_batches_received=[schemas.ChickBatchRead.model_validate(b) for b in chick_recv],
    )


@router.post("/egg-batches", response_model=schemas.EggBatchRead, status_code=201)
async def create_egg_batch(
    data: schemas.EggBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    """Link a breeder/grandparent lot → hatchery lot via egg batch."""
    from .models import EggBatch
    batch = EggBatch(**data.model_dump())
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    return schemas.EggBatchRead.model_validate(batch)


@router.post("/chick-batches", response_model=schemas.ChickBatchRead, status_code=201)
async def create_chick_batch(
    data: schemas.ChickBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    """Link a hatchery lot → destination lot (breeder or broiler) via chick batch."""
    from .models import ChickBatch
    payload = data.model_dump()
    # Sync: if destination_lot_id provided, also set broiler_lot_id for backward compat
    if payload.get("destination_lot_id") and not payload.get("broiler_lot_id"):
        payload["broiler_lot_id"] = payload["destination_lot_id"]
    elif payload.get("broiler_lot_id") and not payload.get("destination_lot_id"):
        payload["destination_lot_id"] = payload["broiler_lot_id"]
    batch = ChickBatch(**payload)
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    return schemas.ChickBatchRead.model_validate(batch)
