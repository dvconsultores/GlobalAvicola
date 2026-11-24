"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020 §3.1-3.2` — contrato de escritura de muestra y cantidades.

La muestra tomada, la dosis por ave, los días de tratamiento y los pollitos son cantidades: una
muestra mayor que las aves recibidas, una muestra o una dosis negativas no describen nada que
haya ocurrido y hasta ahora entraban con un `201`. Aquí se recorre el contrato completo del
servidor —alta, edición y corrección— con lo que ve el operador: un `400` con el mensaje en
español, orientado al campo y sin código interno en el texto (el identificador de la regla
viaja aparte, en el campo `rule` de la respuesta). Y la simetría del otro lado: un campo
anulable se puede vaciar, y la fecha del evento —que no lo es— no.

Trazabilidad: `spec 020 (AC-S2-V01..V04, AC-S2-C01, AC-S2-C02)`.
"""

from __future__ import annotations

import uuid

import pytest

from tests.time_reference import iso_days_ago, recent_event_date

#: Aves de la recepción de referencia: el techo de la muestra (`RR-25`).
AVES_RECIBIDAS = 20


def _sin_codigo_interno(detail: str) -> None:
    """El mensaje no expone el identificador de la regla ni nombres del esquema."""
    for prohibido in ("RR-", "BR-", "None", "null", "_id"):
        assert prohibido not in detail, f"el mensaje expone detalle interno ({prohibido}): {detail}"


async def _lote(client, headers, bird_type: str = "breeder") -> int:
    """Un lote nuevo por caso: la muestra se mide contra **sus** aves recibidas."""
    r = await client.post("/api/v1/lots", headers=headers, json={
        "farm_id": 1, "house_id": 1,
        "lot_code": f"UATS2-{uuid.uuid4().hex[:8].upper()}",
        "bird_type": bird_type, "sex": "mixed",
        # El evento de referencia es reciente pero no de hoy: el lote arranca antes (`BR-06`).
        "start_date": iso_days_ago(21),
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _alta_recepcion(client, headers, **extra):
    """Recepción de reproductoras con el cuadre de `BR-20` bien formado."""
    lote = await _lote(client, headers)
    cuerpo = {
        "lot_id": lote, "farm_id": 1, "house_id": 1,
        "event_type": "bird_reception", "event_date": recent_event_date(),
        "received_total": AVES_RECIBIDAS, "dead_on_arrival": 0, "rejected_on_arrival": 0,
        "bird_movements": [{"sex": "mixed", "quantity": AVES_RECIBIDAS}],
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


async def _alta_pesaje(client, headers, **extra):
    return await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": 2, "event_type": "weight_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "male", "quantity": 10, "avg_weight": 2.0}],
        **extra,
    })


async def _alta_medicacion(client, headers, **extra):
    return await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": 2, "event_type": "medication", "event_date": recent_event_date(),
        "medication_id": 1, **extra,
    })


async def _alta_nacimiento(client, headers, **extra):
    """Nacimiento de incubadora: la cadena donde sanos y débiles son obligatorios (`B13`)."""
    lote = await _lote(client, headers, bird_type="hatchery")
    return await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote, "farm_id": 1, "house_id": 1,
        "event_type": "birth_registration", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 100}],
        "chicks_healthy": 100, "chicks_weak": 0, **extra,
    })


async def _detalle(client, headers, event_id: int) -> dict:
    r = await client.get(f"/api/v1/operations/{event_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def _corregir(client, headers, event_id, campo, valor, motivo="Error de digitación"):
    return await client.post("/api/v1/corrections", headers=headers, json={
        "event_id": event_id, "field_name": campo,
        "corrected_value": valor, "reason": motivo,
    })


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


# ── OPS-S2-04a · la muestra tomada de una recepción ──────────────────────────

@pytest.mark.asyncio
async def test_ops_s2_04a_muestra_igual_a_lo_recibido_es_aceptada(auth_headers, client):
    r = await _alta_recepcion(client, auth_headers, sample_size=AVES_RECIBIDAS)
    assert r.status_code == 201, r.text
    assert r.json()["sample_size"] == AVES_RECIBIDAS


@pytest.mark.asyncio
async def test_ops_s2_04a_muestra_menor_que_lo_recibido_es_aceptada(auth_headers, client):
    r = await _alta_recepcion(client, auth_headers, sample_size=AVES_RECIBIDAS - 5)
    assert r.status_code == 201, r.text
    assert r.json()["sample_size"] == AVES_RECIBIDAS - 5


@pytest.mark.asyncio
async def test_ops_s2_04a_muestra_mayor_que_lo_recibido_es_400(auth_headers, client):
    r = await _alta_recepcion(client, auth_headers, sample_size=AVES_RECIBIDAS + 1)
    assert r.status_code == 400, r.text
    assert "La muestra tomada no puede superar las aves recibidas" in r.json()["detail"]
    _sin_codigo_interno(r.json()["detail"])


@pytest.mark.asyncio
async def test_ops_s2_04a_muestra_negativa_es_400(auth_headers, client):
    r = await _alta_recepcion(client, auth_headers, sample_size=-1)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "El tamaño de muestra debe ser mayor a cero"
    _sin_codigo_interno(r.json()["detail"])


@pytest.mark.asyncio
async def test_ops_s2_04a_muestra_cero_es_400(auth_headers, client):
    r = await _alta_recepcion(client, auth_headers, sample_size=0)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "El tamaño de muestra debe ser mayor a cero"
    _sin_codigo_interno(r.json()["detail"])


# ── OPS-S2-04b · aves pesadas: la muestra no tiene cota superior ─────────────

@pytest.mark.asyncio
async def test_ops_s2_04b_aves_pesadas_negativas_es_400(auth_headers, client):
    r = await _alta_pesaje(client, auth_headers, sample_size=-3)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "El tamaño de muestra debe ser mayor a cero"
    _sin_codigo_interno(r.json()["detail"])


@pytest.mark.asyncio
async def test_ops_s2_04b_aves_pesadas_cero_es_400(auth_headers, client):
    r = await _alta_pesaje(client, auth_headers, sample_size=0)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "El tamaño de muestra debe ser mayor a cero"


@pytest.mark.asyncio
async def test_ops_s2_04b_aves_pesadas_positivas_es_201(auth_headers, client):
    r = await _alta_pesaje(client, auth_headers, sample_size=500)
    assert r.status_code == 201, r.text
    assert r.json()["sample_size"] == 500


# ── OPS-S2-04c · la edición hereda la regla sobre el estado candidato ────────

@pytest.mark.asyncio
async def test_ops_s2_04c_editar_la_muestra_por_encima_de_lo_recibido_es_400(
    auth_headers, client
):
    alta = await _alta_recepcion(client, auth_headers, sample_size=AVES_RECIBIDAS - 5)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                         json={"sample_size": AVES_RECIBIDAS + 1})
    assert r.status_code == 400, r.text
    assert "La muestra tomada no puede superar las aves recibidas" in r.json()["detail"]
    _sin_codigo_interno(r.json()["detail"])

    leido = await _detalle(client, auth_headers, eid)
    assert leido["sample_size"] == AVES_RECIBIDAS - 5, "un rechazo no cambia el dato"


@pytest.mark.asyncio
async def test_ops_s2_04c_editar_la_muestra_hasta_lo_recibido_es_200(auth_headers, client):
    alta = await _alta_recepcion(client, auth_headers, sample_size=AVES_RECIBIDAS - 5)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                         json={"sample_size": AVES_RECIBIDAS})
    assert r.status_code == 200, r.text
    assert r.json()["sample_size"] == AVES_RECIBIDAS


# ── CORR-S2-04 · la corrección de la muestra hereda la misma regla ───────────

@pytest.mark.asyncio
async def test_corr_s2_04_muestra_negativa_en_correccion_es_400(auth_headers, client):
    alta = await _alta_recepcion(client, auth_headers, sample_size=10)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "sample_size", "-1")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "El tamaño de muestra debe ser mayor a cero"
    _sin_codigo_interno(r.json()["detail"])
    assert (await _detalle(client, auth_headers, eid))["sample_size"] == 10


@pytest.mark.asyncio
async def test_corr_s2_04_muestra_cero_en_correccion_es_400(auth_headers, client):
    alta = await _alta_recepcion(client, auth_headers, sample_size=10)
    assert alta.status_code == 201, alta.text

    r = await _corregir(client, auth_headers, alta.json()["id"], "sample_size", "0")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "El tamaño de muestra debe ser mayor a cero"


@pytest.mark.asyncio
async def test_corr_s2_04_muestra_por_encima_de_lo_recibido_en_correccion_es_400(
    auth_headers, client
):
    alta = await _alta_recepcion(client, auth_headers, sample_size=10)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "sample_size", str(AVES_RECIBIDAS + 1))
    assert r.status_code == 400, r.text
    assert "La muestra tomada no puede superar las aves recibidas" in r.json()["detail"]
    assert (await _detalle(client, auth_headers, eid))["sample_size"] == 10


@pytest.mark.asyncio
async def test_corr_s2_04_muestra_valida_en_correccion_se_aplica(auth_headers, client):
    alta = await _alta_recepcion(client, auth_headers, sample_size=10)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "sample_size", str(AVES_RECIBIDAS))
    assert r.status_code in (200, 201), r.text
    assert (await _detalle(client, auth_headers, eid))["sample_size"] == AVES_RECIBIDAS


@pytest.mark.asyncio
async def test_corr_s2_04_vaciar_la_muestra_se_aplica_y_queda_en_el_registro(
    auth_headers, client
):
    """`RR-01`: la muestra es un dato anulable; vaciarla deja el registro sin muestra."""
    alta = await _alta_recepcion(client, auth_headers, sample_size=10)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "sample_size", "")
    assert r.status_code in (200, 201), r.text
    assert r.json()["original_value"] == "10"
    assert not r.json()["corrected_value"], "el registro guarda el valor corregido (vacío)"
    assert (await _detalle(client, auth_headers, eid))["sample_size"] is None


# ── CORR-S2-06 · la fecha del evento no se vacía ─────────────────────────────

@pytest.mark.asyncio
async def test_corr_s2_06_vaciar_la_fecha_del_evento_es_400_y_no_cambia_nada(
    auth_headers, client
):
    alta = await _alta_recepcion(client, auth_headers)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]
    antes = await _detalle(client, auth_headers, eid)

    r = await _corregir(client, auth_headers, eid, "event_date", "")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "La fecha del evento no puede quedar vacía"
    _sin_codigo_interno(r.json()["detail"])

    despues = await _detalle(client, auth_headers, eid)
    assert despues["event_date"] == antes["event_date"], "un rechazo no cambia el dato"
    assert despues["status"] == antes["status"], "un rechazo no cambia el estado"


# ── CORR-S2-07 · los campos anulables sí se vacían ───────────────────────────

@pytest.mark.asyncio
async def test_corr_s2_07_vaciar_las_observaciones_es_aceptado(auth_headers, client):
    alta = await _alta_recepcion(client, auth_headers, observations="Llegó con retraso")
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "observations", "")
    assert r.status_code in (200, 201), r.text
    assert (await _detalle(client, auth_headers, eid))["observations"] in (None, "")


@pytest.mark.asyncio
async def test_corr_s2_07_vaciar_el_peso_medio_de_una_fila_es_aceptado(auth_headers, client):
    """El peso medio de una fila de recepción es un dato opcional: vaciarlo es válido."""
    alta = await _alta_recepcion(client, auth_headers)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]
    fila = await _fila_de(client, auth_headers, eid, ".avg_weight")

    r = await _corregir(client, auth_headers, eid, fila["field_name"], "")
    assert r.status_code in (200, 201), r.text
    detalle = await _detalle(client, auth_headers, eid)
    assert detalle["bird_movements"][0]["avg_weight"] is None


# ── OPS-S2-DOSIS · dosis, días de tratamiento y pollitos ─────────────────────

@pytest.mark.asyncio
async def test_ops_s2_dosis_dosis_negativa_en_el_alta_es_400(auth_headers, client):
    r = await _alta_medicacion(client, auth_headers, dosage_per_bird=-0.5)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "La dosis por ave no puede ser negativa"
    _sin_codigo_interno(r.json()["detail"])


@pytest.mark.asyncio
async def test_ops_s2_dosis_dias_de_tratamiento_negativos_en_el_alta_es_400(auth_headers, client):
    r = await _alta_medicacion(client, auth_headers, dosage_per_bird=0.5, treatment_days=-2)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Los días de tratamiento no pueden ser negativos"
    _sin_codigo_interno(r.json()["detail"])


@pytest.mark.asyncio
async def test_ops_s2_dosis_cero_en_el_alta_esta_permitido(auth_headers, client):
    """`0` es un valor declarado, no una ausencia: no es negativo."""
    r = await _alta_medicacion(client, auth_headers, dosage_per_bird=0, treatment_days=0)
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_ops_s2_dosis_dosis_negativa_en_la_edicion_es_400(auth_headers, client):
    alta = await _alta_medicacion(client, auth_headers, dosage_per_bird=0.5, treatment_days=3)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                         json={"dosage_per_bird": -0.5})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "La dosis por ave no puede ser negativa"
    assert (await _detalle(client, auth_headers, eid))["dosage_per_bird"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_ops_s2_dosis_dias_negativos_en_la_edicion_es_400(auth_headers, client):
    alta = await _alta_medicacion(client, auth_headers, dosage_per_bird=0.5, treatment_days=3)
    assert alta.status_code == 201, alta.text

    r = await client.put(f"/api/v1/operations/{alta.json()['id']}", headers=auth_headers,
                         json={"treatment_days": -2})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Los días de tratamiento no pueden ser negativos"


@pytest.mark.asyncio
async def test_ops_s2_dosis_cero_en_la_edicion_esta_permitido(auth_headers, client):
    alta = await _alta_medicacion(client, auth_headers, dosage_per_bird=0.5, treatment_days=3)
    assert alta.status_code == 201, alta.text

    r = await client.put(f"/api/v1/operations/{alta.json()['id']}", headers=auth_headers,
                         json={"dosage_per_bird": 0, "treatment_days": 0})
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_ops_s2_dosis_dosis_negativa_en_la_correccion_es_400(auth_headers, client):
    alta = await _alta_medicacion(client, auth_headers, dosage_per_bird=0.5)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "dosage_per_bird", "-0.5")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "La dosis por ave no puede ser negativa"
    assert (await _detalle(client, auth_headers, eid))["dosage_per_bird"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_ops_s2_dosis_dias_negativos_en_la_correccion_es_400(auth_headers, client):
    alta = await _alta_medicacion(client, auth_headers, dosage_per_bird=0.5, treatment_days=3)
    assert alta.status_code == 201, alta.text

    r = await _corregir(client, auth_headers, alta.json()["id"], "treatment_days", "-1")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Los días de tratamiento no pueden ser negativos"


@pytest.mark.asyncio
async def test_ops_s2_dosis_cero_en_la_correccion_esta_permitido(auth_headers, client):
    alta = await _alta_medicacion(client, auth_headers, dosage_per_bird=0.5, treatment_days=3)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "dosage_per_bird", "0")
    assert r.status_code in (200, 201), r.text
    assert (await _detalle(client, auth_headers, eid))["dosage_per_bird"] == 0


@pytest.mark.asyncio
async def test_ops_s2_dosis_pollitos_sanos_negativos_en_la_correccion_es_400(
    auth_headers, client
):
    alta = await _alta_nacimiento(client, auth_headers)
    assert alta.status_code == 201, alta.text
    eid = alta.json()["id"]

    r = await _corregir(client, auth_headers, eid, "chicks_healthy", "-5")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Los pollitos sanos no pueden ser negativos"
    _sin_codigo_interno(r.json()["detail"])
    assert (await _detalle(client, auth_headers, eid))["chicks_healthy"] == 100
