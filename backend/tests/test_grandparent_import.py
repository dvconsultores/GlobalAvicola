"""`GA-REM-042` · `R-152` · el plan de importación de abuelas (`grandparent_import`) con estructura, identidades (`BR-22`), proveedor y
transporte de la empresa, adjuntos clasificados y revalidación en edición/corrección (`AC-R152-01…19`). Progenitoras ≠ Reproductoras.

Escenario (prefijo `ABUE-`):
    empresa A   grandparent ON · breeder ON · hatchery OFF     empresa B   grandparent OFF · breeder ON     empresa C   grandparent ON · breeder OFF
    op_gp (A: solo grandparent) · op_br (A: solo breeder) · op_ambos (A: ambas) · sin_perm · acceso · lectura · actor_b (B: ambas, concesión histórica
    sobre grandparent apagada) · op_c (C: grandparent) · global (comodín, sin empresa)
    lotes   lg (A grandparent) · lr (A breeder) · lgb (B grandparent) · lgc (C grandparent)   proveedores sup_a, sup_b   transportes tr_a, tr_b   OC ABUE-OC-A (100)
"""
from __future__ import annotations

import json
import os
import shutil
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
from tests.time_reference import earlier_event_date, iso_days_ago, recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "ABUE-"
CLASES = ("sanitary_document", "import_permit", "customs_document", "vaccination_certificate", "origin_certificate")


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
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus, Supplier, Transport

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a, b, c = (Company(name=f"{PREFIJO}{m}-{uuid.uuid4().hex[:6]}", is_active=True) for m in ("A", "B", "C"))
        s.add_all([a, b, c])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "grandparent", True), (a, "breeder", True), (a, "hatchery", False),
                                  (b, "grandparent", False), (b, "breeder", True), (c, "grandparent", True), (c, "breeder", False)):
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
            "op_gp": _rol("OpGP", a.id, ops), "op_br": _rol("OpBR", a.id, ops), "op_ambos": _rol("OpAmbos", a.id, ops),
            "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]),
            "acceso": _rol("Acceso", a.id, [("business_units", PA.READ), ("business_units", PA.CREATE), ("business_units", PA.UPDATE), ("business_units", PA.DELETE), ("users", PA.READ)]),
            "lectura": _rol("Lectura", a.id, [("review", PA.READ), ("corrections", PA.READ), ("audit", PA.READ), ("reports", PA.READ), ("operations", PA.READ)]),
            "actor_b": _rol("OpB", b.id, ops), "op_c": _rol("OpC", c.id, ops), "global": _rol("Global", None, []),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Abue", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {k: _usuario(a.id, k.upper(), roles[k][0]) for k in ("op_gp", "op_br", "op_ambos", "sin_perm", "acceso", "lectura")}
        u["actor_b"] = _usuario(b.id, "B", roles["actor_b"][0]); u["op_c"] = _usuario(c.id, "C", roles["op_c"][0])
        u["global"] = _usuario(None, "GLOBAL", roles["global"][0])
        s.add_all(u.values())
        await s.flush()
        for k in ("op_gp", "op_ambos", "sin_perm", "acceso", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "grandparent")])
        for k in ("op_br", "op_ambos", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        for code in ("grandparent", "breeder"):
            await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, code)])
        await conceder_unidad(s, user=u["op_c"], company_business_unit=hab[(c.id, "grandparent")])

        granjas = {k: Farm(company_id=e.id, name=f"{PREFIJO}GRANJA-{k[-1].upper()}", code=f"{PREFIJO}G{k[-1].upper()}-{uuid.uuid4().hex[:4]}",
                           farm_type=FarmType.BREEDING, is_active=True) for k, e in (("granja_a", a), ("granja_b", b), ("granja_c", c))}
        s.add_all(granjas.values())
        await s.flush()
        galpones = {k: House(farm_id=f.id, name=f"{PREFIJO}G-{k}", capacity=100_000, is_active=True) for k, f in granjas.items()}
        s.add_all(galpones.values())
        await s.flush()

        def _lote(empresa, marca, tipo, g):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE,
                       farm_id=granjas[g].id, house_id=galpones[g].id)

        lotes = {"lg": _lote(a, "LG", BirdTypeEnum.GRANDPARENT, "granja_a"), "lr": _lote(a, "LR", BirdTypeEnum.BREEDER, "granja_a"),
                 "lgb": _lote(b, "LGB", BirdTypeEnum.GRANDPARENT, "granja_b"), "lgc": _lote(c, "LGC", BirdTypeEnum.GRANDPARENT, "granja_c")}
        s.add_all(lotes.values())
        sup_a = Supplier(company_id=a.id, name=f"{PREFIJO}PROVEEDOR-A", country="Francia", supplier_type="international", is_active=True)
        sup_b = Supplier(company_id=b.id, name=f"{PREFIJO}PROVEEDOR-B", country="Francia", supplier_type="international", is_active=True)
        tr_a = Transport(company_id=a.id, name=f"{PREFIJO}TRANSPORTE-A", plate="ABUE-A", is_active=True)
        tr_b = Transport(company_id=b.id, name=f"{PREFIJO}TRANSPORTE-B", plate="ABUE-B", is_active=True)
        sup_c = Supplier(company_id=c.id, name=f"{PREFIJO}PROVEEDOR-C", country="Francia", supplier_type="international", is_active=True)
        tr_c = Transport(company_id=c.id, name=f"{PREFIJO}TRANSPORTE-C", plate="ABUE-C", is_active=True)
        s.add_all([sup_a, sup_b, tr_a, tr_b, sup_c, tr_c])
        s.add(SapReference(company_id=a.id, ref_type=SapReferenceType.PURCHASE_ORDER, sap_code="ABUE-OC-A", quantity=100, unit="aves", is_active=True))
        s.add(SapReference(company_id=c.id, ref_type=SapReferenceType.PURCHASE_ORDER, sap_code="ABUE-OC-C", quantity=100, unit="aves", is_active=True))
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "c": c.id, "url": test_database_url, "sup_a": sup_a.id, "sup_b": sup_b.id, "sup_c": sup_c.id,
             "tr_a": tr_a.id, "tr_b": tr_b.id, "tr_c": tr_c.id}
        d.update({k: v.id for k, v in granjas.items()}); d.update({f"galpon_{k[-1]}": v.id for k, v in galpones.items()})
        d.update({k: v.id for k, v in u.items()}); d.update({k: v.id for k, v in lotes.items()})
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
            "DELETE FROM evidences WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
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
    for empresa in (d["a"], d["b"], d["c"]):  # adjuntos del servidor (`MEDIA_DIR/evidences/<empresa>`)
        shutil.rmtree(os.path.join(os.environ.get("MEDIA_DIR", "/app/media"), "evidences", str(empresa)), ignore_errors=True)


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


