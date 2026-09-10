"""`GA-REM-023` addendum B · `R-176` (+ `R-45`) · las reglas puras del alta se reevalúan al editar y corregir (`AC-R176-01…12`).

Escenario (prefijo `PARI-`): empresa A (breeder ON · hatchery ON · broiler OFF) y B (breeder ON) · operador con operations + corrections en breeder +
hatchery · operador_r solo breeder · sin_perm · actor_b · granja_a con galpón grande (100 000) y galpón chico (capacidad 50) · planta_a · lotes lr, lr2
(breeder), lh (hatchery), lf (breeder, start_date mañana → BR-06), lb (B) · órdenes de compra PARI-OC-A (100), PARI-OC-B (100), PARI-OC-C (200).
Paridad ≠ repetir el alta: la edición válida no crea alertas, notificaciones ni vínculos (AC-R176-09).
"""
from __future__ import annotations

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
from tests.time_reference import beyond_open_period, earlier_event_date, future_event_date, recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "PARI-"


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
    from app.integrations.sap.models import SapReference, SapReferenceType
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "hatchery", True), (a, "broiler", False), (b, "breeder", True)):
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
        roles = {"operador": _rol("Op", a.id, ops), "operador_r": _rol("OpR", a.id, ops),
                 "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]), "b": _rol("OpB", b.id, ops)}
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Pari", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {k: _usuario(a.id, k.upper(), roles[k][0]) for k in ("operador", "operador_r", "sin_perm")}
        u["actor_b"] = _usuario(b.id, "B", roles["b"][0])
        s.add_all(u.values())
        await s.flush()
        for k in ("operador", "operador_r", "sin_perm"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        for k in ("operador", "sin_perm"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "hatchery")])
        await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, "breeder")])

        granja_a = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        planta_a = Farm(company_id=a.id, name=f"{PREFIJO}PLANTA-A", code=f"{PREFIJO}PA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        granja_b = Farm(company_id=b.id, name=f"{PREFIJO}GRANJA-B", code=f"{PREFIJO}GB-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja_a, planta_a, granja_b])
        await s.flush()
        galpon_a = House(farm_id=granja_a.id, name=f"{PREFIJO}G-GRANDE", capacity=100_000, is_active=True)
        galpon_chico = House(farm_id=granja_a.id, name=f"{PREFIJO}G-CHICO", capacity=50, is_active=True)
        galpon_a2 = House(farm_id=granja_a.id, name=f"{PREFIJO}G-GRANDE-2", capacity=100_000, is_active=True)
        galpon_p = House(farm_id=planta_a.id, name=f"{PREFIJO}G-PLANTA", capacity=100_000, is_active=True)
        galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}G-B", capacity=100_000, is_active=True)
        s.add_all([galpon_a, galpon_chico, galpon_a2, galpon_p, galpon_b])
        await s.flush()

        def _lote(empresa, marca, tipo, granja, galpon, **kw):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo,
                       status=kw.pop("status", LotStatus.ACTIVE), farm_id=granja.id, house_id=galpon.id, **kw)

        lotes = {"lr": _lote(a, "LR", BirdTypeEnum.BREEDER, granja_a, galpon_a), "lr2": _lote(a, "LR2", BirdTypeEnum.BREEDER, granja_a, galpon_a),
                 "lh": _lote(a, "LH", BirdTypeEnum.HATCHERY, planta_a, galpon_p),
                 "lf": _lote(a, "LF", BirdTypeEnum.BREEDER, granja_a, galpon_a, start_date=datetime.now(timezone.utc) + timedelta(days=1)),
                 "lb": _lote(b, "LB", BirdTypeEnum.BREEDER, granja_b, galpon_b)}
        s.add_all(lotes.values())
        for code, qty in (("PARI-OC-A", 100), ("PARI-OC-B", 100), ("PARI-OC-C", 200)):
            s.add(SapReference(company_id=a.id, ref_type=SapReferenceType.PURCHASE_ORDER, sap_code=code, quantity=qty, unit="aves", is_active=True))
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "granja_a": granja_a.id, "galpon_a": galpon_a.id, "galpon_chico": galpon_chico.id, "galpon_a2": galpon_a2.id,
             "planta_a": planta_a.id, "galpon_p": galpon_p.id, "granja_b": granja_b.id, "galpon_b": galpon_b.id, "url": test_database_url}
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
            "DELETE FROM sap_references WHERE sap_code LIKE :p",
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


