"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020 §6` — decisiones Owner ratificadas en la ruta de escritura.

Tres de las siete decisiones ratificadas el 25-11-2026 dejan de ser recomendación y pasan a ser
regla: toda corrección **nueva** declara su tipo (`RR-27`), una vacunación nueva dice con qué lote
de vacuna se aplicó (`RR-31`) y una baja o un descarte dicen por qué (`RR-32`, con el valor
explícito compartido «Desconocida» para lo que no se pudo determinar). Las tres viven en las rutas
de escritura —alta, `PUT` y corrección comparten las mismas funciones— y no en los esquemas de
lectura: los históricos incompletos siguen siendo legibles y no se rellenan.

Trazabilidad: `spec 020 §6` (`RR-27` · `OD-S2-01`, `RR-31` · `OD-S2-05`, `RR-32` · `OD-S2-06`).
Casos: `OD01-01..04`, `OD05-01..06`, `OD06-01..08` y la verificación de la migración que siembra
«Desconocida» y abre `feed_movements.phase_id`.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tests.time_reference import days_ago, iso_days_ago, recent_event_date

#: `RR-27`: el mensaje se lee tal cual en el formulario de corrección.
MENSAJE_TIPO = "Seleccione el tipo de corrección"
#: `RR-31`: el lote con el que se aplicó la vacuna.
MENSAJE_LOTE = "Ingrese el lote de la vacuna aplicada"
#: `RR-32`: la causa de la mortalidad y la del descarte, con la salida explícita «Desconocida».
MENSAJE_MORTALIDAD = (
    "Seleccione la causa de la mortalidad (use «Desconocida» si no se pudo determinar)")
MENSAJE_DESCARTE = (
    "Seleccione la causa del descarte (use «Desconocida» si no se pudo determinar)")

#: Nombre del valor compartido que siembra la migración (`RR-32`).
DESCONOCIDA = "Desconocida"

#: Lote y ubicación sembrados por la suite (`conftest.py`).
LOTE = 2
FARM = 1
HOUSE = 1

# ── Catálogos ────────────────────────────────────────────────────────────────

async def _lista(client, headers, recurso: str) -> list[dict]:
    """Listado de un catálogo de maestros, con la forma laxa que admite el endpoint."""
    r = await client.get(f"/api/v1/masters/{recurso}", headers=headers)
    assert r.status_code == 200, r.text
    datos = r.json()
    return datos["items"] if isinstance(datos, dict) else datos