async def _eventos(esc, lote, tipo="grandparent_import") -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE :t", l=lote, t=tipo)


def _plan(**cambios) -> dict:
    plan = {"origin_country": "Francia", "purchased_total": 110, "shipped_total": 105, "received_total": 100, "transit_mortality": 5,
            "departure_date": earlier_event_date(), "arrival_date": recent_event_date(), "reception_condition": "buena",
            "quarantine_days": 21, "quarantine_end_date": iso_days_ago(-14), "initial_health_inspection": "sin hallazgos"}
    plan.update(cambios)
    return {k: v for k, v in plan.items() if v is not ...}


def _importacion(esc, lote="lg", *, plan=None, filas=None, **extra) -> dict:
    g = {"lg": "a", "lr": "a", "lgb": "b", "lgc": "c"}[lote]
    cuerpo = {"lot_id": esc[lote], "event_type": "grandparent_import", "event_date": recent_event_date(),
              "farm_id": esc[f"granja_{g}"], "house_id": esc[f"galpon_{g}"],
              "sap_document_ref": f"ABUE-OC-{g.upper()}", "supplier_id": esc[f"sup_{g}"], "transport_id": esc[f"tr_{g}"],  # maestros de la empresa del lote
              "bird_movements": filas if filas is not None else [{"sex": "male", "quantity": 40}, {"sex": "female", "quantity": 60}],
              "extra_data": {"import_plan": plan if plan is not None else _plan()}}
    cuerpo.update(extra)
    return {k: v for k, v in cuerpo.items() if v is not ...}


async def _post(http_client, esc, actor, cuerpo, company_id=None):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=cuerpo)


async def _recepcion(esc, lote, n, oc="ABUE-OC-A"):
    g = "a"
    return {"lot_id": esc[lote], "event_type": "bird_reception", "event_date": recent_event_date(), "farm_id": esc[f"granja_{g}"], "house_id": esc[f"galpon_{g}"],
            "sap_document_ref": oc, "bird_movements": [{"sex": "mixed", "quantity": n}]}


async def _sin_rastro(esc, lote, antes_eventos, antes_aud):
    assert await _eventos(esc, esc[lote]) == antes_eventos, "sin fila"
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE action::text ILIKE 'created' AND lot_id = :l", l=esc[lote]) == antes_aud, "sin auditoría de alta"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R152-01 · 08 · 19 — control: la importación completa se registra; es documental (no puebla); se anula sin efecto
# ═══════════════════════════════════════════════════════════════════════════

