"""fundamento del acceso por unidad de negocio (`GA-REM-040` fase 1 · `OD-09` · `OD-10`)

Tres tablas y ninguna columna en las existentes. La fase 1 no toca `lots`, `operational_events`
ni ninguna otra: el filtro por fila es de la fase 3, y añadir ahora una columna que nadie lee
sería adelantar una decisión de diseño que todavía no toca tomar.

El catálogo se siembra desde `seeds/baseline_seeds.py` y **no aquí**, siguiendo el criterio que
el proyecto ya fijó: `l2m3n4o5p6q7` busca los roles por nombre y no los crea. Una migración que
inserta catálogo obliga a mantener el dato en dos sitios.

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "p6q7r8s9t0u1"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_units",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name_key", sa.String(length=100), nullable=False),
        sa.Column("bird_type", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_business_unit_code"),
    )
    op.create_index(op.f("ix_business_units_code"), "business_units", ["code"])

    op.create_table(
        "company_business_units",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("business_unit_id", sa.Integer(),
                  sa.ForeignKey("business_units.id"), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "business_unit_id",
                            name="uq_company_business_unit"),
    )
    op.create_index(op.f("ix_company_business_units_company_id"),
                    "company_business_units", ["company_id"])
    op.create_index(op.f("ix_company_business_units_business_unit_id"),
                    "company_business_units", ["business_unit_id"])

    # Sin `ondelete` hacia `company_business_units`: apagar una unidad a una empresa **no**
    # puede destruir las concesiones de sus usuarios mientras `BU-D10` siga pendiente de
    # ratificación. La concesión sobrevive y deja de ser efectiva, que es reversible; borrarla
    # no lo sería.
    op.create_table(
        "user_business_units",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("business_unit_id", sa.Integer(),
                  sa.ForeignKey("business_units.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "business_unit_id", name="uq_user_business_unit"),
    )
    op.create_index(op.f("ix_user_business_units_user_id"),
                    "user_business_units", ["user_id"])
    op.create_index(op.f("ix_user_business_units_business_unit_id"),
                    "user_business_units", ["business_unit_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_user_business_units_business_unit_id"),
                  table_name="user_business_units")
    op.drop_index(op.f("ix_user_business_units_user_id"), table_name="user_business_units")
    op.drop_table("user_business_units")
    op.drop_index(op.f("ix_company_business_units_business_unit_id"),
                  table_name="company_business_units")
    op.drop_index(op.f("ix_company_business_units_company_id"),
                  table_name="company_business_units")
    op.drop_table("company_business_units")
    op.drop_index(op.f("ix_business_units_code"), table_name="business_units")
    op.drop_table("business_units")
