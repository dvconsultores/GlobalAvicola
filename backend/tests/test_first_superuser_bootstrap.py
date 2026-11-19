"""Pruebas dirigidas de GA-REM-043: bootstrap productivo del primer superusuario."""
from __future__ import annotations

import inspect
import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import Permission, PermissionAction, Role, User
from app.auth.security import hash_password, verify_password
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


# ═══════════════════════════════════════════════════════════════════════════
# AC04 / AC05 — idempotencia real y rechazos que nunca degradan lo existente
# ═══════════════════════════════════════════════════════════════════════════


async def test_t_043_07_repeated_runs_over_canonical_admin_write_nothing(
    pristine_superadmin,
):
    isolated_session = pristine_superadmin
    first = await bootstrap_first_superuser(
        isolated_session, password=STRONG_PASSWORD, commit=False
    )
    permissions_before = (
        await isolated_session.execute(
            select(func.count(Permission.id)).where(Permission.role_id == first.role_id)
        )
    ).scalar_one()

    second = await bootstrap_first_superuser(
        isolated_session, password="Different8!Temporary", commit=False
    )
    third = await bootstrap_first_superuser(
        isolated_session, password=STRONG_PASSWORD, commit=False
    )
    # Sin contraseña: no se valida porque no hay cuenta que crear (AC06 no aplica).
    without_password = await bootstrap_first_superuser(
        isolated_session, password=None, commit=False
    )

    admin_rows = (
        await isolated_session.execute(
            select(func.count(User.id)).where(User.username == ADMIN_USERNAME)
        )
    ).scalar_one()
    permissions_after = (
        await isolated_session.execute(
            select(func.count(Permission.id)).where(Permission.role_id == first.role_id)
        )
    ).scalar_one()

    assert (second.created, third.created, without_password.created) == (False, False, False)
    assert (
        second.permissions_created,
        third.permissions_created,
        without_password.permissions_created,
    ) == (0, 0, 0)
    assert (second.user_id, second.role_id) == (first.user_id, first.role_id)
    assert admin_rows == 1
    assert permissions_after == permissions_before


async def test_t_043_08_does_not_touch_unrelated_normal_user(pristine_superadmin):
    isolated_session = pristine_superadmin
    other_role = Role(
        company_id=None,
        name="Operador Bootstrap",
        description="Rol no global, ajeno al bootstrap",
        is_active=True,
    )
    isolated_session.add(other_role)
    await isolated_session.flush()
    other_user = User(
        company_id=None,
        first_name="Operador",
        last_name="Ajeno",
        email="operador.bootstrap@globalavicola.com",
        username="operador_bootstrap",
        hashed_password=hash_password("Operador1!Secure"),
        role_id=other_role.id,
        view_type="web",
        is_active=True,
    )
    isolated_session.add(other_user)
    await isolated_session.flush()
    snapshot = (other_user.role_id, other_user.is_active, other_user.hashed_password)
    users_before = (
        await isolated_session.execute(select(func.count(User.id)))
    ).scalar_one()

    await bootstrap_first_superuser(isolated_session, password=STRONG_PASSWORD, commit=False)

    untouched = (
        await isolated_session.execute(
            select(User).where(User.username == "operador_bootstrap")
        )
    ).scalar_one()
    superadmin_role = (
        await isolated_session.execute(
            select(Role).where(Role.name == "Super Administrador", Role.company_id.is_(None))
        )
    ).scalar_one()
    admin = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    users_after = (
        await isolated_session.execute(select(func.count(User.id)))
    ).scalar_one()

    assert (untouched.role_id, untouched.is_active, untouched.hashed_password) == snapshot
    assert untouched.role_id != superadmin_role.id
    assert admin.role_id == superadmin_role.id
    assert users_after == users_before + 1


async def test_t_043_09_refuses_reserved_email_owned_by_another_user(pristine_superadmin):
    isolated_session = pristine_superadmin
    other_role = Role(
        company_id=None,
        name="Operador Bootstrap",
        description="Rol no global, ajeno al bootstrap",
        is_active=True,
    )
    isolated_session.add(other_role)
    await isolated_session.flush()
    intruder = User(
        company_id=None,
        first_name="Aspirante",
        last_name="Al Correo Reservado",
        email=ADMIN_EMAIL,
        username="aspirante_admin",
        hashed_password=hash_password("Aspirante1!Secure"),
        role_id=other_role.id,
        view_type="web",
        is_active=True,
    )
    isolated_session.add(intruder)
    await isolated_session.flush()
    snapshot = (intruder.role_id, intruder.is_active, intruder.hashed_password)

    with pytest.raises(BootstrapError, match="rehúsa sobrescribirlo"):
        await bootstrap_first_superuser(
            isolated_session, password=STRONG_PASSWORD, commit=False
        )

    admin_rows = (
        await isolated_session.execute(
            select(func.count(User.id)).where(User.username == ADMIN_USERNAME)
        )
    ).scalar_one()
    created_role = (
        await isolated_session.execute(
            select(Role).where(Role.name == "Super Administrador", Role.company_id.is_(None))
        )
    ).scalar_one_or_none()
    existing = (
        await isolated_session.execute(select(User).where(User.username == "aspirante_admin"))
    ).scalar_one()

    assert admin_rows == 0
    assert created_role is None
    assert existing.email == ADMIN_EMAIL
    assert (existing.role_id, existing.is_active, existing.hashed_password) == snapshot


