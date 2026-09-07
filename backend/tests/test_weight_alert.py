"""Alerta de peso fuera de la curva estándar — `GA-REM-037`, decisión `OD-06`.

Cubre `AC20`, `AC21` y `AC22`.

`docs/03 spec.md §4.5` pedía avisar cuando el peso se desvía del estándar desde el
principio. Lo que faltaba no era el aviso: era la referencia. Sin curva cargada, cualquier
umbral que el software hubiera aplicado habría sido inventado, y `OD-06` fue explícita en
que no se inventa ninguna tolerancia global.

La alerta es un registro y nada más. `P-14` —canales de notificación— sigue sin
implementarse y este archivo lo comprueba.
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

PREFIJO = "WA-TEST-"

#: A los 15 días la interpolación de estos dos puntos da exactamente [135, 150, 165].
TABLA = [
    {"age_days": 10, "min_weight": 90.0, "target_weight": 100.0, "max_weight": 110.0},
    {"age_days": 20, "min_weight": 180.0, "target_weight": 200.0, "max_weight": 220.0},
]

#: El lote nace 30 días atrás y se pesa 15 días atrás: 15 días de edad al pesarlo.
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


async def _lote_con_curva(client, cab, seeded_ids, puntos=TABLA):
    """Un lote de 30 días con su línea genética y la curva activa de esa línea."""
    r = await client.post("/api/v1/masters/genetic-lines", headers=cab, json={
        "company_id": seeded_ids["company_id"], "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}"})
    assert r.status_code in (200, 201), r.text
    linea = r.json()["id"]

    if puntos is not None:
        c = await client.post("/api/v1/masters/weight-curves", headers=cab, json={
            "genetic_line_id": linea, "version_label": "v1", "is_active": True, "points": puntos})
        assert c.status_code == 201, c.text

    l = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
        "genetic_line_id": linea,
        "start_date": iso_days_ago(EDAD_LOTE),
    })
    assert l.status_code == 201, l.text
    return l.json()


async def _pesar(client, cab, lote, peso):
    return await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": lote["id"],
        "farm_id": lote["farm_id"],
        "house_id": lote["house_id"],
        "event_type": "weight_recording",
        "event_date": iso_days_ago(DIAS_DEL_PESAJE),
        "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": peso}],
    })


async def _alertas(test_database_url, lot_id):
    from app.operations.models import OperationalAlert

    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            filas = (await c.execute(
                select(OperationalAlert.alert_type, OperationalAlert.threshold_value,
                       OperationalAlert.actual_value, OperationalAlert.message)
                .where(OperationalAlert.lot_id == lot_id))).all()
        return [dict(zip(("tipo", "umbral", "real", "mensaje"), f)) for f in filas]
    finally:
        await e.dispose()


# ── AC20 — el pesaje fuera de rango alerta ────────────────────────────────────

@pytest.mark.parametrize("peso,umbral", [
    (100.0, 135.0),  # por debajo del mínimo interpolado
    (200.0, 165.0),  # por encima del máximo interpolado
])
async def test_t_037_20_un_peso_fuera_de_rango_crea_alerta(
    client, auth_headers, seeded_ids, motor, test_database_url, peso, umbral
):
    """`AC20` · la alerta nombra el peso, el umbral cruzado y la versión de curva.

    El rango a los 15 días no está en la tabla: sale de interpolar 10 y 20. Que la alerta
    cite 135 o 165 demuestra que se evaluó contra la curva y no contra un número fijo.
    """
    lote = await _lote_con_curva(client, auth_headers, seeded_ids)
    r = await _pesar(client, auth_headers, lote, peso)
    assert r.status_code == 201, r.text

    alertas = await _alertas(test_database_url, lote["id"])
    assert len(alertas) == 1, alertas
    assert alertas[0]["tipo"] == "weight_deviation", alertas[0]
    assert alertas[0]["umbral"] == umbral, alertas[0]
    assert alertas[0]["real"] == peso, alertas[0]
    assert "v1" in alertas[0]["mensaje"], alertas[0]["mensaje"]


# ── AC21 — dentro de rango no alerta ──────────────────────────────────────────

@pytest.mark.parametrize("peso", [
    135.0,  # el mínimo exacto: `AC16` lo declara dentro
    150.0,  # el objetivo
    165.0,  # el máximo exacto
])
async def test_t_037_21_dentro_de_rango_no_alerta(
    client, auth_headers, seeded_ids, motor, test_database_url, peso
):
    """`AC21` · un peso normal no genera aviso, y los bordes cuentan como normales."""
    lote = await _lote_con_curva(client, auth_headers, seeded_ids)
    r = await _pesar(client, auth_headers, lote, peso)
    assert r.status_code == 201, r.text
    assert await _alertas(test_database_url, lote["id"]) == []


async def test_t_037_22_sin_curva_cargada_no_se_inventa_alerta(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC19` y `AC21` · sin referencia no hay veredicto, ni bueno ni malo.

    Un peso de 5 g es absurdo para un ave de 15 días, y aun así no se alerta: alertar
    exigiría un umbral, y el único umbral legítimo es el de una curva que aquí no existe.
    """
    lote = await _lote_con_curva(client, auth_headers, seeded_ids, puntos=None)
    assert lote["weight_curve_id"] is None, lote

    r = await _pesar(client, auth_headers, lote, 5.0)
    assert r.status_code == 201, r.text
    assert await _alertas(test_database_url, lote["id"]) == []


