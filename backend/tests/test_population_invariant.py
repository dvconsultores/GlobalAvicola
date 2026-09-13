"""`GA-REM-005` enmienda B · `R-130` · el saldo de aves nunca es negativo.

`E.3` define cuatro salidas del saldo (mortalidad, descarte, salida, despacho de pollitos) y el
código solo validaba una contra él. Aquí cada decremento se prueba contra el mismo
`get_current_bird_balance` que usa producción, con control y tratamiento sobre la misma
fixture. Las unidades de negocio se habilitan **explícitamente** (`BU-D10` no interviene).

    Empresa A   breeder ON · grandparent ON · hatchery ON · lotes LR (breeder), LG (grandparent),
                LH (hatchery), LC (breeder, cerrado) · granja + galpón
    Empresa B   breeder ON · lote LB · granja + galpón
    ACTOR_A     operations:create/read · lots:read · concesiones breeder/grandparent/hatchery en A
    ACTOR_B     ídem en B
    SIN_PERM    masters:read solamente (control RBAC)
"""
from __future__ import annotations

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "POPI-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House, Lot,
                                    LotStatus)

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        assert {"breeder", "grandparent", "hatchery"} <= set(unidades)
        hab = {}
        for empresa, code in ((a, "breeder"), (a, "grandparent"), (a, "hatchery"), (b, "breeder")):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id,
                                       is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        assert all(f.is_enabled for f in hab.values()), "precondición: unidades habilitadas explícitamente"

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        completo = [("operations", PermissionAction.READ), ("operations", PermissionAction.CREATE),
                    ("lots", PermissionAction.READ)]
        rol_a, p_a = _rol("OpA", a.id, completo)
        rol_b, p_b = _rol("OpB", b.id, completo)
        rol_sin, p_sin = _rol("SinOps", a.id, [("masters", PermissionAction.READ)])
        await s.flush()
        for rol, permisos in ((rol_a, p_a), (rol_b, p_b), (rol_sin, p_sin)):
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Popi",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        actor_a, actor_b, sin_perm = _usuario(a.id, "ACTORA", rol_a), _usuario(b.id, "ACTORB", rol_b), _usuario(a.id, "SINPERM", rol_sin)
        s.add_all([actor_a, actor_b, sin_perm])
        await s.flush()
        for code in ("breeder", "grandparent", "hatchery"):
            await conceder_unidad(s, user=actor_a, company_business_unit=hab[(a.id, code)])
        await conceder_unidad(s, user=actor_b, company_business_unit=hab[(b.id, "breeder")])

        def _granja(empresa, marca):
            return Farm(company_id=empresa.id, name=f"{PREFIJO}GRANJA-{marca}",
                        code=f"{PREFIJO}G{marca}-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)

        granja_a, granja_b = _granja(a, "A"), _granja(b, "B")
        s.add_all([granja_a, granja_b])
        await s.flush()
        galpon_a = House(farm_id=granja_a.id, name=f"{PREFIJO}GALPON-A", capacity=10_000, is_active=True)
        galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}GALPON-B", capacity=10_000, is_active=True)
        s.add_all([galpon_a, galpon_b])
        await s.flush()

        def _lote(empresa, marca, tipo, estado=LotStatus.ACTIVE):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status=estado, farm_id=None)

        lr, lg, lh = _lote(a, "LR", BirdTypeEnum.BREEDER), _lote(a, "LG", BirdTypeEnum.GRANDPARENT), _lote(a, "LH", BirdTypeEnum.HATCHERY)
        lc = _lote(a, "LC", BirdTypeEnum.BREEDER, LotStatus.CLOSED)
        lb = _lote(b, "LB", BirdTypeEnum.BREEDER)
        s.add_all([lr, lg, lh, lc, lb])
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "actor_a": actor_a.id, "actor_b": actor_b.id, "sin_perm": sin_perm.id,
             "granja_a": granja_a.id, "galpon_a": galpon_a.id, "granja_b": granja_b.id, "galpon_b": galpon_b.id,
             "lr": lr.id, "lg": lg.id, "lh": lh.id, "lc": lc.id, "lb": lb.id, "url": test_database_url}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        await c.execute(text("DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)"), p)
        await c.execute(text("DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)"), p)
        await c.execute(text("DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))"), p)
        await c.execute(text("DELETE FROM hatchery_params WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))"), p)
        await c.execute(text("DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM lots WHERE lot_code LIKE :p"), p)
        await c.execute(text("DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM farms WHERE name LIKE :p"), p)
        await c.execute(text("DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM users WHERE username LIKE :p"), p)
        await c.execute(text("DELETE FROM roles WHERE name LIKE :p"), p)
        await c.execute(text("DELETE FROM companies WHERE name LIKE :p"), p)
    await motor.dispose()


