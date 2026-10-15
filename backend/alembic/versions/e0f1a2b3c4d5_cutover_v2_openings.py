"""SPEC 006 · Cutover v2 — apertura por unidad de negocio.

Aditiva y reversible:

    opening_balances   + población mixta, alojadas, salidas parciales, estados por métrica
                         que faltaban (placed/weight/eggs_to_hatchery/outbound/age) y
                         `template_version`
    hatchery_openings    nueva: proceso de incubación en curso al corte (1:1 con el opening)

Sin enums PostgreSQL nuevos (estados en `String(15)`). `downgrade()` elimina lo creado.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None

_CONTADORES = ("initial_mixed_count", "accumulated_mortality_mixed", "accumulated_culls_mixed")
_NULABLES = ("placed_male_count", "placed_female_count", "placed_mixed_count", "accumulated_outbound_birds")
_ESTADOS = ("placed_status", "weight_status", "eggs_to_hatchery_status", "outbound_status", "age_status",
            "initial_mixed_status")


def upgrade() -> None:
    for campo in _CONTADORES:
        op.add_column("opening_balances", sa.Column(campo, sa.Integer(), nullable=False, server_default="0"))
    for campo in _NULABLES:
        op.add_column("opening_balances", sa.Column(campo, sa.Integer(), nullable=True))
    for campo in _ESTADOS:
        op.add_column("opening_balances", sa.Column(campo, sa.String(15), nullable=False, server_default="KNOWN"))
    op.add_column("opening_balances", sa.Column("template_version", sa.String(10), nullable=True))

    op.create_table(
        "hatchery_openings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("opening_id", sa.Integer(), sa.ForeignKey("opening_balances.id"), nullable=False),
        sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column("hatchery_id", sa.Integer(), sa.ForeignKey("hatcheries.id"), nullable=False),
        sa.Column("incubator_id", sa.Integer(), sa.ForeignKey("incubators.id"), nullable=True),
        sa.Column("hatcher_id", sa.Integer(), sa.ForeignKey("hatchers.id"), nullable=True),
        sa.Column("source_lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=True),
        sa.Column("source_lot_reference", sa.String(100), nullable=True),
        sa.Column("generation", sa.String(20), nullable=True),
        sa.Column("reception_date", sa.Date(), nullable=False),
        sa.Column("set_date", sa.Date(), nullable=True),
        sa.Column("expected_hatch_date", sa.Date(), nullable=True),
        sa.Column("eggs_received", sa.Integer(), nullable=True),
        sa.Column("eggs_set", sa.Integer(), nullable=True),
        sa.Column("eggs_transferred", sa.Integer(), nullable=True),
        sa.Column("eggs_discarded", sa.Integer(), nullable=True),
        sa.Column("eggs_received_status", sa.String(15), nullable=False, server_default="KNOWN"),
        sa.Column("eggs_set_status", sa.String(15), nullable=False, server_default="KNOWN"),
        sa.Column("eggs_transferred_status", sa.String(15), nullable=False, server_default="KNOWN"),
        sa.Column("eggs_discarded_status", sa.String(15), nullable=False, server_default="KNOWN"),
        sa.Column("set_date_status", sa.String(15), nullable=False, server_default="KNOWN"),
        sa.Column("expected_hatch_date_status", sa.String(15), nullable=False, server_default="KNOWN"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("opening_id", name="uq_hatchery_openings_opening"),
        sa.UniqueConstraint("lot_id", name="uq_hatchery_openings_lot"),
    )
    op.create_index("ix_hatchery_openings_opening_id", "hatchery_openings", ["opening_id"])
    op.create_index("ix_hatchery_openings_lot_id", "hatchery_openings", ["lot_id"])
    op.create_index("ix_hatchery_openings_hatchery_id", "hatchery_openings", ["hatchery_id"])


def downgrade() -> None:
    op.drop_index("ix_hatchery_openings_hatchery_id", table_name="hatchery_openings")
    op.drop_index("ix_hatchery_openings_lot_id", table_name="hatchery_openings")
    op.drop_index("ix_hatchery_openings_opening_id", table_name="hatchery_openings")
    op.drop_table("hatchery_openings")
    op.drop_column("opening_balances", "template_version")
    for campo in reversed(_ESTADOS + _NULABLES + _CONTADORES):
        op.drop_column("opening_balances", campo)
