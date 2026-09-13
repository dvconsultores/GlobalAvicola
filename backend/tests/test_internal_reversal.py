"""`GA-REM-041` · `R-136` (componente interno) · reverso interno de registros aprobados (`OD-19`).

Cada original se siembra **aprobado** con sus movimientos; la solicitud crea la contrapartida en la cola de revisión y la
aprobación (start + approve por un aprobador ≠ solicitante) aplica la compensación. Las unidades se siembran ON/OFF
explícitamente (`BU-D10` no interviene).

    Empresa A   breeder ON · grandparent ON · hatchery OFF · lotes LR, LR2 (breeder) · LG (grandparent) · LH (hatchery)
                LR: recepción 100 + mortalidad 10 (saldo 90) · LR2: recepción 100 + mortalidad 30 (saldo 70)
    Empresa B   breeder ON · lote LB · original aprobado
    SOLICITANTE reversals:create/read · operations:create/read · lots:read · breeder + hatchery (histórica; OFF)
    SOLICITANTE_G  ídem · solo grandparent
    CORRECTOR   corrections:correct · operations:read/update · breeder
    APROBADOR   approvals:approve/reject · review:review/read · operations:read · breeder
    SIN_PERM    operations:read · breeder        LECTURA  review/corrections/audit/reversals:read · breeder
    ACCESO      Administrador de Accesos          ACTOR_B  reversals:create en B         GLOBAL ("*", all)
"""
from __future__ import annotations

import asyncio
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

pytestmark = pytest.mark.asyncio

