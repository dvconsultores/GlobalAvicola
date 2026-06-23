"""
CorrectionLog model — immutable audit trail for field-level corrections.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class CorrectionLog(Base):
    """Audit trail for every field-level correction made to an operational event."""
    __tablename__ = "correction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("operational_events.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(100))  # e.g. "quantity", "event_date"
    original_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    correction_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("correction_types.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text)  # Mandatory reason
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<CorrectionLog field={self.field_name} event={self.event_id}>"
