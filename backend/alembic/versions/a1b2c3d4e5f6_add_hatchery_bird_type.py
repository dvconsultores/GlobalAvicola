"""add_hatchery_bird_type

Revision ID: a1b2c3d4e5f6
Revises: bfcc893f581a
Create Date: 2026-06-24 00:00:00.000000

Add HATCHERY value to birdtypeenum PostgreSQL enum type.
This enables incubadora lots to be tracked as a first-class lot type.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'bfcc893f581a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL ALTER TYPE ADD VALUE cannot run inside a transaction block.
    # Alembic executes DDL outside transactions when using the 'postgresql'
    # dialect with `execute_timeout` or via op.execute() in non-transactional mode.
    # We use COMMIT/BEGIN to work around this in environments that auto-wrap.
    op.execute("COMMIT")
    op.execute("ALTER TYPE birdtypeenum ADD VALUE IF NOT EXISTS 'hatchery'")
    op.execute("BEGIN")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values natively.
    # Downgrade is a no-op; enum values are additive.
    pass
