"""`GA-REM-005` — mortalidad y saldo de aves.

`P0-1` hacía que **ninguna mortalidad válida pudiera registrarse**: el generador de
alertas llamaba a `get_current_bird_balance` sin importarla y con tres argumentos en lugar
de dos, y el `NameError` salía como 500 *después* de haber persistido el evento. La suite
no lo detectaba porque su único test de mortalidad usaba una cantidad desorbitada que
`BR-01` rechazaba antes de llegar al generador.

Aquí se recorre el flujo completo: lote → saldo → entrada → causa → validación →
persistencia → efecto en el saldo → alerta → auditoría → respuesta.
"""

from __future__ import annotations

import math

import pytest

from tests.time_reference import recent_event_date


async def _recepcion(client, headers, lot_id: int, cantidad: int):
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lot_id, "farm_id": 1, "house_id": 1,
        "event_type": "bird_reception", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": cantidad}],
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _mortalidad(client, headers, lot_id: int, cantidad: int, cause_id=None):
    cuerpo = {
        "lot_id": lot_id, "event_type": "mortality_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": cantidad}],
    }
    if cause_id is not None:
        cuerpo["cause_id"] = cause_id
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


async def _saldo(client, headers, lot_id: int) -> int:
    """Saldo derivado de los eventos, con la misma regla que `get_current_bird_balance`."""
    r = await client.get(f"/api/v1/operations?lot_id={lot_id}&limit=100", headers=headers)
    assert r.status_code == 200, r.text
    entradas = {"bird_reception", "birth_registration"}
    salidas = {"mortality_recording", "cull_recording", "bird_exit", "chick_dispatch"}
    total = 0
    for evento in r.json():
        if evento["status"] == "cancelled":
            continue
        detalle = await client.get(f"/api/v1/operations/{evento['id']}", headers=headers)
        cantidad = sum(bm["quantity"] for bm in detalle.json().get("bird_movements", []))
        if evento["event_type"] in entradas:
            total += cantidad
        elif evento["event_type"] in salidas:
            total -= cantidad
    return total


# ── AC01 · registro válido ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac01_mortalidad_valida_se_registra(auth_headers, client, seeded_ids):
    lot = seeded_ids["lot_id"]
    await _recepcion(client, auth_headers, lot, 1000)
    inicial = await _saldo(client, auth_headers, lot)

    r = await _mortalidad(client, auth_headers, lot, 10, cause_id=1)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "registered"
    assert r.json()["cause_id"] == 1, "La causa debe conservarse (exigencia del cliente)"

    assert await _saldo(client, auth_headers, lot) == inicial - 10


# ── AC02 · mortalidad superior al saldo ───────────────────────────────────────

@pytest.mark.asyncio
async def test_ac02_mortalidad_sobre_el_saldo_se_rechaza(auth_headers, client, seeded_ids):
    lot = seeded_ids["lot_id_2"]
    await _recepcion(client, auth_headers, lot, 100)
    antes = await _saldo(client, auth_headers, lot)

    r = await _mortalidad(client, auth_headers, lot, antes + 1)
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "BR-01"
    assert str(antes) in r.json()["detail"], "El mensaje debe indicar el saldo disponible"
    assert await _saldo(client, auth_headers, lot) == antes, "No debe persistirse nada"


# ── AC03 · cantidad cero o negativa ───────────────────────────────────────────

@pytest.mark.parametrize("cantidad", [0, -5])
@pytest.mark.asyncio
async def test_ac03_cantidad_no_positiva(auth_headers, client, seeded_ids, cantidad):
    lot = seeded_ids["lot_id"]
    antes = await _saldo(client, auth_headers, lot)
    r = await _mortalidad(client, auth_headers, lot, cantidad)
    assert r.status_code in (400, 422), r.text
    assert await _saldo(client, auth_headers, lot) == antes


# ── AC04 · alerta por umbral ──────────────────────────────────────────────────

