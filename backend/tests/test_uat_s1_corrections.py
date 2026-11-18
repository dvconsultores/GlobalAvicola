"""`S1-CORR-01` · `spec 015 §3` — corrección de submovimientos y campos corregibles.

El formulario de corrección solo ofrecía «Observaciones» y los submovimientos no eran
corregibles. Aquí se recorre el contrato completo: el campo corregido de una fila se
identifica con el **id de esa fila** (`bird_movements[<id>].<campo>`, sin migración), la
corrección escribe el valor, conserva original y corregido, y una salida de aves se
revalida por el **delta** contra el saldo del lote (`BR-01`).
"""

from __future__ import annotations

import os

import pytest

from tests.time_reference import recent_event_date


async def _pesaje(client, headers, lot_id: int = 2, avg_weight=2.0, quantity: int = 10):
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lot_id, "event_type": "weight_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "male", "quantity": quantity, "avg_weight": avg_weight}],
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _recepcion(client, headers, lot_id: int, cantidad: int):
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lot_id, "farm_id": 1, "house_id": 1,
        "event_type": "bird_reception", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": cantidad}],
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _mortalidad(client, headers, lot_id: int, cantidad: int):
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lot_id, "event_type": "mortality_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": cantidad}],
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _campos(client, headers, event_id: int):
    r = await client.get(f"/api/v1/corrections/events/{event_id}/correctable-fields",
                         headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def _fila_de(client, headers, event_id: int, sufijo: str) -> dict:
    """La entrada del selector correspondiente al campo de esa fila."""
    for campo in await _campos(client, headers, event_id):
        if campo["field_name"].endswith(sufijo) and campo["row_id"] is not None:
            return campo
    raise AssertionError(f"el selector no ofrece ningún campo '{sufijo}'")


async def _corregir(client, headers, event_id, campo, valor, motivo="Error de digitación"):
    return await client.post("/api/v1/corrections", headers=headers, json={
        "event_id": event_id, "field_name": campo,
        "corrected_value": valor, "reason": motivo,
    })


async def _detalle(client, headers, event_id: int) -> dict:
    r = await client.get(f"/api/v1/operations/{event_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def _headers_aprobador(client) -> dict:
    from seeds.test_seeds import TEST_APPROVER_PASSWORD_ENV, TEST_APPROVER_USERNAME

    r = await client.post("/api/v1/login", json={
        "username": TEST_APPROVER_USERNAME,
        "password": os.environ[TEST_APPROVER_PASSWORD_ENV],
    })
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── AC-S1-C01 · pesaje: el peso medio se corrige en la fila ───────────────────

@pytest.mark.asyncio
async def test_t1_corregir_el_peso_promedio_de_un_pesaje(auth_headers, client):
    evento = await _pesaje(client, auth_headers)
    fila = await _fila_de(client, auth_headers, evento["id"], ".avg_weight")
    assert fila["current_value"] == "2.0"

    r = await _corregir(client, auth_headers, evento["id"], fila["field_name"], "2.5")
    assert r.status_code == 201, r.text
    assert r.json()["field_name"] == fila["field_name"]
    assert r.json()["original_value"] == "2.0"
    assert r.json()["corrected_value"] == "2.5"

    detalle = await _detalle(client, auth_headers, evento["id"])
    assert detalle["bird_movements"][0]["avg_weight"] == pytest.approx(2.5), (
        "la corrección debe escribir el valor en la fila, no solo en el registro")
    assert detalle["status"] == "corrected"


# ── AC-S1-C02 · la cantidad no puede comerse el saldo ────────────────────────

@pytest.mark.asyncio
async def test_t2_cantidad_por_encima_del_saldo_no_cambia_nada(auth_headers, client):
    await _recepcion(client, auth_headers, 2, 100)
    evento = await _mortalidad(client, auth_headers, 2, 5)
    fila = await _fila_de(client, auth_headers, evento["id"], ".quantity")
    antes = await _detalle(client, auth_headers, evento["id"])
    logs_antes = await client.get(f"/api/v1/corrections/event/{evento['id']}",
                                  headers=auth_headers)

    r = await _corregir(client, auth_headers, evento["id"], fila["field_name"], "999999")
    assert r.status_code == 400, r.text
    assert "saldo de aves disponibles" in r.json()["detail"], r.text

    despues = await _detalle(client, auth_headers, evento["id"])
    assert despues["bird_movements"][0]["quantity"] == antes["bird_movements"][0]["quantity"]
    assert despues["status"] == antes["status"], "un rechazo no cambia el estado"
    logs_despues = await client.get(f"/api/v1/corrections/event/{evento['id']}",
                                    headers=auth_headers)
    assert len(logs_despues.json()) == len(logs_antes.json()) == 0, (
        "un rechazo no deja registro de corrección")


# ── AC-S1-C03 · la fila inexistente y el campo no admitido ───────────────────

@pytest.mark.asyncio
async def test_t3_fila_inexistente_devuelve_la_lista_de_campos(auth_headers, client):
    evento = await _pesaje(client, auth_headers)
    fila = await _fila_de(client, auth_headers, evento["id"], ".avg_weight")

    r = await _corregir(client, auth_headers, evento["id"], "bird_movements[999999].quantity", "1")
    assert r.status_code == 400, r.text
    detalle = r.json()["detail"]
    assert "Campos admitidos" in detalle, detalle
    assert fila["field_name"] in detalle, "la lista debe nombrar las filas reales con su id"


@pytest.mark.asyncio
async def test_t4_campo_de_fila_no_admitido(auth_headers, client):
    evento = await _pesaje(client, auth_headers)
    fila = await _fila_de(client, auth_headers, evento["id"], ".avg_weight")
    row_id = fila["row_id"]

    r = await _corregir(client, auth_headers, evento["id"], f"bird_movements[{row_id}].sex", "female")
    assert r.status_code == 400, r.text
    assert "no es corregible" in r.json()["detail"]

    detalle = await _detalle(client, auth_headers, evento["id"])
    assert detalle["bird_movements"][0]["sex"] == "male", "nada cambia"


@pytest.mark.asyncio
async def test_t5_valor_no_numerico_es_400_y_no_500(http_client):
    """Un texto donde va un decimal es una petición inválida, no un fallo del servidor."""
    from seeds.test_seeds import TEST_ADMIN_PASSWORD_ENV, TEST_ADMIN_USERNAME

    login = await http_client.post("/api/v1/login", json={
        "username": TEST_ADMIN_USERNAME,
        "password": os.environ[TEST_ADMIN_PASSWORD_ENV],
    })
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    evento = await _pesaje(http_client, headers)
    fila = await _fila_de(http_client, headers, evento["id"], ".avg_weight")

    r = await _corregir(http_client, headers, evento["id"], fila["field_name"], "dos kilos")
    assert r.status_code == 400, (r.status_code, r.text)
    assert "no es válido" in r.json()["detail"], r.text

    detalle = await _detalle(http_client, headers, evento["id"])
    assert detalle["bird_movements"][0]["avg_weight"] == pytest.approx(2.0), "nada cambia"


# ── AC-S1-C01 · contrato del selector ────────────────────────────────────────

@pytest.mark.asyncio
async def test_t6_el_selector_ofrece_la_fila_y_observaciones(auth_headers, client):
    evento = await _pesaje(client, auth_headers)
    campos = await _campos(client, auth_headers, evento["id"])

    nombres = [c["field_name"] for c in campos]
    assert "observations" in nombres, "el selector incluye siempre Observaciones"
    assert "lot_id" not in nombres and "farm_id" not in nombres and "house_id" not in nombres

    peso = next(c for c in campos if c["field_name"].endswith(".avg_weight"))
    assert peso["row_id"] is not None
    assert peso["label_key"] == "corrections.fields.bird_movements.avg_weight"
    assert peso["row_label"] == "male"
    assert peso["value_type"] == "decimal"
    assert peso["current_value"] == "2.0"

    cantidad = next(c for c in campos if c["field_name"].endswith(".quantity"))
    assert cantidad["value_type"] == "integer"


# ── AC-S1-C05 · fuera de estado corregible ───────────────────────────────────

@pytest.mark.asyncio
async def test_t7_evento_aprobado_no_es_corregible_y_el_mensaje_es_espanol(auth_headers, client):
    evento = await _pesaje(client, auth_headers)
    fila = await _fila_de(client, auth_headers, evento["id"], ".avg_weight")
    # Llevarlo a CORRECTED y aprobarlo con otra identidad (`BR-14`).
    assert (await _corregir(client, auth_headers, evento["id"], "observations", "ajuste")).status_code == 201
    aprobador = await _headers_aprobador(client)
    r = await client.post("/api/v1/approvals/approve", headers=aprobador,
                          json={"event_id": evento["id"], "observations": "ok"})
    assert r.status_code == 200, r.text

    assert await _campos(client, auth_headers, evento["id"]) == [], (
        "un evento aprobado no ofrece campos corregibles")

    r = await _corregir(client, auth_headers, evento["id"], fila["field_name"], "3.0")
    assert r.status_code == 400, r.text
    assert "Aprobado" in r.json()["detail"], r.json()["detail"]
    assert "approved" not in r.json()["detail"], "el estado no se muestra en crudo"


# ── AC-S1-C05 · permiso ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_t8_sin_permiso_de_correccion_es_403(client):
    """El aprobador de pruebas no tiene `corrections:correct`."""
    aprobador = await _headers_aprobador(client)
    r = await client.post("/api/v1/corrections", headers=aprobador, json={
        "event_id": 1, "field_name": "observations",
        "corrected_value": "x", "reason": "prueba de permiso",
    })
    assert r.status_code == 403, r.text
