"""`R-191` · RED/control — transición de fase del lote por la UI (`lot_phases`).

Escenario `esc`: empresa con `breeder` ON; operador (`operations:*`, `lots:read/create`,
`masters:read`); granja y galpón; lote `breeder` activo con fase `CRIA` activa; recepción
aprobada 40♂/60♀ y mortalidad aprobada 5♂ ⇒ saldo 35♂/60♀.

Contrato objetivo (`R-191`): `POST /lots/{id}/phases {lot_id, phase_id, start_date}` —
cierra la fase activa (`end_date = start_date`), deriva poblaciones del saldo por sexo si
faltan, devuelve la fase con su `phase` (código incluido) y rechaza transiciones inválidas
(lote no activo, fase ya activa, fecha anterior al inicio) sin fila. La concurrencia deja
**una sola** fase activa (sin migración: bloqueo por fila).

RED esperado en HEAD: 01/02/03/04a/04b/04c/06 rojos; 05/07 controles verdes.
"""
from __future__ import annotations

import asyncio
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
from tests.time_reference import days_ago, recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "R191-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.lots.models import LotPhase
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House,
                                    Lot, LotStatus, ProductivePhase)
    from app.operations.models import (BirdMovement, EventStatus, EventType,
                                       OperationalEvent)

    motor = create_async_engine(test_database_url)
    datos: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        fila = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades["breeder"].id,
                                   is_enabled=True)
        s.add(fila)
        await s.flush()

        rol = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        for modulo, acciones in (("operations", (PermissionAction.CREATE, PermissionAction.READ,
                                                 PermissionAction.UPDATE)),
                                 ("lots", (PermissionAction.READ, PermissionAction.CREATE)),
                                 ("masters", (PermissionAction.READ,))):
            for accion in acciones:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion,
                                 scope_type="company"))
        await s.flush()

        operador = User(first_name="OP", last_name="R191",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}OP-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=a.id,
                        role_id=rol.id, is_active=True)
        s.add(operador)
        await s.flush()
        await conceder_unidad(s, user=operador, company_business_unit=fila)

        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA",
                      code=f"{PREFIJO}G-{uuid.uuid4().hex[:4]}",
                      farm_type=FarmType.BREEDING, is_active=True)
        s.add(granja)
        await s.flush()
        galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON", capacity=5000,
                       is_active=True)
        s.add(galpon)
        await s.flush()

        def _fase_maestra(code: str, name: str, order: int) -> ProductivePhase:
            return ProductivePhase(name=name, code=code, order=order, duration_days=200)

        fases = {f.code: f for f in (await s.execute(select(ProductivePhase))).scalars()}
        for code, name, order in (("CRIA", "Cría", 1), ("PROD", "Producción", 2)):
            if code not in fases:
                fases[code] = _fase_maestra(code, name, order)
                s.add(fases[code])
        await s.flush()

        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}L-{uuid.uuid4().hex[:6]}",
                   bird_type=BirdTypeEnum.BREEDER, status=LotStatus.ACTIVE,
                   farm_id=granja.id, house_id=galpon.id)
        s.add(lote)
        await s.flush()
        s.add(LotPhase(lot_id=lote.id, phase_id=fases["CRIA"].id,
                       start_date=days_ago(30), is_active=True,
                       start_population_male=0, start_population_female=0))
        await s.flush()

        recepcion = OperationalEvent(company_id=a.id, lot_id=lote.id,
                                     event_type=EventType.BIRD_RECEPTION,
                                     event_date=days_ago(20), status=EventStatus.APPROVED,
                                     registered_by_id=operador.id)
        s.add(recepcion)
        await s.flush()
        s.add_all([
            BirdMovement(event_id=recepcion.id, sex="male", quantity=40),
            BirdMovement(event_id=recepcion.id, sex="female", quantity=60),
        ])
        mortalidad = OperationalEvent(company_id=a.id, lot_id=lote.id,
                                      event_type=EventType.MORTALITY_RECORDING,
                                      event_date=days_ago(5), status=EventStatus.APPROVED,
                                      registered_by_id=operador.id)
        s.add(mortalidad)
        await s.flush()
        s.add(BirdMovement(event_id=mortalidad.id, sex="male", quantity=5))
        await s.commit()

        datos = {"lote": lote.id, "cerrado": None, "operador": operador.id,
                 "cria": fases["CRIA"].id, "prod": fases["PROD"].id,
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
            "DELETE FROM bird_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lot_phases WHERE lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p)",
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


async def _post(http_client, esc, cuerpo):
    return await http_client.post(f"/api/v1/lots/{esc['lote']}/phases",
                                  headers=_token(esc["operador"]), json=cuerpo)


async def _activas(esc) -> list[dict]:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            filas = (await s.execute(text(
                "SELECT phase_id, is_active, end_date::text FROM lot_phases "
                "WHERE lot_id = :l ORDER BY id"), {"l": esc["lote"]})).all()
            return [dict(f._mapping) for f in filas]
    finally:
        await motor.dispose()


async def test_r191_01_add_phase_cierra_la_fase_anterior(http_client, esc):
    r = await _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                       "start_date": recent_event_date()})
    assert r.status_code == 201, r.text
    activas = await _activas(esc)
    assert sum(1 for f in activas if f["is_active"]) == 1, activas
    cria = next(f for f in activas if f["phase_id"] == esc["cria"])
    assert cria["is_active"] is False
    assert cria["end_date"] == recent_event_date()