async def _saldo(esc, lote) -> int:
    from app.operations.validators import get_current_bird_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return await get_current_bird_balance(s, lote)
    finally:
        await motor.dispose()


async def _evento(esc, event_id):
    f = (await _sql(esc, "SELECT lot_id, status::text, version, coalesce(farm_id, 0), coalesce(house_id, 0), event_date::text, coalesce(sap_document_ref, '') "
                         "FROM operational_events WHERE id = :e", e=event_id))[0]
    return {"lot_id": f[0], "status": f[1].lower(), "version": f[2], "farm_id": f[3], "house_id": f[4], "event_date": f[5], "sap_document_ref": f[6]}


async def _efectos(esc):
    """Efectos laterales observables del alta, por empresa A: auditoría, alertas, notificaciones, vínculos."""
    a = esc["a"]
    return {
        "auditoria": await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a", a=a),
        "creadas": await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=a),
        "alertas": await _cuenta(esc, "SELECT count(*) FROM operational_alerts WHERE company_id = :a", a=a),
        "notificaciones": await _cuenta(esc, "SELECT count(*) FROM notifications WHERE company_id = :a", a=a),
        "vinculos": await _cuenta(esc, "SELECT (SELECT count(*) FROM egg_batches WHERE source_lot_id IN (SELECT id FROM lots WHERE company_id = :a)) + "
                                       "(SELECT count(*) FROM chick_batches WHERE hatchery_lot_id IN (SELECT id FROM lots WHERE company_id = :a))", a=a),
        "eventos": await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE company_id = :a", a=a),
    }


def _cuerpo(esc, lote, tipo, n=None, *, galpon=None, **extra):
    granja, galpon_defecto = ("planta_a", "galpon_p") if lote == "lh" else (("granja_b", "galpon_b") if lote == "lb" else ("granja_a", "galpon_a"))
    cuerpo = {"lot_id": esc[lote], "event_type": tipo, "event_date": recent_event_date(), "farm_id": esc[granja], "house_id": esc[galpon or galpon_defecto]}
    if tipo == "bird_reception":
        cuerpo["bird_movements"] = [{"sex": "mixed", "quantity": n}]
        cuerpo.update({"received_total": n, "dead_on_arrival": 0, "rejected_on_arrival": 0})
    elif tipo in ("cull_recording", "mortality_recording", "bird_exit"):
        cuerpo["bird_movements"] = [{"sex": "mixed", "quantity": n}]
    elif tipo == "egg_dispatch":
        cuerpo["egg_movements"] = [{"egg_type": "fertile", "quantity": n}]
        cuerpo["destination_farm_id"] = esc["planta_a"]
    elif tipo == "egg_collection":
        cuerpo["egg_movements"] = [{"egg_type": "fertile", "quantity": n}]
    cuerpo.update(extra)
    return cuerpo


async def _alta(http_client, esc, lote, tipo, n=None, actor="operador", **kw) -> int:
    r = await http_client.post("/api/v1/operations", headers=_token(esc[actor]), json=_cuerpo(esc, lote, tipo, n, **kw))
    assert r.status_code == 201, (tipo, r.text)
    return r.json()["id"]


async def _put(http_client, esc, actor, event_id, cuerpo, company_id=None):
    return await http_client.put(f"/api/v1/operations/{event_id}", headers=_token(esc[actor], company_id), json=cuerpo)


async def _corregir(http_client, esc, actor, event_id, campo, valor):
    return await http_client.post("/api/v1/corrections", headers=_token(esc[actor]),
                                  json={"event_id": event_id, "field_name": campo, "corrected_value": "" if valor is None else str(valor),
                                        "reason": f"{PREFIJO}corrección de prueba"})


