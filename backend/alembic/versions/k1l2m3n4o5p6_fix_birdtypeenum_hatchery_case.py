"""corrige el valor 'hatchery' de birdtypeenum a 'HATCHERY'

La migración `a1b2c3d4e5f6` añadió `'hatchery'` en minúsculas mientras el resto de los
valores del tipo están en mayúsculas: `GRANDPARENT`, `BREEDER`, `BROILER`.

SQLAlchemy persiste el **nombre** del miembro del enum de Python, no su valor, de modo que
un lote con `bird_type=BirdTypeEnum.HATCHERY` intenta escribir `'HATCHERY'` — que no
existe en el tipo. Ningún lote de incubadora podía crearse: el error salía como 500.

Detectado en la Wave 2 al ampliar el comprobador de deriva de esquema a los valores de los
tipos enumerados, que hasta entonces solo comparaba tablas y columnas (`R-41`).

Se añade el valor correcto en lugar de renombrar el existente: PostgreSQL no permite
eliminar valores de un tipo enumerado, y `'hatchery'` queda inerte —ninguna fila puede
haberlo usado, porque escribirlo era imposible desde la aplicación—.

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE birdtypeenum ADD VALUE IF NOT EXISTS 'HATCHERY'")


def downgrade() -> None:
    # PostgreSQL no permite eliminar valores de un tipo enumerado. El valor es aditivo.
    pass
