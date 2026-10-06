"""Escenario compartido de las pruebas de SPEC 005 (SAP HANA Cloud READ ONLY inbound).

Dos empresas GA, cada una enlazada a una sociedad SAP distinta del mismo mandante:

    empresa A  ←  BUKRS 1000 · centro 1100 mapeado · centro 1200 SIN mapear
    empresa B  ←  BUKRS 2000 · centro 2100 mapeado

El mandante es aleatorio por prueba: el mapping es único por (sistema, mandante, tipo, clave)
y así ninguna prueba hereda el de otra. Los números de documento llevan una serie aleatoria
por la misma razón.

Ninguna prueba toca SAP: el driver es `FakeHana`.
"""
from __future__ import annotations

import random
import uuid

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.integrations.sap.inbound.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.integrations.sap.inbound.adapter import HanaCloudReadOnlyAdapter
from app.integrations.sap.inbound.client import SapHanaReadOnlyClient
from app.integrations.sap.inbound.fake_hana import FakeHana, default_dataset
from app.integrations.sap.inbound.models import SOURCE_SYSTEM, SapEntityMapping
from app.integrations.sap.inbound.service import SapInboundService
from app.integrations.sap.inbound.settings import HanaSettings

PREFIJO = "HANA5-"
SECRETO = "s3cr3t-P4ss!-no-debe-salir"


def cfg_de_prueba(client: str, **cambios) -> HanaSettings:
    base = dict(host="hana.invalid", port=443, user="GA_RO_TEST", password=SECRETO,
                schema="SAPFAKE", client=client, environment="test", page_size=200,
                max_rows=5000, lookback_days=30)
    base.update(cambios)
    return HanaSettings(**base)


def adaptador_de_prueba(fake: FakeHana, cfg: HanaSettings) -> HanaCloudReadOnlyAdapter:
    return HanaCloudReadOnlyAdapter(
        cfg, client=SapHanaReadOnlyClient(cfg, connect_factory=fake.connect))


def _mandante() -> str:
    return "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(3))


def _serie() -> str:
    return f"{random.randint(0, 9999):04d}"


async def mapear(sesion, *, client, company_id, entity_type, sap_key, parent=None):
    sesion.add(SapEntityMapping(
        source_system=SOURCE_SYSTEM, client=client, entity_type=entity_type,
        sap_key=sap_key, parent_sap_key=parent, company_id=company_id, is_active=True))
    await sesion.flush()


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.masters.models import Company

    client = _mandante()
    serie = _serie()
    motor = create_async_engine(test_database_url)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)

    async with fabrica() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        def _rol(nombre, company_id, permisos, alcance="company"):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos, alcance

        roles = {
            "analista_a": _rol("AnalistaA", a.id, [("sap", PermissionAction.READ),
                                                  ("sap", PermissionAction.SEND_SAP)]),
            "lector_a": _rol("LectorA", a.id, [("sap", PermissionAction.READ)]),
            "ajeno_a": _rol("AjenoA", a.id, [("lots", PermissionAction.READ)]),
            "analista_b": _rol("AnalistaB", b.id, [("sap", PermissionAction.READ),
                                                  ("sap", PermissionAction.SEND_SAP)]),
            "global": _rol("Global", None, [("*", accion) for accion in PermissionAction], "all"),
        }
        await s.flush()
        for rol, permisos, alcance in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion,
                                 scope_type=alcance))

        def _usuario(marca, company_id, rol):
            u = User(first_name=marca[:8], last_name="HANA5",
                     email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                     username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                     hashed_password=hash_password("x"), company_id=company_id,
                     role_id=rol.id, is_active=True)
            s.add(u)
            return u

        usuarios = {
            "analista_a": _usuario("ANA", a.id, roles["analista_a"][0]),
            "lector_a": _usuario("LEC", a.id, roles["lector_a"][0]),
            "ajeno_a": _usuario("AJE", a.id, roles["ajeno_a"][0]),
            "analista_b": _usuario("ANB", b.id, roles["analista_b"][0]),
            "global": _usuario("GLO", None, roles["global"][0]),
        }
        await s.flush()

        await mapear(s, client=client, company_id=a.id, entity_type="COMPANY_CODE", sap_key="1000")
        await mapear(s, client=client, company_id=a.id, entity_type="PLANT", sap_key="1100",
                     parent="1000")
        await mapear(s, client=client, company_id=b.id, entity_type="COMPANY_CODE", sap_key="2000")
        await mapear(s, client=client, company_id=b.id, entity_type="PLANT", sap_key="2100",
                     parent="2000")
        await s.commit()

        d = {
            "url": test_database_url, "fabrica": fabrica, "client": client, "serie": serie,
            "a": a.id, "b": b.id,
            "ids": {k: u.id for k, u in usuarios.items()},
            "actor_a": {"id": usuarios["analista_a"].id, "company_id": a.id,
                        "is_super_admin": False},
            "actor_b": {"id": usuarios["analista_b"].id, "company_id": b.id,
                        "is_super_admin": False},
            "actor_global_sin_contexto": {"id": usuarios["global"].id, "company_id": None,
                                          "is_super_admin": True},
            "cfg": cfg_de_prueba(client),
            "oc": f"45{serie}0001", "oc_alimento": f"45{serie}0002", "oc_b": f"45{serie}0901",
            "sto": f"49{serie}0001",
        }
    d["datos"] = default_dataset(client=client, serie=serie)
    yield d

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        empresas = "(SELECT id FROM companies WHERE name LIKE :p)"
        for sql in (
            f"DELETE FROM sap_inbound_records WHERE company_id IN {empresas}",
            f"DELETE FROM sap_inbound_watermarks WHERE company_id IN {empresas}",
            f"DELETE FROM sap_inbound_sync_jobs WHERE company_id IN {empresas}",
            f"DELETE FROM sap_entity_mappings WHERE company_id IN {empresas}",
            f"DELETE FROM sap_references WHERE company_id IN {empresas}",
            f"DELETE FROM audit_logs WHERE company_id IN {empresas}",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def sincronizar(esc, actor="actor_a", objetos=None, *, fake=None, cfg=None, **kw):
    """Ejecuta un sync a nivel de servicio y confirma, como haría la ruta."""
    fake = fake if fake is not None else FakeHana(esc["datos"])
    cfg = cfg or esc["cfg"]
    async with esc["fabrica"]() as s:
        servicio = SapInboundService(s, esc[actor], adapter=adaptador_de_prueba(fake, cfg),
                                     cfg=cfg)
        jobs = await servicio.sync(objetos, **kw)
        await s.commit()
    return jobs, fake


async def filas(esc, sql, **params):
    async with esc["fabrica"]() as s:
        return [dict(f._mapping) for f in (await s.execute(text(sql), params)).all()]


async def escalar(esc, sql, **params):
    async with esc["fabrica"]() as s:
        return (await s.execute(text(sql), params)).scalar()


async def registros(esc, objeto, empresa="a", solo_vigentes=True):
    extra = " AND is_current" if solo_vigentes else ""
    return await filas(
        esc,
        "SELECT * FROM sap_inbound_records WHERE company_id = :c AND object_type = :o"
        f"{extra} ORDER BY source_key, version",
        c=esc[empresa], o=objeto)


async def referencias(esc, tipo, empresa="a"):
    return await filas(
        esc,
        "SELECT * FROM sap_references WHERE company_id = :c AND ref_type::text = :t "
        "ORDER BY sap_code",
        c=esc[empresa], t=tipo)
