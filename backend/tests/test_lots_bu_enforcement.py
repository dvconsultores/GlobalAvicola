"""`GA-REM-040` enmienda H · `R-163` + `R-162` · la habilitación de la empresa es absoluta al escribir.

`R-163`: las escrituras de `lots` no exigen la **habilitación** de la unidad a la autoridad global, y
`POST /lots` no exige unidad a nadie. `R-162`: la descarga de evidencia compara la empresa y no la
cadena del evento. Control y tratamiento sobre una fixture que siembra la habilitación de cada unidad
**explícitamente** (`BU-D10` no interviene: nada se reactiva).

    Empresa A   breeder ON · grandparent ON · broiler ON · hatchery OFF (fila explícita)
                lotes LR (breeder) · LG (grandparent) · LH (hatchery) · LN (sin tipo) · eventos y evidencias en LR, LG, LH
    Empresa B   breeder ON · lote LB · evento y evidencia
    ACTOR_A     lots:create/read/update · operations:create/read · concesiones breeder + broiler + hatchery (histórica; OFF)
    ACTOR_G     ídem · solo grandparent (Progenitoras)
    ACTOR_CERO  ídem · sin concesiones (OD-09.c)
    ACTOR_B     ídem en B · breeder
    ACCESO      Administrador de Accesos (OD-15 §6: business_units:* y nada más)
    GLOBAL      ("*", …, "all") · company_id NULL · se sitúa por reclamación (OD-11)
"""
from __future__ import annotations

import os
import pathlib
import uuid
from datetime import date

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

PREFIJO = "BULOT-"
CARPETA = pathlib.Path(os.environ.get("MEDIA_DIR", "/tmp")) / "bulot_evidencias"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


def _filas(r) -> list[dict]:
    cuerpo = r.json()
    return cuerpo["items"] if isinstance(cuerpo, dict) else cuerpo


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus,
                                    ProductivePhase)
    from app.operations.models import EventStatus, EventType, Evidence, OperationalEvent

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

        def _rol(nombre, company_id):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_a, rol_b, rol_acc, rol_global = _rol("Lots", a.id), _rol("LotsB", b.id), _rol("Acceso", a.id), _rol("Global", None)
        await s.flush()
        ops = [("lots", PermissionAction.CREATE), ("lots", PermissionAction.READ), ("lots", PermissionAction.UPDATE),
               ("operations", PermissionAction.CREATE), ("operations", PermissionAction.READ), ("masters", PermissionAction.READ)]
        for rol in (rol_a, rol_b):
            for modulo, accion in ops:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in (PermissionAction.READ, PermissionAction.CREATE, PermissionAction.UPDATE, PermissionAction.DELETE):
            s.add(Permission(role_id=rol_acc.id, module="business_units", action=accion, scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Bulot",
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

        fase = (await s.execute(select(ProductivePhase).limit(1))).scalar_one_or_none()
        if fase is None:
            fase = ProductivePhase(name=f"{PREFIJO}Fase", code=f"BUL{uuid.uuid4().hex[:4]}", order=1, duration_days=10)
            s.add(fase)
            await s.flush()

        def _lote(empresa, marca, tipo):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status=LotStatus.ACTIVE, farm_id=None)

        lr, lg, lh, ln, lb = (_lote(a, "LR", BirdTypeEnum.BREEDER), _lote(a, "LG", BirdTypeEnum.GRANDPARENT),
                              _lote(a, "LH", BirdTypeEnum.HATCHERY), _lote(a, "LN", None), _lote(b, "LB", BirdTypeEnum.BREEDER))
        lh2 = _lote(a, "LH2", BirdTypeEnum.HATCHERY)  # para activate-manual y phases sin tocar LH
        lg2 = _lote(a, "LG2", BirdTypeEnum.GRANDPARENT)  # sin eventos: activate-manual exige un lote sin operaciones
        s.add_all([lr, lg, lh, ln, lb, lh2, lg2])
        await s.flush()

        def _evento(empresa, lote, autor):
            return OperationalEvent(company_id=empresa.id, lot_id=lote.id, event_type=EventType.FARM_INSPECTION,
                                    event_date=date.today(), status=EventStatus.REGISTERED,
                                    registered_by_id=autor.id, version=1, observations=f"{PREFIJO}EVENTO-{lote.lot_code}")

        ev_r, ev_g, ev_h, ev_b = _evento(a, lr, actor_a), _evento(a, lg, actor_g), _evento(a, lh, actor_a), _evento(b, lb, actor_b)
        s.add_all([ev_r, ev_g, ev_h, ev_b])
        await s.flush()

        def _evidencia(empresa, evento, autor, marca):
            ruta = CARPETA / f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}.txt"
            ruta.write_text(f"{PREFIJO}CONTENIDO-{marca}")
            return Evidence(event_id=evento.id, company_id=empresa.id, file_name=ruta.name, file_path=str(ruta),
                            file_size=ruta.stat().st_size, mime_type="text/plain", evidence_type="document",
                            uploaded_by_id=autor.id)

        evi_r, evi_g, evi_h, evi_b = (_evidencia(a, ev_r, actor_a, "R"), _evidencia(a, ev_g, actor_g, "G"),
                                      _evidencia(a, ev_h, actor_a, "H"), _evidencia(b, ev_b, actor_b, "B"))
        s.add_all([evi_r, evi_g, evi_h, evi_b])
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "fase": fase.id,
             "actor_a": actor_a.id, "actor_g": actor_g.id, "actor_cero": actor_cero.id, "actor_b": actor_b.id,
             "acceso": acc.id, "global": glob.id,
             "granja_a": granja_a.id, "galpon_a": galpon_a.id, "granja_b": granja_b.id, "galpon_b": galpon_b.id,
             "lr": lr.id, "lg": lg.id, "lg2": lg2.id, "lh": lh.id, "lh2": lh2.id, "ln": ln.id, "lb": lb.id,
             "ev_r": ev_r.id, "ev_g": ev_g.id, "ev_h": ev_h.id, "ev_b": ev_b.id,
             "evi_r": evi_r.id, "evi_g": evi_g.id, "evi_h": evi_h.id, "evi_b": evi_b.id,
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
            "DELETE FROM feed_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM inspection_details WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM opening_balances WHERE lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM lot_phases WHERE lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM productive_phases WHERE name LIKE :p",  # `GA-REM-015-B` (`R-175`): la fase creada por la fixture se retira
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

