"""`GA-REM-007` enmienda B · `R-166` · una sola decisión efectiva por ciclo de revisión (`AC-R166-01…13`).

`approve` y `reject` leían el estado del evento **sin bloqueo**: dos peticiones concurrentes lo superaban y ambas escribían
decisión, historia (`approval_actions`), auditoría de éxito y —el rechazo— notificación. La fila autoritativa es
`operational_events` (`status`); la primitiva, el `SELECT … FOR UPDATE` que ya usa el reverso.

Escenario (prefijo `REVI-`):
    empresa A (breeder ON · hatchery OFF) · empresa B (breeder ON)
    op (registra) · rev1 · rev2 (revisores distintos del registrador: `BR-14` satisfecha) · sin_perm · actor_b · global
    tres eventos frescos por carrera: la reproducción no depende del tiempo.
"""
from __future__ import annotations

import asyncio
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

PREFIJO = "REVI-"
MOTIVO = f"{PREFIJO}motivo de rechazo suficientemente largo"


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

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "hatchery", False), (b, "breeder", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction
        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]
        revisar = [("review", PA.REVIEW), ("review", PA.READ), ("approvals", PA.APPROVE), ("approvals", PA.REJECT),
                   ("approvals", PA.READ), ("operations", PA.READ)]

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        roles = {"op": _rol("Op", a.id, ops), "rev1": _rol("Rev1", a.id, revisar), "rev2": _rol("Rev2", a.id, revisar),
                 "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]), "rev_b": _rol("RevB", b.id, revisar),
                 "global": _rol("Global", None, [])}
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Revi", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {k: _usuario(a.id, k.upper(), roles[k][0]) for k in ("op", "rev1", "rev2", "sin_perm")}
        u["rev_b"] = _usuario(b.id, "REVB", roles["rev_b"][0])
        u["global"] = _usuario(None, "GLOBAL", roles["global"][0])
        s.add_all(u.values())
        await s.flush()
        for k in ("op", "rev1", "rev2", "sin_perm"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=u["rev_b"], company_business_unit=hab[(b.id, "breeder")])

        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}",
                      farm_type=FarmType.BREEDING, is_active=True)
        granja_b = Farm(company_id=b.id, name=f"{PREFIJO}GRANJA-B", code=f"{PREFIJO}GB-{uuid.uuid4().hex[:4]}",
                        farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja, granja_b])
        await s.flush()
        galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON-A", capacity=100_000, is_active=True)
        galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}GALPON-B", capacity=100_000, is_active=True)
        s.add_all([galpon, galpon_b])
        await s.flush()
        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}LR-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER,
                   status=LotStatus.ACTIVE, farm_id=granja.id, house_id=galpon.id)
        lote_h = Lot(company_id=a.id, lot_code=f"{PREFIJO}LH-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.HATCHERY,
                     status=LotStatus.ACTIVE, farm_id=granja.id, house_id=galpon.id)
        lote_b = Lot(company_id=b.id, lot_code=f"{PREFIJO}LB-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER,
                     status=LotStatus.ACTIVE, farm_id=granja_b.id, house_id=galpon_b.id)
        s.add_all([lote, lote_h, lote_b])
        await s.flush()
        await s.commit()
        d = {"url": test_database_url, "a": a.id, "b": b.id, "granja": granja.id, "galpon": galpon.id,
             "granja_b": granja_b.id, "galpon_b": galpon_b.id, "lote": lote.id, "lote_h": lote_h.id, "lote_b": lote_b.id}
        d.update({k: v.id for k, v in u.items()})
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM review_batches WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM reversals WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p", "DELETE FROM roles WHERE name LIKE :p",
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


async def _verdad(esc, event_id) -> dict:
    """La verdad final: estado, firma, historia efectiva, auditoría de éxito y notificaciones."""
    estado = (await _sql(esc, "SELECT status::text, approved_by_id FROM operational_events WHERE id = :e", e=event_id))[0]
    acciones = dict(await _sql(esc, "SELECT action_type::text, count(*) FROM approval_actions WHERE event_id = :e GROUP BY 1", e=event_id))
    auditoria = dict(await _sql(esc, "SELECT action::text, count(*) FROM audit_logs WHERE entity_type = 'operational_event' "
                                     "AND entity_id = :e GROUP BY 1", e=str(event_id)))
    notif = await _cuenta(esc, "SELECT count(*) FROM notifications WHERE related_entity_type = 'operational_event' AND related_entity_id = :e", e=event_id)
    return {"estado": estado[0].lower(), "aprobado_por": estado[1],
            "acciones": {k.lower(): v for k, v in acciones.items()},
            "auditoria": {k.lower(): v for k, v in auditoria.items()}, "notificaciones": notif}


