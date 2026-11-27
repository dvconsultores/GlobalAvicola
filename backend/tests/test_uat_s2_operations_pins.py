"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020` — pines del contrato **vigente** de operaciones.

A diferencia de los contratos de rechazo (`RR-20`..`RR-23`, `RR-25`, `BR-01`, `BR-08`), aquí no se
fija lo que el producto *debe* hacer sino lo que **hoy** hace en los puntos donde el contenido
mínimo aún no está decidido: la recepción de reproductoras sin datos opcionales de origen. Las
decisiones ratificadas por la Owner el 25-11-2026 ya son regla (`RR-28` la inspección con
contenido, `RR-29` la distribución con aves, `RR-30` la semana derivada de la edad del lote,
`RR-31` el lote de vacuna, `RR-32` la causa de la baja, `RR-33` el tipo de alimento y `RR-34` la
fase derivada del lote), así que sus pines fijan el rechazo y,
con el dato obligatorio presente, lo que **sigue** siendo opcional. Cada caso lleva en su docstring el ID y
la decisión (`OD-S2-0x`) o el hallazgo (`S2-D1`) que fija, de modo que si el producto cambia el
test falla y obliga a revisar la decisión de forma consciente.

Los datos reutilizan el lote sembrado (`lot_id=2`, `farm_id=1`, `house_id=1`) y, cuando el caso
necesita otro tipo de ave, el helper de lote de `test_uat_s2_write_contract.py`.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.operations.semana import semana_productiva
from tests.test_uat_s2_owner_decisions_a import _id_de_la_desconocida, _lista
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


async def _inicio_del_lote(client, headers, lote: int) -> date:
    """Fecha de inicio del lote, leída del propio lote: la base de la semana derivada."""
    r = await client.get(f"/api/v1/lots/{lote}", headers=headers)
    assert r.status_code == 200, r.text
    return date.fromisoformat(r.json()["start_date"][:10])


async def _semana_esperada(client, headers, lote: int, fecha: str) -> int:
    """`RR-30`: la semana que la regla deriva para el evento, según la edad del lote."""
    return semana_productiva(await _inicio_del_lote(client, headers, lote),
                             date.fromisoformat(fecha[:10]))


