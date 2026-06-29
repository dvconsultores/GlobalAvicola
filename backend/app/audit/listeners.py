"""
SQLAlchemy event listeners for automatic audit logging.

Principle: Everything is audited. Nothing is deleted. Records are immutable.

Listens on:
  - Session.after_flush → detect new/changed OperationalEvent,
    CorrectionLog, ApprovalAction and create corresponding AuditLog entries.

The current user is obtained from the context variable set by
get_current_user in app.auth.security.
"""
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from .context import get_current_audit_user
from .models import AuditAction, AuditLog, AuditModule

logger = logging.getLogger(__name__)

# ── Models imported lazily to avoid circular imports ──────────────────────

def _get_op_event():
    from ..operations.models import EventStatus, OperationalEvent
    return OperationalEvent, EventStatus

def _get_correction_log():
    from ..corrections.models import CorrectionLog
    return CorrectionLog

def _get_approval_action():
    from ..review.models import ActionType, ApprovalAction
    return ApprovalAction, ActionType


# ── Status → AuditAction mapping ──────────────────────────────────────────

_STATUS_TO_AUDIT_ACTION: dict[str, AuditAction] = {
    "registered":      AuditAction.CREATED,
    "pending_review":  AuditAction.CREATED,       # submit = state transition tracked separately
    "in_review":       AuditAction.REVIEW_STARTED,
    "returned":        AuditAction.RETURNED,
    "corrected":       AuditAction.CORRECTED,
    "approved":        AuditAction.APPROVED,
    "rejected":        AuditAction.REJECTED,
    "consolidated":    AuditAction.CONSOLIDATED,
    "sent_to_sap":     AuditAction.SENT_TO_SAP,
    "sap_confirmed":   AuditAction.SAP_CONFIRMED,
    "sap_error":       AuditAction.SAP_ERROR,
    "cancelled":       AuditAction.CANCELLED,
}

_APPROVAL_ACTION_TO_AUDIT: dict[str, AuditAction] = {
    "started_review":  AuditAction.REVIEW_STARTED,
    "returned":        AuditAction.RETURNED,
    "corrected":       AuditAction.CORRECTED,
    "approved":        AuditAction.APPROVED,
    "rejected":        AuditAction.REJECTED,
}


# ═══════════════════════════════════════════════════════════════════════════
# Main listener
# ═══════════════════════════════════════════════════════════════════════════

@event.listens_for(Session, "after_flush")
def audit_after_flush(session: Session, flush_context: Any) -> None:
    """
    After every flush, scan new and dirty objects to create AuditLog entries.
    All AuditLog entries are added to the SAME session, so they commit atomically.
    """
    user = get_current_audit_user()
    if user is None:
        # No authenticated user (e.g. startup, scripts). Skip auditing.
        return

    user_id: int = user["id"]
    company_id: int | None = user.get("company_id")

    # ═══════════════════════════════════════════════════════
    # 1. NEW OperationalEvent → CREATED
    # 2. DIRTY OperationalEvent → state transition
    # ═══════════════════════════════════════════════════════
    OperationalEvent, EventStatus = _get_op_event()

    for obj in session.new:
        if isinstance(obj, OperationalEvent):
            _audit_event_created(session, obj, user_id, company_id)

    for obj in session.dirty:
        if isinstance(obj, OperationalEvent):
            _audit_event_modified(session, obj, user_id, company_id, EventStatus)

    # ═══════════════════════════════════════════════════════
    # 3. NEW CorrectionLog → CORRECTED
    # ═══════════════════════════════════════════════════════
    CorrectionLog = _get_correction_log()
    for obj in session.new:
        if isinstance(obj, CorrectionLog):
            _audit_correction(session, obj, user_id, company_id)

    # ═══════════════════════════════════════════════════════
    # 4. NEW ApprovalAction → APPROVED / REJECTED / REVIEW_STARTED / RETURNED
    # ═══════════════════════════════════════════════════════
    ApprovalAction, ActionType = _get_approval_action()
    for obj in session.new:
        if isinstance(obj, ApprovalAction):
            _audit_approval_action(session, obj, user_id, company_id)


# ═══════════════════════════════════════════════════════════════════════════
# Helper: create an AuditLog row
# ═══════════════════════════════════════════════════════════════════════════

def _make_audit_log(
    user_id: int,
    company_id: int | None,
    action: AuditAction,
    entity_type: str,
    entity_id: str,
    module: AuditModule,
    *,
    lot_id: int | None = None,
    farm_id: int | None = None,
    house_id: int | None = None,
    previous_values: dict | None = None,
    new_values: dict | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
    change_reason: str | None = None,
    comments: str | None = None,
) -> AuditLog:
    return AuditLog(
        id=str(uuid4()),
        company_id=company_id or 0,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        module=module,
        lot_id=lot_id,
        farm_id=farm_id,
        house_id=house_id,
        previous_values=previous_values,
        new_values=new_values,
        previous_state=previous_state,
        new_state=new_state,
        change_reason=change_reason,
        comments=comments,
        created_at=datetime.now(timezone.utc),
    )


# ═══════════════════════════════════════════════════════════════════════════
# OperationalEvent handlers
# ═══════════════════════════════════════════════════════════════════════════

