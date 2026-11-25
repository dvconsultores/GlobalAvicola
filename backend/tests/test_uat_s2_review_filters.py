"""UAT `GA-UAT-BREEDER-CRIA-S2` — los filtros del Centro de Revisión.

Guion de aceptación del capítulo S2: quien revisa tiene que poder acotar la cola por
**fecha del evento** y por el **código del lote tal como se teclea**. Dos hallazgos del
UAT quedan fijados aquí:

- `B2`: el rango de fechas de `GET /review/pending` viajaba como texto y se comparaba
  contra una columna `Date`, de modo que cualquier rango terminaba en `HTTP 500`.
- `B1`: ni la bandeja de revisión ni la de aprobaciones aceptaban el código de lote
  —solo su id interno—, mientras el Historial ya filtraba por código.

Trazabilidad: `spec 020 (AC-S2-R01, AC-S2-R02)`.

Las fechas se derivan de `tests/time_reference.py`: nunca literales, porque `BR-19`
rechaza eventos con más de 90 días de antigüedad y una fecha fija caducaría sola.
"""

from __future__ import annotations

import uuid

import pytest

from tests.owner_decisions_support import (
    fase_vigente_del_lote,
    tipo_de_alimento,
    tipo_de_correccion,
)
from tests.time_reference import iso_days_ago

# Prefijo de los lotes que este módulo crea: los hace irrepetibles y reconocibles.
PREFIJO = "S2REV-"


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _crear_lote(client, headers, seeded_ids) -> dict:
    """Lote nuevo en la cadena sembrada, con código irrepetible."""
    codigo = f"{PREFIJO}{uuid.uuid4().hex[:8].upper()}"
    r = await client.post("/api/v1/lots", headers=headers, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": codigo,
        "bird_type": "broiler",
        "sex": "mixed",
        # `BR-06` exige que el evento no preceda a la activación del lote.
        "start_date": iso_days_ago(30),
    })
    assert r.status_code == 201, r.text
    lote = r.json()
    assert lote["lot_code"] == codigo
    return lote


async def _crear_evento(client, headers, lote, event_date: str) -> dict:
    """Evento `feed_registration` sobre el lote, con la fecha pedida."""
    # `RR-33` / `RR-34`: el consumo nombra su tipo de alimento y el lote tiene fase vigente ese día.
    # La fase se abre al inicio del lote (no por evento) para que cubra cualquier fecha del caso.
    await fase_vigente_del_lote(client, headers, lote["id"], iso_days_ago(30))
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote["id"],
        "farm_id": lote["farm_id"],
        "house_id": lote["house_id"],
        "event_type": "feed_registration",
        "event_date": event_date,
        "feed_movements": [{"quantity_kg": 25.0,
                            "feed_type_id": await tipo_de_alimento(client, headers)}],
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _crear_pesaje(client, headers, lote, event_date: str) -> dict:
    """Pesaje sobre el lote: el evento corregible que alimenta la cola de aprobación."""
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote["id"], "event_type": "weight_recording", "event_date": event_date,
        "bird_movements": [{"sex": "male", "quantity": 10, "avg_weight": 2.0}],
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _corregir(client, headers, event_id: int) -> dict:
    """Corrige las observaciones: deja el evento en `corrected` (cola de aprobación)."""
    r = await client.post("/api/v1/corrections", headers=headers, json={
        "event_id": event_id,
        "field_name": "observations",
        "corrected_value": "Ajuste del UAT S2",
        "reason": "Error de digitación",
        # `RR-27` (`OD-S2-01`, ratificado por la Owner): toda corrección declara su tipo.
        "correction_type_id": await tipo_de_correccion(client, headers),
    })
    assert r.status_code == 201, r.text

    detalle = await client.get(f"/api/v1/operations/{event_id}", headers=headers)
    assert detalle.status_code == 200, detalle.text
    assert detalle.json()["status"] == "corrected", detalle.text
    return detalle.json()


