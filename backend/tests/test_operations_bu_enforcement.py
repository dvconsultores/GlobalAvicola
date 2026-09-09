"""`GA-REM-040` enmienda G · `R-160` + `R-159` · la unidad de negocio se exige al **operar**.

La fase 3 acotó lecturas y la mutación de lotes; la alta y la edición de eventos, las evidencias,
las alertas y su resolución seguían mirando solo la empresa. Aquí cada superficie se prueba con
control (lo que ya funcionaba) y tratamiento (lo que faltaba) sobre una fixture que siembra la
habilitación de cada unidad **explícitamente** (`BU-D10` no interviene).

    Empresa A   breeder ON · grandparent ON · broiler ON · hatchery OFF (fila explícita)
                lotes LR (breeder) · LG (grandparent) · LP (broiler) · LH (hatchery) · LN (sin tipo)
                eventos ev_r (LR) · ev_g (LG) · ev_h (LH) · evidencias en ev_g y ev_h
                alertas al_r · al_p · al_g · al_h  (al_g es la más reciente)
    Empresa B   breeder ON · lote LB · evento ev_b · alerta al_b
    ACTOR_A     operations:* · concesiones breeder + broiler + hatchery (histórica; la unidad está OFF)
    ACTOR_G     operations:* · concesión grandparent solamente (Progenitoras)
    ACTOR_CERO  operations:* · sin concesiones (OD-09.c)
    ACTOR_B     operations:* en B · breeder
    ACCESO      Administrador de Accesos (OD-15 §6: business_units:* y nada más) · sin concesiones
    GLOBAL      ("*", …, "all") · company_id NULL · se sitúa por reclamación (OD-11)
"""
from __future__ import annotations

import os
import pathlib
import uuid
from datetime import date, datetime, timedelta, timezone

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

PREFIJO = "BUOP-"
CARPETA = pathlib.Path(os.environ.get("MEDIA_DIR", "/tmp")) / "buop_evidencias"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


def _filas(r) -> list[dict]:
    cuerpo = r.json()
    return cuerpo["items"] if isinstance(cuerpo, dict) else cuerpo


def _ids(r) -> set[int]:
    return {f["id"] for f in _filas(r)}


