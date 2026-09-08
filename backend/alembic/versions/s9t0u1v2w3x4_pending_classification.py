"""clasificación pendiente de la cadena productiva (`GA-REM-040` fase 6 · `OD-10.c`)

Un evento sin lote —las inspecciones de granja lo permiten desde `i9j0k1l2m3n4`— no puede
derivar su cadena. `OD-10.c` decidió que no se adivine, no se abra y no se borre: queda
**pendiente de clasificar**, visible para quien lo registró y para el control autorizado.

El estado **no se persiste**: se deriva. Un evento está pendiente cuando ni su lote ni esta
columna dicen a qué cadena pertenece. Guardar además un `status` daría dos fuentes que acabarían
discrepando el día que alguien rellene el lote sin tocar el estado.

`business_unit_id` apunta a `company_business_units` y no al catálogo, por la misma razón que la
concesión de un usuario (`OD-09.d`): la fila dice bajo qué empresa se clasificó, y la combinación
entre empresas no se puede ni escribir.

Revision ID: s9t0u1v2w3x4
Revises: r8s9t0u1v2w3
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s9t0u1v2w3x4"
down_revision = "r8s9t0u1v2w3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("operational_events",
                  sa.Column("business_unit_id", sa.Integer(), nullable=True))
    op.add_column("operational_events",
                  sa.Column("classified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("operational_events",
                  sa.Column("classified_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_operational_events_bu", "operational_events",
                          "company_business_units", ["business_unit_id"], ["id"])
    op.create_foreign_key("fk_operational_events_classified_by", "operational_events",
                          "users", ["classified_by_id"], ["id"])
    op.create_index(op.f("ix_operational_events_business_unit_id"),
                    "operational_events", ["business_unit_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_operational_events_business_unit_id"),
                  table_name="operational_events")
    op.drop_constraint("fk_operational_events_classified_by", "operational_events",
                       type_="foreignkey")
    op.drop_constraint("fk_operational_events_bu", "operational_events",
                       type_="foreignkey")
    op.drop_column("operational_events", "classified_by_id")
    op.drop_column("operational_events", "classified_at")
    op.drop_column("operational_events", "business_unit_id")