async def _bandeja(client, headers, params: dict) -> dict:
    r = await client.get("/api/v1/review/pending", headers=headers, params=params)
    assert r.status_code == 200, r.text
    return r.json()


async def _aprobaciones(client, headers, params: dict) -> dict:
    r = await client.get("/api/v1/approvals/pending", headers=headers, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _ids(filas) -> set[int]:
    return {f["id"] for f in filas}


def _fragmento(codigo: str) -> str:
    """Trozo del código, en minúsculas: lo que teclea quien busca."""
    return codigo[len(PREFIJO):len(PREFIJO) + 6].lower()


# ── REV-S2-01 · el código del lote acota la bandeja ─────────────────────────

@pytest.mark.asyncio
async def test_rev_s2_01_bandeja_filtra_por_codigo_de_lote(client, auth_headers, seeded_ids):
    """`REV-S2-01` — `B1`: parcial e insensible a mayúsculas, sin comodines vivos.

    Quien revisa reconoce el lote por su código; exigirle el id interno lo obliga a
    llevar su propia tabla de traducción.
    """
    lote_a = await _crear_lote(client, auth_headers, seeded_ids)
    lote_b = await _crear_lote(client, auth_headers, seeded_ids)
    evento_a = await _crear_evento(client, auth_headers, lote_a, iso_days_ago(7))
    await _crear_evento(client, auth_headers, lote_b, iso_days_ago(7))

    trozo = _fragmento(lote_a["lot_code"])
    bandeja = await _bandeja(client, auth_headers, {"lot_code": trozo, "limit": 100})
    assert evento_a["id"] in _ids(bandeja["events"]), (
        f"el filtro parcial '{trozo}' debe encontrar el evento del lote "
        f"'{lote_a['lot_code']}'")
    assert all(e["lot_id"] == lote_a["id"] for e in bandeja["events"]), (
        "el filtro por código de lote no puede devolver eventos de otros lotes: "
        f"{sorted({e['lot_id'] for e in bandeja['events']})}")

    vacia = await _bandeja(client, auth_headers, {"lot_code": "ZZZ-NO-EXISTE", "limit": 100})
    assert vacia["events"] == []
    assert vacia["total"] == 0

    comodin = await _bandeja(client, auth_headers, {"lot_code": "%", "limit": 100})
    assert comodin["events"] == [], (
        "el '%' debe tratarse como carácter literal: ningún código de lote lo contiene, "
        f"pero el filtro devolvió {len(comodin['events'])} eventos")
    assert comodin["total"] == 0


# ── REV-S2-02 · el rango de fechas deja de ser texto ────────────────────────

@pytest.mark.asyncio
async def test_rev_s2_02_rango_de_fechas_filtra_y_es_inclusivo(client, auth_headers, seeded_ids):
    """`REV-S2-02` — `B2`: rango con ambos extremos, y cada extremo por separado.

    Comparar texto contra una columna `Date` no es un filtro estrecho: es un error.
    """
    lote = await _crear_lote(client, auth_headers, seeded_ids)
    evento_5 = await _crear_evento(client, auth_headers, lote, iso_days_ago(5))
    evento_7 = await _crear_evento(client, auth_headers, lote, iso_days_ago(7))
    evento_9 = await _crear_evento(client, auth_headers, lote, iso_days_ago(9))

    rango = await _bandeja(client, auth_headers, {
        "lot_id": lote["id"],
        "date_from": iso_days_ago(9), "date_to": iso_days_ago(7),
        "limit": 100,
    })
    assert _ids(rango["events"]) == {evento_9["id"], evento_7["id"]}, (
        "los dos extremos del rango son inclusivos y el evento posterior queda fuera")
    assert rango["total"] == 2

    solo_desde = await _bandeja(client, auth_headers, {
        "lot_id": lote["id"], "date_from": iso_days_ago(8), "limit": 100,
    })
    assert _ids(solo_desde["events"]) == {evento_7["id"], evento_5["id"]}
    assert solo_desde["total"] == 2

    solo_hasta = await _bandeja(client, auth_headers, {
        "lot_id": lote["id"], "date_to": iso_days_ago(7), "limit": 100,
    })
    assert _ids(solo_hasta["events"]) == {evento_9["id"], evento_7["id"]}
    assert solo_hasta["total"] == 2


# ── REV-S2-03 · un solo día ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rev_s2_03_un_solo_dia_devuelve_los_eventos_de_ese_dia(
    client, auth_headers, seeded_ids
):
    """`REV-S2-03` — `B2`: `date_from == date_to` es el caso más usado y no puede excluir nada."""
    lote = await _crear_lote(client, auth_headers, seeded_ids)
    evento_9 = await _crear_evento(client, auth_headers, lote, iso_days_ago(9))
    await _crear_evento(client, auth_headers, lote, iso_days_ago(7))

    un_dia = await _bandeja(client, auth_headers, {
        "lot_id": lote["id"],
        "date_from": iso_days_ago(9), "date_to": iso_days_ago(9),
        "limit": 100,
    })
    assert _ids(un_dia["events"]) == {evento_9["id"]}, (
        "un rango de un día debe devolver los eventos de ese día y solo esos")
    assert un_dia["total"] == 1