async def _fase(client, headers) -> int:
    """Una fase productiva válida del catálogo de la empresa (se crea si no hay)."""
    items = await _lista(client, headers, "productive-phases")
    if items:
        return items[0]["id"]
    r = await client.post("/api/v1/masters/productive-phases", headers=headers, json={
        "name": f"Fase PIN {uuid.uuid4().hex[:6]}", "code": f"PIN{uuid.uuid4().hex[:6].upper()}",
        "order": 90})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _tipo_de_alimento(client, headers) -> int:
    """Un tipo de alimento válido del catálogo de la empresa (se crea si no hay)."""
    items = await _lista(client, headers, "feed-types")
    if items:
        return items[0]["id"]
    r = await client.post("/api/v1/masters/feed-types", headers=headers, json={
        "name": f"Alimento PIN {uuid.uuid4().hex[:6]}", "code": f"AL{uuid.uuid4().hex[:6].upper()}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _lote_con_fase(client, headers) -> tuple[int, int]:
    """Lote nuevo con una fase productiva vigente desde su inicio (`RR-34`)."""
    lote = await _lote(client, headers)
    fase = await _fase(client, headers)
    r = await client.post(f"/api/v1/lots/{lote}/phases", headers=headers, json={
        "lot_id": lote, "phase_id": fase,
        "start_date": (await _inicio_del_lote(client, headers, lote)).isoformat()})
    assert r.status_code == 201, r.text
    return lote, fase


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


# ── OPS-S2-02 · la inspección completamente vacía (RR-28) ────────────────────

@pytest.mark.asyncio
async def test_ops_s2_02_inspeccion_sin_parametros_es_400(auth_headers, client):
    """`OPS-S2-02` · `RR-28`: ratificado por la Owner el 25-11-2026 (`OD-S2-02`), una inspección completamente vacía se rechaza"""
    r = await _alta_ubicacion(client, auth_headers, "farm_inspection")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-28"


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


# ── OPS-S2-05 · la distribución sin aves (RR-29) ────────────────────────────

@pytest.mark.asyncio
async def test_ops_s2_05_distribucion_sin_aves_es_400(auth_headers, client):
    """`OPS-S2-05` · `RR-29`: ratificado por la Owner el 25-11-2026 (`OD-S2-03`), una distribución completamente vacía se rechaza"""
    r = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[])
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-29"


# ── OPS-S2-06 · el alimento nombra su tipo (RR-33) y su fase es derivada (RR-34) ──

@pytest.mark.asyncio
async def test_ops_s2_06_alimento_sin_tipo_es_400(auth_headers, client):
    """`OPS-S2-06` · `RR-33`: ratificado por la Owner el 25-11-2026 (`OD-S2-07`), el alimento sin tipo se rechaza.

    El tipo de alimento es dato del operador; la fase la deriva el servidor de la fase vigente
    del lote (`RR-34`) y la semana, de la edad del lote (`RR-30`).
    """
    r = await _alta(client, auth_headers, "feed_registration",
                    feed_movements=[{"quantity_kg": 12.5}])
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-33"


@pytest.mark.asyncio
async def test_ops_s2_06_alimento_con_tipo_y_fase_vigente_es_201(auth_headers, client):
    """`OPS-S2-06` · `RR-33`/`RR-34`: con tipo de alimento y fase vigente en el lote, entra con `201`.

    Ni la fase ni la semana viajan en el cuerpo: el servidor deriva la fase de la fase vigente
    del lote en la fecha del evento y la semana de la edad del lote (`RR-30`).
    """
    lote, fase = await _lote_con_fase(client, auth_headers)
    tipo = await _tipo_de_alimento(client, auth_headers)
    fecha = recent_event_date()
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "feed_registration", "event_date": fecha,
        "feed_movements": [{"feed_type_id": tipo, "quantity_kg": 12.5}]})
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    fila = det.json()["feed_movements"][0]
    assert fila["quantity_kg"] == pytest.approx(12.5)
    assert fila["phase_id"] == fase
    assert fila["week_number"] == await _semana_esperada(client, auth_headers, lote, fecha)


@pytest.mark.asyncio
async def test_ops_s2_06_alimento_sin_kilos_es_400(auth_headers, client):
    """`OPS-S2-06` / `RR-23`: el alimento sin ninguna fila de kilos es `400`."""
    r = await _alta(client, auth_headers, "feed_registration")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-23"


# ── OPS-S2-07 · el pesaje sin semana: la semana se deriva (RR-30) ────────────

@pytest.mark.asyncio
async def test_ops_s2_07_pesaje_sin_semana_es_201(auth_headers, client):
    """`OPS-S2-07` · `RR-30`: ratificado por la Owner el 25-11-2026 (`OD-S2-04`), el pesaje sin semana entra con `201`.

    La semana deja de ser dato del cliente: el servidor la deriva de la edad del lote
    (`(fecha_evento − inicio_del_lote).days // 7 + 1`), así que llega rellena con el valor
    que la regla dicta para esa fecha.
    """
    fecha = recent_event_date()
    r = await _alta(client, auth_headers, "weight_recording",
                    bird_movements=[{"sex": "male", "quantity": 10, "avg_weight": 2.1}])
    assert r.status_code == 201, r.text
    det = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    fila = det.json()["bird_movements"][0]
    assert fila["avg_weight"] == pytest.approx(2.1)
    assert fila["week_number"] == await _semana_esperada(client, auth_headers, LOTE, fecha)


@pytest.mark.asyncio
async def test_ops_s2_07_pesaje_sin_peso_es_400(auth_headers, client):
    """`OPS-S2-07` / `RR-20`: el pesaje sin peso promedio es `400`."""
    r = await _alta(client, auth_headers, "weight_recording")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-20"


# ── OPS-S2-08 · la vacunación sin lote de vacuna (RR-31) ─────────────────────