def _audit_event_created(
    session: Session,
    event: Any,  # OperationalEvent
    user_id: int,
    company_id: int | None,
) -> None:
    """A new operational event was created."""
    insp = inspect(event)
    new_vals: dict[str, Any] = {}

    # Collect non-relationship, serializable column values
    for attr in insp.attrs:
        if hasattr(attr, 'key') and not attr.key.startswith("_"):
            try:
                val = attr.value
                if val is not None and not hasattr(val, '__table__'):
                    new_vals[attr.key] = _serialize_value(val)
            except Exception:
                pass

    log = _make_audit_log(
        user_id=user_id,
        company_id=company_id,
        action=AuditAction.CREATED,
        entity_type="operational_event",
        entity_id=str(event.id),
        module=AuditModule.OPERATIONS,
        lot_id=getattr(event, 'lot_id', None),
        farm_id=getattr(event, 'farm_id', None),
        house_id=getattr(event, 'house_id', None),
        new_values=new_vals,
        new_state=getattr(event, 'status', None).value if hasattr(getattr(event, 'status', None), 'value') else str(getattr(event, 'status', '')),
        comments=getattr(event, 'observations', None),
    )
    session.add(log)


def _audit_event_modified(
    session: Session,
    event: Any,  # OperationalEvent
    user_id: int,
    company_id: int | None,
    EventStatus,  # Enum class
) -> None:
    """Detect status changes on an OperationalEvent and create audit entries."""
    insp = inspect(event)
    status_attr = insp.attrs.get("status")
    if status_attr is None:
        return

    history = status_attr.history
    if not history.has_changes():
        return  # No status change — nothing to audit

    old_status = history.deleted[0] if history.deleted else None
    new_status = history.added[0] if history.added else None

    if old_status is None or new_status is None:
        return

    old_str = old_status.value if hasattr(old_status, 'value') else str(old_status)
    new_str = new_status.value if hasattr(new_status, 'value') else str(new_status)

    # Map new status → audit action
    audit_action = _STATUS_TO_AUDIT_ACTION.get(new_str)
    if audit_action is None:
        # Unrecognized transition — still log it as UPDATED
        audit_action = AuditAction.UPDATED

    # Collect other changed fields (non-status)
    changed_fields: dict[str, Any] = {}
    for attr in insp.attrs:
        if attr.key == "status":
            continue
        if hasattr(attr, 'history') and attr.history.has_changes():
            try:
                old_val = attr.history.deleted[0] if attr.history.deleted else None
                new_val = attr.history.added[0] if attr.history.added else None
                changed_fields[attr.key] = {
                    "old": _serialize_value(old_val),
                    "new": _serialize_value(new_val),
                }
            except Exception:
                pass

    log = _make_audit_log(
        user_id=user_id,
        company_id=company_id,
        action=audit_action,
        entity_type="operational_event",
        entity_id=str(event.id),
        module=AuditModule.OPERATIONS,
        lot_id=getattr(event, 'lot_id', None),
        farm_id=getattr(event, 'farm_id', None),
        house_id=getattr(event, 'house_id', None),
        previous_state=old_str,
        new_state=new_str,
        previous_values=changed_fields if changed_fields else None,
        change_reason=getattr(event, 'observations', None),
    )
    session.add(log)


# ═══════════════════════════════════════════════════════════════════════════
# CorrectionLog handler
# ═══════════════════════════════════════════════════════════════════════════

def _audit_correction(
    session: Session,
    correction: Any,  # CorrectionLog
    user_id: int,
    company_id: int | None,
) -> None:
    """A correction was registered → log field-level change."""
    log = _make_audit_log(
        user_id=user_id,
        company_id=company_id,
        action=AuditAction.CORRECTED,
        entity_type="operational_event",
        entity_id=str(correction.event_id),
        module=AuditModule.CORRECTIONS,
        previous_values={correction.field_name: correction.original_value},
        new_values={correction.field_name: correction.corrected_value},
        change_reason=correction.reason,
    )
    session.add(log)


# ═══════════════════════════════════════════════════════════════════════════
# ApprovalAction handler
# ═══════════════════════════════════════════════════════════════════════════

def _audit_approval_action(
    session: Session,
    action_obj: Any,  # ApprovalAction
    user_id: int,
    company_id: int | None,
) -> None:
    """An approval action was recorded → log it."""
    action_type_str = (
        action_obj.action_type.value
        if hasattr(action_obj.action_type, 'value')
        else str(action_obj.action_type)
    )
    audit_action = _APPROVAL_ACTION_TO_AUDIT.get(
        action_type_str, AuditAction.UPDATED
    )

    # Determine module based on action type
    module = AuditModule.APPROVALS
    if audit_action in (AuditAction.REVIEW_STARTED, AuditAction.RETURNED):
        module = AuditModule.REVIEW

    log = _make_audit_log(
        user_id=user_id,
        company_id=company_id,
        action=audit_action,
        entity_type="operational_event",
        entity_id=str(action_obj.event_id),
        module=module,
        comments=action_obj.observations,
    )
    session.add(log)


# ═══════════════════════════════════════════════════════════════════════════
# Utility
# ═══════════════════════════════════════════════════════════════════════════

def _serialize_value(val: Any) -> Any:
    """Convert a value to something JSON-serializable."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    if hasattr(val, 'value'):  # Enum
        return val.value
    return str(val)
