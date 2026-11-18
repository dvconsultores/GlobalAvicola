"""`GA-UAT-BREEDER-CRIA-S1` · `spec 015 §4.1` — reglas «no vacío» `RR-20`..`RR-23`.

Un registro sin su dato mínimo no dice nada y hasta ahora entraba con un `201`: el pesaje
sin peso, la vacunación sin vacuna, la medicación sin medicamento y el alimento sin kilos.
Aquí se recorre el contrato completo del servidor —alta, edición y corrección— con lo que
ve el operador: un `400` con el mensaje en español, orientado al campo y sin código interno
(el identificador de la regla viaja aparte, en el campo `rule` de la respuesta).
"""

from __future__ import annotations

import pytest

from tests.time_reference import recent_event_date

LOTE = 2


def _cuerpo(event_type: str, **extra) -> dict:
    cuerpo = {"lot_id": LOTE, "event_type": event_type, "event_date": recent_event_date()}
    cuerpo.update(extra)
    return cuerpo


async def _alta(client, headers, event_type: str, **extra):
    return await client.post("/api/v1/operations", headers=headers,
                             json=_cuerpo(event_type, **extra))


def _sin_codigo_interno(detail: str) -> None:
    """El mensaje no expone el identificador de la regla ni nombres del esquema."""
    for prohibido in ("RR-", "BR-", "None", "null", "_id"):
        assert prohibido not in detail, f"el mensaje expone detalle interno ({prohibido}): {detail}"


# ── RR-20 · pesaje: al menos una fila con peso > 0 ────────────────────────────

async def test_rr20_pesaje_sin_filas_es_400_en_espanol(auth_headers, client):
    r = await _alta(client, auth_headers, "weight_recording")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Registre el peso promedio de al menos un sexo (mayor a cero)"
    assert r.json()["rule"] == "RR-20"
    _sin_codigo_interno(r.json()["detail"])


async def test_rr20_pesaje_con_peso_cero_es_400(auth_headers, client):
    r = await _alta(client, auth_headers, "weight_recording",
                    bird_movements=[{"sex": "male", "quantity": 10, "avg_weight": 0}])
    assert r.status_code == 400, r.text
    assert "peso promedio" in r.json()["detail"]
    _sin_codigo_interno(r.json()["detail"])


async def test_rr20_pesaje_con_un_peso_positivo_es_201(auth_headers, client):
    r = await _alta(client, auth_headers, "weight_recording",
                    bird_movements=[{"sex": "male", "quantity": 10, "avg_weight": 2.1}])
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert det.json()["bird_movements"][0]["avg_weight"] == pytest.approx(2.1)


# ── RR-21 · vacunación: la vacuna aplicada ───────────────────────────────────

async def test_rr21_vacunacion_sin_vacuna_es_400(auth_headers, client):
    r = await _alta(client, auth_headers, "vaccination", vaccination_route="water")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Seleccione la vacuna aplicada"
    assert r.json()["rule"] == "RR-21"
    _sin_codigo_interno(r.json()["detail"])


async def test_rr21_vacunacion_con_vacuna_es_201(auth_headers, client):
    r = await _alta(client, auth_headers, "vaccination", vaccine_id=1, vaccination_route="water")
    assert r.status_code == 201, r.text
    assert r.json()["vaccine_id"] == 1


# ── RR-22 · medicación: el medicamento aplicado ──────────────────────────────

async def test_rr22_medicacion_sin_medicamento_es_400(auth_headers, client):
    r = await _alta(client, auth_headers, "medication", dosage_per_bird=0.5)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Seleccione el medicamento aplicado"
    assert r.json()["rule"] == "RR-22"
    _sin_codigo_interno(r.json()["detail"])


async def test_rr22_medicacion_con_medicamento_es_201(auth_headers, client):
    r = await _alta(client, auth_headers, "medication", medication_id=1, dosage_per_bird=0.5)
    assert r.status_code == 201, r.text
    assert r.json()["medication_id"] == 1


# ── RR-23 · alimento: al menos una fila con kilos > 0 ────────────────────────

async def test_rr23_alimento_sin_filas_es_400(auth_headers, client):
    r = await _alta(client, auth_headers, "feed_registration")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Registre la cantidad de alimento (kg) mayor a cero"
    assert r.json()["rule"] == "RR-23"
    _sin_codigo_interno(r.json()["detail"])


async def test_rr23_alimento_con_cero_kilos_es_rechazado(auth_headers, client):
    """La fila de kilos cero no es una fila: la rechaza el contrato de escritura (`R-189`)."""
    r = await _alta(client, auth_headers, "feed_registration",
                    feed_movements=[{"quantity_kg": 0}])
    assert r.status_code in (400, 422), r.text
    if r.status_code == 400:
        assert "alimento" in r.json()["detail"]


async def test_rr23_alimento_con_kilos_es_201(auth_headers, client):
    r = await _alta(client, auth_headers, "feed_registration",
                    feed_movements=[{"quantity_kg": 12.5}])
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert det.json()["feed_movements"][0]["quantity_kg"] == pytest.approx(12.5)


# ── edición · la regla se revalida sobre el estado candidato ─────────────────

async def test_edicion_no_puede_vaciar_la_vacuna(auth_headers, client):
    alta = await _alta(client, auth_headers, "vaccination", vaccine_id=1, vaccination_route="water")
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                         json={"vaccine_id": None})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Seleccione la vacuna aplicada"
    _sin_codigo_interno(r.json()["detail"])

    leido = await client.get(f"/api/v1/operations/{eid}", headers=auth_headers)
    assert leido.json()["vaccine_id"] == 1, "un rechazo no cambia el dato"


# ── corrección · vaciar la vacuna tampoco es una puerta trasera ─────────────

async def test_correccion_no_puede_vaciar_la_vacuna(auth_headers, client):
    alta = await _alta(client, auth_headers, "vaccination", vaccine_id=1, vaccination_route="water")
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await client.post("/api/v1/corrections", headers=auth_headers, json={
        "event_id": eid, "field_name": "vaccine_id",
        "corrected_value": "", "reason": "Se cargó la vacuna equivocada",
    })
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Seleccione la vacuna aplicada"
    _sin_codigo_interno(r.json()["detail"])

    leido = await client.get(f"/api/v1/operations/{eid}", headers=auth_headers)
    assert leido.json()["vaccine_id"] == 1, "un rechazo no cambia el dato"
