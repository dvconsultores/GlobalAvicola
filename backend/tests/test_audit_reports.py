"""Tests for Audit & Reports modules."""
import pytest


@pytest.mark.asyncio
async def test_list_audit_logs(auth_headers, client):
    resp = await client.get("/api/v1/audit", headers=auth_headers, params={"limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_dashboard_mobile(auth_headers, client):
    resp = await client.get("/api/v1/dashboard/mobile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "today_events" in data
    assert "pending_corrections" in data
    assert "quick_actions" in data


@pytest.mark.asyncio
async def test_get_dashboard_admin(auth_headers, client):
    resp = await client.get("/api/v1/dashboard/admin", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "pending_review" in data
    assert "by_status" in data


@pytest.mark.asyncio
async def test_get_reports_kpis(auth_headers, client):
    resp = await client.get("/api/v1/reports/kpis", headers=auth_headers, params={"lot_id": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert "mortality" in data
    assert "feed_conversion" in data


@pytest.mark.asyncio
async def test_get_lot_report(auth_headers, client):
    resp = await client.get("/api/v1/reports/lot/2", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "lot" in data
    assert "event_summary" in data


@pytest.mark.asyncio
async def test_get_sap_comparison(auth_headers, client):
    resp = await client.get("/api/v1/reports/sap-comparison", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_with_sap_ref" in data
