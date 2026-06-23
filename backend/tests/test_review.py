"""Tests for Review & Approval workflow."""
import pytest


@pytest.mark.asyncio
async def test_list_pending_review(auth_headers, client):
    resp = await client.get("/api/v1/review/pending", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_pending_approvals(auth_headers, client):
    resp = await client.get("/api/v1/approvals/pending", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_approval_steps(auth_headers, client):
    resp = await client.get("/api/v1/approval-steps", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_seed_default_approval_steps(auth_headers, client):
    resp = await client.post("/api/v1/approval-steps/seed-defaults", headers=auth_headers,
                             params={"approval_levels": 2})
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "Revisión"
    assert data[1]["name"] == "Aprobación"


@pytest.mark.asyncio
async def test_create_review_batch(auth_headers, client):
    # First get a pending event
    pending_resp = await client.get("/api/v1/review/pending", headers=auth_headers)
    pending = pending_resp.json()
    if pending["total"] == 0:
        pytest.skip("No pending events to review")

    event_id = pending["events"][0]["id"]
    resp = await client.post("/api/v1/review/batches", headers=auth_headers, json={
        "batch_name": "Test Batch",
        "event_ids": [event_id],
        "notes": "Test review batch",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["batch_name"] == "Test Batch"
    assert data["total_events"] == 1


@pytest.mark.asyncio
async def test_list_review_batches(auth_headers, client):
    resp = await client.get("/api/v1/review/batches", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "batches" in data


@pytest.mark.asyncio
async def test_list_corrections(auth_headers, client):
    resp = await client.get("/api/v1/corrections", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "corrections" in data
