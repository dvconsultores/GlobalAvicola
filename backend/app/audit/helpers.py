"""
Audit helpers — functions to create AuditLog entries from service layer.

Unlike SQLAlchemy event listeners (which don't fire reliably for AsyncSession),
these are called explicitly by service methods at the right moment.

Usage in a service:
    from ..audit.helpers import audit_event_created, audit_state_transition, audit_correction

    await audit_event_created(self.db, event, self.current_user)
"""
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditAction, AuditLog, AuditModule


# ═══════════════════════════════════════════════════════════════════════════
# Core audit log factory
# ═══════════════════════════════════════════════════════════════════════════

async def _insert_audit_log(
    db: AsyncSession,
    *,
    user_id: int,
    company_id: int,
    action: AuditAction,
    entity_type: str,
    entity_id: str,
    module: AuditModule,
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
    """Create and persist an immutable AuditLog entry."""
    log = AuditLog(
        id=str(uuid4()),
        company_id=company_id,
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
    db.add(log)
    await db.flush()
    return log


# ═══════════════════════════════════════════════════════════════════════════
# Convenience functions for each action type
# ═══════════════════════════════════════════════════════════════════════════

async def audit_event_created(
    db: AsyncSession,
    event: Any,  # OperationalEvent
    current_user: dict[str, Any],
) -> AuditLog:
    """An operational event was created by an operator."""
    return await _insert_audit_log(
        db=db,
        user_id=current_user["id"],
        company_id=current_user.get("company_id", 0),
        action=AuditAction.CREATED,
        entity_type="operational_event",
        entity_id=str(event.id),
        module=AuditModule.OPERATIONS,
        lot_id=getattr(event, "lot_id", None),
        farm_id=getattr(event, "farm_id", None),
        house_id=getattr(event, "house_id", None),
        new_state=_status_str(event),
        comments=getattr(event, "observations", None),
    )


async def audit_state_transition(
    db: AsyncSession,
    event: Any,  # OperationalEvent
    current_user: dict[str, Any],
    old_status: str,
    new_status: str,
    comments: str | None = None,
) -> AuditLog:
    """The event's status changed (submit, review, approve, reject, cancel, etc.)."""
    action_map: dict[str, AuditAction] = {
        "pending_review": AuditAction.UPDATED,         # submitted for review
        "in_review":      AuditAction.REVIEW_STARTED,
        "returned":       AuditAction.RETURNED,
        "corrected":      AuditAction.CORRECTED,
        "approved":       AuditAction.APPROVED,
        "rejected":       AuditAction.REJECTED,
        "consolidated":   AuditAction.CONSOLIDATED,
        "sent_to_sap":    AuditAction.SENT_TO_SAP,
        "sap_confirmed":  AuditAction.SAP_CONFIRMED,
        "sap_error":      AuditAction.SAP_ERROR,
        "cancelled":      AuditAction.CANCELLED,
    }
    audit_action = action_map.get(new_status, AuditAction.UPDATED)

    module = AuditModule.OPERATIONS
    if audit_action in (AuditAction.APPROVED, AuditAction.REJECTED):
        module = AuditModule.APPROVALS
    elif audit_action in (AuditAction.REVIEW_STARTED, AuditAction.RETURNED, AuditAction.CORRECTED):
        module = AuditModule.REVIEW

    return await _insert_audit_log(
        db=db,
        user_id=current_user["id"],
        company_id=current_user.get("company_id", 0),
        action=audit_action,
        entity_type="operational_event",
        entity_id=str(event.id),
        module=module,
        lot_id=getattr(event, "lot_id", None),
        farm_id=getattr(event, "farm_id", None),
        house_id=getattr(event, "house_id", None),
        previous_state=old_status,
        new_state=new_status,
        comments=comments,
    )


async def audit_correction(
    db: AsyncSession,
    event_id: int,
    current_user: dict[str, Any],
    field_name: str,
    original_value: str | None,
    corrected_value: str | None,
    reason: str,
    lot_id: int | None = None,
) -> AuditLog:
    """A field-level correction was registered."""
    return await _insert_audit_log(
        db=db,
        user_id=current_user["id"],
        company_id=current_user.get("company_id", 0),
        action=AuditAction.CORRECTED,
        entity_type="operational_event",
        entity_id=str(event_id),
        module=AuditModule.CORRECTIONS,
        lot_id=lot_id,
        previous_values={field_name: original_value},
        new_values={field_name: corrected_value},
        change_reason=reason,
    )


async def audit_approval_action(
    db: AsyncSession,
    event_id: int,
    current_user: dict[str, Any],
    action_type: str,  # "approved", "rejected", "started_review", "returned"
    observations: str | None = None,
    lot_id: int | None = None,
) -> AuditLog:
    """An approval/review action was recorded."""
    action_map: dict[str, AuditAction] = {
        "started_review": AuditAction.REVIEW_STARTED,
        "returned":       AuditAction.RETURNED,
        "approved":       AuditAction.APPROVED,
        "rejected":       AuditAction.REJECTED,
    }
    audit_action = action_map.get(action_type, AuditAction.UPDATED)

    module = AuditModule.APPROVALS
    if audit_action in (AuditAction.REVIEW_STARTED, AuditAction.RETURNED):
        module = AuditModule.REVIEW

    return await _insert_audit_log(
        db=db,
        user_id=current_user["id"],
        company_id=current_user.get("company_id", 0),
        action=audit_action,
        entity_type="operational_event",
        entity_id=str(event_id),
        module=module,
        lot_id=lot_id,
        comments=observations,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Utility
# ═══════════════════════════════════════════════════════════════════════════

def _status_str(event: Any) -> str:
    """Extract status as string from an OperationalEvent."""
    status = getattr(event, "status", None)
    if status is None:
        return ""
    if hasattr(status, "value"):
        return status.value
    return str(status)


async def audit_accion(
    db: AsyncSession,
    *,
    usuario: dict[str, Any] | None,
    accion: AuditAction,
    modulo: AuditModule,
    entity_type: str,
    entity_id: str | None = None,
    company_id: int | None = None,
    **extra: Any,
) -> AuditLog | None:
    """Registro de auditoría para acciones fuera del ciclo del evento operativo.

    `GA-REM-032` / `R-81`. Los listeners solo vigilan `OperationalEvent`, `CorrectionLog` y
    `ApprovalAction`, de modo que seis de los once módulos declarados no producían ningún
    registro. Esta función cubre el resto —acceso, maestros, lotes, permisos, importación y
    exportación— reutilizando el mismo insertor y, por tanto, la misma transacción que la
    operación de negocio (`GA-REM-026`).

    `company_id` no es nulable en el modelo. Cuando la acción no puede atribuirse a ninguna
    empresa —un Super Admin sin contexto, o un intento de acceso con un usuario inexistente—
    **no se escribe** y se devuelve `None`. Es una limitación conocida y registrada como
    `R-83`; se prefiere dejarla visible antes que hacer nulable la columna y crear registros
    que ninguna consulta podría recuperar.
    """
    empresa = company_id if company_id is not None else (usuario or {}).get("company_id")
    if empresa is None:
        return None
    return await _insert_audit_log(
        db,
        user_id=(usuario or {}).get("id"),
        company_id=empresa,
        action=accion,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        module=modulo,
        **extra,
    )
