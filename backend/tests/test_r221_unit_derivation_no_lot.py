"""`R-221` · eventos sin lote de tipos **inequívocos** derivan su unidad.

    LO QUE NO TIENE CADENA INEQUÍVOCA NO SE ADIVINA;
    LO QUE SÍ LA TIENE NO SE DEJA SIN ATRIBUIR.

`LOT_OPTIONAL_EVENTS` (granja e incubadora) nacían con `business_unit_id = null`
 y la guarda
de escritura degradaba a «alguna unidad»: una inspección de incubadora se
 registraba con la
unidad **apagada** (autoridad global) o sin concesión (actor de empresa) — caso
 runtime
`OD16b-global-actor-bu-off-api` (201 con `hatchery` OFF). La importación de
 abuelas ya derivó
su unidad como regla (`R-153` · `OD-25 (B)`); aquí se extiende la regla al tipo
 inequívoco
restante.

Contrato:
  AC-R221-01  global situada · hatchery OFF · `hatchery_inspection` sin lote ⇒
 denegado · 0 filas
  AC-R221-02  actor solo `broiler` ⇒ denegado · 0 filas
  AC-R221-03  con `hatchery` concedida/ON ⇒ 201 y el evento **nace clasificado**
 (`business_unit_id` = habilitación de hatchery)
  AC-R221-04  `farm_inspection` sin lote: **C-02 pendiente de decisión del
 propietario** —
              este test fija el statu quo para detectar cualquier cambio
 accidental
  AC-R221-05  (control) evento **con lote** intacto: la unidad se deriva del
 lote
  AC-R221-05b (control) importación de abuelas: su flujo R-153 se regresiona en
 `test_grandparent_import.py` + `test_r153_import_lot_auto.py` (misma tranche)

RED esperado en HEAD: 01/02/03 rojos (201/201/null), 04/05 verdes.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "BUR221-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    """Empresa A · breeder/hatchery/broiler habilitadas · actores del contrato."""
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House,
                                    Lot, LotStatus)

    motor = create_async_engine(test_database_url)
    datos: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(
            select(BusinessUnit))).scalars()}
        assert {"breeder", "hatchery", "broiler"} <= set(unidades)

        hab = {}
        for code in ("breeder", "hatchery", "broiler"):
            fila = CompanyBusinessUnit(company_id=a.id,
                                       business_unit_id=unidades[code].id,
                                       is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[code] = fila

        rol_ops = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id,
                       is_active=True)
        rol_global = Role(name=f"{PREFIJO}Gl-{uuid.uuid4().hex[:6]}", company_id=None,
                          is_active=True)
        s.add_all([rol_ops, rol_global])
        await s.flush()
        for accion in (PermissionAction.READ, PermissionAction.CREATE):
            s.add(Permission(role_id=rol_ops.id, module="operations", action=accion,
                             scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion,
                             scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="R221",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        global_, mix, broiler = (_usuario(None, "GLOBAL", rol_global),
                                 _usuario(a.id, "MIX", rol_ops),
                                 _usuario(a.id, "BROILER", rol_ops))
        s.add_all([global_, mix, broiler])
        await s.flush()
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=mix, company_business_unit=hab[code])
        await conceder_unidad(s, user=broiler, company_business_unit=hab["broiler"])

        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA",
                      code=f"{PREFIJO}G-{uuid.uuid4().hex[:4]}",
                      farm_type=FarmType.BREEDING, is_active=True)
        s.add(granja)
        await s.flush()
        galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON",
                       capacity=10_000, is_active=True)
        s.add(galpon)
        await s.flush()
        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}L-{uuid.uuid4().hex[:6]}",
                   bird_type=BirdTypeEnum.BREEDER, status=LotStatus.ACTIVE,
                   farm_id=None)
        s.add(lote)
        await s.flush()
        await s.commit()

        datos = {"a": a.id, "hab_hatchery": hab["hatchery"].id,
                 "global": global_.id, "mix": mix.id, "broiler": broiler.id,
                 "granja": granja.id, "galpon": galpon.id, "lote": lote.id,
                 "url": test_database_url}
    yield datos

    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM operational_alerts WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM evidences WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM hatchery_params WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM inspection_details WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN "
            "(SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN "
            "(SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


def _inspeccion_incubadora() -> dict:
    return {"event_type": "hatchery_inspection",
            "event_date": recent_event_date(),
            "hatchery_params": [{"temperature": 37}]}


async def _crear(http_client, esc, actor, cuerpo, company_id=None):
    return await http_client.post("/api/v1/operations",
                                  headers=_token(esc[actor], company_id), json=cuerpo)


async def _cuenta(esc, sql: str, **params) -> int:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return int((await s.execute(text(sql), params)).scalar() or 0)
    finally:
        await motor.dispose()


async def _filas_inspeccion(esc) -> int:
    return await _cuenta(
        esc, "SELECT count(*) FROM operational_events WHERE company_id = :c "
             "AND event_type = 'HATCHERY_INSPECTION'", c=esc["a"])


async def _unidad_del_evento(esc, evento: int):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(
                "SELECT business_unit_id FROM operational_events WHERE id = :e"),
                {"e": evento})).scalar()
    finally:
        await motor.dispose()


async def _apagar_hatchery(esc, *, apagada: bool) -> None:
    motor = create_async_engine(esc["url"])
    try:
        async with motor.begin() as c:
            await c.execute(text(
                "UPDATE company_business_units SET is_enabled = :v WHERE id = :h"),
                {"v": not apagada, "h": esc["hab_hatchery"]})
    finally:
        await motor.dispose()


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R221-01 · autoridad global situada · hatchery apagada ⇒ denegado
# ═══════════════════════════════════════════════════════════════════════════

async def test_r221_01_hatchery_off_deniega_inspeccion(http_client, esc):
    """`OD-16.e`: apagado = inaccesible también para la autoridad global.

    HEAD: 201 (caso runtime `OD16b-global-actor-bu-off-api`) — la guarda acepta
    «alguna unidad habilitada» porque el tipo no declara la suya.
    """
    await _apagar_hatchery(esc, apagada=True)
    antes = await _filas_inspeccion(esc)
    try:
        r = await _crear(http_client, esc, "global", _inspeccion_incubadora(),
                         company_id=esc["a"])
        despues = await _filas_inspeccion(esc)
    finally:
        await _apagar_hatchery(esc, apagada=False)
    assert 400 <= r.status_code < 500, f"HEAD: {r.status_code} {r.text}"
    assert despues == antes, "una denegación no deja ni una fila (`AC-R221-01`)"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R221-02 · actor de empresa sin concesión hatchery ⇒ denegado
# ═══════════════════════════════════════════════════════════════════════════

async def test_r221_02_sin_concesion_deniega(http_client, esc):
    """`OD-09`: la concesión por unidad vale también para el dato sin lote.

    HEAD: 201 — `efectivas ≠ ∅` (tiene `broiler`) y el tipo no exige `hatchery`.
    """
    antes = await _filas_inspeccion(esc)
    r = await _crear(http_client, esc, "broiler", _inspeccion_incubadora())
    despues = await _filas_inspeccion(esc)
    assert 400 <= r.status_code < 500, f"HEAD: {r.status_code} {r.text}"
    assert despues == antes, "denegado sin concesión ⇒ 0 filas (`AC-R221-02`)"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R221-03 · con hatchery ⇒ 201 y el evento nace clasificado
# ═══════════════════════════════════════════════════════════════════════════

async def test_r221_03_con_unidad_nace_clasificado(http_client, esc):
    """El tipo inequívoco deja de ir a la bandeja de pendientes.

    HEAD: 201 pero `business_unit_id` = NULL ⇒ pendiente de clasificar.
    """
    r = await _crear(http_client, esc, "mix", _inspeccion_incubadora())
    assert r.status_code == 201, r.text
    evento = r.json()["id"]
    unidad = await _unidad_del_evento(esc, evento)
    assert unidad == esc["hab_hatchery"], (
        f"AC-R221-03: el evento debe nacer atribuido a la habilitación de hatchery "
        f"({esc['hab_hatchery']}), HEAD: {unidad}")


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R221-04 · farm_inspection sin lote — C-02 PENDIENTE · statu quo fijado
# ═══════════════════════════════════════════════════════════════════════════

async def test_r221_04_farm_inspection_statu_quo_documentado(http_client, esc):
    """**C-02 `OWNER_DECISION_REQUIRED`**: qué unidad tiene `farm_inspection` sin lote.

    Mientras no haya decisión (`AOD-13` en la cola del propietario) la regla es
    statu quo: 201 con unidad `null` (bandeja de pendientes operativa). Este test
    fija ese comportamiento para que la decisión futura **cambie el test a
    propósito**, no por accidente.
    """
    cuerpo = {"event_type": "farm_inspection", "event_date": recent_event_date(),
              "farm_id": esc["granja"], "house_id": esc["galpon"],
              "observations": f"{PREFIJO}SIN-LOTE"}
    r = await _crear(http_client, esc, "mix", cuerpo)
    assert r.status_code == 201, r.text
    assert await _unidad_del_evento(esc, r.json()["id"]) is None, (
        "AC-R221-04: statu quo C-02 — pendiente de clasificación")


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R221-05 · control: evento con lote ⇒ la unidad se deriva del lote
# ═══════════════════════════════════════════════════════════════════════════

async def test_r221_05_control_evento_con_lote_intacto(http_client, esc):
    """Camino intacto (`GA-REM-040-G`): con lote, la unidad se deriva del lote."""
    cuerpo = {"event_type": "weight_recording", "event_date": recent_event_date(),
              "lot_id": esc["lote"], "farm_id": esc["granja"],
              "house_id": esc["galpon"], "sample_size": 10,
              "bird_movements": [{"sex": "male", "quantity": 5, "avg_weight": 45},
                                 {"sex": "female", "quantity": 5, "avg_weight": 43}]}
    r = await _crear(http_client, esc, "mix", cuerpo)
    assert r.status_code == 201, r.text
