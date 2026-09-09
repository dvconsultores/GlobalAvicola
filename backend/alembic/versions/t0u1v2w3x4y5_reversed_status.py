"""el reverso interno tiene estado propio: `REVERSED` (`OD-19 §1` · `GA-REM-041` · `R-136`)

`OD-19` decide que un registro aprobado y neutralizado no es un `CANCELLED` —que significa «flujo
detenido antes de producir efecto»— sino un estado distinto: fue válido, produjo efecto, y ese
efecto quedó compensado por una contrapartida aprobada. `eventstatus` y `auditaction` son tipos
enumerados **nativos** de PostgreSQL: añadir el miembro solo en Python terminaría en 500 en la
primera aprobación de un reverso (la deriva que `test_los_enums_de_python_existen_en_postgresql`
vigila). SQLAlchemy persiste el **nombre** del miembro, en mayúsculas.

La bajada no retira los valores: PostgreSQL no elimina miembros de un enumerado. Si existieran
filas `REVERSED`, la bajada se detiene con un error explícito en lugar de dejarlas huérfanas.

Revision ID: t0u1v2w3x4y5
Revises: s9t0u1v2w3x4
"""
from __future__ import annotations

from alembic import op

revision = "t0u1v2w3x4y5"
down_revision = "s9t0u1v2w3x4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # `ALTER TYPE … ADD VALUE` no puede correr dentro de un bloque transaccional en versiones
    # antiguas de PostgreSQL; `IF NOT EXISTS` lo hace idempotente (patrón `r8s9t0u1v2w3`).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE eventstatus ADD VALUE IF NOT EXISTS 'REVERSED'")
        op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'REVERSED'")


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM operational_events WHERE status = 'REVERSED') THEN
                RAISE EXCEPTION 'No se puede bajar t0u1v2w3x4y5: existen eventos REVERSED (OD-19)';
            END IF;
        END $$;
    """)
    # El miembro del enumerado permanece: PostgreSQL no lo elimina. Queda documentado.