async def test_r152_01_08_19_la_importacion_completa_es_documental_y_se_anula_sin_efecto(http_client, esc):
    r = await _post(http_client, esc, "op_gp", _importacion(esc))
    assert r.status_code == 201, ("AC-R152-01: actor con solo grandparent", r.text)
    evento = r.json()
    assert evento["extra_data"]["import_plan"]["received_total"] == 100 and evento["supplier_id"] == esc["sup_a"] and evento["sap_document_ref"] == "ABUE-OC-A"
    assert await _saldo(esc, esc["lg"]) == 0, "AC-R152-08: la importación no puebla el lote"
    r2 = await http_client.post("/api/v1/operations", headers=_token(esc["op_gp"]), json=await _recepcion(esc, "lg", 100))
    assert r2.status_code == 201, ("AC-R152-08: la recepción con la misma OC de 100 pasa (la importación no acumula contra la OC)", r2.text)
    assert await _saldo(esc, esc["lg"]) == 100, "AC-R152-08: la población entra una vez, por la recepción"
    assert (await http_client.post(f"/api/v1/operations/{evento['id']}/cancel", headers=_token(esc["op_gp"]))).status_code == 200, "AC-R152-19"
    assert await _saldo(esc, esc["lg"]) == 100
    assert (await http_client.post(f"/api/v1/operations/{evento['id']}/cancel", headers=_token(esc["op_gp"]))).status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R152-02 · 03 · 05 · 09 — estructura e identidades (BR-22); proveedor/transporte; BR-20 prohibida (control)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r152_02_sin_plan_se_deniega(http_client, esc):
    antes, aud = await _eventos(esc, esc["lg"]), await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE action::text ILIKE 'created' AND lot_id = :l", l=esc["lg"])
    cuerpo = _importacion(esc, extra_data={"supplier": "Internacional"})  # el cuerpo de hoy (E2E p01)
    r = await _post(http_client, esc, "op_gp", cuerpo)
    assert _es_br(r, "BR-22"), ("AC-R152-02: sin plan de importación", r.status_code, r.text)
    await _sin_rastro(esc, "lg", antes, aud)
    r = await _post(http_client, esc, "op_gp", _importacion(esc, extra_data=None))
    assert _es_br(r, "BR-22"), ("AC-R152-02: sin extra_data", r.status_code, r.text)
    await _sin_rastro(esc, "lg", antes, aud)


@pytest.mark.parametrize("etiqueta,cambios,filas", [
    ("embarcada ≠ recibida + mortalidad", {"shipped_total": 104}, None),
    ("recibida ≠ Σ ♂/♀", {}, [{"sex": "male", "quantity": 40}, {"sex": "female", "quantity": 59}]),
    ("llegada anterior a la salida", {"departure_date": recent_event_date(), "arrival_date": earlier_event_date()}, None),
    ("fin de cuarentena anterior a la llegada", {"quarantine_end_date": earlier_event_date()}, None),
    ("sin país", {"origin_country": ""}, None),
    ("sin filas ♂/♀", {}, []),
])
async def test_r152_03_identidades_del_plan(http_client, esc, etiqueta, cambios, filas):
    antes = await _eventos(esc, esc["lg"])
    r = await _post(http_client, esc, "op_gp", _importacion(esc, plan=_plan(**cambios), filas=filas))
    assert _es_br(r, "BR-22"), (f"AC-R152-03 · {etiqueta}", r.status_code, r.text)
    assert await _eventos(esc, esc["lg"]) == antes


async def test_r152_03b_cantidad_comprada_cero_se_rechaza(http_client, esc):
    r = await _post(http_client, esc, "op_gp", _importacion(esc, plan=_plan(purchased_total=0)))
    assert r.status_code in (400, 422), ("AC-R152-03: comprada = 0", r.status_code, r.text)
    assert await _eventos(esc, esc["lg"]) == 0


