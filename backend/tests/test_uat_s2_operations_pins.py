"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020` — pines del contrato **vigente** de operaciones.

A diferencia de los contratos de rechazo (`RR-20`..`RR-23`, `RR-25`, `BR-01`, `BR-08`), aquí no se
fija lo que el producto *debe* hacer sino lo que **hoy** hace en los puntos donde el contenido
mínimo aún no está decidido: la inspección sin parámetros, la distribución sin aves, el pesaje sin
semana, la vacunación sin lote de vacuna, la mortalidad y el desecho sin causa ni semana, la
recepción de reproductoras sin datos opcionales de origen. Cada caso lleva en su docstring el ID y
la decisión (`OD-S2-0x`) o el hallazgo (`S2-D1`) que fija, de modo que si el producto cambia el
test falla y obliga a revisar la decisión de forma consciente.

Los datos reutilizan el lote sembrado (`lot_id=2`, `farm_id=1`, `house_id=1`) y, cuando el caso
necesita otro tipo de ave, el helper de lote de `test_uat_s2_write_contract.py`.
"""

from __future__ import annotations

import pytest

from tests.test_uat_s2_write_contract import AVES_RECIBIDAS, _alta_recepcion, _lote
from tests.time_reference import recent_event_date

#: Lote sembrado por la fixture de la suite (`conftest.py`).
LOTE = 2
FARM = 1
HOUSE = 1


def _cuerpo(event_type: str, **extra) -> dict:
    cuerpo = {"lot_id": LOTE, "event_type": event_type, "event_date": recent_event_date()}
    cuerpo.update(extra)
    return cuerpo


async def _alta(client, headers, event_type: str, **extra):
    return await client.post("/api/v1/operations", headers=headers,
                             json=_cuerpo(event_type, **extra))


async def _alta_ubicacion(client, headers, event_type: str, **extra):
    """Alta de un evento que se ancla a la ubicación: granja y galpón en el cuerpo."""
    cuerpo = {
        "lot_id": LOTE, "farm_id": FARM, "house_id": HOUSE,
        "event_type": event_type, "event_date": recent_event_date(),
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


async def _lote_con_aves(client, headers, aves: int = 50) -> int:
    """Un lote nuevo **con aves dentro**: el saldo del lote sembrado es cero.

    Una salida (mortalidad, desecho) se mide contra el saldo de aves disponibles, así que el
    caso necesita una recepción previa que lo alimente.
    """
    lote = await _lote(client, headers)
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote, "farm_id": FARM, "house_id": HOUSE,
        "event_type": "bird_reception", "event_date": recent_event_date(),
        "received_total": aves, "dead_on_arrival": 0, "rejected_on_arrival": 0,
        "bird_movements": [{"sex": "mixed", "quantity": aves}],
    })
    assert r.status_code == 201, r.text
    return lote


# ── OPS-S2-01 · inspección de granja con parámetro observado ─────────────────

@pytest.mark.asyncio
async def test_ops_s2_01_inspeccion_con_parametro_es_201(auth_headers, client):
    """`OPS-S2-01`: una inspección de granja y galpón con un parámetro observado entra con `201`.

    Fija la forma aceptada del alta de `farm_inspection`: ubicación en el cuerpo y una fila de
    detalle por parámetro observado.
    """
    r = await _alta_ubicacion(client, auth_headers, "farm_inspection",
                              inspection_details=[{"parameter": "temperatura", "value": "ok"}])
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert len(det.json()["inspection_details"]) == 1


# ── OPS-S2-02 · el contenido mínimo de la inspección está pendiente (OD-S2-02)

@pytest.mark.asyncio
async def test_ops_s2_02_inspeccion_sin_parametros_es_201(auth_headers, client):
    """`OPS-S2-02`: una inspección **sin** parámetros entra hoy con `201`.

    Pin de `OD-S2-02`: el contenido mínimo de la inspección está pendiente de decisión de la
    Owner. Este test cambiará **solo** con esa decisión: si aparece una regla «no vacío» para
    `inspection_details`, aquí llegará el `400` y habrá que actualizar el pin a conciencia.
    """
    r = await _alta_ubicacion(client, auth_headers, "farm_inspection")
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert not det.json()["inspection_details"]


@pytest.mark.asyncio
async def test_ops_s2_02_inspeccion_sin_galpon_es_400(auth_headers, client):
    """`OPS-S2-02` / `BR-08`: una inspección sin galpón es un registro sin ubicación: `400`."""
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": LOTE, "farm_id": FARM, "event_type": "farm_inspection",
        "event_date": recent_event_date(),
        "inspection_details": [{"parameter": "temperatura", "value": "ok"}],
    })
    assert r.status_code == 400, r.text
    assert r.json()["detail"], "el rechazo debe explicar qué falta"


# ── OPS-S2-03 · la recepción de reproductoras sin datos de origen (S2-D1) ────

@pytest.mark.asyncio
async def test_ops_s2_03_recepcion_sin_proveedor_ni_raza_es_201(auth_headers, client):
    """`OPS-S2-03`: recepción de reproductoras con el cuadre de `BR-20` y **sin** datos opcionales.

    Pin del hallazgo `S2-D1`: `supplier_id`, la línea/raza y el peso promedio de llegada son
    opcionales; el único dato que el contrato exige es que el cuadre cierre.
    """
    r = await _alta_recepcion(client, auth_headers)
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    cuerpo = det.json()
    assert cuerpo["supplier_id"] is None
    assert cuerpo["received_total"] == AVES_RECIBIDAS


# ── OPS-S2-05 · la distribución sin filas con cantidad está pendiente (OD-S2-03)

@pytest.mark.asyncio
async def test_ops_s2_05_distribucion_sin_aves_es_201(auth_headers, client):
    """`OPS-S2-05`: una distribución sin ninguna fila con cantidad entra hoy con `201`.

    Pin de `OD-S2-03`: la regla «la suma de las aves distribuidas debe ser mayor que cero» está
    pendiente de decisión de la Owner. Mover el lote sin mover aves no describe nada, pero el
    producto aún lo acepta.
    """
    r = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[])
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert not det.json()["bird_movements"]


# ── OPS-S2-06 · el alimento sin tipo, fase ni semana ─────────────────────────

@pytest.mark.asyncio
async def test_ops_s2_06_alimento_sin_tipo_ni_fase_ni_semana_es_201(auth_headers, client):
    """`OPS-S2-06`: una fila de kilos sin tipo de alimento, fase ni semana entra con `201`.

    El único dato mínimo del alimento es la cantidad (`RR-23`); tipo, fase y semana se pueden
    completar después.
    """
    r = await _alta(client, auth_headers, "feed_registration",
                    feed_movements=[{"quantity_kg": 12.5}])
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert det.json()["feed_movements"][0]["quantity_kg"] == pytest.approx(12.5)


@pytest.mark.asyncio
async def test_ops_s2_06_alimento_sin_kilos_es_400(auth_headers, client):
    """`OPS-S2-06` / `RR-23`: el alimento sin ninguna fila de kilos es `400`."""
    r = await _alta(client, auth_headers, "feed_registration")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-23"


# ── OPS-S2-07 · el pesaje sin semana está pendiente (OD-S2-04) ───────────────

@pytest.mark.asyncio
async def test_ops_s2_07_pesaje_sin_semana_es_201(auth_headers, client):
    """`OPS-S2-07`: un pesaje con peso y cantidad, pero **sin** semana, entra con `201`.

    Pin de `OD-S2-04`: la semana de vida no es dato obligatorio del pesaje; se puede derivar o
    quedar vacía hasta que la Owner decida.
    """
    r = await _alta(client, auth_headers, "weight_recording",
                    bird_movements=[{"sex": "male", "quantity": 10, "avg_weight": 2.1}])
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    fila = det.json()["bird_movements"][0]
    assert fila["avg_weight"] == pytest.approx(2.1)
    assert fila["week_number"] is None


@pytest.mark.asyncio
async def test_ops_s2_07_pesaje_sin_peso_es_400(auth_headers, client):
    """`OPS-S2-07` / `RR-20`: el pesaje sin peso promedio es `400`."""
    r = await _alta(client, auth_headers, "weight_recording")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-20"


# ── OPS-S2-08 · la vacunación sin lote de vacuna está pendiente (OD-S2-05) ───

@pytest.mark.asyncio
async def test_ops_s2_08_vacunacion_sin_lote_de_vacuna_es_201(auth_headers, client):
    """`OPS-S2-08`: la vacunación con vacuna pero **sin** número de lote entra con `201`.

    Pin de `OD-S2-05`: el lote de la vacuna es trazabilidad deseable, no dato mínimo; la regla
    «no vacío» solo alcanza a la vacuna aplicada (`RR-21`).
    """
    r = await _alta(client, auth_headers, "vaccination", vaccine_id=1, vaccination_route="water")
    assert r.status_code == 201, r.text
    assert r.json()["vaccine_lot_number"] is None


@pytest.mark.asyncio
async def test_ops_s2_08_vacunacion_sin_vacuna_es_400(auth_headers, client):
    """`OPS-S2-08` / `RR-21`: la vacunación sin vacuna aplicada es `400`."""
    r = await _alta(client, auth_headers, "vaccination", vaccination_route="water")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-21"


# ── OPS-S2-09 · la mortalidad sin causa ni semana (OD-S2-06 / OD-S2-04) ──────

@pytest.mark.asyncio
async def test_ops_s2_09_mortalidad_sin_causa_ni_semana_es_201(auth_headers, client):
    """`OPS-S2-09`: una baja con cantidad, **sin** causa ni semana, entra con `201`.

    Pines de `OD-S2-06` (la causa de la muerte no es obligatoria) y `OD-S2-04` (la semana se
    puede derivar). La cantidad se mantiene dentro del saldo del lote.
    """
    lote = await _lote_con_aves(client, auth_headers)
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "mortality_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    })
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert det.json()["cause_id"] is None


@pytest.mark.asyncio
async def test_ops_s2_09_mortalidad_sin_cantidad_es_400(auth_headers, client):
    """`OPS-S2-09` / `BR-01`: la mortalidad sin ninguna cantidad es `400`."""
    r = await _alta(client, auth_headers, "mortality_recording")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "BR-01"


# ── OPS-S2-10 · el desecho sin causa ni semana (OD-S2-06 / OD-S2-04) ────────

@pytest.mark.asyncio
async def test_ops_s2_10_desecho_sin_causa_ni_semana_es_201(auth_headers, client):
    """`OPS-S2-10`: un desecho con cantidad, **sin** causa ni semana, entra con `201`.

    Misma decisión que la mortalidad (`OD-S2-06`, `OD-S2-04`) sobre la otra salida de aves del
    lote: la cantidad es el dato mínimo, la causa se puede completar después.
    """
    lote = await _lote_con_aves(client, auth_headers)
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "cull_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    })
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert det.json()["cull_cause_id"] is None


@pytest.mark.asyncio
async def test_ops_s2_10_desecho_sin_cantidad_es_400(auth_headers, client):
    """`OPS-S2-10` / `BR-01`: el desecho sin ninguna cantidad es `400`."""
    r = await _alta(client, auth_headers, "cull_recording")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "BR-01"


# ── OPS-S2-11 · el techo de la muestra de una recepción de engorde (RR-25) ──

async def _alta_recepcion_engorde(client, headers, aves: int, **extra):
    """Recepción de pollo de engorde sin total recibido: la población son las aves alojadas."""
    lote = await _lote(client, headers, bird_type="broiler")
    cuerpo = {
        "lot_id": lote, "farm_id": FARM, "house_id": HOUSE,
        "event_type": "bird_reception", "event_date": recent_event_date(),
        "dead_on_arrival": 0,
        "bird_movements": [{"sex": "mixed", "quantity": aves}],
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


@pytest.mark.asyncio
async def test_ops_s2_11_muestra_mayor_que_lo_alojado_es_400(auth_headers, client):
    """`OPS-S2-11` / `RR-25`: sin total recibido, el techo de la muestra son las aves alojadas.

    Una muestra mayor que las aves que entraron al galpón (más las muertas al arribo) no describe
    una muestra tomada: `400`.
    """
    aves = 100
    r = await _alta_recepcion_engorde(client, auth_headers, aves, sample_size=aves + 1)
    assert r.status_code == 400, r.text
    assert "muestra" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ops_s2_11_muestra_igual_a_lo_alojado_es_201(auth_headers, client):
    """`OPS-S2-11` / `RR-25`: la muestra igual a la población alojada es aceptada (`201`).

    El límite es inclusivo igual que en la recepción de reproductoras.
    """
    aves = 100
    r = await _alta_recepcion_engorde(client, auth_headers, aves, sample_size=aves)
    assert r.status_code == 201, r.text
    assert r.json()["sample_size"] == aves
