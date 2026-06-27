"""add idempotency_key to operational_events

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-27

Adds a client-generated UUID idempotency key to prevent duplicate event
submission from mobile clients with intermittent connectivity.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'operational_events',
        sa.Column('idempotency_key', sa.String(64), nullable=True),
    )
    op.create_index(
        'ix_operational_events_idempotency_key',
        'operational_events',
        ['idempotency_key'],
        unique=True,
        postgresql_where=sa.text('idempotency_key IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('ix_operational_events_idempotency_key', table_name='operational_events')
    op.drop_column('operational_events', 'idempotency_key')
