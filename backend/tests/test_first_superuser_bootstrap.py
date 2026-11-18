"""Pruebas dirigidas de GA-REM-043: bootstrap productivo del primer superusuario."""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import Permission, PermissionAction, Role, User
from app.auth.security import verify_password
from app.masters.models import Company
from scripts.bootstrap_first_superuser import (
    ADMIN_EMAIL,
    ADMIN_USERNAME,
    BootstrapError,
    bootstrap_first_superuser,
    validate_password,
)

STRONG_PASSWORD = "Temporary9!Secure"


@pytest.fixture
async def isolated_session(test_database_url):
    engine = create_async_engine(test_database_url, poolclass=None)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.fixture
async def pristine_superadmin(isolated_session):
    role = (
        await isolated_session.execute(
            select(Role).where(Role.name == "Super Administrador", Role.company_id.is_(None))
        )
    ).scalar_one_or_none()
    if role is not None:
        users = (
            await isolated_session.execute(select(User).where(User.role_id == role.id))
        ).scalars().all()
        if users or role.permissions:
            pytest.skip("la base dirigida ya contiene un Super Administrador en uso")
        await isolated_session.delete(role)
        await isolated_session.commit()
    conflict = (
        await isolated_session.execute(
            select(User).where(
                (User.username == ADMIN_USERNAME) | (User.email == ADMIN_EMAIL)
            )
        )
    ).scalar_one_or_none()
    if conflict is not None:
        pytest.skip("la base dirigida ya contiene la identidad canónica de admin")
    return isolated_session


async def test_t_043_01_creates_only_minimal_global_authorization(pristine_superadmin):
    isolated_session = pristine_superadmin
    companies_before = (
        await isolated_session.execute(select(func.count(Company.id)))
    ).scalar_one()

    result = await bootstrap_first_superuser(
        isolated_session, password=STRONG_PASSWORD, commit=False
    )

    admin = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    role = (
        await isolated_session.execute(select(Role).where(Role.id == admin.role_id))
    ).scalar_one()
    permissions = (
        await isolated_session.execute(
            select(Permission).where(Permission.role_id == role.id)
        )
    ).scalars().all()
    companies_after = (
        await isolated_session.execute(select(func.count(Company.id)))
    ).scalar_one()

    assert result.created is True
    assert admin.company_id is None and admin.is_active is True
    assert admin.email == ADMIN_EMAIL
    assert verify_password(STRONG_PASSWORD, admin.hashed_password)
    assert role.name == "Super Administrador" and role.company_id is None
    assert {(p.module, p.action, p.scope_type) for p in permissions} == {
        ("*", action, "all") for action in PermissionAction
    }
    assert companies_after == companies_before


async def test_t_043_02_second_run_is_idempotent_and_does_not_rotate_password(
    pristine_superadmin,
):
    isolated_session = pristine_superadmin
    first = await bootstrap_first_superuser(
        isolated_session, password=STRONG_PASSWORD, commit=False
    )
    second = await bootstrap_first_superuser(
        isolated_session, password="Different8!Temporary", commit=False
    )
    admin = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()

    assert first.created is True
    assert second.created is False
    assert second.user_id == first.user_id and second.role_id == first.role_id
    assert verify_password(STRONG_PASSWORD, admin.hashed_password)
    assert not verify_password("Different8!Temporary", admin.hashed_password)


async def test_t_043_03_refuses_incompatible_existing_admin_without_overwrite(
    pristine_superadmin,
):
    isolated_session = pristine_superadmin
    await bootstrap_first_superuser(
        isolated_session, password=STRONG_PASSWORD, commit=False
    )
    admin = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    existing_hash = admin.hashed_password
    admin.email = "incompatible-admin@globalavicola.com"
    await isolated_session.flush()

    with pytest.raises(BootstrapError, match="rehúsa sobrescribirlo"):
        await bootstrap_first_superuser(
            isolated_session, password="Different8!Temporary", commit=False
        )
    existing = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    assert existing.hashed_password == existing_hash
    assert existing.email == "incompatible-admin@globalavicola.com"


@pytest.mark.parametrize(
    "password",
    [None, "", "Short1!", "alllowercase9!", "ALLUPPERCASE9!", "NoDigitsHere!", "NoSymbolHere9"],
)
def test_t_043_04_rejects_missing_or_weak_password(password):
    with pytest.raises(BootstrapError):
        validate_password(password)


def test_t_043_05_cli_has_no_password_argument_or_certification_seed_dependency():
    import scripts.bootstrap_first_superuser as bootstrap

    source = inspect.getsource(bootstrap)
    assert "argparse" not in source
    assert "sys.argv" not in source
    assert "baseline_seeds" not in source
    assert "dev_seeds" not in source
    assert "EMPRESAS_CERTIFICACION" not in source
    assert "GA_FIRST_SUPERUSER_PASSWORD" in source


def test_t_043_06_wrapper_uses_hidden_prompt_and_environment_only():
    path = Path(__file__).parents[1] / "scripts" / "bootstrap-first-superuser.sh"
    source = path.read_text(encoding="utf-8")
    assert "read -r -s" in source
    assert "-e GA_FIRST_SUPERUSER_PASSWORD" in source
    assert "python -m scripts.bootstrap_first_superuser" in source
    assert "(($# != 0))" in source