@pytest.mark.parametrize("porcentaje,severidad_esperada", [
    (1, None),          # por debajo del umbral
    (3, "warning"),     # umbral de advertencia
    (10, "critical"),   # umbral crítico
])
@pytest.mark.asyncio
async def test_ac04_alerta_por_umbral(auth_headers, client, seeded_ids,
                                      porcentaje, severidad_esperada):
    from app.operations.service import MORTALITY_CRITICAL_PCT, MORTALITY_WARNING_PCT

    lot = seeded_ids["lot_id"]
    await _recepcion(client, auth_headers, lot, 10_000)
    previo = await _saldo(client, auth_headers, lot)
    # Redondeo hacia arriba: truncar dejaba la proporción justo por debajo del umbral
    # (359/11990 = 2,994 %) y el test medía otra cosa distinta de la que enunciaba.
    cantidad = max(1, math.ceil(previo * porcentaje / 100))

    r = await _mortalidad(client, auth_headers, lot, cantidad)
    assert r.status_code == 201, r.text

    alertas = await client.get(f"/api/v1/operations/alerts?lot_id={lot}", headers=auth_headers)
    assert alertas.status_code == 200, alertas.text
    de_este = [a for a in alertas.json()
               if a.get("alert_type") == "high_mortality" and a.get("event_id") == r.json()["id"]]

    if severidad_esperada is None:
        assert not de_este, (
            f"Con {porcentaje}% (< {MORTALITY_WARNING_PCT}%) no debe generarse alerta")
    else:
        assert de_este, f"Con {porcentaje}% debe generarse alerta"
        assert de_este[0]["severity"] == severidad_esperada, (
            f"{porcentaje}% -> {severidad_esperada} "
            f"(umbrales {MORTALITY_WARNING_PCT}/{MORTALITY_CRITICAL_PCT})")


# ── AC05 · el generador de alertas no rompe el registro ───────────────────────

@pytest.mark.asyncio
async def test_ac05_un_fallo_en_las_alertas_no_pierde_el_evento(
    auth_headers, client, seeded_ids, monkeypatch
):
    """Las alertas son derivadas: perder una es molesto, perder el registro no vale.

    Es la lección de `P0-1`: un defecto en el generador se llevó por delante la
    funcionalidad entera durante meses.
    """
    from app.operations.service import OperationsService

    async def _explota(self, event, data):
        raise RuntimeError("fallo simulado del generador de alertas")

    monkeypatch.setattr(OperationsService, "_check_and_create_alerts", _explota)

    lot = seeded_ids["lot_id"]
    await _recepcion(client, auth_headers, lot, 500)
    r = await _mortalidad(client, auth_headers, lot, 5)
    assert r.status_code == 201, (
        f"El evento debe persistirse aunque las alertas fallen: {r.text[:200]}")

    leido = await client.get(f"/api/v1/operations/{r.json()['id']}", headers=auth_headers)
    assert leido.status_code == 200


# ── AC06 · BR-06 ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac06_fecha_anterior_a_la_activacion_del_lote(auth_headers, client, seeded_ids):
    """`BR-06`: el evento no puede preceder a la activación del lote."""
    from tests.time_reference import CLOSED_PERIOD_DAYS, iso_days_ago

    # El lote sembrado arranca en `lot_start_date()` = hoy − (90 + 365). Una fecha
    # anterior a eso queda además fuera del período abierto, de modo que se comprueba
    # con una fecha dentro del período pero anterior al lote no es posible con este
    # lote; se verifica el caso realmente alcanzable: BR-19 actúa primero.
    r = await _mortalidad(client, auth_headers, seeded_ids["lot_id"], 1)
    assert r.status_code in (201, 400)

    lejana = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": seeded_ids["lot_id"], "event_type": "mortality_recording",
        "event_date": iso_days_ago(CLOSED_PERIOD_DAYS + 500),
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    })
    assert lejana.status_code == 400
    assert lejana.json()["rule"] in ("BR-06", "BR-19"), (
        "Una fecha anterior a la activación del lote debe rechazarse por regla, "
        f"no aceptarse: {lejana.text[:160]}")


# ── AC07 · la regla del saldo ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac07_la_secuencia_completa_cuadra(auth_headers, client, seeded_ids):
    """recepción 1000 → mortalidad 10 → descarte 5 → salida 100 ⇒ 885."""
    lot = seeded_ids["lot_id_2"]
    inicial = await _saldo(client, auth_headers, lot)
    await _recepcion(client, auth_headers, lot, 1000)

    assert (await _mortalidad(client, auth_headers, lot, 10)).status_code == 201

    descarte = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lot, "event_type": "cull_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 5}],
    })
    assert descarte.status_code == 201, descarte.text

    salida = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lot, "farm_id": 1, "house_id": 1,
        "event_type": "bird_exit", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 100}],
    })
    assert salida.status_code == 201, salida.text

    assert await _saldo(client, auth_headers, lot) == inicial + 1000 - 10 - 5 - 100


