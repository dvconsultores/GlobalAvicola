"""SPEC 018 · incubadora v4 — desglose de no incubables y huevos fértiles a fosa.

Aditiva y reversible:

    hatchery_openings   + `eggs_non_incubable_oversized` / `..._dirty` / `..._broken` (INT, nulo = UNKNOWN):
                          clasificación del huevo recibido que NO se cargó en incubadora
                        + `fertile_eggs_to_pit` (INT, nulo = UNKNOWN):
                          huevos fértiles enviados a fosa antes del corte
                        + sus `*_status` (`String(15)`, `NOT NULL`, server_default `UNKNOWN`):
                          semántica por componente (NULL nunca es «0 conocido»)

`eggs_discarded` / `eggs_discarded_status` se **conservan** (histórico V3). Las aperturas
anteriores quedan con el desglose en `UNKNOWN`: no se inventan ceros ni se reparten históricos.

Sin enums PostgreSQL nuevos. `downgrade()` elimina las ocho columnas.

Revision ID: h3c4d5e6f7a8
Revises: g2b3c4d5e6f7
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "h3c4d5e6f7a8"
down_revision = "g2b3c4d5e6f7"
branch_labels = None
depends_on = None

_COMPONENTES = ("eggs_non_incubable_oversized", "eggs_non_incubable_dirty", "eggs_non_incubable_broken",
                "fertile_eggs_to_pit")


def upgrade() -> None:
    for campo in _COMPONENTES:
        op.add_column("hatchery_openings", sa.Column(campo, sa.Integer(), nullable=True))
    for campo in _COMPONENTES:
        op.add_column("hatchery_openings", sa.Column(f"{campo}_status", sa.String(length=15),
                                                    nullable=False, server_default="UNKNOWN"))


def downgrade() -> None:
    for campo in reversed(_COMPONENTES):
        op.drop_column("hatchery_openings", f"{campo}_status")
    for campo in reversed(_COMPONENTES):
        op.drop_column("hatchery_openings", campo)
