"""GA-REM-022 · R-131 + R-141 — RED (decisión del Owner 2026-09-16).

Rojo en HEAD (`b58136a`):

- **R-131**: FCR = `feed_kg / 1000` (sin dimensión de ganancia). Canonical del
  Owner: `FCR = masa alimento / ganancia total de peso vivo` (misma unidad;
  `/1000` solo como conversión de gramos→kg demostrada). Sin datos de peso ⇒
  **UNKNOWN** (`null`), nunca un número fabricado.
- **R-141**: los agregados no usan el conjunto filtrado por estado del detalle
  certificado (R-218) — pesajes/mortandad **cancelados** alteran IPE,
  uniformidad y tendencia.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from time_reference import days_ago  # noqa: E402


async def _fase() -> int:
    from app.masters.models import ProductivePhase

    async with database.async_session() as session:
        existente = (await session.execute(
            select(ProductivePhase).where(ProductivePhase.code == "REM022"))).scalars().first()
        if existente is not None:
            return existente.id
        fase = ProductivePhase(name="KPI Wave C", code="REM022", is_initial=True, order=1)
        session.add(fase)
        await session.commit()
        await session.refresh(fase)
        return fase.id


async def _lote(empresa: int, codigo: str, *, inicio=None) -> int:
    from app.masters.models import BirdTypeEnum, Lot

    async with database.async_session() as session:
        lote = Lot(company_id=empresa, lot_code=codigo, bird_type=BirdTypeEnum.BROILER,
                   status="active", activation_type="normal", start_date=inicio or days_ago(40))
        session.add(lote)
        await session.commit()
        await session.refresh(lote)
        return lote.id


async def _opening(lot_id: int, user_id: int, *, machos=500, hembras=500, peso_g=None):
    from app.lots.models import OpeningBalance

    fase = await _fase()
    async with database.async_session() as session:
        session.add(OpeningBalance(lot_id=lot_id, activation_date=days_ago(40),
                                   phase_at_activation_id=fase, age_days=0,
                                   initial_male_count=machos, initial_female_count=hembras,
                                   current_avg_weight=peso_g,
                                   is_manual_activation=True, activated_by_id=user_id))
        await session.commit()


async def _evento(lot_id: int, empresa: int, user_id: int, tipo, *, status, movimientos=None, feed_kg=None, fecha=None):
    from app.operations.models import BirdMovement, EventStatus, FeedMovement, OperationalEvent

    estado = {"approved": EventStatus.APPROVED, "cancelled": EventStatus.CANCELLED}[status]
    async with database.async_session() as session:
        evento = OperationalEvent(company_id=empresa, lot_id=lot_id, event_type=tipo,
                                  event_date=fecha or days_ago(2), status=estado,
                                  registered_by_id=user_id)
        session.add(evento)
        await session.flush()
        for mov in (movimientos or []):
            session.add(BirdMovement(event_id=evento.id, **mov))
        if feed_kg is not None:
            session.add(FeedMovement(event_id=evento.id, quantity_kg=feed_kg))
        await session.commit()


@pytest.mark.asyncio
async def test_r131_fcr_canonico_alimento_por_ganancia(auth_headers, http_client, seeded_ids):
    """AC-R131-1: FCR = alimento / (Δpeso × aves) con unidades normalizadas (no `/1000`)."""
    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    lote = await _lote(empresa, "GA022F-R131A")
    await _opening(lote, user_id, machos=1000, hembras=1000, peso_g=1000.0)  # 2000 aves; inicial 1000 g
    await _evento(lote, empresa, user_id, EventType.WEIGHT_RECORDING, status="approved",
                  movimientos=[{"sex": "female", "quantity": 0, "avg_weight": 2000.0}])
    await _evento(lote, empresa, user_id, EventType.FEED_REGISTRATION, status="approved", feed_kg=3000.0)

    r = await http_client.get(f"/api/v1/reports/kpis/feed-conversion?lot_id={lote}", headers=auth_headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["avg_weight_initial_g"] == 1000.0
    assert d["avg_weight_final_g"] == 2000.0
    assert d["weight_gain_kg"] == 2000.0, "Δ1 kg × 2.000 aves = 2.000 kg"
    assert d["feed_conversion_ratio"] == 1.5, "3.000 kg alimento / 2.000 kg ganancia (antes: 3.0 = /1000)"
    assert d["unit"] == "kg feed / kg gain"


@pytest.mark.asyncio
async def test_r131_sin_pesos_fcr_unknown(auth_headers, http_client, seeded_ids):
    """AC-R131-2: sin datos de peso la ganancia no existe ⇒ UNKNOWN, jamás un número fabricado."""
    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    lote = await _lote(empresa, "GA022F-R131B")
    await _opening(lote, user_id)
    await _evento(lote, empresa, user_id, EventType.FEED_REGISTRATION, status="approved", feed_kg=2000.0)

    r = await http_client.get(f"/api/v1/reports/kpis/feed-conversion?lot_id={lote}", headers=auth_headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["feed_conversion_ratio"] is None, "1.99 ó 2.0 fabricados serían el defecto R-131"
    assert d["weight_gain_kg"] is None
    assert "insufficient" in (d.get("note") or "").lower() or d.get("status") == "insufficient_data"


@pytest.mark.asyncio
async def test_r141_ipe_ignora_pesajes_cancelados(auth_headers, http_client, seeded_ids):
    """AC-R141-1: el IPE usa el mismo conjunto filtrado que el detalle (R-218) — cancelados fuera."""
    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    lote = await _lote(empresa, "GA022F-R141A")
    await _opening(lote, user_id)
    await _evento(lote, empresa, user_id, EventType.WEIGHT_RECORDING, status="approved",
                  movimientos=[{"sex": "female", "quantity": 0, "avg_weight": 1500.0}])
    await _evento(lote, empresa, user_id, EventType.WEIGHT_RECORDING, status="cancelled",
                  movimientos=[{"sex": "female", "quantity": 0, "avg_weight": 9000.0}])

    r = await http_client.get(f"/api/v1/reports/kpi/ipe/{lote}", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["avg_weight_g"] == 1500.0, "(1500+9000)/2 = 5250 sería el defecto E-24"


@pytest.mark.asyncio
async def test_r141_uniformidad_mismo_conjunto_que_detalle(auth_headers, http_client, seeded_ids):
    """AC-R141-3: uniformidad con el MISMO conjunto filtrado: un cancelado no cambia el CV."""
    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    base = await _lote(empresa, "GA022F-R141B")
    extra = await _lote(empresa, "GA022F-R141C")
    for lote in (base, extra):
        await _opening(lote, user_id)
        for peso in (1600.0, 1400.0):
            await _evento(lote, empresa, user_id, EventType.WEIGHT_RECORDING, status="approved",
                          movimientos=[{"sex": "female", "quantity": 0, "avg_weight": peso}])
    await _evento(extra, empresa, user_id, EventType.WEIGHT_RECORDING, status="cancelled",
                  movimientos=[{"sex": "female", "quantity": 0, "avg_weight": 9000.0}])

    rb = (await http_client.get(f"/api/v1/reports/kpi/weight-uniformity/{base}", headers=auth_headers)).json()
    re = (await http_client.get(f"/api/v1/reports/kpi/weight-uniformity/{extra}", headers=auth_headers)).json()
    assert re["n_samples"] == rb["n_samples"] == 2, "el cancelado no es una muestra"
    assert re["cv_pct"] == rb["cv_pct"], "el cancelado no puede alterar el CV del lote"


@pytest.mark.asyncio
async def test_r141_tendencia_mortalidad_ignora_cancelados(auth_headers, http_client, seeded_ids):
    """AC-R141-4: la tendencia del panel suma solo eventos del conjunto aceptado."""
    from datetime import datetime, timezone

    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    lote = await _lote(empresa, "GA022F-R141D")

    def _semana_actual(dashboard: dict) -> int:
        from time_reference import reference_today
        wk = f"S{reference_today().isocalendar().week}"
        return sum(t["mortality"] for t in dashboard.get("mortality_trend", []) if t["week"] == wk)

    antes = _semana_actual((await http_client.get("/api/v1/dashboard/admin", headers=auth_headers)).json())
    await _evento(lote, empresa, user_id, EventType.MORTALITY_RECORDING, status="approved",
                  movimientos=[{"sex": "male", "quantity": 10}])
    await _evento(lote, empresa, user_id, EventType.MORTALITY_RECORDING, status="cancelled",
                  movimientos=[{"sex": "male", "quantity": 500}])
    despues = _semana_actual((await http_client.get("/api/v1/dashboard/admin", headers=auth_headers)).json())

    assert despues - antes == 10, f"510 = incluir cancelados; Δ={despues - antes}"
