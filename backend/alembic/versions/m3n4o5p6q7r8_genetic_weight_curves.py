"""curvas estándar de peso por línea genética (`GA-REM-037` / `OD-06`)

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-09-06

`spec.md §4.5` exige alertar cuando el peso queda fuera de la curva estándar, y `OD-06`
resolvió de dónde sale esa curva: una tabla por línea genética, versionada, que el
administrador carga.

Todo lo que se añade es **nulable u opcional**: `lots.weight_curve_id` no rompe a los lotes
existentes —que no tienen genética y a los que no se les inventa—, ni a los clientes de la API.
"""
from alembic import op
import sqlalchemy as sa

revision = "m3n4o5p6q7r8"
down_revision = "l2m3n4o5p6q7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "genetic_weight_curves",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("genetic_line_id", sa.Integer(), nullable=False),
        sa.Column("version_label", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["genetic_line_id"], ["genetic_lines.id"]),
        sa.PrimaryKeyConstraint("id"),
        # Dos versiones con el mismo nombre en una línea harían ambigua la referencia.
        sa.UniqueConstraint("genetic_line_id", "version_label", name="uq_curve_line_version"),
    )
    op.create_index(op.f("ix_genetic_weight_curves_genetic_line_id"),
                    "genetic_weight_curves", ["genetic_line_id"])

    op.create_table(
        "genetic_weight_curve_points",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("curve_id", sa.Integer(), nullable=False),
        sa.Column("age_days", sa.Integer(), nullable=False),
        sa.Column("target_weight", sa.Float(), nullable=True),
        sa.Column("min_weight", sa.Float(), nullable=False),
        sa.Column("max_weight", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["curve_id"], ["genetic_weight_curves.id"],
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Dos valores contradictorios para el mismo día harían la curva ambigua.
        sa.UniqueConstraint("curve_id", "age_days", name="uq_curve_point_age"),
    )
    op.create_index(op.f("ix_genetic_weight_curve_points_curve_id"),
                    "genetic_weight_curve_points", ["curve_id"])

    # La **versión concreta** del lote, no la activa del momento: publicar una curva nueva no
    # puede reescribir la referencia histórica de los lotes ya en marcha.
    op.add_column("lots", sa.Column("weight_curve_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_lots_weight_curve", "lots", "genetic_weight_curves",
                          ["weight_curve_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_lots_weight_curve", "lots", type_="foreignkey")
    op.drop_column("lots", "weight_curve_id")
    op.drop_index(op.f("ix_genetic_weight_curve_points_curve_id"),
                  table_name="genetic_weight_curve_points")
    op.drop_table("genetic_weight_curve_points")
    op.drop_index(op.f("ix_genetic_weight_curves_genetic_line_id"),
                  table_name="genetic_weight_curves")
    op.drop_table("genetic_weight_curves")