# ── helpers ────────────────────────────────────────────────────────────────

def _cuerpo(esc, lote, tipo, cantidad, *, granja=None, galpon=None, extra=None):
    cuerpo = {"lot_id": lote, "event_type": tipo, "event_date": recent_event_date(),
              "bird_movements": [{"sex": "mixed", "quantity": cantidad}]}
    if granja is not None:
        cuerpo["farm_id"], cuerpo["house_id"] = granja, galpon
    cuerpo.update(extra or {})
    return cuerpo


async def _recibir(http_client, esc, lote, n, *, actor="actor_a", granja="granja_a", galpon="galpon_a"):
    # `GA-REM-021-B` (`B01`): la recepción de reproductoras declara su cuadre (solo setup; nada que medir aquí)
    cuadre = {"received_total": n, "dead_on_arrival": 0, "rejected_on_arrival": 0} if lote in (esc["lr"], esc["lc"], esc["lb"]) else None
    r = await http_client.post("/api/v1/operations", headers=_token(esc[actor]),
                               json=_cuerpo(esc, lote, "bird_reception", n, granja=esc[granja], galpon=esc[galpon], extra=cuadre))
    assert r.status_code == 201, r.text
    return r.json()


async def _decremento(http_client, esc, lote, tipo, n, *, actor="actor_a", granja=None, galpon=None, extra=None):
    kwargs = {}
    if tipo == "bird_exit":  # la salida es evento de ubicación (`BR-08`)
        kwargs = {"granja": esc[granja or "granja_a"], "galpon": esc[galpon or "galpon_a"]}
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor]),
                                  json=_cuerpo(esc, lote, tipo, n, extra=extra, **kwargs))


async def _saldo(esc, lote) -> int:
    """El mismo cálculo que producción: `validators.get_current_bird_balance`."""
    from app.operations.validators import get_current_bird_balance
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return await get_current_bird_balance(s, lote)
    finally:
        await motor.dispose()


async def _cuenta(esc, sql: str, **params) -> int:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return int((await s.execute(text(sql), params)).scalar() or 0)
    finally:
        await motor.dispose()


def _es_br(r, regla: str) -> bool:
    return r.status_code == 400 and r.json().get("rule") == regla


# ── AC-R130-01 · happy · AC-R130-02 · límites ──────────────────────────────