async def _evento_en(http_client, esc, estado: str, *, lote="lote", tipo="vaccination") -> int:
    """Crea un evento y lo deja en el estado revisable pedido (sembrado directo: el flujo ya está certificado).

    El tipo por defecto es `vaccination`: la decisión de revisión no depende del tipo, y un evento sin efecto de
    saldo mantiene la carrera limpia de `BR-01` (el defecto que se mide es la serialización, no el saldo).
    """
    cuerpo = {"lot_id": esc[lote], "event_type": tipo, "event_date": recent_event_date(),
              "farm_id": esc["granja_b" if lote == "lote_b" else "granja"],
              "house_id": esc["galpon_b" if lote == "lote_b" else "galpon"]}
    actor = "rev_b" if lote == "lote_b" else "op"
    r = await http_client.post("/api/v1/operations", headers=_token(esc[actor]), json=cuerpo)
    assert r.status_code == 201, r.text
    event_id = r.json()["id"]
    motor = create_async_engine(esc["url"])
    async with motor.begin() as c:
        await c.execute(text("UPDATE operational_events SET status = :s WHERE id = :e"), {"s": estado, "e": event_id})
    await motor.dispose()
    return event_id


async def _sembrar_evento_sql(esc, lot_id: int, estado: str) -> int:
    """Evento sembrado directamente: el lote de incubadora vive en una unidad **apagada** y su alta por API está
    correctamente denegada (`R-165`/`OD-16`). Lo que se mide aquí es la revisión, no el alta."""
    motor = create_async_engine(esc["url"])
    try:
        async with motor.begin() as c:
            fila = await c.execute(text(
                "INSERT INTO operational_events (company_id, lot_id, farm_id, house_id, event_type, event_date, status, "
                "version, registered_by_id, created_at, updated_at) "
                "VALUES (:c, :l, :f, :h, 'VACCINATION', CURRENT_DATE, :s, 1, :u, now(), now()) RETURNING id"),
                {"c": esc["a"], "l": lot_id, "f": esc["granja"], "h": esc["galpon"], "s": estado, "u": esc["op"]})
            return int(fila.scalar_one())
    finally:
        await motor.dispose()


async def _aprobar(http_client, esc, actor, event_id, company_id=None):
    return await http_client.post("/api/v1/approvals/approve", headers=_token(esc[actor], company_id),
                                  json={"event_id": event_id, "observations": f"{PREFIJO}aprobado"})


async def _rechazar(http_client, esc, actor, event_id, company_id=None):
    return await http_client.post("/api/v1/approvals/reject", headers=_token(esc[actor], company_id),
                                  json={"event_id": event_id, "observations": MOTIVO})


def _una_sola(v: dict) -> bool:
    """Una decisión efectiva: una acción, una auditoría de decisión, y coherencia entre estado e historia."""
    acciones = v["acciones"].get("approved", 0) + v["acciones"].get("rejected", 0)
    auditos = v["auditoria"].get("approved", 0) + v["auditoria"].get("rejected", 0) + v["auditoria"].get("reversed", 0)
    coherente = (v["estado"] == "approved" and v["acciones"].get("rejected", 0) == 0) or \
                (v["estado"] == "rejected" and v["acciones"].get("approved", 0) == 0)
    return acciones == 1 and auditos == 1 and coherente


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R166-01 · 04 · 05 · 06 — approve || reject: una sola decisión efectiva
# ═══════════════════════════════════════════════════════════════════════════

