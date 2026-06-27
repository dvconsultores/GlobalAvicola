"""add hatchery_purpose to lots

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-06-27

Adds hatchery_purpose to distinguish grandparent-egg incubation
(→ breeder chicks) from breeder-egg incubation (→ broiler chicks).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'lots',
        sa.Column('hatchery_purpose', sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('lots', 'hatchery_purpose')
