"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020 §6` — inspección con contenido (`RR-28`) y distribución con aves (`RR-29`).

Dos de las siete decisiones ratificadas el 25-11-2026: una inspección de granja no se guarda
completamente vacía (`OD-S2-02`) y una distribución de aves describe una distribución física real
(`OD-S2-03`). Las reglas viven en las rutas de escritura —alta, `PUT` y corrección—, no en los
esquemas de lectura, de modo que los históricos incompletos siguen leyéndose.

Casos: `OD02-01..06` y `OD03-01..07`.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tests.test_uat_s2_operations_pins import _alta_ubicacion
from tests.test_uat_s2_owner_decisions_a import (
    _corregir, _detalle, _evento_historico, _tipo_de_correccion,
)
from tests.time_reference import days_ago, recent_event_date

MENSAJE_INSPECCION = "Registre al menos un dato de la inspección: un valor, una observación o una evidencia"
MENSAJE_SIN_MOVIMIENTOS = "Registre la distribución de aves por galpón o sexo (al menos un movimiento)"
MENSAJE_EN_CERO = "La distribución debe incluir al menos un ave (la suma no puede ser cero)"

LOTE = 2


async def _inspeccion(client, headers, **extra):
    return await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": LOTE, "farm_id": 1, "house_id": 1, "event_type": "farm_inspection",
        "event_date": recent_event_date(),
        **extra,
    })


async def _evidencia_por_modelo(url: str, event_id: int, company_id: int, user_id: int) -> None:
    """Adjunta una evidencia al evento (la API la sube después del alta, con un archivo real)."""
    import app.operations.models  # noqa: F401
    from app.operations.models import Evidence

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as sesion:
            sesion.add(Evidence(event_id=event_id, company_id=company_id, file_name="foto.jpg",
                                file_path="evidences/foto.jpg", evidence_type="photo",
                                uploaded_by_id=user_id))
            await sesion.commit()
    finally:
        await motor.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  OD02 · `RR-28` — la inspección tiene contenido
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_od02_01_inspeccion_completamente_vacia_es_400(auth_headers, client):
    """`OD02-01` · `RR-28`: sin detalles, sin observaciones y sin evidencia no hay inspección."""
    r = await _inspeccion(client, auth_headers)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_INSPECCION, r.json()
    assert r.json()["rule"] == "RR-28", r.json()


@pytest.mark.asyncio
async def test_od02_01b_un_detalle_sin_valor_ni_estado_no_es_contenido(auth_headers, client):
    """`OD02-01` · `RR-28`: el nombre del parámetro solo dice qué se observó; sin valor no cuenta."""
    r = await _inspeccion(client, auth_headers, inspection_details=[
        {"parameter": "temperatura"}, {"parameter": "humedad", "value": "   "}])
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-28", r.json()


@pytest.mark.asyncio
async def test_od02_02_solo_un_valor_numerico_es_201(auth_headers, client):
    """`OD02-02`: la temperatura sola es contenido."""
    r = await _inspeccion(client, auth_headers, inspection_details=[
        {"parameter": "temperatura", "value_numeric": 27.5}])
    assert r.status_code == 201, r.text

    solo_estado = await _inspeccion(client, auth_headers, inspection_details=[
        {"parameter": "litter_condition", "status": "good"}])
    assert solo_estado.status_code == 201, solo_estado.text


@pytest.mark.asyncio
async def test_od02_03_solo_observacion_sustantiva_es_201_y_con_espacios_es_400(auth_headers, client):
    """`OD02-03`: una observación con texto basta; una de espacios no es texto."""
    r = await _inspeccion(client, auth_headers, observations="Cama húmeda en la zona del bebedero")
    assert r.status_code == 201, r.text

    vacia = await _inspeccion(client, auth_headers, observations="    ")
    assert vacia.status_code == 400, vacia.text
    assert vacia.json()["rule"] == "RR-28", vacia.json()


@pytest.mark.asyncio
async def test_od02_04_la_evidencia_ya_adjunta_cuenta_al_corregir(
        auth_headers, client, seeded_ids, test_database_url):
    """`OD02-04`: con una evidencia adjunta, dejar las observaciones vacías ya no vacía la inspección.

    La evidencia se adjunta con posterioridad al alta, así que solo puede contar al evaluar una
    corrección o una edición del evento que ya la tiene.
    """
    alta = await _inspeccion(client, auth_headers, observations="Inspección con foto")
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]
    tipo = await _tipo_de_correccion(client, auth_headers)

    sin_evidencia = await _corregir(client, auth_headers, event_id, "observations", "", tipo=tipo)
    assert sin_evidencia.status_code == 400, sin_evidencia.text
    assert sin_evidencia.json()["rule"] == "RR-28", sin_evidencia.json()

    await _evidencia_por_modelo(test_database_url, event_id, seeded_ids["company_id"],
                                seeded_ids["user_admin_id"])
    con_evidencia = await _corregir(client, auth_headers, event_id, "observations", "", tipo=tipo)
    assert con_evidencia.status_code == 201, con_evidencia.text


@pytest.mark.asyncio
async def test_od02_05_inspeccion_de_granja_sin_lote_con_contenido_es_201(auth_headers, client):
    """`OD02-05`: sin lote (nivel granja) sigue permitida cuando tiene contenido."""
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "farm_id": 1, "house_id": 1, "event_type": "farm_inspection",
        "event_date": recent_event_date(),
        "inspection_details": [{"parameter": "temperatura", "value_numeric": 26}],
    })
    assert r.status_code == 201, r.text
    # La respuesta del alta ya dice que el evento es de granja; el `GET` de detalle aplica el
    # alcance por lote y no devuelve eventos sin lote, así que no se usa aquí.
    assert r.json()["lot_id"] is None