PREFIJO = "REV-"


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
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus
    from app.operations.models import BirdMovement, EggMovement, EventStatus, EventType, OperationalEvent

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True, approval_levels=2)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True, approval_levels=2)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "grandparent", True), (a, "hatchery", False), (b, "breeder", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        roles = {
            "solicitante": _rol("Sol", a.id, [("reversals", PA.CREATE), ("reversals", PA.READ), ("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]),
            "corrector": _rol("Corr", a.id, [("corrections", PA.CORRECT), ("operations", PA.READ), ("operations", PA.UPDATE)]),
            "aprobador": _rol("Apr", a.id, [("approvals", PA.APPROVE), ("approvals", PA.REJECT), ("review", PA.REVIEW), ("review", PA.READ), ("operations", PA.READ)]),
            "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]),
            "lectura": _rol("Lectura", a.id, [("review", PA.READ), ("corrections", PA.READ), ("audit", PA.READ), ("reversals", PA.READ), ("operations", PA.READ)]),
            "acceso": _rol("Acceso", a.id, [("business_units", PA.READ), ("business_units", PA.CREATE), ("business_units", PA.UPDATE), ("business_units", PA.DELETE)]),
            "b": _rol("SolB", b.id, [("reversals", PA.CREATE), ("operations", PA.READ)]),
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
            return User(first_name=marca, last_name="Rev", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {"solicitante": _usuario(a.id, "SOL", roles["solicitante"][0]), "solicitante_g": _usuario(a.id, "SOLG", roles["solicitante"][0]),
             "corrector": _usuario(a.id, "CORR", roles["corrector"][0]), "aprobador": _usuario(a.id, "APR", roles["aprobador"][0]),
             "sin_perm": _usuario(a.id, "SINPERM", roles["sin_perm"][0]), "lectura": _usuario(a.id, "LECT", roles["lectura"][0]),
             "acceso": _usuario(a.id, "ACC", roles["acceso"][0]), "actor_b": _usuario(b.id, "B", roles["b"][0]),
             "global": _usuario(None, "GLOBAL", roles["global"][0])}
        s.add_all(u.values())
        await s.flush()
        for k in ("solicitante", "corrector", "aprobador", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=u["solicitante"], company_business_unit=hab[(a.id, "hatchery")])
        await conceder_unidad(s, user=u["aprobador"], company_business_unit=hab[(a.id, "grandparent")])
        await conceder_unidad(s, user=u["solicitante_g"], company_business_unit=hab[(a.id, "grandparent")])
        await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, "breeder")])

        granja_a = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add(granja_a)
        await s.flush()
        galpon_a = House(farm_id=granja_a.id, name=f"{PREFIJO}GALPON-A", capacity=10_000, is_active=True)
        s.add(galpon_a)
        await s.flush()

        def _lote(empresa, marca, tipo):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE)

        lr, lr2, lg, lh, lb = (_lote(a, "LR", BirdTypeEnum.BREEDER), _lote(a, "LR2", BirdTypeEnum.BREEDER), _lote(a, "LG", BirdTypeEnum.GRANDPARENT),
                               _lote(a, "LH", BirdTypeEnum.HATCHERY), _lote(b, "LB", BirdTypeEnum.BREEDER))
        s.add_all([lr, lr2, lg, lh, lb])
        await s.flush()

        def _evento(empresa, lote, tipo, estado, autor, aves=None):
            ev = OperationalEvent(company_id=empresa.id, lot_id=lote.id, farm_id=granja_a.id if empresa is a else None,
                                  house_id=galpon_a.id if empresa is a else None, event_type=tipo, event_date=date.today(),
                                  status=estado, registered_by_id=autor.id, version=1, observations=f"{PREFIJO}{tipo.value}-{estado.value}")
            s.add(ev)
            return ev, aves

        pares = {
            "rec100": _evento(a, lr, EventType.BIRD_RECEPTION, EventStatus.APPROVED, u["solicitante"], 100),
            "mort10": _evento(a, lr, EventType.MORTALITY_RECORDING, EventStatus.APPROVED, u["solicitante"], 10),
            "rec100b": _evento(a, lr2, EventType.BIRD_RECEPTION, EventStatus.APPROVED, u["solicitante"], 100),
            "mort30": _evento(a, lr2, EventType.MORTALITY_RECORDING, EventStatus.APPROVED, u["solicitante"], 30),
            "reg": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.REGISTERED, u["solicitante"]),
            "pend": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.PENDING_REVIEW, u["solicitante"]),
            "ret": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.RETURNED, u["solicitante"]),
            "rej": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.REJECTED, u["solicitante"]),
            "corr": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.CORRECTED, u["solicitante"]),
            "canc": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.CANCELLED, u["solicitante"]),
            "sap": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.SAP_CONFIRMED, u["solicitante"]),
            "cons": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.CONSOLIDATED, u["solicitante"]),
            "insp": _evento(a, lr, EventType.FARM_INSPECTION, EventStatus.APPROVED, u["solicitante"]),
            "egg": _evento(a, lr, EventType.EGG_COLLECTION, EventStatus.APPROVED, u["solicitante"]),
            "lg": _evento(a, lg, EventType.FARM_INSPECTION, EventStatus.APPROVED, u["solicitante_g"]),
            "lh": _evento(a, lh, EventType.FARM_INSPECTION, EventStatus.APPROVED, u["solicitante"]),
            "lb": _evento(b, lb, EventType.FARM_INSPECTION, EventStatus.APPROVED, u["actor_b"]),
        }
        await s.flush()
        for clave, (ev, aves) in pares.items():
            if aves is not None:
                s.add(BirdMovement(event_id=ev.id, sex="mixed", quantity=aves))
        s.add(EggMovement(event_id=pares["egg"][0].id, egg_type="fertile", quantity=50))
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "lr": lr.id, "lr2": lr2.id, "lg": lg.id, "lh": lh.id, "lb": lb.id, "url": test_database_url}
        d.update({k: v.id for k, v in u.items()})
        d.update({f"ev_{k}": v[0].id for k, v in pares.items()})
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
            "DELETE FROM approval_steps WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
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

MOTIVO = f"{PREFIJO}registro duplicado por error del operador"


async def _sql(esc, sql, **params):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(sql), params)).all()
    finally:
        await motor.dispose()


async def _estado(esc, ev):
    return str((await _sql(esc, "SELECT status FROM operational_events WHERE id = :e", e=ev))[0][0]).lower().split(".")[-1]


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


async def _solicitar(http_client, esc, actor, ev, company_id=None, **cuerpo):
    datos = {"event_id": esc[ev], "reason": MOTIVO}
    datos.update(cuerpo)
    return await http_client.post("/api/v1/reversals", headers=_token(esc[actor], company_id), json=datos)


async def _contrapartida(esc, ev) -> int | None:
    filas = await _sql(esc, "SELECT reversal_event_id FROM reversals WHERE original_event_id = :e ORDER BY id DESC", e=esc[ev])
    return filas[0][0] if filas else None


async def _aprobar_reverso(http_client, esc, contrapartida, actor="aprobador"):
    r = await http_client.post(f"/api/v1/review/start/{contrapartida}", headers=_token(esc[actor]))
    assert r.status_code == 200, r.text
    return await http_client.post("/api/v1/approvals/approve", headers=_token(esc[actor]), json={"event_id": contrapartida})


