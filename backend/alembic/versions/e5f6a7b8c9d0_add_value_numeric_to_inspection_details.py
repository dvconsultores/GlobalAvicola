"""add value_numeric to inspection_details

Revision ID: e5f6a7b8c9d0
Revises: d2e3f4a5b6c7
Create Date: 2026-06-27

Adds a DECIMAL column for numeric inspection values (temperature, humidity, etc.)
alongside the existing string `value` column for backward compatibility.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'inspection_details',
        sa.Column('value_numeric', sa.Numeric(10, 3), nullable=True),
    )
    op.create_index(
        'ix_inspection_details_value_numeric',
        'inspection_details',
        ['value_numeric'],
    )


def downgrade() -> None:
    op.drop_index('ix_inspection_details_value_numeric', table_name='inspection_details')
    op.drop_column('inspection_details', 'value_numeric')
