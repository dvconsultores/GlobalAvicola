"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020 §7` — de `NULL` al maestro: el campo vacío se completa.

Un evento que nació sin proveedor, sin causa o sin vacuna deja esos campos en `NULL`, y hasta
ahora el selector de corrección no los anunciaba: el operador no podía rellenar lo que faltaba,
solo cambiar lo que ya estaba. Aquí se recorre el contrato completo de ese hueco —el campo nulo
aparece en el selector con su catálogo y sin nombre, la corrección que lo completa deja el antes
nulo y el después con nombre, un maestro desactivado o ajeno no se acepta, y un campo que el tipo
de evento no admite (la vacuna en una recepción) tampoco— junto con la simetría de vaciar un
maestro que sí estaba.

Trazabilidad: `spec 020 §7` (`AC-O23-01..08`). Casos: `O23-B01..B09` y el alcance del selector.
"""

from __future__ import annotations

import json
import uuid

import pytest

from tests.test_uat_s2_corrections_masters import (
    _corregir_con_tipo,
    _historial,
    _por_sufijo,
    _proveedor,
    _recepcion_con_proveedor,
    _tipo_de_correccion,
    _token_de_otra_empresa,
    _ultima,
)
from tests.test_uat_s2_owner_decisions_a import (
    _alta_mortalidad,
    _id_de_la_desconocida,
    _lote_con_aves,
)
from tests.test_uat_s2_write_contract import (
    _alta_recepcion,
    _campos,
    _corregir,
    _detalle,
)

#: Ruta del selector de campos corregibles de un evento.
SELECTOR = "/api/v1/corrections/events/{event_id}/correctable-fields"


# ── Datos de operación ───────────────────────────────────────────────────────

async def _recepcion_sin_proveedor(client, headers) -> dict:
    """Recepción de reproductoras sin `supplier_id`: el evento nace con el campo en `NULL`."""
    r = await _alta_recepcion(client, headers)
    assert r.status_code == 201, r.text
    evento = r.json()
    assert evento.get("supplier_id") is None, evento
    return evento


async def _mortalidad_con_causa(client, headers) -> dict:
    """Mortalidad con la causa «Desconocida»: `RR-32` exige una causa explícita."""
    lote = await _lote_con_aves(client, headers)
    causa = await _id_de_la_desconocida(client, headers, "mortality-causes")
    r = await _alta_mortalidad(client, headers, lote, cause_id=causa)
    assert r.status_code == 201, r.text
    return r.json()


async def _vacuna(client, headers) -> int:
    """Una vacuna activa del catálogo de la empresa del actor."""
    r = await client.post("/api/v1/masters/vaccines", headers=headers,
                          json={"name": f"Vacuna O23 {uuid.uuid4().hex[:8].upper()}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _nombres(campos) -> list[str]:
    """Los `field_name` del selector, para buscar por sufijo sin depender del prefijo de fila."""
    return sorted(c["field_name"] for c in campos)


def _tiene(campos, sufijo: str) -> bool:
    return any(c["field_name"].endswith(sufijo) for c in campos)


def _valores(valor) -> dict:
    """`previous_values`/`new_values` llegan como JSON decodificado o como texto."""
    if isinstance(valor, str):
        return json.loads(valor)
    return valor or {}


async def _auditoria_del_evento(client, headers, event_id: int) -> list[dict]:
    r = await client.get("/api/v1/audit", headers=headers, params={
        "entity_type": "operational_event", "entity_id": str(event_id), "limit": 200,
    })
    assert r.status_code == 200, r.text
    return r.json()["logs"]


# ── O23-B01 · el campo nulo se anuncia en el selector ────────────────────────

@pytest.mark.asyncio
async def test_o23_b01_la_recepcion_sin_proveedor_ofrece_el_campo(auth_headers, client):
    """`AC-O23-01/02`: el selector anuncia `supplier_id` con su catálogo y sin nombre."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)

    entrada = _por_sufijo(await _campos(client, auth_headers, evento["id"]), "supplier_id")
    assert entrada["master"] == "suppliers", entrada
    assert entrada["current_value"] is None, entrada
    assert entrada["current_display"] is None, entrada


@pytest.mark.asyncio
async def test_o23_b01_la_mortalidad_no_ofrece_campos_que_no_le_tocan(auth_headers, client):
    """`AC-O23-01/02`: una mortalidad no ofrece proveedor ni vacuna entre sus campos."""
    evento = await _mortalidad_con_causa(client, auth_headers)

    campos = await _campos(client, auth_headers, evento["id"])
    assert not _tiene(campos, "supplier_id"), _nombres(campos)
    assert not _tiene(campos, "vaccine_id"), _nombres(campos)


