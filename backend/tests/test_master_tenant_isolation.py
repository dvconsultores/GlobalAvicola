"""Aislamiento de inquilino en los maestros — `RQ-03` · `AC05` · `R-115` · `R-116`.

Dos huecos de la **misma** función, `MasterService._apply_company_filter`:

```
R-115   `Company` no tiene columna `company_id` — su clave de inquilino es su propio `id`.
        `hasattr(modelo, "company_id")` es falso y el filtro no se aplica nunca.
R-116   `if not self.user_company_id: return query` — un actor sin empresa que no sea
        Super Administrador recibe la consulta **sin acotar**. `fail-open`.
```

Ninguno es requisito nuevo. `AC05` los gobierna desde el primer día; lo que faltó fue que
`TENANT_RESOURCE_CLASSIFICATION.md` los incluyera en el universo de aplicación — la misma
causa que dejó `users` fuera.

**Lo que estas pruebas NO tocan.** `docs/02 §3.1.4` dice literal: «Super Admin (rol con
`module="*"`, `scope_type="all"`) ve TODAS las compañías». Esa semántica se **preserva** y hay
una prueba dedicada a comprobarlo. Cambiarla es `R-126`, decisión de propietario.
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

PREFIJO = "MTEN-"
#: Marcadores distinguibles: si los dos inquilinos tuvieran el mismo dato, una fuga sería
#: invisible. `§32`.
#: **`sap_config` va nulo a propósito.** La columna es `String` y `CompanyRead` la valida como
#: `dict`, de modo que cualquier empresa con configuración `SAP` hace que `/masters/companies`
#: devuelva **500** para todo el mundo — es `R-127`, un defecto distinto y registrado aparte.
#:
#: Eso obliga a precisar la redacción original de `R-115`: la exposición de `sap_config` estaba
#: **latente detrás de ese 500**, no activa. Lo que sí era alcanzable —y lo que estas pruebas
#: cierran— es la fuga de la **fila entera** de la empresa ajena. Y probarlo sobre la fila
#: completa es más fuerte que sobre un campo: si la fila no sale, no sale ninguno de sus campos.
MARCA_A = f"{PREFIJO}TAXA-SOLO-A"
MARCA_B = f"{PREFIJO}TAXB-SOLO-B"


def _token(user_id: int, company_id: int | None = None) -> dict:
    """`company_id` reclama un contexto de empresa. `OD-11`: solo vale para quien puede
    cambiarlo; para el resto la reclamación se descarta y manda la base."""
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """Dos empresas con configuración distinguible, y tres actores.

    ```
    Empresa A   sap_config con `MTEN-SOLO-A`  ·  una granja propia
    Empresa B   sap_config con `MTEN-SOLO-B`  ·  una granja propia
    ACTOR_A     masters:read/update/delete · empresa A · NO super administrador
    SIN_EMPRESA masters:read · company_id NULL · NO super administrador   → `R-116`
    SUPER       comodín ("*", …, "all") — su alcance global se preserva
    ```
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company, Farm, FarmType

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True,
                    tax_id=MARCA_A, country="Venezuela", currency="USD",
                    sap_config=None, approval_levels=2)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True,
                    tax_id=MARCA_B, country="Colombia", currency="COP",
                    sap_config=None, approval_levels=3)
        s.add_all([a, b])
        await s.flush()

        granja_a = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA",
                        farm_type=FarmType.BREEDING, is_active=True)
        granja_b = Farm(company_id=b.id, name=f"{PREFIJO}GRANJA-B", code=f"{PREFIJO}GB",
                        farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja_a, granja_b])
        await s.flush()

        def _rol(nombre):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", is_active=True)
            s.add(r)
            return r

        rol_maestros = _rol("Maestros")
        rol_global = _rol("Global")
        await s.flush()
        for accion in (PermissionAction.READ, PermissionAction.UPDATE,
                       PermissionAction.DELETE, PermissionAction.CREATE):
            s.add(Permission(role_id=rol_maestros.id, module="masters", action=accion,
                             scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Mst",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        actor_a = _usuario(a.id, "ACTORA", rol_maestros)
        sin_empresa = _usuario(None, "SINEMP", rol_maestros)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([actor_a, sin_empresa, superadmin])
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "b": b.id, "actor_a": actor_a.id,
                 "sin_empresa": sin_empresa.id, "super": superadmin.id,
                 "granja_a": granja_a.id, "granja_b": granja_b.id,
                 "nombre_a": a.name, "nombre_b": b.name,
                 "rol_maestros": rol_maestros.id, "url": test_database_url}
    yield datos

    async with motor.begin() as c:
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN "
                             "(SELECT id FROM users WHERE username LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        from app.auth.models import Permission, Role, User
        from app.masters.models import Company, Farm
        ids = (await c.execute(text("SELECT id FROM roles WHERE name LIKE :p"),
                               {"p": f"{PREFIJO}%"})).scalars().all()
        if ids:
            await c.execute(delete(Permission).where(Permission.role_id.in_(ids)))
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
        await c.execute(delete(Role).where(Role.name.like(f"{PREFIJO}%")))
        await c.execute(delete(Farm).where(Farm.name.like(f"{PREFIJO}%")))
        # Las habilitaciones de unidad que crea la prueba de `OD-14`: sin borrarlas, la
        # eliminación de empresas viola la clave foránea y el fallo aparece en el teardown,
        # lejos de su causa.
        await c.execute(text(
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)"), {"p": f"{PREFIJO}%"})
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await motor.dispose()


async def _empresa(esc, company_id: int) -> dict:
    from app.masters.models import Company

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            c = (await s.execute(select(Company).where(Company.id == company_id))).scalar_one()
            return {"name": c.name, "tax_id": c.tax_id, "country": c.country,
                    "currency": c.currency, "sap_config": c.sap_config,
                    "approval_levels": c.approval_levels, "is_active": c.is_active}
    finally:
        await motor.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  `R-115` · la empresa es su propio inquilino
# ══════════════════════════════════════════════════════════════════════════════

async def test_r115_el_listado_de_empresas_no_muestra_la_ajena(http_client, esc):
    """`AC05`. `Company` no tiene `company_id`: su clave de inquilino es su `id`."""
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    nombres = {c["name"] for c in r.json()}

    assert esc["nombre_a"] in nombres, "el actor debe ver la suya"
    assert esc["nombre_b"] not in nombres, "fuga de inquilino: apareció la empresa B"


async def test_r115_ningun_campo_de_la_empresa_ajena_viaja(http_client, esc):
    """La fila entera, no un campo suelto.

    `R-115` nombraba `tax_id`, `country`, `currency`, `approval_levels` y `sap_config`.
    Comprobar que **la fila ajena no sale** los cubre todos a la vez, y sigue cubriendo los
    que se añadan mañana. `sap_config` va nulo por `R-127`.
    """
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    assert MARCA_B not in r.text, "viajó el identificador fiscal de la empresa B"
    # Y la propia sí: sin esto, «no se ve la ajena» sería compatible con «no se ve ninguna».
    assert MARCA_A in r.text


async def test_r115_conocer_el_identificador_ajeno_no_abre_la_empresa(http_client, esc):
    """`IDOR` de inquilino sobre el propio maestro de empresas."""
    r = await http_client.get(f"/api/v1/masters/companies/{esc['b']}",
                              headers=_token(esc["actor_a"]))
    assert r.status_code == 404, f"{r.status_code}: {r.text[:200]}"
    assert MARCA_B not in r.text


async def test_r115_la_empresa_propia_si_se_consulta(http_client, esc):
    r = await http_client.get(f"/api/v1/masters/companies/{esc['a']}",
                              headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    assert r.json()["name"] == esc["nombre_a"]


async def test_r115_no_se_modifica_la_empresa_ajena(http_client, esc):
    """`AC05` sobre la escritura, y sin efectos colaterales."""
    antes = await _empresa(esc, esc["b"])
    r = await http_client.put(f"/api/v1/masters/companies/{esc['b']}",
                              headers=_token(esc["actor_a"]),
                              json={"name": "TOMADA", "approval_levels": 1})
    assert r.status_code == 404, r.text
    assert await _empresa(esc, esc["b"]) == antes, "la empresa ajena cambió"


async def test_r115_no_se_da_de_baja_la_empresa_ajena(http_client, esc):
    antes = await _empresa(esc, esc["b"])
    r = await http_client.delete(f"/api/v1/masters/companies/{esc['b']}",
                                 headers=_token(esc["actor_a"]))
    assert r.status_code == 404, r.text
    assert await _empresa(esc, esc["b"]) == antes


async def test_r115_el_super_administrador_conserva_su_alcance_global(http_client, esc):
    """`docs/02 §3.1.4`, preservado a propósito. Cambiarlo es `R-126`, no esta tanda."""
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(esc["super"]))
    assert r.status_code == 200, r.text
    nombres = {c["name"] for c in r.json()}
    assert esc["nombre_a"] in nombres and esc["nombre_b"] in nombres, (
        "se acotó al Super Administrador: eso contradice `docs/02 §3.1.4`")


# ══════════════════════════════════════════════════════════════════════════════
#  `R-116` · sin empresa efectiva no se ve nada
# ══════════════════════════════════════════════════════════════════════════════

async def test_r116_el_actor_sin_empresa_no_ve_maestros_de_nadie(http_client, esc):
    """`fail-closed`. Antes recibía la consulta **sin acotar**: los maestros de todas."""
    r = await http_client.get("/api/v1/masters/farms?limit=100",
                              headers=_token(esc["sin_empresa"]))
    assert r.status_code == 200, r.text
    nombres = {f["name"] for f in r.json()}
    assert f"{PREFIJO}GRANJA-A" not in nombres
    assert f"{PREFIJO}GRANJA-B" not in nombres, (
        "un actor sin empresa efectiva vio granjas ajenas")


async def test_r116_el_actor_sin_empresa_tampoco_ve_empresas(http_client, esc):
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(esc["sin_empresa"]))
    assert r.status_code == 200, r.text
    assert MARCA_A not in r.text and MARCA_B not in r.text


async def test_r116_el_actor_sin_empresa_no_alcanza_por_identificador(http_client, esc):
    r = await http_client.get(f"/api/v1/masters/farms/{esc['granja_b']}",
                              headers=_token(esc["sin_empresa"]))
    assert r.status_code == 404, r.text


async def test_r116_el_actor_con_empresa_si_ve_lo_suyo(http_client, esc):
    """CONTROL. Sin esto, todo lo anterior pasaría con un filtro que niega a todo el mundo."""
    r = await http_client.get("/api/v1/masters/farms?limit=100",
                              headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    nombres = {f["name"] for f in r.json()}
    assert f"{PREFIJO}GRANJA-A" in nombres
    assert f"{PREFIJO}GRANJA-B" not in nombres


# ══════════════════════════════════════════════════════════════════════════════
#  El filtro vive en la consulta, no después de paginar · `§36` · `§42`
# ══════════════════════════════════════════════════════════════════════════════

async def test_el_filtro_de_maestros_precede_a_la_paginacion(http_client, esc):
    """`§16` · `§36`. Con una fixture que **sí** distingue las dos implementaciones.

    Treinta granjas de `B` y **después** una de `A`, de modo que la de `A` tenga el
    identificador más alto:

    ```
    FILTRO EN LA CONSULTA   `A` tiene 2 granjas · la nueva entra en la primera página
    FILTRO DESPUÉS          la primera página son treinta filas de `B` · la de `A` no está
    ```

    Y el recuento: `total` se calcula sobre la subconsulta ya acotada, de modo que las filas
    ajenas no se delatan por diferencia.
    """
    from app.masters.models import Farm, FarmType

    marca = f"{PREFIJO}GRANJA-TARDIA"
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            for i in range(30):
                s.add(Farm(company_id=esc["b"], name=f"{PREFIJO}REL{i}",
                           code=f"{PREFIJO}R{i}", farm_type=FarmType.BREEDING,
                           is_active=True))
            await s.flush()
            s.add(Farm(company_id=esc["a"], name=marca, code=f"{PREFIJO}GT",
                       farm_type=FarmType.BREEDING, is_active=True))
            await s.commit()
    finally:
        await motor.dispose()

    r = await http_client.get("/api/v1/masters/farms?limit=20",
                              headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    nombres = {f["name"] for f in r.json()}

    assert marca in nombres, (
        "la granja más reciente de la empresa propia no está en la primera página: "
        "el filtro se aplicó después de paginar")
    assert not [n for n in nombres if n.startswith(f"{PREFIJO}REL")]

    total = r.headers.get("X-Total-Count")
    if total is not None:
        assert int(total) == 2, f"el recuento delata filas ajenas: {total}"


# ══════════════════════════════════════════════════════════════════════════════
#  `OD-14` · la autoridad global situada opera en una sola empresa
# ══════════════════════════════════════════════════════════════════════════════

async def test_od14_la_autoridad_global_situada_solo_ve_las_granjas_de_esa_empresa(
        http_client, esc):
    """`AC-G05` · `§68`. Las granjas son maestro de **inquilino**, no control global."""
    en_a = await http_client.get("/api/v1/masters/farms?limit=100",
                                 headers=_token(esc["super"], company_id=esc["a"]))
    assert en_a.status_code == 200, en_a.text
    nombres_a = {f["name"] for f in en_a.json()}
    assert f"{PREFIJO}GRANJA-A" in nombres_a
    assert f"{PREFIJO}GRANJA-B" not in nombres_a, (
        "situada en A y devolvió la granja de B")

    en_b = await http_client.get("/api/v1/masters/farms?limit=100",
                                 headers=_token(esc["super"], company_id=esc["b"]))
    assert en_b.status_code == 200, en_b.text
    nombres_b = {f["name"] for f in en_b.json()}
    assert f"{PREFIJO}GRANJA-B" in nombres_b
    assert f"{PREFIJO}GRANJA-A" not in nombres_b, "el contexto no se movió con el actor"


async def test_od14_la_autoridad_global_sin_contexto_no_ve_granjas(http_client, esc):
    """`OD-14.d`. Sin empresa elegida no hay unión de inquilinos, hay cero filas."""
    r = await http_client.get("/api/v1/masters/farms?limit=100",
                              headers=_token(esc["super"]))
    assert r.status_code == 200, r.text
    nombres = {f["name"] for f in r.json()}
    assert f"{PREFIJO}GRANJA-A" not in nombres and f"{PREFIJO}GRANJA-B" not in nombres


async def test_od14_la_administracion_de_unidades_sigue_el_contexto(http_client, esc):
    """`AC-G05` · `§69`. La fase 7 ya lo exigía; aquí se comprueba que no ha cambiado.

    Se habilita Incubadora en `B` y **no** en `A`. La autoridad global situada en `A` debe
    ver su propio estado, no el del vecino: el identificador de la habilitación de `B` ni
    siquiera es expresable, porque estas rutas direccionan por código.
    """
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            unidad = (await s.execute(select(BusinessUnit).where(
                BusinessUnit.code == "hatchery"))).scalar_one()
            s.add(CompanyBusinessUnit(company_id=esc["b"],
                                      business_unit_id=unidad.id, is_enabled=True))
            await s.commit()
    finally:
        await motor.dispose()

    en_a = await http_client.get("/api/v1/business-units",
                                 headers=_token(esc["super"], company_id=esc["a"]))
    assert en_a.status_code == 200, en_a.text
    estado_a = {u["code"]: u["is_enabled"] for u in en_a.json()}
    assert estado_a["hatchery"] is False, "vio la habilitación de la empresa B"

    en_b = await http_client.get("/api/v1/business-units",
                                 headers=_token(esc["super"], company_id=esc["b"]))
    assert en_b.status_code == 200, en_b.text
    assert {u["code"]: u["is_enabled"] for u in en_b.json()}["hatchery"] is True


async def test_od14_contraste_empresas_global_frente_a_granjas_de_inquilino(
        http_client, esc):
    """`AC-G03` · `§73`. El contraste, también en maestros.

    El mismo actor, situado en `A`: el catálogo de empresas devuelve las dos, y las granjas
    solo las de `A`. Es la prueba de que la clasificación existe y no es una casualidad del
    filtro.
    """
    cabeceras = _token(esc["super"], company_id=esc["a"])

    empresas = await http_client.get("/api/v1/masters/companies?limit=100",
                                     headers=cabeceras)
    assert empresas.status_code == 200, empresas.text
    ids = {c["id"] for c in empresas.json()}
    assert esc["a"] in ids and esc["b"] in ids, "el catálogo de empresas dejó de ser global"

    granjas = await http_client.get("/api/v1/masters/farms?limit=100", headers=cabeceras)
    assert granjas.status_code == 200, granjas.text
    assert f"{PREFIJO}GRANJA-B" not in {f["name"] for f in granjas.json()}
