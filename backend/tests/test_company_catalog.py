"""`GA-REM-033` enmienda A · `R-127` · `OD-18`: el catálogo de empresas es una proyección
acotada y segura.

La columna `Company.sap_config` es `String`. El contrato de lectura anterior
(`CompanyRead.sap_config: Optional[dict]`) validaba ese texto como diccionario y respondía
`500` en cuanto una empresa lo tenía poblado — para el actor de la empresa y para la
autoridad global por igual. `OD-18` decide que el catálogo general **no contiene**
configuración SAP; esta prueba fija ese contrato.

Fixture propia, no la de `test_master_tenant_isolation`: aquélla deja `sap_config` nulo a
propósito para no tropezar con `R-127`; ésta lo puebla a propósito para tropezar con él.

    Empresa A   sap_config TEXTO NO NULO   ← tratamiento
    Empresa B   sap_config NULL            ← control
    ACTOR_A     masters:read · empresa A
    ACTOR_B     masters:read · empresa B
    SUPER       comodín ("*", …, "all") · sin empresa persistida
"""
from __future__ import annotations

import pathlib
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "CCAT-"
MARCA_A = f"{PREFIJO}TAXA"
MARCA_B = f"{PREFIJO}TAXB"
#: Texto, que es lo que la columna admite. La marca interior es lo que no debe viajar nunca.
SAP_CONFIG_A = '{"sap_client": "100", "system": "CCAT-S4H-SECRETO"}'
MARCA_SAP = "CCAT-S4H-SECRETO"

#: `AC16` · el conjunto exacto. No «al menos»: exacto.
CAMPOS_APROBADOS = {
    "id", "name", "tax_id", "country", "currency", "approval_levels",
    "is_active", "created_at", "updated_at",
}
#: `AC23` · lo que el selector de la fase 9 necesita.
CAMPOS_DEL_SELECTOR = {"id", "name", "is_active"}


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def cat(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True,
                    tax_id=MARCA_A, country="Venezuela", currency="USD",
                    sap_config=SAP_CONFIG_A, approval_levels=2)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True,
                    tax_id=MARCA_B, country="Colombia", currency="COP",
                    sap_config=None, approval_levels=3)
        s.add_all([a, b])
        await s.flush()

        def _rol(nombre):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", is_active=True)
            s.add(r)
            return r

        rol_lector = _rol("Lector")
        rol_global = _rol("Global")
        await s.flush()
        s.add(Permission(role_id=rol_lector.id, module="masters",
                         action=PermissionAction.READ, scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Cat",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        actor_a = _usuario(a.id, "ACTORA", rol_lector)
        actor_b = _usuario(b.id, "ACTORB", rol_lector)
        superadmin = _usuario(None, "SUPER", rol_global)
        s.add_all([actor_a, actor_b, superadmin])
        await s.flush()
        await s.commit()
        datos = {"a": a.id, "b": b.id, "nombre_a": a.name, "nombre_b": b.name,
                 "actor_a": actor_a.id, "actor_b": actor_b.id, "super": superadmin.id}
    yield datos
    async with motor.begin() as c:
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN "
                             "(SELECT id FROM users WHERE username LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM permissions WHERE role_id IN "
                             "(SELECT id FROM roles WHERE name LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM users WHERE username LIKE :p"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM roles WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM company_business_units WHERE company_id IN "
                             "(SELECT id FROM companies WHERE name LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await motor.dispose()


def _filas(respuesta) -> list[dict]:
    cuerpo = respuesta.json()
    return cuerpo["items"] if isinstance(cuerpo, dict) else cuerpo


# ═══════════════════════════════════════════════════════════════════════════
#  Control y tratamiento
# ═══════════════════════════════════════════════════════════════════════════

async def test_t1_ac13_control_con_sap_config_nulo_el_catalogo_responde_200(http_client, cat):
    """`AC13`. Control: la empresa B no tiene `sap_config`. Demuestra que autenticación,
    permiso y ruta están bien: lo que falle en el tratamiento no será eso."""
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(cat["actor_b"]))
    assert r.status_code == 200, r.text
    assert cat["nombre_b"] in {c["name"] for c in _filas(r)}


async def test_t2_ac14_tratamiento_con_sap_config_no_nulo_el_catalogo_responde_200(
        http_client, cat):
    """`AC14` · **el rojo de `R-127`**. Mismo rol, misma ruta; la única diferencia es que
    la empresa A tiene `sap_config` poblado. Antes: `500`."""
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(cat["actor_a"]))
    assert r.status_code == 200, r.text
    assert cat["nombre_a"] in {c["name"] for c in _filas(r)}


async def test_t2b_ac14_el_detalle_de_la_empresa_con_sap_config_responde_200(http_client, cat):
    """`AC14`, en la lectura individual: es la misma proyección."""
    r = await http_client.get(f"/api/v1/masters/companies/{cat['a']}",
                              headers=_token(cat["actor_a"]))
    assert r.status_code == 200, r.text
    assert r.json()["id"] == cat["a"]


# ═══════════════════════════════════════════════════════════════════════════
#  El contrato
# ═══════════════════════════════════════════════════════════════════════════

