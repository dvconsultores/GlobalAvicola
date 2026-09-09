"""`GA-REM-041` enmienda A · `OD-19` Aclaración A · titulares sembrados de la capacidad de reverso.

La asignación es **gobierno de semillas**: se comprueba sobre los tres ficheros de semillas (estáticamente, como
`test_rbac` lee `dev_seeds`) y, en tiempo de ejecución, con un usuario que lleva el rol sembrado «Supervisor Avícola»
de `test_seeds`. Ningún control de autorización consulta nombres de rol.
"""
from __future__ import annotations

import pathlib
import re
import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

RAIZ = pathlib.Path(__file__).resolve().parents[1] / "seeds"
PREFIJO = "RRM-"


def _bloque(texto: str, nombre: str, formato: str) -> str:
    """El trozo del fichero que define ese rol: hasta el siguiente rol.

    `dev_seeds`/`integration_seeds` (`formato="dict"`) abren cada rol con `"name":`; `test_seeds`
    (`formato="tupla"`) usa el nombre como clave de un diccionario (`"Rol": [`). Se corta en el
    siguiente rol del mismo formato para no leer sus permisos como si fueran de éste.
    """
    inicio = texto.index(f'"{nombre}"')
    resto = texto[inicio + 1:]
    patron = r'"name"\s*:' if formato == "dict" else r'\n\s{12}"[^"]+": \['
    fin = re.search(patron, resto)
    return resto[: fin.start()] if fin else resto


def _permisos_dict(texto: str, nombre: str) -> set[tuple[str, str]]:
    b = _bloque(texto, nombre, "dict")
    return {(m, a.lower()) for m, a in re.findall(r'\{"module": "(\w+)", "action": PermissionAction\.(\w+)\}', b)}


def _permisos_tupla(texto: str, nombre: str) -> set[tuple[str, str]]:
    b = _bloque(texto, nombre, "tupla")
    return {(m, a.lower()) for m, a in re.findall(r'\("(\w+)", PermissionAction\.(\w+)\)', b)}


DEV = (RAIZ / "dev_seeds.py").read_text(encoding="utf-8")
TEST = (RAIZ / "test_seeds.py").read_text(encoding="utf-8")
INTEG = (RAIZ / "integration_seeds.py").read_text(encoding="utf-8")


def test_rev_r01_r02_el_supervisor_avicola_solicita_y_lee_reversos():
    for texto, extraer in ((DEV, _permisos_dict), (TEST, _permisos_tupla)):
        permisos = extraer(texto, "Supervisor Avícola")
        assert ("reversals", "create") in permisos and ("reversals", "read") in permisos, permisos


def test_rev_r03_r04_la_contraloria_lee_y_no_solicita():
    permisos = _permisos_dict(INTEG, "Contralor Avícola")
    assert ("reversals", "read") in permisos, permisos
    assert ("reversals", "create") not in permisos, permisos


def test_rev_r05_r06_acceso_y_operador_no_reciben_reverso():
    acceso = _permisos_dict(DEV, "Administrador de Accesos")
    assert not {p for p in acceso if p[0] == "reversals"}, acceso
    assert acceso == {("business_units", a) for a in ("read", "update", "create", "delete")}, "OD-15 §6: exactamente cuatro"
    operador = _permisos_dict(DEV, "Operador de Granja")
    assert not {p for p in operador if p[0] == "reversals"}, operador


def test_rev_r07_nadie_gana_comodin_ni_autoridad_ajena():
    for texto, extraer in ((DEV, _permisos_dict), (TEST, _permisos_tupla)):
        permisos = extraer(texto, "Supervisor Avícola")
        assert not {p for p in permisos if p[0] in ("*", "users", "business_units", "approvals") and p[1] != "read"}, permisos
        assert ("approvals", "approve") not in permisos and ("approvals", "reject") not in permisos
    assert 'scope_type="all"' not in _bloque(DEV, "Supervisor Avícola", "dict")


@pytest_asyncio.fixture
async def esc(test_database_url, seeded_ids):
    """Un usuario con el rol sembrado «Supervisor Avícola» (test_seeds) y un evento aprobado de su empresa."""
    from app.auth.models import Role, User
    from app.auth.security import hash_password
    from app.business_units.service import conceder_unidad
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.masters.models import BirdTypeEnum, Lot, LotStatus
    from app.operations.models import EventStatus, EventType, OperationalEvent

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        rol = (await s.execute(select(Role).where(Role.name == "Supervisor Avícola"))).scalars().first()
        assert rol is not None, "test_seeds siembra «Supervisor Avícola»"
        empresa = seeded_ids["company_id"]
        u = User(first_name="Sup", last_name="Rrm", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                 username=f"{PREFIJO}SUP-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                 company_id=empresa, role_id=rol.id, is_active=True)
        s.add(u)
        await s.flush()
        hab = (await s.execute(select(CompanyBusinessUnit).join(BusinessUnit).where(
            CompanyBusinessUnit.company_id == empresa, BusinessUnit.code == "breeder"))).scalars().first()
        await conceder_unidad(s, user=u, company_business_unit=hab)
        lote = Lot(company_id=empresa, lot_code=f"{PREFIJO}LR-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER, status=LotStatus.ACTIVE)
        s.add(lote)
        await s.flush()
        ev = OperationalEvent(company_id=empresa, lot_id=lote.id, event_type=EventType.FARM_INSPECTION, event_date=date.today(),
                              status=EventStatus.APPROVED, registered_by_id=seeded_ids["user_operator_id"], version=1, observations=f"{PREFIJO}aprobado")
        s.add(ev)
        await s.flush()
        await s.commit()
        d = {"sup": u.id, "ev": ev.id, "url": test_database_url}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE entity_type = 'reversal' AND entity_id IN (SELECT id::text FROM reversals WHERE original_event_id IN (SELECT id FROM operational_events WHERE observations LIKE :p))",
            "DELETE FROM reversals WHERE original_event_id IN (SELECT id FROM operational_events WHERE observations LIKE :p)",
            "DELETE FROM operational_events WHERE observations LIKE 'Reverso de #%' AND lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM operational_events WHERE observations LIKE :p",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM users WHERE username LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def test_rev_r08_en_ejecucion_el_supervisor_solicita_y_no_aprueba(http_client, esc):
    cab = {"Authorization": f"Bearer {create_access_token(data={'sub': str(esc['sup'])})}"}
    r = await http_client.post("/api/v1/reversals", headers=cab, json={"event_id": esc["ev"], "reason": f"{PREFIJO}registro duplicado por error"})
    assert r.status_code == 201, r.text
    contrapartida = r.json()["reversal_event_id"]
    r = await http_client.post("/api/v1/approvals/approve", headers=cab, json={"event_id": contrapartida})
    assert r.status_code == 403, "sin approvals:approve: el solicitante no aprueba"
    r = await http_client.get("/api/v1/reversals", headers=cab)
    assert r.status_code == 200 and r.json()["total"] >= 1
