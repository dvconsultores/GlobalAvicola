"""R-187 — Escala estándar del IPE (`GET /reports/kpi/ipe/{lot_id}`) — OD-22.

Contrato canónico (G-06) tras OD-22 (2026-09-11, decisión del propietario «Opción A»):

    IPE = (Viabilidad% × Ganancia_Diaria_g) / (FCR × 10)
    Ganancia_Diaria_g = avg_weight_g / age_days

La viabilidad ya llega como porcentaje (0-100: `100 − mortality_rate_pct`); el
`× 100` histórico era una doble conversión fracción→porcentaje y se retira. Bandas,
etiquetas, umbrales, fuentes, redondeos y esquema **no** cambian. R-184 (normalización
temporal `_dia()`) se preserva íntegro; el valor histórico del lote 11 (556.6) queda
**sustituido por OD-22** y NO es objetivo de regresión: los mismos insumos crudos deben
producir el valor OD-22 calculado independientemente.

Nota de ejecución: requiere PostgreSQL (suite canónica del repo). En local sin credenciales
de siembra (`GA_TEST_ADMIN_PASSWORD`, vía `test_credentials`) la suite queda `skipped` —
declarado, no fingido; corre en CI con `backend/scripts/run_tests.sh`. La evidencia
RED/GREEN ejecutada de esta tranche vive en `audit/ga-r187/`.
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

PREFIJO = "IPE-R187-"

# ═══════════════════════════════════════════════════════════════════════════
# Insumos crudos y valores esperados calculados A MANO desde OD-22
# (NUNCA desde el código bajo prueba). Redondeo final igual al contrato (1d).
# ═══════════════════════════════════════════════════════════════════════════
# Fórmula OD-22:  ipe = viabilidad × (peso/edad) / (fcr × 10);  fcr = kg_alimento/1000

# DET — mismos insumos crudos que la suite R-184 (19 d · 5 % muertes · 2000 g · 3000 kg)
#   viab = 95.0 · gain = 2000/19 = 105.2631… · fcr = 3.0
#   ipe  = (95.0 × (2000/19)) / 30 = 10000/30 = 333.333… → 333.3
#   (régimen anterior ×100 daba 33333.3 — aserción explícita de que no vuelve)
DET_DIAS, DET_MUERTES, DET_PESO, DET_ALIMENTO = 19, 50, 2000.0, 3000.0
IPE_DET = 333.3
GANANCIA_DET = 105.26

# BAJA — 28 d · 10 % muertes · 1500 g · 2000 kg (fcr 2.0)
#   ipe = 90.0 × (1500/28) / 20 = (135000/28)/20 = 241.0714… → 241.1 → 🔴 (<250)
BAJA_DIAS, BAJA_MUERTES, BAJA_PESO, BAJA_ALIMENTO = 28, 100, 1500.0, 2000.0
IPE_BAJA = 241.1

# MEDIA — 28 d · 5 % muertes · 2500 g · 3000 kg (fcr 3.0)
#   ipe = 95.0 × (2500/28) / 30 = (237500/28)/30 = 282.7380… → 282.7 → 🟡
MEDIA_DIAS, MEDIA_MUERTES, MEDIA_PESO, MEDIA_ALIMENTO = 28, 50, 2500.0, 3000.0
IPE_MEDIA = 282.7

# FRONTERAS EXACTAS (comparadores de UI intactos: >=300 🟢 · >=250 🟡 · resto 🔴)
# B249 — 10 d · 2 % muertes · 1020 g · 4000 kg (fcr 4.0) → 98×(1020/10)/40 = 249.9 → 🔴
B249_DIAS, B249_MUERTES, B249_PESO, B249_ALIMENTO = 10, 20, 1020.0, 4000.0
IPE_B249 = 249.9
# B250 — 10 d · 0 muertes · 1000 g · 4000 kg → 100×100/40 = 250.0 → 🟡
B250_DIAS, B250_MUERTES, B250_PESO, B250_ALIMENTO = 10, 0, 1000.0, 4000.0
IPE_B250 = 250.0
# B300 — 10 d · 0 muertes · 1200 g · 4000 kg → 100×120/40 = 300.0 → 🟢
B300_DIAS, B300_MUERTES, B300_PESO, B300_ALIMENTO = 10, 0, 1200.0, 4000.0
IPE_B300 = 300.0

REFERENCIA_CANONICA = {"excellent": ">300", "good": "250-300", "average": "200-250"}
CLAVES_RESPUESTA = {
    "lot_id", "viabilidad_pct", "avg_weight_g", "ganancia_diaria_g",
    "age_days", "fcr", "ipe", "reference",
}


def _banda(ipe: float) -> str:
    """Espejo EXACTO del comparador de UI (LotDetailPage.tsx:396-397 · LotReportPage.tsx:167-168).

    Control de comportamiento de frontera — NO es producto y NO redefine bandas:
    `>= 300 → 🟢` · `>= 250 → 🟡` · resto `→ 🔴`.
    """
    if ipe >= 300:
        return "🟢"
    if ipe >= 250:
        return "🟡"
    return "🔴"


def _cab(uid: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(uid)})}"}


@pytest_asyncio.fixture
async def ipe_od22(test_database_url, test_credentials):
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

        def _inicio(dias: int) -> datetime:
            return datetime.combine(date.today() - timedelta(days=dias),
                                    time.min, tzinfo=timezone.utc)

        def _lote(company_id: int, marca: str, start) -> Lot:
            lote = Lot(company_id=company_id,
                       lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=BirdTypeEnum.BROILER, status="active", start_date=start)
            s.add(lote)
            return lote

        # Lotes con datos OD-22 (alias → (días, muertes, peso_g, alimento_kg))
        specs = {
            "DET": (DET_DIAS, DET_MUERTES, DET_PESO, DET_ALIMENTO),
            "BAJA": (BAJA_DIAS, BAJA_MUERTES, BAJA_PESO, BAJA_ALIMENTO),
            "MEDIA": (MEDIA_DIAS, MEDIA_MUERTES, MEDIA_PESO, MEDIA_ALIMENTO),
            "B249": (B249_DIAS, B249_MUERTES, B249_PESO, B249_ALIMENTO),
            "B250": (B250_DIAS, B250_MUERTES, B250_PESO, B250_ALIMENTO),
            "B300": (B300_DIAS, B300_MUERTES, B300_PESO, B300_ALIMENTO),
        }
        lotes: dict[str, Lot] = {}
        for marca, (dias, muertes, peso, alimento) in specs.items():
            lotes[marca] = _lote(a.id, marca, _inicio(dias))
        l_hoy = _lote(a.id, "HOY", _inicio(0))
        l_nulo = _lote(a.id, "NULO", None)
        l_ajeno = _lote(b.id, "AJENO", _inicio(DET_DIAS))
        await s.flush()

        for marca, (dias, muertes, peso, alimento) in specs.items():
            lote = lotes[marca]
            s.add(OpeningBalance(
                lot_id=lote.id, activation_date=days_ago(dias),
                phase_at_activation_id=fase.id,
                initial_male_count=500, initial_female_count=500,
                is_manual_activation=True, activated_by_id=u_ok.id))
            if muertes > 0:
                ev_m = OperationalEvent(company_id=a.id, lot_id=lote.id,
                                        event_type=EventType.MORTALITY_RECORDING,
                                        event_date=days_ago(2), status=EventStatus.APPROVED,
                                        registered_by_id=u_ok.id)
                s.add(ev_m)
                await s.flush()
                s.add(BirdMovement(event_id=ev_m.id, quantity=muertes))
            ev_w = OperationalEvent(company_id=a.id, lot_id=lote.id,
                                    event_type=EventType.WEIGHT_RECORDING,
                                    event_date=days_ago(2), status=EventStatus.APPROVED,
                                    registered_by_id=u_ok.id)
            s.add(ev_w)
            await s.flush()
            s.add(BirdMovement(event_id=ev_w.id, quantity=0, avg_weight=peso))
            ev_f = OperationalEvent(company_id=a.id, lot_id=lote.id,
                                    event_type=EventType.FEED_REGISTRATION,
                                    event_date=days_ago(1), status=EventStatus.APPROVED,
                                    registered_by_id=u_ok.id)
            s.add(ev_f)
            await s.flush()
            s.add(FeedMovement(event_id=ev_f.id, quantity_kg=alimento))
        await s.commit()

        datos = {
            **{f"lote_{m.lower()}": l.id for m, l in lotes.items()},
            "lote_hoy": l_hoy.id, "lote_nulo": l_nulo.id, "lote_ajeno": l_ajeno.id,
            "u_ok": u_ok.id, "u_sin_concesion": u_sin_concesion.id,
            "u_sin_permiso": u_sin_permiso.id, "u_global": u_global.id,
        }

    yield datos

    # ── Limpieza determinista por prefijo ─────────────────────────────────────
    from app.audit.models import AuditLog
    from app.lots.models import OpeningBalance
    from app.masters.models import Lot
    from app.operations.models import BirdMovement, FeedMovement, OperationalEvent

    async with motor.begin() as c:
        lotes_ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        usuarios = (await c.execute(text(
            "SELECT id FROM users WHERE username LIKE :p"), {"p": f"{PREFIJO}%"})).scalars().all()
        if lotes_ids:
            existe_n = (await c.execute(text("SELECT to_regclass('public.notifications')"))).scalar()
            if existe_n:
                await c.execute(text(
                    "DELETE FROM notifications WHERE related_entity_type = 'lot' "
                    "AND related_entity_id = ANY(:ids)"), {"ids": list(lotes_ids)})
            await c.execute(delete(BirdMovement).where(BirdMovement.event_id.in_(
                select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(lotes_ids)))))
            await c.execute(delete(FeedMovement).where(FeedMovement.event_id.in_(
                select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(lotes_ids)))))
            await c.execute(delete(OperationalEvent).where(OperationalEvent.lot_id.in_(lotes_ids)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(lotes_ids)))
        if lotes_ids or usuarios:
            await c.execute(delete(AuditLog).where(or_(
                AuditLog.lot_id.in_(lotes_ids) if lotes_ids else AuditLog.lot_id.is_(None),
                AuditLog.user_id.in_(usuarios) if usuarios else AuditLog.user_id.is_(None))))
        if lotes_ids:
            await c.execute(delete(Lot).where(Lot.id.in_(lotes_ids)))
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
# Núcleo OD-22 — el ×100 debe desaparecer (R187-AC06, AC07, AC24, AC25)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r187_ac06_ac07_det_od22_333_3_y_sin_x100(http_client, ipe_od22):
    """Determinista: mismos insumos crudos que R-184 ⇒ valor OD-22 (333.3), no 33333.3."""
    r = await http_client.get(_ipe_url(ipe_od22["lote_det"]), headers=_cab(ipe_od22["u_ok"]))
    assert r.status_code == 200, f"IPE devolvió {r.status_code}: {r.text}"
    d = r.json()
    assert set(d) == CLAVES_RESPUESTA
    assert d["viabilidad_pct"] == 95.0
    assert d["avg_weight_g"] == 2000.0
    assert d["age_days"] == DET_DIAS
    assert d["ganancia_diaria_g"] == GANANCIA_DET
    assert d["fcr"] == 3.0
    assert d["ipe"] == IPE_DET
    assert d["ipe"] != 33333.3, "el ×100 histórico (régimen anterior) no debe volver"
    assert d["reference"] == REFERENCIA_CANONICA


def test_r187_ac25_matematica_independiente():
    """El esperado se calcula a mano desde OD-22 — nunca desde el código bajo prueba."""
    esperado = (95.0 * (2000.0 / 19)) / (3.0 * 10)
    assert round(esperado, 1) == IPE_DET
    # Nota histórica (régimen anterior, ×100) — documentada, NO objetivo de regresión:
    assert round(esperado * 100, 1) == 33333.3


async def test_r187_ac08_estable_entre_llamadas(http_client, ipe_od22):
    r1 = await http_client.get(_ipe_url(ipe_od22["lote_det"]), headers=_cab(ipe_od22["u_ok"]))
    r2 = await http_client.get(_ipe_url(ipe_od22["lote_det"]), headers=_cab(ipe_od22["u_ok"]))
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


# ═══════════════════════════════════════════════════════════════════════════
# Bandas con resultado OD-22 exacto — comparadores SIN tocar (AC13, AC24)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r187_ac13_banda_baja_241_1(http_client, ipe_od22):
    r = await http_client.get(_ipe_url(ipe_od22["lote_baja"]), headers=_cab(ipe_od22["u_ok"]))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ipe"] == IPE_BAJA
    assert _banda(d["ipe"]) == "🔴"


async def test_r187_ac13_banda_media_282_7(http_client, ipe_od22):
    r = await http_client.get(_ipe_url(ipe_od22["lote_media"]), headers=_cab(ipe_od22["u_ok"]))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ipe"] == IPE_MEDIA
    assert _banda(d["ipe"]) == "🟡"


async def test_r187_ac13_banda_alta_333_3(http_client, ipe_od22):
    r = await http_client.get(_ipe_url(ipe_od22["lote_det"]), headers=_cab(ipe_od22["u_ok"]))
    d = r.json()
    assert d["ipe"] == IPE_DET
    assert _banda(d["ipe"]) == "🟢"


# ═══════════════════════════════════════════════════════════════════════════
# Fronteras exactas — comportamiento ACTUAL de los comparadores (AC15, AC16)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r187_ac15_frontera_250(http_client, ipe_od22):
    """249.9 → 🔴 · 250.0 → 🟡 (dispara `>= 250`). Sin cambio de umbral."""
    r249 = await http_client.get(_ipe_url(ipe_od22["lote_b249"]), headers=_cab(ipe_od22["u_ok"]))
    r250 = await http_client.get(_ipe_url(ipe_od22["lote_b250"]), headers=_cab(ipe_od22["u_ok"]))
    assert r249.status_code == 200 and r250.status_code == 200
    assert r249.json()["ipe"] == IPE_B249 and _banda(r249.json()["ipe"]) == "🔴"
    assert r250.json()["ipe"] == IPE_B250 and _banda(r250.json()["ipe"]) == "🟡"


async def test_r187_ac16_frontera_300(http_client, ipe_od22):
    """300.0 → 🟢 (dispara `>= 300`). Sin cambio de umbral."""
    r = await http_client.get(_ipe_url(ipe_od22["lote_b300"]), headers=_cab(ipe_od22["u_ok"]))
    assert r.status_code == 200, r.text
    assert r.json()["ipe"] == IPE_B300
    assert _banda(r.json()["ipe"]) == "🟢"


# ═══════════════════════════════════════════════════════════════════════════
# Control de fechas (GREEN CONTROL R-184) — AC19…AC23, AC29
# ═══════════════════════════════════════════════════════════════════════════

async def test_r187_ac19_ac23_mismo_dia_y_sin_fecha_controlados(http_client, ipe_od22):
    """Mismo día ⇒ age 1 · sin fecha ⇒ 30. Nunca 500; ipe 0.0 sin datos."""
    r_hoy = await http_client.get(_ipe_url(ipe_od22["lote_hoy"]), headers=_cab(ipe_od22["u_ok"]))
    assert r_hoy.status_code == 200, r_hoy.text
    d_hoy = r_hoy.json()
    assert d_hoy["age_days"] == 1
    assert d_hoy["ipe"] == 0.0
    assert d_hoy["fcr"] == 0

    r_nulo = await http_client.get(_ipe_url(ipe_od22["lote_nulo"]), headers=_cab(ipe_od22["u_ok"]))
    assert r_nulo.status_code == 200, r_nulo.text
    d_nulo = r_nulo.json()
    assert d_nulo["age_days"] == 30
    assert d_nulo["ipe"] == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Seguridad — AC37, AC39, AC40 (comportamiento gobernado existente)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r187_ac37_ajeno_404_anti_enumeracion(http_client, ipe_od22):
    r = await http_client.get(_ipe_url(ipe_od22["lote_ajeno"]), headers=_cab(ipe_od22["u_ok"]))
    assert r.status_code == 404
    assert r.json()["detail"] == "Lote no encontrado"


async def test_r187_ac37_inexistente_404(http_client, ipe_od22):
    r = await http_client.get(_ipe_url(999_999_999), headers=_cab(ipe_od22["u_ok"]))
    assert r.status_code == 404


async def test_r187_ac39_sin_concesion_404(http_client, ipe_od22):
    r = await http_client.get(_ipe_url(ipe_od22["lote_det"]),
                              headers=_cab(ipe_od22["u_sin_concesion"]))
    assert r.status_code == 404
    assert r.json()["detail"] == "Lote no encontrado"


async def test_r187_ac40_rbac_ausente_403(http_client, ipe_od22):
    r = await http_client.get(_ipe_url(ipe_od22["lote_det"]),
                              headers=_cab(ipe_od22["u_sin_permiso"]))
    assert r.status_code == 403
    assert "reports:read" in r.json()["detail"]
