"""
AuditLog model — immutable audit trail for every action in the system.
Principle: Everything is audited. Nothing is deleted. Records are immutable.
"""
import enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    DateTime, Enum, ForeignKey, Integer,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


# ============================================================
# Enums
# ============================================================

class AuditAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    CORRECTED = "corrected"
    REVIEW_STARTED = "review_started"
    REVIEW_COMPLETED = "review_completed"
    RETURNED = "returned"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONSOLIDATED = "consolidated"
    SENT_TO_SAP = "sent_to_sap"
    SAP_CONFIRMED = "sap_confirmed"
    SAP_ERROR = "sap_error"
    CANCELLED = "cancelled"
    REVERSED = "reversed"  # `OD-19`: reverso interno efectivo
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    #: `OD-11 §6`: situarse en otra empresa es un acto de administración con consecuencias
    #: sobre qué datos se tocan, y no dejaba constancia de haber ocurrido.
    CONTEXT_SWITCHED = "context_switched"
    PERMISSION_CHANGE = "permission_change"
    CONFIG_CHANGE = "config_change"
    IMPORT = "import"
    EXPORT = "export"
    DELETED = "deleted"


class AuditModule(str, enum.Enum):
    AUTH = "auth"
    MASTERS = "masters"
    LOTS = "lots"
    OPERATIONS = "operations"
    REVIEW = "review"
    APPROVALS = "approvals"
    CORRECTIONS = "corrections"
    SAP = "sap"
    REPORTS = "reports"
    USERS = "users"
    CONFIG = "config"


# ============================================================
# AuditLog
# ============================================================

class AuditLog(Base):
    """
    Immutable audit trail. Created automatically via SQLAlchemy event listeners.
    Never modified or deleted through the API.
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)  # e.g. "operational_event", "lot", "user"
    entity_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    module: Mapped[AuditModule] = mapped_column(Enum(AuditModule), index=True)
    lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lots.id"), nullable=True, index=True)
    farm_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("farms.id"), nullable=True, index=True)
    house_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("houses.id"), nullable=True)
    previous_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    previous_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sap_reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # SAP document ref (no FK — audit is decoupled)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_sensitive: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} on {self.entity_type}#{self.entity_id}>"
