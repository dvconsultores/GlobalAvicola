"""GA-REQ-061 · T14 · C5 — reconciliación Opening/Post/Lifetime (RED).

Rojo en HEAD (`fe5fe98`): no existe `GET /cutover-batches/{id}/reconciliation`
(404). Goldens de la spec: **10.000 − 35 = 9.965** (saldo vivo; prohibido
9.465), **lifetime 535**, UNKNOWN visible (jamás 0), post-cutover = solo eventos
con fecha **posterior** al corte, y reconciliación reproducible.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from test_ga_req_061_cutover_c2_lifecycle import _subir, _xlsx  # noqa: E402
from test_ga_req_061_cutover_c4_apply import _batch_aprobado, _fase  # noqa: E402
from time_reference import days_ago, iso_days_ago  # noqa: E402

# Corte fijado por `_batch_aprobado` (`CORTE` de C4): mismo día civil computado.
DIA_CORTE = days_ago(40).isoformat()



def _filas(etiqueta: str) -> list[list]:
    return [
        [f"CUT-G5-{etiqueta}-1", iso_days_ago(60), 5000, 5000, 300, 200, None, "golden 10.000/500"],
        [f"CUT-G5-{etiqueta}-2", iso_days_ago(45), 2000, 2000, None, None, None, "histórico desconocido"],
    ]


async def _evento_mortalidad(lot_id: int, empresa: int, user_id: int, fecha: str, machos: int, hembras: int) -> None:
    from app.operations.models import BirdMovement, EventStatus, EventType, OperationalEvent

    async with database.async_session() as session:
        evento = OperationalEvent(
            company_id=empresa, lot_id=lot_id, event_type=EventType.MORTALITY_RECORDING,
            event_date=date.fromisoformat(fecha), status=EventStatus.APPROVED,
            registered_by_id=user_id,
        )
        session.add(evento)
        await session.flush()
        session.add(BirdMovement(event_id=evento.id, sex="male", quantity=machos))
        session.add(BirdMovement(event_id=evento.id, sex="female", quantity=hembras))
        await session.commit()


async def _escenario(client, auth_headers, seeded_ids, etiqueta: str):
    """Batch aplicado (caso dorado) + eventos pre/post-corte; devuelve (batch_id, lote1)."""
    await _fase()
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=_filas(etiqueta))
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert r.status_code == 200, r.text
    items = (await client.get(f"/api/v1/cutover-batches/{batch_id}/items", headers=auth_headers)).json()["items"]
    por_ref = {it["legacy_lot_reference"]: it["lot_id"] for it in items}

    # PRE-corte (no debe contar) y POST-corte (35 = 20+15), ambos relativos al corte.
    await _evento_mortalidad(por_ref[f"CUT-G5-{etiqueta}-1"], seeded_ids["company_id"],
                             seeded_ids["user_admin_id"], iso_days_ago(45), 999, 0)
    await _evento_mortalidad(por_ref[f"CUT-G5-{etiqueta}-1"], seeded_ids["company_id"],
                             seeded_ids["user_admin_id"], iso_days_ago(7), 20, 15)
    return batch_id, por_ref[f"CUT-G5-{etiqueta}-1"]


@pytest.mark.asyncio
async def test_c5_golden_saldo_y_lifetime(auth_headers, client, seeded_ids):
    """El caso canónico: current = 9.965 · lifetime = 535 · NUNCA 10.000−500−35."""
    batch_id, lote1 = await _escenario(client, auth_headers, seeded_ids, "G1")
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    assert r.status_code == 200, r.text
    datos = r.json()

    fila = next(f for f in datos["lots"] if f["lot_id"] == lote1)
    assert fila["opening"]["live"] == 10000
    assert fila["opening"]["historical_mortality"] == 500
    assert fila["opening"]["mortality_status"] == "KNOWN"
    assert fila["post"]["mortality"] == 35           # solo el evento posterior al corte
    assert fila["current_live"] == 9965              # 10.000 − 35
    assert fila["current_live"] != 9465              # prohibido: resta doble del histórico
    assert fila["lifetime"]["mortality"] == 535      # histórico + post


@pytest.mark.asyncio
async def test_c5_post_solo_eventos_posteriores_al_corte(auth_headers, client, seeded_ids):
    """Un evento EN la fecha de corte no cuenta; uno posterior sí (fecha civil estricta)."""
    batch_id, lote1 = await _escenario(client, auth_headers, seeded_ids, "G2")
    # Evento exactamente el día del corte: NO es post-cutover.
    await _evento_mortalidad(lote1, seeded_ids["company_id"], seeded_ids["user_admin_id"], DIA_CORTE, 7, 3)

    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    fila = next(f for f in r.json()["lots"] if f["lot_id"] == lote1)
    assert fila["post"]["mortality"] == 35, "el evento del mismo día del corte no es post-cutover"
    assert fila["current_live"] == 9965


@pytest.mark.asyncio
async def test_c5_unknown_no_es_cero(auth_headers, client, seeded_ids):
    """Histórico desconocido ⇒ lifetime UNKNOWN (null), nunca fabricado; el post sigue visible."""
    batch_id, _ = await _escenario(client, auth_headers, seeded_ids, "G3")
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    datos = r.json()
    fila2 = next(f for f in datos["lots"] if f["legacy_lot_code"] == "CUT-G5-G3-2")

    assert fila2["opening"]["mortality_status"] == "UNKNOWN"
    assert fila2["lifetime"]["mortality"] is None, "UNKNOWN jamás un número fabricado"
    assert fila2["post"]["feed_kg"] is None and fila2["opening"]["feed_status"] == "UNKNOWN"
    assert fila2["current_live"] == 4000  # el saldo vivo no depende del histórico
    assert datos["unknown_metrics"] >= 2  # UNKNOWN visible y contado


@pytest.mark.asyncio
async def test_c5_reconciliacion_reproducible(auth_headers, client, seeded_ids):
    """Mismas entradas ⇒ mismo reporte; incluye source/checksum/cutover."""
    batch_id, _ = await _escenario(client, auth_headers, seeded_ids, "G4")
    r1 = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    r2 = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()

    datos = r1.json()
    assert datos["source"]["checksum"] and len(datos["source"]["checksum"]) == 64
    assert datos["source"]["filename"] == "corte.xlsx"
    assert datos["cutover_datetime"].startswith(DIA_CORTE)
    assert datos["items"] == 2 and datos["openings"] == 2
    assert datos["status"] == "applied"
