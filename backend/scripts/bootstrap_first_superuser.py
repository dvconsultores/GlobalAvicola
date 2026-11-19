"""Bootstrap productivo, mínimo y manual del primer Super Administrador.

GA-REM-043. No usar seeds de desarrollo ni de certificación para una instalación real.
La contraseña se recibe exclusivamente por ``GA_FIRST_SUPERUSER_PASSWORD``.
"""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Los mappers tienen relaciones cruzadas; cargar los modelos antes de operar el ORM.
import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.masters.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.models import Permission, PermissionAction, Role, User
from app.auth.security import hash_password
from app.database import async_session, engine

PASSWORD_ENV = "GA_FIRST_SUPERUSER_PASSWORD"
ROLE_NAME = "Super Administrador"
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@globalavicola.com"


class BootstrapError(RuntimeError):
    """Fallo seguro y esperado del bootstrap."""


@dataclass(frozen=True)
class BootstrapResult:
    created: bool
    role_id: int
    user_id: int
    permissions_created: int


def validate_password(password: str | None) -> str:
    """Exige una contraseña temporal fuerte sin mostrarla ni transformarla."""
    if not password:
        raise BootstrapError(f"Falta la variable de entorno {PASSWORD_ENV}")

    failures: list[str] = []
    if len(password) < 12:
        failures.append("al menos 12 caracteres")
    if not any(char.islower() for char in password):
        failures.append("una letra minúscula")
    if not any(char.isupper() for char in password):
        failures.append("una letra mayúscula")
    if not any(char.isdigit() for char in password):
        failures.append("un dígito")
    if not any(not char.isalnum() for char in password):
        failures.append("un símbolo")
    if failures:
        raise BootstrapError("La contraseña temporal requiere " + ", ".join(failures))
    return password


async def bootstrap_first_superuser(
    session: AsyncSession,
    *,
    password: str,
    commit: bool = True,
) -> BootstrapResult:
    """Crea el RBAC global mínimo y ``admin``; nunca altera una cuenta existente.

    ``commit=False`` existe solo para pruebas aisladas; el CLI productivo siempre confirma.
    """
    existing_username = (
        await session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one_or_none()
    existing_email = (
        await session.execute(select(User).where(User.email == ADMIN_EMAIL))
    ).scalar_one_or_none()

    if existing_username is not None:
        existing_role = (
            await session.execute(select(Role).where(Role.id == existing_username.role_id))
        ).scalar_one_or_none()
        if not (
            existing_username.email == ADMIN_EMAIL
            and existing_username.company_id is None
            and existing_username.is_active
            and existing_role is not None
            and existing_role.name == ROLE_NAME
            and existing_role.company_id is None
            and existing_role.is_active
        ):
            raise BootstrapError(
                "El usuario 'admin' ya existe con una configuración incompatible; "
                "se rehúsa sobrescribirlo"
            )
    # El correo reservado solo bloquea si pertenece a OTRA cuenta: cuando `existing_email`
    # es el propio `admin` canónico, la repetición es idempotente (AC04).
    if existing_email is not None and (
        existing_username is None or existing_email.id != existing_username.id
    ):
        raise BootstrapError(
            "El correo reservado del bootstrap ya pertenece a otro usuario; "
            "se rehúsa sobrescribirlo"
        )

    role = (
        await session.execute(select(Role).where(Role.name == ROLE_NAME))
    ).scalar_one_or_none()
    if role is None:
        role = Role(
            company_id=None,
            name=ROLE_NAME,
            description="Control total del sistema",
            is_active=True,
        )
        session.add(role)
        await session.flush()
    elif role.company_id is not None:
        raise BootstrapError(
            "Existe un rol tenant llamado 'Super Administrador'; no puede usarse "
            "como autoridad global"
        )
    elif not role.is_active:
        raise BootstrapError(
            "El rol global 'Super Administrador' está inactivo; se rehúsa reactivarlo "
            "implícitamente"
        )

    existing_permissions = {
        (
            permission.module,
            permission.action.value
            if isinstance(permission.action, PermissionAction)
            else str(permission.action),
            permission.scope_type,
            permission.scope_id,
        )
        for permission in (
            await session.execute(select(Permission).where(Permission.role_id == role.id))
        ).scalars()
    }
    permissions_created = 0
    for action in PermissionAction:
        expected = ("*", action.value, "all", None)
        if expected in existing_permissions:
            continue
        session.add(
            Permission(
                role_id=role.id,
                module="*",
                action=action,
                scope_type="all",
                scope_id=None,
            )
        )
        permissions_created += 1

    if existing_username is None:
        password = validate_password(password)
        user = User(
            company_id=None,
            first_name="Administrador",
            last_name="del Sistema",
            email=ADMIN_EMAIL,
            username=ADMIN_USERNAME,
            hashed_password=hash_password(password),
            role_id=role.id,
            view_type="web",
            is_active=True,
        )
        session.add(user)
        await session.flush()
        created = True
    else:
        user = existing_username
        created = False
    if commit:
        await session.commit()

    return BootstrapResult(
        created=created,
        role_id=role.id,
        user_id=user.id,
        permissions_created=permissions_created,
    )


async def _main() -> int:
    try:
        password = os.environ.get(PASSWORD_ENV)
        async with async_session() as session:
            try:
                result = await bootstrap_first_superuser(session, password=password)
            except Exception:
                await session.rollback()
                raise
    except BootstrapError as exc:
        print(f"[bootstrap] ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[bootstrap] ERROR: operación fallida ({type(exc).__name__})", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()

    if result.created:
        print(
            "[bootstrap] Primer Super Administrador creado: usuario 'admin'; "
            f"permisos comodín añadidos={result.permissions_created}"
        )
        print("[bootstrap] Cambie inmediatamente la contraseña temporal después del login")
    else:
        print("[bootstrap] Ya existe el Super Administrador canónico; no se realizaron cambios")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
