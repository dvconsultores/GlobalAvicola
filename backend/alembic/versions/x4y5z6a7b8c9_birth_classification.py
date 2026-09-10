"""sanos y débiles al nacer (`GA-REM-021-C` · `B13` · `H360-B13` · `Bases` p.9)

«Número de Pollitos Sanos: cantidad de pollitos nacidos sanos y viables» y «Número de Pollitos Débiles: cantidad de
pollitos nacidos débiles o con problemas». Son dos atributos del nacimiento (`birth_registration` de un lote de
incubadora), subconjuntos disjuntos de los nacidos; **no** entran en ningún saldo (los nacidos siguen siendo
Σ `bird_movements.quantity`, `BR-21`, `GA-REM-005-C`). Dos enteros nulos en `operational_events`, como los demás
escalares por tipo de evento. Filas históricas `NULL` (no declarado); sin relleno.

Revision ID: x4y5z6a7b8c9
Revises: w3x4y5z6a7b8
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "x4y5z6a7b8c9"
down_revision = "w3x4y5z6a7b8"
branch_labels = None
depends_on = None

COLUMNAS = ("chicks_healthy", "chicks_weak")


def upgrade() -> None:
    for columna in COLUMNAS:
        op.add_column("operational_events", sa.Column(columna, sa.Integer(), nullable=True))


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM operational_events WHERE chicks_healthy IS NOT NULL OR chicks_weak IS NOT NULL) THEN
                RAISE EXCEPTION 'No se puede bajar x4y5z6a7b8c9: existen nacimientos con sanos/débiles declarados (GA-REM-021-C)';
            END IF;
        END $$;
    """)
    for columna in reversed(COLUMNAS):
        op.drop_column("operational_events", columna)
