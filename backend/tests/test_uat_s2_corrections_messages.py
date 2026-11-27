"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020 §3.3` — los mensajes de error de una corrección.

Cuando una corrección llega con un valor imposible, el rechazo se explica con el nombre que el
operador lee en el formulario —«Peso promedio», «Semana», «Cantidad de alimento (kg)», «Tamaño de
muestra», «Fecha del evento»— y no con el identificador técnico del campo: el aviso se muestra en
pantalla, junto al dato que se está corrigiendo. Y una corrección no puede mudar un evento de
empresa a través de un maestro ajeno: el evento conserva el proveedor que tenía.

Trazabilidad: `spec 020 (AC-S2-C06..C07)` · casos `CORR-S2-05, 10`.
"""

from __future__ import annotations

import uuid

import pytest

from tests.owner_decisions_support import fase_vigente_del_lote, tipo_de_alimento
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


async def _token_de_otra_empresa(client, headers, company_id: int) -> dict:
    """Un token con el contexto de la otra empresa, emitido por el super admin."""
    r = await client.post("/api/v1/switch-company", headers=headers,
                          json={"company_id": company_id})
    assert r.status_code == 200, r.text
    datos = r.json()
    token = datos.get("access_token") or datos.get("token")
    assert token, f"switch-company no devolvió un token: {datos}"
    return {"Authorization": f"Bearer {token}"}


def _campo_de_fila(campos, sufijo: str) -> dict:
    """La fila del selector que corrige el campo `sufijo` de un submovimiento concreto."""
    for campo in campos:
        if campo["field_name"].endswith(sufijo) and campo.get("row_id") is not None:
            return campo
    raise AssertionError(
        f"el selector no ofrece la fila '{sufijo}': "
        f"{sorted(c['field_name'] for c in campos)}"
    )


def _campo_simple(campos, nombre: str) -> dict:
    """La entrada del selector para un campo propio del evento (no de una fila)."""
    for campo in campos:
        if campo["field_name"].endswith(nombre):
            return campo
    raise AssertionError(
        f"el selector no ofrece el campo '{nombre}': "
        f"{sorted(c['field_name'] for c in campos)}"
    )


async def _mensaje_de_rechazo(client, headers, event_id: int, campo: str, valor: str) -> str:
    """Corrige con un valor imposible y devuelve el mensaje del rechazo (400)."""
    r = await _corregir(client, headers, event_id, campo, valor)
    assert r.status_code == 400, (
        f"la corrección «{campo} = {valor}» debía rechazarse con 400 y respondió "
        f"{r.status_code}: {r.text}"
    )
    detalle = r.json().get("detail")
    assert isinstance(detalle, str) and detalle, (
        f"el rechazo no trae un mensaje legible para el operador: {r.text}"
    )
    return detalle


async def _recepcion_breeder(client, headers) -> dict:
    """Recepción de 100 reproductoras con el cuadre de `BR-20` y una muestra de la mitad."""
    r = await _alta_recepcion(client, headers, received_total=100, dead_on_arrival=0,
                              rejected_on_arrival=0, sample_size=50,
                              bird_movements=[{"sex": "mixed", "quantity": 100}])
    assert r.status_code == 201, r.text
    return r.json()


async def _evento_con_alimento(client, headers, cantidad_kg: float = 25.0) -> dict:
    lote = await _lote(client, headers)
    # `RR-34`: el alimento se registra sobre un lote con fase productiva vigente en la fecha del
    # evento, y `RR-33`: cada fila con kilos nombra su tipo de alimento.
    await fase_vigente_del_lote(client, headers, lote, recent_event_date())
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote, "event_type": "feed_registration", "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": cantidad_kg,
                            "feed_type_id": await tipo_de_alimento(client, headers)}],
    })
    assert r.status_code == 201, r.text
    return r.json()


# ── CORR-S2-05 · el mensaje habla el idioma del formulario ───────────────────

@pytest.mark.asyncio
async def test_corr_s2_05_a_el_peso_promedio_se_nombra_en_castellano(auth_headers, client):
    """CORR-S2-05a: un peso medio negativo se rechaza nombrando «Peso promedio»."""
    evento = await _recepcion_breeder(client, auth_headers)
    fila = _campo_de_fila(await _campos(client, auth_headers, evento["id"]), ".avg_weight")

    mensaje = await _mensaje_de_rechazo(client, auth_headers, evento["id"], fila["field_name"],
                                        "-100")

    assert "«Peso promedio»" in mensaje, mensaje
    assert "avg_weight" not in mensaje, mensaje
    assert "bird_movements[" not in mensaje, mensaje


@pytest.mark.asyncio
async def test_corr_s2_05_b_la_semana_se_nombra_en_castellano(auth_headers, client):
    """CORR-S2-05b: una semana negativa se rechaza nombrando «Semana»."""
    evento = await _recepcion_breeder(client, auth_headers)
    fila = _campo_de_fila(await _campos(client, auth_headers, evento["id"]), ".week_number")

    mensaje = await _mensaje_de_rechazo(client, auth_headers, evento["id"], fila["field_name"],
                                        "-1")

    assert "«Semana»" in mensaje, mensaje
    assert "week_number" not in mensaje, mensaje
    assert "bird_movements[" not in mensaje, mensaje


@pytest.mark.asyncio
async def test_corr_s2_05_c_la_cantidad_de_alimento_se_nombra_en_castellano(auth_headers, client):
    """CORR-S2-05c: cero kilos de alimento se rechazan nombrando «Cantidad de alimento (kg)»."""
    evento = await _evento_con_alimento(client, auth_headers)
    fila = _campo_de_fila(await _campos(client, auth_headers, evento["id"]), ".quantity_kg")

    mensaje = await _mensaje_de_rechazo(client, auth_headers, evento["id"], fila["field_name"],
                                        "0")

    assert "«Cantidad de alimento (kg)»" in mensaje, mensaje
    assert "quantity_kg" not in mensaje, mensaje
    assert "feed_movements[" not in mensaje, mensaje


@pytest.mark.asyncio
async def test_corr_s2_05_d_el_tamano_de_muestra_se_nombra_en_castellano(auth_headers, client):
    """CORR-S2-05d: una muestra no numérica se rechaza nombrando «Tamaño de muestra»."""
    evento = await _recepcion_breeder(client, auth_headers)
    campo = _campo_simple(await _campos(client, auth_headers, evento["id"]), "sample_size")

    mensaje = await _mensaje_de_rechazo(client, auth_headers, evento["id"],
                                        campo["field_name"], "abc")

    assert "«Tamaño de muestra»" in mensaje, mensaje
    assert "sample_size" not in mensaje, mensaje


@pytest.mark.asyncio
async def test_corr_s2_05_e_la_fecha_del_evento_se_nombra_en_castellano(auth_headers, client):
    """CORR-S2-05e: una fecha ilegible se rechaza nombrando «Fecha del evento»."""
    evento = await _recepcion_breeder(client, auth_headers)
    campo = _campo_simple(await _campos(client, auth_headers, evento["id"]), "event_date")

    mensaje = await _mensaje_de_rechazo(client, auth_headers, evento["id"],
                                        campo["field_name"], "xx")

    assert "«Fecha del evento»" in mensaje, mensaje
    assert "event_date" not in mensaje, mensaje


# ── CORR-S2-10 · un maestro de otra empresa no mueve el evento ───────────────

@pytest.mark.asyncio
async def test_corr_s2_10_no_se_puede_mudar_un_evento_a_un_proveedor_ajeno(
        auth_headers, client, seeded_ids):
    """CORR-S2-10: corregir el proveedor a uno de otra empresa se rechaza y no toca el evento."""
    propio_id, _ = await _proveedor(client, auth_headers)
    headers_ajenos = await _token_de_otra_empresa(client, auth_headers,
                                                  seeded_ids["company_id_2"])
    ajeno_id, _ = await _proveedor(client, headers_ajenos)
    assert ajeno_id != propio_id, (propio_id, ajeno_id)

    alta = await _alta_recepcion(client, auth_headers, supplier_id=propio_id)
    assert alta.status_code == 201, alta.text
    evento_id = alta.json()["id"]

    r = await _corregir(client, auth_headers, evento_id, "supplier_id", str(ajeno_id))
    assert r.status_code in (400, 404), (
        f"un proveedor de otra empresa debía ser inalcanzable y la API respondió "
        f"{r.status_code}: {r.text}"
    )

    evento = await _detalle(client, auth_headers, evento_id)
    assert evento.get("supplier_id") == propio_id, (
        f"el evento cambió de proveedor tras un rechazo: {evento}"
    )