async def test_ac01_descarte_y_salida_dentro_del_saldo_se_registran(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    assert (await _decremento(http_client, esc, esc["lr"], "cull_recording", 10)).status_code == 201
    assert (await _decremento(http_client, esc, esc["lr"], "bird_exit", 40)).status_code == 201
    assert await _saldo(esc, esc["lr"]) == 50


async def test_ac02_limite_inferior_y_saldo_exacto(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    assert (await _decremento(http_client, esc, esc["lr"], "cull_recording", 1)).status_code == 201
    assert (await _decremento(http_client, esc, esc["lr"], "cull_recording", 99)).status_code == 201, "descarte = saldo debe pasar"
    assert await _saldo(esc, esc["lr"]) == 0
    r = await _decremento(http_client, esc, esc["lr"], "cull_recording", 1)
    assert _es_br(r, "BR-01"), f"con saldo 0 un descarte de 1 debe rechazarse: {r.status_code} {r.text}"
    assert await _saldo(esc, esc["lr"]) == 0, "el saldo quedó negativo"


# ── AC-R130-03 · sobre el saldo (tratamiento) ──────────────────────────────

async def test_ac03_descarte_sobre_el_saldo_se_rechaza(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    r = await _decremento(http_client, esc, esc["lr"], "cull_recording", 101)
    assert _es_br(r, "BR-01"), f"{r.status_code} {r.text}"
    assert "100" in r.json()["detail"], "el mensaje debe traer el saldo real"
    assert await _saldo(esc, esc["lr"]) == 100


async def test_ac03_salida_sobre_el_saldo_se_rechaza(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    r = await _decremento(http_client, esc, esc["lr"], "bird_exit", 101)
    assert _es_br(r, "BR-01"), f"{r.status_code} {r.text}"
    assert await _saldo(esc, esc["lr"]) == 100


async def test_ac03_control_la_mortalidad_ya_se_rechazaba(http_client, esc):
    """Control: `BR-01` de mortalidad vigente antes de la enmienda (`AC-R130-13`)."""
    await _recibir(http_client, esc, esc["lr"], 100)
    r = await _decremento(http_client, esc, esc["lr"], "mortality_recording", 101)
    assert _es_br(r, "BR-01") and "excede el saldo" in r.json()["detail"], r.text


# ── AC-R130-04 · cero y negativo ───────────────────────────────────────────

@pytest.mark.parametrize("tipo", ["cull_recording", "bird_exit"])
async def test_ac04_cantidad_cero_se_rechaza(http_client, esc, tipo):
    await _recibir(http_client, esc, esc["lr"], 100)
    r = await _decremento(http_client, esc, esc["lr"], tipo, 0)
    assert _es_br(r, "BR-01"), f"{tipo} de cero aves aceptado: {r.status_code} {r.text}"


async def test_ac04_control_cantidad_negativa_la_rechaza_el_esquema(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    r = await _decremento(http_client, esc, esc["lr"], "cull_recording", -5)
    assert r.status_code == 422, r.text


# ── AC-R130-05 · sin efectos colaterales tras un rechazo ───────────────────

async def test_ac05_un_rechazo_no_deja_rastro(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    eventos = "SELECT count(*) FROM operational_events WHERE lot_id = :l"
    movimientos = ("SELECT count(*) FROM bird_movements WHERE event_id IN "
                   "(SELECT id FROM operational_events WHERE lot_id = :l)")
    auditoria = "SELECT count(*) FROM audit_logs WHERE company_id = :c"
    alertas = "SELECT count(*) FROM operational_alerts WHERE lot_id = :l"
    antes = tuple([await _cuenta(esc, eventos, l=esc["lr"]), await _cuenta(esc, movimientos, l=esc["lr"]),
                   await _cuenta(esc, auditoria, c=esc["a"]), await _cuenta(esc, alertas, l=esc["lr"])])
    r = await _decremento(http_client, esc, esc["lr"], "cull_recording", 500, extra={"observations": f"{PREFIJO}RECHAZADO"})
    assert _es_br(r, "BR-01"), f"{r.status_code} {r.text}"
    despues = tuple([await _cuenta(esc, eventos, l=esc["lr"]), await _cuenta(esc, movimientos, l=esc["lr"]),
                     await _cuenta(esc, auditoria, c=esc["a"]), await _cuenta(esc, alertas, l=esc["lr"])])
    assert despues == antes, f"un rechazo escribió algo: antes {antes} · después {despues}"
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE observations = :o", o=f"{PREFIJO}RECHAZADO") == 0
    assert await _saldo(esc, esc["lr"]) == 100


# ── AC-R130-06 · secuencia · AC-R130-07 · cancelación ──────────────────────

async def test_ac06_la_secuencia_completa_cuadra_y_el_saldo_cero_cierra(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    assert (await _decremento(http_client, esc, esc["lr"], "mortality_recording", 30)).status_code == 201
    assert (await _decremento(http_client, esc, esc["lr"], "cull_recording", 30)).status_code == 201
    assert (await _decremento(http_client, esc, esc["lr"], "bird_exit", 40)).status_code == 201
    assert await _saldo(esc, esc["lr"]) == 0
    r = await _decremento(http_client, esc, esc["lr"], "bird_exit", 1)
    assert _es_br(r, "BR-01"), f"{r.status_code} {r.text}"
    assert await _saldo(esc, esc["lr"]) == 0


async def test_ac07_cancelar_un_descarte_devuelve_el_saldo(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    descarte = await _decremento(http_client, esc, esc["lr"], "cull_recording", 30)
    assert descarte.status_code == 201
    assert await _saldo(esc, esc["lr"]) == 70
    cancel = await http_client.post(f"/api/v1/operations/{descarte.json()['id']}/cancel", headers=_token(esc["actor_a"]))
    assert cancel.status_code == 200, cancel.text
    assert await _saldo(esc, esc["lr"]) == 100
    assert (await _decremento(http_client, esc, esc["lr"], "bird_exit", 100)).status_code == 201


# ── AC-R130-08 · Progenitoras, de forma independiente ──────────────────────

async def test_ac08_progenitoras_mismo_invariante(http_client, esc):
    await _recibir(http_client, esc, esc["lg"], 60)
    assert (await _decremento(http_client, esc, esc["lg"], "cull_recording", 60)).status_code == 201
    assert await _saldo(esc, esc["lg"]) == 0
    r = await _decremento(http_client, esc, esc["lg"], "bird_exit", 1)
    assert _es_br(r, "BR-01"), f"progenitoras: {r.status_code} {r.text}"
    assert await _saldo(esc, esc["lg"]) == 0


async def test_ac08_progenitoras_descarte_sobre_el_saldo(http_client, esc):
    await _recibir(http_client, esc, esc["lg"], 60)
    r = await _decremento(http_client, esc, esc["lg"], "cull_recording", 61)
    assert _es_br(r, "BR-01"), f"progenitoras: {r.status_code} {r.text}"
    assert await _saldo(esc, esc["lg"]) == 60


# ── AC-R130-09 · incubación: el viable descuenta mortalidad y descartes ─────

async def test_ac09_el_despacho_de_pollitos_no_supera_los_viables_reales(http_client, esc):
    r = await http_client.post("/api/v1/operations", headers=_token(esc["actor_a"]),
                               json=_cuerpo(esc, esc["lh"], "birth_registration", 100,
                                            extra={"chicks_healthy": 100, "chicks_weak": 0}))  # `B13`, solo setup
    assert r.status_code == 201, r.text
    assert (await _decremento(http_client, esc, esc["lh"], "mortality_recording", 10)).status_code == 201
    assert (await _decremento(http_client, esc, esc["lh"], "cull_recording", 5)).status_code == 201
    assert await _saldo(esc, esc["lh"]) == 85
    r = await http_client.post("/api/v1/operations", headers=_token(esc["actor_a"]),
                               json=_cuerpo(esc, esc["lh"], "chick_dispatch", 90, granja=esc["granja_a"], galpon=esc["galpon_a"]))
    assert _es_br(r, "BR-04"), f"despacho de 90 con 85 viables aceptado: {r.status_code} {r.text}"
    assert await _saldo(esc, esc["lh"]) == 85
    r = await http_client.post("/api/v1/operations", headers=_token(esc["actor_a"]),
                               json=_cuerpo(esc, esc["lh"], "chick_dispatch", 85, granja=esc["granja_a"], galpon=esc["galpon_a"]))
    assert r.status_code == 201, r.text
    assert await _saldo(esc, esc["lh"]) == 0
    r = await http_client.post("/api/v1/operations", headers=_token(esc["actor_a"]),
                               json=_cuerpo(esc, esc["lh"], "chick_dispatch", 1, granja=esc["granja_a"], galpon=esc["galpon_a"]))
    assert _es_br(r, "BR-04"), f"{r.status_code} {r.text}"


# ── AC-R130-10 · concurrencia ──────────────────────────────────────────────

async def test_ac10_tres_descartes_concurrentes_no_bajan_de_cero(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    respuestas = await asyncio.gather(*[
        _decremento(http_client, esc, esc["lr"], "cull_recording", 60) for _ in range(3)
    ])
    codigos = sorted(r.status_code for r in respuestas)
    saldo = await _saldo(esc, esc["lr"])
    assert saldo >= 0, f"decrementos concurrentes dejaron el saldo en {saldo} · códigos {codigos}"
    assert codigos == [201, 400, 400], f"solo cabe un descarte de 60 en 100: {codigos} · saldo {saldo}"
    assert saldo == 40


# ── AC-R130-11 · idempotencia · AC-R130-12 · controles ─────────────────────

async def test_ac11_la_misma_clave_de_idempotencia_decrementa_una_sola_vez(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    clave = f"{PREFIJO}{uuid.uuid4().hex}"
    r1 = await _decremento(http_client, esc, esc["lr"], "cull_recording", 10, extra={"idempotency_key": clave})
    r2 = await _decremento(http_client, esc, esc["lr"], "cull_recording", 10, extra={"idempotency_key": clave})
    assert r1.status_code == 201 and r2.status_code == 201 and r1.json()["id"] == r2.json()["id"]
    assert await _saldo(esc, esc["lr"]) == 90


async def test_ac12_control_lote_ajeno(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    r = await _decremento(http_client, esc, esc["lr"], "cull_recording", 10, actor="actor_b")
    assert _es_br(r, "BR-07"), f"{r.status_code} {r.text}"
    assert await _saldo(esc, esc["lr"]) == 100


async def test_ac12_control_ubicacion_ajena_en_la_salida(http_client, esc):
    await _recibir(http_client, esc, esc["lr"], 100)
    r = await _decremento(http_client, esc, esc["lr"], "bird_exit", 10, granja="granja_b", galpon="galpon_b")
    assert _es_br(r, "BR-07"), f"{r.status_code} {r.text}"


async def test_ac12_control_lote_cerrado(http_client, esc):
    r = await _decremento(http_client, esc, esc["lc"], "cull_recording", 1)
    assert _es_br(r, "BR-07"), f"{r.status_code} {r.text}"


async def test_ac12_control_sin_permiso(http_client, esc):
    r = await _decremento(http_client, esc, esc["lr"], "cull_recording", 1, actor="sin_perm")
    assert r.status_code == 403, r.text


# ── AC-R130-14 · sin migración ni rutas nuevas ─────────────────────────────

def test_ac14_sin_migracion_ni_rutas_nuevas():
    import pathlib
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from app.authorization_coverage import enumerar_rutas
    from app.main import app
    raiz = pathlib.Path(__file__).resolve().parents[1]
    # GA-GOV-03 (T1) fijó la cabeza en `y5z6a7b8c9d0` (catálogo de unidades,
    # `GA-FE-02-C §2`); `GA-REM-003` · AC04 la avanzó a `z6a7b8c9d0e1` (denylist del
    # logout). Cabeza única, fijada; recuentos exactos, nunca `>=`.
    cabezas = ScriptDirectory.from_config(Config(str(raiz / "alembic.ini"))).get_heads()
    assert len(cabezas) == 1, cabezas
    assert cabezas == ["z6a7b8c9d0e1"], cabezas
    # y hay una ruta nueva de `GA-REM-003` · AC04 (`/api/v1/logout`), 211 → 212.
    assert sum(1 for p, _, _ in enumerar_rutas(app) if p.startswith("/api/")) == 212
