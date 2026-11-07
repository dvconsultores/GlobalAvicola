"""SPEC 014 · transferencias históricas entre lotes en opening_balances.

Aditiva y reversible:

    opening_balances    + `accumulated_transfers_in_male` / `..._in_female` (INT, nulo = UNKNOWN):
                          aves recibidas desde otros lotes antes del corte
                        + `accumulated_transfers_out_male` / `..._out_female` (INT, nulo = UNKNOWN):
                          aves enviadas a otros lotes antes del corte
                        + `transfers_in_status` / `transfers_out_status` (`String(15)`, `UNKNOWN`):
                          semántica del acumulado por sentido (NULL nunca es «0 conocido»)

Las aperturas anteriores quedan en `UNKNOWN`: no se inventan ceros.

Sin enums PostgreSQL nuevos. `downgrade()` elimina las seis columnas.

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "g2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("opening_balances", sa.Column("accumulated_transfers_in_male", sa.Integer(), nullable=True))
    op.add_column("opening_balances", sa.Column("accumulated_transfers_in_female", sa.Integer(), nullable=True))
    op.add_column("opening_balances", sa.Column("accumulated_transfers_out_male", sa.Integer(), nullable=True))
    op.add_column("opening_balances", sa.Column("accumulated_transfers_out_female", sa.Integer(), nullable=True))
    op.add_column("opening_balances", sa.Column("transfers_in_status", sa.String(length=15),
                                                nullable=False, server_default="UNKNOWN"))
    op.add_column("opening_balances", sa.Column("transfers_out_status", sa.String(length=15),
                                                nullable=False, server_default="UNKNOWN"))


def downgrade() -> None:
    op.drop_column("opening_balances", "transfers_out_status")
    op.drop_column("opening_balances", "transfers_in_status")
    op.drop_column("opening_balances", "accumulated_transfers_out_female")
    op.drop_column("opening_balances", "accumulated_transfers_out_male")
    op.drop_column("opening_balances", "accumulated_transfers_in_female")
    op.drop_column("opening_balances", "accumulated_transfers_in_male")
