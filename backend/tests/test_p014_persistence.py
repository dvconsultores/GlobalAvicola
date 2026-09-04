"""`P0-14`, `R-32`, `R-34` — persistencia completa del contrato de operaciones.

La API aceptaba 22 campos, guardaba 11 y devolvía `null` en los otros 14 con un `201`.
Aquí se verifica el viaje completo de cada campo —petición → base → lectura por API— y se
protege la propiedad estructural que impide que el defecto vuelva: el conjunto que se
persiste se deriva del contrato, no de una lista escrita a mano.
"""

from __future__ import annotations

import pytest

from app.operations.schemas import (
    IMMUTABLE_AFTER_CREATE,
    SUBMOVEMENT_FIELDS,
    OperationalEventBase,
    OperationalEventUpdate,
)
from tests.time_reference import recent_event_date

# Un valor distinguible por campo: si algo se pierde, se ve cuál.
CAMPOS_OPERATIVOS = {
    "supplier_id": 1,
    "cause_id": 1,
    "cull_cause_id": 1,
    "vaccine_id": 1,
    "vaccination_route": "water",
    "vaccine_lot_number": "LOT-P014-001",
    "medication_id": 1,
    "dosage_per_bird": 0.75,
    "treatment_days": 5,
    "destination_farm_id": 2,
    "destination_plant_id": 1,
    "transport_id": 1,
    "sample_size": 30,
    "extra_data": {"origen": "test_p014", "anidado": {"n": 1}},
}


def _payload(**extra) -> dict:
    base = {
        "lot_id": 2,
        "event_type": "vaccination",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 10}],
    }
    base.update(extra)
    return base


# ── AC03 · la propiedad estructural ───────────────────────────────────────────

def test_ac03_el_contrato_de_creacion_no_puede_quedarse_corto():
    """Todo campo del contrato de entrada debe tener columna en el modelo.

    Es la guarda que faltaba: cuando la migración `c1d2e3f4a5b6` añadió columnas y el
    esquema las expuso, nadie tocó el servicio y **nada falló**. Si mañana se declara un
    campo sin columna, este test lo dice.
    """
    from app.operations.models import OperationalEvent

    columnas = {c.name for c in OperationalEvent.__table__.columns}
    declarados = set(OperationalEventBase.model_fields) - set(SUBMOVEMENT_FIELDS)
    huerfanos = sorted(declarados - columnas)
    assert not huerfanos, f"Campos del contrato sin columna: {huerfanos}"


def test_ac03_la_creacion_asigna_todo_lo_que_declara_el_contrato():
    """El servicio no puede volver a enumerar a mano un subconjunto.

    Se comprueba sobre el código: `create_event` construye el modelo desdoblando el
    `model_dump` del contrato. Si alguien vuelve a escribir la lista campo a campo, el
    conjunto dejará de derivarse y este test lo detecta.
    """
    import inspect

    from app.operations.service import OperationsService

    fuente = inspect.getsource(OperationsService.create_event)
    assert "**event_fields" in fuente, (
        "La creación debe derivar sus campos del contrato, no enumerarlos a mano (P0-14)")
    assert "data.model_dump(exclude=" in fuente


def test_ac09_update_cubre_el_contrato_operativo():
    """La edición admite lo mismo que la creación, salvo lo deliberadamente inmutable."""
    creables = set(OperationalEventBase.model_fields) - set(SUBMOVEMENT_FIELDS)
    editables = set(OperationalEventUpdate.model_fields)
    faltan = sorted(creables - editables - set(IMMUTABLE_AFTER_CREATE))
    assert not faltan, f"Campos creables que no se pueden corregir antes de revisar: {faltan}"
    assert not (editables - creables), "La edición no puede admitir campos que la creación no declara"


def test_ac10_status_no_es_editable_por_contrato():
    """`status` fuera del esquema de edición: el estado solo cambia por el flujo (R-32)."""
    assert "status" not in OperationalEventUpdate.model_fields
    assert "event_type" not in OperationalEventUpdate.model_fields
    assert "idempotency_key" not in OperationalEventUpdate.model_fields


# ── AC01 / AC02 · ida y vuelta de cada campo ──────────────────────────────────

@pytest.mark.asyncio
async def test_ac01_la_creacion_persiste_todos_los_campos(auth_headers, client):
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_payload(**CAMPOS_OPERATIVOS))
    assert r.status_code == 201, r.text
    creado = r.json()

    perdidos = {k: v for k, v in CAMPOS_OPERATIVOS.items() if creado.get(k) != v}
    assert not perdidos, f"Campos no persistidos en la respuesta de creación: {perdidos}"

    leido = await client.get(f"/api/v1/operations/{creado['id']}", headers=auth_headers)
    assert leido.status_code == 200
    perdidos_lectura = {k: v for k, v in CAMPOS_OPERATIVOS.items() if leido.json().get(k) != v}
    assert not perdidos_lectura, f"Campos ausentes al releer: {perdidos_lectura}"


