"""QA Yolinel — los listados traen nombres, no solo ids.

Cubre el enriquecimiento aditivo de `app/operations/enrichment.py`:

- `/lots` anota `farm_name` y `house_name` sobre cada lote.
- `/operations` anota `lot_code`, `farm_name` y `registered_by_name` sobre cada evento.
- `/review/pending` anota los mismos tres campos por la misma vía.

Los nombres no se persisten: viajan solo en la respuesta. Por eso cada comprobación
contrasta contra el maestro (`/masters/farms/{id}`) y contra el código del lote que
el propio test acaba de crear.
"""
import uuid

import pytest

from tests.time_reference import iso_days_ago, recent_event_date

PREFIJO = "ENR-"


async def _crear_lote(client, cabecera, seeded_ids) -> dict:
    """Lote nuevo con código irrepetible, en la cadena sembrada."""
    codigo = f"{PREFIJO}{uuid.uuid4().hex[:8].upper()}"
    resp = await client.post("/api/v1/lots", headers=cabecera, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": codigo,
        "bird_type": "broiler",
        "sex": "mixed",
        # `BR-06` exige que el evento no preceda a la activación del lote; sin esta
        # fecha el lote nace hoy y el evento de `recent_event_date()` queda antes.
        "start_date": iso_days_ago(30),
    })
    assert resp.status_code == 201, resp.text
    lote = resp.json()
    assert lote["lot_code"] == codigo
    return lote


async def _crear_evento(client, cabecera, lote) -> dict:
    """Evento `feed_registration` sobre el lote, con la cadena del propio lote."""
    resp = await client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": lote["id"],
        "farm_id": lote["farm_id"],
        "house_id": lote["house_id"],
        "event_type": "feed_registration",
        "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 120.0}],
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_lot_list_trae_nombre_de_granja(client, auth_headers, seeded_ids):
    """`GET /lots` devuelve `farm_name` y `house_name` del lote creado."""
    lote = await _crear_lote(client, auth_headers, seeded_ids)

    granja = await client.get(
        f"/api/v1/masters/farms/{lote['farm_id']}", headers=auth_headers
    )
    assert granja.status_code == 200, granja.text
    nombre_granja = granja.json()["name"]

    resp = await client.get(
        "/api/v1/lots", headers=auth_headers, params={"limit": 100}
    )
    assert resp.status_code == 200, resp.text
    listado = resp.json()
    assert isinstance(listado, list)

    filas = [f for f in listado if f["id"] == lote["id"]]
    if not filas:
        # El lote recién creado puede quedar fuera de la primera página.
        busqueda = await client.get(
            "/api/v1/lots",
            headers=auth_headers,
            params={"search": lote["lot_code"], "limit": 100},
        )
        assert busqueda.status_code == 200, busqueda.text
        filas = [f for f in busqueda.json() if f["id"] == lote["id"]]
    assert filas, f"el lote {lote['id']} no aparece en /lots"
    fila = filas[0]

    assert fila["farm_name"] == nombre_granja
    assert fila.get("house_name"), "house_name vacío en /lots"
    assert fila["farm_id"] == lote["farm_id"]


@pytest.mark.asyncio
async def test_operations_list_trae_codigo_y_nombres(client, auth_headers, seeded_ids):
    """`GET /operations` devuelve `lot_code`, `farm_name` y `registered_by_name`."""
    lote = await _crear_lote(client, auth_headers, seeded_ids)
    evento = await _crear_evento(client, auth_headers, lote)

    resp = await client.get(
        "/api/v1/operations",
        headers=auth_headers,
        params={"lot_id": lote["id"], "limit": 50},
    )
    assert resp.status_code == 200, resp.text
    listado = resp.json()
    assert isinstance(listado, list)

    filas = [e for e in listado if e["id"] == evento["id"]]
    assert filas, f"el evento {evento['id']} no aparece en /operations"
    fila = filas[0]

    assert fila["lot_code"] == lote["lot_code"]
    assert fila["farm_name"], "farm_name vacío en /operations"
    assert fila["registered_by_name"], "registered_by_name vacío en /operations"
    assert fila["created_at"], "created_at vacío en /operations"
    assert fila["event_date"]


@pytest.mark.asyncio
async def test_bandeja_de_revision_trae_los_mismos_nombres(
    client, auth_headers, seeded_ids
):
    """Tras `submit`, la bandeja de revisión trae los mismos tres nombres."""
    lote = await _crear_lote(client, auth_headers, seeded_ids)
    evento = await _crear_evento(client, auth_headers, lote)

    envio = await client.post(
        f"/api/v1/operations/{evento['id']}/submit", headers=auth_headers
    )
    assert envio.status_code == 200, envio.text
    assert envio.json()["status"] == "pending_review"

    resp = await client.get(
        "/api/v1/review/pending",
        headers=auth_headers,
        params={"lot_id": lote["id"], "status": "pending_review", "limit": 100},
    )
    assert resp.status_code == 200, resp.text
    bandeja = resp.json()
    assert "events" in bandeja and "total" in bandeja

    filas = [e for e in bandeja["events"] if e["id"] == evento["id"]]
    assert filas, f"el evento {evento['id']} no aparece en /review/pending"
    fila = filas[0]

    assert fila["lot_code"] == lote["lot_code"]
    assert fila["farm_name"], "farm_name vacío en /review/pending"
    assert fila["registered_by_name"], "registered_by_name vacío en /review/pending"
