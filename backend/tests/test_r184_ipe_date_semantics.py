"""R-184 — Semántica temporal del IPE (`GET /reports/kpi/ipe/{lot_id}`).

Contrato canónico (G-06): `app/reports/router.py` y `app/reports/service.py`.
`OD-22` / `R-187` (fecha en el registro de decisión) sustituyó el régimen numérico (`× 100` histórico
retirado; escala estándar). Esta suite conserva los **invariantes técnicos** de
R-184 (200, fechas, esquema, seguridad) y su aserción numérica usa los mismos
insumos crudos con el valor OD-22 calculado a mano (no congela el valor anterior).

    IPE(OD-22) = (Viabilidad% × Ganancia_Diaria_g) / (FCR × 10)
    Ganancia_Diaria_g = avg_weight_g / age_days

R-184: `get_kpi_ipe` evaluaba `date.today() - lot.start_date` mezclando un
`datetime.date` con el `datetime` con zona que devuelve la columna
`DateTime(timezone=True)` de `Lot.start_date` ⇒ `TypeError` ⇒ **HTTP 500** en
cualquier lote con `start_date` (todo alta fija). La corrección normaliza el día
de calendario con `_dia(...)` (`R-75` / `GA-REM-028`, `app/lots/service.py`)
antes de restar — misma convención que `lots/service.py:379` y
`operations/service.py:776`.

Nota de ejecución: requiere PostgreSQL (suite canónica del repo). En local sin
credenciales de siembra (`GA_TEST_ADMIN_PASSWORD`, vía `test_credentials`) la
suite queda `skipped` — declarado, no fingido; corre en CI con
`backend/scripts/run_tests.sh`. La evidencia RED/GREEN ejecutada de esta tranche
vive en `audit/ga-r184/`.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import delete, or_, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.security import create_access_token
from tests.time_reference import days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "IPE-R184-"

# Constantes del fixture determinista (independientes de la implementación bajo prueba):
DIAS_EDAD = 19
POBLACION = 1000
MUERTES = 50              # 5 % ⇒ viabilidad 95.0
PESO_MEDIO_G = 2000.0     # ganancia = 2000 / 19
ALIMENTO_KG = 3000.0      # FCR simplificado = 3000 / 1000 = 3.0

# Valor esperado calculado a mano (NO desde el código). `OD-22` / `R-187` (fecha en el registro):
# la fórmula estándar ya no lleva el `× 100` histórico (la viabilidad llega como %).
#   viabilidad = 100 − (50 / 1000 × 100) = 95.0
#   ganancia   = 2000 / 19               = 105.263157…
#   IPE(OD-22) = (95.0 × (2000/19)) / (3.0 × 10) = 10_000 / 30 = 333.333… → 333.3
# Régimen anterior (×100, superseded por OD-22): 33333.3 — NO es objetivo de regresión.
IPE_ESPERADO = 333.3
GANANCIA_ESPERADA = 105.26
REFERENCIA_CANONICA = {"excellent": ">300", "good": "250-300", "average": "200-250"}
CLAVES_RESPUESTA = {
    "lot_id", "viabilidad_pct", "avg_weight_g", "ganancia_diaria_g",
    "age_days", "fcr", "ipe", "reference",
}


def _cab(uid: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(uid)})}"}


@pytest_asyncio.fixture
async def ipe(test_database_url, test_credentials):
    """Fixture determinista autocontenido (empresa A productiva + empresa B ajena).

    `test_credentials` se resuelve primero: sin credenciales de siembra (local) la
    suite queda `skipped` sin tocar la base.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.lots.models import OpeningBalance
    from app.masters.models import BirdTypeEnum, Company, Lot, ProductivePhase
    from app.operations.models import (
        BirdMovement, EventStatus, EventType, FeedMovement, OperationalEvent,
    )

    motor = create_async_engine(test_database_url)
    datos: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab_a = CompanyBusinessUnit(
            company_id=a.id, business_unit_id=unidades["broiler"].id, is_enabled=True)
        s.add(hab_a)
        await s.flush()

        fase = (await s.execute(select(ProductivePhase).limit(1))).scalar_one_or_none()
        if fase is None:
            fase = ProductivePhase(name=f"{PREFIJO}F", code=f"IR{uuid.uuid4().hex[:4]}",
                                   order=1, duration_days=10)
            s.add(fase)
            await s.flush()

        rol_ok = Role(name=f"{PREFIJO}R-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        rol_global = Role(name=f"{PREFIJO}G-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        rol_sin = Role(name=f"{PREFIJO}S-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add_all([rol_ok, rol_global, rol_sin])
        await s.flush()
        s.add(Permission(role_id=rol_ok.id, module="reports",
                         action=PermissionAction.READ, scope_type="company"))
        s.add(Permission(role_id=rol_global.id, module="*",
                         action=PermissionAction.READ, scope_type="all"))
        s.add(Permission(role_id=rol_sin.id, module="lots",
                         action=PermissionAction.READ, scope_type="company"))
        await s.flush()

        def _u(marca: str, role_id: int) -> User:
            return User(first_name=marca, last_name="Ipe",
                        email=f"{PREFIJO}{marca.lower()}-{uuid.uuid4().hex[:6]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=a.id,
                        role_id=role_id, is_active=True)

        u_ok = _u("OK", rol_ok.id)
        u_sin_concesion = _u("NOBU", rol_ok.id)
        u_sin_permiso = _u("NOPERM", rol_sin.id)
        u_global = _u("GLOBAL", rol_global.id)
        s.add_all([u_ok, u_sin_concesion, u_sin_permiso, u_global])
        await s.flush()
        await conceder_unidad(s, user=u_ok, company_business_unit=hab_a)
        await s.flush()

        inicio = datetime.combine(date.today() - timedelta(days=DIAS_EDAD),
                                  time.min, tzinfo=timezone.utc)
        hoy = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)

        def _lote(company_id: int, marca: str, start) -> Lot:
            lote = Lot(company_id=company_id,
                       lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=BirdTypeEnum.BROILER, status="active", start_date=start)
            s.add(lote)
            return lote

        l_ok = _lote(a.id, "OK", inicio)
        l_hoy = _lote(a.id, "HOY", hoy)
        l_nulo = _lote(a.id, "NULO", None)
        l_ajeno = _lote(b.id, "AJENO", inicio)
        await s.flush()

        s.add(OpeningBalance(
            lot_id=l_ok.id, activation_date=days_ago(DIAS_EDAD),
            phase_at_activation_id=fase.id,
            initial_male_count=POBLACION // 2, initial_female_count=POBLACION // 2,
            is_manual_activation=True, activated_by_id=u_ok.id))
        ev_m = OperationalEvent(company_id=a.id, lot_id=l_ok.id,
                                event_type=EventType.MORTALITY_RECORDING,
                                event_date=days_ago(5), status=EventStatus.APPROVED,
                                registered_by_id=u_ok.id)
        s.add(ev_m)
        await s.flush()
        s.add(BirdMovement(event_id=ev_m.id, quantity=MUERTES))
        ev_w = OperationalEvent(company_id=a.id, lot_id=l_ok.id,
                                event_type=EventType.WEIGHT_RECORDING,
                                event_date=days_ago(2), status=EventStatus.APPROVED,
                                registered_by_id=u_ok.id)
        s.add(ev_w)
        await s.flush()
        s.add(BirdMovement(event_id=ev_w.id, quantity=0, avg_weight=PESO_MEDIO_G))
        ev_f = OperationalEvent(company_id=a.id, lot_id=l_ok.id,
                                event_type=EventType.FEED_REGISTRATION,
                                event_date=days_ago(1), status=EventStatus.APPROVED,
                                registered_by_id=u_ok.id)
        s.add(ev_f)
        await s.flush()
        s.add(FeedMovement(event_id=ev_f.id, quantity_kg=ALIMENTO_KG))
        await s.commit()

        datos = {
            "lote_ok": l_ok.id, "lote_hoy": l_hoy.id,
            "lote_nulo": l_nulo.id, "lote_ajeno": l_ajeno.id,
            "u_ok": u_ok.id, "u_sin_concesion": u_sin_concesion.id,
            "u_sin_permiso": u_sin_permiso.id, "u_global": u_global.id,
            "hab_a": hab_a.id,
        }

    yield datos

    # ── Limpieza determinista por prefijo ─────────────────────────────────────
    from app.audit.models import AuditLog
    from app.lots.models import OpeningBalance
    from app.masters.models import Lot
    from app.operations.models import BirdMovement, FeedMovement, OperationalEvent

    async with motor.begin() as c:
        lotes = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        usuarios = (await c.execute(text(
            "SELECT id FROM users WHERE username LIKE :p"), {"p": f"{PREFIJO}%"})).scalars().all()
        if lotes:
            existe_n = (await c.execute(text("SELECT to_regclass('public.notifications')"))).scalar()
            if existe_n:
                await c.execute(text(
                    "DELETE FROM notifications WHERE related_entity_type = 'lot' "
                    "AND related_entity_id = ANY(:ids)"), {"ids": list(lotes)})
            await c.execute(delete(BirdMovement).where(BirdMovement.event_id.in_(
                select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(lotes)))))
            await c.execute(delete(FeedMovement).where(FeedMovement.event_id.in_(
                select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(lotes)))))
            await c.execute(delete(OperationalEvent).where(OperationalEvent.lot_id.in_(lotes)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(lotes)))
        if lotes or usuarios:
            await c.execute(delete(AuditLog).where(or_(
                AuditLog.lot_id.in_(lotes) if lotes else AuditLog.lot_id.is_(None),
                AuditLog.user_id.in_(usuarios) if usuarios else AuditLog.user_id.is_(None))))
        if lotes:
            await c.execute(delete(Lot).where(Lot.id.in_(lotes)))
        if usuarios:
            await c.execute(text("DELETE FROM user_business_units WHERE user_id = ANY(:ids)"),
                            {"ids": list(usuarios)})
        await c.execute(text(
            "DELETE FROM permissions WHERE role_id IN "
            "(SELECT id FROM roles WHERE name LIKE :p)"), {"p": f"{PREFIJO}%"})
        await c.execute(text(
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)"), {"p": f"{PREFIJO}%"})
        if usuarios:
            await c.execute(text("DELETE FROM users WHERE id = ANY(:ids)"),
                            {"ids": list(usuarios)})
        await c.execute(text("DELETE FROM roles WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM companies WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})
    await motor.dispose()


def _ipe_url(lote_id: int) -> str:
    return f"/api/v1/reports/kpi/ipe/{lote_id}"


# ═══════════════════════════════════════════════════════════════════════════
# Camino feliz determinista — R184-AC06…AC11, AC14, AC15
# ═══════════════════════════════════════════════════════════════════════════

async def test_r184_ac06_ac08_ac09_ipe_valido_200_y_valor_determinista(http_client, ipe):
    """El lote válido responde 200 con el valor del contrato, no 500 (defecto original).

    Valor esperado derivado a mano (ver constantes del módulo), nunca del código.
    """
    r = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_ok"]))
    assert r.status_code == 200, f"R-184 sigue devolviendo {r.status_code}: {r.text}"
    d = r.json()
    assert set(d) == CLAVES_RESPUESTA
    assert d["lot_id"] == ipe["lote_ok"]
    assert d["viabilidad_pct"] == 95.0
    assert d["avg_weight_g"] == 2000.0
    assert d["age_days"] == DIAS_EDAD
    assert d["ganancia_diaria_g"] == GANANCIA_ESPERADA
    assert d["fcr"] == 3.0
    assert d["ipe"] == IPE_ESPERADO
    assert d["reference"] == REFERENCIA_CANONICA


async def test_r184_ac10_estable_entre_llamadas(http_client, ipe):
    """R184-AC10: dos llamadas seguidas con los mismos datos devuelven lo mismo."""
    r1 = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_ok"]))
    r2 = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_ok"]))
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


# ═══════════════════════════════════════════════════════════════════════════
# Fronteras temporales — R184-AC16, AC17, AC18
# ═══════════════════════════════════════════════════════════════════════════

async def test_r184_ac16_ac17_hoy_y_sin_inicio_se_calculan_sin_500(http_client, ipe):
    """Lote del mismo día ⇒ clamp 1; sin `start_date` ⇒ legado 30. Nunca 500."""
    r_hoy = await http_client.get(_ipe_url(ipe["lote_hoy"]), headers=_cab(ipe["u_ok"]))
    assert r_hoy.status_code == 200, r_hoy.text
    d_hoy = r_hoy.json()
    assert d_hoy["age_days"] == 1
    assert d_hoy["ipe"] == 0.0  # sin pesajes: ganancia 0 (agregado vacío = 0, contrato existente)

    r_nulo = await http_client.get(_ipe_url(ipe["lote_nulo"]), headers=_cab(ipe["u_ok"]))
    assert r_nulo.status_code == 200, r_nulo.text
    d_nulo = r_nulo.json()
    assert d_nulo["age_days"] == 30
    assert d_nulo["ipe"] == 0.0


async def test_r184_ac18_sin_alimento_no_divide_por_cero(http_client, ipe):
    """Guarda `fcr > 0`: sin alimento el IPE es 0.0 controlado (no ZeroDivisionError)."""
    r = await http_client.get(_ipe_url(ipe["lote_hoy"]), headers=_cab(ipe["u_ok"]))
    assert r.status_code == 200
    d = r.json()
    assert d["fcr"] == 0
    assert d["ipe"] == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Seguridad — R184-AC20, AC22…AC27
# ═══════════════════════════════════════════════════════════════════════════

async def test_r184_ac20_inexistente_404_sin_fuga(http_client, ipe):
    r = await http_client.get(_ipe_url(999_999_999), headers=_cab(ipe["u_ok"]))
    assert r.status_code == 404
    assert r.json()["detail"] == "Lote no encontrado"


async def test_r184_ac22_ajeno_404_anti_enumeracion(http_client, ipe):
    r = await http_client.get(_ipe_url(ipe["lote_ajeno"]), headers=_cab(ipe["u_ok"]))
    assert r.status_code == 404
    assert r.json()["detail"] == "Lote no encontrado"


async def test_r184_ac24_sin_concesion_404(http_client, ipe):
    r = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_sin_concesion"]))
    assert r.status_code == 404
    assert r.json()["detail"] == "Lote no encontrado"


async def test_r184_ac25_rbac_ausente_403(http_client, ipe):
    r = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_sin_permiso"]))
    assert r.status_code == 403
    assert "reports:read" in r.json()["detail"]


async def test_r184_ac23_bu_empresa_off_404(http_client, ipe, test_database_url):
    """Empresa con la unidad APAGADA: lectura productiva denegada (GA-REM-040 · OD-16)."""
    motor = create_async_engine(test_database_url)
    async with motor.begin() as c:
        await c.execute(text("UPDATE company_business_units SET is_enabled = false WHERE id = :id"),
                        {"id": ipe["hab_a"]})
    try:
        r = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_ok"]))
        assert r.status_code == 404
        assert r.json()["detail"] == "Lote no encontrado"
    finally:
        async with motor.begin() as c:
            await c.execute(text("UPDATE company_business_units SET is_enabled = true WHERE id = :id"),
                            {"id": ipe["hab_a"]})
        await motor.dispose()


async def test_r184_ac26_actor_global_no_bypassa_bu_off(http_client, ipe, test_database_url):
    """La autoridad global lee por unidades HABILITADAS: con la BU apagada, 404 (OD-16)."""
    r_on = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_global"]))
    assert r_on.status_code == 200, r_on.text
    motor = create_async_engine(test_database_url)
    async with motor.begin() as c:
        await c.execute(text("UPDATE company_business_units SET is_enabled = false WHERE id = :id"),
                        {"id": ipe["hab_a"]})
    try:
        r_off = await http_client.get(_ipe_url(ipe["lote_ok"]), headers=_cab(ipe["u_global"]))
        assert r_off.status_code == 404, r_off.text
        assert r_off.json()["detail"] == "Lote no encontrado"
    finally:
        async with motor.begin() as c:
            await c.execute(text("UPDATE company_business_units SET is_enabled = true WHERE id = :id"),
                            {"id": ipe["hab_a"]})
        await motor.dispose()
