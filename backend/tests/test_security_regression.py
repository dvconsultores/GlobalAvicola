"""Regresión permanente de los defectos de seguridad de la Wave 2 — `R-43` y `R-32`.

Ambos están corregidos. Se fijan aquí porque su reaparición sería silenciosa: el sistema
seguiría respondiendo `200` en los dos casos, y ninguna suite funcional lo notaría.
"""

from __future__ import annotations

import pytest

from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio


# ── R-43 · el ciclo completo de sesión ────────────────────────────────────────

async def test_r43_login_refresh_y_peticion_autenticada(client, test_credentials):
    """`login → access → refresh → nuevo access → petición autenticada`.

    El refresco comparaba `sub` (cadena) con `User.id` (entero) y PostgreSQL rechazaba la
    comparación: **nunca funcionó**. Toda sesión moría al expirar el token de acceso.
    """
    usuario, password = test_credentials

    login = await client.post("/api/v1/login", json={"username": usuario, "password": password})
    assert login.status_code == 200, login.text
    assert {"access_token", "refresh_token"} <= set(login.json())

    renovado = await client.post("/api/v1/refresh",
                                 json={"refresh_token": login.json()["refresh_token"]})
    assert renovado.status_code == 200, f"El refresco debe funcionar: {renovado.text[:200]}"

    nuevo = {"Authorization": f"Bearer {renovado.json()['access_token']}"}
    yo = await client.get("/api/v1/me", headers=nuevo)
    assert yo.status_code == 200, "El token renovado debe autenticar"
    assert yo.json()["username"] == usuario


async def test_r43_el_contexto_sobrevive_a_la_renovacion(client, test_credentials):
    """`sub`, rol, compañía y vista deben seguir ahí: el frontend los lee del token."""
    import base64
    import json

    def claims(token: str) -> dict:
        carga = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(carga + "=" * (-len(carga) % 4)))

    usuario, password = test_credentials
    login = await client.post("/api/v1/login", json={"username": usuario, "password": password})
    renovado = await client.post("/api/v1/refresh",
                                 json={"refresh_token": login.json()["refresh_token"]})

    antes, despues = claims(login.json()["access_token"]), claims(renovado.json()["access_token"])
    for campo in ("sub", "username", "company_id", "role_id", "view_type"):
        assert despues.get(campo) == antes.get(campo), f"La renovación alteró '{campo}'"


async def test_r43_la_sesion_continua_con_el_acceso_caducado(client, test_credentials, monkeypatch):
    """Sesión larga, sin esperar media hora.

    Se emite un token de acceso ya caducado y se comprueba lo que importa: que la
    aplicación lo rechaza y que el token de refresco permite continuar.
    """
    from datetime import timedelta

    from app.auth.security import create_access_token

    usuario, password = test_credentials
    login = await client.post("/api/v1/login", json={"username": usuario, "password": password})
    refresco = login.json()["refresh_token"]

    caducado = create_access_token(data={"sub": "1"}, expires_delta=timedelta(seconds=-1))
    r = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {caducado}"})
    assert r.status_code == 401, "Un token de acceso caducado debe rechazarse"

    renovado = await client.post("/api/v1/refresh", json={"refresh_token": refresco})
    assert renovado.status_code == 200, "El refresco debe permitir continuar la sesión"

    sigue = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {renovado.json()['access_token']}"})
    assert sigue.status_code == 200


async def test_r43_un_refresco_invalido_se_rechaza(client, test_credentials):
    usuario, password = test_credentials
    login = await client.post("/api/v1/login", json={"username": usuario, "password": password})

    # Un token de **acceso** no sirve como token de refresco.
    r = await client.post("/api/v1/refresh",
                          json={"refresh_token": login.json()["access_token"]})
    assert r.status_code == 401, "Solo un token de refresco renueva la sesión"

    basura = await client.post("/api/v1/refresh", json={"refresh_token": "no-es-un-token"})
    assert basura.status_code == 401


async def test_r43_un_subject_no_numerico_se_rechaza_con_401(client):
    """El defecto original: `sub` llegaba como texto y reventaba contra la base.

    Debe traducirse a un 401 limpio, no a un error de base de datos.
    """
    from app.auth.security import create_refresh_token

    r = await client.post("/api/v1/refresh",
                          json={"refresh_token": create_refresh_token(data={"sub": "no-numerico"})})
    assert r.status_code == 401, f"Debe ser 401, no un 500: {r.status_code}"


