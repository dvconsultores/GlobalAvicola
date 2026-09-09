"""cuadre de la recepción de reproductoras: recibidas, mortalidad al arribo y rechazo (`GA-REM-021-B` · `B01` · `H360-B01`)

`Recomendación central §6`: «Que hembras + machos + mortalidad + rechazo cuadren contra recibido». El modelo
solo persistía las aves alojadas por sexo y galpón (`bird_movements`); los otros tres datos de la misma captura
no tenían dónde vivir y la identidad no era comprobable. Tres enteros en `operational_events`, como los demás
escalares por tipo de evento (`sample_size`, `water_liters`):

    received_total        aves recibidas declaradas (≥ 1)
    dead_on_arrival       muertas al arribo (≥ 0)
    rejected_on_arrival   rechazadas (≥ 0)

Las alojadas no se persisten: son Σ `bird_movements.quantity`, las entradas del saldo (`R-130`, sin cambio).
Las filas históricas quedan `NULL` (no declarado); no se rellena nada. La bajada se detiene si alguna fila
tiene alguno de los tres declarado.

Revision ID: w3x4y5z6a7b8
Revises: v2w3x4y5z6a7
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "w3x4y5z6a7b8"
down_revision = "v2w3x4y5z6a7"
branch_labels = None
depends_on = None

COLUMNAS = ("received_total", "dead_on_arrival", "rejected_on_arrival")


def upgrade() -> None:
    for columna in COLUMNAS:
        op.add_column("operational_events", sa.Column(columna, sa.Integer(), nullable=True))


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM operational_events
                       WHERE received_total IS NOT NULL OR dead_on_arrival IS NOT NULL OR rejected_on_arrival IS NOT NULL) THEN
                RAISE EXCEPTION 'No se puede bajar w3x4y5z6a7b8: existen recepciones con cuadre declarado (GA-REM-021-B)';
            END IF;
        END $$;
    """)
    for columna in reversed(COLUMNAS):
        op.drop_column("operational_events", columna)