def _es_br(r, regla: str) -> bool:
    return r.status_code == 400 and r.json().get("rule") == regla


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus
    from app.operations.models import (EventStatus, EventType, Evidence, OperationalAlert,
                                       OperationalEvent)

    CARPETA.mkdir(parents=True, exist_ok=True)
    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        assert {"breeder", "grandparent", "hatchery", "broiler"} <= set(unidades)
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "grandparent", True), (a, "broiler", True),
                                  (a, "hatchery", False), (b, "breeder", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        assert hab[(a.id, "hatchery")].is_enabled is False, "precondición: hatchery apagada explícitamente"

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        ops = [("operations", ac) for ac in (PermissionAction.READ, PermissionAction.CREATE,
                                              PermissionAction.UPDATE, PermissionAction.DELETE)] + \
              [("lots", PermissionAction.READ)]
        acceso = [("business_units", ac) for ac in (PermissionAction.READ, PermissionAction.CREATE,
                                                    PermissionAction.UPDATE, PermissionAction.DELETE)]
        rol_a, p_a = _rol("OpA", a.id, ops)
        rol_b, p_b = _rol("OpB", b.id, ops)
        rol_acc, p_acc = _rol("Acceso", a.id, acceso)
        rol_global, _ = _rol("Global", None, [])
        await s.flush()
        for rol, permisos in ((rol_a, p_a), (rol_b, p_b), (rol_acc, p_acc)):
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Buop",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        actor_a, actor_g, actor_cero = _usuario(a.id, "ACTORA", rol_a), _usuario(a.id, "ACTORG", rol_a), _usuario(a.id, "CERO", rol_a)
        actor_b, acc, glob = _usuario(b.id, "ACTORB", rol_b), _usuario(a.id, "ACCESO", rol_acc), _usuario(None, "GLOBAL", rol_global)
        s.add_all([actor_a, actor_g, actor_cero, actor_b, acc, glob])
        await s.flush()
        comodines = (await s.execute(select(Permission).where(
            Permission.role_id == rol_global.id, Permission.module == "*", Permission.scope_type == "all"))).scalars().all()
        assert len(comodines) == len(list(PermissionAction)), "precondición: autoridad global = capacidad, no nombre"

        for code in ("breeder", "broiler", "hatchery"):
            await conceder_unidad(s, user=actor_a, company_business_unit=hab[(a.id, code)])
        await conceder_unidad(s, user=actor_g, company_business_unit=hab[(a.id, "grandparent")])
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

        lr, lg, lp = _lote(a, "LR", BirdTypeEnum.BREEDER), _lote(a, "LG", BirdTypeEnum.GRANDPARENT), _lote(a, "LP", BirdTypeEnum.BROILER)
        lh, ln, lb = _lote(a, "LH", BirdTypeEnum.HATCHERY), _lote(a, "LN", None), _lote(b, "LB", BirdTypeEnum.BREEDER)
        lc = _lote(a, "LC", BirdTypeEnum.BREEDER, LotStatus.CLOSED)  # misma unidad efectiva, cerrado
        s.add_all([lr, lg, lp, lh, ln, lb, lc])
        await s.flush()

        def _evento(empresa, lote, autor):
            return OperationalEvent(company_id=empresa.id, lot_id=lote.id, event_type=EventType.FARM_INSPECTION,
                                    event_date=date.today(), status=EventStatus.REGISTERED,
                                    registered_by_id=autor.id, version=1,
                                    observations=f"{PREFIJO}EVENTO-{lote.lot_code}")

        ev_r, ev_g, ev_h, ev_b = _evento(a, lr, actor_a), _evento(a, lg, actor_g), _evento(a, lh, actor_a), _evento(b, lb, actor_b)
        ev_h2 = _evento(a, lh, actor_a)  # para cancelar sin consumir el que `submit` necesita
        s.add_all([ev_r, ev_g, ev_h, ev_h2, ev_b])
        await s.flush()

        def _evidencia(empresa, evento, autor, marca):
            ruta = CARPETA / f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}.txt"
            ruta.write_text(f"{PREFIJO}CONTENIDO-{marca}")
            return Evidence(event_id=evento.id, company_id=empresa.id, file_name=ruta.name, file_path=str(ruta),
                            file_size=ruta.stat().st_size, mime_type="text/plain", evidence_type="document",
                            uploaded_by_id=autor.id)

        evi_g, evi_h, evi_r = _evidencia(a, ev_g, actor_g, "G"), _evidencia(a, ev_h, actor_a, "H"), _evidencia(a, ev_r, actor_a, "R")
        s.add_all([evi_g, evi_h, evi_r])

        ahora = datetime.now(timezone.utc)

        def _alerta(empresa, lote, marca, hace):
            return OperationalAlert(company_id=empresa.id, lot_id=lote.id, alert_type="high_mortality",
                                    severity="warning", message=f"{PREFIJO}ALERTA-{marca}", is_resolved=False,
                                    created_at=ahora - timedelta(minutes=hace))

        al_r, al_p, al_h, al_b = _alerta(a, lr, "R", 40), _alerta(a, lp, "P", 30), _alerta(a, lh, "H", 20), _alerta(b, lb, "B", 10)
        al_g = _alerta(a, lg, "G", 0)  # la más reciente de A, en una unidad que ACTOR_A no alcanza
        s.add_all([al_r, al_p, al_h, al_b, al_g])
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "actor_a": actor_a.id, "actor_g": actor_g.id, "actor_cero": actor_cero.id,
             "actor_b": actor_b.id, "acceso": acc.id, "global": glob.id,
             "granja_a": granja_a.id, "galpon_a": galpon_a.id, "granja_b": granja_b.id, "galpon_b": galpon_b.id,
             "lr": lr.id, "lg": lg.id, "lp": lp.id, "lh": lh.id, "ln": ln.id, "lb": lb.id, "lc": lc.id,
             "ev_r": ev_r.id, "ev_g": ev_g.id, "ev_h": ev_h.id, "ev_h2": ev_h2.id, "ev_b": ev_b.id,
             "evi_g": evi_g.id, "evi_h": evi_h.id, "evi_r": evi_r.id, "ruta_evi_g": str(evi_g.file_path),
             "al_r": al_r.id, "al_p": al_p.id, "al_g": al_g.id, "al_h": al_h.id, "al_b": al_b.id,
             "url": test_database_url}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM evidences WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM inspection_details WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
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
    for f in CARPETA.glob(f"{PREFIJO}*"):
        try:
            f.unlink()
        except OSError:
            pass
    await motor.dispose()