# ── O23-B02 · de `NULL` a un proveedor activo propio ─────────────────────────

@pytest.mark.asyncio
async def test_o23_b02_completar_el_proveedor_nulo_deja_la_traza(auth_headers, client):
    """`AC-O23-03` (A) y `AC-O23-06`: el antes nulo y el después con nombre, y el evento corregido."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)
    proveedor_id, nombre = await _proveedor(client, auth_headers)

    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(proveedor_id))
    assert r.status_code == 201, r.text
    creada = r.json()
    assert creada["original_value"] is None, creada
    assert creada["corrected_value"] == str(proveedor_id), creada
    assert creada["corrected_display"] == nombre, creada

    detalle = await _detalle(client, auth_headers, evento["id"])
    assert detalle["supplier_id"] == proveedor_id, detalle
    assert detalle["status"] == "corrected", detalle


# ── O23-B03 · un proveedor desactivado no se acepta ──────────────────────────

@pytest.mark.asyncio
async def test_o23_b03_un_proveedor_desactivado_es_400(auth_headers, client):
    """`AC-O23-05`: un maestro dado de baja no completa nada y no deja fila."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)
    proveedor_id, _ = await _proveedor(client, auth_headers)
    baja = await client.delete(f"/api/v1/masters/suppliers/{proveedor_id}", headers=auth_headers)
    assert baja.status_code == 204, baja.text

    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(proveedor_id))
    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "OD-21", r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] is None
    historial = await _historial(client, auth_headers, evento["id"])
    assert not [c for c in historial if c["field_name"].endswith("supplier_id")], historial


# ── O23-B04 · un proveedor de otra empresa no se acepta ni se nombra ─────────

@pytest.mark.asyncio
async def test_o23_b04_un_proveedor_ajeno_es_400_y_no_se_nombra(
        auth_headers, client, seeded_ids):
    """`AC-O23-03` (D): el maestro de la otra empresa se comporta como inexistente."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)
    headers_ajenos = await _token_de_otra_empresa(client, auth_headers,
                                                  seeded_ids["company_id_2"])
    ajeno_id, nombre_ajeno = await _proveedor(client, headers_ajenos)

    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(ajeno_id))
    assert r.status_code == 400, r.text
    assert nombre_ajeno not in r.text, r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] is None


# ── O23-B05 · de un proveedor a otro ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_o23_b05_cambiar_el_proveedor_por_otro_es_201(auth_headers, client):
    """`AC-O23-03` (B): la corrección de un maestro ya cargado sigue funcionando."""
    id_a, _ = await _proveedor(client, auth_headers)
    id_b, _ = await _proveedor(client, auth_headers)
    evento = await _recepcion_con_proveedor(client, auth_headers, id_a)

    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(id_b))
    assert r.status_code == 201, r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] == id_b


# ── O23-B06 · la causa de una mortalidad no se puede vaciar ──────────────────

@pytest.mark.asyncio
async def test_o23_b06_vaciar_la_causa_de_la_mortalidad_es_400(auth_headers, client):
    """`AC-O23-03` (C) y `AC-O23-08`: `RR-32` impide dejar una mortalidad sin causa, también al corregir."""
    evento = await _mortalidad_con_causa(client, auth_headers)
    antes = (await _detalle(client, auth_headers, evento["id"]))["cause_id"]

    r = await _corregir(client, auth_headers, evento["id"], "cause_id", "")
    assert r.status_code == 400, r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["cause_id"] == antes


# ── O23-B07 · el proveedor sí se puede vaciar ────────────────────────────────

@pytest.mark.asyncio
async def test_o23_b07_vaciar_el_proveedor_de_una_recepcion_es_201(auth_headers, client):
    """`AC-O23-03` (C): el proveedor es anulable; vaciarlo deja el evento en `NULL`."""
    proveedor_id, _ = await _proveedor(client, auth_headers)
    evento = await _recepcion_con_proveedor(client, auth_headers, proveedor_id)

    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", "")
    assert r.status_code == 201, r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] is None


# ── O23-B08 · la traza completa de la corrección con tipo y motivo ───────────

@pytest.mark.asyncio
async def test_o23_b08_la_fila_y_la_auditoria_dejan_el_antes_nulo(auth_headers, client):
    """`AC-O23-06`: historial y auditoría registran el paso de `NULL` al maestro."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)
    proveedor_id, nombre = await _proveedor(client, auth_headers)
    tipo_id = await _tipo_de_correccion(client, auth_headers)
    motivo = "Completar proveedor omitido"

    r = await _corregir_con_tipo(client, auth_headers, evento["id"], "supplier_id",
                                 str(proveedor_id), tipo_id, motivo)
    assert r.status_code == 201, r.text

    fila = _ultima(await _historial(client, auth_headers, evento["id"]), "supplier_id")
    assert fila["original_value"] is None, fila
    assert fila["original_display"] is None, fila
    assert fila["corrected_value"] == str(proveedor_id), fila
    assert fila["corrected_display"] == nombre, fila
    assert fila["reason"] == motivo, fila
    assert fila["correction_type_id"] == tipo_id, fila
    assert fila.get("corrected_by_id") is not None, fila

    logs = await _auditoria_del_evento(client, auth_headers, evento["id"])
    corregidos = [log for log in logs if log["action"] == "corrected"]
    assert corregidos, logs
    assert any(
        str(proveedor_id) in json.dumps(_valores(log.get("new_values")), ensure_ascii=False)
        for log in corregidos
    ), corregidos


