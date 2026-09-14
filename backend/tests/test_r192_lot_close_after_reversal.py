"""`R-192` · RED — cierre de lote con reversos efectivos, resumen de cierre **neto** y `R7`.

`OD-19`/`GA-REM-041` añadió el reverso interno: la contrapartida aprobada deja original y
contrapartida en `REVERSED`, estado terminal no cancelable, con efecto neto 0 sobre los
saldos (`_suma_neta`). `R7` (`GA-REM-036`) y el resumen de cierre (`R-73`) se escribieron
**antes** y no conocen `REVERSED`:

- `R7` lo trata como «sin aprobar» ⇒ un lote con un par revertido **no puede cerrarse**
  («2 en «reversed»… apruébelos») — imposible de resolver: `REVERSED` no admite acción.
- Los tres sumatorios del resumen no filtran estado: mortalidad/alimento/huevos **anulados
  o revertidos cuentan**.
- La UI de cierre (`LotDetailPage.handleCloseLot`) sólo hace `console.error` ante un 400.

El par `REVERSED` se crea por la **ruta real**: `POST /reversals` + aprobación por el motor
de revisión (aprobador ≠ solicitante, `BR-14`). `_fijar_estado` sólo se usa para los
originales (como en `test_lot_close_approval.py`) y para el parámetro documental de `R-192-06`.

RED esperado en HEAD: 01 (400 R7 en vez de 200), 02 (falta «reverso pendiente» — C-07),
03 (`total_mortality` 15 y `total_eggs` 140 en vez de 5/100), 04 (400 R7), 05 (rule R7 en vez
de BR-05) y 06 (`reversed` bloquea). Controles verdes: estado del par, no-mutación ante 400.
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
from app.masters.models import Lot
from app.operations.models import EventStatus, OperationalEvent, Reversal
from tests.time_reference import iso_days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "R192-"

BLOQUEAN = [
    EventStatus.DRAFT, EventStatus.REGISTERED, EventStatus.PENDING_REVIEW,
    EventStatus.IN_REVIEW, EventStatus.RETURNED, EventStatus.CORRECTED,
    EventStatus.REJECTED,
]
NO_BLOQUEAN = [
    EventStatus.APPROVED, EventStatus.CONSOLIDATED, EventStatus.SENT_TO_SAP,
    EventStatus.SAP_CONFIRMED, EventStatus.SAP_ERROR, EventStatus.CANCELLED,
]


def _cabecera(user_id: int) -> dict:
    from app.auth.security import create_access_token
    return {"Authorization": "Bearer " + create_access_token(data={"sub": str(user_id)})}


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
    await e.dispose()


async def _fijar_estado(motor, event_id, estado):
    """Coloca un original en un estado concreto (la guarda es lo que se prueba, no el flujo)."""
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        evento = (await s.execute(select(OperationalEvent).where(
            OperationalEvent.id == event_id))).scalar_one()
        evento.status = estado
        await s.commit()


async def _estado(motor, event_id) -> str:
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        estado = (await s.execute(select(OperationalEvent.status).where(
            OperationalEvent.id == event_id))).scalar_one()
        return estado.value


@pytest_asyncio.fixture
async def lote_cerrable(client, auth_headers, seeded_ids, motor):
    """Lote activo con recepción, pesaje, alimento e inspección **aprobados** (`BR-05` ok).

    La inspección es el registro movible de los tests de estados; el pesaje y el alimento no
    se tocan para no romper `BR-05` por la causa equivocada.
    """
    r = await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    lot_id = r.json()["id"]

    ids = []
    for tipo, extra in (
        ("bird_reception", {"bird_movements": [
            {"sex": "mixed", "quantity": 100, "house_id": seeded_ids["house_id"]}]}),
        ("weight_recording", {"bird_movements": [
            {"sex": "mixed", "quantity": 10, "avg_weight": 2000}]}),
        ("feed_registration", {"feed_movements": [{"quantity_kg": 100.0}]}),
        ("farm_inspection", {"inspection_details": [
            {"parameter": "Bioseguridad", "value": "ok", "status": "ok"}]}),
    ):
        ev = await client.post("/api/v1/operations", headers=auth_headers, json={
            "lot_id": lot_id, "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"], "event_type": tipo,
            "event_date": iso_days_ago(0), **extra,
        })
        assert ev.status_code == 201, f"{tipo}: {ev.text}"
        ids.append(ev.json()["id"])
        await _fijar_estado(motor, ev.json()["id"], EventStatus.APPROVED)

    return {"lot_id": lot_id, "eventos": ids}


async def _solicitar_reverso(client, cab, event_id):
    return await client.post("/api/v1/reversals", headers=cab,
                             json={"event_id": event_id, "reason": f"{PREFIJO}prueba"})


async def _contrapartida(motor, event_id) -> int:
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return (await s.execute(select(Reversal.reversal_event_id).where(
            Reversal.original_event_id == event_id))).scalar_one()


async def _aprobar_contrapartida(client, cab_aprobador, cp_id):
    r = await client.post(f"/api/v1/review/start/{cp_id}", headers=cab_aprobador)
    assert r.status_code in (200, 201), r.text
    r = await client.post("/api/v1/approvals/approve", headers=cab_aprobador,
                          json={"event_id": cp_id})
    assert r.status_code in (200, 201), r.text
    return r


async def _reverso_efectivo(client, motor, cab, cab_aprobador, event_id) -> int:
    r = await _solicitar_reverso(client, cab, event_id)
    assert r.status_code == 201, r.text
    cp = await _contrapartida(motor, event_id)
    await _aprobar_contrapartida(client, cab_aprobador, cp)
    return cp


async def _cerrar(client, cab, lot_id):
    return await client.post(f"/api/v1/lots/{lot_id}/close", headers=cab)


async def _estado_del_lote(motor, lot_id):
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == lot_id))).scalar_one()
        return lote.status, lote.end_date


# ── R-192-01 · el par revertido no impide el cierre ───────────────────────────

async def test_r192_01_un_par_revertido_no_impide_el_cierre(
    client, auth_headers, seeded_ids, lote_cerrable, motor
):
    """`AC01` · mortalidad aprobada + revertida (par real) ⇒ el lote cierra y el resumen es neto."""
    mort = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote_cerrable["lot_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "mortality_recording",
        "event_date": iso_days_ago(0),
        "bird_movements": [{"sex": "mixed", "quantity": 5}],
    })
    assert mort.status_code == 201, mort.text
    mort_id = mort.json()["id"]
    await _fijar_estado(motor, mort_id, EventStatus.APPROVED)

    aprobador = _cabecera(seeded_ids["user_approver_id"])
    cp = await _reverso_efectivo(client, motor, auth_headers, aprobador, mort_id)

    # CONTROL · el par quedó efectivamente en reversed.
    assert await _estado(motor, mort_id) == "reversed"
    assert await _estado(motor, cp) == "reversed"

    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, (
        f"un par revertido (estado terminal decidido) no puede impedir el cierre: "
        f"{r.status_code} {r.text}"
    )


# ── R-192-02 · la contrapartida pendiente sí bloquea, y se nombra (C-07) ──────

async def test_r192_02_la_contrapartida_pendiente_si_impide_el_cierre(
    client, auth_headers, seeded_ids, lote_cerrable, motor
):
    """`AC03` · control exacto de `R7` + `AC17` · `C-07`: el detalle distingue el reverso."""
    mort = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote_cerrable["lot_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "mortality_recording",
        "event_date": iso_days_ago(0),
        "bird_movements": [{"sex": "mixed", "quantity": 5}],
    })
    assert mort.status_code == 201, mort.text
    mort_id = mort.json()["id"]
    await _fijar_estado(motor, mort_id, EventStatus.APPROVED)

    r = await _solicitar_reverso(client, auth_headers, mort_id)
    assert r.status_code == 201, r.text
    assert await _estado(motor, await _contrapartida(motor, mort_id)) == "pending_review"

    cierre = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert cierre.status_code == 400, cierre.text
    assert cierre.json().get("rule") == "R7", cierre.json()
    assert "reverso pendiente" in cierre.json().get("detail", ""), (
        f"`C-07`: el detalle debe distinguir el reverso pendiente de otro registro vivo: "
        f"{cierre.json().get('detail')}"
    )

    # No mutación: la negativa precede a tocar el lote.
    situacion, fecha = await _estado_del_lote(motor, lote_cerrable["lot_id"])
    assert situacion == "active", f"el lote cambió pese al rechazo: {situacion}"
    assert fecha is None, "se fijó la fecha de cierre pese al rechazo"


# ── R-192-03 · el resumen excluye lo cancelado ────────────────────────────────

async def test_r192_03_el_resumen_excluye_cancelados(
    client, auth_headers, seeded_ids, lote_cerrable, motor
):
    """`AC05`/`AC07` · mortalidad 5 aprobada + 10 anulada ⇒ 5; huevos 100 + 40 anulados ⇒ 100."""
    creados = []
    for tipo, extra in (
        ("mortality_recording", {"bird_movements": [{"sex": "mixed", "quantity": 5}]}),
        ("mortality_recording", {"bird_movements": [{"sex": "mixed", "quantity": 10}]}),
        ("egg_collection", {"egg_movements": [{"egg_type": "table", "quantity": 100}]}),
        ("egg_collection", {"egg_movements": [{"egg_type": "table", "quantity": 40}]}),
    ):
        ev = await client.post("/api/v1/operations", headers=auth_headers, json={
            "lot_id": lote_cerrable["lot_id"], "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"], "event_type": tipo,
            "event_date": iso_days_ago(0), **extra,
        })
        assert ev.status_code == 201, f"{tipo}: {ev.text}"
        creados.append(ev.json()["id"])

    mort5, mort10, egg100, egg40 = creados
    await _fijar_estado(motor, mort5, EventStatus.APPROVED)
    await _fijar_estado(motor, egg100, EventStatus.APPROVED)
    # Las dos de 10 y 40 se anulan antes de aprobar: no representan operación.
    for ev_id in (mort10, egg40):
        r = await client.post(f"/api/v1/operations/{ev_id}/cancel", headers=auth_headers)
        assert r.status_code in (200, 201), r.text

    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["total_mortality"] == 5, (
        f"la mortalidad anulada (10) no puede contar: {cuerpo['total_mortality']}"
    )
    assert cuerpo["total_eggs"] == 100, (
        f"los huevos anulados (40) no pueden contar: {cuerpo['total_eggs']}"
    )


# ── R-192-04 · el resumen excluye el par revertido ────────────────────────────

async def test_r192_04_el_resumen_excluye_el_par_revertido(
    client, auth_headers, seeded_ids, lote_cerrable, motor
):
    """`AC06` · alimento 100 (fixture) + 7 revertido (par real) ⇒ `total_feed_kg` 100."""
    feed = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote_cerrable["lot_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "feed_registration",
        "event_date": iso_days_ago(0),
        "feed_movements": [{"quantity_kg": 7.0}],
    })
    assert feed.status_code == 201, feed.text
    feed_id = feed.json()["id"]
    await _fijar_estado(motor, feed_id, EventStatus.APPROVED)

    aprobador = _cabecera(seeded_ids["user_approver_id"])
    await _reverso_efectivo(client, motor, auth_headers, aprobador, feed_id)

    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["total_feed_kg"] == 100.0, (
        f"el alimento revertido (7 kg, par efectivo) no puede contar: {cuerpo['total_feed_kg']}"
    )
    assert cuerpo["approved_events"] == 4, (
        f"`AC08`: el par revertido no cuenta como aprobado (fixture: 4 aprobados): "
        f"{cuerpo['approved_events']}"
    )


# ── R-192-05 · BR-05 ignora el pesaje revertido ───────────────────────────────

async def test_r192_05_br05_ignora_el_pesaje_revertido(
    client, auth_headers, seeded_ids, motor
):
    """`AC09` · único pesaje revertido + alimento vigente ⇒ `400 BR-05` (no `R7`)."""
    r = await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    lot_id = r.json()["id"]

    peso = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lot_id, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "weight_recording",
        "event_date": iso_days_ago(0),
        "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 2000}],
    })
    assert peso.status_code == 201, peso.text
    peso_id = peso.json()["id"]
    await _fijar_estado(motor, peso_id, EventStatus.APPROVED)

    feed = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lot_id, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "feed_registration",
        "event_date": iso_days_ago(0),
        "feed_movements": [{"quantity_kg": 50.0}],
    })
    assert feed.status_code == 201, feed.text
    await _fijar_estado(motor, feed.json()["id"], EventStatus.APPROVED)

    aprobador = _cabecera(seeded_ids["user_approver_id"])
    await _reverso_efectivo(client, motor, auth_headers, aprobador, peso_id)

    cierre = await _cerrar(client, auth_headers, lot_id)
    assert cierre.status_code == 400, (
        f"un pesaje revertido no es un pesaje vigente para `BR-05`: {cierre.text}"
    )
    assert cierre.json().get("rule") == "BR-05", cierre.json()


# ── R-192-06 · los trece estados conservan su veredicto; `REVERSED` no bloquea ─

@pytest.mark.parametrize("estado", BLOQUEAN, ids=[f"bloquea_{e.value}" for e in BLOQUEAN])
async def test_r192_06_bloqueantes(
    client, auth_headers, lote_cerrable, motor, estado
):
    """`AC04` · los siete estados sin decidir siguen bloqueando el cierre."""
    await _fijar_estado(motor, lote_cerrable["eventos"][3], estado)
    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 400, f"«{estado.value}» debe bloquear: {r.status_code} {r.text}"
    assert r.json().get("rule") == "R7", r.json()


@pytest.mark.parametrize("estado", NO_BLOQUEAN, ids=[f"no_bloquea_{e.value}" for e in NO_BLOQUEAN])
async def test_r192_06_no_bloqueantes(
    client, auth_headers, lote_cerrable, motor, estado
):
    """`AC04` · los seis no gobernados no bloquean (control de no-bloqueo excesivo)."""
    await _fijar_estado(motor, lote_cerrable["eventos"][3], estado)
    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, f"«{estado.value}» no debe bloquear: {r.status_code} {r.text}"


async def test_r192_06_reversed_por_base_no_bloquea(
    client, auth_headers, lote_cerrable, motor
):
    """`AC04`/`C-10` · `R7` decide por **estado**: `REVERSED` sin fila `reversals` tampoco bloquea."""
    await _fijar_estado(motor, lote_cerrable["eventos"][3], EventStatus.REVERSED)
    r = await _cerrar(client, auth_headers, lote_cerrable["lot_id"])
    assert r.status_code == 200, (
        f"`REVERSED` es un estado terminal decidido y no puede bloquear: {r.status_code} {r.text}"
    )