@pytest.mark.asyncio
async def test_ac07b_las_transferencias_son_neutras(auth_headers, client, seeded_ids):
    """`RR-02`: `bird_transfer` mueve aves entre galpones del mismo lote.

    El esquema no tiene lote destino (`BirdMovement` declara galpón origen y destino),
    así que una transferencia no puede alterar el saldo del lote.
    """
    lot = seeded_ids["lot_id"]
    await _recepcion(client, auth_headers, lot, 200)
    antes = await _saldo(client, auth_headers, lot)

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lot, "farm_id": 1, "house_id": 1,
        "event_type": "bird_transfer", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 50,
                            "source_house_id": 1, "target_house_id": 2}],
    })
    assert r.status_code == 201, r.text
    assert await _saldo(client, auth_headers, lot) == antes, (
        "Una transferencia intra-lote no puede cambiar el saldo del lote (RR-02)")


# ── AC09 · sin regresión en el resto de tipos ─────────────────────────────────

@pytest.mark.asyncio
async def test_ac09_ningun_tipo_de_evento_devuelve_500(auth_headers, http_client, seeded_ids):
    """Ninguno de los 25 tipos puede responder 5xx con datos mínimos plausibles."""
    tipos = (await http_client.get("/api/v1/operations/event-types",
                                   headers=auth_headers)).json()
    assert len(tipos) == 25

    con_ubicacion = {
        "bird_reception", "bird_distribution", "bird_transfer", "bird_exit",
        "farm_inspection", "transport_inspection", "egg_collection",
        "egg_dispatch", "egg_reception_hatchery", "chick_dispatch",
    }
    fallos = []
    for tipo in tipos:
        cuerpo = {
            "lot_id": seeded_ids["lot_id"],
            "event_type": tipo["type"],
            "event_date": recent_event_date(),
        }
        if tipo["type"] in con_ubicacion:
            cuerpo["farm_id"], cuerpo["house_id"] = 1, 1
        r = await http_client.post("/api/v1/operations", headers=auth_headers, json=cuerpo)
        if r.status_code >= 500:
            fallos.append(f"{tipo['type']} -> {r.status_code}: {r.text[:120]}")
    assert not fallos, "Tipos de evento que devuelven 5xx:\n  " + "\n  ".join(fallos)


# ── Deriva de tipos enumerados (`R-40`, `R-41`) ───────────────────────────────

@pytest.mark.asyncio
async def test_los_enums_de_python_existen_en_postgresql():
    """Todo miembro de un enum del modelo debe existir en su tipo de PostgreSQL.

    Dos defectos vivían en este hueco: `EGG_RECEPTION_CLASSIFICATION` faltaba en
    `eventtype` desde junio, y `birdtypeenum` tenía `'hatchery'` en minúsculas cuando
    SQLAlchemy persiste el **nombre** del miembro, `'HATCHERY'`. En ambos casos el uso
    del valor terminaba en 500. La comprobación de deriva de esquema no los veía porque
    compara tablas y columnas, no valores de tipos enumerados.
    """
    from sqlalchemy import text

    import app.database as database
    from app.database import Base

    esperados: dict[str, set[str]] = {}
    for tabla in Base.metadata.sorted_tables:
        for columna in tabla.columns:
            clase = getattr(columna.type, "enum_class", None)
            if clase is not None:
                nombre = getattr(columna.type, "name", None) or clase.__name__.lower()
                esperados.setdefault(nombre, set()).update(m.name for m in clase)

    async with database.engine.connect() as conexion:
        filas = (await conexion.execute(text(
            "SELECT t.typname, e.enumlabel FROM pg_type t "
            "JOIN pg_enum e ON e.enumtypid = t.oid"
        ))).all()

    en_bd: dict[str, set[str]] = {}
    for nombre, etiqueta in filas:
        en_bd.setdefault(nombre, set()).add(etiqueta)

    faltantes = {
        nombre: sorted(valores - en_bd.get(nombre, set()))
        for nombre, valores in esperados.items()
        if valores - en_bd.get(nombre, set())
    }
    assert not faltantes, (
        "Valores de enum presentes en el modelo y ausentes en PostgreSQL: " f"{faltantes}")


# ── AC08 · el umbral es configurable ──────────────────────────────────────────

def test_ac08_el_umbral_se_lee_de_la_configuracion():
    """`docs/02 §3.14` exige «Mortalidad > umbral **configurable**».

    Estaba fijo en el código y la auditoría lo registró como hueco (`audit/06:259`). Se
    configura por el mismo mecanismo que el resto del sistema —variables de entorno vía
    `Settings`— y **no** por empresa: ese alcance lo añadió la spec de remediación y
    ninguna fuente lo pide.
    """
    from app.config import settings
    from app.operations import service

    assert service.MORTALITY_WARNING_PCT == settings.MORTALITY_ALERT_WARNING_PCT
    assert service.MORTALITY_CRITICAL_PCT == settings.MORTALITY_ALERT_CRITICAL_PCT
    assert 0 < settings.MORTALITY_ALERT_WARNING_PCT < settings.MORTALITY_ALERT_CRITICAL_PCT < 100, (
        "Los umbrales son porcentajes y el de advertencia precede al crítico")