# ── helpers ────────────────────────────────────────────────────────────────

def _recepcion(esc, lote, n=10, *, granja="granja_a", galpon="galpon_a"):
    cuerpo = {"lot_id": lote, "event_type": "bird_reception", "event_date": recent_event_date(),
              "farm_id": esc[granja], "house_id": esc[galpon], "bird_movements": [{"sex": "mixed", "quantity": n}]}
    if lote in (esc["lr"], esc["lb"], esc["lc"]):  # `GA-REM-021-B` (`B01`): cuadre de reproductoras (solo setup)
        cuerpo.update({"received_total": n, "dead_on_arrival": 0, "rejected_on_arrival": 0})
    return cuerpo


def _inspeccion_sin_lote(esc):
    return {"event_type": "farm_inspection", "event_date": recent_event_date(),
            "farm_id": esc["granja_a"], "house_id": esc["galpon_a"], "observations": f"{PREFIJO}SIN-LOTE"}


async def _crear(http_client, esc, actor, cuerpo, company_id=None):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=cuerpo)


async def _cuenta(esc, sql: str, **params) -> int:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return int((await s.execute(text(sql), params)).scalar() or 0)
    finally:
        await motor.dispose()


async def _eventos_del_lote(esc, lote) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l", l=lote)


async def _saldo(esc, lote) -> int:
    from app.operations.validators import get_current_bird_balance
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return await get_current_bird_balance(s, lote)
    finally:
        await motor.dispose()


async def _lote_del_evento(esc, evento) -> int | None:
    return await _cuenta(esc, "SELECT lot_id FROM operational_events WHERE id = :e", e=evento) or None


async def _sin_efectos(esc, lote, antes_eventos, antes_saldo):
    assert await _eventos_del_lote(esc, lote) == antes_eventos, "AC-W11: no debe quedar fila"
    assert await _saldo(esc, lote) == antes_saldo, "AC-W11: el saldo no cambia"


# ═══════════════════════════════════════════════════════════════════════════
#  R-160 · escritura · AC-W01…W15
# ═══════════════════════════════════════════════════════════════════════════

async def test_w01_control_el_actor_crea_sobre_lote_de_su_unidad_efectiva(http_client, esc):
    r = await _crear(http_client, esc, "actor_a", _recepcion(esc, esc["lr"]))
    assert r.status_code == 201, r.text
    assert r.json()["lot_id"] == esc["lr"]
    assert await _saldo(esc, esc["lr"]) == 10


async def test_w02_la_unidad_apagada_bloquea_aunque_haya_concesion_historica(http_client, esc):
    antes, saldo = await _eventos_del_lote(esc, esc["lh"]), await _saldo(esc, esc["lh"])
    r = await _crear(http_client, esc, "actor_a", _recepcion(esc, esc["lh"]))
    assert _es_br(r, "BR-07"), r.text
    await _sin_efectos(esc, esc["lh"], antes, saldo)


async def test_w03_la_unidad_habilitada_sin_concesion_bloquea(http_client, esc):
    antes, saldo = await _eventos_del_lote(esc, esc["lg"]), await _saldo(esc, esc["lg"])
    r = await _crear(http_client, esc, "actor_a", _recepcion(esc, esc["lg"]))
    assert _es_br(r, "BR-07"), r.text
    await _sin_efectos(esc, esc["lg"], antes, saldo)


async def test_w03b_cero_unidades_efectivas_no_opera_dato_productivo(http_client, esc):
    antes, saldo = await _eventos_del_lote(esc, esc["lr"]), await _saldo(esc, esc["lr"])
    r = await _crear(http_client, esc, "actor_cero", _recepcion(esc, esc["lr"]))
    assert _es_br(r, "BR-07"), r.text
    await _sin_efectos(esc, esc["lr"], antes, saldo)


async def test_w03b_cero_unidades_efectivas_tampoco_crea_dato_pendiente(http_client, esc):
    antes = await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE company_id = :c AND lot_id IS NULL", c=esc["a"])
    r = await _crear(http_client, esc, "actor_cero", _inspeccion_sin_lote(esc))
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE company_id = :c AND lot_id IS NULL", c=esc["a"]) == antes


