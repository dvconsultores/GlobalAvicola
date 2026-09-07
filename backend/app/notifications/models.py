"""Notificaciones internas — `GA-REM-038`, decisión `OD-07`.

Una notificación pertenece a **una persona**. Es lo que la separa de las otras dos cosas que
el sistema ya guardaba y con las que es fácil confundirla:

    OperationalAlert   pertenece al LOTE       no tiene destinatario ni lectura
    AuditLog           pertenece al SISTEMA    historia inmutable, `P-09`
    Notification       pertenece a UNA PERSONA bandeja con estado de lectura

Reutilizar `AuditLog` como buzón habría mezclado dos procesos certificados por separado.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime, ForeignKey, Index, Integer, String, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Notification(Base):
    """Un aviso dirigido a un usuario concreto."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), index=True)
    recipient_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True)

    #: `record_rejected` · `sap_send_failed`. Los dos tipos de `docs/02 §3.14` que tienen
    #: disparador **y** destinatario escritos; los otros cuatro esperan a `OD-08`.
    notification_type: Mapped[str] = mapped_column(String(50))

    #: Datos con los que se compone el texto al mostrarlo. **No** se guarda la frase ya
    #: redactada: quedaría congelada en el idioma que tuviera el servidor ese día, y un
    #: usuario que cambia a inglés seguiría leyendo español. Tampoco lleva secretos ni
    #: trazas internas.
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    #: Genérico y sin clave foránea a propósito: los tipos apuntan a tablas distintas, y una
    #: columna por cada uno haría crecer el modelo con cada evento nuevo. El efecto buscado
    #: es además que **borrar la entidad no borre el aviso**: sin `FK` no hay `CASCADE`, y el
    #: historial sobrevive a la desaparición de aquello de lo que informaba.
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    #: `NULL` es no leída. Sin enum de estados: no hay `SENT`, `DELIVERED` ni `OPENED`,
    #: que son de correo y de push, y los dos están fuera de alcance por `OD-07`.
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Las dos consultas reales son «mi bandeja, la más reciente primero» y «cuántas
        # tengo sin leer». Nada más se indexa: optimizar de más también cuesta.
        Index("ix_notifications_bandeja", "recipient_user_id", "created_at"),
        Index("ix_notifications_sin_leer", "recipient_user_id", "read_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification {self.notification_type} → user={self.recipient_user_id}>"
