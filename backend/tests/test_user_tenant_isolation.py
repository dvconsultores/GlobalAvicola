"""Aislamiento de inquilino en la administración de usuarios.

`GA-REM-002` enmienda B · `AC13` · `AC14` · `AC15` · `R-114`…`R-118`.

```
CONOCER UN IDENTIFICADOR   ≠   TENER DERECHO A ESE USUARIO
`users:update`             ≠   AUTORIDAD SOBRE OTRO INQUILINO
ADMINISTRAR UNA EMPRESA    ≠   PODER CREAR UNA AUTORIDAD GLOBAL
```

Estas cuatro superficies quedaron fuera de `TENANT_RESOURCE_CLASSIFICATION.md`, que se
construyó desde el modelo de datos **operativo**. `AC05` ya exigía en abstracto que un recurso
de la compañía B no se alcanzara; la lista que operacionalizó esa `AC` nunca incluyó `users`, y
por eso el filtro no llegó nunca a la administración.

El sujeto es un administrador de empresa **real**: tiene `users:read`, `users:create` y
`users:update` concedidos explícitamente, y **no** es Super Administrador. Es exactamente el
actor que `R-113` creará el día que el propietario conteste, y por eso estas pruebas describen
un riesgo activo y no teórico.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "UTEN-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """Dos empresas, un administrador de empresa real y un rol de autoridad global.

    ```
    Empresa A   ADMIN_A   users:read + create + update   ·  NO es super administrador
                A1        usuario ordinario de A
    Empresa B   B1        usuario ordinario de B — invisible e inmutable para ADMIN_A
                ADMIN_B   administrador de B, para el caso simétrico
    Roles       ORDINARIO   asignable
                GLOBAL      ("*", …) con alcance `all` — es lo que hace Super Administrador
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        def _rol(nombre):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", is_active=True)
            s.add(r)
            return r

        rol_admin = _rol("AdminEmpresa")
        rol_admin_b = _rol("AdminEmpresaB")
        rol_ordinario = _rol("Ordinario")
        rol_global = _rol("Global")
        await s.flush()

        for rol in (rol_admin, rol_admin_b):
            for accion in (PermissionAction.READ, PermissionAction.CREATE,
                           PermissionAction.UPDATE):
                s.add(Permission(role_id=rol.id, module="users", action=accion,
                                 scope_type="company"))
        s.add(Permission(role_id=rol_ordinario.id, module="operations",
                         action=PermissionAction.READ, scope_type="company"))
        # La autoridad global: es la forma exacta que `docs/02 §3.1.4` describe como Super
        # Administrador — «rol con `module="*"`, `scope_type="all"` ve TODAS las compañías».
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Ten",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        admin_a = _usuario(a.id, "ADMINA", rol_admin)
        a1 = _usuario(a.id, "A1", rol_ordinario)
        admin_b = _usuario(b.id, "ADMINB", rol_admin_b)
        b1 = _usuario(b.id, "B1", rol_ordinario)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([admin_a, a1, admin_b, b1, superadmin])
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "b": b.id, "admin_a": admin_a.id, "a1": a1.id,
                 "admin_b": admin_b.id, "b1": b1.id, "super": superadmin.id,
                 "rol_ordinario": rol_ordinario.id, "rol_global": rol_global.id,
                 "rol_admin": rol_admin.id, "url": test_database_url,
                 "b1_username": b1.username, "a1_username": a1.username}
    yield datos

    async with motor.begin() as c:
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN "
                             "(SELECT id FROM users WHERE username LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        from app.auth.models import Permission, Role, User
        from app.masters.models import Company
        ids = (await c.execute(text("SELECT id FROM roles WHERE name LIKE :p"),
                               {"p": f"{PREFIJO}%"})).scalars().all()
        if ids:
            await c.execute(delete(Permission).where(Permission.role_id.in_(ids)))
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
        await c.execute(delete(Role).where(Role.name.like(f"{PREFIJO}%")))
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await motor.dispose()


async def _fila(esc, user_id: int) -> dict:
    from app.auth.models import User

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            u = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
            return {"role_id": u.role_id, "company_id": u.company_id,
                    "is_active": u.is_active, "first_name": u.first_name,
                    "email": u.email, "username": u.username}
    finally:
        await motor.dispose()


async def _auditorias(esc, user_id: int) -> int:
    from app.audit.models import AuditLog
    from sqlalchemy import func

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return (await s.execute(
                select(func.count()).select_from(AuditLog)
                .where(AuditLog.entity_type == "user",
                       AuditLog.entity_id == str(user_id)))).scalar_one()
    finally:
        await motor.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  `AC13` · listar y leer
# ══════════════════════════════════════════════════════════════════════════════

async def test_p0a_el_listado_no_expone_usuarios_de_otra_empresa(http_client, esc):
    """`P0-A` · `R-114`. El listado se acota a la empresa efectiva."""
    r = await http_client.get("/api/v1/users?limit=100", headers=_token(esc["admin_a"]))
    assert r.status_code == 200, r.text
    nombres = {u["username"] for u in r.json()}

    assert esc["a1_username"] in nombres, "el administrador debe ver a los suyos"
    assert esc["b1_username"] not in nombres, (
        f"fuga de inquilino: {esc['b1_username']} es de la empresa B")


async def test_p0a_el_listado_del_otro_lado_es_simetrico(http_client, esc):
    """Sin esto, «no ve a B» sería compatible con «no ve a nadie» (`R-72`)."""
    r = await http_client.get("/api/v1/users?limit=100", headers=_token(esc["admin_b"]))
    assert r.status_code == 200, r.text
    nombres = {u["username"] for u in r.json()}
    assert esc["b1_username"] in nombres
    assert esc["a1_username"] not in nombres


async def test_el_filtro_vive_en_la_consulta_y_no_despues_de_paginar(http_client, esc):
    """`AC13` · `§41`. El predicado va **dentro** de la consulta, antes de la paginación.

    Esta prueba existe porque una mutación sobrevivió **dos veces**, y la segunda por culpa
    mía: filtrar en Python después de paginar daba el mismo resultado, y mi primer intento
    pedía la primera página —donde los usuarios de `A`, con identificadores bajos, sobrevivían
    igualmente al filtro posterior—. La prueba prometía en su descripción algo que su código
    no hacía.

    Ahora discrimina de verdad. Se siembran treinta usuarios de `B` y **después** uno de `A`,
    de modo que el de `A` queda con el identificador más alto de todos:

    ```
    FILTRO EN LA CONSULTA   `A` tiene 3 usuarios · el nuevo entra en la primera página
    FILTRO DESPUÉS          la primera página son treinta filas de `B` · el de `A` no está
    ```
    """
    from app.auth.models import User
    from app.auth.security import hash_password

    marca = f"{PREFIJO}TARDIO-{uuid.uuid4().hex[:6]}"
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            for i in range(30):
                s.add(User(first_name="Relleno", last_name=str(i),
                           email=f"{PREFIJO}rel{i}-{uuid.uuid4().hex[:6]}@globalavicola.com",
                           username=f"{PREFIJO}REL{i}-{uuid.uuid4().hex[:6]}",
                           hashed_password=hash_password("x1234567"),
                           company_id=esc["b"], role_id=esc["rol_ordinario"],
                           is_active=True))
            await s.flush()
            # El de `A`, el último de todos.
            s.add(User(first_name="Tardio", last_name="A",
                       email=f"{marca}@globalavicola.com", username=marca,
                       hashed_password=hash_password("x1234567"),
                       company_id=esc["a"], role_id=esc["rol_ordinario"], is_active=True))
            await s.commit()
    finally:
        await motor.dispose()

    r = await http_client.get("/api/v1/users?limit=20", headers=_token(esc["admin_a"]))
    assert r.status_code == 200, r.text
    nombres = {u["username"] for u in r.json()}

    assert marca in nombres, (
        "el usuario más reciente de la empresa propia no aparece en la primera página: "
        "el filtro se está aplicando después de paginar")
    assert not [n for n in nombres if n.startswith(f"{PREFIJO}REL")], (
        "se colaron usuarios de la empresa B")


async def test_p0b_conocer_el_identificador_ajeno_no_abre_el_usuario(http_client, esc):
    """`P0-B` · `R-114`. `IDOR` de inquilino en la consulta directa."""
    r = await http_client.get(f"/api/v1/users/{esc['b1']}", headers=_token(esc["admin_a"]))
    assert r.status_code == 404, (
        f"esperado 404 y llegó {r.status_code}: {r.text[:200]}")
    assert esc["b1_username"] not in r.text


async def test_p0b_el_usuario_propio_si_se_lee(http_client, esc):
    """La contraparte: el arreglo no puede consistir en denegarlo todo."""
    r = await http_client.get(f"/api/v1/users/{esc['a1']}", headers=_token(esc["admin_a"]))
    assert r.status_code == 200, r.text
    assert r.json()["username"] == esc["a1_username"]


# ══════════════════════════════════════════════════════════════════════════════
#  `AC14` · mutar
# ══════════════════════════════════════════════════════════════════════════════

async def test_p0c_no_se_modifica_un_usuario_de_otra_empresa(http_client, esc):
    """`P0-C` · `R-114`. Y sin **ningún** efecto colateral."""
    antes = await _fila(esc, esc["b1"])
    auditorias_antes = await _auditorias(esc, esc["b1"])

    r = await http_client.put(f"/api/v1/users/{esc['b1']}",
                              headers=_token(esc["admin_a"]),
                              json={"first_name": "TOMADO", "is_active": False})
    assert r.status_code == 404, r.text

    assert await _fila(esc, esc["b1"]) == antes, "la fila ajena cambió"
    assert await _auditorias(esc, esc["b1"]) == auditorias_antes, (
        "una operación denegada dejó auditoría de éxito")


async def test_p0c_el_usuario_propio_si_se_edita(http_client, esc):
    """La administración legítima debe seguir funcionando."""
    r = await http_client.put(f"/api/v1/users/{esc['a1']}",
                              headers=_token(esc["admin_a"]),
                              json={"first_name": "Editado"})
    assert r.status_code == 200, r.text
    assert (await _fila(esc, esc["a1"]))["first_name"] == "Editado"


# ══════════════════════════════════════════════════════════════════════════════
#  `AC15` · asignar un rol es modificar autoridad
# ══════════════════════════════════════════════════════════════════════════════

async def test_p0d_no_se_concede_autoridad_a_un_usuario_de_otra_empresa(http_client, esc):
    """`P0-D` · `R-117`. Escalada de privilegios que cruza inquilinos.

    Es el hallazgo más grave de la auditoría: por la ruta **documentada** de edición, un
    administrador de la empresa A convertía a un usuario de la B en Super Administrador.
    """
    antes = await _fila(esc, esc["b1"])
    auditorias_antes = await _auditorias(esc, esc["b1"])

    r = await http_client.put(f"/api/v1/users/{esc['b1']}",
                              headers=_token(esc["admin_a"]),
                              json={"role_id": esc["rol_global"]})
    assert r.status_code == 404, r.text

    despues = await _fila(esc, esc["b1"])
    assert despues["role_id"] == antes["role_id"], "el rol ajeno cambió"
    assert despues["company_id"] == antes["company_id"]
    assert await _auditorias(esc, esc["b1"]) == auditorias_antes


async def test_p0d_un_actor_de_empresa_no_crea_una_autoridad_global(http_client, esc):
    """`AC15`. Ni siquiera dentro de su propia empresa.

    `docs/02 §3.1.4` define al Super Administrador como «rol con `module="*"`,
    `scope_type="all"`» y le da visibilidad sobre **todas** las compañías. Conceder ese rol
    desde una superficie acotada a una empresa **fabrica una autoridad global** desde dentro
    de un inquilino, que es escalada aunque el objetivo sea de casa.

    No se inventa una regla de «solo roles más débiles que el mío»: se prohíbe exactamente lo
    que la spec ya describe como alcance global.
    """
    antes = await _fila(esc, esc["a1"])
    r = await http_client.put(f"/api/v1/users/{esc['a1']}",
                              headers=_token(esc["admin_a"]),
                              json={"role_id": esc["rol_global"]})
    assert r.status_code == 403, (
        f"esperado 403 y llegó {r.status_code}: {r.text[:200]}")
    assert (await _fila(esc, esc["a1"]))["role_id"] == antes["role_id"]


async def test_p0d_el_rol_ordinario_si_se_asigna(http_client, esc):
    """Sin esta, la anterior pasaría también si se hubieran prohibido **todos** los roles."""
    r = await http_client.put(f"/api/v1/users/{esc['a1']}",
                              headers=_token(esc["admin_a"]),
                              json={"role_id": esc["rol_admin"]})
    assert r.status_code == 200, r.text
    assert (await _fila(esc, esc["a1"]))["role_id"] == esc["rol_admin"]


async def test_el_super_administrador_si_puede_conceder_autoridad_global(http_client, esc):
    """`AC15` acota a los actores de empresa, no a la autoridad global legítima."""
    r = await http_client.put(f"/api/v1/users/{esc['a1']}",
                              headers=_token(esc["super"], company_id=esc["a"]),
                              json={"role_id": esc["rol_global"]})
    assert r.status_code == 200, r.text


# ══════════════════════════════════════════════════════════════════════════════
#  La empresa no la elige el cliente
# ══════════════════════════════════════════════════════════════════════════════

async def test_el_alta_no_acepta_la_empresa_del_cliente(http_client, esc):
    """`R-118`. El actor de A no crea usuarios en B."""
    marca = f"{PREFIJO}NUEVO-{uuid.uuid4().hex[:6]}"
    r = await http_client.post("/api/v1/users", headers=_token(esc["admin_a"]),
                               json={"first_name": "N", "last_name": "N",
                                     "email": f"{marca}@globalavicola.com",
                                     "username": marca, "password": "x1234567",
                                     "role_id": esc["rol_ordinario"],
                                     "company_id": esc["b"]})
    assert r.status_code in (201, 400, 403), r.text
    if r.status_code == 201:
        assert r.json()["company_id"] == esc["a"], (
            "la empresa se resuelve, no se recibe: el alta cayó en la empresa B")


async def test_el_parametro_de_empresa_no_amplia_el_alcance(http_client, esc):
    """`AC14`. Ni por consulta ni por reclamación del token."""
    r = await http_client.get(f"/api/v1/users?limit=100&company_id={esc['b']}",
                              headers=_token(esc["admin_a"]))
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        assert esc["b1_username"] not in {u["username"] for u in r.json()}

    # `OD-11`: una reclamación de empresa en el token no es autoridad para quien no puede
    # cambiar de contexto.
    r2 = await http_client.get("/api/v1/users?limit=100",
                               headers=_token(esc["admin_a"], company_id=esc["b"]))
    assert r2.status_code == 200, r2.text
    assert esc["b1_username"] not in {u["username"] for u in r2.json()}


async def test_la_autoridad_global_conserva_su_alcance(http_client, esc):
    """`docs/02 §3.1.4` · `GA-REM-002 AC09`. El Super Administrador ve todas las compañías.

    Esta prueba nació afirmando lo contrario —que situarse en A acotaba a A— y estaba
    equivocada: la spec dice literalmente «Super Admin ve TODAS las compañías», y
    `get_company_filter` lo aplica así en todo el producto. Acotarlo solo en `/users` habría
    hecho que esta ruta se comportara distinto de `/masters` sin norma que lo pidiera, y
    rompió dos pruebas certificadas que provisionan usuarios entre empresas.

    **No es la fuga que cierra la enmienda.** El actor del hallazgo es el administrador
    acotado, y para él el filtro es obligatorio — lo prueban las cuatro primeras de esta
    suite. Si el propietario quiere además que `switch-company` acote a la autoridad global,
    es decisión de producto para todos los servicios: `R-126`.
    """
    r = await http_client.get("/api/v1/users?limit=100",
                              headers=_token(esc["super"], company_id=esc["a"]))
    assert r.status_code == 200, r.text
    nombres = {u["username"] for u in r.json()}
    assert esc["a1_username"] in nombres and esc["b1_username"] in nombres


async def test_sin_empresa_efectiva_y_sin_autoridad_global_se_deniega(http_client, esc):
    """`fail-closed`. El caso que el código anterior resolvía devolviéndolo todo.

    `MasterService` todavía lo hace —`R-116`, registrado y fuera de esta tanda—; aquí no.
    """
    from app.auth.models import User

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            u = (await s.execute(select(User).where(User.id == esc["admin_a"]))).scalar_one()
            u.company_id = None
            await s.commit()
        r = await http_client.get("/api/v1/users?limit=100", headers=_token(esc["admin_a"]))
        assert r.status_code == 403, (
            f"un actor sin empresa efectiva obtuvo {r.status_code}: {r.text[:120]}")
    finally:
        await motor.dispose()
