"""Tests for Operations module — events, business rules."""
import pytest


@pytest.mark.asyncio
async def test_list_operations(auth_headers, client):
    resp = await client.get("/api/v1/operations", headers=auth_headers, params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_event_types(auth_headers, client):
    resp = await client.get("/api/v1/operations/event-types", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 24  # 24 event types documented


@pytest.mark.asyncio
async def test_create_bird_reception(auth_headers, client):
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "bird_reception",
        "event_date": "2026-06-23",
        "bird_movements": [{"sex": "female", "quantity": 500, "avg_weight": 40.0}],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "bird_reception"
    assert data["status"] == "registered"


@pytest.mark.asyncio
async def test_create_feed_registration(auth_headers, client):
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": "2026-06-23",
        "feed_movements": [{"quantity_kg": 250.0}],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "feed_registration"


@pytest.mark.asyncio
async def test_mortality_exceeds_balance_blocked(auth_headers, client):
    """BR-01: Mortality cannot exceed available bird balance."""
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "mortality_recording",
        "event_date": "2026-06-23",
        "bird_movements": [{"sex": "female", "quantity": 99999, "avg_weight": 2000.0}],
    })
    assert resp.status_code == 400
    assert "saldo" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_operations_filter_by_lot(auth_headers, client):
    resp = await client.get("/api/v1/operations", headers=auth_headers, params={"lot_id": 2, "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    for event in data:
        assert event["lot_id"] == 2


@pytest.mark.asyncio
async def test_operations_filter_by_type(auth_headers, client):
    resp = await client.get("/api/v1/operations", headers=auth_headers, params={
        "event_type": "feed_registration", "limit": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    for event in data:
        assert event["event_type"] == "feed_registration"


# ──────────────────────────────────────────────────────────────────────────────
# Fase 0 tests — farm_inspection con datos numéricos por galpón
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_farm_inspection_numeric_values_per_house(auth_headers, client):
    """farm_inspection debe aceptar inspection_details con house_id y valores numéricos reales."""
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "farm_inspection",
        "event_date": "2026-06-23",
        "inspection_details": [
            {"house_id": 1, "parameter": "temperature", "value": "28.5"},
            {"house_id": 1, "parameter": "humidity",    "value": "65.0"},
            {"house_id": 1, "parameter": "litter_condition", "status": "seca"},
            {"house_id": 2, "parameter": "temperature", "value": "30.1"},
            {"house_id": 2, "parameter": "humidity",    "value": "70.0"},
            {"house_id": 2, "parameter": "litter_condition", "status": "húmeda"},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "farm_inspection"
    # All 6 inspection_details records stored
    assert len(data["inspection_details"]) == 6
    # Temperature values are stored as strings (InspectionDetail.value is String)
    temps = [d for d in data["inspection_details"] if d["parameter"] == "temperature"]
    assert len(temps) == 2
    assert temps[0]["value"] == "28.5"
    assert temps[1]["value"] == "30.1"
    # house_id is persisted
    house_ids = {d["house_id"] for d in data["inspection_details"]}
    assert house_ids == {1, 2}


@pytest.mark.asyncio
async def test_farm_inspection_without_house_id_still_accepted(auth_headers, client):
    """Backward compat: farm_inspection sin house_id (legacy) debe seguir funcionando."""
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "farm_inspection",
        "event_date": "2026-06-23",
        "inspection_details": [
            {"parameter": "temperature", "value": "27.0"},
            {"parameter": "humidity",    "value": "60.0"},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "farm_inspection"
    for detail in data["inspection_details"]:
        assert detail["house_id"] is None  # NULL = farm-level record


@pytest.mark.asyncio
async def test_farm_inspection_rejects_qualitative_only(auth_headers, client):
    """farm_inspection con solo status bueno/regular/malo sin value numérico aún es válido
    (no bloqueamos el legacy), pero el campo value debe quedar NULL."""
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "farm_inspection",
        "event_date": "2026-06-23",
        "inspection_details": [
            {"parameter": "litter_condition", "status": "good"},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    detail = data["inspection_details"][0]
    assert detail["status"] == "good"
    assert detail["value"] is None


@pytest.mark.asyncio
async def test_vaccination_stores_vaccine_id(auth_headers, client):
    """Formulario de vacunación: vaccine_id debe guardarse en el evento."""
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "vaccination",
        "event_date": "2026-06-23",
        "vaccine_id": 1,
        "vaccination_route": "water",
        "vaccine_lot_number": "LOT-2026-01",
        "dosage_per_bird": 0.5,
        "bird_movements": [
            {"sex": "male",   "quantity": 200},
            {"sex": "female", "quantity": 800},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["vaccine_id"] == 1
    assert data["vaccination_route"] == "water"
    assert data["vaccine_lot_number"] == "LOT-2026-01"


@pytest.mark.asyncio
async def test_medication_stores_medication_id(auth_headers, client):
    """Formulario de medicación: medication_id debe guardarse en el evento."""
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "medication",
        "event_date": "2026-06-23",
        "medication_id": 1,
        "dosage_per_bird": 2.0,
        "treatment_days": 5,
        "bird_movements": [
            {"sex": "male",   "quantity": 200},
            {"sex": "female", "quantity": 800},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["medication_id"] == 1
    assert data["treatment_days"] == 5



@pytest.mark.asyncio
async def test_list_operations(auth_headers, client):
    resp = await client.get("/api/v1/operations", headers=auth_headers, params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_event_types(auth_headers, client):
    resp = await client.get("/api/v1/operations/event-types", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 24  # 24 event types documented


@pytest.mark.asyncio
async def test_create_bird_reception(auth_headers, client):
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "bird_reception",
        "event_date": "2026-06-23",
        "bird_movements": [{"sex": "female", "quantity": 500, "avg_weight": 40.0}],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "bird_reception"
    assert data["status"] == "registered"


@pytest.mark.asyncio
async def test_create_feed_registration(auth_headers, client):
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": "2026-06-23",
        "feed_movements": [{"quantity_kg": 250.0}],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "feed_registration"


@pytest.mark.asyncio
async def test_mortality_exceeds_balance_blocked(auth_headers, client):
    """BR-01: Mortality cannot exceed available bird balance."""
    resp = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "mortality_recording",
        "event_date": "2026-06-23",
        "bird_movements": [{"sex": "female", "quantity": 99999, "avg_weight": 2000.0}],
    })
    assert resp.status_code == 400
    assert "saldo" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_operations_filter_by_lot(auth_headers, client):
    resp = await client.get("/api/v1/operations", headers=auth_headers, params={"lot_id": 2, "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    for event in data:
        assert event["lot_id"] == 2


@pytest.mark.asyncio
async def test_operations_filter_by_type(auth_headers, client):
    resp = await client.get("/api/v1/operations", headers=auth_headers, params={
        "event_type": "feed_registration", "limit": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    for event in data:
        assert event["event_type"] == "feed_registration"
