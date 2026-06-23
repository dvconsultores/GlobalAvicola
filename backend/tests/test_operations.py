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
