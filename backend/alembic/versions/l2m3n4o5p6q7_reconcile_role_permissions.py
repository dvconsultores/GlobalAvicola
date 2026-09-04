"""reconcilia los permisos de rol con el enforcement de RBAC (R-44)

`GA-REM-002` activó la comprobación de permisos en 170 rutas. El modelo de permisos ya
existía y los roles se sembraban con los suyos, pero **nada los leía**, de modo que las
definiciones podían estar incompletas sin que se notara. Al activarse el enforcement, 18 de
los 29 permisos exigidos no los concedía ningún rol — entre ellos `masters:read`, que
necesitan 40 rutas y sin el cual no carga ningún catálogo.

Actualizar las semillas no basta: las semillas sirven a instalaciones nuevas. Una
instalación existente conserva su matriz histórica, y desplegar el enforcement sobre ella
dejaría a todo usuario que no sea Super Admin con 403 en casi toda la aplicación.

De ahí que esto sea una **migración de datos** y no un cambio de semillas.

Criterios (ver `audit/remediation/RBAC_ROLE_PERMISSION_MATRIX.md`):

* solo **añade** asociaciones; nunca elimina — una instalación puede tener permisos
  personalizados legítimos y esta migración no tiene forma de distinguirlos de un error;
* **mínimo privilegio**: cada permiso va al rol cuya responsabilidad documentada en
  `docs/12 §3` lo requiere, y a ninguno más;
* las 13 operaciones de administración siguen siendo exclusivas del Super Admin;
* **idempotente**: ejecutarla dos veces deja el mismo estado;
* tolera que un rol no exista —una instalación puede haber renombrado o eliminado roles—
  sin fallar;
* no crea ni borra roles ni usuarios.

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-09-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'l2m3n4o5p6q7'
down_revision: Union[str, None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Rol -> permisos que su responsabilidad documentada requiere.
# Derivado de `docs/12-approval-workflow.md §3` cruzado con el permiso que declara cada
# ruta. No es «lo que hace falta para que pasen los tests».
PERMISOS_POR_ROL: dict[str, list[tuple[str, str]]] = {
    "Operador de Granja": [
        ("operations", "create"),   # registrar en campo
        ("operations", "read"),
        ("operations", "update"),   # docs/12 §3: «Editar (antes de enviar)»
        ("lots", "read"),
        ("masters", "read"),        # sin esto no puede elegir granja, galpón ni vacuna
        ("dashboard", "read"),
    ],
    "Supervisor Avícola": [
        ("operations", "read"),
        ("operations", "update"),
        ("lots", "read"),
        ("masters", "read"),
        ("review", "read"),
        ("review", "review"),       # tomar y completar la revisión
        ("review", "correct"),
        ("corrections", "read"),
        ("corrections", "correct"), # docs/12 §3: «Corregir (si está autorizado)»
        ("approvals", "read"),
        ("reports", "read"),
        ("dashboard", "read"),
    ],
    "Aprobador": [
        ("operations", "read"),
        ("lots", "read"),
        ("masters", "read"),
        ("review", "read"),
        ("approvals", "approve"),
        ("approvals", "reject"),
        ("approvals", "review"),
        ("approvals", "correct"),
        ("corrections", "read"),
        ("corrections", "correct"), # docs/12 §3: el aprobador también corrige
        ("reports", "read"),
        ("dashboard", "read"),
    ],
    "Analista SAP": [
        ("sap", "read"),
        ("sap", "create"),
        ("sap", "send_sap"),
        ("operations", "read"),
        ("lots", "read"),
        ("masters", "read"),
        ("reports", "read"),
        ("dashboard", "read"),
    ],
    "Auditor": [
        # docs/12 §3: «Consultar auditoría (solo lectura)». Ni una acción de escritura.
        ("audit", "read"),
        ("reports", "read"),
        ("operations", "read"),
        ("lots", "read"),
        ("masters", "read"),
        ("review", "read"),
        ("corrections", "read"),
        ("dashboard", "read"),
    ],
}


def upgrade() -> None:
    conexion = op.get_bind()

    roles = {
        nombre: rid
        for rid, nombre in conexion.execute(sa.text("SELECT id, name FROM roles")).all()
    }
    existentes = {
        (rid, modulo, accion)
        for rid, modulo, accion in conexion.execute(
            sa.text("SELECT role_id, module, action::text FROM permissions")
        ).all()
    }

    añadidos = 0
    for nombre_rol, permisos in PERMISOS_POR_ROL.items():
        rid = roles.get(nombre_rol)
        if rid is None:
            # La instalación no tiene este rol: puede haberlo renombrado o eliminado. No
            # se crea —el catálogo de roles es dato del cliente— y no se falla por ello.
            continue
        for modulo, accion in permisos:
            if (rid, modulo, accion.upper()) in existentes or (rid, modulo, accion) in existentes:
                continue
            conexion.execute(
                sa.text(
                    "INSERT INTO permissions (role_id, module, action, scope_type) "
                    "VALUES (:rid, :modulo, CAST(:accion AS permissionaction), 'all')"
                ),
                {"rid": rid, "modulo": modulo, "accion": accion.upper()},
            )
            añadidos += 1

    print(f"[R-44] asociaciones rol-permiso añadidas: {añadidos}")


def downgrade() -> None:
    # No se revierte. Eliminar las asociaciones dejaría la instalación en el estado que
    # esta migración corrige —usuarios legítimos con 403 en casi toda la aplicación— y no
    # hay forma de distinguir las que añadió esta migración de las que un administrador
    # haya configurado después. Conceder un permiso que la responsabilidad del rol ya
    # requiere no es un cambio que convenga deshacer a ciegas.
    pass
