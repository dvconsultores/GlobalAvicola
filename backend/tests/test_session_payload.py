"""La sesión — `GA-REM-040` fase 8 · `T-040-20` · enmienda E · `AC-H11`…`AC-H14`.

```
LA SESIÓN REPRESENTA LA AUTORIDAD   ·   NO LA DEFINE
```

Cuatro conceptos que `§14.1` nombra por separado y que aquí se comprueban por separado:

```
habilitadas   de la empresa efectiva
concedidas    al usuario en esa empresa
efectivas     lo habilitado ∩ lo concedido
capacidades   los permisos `RBAC`
```

Si «concedidas» y «efectivas» nunca pudieran diferir, una de las dos sobraría. Hay una prueba
dedicada a que difieran.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "SESS-"
#: Los cuatro permisos del Administrador de Accesos — `OD-15 §6`.
ACCESO = {("business_units", "read"), ("business_units", "update"),
          ("business_units", "create"), ("business_units", "delete")}


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """Cinco actores y dos empresas, con estados que **no** coinciden entre sí.

    ```
    Empresa A   grandparent ON · breeder ON · hatchery ON · broiler SIN FILA
        MULTI       grandparent + breeder            → efectivas: las dos
        CERO        ninguna concesión                → efectivas: []
        DESHAB      concesión de hatchery            → se apagará hatchery en su prueba
        ACCESO      Administrador de Accesos         → capacidades sí · efectivas []
        SUPERVISOR  operativo, con breeder           → sin capacidades de administración
    Empresa B   hatchery ON · un usuario
    SUPER       autoridad global, sin empresa
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
        hab: dict[tuple[int, str], CompanyBusinessUnit] = {}
        for empresa, codes in ((a, ("grandparent", "breeder", "hatchery")),
                               (b, ("hatchery",))):
            for code in codes:
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id,
                                           is_enabled=True)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila

        def _rol(nombre, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", is_active=True)
            s.add(r)
            return r, permisos

        definiciones = [
            _rol("Operativo", [("lots", "read"), ("operations", "read")]),
            _rol("Acceso", sorted(ACCESO)),
            _rol("Supervisor", [("lots", "read"), ("operations", "read"),
                                ("review", "review")]),
            _rol("Global", [("*", a.value) for a in PermissionAction]),
        ]
        await s.flush()
        for rol, permisos in definiciones:
            for modulo, accion in permisos:
                # `scope_type` **no** es decorativo: la autoridad global es exactamente
                # `("*", …, "all")` (`docs/02 §3.1.4`). Sembrar el rol comodín con alcance
                # `"company"` lo dejaría sin ser global, y las pruebas de `AC-H13` medirían
                # un actor corriente creyendo medir uno global.
                s.add(Permission(role_id=rol.id, module=modulo,
                                 action=PermissionAction(accion),
                                 scope_type="all" if modulo == "*" else "company"))
        await s.flush()
        rol_op, rol_acceso, rol_sup, rol_global = (d[0] for d in definiciones)

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Ses",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        multi = _usuario(a.id, "MULTI", rol_op)
        cero = _usuario(a.id, "CERO", rol_op)
        deshab = _usuario(a.id, "DESHAB", rol_op)
        acceso = _usuario(a.id, "ACCESO", rol_acceso)
        supervisor = _usuario(a.id, "SUPERVISOR", rol_sup)
        user_b = _usuario(b.id, "USERB", rol_op)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([multi, cero, deshab, acceso, supervisor, user_b, superadmin])
        await s.flush()

        for code in ("grandparent", "breeder"):
            await conceder_unidad(s, user=multi, company_business_unit=hab[(a.id, code)])
        await conceder_unidad(s, user=deshab, company_business_unit=hab[(a.id, "hatchery")])
        await conceder_unidad(s, user=supervisor,
                              company_business_unit=hab[(a.id, "breeder")])
        await s.commit()

        # `§57`: no se infiere privilegio del nombre del rol ni de la empresa nula.
        assert any(p.module == "*" and p.scope_type == "all"
                   for p in (await s.execute(select(Permission).where(
                       Permission.role_id == rol_global.id))).scalars()), (
            "el rol global de la fixture no confiere autoridad global")

        datos = {"a": a.id, "b": b.id, "multi": multi.id, "cero": cero.id,
                 "deshab": deshab.id, "acceso": acceso.id, "supervisor": supervisor.id,
                 "user_b": user_b.id, "super": superadmin.id,
                 "hab_a_hatchery": hab[(a.id, "hatchery")].id,
                 "usuario_multi": multi.username, "url": test_database_url}
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


async def _sesion(http_client, user_id: int, company_id: int | None = None) -> dict:
    r = await http_client.get("/api/v1/me", headers=_token(user_id, company_id))
    assert r.status_code == 200, r.text
    return r.json()


async def _apagar(esc, cbu_id: int) -> None:
    from app.business_units.models import CompanyBusinessUnit

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            fila = (await s.execute(select(CompanyBusinessUnit).where(
                CompanyBusinessUnit.id == cbu_id))).scalar_one()
            fila.is_enabled = False
            await s.commit()
    finally:
        await motor.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-H11` · cuatro conceptos, cuatro campos
