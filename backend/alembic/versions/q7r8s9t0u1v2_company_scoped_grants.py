"""la concesión se acota a la empresa que la otorgó (`GA-REM-040` enm. A · `OD-09.d`)

`user_business_units` apuntaba al catálogo de unidades, de modo que la fila no decía de qué
empresa venía. Pasa a apuntar a `company_business_units`.

**Sobre el dato existente.** `ENV-01` establece que lo desplegado es de desarrollo, prueba y
certificación, y ninguna semilla crea concesiones: en la práctica no hay filas. Aun así la
conversión no adivina —`§22`—: resuelve la habilitación por la empresa **actual** del usuario, y
si alguna fila no se puede resolver **se detiene con un error** en lugar de borrarla o de
inventarle una empresa. Perder en silencio una concesión sería peor que fallar la migración.

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "q7r8s9t0u1v2"
down_revision = "p6q7r8s9t0u1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_business_units",
        sa.Column("company_business_unit_id", sa.Integer(), nullable=True),
    )

    # La habilitación correspondiente, buscada por la empresa ACTUAL del usuario y la unidad
    # que la concesión nombraba. Es derivación de dato persistido, no conjetura.
    op.execute(
        """
        UPDATE user_business_units AS ubu
           SET company_business_unit_id = cbu.id
          FROM users AS u, company_business_units AS cbu
         WHERE u.id = ubu.user_id
           AND cbu.company_id = u.company_id
           AND cbu.business_unit_id = ubu.business_unit_id
        """
    )

    huerfanas = op.get_bind().execute(
        sa.text("SELECT count(*) FROM user_business_units "
                "WHERE company_business_unit_id IS NULL")
    ).scalar()
    if huerfanas:
        raise RuntimeError(
            f"{huerfanas} concesiones sin habilitación de empresa resoluble. "
            "No se borran ni se les inventa empresa: resuélvanse a mano y reintente."
        )

    op.alter_column("user_business_units", "company_business_unit_id", nullable=False)
    op.create_foreign_key(
        "fk_user_business_units_cbu", "user_business_units",
        "company_business_units", ["company_business_unit_id"], ["id"],
    )
    op.create_index(op.f("ix_user_business_units_company_business_unit_id"),
                    "user_business_units", ["company_business_unit_id"])
    op.create_unique_constraint(
        "uq_user_company_business_unit", "user_business_units",
        ["user_id", "company_business_unit_id"],
    )

    op.drop_constraint("uq_user_business_unit", "user_business_units", type_="unique")
    op.drop_index(op.f("ix_user_business_units_business_unit_id"),
                  table_name="user_business_units")
    op.drop_column("user_business_units", "business_unit_id")


def downgrade() -> None:
    op.add_column("user_business_units",
                  sa.Column("business_unit_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE user_business_units AS ubu
           SET business_unit_id = cbu.business_unit_id
          FROM company_business_units AS cbu
         WHERE cbu.id = ubu.company_business_unit_id
        """
    )
    op.alter_column("user_business_units", "business_unit_id", nullable=False)
    op.create_foreign_key("fk_user_business_units_bu", "user_business_units",
                          "business_units", ["business_unit_id"], ["id"])
    op.create_index(op.f("ix_user_business_units_business_unit_id"),
                    "user_business_units", ["business_unit_id"])
    op.create_unique_constraint("uq_user_business_unit", "user_business_units",
                                ["user_id", "business_unit_id"])
    op.drop_constraint("uq_user_company_business_unit", "user_business_units", type_="unique")
    op.drop_index(op.f("ix_user_business_units_company_business_unit_id"),
                  table_name="user_business_units")
    op.drop_constraint("fk_user_business_units_cbu", "user_business_units",
                       type_="foreignkey")
    op.drop_column("user_business_units", "company_business_unit_id")