async def test_r152_05_09_oc_proveedor_transporte_y_tupla_de_recepcion(http_client, esc):
    antes = await _eventos(esc, esc["lg"])
    assert _es_br(await _post(http_client, esc, "op_gp", _importacion(esc, sap_document_ref=None)), "BR-22"), "AC-R152-05: sin OC"
    assert _es_br(await _post(http_client, esc, "op_gp", _importacion(esc, supplier_id=None)), "BR-22"), "AC-R152-05: sin proveedor"
    r = await _post(http_client, esc, "op_gp", _importacion(esc, supplier_id=esc["sup_b"]))
    assert _es_br(r, "BR-07"), ("AC-R152-05: proveedor de otra empresa", r.status_code, r.text)
    r = await _post(http_client, esc, "op_gp", _importacion(esc, transport_id=esc["tr_b"]))
    assert _es_br(r, "BR-07"), ("AC-R152-05: transporte de otra empresa", r.status_code, r.text)
    r = await _post(http_client, esc, "op_gp", _importacion(esc, dead_on_arrival=5))
    assert _es_br(r, "BR-20"), ("AC-R152-09: la tupla de la recepción de reproductoras está prohibida en la importación (control)", r.status_code, r.text)
    assert await _eventos(esc, esc["lg"]) == antes


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R152-04 — Progenitoras ≠ Reproductoras: la importación solo sobre un lote grandparent
# ═══════════════════════════════════════════════════════════════════════════

async def test_r152_04_la_importacion_solo_sobre_un_lote_de_abuelas(http_client, esc):
    r = await _post(http_client, esc, "op_ambos", _importacion(esc, "lr"))
    assert _es_br(r, "BR-22"), ("AC-R152-04: lote breeder", r.status_code, r.text)
    assert await _eventos(esc, esc["lr"]) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R152-06 · 07 — adjuntos clasificados
# ═══════════════════════════════════════════════════════════════════════════

async def _adjuntar(http_client, esc, event_id, clase=None):
    datos = {"description": f"{PREFIJO}adjunto"}
    if clase is not None:
        datos["evidence_type"] = clase
    return await http_client.post(f"/api/v1/operations/{event_id}/evidences", headers=_token(esc["op_gp"]),
                                  files={"file": (f"{PREFIJO}doc.pdf", b"%PDF-1.4\n%abue\n", "application/pdf")}, data=datos)


async def test_r152_06_07_los_adjuntos_del_plan_se_clasifican(http_client, esc):
    evento = (await _post(http_client, esc, "op_gp", _importacion(esc))).json()
    for clase in CLASES:
        r = await _adjuntar(http_client, esc, evento["id"], clase)
        assert r.status_code == 201 and r.json()["evidence_type"] == clase, (f"AC-R152-06 · {clase}", r.status_code, r.text)
    r = await _adjuntar(http_client, esc, evento["id"], "banana")
    assert r.status_code == 400, ("AC-R152-07: clase fuera del conjunto", r.status_code, r.text)
    r = await _adjuntar(http_client, esc, evento["id"])
    assert r.status_code == 201 and r.json()["evidence_type"] == "document", "AC-R152-07: sin clase → derivada del MIME (control)"
    assert await _cuenta(esc, "SELECT count(*) FROM evidences WHERE event_id = :e", e=evento["id"]) == 6


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R152-10 … 16 — cadena de seguridad sobre la importación (controles)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r152_10_11_las_concesiones_no_se_heredan_entre_unidades(http_client, esc):
    r = await _post(http_client, esc, "op_br", _importacion(esc))
    assert _es_br(r, "BR-07"), ("AC-R152-10: solo breeder no importa abuelas", r.status_code, r.text)
    assert await _eventos(esc, esc["lg"]) == 0
    r = await _post(http_client, esc, "op_gp", _importacion(esc))
    assert r.status_code == 201, ("AC-R152-11: solo grandparent importa sin necesitar breeder", r.text)
    r = await http_client.post("/api/v1/operations", headers=_token(esc["op_gp"]), json=await _recepcion(esc, "lr", 10, oc="ABUE-OC-A"))
    assert _es_br(r, "BR-07"), ("AC-R152-11: grandparent no autoriza reproductoras", r.status_code, r.text)


async def test_r152_11b_una_empresa_con_progenitoras_y_sin_reproductoras_importa(http_client, esc):
    r = await _post(http_client, esc, "op_c", _importacion(esc, "lgc"))
    assert r.status_code == 201, ("AC-R152-11b: grandparent es unidad de primera clase", r.text)