# ── R-32 · inyección de estado ────────────────────────────────────────────────

@pytest.mark.parametrize("campo,valor", [
    ("status", "approved"),
    ("status", "sent_to_sap"),
    ("approved_by_id", 1),
    ("reviewed_by_id", 1),
    ("registered_by_id", 999),
    ("company_id", 999),
    ("version", 99),
])
async def test_r32_ningun_campo_de_flujo_es_fijable_por_put(
    auth_headers, http_client, seeded_ids, campo, valor
):
    """`PUT /operations/{id}` aprobaba sin revisión, sin segregación y sin aprobador."""
    creado = await http_client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": seeded_ids["lot_id"], "event_type": "feed_registration",
        "event_date": recent_event_date(), "feed_movements": [{"quantity_kg": 5.0}]})
    assert creado.status_code == 201, creado.text
    eid = creado.json()["id"]

    r = await http_client.put(f"/api/v1/operations/{eid}", headers=auth_headers,
                              json={campo: valor})
    assert r.status_code == 422, (
        f"'{campo}' no puede fijarse por PUT; debe rechazarse, no ignorarse: {r.status_code}")

    leido = await http_client.get(f"/api/v1/operations/{eid}", headers=auth_headers)
    assert leido.json()["status"] == "registered"
    assert leido.json()["approved_by_id"] is None


async def test_r32_el_estado_solo_avanza_por_el_flujo(auth_headers, client, seeded_ids):
    """La vía legítima sigue existiendo: enviar a revisión sí cambia el estado."""
    creado = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": seeded_ids["lot_id"], "event_type": "feed_registration",
        "event_date": recent_event_date(), "feed_movements": [{"quantity_kg": 5.0}]})
    eid = creado.json()["id"]

    enviado = await client.post(f"/api/v1/operations/{eid}/submit", headers=auth_headers)
    assert enviado.status_code == 200, enviado.text
    assert enviado.json()["status"] == "pending_review"


async def test_r32_ningun_esquema_de_escritura_expone_campos_de_flujo():
    """Barrido sobre los 49 esquemas: la clase de defecto, no solo su instancia.

    Detalle en `audit/remediation/UPDATE_SCHEMA_SECURITY_MATRIX.md`.
    """
    import importlib

    from pydantic import BaseModel

    gestionados = {"status", "approved_by_id", "reviewed_by_id", "registered_by_id",
                   "version", "hashed_password", "password"}
    # `password` es legítima al **crear** un usuario; lo que no puede es viajar en una
    # edición, que era el camino por el que `P0-13` mentía.
    permitidos_en_creacion = {"password"}

    infractores = []
    for modulo in ("auth", "masters", "operations", "lots", "review", "corrections"):
        try:
            m = importlib.import_module(f"app.{modulo}.schemas")
        except ModuleNotFoundError:
            continue
        for nombre, cls in vars(m).items():
            if not (isinstance(cls, type) and issubclass(cls, BaseModel) and cls is not BaseModel):
                continue
            if not any(k in nombre for k in ("Update", "Create", "Patch")):
                continue
            expuestos = set(cls.model_fields) & gestionados
            if "Create" in nombre:
                expuestos -= permitidos_en_creacion
            if expuestos:
                infractores.append(f"{modulo}.{nombre}: {sorted(expuestos)}")

    assert not infractores, (
        "Esquemas de escritura que exponen campos gestionados por el flujo o el sistema:\n  "
        + "\n  ".join(infractores))


async def test_r51_el_estado_del_lote_no_es_fijable_por_put(auth_headers, http_client, seeded_ids):
    """Misma clase que `R-32`, encontrada por el barrido: `LotUpdate` exponía `status`.

    Permitía cerrar un lote saltándose `close_lot` —sin precondición, sin resumen y sin
    `end_date`— y reabrir uno cerrado, con lo que volvían a admitirse movimientos contra
    él (`BR-07`).
    """
    r = await http_client.put(f"/api/v1/lots/{seeded_ids['lot_id']}", headers=auth_headers,
                              json={"status": "closed"})
    assert r.status_code == 422, (
        f"El estado del lote debe cambiar por su transición, no por PUT: {r.status_code}")

    leido = await http_client.get(f"/api/v1/lots/{seeded_ids['lot_id']}", headers=auth_headers)
    assert leido.json()["status"] == "active", "El lote no puede haber cambiado de estado"
