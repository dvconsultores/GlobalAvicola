"""
Audit context — context variable to carry current user info
through the request lifecycle into SQLAlchemy event listeners.

SQLAlchemy session events don't have access to FastAPI's
dependency injection, so we use a Python contextvars.ContextVar
that is set by get_current_user and read by audit listeners.
"""
from contextvars import ContextVar
from typing import Any

#: Carries the authenticated user dict during a request.
#: Set by get_current_user in app.auth.security.
#: Read by audit listeners in app.audit.listeners.
current_audit_user: ContextVar[dict[str, Any] | None] = ContextVar(
    "current_audit_user", default=None
)


def set_current_audit_user(user: dict[str, Any]) -> None:
    """Store the current user for audit purposes."""
    current_audit_user.set(user)


def get_current_audit_user() -> dict[str, Any] | None:
    """Retrieve the current user for audit purposes."""
    return current_audit_user.get()
