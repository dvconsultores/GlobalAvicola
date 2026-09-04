"""Gate sistémico de aislamiento multiempresa — Wave 3, obligatorio antes de certificar procesos.

```
LIST FILTERING  ≠  TENANT DATA INTEGRITY
READ ISOLATION  ≠  WRITE ISOLATION
```

`R-42` lo demostró: los filtros de listado protegían la lectura mientras la escritura
aceptaba una clave foránea de otra empresa. El evento quedaba archivado bajo la empresa A
pero ligado a un lote de B, y el saldo de aves —que se calcula por `lot_id`— quedaba
contaminado.

Principio que esta suite verifica:

> **Un inquilino no puede mutar a otro, ni directa ni indirectamente.**

Para toda clave foránea tenant-scoped que el cliente pueda enviar no basta con que el
recurso exista: debe **pertenecer** a la empresa efectiva.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from app.auth.security import create_access_token
from tests.time_reference import iso_days_ago

pytestmark = pytest.mark.asyncio


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


async def _como_empresa_b(client, seeded_ids) -> dict:
    """Cabecera del Super Admin situado en la empresa B."""
    cambio = await client.post("/api/v1/switch-company",
                               headers=_token(seeded_ids["user_admin_id"]),
                               json={"company_id": seeded_ids["company_id_2"]})
    assert cambio.status_code == 200, cambio.text
    return {"Authorization": f"Bearer {cambio.json()['access_token']}"}


@pytest_asyncio.fixture
async def recursos_b(http_client, seeded_ids) -> dict:
    """Recursos reales de la empresa B, para intentar alcanzarlos desde la A."""
    cabecera = await _como_empresa_b(http_client, seeded_ids)
    s = uuid.uuid4().hex[:8]

    granja = await http_client.post("/api/v1/masters/farms", headers=cabecera, json={
        "name": f"B {s}", "code": f"MT-FARM-{s}", "company_id": seeded_ids["company_id_2"]})
    assert granja.status_code == 201, granja.text

    galpon = await http_client.post("/api/v1/masters/houses", headers=cabecera, json={
        "name": f"B galpon {s}", "farm_id": granja.json()["id"], "capacity": 5000})
    lote = await http_client.post("/api/v1/lots", headers=cabecera, json={
        "lot_code": f"MT-LOT-{s}", "farm_id": granja.json()["id"],
        "bird_type": "broiler", "sex": "mixed"})
    assert lote.status_code in (200, 201), lote.text

    evento = await http_client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": lote.json()["id"], "event_type": "feed_registration",
        "event_date": iso_days_ago(0), "feed_movements": [{"quantity_kg": 5.0}]})
    assert evento.status_code == 201, evento.text

    return {
        "farm_id": granja.json()["id"],
        "house_id": galpon.json()["id"] if galpon.status_code == 201 else None,
        "lot_id": lote.json()["id"],
        "event_id": evento.json()["id"],
        "company_id": seeded_ids["company_id_2"],
    }


# ── §25 · inyección de clave foránea ajena en una escritura ──────────────────

@pytest.mark.parametrize("campo", ["lot_id", "farm_id", "house_id"])
async def test_no_se_puede_referenciar_una_clave_ajena_al_crear_una_operacion(
    http_client, seeded_ids, recursos_b, campo
):
    """La empresa A intenta registrar una operación apuntando a un recurso de la B.

    `lot_id` es el caso que `R-42` describía. `farm_id` y `house_id` completan la terna de
    ubicación: apuntar a la granja de otra empresa asocia el registro a un lugar ajeno.
    """
    if recursos_b[campo] is None:
        pytest.skip(f"no se pudo preparar {campo}")

    cuerpo = {
        "lot_id": seeded_ids["lot_id"],
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "event_type": "bird_reception",
        "event_date": iso_days_ago(0),
        "bird_movements": [{"sex": "mixed", "quantity": 10}],
    }
    cuerpo[campo] = recursos_b[campo]

    r = await http_client.post("/api/v1/operations",
                               headers=_token(seeded_ids["user_operator_id"]), json=cuerpo)
    assert r.status_code >= 400, (
        f"'{campo}' de otra empresa fue aceptado ({r.status_code}): "
        "existir no basta, el recurso debe pertenecer al inquilino efectivo")


async def test_no_se_puede_corregir_un_evento_ajeno(http_client, seeded_ids, recursos_b):
    """`event_id` de otra empresa en una corrección."""
    r = await http_client.post("/api/v1/corrections",
                               headers=_token(seeded_ids["user_approver_id"]), json={
                                   "event_id": recursos_b["event_id"],
                                   "field_name": "observations",
                                   "corrected_value": "intruso",
                                   "reason": "prueba de aislamiento entre empresas"})
    assert r.status_code >= 400, (
        f"Se corrigió un evento de otra empresa: {r.status_code}")


async def test_no_se_puede_revisar_un_evento_ajeno(http_client, seeded_ids, recursos_b):
    r = await http_client.post(f"/api/v1/review/start/{recursos_b['event_id']}",
                               headers=_token(seeded_ids["user_approver_id"]))
    assert r.status_code >= 400, f"Se inició la revisión de un evento ajeno: {r.status_code}"


async def test_no_se_puede_aprobar_un_evento_ajeno(http_client, seeded_ids, recursos_b):
    r = await http_client.post("/api/v1/approvals/approve",
                               headers=_token(seeded_ids["user_approver_id"]),
                               json={"event_id": recursos_b["event_id"]})
    assert r.status_code >= 400, f"Se aprobó un evento de otra empresa: {r.status_code}"


async def test_no_se_puede_crear_un_galpon_en_una_granja_ajena(
    http_client, seeded_ids, recursos_b
):
    """`farm_id` ajeno al crear un maestro hijo."""
    r = await http_client.post("/api/v1/masters/houses",
                               headers=_token(seeded_ids["user_admin_id"]), json={
                                   "name": f"intruso {uuid.uuid4().hex[:6]}",
                                   "farm_id": recursos_b["farm_id"], "capacity": 100})
    # `R-59`: crear bajo una granja ajena asociaría un galpón de la empresa B a la
    # estructura de la A. Misma clase que `R-42`, en el árbol de maestros.
    assert r.status_code >= 400, (
        f"Se creó un galpón bajo la granja de otra empresa: {r.status_code}")


# ── §26 · contaminación de datos derivados ───────────────────────────────────

async def test_el_saldo_de_un_lote_ajeno_no_se_contamina(
    http_client, seeded_ids, recursos_b
):
    """El daño real de `R-42`: no la fuga, sino el balance corrompido.

    Se mide el saldo del lote de la empresa B antes y después de que la A intente
    escribir contra él. Debe quedar intacto.
    """
    cabecera_b = await _como_empresa_b(http_client, seeded_ids)

    async def saldo() -> int:
        r = await http_client.get(
            f"/api/v1/operations?lot_id={recursos_b['lot_id']}&limit=100", headers=cabecera_b)
        assert r.status_code == 200, r.text
        entradas, salidas = {"bird_reception", "birth_registration"}, {
            "mortality_recording", "cull_recording", "bird_exit", "chick_dispatch"}
        total = 0
        for evento in r.json():
            if evento["status"] == "cancelled":
                continue
            detalle = await http_client.get(f"/api/v1/operations/{evento['id']}",
                                            headers=cabecera_b)
            cantidad = sum(bm["quantity"] for bm in detalle.json().get("bird_movements", []))
            if evento["event_type"] in entradas:
                total += cantidad
            elif evento["event_type"] in salidas:
                total -= cantidad
        return total

    antes = await saldo()

    intruso = await http_client.post("/api/v1/operations",
                                     headers=_token(seeded_ids["user_operator_id"]), json={
                                         "lot_id": recursos_b["lot_id"],
                                         "event_type": "bird_reception",
                                         "farm_id": seeded_ids["farm_id"],
                                         "house_id": seeded_ids["house_id"],
                                         "event_date": iso_days_ago(0),
                                         "bird_movements": [{"sex": "mixed", "quantity": 9999}]})
    assert intruso.status_code >= 400, "La escritura entre inquilinos debe rechazarse"
    assert await saldo() == antes, (
        "El saldo del lote de la otra empresa cambió: contaminación entre inquilinos")


# ── §25 · sin efectos colaterales ────────────────────────────────────────────

async def test_un_intento_rechazado_no_deja_rastro(http_client, seeded_ids, recursos_b):
    """No basta con el código HTTP: no debe crearse fila, ni auditoría, ni estado."""
    from sqlalchemy import text

    import app.database as database

    async with database.engine.connect() as c:
        eventos_antes = (await c.execute(text("SELECT count(*) FROM operational_events"))).scalar()
        auditoria_antes = (await c.execute(text("SELECT count(*) FROM audit_logs"))).scalar()

    r = await http_client.post("/api/v1/operations",
                               headers=_token(seeded_ids["user_operator_id"]), json={
                                   "lot_id": recursos_b["lot_id"],
                                   "event_type": "feed_registration",
                                   "event_date": iso_days_ago(0),
                                   "feed_movements": [{"quantity_kg": 1.0}]})
    assert r.status_code >= 400

    async with database.engine.connect() as c:
        eventos_despues = (await c.execute(text("SELECT count(*) FROM operational_events"))).scalar()
        auditoria_despues = (await c.execute(text("SELECT count(*) FROM audit_logs"))).scalar()

    assert eventos_despues == eventos_antes, "Se creó una fila pese al rechazo"
    assert auditoria_despues == auditoria_antes, "Se registró auditoría de una operación rechazada"


# ── Lectura: el otro lado del aislamiento ────────────────────────────────────

@pytest.mark.parametrize("recurso,plantilla", [
    ("lot_id", "/api/v1/lots/{}"),
    ("event_id", "/api/v1/operations/{}"),
    ("farm_id", "/api/v1/masters/farms/{}"),
])
async def test_no_se_puede_leer_un_recurso_ajeno(
    http_client, seeded_ids, recursos_b, recurso, plantilla
):
    r = await http_client.get(plantilla.format(recursos_b[recurso]),
                              headers=_token(seeded_ids["user_operator_id"]))
    assert r.status_code in (403, 404), f"{plantilla}: {r.status_code}"
