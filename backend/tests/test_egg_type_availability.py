"""`GA-REM-005` enmienda F · `R-172` · solo el huevo fértil cuenta como disponible en `BR-02` y `BR-03` (`AC-R172-01…07`).

Escenario (prefijo `TIPO-`): empresa A (breeder ON · hatchery ON) · operador con ambas unidades · lotes lr, lr2, lr3 (breeder) ·
lt_<tipo> uno por tipo no disponible (breeder) · lh (hatchery). `CAPTURADO ≠ DISPONIBLE`: las filas se persisten y no cuentan.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "TIPO-"
NO_DISPONIBLES = ("dirty", "broken", "infertile", "discarded", "commercial")


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
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for code in ("breeder", "hatchery"):
            fila = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades[code].id, is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[code] = fila
        PA = PermissionAction
        rol = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        for modulo, accion in (("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)):
            s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        operador = User(first_name="OP", last_name="Tipo", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}OP-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=a.id, role_id=rol.id, is_active=True)
        s.add(operador)
        await s.flush()
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=operador, company_business_unit=hab[code])
        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA", code=f"{PREFIJO}G-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        planta = Farm(company_id=a.id, name=f"{PREFIJO}PLANTA", code=f"{PREFIJO}P-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja, planta])
        await s.flush()
        galpones = {f: House(farm_id=f.id, name=f"{PREFIJO}G-{f.code}", capacity=100_000, is_active=True) for f in (granja, planta)}
        s.add_all(galpones.values())
        await s.flush()

        def _lote(marca, tipo, f):
            return Lot(company_id=a.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE,
                       farm_id=f.id, house_id=galpones[f].id)

        lotes = {"lr": _lote("LR", BirdTypeEnum.BREEDER, granja), "lr2": _lote("LR2", BirdTypeEnum.BREEDER, granja),
                 "lr3": _lote("LR3", BirdTypeEnum.BREEDER, granja), "lh": _lote("LH", BirdTypeEnum.HATCHERY, planta)}
        lotes.update({f"lt_{t}": _lote(f"LT-{t.upper()}", BirdTypeEnum.BREEDER, granja) for t in NO_DISPONIBLES})
        s.add_all(lotes.values())
        await s.flush()
        await s.commit()
        d = {"a": a.id, "operador": operador.id, "granja": granja.id, "galpon_g": galpones[granja].id, "planta": planta.id, "galpon_p": galpones[planta].id,
             "url": test_database_url}
        d.update({k: v.id for k, v in lotes.items()})
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM egg_batches WHERE source_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p) OR hatchery_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM hatchery_params WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


# ── helpers ────────────────────────────────────────────────────────────────

async def _cuenta(esc, sql, **params) -> int:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return int((await s.execute(text(sql), params)).scalar() or 0)
    finally:
        await motor.dispose()


async def _saldos(esc, lote):
    from app.operations.validators import get_egg_balance, get_hatchery_egg_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return {"huevos": await get_egg_balance(s, lote), "incubadora": await get_hatchery_egg_balance(s, lote)}
    finally:
        await motor.dispose()


async def _eventos(esc, lote, tipo) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE :t", l=lote, t=tipo)


async def _filas(esc, lote, tipo) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM egg_movements em JOIN operational_events e ON e.id = em.event_id "
                              "WHERE e.lot_id = :l AND e.event_type::text ILIKE :t", l=lote, t=tipo)


async def _op(http_client, esc, lote, tipo, filas, n=None):
    """`filas`: lista de (egg_type, cantidad) para eventos de huevos; `n` para la carga de incubadora."""
    en_planta = lote.startswith("lh")
    cuerpo = {"lot_id": esc[lote], "event_type": tipo, "event_date": recent_event_date(),
              "farm_id": esc["planta" if en_planta else "granja"], "house_id": esc["galpon_p" if en_planta else "galpon_g"]}
    if tipo == "incubation_load":
        cuerpo["hatchery_params"] = [{"quantity_loaded": n}]
    else:
        cuerpo["egg_movements"] = [{"egg_type": t, "quantity": q} for t, q in filas]
    if tipo == "egg_dispatch":
        cuerpo["destination_farm_id"] = esc["planta"]
    return await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json=cuerpo)


async def _alta(http_client, esc, lote, tipo, filas, n=None):
    r = await _op(http_client, esc, lote, tipo, filas, n)
    assert r.status_code == 201, (tipo, filas, r.text)
    return r.json()["id"]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R172-01 — tipo positivo: el fértil cuenta
# ═══════════════════════════════════════════════════════════════════════════

async def test_r172_01_el_huevo_fertil_cuenta_como_disponible(http_client, esc):
    await _alta(http_client, esc, "lr", "egg_collection", [("fertile", 100)])
    assert (await _saldos(esc, esc["lr"]))["huevos"] == 100, "AC-R172-01"
    assert (await _op(http_client, esc, "lr", "egg_dispatch", [("fertile", 100)])).status_code == 201
    assert (await _saldos(esc, esc["lr"]))["huevos"] == 0
    assert _es_br(await _op(http_client, esc, "lr", "egg_dispatch", [("fertile", 1)]), "BR-02")


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R172-02 · 05 — lote mixto: la suma es selectiva; las filas capturadas persisten
# ═══════════════════════════════════════════════════════════════════════════

async def test_r172_02_05_recoleccion_mixta_solo_cuenta_el_fertil_y_conserva_las_filas(http_client, esc):
    recoleccion = await _alta(http_client, esc, "lr2", "egg_collection",
                              [("fertile", 100), ("dirty", 50), ("broken", 10), ("infertile", 5), ("discarded", 5)])
    assert (await _saldos(esc, esc["lr2"]))["huevos"] == 100, "AC-R172-02: 100 fértiles + 70 de otros tipos → disponibles 100"
    r = await _op(http_client, esc, "lr2", "egg_dispatch", [("fertile", 101)])
    assert _es_br(r, "BR-02"), ("AC-R172-02: 101 > 100 fértiles", r.status_code, r.text)
    assert (await _op(http_client, esc, "lr2", "egg_dispatch", [("fertile", 100)])).status_code == 201
    assert (await _saldos(esc, esc["lr2"]))["huevos"] == 0
    assert await _filas(esc, esc["lr2"], "egg_collection") == 5, "AC-R172-05: las cinco filas capturadas siguen ahí"
    assert await _cuenta(esc, "SELECT coalesce(sum(quantity), 0) FROM egg_movements WHERE event_id = :e AND egg_type = 'dirty'", e=recoleccion) == 50


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R172-03 — cada tipo no disponible por separado (tipo real del enum, no etiquetas distintas)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("tipo", NO_DISPONIBLES)
async def test_r172_03_un_tipo_no_disponible_no_infla_el_saldo(http_client, esc, tipo):
    lote = f"lt_{tipo}"
    await _alta(http_client, esc, lote, "egg_collection", [(tipo, 50)])
    assert (await _saldos(esc, esc[lote]))["huevos"] == 0, f"AC-R172-03: {tipo} no es disponibilidad"
    r = await _op(http_client, esc, lote, "egg_dispatch", [("fertile", 1)])
    assert _es_br(r, "BR-02"), (f"AC-R172-03: no hay fértiles que despachar ({tipo})", r.status_code, r.text)
    assert await _eventos(esc, esc[lote], "egg_dispatch") == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R172-04 — el despacho a incubadora solo lleva huevo fértil
# ═══════════════════════════════════════════════════════════════════════════

async def test_r172_04_un_despacho_con_fila_no_fertil_se_rechaza_sin_fila(http_client, esc):
    await _alta(http_client, esc, "lr3", "egg_collection", [("fertile", 100), ("dirty", 20)])
    antes = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"])
    r = await _op(http_client, esc, "lr3", "egg_dispatch", [("fertile", 10), ("dirty", 5)])
    assert _es_br(r, "BR-02"), ("AC-R172-04: una fila 'dirty' no se despacha a incubadora", r.status_code, r.text)
    assert await _eventos(esc, esc["lr3"], "egg_dispatch") == 0, "sin fila"
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"]) == antes, "sin auditoría de alta"
    assert (await _saldos(esc, esc["lr3"]))["huevos"] == 100


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R172-06 — BR-03, trazado por separado: en la incubadora solo cuenta el fértil recibido
# ═══════════════════════════════════════════════════════════════════════════

async def test_r172_06_en_la_incubadora_solo_cuenta_el_fertil_recibido(http_client, esc):
    await _alta(http_client, esc, "lh", "egg_reception_hatchery", [("fertile", 100), ("broken", 5), ("contaminated", 3)])
    assert (await _saldos(esc, esc["lh"]))["incubadora"] == 100, "AC-R172-06: 100 fértiles + 8 no fértiles → cargables 100"
    r = await _op(http_client, esc, "lh", "incubation_load", None, n=101)
    assert _es_br(r, "BR-03"), ("AC-R172-06: 101 > 100", r.status_code, r.text)
    assert (await _op(http_client, esc, "lh", "incubation_load", None, n=100)).status_code == 201
    assert (await _saldos(esc, esc["lh"]))["incubadora"] == 0
    assert await _filas(esc, esc["lh"], "egg_reception_hatchery") == 3, "las diferencias vs enviado se conservan"