def _lote_nuevo(esc, tipo, *, granja=True):
    cuerpo = {"lot_code": f"{PREFIJO}NEW-{uuid.uuid4().hex[:8]}", "sex": "mixed"}
    if tipo is not None:
        cuerpo["bird_type"] = tipo
    if granja:
        cuerpo["farm_id"], cuerpo["house_id"] = esc["granja_a"], esc["galpon_a"]
    return cuerpo


async def _crear(http_client, esc, actor, tipo, company_id=None, **kw):
    return await http_client.post("/api/v1/lots", headers=_token(esc[actor], company_id), json=_lote_nuevo(esc, tipo, **kw))


def _apertura(esc, lote):
    return {"lot_id": lote, "activation_date": date.today().isoformat(), "phase_at_activation_id": esc["fase"],
            "age_days": 10, "initial_male_count": 100, "initial_female_count": 900}


def _fase(esc, lote):
    return {"lot_id": lote, "phase_id": esc["fase"], "start_date": date.today().isoformat()}


async def _cuenta(esc, sql: str, **params) -> int:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return int((await s.execute(text(sql), params)).scalar() or 0)
    finally:
        await motor.dispose()


async def _lotes_nuevos(esc) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM lots WHERE lot_code LIKE :p", p=f"{PREFIJO}NEW-%")


async def _estado(esc, lote) -> str:
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return str((await s.execute(text("SELECT status FROM lots WHERE id = :l"), {"l": lote})).scalar())
    finally:
        await motor.dispose()


