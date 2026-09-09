"""la capacidad de reverso llega a las instalaciones existentes (`OD-19` Aclaración A · `GA-REM-041-B`)

El propietario asignó `reversals:create` y `reversals:read` al «Supervisor Avícola» y
`reversals:read` al «Contralor Avícola» (`OD-19` Aclaración A). Las semillas ya lo hacen para
instalaciones nuevas; una instalación existente conserva su matriz histórica (`R-44`,
`l2m3n4o5p6q7`), de modo que sin esta migración de datos la decisión nunca llegaría a ella.

Mismo contrato que `l2m3n4o5p6q7`: solo **añade**, es idempotente, tolera que un rol no exista
(no crea roles: el catálogo de roles es dato del cliente). A diferencia de aquella, sí se
revierte: el módulo `reversals` nace con `OD-19`, no hay personalización previa que confundir,
y la bajada retira exactamente estas asociaciones.

`seeds/baseline_seeds._matriz_de_la_migracion` compone `PERMISOS_ADICIONALES` con la base:
una copia de cada hecho.

Revision ID: v2w3x4y5z6a7
Revises: u1v2w3x4y5z6
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "v2w3x4y5z6a7"
down_revision = "u1v2w3x4y5z6"
branch_labels = None
depends_on = None

# Rol -> asociaciones que `OD-19` Aclaración A añade a la matriz de `l2m3n4o5p6q7`.
PERMISOS_ADICIONALES: dict[str, list[tuple[str, str]]] = {
    "Supervisor Avícola": [
        ("reversals", "create"),   # solicita el reverso; no lo aprueba (BR-14)
        ("reversals", "read"),
    ],
    "Contralor Avícola": [         # figura de contraloría (`integration_seeds`); si no existe, se salta
        ("reversals", "read"),
    ],
}


def _roles(conexion) -> dict[str, int]:
    return {nombre: rid for rid, nombre in conexion.execute(sa.text("SELECT id, name FROM roles")).all()}


def aplicar(conexion) -> int:
    """Añade las asociaciones que falten. Devuelve cuántas añadió."""
    roles = _roles(conexion)
    existentes = {
        (rid, modulo, accion.upper())
        for rid, modulo, accion in conexion.execute(
            sa.text("SELECT role_id, module, action::text FROM permissions")).all()
    }
    añadidos = 0
    for nombre_rol, permisos in PERMISOS_ADICIONALES.items():
        rid = roles.get(nombre_rol)
        if rid is None:
            continue
        for modulo, accion in permisos:
            if (rid, modulo, accion.upper()) in existentes:
                continue
            conexion.execute(
                sa.text(
                    "INSERT INTO permissions (role_id, module, action, scope_type) "
                    "VALUES (:rid, :modulo, CAST(:accion AS permissionaction), 'all')"),
                {"rid": rid, "modulo": modulo, "accion": accion.upper()},
            )
            añadidos += 1
    return añadidos


def retirar(conexion) -> int:
    """Retira exactamente las asociaciones de `PERMISOS_ADICIONALES`. Devuelve cuántas retiró."""
    roles = _roles(conexion)
    retirados = 0
    for nombre_rol, permisos in PERMISOS_ADICIONALES.items():
        rid = roles.get(nombre_rol)
        if rid is None:
            continue
        for modulo, accion in permisos:
            resultado = conexion.execute(
                sa.text("DELETE FROM permissions WHERE role_id = :rid AND module = :modulo AND action::text = :accion"),
                {"rid": rid, "modulo": modulo, "accion": accion.upper()},
            )
            retirados += resultado.rowcount or 0
    return retirados


def upgrade() -> None:
    print(f"[OD-19 Acl. A] asociaciones rol-permiso añadidas: {aplicar(op.get_bind())}")


def downgrade() -> None:
    print(f"[OD-19 Acl. A] asociaciones rol-permiso retiradas: {retirar(op.get_bind())}")