async def test_t_043_10_refuses_admin_with_non_global_role(pristine_superadmin):
    isolated_session = pristine_superadmin
    tenant_role = Role(
        company_id=None,
        name="Administrador de Empresa",
        description="Rol de empresa, no autoridad global",
        is_active=True,
    )
    isolated_session.add(tenant_role)
    await isolated_session.flush()
    admin_previo = User(
        company_id=None,
        first_name="Admin",
        last_name="Equivocado",
        email=ADMIN_EMAIL,
        username=ADMIN_USERNAME,
        hashed_password=hash_password("Equivocado1!Secure"),
        role_id=tenant_role.id,
        view_type="web",
        is_active=True,
    )
    isolated_session.add(admin_previo)
    await isolated_session.flush()
    snapshot = (
        admin_previo.role_id,
        admin_previo.is_active,
        admin_previo.hashed_password,
        admin_previo.email,
    )

    with pytest.raises(BootstrapError, match="configuración incompatible"):
        await bootstrap_first_superuser(
            isolated_session, password=STRONG_PASSWORD, commit=False
        )

    existing = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    created_role = (
        await isolated_session.execute(
            select(Role).where(Role.name == "Super Administrador", Role.company_id.is_(None))
        )
    ).scalar_one_or_none()

    assert created_role is None
    assert (
        existing.role_id,
        existing.is_active,
        existing.hashed_password,
        existing.email,
    ) == snapshot


async def test_t_043_11_weak_password_fails_safely_and_leaves_no_records(
    pristine_superadmin,
):
    isolated_session = pristine_superadmin

    with pytest.raises(BootstrapError):
        await bootstrap_first_superuser(isolated_session, password="debil", commit=False)
    await isolated_session.rollback()

    admin = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one_or_none()
    role = (
        await isolated_session.execute(
            select(Role).where(Role.name == "Super Administrador", Role.company_id.is_(None))
        )
    ).scalar_one_or_none()

    assert admin is None
    assert role is None


async def test_t_043_12_never_degrades_an_inactive_canonical_admin(pristine_superadmin):
    isolated_session = pristine_superadmin
    first = await bootstrap_first_superuser(
        isolated_session, password=STRONG_PASSWORD, commit=False
    )
    admin = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    admin.is_active = False
    await isolated_session.flush()
    snapshot = (admin.role_id, admin.is_active, admin.hashed_password)

    with pytest.raises(BootstrapError, match="rehúsa sobrescribirlo"):
        await bootstrap_first_superuser(
            isolated_session, password="Different8!Temporary", commit=False
        )

    existing = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    await isolated_session.refresh(existing)
    role = (
        await isolated_session.execute(select(Role).where(Role.id == existing.role_id))
    ).scalar_one()

    assert (existing.role_id, existing.is_active, existing.hashed_password) == snapshot
    assert existing.is_active is False
    assert existing.id == first.user_id
    assert role.name == "Super Administrador" and role.company_id is None


async def test_t_043_13_refuses_admin_bound_to_a_company(pristine_superadmin):
    """Un `admin` canónico atado a una empresa no es autoridad global: se rechaza."""
    isolated_session = pristine_superadmin
    first = await bootstrap_first_superuser(
        isolated_session, password=STRONG_PASSWORD, commit=False
    )
    company = Company(name=f"Empresa Bootstrap {uuid.uuid4().hex[:8]}", is_active=True)
    isolated_session.add(company)
    await isolated_session.flush()
    admin = (
        await isolated_session.execute(select(User).where(User.username == ADMIN_USERNAME))
    ).scalar_one()
    admin.company_id = company.id
    await isolated_session.flush()
    snapshot = (
        admin.role_id,
        admin.is_active,
        admin.hashed_password,
        admin.email,
        admin.company_id,
    )
    users_before = (
        await isolated_session.execute(select(func.count(User.id)))
    ).scalar_one()

    with pytest.raises(BootstrapError, match="configuración incompatible"):
        await bootstrap_first_superuser(
            isolated_session, password="Different8!Temporary", commit=False
        )

    await isolated_session.refresh(admin)
    admin_rows = (
        await isolated_session.execute(
            select(func.count(User.id)).where(User.username == ADMIN_USERNAME)
        )
    ).scalar_one()
    users_after = (
        await isolated_session.execute(select(func.count(User.id)))
    ).scalar_one()

    assert admin.company_id == company.id
    assert (
        admin.role_id,
        admin.is_active,
        admin.hashed_password,
        admin.email,
        admin.company_id,
    ) == snapshot
    assert admin.id == first.user_id
    assert admin_rows == 1
    assert users_after == users_before
    assert not verify_password("Different8!Temporary", admin.hashed_password)