async def test_r166_01_aprobar_y_rechazar_a_la_vez_dejan_una_sola_decision(http_client, esc):
    resultados = []
    for _ in range(3):  # tres eventos frescos: la reproducción no depende del tiempo
        ev = await _evento_en(http_client, esc, "CORRECTED")
        ra, rr = await asyncio.gather(_aprobar(http_client, esc, "rev1", ev), _rechazar(http_client, esc, "rev2", ev))
        v = await _verdad(esc, ev)
        v["codigos"] = sorted([ra.status_code, rr.status_code])
        resultados.append(v)
    for v in resultados:
        assert _una_sola(v), ("AC-R166-01: dos decisiones efectivas sobre el mismo evento", v)
        assert v["codigos"] == [200, 400], ("AC-R166-05: la segunda revalida bajo el bloqueo y se deniega", v)
        if v["estado"] == "approved":
            assert v["notificaciones"] == 0, ("AC-R166-06: notificación de rechazo de un evento aprobado", v)
        else:
            assert v["notificaciones"] == 1, ("AC-R166-06: el rechazo efectivo notifica una vez", v)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R166-02 — approve || approve
# ═══════════════════════════════════════════════════════════════════════════

async def test_r166_02_dos_aprobaciones_concurrentes_dejan_una(http_client, esc):
    resultados = []
    for _ in range(3):
        ev = await _evento_en(http_client, esc, "CORRECTED")
        r1, r2 = await asyncio.gather(_aprobar(http_client, esc, "rev1", ev), _aprobar(http_client, esc, "rev2", ev))
        v = await _verdad(esc, ev)
        v["codigos"] = sorted([r1.status_code, r2.status_code])
        resultados.append(v)
    for v in resultados:
        assert v["acciones"].get("approved", 0) == 1, ("AC-R166-02: una sola aprobación efectiva", v)
        assert v["auditoria"].get("approved", 0) == 1, ("AC-R166-06: una sola auditoría de éxito", v)
        assert v["codigos"] == [200, 400], ("AC-R166-05", v)
        assert v["estado"] == "approved"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R166-03 — reject || reject
# ═══════════════════════════════════════════════════════════════════════════

async def test_r166_03_dos_rechazos_concurrentes_dejan_uno(http_client, esc):
    resultados = []
    for _ in range(3):
        ev = await _evento_en(http_client, esc, "CORRECTED")
        r1, r2 = await asyncio.gather(_rechazar(http_client, esc, "rev1", ev), _rechazar(http_client, esc, "rev2", ev))
        v = await _verdad(esc, ev)
        v["codigos"] = sorted([r1.status_code, r2.status_code])
        resultados.append(v)
    for v in resultados:
        assert v["acciones"].get("rejected", 0) == 1, ("AC-R166-03: un solo rechazo efectivo", v)
        assert v["auditoria"].get("rejected", 0) == 1, ("AC-R166-06: una sola auditoría", v)
        assert v["notificaciones"] == 1, ("AC-R166-06: una sola notificación", v)
        assert v["codigos"] == [200, 400] and v["estado"] == "rejected"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R166-07 · 08 — BR-14 y el contrato secuencial siguen intactos
# ═══════════════════════════════════════════════════════════════════════════

async def test_r166_07_08_segregacion_y_secuencia(http_client, esc):
    ev = await _evento_en(http_client, esc, "CORRECTED")
    assert (await _aprobar(http_client, esc, "rev1", ev)).status_code == 200
    r = await _rechazar(http_client, esc, "rev2", ev)
    assert r.status_code == 400, ("AC-R166-08: lo aprobado no se rechaza después", r.status_code, r.text)
    v = await _verdad(esc, ev)
    assert v["acciones"] == {"approved": 1} and v["notificaciones"] == 0
    # `BR-14` (`GA-REM-007`): quien registra no aprueba — control, sin cambio de contrato
    ev2 = await _evento_en(http_client, esc, "CORRECTED")
    r = await _aprobar(http_client, esc, "op", ev2)
    assert r.status_code in (403, 200), ("AC-R166-07: BR-14 según la configuración de la empresa", r.status_code, r.text)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R166-09 · 10 — los demás escritores de decisión comparten el contrato
# ═══════════════════════════════════════════════════════════════════════════

