"""
Review & Approval models — ReviewBatch, ApprovalStep, ApprovalAction.
Implements configurable 1/2/3-level approval workflows per company.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer,
    String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


# ============================================================
# Enums
# ============================================================

class BatchStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActionType(str, enum.Enum):
    STARTED_REVIEW = "started_review"
    RETURNED = "returned"
    CORRECTED = "corrected"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================
# ReviewBatch
# ============================================================

class ReviewBatch(Base):
    """Groups operational events for batch review/approval."""
    __tablename__ = "review_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    batch_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.OPEN)
    total_events: Mapped[int] = mapped_column(Integer, default=0)
    approved_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    actions: Mapped[list["ApprovalAction"]] = relationship(
        "ApprovalAction", back_populates="batch", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ReviewBatch {self.batch_name} status={self.status.value}>"


# ============================================================
# ApprovalStep (Configuration per company)
# ============================================================

class ApprovalStep(Base):
    """Configurable approval workflow step per company."""
    __tablename__ = "approval_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)  # 1, 2, 3
    name: Mapped[str] = mapped_column(String(100))  # e.g. "Revisión", "Aprobación", "Confirmación"
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))
    can_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    can_approve: Mapped[bool] = mapped_column(Boolean, default=False)
    can_reject: Mapped[bool] = mapped_column(Boolean, default=False)
    require_segregation: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<ApprovalStep {self.step_order}:{self.name} company={self.company_id}>"


# ============================================================
# ApprovalAction (Audit trail)
# ============================================================

class ApprovalAction(Base):
    """Individual action in the review/approval workflow — immutable audit trail."""
    __tablename__ = "approval_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("review_batches.id"), nullable=True, index=True)
    step_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("approval_steps.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType))
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    batch: Mapped[Optional["ReviewBatch"]] = relationship("ReviewBatch", back_populates="actions")

    def __repr__(self) -> str:
        return f"<ApprovalAction {self.action_type.value} event={self.event_id}>"