async def _sin_cambios(esc, event_id, antes_evento, antes_efectos, *, lote=None, saldo=None):
    """`AC-R176-08`: una denegación no deja rastro."""
    assert await _evento(esc, event_id) == antes_evento, "el evento no cambia"
    despues = await _efectos(esc)
    assert despues == antes_efectos, ("sin auditoría de éxito, alertas, notificaciones ni vínculos", antes_efectos, despues)
    if lote is not None:
        assert await _saldo(esc, esc[lote]) == saldo


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R176-01 · 02 — BR-17 (capacidad del galpón) en PUT y en corrección
# ═══════════════════════════════════════════════════════════════════════════

async def test_r176_01_02_editar_o_corregir_el_galpon_por_debajo_de_la_capacidad_se_deniega(http_client, esc):
    recepcion = await _alta(http_client, esc, "lr", "bird_reception", 100)
    antes, efectos = await _evento(esc, recepcion), await _efectos(esc)
    r = await _put(http_client, esc, "operador", recepcion, {"house_id": esc["galpon_chico"]})
    assert _es_br(r, "BR-17"), ("AC-R176-01: 100 aves no caben en un galpón de 50", r.status_code, r.text)
    await _sin_cambios(esc, recepcion, antes, efectos, lote="lr", saldo=100)
    r = await _corregir(http_client, esc, "operador", recepcion, "house_id", esc["galpon_chico"])
    assert _es_br(r, "BR-17"), ("AC-R176-02: la corrección tampoco es una puerta trasera", r.status_code, r.text)
    await _sin_cambios(esc, recepcion, antes, efectos, lote="lr", saldo=100)
    assert await _cuenta(esc, "SELECT count(*) FROM correction_logs WHERE event_id = :e", e=recepcion) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R176-03 · 04 · 06 · 07 — BR-18 (acumulado de la OC) en PUT y en corrección; la edición válida sigue
# ═══════════════════════════════════════════════════════════════════════════

async def test_r176_03_04_06_07_mover_el_acumulado_a_una_oc_sin_cupo_se_deniega_y_con_cupo_se_acepta(http_client, esc):
    await _alta(http_client, esc, "lr", "bird_reception", 80, sap_document_ref="PARI-OC-A")
    segunda = await _alta(http_client, esc, "lr2", "bird_reception", 50, sap_document_ref="PARI-OC-B")
    antes, efectos = await _evento(esc, segunda), await _efectos(esc)
    r = await _put(http_client, esc, "operador", segunda, {"sap_document_ref": "PARI-OC-A"})
    assert _es_br(r, "BR-18"), ("AC-R176-03: 80 + 50 = 130 > 100 de la OC-A", r.status_code, r.text)
    await _sin_cambios(esc, segunda, antes, efectos, lote="lr2", saldo=50)
    r = await _corregir(http_client, esc, "operador", segunda, "sap_document_ref", "PARI-OC-A")
    assert _es_br(r, "BR-18"), ("AC-R176-04", r.status_code, r.text)
    await _sin_cambios(esc, segunda, antes, efectos, lote="lr2", saldo=50)
    # con cupo: la edición válida se aplica y solo deja su auditoría (AC-R176-06 · 09)
    r = await _put(http_client, esc, "operador", segunda, {"sap_document_ref": "PARI-OC-C"})
    assert r.status_code == 200, ("AC-R176-06", r.text)
    assert (await _evento(esc, segunda))["sap_document_ref"] == "PARI-OC-C"
    despues = await _efectos(esc)
    assert despues["auditoria"] == efectos["auditoria"] + 1 and despues["creadas"] == efectos["creadas"], "AC-R176-09: una auditoría de edición, ninguna de alta"
    assert {k: despues[k] for k in ("alertas", "notificaciones", "vinculos", "eventos")} == {k: efectos[k] for k in ("alertas", "notificaciones", "vinculos", "eventos")}
    # corrección válida (AC-R176-07): vuelve a OC-B, que sigue con cupo
    r = await _corregir(http_client, esc, "operador", segunda, "sap_document_ref", "PARI-OC-B")
    assert r.status_code == 201, ("AC-R176-07", r.text)
    ev = await _evento(esc, segunda)
    assert ev["sap_document_ref"] == "PARI-OC-B" and ev["status"] == "corrected" and ev["version"] == antes["version"] + 2


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R176-05 — fecha: período cerrado, futura, anterior al lote; PUT y corrección
# ═══════════════════════════════════════════════════════════════════════════