async def _reverso_efectivo(http_client, esc, ev):
    r = await _solicitar(http_client, esc, "solicitante", ev)
    assert r.status_code == 201, r.text
    cp = await _contrapartida(esc, ev)
    r2 = await _aprobar_reverso(http_client, esc, cp)
    return r, cp, r2


# ═══════════════════════════════════════════════════════════════════════════
#  AC-RV · elegibilidad
# ═══════════════════════════════════════════════════════════════════════════

async def test_rv01_la_solicitud_crea_la_contrapartida_y_el_original_sigue_aprobado(http_client, esc):
    r = await _solicitar(http_client, esc, "solicitante", "ev_mort10")
    assert r.status_code == 201, r.text
    cp = await _contrapartida(esc, "ev_mort10")
    assert cp is not None and await _estado(esc, cp) == "pending_review"
    assert await _estado(esc, esc["ev_mort10"]) == "approved"
    assert r.json()["original_event_id"] == esc["ev_mort10"] and r.json()["reversal_event_id"] == cp


async def test_rv02_los_estados_no_elegibles_se_rechazan(http_client, esc):
    for ev in ("ev_reg", "ev_pend", "ev_ret", "ev_rej", "ev_corr", "ev_canc", "ev_sap", "ev_cons"):
        r = await _solicitar(http_client, esc, "solicitante", ev)
        assert r.status_code == 400 and r.json().get("rule") == "BR-16", (ev, r.text)
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE company_id = :a", a=esc["a"]) == 0


async def test_rv03_ef04_un_original_admite_una_sola_contrapartida_efectiva(http_client, esc):
    _, cp, r2 = await _reverso_efectivo(http_client, esc, "ev_mort10")
    assert r2.status_code == 200, r2.text
    r = await _solicitar(http_client, esc, "solicitante", "ev_mort10")
    assert r.status_code == 400 and r.json().get("rule") == "BR-16", r.text
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE original_event_id = :e", e=esc["ev_mort10"]) == 1
    assert await _saldo(esc, esc["lr"]) == 100, "AC-EF04: efecto extra 0"


async def test_rv03_con_solicitud_activa_la_segunda_es_409(http_client, esc):
    assert (await _solicitar(http_client, esc, "solicitante", "ev_mort10")).status_code == 201
    r = await _solicitar(http_client, esc, "solicitante", "ev_mort10")
    assert r.status_code == 409, r.text
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE original_event_id = :e", e=esc["ev_mort10"]) == 1


async def test_rv04_la_contrapartida_cancelada_no_es_efectiva_y_permite_nueva_solicitud(http_client, esc):
    assert (await _solicitar(http_client, esc, "solicitante", "ev_insp")).status_code == 201
    cp = await _contrapartida(esc, "ev_insp")
    r = await http_client.post(f"/api/v1/operations/{cp}/cancel", headers=_token(esc["solicitante"]))
    assert r.status_code == 200, r.text
    assert await _estado(esc, esc["ev_insp"]) == "approved"
    r = await _solicitar(http_client, esc, "solicitante", "ev_insp")
    assert r.status_code == 201, r.text


async def test_rv05_rv02_control_los_corregibles_no_entran_en_el_reverso(http_client, esc):
    for ev in ("ev_ret", "ev_rej"):
        assert (await _solicitar(http_client, esc, "solicitante", ev)).status_code == 400


async def test_rv06_el_original_y_la_contrapartida_son_inmutables(http_client, esc):
    r = await http_client.put(f"/api/v1/operations/{esc['ev_mort10']}", headers=_token(esc["solicitante"]), json={"observations": "x"})
    assert r.status_code == 400, "control: el aprobado no se edita"
    _, cp, r2 = await _reverso_efectivo(http_client, esc, "ev_mort10")
    assert r2.status_code == 200, r2.text
    for ev in (esc["ev_mort10"], cp):
        assert (await http_client.put(f"/api/v1/operations/{ev}", headers=_token(esc["solicitante"]), json={"observations": "x"})).status_code == 400
        assert (await http_client.post(f"/api/v1/operations/{ev}/submit", headers=_token(esc["solicitante"]))).status_code == 400
        r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                                   json={"event_id": ev, "field_name": "observations", "corrected_value": "y", "reason": MOTIVO})
        assert r.status_code == 400, r.text


