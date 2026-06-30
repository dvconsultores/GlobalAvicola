"""make operational_events.lot_id nullable for inspection events

Revision ID: i9j0k1l2m3n4
Revises: c574733bab64
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, None] = 'c574733bab64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('operational_events', 'lot_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column('operational_events', 'lot_id', existing_type=sa.Integer(), nullable=False)