async def test_r152_12_13_14_empresa_apagada_global_e_inquilino(http_client, esc):
    assert _es_br(await _post(http_client, esc, "actor_b", _importacion(esc, "lgb")), "BR-07"), "AC-R152-12: grandparent apagada en B (concesión histórica)"
    assert (await _post(http_client, esc, "global", _importacion(esc, "lgb"), company_id=esc["b"])).status_code == 403, "AC-R152-12: global situada en B"
    assert _es_br(await _post(http_client, esc, "global", _importacion(esc)), "BR-07"), "AC-R152-13: global sin empresa"
    r = await _post(http_client, esc, "global", _importacion(esc), company_id=esc["a"])
    assert r.status_code == 201, ("AC-R152-13: global situada en A sobre unidad habilitada (AC-W14)", r.text)
    assert _es_br(await _post(http_client, esc, "actor_b", _importacion(esc)), "BR-07"), "AC-R152-14: lote de A para actor de B"
    assert await _eventos(esc, esc["lgb"]) == 0


async def test_r152_15_16_rbac_administrador_de_accesos_y_contraloria(http_client, esc):
    for actor in ("sin_perm", "acceso", "lectura"):
        r = await _post(http_client, esc, actor, _importacion(esc))
        assert r.status_code == 403, (f"AC-R152-15/16 · {actor}", r.status_code, r.text)
    assert await _eventos(esc, esc["lg"]) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R152-17 · 18 — edición y corrección revalidan el plan (BR-22) y la pertenencia
# ═══════════════════════════════════════════════════════════════════════════

async def _evento(esc, event_id):
    f = (await _sql(esc, "SELECT lot_id, extra_data::text, supplier_id, status::text FROM operational_events WHERE id = :e", e=event_id))[0]
    return {"lot_id": f[0], "extra_data": json.loads(f[1]) if f[1] else None, "supplier_id": f[2], "status": f[3].lower()}


async def test_r152_17_la_edicion_revalida_el_plan(http_client, esc):
    evento = (await _post(http_client, esc, "op_ambos", _importacion(esc))).json()
    antes = await _evento(esc, evento["id"])
    r = await http_client.put(f"/api/v1/operations/{evento['id']}", headers=_token(esc["op_ambos"]), json={"extra_data": {"import_plan": _plan(shipped_total=999)}})
    assert _es_br(r, "BR-22"), ("AC-R152-17: identidad rota por PUT", r.status_code, r.text)
    assert await _evento(esc, evento["id"]) == antes
    r = await http_client.put(f"/api/v1/operations/{evento['id']}", headers=_token(esc["op_ambos"]), json={"lot_id": esc["lr"]})
    assert _es_br(r, "BR-22"), ("AC-R152-17: mover la importación a un lote breeder", r.status_code, r.text)
    r = await http_client.put(f"/api/v1/operations/{evento['id']}", headers=_token(esc["op_ambos"]), json={"supplier_id": esc["sup_b"]})
    assert _es_br(r, "BR-07"), ("AC-R152-17: proveedor de otra empresa por PUT", r.status_code, r.text)
    aud = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE action::text ILIKE 'created' AND lot_id = :l", l=esc["lg"])
    r = await http_client.put(f"/api/v1/operations/{evento['id']}", headers=_token(esc["op_ambos"]), json={"extra_data": {"import_plan": _plan(quarantine_days=28, quarantine_end_date=iso_days_ago(-21))}})
    assert r.status_code == 200, ("AC-R152-17: edición válida", r.text)
    assert (await _evento(esc, evento["id"]))["extra_data"]["import_plan"]["quarantine_days"] == 28
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE action::text ILIKE 'created' AND lot_id = :l", l=esc["lg"]) == aud, "sin repetir el alta"


async def test_r152_18_la_correccion_revalida_el_plan(http_client, esc):
    evento = (await _post(http_client, esc, "op_ambos", _importacion(esc))).json()
    antes = await _evento(esc, evento["id"])

    async def _corregir(campo, valor):
        return await http_client.post("/api/v1/corrections", headers=_token(esc["op_ambos"]),
                                      json={"event_id": evento["id"], "field_name": campo, "corrected_value": valor, "reason": f"{PREFIJO}corrección de prueba"})

    r = await _corregir("extra_data", json.dumps({"import_plan": _plan(transit_mortality=50)}))
    assert _es_br(r, "BR-22"), ("AC-R152-18: identidad rota por corrección", r.status_code, r.text)
    assert await _evento(esc, evento["id"]) == antes
    r = await _corregir("supplier_id", str(esc["sup_b"]))
    assert _es_br(r, "BR-07"), ("AC-R152-18: proveedor de otra empresa por corrección", r.status_code, r.text)
    r = await _corregir("extra_data", json.dumps({"import_plan": _plan(reception_condition="regular")}))
    assert r.status_code == 201, ("AC-R152-18: corrección válida", r.text)
    despues = await _evento(esc, evento["id"])
    assert despues["extra_data"]["import_plan"]["reception_condition"] == "regular" and despues["status"] == "corrected"
