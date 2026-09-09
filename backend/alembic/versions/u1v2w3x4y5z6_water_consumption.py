"""consumo diario de agua: tipo de evento y columna (`GA-REM-021` enmienda A · `B05` · `R-13` · `H360-B05`)

El cliente exige «Cantidad de agua consumida … durante el día» en Reproductoras (cría y producción) y
Engorde (`Bases Consideradas…pdf` p.2, 4, 12) y el sistema no tenía dónde guardarla. Un dato, un registro:
`water_consumption` es un tipo de evento propio (con su cola de revisión, su corrección y su serie) y
`water_liters` su valor, en litros (`RR-10`), estrictamente positivo (`RR-11`), como `quantity_kg`.

`eventtype` es un enumerado nativo de PostgreSQL: el miembro se añade con `ADD VALUE IF NOT EXISTS`
(patrón `j0k1l2m3n4o5`). Las filas existentes quedan con `water_liters = NULL`: la ausencia de dato es
ausencia, nunca `0` (`RR-11`). La bajada retira la columna y se detiene si existen eventos de agua; el
miembro del enumerado permanece (PostgreSQL no lo elimina).

Revision ID: u1v2w3x4y5z6
Revises: t0u1v2w3x4y5
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "u1v2w3x4y5z6"
down_revision = "t0u1v2w3x4y5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'WATER_CONSUMPTION'")
    op.add_column("operational_events", sa.Column("water_liters", sa.Float(), nullable=True))


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM operational_events WHERE event_type = 'WATER_CONSUMPTION') THEN
                RAISE EXCEPTION 'No se puede bajar u1v2w3x4y5z6: existen eventos WATER_CONSUMPTION (GA-REM-021-A)';
            END IF;
        END $$;
    """)
    op.drop_column("operational_events", "water_liters")