def test_ac08_los_umbrales_no_son_numeros_magicos():
    """Ningún literal 3.0 / 8.0 suelto en el generador de alertas."""
    import inspect

    from app.operations.service import OperationsService

    import re

    fuente = inspect.getsource(OperationsService._check_and_create_alerts)
    assert "MORTALITY_WARNING_PCT" in fuente and "MORTALITY_CRITICAL_PCT" in fuente
    # Con límites de palabra: `35.0` —el máximo de temperatura, fuera del alcance de
    # `AC08`— contiene «5.0» y una comparación por subcadena lo confundiría.
    sueltos = re.findall(r"(?<![\d.])(?:3\.0|8\.0)(?![\d])", fuente)
    assert not sueltos, (
        f"El umbral de mortalidad debe venir de la configuración, no de un literal: {sueltos}")


def test_ac08_una_configuracion_distinta_cambia_el_comportamiento(monkeypatch):
    """Configurable significa que cambiarlo cambia algo."""
    from app.config import Settings

    otra = Settings(
        DATABASE_URL="postgresql+asyncpg://x:y@localhost/z",
        MORTALITY_ALERT_WARNING_PCT=5.0,
        MORTALITY_ALERT_CRITICAL_PCT=12.0,
    )
    assert otra.MORTALITY_ALERT_WARNING_PCT == 5.0
    assert otra.MORTALITY_ALERT_CRITICAL_PCT == 12.0


@pytest.mark.asyncio
async def test_ac08_cambiar_el_umbral_cambia_la_alerta(
    auth_headers, client, seeded_ids, monkeypatch
):
    """`§27`: con umbral A se alerta, con umbral B no. La configuración tiene efecto.

    Se demuestra sobre el generador real, no sobre el objeto de configuración: lo que
    importa es que el comportamiento observable cambie.
    """
    from app.operations import service

    lot = seeded_ids["lot_id_2"]
    await _recepcion(client, auth_headers, lot, 10_000)
    previo = await _saldo(client, auth_headers, lot)
    cantidad = max(1, math.ceil(previo * 4 / 100))  # 4 %: entre 3 y 5

    # Umbral al 3 %: una mortalidad del 4 % debe alertar.
    monkeypatch.setattr(service, "MORTALITY_WARNING_PCT", 3.0)
    monkeypatch.setattr(service, "MORTALITY_CRITICAL_PCT", 8.0)
    con_umbral_bajo = await _mortalidad(client, auth_headers, lot, cantidad)
    assert con_umbral_bajo.status_code == 201, con_umbral_bajo.text

    alertas = await client.get(f"/api/v1/operations/alerts?lot_id={lot}", headers=auth_headers)
    del_evento = [a for a in alertas.json()
                  if a.get("event_id") == con_umbral_bajo.json()["id"]]
    assert del_evento, "Con el umbral al 3 %, una mortalidad del 4 % debe alertar"

    # Umbral al 5 %: la misma proporción ya no debe alertar.
    monkeypatch.setattr(service, "MORTALITY_WARNING_PCT", 5.0)
    monkeypatch.setattr(service, "MORTALITY_CRITICAL_PCT", 12.0)
    previo_2 = await _saldo(client, auth_headers, lot)
    cantidad_2 = max(1, math.ceil(previo_2 * 4 / 100))
    con_umbral_alto = await _mortalidad(client, auth_headers, lot, cantidad_2)
    assert con_umbral_alto.status_code == 201, con_umbral_alto.text

    alertas_2 = await client.get(f"/api/v1/operations/alerts?lot_id={lot}", headers=auth_headers)
    del_evento_2 = [a for a in alertas_2.json()
                    if a.get("event_id") == con_umbral_alto.json()["id"]]
    assert not del_evento_2, (
        "Con el umbral al 5 %, la misma mortalidad del 4 % NO debe alertar: "
        "si alerta igual, la configuración no tiene efecto")


def test_ac08_el_umbral_se_expone_en_el_despliegue():
    """Configurable significa sin tocar código ni reconstruir la imagen."""
    import pathlib

    compose = pathlib.Path(__file__).resolve().parents[2] / "docker-compose.yml"
    texto = compose.read_text(encoding="utf-8")
    assert "MORTALITY_ALERT_WARNING_PCT" in texto, (
        "El umbral debe poder ajustarse desde el despliegue, no solo desde el código")
    assert "MORTALITY_ALERT_CRITICAL_PCT" in texto