async def test_rv06_la_contrapartida_pendiente_no_se_edita_ni_corrige(http_client, esc):
    assert (await _solicitar(http_client, esc, "solicitante", "ev_mort10")).status_code == 201
    cp = await _contrapartida(esc, "ev_mort10")
    assert (await http_client.put(f"/api/v1/operations/{cp}", headers=_token(esc["solicitante"]), json={"observations": "x"})).status_code == 400
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                               json={"event_id": cp, "field_name": "observations", "corrected_value": "y", "reason": MOTIVO})
    assert r.status_code == 400, r.text


async def test_rv07_huevos_e_incubacion_quedan_bloqueados_por_r161(http_client, esc):
    r = await _solicitar(http_client, esc, "solicitante", "ev_egg")
    assert r.status_code == 400 and r.json().get("rule") == "BR-16" and "R-161" in r.text, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  AC-EF · efecto
# ═══════════════════════════════════════════════════════════════════════════

async def test_ef01_ef03_el_reverso_aprobado_restaura_exactamente_el_saldo_previo(http_client, esc):
    assert await _saldo(esc, esc["lr"]) == 90
    _, cp, r2 = await _reverso_efectivo(http_client, esc, "ev_mort10")
    assert r2.status_code == 200, r2.text
    assert await _saldo(esc, esc["lr"]) == 100, "AC-EF01/EF03: 100 → −10 → 90 → +10 → 100"
    assert await _estado(esc, esc["ev_mort10"]) == "reversed" and await _estado(esc, cp) == "reversed"
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE id IN (:a, :b)", a=esc["ev_mort10"], b=cp) == 2, "la historia conserva ambas filas"


async def test_ef02_ef05_un_reverso_que_dejaria_saldo_negativo_no_se_aplica_y_no_deja_efectos(http_client, esc):
    assert await _saldo(esc, esc["lr2"]) == 70
    r = await _solicitar(http_client, esc, "solicitante", "ev_rec100b")
    assert r.status_code == 201, r.text
    cp = await _contrapartida(esc, "ev_rec100b")
    audit0 = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE action::text ILIKE 'reversed'")
    r2 = await _aprobar_reverso(http_client, esc, cp)
    assert r2.status_code == 400 and r2.json().get("rule") == "BR-01", r2.text
    assert await _saldo(esc, esc["lr2"]) == 70
    assert await _estado(esc, esc["ev_rec100b"]) == "approved" and await _estado(esc, cp) == "in_review"
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE action::text ILIKE 'reversed'") == audit0, "AC-EF05/AU06"


async def test_ef06_dos_solicitudes_concurrentes_producen_una_sola_contrapartida(http_client, esc):
    async def _una():
        return await _solicitar(http_client, esc, "solicitante", "ev_mort10")
    r1, r2 = await asyncio.gather(_una(), _una())
    assert sorted([r1.status_code, r2.status_code]) == [201, 409], (r1.text, r2.text)
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE original_event_id = :e", e=esc["ev_mort10"]) == 1


async def test_ef07_un_evento_sin_efecto_de_saldo_se_reversa_sin_tocar_el_saldo(http_client, esc):
    saldo0 = await _saldo(esc, esc["lr"])
    _, cp, r2 = await _reverso_efectivo(http_client, esc, "ev_insp")
    assert r2.status_code == 200, r2.text
    assert await _estado(esc, esc["ev_insp"]) == "reversed" and await _estado(esc, cp) == "reversed"
    assert await _saldo(esc, esc["lr"]) == saldo0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-S · seguridad
# ═══════════════════════════════════════════════════════════════════════════

async def test_s01_s02_otra_empresa_y_la_global_sin_contexto_fallan_cerradas(http_client, esc):
    assert (await _solicitar(http_client, esc, "actor_b", "ev_mort10")).status_code == 404
    assert (await _solicitar(http_client, esc, "global", "ev_mort10")).status_code in (403, 404)
    assert (await _solicitar(http_client, esc, "global", "ev_mort10", company_id=esc["b"])).status_code == 404
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE original_event_id = :e", e=esc["ev_mort10"]) == 0


async def test_s03_s04_la_unidad_apagada_o_no_concedida_no_se_reversa(http_client, esc):
    assert (await _solicitar(http_client, esc, "solicitante", "ev_lh")).status_code == 404, "apagada con concesión histórica"
    r = await _solicitar(http_client, esc, "global", "ev_lh", company_id=esc["a"])
    # `OD-16` (`9ffc5ec`): la unidad apagada es fail-closed en la frontera productiva (404).
    assert r.status_code == 404, r.text
    assert (await _solicitar(http_client, esc, "solicitante", "ev_lg")).status_code == 404, "habilitada, no concedida"
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE company_id = :a", a=esc["a"]) == 0


