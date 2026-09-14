"""Arnés de auditoría en runtime — `P1-12-REOPEN`.

El `lifespan` de uvicorn registra el listener `after_flush`; el transporte ASGI del arnés
de tests no lo hace, por lo que la duplicación listener↔helpers y los productores del
listener no eran visibles (`FINDING §1.2`). Los módulos que verifican conteos de auditoría
en runtime declaran::

    from tests.audit_harness import listener_auditoria_como_runtime  # noqa: F401
    pytestmark = pytest.mark.usefixtures("listener_auditoria_como_runtime")

El registro es por test (se retira al terminar) para no alterar al resto de la suite.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def listener_auditoria_como_runtime():
    """Registra el listener de auditoría durante el test (equivalente al `lifespan`)."""
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    from app.audit import listeners as audit_listeners

    presente = event.contains(Session, "after_flush", audit_listeners.audit_after_flush)
    if not presente:
        event.listen(Session, "after_flush", audit_listeners.audit_after_flush)
    yield
    event.remove(Session, "after_flush", audit_listeners.audit_after_flush)