async def test_r176_05_editar_o_corregir_la_fecha_fuera_de_las_reglas_se_deniega(http_client, esc):
    descarte_base = await _alta(http_client, esc, "lr", "bird_reception", 100)
    antes, efectos = await _evento(esc, descarte_base), await _efectos(esc)
    for etiqueta, fecha, regla in (("período cerrado (+90 d)", beyond_open_period(), "BR-19"), ("fecha futura", future_event_date(), "BR-19")):
        r = await _put(http_client, esc, "operador", descarte_base, {"event_date": fecha})
        assert _es_br(r, regla), (f"AC-R176-05 PUT · {etiqueta}", r.status_code, r.text)
        await _sin_cambios(esc, descarte_base, antes, efectos)
        r = await _corregir(http_client, esc, "operador", descarte_base, "event_date", fecha)
        assert _es_br(r, regla), (f"AC-R176-05 corrección · {etiqueta} (R-45)", r.status_code, r.text)
        await _sin_cambios(esc, descarte_base, antes, efectos)
    # anterior al inicio del lote destino: mover a lf (start_date mañana) con fecha de hoy − 7
    r = await _put(http_client, esc, "operador", descarte_base, {"lot_id": esc["lf"]})
    assert _es_br(r, "BR-06"), ("AC-R176-05 · BR-06 al cambiar de lote (R-173, control)", r.status_code, r.text)
    # y con una fecha válida (14 días atrás, dentro del período) la edición pasa
    r = await _put(http_client, esc, "operador", descarte_base, {"event_date": earlier_event_date()})
    assert r.status_code == 200, r.text
    assert (await _evento(esc, descarte_base))["event_date"] == earlier_event_date()


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R176-05b — BR-08: la ubicación obligatoria no se anula por edición ni corrección
# ═══════════════════════════════════════════════════════════════════════════

async def test_r176_05b_quitar_la_ubicacion_de_un_evento_que_la_exige_se_deniega(http_client, esc):
    recepcion = await _alta(http_client, esc, "lr", "bird_reception", 100)
    antes, efectos = await _evento(esc, recepcion), await _efectos(esc)
    r = await _put(http_client, esc, "operador", recepcion, {"house_id": None})
    assert _es_br(r, "BR-08"), ("AC-R176-05b PUT: la recepción exige galpón", r.status_code, r.text)
    await _sin_cambios(esc, recepcion, antes, efectos)
    await _alta(http_client, esc, "lr", "egg_collection", 100)
    despacho = await _alta(http_client, esc, "lr", "egg_dispatch", 10)
    antes_d, efectos_d = await _evento(esc, despacho), await _efectos(esc)
    r = await _corregir(http_client, esc, "operador", despacho, "farm_id", None)
    assert _es_br(r, "BR-08"), ("AC-R176-05b corrección: el despacho exige granja", r.status_code, r.text)
    await _sin_cambios(esc, despacho, antes_d, efectos_d)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R176-05c — BR-11 (etiqueta BR-10): el documento SAP no se duplica por edición, corrección ni cambio de lote
# ═══════════════════════════════════════════════════════════════════════════

