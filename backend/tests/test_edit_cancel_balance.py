"""`GA-REM-005` enmienda E · `R-173` (P1) + `R-174` · las mutaciones posteriores al alta respetan el invariante del saldo.

Escenario (prefijo `MUTA-`):
    empresa A   breeder ON · hatchery ON · broiler OFF          empresa B   breeder ON · hatchery ON
    operador    operations:create/read/update + corrections:correct · breeder + hatchery
    operador_r  mismos permisos · solo breeder            sin_perm / lectura / acceso · actor_b (B) · global (comodín, sin empresa)
    lotes A     lr, lr2, lr3, lr4 (breeder, granja_a) · lh, lh2, lh3 (hatchery, planta_a) · lbo (broiler, unidad apagada) ·
                lc (breeder, CERRADO) · lf (breeder, start_date mañana → BR-06)         lotes B: lb (breeder) · lhb (hatchery)
Toda prueba mide la verdad final (saldos por las mismas funciones de producción), no solo el HTTP.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

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

PREFIJO = "MUTA-"


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
        for empresa, code, on in ((a, "breeder", True), (a, "hatchery", True), (a, "broiler", False), (b, "breeder", True), (b, "hatchery", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ),
               ("corrections", PA.CORRECT), ("corrections", PA.READ)]
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
            return User(first_name=marca, last_name="Muta", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
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

        def _lote(empresa, marca, tipo, granja, **kw):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo,
                       status=kw.pop("status", LotStatus.ACTIVE), farm_id=granja.id, house_id=galpones[granja].id, **kw)

        lotes = {f"lr{i}": _lote(a, f"LR{i}", BirdTypeEnum.BREEDER, granja_a) for i in ("", "2", "3", "4")}
        lotes.update({f"lh{i}": _lote(a, f"LH{i}", BirdTypeEnum.HATCHERY, planta_a) for i in ("", "2", "3")})
        lotes["lbo"] = _lote(a, "LBO", BirdTypeEnum.BROILER, granja_a)
        lotes["lc"] = _lote(a, "LC", BirdTypeEnum.BREEDER, granja_a, status=LotStatus.CLOSED)
        lotes["lf"] = _lote(a, "LF", BirdTypeEnum.BREEDER, granja_a, start_date=datetime.now(timezone.utc) + timedelta(days=1))
        lotes["lb"] = _lote(b, "LB", BirdTypeEnum.BREEDER, granja_b)
        lotes["lhb"] = _lote(b, "LHB", BirdTypeEnum.HATCHERY, granja_b)
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
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM egg_batches WHERE source_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p) OR hatchery_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM chick_batches WHERE hatchery_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM hatchery_params WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM feed_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
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
    """Las mismas funciones que producción (`validators`): aves, viables, huevos, incubadora."""
    from app.operations.validators import get_current_bird_balance, get_egg_balance, get_hatchery_egg_balance, get_viable_chick_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return {"aves": await get_current_bird_balance(s, lote), "viables": await get_viable_chick_balance(s, lote),
                    "huevos": await get_egg_balance(s, lote), "incubadora": await get_hatchery_egg_balance(s, lote)}
    finally:
        await motor.dispose()


async def _evento(esc, event_id):
    fila = (await _sql(esc, "SELECT lot_id, status::text, version, coalesce(farm_id, 0) FROM operational_events WHERE id = :e", e=event_id))[0]
    return {"lot_id": fila[0], "status": fila[1].lower(), "version": fila[2], "farm_id": fila[3]}


async def _eventos(esc, lote, tipo) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE :t", l=lote, t=tipo)


async def _auditorias(esc, event_id, accion) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e AND action::text ILIKE :a",
                         e=str(event_id), a=accion)


def _ubicacion(lote: str):
    if lote.startswith("lh") and lote != "lhb":
        return "planta_a", "galpon_p"
    if lote in ("lb", "lhb"):
        return "granja_b", "galpon_b"
    return "granja_a", "galpon_a"


def _cuerpo(esc, lote, tipo, n, *, egg_type="fertile"):
    granja, galpon = _ubicacion(lote)
    cuerpo = {"lot_id": esc[lote], "event_type": tipo, "event_date": recent_event_date(), "farm_id": esc[granja], "house_id": esc[galpon]}
    if tipo == "incubation_load":
        cuerpo["hatchery_params"] = [{"quantity_loaded": n}]
    elif tipo in ("mortality_recording", "cull_recording", "chick_dispatch", "birth_registration", "bird_reception", "bird_exit"):
        cuerpo["bird_movements"] = [{"sex": "mixed", "quantity": n}]
        if tipo == "birth_registration":
            cuerpo.update({"chicks_healthy": n, "chicks_weak": 0})
        if tipo == "bird_reception":  # `BR-20`: la recepción de reproductoras declara su cuadre (setup)
            cuerpo.update({"received_total": n, "dead_on_arrival": 0, "rejected_on_arrival": 0})
    elif tipo == "feed_registration":
        cuerpo["feed_movements"] = [{"quantity_kg": float(n)}]
    else:
        cuerpo["egg_movements"] = [{"egg_type": egg_type, "quantity": n}]
    if tipo == "egg_dispatch":
        cuerpo["destination_farm_id"] = esc["planta_a"]
    return cuerpo


async def _op(http_client, esc, actor, lote, tipo, n, company_id=None, **kw):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=_cuerpo(esc, lote, tipo, n, **kw))


async def _alta(http_client, esc, lote, tipo, n) -> int:
    r = await _op(http_client, esc, "operador", lote, tipo, n)
    assert r.status_code == 201, (tipo, r.text)
    return r.json()["id"]


async def _put(http_client, esc, actor, event_id, cuerpo, company_id=None):
    return await http_client.put(f"/api/v1/operations/{event_id}", headers=_token(esc[actor], company_id), json=cuerpo)


async def _corregir(http_client, esc, actor, event_id, campo, valor, company_id=None):
    return await http_client.post("/api/v1/corrections", headers=_token(esc[actor], company_id),
                                  json={"event_id": event_id, "field_name": campo, "corrected_value": str(valor), "reason": f"{PREFIJO}corrección de prueba"})


async def _cancelar(http_client, esc, actor, event_id, company_id=None):
    return await http_client.post(f"/api/v1/operations/{event_id}/cancel", headers=_token(esc[actor], company_id))


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-01 — control: la cantidad no se edita ni se corrige
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_01_control_la_cantidad_no_se_edita_ni_se_corrige(http_client, esc):
    r = await _alta(http_client, esc, "lr", "bird_reception", 100)
    assert (await _put(http_client, esc, "operador", r, {"bird_movements": [{"sex": "mixed", "quantity": 1000}]})).status_code == 422
    assert (await _corregir(http_client, esc, "operador", r, "bird_movements", "1000")).status_code == 400
    assert (await _saldos(esc, esc["lr"]))["aves"] == 100


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-02 — mover una salida a un lote sin saldo se deniega (cuatro familias)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_02_mover_una_salida_a_un_lote_sin_saldo_se_deniega(http_client, esc):
    casos = []
    # aves: descarte de 80 sobre 100 en lr → lr2 solo tiene 50
    await _alta(http_client, esc, "lr", "bird_reception", 100); await _alta(http_client, esc, "lr2", "bird_reception", 50)
    casos.append((await _alta(http_client, esc, "lr", "cull_recording", 80), "lr", "lr2", "BR-01", "aves", 20, 50))
    # pollitos: despacho de 80 sobre 100 nacidos en lh → lh2 solo tiene 50 viables
    await _alta(http_client, esc, "lh", "birth_registration", 100); await _alta(http_client, esc, "lh2", "birth_registration", 50)
    casos.append((await _alta(http_client, esc, "lh", "chick_dispatch", 80), "lh", "lh2", "BR-04", "viables", 20, 50))
    # huevos: despacho de 80 sobre 100 en lr3 → lr4 solo tiene 50
    await _alta(http_client, esc, "lr3", "egg_collection", 100); await _alta(http_client, esc, "lr4", "egg_collection", 50)
    casos.append((await _alta(http_client, esc, "lr3", "egg_dispatch", 80), "lr3", "lr4", "BR-02", "huevos", 20, 50))
    # incubadora: carga de 80 sobre 100 recibidos en lh3 → lh2 solo recibió 50
    await _alta(http_client, esc, "lh3", "egg_reception_hatchery", 100); await _alta(http_client, esc, "lh2", "egg_reception_hatchery", 50)
    casos.append((await _alta(http_client, esc, "lh3", "incubation_load", 80), "lh3", "lh2", "BR-03", "incubadora", 20, 50))

    for evento, origen, destino, regla, clave, saldo_a, saldo_b in casos:
        r = await _put(http_client, esc, "operador", evento, {"lot_id": esc[destino]})
        assert _es_br(r, regla), (f"AC-R173-02 {clave}: el destino no tiene saldo para la salida", r.status_code, r.text)
        ev = await _evento(esc, evento)
        assert ev["lot_id"] == esc[origen] and ev["version"] == 1, ("el evento no cambia", clave, ev)
        assert (await _saldos(esc, esc[origen]))[clave] == saldo_a and (await _saldos(esc, esc[destino]))[clave] == saldo_b, clave
        assert await _auditorias(esc, evento, "updated") == 0, "una denegación no audita"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-03 · 10 — mover una salida con saldo: verdad final en A y B, auditoría con valores
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_03_10_mover_una_salida_con_saldo_es_verdad_final_y_auditada(http_client, esc):
    await _alta(http_client, esc, "lr", "bird_reception", 100); await _alta(http_client, esc, "lr2", "bird_reception", 100)
    descarte = await _alta(http_client, esc, "lr", "cull_recording", 30)
    assert (await _saldos(esc, esc["lr"]))["aves"] == 70
    r = await _put(http_client, esc, "operador", descarte, {"lot_id": esc["lr2"]})
    assert r.status_code == 200, r.text
    assert (await _saldos(esc, esc["lr"]))["aves"] == 100 and (await _saldos(esc, esc["lr2"]))["aves"] == 70, "AC-R173-03: verdad final en A y B"
    assert (await _evento(esc, descarte))["lot_id"] == esc["lr2"]
    fila = await _sql(esc, "SELECT previous_values->>'lot_id', new_values->>'lot_id' FROM audit_logs WHERE entity_type = 'operational_event' "
                           "AND entity_id = :e AND action::text ILIKE 'updated' ORDER BY created_at DESC LIMIT 1", e=str(descarte))
    assert fila and fila[0][0] == str(esc["lr"]) and fila[0][1] == str(esc["lr2"]), ("AC-R173-10: la auditoría conserva lote anterior y nuevo", fila)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-04 — mover una entrada: el origen conserva saldo ≥ 0
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_04_mover_una_entrada_conserva_el_origen_no_negativo(http_client, esc):
    # aves: la recepción de 100 con un descarte de 30 no puede irse (lr quedaría en −30)
    recepcion = await _alta(http_client, esc, "lr", "bird_reception", 100)
    await _alta(http_client, esc, "lr", "cull_recording", 30)
    r = await _put(http_client, esc, "operador", recepcion, {"lot_id": esc["lr2"]})
    assert _es_br(r, "BR-01"), ("AC-R173-04 aves: el origen quedaría negativo", r.status_code, r.text)
    assert (await _evento(esc, recepcion))["lot_id"] == esc["lr"] and (await _saldos(esc, esc["lr"]))["aves"] == 70 and (await _saldos(esc, esc["lr2"]))["aves"] == 0
    # nacimiento con despachos: viables (BR-04)
    nacimiento = await _alta(http_client, esc, "lh", "birth_registration", 100)
    await _alta(http_client, esc, "lh", "chick_dispatch", 30)
    r = await _put(http_client, esc, "operador", nacimiento, {"lot_id": esc["lh2"]})
    assert _es_br(r, "BR-04"), ("AC-R173-04 viables", r.status_code, r.text)
    assert (await _saldos(esc, esc["lh"]))["viables"] == 70 and (await _saldos(esc, esc["lh2"]))["viables"] == 0
    # huevos: recolección con despachos
    recoleccion = await _alta(http_client, esc, "lr3", "egg_collection", 100)
    await _alta(http_client, esc, "lr3", "egg_dispatch", 40)
    r = await _put(http_client, esc, "operador", recoleccion, {"lot_id": esc["lr4"]})
    assert _es_br(r, "BR-02"), ("AC-R173-04 huevos", r.status_code, r.text)
    assert (await _saldos(esc, esc["lr3"]))["huevos"] == 60 and (await _saldos(esc, esc["lr4"]))["huevos"] == 0
    # incubadora: recepción con cargas
    recibida = await _alta(http_client, esc, "lh3", "egg_reception_hatchery", 100)
    await _alta(http_client, esc, "lh3", "incubation_load", 40)
    r = await _put(http_client, esc, "operador", recibida, {"lot_id": esc["lh2"]})
    assert _es_br(r, "BR-03"), ("AC-R173-04 incubadora", r.status_code, r.text)
    assert (await _saldos(esc, esc["lh3"]))["incubadora"] == 60
    # entrada sin salidas: se mueve; A baja, B sube
    libre = await _alta(http_client, esc, "lr4", "bird_reception", 80)
    r = await _put(http_client, esc, "operador", libre, {"lot_id": esc["lr2"]})
    assert r.status_code == 200, r.text
    assert (await _saldos(esc, esc["lr4"]))["aves"] == 0 and (await _saldos(esc, esc["lr2"]))["aves"] == 80, "AC-R173-04: verdad final tras mover una entrada"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-05 — cancelar una entrada que dejaría el saldo negativo se deniega (cuatro familias)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_05_cancelar_una_entrada_que_dejaria_negativo_se_deniega(http_client, esc):
    casos = [
        (await _alta(http_client, esc, "lr", "bird_reception", 100), "lr", "cull_recording", "BR-01", "aves"),
        (await _alta(http_client, esc, "lh", "birth_registration", 100), "lh", "chick_dispatch", "BR-04", "viables"),
        (await _alta(http_client, esc, "lr3", "egg_collection", 100), "lr3", "egg_dispatch", "BR-02", "huevos"),
        (await _alta(http_client, esc, "lh3", "egg_reception_hatchery", 100), "lh3", "incubation_load", "BR-03", "incubadora"),
    ]
    for entrada, lote, salida, regla, clave in casos:
        await _alta(http_client, esc, lote, salida, 30)
        r = await _cancelar(http_client, esc, "operador", entrada)
        assert _es_br(r, regla), (f"AC-R173-05 {clave}: la anulación dejaría el saldo en −30", r.status_code, r.text)
        ev = await _evento(esc, entrada)
        assert ev["status"] == "registered", ("el estado no cambia", clave, ev)
        assert (await _saldos(esc, esc[lote]))[clave] == 70, clave
        assert await _auditorias(esc, entrada, "cancelled") == 0, "una denegación no audita la cancelación"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-06 · 07 — cancelar con saldo suficiente; cancelar una salida restaura; segunda cancelación sin efecto
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_06_07_cancelar_con_saldo_suficiente_y_segunda_cancelacion_sin_efecto(http_client, esc):
    r1 = await _alta(http_client, esc, "lr", "bird_reception", 100)
    r2 = await _alta(http_client, esc, "lr", "bird_reception", 50)
    descarte = await _alta(http_client, esc, "lr", "cull_recording", 30)
    assert (await _saldos(esc, esc["lr"]))["aves"] == 120
    assert (await _cancelar(http_client, esc, "operador", r2)).status_code == 200
    assert (await _saldos(esc, esc["lr"]))["aves"] == 70, "AC-R173-06: 100 − 30"
    assert (await _cancelar(http_client, esc, "operador", descarte)).status_code == 200
    assert (await _saldos(esc, esc["lr"]))["aves"] == 100, "AC-R130-07: cancelar una salida devuelve el saldo"
    assert (await _cancelar(http_client, esc, "operador", r1)).status_code == 200
    assert (await _saldos(esc, esc["lr"]))["aves"] == 0
    r = await _cancelar(http_client, esc, "operador", r2)
    assert r.status_code == 400, ("AC-R173-07: segunda cancelación", r.text)
    assert (await _saldos(esc, esc["lr"]))["aves"] == 0 and await _auditorias(esc, r2, "cancelled") == 1, "sin segundo efecto ni segunda auditoría"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-08 · 09 — carreras: cancelar/mover una entrada frente a salidas concurrentes
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_07b_dos_cancelaciones_concurrentes_una_sola_transicion(http_client, esc):
    """`AC-R173-07`: a lo sumo una transición efectiva; la segunda relee el estado bajo el bloqueo y responde 400."""
    resultados = []
    for lote in ("lr", "lr2", "lr3"):
        recepcion = await _alta(http_client, esc, lote, "bird_reception", 100)
        respuestas = await asyncio.gather(*[_cancelar(http_client, esc, "operador", recepcion) for _ in range(3)])
        resultados.append({"lote": lote, "codigos": sorted(r.status_code for r in respuestas),
                           "auditorias": await _auditorias(esc, recepcion, "cancelled"), "estado": (await _evento(esc, recepcion))["status"]})
    for r in resultados:
        assert r["codigos"] == [200, 400, 400] and r["auditorias"] == 1 and r["estado"] == "cancelled", ("AC-R173-07: una sola transición", r)


async def test_r173_08_carrera_cancelar_una_entrada_frente_a_salidas_concurrentes(http_client, esc):
    resultados = []
    for lote in ("lr", "lr2", "lr3"):
        recepcion = await _alta(http_client, esc, lote, "bird_reception", 100)
        respuestas = await asyncio.gather(_cancelar(http_client, esc, "operador", recepcion),
                                          *[_op(http_client, esc, "operador", lote, "cull_recording", 20) for _ in range(5)])
        cancel, salidas = respuestas[0].status_code, sorted(r.status_code for r in respuestas[1:])
        saldo = (await _saldos(esc, esc[lote]))["aves"]
        vigentes = await _cuenta(esc, "SELECT coalesce(sum(bm.quantity), 0) FROM bird_movements bm JOIN operational_events e ON e.id = bm.event_id "
                                      "WHERE e.lot_id = :l AND e.event_type::text ILIKE 'cull_recording' AND e.status::text NOT ILIKE 'cancelled'", l=esc[lote])
        resultados.append({"lote": lote, "cancel": cancel, "salidas": salidas, "saldo": saldo, "descartes_vigentes": vigentes,
                           "estado": (await _evento(esc, recepcion))["status"]})
    negativos = [r for r in resultados if r["saldo"] < 0]
    assert not negativos, f"AC-R173-08: la cancelación y las salidas no se serializaron: {negativos}"
    for r in resultados:
        if r["cancel"] == 200:
            assert r["estado"] == "cancelled" and r["salidas"] == [400] * 5 and r["saldo"] == 0, r
        else:
            assert r["cancel"] == 400 and r["estado"] == "registered" and r["saldo"] == 100 - r["descartes_vigentes"] and r["saldo"] >= 0, r


async def test_r173_09_carrera_mover_una_entrada_frente_a_una_salida_en_el_origen(http_client, esc):
    resultados = []
    for origen, destino in (("lr", "lr2"), ("lr3", "lr4")):
        recepcion = await _alta(http_client, esc, origen, "bird_reception", 100)
        respuestas = await asyncio.gather(_put(http_client, esc, "operador", recepcion, {"lot_id": esc[destino]}),
                                          _op(http_client, esc, "operador", origen, "bird_exit", 100))
        codigos = [r.status_code for r in respuestas]
        a, b = (await _saldos(esc, esc[origen]))["aves"], (await _saldos(esc, esc[destino]))["aves"]
        resultados.append({"par": (origen, destino), "put": codigos[0], "salida": codigos[1], "a": a, "b": b, "lote": (await _evento(esc, recepcion))["lot_id"]})
    for r in resultados:
        assert r["a"] >= 0 and r["b"] >= 0, ("AC-R173-09: saldo negativo", r)
        assert sorted([r["put"], r["salida"]]) in ([200, 400], [201, 400]), ("AC-R173-09: exactamente una gana", r)
        if r["put"] == 200:
            assert r["a"] == 0 and r["b"] == 100 and r["lote"] == esc[r["par"][1]], r
        else:
            assert r["a"] == 0 and r["b"] == 0 and r["lote"] == esc[r["par"][0]], r


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-11 … 14 — la corrección de lot_id / ubicación se verifica como un alta (inquilino, unidad, saldo, activo, fecha)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_11_correccion_de_lote_a_otra_empresa_se_deniega(http_client, esc):
    recepcion = await _alta(http_client, esc, "lr", "bird_reception", 100)
    r = await _corregir(http_client, esc, "operador", recepcion, "lot_id", esc["lb"])
    assert _es_br(r, "BR-07"), ("AC-R173-11: el lote de B no existe para A", r.status_code, r.text)
    assert (await _evento(esc, recepcion))["lot_id"] == esc["lr"]
    assert (await _saldos(esc, esc["lb"]))["aves"] == 0 and (await _saldos(esc, esc["lr"]))["aves"] == 100, "los saldos de B no se tocan"
    assert await _cuenta(esc, "SELECT count(*) FROM correction_logs WHERE event_id = :e", e=recepcion) == 0


async def test_r173_12_correccion_de_lote_a_unidad_apagada_o_sin_concesion_se_deniega(http_client, esc):
    await _alta(http_client, esc, "lr", "bird_reception", 100)
    descarte = await _alta(http_client, esc, "lr", "cull_recording", 10)
    r = await _corregir(http_client, esc, "operador", descarte, "lot_id", esc["lbo"])
    assert _es_br(r, "BR-07"), ("AC-R173-12: unidad broiler apagada en A (actor de empresa)", r.status_code, r.text)
    r = await _corregir(http_client, esc, "global", descarte, "lot_id", esc["lbo"], company_id=esc["a"])
    assert r.status_code == 403, ("AC-R173-12: la autoridad global situada en A no opera la unidad apagada", r.status_code, r.text)
    # operador_r solo alcanza breeder: no puede mover su descarte a un lote de incubadora
    r_op = await _op(http_client, esc, "operador_r", "lr", "cull_recording", 10)
    assert r_op.status_code == 201, r_op.text
    r = await _corregir(http_client, esc, "operador_r", r_op.json()["id"], "lot_id", esc["lh"])
    assert _es_br(r, "BR-07"), ("AC-R173-12: sin concesión de la unidad destino", r.status_code, r.text)
    assert (await _evento(esc, descarte))["lot_id"] == esc["lr"] and (await _evento(esc, r_op.json()["id"]))["lot_id"] == esc["lr"]
    assert (await _saldos(esc, esc["lbo"]))["aves"] == 0 and (await _saldos(esc, esc["lh"]))["aves"] == 0


async def test_r173_13_correccion_de_lote_a_destino_sin_saldo_inactivo_o_con_fecha_invalida_se_deniega(http_client, esc):
    await _alta(http_client, esc, "lr", "bird_reception", 100); await _alta(http_client, esc, "lr2", "bird_reception", 50)
    descarte = await _alta(http_client, esc, "lr", "cull_recording", 80)
    r = await _corregir(http_client, esc, "operador", descarte, "lot_id", esc["lr2"])
    assert _es_br(r, "BR-01"), ("AC-R173-13: el destino no tiene saldo", r.status_code, r.text)
    r = await _corregir(http_client, esc, "operador", descarte, "lot_id", esc["lc"])
    assert _es_br(r, "BR-07") and "no está activo" in r.json()["detail"], ("AC-R173-13: lote cerrado", r.status_code, r.text)
    r = await _corregir(http_client, esc, "operador", descarte, "lot_id", esc["lf"])
    assert _es_br(r, "BR-06"), ("AC-R173-13: fecha anterior al inicio del lote destino", r.status_code, r.text)
    ev = await _evento(esc, descarte)
    assert ev["lot_id"] == esc["lr"] and ev["status"] == "registered" and ev["version"] == 1
    assert (await _saldos(esc, esc["lr"]))["aves"] == 20 and (await _saldos(esc, esc["lr2"]))["aves"] == 50
    # con saldo suficiente la corrección mueve el efecto: verdad final en ambos lotes
    await _alta(http_client, esc, "lr2", "bird_reception", 50)
    r = await _corregir(http_client, esc, "operador", descarte, "lot_id", esc["lr2"])
    assert r.status_code == 201, r.text
    assert (await _saldos(esc, esc["lr"]))["aves"] == 100 and (await _saldos(esc, esc["lr2"]))["aves"] == 20, "verdad final tras corregir el lote"


async def test_r173_14_correccion_de_ubicacion_a_otra_empresa_se_deniega(http_client, esc):
    recepcion = await _alta(http_client, esc, "lr", "bird_reception", 100)
    r = await _corregir(http_client, esc, "operador", recepcion, "farm_id", esc["granja_b"])
    assert _es_br(r, "BR-07"), ("AC-R173-14: granja de otra empresa", r.status_code, r.text)
    assert (await _evento(esc, recepcion))["farm_id"] == esc["granja_a"]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R173-17 — control: un evento sin efecto en saldo cambia de lote como hoy
# ═══════════════════════════════════════════════════════════════════════════

async def test_r173_17_control_un_evento_sin_efecto_cambia_de_lote(http_client, esc):
    alimento = await _alta(http_client, esc, "lr", "feed_registration", 10)
    r = await _put(http_client, esc, "operador", alimento, {"lot_id": esc["lr2"]})
    assert r.status_code == 200, r.text
    assert (await _evento(esc, alimento))["lot_id"] == esc["lr2"]


# ═══════════════════════════════════════════════════════════════════════════
#  R-174 · AC-R174-01 … 05 — el despacho de pollitos es > 0
# ═══════════════════════════════════════════════════════════════════════════

async def test_r174_01_despacho_de_cero_pollitos_se_rechaza_sin_fila(http_client, esc):
    await _alta(http_client, esc, "lh", "birth_registration", 100)
    antes = {"eventos": await _eventos(esc, esc["lh"], "chick_dispatch"),
             "auditoria": await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"]),
             "notificaciones": await _cuenta(esc, "SELECT count(*) FROM notifications WHERE company_id = :a", a=esc["a"])}
    r = await _op(http_client, esc, "operador", "lh", "chick_dispatch", 0)
    assert _es_br(r, "BR-04"), ("AC-R174-01: un despacho de 0 pollitos no es un despacho", r.status_code, r.text)
    assert await _eventos(esc, esc["lh"], "chick_dispatch") == antes["eventos"] == 0, "sin fila"
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"]) == antes["auditoria"], "sin auditoría de alta"
    assert await _cuenta(esc, "SELECT count(*) FROM notifications WHERE company_id = :a", a=esc["a"]) == antes["notificaciones"], "sin notificación"
    assert (await _saldos(esc, esc["lh"]))["viables"] == 100


async def test_r174_02_05_negativo_uno_resto_exacto_y_uno_de_mas(http_client, esc):
    await _alta(http_client, esc, "lh", "birth_registration", 100)
    assert (await _op(http_client, esc, "operador", "lh", "chick_dispatch", -1)).status_code == 422, "AC-R174-02: negativo lo rechaza el esquema"
    assert (await _op(http_client, esc, "operador", "lh", "chick_dispatch", 1)).status_code == 201, "AC-R174-03"
    assert (await _saldos(esc, esc["lh"]))["viables"] == 99
    assert (await _op(http_client, esc, "operador", "lh", "chick_dispatch", 99)).status_code == 201, "AC-R174-04: resto exacto"
    assert (await _saldos(esc, esc["lh"]))["viables"] == 0
    assert _es_br(await _op(http_client, esc, "operador", "lh", "chick_dispatch", 1), "BR-04"), "AC-R174-05: uno de más"
    assert await _eventos(esc, esc["lh"], "chick_dispatch") == 2
