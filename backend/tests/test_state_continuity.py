"""`GA-REM-006` enmienda A · `R-135` (+ `R-140` PARTE A · `R-154` subconjunto) · continuidad de estados de `P-07`.

`OD-17.a`: un rechazo corregible no es terminal. Cada estado se siembra **directamente** (con su historia de
revisión en `approval_actions`) para que cada prueba mida una transición y no una cadena; la habilitación de
cada unidad se siembra explícitamente (`BU-D10` no interviene).

    Empresa A   breeder ON · grandparent ON · hatchery OFF · lotes LR (breeder) · LG (grandparent) · LH (hatchery)
                eventos en RETURNED, REJECTED, CORRECTED, APPROVED, CANCELLED, SAP_CONFIRMED, SAP_ERROR, DRAFT
    Empresa B   breeder ON · lote LB · evento RETURNED
    OPERADOR    operations:create/read/update · lots:read · breeder + hatchery (histórica; OFF)
    OPERADOR_G  ídem · solo grandparent (Progenitoras)
    CORRECTOR   corrections:correct/read · operations:read · breeder + hatchery (histórica)
    APROBADOR   approvals:approve/reject · review:review/read · operations:read · breeder
    SIN_PERM    operations:read · breeder
    LECTURA     review:read · corrections:read · audit:read (control transversal, sin escritura) · breeder
    ACCESO      Administrador de Accesos (business_units:*)
    ACTOR_B     operations:create/update · corrections:correct en B · breeder
    GLOBAL      ("*", …, "all") · company_id NULL
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

pytestmark = pytest.mark.asyncio

PREFIJO = "STCO-"


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
    from app.operations.models import BirdMovement, EventStatus, EventType, OperationalEvent
    from app.review.models import ActionType, ApprovalAction

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
        assert hab[(a.id, "hatchery")].is_enabled is False

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        PA = PermissionAction
        roles = {
            "operador": _rol("Op", a.id, [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]),
            "corrector": _rol("Corr", a.id, [("corrections", PA.CORRECT), ("corrections", PA.READ), ("operations", PA.READ)]),
            "aprobador": _rol("Apr", a.id, [("approvals", PA.APPROVE), ("approvals", PA.REJECT), ("review", PA.REVIEW), ("review", PA.READ), ("operations", PA.READ)]),
            "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]),
            "lectura": _rol("Lectura", a.id, [("review", PA.READ), ("corrections", PA.READ), ("audit", PA.READ), ("operations", PA.READ)]),
            "acceso": _rol("Acceso", a.id, [("business_units", PA.READ), ("business_units", PA.CREATE), ("business_units", PA.UPDATE), ("business_units", PA.DELETE)]),
            "b": _rol("OpB", b.id, [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("corrections", PA.CORRECT)]),
            "global": _rol("Global", None, []),
        }
        await s.flush()
        for clave, (rol, permisos) in roles.items():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Stco", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {
            "operador": _usuario(a.id, "OPERADOR", roles["operador"][0]),
            "operador_g": _usuario(a.id, "OPERADORG", roles["operador"][0]),
            "corrector": _usuario(a.id, "CORRECTOR", roles["corrector"][0]),
            "aprobador": _usuario(a.id, "APROBADOR", roles["aprobador"][0]),
            "revisor": _usuario(a.id, "REVISOR", roles["aprobador"][0]),
            "sin_perm": _usuario(a.id, "SINPERM", roles["sin_perm"][0]),
            "lectura": _usuario(a.id, "LECTURA", roles["lectura"][0]),
            "acceso": _usuario(a.id, "ACCESO", roles["acceso"][0]),
            "actor_b": _usuario(b.id, "ACTORB", roles["b"][0]),
            "global": _usuario(None, "GLOBAL", roles["global"][0]),
        }
        s.add_all(u.values())
        await s.flush()
        for clave in ("operador", "corrector", "aprobador", "revisor", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[clave], company_business_unit=hab[(a.id, "breeder")])
        for clave in ("operador", "corrector"):
            await conceder_unidad(s, user=u[clave], company_business_unit=hab[(a.id, "hatchery")])
        await conceder_unidad(s, user=u["operador_g"], company_business_unit=hab[(a.id, "grandparent")])
        await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, "breeder")])

        granja_a = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        granja_b = Farm(company_id=b.id, name=f"{PREFIJO}GRANJA-B", code=f"{PREFIJO}GB-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja_a, granja_b])
        await s.flush()
        galpon_a = House(farm_id=granja_a.id, name=f"{PREFIJO}GALPON-A", capacity=10_000, is_active=True)
        galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}GALPON-B", capacity=10_000, is_active=True)
        s.add_all([galpon_a, galpon_b])
        await s.flush()

        def _lote(empresa, marca, tipo):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE, farm_id=None)

        lr, lg, lh, lb = _lote(a, "LR", BirdTypeEnum.BREEDER), _lote(a, "LG", BirdTypeEnum.GRANDPARENT), _lote(a, "LH", BirdTypeEnum.HATCHERY), _lote(b, "LB", BirdTypeEnum.BREEDER)
        s.add_all([lr, lg, lh, lb])
        await s.flush()

        def _evento(empresa, lote, estado, autor, granja=None, galpon=None, tipo=EventType.FARM_INSPECTION):
            return OperationalEvent(company_id=empresa.id, lot_id=lote.id, farm_id=granja, house_id=galpon, event_type=tipo,
                                    event_date=date.today(), status=estado, registered_by_id=autor.id, version=1,
                                    observations=f"{PREFIJO}{estado.value}-{lote.lot_code}")

        ev = {
            "ret": _evento(a, lr, EventStatus.RETURNED, u["operador"], granja_a.id, galpon_a.id, EventType.BIRD_RECEPTION),
            "ret2": _evento(a, lr, EventStatus.RETURNED, u["operador"]),
            "ret3": _evento(a, lr, EventStatus.RETURNED, u["operador"]),
            "rej": _evento(a, lr, EventStatus.REJECTED, u["operador"]),
            "rej2": _evento(a, lr, EventStatus.REJECTED, u["operador"]),
            "rej3": _evento(a, lr, EventStatus.REJECTED, u["operador"]),
            "corr": _evento(a, lr, EventStatus.CORRECTED, u["operador"]),
            "appr": _evento(a, lr, EventStatus.APPROVED, u["operador"]),
            "canc": _evento(a, lr, EventStatus.CANCELLED, u["operador"]),
            "sap": _evento(a, lr, EventStatus.SAP_CONFIRMED, u["operador"]),
            "saperr": _evento(a, lr, EventStatus.SAP_ERROR, u["operador"]),
            "draft": _evento(a, lr, EventStatus.DRAFT, u["operador"]),
            "reg": _evento(a, lr, EventStatus.REGISTERED, u["operador"]),
            "ret_g": _evento(a, lg, EventStatus.RETURNED, u["operador_g"]),
            "ret_g2": _evento(a, lg, EventStatus.RETURNED, u["operador_g"]),
            "ret_h": _evento(a, lh, EventStatus.RETURNED, u["operador"]),
            "ret_h2": _evento(a, lh, EventStatus.RETURNED, u["operador"]),
            "ret_b": _evento(b, lb, EventStatus.RETURNED, u["actor_b"]),
        }
        s.add_all(ev.values())
        await s.flush()
        s.add(BirdMovement(event_id=ev["ret"].id, sex="mixed", quantity=10))
        MOTIVO_REV = f"{PREFIJO}MOTIVO-DEL-REVISOR: falta el pesaje del galpón 3"
        for clave in ("ret", "ret2", "ret3", "ret_g", "ret_g2", "ret_h", "ret_h2", "ret_b"):
            s.add(ApprovalAction(event_id=ev[clave].id, user_id=u["revisor"].id, action_type=ActionType.RETURNED, observations=MOTIVO_REV))
        MOTIVO_REJ = f"{PREFIJO}MOTIVO-DEL-RECHAZO: cantidad incoherente con la recepción"
        for clave in ("rej", "rej2", "rej3"):
            s.add(ApprovalAction(event_id=ev[clave].id, user_id=u["aprobador"].id, action_type=ActionType.REJECTED, observations=MOTIVO_REJ))
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "granja_a": granja_a.id, "galpon_a": galpon_a.id, "lr": lr.id, "lg": lg.id, "lh": lh.id, "lb": lb.id,
             "motivo_rev": MOTIVO_REV, "motivo_rej": MOTIVO_REJ, "url": test_database_url}
        d.update({k: v.id for k, v in u.items()})
        d.update({f"ev_{k}": v.id for k, v in ev.items()})
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_steps WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
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

async def _sql(esc, sql: str, **params):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(sql), params)).all()
    finally:
        await motor.dispose()


async def _estado(esc, ev) -> str:
    return str((await _sql(esc, "SELECT status FROM operational_events WHERE id = :e", e=ev))[0][0]).lower().split(".")[-1]


async def _version(esc, ev) -> int:
    return int((await _sql(esc, "SELECT version FROM operational_events WHERE id = :e", e=ev))[0][0])


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


async def _submit(http_client, esc, actor, ev, company_id=None):
    return await http_client.post(f"/api/v1/operations/{esc[ev]}/submit", headers=_token(esc[actor], company_id))


async def _corregir(http_client, esc, actor, ev, company_id=None, **extra):
    cuerpo = {"event_id": esc[ev], "field_name": "observations", "corrected_value": f"{PREFIJO}corregido",
              "reason": f"{PREFIJO}error de digitación en observaciones"}
    cuerpo.update(extra)
    return await http_client.post("/api/v1/corrections", headers=_token(esc[actor], company_id), json=cuerpo)


async def _editar(http_client, esc, actor, ev, cuerpo=None):
    return await http_client.put(f"/api/v1/operations/{esc[ev]}", headers=_token(esc[actor]),
                                 json=cuerpo or {"observations": f"{PREFIJO}editado por el operador"})


async def _cancelar(http_client, esc, actor, ev):
    return await http_client.post(f"/api/v1/operations/{esc[ev]}/cancel", headers=_token(esc[actor]))


# ═══════════════════════════════════════════════════════════════════════════
#  AC-S · continuidad
# ═══════════════════════════════════════════════════════════════════════════

async def test_s01_el_devuelto_se_reenvia_y_vuelve_a_la_cola_de_revision(http_client, esc):
    r = await _submit(http_client, esc, "operador", "ev_ret")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "pending_review"
    assert await _estado(esc, esc["ev_ret"]) == "pending_review"


async def test_s01_el_rechazado_se_reenvia_no_es_terminal(http_client, esc):
    r = await _submit(http_client, esc, "operador", "ev_rej")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "pending_review"


async def test_s02_el_rechazado_es_editable_por_el_operador(http_client, esc):
    r = await _editar(http_client, esc, "operador", "ev_rej2")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "rejected" and r.json()["observations"].endswith("editado por el operador")


async def test_s02_el_rechazado_es_corregible_y_produce_corrected(http_client, esc):
    r = await _corregir(http_client, esc, "corrector", "ev_rej3")
    assert r.status_code == 201, r.text
    assert await _estado(esc, esc["ev_rej3"]) == "corrected"


async def test_s03_control_el_devuelto_corregido_produce_corrected(http_client, esc):
    r = await _corregir(http_client, esc, "corrector", "ev_ret2")
    assert r.status_code == 201, r.text
    assert await _estado(esc, esc["ev_ret2"]) == "corrected"


async def test_s04_s08_control_sin_permiso_ni_se_corrige_ni_se_reenvia(http_client, esc):
    assert (await _corregir(http_client, esc, "sin_perm", "ev_ret")).status_code == 403
    assert (await _submit(http_client, esc, "sin_perm", "ev_ret")).status_code == 403
    assert (await _corregir(http_client, esc, "lectura", "ev_ret")).status_code == 403, "control transversal ≠ operación"
    assert (await _corregir(http_client, esc, "acceso", "ev_ret")).status_code == 403
    assert (await _submit(http_client, esc, "acceso", "ev_ret")).status_code == 403
    assert await _estado(esc, esc["ev_ret"]) == "returned"


async def test_s05_control_otra_empresa_no_corrige_ni_reenvia(http_client, esc):
    assert (await _corregir(http_client, esc, "actor_b", "ev_ret")).status_code == 404
    assert (await _submit(http_client, esc, "actor_b", "ev_ret")).status_code == 404
    assert await _estado(esc, esc["ev_ret"]) == "returned"


async def test_s06_la_unidad_no_concedida_no_se_corrige(http_client, esc):
    r = await _corregir(http_client, esc, "corrector", "ev_ret_g")
    assert r.status_code == 404, r.text
    assert await _estado(esc, esc["ev_ret_g"]) == "returned"
    assert await _cuenta(esc, "SELECT count(*) FROM correction_logs WHERE event_id = :e", e=esc["ev_ret_g"]) == 0


async def test_s06_control_la_unidad_no_concedida_no_se_reenvia(http_client, esc):
    assert (await _submit(http_client, esc, "operador", "ev_ret_g")).status_code == 404


async def test_s07_la_unidad_apagada_no_se_corrige_aunque_haya_concesion(http_client, esc):
    r = await _corregir(http_client, esc, "corrector", "ev_ret_h")
    assert r.status_code == 404, r.text
    assert await _estado(esc, esc["ev_ret_h"]) == "returned"


async def test_s07_la_autoridad_global_no_corrige_ni_reenvia_sobre_unidad_apagada(http_client, esc):
    r = await _corregir(http_client, esc, "global", "ev_ret_h2", company_id=esc["a"])
    assert r.status_code == 403, r.text
    r = await _submit(http_client, esc, "global", "ev_ret_h2", company_id=esc["a"])
    assert r.status_code == 403, r.text
    assert await _estado(esc, esc["ev_ret_h2"]) == "returned"


async def test_s07_control_la_autoridad_global_sin_contexto_falla_cerrada(http_client, esc):
    assert (await _corregir(http_client, esc, "global", "ev_ret")).status_code in (403, 404)
    assert (await _submit(http_client, esc, "global", "ev_ret")).status_code in (403, 404)


async def test_s09_control_estado_origen_invalido(http_client, esc):
    for ev in ("ev_corr", "ev_appr", "ev_canc", "ev_draft"):
        r = await _submit(http_client, esc, "operador", ev)
        assert r.status_code == 400, (ev, r.text)
    for ev in ("ev_appr", "ev_canc", "ev_sap"):
        r = await _corregir(http_client, esc, "corrector", ev)
        assert r.status_code == 400, (ev, r.text)


async def test_s10_control_el_aprobado_es_inmutable(http_client, esc):
    assert (await _editar(http_client, esc, "operador", "ev_appr")).status_code == 400
    assert (await _corregir(http_client, esc, "corrector", "ev_appr")).status_code == 400
    assert (await _submit(http_client, esc, "operador", "ev_appr")).status_code == 400
    assert await _estado(esc, esc["ev_appr"]) == "approved"


async def test_s11_los_terminales_no_se_cancelan_ni_reentran(http_client, esc):
    """`R-140` PARTE A: hoy `cancel` acepta `SAP_CONFIRMED`, `SAP_ERROR` y un `CANCELLED`."""
    for ev, estado in (("ev_sap", "sap_confirmed"), ("ev_saperr", "sap_error"), ("ev_canc", "cancelled")):
        r = await _cancelar(http_client, esc, "operador", ev)
        assert r.status_code == 400, (ev, r.text)
        assert await _estado(esc, esc[ev]) == estado
    assert (await _submit(http_client, esc, "operador", "ev_canc")).status_code == 400


async def test_s12_control_ni_la_edicion_ni_la_correccion_fijan_estado_o_propietario(http_client, esc):
    r = await _editar(http_client, esc, "operador", "ev_ret", {"status": "approved"})
    assert r.status_code == 422, r.text
    r = await _corregir(http_client, esc, "corrector", "ev_ret", field_name="company_id", corrected_value=str(esc["b"]))
    assert r.status_code == 400, r.text
    r = await _corregir(http_client, esc, "corrector", "ev_ret", field_name="status", corrected_value="approved")
    assert r.status_code == 400, r.text
    fila = (await _sql(esc, "SELECT company_id, registered_by_id, status FROM operational_events WHERE id = :e", e=esc["ev_ret"]))[0]
    assert fila[0] == esc["a"] and fila[1] == esc["operador"]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R · motivo y auditoría
# ═══════════════════════════════════════════════════════════════════════════

async def test_r01_r05_el_motivo_del_revisor_y_la_historia_sobreviven_a_la_correccion_y_al_reenvio(http_client, esc):
    assert (await _corregir(http_client, esc, "corrector", "ev_ret3")).status_code == 201
    r = await _submit(http_client, esc, "operador", "ev_ret3")
    assert r.status_code == 400, "un corregido espera al aprobador; el reenvío es del devuelto/rechazado"
    r = await _submit(http_client, esc, "operador", "ev_ret")
    assert r.status_code == 200, r.text
    motivo = (await _sql(esc, "SELECT observations FROM approval_actions WHERE event_id = :e AND action_type::text ILIKE 'returned'", e=esc["ev_ret"]))
    assert motivo and motivo[0][0] == esc["motivo_rev"], "AC-R01: el motivo del revisor permanece"
    auditoria = await _sql(esc, "SELECT user_id, previous_state, new_state FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e AND new_state = 'pending_review'", e=str(esc["ev_ret"]))
    assert auditoria and auditoria[-1][0] == esc["operador"] and auditoria[-1][1] == "returned", "AC-R04/R05"


async def test_r02_r03_control_el_motivo_de_la_correccion_es_obligatorio_y_no_vacio(http_client, esc):
    assert (await _corregir(http_client, esc, "corrector", "ev_ret", reason="abc")).status_code == 422
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                               json={"event_id": esc["ev_ret"], "field_name": "observations", "corrected_value": "x"})
    assert r.status_code == 422
    r = await _corregir(http_client, esc, "corrector", "ev_ret", reason="        ")
    assert r.status_code in (400, 422), "AC-R03: un motivo en blanco no es un motivo"
    assert await _estado(esc, esc["ev_ret"]) == "returned"


async def test_r06_r07_una_denegacion_no_deja_rastro_de_exito_ni_efectos(http_client, esc):
    antes_v = await _version(esc, esc["ev_appr"])
    antes_log = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e", e=str(esc["ev_appr"]))
    assert (await _corregir(http_client, esc, "corrector", "ev_appr")).status_code == 400
    assert (await _submit(http_client, esc, "operador", "ev_appr")).status_code == 400
    assert (await _corregir(http_client, esc, "sin_perm", "ev_ret")).status_code == 403
    assert await _version(esc, esc["ev_appr"]) == antes_v
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e", e=str(esc["ev_appr"])) == antes_log
    assert await _cuenta(esc, "SELECT count(*) FROM correction_logs WHERE event_id IN (:a, :b)", a=esc["ev_appr"], b=esc["ev_ret"]) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-D · DRAFT (R-154 subconjunto) · AC-U · reenvío
# ═══════════════════════════════════════════════════════════════════════════

async def test_d01_d05_control_el_borrador_se_edita_con_alcance_y_avanza_de_version(http_client, esc):
    v0 = await _version(esc, esc["ev_draft"])
    r = await _editar(http_client, esc, "operador", "ev_draft")
    assert r.status_code == 200 and r.json()["status"] == "draft", r.text
    assert await _version(esc, esc["ev_draft"]) == v0 + 1, "AC-D05"
    assert (await _editar(http_client, esc, "operador_g", "ev_draft")).status_code == 404, "AC-D02: otra cadena"
    assert (await _editar(http_client, esc, "sin_perm", "ev_draft")).status_code == 403, "AC-D02: sin permiso"
    assert (await _editar(http_client, esc, "operador", "ev_draft", {"status": "approved"})).status_code == 422, "AC-D03"
    assert (await _submit(http_client, esc, "operador", "ev_draft")).status_code == 400, "AC-D04"
    assert await _estado(esc, esc["ev_draft"]) == "draft"


async def test_u01_u02_control_corrected_espera_al_aprobador_y_nada_reenvia_solo(http_client, esc):
    assert await _estado(esc, esc["ev_corr"]) == "corrected"
    r = await _editar(http_client, esc, "operador", "ev_ret2")
    assert r.status_code == 200 and r.json()["status"] == "returned", "editar no reenvía"
    assert (await _corregir(http_client, esc, "corrector", "ev_ret2")).status_code == 201
    assert await _estado(esc, esc["ev_ret2"]) == "corrected", "corregir no reenvía a revisión: va al aprobador"


async def test_u03_u04_el_reenviado_vuelve_a_la_cola_y_la_revision_sigue_gobernada(http_client, esc):
    assert (await _submit(http_client, esc, "operador", "ev_rej")).status_code == 200
    r = await http_client.post(f"/api/v1/review/start/{esc['ev_rej']}", headers=_token(esc["aprobador"]))
    assert r.status_code == 200, r.text
    assert await _estado(esc, esc["ev_rej"]) == "in_review"


async def test_u05_el_reenvio_no_duplica_el_efecto(http_client, esc):
    saldo0 = await _saldo(esc, esc["lr"])
    eventos0 = await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l", l=esc["lr"])
    movs0 = await _cuenta(esc, "SELECT count(*) FROM bird_movements WHERE event_id = :e", e=esc["ev_ret"])
    assert (await _submit(http_client, esc, "operador", "ev_ret")).status_code == 200
    assert await _saldo(esc, esc["lr"]) == saldo0 == 10
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l", l=esc["lr"]) == eventos0
    assert await _cuenta(esc, "SELECT count(*) FROM bird_movements WHERE event_id = :e", e=esc["ev_ret"]) == movs0 == 1


async def test_progenitoras_el_actor_de_abuelas_reenvia_lo_suyo_y_el_de_reproductoras_no(http_client, esc):
    assert (await _submit(http_client, esc, "operador", "ev_ret_g2")).status_code == 404
    r = await _submit(http_client, esc, "operador_g", "ev_ret_g2")
    assert r.status_code == 200, r.text