async def test_t_037_23_fuera_del_rango_de_edades_no_se_extrapola(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC18` · a los 15 días con una tabla que empieza a los 30, no hay referencia.

    `OD-06` prohíbe extrapolar sin spec. Prolongar la recta más allá del último punto
    daría un rango con apariencia de dato y ningún respaldo del proveedor.
    """
    lote = await _lote_con_curva(client, auth_headers, seeded_ids, puntos=[
        {"age_days": 30, "min_weight": 400.0, "max_weight": 500.0},
        {"age_days": 40, "min_weight": 600.0, "max_weight": 700.0},
    ])
    r = await _pesar(client, auth_headers, lote, 50.0)
    assert r.status_code == 201, r.text
    assert await _alertas(test_database_url, lote["id"]) == []


# ── AC22 — ningún canal de notificación ───────────────────────────────────────

async def test_t_037_24_no_se_introduce_canal_de_notificacion(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC22` · la alerta es un registro. `GA-REM-037` no abrió ningún canal.

    **Corregida.** La versión original prohibía cualquier tabla que contuviera
    «notification», porque en su momento eso solo podía significar que `P-14` se había
    colado. Desde `OD-07`, `P-14` existe por decisión del propietario y con su spec
    (`GA-REM-038`), de modo que `notifications` es legítima y esta guarda la señalaba por su
    nombre.

    Lo que la guarda **quería** decir sigue en pie y es lo que ahora comprueba: `GA-REM-037`
    no introduce ningún **canal externo** ni cuelga la alerta de peso de una bandeja. La
    alerta sigue siendo una fila de `operational_alerts` y nada más.
    """
    from app.database import Base

    lote = await _lote_con_curva(client, auth_headers, seeded_ids)
    r = await _pesar(client, auth_headers, lote, 100.0)
    assert r.status_code == 201, r.text

    alertas = await _alertas(test_database_url, lote["id"])
    assert len(alertas) == 1, alertas

    sospechosas = [
        t for t in Base.metadata.tables
        if any(p in t for p in ("email", "smtp", "sms", "whatsapp", "push", "telegram",
                                "subscription", "delivery_attempt"))
    ]
    assert sospechosas == [], f"canal externo en el esquema: {sospechosas}"

    # Y la alerta de peso no se convirtió en notificación: `GA-REM-038` implementa dos tipos
    # —rechazo de registro y fallo de envío SAP— y `weight_deviation` no es ninguno.
    from app.notifications.models import Notification

    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            avisos = (await c.execute(
                select(Notification.id).where(Notification.company_id.isnot(None))
                .where(Notification.related_entity_type == "operational_alert"))).scalars().all()
        assert avisos == [], (
            "la alerta de peso acabó creando notificaciones, que `OD-08` aún no autoriza"
        )
    finally:
        await e.dispose()
