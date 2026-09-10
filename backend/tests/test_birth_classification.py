"""`GA-REM-021` enmienda C · `B13` sanos/débiles al nacer (`Bases` p.9) + `R-170` una sola contabilidad de nacimientos
(`GA-REM-005` enmienda C · `BR-21`).

Escenario (prefijo `NACER-`):
    empresa A   hatchery ON · breeder ON            empresa B   hatchery OFF · breeder ON
    operador    operations:create/read/update · hatchery + breeder
    corrector   corrections:correct/read
    sin_perm / acceso (Administrador de Accesos) / lectura (control transversal) · actor_b · global (comodín, sin empresa)
    lotes       lh (A, hatchery) · lh2 (A, hatchery) · lr (A, breeder) · lhb (B, hatchery)
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

PREFIJO = "NACER-"


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
    from app.masters.models import BirdTypeEnum, Company, Lot, LotStatus

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "hatchery", True), (a, "breeder", True), (b, "hatchery", False), (b, "breeder", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ), ("reports", PA.READ)]
        roles = {
            "operador": _rol("Op", a.id, ops),
            "corrector": _rol("Corr", a.id, [("corrections", PA.CORRECT), ("corrections", PA.READ), ("operations", PA.READ)]),
            "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]),
            "lectura": _rol("Lectura", a.id, [("review", PA.READ), ("corrections", PA.READ), ("audit", PA.READ), ("reports", PA.READ), ("operations", PA.READ)]),
            "acceso": _rol("Acceso", a.id, [("business_units", PA.READ), ("business_units", PA.CREATE), ("business_units", PA.UPDATE), ("business_units", PA.DELETE)]),
            "b": _rol("OpB", b.id, ops),
            "global": _rol("Global", None, []),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Nacer", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {"operador": _usuario(a.id, "OP", roles["operador"][0]), "corrector": _usuario(a.id, "CORR", roles["corrector"][0]),
             "sin_perm": _usuario(a.id, "SINPERM", roles["sin_perm"][0]), "lectura": _usuario(a.id, "LECT", roles["lectura"][0]),
             "acceso": _usuario(a.id, "ACC", roles["acceso"][0]), "actor_b": _usuario(b.id, "B", roles["b"][0]),
             "global": _usuario(None, "GLOBAL", roles["global"][0])}
        s.add_all(u.values())
        await s.flush()
        for k in ("operador", "corrector", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "hatchery")])
        await conceder_unidad(s, user=u["operador"], company_business_unit=hab[(a.id, "breeder")])
        for code in ("hatchery", "breeder"):
            await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, code)])

        def _lote(empresa, marca, tipo):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE)

        lotes = {"lh": _lote(a, "LH", BirdTypeEnum.HATCHERY), "lh2": _lote(a, "LH2", BirdTypeEnum.HATCHERY), "lh3": _lote(a, "LH3", BirdTypeEnum.HATCHERY),
                 "lr": _lote(a, "LR", BirdTypeEnum.BREEDER), "lhb": _lote(b, "LHB", BirdTypeEnum.HATCHERY)}
        s.add_all(lotes.values())
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "url": test_database_url}
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
            "DELETE FROM chick_batches WHERE hatchery_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p) OR destination_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
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


async def _viables(esc, lote) -> int:
    from app.operations.validators import get_viable_chick_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return await get_viable_chick_balance(s, lote)
    finally:
        await motor.dispose()


async def _saldo(esc, lote) -> int:
    from app.operations.validators import get_current_bird_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return await get_current_bird_balance(s, lote)
    finally:
        await motor.dispose()


async def _nacimientos(esc, lote) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE 'birth_registration'", l=lote)


def _cuerpo(esc, lote, filas, sanos=90, debiles=5, **extra):
    cuerpo = {"lot_id": esc[lote], "event_type": "birth_registration", "event_date": recent_event_date(),
              "bird_movements": [{"sex": sexo, "quantity": n} for sexo, n in filas]}
    if sanos is not None:
        cuerpo["chicks_healthy"] = sanos
    if debiles is not None:
        cuerpo["chicks_weak"] = debiles
    cuerpo.update(extra)
    return cuerpo


async def _nacer(http_client, esc, actor, lote, filas=(("male", 48), ("female", 47)), company_id=None, **kw):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=_cuerpo(esc, lote, filas, **kw))


# ═══════════════════════════════════════════════════════════════════════════
#  R-170 · una sola contabilidad de nacimientos (BR-21)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r170_la_forma_del_formulario_total_mas_desglose_no_duplica_los_nacidos(http_client, esc):
    """La UI emitía «Total nacidos» (mixed) + machos + hembras + «Débiles» (mixed): cuatro filas que el saldo sumaba
    como nacidos (100 + 48 + 47 + 5 = 200). Contrato: una fila por sexo; sin sexar (mixed) excluye las filas sexadas."""
    r = await _nacer(http_client, esc, "operador", "lh", filas=(("mixed", 100), ("male", 48), ("female", 47), ("mixed", 5)), sanos=95, debiles=5)
    assert _es_br(r, "BR-21"), ("R-170: la forma total + desglose debe rechazarse", r.status_code, r.text[:200])
    r = await _nacer(http_client, esc, "operador", "lh", filas=(("mixed", 100), ("male", 48), ("female", 47)), sanos=95, debiles=5)
    assert _es_br(r, "BR-21"), ("mixed + sexadas", r.text[:200])
    r = await _nacer(http_client, esc, "operador", "lh", filas=(("male", 48), ("male", 2), ("female", 47)), sanos=95, debiles=2)
    assert _es_br(r, "BR-21"), ("dos filas del mismo sexo", r.text[:200])
    assert await _nacimientos(esc, esc["lh"]) == 0 and await _viables(esc, esc["lh"]) == 0, "cero efectos"


# ═══════════════════════════════════════════════════════════════════════════
#  B13 · sanos y débiles al nacer
# ═══════════════════════════════════════════════════════════════════════════

async def test_b13_01_10_12_el_nacimiento_declara_sanos_y_debiles_y_los_nacidos_son_la_suma_de_las_filas(http_client, esc):
    r = await _nacer(http_client, esc, "operador", "lh", sanos=90, debiles=5)  # 48 ♂ + 47 ♀ = 95 nacidos
    assert r.status_code == 201, r.text
    ev = r.json()
    assert (ev["chicks_healthy"], ev["chicks_weak"]) == (90, 5), "B13-01: se persisten y se leen"
    fila = (await _sql(esc, "SELECT chicks_healthy, chicks_weak FROM operational_events WHERE id = :e", e=ev["id"]))[0]
    assert tuple(fila) == (90, 5)
    assert await _viables(esc, esc["lh"]) == 95 and await _saldo(esc, esc["lh"]) == 95, "B13-12/13: los nacidos entran una vez; sanos/débiles no son una segunda cuenta"
    # sin sexar: una sola fila mixed
    r = await _nacer(http_client, esc, "operador", "lh2", filas=(("mixed", 60),), sanos=60, debiles=0)
    assert r.status_code == 201, r.text
    assert await _viables(esc, esc["lh2"]) == 60
    # KPI: los nacidos del reporte (que cuenta solo lo aprobado) son 95, no una suma inflada
    motor = create_async_engine(esc["url"])
    async with motor.begin() as c:
        await c.execute(text("UPDATE operational_events SET status = 'APPROVED' WHERE id = :e"), {"e": ev["id"]})
    await motor.dispose()
    k = await http_client.get(f"/api/v1/reports/kpis/hatchery?lot_id={esc['lh']}", headers=_token(esc["operador"]))
    assert k.status_code == 200, k.text
    assert k.json().get("total_chicks_born") == 95, k.json()


async def test_b13_02_03_04_cantidades_enteras_no_negativas_y_acotadas_por_los_nacidos(http_client, esc):
    for malo in ({"sanos": -1}, {"debiles": -1}, {"sanos": 3.5}, {"sanos": "muchos"}):
        r = await _nacer(http_client, esc, "operador", "lh", **malo)
        assert r.status_code == 422, ("B13-02", malo, r.text[:160])
    r = await _nacer(http_client, esc, "operador", "lh", sanos=91, debiles=5)  # 96 > 95
    assert _es_br(r, "BR-21"), ("B13-03/04: sanos + débiles no pueden superar los nacidos", r.text[:200])
    r = await _nacer(http_client, esc, "operador", "lh", sanos=90, debiles=5, filas=(("male", 0), ("female", 0)))
    assert _es_br(r, "BR-21"), ("un nacimiento sin nacidos no es un nacimiento", r.text[:200])
    for faltante in ({"sanos": None}, {"debiles": None}):
        r = await _nacer(http_client, esc, "operador", "lh", **faltante)
        assert _es_br(r, "BR-21"), ("B13: sanos y débiles se declaran explícitamente (Bases p.9)", faltante, r.text[:200])
    r = await _nacer(http_client, esc, "operador", "lh", sanos=95, debiles=0)  # partición completa: válida
    assert r.status_code == 201, r.text
    r = await _nacer(http_client, esc, "operador", "lh2", sanos=80, debiles=5)  # 85 ≤ 95: clasificación incompleta admitida (AOD-23)
    assert r.status_code == 201, r.text
    assert await _nacimientos(esc, esc["lh"]) == 1


async def test_b13_15_solo_el_nacimiento_en_incubadora_lleva_sanos_y_debiles(http_client, esc):
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json={
        "lot_id": esc["lh"], "event_type": "chick_dispatch", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1}], "chicks_healthy": 1, "chicks_weak": 0})
    assert r.status_code == 400, ("otro tipo de evento", r.text[:200])
    r = await _nacer(http_client, esc, "operador", "lr")  # lote de reproductoras: B13 no aplica por fuente
    assert r.status_code == 400, ("lote que no es de incubadora", r.text[:200])
    assert await _nacimientos(esc, esc["lh"]) == 0 and await _nacimientos(esc, esc["lr"]) == 0


async def test_b13_05_09_cadena_de_seguridad(http_client, esc):
    assert _es_br(await _nacer(http_client, esc, "actor_b", "lh"), "BR-07"), "B13-05: otra empresa"
    assert _es_br(await _nacer(http_client, esc, "global", "lh"), "BR-07"), "B13-09: global sin contexto"
    assert (await _nacer(http_client, esc, "global", "lhb", company_id=esc["b"])).status_code == 403, "B13-06: incubadora apagada en B"
    assert _es_br(await _nacer(http_client, esc, "actor_b", "lhb"), "BR-07"), "B13-06/07: concesión sobre unidad apagada"
    for actor in ("sin_perm", "acceso", "lectura"):
        assert (await _nacer(http_client, esc, actor, "lh")).status_code == 403, ("B13-08", actor)
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json={**_cuerpo(esc, "lh", (("male", 48), ("female", 47))), "company_id": esc["b"], "business_unit_id": 999})
    assert r.status_code == 201 and r.json()["company_id"] == esc["a"], r.text
    assert await _nacimientos(esc, esc["lh"]) == 1 and await _nacimientos(esc, esc["lhb"]) == 0


async def test_b13_11_14_edicion_correccion_y_auditoria(http_client, esc):
    antes = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a", a=esc["a"])
    ev = (await _nacer(http_client, esc, "operador", "lh", sanos=90, debiles=5)).json()
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e AND action::text ILIKE 'created'", e=str(ev["id"])) == 1
    ruta = f"/api/v1/operations/{ev['id']}"
    assert _es_br(await http_client.put(ruta, headers=_token(esc["operador"]), json={"chicks_healthy": 91}), "BR-21"), "edición que supera los nacidos"
    r = await http_client.put(ruta, headers=_token(esc["operador"]), json={"chicks_healthy": 89, "chicks_weak": 6})
    assert r.status_code == 200 and (r.json()["chicks_healthy"], r.json()["chicks_weak"]) == (89, 6), r.text
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                               json={"event_id": ev["id"], "field_name": "chicks_weak", "corrected_value": "7", "reason": f"{PREFIJO}reconteo"})
    assert r.status_code == 400, ("corrección que supera los nacidos (89 + 7 > 95)", r.text[:160])
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                               json={"event_id": ev["id"], "field_name": "chicks_weak", "corrected_value": "4", "reason": f"{PREFIJO}reconteo"})
    assert r.status_code == 201, r.text
    assert (await _sql(esc, "SELECT chicks_weak FROM operational_events WHERE id = :e", e=ev["id"]))[0][0] == 4
    assert await _viables(esc, esc["lh"]) == 95, "ni la edición ni la corrección tocan los nacidos"
    denegada = await _nacer(http_client, esc, "sin_perm", "lh")
    assert denegada.status_code == 403
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a", a=esc["a"]) >= antes + 1
