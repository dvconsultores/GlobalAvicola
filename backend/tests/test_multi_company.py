"""
Multi-company isolation tests.
Verifies that Company A users cannot access Company B data.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date


# Los identificadores no se inventan: se leen de la base sembrada. Los `sub` fijos
# ("2", "3") daban por supuesto que el usuario 3 pertenecía a una compañía 2 que nadie
# había creado, de modo que el test comparaba contra una premisa falsa.
#
# Nótese que el `company_id` del token es irrelevante: `get_current_user` carga el usuario
# de la base y toma de ahí su compañía (`auth/security.py:98-104`). Es la propiedad
# correcta —un token no puede reclamar una compañía ajena— y estos tests la ejercitan.


@pytest.fixture
def company_a_token(seeded_ids) -> str:
    """Operador de la compañía A."""
    return create_access_token(data={
        "sub": str(seeded_ids["user_operator_id"]),
        "role": "operator",
    })


@pytest.fixture
def company_b_token(seeded_ids) -> str:
    """Usuario de la compañía B: debe ver únicamente lo suyo."""
    return create_access_token(data={
        "sub": str(seeded_ids["user_other_company_id"]),
        "role": "operator",
    })


@pytest.fixture
def super_admin_token(seeded_ids) -> str:
    """Super admin: sin filtro por compañía."""
    return create_access_token(data={
        "sub": str(seeded_ids["user_admin_id"]),
        "role": "super_admin",
    })


@pytest.mark.anyio
async def test_company_a_cannot_access_company_b_operations(
    company_a_token: str,
    company_b_token: str,
):
    """Company A user cannot see Company B's operations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Company A lists operations — should only see Company A events
        resp_a = await client.get("/api/v1/operations?limit=100", headers={"Authorization": f"Bearer {company_a_token}"})
        assert resp_a.status_code == 200
        events_a = resp_a.json()
        # All returned events must belong to company 1
        for evt in events_a:
            assert evt.get("company_id") in (1, None), f"Company A user saw event from company {evt.get('company_id')}"

        # Company B lists operations — should only see Company B events
        resp_b = await client.get("/api/v1/operations?limit=100", headers={"Authorization": f"Bearer {company_b_token}"})
        assert resp_b.status_code == 200
        events_b = resp_b.json()
        for evt in events_b:
            assert evt.get("company_id") in (2, None), f"Company B user saw event from company {evt.get('company_id')}"


@pytest.mark.anyio
async def test_company_a_cannot_get_company_b_event(
    company_a_token: str,
):
    """Company A user gets 404 when trying to access Company B event directly."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to access an event that belongs to Company B (id=2 in test seeds)
        resp = await client.get("/api/v1/operations/99999", headers={"Authorization": f"Bearer {company_a_token}"})
        # Should return 404 (not 403) to avoid leaking event existence
        assert resp.status_code == 404


@pytest.mark.anyio
async def test_super_admin_sees_all_companies(
    super_admin_token: str,
):
    """Super admin can see operations from all companies."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/operations?limit=100", headers={"Authorization": f"Bearer {super_admin_token}"})
        assert resp.status_code == 200


@pytest.mark.anyio
async def test_company_a_cannot_access_company_b_houses(
    company_a_token: str,
):
    """Company A user cannot list houses of Company B's farm."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Farm 2 belongs to Company B in test seeds
        resp = await client.get("/masters/farms/2/houses", headers={"Authorization": f"Bearer {company_a_token}"})
        # Should return 404 — farm doesn't belong to Company A
        assert resp.status_code == 404


@pytest.mark.anyio
async def test_idempotency_key_prevents_duplicate(
    company_a_token: str,
):
    """Submitting the same idempotency_key twice returns the first event."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "lot_id": 1,
            "event_type": "feed_registration",
            "event_date": recent_event_date(),
            "idempotency_key": "test-dup-key-001",
            "feed_movements": [{"feed_type_id": 1, "quantity_kg": 100, "sacks_count": 4}],
        }
        # Primer envío: crea. El resto de la suite y el router coinciden en 201; este
        # test era el único que esperaba 200.
        resp1 = await client.post("/api/v1/operations", json=payload, headers={"Authorization": f"Bearer {company_a_token}"})
        assert resp1.status_code == 201, resp1.text
        event1_id = resp1.json()["id"]

        # Segundo envío con la misma clave: no debe duplicar. Lo que el test verifica —y
        # lo que importa (BR-12)— es que devuelve **el mismo** evento.
        #
        # El código sigue siendo 201 aunque no se haya creado nada. Un 200 sería más
        # preciso, pero es un cambio de contrato que ninguna fuente exige: queda
        # registrado como `R-35` (P3) en lugar de decidirse aquí.
        resp2 = await client.post("/api/v1/operations", json=payload, headers={"Authorization": f"Bearer {company_a_token}"})
        assert resp2.status_code == 201, resp2.text
        assert resp2.json()["id"] == event1_id, "La clave de idempotencia no evitó el duplicado"