# ── O23-B09 · una recepción no admite vacuna ─────────────────────────────────

@pytest.mark.asyncio
async def test_o23_b09_poner_vacuna_a_una_recepcion_es_400(auth_headers, client):
    """`AC-O23-04`: el campo no pertenece al tipo de evento y no se escribe."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)
    vacuna_id = await _vacuna(client, auth_headers)

    r = await _corregir(client, auth_headers, evento["id"], "vaccine_id", str(vacuna_id))
    assert r.status_code == 400, r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["vaccine_id"] is None


# ── Selector · alcance del endpoint ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_o23_s01_el_selector_exige_autenticacion_y_respeta_la_empresa(
        auth_headers, client, seeded_ids):
    """El selector no se abre sin token, no inventa eventos y no cruza de empresa."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)

    sin_token = await client.get(SELECTOR.format(event_id=evento["id"]))
    assert sin_token.status_code == 401, sin_token.text

    inexistente = await client.get(SELECTOR.format(event_id=999999999), headers=auth_headers)
    assert inexistente.status_code == 404, inexistente.text

    headers_ajenos = await _token_de_otra_empresa(client, auth_headers,
                                                  seeded_ids["company_id_2"])
    cruzado = await client.get(SELECTOR.format(event_id=evento["id"]), headers=headers_ajenos)
    # Fail closed: el evento de otra empresa no existe para el actor (404).
    assert cruzado.status_code == 404, cruzado.text


# ── O23-B03b · tampoco se cambia a un proveedor desactivado ──────────────────

@pytest.mark.asyncio
async def test_o23_b03b_cambiar_a_un_proveedor_desactivado_es_400(auth_headers, client):
    """`AC-O23-05`: `OD-21` vale sea cual sea el original; el evento conserva su proveedor."""
    id_a, _ = await _proveedor(client, auth_headers)
    id_b, _ = await _proveedor(client, auth_headers)
    baja = await client.delete(f"/api/v1/masters/suppliers/{id_b}", headers=auth_headers)
    assert baja.status_code == 204, baja.text
    evento = await _recepcion_con_proveedor(client, auth_headers, id_a)

    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(id_b))
    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "OD-21", r.text

    assert (await _detalle(client, auth_headers, evento["id"]))["supplier_id"] == id_a


# ── O23-B09b · la recepción no anuncia maestros ajenos a su tipo ─────────────

@pytest.mark.asyncio
async def test_o23_b09b_la_recepcion_no_ofrece_vacuna_ni_causa(auth_headers, client):
    """`AC-O23-01`: el selector de una recepción no ofrece vacuna, causa ni medicamento vacíos."""
    evento = await _recepcion_sin_proveedor(client, auth_headers)

    campos = await _campos(client, auth_headers, evento["id"])
    assert not _tiene(campos, "vaccine_id"), _nombres(campos)
    assert not _tiene(campos, "cause_id"), _nombres(campos)
    assert not _tiene(campos, "medication_id"), _nombres(campos)


# ── O23-B10 · el original hoy inactivo se sigue leyendo por nombre ───────────

@pytest.mark.asyncio
async def test_o23_b10_un_original_hoy_inactivo_se_sigue_leyendo(auth_headers, client):
    """`AC-O23-05`: la baja lógica no oculta el valor histórico del evento."""
    id_a, nombre_a = await _proveedor(client, auth_headers)
    evento = await _recepcion_con_proveedor(client, auth_headers, id_a)
    baja = await client.delete(f"/api/v1/masters/suppliers/{id_a}", headers=auth_headers)
    assert baja.status_code == 204, baja.text

    entrada = _por_sufijo(await _campos(client, auth_headers, evento["id"]), "supplier_id")
    assert entrada["current_value"] == str(id_a), entrada
    assert entrada["current_display"] == nombre_a, entrada
