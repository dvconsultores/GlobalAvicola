"""`GA-REM-005` enmienda D · `R-161` · los saldos de huevos (`BR-02`) e incubación (`BR-03`) bajo el bloqueo del lote (`AC-R161-01…16`).

Escenario (prefijo `HUEVO-`):
    empresa A   breeder ON · hatchery ON            empresa B   breeder ON · hatchery OFF
    operador    operations:create/read/update · breeder + hatchery       operador_r  solo breeder (sin incubadora)
    sin_perm / acceso / lectura · actor_b (B) · global (comodín, sin empresa)
    lotes       lr, lr2 (A breeder, huevos) · lh, lh2 (A hatchery) · lhb (B hatchery, apagada) · lb (B breeder)
Carreras: tres decrementos de 70 sobre un saldo de 100, lanzados con `asyncio.gather` (mismo patrón que `R-130 AC10`).
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
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "HUEVO-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


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
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "hatchery", True), (b, "breeder", True), (b, "hatchery", False)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]
        roles = {
            "operador": _rol("Op", a.id, ops), "operador_r": _rol("OpR", a.id, ops),
            "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]),
            "lectura": _rol("Lectura", a.id, [("review", PA.READ), ("corrections", PA.READ), ("audit", PA.READ), ("reports", PA.READ), ("operations", PA.READ)]),
            "acceso": _rol("Acceso", a.id, [("business_units", PA.READ), ("business_units", PA.CREATE), ("business_units", PA.UPDATE), ("business_units", PA.DELETE)]),
            "b": _rol("OpB", b.id, ops), "global": _rol("Global", None, []),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Huevo", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {k: _usuario(a.id, k.upper(), roles[k][0]) for k in ("operador", "operador_r", "sin_perm", "lectura", "acceso")}
        u["actor_b"] = _usuario(b.id, "B", roles["b"][0]); u["global"] = _usuario(None, "GLOBAL", roles["global"][0])
        s.add_all(u.values())
        await s.flush()
        for k in ("operador", "operador_r", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        for k in ("operador", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "hatchery")])
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, code)])

        granja_a = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        planta_a = Farm(company_id=a.id, name=f"{PREFIJO}PLANTA-A", code=f"{PREFIJO}PA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        granja_b = Farm(company_id=b.id, name=f"{PREFIJO}GRANJA-B", code=f"{PREFIJO}GB-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja_a, planta_a, granja_b])
        await s.flush()
        galpones = {f: House(farm_id=f.id, name=f"{PREFIJO}G-{f.code}", capacity=100_000, is_active=True) for f in (granja_a, planta_a, granja_b)}
        s.add_all(galpones.values())
        await s.flush()

        def _lote(empresa, marca, tipo, granja):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE,
                       farm_id=granja.id, house_id=galpones[granja].id)

        lotes = {"lr": _lote(a, "LR", BirdTypeEnum.BREEDER, granja_a), "lr2": _lote(a, "LR2", BirdTypeEnum.BREEDER, granja_a),
                 "lr3": _lote(a, "LR3", BirdTypeEnum.BREEDER, granja_a),
                 "lh": _lote(a, "LH", BirdTypeEnum.HATCHERY, planta_a), "lh2": _lote(a, "LH2", BirdTypeEnum.HATCHERY, planta_a),
                 "lh3": _lote(a, "LH3", BirdTypeEnum.HATCHERY, planta_a),
                 "lhb": _lote(b, "LHB", BirdTypeEnum.HATCHERY, granja_b), "lb": _lote(b, "LB", BirdTypeEnum.BREEDER, granja_b)}
        s.add_all(lotes.values())
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "granja_a": granja_a.id, "galpon_a": galpones[granja_a].id, "planta_a": planta_a.id, "galpon_p": galpones[planta_a].id,
             "granja_b": granja_b.id, "galpon_b": galpones[granja_b].id, "url": test_database_url}
        d.update({k: v.id for k, v in u.items()})
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
            "DELETE FROM chick_batches WHERE hatchery_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
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

async def _sql(esc, sql, **params):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(sql), params)).all()
    finally:
        await motor.dispose()


async def _cuenta(esc, sql, **params) -> int:
    return int((await _sql(esc, sql, **params))[0][0] or 0)


async def _saldos(esc, lote):
    from app.operations.validators import get_egg_balance, get_hatchery_egg_balance, get_viable_chick_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return {"huevos": await get_egg_balance(s, lote), "incubadora": await get_hatchery_egg_balance(s, lote),
                    "viables": await get_viable_chick_balance(s, lote)}
    finally:
        await motor.dispose()


async def _eventos(esc, lote, tipo) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE :t", l=lote, t=tipo)


def _cuerpo(esc, lote, tipo, n, *, granja, galpon, egg_type="fertile"):
    cuerpo = {"lot_id": esc[lote], "event_type": tipo, "event_date": recent_event_date(), "farm_id": esc[granja], "house_id": esc[galpon]}
    if tipo == "incubation_load":
        cuerpo["hatchery_params"] = [{"quantity_loaded": n}]
    elif tipo in ("mortality_recording", "cull_recording", "chick_dispatch", "birth_registration"):
        cuerpo["bird_movements"] = [{"sex": "mixed", "quantity": n}]
        if tipo == "birth_registration":
            cuerpo.update({"chicks_healthy": n, "chicks_weak": 0})
    else:
        cuerpo["egg_movements"] = [{"egg_type": egg_type, "quantity": n}]
    if tipo == "egg_dispatch":
        cuerpo["destination_farm_id"] = esc["planta_a"]
    return cuerpo


async def _op(http_client, esc, actor, lote, tipo, n, company_id=None, **kw):
    granja, galpon = ("planta_a", "galpon_p") if lote.startswith("lh") and lote != "lhb" else (("granja_b", "galpon_b") if lote in ("lhb", "lb") else ("granja_a", "galpon_a"))
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=_cuerpo(esc, lote, tipo, n, granja=granja, galpon=galpon, **kw))


async def _recolectar(http_client, esc, lote, n):
    r = await _op(http_client, esc, "operador", lote, "egg_collection", n)
    assert r.status_code == 201, r.text
    return r.json()


async def _recibir_huevos(http_client, esc, lote, n):
    r = await _op(http_client, esc, "operador", lote, "egg_reception_hatchery", n)
    assert r.status_code == 201, r.text
    return r.json()


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R161-01 · 02 · 03 · 04 · 15 — secuencial, bordes, cero, auditoría
# ═══════════════════════════════════════════════════════════════════════════

async def test_r161_01_02_03_15_secuencial_resto_exacto_y_uno_de_mas(http_client, esc):
    await _recolectar(http_client, esc, "lr", 100)
    assert (await _op(http_client, esc, "operador", "lr", "egg_dispatch", 60)).status_code == 201
    assert (await _saldos(esc, esc["lr"]))["huevos"] == 40, "AC-R161-01"
    r = await _op(http_client, esc, "operador", "lr", "egg_dispatch", 40)  # resto exacto
    assert r.status_code == 201, ("AC-R161-02", r.text)
    assert (await _saldos(esc, esc["lr"]))["huevos"] == 0
    antes = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"])
    r = await _op(http_client, esc, "operador", "lr", "egg_dispatch", 1)  # uno de más
    assert _es_br(r, "BR-02"), ("AC-R161-03", r.text)
    assert await _eventos(esc, esc["lr"], "egg_dispatch") == 2 and (await _saldos(esc, esc["lr"]))["huevos"] == 0
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"]) == antes, "AC-R161-15: la denegada no audita"
    # incubadora: resto exacto de una vez y uno de más
    await _recibir_huevos(http_client, esc, "lh", 100)
    assert (await _op(http_client, esc, "operador", "lh", "incubation_load", 100)).status_code == 201, "AC-R161-02 (BR-03)"
    assert (await _saldos(esc, esc["lh"]))["incubadora"] == 0
    assert _es_br(await _op(http_client, esc, "operador", "lh", "incubation_load", 1), "BR-03"), "AC-R161-03 (BR-03)"


async def test_r161_04_la_cantidad_cero_se_rechaza(http_client, esc):
    await _recolectar(http_client, esc, "lr", 10)
    await _recibir_huevos(http_client, esc, "lh", 10)
    assert _es_br(await _op(http_client, esc, "operador", "lr", "egg_dispatch", 0), "BR-02"), "AC-R161-04: un despacho de 0 huevos no es un despacho"
    assert _es_br(await _op(http_client, esc, "operador", "lh", "incubation_load", 0), "BR-03"), "AC-R161-04: una carga de 0 no es una carga"
    assert await _eventos(esc, esc["lr"], "egg_dispatch") == 0 and await _eventos(esc, esc["lh"], "incubation_load") == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R161-05 · 06 · 07 — carreras (verdad final, no solo HTTP)
# ═══════════════════════════════════════════════════════════════════════════

CONCURRENTES = 5  # cinco decrementos de 70 sobre 100: solo cabe uno; tres lotes frescos por carrera para que la reproducción no dependa del tiempo


async def _carrera(http_client, esc, lotes, tipo, entrada, clave):
    """Lanza `CONCURRENTES` decrementos de 70 sobre un saldo de 100 en cada lote y devuelve la verdad final por lote."""
    resultados = []
    for lote in lotes:
        await entrada(http_client, esc, lote, 100)
        respuestas = await asyncio.gather(*[_op(http_client, esc, "operador", lote, tipo, 70) for _ in range(CONCURRENTES)])
        resultados.append({"lote": lote, "codigos": sorted(r.status_code for r in respuestas),
                           "saldo": (await _saldos(esc, esc[lote]))[clave], "filas": await _eventos(esc, esc[lote], tipo)})
    return resultados


async def test_r161_05_despachos_de_huevos_concurrentes_no_exceden_el_saldo(http_client, esc):
    resultados = await _carrera(http_client, esc, ("lr", "lr2", "lr3"), "egg_dispatch", _recolectar, "huevos")
    negativos = [r for r in resultados if r["saldo"] < 0]
    assert not negativos, f"AC-R161-05: despachos concurrentes dejaron saldos negativos: {negativos}"
    for r in resultados:
        assert r["codigos"] == [201] + [400] * (CONCURRENTES - 1) and r["filas"] == 1 and r["saldo"] == 30, r


async def test_r161_06_cargas_de_incubadora_concurrentes_no_exceden_lo_recibido(http_client, esc):
    resultados = await _carrera(http_client, esc, ("lh", "lh2", "lh3"), "incubation_load", _recibir_huevos, "incubadora")
    negativos = [r for r in resultados if r["saldo"] < 0]
    assert not negativos, f"AC-R161-06: cargas concurrentes dejaron saldos negativos: {negativos}"
    for r in resultados:
        assert r["codigos"] == [201] + [400] * (CONCURRENTES - 1) and r["filas"] == 1 and r["saldo"] == 30, r


async def test_r161_07_dos_lotes_distintos_no_se_serializan_entre_si(http_client, esc):
    await _recolectar(http_client, esc, "lr", 100)
    await _recolectar(http_client, esc, "lr2", 100)
    respuestas = await asyncio.gather(_op(http_client, esc, "operador", "lr", "egg_dispatch", 70), _op(http_client, esc, "operador", "lr2", "egg_dispatch", 70))
    assert [r.status_code for r in respuestas] == [201, 201], [r.text[:120] for r in respuestas]
    assert (await _saldos(esc, esc["lr"]))["huevos"] == 30 and (await _saldos(esc, esc["lr2"]))["huevos"] == 30


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R161-10 … 14 — cadena de seguridad
# ═══════════════════════════════════════════════════════════════════════════

async def test_r161_10_14_empresa_unidad_concesion_rbac_y_contexto_global(http_client, esc):
    await _recolectar(http_client, esc, "lr", 100)
    assert _es_br(await _op(http_client, esc, "actor_b", "lr", "egg_dispatch", 10), "BR-07"), "AC-R161-10: otra empresa"
    assert _es_br(await _op(http_client, esc, "global", "lr", "egg_dispatch", 10), "BR-07"), "AC-R161-13: global sin contexto"
    assert (await _op(http_client, esc, "global", "lhb", "incubation_load", 10, company_id=esc["b"])).status_code == 403, "AC-R161-11: incubadora apagada en B"
    assert _es_br(await _op(http_client, esc, "actor_b", "lhb", "incubation_load", 10), "BR-07"), "AC-R161-11: concesión histórica sobre unidad apagada"
    assert _es_br(await _op(http_client, esc, "operador_r", "lh", "incubation_load", 10), "BR-07"), "AC-R161-12: sin la unidad de incubadora"
    for actor in ("sin_perm", "acceso", "lectura"):
        assert (await _op(http_client, esc, actor, "lr", "egg_dispatch", 10)).status_code == 403, ("AC-R161-14", actor)
    assert (await _saldos(esc, esc["lr"]))["huevos"] == 100 and await _eventos(esc, esc["lr"], "egg_dispatch") == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R161-16 — control R-171: el backend ya admite mortalidad y descarte en incubadora
# ═══════════════════════════════════════════════════════════════════════════

async def test_r161_16_control_r171_mortalidad_y_descarte_en_incubadora_restan_de_viables_una_vez(http_client, esc):
    r = await _op(http_client, esc, "operador", "lh", "birth_registration", 100)
    assert r.status_code == 201, r.text
    assert (await _saldos(esc, esc["lh"]))["viables"] == 100
    assert (await _op(http_client, esc, "operador", "lh", "mortality_recording", 10)).status_code == 201
    assert (await _op(http_client, esc, "operador", "lh", "cull_recording", 5)).status_code == 201
    assert (await _saldos(esc, esc["lh"]))["viables"] == 85, "R-171 es UI_ONLY: el dominio ya resta mortalidad y descarte de viables"
    assert _es_br(await _op(http_client, esc, "operador", "lh", "chick_dispatch", 86), "BR-04")
