"""R-213 · `/me` y `/users` toleran correos legacy en lectura (no 500).

RED en HEAD:
- `UserRead.email: EmailStr` (heredado de `UserBase`) valida también al SERIALIZAR
  desde BD ⇒ 500 en `/me` y en la lista `/users` con filas de correo fuera de la
  política actual (`*.test`, `.invalid`, `.local`…).
- Escritura debe seguir estricta (422) — controles ya verdes.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R213-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc_r213(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    motor = create_async_engine(test_database_url)
    s = async_sessionmaker(motor, expire_on_commit=False)()
    empresa = Company(name=f"{PREFIJO}{uuid.uuid4().hex[:6]}", is_active=True)
    s.add(empresa)
    await s.flush()

    rol = Role(name=f"{PREFIJO}admin-{uuid.uuid4().hex[:6]}", company_id=empresa.id, is_active=True)
    s.add(rol)
    await s.flush()
    for accion in (PermissionAction.READ, PermissionAction.CREATE, PermissionAction.UPDATE):
        s.add(Permission(role_id=rol.id, module="users", action=accion, scope_type="company"))
    await s.flush()

    def _usuario(marca: str, email: str) -> User:
        return User(first_name=marca, last_name="R213", email=email,
                    username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                    hashed_password=hash_password("x1234567"),
                    company_id=empresa.id, role_id=rol.id, is_active=True)

    admin = _usuario("ADMIN", f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com")
    # Correo heredado: `email_validator` lo rechaza en LECTURA (special-use `.test`).
    legacy = _usuario("LEGACY", f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test")
    s.add_all([admin, legacy])
    await s.commit()

    yield {
        "url": test_database_url, "empresa": empresa, "admin": admin, "legacy": legacy,
        "token_admin": _token(admin.id), "token_legacy": _token(legacy.id),
        "rol": rol.id,
    }

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def test_r213_01_me_con_correo_legacy_es_200(client, esc_r213):
    r = await client.get("/api/v1/me", headers=esc_r213["token_legacy"])
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    assert r.json()["email"] == esc_r213["legacy"].email


async def test_r213_02_lista_de_usuarios_200_con_fila_legacy(client, esc_r213):
    r = await client.get("/api/v1/users?limit=100", headers=esc_r213["token_admin"])
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    correos = {u["email"] for u in r.json()}
    assert esc_r213["legacy"].email in correos


async def test_r213_03_alta_con_correo_invalido_es_422(client, esc_r213):
    r = await client.post("/api/v1/users", headers=esc_r213["token_admin"], json={
        "first_name": "Nuevo", "last_name": "R213",
        "email": f"invalido-{uuid.uuid4().hex[:6]}@e.test",
        "username": f"{PREFIJO}alta-{uuid.uuid4().hex[:6]}", "password": "x1234567",
        "role_id": esc_r213["rol"], "company_id": esc_r213["empresa"].id,
    })
    assert r.status_code == 422, r.text


async def test_r213_04_edicion_con_correo_invalido_es_422(client, esc_r213):
    r = await client.put(f"/api/v1/users/{esc_r213['legacy'].id}",
                         headers=esc_r213["token_admin"], json={"email": "x-e.test"})
    assert r.status_code == 422, r.text