async def test_w03c_control_con_una_unidad_efectiva_el_dato_pendiente_se_crea(http_client, esc):
    r = await _crear(http_client, esc, "actor_a", _inspeccion_sin_lote(esc))
    assert r.status_code == 201, r.text
    assert r.json()["lot_id"] is None


async def test_w04_control_el_lote_de_otra_empresa_no_existe(http_client, esc):
    antes = await _eventos_del_lote(esc, esc["lb"])
    r = await _crear(http_client, esc, "actor_a", _recepcion(esc, esc["lb"], granja="granja_b", galpon="galpon_b"))
    assert _es_br(r, "BR-07"), r.text
    assert await _eventos_del_lote(esc, esc["lb"]) == antes


async def test_w05_progenitoras_el_actor_de_abuelas_no_escribe_en_reproductoras(http_client, esc):
    antes, saldo = await _eventos_del_lote(esc, esc["lr"]), await _saldo(esc, esc["lr"])
    r = await _crear(http_client, esc, "actor_g", _recepcion(esc, esc["lr"]))
    assert _es_br(r, "BR-07"), r.text
    await _sin_efectos(esc, esc["lr"], antes, saldo)


async def test_w05_progenitoras_control_el_actor_de_abuelas_escribe_en_abuelas(http_client, esc):
    r = await _crear(http_client, esc, "actor_g", _recepcion(esc, esc["lg"]))
    assert r.status_code == 201, r.text
    assert await _saldo(esc, esc["lg"]) == 10


async def test_w06_control_el_evento_de_unidad_no_alcanzable_no_se_edita(http_client, esc):
    r = await http_client.put(f"/api/v1/operations/{esc['ev_g']}", headers=_token(esc["actor_a"]),
                              json={"observations": "intruso"})
    assert r.status_code == 404, r.text


async def test_w06b_la_evidencia_de_un_evento_de_unidad_no_alcanzable_no_se_borra(http_client, esc):
    r = await http_client.delete(f"/api/v1/operations/{esc['ev_g']}/evidences/{esc['evi_g']}", headers=_token(esc["actor_a"]))
    assert r.status_code == 404, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM evidences WHERE id = :i", i=esc["evi_g"]) == 1
    assert pathlib.Path(esc["ruta_evi_g"]).exists()


async def test_w07_control_el_evento_propio_se_edita(http_client, esc):
    r = await http_client.put(f"/api/v1/operations/{esc['ev_r']}", headers=_token(esc["actor_a"]),
                              json={"observations": f"{PREFIJO}editado"})
    assert r.status_code == 200, r.text
    assert r.json()["observations"] == f"{PREFIJO}editado"


async def test_w09_la_edicion_no_repunta_el_evento_a_un_lote_de_otra_unidad(http_client, esc):
    r = await http_client.put(f"/api/v1/operations/{esc['ev_r']}", headers=_token(esc["actor_a"]),
                              json={"lot_id": esc["lg"]})
    assert _es_br(r, "BR-07"), r.text
    assert await _lote_del_evento(esc, esc["ev_r"]) == esc["lr"], "el evento no cambia"


async def test_w09_la_edicion_no_repunta_el_evento_a_un_lote_de_otra_empresa(http_client, esc):
    r = await http_client.put(f"/api/v1/operations/{esc['ev_r']}", headers=_token(esc["actor_a"]),
                              json={"lot_id": esc["lb"]})
    assert _es_br(r, "BR-07"), r.text
    assert await _lote_del_evento(esc, esc["ev_r"]) == esc["lr"]


async def test_w09_la_edicion_no_repunta_el_evento_a_un_lote_cerrado(http_client, esc):
    """`§G.4`: el destino de una edición se verifica como el de un alta — `validate_lot_active` incluido.

    La sensibilidad `S4b` (sin `validate_lot_active` en la edición) sobrevivía: la guarda de unidad ya
    cubre la empresa, y el estado del lote era lo único sin prueba."""
    r = await http_client.put(f"/api/v1/operations/{esc['ev_r']}", headers=_token(esc["actor_a"]),
                              json={"lot_id": esc["lc"]})
    assert _es_br(r, "BR-07") and "no está activo" in r.json()["detail"], r.text
    assert await _lote_del_evento(esc, esc["ev_r"]) == esc["lr"]


