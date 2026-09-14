"""`R-194` · RED (cadena) + controles backend (verdes en HEAD) — la **cadena real de incubadora**.

Demuestra que el servidor soporta la cadena completa con estados y persistencia
(`P-05`): recepción de fértiles ⇒ saldo BR-03 ⇒ carga ⇒ nacimiento ⇒ despacho ⇒ `ChickBatch`,
con las reglas intactas (BR-03/BR-04/BR-08/BR-21).

**Hallazgo adicional (C1, real)**: la recepción canónica con almacenamiento (`arrival_date` +
`eggs_received`) devuelve **500** — `egg_storage` se inserta con `lot_id=NULL`: el
`setdefault("lot_id", data.lot_id)` no opera porque el schema emite `lot_id: None`
explícito. El test `test_r194_01` es **RED legítimo en HEAD** hasta el C2 (fix de servicio,
sin migración; `AC-R194-09`). Los demás tests son controles verdes.
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

PREFIJO = "R194-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


def _es_br(r, regla: str) -> bool:
    return r.status_code == 400 and r.json().get("rule") == regla


@pytest_asyncio.fixture
async def esc(test_database_url):
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

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        fila = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades["hatchery"].id,
                                   is_enabled=True)
        s.add(fila)
        await s.flush()

        rol = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        for accion in (PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE):
            s.add(Permission(role_id=rol.id, module="operations", action=accion,
                             scope_type="company"))
        s.add(Permission(role_id=rol.id, module="lots", action=PermissionAction.READ,
                         scope_type="company"))
        await s.flush()

        operador = User(first_name="OP", last_name="R194",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}OP-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=a.id,
                        role_id=rol.id, is_active=True)
        s.add(operador)
        await s.flush()
        await conceder_unidad(s, user=operador, company_business_unit=fila)

        planta = Farm(company_id=a.id, name=f"{PREFIJO}PLANTA",
                      code=f"{PREFIJO}P-{uuid.uuid4().hex[:4]}",
                      farm_type=FarmType.BREEDING, is_active=True)
        destino = Farm(company_id=a.id, name=f"{PREFIJO}DESTINO",
                       code=f"{PREFIJO}D-{uuid.uuid4().hex[:4]}",
                       farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([planta, destino])
        await s.flush()
        galpon_p = House(farm_id=planta.id, name=f"{PREFIJO}GP", capacity=100_000, is_active=True)
        galpon_d = House(farm_id=destino.id, name=f"{PREFIJO}GD", capacity=100_000, is_active=True)
        s.add_all([galpon_p, galpon_d])
        await s.flush()

        def _lote(marca: str) -> Lot:
            return Lot(company_id=a.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=BirdTypeEnum.HATCHERY, status=LotStatus.ACTIVE,
                       farm_id=planta.id, house_id=galpon_p.id)

        lh, lh2 = _lote("LH"), _lote("LH2")
        s.add_all([lh, lh2])
        await s.commit()

        datos = {"a": a.id, "operador": operador.id, "planta": planta.id,
                 "galpon_p": galpon_p.id, "destino": destino.id,
                 "galpon_d": galpon_d.id, "lh": lh.id, "lh2": lh2.id,
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
            "DELETE FROM hatchery_params WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_storage WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM chick_batches WHERE hatchery_lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p) "
            "OR destination_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM egg_batches WHERE hatchery_lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p)",
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


def _cuerpo(esc, lote: str, tipo: str, n: int, **extra) -> dict:
    cuerpo = {"lot_id": esc[lote], "event_type": tipo,
              "event_date": recent_event_date(),
              "farm_id": esc["planta"], "house_id": esc["galpon_p"]}
    if tipo == "egg_reception_hatchery":
        cuerpo["egg_storage_records"] = [{"eggs_received": n,
                                          "arrival_date": recent_event_date()}]
        cuerpo["egg_movements"] = [{"egg_type": "fertile", "quantity": n}]
    elif tipo == "incubation_load":
        cuerpo["hatchery_params"] = [{"quantity_loaded": n}]
    elif tipo == "birth_registration":
        cuerpo["bird_movements"] = [{"sex": "mixed", "quantity": n}]
        cuerpo["chicks_healthy"] = n
        cuerpo["chicks_weak"] = 0
    elif tipo == "chick_dispatch":
        cuerpo["bird_movements"] = [{"sex": "mixed", "quantity": n}]
        cuerpo["destination_farm_id"] = esc["destino"]
    cuerpo.update(extra)
    return cuerpo


async def _op(http_client, esc, lote: str, tipo: str, n: int, **extra):
    return await http_client.post("/api/v1/operations",
                                  headers=_token(esc["operador"]),
                                  json=_cuerpo(esc, lote, tipo, n, **extra))


async def _cuenta(esc, sql: str, **params) -> int:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return int((await s.execute(text(sql), params)).scalar() or 0)
    finally:
        await motor.dispose()


async def test_r194_01_cadena_persistente_recepcion_carga_nacimiento_despacho(http_client, esc):
    """La cadena completa del proceso P-05 en secuencia, con saldos y persistencia."""
    r = await _op(http_client, esc, "lh", "egg_reception_hatchery", 1000)
    assert r.status_code == 201, ("recepción", r.text)
    fertiles = await _cuenta(esc, "SELECT COALESCE(sum(quantity),0) FROM egg_movements em "
                                  "JOIN operational_events oe ON oe.id = em.event_id "
                                  "WHERE oe.lot_id = :l AND em.egg_type = 'fertile'",
                             l=esc["lh"])
    assert fertiles == 1000, "el saldo fértil persiste tras la recepción"

    r = await _op(http_client, esc, "lh", "incubation_load", 500)
    assert r.status_code == 201, ("carga 500", r.text)
    cargados = await _cuenta(esc, "SELECT COALESCE(sum(quantity_loaded),0) FROM hatchery_params hp "
                                  "JOIN operational_events oe ON oe.id = hp.event_id "
                                  "WHERE oe.lot_id = :l", l=esc["lh"])
    assert cargados == 500

    r = await _op(http_client, esc, "lh", "incubation_load", 501)
    assert _es_br(r, "BR-03"), ("carga sobre saldo", r.text)

    r = await _op(http_client, esc, "lh", "birth_registration", 300)
    assert r.status_code == 201, ("nacimiento", r.text)

    r = await _op(http_client, esc, "lh", "chick_dispatch", 100)
    assert r.status_code == 201, ("despacho", r.text)
    r = await _op(http_client, esc, "lh", "chick_dispatch", 10000)
    assert _es_br(r, "BR-04"), ("despacho sobre viables", r.text)

    pollitos = await _cuenta(esc, "SELECT count(*) FROM chick_batches "
                                  "WHERE hatchery_lot_id = :l", l=esc["lh"])
    assert pollitos >= 1, "el despacho deja vínculo persistente (ChickBatch)"

    tr = await http_client.get(f"/api/v1/lots/{esc['lh']}/traceability",
                               headers=_token(esc["operador"]))
    assert tr.status_code == 200, tr.text
    nodo = tr.json()
    assert set(nodo.keys()) >= {"egg_batches_sent", "chick_batches_sent"}, nodo.keys()


async def test_r194_02_recepcion_sin_ubicacion_es_400_br08(http_client, esc):
    cuerpo = _cuerpo(esc, "lh2", "egg_reception_hatchery", 100)
    cuerpo.pop("farm_id")
    cuerpo.pop("house_id")
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]),
                               json=cuerpo)
    assert _es_br(r, "BR-08"), r.text


async def test_r194_03_carga_sobre_saldo_cero_es_400_br03(http_client, esc):
    r = await _op(http_client, esc, "lh2", "incubation_load", 10)
    assert _es_br(r, "BR-03"), r.text


async def test_r194_04_despacho_sobre_viables_es_400_br04(http_client, esc):
    assert (await _op(http_client, esc, "lh2", "birth_registration", 10)).status_code == 201
    r = await _op(http_client, esc, "lh2", "chick_dispatch", 20)
    assert _es_br(r, "BR-04"), r.text


async def test_r194_05_nacimiento_con_sanos_y_debiles_es_201(http_client, esc):
    r = await _op(http_client, esc, "lh", "birth_registration", 50,
                  chicks_healthy=40, chicks_weak=10)
    assert r.status_code == 201, r.text