@pytest.mark.parametrize("campo,valor", sorted(CAMPOS_OPERATIVOS.items()))
@pytest.mark.asyncio
async def test_ac02_cada_campo_viaja_de_ida_y_vuelta(auth_headers, client, campo, valor):
    """Un test por campo: si uno se pierde, el informe dice cuál."""
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_payload(**{campo: valor}))
    assert r.status_code == 201, r.text
    assert r.json().get(campo) == valor, f"'{campo}' no se persistió"

    leido = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert leido.json().get(campo) == valor, f"'{campo}' se pierde entre escritura y lectura"


@pytest.mark.asyncio
async def test_ac02_cause_id_en_mortalidad(auth_headers, client):
    """`cause_id` en su uso real: el cliente exige registrar la causa de la mortalidad.

    Hoy falla, y no por `P0-14`: falla por **`P0-1`**. Todo registro de mortalidad con
    cantidad positiva entra en `_check_and_create_alerts`, que llama a
    `get_current_bird_balance` sin importarla y con tres argumentos en lugar de dos
    (`service.py:244`). El resultado es que **no puede registrarse ninguna mortalidad
    válida**, que es el alcance real de `P0-1`.

    El test se deja rojo y trazado: lo pone en verde el **Stage 4** (`GA-REM-005`).
    Requiere además un saldo de aves inicial en el lote de prueba, que hoy es cero.
    """
    # Saldo inicial: sin aves en el lote, `BR-01` rechaza cualquier mortalidad.
    recepcion = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "farm_id": 1,
        "house_id": 1,
        "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 500}],
    })
    assert recepcion.status_code == 201, recepcion.text

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": 2,
        "event_type": "mortality_recording",
        "event_date": recent_event_date(),
        "cause_id": 1,
        "bird_movements": [{"sex": "female", "quantity": 1}],
    })
    assert r.status_code == 201, r.text
    assert r.json()["cause_id"] == 1, "La mortalidad debe conservar su causa"


# ── AC09 / AC11 · edición ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac09_la_edicion_persiste_los_campos_operativos(auth_headers, client):
    r = await client.post("/api/v1/operations", headers=auth_headers, json=_payload())
    assert r.status_code == 201, r.text
    eid = r.json()["id"]

    u = await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                         json={"vaccine_id": 1, "vaccination_route": "ocular",
                               "dosage_per_bird": 0.25})
    assert u.status_code == 200, u.text
    assert u.json()["vaccine_id"] == 1
    assert u.json()["vaccination_route"] == "ocular"
    assert u.json()["dosage_per_bird"] == 0.25


@pytest.mark.asyncio
async def test_ac09_la_edicion_parcial_no_borra_lo_que_no_menciona(auth_headers, client):
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_payload(vaccine_id=1, vaccine_lot_number="LOT-INTACTO"))
    eid = r.json()["id"]

    await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                     json={"observations": "solo cambio esto"})

    leido = await client.get(f"/api/v1/operations/{eid}", headers=auth_headers)
    assert leido.json()["vaccine_lot_number"] == "LOT-INTACTO", (
        "Una edición parcial no puede borrar campos que no menciona")
    assert leido.json()["observations"] == "solo cambio esto"


@pytest.mark.asyncio
async def test_ac11_r32_no_se_puede_aprobar_con_un_put(auth_headers, client):
    """`R-32`: fijar `status` por `PUT` saltaba revisión, `BR-13`, `BR-14` y el aprobador."""
    r = await client.post("/api/v1/operations", headers=auth_headers, json=_payload())
    eid = r.json()["id"]
    assert r.json()["status"] == "registered"

    u = await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                         json={"status": "approved"})
    assert u.status_code == 422, (
        f"Fijar el estado por PUT debe rechazarse explícitamente, no ignorarse: {u.status_code}")

    leido = await client.get(f"/api/v1/operations/{eid}", headers=auth_headers)
    assert leido.json()["status"] == "registered", "El evento no puede haber cambiado de estado"
    assert leido.json()["approved_by_id"] is None


@pytest.mark.asyncio
async def test_ac12_el_tipo_de_evento_es_inmutable(auth_headers, client):
    r = await client.post("/api/v1/operations", headers=auth_headers, json=_payload())
    eid = r.json()["id"]
    u = await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                         json={"event_type": "mortality_recording"})
    assert u.status_code == 422, "El tipo de evento no puede cambiarse tras registrarlo"
    leido = await client.get(f"/api/v1/operations/{eid}", headers=auth_headers)
    assert leido.json()["event_type"] == "vaccination"