async def test_w09_la_edicion_no_repunta_la_ubicacion_a_otra_empresa(http_client, esc):
    r = await http_client.put(f"/api/v1/operations/{esc['ev_r']}", headers=_token(esc["actor_a"]),
                              json={"farm_id": esc["granja_b"], "house_id": esc["galpon_b"]})
    assert _es_br(r, "BR-07"), r.text
    assert await _cuenta(esc, "SELECT coalesce(farm_id, 0) FROM operational_events WHERE id = :e", e=esc["ev_r"]) == 0


async def test_w10_control_el_administrador_de_accesos_no_opera(http_client, esc):
    antes = await _eventos_del_lote(esc, esc["lr"])
    r = await _crear(http_client, esc, "acceso", _recepcion(esc, esc["lr"]))
    assert r.status_code == 403, r.text
    assert await _eventos_del_lote(esc, esc["lr"]) == antes


async def test_w12_control_la_autoridad_global_sin_contexto_no_crea(http_client, esc):
    antes = await _eventos_del_lote(esc, esc["lr"])
    r = await _crear(http_client, esc, "global", _recepcion(esc, esc["lr"]))
    assert _es_br(r, "BR-07"), r.text
    r = await _crear(http_client, esc, "global", _recepcion(esc, esc["lr"]), company_id=esc["b"])
    assert _es_br(r, "BR-07"), r.text
    assert await _eventos_del_lote(esc, esc["lr"]) == antes


async def test_w13_la_autoridad_global_situada_no_crea_sobre_unidad_apagada(http_client, esc):
    antes, saldo = await _eventos_del_lote(esc, esc["lh"]), await _saldo(esc, esc["lh"])
    r = await _crear(http_client, esc, "global", _recepcion(esc, esc["lh"]), company_id=esc["a"])
    assert r.status_code == 403, r.text
    await _sin_efectos(esc, esc["lh"], antes, saldo)