@pytest.mark.asyncio
async def test_od02_06_corregir_las_observaciones_a_vacio_sin_otro_contenido_es_400(auth_headers, client):
    """`OD02-06` · `RR-28`: la corrección tampoco deja la inspección vacía."""
    alta = await _inspeccion(client, auth_headers, observations="Único contenido")
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]
    tipo = await _tipo_de_correccion(client, auth_headers)

    r = await _corregir(client, auth_headers, event_id, "observations", "   ", tipo=tipo)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_INSPECCION, r.json()
    assert (await _detalle(client, auth_headers, event_id))["observations"] == "Único contenido"


@pytest.mark.asyncio
async def test_od02_07_la_edicion_no_deja_la_inspeccion_vacia(auth_headers, client):
    """`OD02-07` · `RR-28`: tampoco por `PUT`."""
    alta = await _inspeccion(client, auth_headers, observations="Único contenido")
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]

    r = await client.put(f"/api/v1/operations/{event_id}", headers=auth_headers,
                         json={"observations": ""})
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-28", r.json()


@pytest.mark.asyncio
async def test_od02_08_inspeccion_historica_vacia_es_legible(
        auth_headers, client, seeded_ids, test_database_url):
    """`OD02-08`: el histórico sin contenido sigue leyéndose."""
    from app.operations.models import EventStatus, EventType

    event_id = await _evento_historico(
        test_database_url, company_id=seeded_ids["company_id"], lot_id=LOTE, farm_id=1, house_id=1,
        event_type=EventType.FARM_INSPECTION, event_date=days_ago(7), status=EventStatus.REGISTERED,
        version=1, registered_by_id=seeded_ids["user_admin_id"])
    detalle = await _detalle(client, auth_headers, event_id)
    assert detalle["inspection_details"] == [] and not detalle["observations"]


# ══════════════════════════════════════════════════════════════════════════════
#  OD03 · `RR-29` — la distribución mueve aves
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_od03_01_distribucion_sin_movimientos_es_400(auth_headers, client):
    """`OD03-01` · `RR-29`."""
    r = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[])
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_SIN_MOVIMIENTOS, r.json()
    assert r.json()["rule"] == "RR-29", r.json()


@pytest.mark.asyncio
async def test_od03_02_distribucion_con_suma_cero_es_400(auth_headers, client):
    """`OD03-02` · `RR-29`: una fila con cero aves no es un movimiento."""
    r = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[
        {"sex": "male", "quantity": 0}, {"sex": "female", "quantity": 0}])
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_EN_CERO, r.json()
    assert r.json()["rule"] == "RR-29", r.json()


@pytest.mark.asyncio
async def test_od03_03_cantidad_negativa_es_rechazada(auth_headers, client):
    """`OD03-03`: una cantidad negativa nunca entra (el esquema la rechaza antes de la regla)."""
    r = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[
        {"sex": "male", "quantity": -5}])
    assert r.status_code in (400, 422), r.text


@pytest.mark.asyncio
async def test_od03_04_distribucion_positiva_valida_es_201(auth_headers, client):
    """`OD03-04`."""
    r = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[
        {"sex": "male", "quantity": 40}, {"sex": "female", "quantity": 0}])
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_od03_05_la_capacidad_del_galpon_sigue_rigiendo(auth_headers, client):
    """`OD03-05`: exceder la capacidad del galpón sigue siendo `400 BR-17` (la regla existente)."""
    r = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[
        {"sex": "male", "quantity": 900000}])
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "BR-17", r.json()


@pytest.mark.asyncio
async def test_od03_06_corregir_la_unica_cantidad_a_cero_es_400(auth_headers, client):
    """`OD03-06` · `RR-29`: la corrección no deja la distribución en cero."""
    alta = await _alta_ubicacion(client, auth_headers, "bird_distribution", bird_movements=[
        {"sex": "male", "quantity": 40}])
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]
    campos = await client.get(f"/api/v1/corrections/events/{event_id}/correctable-fields",
                              headers=auth_headers)
    assert campos.status_code == 200, campos.text
    fila_id = next(c["row_id"] for c in campos.json()
                   if c["field_name"].endswith(".quantity") and c["row_id"] is not None)
    tipo = await _tipo_de_correccion(client, auth_headers)

    r = await _corregir(client, auth_headers, event_id, f"bird_movements[{fila_id}].quantity", "0", tipo=tipo)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_EN_CERO, r.json()
    assert r.json()["rule"] == "RR-29", r.json()
    assert (await _detalle(client, auth_headers, event_id))["bird_movements"][0]["quantity"] == 40

    valida = await _corregir(client, auth_headers, event_id, f"bird_movements[{fila_id}].quantity", "35", tipo=tipo)
    assert valida.status_code == 201, valida.text


@pytest.mark.asyncio
async def test_od03_07_distribucion_historica_con_suma_cero_es_legible(
        auth_headers, client, seeded_ids, test_database_url):
    """`OD03-07`: el histórico sin aves sigue leyéndose."""
    from app.operations.models import EventStatus, EventType

    event_id = await _evento_historico(
        test_database_url, company_id=seeded_ids["company_id"], lot_id=LOTE, farm_id=1, house_id=1,
        event_type=EventType.BIRD_DISTRIBUTION, event_date=days_ago(7), status=EventStatus.REGISTERED,
        version=1, registered_by_id=seeded_ids["user_admin_id"])
    assert (await _detalle(client, auth_headers, event_id))["bird_movements"] == []