# ── REV-S2-04 · rango imposible y valor que no es fecha ─────────────────────

@pytest.mark.asyncio
async def test_rev_s2_04_rango_invertido_es_400_y_valor_no_fecha_es_422(
    client, auth_headers, seeded_ids
):
    """`REV-S2-04` — `B2`: la petición inválida se explica; no se convierte en 500."""
    lote = await _crear_lote(client, auth_headers, seeded_ids)

    invertido = await client.get("/api/v1/review/pending", headers=auth_headers, params={
        "lot_id": lote["id"],
        "date_from": iso_days_ago(5), "date_to": iso_days_ago(9),
    })
    assert invertido.status_code == 400, invertido.text
    assert invertido.json()["detail"] == (
        "La fecha inicial no puede ser posterior a la fecha final"), invertido.text

    no_fecha = await client.get("/api/v1/review/pending", headers=auth_headers, params={
        "date_from": "ayer",
    })
    assert no_fecha.status_code == 422, (
        f"un valor que no es fecha es una petición inválida: {no_fecha.text}")


# ── REV-S2-05 · el código del lote también acota las aprobaciones ───────────

@pytest.mark.asyncio
async def test_rev_s2_05_aprobaciones_filtran_por_codigo_de_lote(
    client, auth_headers, seeded_ids
):
    """`REV-S2-05` — `B1`: el mismo contrato en la cola de aprobación.

    Aprobar es la decisión que cierra el ciclo: quien aprueba necesita la misma
    búsqueda por código que quien revisa.
    """
    lote_a = await _crear_lote(client, auth_headers, seeded_ids)
    lote_b = await _crear_lote(client, auth_headers, seeded_ids)
    pesaje_a = await _crear_pesaje(client, auth_headers, lote_a, iso_days_ago(7))
    pesaje_b = await _crear_pesaje(client, auth_headers, lote_b, iso_days_ago(7))
    await _corregir(client, auth_headers, pesaje_a["id"])
    await _corregir(client, auth_headers, pesaje_b["id"])

    trozo = _fragmento(lote_a["lot_code"])
    cola = await _aprobaciones(client, auth_headers, {"lot_code": trozo, "limit": 100})
    assert pesaje_a["id"] in _ids(cola["events"]), (
        f"el filtro parcial '{trozo}' debe encontrar el evento corregido del lote "
        f"'{lote_a['lot_code']}'")
    assert all(e["lot_id"] == lote_a["id"] for e in cola["events"]), (
        "el filtro por código de lote no puede devolver eventos de otros lotes: "
        f"{sorted({e['lot_id'] for e in cola['events']})}")

    vacia = await _aprobaciones(client, auth_headers, {
        "lot_code": "ZZZ-NO-EXISTE", "limit": 100})
    assert vacia["events"] == []
    assert vacia["total"] == 0
