"""Review & Approval REST API router."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user, require_permission
from . import schemas
from .service import ApprovalService, ApprovalStepService, ReviewService

router = APIRouter(prefix="/review", tags=["Review"])
approval_router = APIRouter(prefix="/approvals", tags=["Approvals"])
steps_router = APIRouter(prefix="/approval-steps", tags=["Approval Steps"])


# ============================================================
# Review — Pending events
# ============================================================

@router.get("/pending")
async def list_pending_review(
    farm_id: Optional[int] = Query(None),
    lot_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "read")),
):
    """Get events pending review (registered / pending_review)."""
    svc = ReviewService(db, current_user)
    events, total = await svc.get_pending_review_events(
        farm_id=farm_id, lot_id=lot_id, event_type=event_type,
        date_from=date_from, date_to=date_to, limit=limit, offset=offset,
    )
    return {"events": events, "total": total}


# ============================================================
# Review — Batches
# ============================================================

@router.post("/batches", response_model=schemas.ReviewBatchRead, status_code=201)
async def create_review_batch(
    data: schemas.ReviewBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "review")),
):
    """Create a review batch from event IDs."""
    return await ReviewService(db, current_user).create_review_batch(data)


@router.get("/batches")
async def list_review_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "read")),
):
    """List review batches for current company."""
    batches, total = await ReviewService(db, current_user).get_batches(limit=limit, offset=offset)
    return {"batches": batches, "total": total}


# ============================================================
# Review — Single event actions
# ============================================================

@router.post("/start/{event_id}")
async def start_review(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "review")),
):
    """Start reviewing a single event."""
    return await ReviewService(db, current_user).start_review(event_id)


@router.post("/return")
async def return_to_operator(
    data: schemas.ReturnToOperatorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "review")),
):
    """Return event to operator with observations."""
    return await ReviewService(db, current_user).return_to_operator(data.event_id, data.observations)


@router.post("/complete")
async def complete_review(
    data: schemas.CompleteReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "review")),
):
    """Complete review (auto-approve if single-level, else move to approval)."""
    return await ReviewService(db, current_user).complete_review(data.event_id, data.observations)


# ============================================================
# Approvals
# ============================================================

@approval_router.get("/pending")
async def list_pending_approvals(
    farm_id: Optional[int] = Query(None),
    lot_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("approvals", "approve")),
):
    """Get events pending approval (status=corrected)."""
    events, total = await ApprovalService(db, current_user).get_pending_approvals(
        farm_id=farm_id, lot_id=lot_id, limit=limit, offset=offset,
    )
    return {"events": events, "total": total}


@approval_router.post("/approve")
async def approve_event(
    data: schemas.ApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("approvals", "approve")),
):
    """Approve a single event."""
    return await ApprovalService(db, current_user).approve(data.event_id, data.observations)


@approval_router.post("/reject")
async def reject_event(
    data: schemas.RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("approvals", "reject")),
):
    """Reject a single event (reason mandatory)."""
    return await ApprovalService(db, current_user).reject(data.event_id, data.observations)


@approval_router.post("/batch-approve")
async def batch_approve(
    data: schemas.BatchApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "review")),
):
    """Approve multiple events."""
    return await ApprovalService(db, current_user).batch_approve(data.event_ids, data.observations)


@approval_router.post("/batch-reject")
async def batch_reject(
    data: schemas.BatchRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "review")),
):
    """Reject multiple events (reason mandatory)."""
    return await ApprovalService(db, current_user).batch_reject(data.event_ids, data.observations)


# ============================================================
# Approval Steps (Configuration)
# ============================================================

@steps_router.get("")
async def list_approval_steps(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "read")),
):
    """Get approval steps for current company."""
    return await ApprovalStepService(db, current_user).get_steps()


@steps_router.post("", response_model=schemas.ApprovalStepRead, status_code=201)
async def create_approval_step(
    data: schemas.ApprovalStepCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "create")),
):
    """Create an approval step for current company."""
    return await ApprovalStepService(db, current_user).create_step(data)


@steps_router.put("/{step_id}", response_model=schemas.ApprovalStepRead)
async def update_approval_step(
    step_id: int,
    data: schemas.ApprovalStepUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "update")),
):
    """Update an approval step."""
    return await ApprovalStepService(db, current_user).update_step(step_id, data)


@steps_router.delete("/{step_id}", status_code=204)
async def delete_approval_step(
    step_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "delete")),
):
    """Delete an approval step."""
    await ApprovalStepService(db, current_user).delete_step(step_id)


@steps_router.post("/seed-defaults", status_code=201)
async def seed_default_steps(
    approval_levels: int = Query(2, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("review", "create")),
):
    """Seed default approval steps based on levels (1/2/3)."""
    return await ApprovalStepService(db, current_user).seed_default_steps(approval_levels)
