"""añade EGG_RECEPTION_CLASSIFICATION al tipo enum eventtype

El valor se incorporó al enum de Python en el commit 939fd14 (2026-06-27) sin la
migración correspondiente. El tipo `eventtype` de PostgreSQL se quedó con 24 valores
frente a los 25 del código, de modo que cualquier intento de registrar ese evento
terminaba en `InvalidTextRepresentationError` y llegaba al cliente como 500.

Detectado en la Wave 2 (`GA-REM-005 AC09`) al comprobar que ningún tipo de evento
devolviera 5xx. El comprobador de deriva de esquema no lo veía porque compara tablas y
columnas, no los valores de los tipos enumerados.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `IF NOT EXISTS` para que la migración sea idempotente sobre bases en las que el
    # valor se hubiera añadido a mano.
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'EGG_RECEPTION_CLASSIFICATION'")


def downgrade() -> None:
    # PostgreSQL no permite eliminar un valor de un tipo enumerado. Revertir exigiría
    # recrear el tipo y reescribir todas las columnas que lo usan, con riesgo de pérdida
    # si algún registro ya lo utiliza. No se hace: el valor es aditivo e inocuo.
    pass
