"""merge_hatchery_purpose_and_company_indexes

Revision ID: c574733bab64
Revises: 4982c3092c14, h8i9j0k1l2m3
Create Date: 2026-06-29 18:35:36.593486
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c574733bab64'
down_revision: Union[str, None] = ('4982c3092c14', 'h8i9j0k1l2m3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