@pytest.mark.asyncio
async def test_ops_s2_08_vacunacion_sin_lote_de_vacuna_es_400(auth_headers, client):
    """`OPS-S2-08` · `RR-31`: ratificado por la Owner el 25-11-2026 (`OD-S2-05`), la vacunación sin lote de vacuna se rechaza.

    Con el lote de vacuna presente, el alta entra; la semana la deriva el servidor (`RR-30`).
    """
    r = await _alta(client, auth_headers, "vaccination", vaccine_id=1, vaccination_route="water")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-31"

    valida = await _alta(client, auth_headers, "vaccination", vaccine_id=1, vaccination_route="water",
                         vaccine_lot_number="PIN-VAC-1")
    assert valida.status_code == 201, valida.text
    assert valida.json()["vaccine_lot_number"] == "PIN-VAC-1"


@pytest.mark.asyncio
async def test_ops_s2_08_vacunacion_sin_vacuna_es_400(auth_headers, client):
    """`OPS-S2-08` / `RR-21`: la vacunación sin vacuna aplicada es `400`."""
    r = await _alta(client, auth_headers, "vaccination", vaccination_route="water")
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-21"


# ── OPS-S2-09 · la mortalidad sin causa (RR-32) ─────────────────────────────

@pytest.mark.asyncio
async def test_ops_s2_09_mortalidad_sin_causa_es_400(auth_headers, client):
    """`OPS-S2-09` · `RR-32`: ratificado por la Owner el 25-11-2026 (`OD-S2-06`), la baja sin causa se rechaza.

    Con la causa presente (la compartida «Desconocida»), el alta entra y la semana la deriva el
    servidor de la edad del lote (`RR-30`). La cantidad se mantiene dentro del saldo del lote.
    """
    lote = await _lote_con_aves(client, auth_headers)
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "mortality_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    })
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-32"

    causa = await _id_de_la_desconocida(client, auth_headers, "mortality-causes")
    valida = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "mortality_recording",
        "event_date": recent_event_date(), "cause_id": causa,
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    })
    assert valida.status_code == 201, valida.text
    det = await client.get(f"/api/v1/operations/{valida.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert det.json()["cause_id"] == causa
    assert det.json()["bird_movements"][0]["week_number"] == await _semana_esperada(
        client, auth_headers, lote, recent_event_date())


@pytest.mark.asyncio
async def test_ops_s2_09_mortalidad_sin_cantidad_es_400(auth_headers, client):
    """`OPS-S2-09` / `BR-01`: la mortalidad sin ninguna cantidad es `400` (con la causa ya declarada)."""
    causa = await _id_de_la_desconocida(client, auth_headers, "mortality-causes")
    r = await _alta(client, auth_headers, "mortality_recording", cause_id=causa)
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "BR-01"


# ── OPS-S2-10 · el desecho sin causa (RR-32) ────────────────────────────────

@pytest.mark.asyncio
async def test_ops_s2_10_desecho_sin_causa_es_400(auth_headers, client):
    """`OPS-S2-10` · `RR-32`: ratificado por la Owner el 25-11-2026 (`OD-S2-06`), el desecho sin causa se rechaza.

    Con la causa presente (la compartida «Desconocida»), el alta entra y la semana la deriva el
    servidor de la edad del lote (`RR-30`).
    """
    lote = await _lote_con_aves(client, auth_headers)
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "cull_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    })
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-32"

    causa = await _id_de_la_desconocida(client, auth_headers, "cull-causes")
    valida = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "cull_recording",
        "event_date": recent_event_date(), "cull_cause_id": causa,
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    })
    assert valida.status_code == 201, valida.text
    det = await client.get(f"/api/v1/operations/{valida.json()['id']}", headers=auth_headers)
    assert det.status_code == 200, det.text
    assert det.json()["cull_cause_id"] == causa
    assert det.json()["bird_movements"][0]["week_number"] == await _semana_esperada(
        client, auth_headers, lote, recent_event_date())


@pytest.mark.asyncio
async def test_ops_s2_10_desecho_sin_cantidad_es_400(auth_headers, client):
    """`OPS-S2-10` / `BR-01`: el desecho sin ninguna cantidad es `400` (con la causa ya declarada)."""
    causa = await _id_de_la_desconocida(client, auth_headers, "cull-causes")
    r = await _alta(client, auth_headers, "cull_recording", cull_cause_id=causa)
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