async def _tipo_de_correccion(client, headers) -> int:
    """`RR-27`: un tipo de corrección válido del catálogo de la empresa (se crea si no hay)."""
    items = [i for i in await _lista(client, headers, "correction-types") if i.get("is_active", True)]
    if items:
        return items[0]["id"]
    r = await client.post("/api/v1/masters/correction-types", headers=headers,
                          json={"name": f"Tipo OD {uuid.uuid4().hex[:8].upper()}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _causa_nueva(client, headers, recurso: str) -> int:
    """Una causa válida del catálogo indicado, propia de la empresa del actor."""
    r = await client.post(f"/api/v1/masters/{recurso}", headers=headers,
                          json={"name": f"Causa OD {uuid.uuid4().hex[:8].upper()}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _id_de_la_desconocida(client, headers, recurso: str) -> int:
    """`RR-32`: el valor compartido sembrado por la migración, leído por el listado del catálogo."""
    nombres = [c["name"] for c in await _lista(client, headers, recurso)]
    desconocidas = [c for c in await _lista(client, headers, recurso) if c["name"] == DESCONOCIDA]
    assert len(desconocidas) == 1, (
        f"el catálogo '{recurso}' debe ofrecer «{DESCONOCIDA}» una sola vez —la siembra la crea "
        f"compartida para toda empresa—: {nombres}")
    return desconocidas[0]["id"]


async def _token_de_otra_empresa(client, headers, company_id: int) -> dict:
    """Un token con el contexto de la otra empresa, emitido por el super admin."""
    r = await client.post("/api/v1/switch-company", headers=headers,
                          json={"company_id": company_id})
    assert r.status_code == 200, r.text
    datos = r.json()
    token = datos.get("access_token") or datos.get("token")
    assert token, f"switch-company no devolvió un token: {datos}"
    return {"Authorization": f"Bearer {token}"}

# ── Datos de operación ───────────────────────────────────────────────────────

async def _lote(client, headers, bird_type: str = "breeder") -> int:
    r = await client.post("/api/v1/lots", headers=headers, json={
        "farm_id": FARM, "house_id": HOUSE,
        "lot_code": f"OD-{uuid.uuid4().hex[:8].upper()}",
        "bird_type": bird_type, "sex": "mixed",
        "start_date": iso_days_ago(21),
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _lote_con_aves(client, headers, aves: int = 50) -> int:
    """Un lote con aves dentro: una salida se mide contra el saldo disponible."""
    lote = await _lote(client, headers)
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote, "farm_id": FARM, "house_id": HOUSE,
        "event_type": "bird_reception", "event_date": recent_event_date(),
        "received_total": aves, "dead_on_arrival": 0, "rejected_on_arrival": 0,
        "bird_movements": [{"sex": "mixed", "quantity": aves}],
    })
    assert r.status_code == 201, r.text
    return lote


async def _alta_vacunacion(client, headers, **extra):
    """Vacunación sobre el lote sembrado: el dato del caso es el lote de vacuna."""
    cuerpo = {
        "lot_id": LOTE, "event_type": "vaccination", "event_date": recent_event_date(),
        "vaccine_id": 1, "vaccination_route": "water",
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


async def _alta_mortalidad(client, headers, lote: int, **extra):
    cuerpo = {
        "lot_id": lote, "event_type": "mortality_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


async def _alta_descarte(client, headers, lote: int, **extra):
    cuerpo = {
        "lot_id": lote, "event_type": "cull_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 1}],
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/operations", headers=headers, json=cuerpo)


async def _detalle(client, headers, event_id: int) -> dict:
    r = await client.get(f"/api/v1/operations/{event_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def _corregir(client, headers, event_id, campo, valor, *, tipo=None,
                    motivo="Error de digitación"):
    """Corrección; con `tipo=None` se omite el campo (contrato de `RR-27`)."""
    cuerpo = {"event_id": event_id, "field_name": campo, "corrected_value": valor,
              "reason": motivo}
    if tipo is not None:
        cuerpo["correction_type_id"] = tipo
    return await client.post("/api/v1/corrections", headers=headers, json=cuerpo)

# ── Estado heredado: filas que la API ya no deja escribir ────────────────────

async def _evento_historico(url: str, **campos) -> int:
    """Inserta un evento que la API ya no aceptaría: el histórico que debe seguir leyéndose."""
    import app.corrections.models  # noqa: F401  (registra la tabla en los metadatos)
    import app.operations.models  # noqa: F401
    from app.operations.models import OperationalEvent

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as sesion:
            evento = OperationalEvent(**campos)
            sesion.add(evento)
            await sesion.commit()
            return evento.id
    finally:
        await motor.dispose()


async def _correccion_historica(url: str, event_id: int, corrected_by_id: int,
                                campo: str = "observations") -> int:
    """Un `CorrectionLog` anterior a `RR-27`: su `correction_type_id` es `NULL` y así se lee."""
    from app.corrections.models import CorrectionLog

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as sesion:
            registro = CorrectionLog(
                event_id=event_id, field_name=campo, original_value="previo",
                corrected_value="histórico", corrected_by_id=corrected_by_id,
                correction_type_id=None, reason="Corrección anterior al tipo obligatorio",
            )
            sesion.add(registro)
            await sesion.commit()
            return registro.id
    finally:
        await motor.dispose()


# ══════════════════════════════════════════════════════════════════════════════
#  OD01 · `RR-27` — toda corrección nueva declara su tipo
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_od01_01_correccion_sin_tipo_es_400_en_espanol(auth_headers, client):
    """`OD01-01` · `RR-27`: sin tipo no hay corrección, y el rechazo se lee en español.

    Ni ausente, ni `null`, ni `0`, ni negativo: el tipo es un dato del registro de corrección.
    El mensaje no expone el identificador de la regla en el texto (viaja en `rule`).
    """
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-01")
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]

    sin_tipo = await _corregir(client, auth_headers, event_id, "observations", "sin tipo")
    assert sin_tipo.status_code == 400, sin_tipo.text
    assert sin_tipo.json()["detail"] == MENSAJE_TIPO, sin_tipo.json()
    assert sin_tipo.json()["rule"] == "RR-27", sin_tipo.json()

    tipo_cero = await _corregir(client, auth_headers, event_id, "observations", "tipo cero",
                                tipo=0)
    assert tipo_cero.status_code == 400, tipo_cero.text
    assert tipo_cero.json()["detail"] == MENSAJE_TIPO, tipo_cero.json()
    assert tipo_cero.json()["rule"] == "RR-27", tipo_cero.json()

    negativo = await _corregir(client, auth_headers, event_id, "observations", "negativo",
                               tipo=-3)
    assert negativo.status_code == 400, negativo.text
    assert negativo.json()["detail"] == MENSAJE_TIPO, negativo.json()

    # Nada cambió: un rechazo no escribe ni deja registro.
    assert (await _detalle(client, auth_headers, event_id))["status"] == "registered"
    historial = await client.get(f"/api/v1/corrections/event/{event_id}", headers=auth_headers)
    assert historial.json() == [], historial.text

@pytest.mark.asyncio
async def test_od01_02_correccion_con_tipo_valido_es_201(auth_headers, client):
    """`OD01-02` · `RR-27`: con un tipo del catálogo propio la corrección se registra con él."""
    tipo = await _tipo_de_correccion(client, auth_headers)
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-02")
    assert evento.status_code == 201, evento.text

    r = await _corregir(client, auth_headers, evento.json()["id"], "observations",
                        "con tipo", tipo=tipo)
    assert r.status_code == 201, r.text
    assert r.json()["correction_type_id"] == tipo, r.json()


@pytest.mark.asyncio
async def test_od01_03_correccion_historica_sin_tipo_sigue_siendo_legible(
        auth_headers, client, seeded_ids, test_database_url):
    """`OD01-03` · `RR-27`: el esquema de **lectura** admite `NULL` en las históricas.

    La regla vive en la escritura. Una corrección anterior al contrato se lee tal como quedó:
    sin tipo, con su motivo y su campo. Sin esto, `RR-27` habría roto el historial de auditoría.
    """
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-03")
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]
    await _correccion_historica(test_database_url, event_id, seeded_ids["user_admin_id"])

    r = await client.get(f"/api/v1/corrections/event/{event_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    historial = r.json()
    assert len(historial) == 1, historial
    fila = historial[0]
    assert fila["correction_type_id"] is None, fila
    assert fila["field_name"] == "observations", fila
    assert fila["reason"], fila


@pytest.mark.asyncio
async def test_od01_04_tipo_inexistente_o_de_otra_empresa_es_400(
        auth_headers, client, seeded_ids):
    """`OD01-04` · `RR-27`: el tipo debe existir, estar activo y ser alcanzable.

    Un identificador inventado y el tipo de otra empresa se comportan igual: no es un tipo de
    corrección para quien corrige.
    """
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-04")
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]

    inexistente = await _corregir(client, auth_headers, event_id, "observations", "x",
                                  tipo=987654321)
    assert inexistente.status_code == 400, inexistente.text
    assert inexistente.json()["detail"] == MENSAJE_TIPO, inexistente.json()
    assert inexistente.json()["rule"] == "RR-27", inexistente.json()

    headers_ajenos = await _token_de_otra_empresa(client, auth_headers,
                                                 seeded_ids["company_id_2"])
    ajeno = await client.post("/api/v1/masters/correction-types", headers=headers_ajenos,
                              json={"name": f"Tipo ajeno {uuid.uuid4().hex[:6].upper()}"})
    assert ajeno.status_code == 201, ajeno.text

    de_otra_empresa = await _corregir(client, auth_headers, event_id, "observations", "x",
                                      tipo=ajeno.json()["id"])
    assert de_otra_empresa.status_code == 400, de_otra_empresa.text
    assert de_otra_empresa.json()["detail"] == MENSAJE_TIPO, de_otra_empresa.json()


@pytest.mark.asyncio
async def test_od01_05_tipo_inactivo_es_400_y_reactivado_vuelve_a_servir(auth_headers, client):
    """`OD01-05` · `RR-27` (`OD-21`): un tipo desactivado no tipifica correcciones nuevas.

    El catálogo conserva el tipo (las correcciones históricas lo siguen nombrando), pero una
    corrección nueva con él es 400 con el mismo mensaje que «sin tipo». Reactivado, el mismo
    tipo vuelve a servir: el rechazo se debe a la inactividad y a nada más.
    """
    alta = await client.post("/api/v1/masters/correction-types", headers=auth_headers,
                             json={"name": f"Tipo retirado {uuid.uuid4().hex[:6].upper()}"})
    assert alta.status_code == 201, alta.text
    tipo = alta.json()["id"]
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-05")
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]

    baja = await client.put(f"/api/v1/masters/correction-types/{tipo}", headers=auth_headers,
                            json={"is_active": False})
    assert baja.status_code == 200, baja.text
    assert baja.json()["is_active"] is False, baja.json()

    inactivo = await _corregir(client, auth_headers, event_id, "observations", "x", tipo=tipo)
    assert inactivo.status_code == 400, inactivo.text
    assert inactivo.json()["detail"] == MENSAJE_TIPO, inactivo.json()
    assert inactivo.json()["rule"] == "RR-27", inactivo.json()

    reactivado = await client.put(f"/api/v1/masters/correction-types/{tipo}", headers=auth_headers,
                                  json={"is_active": True})
    assert reactivado.status_code == 200, reactivado.text
    ok = await _corregir(client, auth_headers, event_id, "observations", "x", tipo=tipo)
    assert ok.status_code == 201, ok.text
    assert ok.json()["correction_type_id"] == tipo, ok.json()

# ══════════════════════════════════════════════════════════════════════════════
#  OD05 · `RR-31` — la vacunación dice con qué lote de vacuna se aplicó
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_od05_01_vacunacion_sin_lote_de_vacuna_es_400(auth_headers, client):
    """`OD05-01` · `RR-31`: una vacunación nueva sin lote de vacuna no describe una aplicación."""
    r = await _alta_vacunacion(client, auth_headers)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_LOTE, r.json()
    assert r.json()["rule"] == "RR-31", r.json()


@pytest.mark.asyncio
async def test_od05_02_lote_de_vacuna_en_blanco_es_400(auth_headers, client):
    """`OD05-02` · `RR-31`: espacios no son texto: tras `trim` el lote sigue vacío."""
    r = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="   ")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_LOTE, r.json()
    assert r.json()["rule"] == "RR-31", r.json()


@pytest.mark.asyncio
async def test_od05_03_vacunacion_con_lote_valido_es_201(auth_headers, client):
    """`OD05-03` · `RR-31`: con lote de vacuna la vacunación se registra y lo conserva."""
    r = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-031")
    assert r.status_code == 201, r.text
    assert r.json()["vaccine_lot_number"] == "OD-VAC-031", r.json()


@pytest.mark.asyncio
async def test_od05_04_vacunacion_historica_sin_lote_es_legible_y_editable(
        auth_headers, client, seeded_ids, test_database_url):
    """`OD05-04` · `RR-31`: el histórico con `NULL` se lee y se corrige en **otros** campos.

    La regla se evalúa solo cuando la modificación **toca** el lote de vacuna: un registro
    heredado sin ese dato puede seguir corrigiéndose en observaciones.
    """
    from app.operations.models import EventStatus, EventType

    event_id = await _evento_historico(
        test_database_url,
        company_id=seeded_ids["company_id"], lot_id=LOTE, event_type=EventType.VACCINATION,
        event_date=days_ago(7), status=EventStatus.REGISTERED, version=1,
        registered_by_id=seeded_ids["user_admin_id"], vaccine_id=1,
        vaccination_route="water", vaccine_lot_number=None,
    )

    detalle = await _detalle(client, auth_headers, event_id)
    assert detalle["vaccine_lot_number"] is None, detalle

    tipo = await _tipo_de_correccion(client, auth_headers)
    r = await _corregir(client, auth_headers, event_id, "observations",
                        "histórico editable", tipo=tipo)
    assert r.status_code == 201, r.text
    assert (await _detalle(client, auth_headers, event_id))["observations"] == "histórico editable"

@pytest.mark.asyncio
async def test_od05_05_corregir_el_lote_de_vacuna_a_vacio_es_400(auth_headers, client):
    """`OD05-05` · `RR-31`: el lote de vacuna es campo corregible, pero no se puede vaciar."""
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-055")
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]

    tipo = await _tipo_de_correccion(client, auth_headers)
    r = await _corregir(client, auth_headers, event_id, "vaccine_lot_number", "", tipo=tipo)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_LOTE, r.json()
    assert r.json()["rule"] == "RR-31", r.json()
    assert (await _detalle(client, auth_headers, event_id))["vaccine_lot_number"] == "OD-VAC-055"


@pytest.mark.asyncio
async def test_od05_06_la_edicion_no_puede_vaciar_el_lote_de_vacuna(auth_headers, client):
    """`OD05-06` · `RR-31`: tampoco por `PUT`; el dato se conserva y el evento no cambia."""
    evento = await _alta_vacunacion(client, auth_headers, vaccine_lot_number="OD-VAC-056")
    assert evento.status_code == 201, evento.text
    event_id = evento.json()["id"]
    antes = await _detalle(client, auth_headers, event_id)

    r = await client.put(f"/api/v1/operations/{event_id}", headers=auth_headers,
                         json={"vaccine_lot_number": ""})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_LOTE, r.json()
    assert r.json()["rule"] == "RR-31", r.json()

    despues = await _detalle(client, auth_headers, event_id)
    assert despues["vaccine_lot_number"] == antes["vaccine_lot_number"], (antes, despues)
    assert despues["version"] == antes["version"], "un rechazo no produce versión nueva"


# ══════════════════════════════════════════════════════════════════════════════
#  OD06 · `RR-32` — la baja y el descarte dicen por qué
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_od06_01_mortalidad_sin_causa_es_400(auth_headers, client):
    """`OD06-01` · `RR-32`: una mortalidad sin causa no dice qué ocurrió."""
    lote = await _lote_con_aves(client, auth_headers)

    r = await _alta_mortalidad(client, auth_headers, lote)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_MORTALIDAD, r.json()
    assert r.json()["rule"] == "RR-32", r.json()

@pytest.mark.asyncio
async def test_od06_02_mortalidad_con_la_causa_desconocida_es_201(auth_headers, client):
    """`OD06-02` · `RR-32`: «Desconocida» es un valor explícito de catálogo; `NULL` no lo es."""
    lote = await _lote_con_aves(client, auth_headers)
    causa = await _id_de_la_desconocida(client, auth_headers, "mortality-causes")

    r = await _alta_mortalidad(client, auth_headers, lote, cause_id=causa)
    assert r.status_code == 201, r.text
    assert (await _detalle(client, auth_headers, r.json()["id"]))["cause_id"] == causa


@pytest.mark.asyncio
async def test_od06_03_descarte_sin_causa_es_400(auth_headers, client):
    """`OD06-03` · `RR-32`: lo mismo para el descarte."""
    lote = await _lote_con_aves(client, auth_headers)

    r = await _alta_descarte(client, auth_headers, lote)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_DESCARTE, r.json()
    assert r.json()["rule"] == "RR-32", r.json()


@pytest.mark.asyncio
async def test_od06_04_descarte_con_causa_valida_es_201(auth_headers, client):
    """`OD06-04` · `RR-32`: una causa propia y la compartida «Desconocida» son válidas."""
    lote = await _lote_con_aves(client, auth_headers)
    propia = await _causa_nueva(client, auth_headers, "cull-causes")
    r = await _alta_descarte(client, auth_headers, lote, cull_cause_id=propia)
    assert r.status_code == 201, r.text

    desconocida = await _id_de_la_desconocida(client, auth_headers, "cull-causes")
    r = await _alta_descarte(client, auth_headers, lote, cull_cause_id=desconocida)
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_od06_05_mortalidad_historica_sin_causa_es_legible_y_editable(
        auth_headers, client, seeded_ids, test_database_url):
    """`OD06-05` · `RR-32`: el histórico sin causa se lee y se corrige en **otros** campos."""
    from app.operations.models import EventStatus, EventType

    event_id = await _evento_historico(
        test_database_url,
        company_id=seeded_ids["company_id"], lot_id=LOTE, event_type=EventType.MORTALITY_RECORDING,
        event_date=days_ago(7), status=EventStatus.REGISTERED, version=1,
        registered_by_id=seeded_ids["user_admin_id"], cause_id=None,
    )
    detalle = await _detalle(client, auth_headers, event_id)
    assert detalle["cause_id"] is None, detalle

    tipo = await _tipo_de_correccion(client, auth_headers)
    r = await _corregir(client, auth_headers, event_id, "observations", "histórico editable", tipo=tipo)
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_od06_06_corregir_la_causa_a_vacio_es_400(auth_headers, client):
    """`OD06-06` · `RR-32`: la causa es corregible, pero no puede dejarse en `NULL`."""
    lote = await _lote_con_aves(client, auth_headers)
    causa = await _id_de_la_desconocida(client, auth_headers, "mortality-causes")
    alta = await _alta_mortalidad(client, auth_headers, lote, cause_id=causa)
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]

    tipo = await _tipo_de_correccion(client, auth_headers)
    r = await _corregir(client, auth_headers, event_id, "cause_id", "", tipo=tipo)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_MORTALIDAD, r.json()
    assert r.json()["rule"] == "RR-32", r.json()
    assert (await _detalle(client, auth_headers, event_id))["cause_id"] == causa


@pytest.mark.asyncio
async def test_od06_07_corregir_la_causa_del_descarte_a_vacio_es_400(auth_headers, client):
    """`OD06-07` · `RR-32`: igual para `cull_cause_id`."""
    lote = await _lote_con_aves(client, auth_headers)
    causa = await _id_de_la_desconocida(client, auth_headers, "cull-causes")
    alta = await _alta_descarte(client, auth_headers, lote, cull_cause_id=causa)
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]

    tipo = await _tipo_de_correccion(client, auth_headers)
    r = await _corregir(client, auth_headers, event_id, "cull_cause_id", "", tipo=tipo)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == MENSAJE_DESCARTE, r.json()
    assert r.json()["rule"] == "RR-32", r.json()


@pytest.mark.asyncio
async def test_od06_08_la_edicion_no_puede_dejar_la_causa_en_null(auth_headers, client):
    """`OD06-08` · `RR-32`: tampoco por `PUT` con la causa explícitamente nula."""
    lote = await _lote_con_aves(client, auth_headers)
    causa = await _id_de_la_desconocida(client, auth_headers, "mortality-causes")
    alta = await _alta_mortalidad(client, auth_headers, lote, cause_id=causa)
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]

    r = await client.put(f"/api/v1/operations/{event_id}", headers=auth_headers,
                         json={"cause_id": None})
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-32", r.json()
    assert (await _detalle(client, auth_headers, event_id))["cause_id"] == causa