async def _cerrable(http_client, esc, cab, lote):
    """`BR-05` (pesaje + alimento) y `R-76` (todo aprobado): lo mínimo para poder cerrar."""
    base = {"lot_id": lote, "farm_id": esc["granja_a"], "house_id": esc["galpon_a"], "event_date": recent_event_date()}
    r = await http_client.post("/api/v1/operations", headers=cab, json={**base, "event_type": "weight_recording",
                               "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 2000}]})
    assert r.status_code == 201, r.text
    r = await http_client.post("/api/v1/operations", headers=cab, json={**base, "event_type": "feed_registration",
                               "feed_movements": [{"quantity_kg": 100.0}]})
    assert r.status_code == 201, r.text
    motor = create_async_engine(esc["url"])
    try:
        async with motor.begin() as c:
            await c.execute(text("UPDATE operational_events SET status = 'APPROVED' WHERE lot_id = :l"), {"l": lote})
    finally:
        await motor.dispose()


# ═══════════════════════════════════════════════════════════════════════════
#  R-163 · escritura de lots · AC-L01…L15
# ═══════════════════════════════════════════════════════════════════════════

async def test_l01_control_el_actor_crea_un_lote_de_su_unidad_efectiva(http_client, esc):
    r = await _crear(http_client, esc, "actor_a", "breeder")
    assert r.status_code == 201, r.text
    assert r.json()["bird_type"] == "breeder" and r.json()["company_id"] == esc["a"]


async def test_l02_la_unidad_habilitada_sin_concesion_no_admite_alta(http_client, esc):
    antes = await _lotes_nuevos(esc)
    r = await _crear(http_client, esc, "actor_a", "grandparent")
    assert r.status_code == 403, r.text
    assert await _lotes_nuevos(esc) == antes, "AC-L13: cero filas"


async def test_l03_la_unidad_apagada_no_admite_alta_aunque_haya_concesion_historica(http_client, esc):
    antes = await _lotes_nuevos(esc)
    r = await _crear(http_client, esc, "actor_a", "hatchery")
    assert r.status_code == 403, r.text
    assert await _lotes_nuevos(esc) == antes


async def test_l04_cero_unidades_efectivas_no_crea_lotes(http_client, esc):
    antes = await _lotes_nuevos(esc)
    r = await _crear(http_client, esc, "actor_cero", "breeder")
    assert r.status_code == 403, r.text
    r = await _crear(http_client, esc, "actor_cero", None)
    assert r.status_code == 403, r.text
    assert await _lotes_nuevos(esc) == antes


async def test_l04_control_con_una_unidad_efectiva_el_lote_sin_cadena_nace_pendiente(http_client, esc):
    r = await _crear(http_client, esc, "actor_a", None)
    assert r.status_code == 201, r.text
    assert r.json()["bird_type"] is None


async def test_l05_la_autoridad_global_sin_contexto_no_crea_lotes(http_client, esc):
    antes = await _lotes_nuevos(esc)
    r = await _crear(http_client, esc, "global", "breeder", granja=False)
    assert r.status_code == 403, r.text
    # `S7` sobrevivía con solo el caso anterior: sin contexto, `habilitadas` es `[]` y la rama
    # «no habilitada» ya denegaba un lote **con** cadena. El lote **sin** cadena (pendiente) es
    # el que solo `OD-14.d` detiene.
    r = await _crear(http_client, esc, "global", None, granja=False)
    assert r.status_code == 403, r.text
    assert await _lotes_nuevos(esc) == antes


async def test_l06_control_la_autoridad_global_situada_crea_en_unidad_habilitada_sin_concesion(http_client, esc):
    r = await _crear(http_client, esc, "global", "grandparent", company_id=esc["a"])
    assert r.status_code == 201, r.text
    assert r.json()["company_id"] == esc["a"]


async def test_l07_la_autoridad_global_situada_no_crea_en_unidad_apagada(http_client, esc):
    antes = await _lotes_nuevos(esc)
    r = await _crear(http_client, esc, "global", "hatchery", company_id=esc["a"])
    assert r.status_code == 403, r.text
    assert await _lotes_nuevos(esc) == antes


async def test_l08_put_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    r = await http_client.put(f"/api/v1/lots/{esc['lh']}", headers=_token(esc["global"], esc["a"]), json={"farm_id": esc["granja_a"]})
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT coalesce(farm_id, 0) FROM lots WHERE id = :l", l=esc["lh"]) == 0, "el lote no cambia"


async def test_l08_close_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    r = await http_client.post(f"/api/v1/lots/{esc['lh']}/close", headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 403, r.text
    assert (await _estado(esc, esc["lh"])).lower().endswith("active")


async def test_l08_activate_manual_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    r = await http_client.post("/api/v1/lots/activate-manual", headers=_token(esc["global"], esc["a"]), json=_apertura(esc, esc["lh2"]))
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM opening_balances WHERE lot_id = :l", l=esc["lh2"]) == 0


async def test_l08_phases_sobre_unidad_apagada_es_403_para_la_autoridad_global(http_client, esc):
    r = await http_client.post(f"/api/v1/lots/{esc['lh2']}/phases", headers=_token(esc["global"], esc["a"]), json=_fase(esc, esc["lh2"]))
    assert r.status_code == 403, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM lot_phases WHERE lot_id = :l", l=esc["lh2"]) == 0


async def test_l09_control_la_autoridad_global_situada_escribe_sobre_unidad_habilitada(http_client, esc):
    cab = _token(esc["global"], esc["a"])
    r = await http_client.put(f"/api/v1/lots/{esc['lg']}", headers=cab, json={"farm_id": esc["granja_a"]})
    assert r.status_code == 200, r.text
    r = await http_client.post("/api/v1/lots/activate-manual", headers=cab, json=_apertura(esc, esc["lg2"]))
    assert r.status_code == 201, r.text
    r = await http_client.post(f"/api/v1/lots/{esc['lg']}/phases", headers=cab, json=_fase(esc, esc["lg"]))
    assert r.status_code == 201, r.text


async def test_l09_control_la_autoridad_global_situada_cierra_un_lote_de_unidad_habilitada(http_client, esc):
    cab = _token(esc["global"], esc["a"])
    await _cerrable(http_client, esc, cab, esc["lr"])
    r = await http_client.post(f"/api/v1/lots/{esc['lr']}/close", headers=cab)
    assert r.status_code == 200, r.text
    assert (await _estado(esc, esc["lr"])).lower().endswith("closed")


async def test_l10_control_el_actor_edita_el_suyo_y_no_el_de_otra_cadena(http_client, esc):
    r = await http_client.put(f"/api/v1/lots/{esc['lg']}", headers=_token(esc["actor_a"]), json={"farm_id": esc["granja_a"]})
    assert r.status_code == 404, r.text
    r = await http_client.put(f"/api/v1/lots/{esc['lr']}", headers=_token(esc["actor_a"]), json={"farm_id": esc["granja_a"]})
    assert r.status_code == 200, r.text


async def test_l11_frontera_de_lectura_la_autoridad_global_situada_sigue_viendo_la_unidad_apagada(http_client, esc):
    """Control: este tranche no reabre las lecturas (fase 3 `:88`, `R-139` S02)."""
    cab = _token(esc["global"], esc["a"])
    r = await http_client.get("/api/v1/lots?limit=100", headers=cab)
    assert r.status_code == 200 and esc["lh"] in {f["id"] for f in _filas(r)}
    r = await http_client.get(f"/api/v1/lots/{esc['lh']}", headers=cab)
    assert r.status_code == 200, r.text


async def test_l11_frontera_de_lectura_el_actor_no_ve_la_unidad_apagada_ni_la_no_concedida(http_client, esc):
    r = await http_client.get("/api/v1/lots?limit=100", headers=_token(esc["actor_a"]))
    ids = {f["id"] for f in _filas(r)}
    assert esc["lr"] in ids and esc["lh"] not in ids and esc["lg"] not in ids


async def test_l12_control_el_administrador_de_accesos_no_crea_lotes(http_client, esc):
    antes = await _lotes_nuevos(esc)
    r = await _crear(http_client, esc, "acceso", "breeder")
    assert r.status_code == 403, r.text
    assert await _lotes_nuevos(esc) == antes


async def test_l14_progenitoras_el_actor_de_abuelas_crea_abuelas_y_no_reproductoras(http_client, esc):
    r = await _crear(http_client, esc, "actor_g", "grandparent")
    assert r.status_code == 201, r.text
    antes = await _lotes_nuevos(esc)
    r = await _crear(http_client, esc, "actor_g", "breeder")
    assert r.status_code == 403, r.text
    assert await _lotes_nuevos(esc) == antes


async def test_l15_control_el_plano_de_control_administra_la_unidad_apagada(http_client, esc):
    """Administrar ≠ operar (`OD-09.b`, `OD-16 §7`, fase 7): sin reactivar nada (`BU-D10`)."""
    cab = _token(esc["acceso"])
    r = await http_client.get("/api/v1/business-units", headers=cab)
    assert r.status_code == 200, r.text
    estado = {f["code"]: f["is_enabled"] for f in r.json()}
    assert estado["hatchery"] is False and estado["broiler"] is True
    r = await http_client.patch("/api/v1/business-units/broiler/disable", headers=cab)
    assert r.status_code == 200, r.text
    assert r.json()["is_enabled"] is False


# ═══════════════════════════════════════════════════════════════════════════
#  R-162 · descarga de evidencia · AC-E01…E08
# ═══════════════════════════════════════════════════════════════════════════

async def _descarga(http_client, esc, actor, evento, evidencia, company_id=None):
    return await http_client.get(f"/api/v1/operations/{esc[evento]}/evidences/{esc[evidencia]}/download",
                                 headers=_token(esc[actor], company_id))


async def test_e01_control_el_actor_descarga_la_evidencia_de_su_unidad(http_client, esc):
    r = await _descarga(http_client, esc, "actor_a", "ev_r", "evi_r")
    assert r.status_code == 200 and f"{PREFIJO}CONTENIDO-R" in r.text


async def test_e02_la_evidencia_de_una_unidad_habilitada_no_concedida_es_inalcanzable(http_client, esc):
    r = await _descarga(http_client, esc, "actor_a", "ev_g", "evi_g")
    assert r.status_code == 404, r.text[:200]
    assert f"{PREFIJO}CONTENIDO-G" not in r.text


async def test_e03_la_evidencia_de_una_unidad_apagada_es_inalcanzable_aunque_haya_concesion(http_client, esc):
    r = await _descarga(http_client, esc, "actor_a", "ev_h", "evi_h")
    assert r.status_code == 404, r.text[:200]
    assert f"{PREFIJO}CONTENIDO-H" not in r.text


async def test_e04_cero_unidades_efectivas_no_descarga_nada(http_client, esc):
    r = await _descarga(http_client, esc, "actor_cero", "ev_r", "evi_r")
    assert r.status_code == 404, r.text[:200]
    assert f"{PREFIJO}CONTENIDO-R" not in r.text


async def test_e05_control_la_evidencia_de_otra_empresa_sigue_siendo_403(http_client, esc):
    r = await _descarga(http_client, esc, "actor_a", "ev_b", "evi_b")
    assert r.status_code == 403, r.text[:200]


async def test_e06_control_la_autoridad_global(http_client, esc):
    r = await _descarga(http_client, esc, "global", "ev_r", "evi_r")
    assert r.status_code == 403, "sin contexto no descarga (R-139)"
    r = await _descarga(http_client, esc, "global", "ev_h", "evi_h", company_id=esc["a"])
    assert r.status_code == 200 and f"{PREFIJO}CONTENIDO-H" in r.text, "situada: visibilidad de control, unidad apagada incluida"
    r = await _descarga(http_client, esc, "global", "ev_b", "evi_b", company_id=esc["a"])
    assert r.status_code == 403


async def test_e07_control_el_administrador_de_accesos_no_descarga(http_client, esc):
    r = await _descarga(http_client, esc, "acceso", "ev_r", "evi_r")
    assert r.status_code == 403, r.text[:200]


async def test_e08_control_el_listado_de_evidencias_ya_acota_por_unidad(http_client, esc):
    r = await http_client.get(f"/api/v1/operations/{esc['ev_g']}/evidences", headers=_token(esc["actor_a"]))
    assert r.status_code == 404, r.text
    r = await http_client.get(f"/api/v1/operations/{esc['ev_r']}/evidences", headers=_token(esc["actor_a"]))
    assert r.status_code == 200 and len(r.json()) == 1
