"""Add egg_batches and chick_batches for generational traceability (T-083).

Revision ID: f1e2d3c4b5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "f1e2d3c4b5a6"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── egg_batches ───────────────────────────────────────────────────────────
    op.create_table(
        "egg_batches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_lot_id", sa.Integer, sa.ForeignKey("lots.id"), nullable=False, index=True),
        sa.Column("hatchery_lot_id", sa.Integer, sa.ForeignKey("lots.id"), nullable=True, index=True),
        sa.Column("dispatch_event_id", sa.Integer, sa.ForeignKey("operational_events.id"), nullable=True),
        sa.Column("reception_event_id", sa.Integer, sa.ForeignKey("operational_events.id"), nullable=True),
        sa.Column("quantity_dispatched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("quantity_received", sa.Integer, nullable=True),
        sa.Column("dispatch_date", sa.Date, nullable=False),
        sa.Column("reception_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── chick_batches ─────────────────────────────────────────────────────────
    op.create_table(
        "chick_batches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("hatchery_lot_id", sa.Integer, sa.ForeignKey("lots.id"), nullable=False, index=True),
        sa.Column("broiler_lot_id", sa.Integer, sa.ForeignKey("lots.id"), nullable=True, index=True),
        sa.Column("dispatch_event_id", sa.Integer, sa.ForeignKey("operational_events.id"), nullable=True),
        sa.Column("reception_event_id", sa.Integer, sa.ForeignKey("operational_events.id"), nullable=True),
        sa.Column("egg_batch_id", sa.Integer, sa.ForeignKey("egg_batches.id"), nullable=True),
        sa.Column("quantity_dispatched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("quantity_received", sa.Integer, nullable=True),
        sa.Column("dispatch_date", sa.Date, nullable=False),
        sa.Column("reception_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("chick_batches")
    op.drop_table("egg_batches")
