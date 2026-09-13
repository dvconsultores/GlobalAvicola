"""Refresh tokens revocados — `GA-REM-003` · AC04 (el logout revoca).

Denylist mínima por `jti`: el refresh emitido lleva un identificador único
(`security.py`) y el logout inserta aquí su revocación con TTL = expiración del
refresh (7 días). El endpoint de renovación consulta; la purga es oportunista en
cada inserción. El almacén en memoria se descartó en revisión de spec
(multi-instancia). `downgrade()` funcional: la tabla es nueva y no destruye datos
existentes.

Revision ID: z6a7b8c9d0e1
Revises: y5z6a7b8c9d0
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "z6a7b8c9d0e1"
down_revision = "y5z6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )
    # Mismo nombre que produce el modelo (`unique=True, index=True` → índice único).
    op.create_index("ix_revoked_tokens_jti", "revoked_tokens", ["jti"], unique=True)
    op.create_index("ix_revoked_tokens_user_id", "revoked_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_revoked_tokens_user_id", table_name="revoked_tokens")
    op.drop_index("ix_revoked_tokens_jti", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
