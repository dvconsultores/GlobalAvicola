"""notificaciones internas (`GA-REM-038` / `OD-07`)

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-09-07

`docs/02 §3.14` exige avisar al usuario y `OD-07` fijó el canal: dentro de Global Avícola.
Hasta ahora no existía ninguna bandeja, de modo que un registro rechazado se quedaba sin que
su operador se enterase.

`related_entity_type` / `related_entity_id` **no** llevan clave foránea, y es deliberado: el
aviso debe sobrevivir a la desaparición de aquello de lo que informaba. Con una `FK` y su
`CASCADE`, borrar un evento borraría la historia de que fue rechazado.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "n4o5p6q7r8s9"
down_revision = "m3n4o5p6q7r8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("related_entity_type", sa.String(length=50), nullable=True),
        sa.Column("related_entity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        # NULL = sin leer. No hay enum de estados: `OD-07` deja fuera correo y push, que son
        # los que necesitarían SENT / DELIVERED / OPENED.
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_company_id"), "notifications", ["company_id"])
    op.create_index(op.f("ix_notifications_recipient_user_id"), "notifications",
                    ["recipient_user_id"])
    # Las dos consultas reales: «mi bandeja, lo más reciente primero» y «cuántas sin leer».
    op.create_index("ix_notifications_bandeja", "notifications",
                    ["recipient_user_id", "created_at"])
    op.create_index("ix_notifications_sin_leer", "notifications",
                    ["recipient_user_id", "read_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_sin_leer", table_name="notifications")
    op.drop_index("ix_notifications_bandeja", table_name="notifications")
    op.drop_index(op.f("ix_notifications_recipient_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_company_id"), table_name="notifications")
    op.drop_table("notifications")
