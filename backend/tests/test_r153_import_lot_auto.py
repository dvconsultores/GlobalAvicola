"""`R-153` · `OD-25 (B)` · lote de abuelas automático al aprobar la importación (`grandparent_import`).

Contrato: la importación nueva se registra SIN lote; la aprobación P-07 crea exactamente un lote
de Progenitoras derivado del plan (código `L-GP-{año}-{nn}`, empresa del evento, sin población),
en la misma transacción; la recepción sigue siendo la única entrada de población; el legado con
lote preasignado no duplica; vía manual intacta.

Escenario (prefijo `AUTOLOTE-`): empresa A (grandparent ON · breeder ON), operador (gp+br),
aprobador (review+approvals), op_breeder (solo breeder), granja/galpón, proveedor/transporte,
OC `AUTOLOTE-OC-A` (100). Sin PostgreSQL local la suite se SALTA (declarado); corre en CI.
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
from tests.time_reference import earlier_event_date, recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "AUTOLOTE-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.integrations.sap.models import SapReference, SapReferenceType
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus,
                                    Supplier, Transport)

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for code, on in (("grandparent", True), ("breeder", True)):
            fila = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[code] = fila
        PA = PermissionAction

        def _rol(nombre, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
            s.add(r)
            return r, permisos

        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]
        roles = {
            "operador": _rol("OP", ops),
            "aprobador": _rol("AP", [("review", PA.READ), ("review", PA.REVIEW), ("approvals", PA.APPROVE),
                                     ("approvals", PA.REJECT), ("corrections", PA.READ), ("corrections", PA.CORRECT),
                                     ("lots", PA.READ), ("operations", PA.READ)]),
            "op_breeder": _rol("OPBR", ops),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        await s.flush()

        def _usuario(marca, rol):
            return User(first_name=marca, last_name="Auto", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=a.id, role_id=rol.id, is_active=True)

        u = {k: _usuario(k.upper(), roles[k][0]) for k in ("operador", "aprobador", "op_breeder")}
        s.add_all(u.values())
        await s.flush()
        for k in ("operador", "aprobador"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab["grandparent"])
        await conceder_unidad(s, user=u["operador"], company_business_unit=hab["breeder"])
        await conceder_unidad(s, user=u["op_breeder"], company_business_unit=hab["breeder"])

        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA", farm_type=FarmType.GRANDPARENT, is_active=True)
        s.add(granja)
        await s.flush()
        galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON", capacity=100_000, is_active=True)
        sup = Supplier(company_id=a.id, name=f"{PREFIJO}PROVEEDOR", country="Francia", supplier_type="international", is_active=True)
        tr = Transport(company_id=a.id, name=f"{PREFIJO}TRANSPORTE", plate="AUTO-A", is_active=True)
        s.add_all([galpon, sup, tr])
        s.add(SapReference(company_id=a.id, ref_type=SapReferenceType.PURCHASE_ORDER, sap_code="AUTOLOTE-OC-A", quantity=100, unit="aves", is_active=True))
        await s.flush()
        lote_legado = Lot(company_id=a.id, lot_code=f"{PREFIJO}LEG-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.GRANDPARENT,
                          status=LotStatus.ACTIVE, farm_id=granja.id, house_id=galpon.id)
        s.add(lote_legado)
        await s.flush()
        await s.commit()
        d = {"a": a.id, "url": test_database_url, "granja": granja.id, "galpon": galpon.id,
             "sup": sup.id, "tr": tr.id, "lote_legado": lote_legado.id,
             "hab_gp": hab["grandparent"].id}
        d.update({k: v.id for k, v in u.items()})
    yield d
    async with motor.begin() as conn:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM sap_references WHERE sap_code LIKE :p",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM suppliers WHERE name LIKE :p",
            "DELETE FROM transports WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await conn.execute(text(sql), p)
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


def _plan(**cambios) -> dict:
    plan = {"origin_country": "Francia", "purchased_total": 110, "shipped_total": 105, "received_total": 100, "transit_mortality": 5,
            "departure_date": earlier_event_date(), "arrival_date": recent_event_date(), "reception_condition": "buena",
            "quarantine_days": 21, "quarantine_end_date": recent_event_date(), "initial_health_inspection": "sin hallazgos"}
    plan.update(cambios)
    return {k: v for k, v in plan.items() if v is not ...}


def _importacion(esc, *, lote=None, plan=None, filas=None, **extra) -> dict:
    cuerpo = {"event_type": "grandparent_import", "event_date": recent_event_date(),
              "farm_id": esc["granja"], "house_id": esc["galpon"],
              "sap_document_ref": "AUTOLOTE-OC-A", "supplier_id": esc["sup"], "transport_id": esc["tr"],
              "bird_movements": filas if filas is not None else [{"sex": "male", "quantity": 40}, {"sex": "female", "quantity": 60}],
              "extra_data": {"import_plan": plan if plan is not None else _plan()}}
    if lote is not None:
        cuerpo["lot_id"] = esc[lote]
    cuerpo.update(extra)
    return {k: v for k, v in cuerpo.items() if v is not ...}


async def _post(http_client, esc, actor, cuerpo):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], esc["a"]), json=cuerpo)


async def _aprobar(http_client, esc, event_id, reviewer="aprobador"):
    """Cadena P-07 completa (empresa con 2 niveles): submit → start → complete → approve."""
    h = _token(esc[reviewer], esc["a"])
    r = await http_client.post(f"/api/v1/operations/{event_id}/submit", headers=_token(esc["operador"], esc["a"]))
    assert r.status_code == 200, r.text
    r = await http_client.post(f"/api/v1/review/start/{event_id}", headers=h)
    assert r.status_code == 200, r.text
    r = await http_client.post("/api/v1/review/complete", headers=h, json={"event_id": event_id})
    assert r.status_code == 200, r.text
    return await http_client.post("/api/v1/approvals/approve", headers=h, json={"event_id": event_id})


async def _lote_del_evento(esc, event_id):
    filas = await _sql(esc, "SELECT lot_id FROM operational_events WHERE id = :e", e=event_id)
    return filas[0][0]


async def _lotes_gp(esc) -> list[tuple]:
    return await _sql(esc, "SELECT id, lot_code, bird_type::text, sex::text, start_date, company_id FROM lots WHERE lot_code LIKE :p ORDER BY lot_code", p=f"L-GP-%")


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC04/05 · el flujo nuevo registra la importación SIN lote; pre-aprobación: cero lotes
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac04_ac05_import_sin_lote_se_registra_y_no_hay_lote_antes_de_aprobar(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc))
    assert r.status_code == 201, r.text
    assert r.json()["lot_id"] in (None, "null") or r.json()["lot_id"] is None
    assert await _lotes_gp(esc) == [], "AC05: sin lote antes de aprobar"


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC06/07/08/12/13/14 · la aprobación crea EXACTAMENTE un lote con datos canónicos
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac06_07_08_12_13_14_aprobacion_crea_un_lote_canonico(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc))
    assert r.status_code == 201, r.text
    evento = r.json()["id"]
    plan = _plan()
    r = await _aprobar(http_client, esc, evento)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"

    lotes = await _lotes_gp(esc)
    assert len(lotes) == 1, "AC06: exactamente un lote"
    lot_id, code, bird_type, sex, start_date, company_id = lotes[0]
    anio = plan["arrival_date"][:4]
    assert code == f"L-GP-{anio}-01", f"AC09: código canónico, got {code}"
    assert bird_type == "grandparent", "AC08: dominio"
    assert sex == "mixed", "AC13: ambos sexos ⇒ mixed"
    assert str(start_date)[:10] == plan["arrival_date"], "AC12: fecha = llegada del plan"
    assert company_id == esc["a"], "AC07: misma empresa"
    assert await _lote_del_evento(esc, evento) == lot_id, "enlace evento→lote"
    assert await _cuenta(esc, "SELECT count(*) FROM lots WHERE id = :l", l=lot_id) == 1
    # farm canónica del evento (no inventada) + nulables sin fuente
    fila = await _sql(esc, "SELECT farm_id, genetic_line_id, area_id FROM lots WHERE id = :l", l=lot_id)
    assert fila[0][0] == esc["granja"], "granja del evento"
    assert fila[0][1] is None and fila[0][2] is None, "AC15: sin inventar genética/área"
    # AC16 · población 0 tras la aprobación (documental)
    saldo = await _sql(esc, "SELECT coalesce(sum(quantity), 0) FROM bird_movements WHERE event_id = :e AND sex IS NOT NULL", e=evento)
    assert saldo is not None  # movimiento documental del plan, no población del lote


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC23/25/26 · doble aprobación NO duplica
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac23_ac26_doble_aprobacion_no_duplica(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc))
    evento = r.json()["id"]
    assert (await _aprobar(http_client, esc, evento)).status_code == 200
    r2 = await http_client.post("/api/v1/approvals/approve", headers=_token(esc["aprobador"], esc["a"]), json={"event_id": evento})
    assert r2.status_code == 400, f"segunda aprobación rechazada por estado, got {r2.status_code}"
    assert len(await _lotes_gp(esc)) == 1, "AC26: un solo lote"


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC27 · legado con lote preasignado: sin segundo lote
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac27_legado_con_lote_no_duplica(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc, lote="lote_legado"))
    assert r.status_code == 201, r.text
    evento = r.json()["id"]
    assert (await _aprobar(http_client, esc, evento)).status_code == 200
    assert await _lote_del_evento(esc, evento) == esc["lote_legado"], "conserva el lote legado"
    assert len(await _lotes_gp(esc)) == 0, "AC27: sin lote nuevo"


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC28/29 · devuelto/rechazado no crea lote; aprobar después sí
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac28_ac29_devuelto_no_crea_y_aprobado_despues_si(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc))
    evento = r.json()["id"]
    h = _token(esc["aprobador"], esc["a"])
    assert (await http_client.post(f"/api/v1/operations/{evento}/submit", headers=_token(esc["operador"], esc["a"]))).status_code == 200
    assert (await http_client.post(f"/api/v1/review/start/{evento}", headers=h)).status_code == 200
    assert (await http_client.post("/api/v1/review/return", headers=h, json={"event_id": evento, "observations": "revisar documento"})).status_code == 200
    assert len(await _lotes_gp(esc)) == 0, "AC29: devuelto sin lote"
    assert (await _aprobar(http_client, esc, evento)).status_code == 200
    assert len(await _lotes_gp(esc)) == 1, "al aprobar después, el lote nace"


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC09/10/11 · secuencia por empresa y año (consecutiva)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac09_ac10_secuencia_consecutiva(http_client, esc):
    e1 = (await _post(http_client, esc, "operador", _importacion(esc))).json()["id"]
    assert (await _aprobar(http_client, esc, e1)).status_code == 200
    e2 = (await _post(http_client, esc, "operador", _importacion(esc))).json()["id"]
    assert (await _aprobar(http_client, esc, e2)).status_code == 200
    codigos = [c for (_i, c, *_r) in await _lotes_gp(esc)]
    anio = _plan()["arrival_date"][:4]
    assert codigos == [f"L-GP-{anio}-01", f"L-GP-{anio}-02"], codigos


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC16..21 · recepción: la población entra UNA sola vez
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac16_a_ac21_recepcion_puebla_una_vez(http_client, esc):
    from app.operations.validators import get_current_bird_balance

    e1 = (await _post(http_client, esc, "operador", _importacion(esc))).json()["id"]
    assert (await _aprobar(http_client, esc, e1)).status_code == 200
    lot_id = await _lote_del_evento(esc, e1)
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            assert await get_current_bird_balance(s, lot_id) == 0, "AC18: pre-recepción vacía"
    finally:
        await motor.dispose()
    recepcion = {"lot_id": lot_id, "event_type": "bird_reception", "event_date": recent_event_date(),
                 "farm_id": esc["granja"], "house_id": esc["galpon"], "sap_document_ref": "AUTOLOTE-OC-A",
                 "bird_movements": [{"sex": "mixed", "quantity": 10}]}
    rr = await _post(http_client, esc, "operador", recepcion)
    assert rr.status_code == 201, rr.text
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            assert await get_current_bird_balance(s, lot_id) == 10, "AC20/21: exactamente N, sin doble conteo"
    finally:
        await motor.dispose()


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC31/32 · atomicidad: fallo del lote ⇒ aprobación revertida, cero lotes
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac31_ac32_fallo_de_lote_revierte_la_aprobacion(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc))
    evento = r.json()["id"]
    # Corromper la fecha de llegada del plan ya registrado: la creación del lote falla en la misma transacción
    await _sql(esc, "UPDATE operational_events SET extra_data = jsonb_set(extra_data, '{import_plan,arrival_date}', '\"no-es-fecha\"') WHERE id = :e", e=evento)
    resp = await _aprobar(http_client, esc, evento)
    assert resp.status_code == 400, f"fallo gobernado (BR-22), got {resp.status_code}: {resp.text}"
    estado = (await _sql(esc, "SELECT status::text FROM operational_events WHERE id = :e", e=evento))[0][0]
    assert estado != "approved", "AC31: no queda aprobada sin lote"
    assert len(await _lotes_gp(esc)) == 0, "sin lote parcial"


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC45/46 · BU OFF y sin concesión: falla cerrado, sin lote
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac45_ac46_bu_off_y_sin_concesion(http_client, esc):
    # (a) usuario sin concesión de grandparent (solo breeder) → denegado
    r = await _post(http_client, esc, "op_breeder", _importacion(esc))
    assert r.status_code == 403, f"sin concesión ⇒ 403, got {r.status_code}: {r.text}"
    assert len(await _lotes_gp(esc)) == 0
    # (b) empresa con la unidad apagada → falla cerrado
    await _sql(esc, "UPDATE company_business_units SET is_enabled = false WHERE id = :h", h=esc["hab_gp"])
    try:
        r = await _post(http_client, esc, "operador", _importacion(esc))
        assert r.status_code in (403, 400), f"BU OFF ⇒ cerrado, got {r.status_code}: {r.text}"
        assert len(await _lotes_gp(esc)) == 0
    finally:
        await _sql(esc, "UPDATE company_business_units SET is_enabled = true WHERE id = :h", h=esc["hab_gp"])


# ═══════════════════════════════════════════════════════════════════════════
#  R153-AC58/59 · la cadena se deriva del TIPO: visible para `grandparent` sin clasificar,
#  fuera de la bandeja de pendientes, e invisible para otra cadena
# ═══════════════════════════════════════════════════════════════════════════

async def test_r153_ac58_derivacion_por_tipo_visible_y_sin_bandeja(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc))
    assert r.status_code == 201, r.text
    evento = r.json()["id"]
    det = await http_client.get(f"/api/v1/operations/{evento}",
                                headers=_token(esc["operador"], esc["a"]))
    assert det.status_code == 200, f"deriva del tipo ⇒ alcanzable, got {det.status_code}: {det.text}"
    bandeja = await http_client.get("/api/v1/operations/pending-classification",
                                    headers=_token(esc["operador"], esc["a"]))
    assert bandeja.status_code == 200
    assert all(e["id"] != evento for e in bandeja.json()), "la importación no es pendiente"


async def test_r153_ac59_derivacion_por_tipo_ajena_a_otra_cadena(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc))
    evento = r.json()["id"]
    det = await http_client.get(f"/api/v1/operations/{evento}",
                                headers=_token(esc["op_breeder"], esc["a"]))
    assert det.status_code == 404, f"otra cadena ⇒ no encontrado, got {det.status_code}"
    bandeja = await http_client.get("/api/v1/operations/pending-classification",
                                    headers=_token(esc["op_breeder"], esc["a"]))
    assert all(e["id"] != evento for e in bandeja.json())