# ══════════════════════════════════════════════════════════════════════════════

async def test_h11_el_usuario_normal_recibe_los_cuatro_conjuntos(http_client, esc):
    """`AC-H11`. Exactos, no «al menos»."""
    s = await _sesion(http_client, esc["multi"])

    assert s["effective_company_id"] == esc["a"]
    assert s["is_super_admin"] is False
    assert sorted(s["company_business_units"]) == ["breeder", "grandparent", "hatchery"], (
        "las habilitadas son las de la empresa, no las del usuario")
    assert sorted(s["granted_business_units"]) == ["breeder", "grandparent"]
    assert sorted(s["effective_business_units"]) == ["breeder", "grandparent"]
    assert sorted(s["permissions"]) == ["lots:read", "operations:read"]


async def test_h11_concedidas_y_efectivas_pueden_diferir(http_client, esc):
    """El punto de tener las dos listas.

    `DESHAB` tiene Incubadora concedida. Al apagarla para la empresa, la concesión **sigue**
    —`AC-A04`, no se borra— y deja de ser efectiva. Si las dos listas no pudieran diferir,
    una de ellas sobraría.
    """
    antes = await _sesion(http_client, esc["deshab"])
    assert antes["granted_business_units"] == ["hatchery"]
    assert antes["effective_business_units"] == ["hatchery"]

    await _apagar(esc, esc["hab_a_hatchery"])

    despues = await _sesion(http_client, esc["deshab"])
    assert despues["granted_business_units"] == ["hatchery"], (
        "la concesión se borró: deshabilitar no revoca (`AC-A04`)")
    assert despues["effective_business_units"] == [], (
        "una unidad deshabilitada sigue apareciendo como efectiva")
    assert "hatchery" not in despues["company_business_units"]


async def test_h11_el_usuario_sin_concesiones_no_hereda_las_de_la_empresa(http_client, esc):
    """`OD-09.c`. La empresa tiene tres habilitadas; él, ninguna concedida."""
    s = await _sesion(http_client, esc["cero"])

    assert len(s["company_business_units"]) == 3
    assert s["granted_business_units"] == []
    assert s["effective_business_units"] == [], (
        "sin concesiones aparecieron unidades efectivas")
    assert s["permissions"], "y sigue teniendo sus capacidades CORE"