async def test_w13_submit_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    r = await http_client.post(f"/api/v1/operations/{esc['ev_h']}/submit", headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE id = :e AND upper(status::text) = 'REGISTERED'", e=esc["ev_h"]) == 1


async def test_w13_cancel_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    r = await http_client.post(f"/api/v1/operations/{esc['ev_h2']}/cancel", headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE id = :e AND upper(status::text) = 'REGISTERED'", e=esc["ev_h2"]) == 1


async def test_w13_upload_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    antes = await _cuenta(esc, "SELECT count(*) FROM evidences WHERE event_id = :e", e=esc["ev_h"])
    r = await http_client.post(f"/api/v1/operations/{esc['ev_h']}/evidences", headers=_token(esc["global"], esc["a"]),
                               files={"file": ("foto.png", PNG, "image/png")})
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM evidences WHERE event_id = :e", e=esc["ev_h"]) == antes


async def test_w13_delete_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    r = await http_client.delete(f"/api/v1/operations/{esc['ev_h']}/evidences/{esc['evi_h']}", headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM evidences WHERE id = :i", i=esc["evi_h"]) == 1


async def test_w14_control_la_autoridad_global_situada_crea_sobre_unidad_habilitada_sin_concesion(http_client, esc):
    r = await _crear(http_client, esc, "global", _recepcion(esc, esc["lg"]), company_id=esc["a"])
    assert r.status_code == 201, r.text
    assert r.json()["company_id"] == esc["a"]


async def test_w14_control_la_autoridad_global_situada_transita_y_adjunta_sobre_unidad_habilitada(http_client, esc):
    r = await http_client.post(f"/api/v1/operations/{esc['ev_r']}/evidences", headers=_token(esc["global"], esc["a"]),
                               files={"file": ("foto.png", PNG, "image/png")})
    assert r.status_code == 201, r.text
    r = await http_client.post(f"/api/v1/operations/{esc['ev_r']}/submit", headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 200, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  R-159 · alertas · AC-A01…A13
# ═══════════════════════════════════════════════════════════════════════════

async def _alertas(http_client, esc, actor, company_id=None, **params):
    q = "&".join(f"{k}={v}" for k, v in {"limit": 50, **params}.items())
    return await http_client.get(f"/api/v1/operations/alerts?{q}", headers=_token(esc[actor], company_id))


async def test_a01_a04_el_actor_ve_exactamente_las_alertas_de_sus_unidades_efectivas(http_client, esc):
    r = await _alertas(http_client, esc, "actor_a")
    assert r.status_code == 200, r.text
    assert _ids(r) == {esc["al_r"], esc["al_p"]}, "AC-A01/A04: unión exacta breeder + broiler"


async def test_a02_la_unidad_apagada_con_concesion_historica_no_aporta_alertas(http_client, esc):
    r = await _alertas(http_client, esc, "actor_a")
    assert esc["al_h"] not in _ids(r), "AC-A02: hatchery está OFF aunque ACTOR_A tenga concesión"


async def test_a03_la_unidad_habilitada_sin_concesion_no_aporta_alertas(http_client, esc):
    r = await _alertas(http_client, esc, "actor_a")
    assert esc["al_g"] not in _ids(r), "AC-A03: grandparent está ON pero no concedida"


async def test_a03_progenitoras_el_actor_de_abuelas_ve_solo_las_suyas(http_client, esc):
    r = await _alertas(http_client, esc, "actor_g")
    assert _ids(r) == {esc["al_g"]}


async def test_a05_cero_unidades_efectivas_es_lista_vacia(http_client, esc):
    r = await _alertas(http_client, esc, "actor_cero")
    assert r.status_code == 200, r.text
    assert _filas(r) == []


async def test_a06_control_las_alertas_de_otra_empresa_nunca(http_client, esc):
    r = await _alertas(http_client, esc, "actor_a")
    assert esc["al_b"] not in _ids(r)
    r = await _alertas(http_client, esc, "actor_b")
    assert _ids(r) == {esc["al_b"]}


async def test_a07_el_predicado_precede_a_la_paginacion(http_client, esc):
    r = await _alertas(http_client, esc, "actor_a", limit=1)
    assert r.status_code == 200, r.text
    filas = _filas(r)
    assert len(filas) == 1
    assert filas[0]["id"] in {esc["al_r"], esc["al_p"]}, "con limit=1 la más reciente (al_g, ajena) no debe consumir la página"


async def test_a07_el_filtro_por_lote_no_salta_el_predicado(http_client, esc):
    r = await _alertas(http_client, esc, "actor_a", lot_id=esc["lg"])
    assert r.status_code == 200, r.text
    assert _filas(r) == []


async def test_a08_control_la_autoridad_global_situada_ve_toda_la_empresa(http_client, esc):
    r = await _alertas(http_client, esc, "global", esc["a"])
    assert _ids(r) == {esc["al_r"], esc["al_p"], esc["al_g"], esc["al_h"]}, "visibilidad de control certificada, unidades apagadas incluidas"


async def test_a09_control_la_autoridad_global_sin_contexto_obtiene_cero(http_client, esc):
    r = await _alertas(http_client, esc, "global")
    assert r.status_code == 200 and _filas(r) == []


async def test_a11_control_el_administrador_de_accesos_no_lee_alertas(http_client, esc):
    r = await _alertas(http_client, esc, "acceso")
    assert r.status_code == 403, r.text


async def test_a12_el_contrato_de_respuesta_no_cambia(http_client, esc):
    r = await _alertas(http_client, esc, "actor_a")
    fila = _filas(r)[0]
    assert set(fila) == {"id", "company_id", "lot_id", "event_id", "alert_type", "severity", "message",
                         "threshold_value", "actual_value", "is_resolved", "resolved_at", "created_at"}


async def test_a13_resolver_una_alerta_de_unidad_no_alcanzable_es_404(http_client, esc):
    r = await http_client.patch(f"/api/v1/operations/alerts/{esc['al_g']}/resolve", headers=_token(esc["actor_a"]))
    assert r.status_code == 404, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM operational_alerts WHERE id = :i AND is_resolved = false", i=esc["al_g"]) == 1


async def test_a13_la_autoridad_global_no_resuelve_sobre_unidad_apagada(http_client, esc):
    r = await http_client.patch(f"/api/v1/operations/alerts/{esc['al_h']}/resolve", headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM operational_alerts WHERE id = :i AND is_resolved = false", i=esc["al_h"]) == 1


async def test_a13_control_la_alerta_propia_se_resuelve(http_client, esc):
    r = await http_client.patch(f"/api/v1/operations/alerts/{esc['al_r']}/resolve", headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    assert r.json()["is_resolved"] is True
