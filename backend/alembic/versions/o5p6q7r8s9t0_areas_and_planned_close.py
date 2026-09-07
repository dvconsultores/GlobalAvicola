"""áreas funcionales y fecha prevista de cierre (`GA-REM-039` / `GA-REM-038` B / `OD-08`)

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-09-07

`OD-08` decidió que los avisos de `P-14` lleguen también al gerente y al supervisor **del
área**, y que «lote próximo a cierre» signifique tres días antes de la fecha **prevista**.

Todo lo que se añade es nulable. Existen usuarios y lotes anteriores a esta migración, y no
hay fuente segura para completarlos: asignarles un área por su rol, o una fecha de cierre por
su genética, sería fabricar el dato que después se notifica.

`end_date` **no se toca**. Sigue significando la fecha real de cierre, que fija `close_lot`
(`R-73`, `R-75`).
"""
from alembic import op
import sqlalchemy as sa

revision = "o5p6q7r8s9t0"
down_revision = "n4o5p6q7r8s9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # Nulable como en los otros maestros, aunque el uso real siempre la trae: el patrón
        # de `MasterService` la asigna desde el usuario cuando llega vacía.
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        # Baja lógica: un área con usuarios, lotes o avisos históricos no se borra.
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_areas_company_id"), "areas", ["company_id"])

    # Sin `CASCADE` en ninguna de las dos: dar de baja un área no puede arrastrarse usuarios
    # ni lotes. La baja es lógica y el histórico se conserva.
    op.add_column("users", sa.Column("area_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_area", "users", "areas", ["area_id"], ["id"])
    op.create_index(op.f("ix_users_area_id"), "users", ["area_id"])

    op.add_column("lots", sa.Column("area_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_lots_area", "lots", "areas", ["area_id"], ["id"])
    op.create_index(op.f("ix_lots_area_id"), "lots", ["area_id"])

    # La fecha **prevista**. Distinta de `end_date`, que es la real.
    op.add_column("lots", sa.Column("planned_close_date",
                                    sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("lots", "planned_close_date")
    op.drop_index(op.f("ix_lots_area_id"), table_name="lots")
    op.drop_constraint("fk_lots_area", "lots", type_="foreignkey")
    op.drop_column("lots", "area_id")
    op.drop_index(op.f("ix_users_area_id"), table_name="users")
    op.drop_constraint("fk_users_area", "users", type_="foreignkey")
    op.drop_column("users", "area_id")
    op.drop_index(op.f("ix_areas_company_id"), table_name="areas")
    op.drop_table("areas")
