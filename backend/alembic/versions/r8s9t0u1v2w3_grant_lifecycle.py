"""la concesión se marca al cambiar de empresa, no se borra (`OD-09.e` · `AC-B12`)

`OD-09.e` exige que volver a una empresa anterior **no** reactive la concesión que se tuvo allí.
Eso no se puede cumplir sin registrar la salida: sin una marca, «volvió a A» y «nunca salió de A»
son el mismo estado y el resolutor no tiene con qué distinguirlos.

Se añade `revoked_at`, nulable. Y la unicidad pasa a ser **parcial**: única entre las vivas, de
modo que una concesión revocada pueda volver a otorgarse. Con la restricción total, revocar
habría dejado al usuario sin poder recuperar nunca ese acceso, que no es lo que revocar
significa.

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "r8s9t0u1v2w3"
down_revision = "q7r8s9t0u1v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # `OD-11 §6` / `AC-I06`: el cambio de contexto de empresa se audita, y `auditaction` es un
    # tipo enumerado **nativo** de PostgreSQL. Añadir el miembro solo en Python haría que cada
    # `switch-company` terminase en 500 — el hueco exacto que `test_los_enums_de_python_existen_
    # en_postgresql` vigila desde que `EGG_RECEPTION_CLASSIFICATION` faltó en `eventtype`.
    #
    # SQLAlchemy persiste el **nombre** del miembro, en mayúsculas, no su valor.
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'CONTEXT_SWITCHED'")

    op.add_column("user_business_units",
                  sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint("uq_user_company_business_unit", "user_business_units", type_="unique")
    op.create_index(
        "uq_user_company_business_unit", "user_business_units",
        ["user_id", "company_business_unit_id"],
        unique=True, postgresql_where=sa.text("revoked_at IS NULL"),
    )


def downgrade() -> None:
    # Una concesión revocada no puede sobrevivir a la vuelta atrás si colisiona con la viva:
    # se retiran las revocadas, que es lo único que la restricción total admite.
    op.execute("DELETE FROM user_business_units WHERE revoked_at IS NOT NULL")
    op.drop_index("uq_user_company_business_unit", table_name="user_business_units")
    op.create_unique_constraint("uq_user_company_business_unit", "user_business_units",
                                ["user_id", "company_business_unit_id"])
    op.drop_column("user_business_units", "revoked_at")