async def test_h11_las_listas_llegan_ordenadas(http_client, esc):
    """Determinismo: el contrato no depende del orden físico de las filas."""
    s = await _sesion(http_client, esc["multi"])
    for clave in ("company_business_units", "granted_business_units",
                  "effective_business_units", "permissions"):
        assert s[clave] == sorted(s[clave]), f"{clave} llegó sin ordenar"


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-H12` · `AC-H13` · empresa persistida, efectiva y actor global
# ══════════════════════════════════════════════════════════════════════════════

async def test_h13_la_autoridad_global_sin_contexto(http_client, esc):
    """`OD-14.d` representado. Sin empresa elegida no hay dato de inquilino."""
    s = await _sesion(http_client, esc["super"])

    assert s["is_super_admin"] is True
    assert s["effective_company_id"] is None, "apareció una empresa que nadie eligió"
    assert s["company_business_units"] == []
    assert s["granted_business_units"] == []
    assert s["effective_business_units"] == []


async def test_h13_la_autoridad_global_situada_cambia_de_inquilino(http_client, esc):
    """`AC-G05` en la sesión: el actor global no deja de serlo al situarse."""
    en_a = await _sesion(http_client, esc["super"], company_id=esc["a"])
    assert en_a["is_super_admin"] is True, "situarse le quitó la autoridad global"
    assert en_a["effective_company_id"] == esc["a"]
    assert sorted(en_a["company_business_units"]) == ["breeder", "grandparent", "hatchery"]

    en_b = await _sesion(http_client, esc["super"], company_id=esc["b"])
    assert en_b["is_super_admin"] is True
    assert en_b["effective_company_id"] == esc["b"]
    assert en_b["company_business_units"] == ["hatchery"], "quedó contexto de A"


async def test_h13_la_autoridad_global_no_hereda_unidades_productivas(http_client, esc):
    """Ser global no es tener las cuatro cadenas concedidas.

    `BU-D04` dejó la transversalidad como excepción **de SAP**, no como regla general.
    """
    s = await _sesion(http_client, esc["super"], company_id=esc["a"])
    assert s["granted_business_units"] == []
    assert s["effective_business_units"] == [], (
        "la autoridad global se convirtió en acceso productivo")


async def test_h12_la_empresa_persistida_no_es_la_efectiva(http_client, esc):
    """`AC-H12`. Para el actor global situado, difieren, y la sesión lo dice."""
    s = await _sesion(http_client, esc["super"], company_id=esc["a"])
    assert s["company_id"] is None, "la persistida del Super Administrador es nula"
    assert s["effective_company_id"] == esc["a"]

    # Y para un usuario corriente coinciden, que es lo que hace legible la distinción.
    n = await _sesion(http_client, esc["multi"])
    assert n["company_id"] == n["effective_company_id"] == esc["a"]


async def test_h13_el_usuario_corriente_no_falsifica_la_empresa(http_client, esc):
    """`OD-11` sigue mandando: una reclamación en el token no es autoridad."""
    s = await _sesion(http_client, esc["multi"], company_id=esc["b"])
    assert s["effective_company_id"] == esc["a"], "el token amplió el contexto"
    assert s["is_super_admin"] is False
    assert "hatchery" not in s["effective_business_units"]


# ══════════════════════════════════════════════════════════════════════════════
#  `AC-H14` · administrar no aparece como acceder
# ══════════════════════════════════════════════════════════════════════════════

async def test_h14_el_administrador_de_accesos_tiene_capacidades_y_cero_unidades(
        http_client, esc):
    """`AC-H14` · `OD-09.b` visible en el contrato. Las dos cosas **a la vez**."""
    s = await _sesion(http_client, esc["acceso"])

    assert set(s["permissions"]) == {f"{m}:{a}" for m, a in ACCESO}, s["permissions"]
    assert s["effective_business_units"] == [], (
        "administrar el acceso trajo acceso productivo")
    assert s["granted_business_units"] == []
    # Y sí ve la configuración de su empresa, que es lo que administra.
    assert len(s["company_business_units"]) == 3


async def test_h14_el_administrador_de_accesos_no_recibe_users_read(http_client, esc):
    """`OD-15 §6`, decidido al revés a propósito. La sesión lo refleja, no lo corrige."""
    s = await _sesion(http_client, esc["acceso"])
    assert "users:read" not in s["permissions"]
    assert not [p for p in s["permissions"] if p.startswith("users:")]


async def test_h14_el_administrador_de_accesos_no_tiene_comodin(http_client, esc):
    """`AC-S09` representado. Se comprueba sobre la carga real, no sobre texto."""
    s = await _sesion(http_client, esc["acceso"])
    assert s["is_super_admin"] is False
    assert not [p for p in s["permissions"] if p.startswith("*:")], s["permissions"]


async def test_el_supervisor_no_gana_capacidades_de_administracion(http_client, esc):
    """`Supervisor Avícola` ≠ `Administrador de Accesos`, también en la sesión."""
    s = await _sesion(http_client, esc["supervisor"])
    assert not [p for p in s["permissions"] if p.startswith("business_units:")]
    assert s["effective_business_units"] == ["breeder"], "y sí opera lo suyo"


# ══════════════════════════════════════════════════════════════════════════════
#  Frescura y contrato
# ══════════════════════════════════════════════════════════════════════════════

async def test_una_revocacion_se_ve_en_la_sesion_siguiente(http_client, esc):
    """La sesión se resuelve en el servidor: no arrastra autorización caducada.

    `§6.4` de la spec lo exigía para la autorización; aquí se comprueba que la
    **representación** tampoco se queda atrás.
    """
    from app.auth.models import User
    from app.business_units.models import CompanyBusinessUnit
    from app.business_units.service import revocar_unidad

    assert (await _sesion(http_client, esc["supervisor"]))["effective_business_units"] \
        == ["breeder"]

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            u = (await s.execute(
                select(User).where(User.id == esc["supervisor"]))).scalar_one()
            from app.business_units.models import BusinessUnit
            cbu = (await s.execute(
                select(CompanyBusinessUnit)
                .join(BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id)
                .where(CompanyBusinessUnit.company_id == esc["a"],
                       BusinessUnit.code == "breeder"))).scalar_one()
            await revocar_unidad(s, user=u, company_business_unit=cbu)
            await s.commit()
    finally:
        await motor.dispose()

    despues = await _sesion(http_client, esc["supervisor"])
    assert despues["effective_business_units"] == [], "la sesión sirvió una concesión revocada"
    assert despues["granted_business_units"] == [], "una concesión revocada sigue contando"


async def test_la_sesion_no_arrastra_campos_internos(http_client, esc):
    """`R-112`. La proyección es declarada: lo que no está en el contrato no viaja."""
    s = await _sesion(http_client, esc["multi"])

    for prohibido in ("hashed_password", "password", "role", "permissions_raw"):
        assert prohibido not in s, f"la sesión expuso {prohibido!r}"
    assert isinstance(s["permissions"], list)
    assert all(isinstance(p, str) and ":" in p for p in s["permissions"])


async def test_la_sesion_no_expone_dato_de_otra_empresa(http_client, esc):
    """El actor de A no ve nada de B, ni siquiera por el nombre de una unidad ajena."""
    s = await _sesion(http_client, esc["multi"])
    assert str(esc["b"]) not in str(s.get("effective_company_id"))
    assert s["company_id"] == esc["a"]
