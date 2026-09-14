"""
SQLAlchemy event listeners for automatic audit logging.

Principle: Everything is audited. Nothing is deleted. Records are immutable.

Listens on:
  - Session.after_flush → detect new/changed OperationalEvent (alta y transiciones de
    estado) y nuevos CorrectionLog (corrección con diff por campo).

`P1-12-REOPEN` (C-01 registrada): la ruta `ApprovalAction` se **retiró** — cada decisión
(`start`/`return`/`complete`/`approve`/`reject`) transita el estado del evento, que es la
fuente única; el batch y la contrapartida (update masivo / alta directa) producen su fila
de transición de forma explícita en el servicio. El registro compartido
(`helpers.ya_emitida`/`marcar_emitida`) garantiza **un productor por acción** tanto aquí
como en contextos sin listener.

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
from .helpers import marcar_emitida, ya_emitida
from .models import AuditAction, AuditLog, AuditModule

logger = logging.getLogger(__name__)

# ── Models imported lazily to avoid circular imports ──────────────────────

def _get_op_event():
    from ..operations.models import EventStatus, OperationalEvent
    return OperationalEvent, EventStatus

def _get_correction_log():
    from ..corrections.models import CorrectionLog
    return CorrectionLog


# ── Status → AuditAction mapping ──────────────────────────────────────────

_STATUS_TO_AUDIT_ACTION: dict[str, AuditAction] = {
    "registered":      AuditAction.CREATED,
    "pending_review":  AuditAction.UPDATED,       # `P1-12-REOPEN`: enviar a revisión **es** una actualización
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
    "reversed":        AuditAction.REVERSED,      # `OD-19` · `GA-REM-041`
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
    # 3. NEW CorrectionLog → CORRECTED (diff por campo)
    # ═══════════════════════════════════════════════════════
    CorrectionLog = _get_correction_log()
    for obj in session.new:
        if isinstance(obj, CorrectionLog):
            _audit_correction(session, obj, user_id, company_id)

    # `P1-12-REOPEN`: fin de la ruta `ApprovalAction` (C-01). Las decisiones se auditan por
    # la transición de estado del evento; el batch y la contrapartida añaden su fila de
    # transición en el servicio.


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
    if ya_emitida(session, entity_type="operational_event", entity_id=event.id,
                  action=AuditAction.CREATED):
        return  # `P1-12-REOPEN`: el helper ya la escribió en esta sesión
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
    marcar_emitida(session, entity_type="operational_event", entity_id=event.id,
                   action=AuditAction.CREATED)


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

    # `P1-12-REOPEN`: la corrección rica (diff por campo) la escribe la ruta
    # `CorrectionLog` del mismo flush — si está presente, esta ruta se abstiene.
    if new_str == "corrected":
        CorrectionLog = _get_correction_log()
        if any(isinstance(o, CorrectionLog) and o.event_id == event.id for o in session.new):
            return

    if ya_emitida(session, entity_type="operational_event", entity_id=event.id,
                  action=audit_action):
        return  # `P1-12-REOPEN`: el helper ya la escribió en esta sesión

    # Módulo alineado con los helpers (`audit_state_transition`): la misma transición
    # produce la misma fila con listener o sin él.
    module = AuditModule.OPERATIONS
    if audit_action in (AuditAction.REVIEW_STARTED, AuditAction.RETURNED, AuditAction.CORRECTED):
        module = AuditModule.REVIEW
    elif audit_action in (AuditAction.APPROVED, AuditAction.REJECTED):
        module = AuditModule.APPROVALS

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
        module=module,
        lot_id=getattr(event, 'lot_id', None),
        farm_id=getattr(event, 'farm_id', None),
        house_id=getattr(event, 'house_id', None),
        previous_state=old_str,
        new_state=new_str,
        previous_values=changed_fields if changed_fields else None,
        change_reason=getattr(event, 'observations', None),
    )
    session.add(log)
    marcar_emitida(session, entity_type="operational_event", entity_id=event.id,
                   action=audit_action)


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
    if ya_emitida(session, entity_type="operational_event", entity_id=correction.event_id,
                  action=AuditAction.CORRECTED):
        return  # `P1-12-REOPEN`: el helper ya la escribió en esta sesión
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
    marcar_emitida(session, entity_type="operational_event", entity_id=correction.event_id,
                   action=AuditAction.CORRECTED)


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