async def test_r191_02_lectura_incluye_codigo_de_fase(http_client, esc):
    r = await _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                       "start_date": recent_event_date()})
    assert r.status_code == 201, r.text
    assert r.json()["phase"]["code"] == "PROD"
    g = await http_client.get(f"/api/v1/lots/{esc['lote']}/phases",
                              headers=_token(esc["operador"]))
    assert g.status_code == 200
    activa = next(f for f in g.json() if f["is_active"])
    assert activa["phase"]["code"] == "PROD"


async def test_r191_03_poblacion_por_sexo_derivada_del_saldo(http_client, esc):
    r = await _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                       "start_date": recent_event_date()})
    assert r.status_code == 201, r.text
    assert r.json()["start_population_male"] == 35, r.text
    assert r.json()["start_population_female"] == 60, r.text


async def test_r191_04a_lote_no_activo_es_400(http_client, esc):
    from app.masters.models import Lot, LotStatus

    motor = create_async_engine(esc["url"])
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == esc["lote"]))).scalar_one()
        lote.status = LotStatus.CLOSED
        await s.commit()
    await motor.dispose()

    antes = await _activas(esc)
    r = await _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                       "start_date": recent_event_date()})
    assert r.status_code == 400, r.text
    assert await _activas(esc) == antes


async def test_r191_04b_fase_ya_activa_es_400(http_client, esc):
    antes = await _activas(esc)
    r = await _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["cria"],
                                       "start_date": recent_event_date()})
    assert r.status_code == 400, r.text
    assert await _activas(esc) == antes


async def test_r191_04c_fecha_anterior_al_inicio_es_400(http_client, esc):
    antes = await _activas(esc)
    r = await _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                       "start_date": days_ago(40).isoformat()})
    assert r.status_code == 400, r.text
    assert await _activas(esc) == antes


async def test_r191_05_contrato_actual_phase_id_sigue_vigente(http_client, esc):
    r = await _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                       "start_date": recent_event_date(),
                                       "start_population_male": 40,
                                       "start_population_female": 60})
    assert r.status_code == 201, r.text
    assert r.json()["start_population_male"] == 40
    assert r.json()["start_population_female"] == 60


async def test_r191_06_dos_transiciones_concurrentes_una_sola_activa(http_client, esc):
    uno, dos = await asyncio.gather(
        _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                 "start_date": recent_event_date()}),
        _post(http_client, esc, {"lot_id": esc["lote"], "phase_id": esc["prod"],
                                 "start_date": recent_event_date()}),
    )
    codigos = sorted([uno.status_code, dos.status_code])
    assert codigos == [201, 400], f"{codigos}: {uno.text} | {dos.text}"
    activas = await _activas(esc)
    assert sum(1 for f in activas if f["is_active"]) == 1


async def test_r191_07_cuerpo_de_la_ui_actual_es_422(http_client, esc):
    r = await _post(http_client, esc, {"phase_code": "production",
                                       "start_date": recent_event_date(),
                                       "start_population_male": 0,
                                       "start_population_female": 0})
    assert r.status_code == 422, r.text
    locs = " ".join(str(p) for d in r.json()["detail"] for p in d.get("loc", []))
    assert "lot_id" in locs and "phase_id" in locs
