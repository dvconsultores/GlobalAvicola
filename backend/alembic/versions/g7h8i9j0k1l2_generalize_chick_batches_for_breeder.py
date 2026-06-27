"""generalize chick_batches for breeder + add generation to egg_batches

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-27

- Adds destination_lot_id to chick_batches (generalizes from broiler-only)
- Adds generation column to egg_batches (grandparent vs breeder)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # chick_batches: add generalized destination_lot_id alongside broiler_lot_id
    op.add_column(
        'chick_batches',
        sa.Column('destination_lot_id', sa.Integer(), nullable=True),
    )
    op.create_index(
        'ix_chick_batches_destination_lot_id',
        'chick_batches',
        ['destination_lot_id'],
    )
    op.create_foreign_key(
        'fk_chick_batches_destination_lot_id',
        'chick_batches',
        'lots',
        ['destination_lot_id'],
        ['id'],
    )

    # Migrate existing broiler_lot_id → destination_lot_id for data consistency
    op.execute(
        'UPDATE chick_batches SET destination_lot_id = broiler_lot_id WHERE broiler_lot_id IS NOT NULL'
    )

    # egg_batches: add generation discriminator
    op.add_column(
        'egg_batches',
        sa.Column('generation', sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('egg_batches', 'generation')
    op.drop_constraint('fk_chick_batches_destination_lot_id', 'chick_batches', type_='foreignkey')
    op.drop_index('ix_chick_batches_destination_lot_id', table_name='chick_batches')
    op.drop_column('chick_batches', 'destination_lot_id')
