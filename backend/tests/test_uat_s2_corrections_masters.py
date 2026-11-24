"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020 §3.1-3.2` — corrección de campos maestros y de cantidades.

Un campo que apunta a un catálogo (proveedor, medicamento, causa, vacuna, granja, planta,
transporte) se corrige con el identificador del maestro, pero se **lee** con el nombre de lo que
había y el nombre de lo que quedó: el operador no reconoce un número. Y no todo campo del evento
es un maestro: la muestra tomada y las observaciones no pertenecen a ningún catálogo, así que su
fila del selector no debe anunciar ninguno.

Trazabilidad: `spec 020 (AC-S2-C03..C05)` · casos `CORR-S2-01, 02, 03, 08, 09`.
"""

from __future__ import annotations

import uuid

import pytest

from tests.test_uat_s2_write_contract import (
    _alta_recepcion,
    _campos,
    _corregir,
    _detalle,
    _lote,
)
from tests.time_reference import recent_event_date


async def _proveedor(client, headers) -> tuple[int, str]:
    nombre = f"Proveedor UATS2 {uuid.uuid4().hex[:8].upper()}"
    r = await client.post("/api/v1/masters/suppliers", headers=headers, json={"name": nombre})
    assert r.status_code == 201, r.text
    return r.json()["id"], nombre


async def _medicamento(client, headers) -> tuple[int, str]:
    nombre = f"Medicamento UATS2 {uuid.uuid4().hex[:8].upper()}"
    r = await client.post("/api/v1/masters/medications", headers=headers, json={"name": nombre})
    assert r.status_code == 201, r.text
    return r.json()["id"], nombre


async def _historial(client, headers, event_id: int) -> list[dict]:
    r = await client.get(f"/api/v1/corrections/event/{event_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def _tipo_de_correccion(client, headers) -> int:
    r = await client.get("/api/v1/masters/correction-types", headers=headers)
    assert r.status_code == 200, r.text
    datos = r.json()
    items = datos["items"] if isinstance(datos, dict) else datos
    if items:
        return items[0]["id"]
    r = await client.post("/api/v1/masters/correction-types", headers=headers,
                          json={"name": f"Tipo UATS2 {uuid.uuid4().hex[:6].upper()}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _corregir_con_tipo(client, headers, event_id, campo, valor, tipo_id, motivo):
    return await client.post("/api/v1/corrections", headers=headers, json={
        "event_id": event_id, "field_name": campo, "corrected_value": valor,
        "reason": motivo, "correction_type_id": tipo_id,
    })


def _por_sufijo(campos, sufijo: str) -> dict:
    for campo in campos:
        if campo["field_name"].endswith(sufijo):
            return campo
    raise AssertionError(
        f"el selector no ofrece ningún campo '{sufijo}': "
        f"{sorted(c['field_name'] for c in campos)}"
    )


def _ultima(historial, sufijo: str) -> dict:
    filas = [c for c in historial if c["field_name"].endswith(sufijo)]
    assert filas, f"el historial no registra '{sufijo}': {historial}"
    return filas[-1]


async def _recepcion_con_proveedor(client, headers, supplier_id: int) -> dict:
    r = await _alta_recepcion(client, headers, supplier_id=supplier_id)
    assert r.status_code == 201, r.text
    return r.json()


async def _recepcion_breeder_100(client, headers, **extra) -> dict:
    """Recepción de 100 reproductoras con el cuadre de `BR-20` y una muestra de la mitad.

    Alojadas + muertas al llegar + rechazadas al llegar es exactamente lo recibido, y la muestra
    (50) no supera el techo de aves recibidas.
    """
    cuerpo = {
        "received_total": 100,
        "dead_on_arrival": 0,
        "rejected_on_arrival": 0,
        "bird_movements": [{"sex": "mixed", "quantity": 100}],
        "sample_size": 50,
    }
    cuerpo.update(extra)
    respuesta = await _alta_recepcion(client, headers, **cuerpo)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


# ── CORR-S2-01 · el selector de un campo maestro ─────────────────────────────

@pytest.mark.asyncio
async def test_corr_s2_01_el_selector_dice_de_que_catalogo_es_el_campo(auth_headers, client):
    """CORR-S2-01: la fila de `supplier_id` anuncia el catálogo y el nombre del proveedor."""
    proveedor_id, nombre = await _proveedor(client, auth_headers)
    evento = await _recepcion_con_proveedor(client, auth_headers, proveedor_id)

    entrada = _por_sufijo(await _campos(client, auth_headers, evento["id"]), "supplier_id")

    assert entrada["master"] == "suppliers", entrada
    assert entrada["current_display"] == nombre, entrada
    assert entrada["current_value"] == str(proveedor_id), entrada


# ── CORR-S2-02 · el historial de una corrección de maestro ───────────────────

@pytest.mark.asyncio
async def test_corr_s2_02_el_historial_lee_el_antes_y_el_despues_por_nombre(auth_headers, client):
    """CORR-S2-02: cambiar el proveedor deja en el historial los dos nombres y los dos ids."""
    id_a, nombre_a = await _proveedor(client, auth_headers)
    id_b, nombre_b = await _proveedor(client, auth_headers)
    evento = await _recepcion_con_proveedor(client, auth_headers, id_a)

    # El valor corregido viaja como texto: el contrato de escritura no acepta números.
    r = await _corregir(client, auth_headers, evento["id"], "supplier_id", str(id_b))
    assert r.status_code == 201, r.text

    fila = _ultima(await _historial(client, auth_headers, evento["id"]), "supplier_id")
    assert fila["original_display"] == nombre_a, fila
    assert fila["corrected_display"] == nombre_b, fila
    assert fila["original_value"] == str(id_a), fila
    assert fila["corrected_value"] == str(id_b), fila


# ── CORR-S2-03 · el mismo contrato para el medicamento ───────────────────────

@pytest.mark.asyncio
async def test_corr_s2_03_el_medicamento_se_lee_por_nombre_en_selector_e_historial(
        auth_headers, client):
    """CORR-S2-03: `medication_id` expone el nombre del medicamento, no su identificador."""
    id_a, nombre_a = await _medicamento(client, auth_headers)
    id_b, nombre_b = await _medicamento(client, auth_headers)
    lote = await _lote(client, auth_headers)
    alta = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "medication", "event_date": recent_event_date(),
        "medication_id": id_a,
    })
    assert alta.status_code == 201, alta.text
    evento_id = alta.json()["id"]

    entrada = _por_sufijo(await _campos(client, auth_headers, evento_id), "medication_id")
    assert entrada["master"] == "medications", entrada
    assert entrada["current_display"] == nombre_a, entrada
    assert entrada["current_value"] == str(id_a), entrada

    r = await _corregir(client, auth_headers, evento_id, "medication_id", str(id_b))
    assert r.status_code == 201, r.text

    fila = _ultima(await _historial(client, auth_headers, evento_id), "medication_id")
    assert fila["original_display"] == nombre_a, fila
    assert fila["corrected_display"] == nombre_b, fila
    assert fila["original_value"] == str(id_a), fila
    assert fila["corrected_value"] == str(id_b), fila


# ── CORR-S2-08 · qué campos son maestros y cuáles no ─────────────────────────

@pytest.mark.asyncio
async def test_corr_s2_08_el_mapa_de_maestros_y_los_campos_sin_catalogo(auth_headers, client):
    """CORR-S2-08: el mapa de maestros corregibles y los campos que no son de ningún catálogo."""
    # En el cuerpo del test: si el mapa no existe, falla este caso y no la recolección entera.
    from app.corrections.service import MAESTROS_CORREGIBLES

    esperado = {
        "supplier_id": "suppliers",
        "cause_id": "mortality-causes",
        "cull_cause_id": "cull-causes",
        "vaccine_id": "vaccines",
        "medication_id": "medications",
        "destination_farm_id": "farms",
        "destination_plant_id": "processing-plants",
        "transport_id": "transports",
    }
    assert isinstance(MAESTROS_CORREGIBLES, dict), MAESTROS_CORREGIBLES
    assert set(MAESTROS_CORREGIBLES) == set(esperado), MAESTROS_CORREGIBLES
    for campo, maestro in esperado.items():
        valores = MAESTROS_CORREGIBLES[campo]
        assert valores, f"{campo} no declara ningún maestro: {valores}"
        assert valores[0] == maestro, f"{campo} apunta a {valores[0]}, se esperaba {maestro}"

    proveedor_id, _ = await _proveedor(client, auth_headers)
    evento = await _recepcion_con_proveedor(client, auth_headers, proveedor_id)
    campos = await _campos(client, auth_headers, evento["id"])

    sin_catalogo = [c for c in campos
                    if "sample_size" in c["field_name"] or "observation" in c["field_name"]]
    assert any("observation" in c["field_name"] for c in sin_catalogo), (
        "el selector no ofrece observaciones: " + ", ".join(sorted(c["field_name"] for c in campos))
    )
    for campo in sin_catalogo:
        assert campo.get("master") is None, campo
        assert campo.get("current_display") is None, campo


# ── CORR-S2-09 · corregir una cantidad de la recepción ───────────────────────

@pytest.mark.asyncio
async def test_corr_s2_09_corregir_la_muestra_guarda_la_traza_y_sube_la_version(
        auth_headers, client):
    """CORR-S2-09: la corrección de la muestra queda con motivo, autor, tipo y nueva versión."""
    tipo_id = await _tipo_de_correccion(client, auth_headers)
    evento = await _recepcion_breeder_100(client, auth_headers)
    antes = await _detalle(client, auth_headers, evento["id"])

    motivo = "Muestra mal tomada en campo"
    r = await _corregir_con_tipo(client, auth_headers, evento["id"], "sample_size", "40",
                                 tipo_id, motivo)
    assert r.status_code == 201, r.text

    fila = _ultima(await _historial(client, auth_headers, evento["id"]), "sample_size")
    assert fila["original_value"] == "50", fila
    assert fila["corrected_value"] == "40", fila
    assert fila["reason"] == motivo, fila
    assert fila.get("corrected_by_id") is not None, fila
    assert fila.get("correction_type_id") == tipo_id, fila

    despues = await _detalle(client, auth_headers, evento["id"])
    assert despues["status"] == "corrected", despues
    assert despues["version"] == antes["version"] + 1, (antes, despues)
    assert despues["sample_size"] == 40, despues
