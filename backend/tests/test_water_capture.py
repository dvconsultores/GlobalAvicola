"""`GA-REM-021` enmienda A · `B05` · consumo diario de agua (`R-13`, `H360-B05`).

Fuente: `Bases Consideradas…pdf` p.2, 4, 12 («Cantidad de agua consumida … durante el día») — Reproductoras (cría y
producción) y Engorde; Incubadora no; Progenitoras no es etapa del cliente. `RR-10` litros · `RR-11` > 0. Unidades sembradas
explícitamente ON/OFF (`BU-D10` no interviene).

    Empresa A   breeder ON · broiler OFF · grandparent ON · hatchery ON · lotes LR (breeder) · LP (broiler) · LG · LH · LN (sin tipo) · LC (breeder cerrado)
    Empresa B   breeder ON · broiler ON · lotes LB (breeder) · LPB (broiler)
    OPERADOR    operations:create/read/update · lots:read · breeder + broiler (histórica; OFF)
    OPERADOR_G  ídem · solo grandparent          CORRECTOR  corrections:correct/read · operations:read · breeder
    SOLICITANTE reversals:create · operations:read · breeder      SIN_PERM operations:read · breeder
    LECTURA     review/corrections/audit/reports/operations:read · breeder (control transversal)
    ACCESO      Administrador de Accesos     ACTOR_B  operations:create/read en B · breeder + broiler     GLOBAL ("*", all)
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date, earlier_event_date, future_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "AGUA-"


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
        for empresa, code, on in ((a, "breeder", True), (a, "broiler", False), (a, "grandparent", True), (a, "hatchery", True),
                                  (b, "breeder", True), (b, "broiler", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        assert hab[(a.id, "broiler")].is_enabled is False
        PA = PermissionAction

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]
        roles = {
            "operador": _rol("Op", a.id, ops),
            "corrector": _rol("Corr", a.id, [("corrections", PA.CORRECT), ("corrections", PA.READ), ("operations", PA.READ)]),
            "solicitante": _rol("Sol", a.id, [("reversals", PA.CREATE), ("reversals", PA.READ), ("operations", PA.READ)]),
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
            return User(first_name=marca, last_name="Agua", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {"operador": _usuario(a.id, "OP", roles["operador"][0]), "operador_g": _usuario(a.id, "OPG", roles["operador"][0]),
             "corrector": _usuario(a.id, "CORR", roles["corrector"][0]), "solicitante": _usuario(a.id, "SOL", roles["solicitante"][0]),
             "sin_perm": _usuario(a.id, "SINPERM", roles["sin_perm"][0]), "lectura": _usuario(a.id, "LECT", roles["lectura"][0]),
             "acceso": _usuario(a.id, "ACC", roles["acceso"][0]), "actor_b": _usuario(b.id, "B", roles["b"][0]),
             "global": _usuario(None, "GLOBAL", roles["global"][0])}
        s.add_all(u.values())
        await s.flush()
        for k in ("operador", "corrector", "solicitante", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=u["operador"], company_business_unit=hab[(a.id, "broiler")])
        await conceder_unidad(s, user=u["operador_g"], company_business_unit=hab[(a.id, "grandparent")])
        for code in ("breeder", "broiler"):
            await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, code)])

        granja_a = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        granja_b = Farm(company_id=b.id, name=f"{PREFIJO}GRANJA-B", code=f"{PREFIJO}GB-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja_a, granja_b])
        await s.flush()
        galpon_a = House(farm_id=granja_a.id, name=f"{PREFIJO}GALPON-A", capacity=10_000, is_active=True)
        galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}GALPON-B", capacity=10_000, is_active=True)
        s.add_all([galpon_a, galpon_b])
        await s.flush()

        def _lote(empresa, marca, tipo, estado=LotStatus.ACTIVE):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=estado)

        lotes = {"lr": _lote(a, "LR", BirdTypeEnum.BREEDER), "lp": _lote(a, "LP", BirdTypeEnum.BROILER), "lg": _lote(a, "LG", BirdTypeEnum.GRANDPARENT),
                 "lh": _lote(a, "LH", BirdTypeEnum.HATCHERY), "ln": _lote(a, "LN", None), "lc": _lote(a, "LC", BirdTypeEnum.BREEDER, LotStatus.CLOSED),
                 "lb": _lote(b, "LB", BirdTypeEnum.BREEDER), "lpb": _lote(b, "LPB", BirdTypeEnum.BROILER)}
        s.add_all(lotes.values())
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "granja_a": granja_a.id, "galpon_a": galpon_a.id, "granja_b": granja_b.id, "galpon_b": galpon_b.id, "url": test_database_url}
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
            "DELETE FROM reversals WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
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


async def _eventos_agua(esc, lote) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE 'water_consumption'", l=lote)


async def _agua(http_client, esc, actor, lote, litros=123.5, fecha=None, company_id=None, **extra):
    cuerpo = {"lot_id": esc[lote], "event_type": "water_consumption", "event_date": fecha or recent_event_date()}
    if litros is not None:
        cuerpo["water_liters"] = litros
    cuerpo.update(extra)
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=cuerpo)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-W · captura
# ═══════════════════════════════════════════════════════════════════════════

async def test_w01_w02_w07_el_operador_registra_el_consumo_de_agua_y_el_valor_se_persiste_y_se_lee(http_client, esc):
    r = await _agua(http_client, esc, "operador", "lr", 123.5)
    assert r.status_code == 201, r.text
    ev = r.json()
    assert ev["event_type"] == "water_consumption" and ev["water_liters"] == 123.5 and ev["status"] == "registered"
    assert (await _sql(esc, "SELECT water_liters FROM operational_events WHERE id = :e", e=ev["id"]))[0][0] == 123.5, "AC-W02"
    r = await http_client.get(f"/api/v1/operations/{ev['id']}", headers=_token(esc["operador"]))
    assert r.status_code == 200 and r.json()["water_liters"] == 123.5, "AC-W07"
    r = await http_client.get(f"/api/v1/operations?lot_id={esc['lr']}&limit=50", headers=_token(esc["operador"]))
    filas = r.json().get("events", r.json()) if isinstance(r.json(), dict) else r.json()
    assert any(f["id"] == ev["id"] and f.get("water_liters") == 123.5 for f in filas), "la serie del reporte tiene dato"


async def test_w03_s09_w04_la_empresa_y_la_unidad_se_derivan_del_lote_no_del_cuerpo(http_client, esc):
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json={
        "lot_id": esc["lr"], "event_type": "water_consumption", "event_date": recent_event_date(), "water_liters": 123.5,
        "company_id": esc["b"], "business_unit_id": 999})
    assert r.status_code == 201, r.text
    assert r.json()["company_id"] == esc["a"] and r.json()["lot_id"] == esc["lr"]
    assert (await _sql(esc, "SELECT company_id FROM operational_events WHERE id = :e", e=r.json()["id"]))[0][0] == esc["a"]


async def test_w05_w06_la_fecha_de_negocio_y_la_unidad_del_contrato(http_client, esc):
    fecha = earlier_event_date()  # la fecha de negocio es la del cuerpo, no la del servidor
    r = await _agua(http_client, esc, "operador", "lr", 80, fecha=fecha)
    assert r.status_code == 201, r.text
    assert r.json()["event_date"] == fecha
    assert "water_liters" in r.json() and "water_unit" not in r.json() and "unit" not in r.json(), "AC-W06: litros por contrato, sin unidad libre"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-V · validación
# ═══════════════════════════════════════════════════════════════════════════

async def test_v01_v04_el_valor_es_obligatorio_numerico_y_estrictamente_positivo(http_client, esc):
    antes = await _eventos_agua(esc, esc["lr"])
    assert (await _agua(http_client, esc, "operador", "lr", None)).status_code == 400, "AC-V01"
    assert (await _agua(http_client, esc, "operador", "lr", "abc")).status_code == 422, "AC-V02"
    assert (await _agua(http_client, esc, "operador", "lr", 0)).status_code == 400, "AC-V03 (RR-11)"
    assert (await _agua(http_client, esc, "operador", "lr", -1)).status_code == 400, "AC-V04"
    assert await _eventos_agua(esc, esc["lr"]) == antes, "cero filas"
    # §A.2: la regla `> 0` rige también en la edición del registro vivo (RR-11)
    ev = (await _agua(http_client, esc, "operador", "lr", 40)).json()
    ruta = f"/api/v1/operations/{ev['id']}"
    assert (await http_client.put(ruta, headers=_token(esc["operador"]), json={"water_liters": 0})).status_code == 400, "AC-V03 en edición"
    r = await http_client.put(ruta, headers=_token(esc["operador"]), json={"water_liters": 80})
    assert r.status_code == 200 and r.json()["water_liters"] == 80, r.text


async def test_v05_v06_precision_y_fecha(http_client, esc):
    r = await _agua(http_client, esc, "operador", "lr", 12.345)
    assert r.status_code == 201 and r.json()["water_liters"] == 12.345, "AC-V05: sin redondeo inventado"
    r = await _agua(http_client, esc, "operador", "lr", 10, fecha=future_event_date())
    assert _es_br(r, "BR-19"), ("AC-V06: sin regla propia del agua; rige la genérica R-30/BR-19 ya vigente para todo evento", r.text)


async def test_v07_bu03_bu04_los_lotes_no_aplicables_se_rechazan(http_client, esc):
    for lote, motivo in (("lc", "cerrado"), ("ln", "sin cadena"), ("lh", "hatchery"), ("lg", "grandparent")):
        actor = "operador_g" if lote == "lg" else "operador"
        r = await _agua(http_client, esc, actor, lote)
        assert r.status_code == 400, (lote, motivo, r.text)
        assert await _eventos_agua(esc, esc[lote]) == 0


async def test_v08_dos_registros_del_mismo_dia_son_aditivos(http_client, esc):
    fecha = recent_event_date()
    assert (await _agua(http_client, esc, "operador", "lr", 50, fecha=fecha)).status_code == 201
    assert (await _agua(http_client, esc, "operador", "lr", 70, fecha=fecha)).status_code == 201
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_date = :f AND event_type::text ILIKE 'water_consumption'", l=esc["lr"], f=date.fromisoformat(fecha)) == 2


async def test_v09_el_agua_no_viaja_en_otro_tipo_de_evento(http_client, esc):
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json={
        "lot_id": esc["lr"], "event_type": "feed_registration", "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 5.0}], "water_liters": 10})
    assert r.status_code == 400, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  AC-S · seguridad · AC-BU · cobertura
# ═══════════════════════════════════════════════════════════════════════════

async def test_s01_s06_otra_empresa_y_la_autoridad_global_fuera_de_contexto(http_client, esc):
    assert _es_br(await _agua(http_client, esc, "actor_b", "lr"), "BR-07"), "AC-S01"
    assert _es_br(await _agua(http_client, esc, "global", "lr"), "BR-07"), "AC-S05: sin contexto, fallo cerrado"
    assert _es_br(await _agua(http_client, esc, "global", "lr", company_id=esc["b"]), "BR-07"), "AC-S06"
    assert await _eventos_agua(esc, esc["lr"]) == 0
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE company_id IS NULL AND event_type::text ILIKE 'water_consumption'") == 0


async def test_s02_s03_unidad_apagada_y_unidad_no_concedida(http_client, esc):
    assert _es_br(await _agua(http_client, esc, "operador", "lp"), "BR-07"), "AC-S02: broiler apagada con concesión histórica"
    r = await _agua(http_client, esc, "global", "lp", company_id=esc["a"])
    assert r.status_code == 403, "AC-S02: la autoridad global no salta la habilitación"
    assert _es_br(await _agua(http_client, esc, "operador_g", "lr"), "BR-07"), "AC-S03: sin la unidad del lote"
    assert await _eventos_agua(esc, esc["lp"]) == 0 and await _eventos_agua(esc, esc["lr"]) == 0


async def test_s04_s07_s08_sin_rbac_ni_plano_de_control_ni_lectura_transversal(http_client, esc):
    for actor in ("sin_perm", "acceso", "lectura"):
        r = await _agua(http_client, esc, actor, "lr")
        assert r.status_code == 403, (actor, r.text)
    assert await _eventos_agua(esc, esc["lr"]) == 0


async def test_bu02_engorde_positivo_independiente(http_client, esc):
    r = await http_client.post("/api/v1/operations", headers=_token(esc["actor_b"]), json={
        "lot_id": esc["lpb"], "event_type": "water_consumption", "event_date": recent_event_date(), "water_liters": 300.25,
        "farm_id": esc["granja_b"], "house_id": esc["galpon_b"]})
    assert r.status_code == 201, r.text
    assert r.json()["water_liters"] == 300.25 and r.json()["company_id"] == esc["b"]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-C · corrección · AC-AU · auditoría · reverso N/A
# ═══════════════════════════════════════════════════════════════════════════

async def test_c01_c03_la_correccion_aplica_el_valor_conserva_el_original_y_respeta_rr11(http_client, esc):
    ev = (await _agua(http_client, esc, "operador", "lr", 123.5)).json()
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                               json={"event_id": ev["id"], "field_name": "water_liters", "corrected_value": "200.5", "reason": f"{PREFIJO}lectura mal anotada"})
    assert r.status_code == 201, r.text
    assert (await _sql(esc, "SELECT water_liters FROM operational_events WHERE id = :e", e=ev["id"]))[0][0] == 200.5
    assert (await _sql(esc, "SELECT original_value FROM correction_logs WHERE event_id = :e", e=ev["id"]))[0][0] == "123.5"
    for malo in ("0", "-5"):
        r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                                   json={"event_id": ev["id"], "field_name": "water_liters", "corrected_value": malo, "reason": f"{PREFIJO}error"})
        assert r.status_code == 400, (malo, r.text)


async def test_c02_sin_permiso_no_se_corrige_y_el_aprobado_es_inmutable(http_client, esc):
    ev = (await _agua(http_client, esc, "operador", "lr", 123.5)).json()
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["sin_perm"]),
                               json={"event_id": ev["id"], "field_name": "water_liters", "corrected_value": "1", "reason": f"{PREFIJO}x"})
    assert r.status_code == 403
    motor = create_async_engine(esc["url"])
    async with motor.begin() as c:
        await c.execute(text("UPDATE operational_events SET status = 'APPROVED' WHERE id = :e"), {"e": ev["id"]})
    await motor.dispose()
    assert (await http_client.put(f"/api/v1/operations/{ev['id']}", headers=_token(esc["operador"]), json={"water_liters": 1})).status_code == 400
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                               json={"event_id": ev["id"], "field_name": "water_liters", "corrected_value": "1", "reason": f"{PREFIJO}x"})
    assert r.status_code == 400


async def test_au01_au02_el_alta_deja_auditoria_y_la_denegada_no(http_client, esc):
    antes = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"])
    ev = (await _agua(http_client, esc, "operador", "lr", 5)).json()
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e AND action::text ILIKE 'created'", e=str(ev["id"])) == 1
    despues = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"])
    assert (await _agua(http_client, esc, "sin_perm", "lr")).status_code == 403
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"]) == despues == antes + 1


async def test_rv_el_consumo_de_agua_no_es_reversible(http_client, esc):
    ev = (await _agua(http_client, esc, "operador", "lr", 5)).json()
    motor = create_async_engine(esc["url"])
    async with motor.begin() as c:
        await c.execute(text("UPDATE operational_events SET status = 'APPROVED' WHERE id = :e"), {"e": ev["id"]})
    await motor.dispose()
    r = await http_client.post("/api/v1/reversals", headers=_token(esc["solicitante"]), json={"event_id": ev["id"], "reason": f"{PREFIJO}no procede"})
    assert _es_br(r, "BR-16"), r.text
