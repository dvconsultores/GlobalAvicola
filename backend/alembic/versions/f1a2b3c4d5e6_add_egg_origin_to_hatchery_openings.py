"""SPEC 009 · egg_origin (origen comercial del huevo) en hatchery_openings.

Aditiva y reversible:

    hatchery_openings    + `egg_origin` (`String(20)`, nulo = no declarado): `internal` (huevo propio)
                           o `purchased` (huevo comprado)

Sin enums PostgreSQL nuevos. `downgrade()` elimina la columna.

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("hatchery_openings", sa.Column("egg_origin", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("hatchery_openings", "egg_origin")
