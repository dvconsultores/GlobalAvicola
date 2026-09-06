"""Observabilidad de la evaluación de curva — `GA-REM-037` enmienda A, hallazgo `R-97`.

Cubre `AC26`, `AC27` y `AC28`.

El motor de curva existía y funcionaba, pero tenía **un solo consumidor**: el generador de
alertas, que solo actúa cuando el peso queda fuera de rango. Desde fuera del backend,
«dentro de norma» y «sin referencia» se veían igual —ninguna alerta—, y una interfaz no
puede distinguir dos conclusiones opuestas por la ausencia de una señal.

Deducirlo en el cliente habría exigido interpolar allí, que es exactamente lo que crea un
segundo motor. Se expone lo que ya se calculaba.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago

PREFIJO = "WE-TEST-"

#: A los 15 días interpola a [135, 150, 165] exactamente.
TABLA = [
    {"age_days": 10, "min_weight": 90.0, "target_weight": 100.0, "max_weight": 110.0},
    {"age_days": 20, "min_weight": 180.0, "target_weight": 200.0, "max_weight": 220.0},
]
EDAD_LOTE = 30
DIAS_DEL_PESAJE = 15


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.masters.models import GeneticLine, GeneticWeightCurve, GeneticWeightCurvePoint
    from app.operations.models import BirdMovement, OperationalAlert, OperationalEvent

    async with e.begin() as c:
        lotes = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if lotes:
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(lotes)))).scalars().all()
            await c.execute(delete(OperationalAlert).where(OperationalAlert.lot_id.in_(lotes)))
            if eventos:
                await c.execute(delete(BirdMovement).where(BirdMovement.event_id.in_(eventos)))
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lotes)))
            await c.execute(delete(Lot).where(Lot.id.in_(lotes)))
        lineas = (await c.execute(
            select(GeneticLine.id).where(GeneticLine.name.like(f"{PREFIJO}%")))).scalars().all()
        if lineas:
            curvas = (await c.execute(select(GeneticWeightCurve.id).where(
                GeneticWeightCurve.genetic_line_id.in_(lineas)))).scalars().all()
            if curvas:
                await c.execute(delete(GeneticWeightCurvePoint).where(
                    GeneticWeightCurvePoint.curve_id.in_(curvas)))
                await c.execute(delete(GeneticWeightCurve).where(
                    GeneticWeightCurve.id.in_(curvas)))
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "geneticline",
                AuditLog.entity_id.in_([str(i) for i in lineas])))
            await c.execute(delete(GeneticLine).where(GeneticLine.id.in_(lineas)))
    await e.dispose()


async def _escenario(client, cab, seeded_ids, puntos=TABLA, con_linea=True):
    linea_id = None
    if con_linea:
        r = await client.post("/api/v1/masters/genetic-lines", headers=cab, json={
            "company_id": seeded_ids["company_id"], "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}"})
        assert r.status_code in (200, 201), r.text
        linea_id = r.json()["id"]
        if puntos is not None:
            c = await client.post("/api/v1/masters/weight-curves", headers=cab, json={
                "genetic_line_id": linea_id, "version_label": "v1",
                "is_active": True, "points": puntos})
            assert c.status_code == 201, c.text

    l = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
        "genetic_line_id": linea_id, "start_date": iso_days_ago(EDAD_LOTE),
    })
    assert l.status_code == 201, l.text
    return l.json()


async def _pesar(client, cab, lote, *pesos):
    r = await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": lote["id"], "farm_id": lote["farm_id"], "house_id": lote["house_id"],
        "event_type": "weight_recording", "event_date": iso_days_ago(DIAS_DEL_PESAJE),
        "bird_movements": [
            {"sex": "mixed", "quantity": 100, "avg_weight": p} for p in pesos
        ],
    })
    assert r.status_code == 201, r.text
    return r.json()


# ── AC26 — la evaluación es legible ───────────────────────────────────────────

@pytest.mark.parametrize("peso,estado", [
    (100.0, "below_standard"),
    (150.0, "within_standard"),
    (200.0, "above_standard"),
])
async def test_t_037_26_la_evaluacion_es_legible(
    client, auth_headers, seeded_ids, motor, peso, estado
):
    """`AC26` · estado, rango esperado y versión de curva, para los tres veredictos.

    El rango a los 15 días **no está en la tabla**: sale de interpolar 10 y 20. Que la
    lectura devuelva 135/165 demuestra que consultó el motor y no un valor guardado.
    """
    lote = await _escenario(client, auth_headers, seeded_ids)
    evento = await _pesar(client, auth_headers, lote, peso)

    r = await client.get(
        f"/api/v1/operations/{evento['id']}/weight-evaluation", headers=auth_headers)
    assert r.status_code == 200, r.text
    cuerpo = r.json()

    assert cuerpo["age_days"] == DIAS_DEL_PESAJE, cuerpo
    assert cuerpo["curve_version_label"] == "v1", cuerpo
    assert len(cuerpo["evaluations"]) == 1, cuerpo
    fila = cuerpo["evaluations"][0]
    assert fila["status"] == estado, fila
    assert fila["avg_weight"] == peso, fila
    assert (fila["expected_min"], fila["expected_target"], fila["expected_max"]) == (
        135.0, 150.0, 165.0), fila


async def test_t_037_27_una_evaluacion_por_pesaje(client, auth_headers, seeded_ids, motor):
    """`AC26` · un evento con varias muestras devuelve una conclusión por muestra."""
    lote = await _escenario(client, auth_headers, seeded_ids)
    evento = await _pesar(client, auth_headers, lote, 100.0, 150.0, 200.0)

    r = await client.get(
        f"/api/v1/operations/{evento['id']}/weight-evaluation", headers=auth_headers)
    assert r.status_code == 200, r.text
    estados = [f["status"] for f in r.json()["evaluations"]]
    assert estados == ["below_standard", "within_standard", "above_standard"], estados


async def test_t_037_28_el_motor_no_se_duplica(client, auth_headers, seeded_ids, motor):
    """`AC26` · la lectura y la alerta concuerdan, porque son el mismo cálculo.

    Si divergieran habría dos motores, que es el defecto que esta lectura evita.
    """
    lote = await _escenario(client, auth_headers, seeded_ids)
    evento = await _pesar(client, auth_headers, lote, 100.0)

    lectura = (await client.get(
        f"/api/v1/operations/{evento['id']}/weight-evaluation",
        headers=auth_headers)).json()["evaluations"][0]
    alertas = (await client.get(
        f"/api/v1/operations/alerts?lot_id={lote['id']}", headers=auth_headers)).json()

    assert len(alertas) == 1, alertas
    assert alertas[0]["threshold_value"] == lectura["expected_min"], (alertas[0], lectura)
    assert alertas[0]["actual_value"] == lectura["avg_weight"], (alertas[0], lectura)


# ── AC27 — «dentro de norma» ≠ «sin referencia» ───────────────────────────────

@pytest.mark.parametrize("puntos,con_linea,motivo", [
    (None, True, "no_curve_assigned"),
    (None, False, "lot_without_genetic_line"),
    ([{"age_days": 30, "min_weight": 400.0, "max_weight": 500.0},
      {"age_days": 40, "min_weight": 600.0, "max_weight": 700.0}], True,
     "age_outside_curve_table"),
])
async def test_t_037_29_sin_referencia_se_declara(
    client, auth_headers, seeded_ids, motor, puntos, con_linea, motivo
):
    """`AC27` · la ausencia de referencia se nombra; nunca se presenta como normalidad.

    Los tres caminos por los que puede faltar —sin curva, sin línea genética y con una edad
    que la tabla no cubre— devuelven `no_reference` **declarado**. Antes de esta lectura los
    tres eran indistinguibles de «el peso está bien».
    """
    lote = await _escenario(client, auth_headers, seeded_ids,
                            puntos=puntos, con_linea=con_linea)
    evento = await _pesar(client, auth_headers, lote, 50.0)

    r = await client.get(
        f"/api/v1/operations/{evento['id']}/weight-evaluation", headers=auth_headers)
    assert r.status_code == 200, r.text
    cuerpo = r.json()

    assert cuerpo["reason"] == motivo, cuerpo
    fila = cuerpo["evaluations"][0]
    assert fila["status"] == "no_reference", fila
    assert fila["status"] != "within_standard"
    # Ni cero ni ausencia: cero sería un rango de verdad y engañaría igual.
    assert fila["expected_min"] is None, fila
    assert fila["expected_max"] is None, fila


async def test_t_037_30_dentro_de_norma_no_es_sin_referencia(
    client, auth_headers, seeded_ids, motor
):
    """`AC27` · el caso que `R-97` hacía imposible distinguir, distinguido."""
    con = await _escenario(client, auth_headers, seeded_ids)
    sin = await _escenario(client, auth_headers, seeded_ids, puntos=None)

    e_con = await _pesar(client, auth_headers, con, 150.0)
    e_sin = await _pesar(client, auth_headers, sin, 150.0)

    def leer(evento):
        return client.get(f"/api/v1/operations/{evento['id']}/weight-evaluation",
                          headers=auth_headers)

    dentro = (await leer(e_con)).json()["evaluations"][0]
    ninguna = (await leer(e_sin)).json()["evaluations"][0]

    assert dentro["status"] == "within_standard", dentro
    assert ninguna["status"] == "no_reference", ninguna
    assert dentro["status"] != ninguna["status"], (
        "el mismo peso da la misma conclusión con curva y sin ella"
    )


# ── AC28 — tenencia ───────────────────────────────────────────────────────────

async def test_t_037_31_la_evaluacion_no_cruza_de_empresa(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC28` · un operador de otra empresa no lee la evaluación de un lote ajeno.

    El sujeto negativo tiene empresa propia: el Super Administrador está exento de tenencia
    y haría pasar la prueba sin comprobar nada.
    """
    from app.auth.security import create_access_token

    lote = await _escenario(client, auth_headers, seeded_ids)
    evento = await _pesar(client, auth_headers, lote, 150.0)

    # CONTROL · quien sí puede, lee.
    propio = await client.get(
        f"/api/v1/operations/{evento['id']}/weight-evaluation", headers=auth_headers)
    assert propio.status_code == 200, propio.text

    # TRATAMIENTO · el operador de la otra empresa, no.
    ajeno = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_other_company_id"])})}
    cruzado = await http_client.get(
        f"/api/v1/operations/{evento['id']}/weight-evaluation", headers=ajeno)
    assert cruzado.status_code == 404, (
        f"una empresa ajena leyó la evaluación de otro lote: {cruzado.text}"
    )