async def test_r166_09_completar_revision_y_aprobar_a_la_vez(http_client, esc):
    """`AC-R166-09`: `complete_review` y `approve` son transiciones **encadenadas legales** (`IN_REVIEW → CORRECTED
    → APPROVED`), no dos decisiones del mismo estado. Lo que el bloqueo garantiza no es que una falle, sino que se
    **serialicen**: cada transición parte del estado en que la anterior dejó el evento. Sin bloqueo ambas leen
    `IN_REVIEW` y quedan dos transiciones con el **mismo estado origen** — historia imposible."""
    for _ in range(3):
        ev = await _evento_en(http_client, esc, "IN_REVIEW")
        r1, r2 = await asyncio.gather(
            http_client.post("/api/v1/review/complete", headers=_token(esc["rev1"]),
                             json={"event_id": ev, "observations": f"{PREFIJO}completo"}),
            _aprobar(http_client, esc, "rev2", ev))
        origenes = [f[0] for f in await _sql(esc, "SELECT previous_state FROM audit_logs WHERE entity_type = 'operational_event' "
                                                  "AND entity_id = :e AND previous_state IS NOT NULL AND action::text NOT ILIKE 'created'", e=str(ev))]
        v = await _verdad(esc, ev)
        assert 200 in (r1.status_code, r2.status_code), ("AC-R166-09: al menos una transición ocurre", r1.status_code, r2.status_code, v)
        assert len(origenes) == len(set(origenes)), ("AC-R166-09: dos transiciones desde el mismo estado origen", origenes, v)
        assert v["estado"] in ("approved", "corrected"), ("AC-R166-09: estado final coherente con la cadena", v)


async def test_r166_10_iniciar_revision_dos_veces(http_client, esc):
    for _ in range(3):
        ev = await _evento_en(http_client, esc, "PENDING_REVIEW")
        r1, r2 = await asyncio.gather(
            http_client.post(f"/api/v1/review/start/{ev}", headers=_token(esc["rev1"])),
            http_client.post(f"/api/v1/review/start/{ev}", headers=_token(esc["rev2"])))
        estado = (await _sql(esc, "SELECT status::text FROM operational_events WHERE id = :e", e=ev))[0][0].lower()
        aud = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e "
                                 "AND action::text ILIKE 'review_started'", e=str(ev))
        assert sorted([r1.status_code, r2.status_code]) == [200, 400], ("AC-R166-10", r1.status_code, r2.status_code)
        assert estado == "in_review" and aud == 1, ("AC-R166-10: una sola transición", estado, aud)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R166-12 · 13 — seguridad y ausencia de bloqueo de saldos
# ═══════════════════════════════════════════════════════════════════════════

async def test_r166_12_la_cadena_de_seguridad_se_mantiene(http_client, esc):
    ev = await _evento_en(http_client, esc, "CORRECTED")
    assert (await _aprobar(http_client, esc, "rev_b", ev)).status_code == 404, "AC-R166-12: otra empresa"
    assert (await _aprobar(http_client, esc, "sin_perm", ev)).status_code == 403, "AC-R166-12: sin permiso"
    r = await _aprobar(http_client, esc, "global", ev)
    assert r.status_code in (400, 403, 404), ("AC-R166-12: autoridad global sin contexto", r.status_code, r.text)
    ev_h = await _sembrar_evento_sql(esc, esc["lote_h"], "CORRECTED")
    r = await _aprobar(http_client, esc, "global", ev_h, company_id=esc["a"])
    assert r.status_code == 403, ("AC-R166-12: unidad apagada (R-165 · OD-16)", r.status_code, r.text)
    assert (await _verdad(esc, ev))["acciones"] == {}, "ninguna denegación deja historia"


async def test_r166_13_revisar_no_serializa_el_saldo_del_lote(http_client, esc):
    """Control (`R-166` ≠ `R-161`): dos eventos del **mismo lote** se deciden a la vez sin bloquearse entre sí."""
    ev1 = await _evento_en(http_client, esc, "CORRECTED")
    ev2 = await _evento_en(http_client, esc, "CORRECTED")
    r1, r2 = await asyncio.gather(_aprobar(http_client, esc, "rev1", ev1), _aprobar(http_client, esc, "rev2", ev2))
    assert [r1.status_code, r2.status_code] == [200, 200], ("AC-R166-13: eventos distintos no se serializan", r1.text, r2.text)
    assert (await _verdad(esc, ev1))["acciones"] == {"approved": 1}
    assert (await _verdad(esc, ev2))["acciones"] == {"approved": 1}
