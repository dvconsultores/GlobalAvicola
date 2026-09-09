"""Los candidatos a recibir una unidad — `GA-REM-040` enmienda F · `R-129` · `AC-H15` · `AC-H16`.

```
DESCUBRIR A QUIÉN CONCEDER   ≠   ADMINISTRAR USUARIOS
```

El sujeto es el `Administrador de Accesos` real: cuatro permisos de `business_units`, sin
`users:*`, sin comodín, sin ninguna cadena concedida. Puede pedir candidatos y sigue sin poder
listar usuarios. Si alguna vez las dos cosas coincidieran, `R-129` habría reabierto lo que
`OD-15 §6` cerró.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "CAND-"
ACCESO = {("business_units", "read"), ("business_units", "update"),
          ("business_units", "create"), ("business_units", "delete")}
#: El contrato exacto de `AC-H15`. Un campo de más rompe.
CAMPOS = {"user_id", "username", "display_name", "already_granted"}


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """El escenario, con **precondiciones afirmadas** y no supuestas (`§35`).

    ```
    Empresa A   hatchery ON · breeder ON · broiler OFF (fila explícita)
        ADMIN       Administrador de Accesos · sin concesiones
        A1          activo · elegible
        A2          activo · YA tiene hatchery
        INACTIVO    is_active = False
        SUPERVISOR  opera hatchery · sin permisos de administración
        NORMAL      solo lots:read
    Empresa B   hatchery ON · B1
    SUPER       comodín ("*", …, "all"), sin empresa
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import Company

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, estados in ((a, {"hatchery": True, "breeder": True, "broiler": False}),
                                 (b, {"hatchery": True})):
            for code, on in estados.items():
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id, is_enabled=on)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila

        def _rol(nombre):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", is_active=True)
            s.add(r)
            return r

        rol_acceso, rol_sup, rol_normal, rol_global = (
            _rol("Acceso"), _rol("Supervisor"), _rol("Normal"), _rol("Global"))
        await s.flush()
        for m, acc in ACCESO:
            s.add(Permission(role_id=rol_acceso.id, module=m,
                             action=PermissionAction(acc), scope_type="company"))
        for rol in (rol_sup, rol_normal):
            s.add(Permission(role_id=rol.id, module="lots",
                             action=PermissionAction.READ, scope_type="company"))
        for acc in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=acc,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol, activo=True):
            return User(first_name=marca, last_name="Cand",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=activo)

        admin = _usuario(a.id, "ADMIN", rol_acceso)
        a1 = _usuario(a.id, "A1", rol_normal)
        a2 = _usuario(a.id, "A2", rol_normal)
        inactivo = _usuario(a.id, "INACTIVO", rol_normal, activo=False)
        supervisor = _usuario(a.id, "SUPERVISOR", rol_sup)
        normal = _usuario(a.id, "NORMAL", rol_normal)
        b1 = _usuario(b.id, "B1", rol_normal)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([admin, a1, a2, inactivo, supervisor, normal, b1, superadmin])
        await s.flush()

        await conceder_unidad(s, user=a2, company_business_unit=hab[(a.id, "hatchery")])
        await conceder_unidad(s, user=supervisor,
                              company_business_unit=hab[(a.id, "hatchery")])

        # `§35` · `§57`: la fixture afirma sus precondiciones en vez de darlas por hechas.
        assert admin.company_id == a.id and b1.company_id == b.id and a.id != b.id
        permisos_admin = {(p.module, p.action.value) for p in (await s.execute(
            select(Permission).where(Permission.role_id == rol_acceso.id))).scalars()}
        assert permisos_admin == ACCESO, "el administrador de la fixture no es mínimo"
        assert any(p.module == "*" and p.scope_type == "all" for p in (await s.execute(
            select(Permission).where(Permission.role_id == rol_global.id))).scalars())
        await s.commit()

        datos = {"a": a.id, "b": b.id, "admin": admin.id, "a1": a1.id, "a2": a2.id,
                 "inactivo": inactivo.id, "supervisor": supervisor.id, "normal": normal.id,
                 "b1": b1.id, "super": superadmin.id,
                 "u_admin": admin.username, "u_a1": a1.username, "u_a2": a2.username,
                 "u_inactivo": inactivo.username, "u_b1": b1.username,
                 "u_supervisor": supervisor.username, "url": test_database_url}
    yield datos

    async with motor.begin() as c:
        for sql in (
            "DELETE FROM audit_logs WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM user_business_units WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
        ):
            await c.execute(text(sql), {"p": f"{PREFIJO}%"})
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


RUTA = "/api/v1/business-units/hatchery/grant-candidates"


async def _candidatos(http_client, user_id, company_id=None):
    r = await http_client.get(RUTA, headers=_token(user_id, company_id))
    assert r.status_code == 200, r.text
    return {c["username"]: c for c in r.json()}


async def _efectivas(esc, user_id):
    from app.business_units.service import unidades_efectivas_por_id

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            return await unidades_efectivas_por_id(s, user_id=user_id, company_id=esc["a"])
    finally:
        await motor.dispose()


async def _cuenta(esc, tabla, where, params):
    motor = create_async_engine(esc["url"])
    try:
        async with motor.connect() as c:
            return (await c.execute(
                text(f"SELECT count(*) FROM {tabla} WHERE {where}"), params)).scalar()
    finally:
        await motor.dispose()


# ── `AC-H15` · la superficie ─────────────────────────────────────────────────

async def test_c1_el_administrador_ve_a_los_elegibles_de_su_empresa(http_client, esc):
    c = await _candidatos(http_client, esc["admin"])
    assert esc["u_a1"] in c and esc["u_a2"] in c, "faltan elegibles"
    assert esc["u_b1"] not in c, "apareció un usuario de la empresa B"
    assert esc["u_inactivo"] not in c, "un usuario inactivo no es elegible"
    assert esc["u_admin"] not in c, "el actor se ofreció a sí mismo (`OD-15.a`)"


async def test_c9_quien_ya_la_tiene_aparece_marcado(http_client, esc):
    """Ocultarlo haría indistinguible «nunca se le dio» de «ya la tiene»."""
    c = await _candidatos(http_client, esc["admin"])
    assert c[esc["u_a2"]]["already_granted"] is True
    assert c[esc["u_a1"]]["already_granted"] is False
    assert c[esc["u_supervisor"]]["already_granted"] is True, (
        "el supervisor tiene hatchery concedida y debe verse marcado")


async def test_c8_la_proyeccion_es_minima_y_exacta(http_client, esc):
    """`§23`. Ni correo, ni teléfono, ni rol, ni permisos, ni hash."""
    c = await _candidatos(http_client, esc["admin"])
    for candidato in c.values():
        assert set(candidato) == CAMPOS, f"campos inesperados: {set(candidato) - CAMPOS}"
    assert c[esc["u_a1"]]["display_name"] == "A1 Cand"
    assert c[esc["u_a1"]]["user_id"] == esc["a1"]


async def test_las_listas_llegan_ordenadas_por_username(http_client, esc):
    r = await http_client.get(RUTA, headers=_token(esc["admin"]))
    nombres = [c["username"] for c in r.json()]
    assert nombres == sorted(nombres)


async def test_una_unidad_no_habilitada_no_tiene_candidatos(http_client, esc):
    """Refleja la puerta del `POST`: para una unidad apagada no hay nada que conceder."""
    r = await http_client.get("/api/v1/business-units/broiler/grant-candidates",
                              headers=_token(esc["admin"]))
    assert r.status_code == 409, r.text
    r = await http_client.get("/api/v1/business-units/pescado/grant-candidates",
                              headers=_token(esc["admin"]))
    assert r.status_code == 404, r.text


# ── `AC-H16` · descubrir no es administrar ───────────────────────────────────

async def test_c2_el_mismo_actor_sigue_sin_poder_listar_usuarios(http_client, esc):
    """El contraste obligatorio. Sin él, esto sería `users:read` con otro nombre."""
    ok = await http_client.get(RUTA, headers=_token(esc["admin"]))
    assert ok.status_code == 200, ok.text

    negado = await http_client.get("/api/v1/users", headers=_token(esc["admin"]))
    assert negado.status_code == 403, f"`/users` se abrió: {negado.status_code}"

    sesion = await http_client.get("/api/v1/me", headers=_token(esc["admin"]))
    assert "users:read" not in sesion.json()["permissions"]


async def test_c4_c5_sin_autoridad_de_conceder_no_hay_candidatos(http_client, esc):
    """El supervisor opera hatchery y no reparte; el normal ni eso."""
    for quien in ("supervisor", "normal"):
        r = await http_client.get(RUTA, headers=_token(esc[quien]))
        assert r.status_code == 403, f"{quien}: {r.status_code}"


async def test_c3_conocer_a_un_usuario_ajeno_no_lo_trae(http_client, esc):
    """No hay parámetro de búsqueda ni de identificador: no hay oráculo que consultar."""
    r = await http_client.get(f"{RUTA}?search={esc['u_b1']}&user_id={esc['b1']}",
                              headers=_token(esc["admin"]))
    assert r.status_code == 200, r.text
    assert esc["u_b1"] not in {c["username"] for c in r.json()}


# ── `OD-14` · la autoridad global ────────────────────────────────────────────

async def test_c6_la_autoridad_global_situada_ve_solo_esa_empresa(http_client, esc):
    en_a = await _candidatos(http_client, esc["super"], esc["a"])
    assert esc["u_a1"] in en_a and esc["u_b1"] not in en_a
    en_b = await _candidatos(http_client, esc["super"], esc["b"])
    assert esc["u_b1"] in en_b and esc["u_a1"] not in en_b


async def test_c7_la_autoridad_global_sin_contexto_no_obtiene_la_union(http_client, esc):
    r = await http_client.get(RUTA, headers=_token(esc["super"]))
    assert r.status_code == 403, r.text


# ── lectura pura ─────────────────────────────────────────────────────────────

async def test_c13_descubrir_no_escribe_nada(http_client, esc):
    p = {"p": f"{PREFIJO}%"}
    antes = (
        await _cuenta(esc, "user_business_units",
                      "user_id IN (SELECT id FROM users WHERE username LIKE :p)", p),
        await _cuenta(esc, "audit_logs", "entity_type = 'user_business_unit'", {}),
    )
    await _candidatos(http_client, esc["admin"])
    despues = (
        await _cuenta(esc, "user_business_units",
                      "user_id IN (SELECT id FROM users WHERE username LIKE :p)", p),
        await _cuenta(esc, "audit_logs", "entity_type = 'user_business_unit'", {}),
    )
    assert antes == despues, "la lectura dejó rastro de escritura"


# ── `C10`…`C12` · el flujo completo, y sus dos negativas ─────────────────────

async def test_c10_e2e_descubrir_elegir_y_conceder(client, http_client, esc):
    """El flujo que la fase 9 va a recorrer, sin interfaz."""
    c = await _candidatos(http_client, esc["admin"])
    elegido = c[esc["u_a1"]]
    assert elegido["already_granted"] is False

    r = await client.post(f"/api/v1/users/{elegido['user_id']}/business-units",
                          headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 201, r.text
    assert await _efectivas(esc, esc["a1"]) == ["hatchery"]

    # Y la lista lo refleja en la lectura siguiente.
    assert (await _candidatos(http_client, esc["admin"]))[esc["u_a1"]]["already_granted"] is True


async def test_c11_la_auto_concesion_sigue_denegada_aunque_no_se_ofrezca(http_client, esc):
    """La exclusión del actor es cortesía; la seguridad está en el `POST`."""
    r = await http_client.post(f"/api/v1/users/{esc['admin']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 403, r.text
    assert await _efectivas(esc, esc["admin"]) == []


async def test_c12_un_objetivo_ajeno_enviado_a_mano_sigue_denegado(http_client, esc):
    """Filtrar candidatos no es la frontera de seguridad. La frontera es la concesión."""
    r = await http_client.post(f"/api/v1/users/{esc['b1']}/business-units",
                               headers=_token(esc["admin"]), json={"code": "hatchery"})
    assert r.status_code == 404, r.text
    assert await _cuenta(esc, "user_business_units", "user_id = :u", {"u": esc["b1"]}) == 0
