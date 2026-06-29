"""
Auditoría automática — SQLAlchemy event listeners.

Los listeners se registran llamando a `register_audit_listeners()` durante
el arranque de la aplicación (en main.py lifespan).

Principio: Todo lo que ocurre en el sistema queda registrado.
Nada se borra. Todo se audita.
"""

_registered = False


def register_audit_listeners() -> None:
    """
    Register SQLAlchemy after_flush listeners that automatically
    create AuditLog entries for every relevant data change.

    Idempotent — calling multiple times has no effect.
    """
    global _registered
    if _registered:
        return

    # Import triggers the @event.listens_for decorators
    from . import listeners  # noqa: F401

    _registered = True

