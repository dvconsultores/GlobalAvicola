"""Review & Approval schemas — Pydantic models for the review workflow."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# ReviewBatch
# ============================================================

class ReviewBatchCreate(BaseModel):
    batch_name: str = Field(..., max_length=200, examples=["Lote L-001 — Revisión Junio"])
    event_ids: list[int] = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = None


class ReviewBatchRead(BaseModel):
    id: int
    company_id: int
    batch_name: str
    status: str
    total_events: int
    approved_count: int
    rejected_count: int
    created_by_id: int
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# ApprovalStep
# ============================================================

class ApprovalStepCreate(BaseModel):
    step_order: int = Field(..., ge=1, le=3)
    name: str = Field(..., max_length=100, examples=["Revisión"])
    role_id: int
    can_correct: bool = False
    can_approve: bool = False
    can_reject: bool = False
    require_segregation: bool = True


class ApprovalStepRead(BaseModel):
    id: int
    company_id: int
    step_order: int
    name: str
    role_id: int
    can_correct: bool
    can_approve: bool
    can_reject: bool
    require_segregation: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalStepUpdate(BaseModel):
    name: Optional[str] = None
    role_id: Optional[int] = None
    can_correct: Optional[bool] = None
    can_approve: Optional[bool] = None
    can_reject: Optional[bool] = None
    require_segregation: Optional[bool] = None


# ============================================================
# ApprovalAction
# ============================================================

class ApprovalActionRead(BaseModel):
    id: int
    event_id: int
    batch_id: Optional[int] = None
    step_id: Optional[int] = None
    user_id: int
    action_type: str
    observations: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Review Actions
# ============================================================

class ReviewActionRequest(BaseModel):
    """Start review of a single event."""
    event_id: int


class ReturnToOperatorRequest(BaseModel):
    """Return event to operator with observations."""
    event_id: int
    observations: str = Field(..., min_length=10, max_length=2000)


class CompleteReviewRequest(BaseModel):
    """Complete review (move to next approval step or mark approved)."""
    event_id: int
    observations: Optional[str] = None


# ============================================================
# Approval Actions
# ============================================================

class ApproveRequest(BaseModel):
    event_id: int
    observations: Optional[str] = None


class RejectRequest(BaseModel):
    event_id: int
    observations: str = Field(..., min_length=10, max_length=2000)


class BatchApproveRequest(BaseModel):
    event_ids: list[int] = Field(..., min_length=1, max_length=500)
    observations: Optional[str] = None


class BatchRejectRequest(BaseModel):
    event_ids: list[int] = Field(..., min_length=1, max_length=500)
    observations: str = Field(..., min_length=10, max_length=2000)
