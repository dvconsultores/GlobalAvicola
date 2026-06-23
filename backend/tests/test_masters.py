"""Tests for Masters module — CRUD on companies, farms, houses."""
import pytest


@pytest.mark.asyncio
async def test_list_companies(auth_headers, client):
    resp = await client.get("/api/v1/masters/companies", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_and_list_company(auth_headers, client):
    # Create
    resp = await client.post("/api/v1/masters/companies", headers=auth_headers, json={
        "name": "Test Company",
        "tax_id": "T-12345678-9",
        "country": "TestLand",
    })
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "Test Company"

    # List and verify
    resp2 = await client.get("/api/v1/masters/companies", headers=auth_headers)
    companies = resp2.json()
    assert any(c["name"] == "Test Company" for c in companies)


@pytest.mark.asyncio
async def test_list_farms(auth_headers, client):
    resp = await client.get("/api/v1/masters/farms", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_houses(auth_headers, client):
    resp = await client.get("/api/v1/masters/houses", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_suppliers(auth_headers, client):
    resp = await client.get("/api/v1/masters/suppliers", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_lots(auth_headers, client):
    resp = await client.get("/api/v1/lots", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_breeds(auth_headers, client):
    resp = await client.get("/api/v1/masters/breeds", headers=auth_headers)
    assert resp.status_code == 200