async def test_r176_05c_duplicar_el_documento_sap_por_edicion_se_deniega(http_client, esc):
    await _alta(http_client, esc, "lr", "vaccination", sap_document_ref="PARI-DOC-1")
    segunda = await _alta(http_client, esc, "lr", "vaccination", sap_document_ref="PARI-DOC-2")
    antes, efectos = await _evento(esc, segunda), await _efectos(esc)
    r = await _put(http_client, esc, "operador", segunda, {"sap_document_ref": "PARI-DOC-1"})
    assert _es_br(r, "BR-10"), ("AC-R176-05c PUT: DOC-1 ya existe en el lote", r.status_code, r.text)
    await _sin_cambios(esc, segunda, antes, efectos)
    r = await _corregir(http_client, esc, "operador", segunda, "sap_document_ref", "PARI-DOC-1")
    assert _es_br(r, "BR-10"), ("AC-R176-05c corrección", r.status_code, r.text)
    await _sin_cambios(esc, segunda, antes, efectos)
    # cambio de lote hacia un lote donde DOC-2 ya existe (el alta de control se hace antes de medir los efectos)
    await _alta(http_client, esc, "lr2", "vaccination", sap_document_ref="PARI-DOC-2")
    efectos = await _efectos(esc)
    r = await _put(http_client, esc, "operador", segunda, {"lot_id": esc["lr2"]})
    assert _es_br(r, "BR-10"), ("AC-R176-05c: el destino ya tiene DOC-2", r.status_code, r.text)
    await _sin_cambios(esc, segunda, antes, efectos)
    # sin conflicto: DOC-3 pasa
    assert (await _put(http_client, esc, "operador", segunda, {"sap_document_ref": "PARI-DOC-3"})).status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R176-09 — la paridad no repite el alta (edición válida de galpón: sin alertas, notificaciones ni vínculos nuevos)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r176_09_la_edicion_valida_no_repite_los_efectos_del_alta(http_client, esc):
    recepcion = await _alta(http_client, esc, "lr", "bird_reception", 100)
    efectos = await _efectos(esc)
    r = await _put(http_client, esc, "operador", recepcion, {"house_id": esc["galpon_a2"], "observations": f"{PREFIJO}galpón cambiado"})
    assert r.status_code == 200, r.text
    despues = await _efectos(esc)
    assert despues["auditoria"] == efectos["auditoria"] + 1, "una sola auditoría (updated)"
    assert despues["creadas"] == efectos["creadas"] and despues["eventos"] == efectos["eventos"], "sin auditoría de alta ni evento nuevo"
    assert despues["alertas"] == efectos["alertas"] and despues["notificaciones"] == efectos["notificaciones"] and despues["vinculos"] == efectos["vinculos"]
    assert await _saldo(esc, esc["lr"]) == 100 and (await _evento(esc, recepcion))["house_id"] == esc["galpon_a2"]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R176-11 · 12 — aprobado inmutable; cadena de seguridad antes de cualquier regla
# ═══════════════════════════════════════════════════════════════════════════

async def test_r176_11_12_aprobado_inmutable_y_cadena_de_seguridad_antes_de_las_reglas(http_client, esc):
    recepcion = await _alta(http_client, esc, "lr", "bird_reception", 100)
    antes, efectos = await _evento(esc, recepcion), await _efectos(esc)
    r = await _put(http_client, esc, "actor_b", recepcion, {"house_id": esc["galpon_chico"]})
    assert r.status_code in (403, 404), ("AC-R176-12: otra empresa no llega a BR-17", r.status_code, r.text)
    r = await _put(http_client, esc, "sin_perm", recepcion, {"house_id": esc["galpon_chico"]})
    assert r.status_code == 403, ("AC-R176-12: sin permiso", r.status_code, r.text)
    en_incubadora = await _alta(http_client, esc, "lh", "egg_collection", 10)
    efectos = await _efectos(esc)  # el alta de control precede a la medición
    r = await _put(http_client, esc, "operador_r", en_incubadora, {"event_date": beyond_open_period()})
    assert r.status_code == 404 or _es_br(r, "BR-07"), ("AC-R176-12: sin la unidad de incubadora el evento ni se ve (R-159/R-160); la fecha ni se mira", r.status_code, r.text)
    await _sin_cambios(esc, recepcion, antes, efectos)
    motor = create_async_engine(esc["url"])
    async with motor.begin() as c:
        await c.execute(text("UPDATE operational_events SET status = 'APPROVED' WHERE id = :e"), {"e": recepcion})
    await motor.dispose()
    r = await _put(http_client, esc, "operador", recepcion, {"house_id": esc["galpon_a2"]})
    assert r.status_code == 400, ("AC-R176-11: lo aprobado no se edita", r.status_code, r.text)
    assert (await _evento(esc, recepcion))["house_id"] == esc["galpon_a"]
