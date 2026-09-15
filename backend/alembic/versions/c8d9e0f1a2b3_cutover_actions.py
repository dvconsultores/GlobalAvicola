"""Acciones RBAC y de auditoría del cutover — `GA-REQ-061` · T14 (C2).

El catálogo cerrado de acciones (`PermissionAction`) y la trazabilidad
(`AuditAction`) ganan los valores que la matriz de seguridad del cutover nombra.
`downgrade()` es no-op: PostgreSQL no retira valores de un tipo enumerado sin
reescribir el tipo (y los datos de auditoría son inmutables, T8).

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""
from __future__ import annotations

from alembic import op

revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None

_PERMISSION_ACTIONS = ("VALIDATE", "SUBMIT", "APPLY")
_AUDIT_ACTIONS = ("CREATE_BATCH", "UPLOAD", "VALIDATE", "SUBMIT", "APPLY", "FAILED_APPLY", "CORRECT")


def upgrade() -> None:
    # `AuditModule.CUTOVER` (C1) — el módulo de los eventos del cutover.
    op.execute("ALTER TYPE auditmodule ADD VALUE IF NOT EXISTS 'CUTOVER'")
    for valor in _PERMISSION_ACTIONS:
        op.execute(f"ALTER TYPE permissionaction ADD VALUE IF NOT EXISTS '{valor}'")
    for valor in _AUDIT_ACTIONS:
        op.execute(f"ALTER TYPE auditaction ADD VALUE IF NOT EXISTS '{valor}'")


def downgrade() -> None:
    # Los valores de un enum no se retiran de forma segura con datos vivos (auditoría inmutable).
    pass