async def test_t3_ac15_sap_config_no_viaja_en_el_catalogo(http_client, cat):
    """`AC15` · `OD-18.a`. Ni la clave ni su contenido, en listado ni en detalle."""
    listado = await http_client.get("/api/v1/masters/companies?limit=100",
                                    headers=_token(cat["actor_a"]))
    assert listado.status_code == 200, listado.text
    for fila in _filas(listado):
        assert "sap_config" not in fila, f"viajó sap_config: {fila}"
    assert MARCA_SAP not in listado.text, "viajó el contenido de la configuración SAP"
    detalle = await http_client.get(f"/api/v1/masters/companies/{cat['a']}",
                                    headers=_token(cat["actor_a"]))
    assert detalle.status_code == 200, detalle.text
    assert "sap_config" not in detalle.json()
    assert MARCA_SAP not in detalle.text


async def test_t4_ac16_el_catalogo_expone_exactamente_los_campos_aprobados(http_client, cat):
    """`AC16`. Igualdad de conjuntos: un campo de más es fuga; uno de menos, regresión."""
    listado = await http_client.get("/api/v1/masters/companies?limit=100",
                                    headers=_token(cat["actor_a"]))
    assert listado.status_code == 200, listado.text
    for fila in _filas(listado):
        assert set(fila) == CAMPOS_APROBADOS, set(fila) ^ CAMPOS_APROBADOS
    detalle = await http_client.get(f"/api/v1/masters/companies/{cat['a']}",
                                    headers=_token(cat["actor_a"]))
    assert set(detalle.json()) == CAMPOS_APROBADOS, set(detalle.json()) ^ CAMPOS_APROBADOS


async def test_t8_ac22_sin_campos_internos_del_orm(http_client, cat):
    """`AC22`. La proyección es explícita: nada del ORM se cuela."""
    r = await http_client.get(f"/api/v1/masters/companies/{cat['a']}",
                              headers=_token(cat["actor_a"]))
    assert r.status_code == 200, r.text
    claves = set(r.json())
    assert not any(k.startswith("_") for k in claves), claves
    assert "sap_config" not in claves


async def test_t9_ac23_los_campos_del_selector_de_la_fase_9_estan_presentes(http_client, cat):
    """`AC23`. `company.store.ts` necesita `id`, `name`, `is_active`."""
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(cat["actor_a"]))
    assert r.status_code == 200, r.text
    for fila in _filas(r):
        assert CAMPOS_DEL_SELECTOR <= set(fila)
        assert isinstance(fila["id"], int)
        assert isinstance(fila["name"], str) and fila["name"]
        assert isinstance(fila["is_active"], bool)


# ═══════════════════════════════════════════════════════════════════════════
#  Inquilino y autoridad global — la enmienda no debe moverlos
# ═══════════════════════════════════════════════════════════════════════════

async def test_t5_ac17_el_actor_de_empresa_solo_ve_la_suya(http_client, cat):
    """`AC17` · `R-115` sigue vigente con la proyección nueva."""
    ra = await http_client.get("/api/v1/masters/companies?limit=100",
                               headers=_token(cat["actor_a"]))
    rb = await http_client.get("/api/v1/masters/companies?limit=100",
                               headers=_token(cat["actor_b"]))
    assert ra.status_code == 200 and rb.status_code == 200, (ra.text, rb.text)
    assert {c["id"] for c in _filas(ra)} == {cat["a"]}
    assert {c["id"] for c in _filas(rb)} == {cat["b"]}
    assert MARCA_B not in ra.text and MARCA_A not in rb.text


async def test_t6_ac18_la_autoridad_global_ve_todas_sin_contexto(http_client, cat):
    """`AC18` · `OD-14.c`: el catálogo de empresas es `CONTROL_GLOBAL`. Incluye a la
    empresa con `sap_config` poblado: antes, ella sola rompía el catálogo para todos."""
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(cat["super"]))
    assert r.status_code == 200, r.text
    ids = {c["id"] for c in _filas(r)}
    assert {cat["a"], cat["b"]} <= ids
    assert "sap_config" not in r.text and MARCA_SAP not in r.text


async def test_t7_ac19_el_contexto_seleccionado_no_estrecha_el_catalogo_global(
        http_client, cat):
    """`AC19` · `OD-14.b`: `switch-company` elige inquilino, no retira autoridad."""
    r = await http_client.get("/api/v1/masters/companies?limit=100",
                              headers=_token(cat["super"], company_id=cat["b"]))
    assert r.status_code == 200, r.text
    ids = {c["id"] for c in _filas(r)}
    assert {cat["a"], cat["b"]} <= ids, "el contexto estrechó el catálogo global"


# ═══════════════════════════════════════════════════════════════════════════
#  Sin migración, sin SAP
# ═══════════════════════════════════════════════════════════════════════════

def test_t10_ac20_ac21_sin_migracion_y_sin_conector():
    """`AC20`, `AC21`. La cadena Alembic conserva su cabeza única, la columna sigue siendo
    `String` y no aparece ningún adaptador real."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import String

    from app.config import settings
    from app.masters.models import Company

    raiz = pathlib.Path(__file__).resolve().parents[1]
    cabezas = ScriptDirectory.from_config(Config(str(raiz / "alembic.ini"))).get_heads()
    assert cabezas == ["t0u1v2w3x4y5"], cabezas  # `GA-REM-041 §5`
    assert isinstance(Company.__table__.c.sap_config.type, String)
    assert settings.SAP_ADAPTER in ("manual", "mock")
