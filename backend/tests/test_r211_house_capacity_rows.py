"""`R-211` · RED — capacidad del galpón **por fila** (`BR-17`) y decisión de acumulación.

La recepción de aves captura filas por galpón (`bird_movements[].target_house_id`). El
backend valida `BR-17` con la **Σ del evento** contra un solo galpón (el `house_id` del
evento, que la UI fija al primer destino — F-01e). Resultado: una llegada repartida entre dos
galpones —cada uno dentro de su capacidad— rechaza con **400 BR-17** (falso positivo); y el
mensaje no nombra el galpón.

Esperado: `BR-17` compara **por cada `target_house_id` de las filas** la Σ de ese galpón
contra su `capacity`; el `house_id` del evento deja de usarse para la Σ. Mensaje con galpón
y capacidad concretos.

`C-02` (decisión del propietario, **defecto A**): validar solo el evento — el exceso
**acumulado** entre eventos al mismo galpón queda como residual documentado (opción B lo
acumularía; no es este paquete). `R211-04` documenta el residual con A.

RED esperado en HEAD: 01 (400 falso positivo) y 02 (mensaje sin galpón); 03 (mono-galpón) y
04 (residual C-02=A) son controles verdes.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import House, Lot
from app.operations.models import OperationalEvent, Reversal
from tests.time_reference import iso_days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "R211-"
CAPACIDAD = 500


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, InspectionDetail, OperationalAlert,
    )
    from app.review.models import ApprovalAction

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(ids)))).scalars().all()
            if eventos:
                await c.execute(delete(OperationalAlert).where(
                    OperationalAlert.event_id.in_(eventos)))
                await c.execute(text(
                    "DELETE FROM notifications WHERE related_entity_id = ANY(:e)"
                ), {"e": eventos})
                await c.execute(delete(Reversal).where(
                    Reversal.original_event_id.in_(eventos)
                    | Reversal.reversal_event_id.in_(eventos)))
                for sub in (BirdMovement, EggMovement, FeedMovement, InspectionDetail,
                            ApprovalAction):
                    await c.execute(delete(sub).where(sub.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
        # Los eventos propios ya no existen: los galpones de prueba pueden irse.
        await c.execute(delete(House).where(House.name.like(f"{PREFIJO}%")))
    await e.dispose()


@pytest_asyncio.fixture
async def casas(motor, seeded_ids):
    """Dos galpones de 500 en la granja sembrada (el evento y las filas los referencian)."""
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        a = House(farm_id=seeded_ids["farm_id"], name=f"{PREFIJO}GALPON-A",
                  capacity=CAPACIDAD, is_active=True)
        b = House(farm_id=seeded_ids["farm_id"], name=f"{PREFIJO}GALPON-B",
                  capacity=CAPACIDAD, is_active=True)
        s.add_all([a, b])
        await s.commit()
        return {"a": a.id, "b": b.id}


async def _lote(client, cab, ids) -> int:
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": ids["company_id"], "farm_id": ids["farm_id"],
        "house_id": ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _recepcion(client, cab, ids, lote, filas):
    """`filas`: lista de `(target_house_id, cantidad)`. El `house_id` del evento imita a la UI."""
    return await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": lote, "farm_id": ids["farm_id"], "house_id": filas[0][0],
        "event_type": "bird_reception", "event_date": iso_days_ago(0),
        "bird_movements": [
            {"sex": "mixed", "quantity": n, "target_house_id": casa} for casa, n in filas
        ],
    })


# ── R211-01 · reparto válido entre dos galpones ───────────────────────────────

async def test_r211_01_dos_galpones_cada_uno_en_capacidad_es_201(
    client, auth_headers, seeded_ids, casas, motor
):
    """`AC-R211-01` · 500+500 a A+B (Σ del evento 1000 > capacidad de A) ⇒ **201**."""
    lote = await _lote(client, auth_headers, seeded_ids)
    r = await _recepcion(client, auth_headers, seeded_ids, lote,
                         [(casas["a"], 500), (casas["b"], 500)])
    assert r.status_code == 201, (
        f"cada galpón está dentro de su capacidad; la Σ del evento no puede decidir: "
        f"{r.status_code} {r.text}"
    )


# ── R211-02 · una fila excedida se rechaza y el mensaje nombra el galpón ──────

async def test_r211_02_fila_excedida_es_400_con_galpon(
    client, auth_headers, seeded_ids, casas, motor
):
    """`AC-R211-02` · A con 600 ⇒ 400 y el detalle nombra el galpón y su capacidad."""
    lote = await _lote(client, auth_headers, seeded_ids)
    r = await _recepcion(client, auth_headers, seeded_ids, lote, [(casas["a"], 600)])
    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "BR-17", r.json()
    detalle = r.json().get("detail", "")
    assert f"{PREFIJO}GALPON-A" in detalle and str(CAPACIDAD) in detalle, (
        f"el mensaje debe indicar el galpón concreto y su capacidad: {detalle}"
    )


# ── R211-03 · control mono-galpón ─────────────────────────────────────────────

async def test_r211_03_mono_galpon_control(
    client, auth_headers, seeded_ids, casas, motor
):
    """`AC-R211-03` · mono-galpón excedido sigue siendo 400 (sin relajación)."""
    lote = await _lote(client, auth_headers, seeded_ids)
    r = await _recepcion(client, auth_headers, seeded_ids, lote, [(casas["a"], 600)])
    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "BR-17", r.json()


# ── R211-04 · residual C-02=A documentado ─────────────────────────────────────

async def test_r211_04_dos_eventos_al_mismo_galpon_residual_documentado(
    client, auth_headers, seeded_ids, casas, motor
):
    """`AC-R211-04` (`C-02=A`) · dos eventos de 500 a A ⇒ 201+201 y el residual documentado.

    Con la opción B del propietario (acumular entre eventos) el segundo sería 400; el defecto
    A corrige el falso positivo y deja este residual **explícito** aquí.
    """
    lote = await _lote(client, auth_headers, seeded_ids)
    primera = await _recepcion(client, auth_headers, seeded_ids, lote, [(casas["a"], 500)])
    assert primera.status_code == 201, primera.text
    segunda = await _recepcion(client, auth_headers, seeded_ids, lote, [(casas["a"], 500)])
    assert segunda.status_code == 201, (
        f"`C-02=A`: sin acumulación entre eventos el segundo registro pasa (residual "
        f"documentado): {segunda.status_code} {segunda.text}"
    )
