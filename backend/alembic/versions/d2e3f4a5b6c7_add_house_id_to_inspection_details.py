"""add house_id to inspection_details

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-06-26

Adds nullable house_id FK to inspection_details so each inspection
parameter can be scoped to a specific house (galpón), enabling
per-house temperature, humidity and litter data.
"""
from alembic import op
import sqlalchemy as sa

revision = 'd2e3f4a5b6c7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'inspection_details',
        sa.Column('house_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_inspection_detail_house',
        'inspection_details', 'houses',
        ['house_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_inspection_details_house_id',
        'inspection_details',
        ['house_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_inspection_details_house_id', table_name='inspection_details')
    op.drop_constraint('fk_inspection_detail_house', 'inspection_details', type_='foreignkey')
    op.drop_column('inspection_details', 'house_id')
