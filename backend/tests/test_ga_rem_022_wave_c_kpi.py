"""GA-REM-022 · Wave C KPI — RED (R-132 + R-131b).

Rojo en HEAD (`e58cfd4`):

- **R-132**: `% mortalidad` divide solo por `OpeningBalance` ⇒ un lote activado
  por **recepción** (sin apertura) reporta 0 % con muertes reales.
- **R-131(b)**: la edad del IPE usa `date.today()` incluso en lotes **cerrados**
  ⇒ sigue creciendo después del cierre (`end_date`).
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
    """Fase productiva única para los openings del test (código propio)."""
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


async def _lote(empresa: int, user_id: int, codigo: str, *, inicio, cierre=None, estado="active") -> int:
    from app.masters.models import BirdTypeEnum, Lot

    async with database.async_session() as session:
        lote = Lot(company_id=empresa, lot_code=codigo, bird_type=BirdTypeEnum.BROILER,
                   status=estado, activation_type="normal", start_date=inicio, end_date=cierre)
        session.add(lote)
        await session.commit()
        await session.refresh(lote)
        return lote.id


async def _evento(lot_id: int, empresa: int, user_id: int, tipo, fecha, movimientos: list[dict]):
    from app.operations.models import BirdMovement, EventStatus, OperationalEvent

    async with database.async_session() as session:
        evento = OperationalEvent(company_id=empresa, lot_id=lot_id, event_type=tipo,
                                  event_date=fecha, status=EventStatus.APPROVED,
                                  registered_by_id=user_id)
        session.add(evento)
        await session.flush()
        for mov in movimientos:
            session.add(BirdMovement(event_id=evento.id, **mov))
        await session.commit()


@pytest.mark.asyncio
async def test_rem022_r132_mortalidad_sobre_recepcion(auth_headers, http_client, seeded_ids):
    """AC-1/R-132: base = apertura + entradas ⇒ 10 muertes de 100 recibidas = 10 % (hoy 0 %)."""
    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    lote = await _lote(empresa, user_id, "GA022-R1", inicio=days_ago(50))
    await _evento(lote, empresa, user_id, EventType.BIRD_RECEPTION, days_ago(48),
                  [{"sex": "male", "quantity": 100}])
    await _evento(lote, empresa, user_id, EventType.MORTALITY_RECORDING, days_ago(2),
                  [{"sex": "male", "quantity": 10}])

    r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={lote}", headers=auth_headers)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["initial_population"] == 100, "la base incluye las entradas del motor (recepción)"
    assert cuerpo["total_deaths"] == 10
    assert cuerpo["mortality_rate_pct"] == 10.0, "0 % fabricado sobre muertes reales es el defecto"


@pytest.mark.asyncio
async def test_rem022_r132_sin_regresion_con_apertura(auth_headers, http_client, seeded_ids):
    """AC-2/R-132: lote con apertura y sin entradas ⇒ misma cifra que antes (no regresión)."""
    from app.lots.models import OpeningBalance
    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    lote = await _lote(empresa, user_id, "GA022-R2", inicio=days_ago(40))
    fase = await _fase()
    async with database.async_session() as session:
        session.add(OpeningBalance(lot_id=lote, activation_date=days_ago(40),
                                   phase_at_activation_id=fase, age_days=0,
                                   initial_male_count=250, initial_female_count=250,
                                   is_manual_activation=True, activated_by_id=user_id))
        await session.commit()
    await _evento(lote, empresa, user_id, EventType.MORTALITY_RECORDING, days_ago(1),
                  [{"sex": "female", "quantity": 25}])

    r = await http_client.get(f"/api/v1/reports/kpis/mortality?lot_id={lote}", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["mortality_rate_pct"] == 5.0
    assert r.json()["initial_population"] == 500


@pytest.mark.asyncio
async def test_rem022_r131b_edad_lote_cerrado(auth_headers, http_client, seeded_ids):
    """AC-4/R-131(b): lote cerrado ⇒ la edad se congela en `end_date` (60 días), no sigue con hoy."""
    from app.lots.models import OpeningBalance
    from app.operations.models import EventType

    empresa, user_id = seeded_ids["company_id"], seeded_ids["user_admin_id"]
    lote = await _lote(empresa, user_id, "GA022-C1", inicio=days_ago(70),
                       cierre=days_ago(10), estado="closed")
    fase = await _fase()
    async with database.async_session() as session:
        session.add(OpeningBalance(lot_id=lote, activation_date=days_ago(70),
                                   phase_at_activation_id=fase, age_days=0,
                                   initial_male_count=500, initial_female_count=500,
                                   is_manual_activation=True, activated_by_id=user_id))
        await session.commit()
    await _evento(lote, empresa, user_id, EventType.WEIGHT_RECORDING, days_ago(12),
                  [{"sex": "female", "quantity": 0, "avg_weight": 2100.0}])

    r = await http_client.get(f"/api/v1/reports/kpi/ipe/{lote}", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["age_days"] == 60, "70 = edad con hoy; 60 = edad con end_date (correcta)"
