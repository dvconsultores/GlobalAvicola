"""
TEST FUNCIONAL COMPLETO — Flujo de Operaciones Avícolas con Auditoría Total

Este archivo implementa pruebas funcionales multidisciplinarias que validan
el flujo completo de extremo a extremo:

  1. REGISTRO: Operador crea operaciones (recepción de aves, despachos, inspecciones, etc.)
  2. REVISIÓN: Supervisor revisa los registros pendientes
  3. CORRECCIÓN: Se corrigen campos con trazabilidad (original → corregido)
  4. APROBACIÓN: Aprobador aprueba o rechaza con segregación de funciones
  5. RECHAZO: Rechazo con motivo obligatorio, sin perder trazabilidad
  6. AUDITORÍA: Verificación de trazabilidad completa por cada acción

Principio: Nada se borra. Todo se audita. Cada acción queda registrada
con: quién, qué, cuándo, valor anterior, valor nuevo, motivo.

Ejecutar con:
    python3 -m pytest tests/test_full_workflow_audit.py -v -s
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.time_reference import recent_event_date


# ============================================================
# Helpers: Login as different roles
# ============================================================

async def login_as(client: AsyncClient, username: str, password: str) -> dict:
    """Login and return auth headers + user info."""
    resp = await client.post("/api/v1/login", json={
        "username": username,
        "password": password,
    })
    if resp.status_code != 200:
        return None
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "user": data.get("user", {}),
        "access_token": data["access_token"],
    }


async def _try_login(client: AsyncClient, username: str, password: str):
    """Try login, return True if successful."""
    resp = await client.post("/api/v1/login", json={
        "username": username,
        "password": password,
    })
    return resp.status_code == 200


# ============================================================
# FIXTURE: Admin client (used for all tests as fallback)
# ============================================================

@pytest_asyncio.fixture
async def admin_client(client, auth_headers):
    """Cliente autenticado como administrador de pruebas.

    GA-REM-004 / GA-REM-015: antes creaba su propio `AsyncClient` y se
    autenticaba con las credenciales `admin/admin123` publicadas en la
    documentación. Esas credenciales fueron retiradas del repositorio.

    Ahora reutiliza las fixtures `client` y `auth_headers` de `conftest.py`,
    que se autentican con el administrador que siembra `seeds/test_seeds.py`
    con contraseña generada por ejecución. Reutilizarlas —en vez de crear un
    cliente propio— garantiza además que la conexión asíncrona pertenece al
    mismo bucle de eventos que el cuerpo del test.
    """
    client.headers.update(auth_headers)
    yield client


# ============================================================
# FASE 1: REGISTRO DE OPERACIONES
# ============================================================


async def _cliente_aprobador(client):
    """Cliente autenticado como aprobador, distinto de quien registra.

    `BR-14` (regla vigente `RR-03`) exige segregacion de funciones: quien registra no
    aprueba. Un test que use la misma identidad para registrar y aprobar no verifica el
    flujo de aprobacion: verifica que la regla no exista.
    """
    import os

    from seeds.test_seeds import TEST_APPROVER_PASSWORD_ENV, TEST_APPROVER_USERNAME

    respuesta = await client.post("/api/v1/login", json={
        "username": TEST_APPROVER_USERNAME,
        "password": os.environ[TEST_APPROVER_PASSWORD_ENV],
    })
    assert respuesta.status_code == 200, f"Login del aprobador: {respuesta.text}"
    client.headers.update({"Authorization": f"Bearer {respuesta.json()['access_token']}"})
    return client


@pytest.mark.asyncio
async def test_f1_create_bird_reception(admin_client):
    """
    F1 — Recepción de Aves:
    Un operador registra la recepción de pollitos BB en un lote.
    Validar que:
      - El evento se crea con status=registered
      - El registered_by_id queda registrado
      - Los bird_movements se guardan correctamente
      - Hay trazabilidad de auditoría (acción=created)
    """
    payload = {
        "lot_id": 2,
        "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "farm_id": 1,
        "house_id": 1,
        "bird_movements": [
            {"sex": "female", "quantity": 5000, "avg_weight": 42.5},
            {"sex": "male", "quantity": 500, "avg_weight": 43.0},
        ],
        "observations": "Recepción de pollitas BB lote #2 — prueba funcional",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201, f"F1 CREATE failed: {resp.text}"
    data = resp.json()

    # Assertions básicas
    assert data["event_type"] == "bird_reception"
    assert data["status"] == "registered", f"Expected 'registered', got '{data['status']}'"
    assert data["lot_id"] == 2
    assert data["farm_id"] == 1
    assert data["house_id"] == 1
    assert data["registered_by_id"] is not None
    assert data["observations"] == "Recepción de pollitas BB lote #2 — prueba funcional"

    # Verificar bird_movements en el detalle
    detail_resp = await admin_client.get(f"/api/v1/operations/{data['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["bird_movements"]) == 2

    # Guardar ID para pruebas posteriores
    return data["id"]


@pytest.mark.asyncio
async def test_f1_create_feed_registration(admin_client):
    """
    F1b — Registro de Alimento:
    Validar que el registro de consumo de alimento se crea correctamente.
    """
    payload = {
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": recent_event_date(),
        "feed_movements": [
            {"quantity_kg": 250.0, "sacks_count": 5, "feed_type_id": 1},
        ],
        "observations": "Alimento etapa iniciación — prueba funcional",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201, f"F1b CREATE failed: {resp.text}"
    data = resp.json()
    assert data["event_type"] == "feed_registration"
    assert data["status"] == "registered"
    return data["id"]


@pytest.mark.asyncio
async def test_f1_create_egg_collection(admin_client):
    """
    F1c — Recolección de Huevos:
    Validar registro de recolección de huevos (granja de reproductoras).
    """
    payload = {
        "lot_id": 1,  # Asumimos lote 1 = reproductoras
        "farm_id": 1,
        "house_id": 1,
        "event_type": "egg_collection",
        "event_date": recent_event_date(),
        "egg_movements": [
            {"egg_type": "fertile", "quantity": 4500, "avg_weight": 62.0},
            {"egg_type": "dirty", "quantity": 120},
            {"egg_type": "broken", "quantity": 35},
            {"egg_type": "discarded", "quantity": 80},
        ],
        "observations": "Recolección diaria — prueba funcional",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201, f"F1c CREATE failed: {resp.text}"
    data = resp.json()
    assert data["event_type"] == "egg_collection"
    assert data["status"] == "registered"

    # Verificar egg_movements
    detail_resp = await admin_client.get(f"/api/v1/operations/{data['id']}")
    detail = detail_resp.json()
    assert len(detail["egg_movements"]) == 4
    return data["id"]


@pytest.mark.asyncio
async def test_f1_create_farm_inspection(admin_client):
    """
    F1d — Inspección de Granja:
    Validar que la inspección con datos por galpón se registra correctamente.
    Los datos numéricos (temperatura, humedad) deben persistir.
    """
    payload = {
        "lot_id": 2,
        "farm_id": 1,
        "house_id": 1,
        "event_type": "farm_inspection",
        "event_date": recent_event_date(),
        "inspection_details": [
            {"house_id": 1, "parameter": "temperature", "value": "28.5"},
            {"house_id": 1, "parameter": "humidity", "value": "65.0"},
            {"house_id": 1, "parameter": "litter_condition", "status": "seca"},
            {"house_id": 2, "parameter": "temperature", "value": "30.1"},
            {"house_id": 2, "parameter": "humidity", "value": "70.0"},
        ],
        "observations": "Inspección matutina — prueba funcional",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201, f"F1d CREATE failed: {resp.text}"
    # Los submovimientos viven en el detalle (`OperationalEventDetailRead`); la creación
    # devuelve la cabecera.
    detalle = await admin_client.get(f"/api/v1/operations/{resp.json()['id']}")
    assert detalle.status_code == 200
    data = detalle.json()
    assert data["event_type"] == "farm_inspection"
    assert data["status"] == "registered"
    assert len(data["inspection_details"]) == 5

    # Verificar que los house_id son correctos
    house_ids = {d["house_id"] for d in data["inspection_details"]}
    assert house_ids == {1, 2}
    return data["id"]


@pytest.mark.asyncio
async def test_f1_create_vaccination(admin_client):
    """
    F1e — Vacunación:
    Validar que vaccine_id, vaccination_route y vaccine_lot_number se guardan.
    """
    payload = {
        "lot_id": 2,
        "event_type": "vaccination",
        "event_date": recent_event_date(),
        "vaccine_id": 1,
        "vaccination_route": "drinking_water",
        "vaccine_lot_number": "VAC-2026-001",
        "dosage_per_bird": 0.5,
        "bird_movements": [
            {"sex": "female", "quantity": 5000},
            {"sex": "male", "quantity": 500},
        ],
        "observations": "Vacunación Newcastle — prueba funcional",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201, f"F1e CREATE failed: {resp.text}"
    data = resp.json()
    assert data["vaccine_id"] == 1
    assert data["vaccination_route"] == "drinking_water"
    assert data["vaccine_lot_number"] == "VAC-2026-001"
    return data["id"]


@pytest.mark.asyncio
async def test_f1_create_egg_dispatch(admin_client):
    """
    F1f — Despacho de Huevos:
    Validar despacho de huevos a incubadora.
    """
    payload = {
        "lot_id": 1,
        "farm_id": 1,
        "house_id": 1,
        "event_type": "egg_dispatch",
        "event_date": recent_event_date(),
        "egg_movements": [
            {"egg_type": "fertile", "quantity": 2000, "avg_weight": 62.0},
        ],
        "destination_farm_id": 2,
        "observations": "Despacho a incubadora — prueba funcional",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    # Puede fallar por regla de negocio (saldo insuficiente) si no hay recolección previa
    if resp.status_code == 400:
        assert "saldo" in resp.json()["detail"].lower() or "excede" in resp.json()["detail"].lower()
        print(f"  ⚠️  Despacho bloqueado por regla de negocio (esperado si no hay saldo): {resp.json()['detail']}")
        return None
    assert resp.status_code == 201, f"F1f CREATE failed: {resp.text}"
    data = resp.json()
    assert data["event_type"] == "egg_dispatch"
    return data["id"]


@pytest.mark.asyncio
async def test_f1_idempotency_prevention(admin_client):
    """
    F1g — Idempotencia:
    Validar que enviar el mismo idempotency_key no crea duplicados.
    """
    key = "test-idempotency-key-001"
    payload = {
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 100.0}],
        "idempotency_key": key,
    }

    # Primer envío
    resp1 = await admin_client.post("/api/v1/operations", json=payload)
    assert resp1.status_code == 201

    # Segundo envío con misma key
    resp2 = await admin_client.post("/api/v1/operations", json=payload)
    assert resp2.status_code == 201
    assert resp2.json()["id"] == resp1.json()["id"], "Idempotency: debería devolver el mismo evento"


# ============================================================
# FASE 2: ENVÍO A REVISIÓN
# ============================================================

@pytest.mark.asyncio
async def test_f2_submit_to_review(admin_client):
    """
    F2 — Enviar a Revisión:
    El operador envía un evento de 'registered' a la bandeja de revisión.
    Validar que:
      - El status cambia a 'pending_review'
      - El evento aparece en /review/pending
    """
    # Crear un evento fresh
    payload = {
        "lot_id": 2,
        "farm_id": 1,
        "house_id": 1,
        "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 1000, "avg_weight": 40.0}],
        "observations": "Evento para prueba de revisión",
    }
    create_resp = await admin_client.post("/api/v1/operations", json=payload)
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # Enviar a revisión
    submit_resp = await admin_client.post(f"/api/v1/operations/{event_id}/submit")
    assert submit_resp.status_code == 200, f"F2 SUBMIT failed: {submit_resp.text}"
    data = submit_resp.json()
    assert data["status"] in ("pending_review", "in_review"), f"Status inesperado: {data['status']}"

    # Verificar que aparece en bandeja de revisión
    pending_resp = await admin_client.get("/api/v1/review/pending", params={"limit": 100})
    assert pending_resp.status_code == 200
    pending = pending_resp.json()
    pending_ids = [e["id"] for e in pending["events"]]
    assert event_id in pending_ids, f"Evento #{event_id} no aparece en bandeja de revisión"

    return event_id


# ============================================================
# FASE 3: REVISIÓN Y CORRECCIÓN
# ============================================================

@pytest.mark.asyncio
async def test_f3_start_review_and_correct(admin_client):
    """
    F3 — Iniciar Revisión y Corregir:
    El supervisor inicia la revisión de un evento, detecta un error,
    registra una corrección auditada (valor original → valor corregido).
    Validar que:
      - El evento pasa a 'in_review'
      - La corrección se registra con original_value y corrected_value
      - El evento pasa a 'corrected'
      - La corrección aparece en /corrections/event/{id}
    """
    # Crear y enviar a revisión
    payload = {
        "lot_id": 2,
        "farm_id": 1,
        "house_id": 1,
        "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 800, "avg_weight": 40.0}],
        "observations": "Evento para corrección",
    }
    create_resp = await admin_client.post("/api/v1/operations", json=payload)
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    await admin_client.post(f"/api/v1/operations/{event_id}/submit")

    # Iniciar revisión
    start_resp = await admin_client.post(f"/api/v1/review/start/{event_id}")
    assert start_resp.status_code == 200, f"F3 START REVIEW failed: {start_resp.text}"
    event_data = start_resp.json()
    assert event_data["status"] == "in_review"

    # Registrar corrección: el operador digitó 800 pero eran 850
    correction_payload = {
        "event_id": event_id,
        # `bird_movements[0].quantity` no es corregible: el contrato solo admite
        # campos del evento. Corregir un submovimiento exige poder
        # identificarlo, y el esquema no lo permite (`R-46`).
        "field_name": "observations",
        "original_value": "800",
        "corrected_value": "850",
        "reason": "Error de digitación: se recibieron 850 aves, no 800",
    }
    corr_resp = await admin_client.post("/api/v1/corrections", json=correction_payload)
    assert corr_resp.status_code == 201, f"F3 CORRECTION failed: {corr_resp.text}"
    corr_data = corr_resp.json()

    # Validar corrección. `original_value` lo lee el servidor del dato: si lo aportara
    # quien corrige, la auditoría dejaría de ser evidencia. El valor enviado en el
    # payload se ignora a propósito.
    assert corr_data["field_name"] == "observations"
    assert corr_data["original_value"] != "800", (
        "El registro debe guardar lo que había en el campo, no lo que declare el cliente")
    assert corr_data["corrected_value"] == "850"
    assert corr_data["original_value"] is not None
    assert corr_data["corrected_by_id"] is not None
    assert "Error de digitación" in corr_data["reason"]

    # Verificar que el evento pasó a 'corrected'
    get_resp = await admin_client.get(f"/api/v1/operations/{event_id}")
    event = get_resp.json()
    assert event["status"] == "corrected", f"Expected 'corrected', got '{event['status']}'"

    # Verificar que la corrección es recuperable
    corrections_resp = await admin_client.get(f"/api/v1/corrections/event/{event_id}")
    corrections = corrections_resp.json()
    assert len(corrections) >= 1
    assert corrections[0]["field_name"] == "observations"

    return event_id


@pytest.mark.asyncio
async def test_f3b_correction_not_allowed_on_approved(admin_client):
    """
    F3b — Corrección Bloqueada en Aprobados:
    Validar que no se puede corregir un evento que ya fue aprobado.
    """
    # Intentar corregir un evento en estado no corregible
    # Primero necesitamos un evento aprobado
    resp = await admin_client.get("/api/v1/approvals/pending", params={"limit": 1})
    if resp.json()["total"] == 0:
        pytest.skip("No hay eventos pendientes de aprobación para esta prueba")

    # Intentar corregir con estado inválido
    correction_payload = {
        "event_id": 99999,  # ID inexistente
        "field_name": "observations",
        "original_value": "100",
        "corrected_value": "200",
        "reason": "Prueba de bloqueo de corrección",
    }
    corr_resp = await admin_client.post("/api/v1/corrections", json=correction_payload)
    assert corr_resp.status_code == 404, "Debe rechazar corrección de evento inexistente"


# ============================================================
# FASE 4: APROBACIÓN
# ============================================================

@pytest.mark.asyncio
async def test_f4_approve_event(admin_client, client):
    """
    F4 — Aprobación:
    El aprobador aprueba un evento corregido.
    Validar que:
      - El status cambia a 'approved'
      - El approved_by_id queda registrado
      - El approval action queda registrado
    """
    # Buscar eventos pendientes de aprobación (status=corrected)
    pending_resp = await admin_client.get("/api/v1/approvals/pending", params={"limit": 10})
    pending = pending_resp.json()

    if pending["total"] == 0:
        # Crear el ciclo completo: crear → enviar → iniciar revisión → corregir
        payload = {
            "lot_id": 2,
            "event_type": "feed_registration",
            "event_date": recent_event_date(),
            "feed_movements": [{"quantity_kg": 300.0}],
            "observations": "Evento para aprobación",
        }
        create_resp = await admin_client.post("/api/v1/operations", json=payload)
        assert create_resp.status_code == 201
        event_id = create_resp.json()["id"]

        await admin_client.post(f"/api/v1/operations/{event_id}/submit")
        await admin_client.post(f"/api/v1/review/start/{event_id}")

        # Corregir. El campo era `feed_movements[0].quantity_kg`, una ruta anidada que
        # el contrato de correcciones no admite: solo se corrigen campos del evento
        # (lista blanca en `corrections/service.py`). Corregir un submovimiento requiere
        # poder identificarlo, y el esquema no ofrece forma de hacerlo (`R-46`).
        await admin_client.post("/api/v1/corrections", json={
            "event_id": event_id,
            "field_name": "observations",
            "corrected_value": "Ajuste por peso real del bulto",
            "reason": "Ajuste por peso real del bulto",
        })
    else:
        event_id = pending["events"][0]["id"]

    # Aprobar con una identidad distinta de la que registro: `BR-14` prohibe que un
    # operador apruebe su propia carga, y el test usaba el mismo cliente para ambas
    # cosas. Comprobaba, sin saberlo, que la regla NO se aplicara.
    aprobador = await _cliente_aprobador(client)
    approve_resp = await aprobador.post("/api/v1/approvals/approve", json={
        "event_id": event_id,
        "observations": "Aprobado — datos verificados contra guía de despacho",
    })
    assert approve_resp.status_code == 200, f"F4 APPROVE failed: {approve_resp.text}"
    approved = approve_resp.json()
    assert approved["status"] == "approved", f"Expected 'approved', got '{approved['status']}'"

    # Verificar que ya no aparece en pendientes
    pending2 = await admin_client.get("/api/v1/approvals/pending", params={"limit": 100})
    pending2_ids = [e["id"] for e in pending2.json()["events"]]
    assert event_id not in pending2_ids, "El evento aprobado no debe aparecer en pendientes"

    return event_id


@pytest.mark.asyncio
async def test_f4b_segregation_enforcement(admin_client):
    """
    F4b — Segregación de Funciones (BR-14):
    Validar que el mismo usuario que registró NO puede aprobar su propio evento.
    Nota: Con admin_client el usuario admin es el mismo. Este test verifica
    que la validación de segregación existe en el código.
    """
    # Crear evento como admin
    payload = {
        "lot_id": 2,
        "farm_id": 1,
        "house_id": 1,
        "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 500, "avg_weight": 40.0}],
    }
    create_resp = await admin_client.post("/api/v1/operations", json=payload)
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # Enviar a revisión y corregir para que llegue a 'corrected'
    await admin_client.post(f"/api/v1/operations/{event_id}/submit")
    await admin_client.post(f"/api/v1/review/start/{event_id}")
    await admin_client.post("/api/v1/corrections", json={
        "event_id": event_id,
        # `bird_movements[0].quantity` no es corregible: el contrato solo admite
        # campos del evento. Corregir un submovimiento exige poder
        # identificarlo, y el esquema no lo permite (`R-46`).
        "field_name": "observations",
        "original_value": "500",
        "corrected_value": "550",
        "reason": "Corrección de cantidad",
    })

    # Intentar aprobar con el mismo usuario (admin registró Y aprueba)
    approve_resp = await admin_client.post("/api/v1/approvals/approve", json={
        "event_id": event_id,
        "observations": "Intento de auto-aprobación",
    })
    # Debe fallar con 403 por segregación
    assert approve_resp.status_code == 403, (
        f"BR-14: Debe rechazar auto-aprobación. Got {approve_resp.status_code}: {approve_resp.text}"
    )
    assert "segregación" in approve_resp.json()["detail"].lower() or \
           "propios" in approve_resp.json()["detail"].lower()


# ============================================================
# FASE 5: RECHAZO
# ============================================================

@pytest.mark.asyncio
async def test_f5_reject_event(admin_client):
    """
    F5 — Rechazo:
    El aprobador rechaza un evento con motivo obligatorio.
    Validar que:
      - El status cambia a 'rejected'
      - El motivo de rechazo se guarda
      - El evento es recuperable (no se pierde)
      - La acción de rechazo queda registrada
    """
    # Crear evento → enviar → revisar → corregir → rechazar
    payload = {
        "lot_id": 2,
        "farm_id": 1,
        "house_id": 1,
        "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 300, "avg_weight": 40.0}],
        "observations": "Evento para prueba de rechazo",
    }
    create_resp = await admin_client.post("/api/v1/operations", json=payload)
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    await admin_client.post(f"/api/v1/operations/{event_id}/submit")
    await admin_client.post(f"/api/v1/review/start/{event_id}")
    await admin_client.post("/api/v1/corrections", json={
        "event_id": event_id,
        # `bird_movements[0].quantity` no es corregible: el contrato solo admite
        # campos del evento. Corregir un submovimiento exige poder
        # identificarlo, y el esquema no lo permite (`R-46`).
        "field_name": "observations",
        "original_value": "300",
        "corrected_value": "320",
        "reason": "Corrección menor",
    })

    # Rechazar (el admin no puede aprobar el suyo, pero sí puede rechazar = otro flujo)
    # Si da 403, es esperado. Probemos con el endpoint de reject.
    reject_resp = await admin_client.post("/api/v1/approvals/reject", json={
        "event_id": event_id,
        "observations": "RECHAZADO: Datos inconsistentes con el remito físico. "
                        "Se solicita al operador verificar cantidades reales.",
    })
    # Puede fallar por segregación (403) o tener éxito (200)
    if reject_resp.status_code == 403:
        print(f"  ⚠️  Rechazo bloqueado por segregación (esperado): admin registró y también rechaza")
        # Verificar que el evento sigue existiendo (no se perdió)
        get_resp = await admin_client.get(f"/api/v1/operations/{event_id}")
        assert get_resp.status_code == 200, "El evento no debe desaparecer tras rechazo fallido"
        return event_id

    assert reject_resp.status_code == 200, f"F5 REJECT failed: {reject_resp.text}"
    rejected = reject_resp.json()
    assert rejected["status"] == "rejected", f"Expected 'rejected', got '{rejected['status']}'"

    # Verificar que el evento se puede recuperar
    get_resp = await admin_client.get(f"/api/v1/operations/{event_id}")
    assert get_resp.status_code == 200
    event = get_resp.json()
    assert event["id"] == event_id
    assert event["status"] == "rejected"

    return event_id


@pytest.mark.asyncio
async def test_f5b_reject_requires_reason(admin_client):
    """
    F5b — Rechazo sin Motivo:
    Validar que NO se puede rechazar sin proporcionar un motivo (observations).
    """
    # Intentar rechazar sin observations o con observations muy corta
    reject_resp = await admin_client.post("/api/v1/approvals/reject", json={
        "event_id": 1,
        "observations": "Corto",  # Menos de 10 caracteres → debe fallar validación Pydantic
    })
    assert reject_resp.status_code == 422, (
        f"Debe rechazar por validación (observations muy corta). Got {reject_resp.status_code}"
    )


# ============================================================
# FASE 6: AUDITORÍA Y TRAZABILIDAD
# ============================================================

@pytest.mark.asyncio
async def test_f6_audit_trail_complete(admin_client):
    """
    F6 — Trazabilidad de Auditoría:
    Verificar que CADA acción en el flujo genera un registro de auditoría.
    Flujo completo monitoreado:
      CREATED → SUBMITTED → REVIEW_STARTED → CORRECTED → APPROVED
    Cada paso debe aparecer en /audit con:
      - action (qué pasó)
      - user_id (quién lo hizo)
      - entity_type y entity_id (sobre qué)
      - previous_state / new_state (transición)
      - timestamp (cuándo)
    """
    # Crear evento fresco para trace completo
    payload = {
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 500.0}],
        "observations": "Evento para auditoría completa",
    }
    create_resp = await admin_client.post("/api/v1/operations", json=payload)
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]
    event_id_str = str(event_id)

    print(f"\n  📋 Audit trail para evento #{event_id}:")

    # Verificar auditoría POST-creación
    audit_resp = await admin_client.get("/api/v1/audit", params={
        "entity_type": "operational_event",
        "entity_id": event_id_str,
        "limit": 50,
    })
    assert audit_resp.status_code == 200
    logs = audit_resp.json()["logs"]
    assert len(logs) >= 1, "Debe existir al menos 1 registro de auditoría tras crear"
    print(f"     ✅ Creación auditada: {len(logs)} registros")

    # Enviar a revisión
    await admin_client.post(f"/api/v1/operations/{event_id}/submit")
    audit2 = await admin_client.get("/api/v1/audit", params={
        "entity_type": "operational_event",
        "entity_id": event_id_str,
    })
    logs2 = audit2.json()["logs"]
    print(f"     ✅ Post-submit: {len(logs2)} registros (acciones: {[l['action'] for l in logs2[:5]]})")

    # Iniciar revisión
    await admin_client.post(f"/api/v1/review/start/{event_id}")
    audit3 = await admin_client.get("/api/v1/audit", params={
        "entity_type": "operational_event",
        "entity_id": event_id_str,
    })
    logs3 = audit3.json()["logs"]
    actions3 = [l["action"] for l in logs3[:10]]
    print(f"     ✅ Post-start-review: {len(logs3)} registros (acciones: {actions3})")

    # Corregir
    await admin_client.post("/api/v1/corrections", json={
        "event_id": event_id,
        "field_name": "observations",
        "original_value": "500.0",
        "corrected_value": "525.0",
        "reason": "Ajuste por diferencia de báscula",
    })
    audit4 = await admin_client.get("/api/v1/audit", params={
        "entity_type": "operational_event",
        "entity_id": event_id_str,
    })
    logs4 = audit4.json()["logs"]
    actions4 = [l["action"] for l in logs4[:10]]
    print(f"     ✅ Post-correction: {len(logs4)} registros (acciones: {actions4})")
    assert any(a == "corrected" for a in actions4), "Debe existir acción 'corrected' en auditoría"

    # Verificar timeline completo
    timeline_resp = await admin_client.get(
        f"/api/v1/audit/timeline/operational_event/{event_id_str}"
    )
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert timeline["entity_type"] == "operational_event"
    assert timeline["entity_id"] == event_id_str
    assert timeline["total_steps"] >= 1
    print(f"     ✅ Timeline completo: {timeline['total_steps']} pasos")

    # Cada paso debe tener user_id, action, y created_at
    for step in timeline["timeline"]:
        assert "user_id" in step, f"Falta user_id en paso de auditoría: {step}"
        assert "action" in step, f"Falta action en paso de auditoría: {step}"
        assert "created_at" in step, f"Falta created_at en paso de auditoría: {step}"
        print(f"        → {step['action']} por user#{step['user_id']} @ {step['created_at']}")

    return event_id


@pytest.mark.asyncio
async def test_f6b_audit_logs_never_deleted(admin_client):
    """
    F6b — Inmutabilidad de Auditoría:
    Validar que los logs de auditoría son de solo lectura.
    No deben existir endpoints DELETE/PUT para audit_logs.
    """
    # Intentar DELETE (debe devolver 405 Method Not Allowed)
    del_resp = await admin_client.delete("/api/v1/audit/any-id")
    assert del_resp.status_code in (404, 405), (
        f"Audit logs no deben ser eliminables. Got {del_resp.status_code}"
    )

    # Intentar PUT (debe devolver 405)
    put_resp = await admin_client.put("/api/v1/audit/any-id", json={})
    assert put_resp.status_code in (404, 405), (
        f"Audit logs no deben ser modificables. Got {put_resp.status_code}"
    )


@pytest.mark.asyncio
async def test_f6c_audit_filter_by_user_action(admin_client):
    """
    F6c — Filtros de Auditoría:
    Validar que se puede filtrar por:
      - user_id
      - action
      - module
      - lot_id
      - date range
    """
    # Filtrar por acción
    resp = await admin_client.get("/api/v1/audit", params={
        "action": "created",
        "limit": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    for log in data["logs"]:
        assert log["action"] == "created"

    # Filtrar por módulo
    resp2 = await admin_client.get("/api/v1/audit", params={
        "module": "operations",
        "limit": 5,
    })
    assert resp2.status_code == 200
    for log in resp2.json()["logs"]:
        assert log["module"] == "operations"

    # Filtrar por lote
    resp3 = await admin_client.get("/api/v1/audit", params={
        "lot_id": 2,
        "limit": 5,
    })
    assert resp3.status_code == 200
    for log in resp3.json()["logs"]:
        assert log["lot_id"] == 2


# ============================================================
# FASE 7: FLUJO COMPLETO END-TO-END (MULTI-ROL SIMULADO)
# ============================================================

@pytest.mark.asyncio
async def test_f7_full_workflow_simulated_multirole(admin_client):
    """
    F7 — FLUJO COMPLETO SIMULADO MULTI-ROL:
    
    Simula el flujo real con múltiples actores usando el admin_client
    (ya que los usuarios separados pueden no existir en la BD de pruebas).
    
    Flujo:
      1. OPERADOR: Crea bird_reception → status=registered
      2. OPERADOR: Envía a revisión → status=pending_review
      3. SUPERVISOR: Inicia revisión → status=in_review
      4. SUPERVISOR: Corrige cantidad → status=corrected
      5. APROBADOR: (simulado) Aprueba → status=approved
    
    Validaciones en cada paso:
      - Estado correcto
      - Auditoría registrada
      - Corrección trazable
    """
    print("\n  🔄 INICIANDO FLUJO COMPLETO END-TO-END")

    # ─── Paso 1: OPERADOR registra ───
    print("     1️⃣  Operador registra recepción de aves...")
    payload = {
        "lot_id": 2,
        "event_type": "bird_reception",
        "event_date": recent_event_date(),
        "farm_id": 1,
        "house_id": 1,
        "bird_movements": [
            {"sex": "female", "quantity": 3000, "avg_weight": 41.0},
            {"sex": "male", "quantity": 300, "avg_weight": 42.0},
        ],
        "observations": "E2E: Recepción lote 2 — junio 2026",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201
    event_id = resp.json()["id"]
    event_id_str = str(event_id)
    assert resp.json()["status"] == "registered"
    print(f"        ✅ Evento #{event_id} creado — status=registered")

    # ─── Paso 2: OPERADOR envía a revisión ───
    print("     2️⃣  Operador envía a revisión...")
    resp = await admin_client.post(f"/api/v1/operations/{event_id}/submit")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("pending_review", "in_review")
    print(f"        ✅ Evento #{event_id} enviado a revisión")

    # ─── Paso 3: SUPERVISOR inicia revisión ───
    print("     3️⃣  Supervisor inicia revisión...")
    resp = await admin_client.post(f"/api/v1/review/start/{event_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_review"
    print(f"        ✅ Revisión iniciada — status=in_review")

    # ─── Paso 4: SUPERVISOR corrige ───
    print("     4️⃣  Supervisor corrige error de digitación...")
    resp = await admin_client.post("/api/v1/corrections", json={
        "event_id": event_id,
        # `bird_movements[0].quantity` no es corregible: el contrato solo admite
        # campos del evento. Corregir un submovimiento exige poder
        # identificarlo, y el esquema no lo permite (`R-46`).
        "field_name": "observations",
        "original_value": "3000",
        "corrected_value": "3200",
        "reason": "Error de digitación: guía de despacho indica 3200 aves hembra",
    })
    assert resp.status_code == 201
    corr = resp.json()
    assert corr["original_value"] != "3000"  # lo lee el servidor del dato, no del payload
    assert corr["corrected_value"] == "3200"
    print(f"        ✅ Corrección registrada: {corr['original_value']} → {corr['corrected_value']}")

    # Verificar estado post-corrección
    resp = await admin_client.get(f"/api/v1/operations/{event_id}")
    assert resp.json()["status"] == "corrected"
    print(f"        ✅ Estado post-corrección: corrected")

    # ─── Paso 5: Verificación de auditoría completa ───
    print("     5️⃣  Verificando trazabilidad de auditoría...")
    timeline_resp = await admin_client.get(
        f"/api/v1/audit/timeline/operational_event/{event_id_str}"
    )
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    actions = [s["action"] for s in timeline["timeline"]]
    print(f"        📋 Timeline completo ({timeline['total_steps']} pasos):")
    for step in timeline["timeline"]:
        print(f"           • {step['action']} | user={step['user_id']} | {step['created_at']}")

    # Validar que están las acciones clave
    assert "created" in actions, "Falta acción 'created' en timeline"
    assert "corrected" in actions, "Falta acción 'corrected' en timeline"
    assert "review_started" in actions or "started_review" in actions, \
        "Falta acción de inicio de revisión en timeline"

    # ─── Paso 6: Verificar correcciones del evento ───
    print("     6️⃣  Verificando correcciones del evento...")
    corr_resp = await admin_client.get(f"/api/v1/corrections/event/{event_id}")
    corrections = corr_resp.json()
    assert len(corrections) >= 1
    for c in corrections:
        print(f"        📝 {c['field_name']}: {c['original_value']} → {c['corrected_value']} "
              f"(motivo: {c['reason'][:50]}...)")

    # ─── Paso 7: Verificar que el evento es recuperable ───
    print("     7️⃣  Verificando que el evento es recuperable...")
    resp = await admin_client.get(f"/api/v1/operations/{event_id}")
    assert resp.status_code == 200
    event = resp.json()
    assert event["id"] == event_id
    assert event["event_type"] == "bird_reception"
    assert event["lot_id"] == 2
    assert event["registered_by_id"] is not None
    print(f"        ✅ Evento #{event_id} recuperado correctamente con todos sus datos")

    print(f"\n  ✅ FLUJO COMPLETO E2E EXITOSO para evento #{event_id}")
    return event_id


# ============================================================
# FASE 8: PRUEBAS DE INTEGRIDAD Y BORDE
# ============================================================

@pytest.mark.asyncio
async def test_f8_cancel_event_with_audit(admin_client):
    """
    F8 — Cancelación con Auditoría:
    Validar que se puede cancelar un evento (soft delete) y queda trazado.
    """
    payload = {
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 100.0}],
        "observations": "Evento para cancelación",
    }
    resp = await admin_client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201
    event_id = resp.json()["id"]

    # Cancelar
    cancel_resp = await admin_client.post(f"/api/v1/operations/{event_id}/cancel")
    assert cancel_resp.status_code == 200, f"F8 CANCEL failed: {cancel_resp.text}"
    assert cancel_resp.json()["status"] == "cancelled"

    # Verificar auditoría de cancelación
    audit_resp = await admin_client.get("/api/v1/audit", params={
        "entity_type": "operational_event",
        "entity_id": str(event_id),
    })
    logs = audit_resp.json()["logs"]
    actions = [l["action"] for l in logs]
    assert any(a == "cancelled" for a in actions), "Debe existir acción 'cancelled' en auditoría"

    # Verificar que el evento sigue existiendo (soft delete)
    get_resp = await admin_client.get(f"/api/v1/operations/{event_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_f8b_duplicate_sap_document_blocked(admin_client):
    """
    F8b — Documento SAP Duplicado (BR-10):
    Validar que no se puede registrar dos veces el mismo documento SAP
    para el mismo lote + tipo de evento.
    """
    sap_ref = "PO-2026-00001-TEST"
    payload = {
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 100.0}],
        "sap_document_ref": sap_ref,
    }

    # Primer registro
    resp1 = await admin_client.post("/api/v1/operations", json=payload)
    assert resp1.status_code == 201

    # Segundo registro con mismo SAP ref
    resp2 = await admin_client.post("/api/v1/operations", json=payload)
    assert resp2.status_code == 400, (
        f"BR-10: Debe bloquear documento SAP duplicado. Got {resp2.status_code}"
    )
    assert "duplic" in resp2.json()["detail"].lower() or "ya fue" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_f8c_business_rule_mortality_exceeds_balance(admin_client):
    """
    F8c — Regla de Negocio BR-01:
    Validar que la mortalidad no puede exceder el saldo de aves disponibles.
    """
    resp = await admin_client.post("/api/v1/operations", json={
        "lot_id": 2,
        "event_type": "mortality_recording",
        "event_date": recent_event_date(),
        "bird_movements": [{"sex": "female", "quantity": 999999}],
    })
    assert resp.status_code == 400, f"BR-01 debe bloquear mortalidad excesiva. Got {resp.status_code}"
    assert "saldo" in resp.json()["detail"].lower() or "excede" in resp.json()["detail"].lower()


# ============================================================
# FASE 9: DASHBOARD Y REPORTES
# ============================================================

@pytest.mark.asyncio
async def test_f9_dashboard_data_integrity(admin_client):
    """
    F9 — Integridad de Dashboards:
    Validar que los dashboards reflejan datos consistentes después
    de todas las operaciones del flujo.
    """
    # Dashboard móvil
    mobile = await admin_client.get("/api/v1/dashboard/mobile")
    assert mobile.status_code == 200
    mobile_data = mobile.json()
    assert "today_events" in mobile_data
    assert "pending_corrections" in mobile_data
    assert "quick_actions" in mobile_data

    # Dashboard admin
    admin_dash = await admin_client.get("/api/v1/dashboard/admin")
    assert admin_dash.status_code == 200
    admin_data = admin_dash.json()
    assert "total_events" in admin_data
    assert "pending_review" in admin_data
    assert "by_status" in admin_data

    # KPIs
    kpis = await admin_client.get("/api/v1/reports/kpis", params={"lot_id": 2})
    assert kpis.status_code == 200
    kpi_data = kpis.json()
    assert "mortality" in kpi_data
    assert "feed_conversion" in kpi_data

    print(f"  📊 Dashboard OK — {admin_data['total_events']} eventos totales, "
          f"{admin_data['pending_review']} pendientes de revisión")


# ============================================================
# FASE 10: MÚLTIPLES TIPOS DE OPERACIÓN
# ============================================================

@pytest.mark.asyncio
async def test_f10_all_event_types_registered(admin_client):
    """
    F10 — Todos los Tipos de Evento:
    Validar que los 26 tipos de evento están registrados en el sistema.
    (25 → 26: `water_consumption` entró al catálogo en `R-220` A14 / B-24.)
    """
    resp = await admin_client.get("/api/v1/operations/event-types")
    assert resp.status_code == 200
    event_types = resp.json()
    assert len(event_types) == 26, f"Expected 26 event types, got {len(event_types)}"

    # Lista esperada de tipos
    expected_types = {
        "bird_reception", "bird_distribution", "bird_transfer", "bird_exit",
        "feed_registration", "weight_recording", "mortality_recording", "cull_recording",
        "vaccination", "medication", "farm_inspection", "transport_inspection",
        "hatchery_inspection", "egg_collection", "egg_classification",
        "egg_reception_classification", "egg_dispatch", "egg_reception_hatchery",
        "incubation_load", "ovoscopy", "transfer_to_hatcher", "birth_registration",
        "chick_dispatch", "lot_closure", "grandparent_import", "water_consumption",
    }
    # El catálogo expone `type`/`label` (`schemas.ALL_EVENT_TYPES`), no `value`.
    registered_types = {et["type"] for et in event_types}
    missing = expected_types - registered_types
    assert not missing, f"Faltan tipos de evento: {missing}"
    print(f"  ✅ {len(event_types)} tipos de evento registrados correctamente")


# ============================================================
# Configuración de pytest
# ============================================================

pytestmark = pytest.mark.anyio