async def test_s05_s07_sin_capacidad_de_reverso_no_hay_reverso(http_client, esc):
    for actor in ("sin_perm", "acceso", "lectura", "corrector", "aprobador"):
        r = await _solicitar(http_client, esc, actor, "ev_mort10")
        assert r.status_code == 403, (actor, r.text)
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE company_id = :a", a=esc["a"]) == 0


async def test_s08_el_cuerpo_no_es_autoridad_sobre_cantidades_ni_empresa(http_client, esc):
    for extra in ({"quantity": 5}, {"company_id": esc["b"]}, {"reversal_event_id": 1}, {"status": "reversed"}):
        r = await http_client.post("/api/v1/reversals", headers=_token(esc["solicitante"]),
                                   json={"event_id": esc["ev_mort10"], "reason": MOTIVO, **extra})
        assert r.status_code == 422, (extra, r.text)


async def test_s09_progenitoras_reversa_lo_suyo_y_no_lo_de_reproductoras(http_client, esc):
    assert (await _solicitar(http_client, esc, "solicitante_g", "ev_mort10")).status_code == 404
    r = await _solicitar(http_client, esc, "solicitante_g", "ev_lg")
    assert r.status_code == 201, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  AC-AU · motivo y auditoría
# ═══════════════════════════════════════════════════════════════════════════

async def test_au01_au02_el_motivo_es_obligatorio_y_no_vacio(http_client, esc):
    r = await http_client.post("/api/v1/reversals", headers=_token(esc["solicitante"]), json={"event_id": esc["ev_mort10"]})
    assert r.status_code == 422, r.text
    for motivo in ("", "     ", "abc"):
        assert (await _solicitar(http_client, esc, "solicitante", "ev_mort10", reason=motivo)).status_code == 422, motivo
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE original_event_id = :e", e=esc["ev_mort10"]) == 0


async def test_au03_au05_la_historia_completa_queda_registrada(http_client, esc):
    _, cp, r2 = await _reverso_efectivo(http_client, esc, "ev_mort10")
    assert r2.status_code == 200, r2.text
    fila = (await _sql(esc, "SELECT reason, reversed_by_id, created_at, original_data_snapshot, reversal_event_id FROM reversals WHERE original_event_id = :e", e=esc["ev_mort10"]))[0]
    assert fila[0] == MOTIVO and fila[1] == esc["solicitante"] and fila[2] is not None and fila[4] == cp
    assert "10" in str(fila[3]), "AC-AU05: la instantánea conserva la cantidad original"
    assert (await _sql(esc, "SELECT approved_by_id FROM operational_events WHERE id = :e", e=cp))[0][0] == esc["aprobador"], "AC-AU03: aprobador"
    trans = await _sql(esc, "SELECT entity_id, previous_state, new_state FROM audit_logs WHERE action::text ILIKE 'reversed' AND entity_id IN (:a, :b)", a=str(esc["ev_mort10"]), b=str(cp))
    pares = {(f[0], f[1], f[2]) for f in trans}
    assert (str(esc["ev_mort10"]), "approved", "reversed") in pares and (str(cp), "in_review", "reversed") in pares, pares


async def test_au06_una_solicitud_denegada_no_deja_fila_ni_auditoria(http_client, esc):
    antes = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'reversal'")
    assert (await _solicitar(http_client, esc, "sin_perm", "ev_mort10")).status_code == 403
    assert (await _solicitar(http_client, esc, "solicitante", "ev_canc")).status_code == 400
    assert await _cuenta(esc, "SELECT count(*) FROM reversals WHERE company_id = :a", a=esc["a"]) == 0
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'reversal'") == antes


async def test_rv01_control_las_lecturas_muestran_el_reverso_a_quien_puede_leerlo(http_client, esc):
    assert (await _solicitar(http_client, esc, "solicitante", "ev_mort10")).status_code == 201
    r = await http_client.get(f"/api/v1/reversals/event/{esc['ev_mort10']}", headers=_token(esc["lectura"]))
    assert r.status_code == 200 and len(r.json()) == 1, r.text
    r = await http_client.get("/api/v1/reversals", headers=_token(esc["actor_b"]))
    assert r.status_code == 403, "B no tiene reversals:read"
    r = await http_client.get("/api/v1/reversals", headers=_token(esc["lectura"]))
    assert r.status_code == 200 and all(f["original_event_id"] != esc["ev_lb"] for f in r.json()["reversals"])
