"""Tests for SAP Integration module."""
import pytest

from app.config import settings

# Skip all SAP tests when SAP feature is disabled (development mode)
pytestmark = pytest.mark.skipif(
    not settings.FEATURE_SAP_ENABLED,
    reason="SAP integration disabled (FEATURE_SAP_ENABLED=false in .env). "
           "Set FEATURE_SAP_ENABLED=true to run these tests."
)


@pytest.mark.asyncio
async def test_import_sap_references(auth_headers, client):
    resp = await client.post("/api/v1/sap/references/import", headers=auth_headers, json={
        "references": [
            {"ref_type": "purchase_order", "sap_code": "PO-TEST-001", "description": "Test PO"},
            {"ref_type": "material", "sap_code": "MAT-TEST-001", "description": "Test Material"},
        ]
    })
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_sap_references(auth_headers, client):
    resp = await client.get("/api/v1/sap/references", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "references" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_consolidate_approved(auth_headers, client):
    resp = await client.post("/api/v1/sap/consolidate", headers=auth_headers, json={})
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_consolidated(auth_headers, client):
    resp = await client.get("/api/v1/sap/consolidated", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "consolidated" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_export_to_sap(auth_headers, client):
    resp = await client.post("/api/v1/sap/export", headers=auth_headers, json={})
    # May return 200 or 400 if nothing to export
    assert resp.status_code in (200, 400)


@pytest.mark.asyncio
async def test_list_sync_jobs(auth_headers, client):
    resp = await client.get("/api/v1/sap/sync/jobs", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "jobs" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_payloads(auth_headers, client):
    resp = await client.get("/api/v1/sap/payloads", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "payloads" in data


@pytest.mark.asyncio
async def test_sap_connection_check(auth_headers, client):
    """El adaptador manual no está conectado a SAP, y debe decirlo.

    El test esperaba `connected == True` cuando `check_connection()` devolvía un
    optimismo sin respaldo. `GA-REM-010` lo hizo honesto: `ManualSapAdapter` genera un
    artefacto para envío manual y **no entrega nada a SAP**, de modo que declararse
    conectado sería exactamente el falso positivo que esa remediación eliminó.
    """
    resp = await client.get("/api/v1/sap/connection-check", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is False, (
        "El adaptador manual no entrega a SAP: no puede declararse conectado (GA-REM-010)")
    assert "ManualSapAdapter" in data["adapter"]


@pytest.mark.asyncio
async def test_list_sap_errors(auth_headers, client):
    resp = await client.get("/api/v1/sap/errors", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
