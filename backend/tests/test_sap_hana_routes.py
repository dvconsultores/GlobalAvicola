"""SPEC 005 · API interna `/sap/inbound/*`, RBAC, alcance, R-201 y fase READ ONLY.

`AC-HANA-04`, `05`, `10`, `34…39`. La API es de Global Avícola: ninguna ruta acepta SQL,
ninguna devuelve secretos y ninguna finge una conexión que no ha ocurrido.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from app.auth.security import create_access_token
from app.config import Settings, settings
from app.integrations.sap.inbound.fake_hana import FakeHana, FakeHanaError
from tests.sap_hana_fixtures import (  # noqa: F401  (`esc` es una fixture)
    SECRETO,
    adaptador_de_prueba,
    esc,
    escalar,
    filas,
    referencias,
)

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/sap/inbound"
RUTAS_INBOUND = {
    f"{BASE}/readiness", f"{BASE}/objects", f"{BASE}/sync", f"{BASE}/sync/{{object_type}}",
    f"{BASE}/jobs", f"{BASE}/records", f"{BASE}/errors", f"{BASE}/mappings",
    f"{BASE}/mappings/{{mapping_id}}",
}
VARIABLES = ("SAP_HANA_HOST", "SAP_HANA_USER", "SAP_HANA_PASSWORD", "SAP_HANA_SCHEMA",
             "SAP_HANA_CLIENT")


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest.fixture
def sin_credenciales(monkeypatch):
    for nombre in VARIABLES:
        monkeypatch.setattr(settings, nombre, "")
    monkeypatch.setattr(settings, "SAP_HANA_DRIVER", "hdbcli")


@pytest.fixture
def hana(monkeypatch, esc):  # noqa: F811
    """Configura la app contra el fake y devuelve el driver para inspeccionarlo."""
    fake = FakeHana(esc["datos"])
    monkeypatch.setattr(settings, "SAP_HANA_HOST", "hana.invalid")
    monkeypatch.setattr(settings, "SAP_HANA_USER", "GA_RO_TEST")
    monkeypatch.setattr(settings, "SAP_HANA_PASSWORD", SECRETO)
    monkeypatch.setattr(settings, "SAP_HANA_SCHEMA", "SAPFAKE")
    monkeypatch.setattr(settings, "SAP_HANA_CLIENT", esc["client"])
    monkeypatch.setattr(settings, "SAP_HANA_DRIVER", "fake")
    monkeypatch.setattr("app.integrations.sap.inbound.adapter.build_adapter",
                        lambda cfg: adaptador_de_prueba(fake, cfg))
    return fake


# ── Cobertura de arranque (`AC-HANA-37`, `38`) ───────────────────────────────

def test_sap_inbound_routes_exist_and_declare_authorization():
    from app.authorization_coverage import enumerar_rutas, permiso_declarado, rutas_sin_autorizacion
    from app.main import app

    rutas = {c: (m, r) for c, m, r in enumerar_rutas(app) if c.startswith(BASE)}
    assert set(rutas) == RUTAS_INBOUND
    assert rutas_sin_autorizacion(app) == []

    for camino, metodos, ruta in enumerar_rutas(app):
        if not camino.startswith(BASE):
            continue
        modulo, accion = permiso_declarado(ruta)
        assert modulo == "sap", camino
        esperado = "read" if metodos == ["GET"] else "send_sap"
        assert accion == esperado, f"{metodos} {camino}: {accion}"


def test_sap_inbound_routes_scope_declared():
    from app.business_units.route_scope import Alcance, clasificar, rutas_sin_clasificar
    from app.business_units.sap_contract import SUPERFICIES_TRANSVERSALES
    from app.main import app

    assert rutas_sin_clasificar(app) == []
    control = {f"{BASE}/readiness", f"{BASE}/objects", f"{BASE}/mappings",
               f"{BASE}/mappings/{{mapping_id}}"}
    for camino in RUTAS_INBOUND:
        alcance, unidad = clasificar(camino)
        assert unidad is None
        assert alcance is (Alcance.CONTROL if camino in control else Alcance.CONTRATO), camino
        assert (camino in SUPERFICIES_TRANSVERSALES) is (camino not in control), camino


def test_sap_inbound_transaction_coverage():
    from app.main import app
    from app.transaction import rutas_sin_frontera

    assert rutas_sin_frontera(app) == []


# ── Sin SQL desde HTTP (`AC-HANA-04`, `10`) ──────────────────────────────────

async def test_hana_no_raw_sql_endpoint(http_client, esc, hana):
    from app.main import app

    esquema = app.openapi()
    sospechosos = {"sql", "query", "statement", "sql_template", "raw_sql", "schema", "table"}
    for camino, operaciones in esquema["paths"].items():
        if "/sap/" not in camino:
            continue
        assert not any(p in camino.lower() for p in ("execute", "sql", "query")), camino
        for operacion in operaciones.values():
            nombres = {p["name"].lower() for p in operacion.get("parameters", [])}
            assert not (nombres & sospechosos), f"{camino}: {nombres & sospechosos}"

    cab = _token(esc["ids"]["analista_a"])
    for cuerpo in ({"sql": "SELECT * FROM MATDOC"}, {"query": "DROP TABLE T001W"},
                   {"schema": "OTRO"}, {"object_types": ["plant"], "where": "1=1"}):
        r = await http_client.post(f"{BASE}/sync", headers=cab, json=cuerpo)
        assert r.status_code == 422, f"{cuerpo}: {r.status_code} {r.text}"
    for libre in ("select", "T001W", "plant;drop", "MATDOC"):
        r = await http_client.post(f"{BASE}/sync/{libre}", headers=cab, json={})
        assert r.status_code in (404, 422), f"{libre}: {r.status_code}"
    assert hana.connections_opened == 0


# ── RBAC (`AC-HANA-36`) ──────────────────────────────────────────────────────

async def test_sap_inbound_routes_rbac(http_client, esc, hana):
    lector, ajeno, analista = (_token(esc["ids"][k]) for k in ("lector_a", "ajeno_a", "analista_a"))

    for camino in ("readiness", "objects", "jobs", "records", "errors", "mappings"):
        assert (await http_client.get(f"{BASE}/{camino}", headers=lector)).status_code == 200, camino
        assert (await http_client.get(f"{BASE}/{camino}", headers=ajeno)).status_code == 403, camino
        assert (await http_client.get(f"{BASE}/{camino}")).status_code == 401, camino

    for metodo, camino, cuerpo in (
        ("post", "sync", {}), ("post", "sync/plant", {}),
        ("put", "mappings", {"entity_type": "PLANT", "sap_key": "1300", "parent_sap_key": "1000"}),
        ("delete", "mappings/1", None),
    ):
        kw = {"json": cuerpo} if cuerpo is not None else {}
        for cab in (lector, ajeno):
            r = await getattr(http_client, metodo)(f"{BASE}/{camino}", headers=cab, **kw)
            assert r.status_code == 403, f"{metodo} {camino}: leer no autoriza operar"
    assert hana.connections_opened == 0, "una operación denegada no llega a HANA"

    r = await http_client.post(f"{BASE}/sync/plant", headers=analista, json={})
    assert r.status_code == 200, r.text


# ── Sync por HTTP y lecturas ─────────────────────────────────────────────────

async def test_sync_endpoint_runs_and_reports(http_client, esc, hana):
    cab = _token(esc["ids"]["analista_a"])
    r = await http_client.post(f"{BASE}/sync/plant", headers=cab, json={})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["sync_request_id"] and len(cuerpo["jobs"]) == 1
    job = cuerpo["jobs"][0]
    assert (job["object_type"], job["status"], job["rows_read"]) == ("plant", "completed", 2)
    assert job["rows_promoted"] == 1 and job["rows_pending_mapping"] == 1

    # La respuesta salió con la transacción confirmada (`GA-REM-026`).
    assert await escalar(esc, "SELECT count(*) FROM sap_inbound_records WHERE company_id = :c",
                         c=esc["a"]) == 2
    assert [x["sap_code"] for x in await referencias(esc, "PLANT")] == ["1100"]

    jobs = (await http_client.get(f"{BASE}/jobs", headers=cab)).json()
    assert jobs["total"] == 1 and jobs["jobs"][0]["id"] == job["id"]

    registros = (await http_client.get(f"{BASE}/records?object_type=plant", headers=cab)).json()
    assert registros["total"] == 2
    assert {x["source_key"] for x in registros["records"]} == {
        f"{esc['client']}|1100", f"{esc['client']}|1200"}
    pendientes = (await http_client.get(
        f"{BASE}/records?mapping_status=PENDING_MAPPING", headers=cab)).json()
    assert [x["plant_code"] for x in pendientes["records"]] == ["1200"]

    errores = (await http_client.get(f"{BASE}/errors", headers=cab)).json()
    assert [x["error_code"] for x in errores["records"]] == ["SAP_MAPPING_PENDING"]
    assert SECRETO not in r.text + str(jobs) + str(registros) + str(errores)


async def test_sync_all_endpoint(http_client, esc, hana):
    r = await http_client.post(f"{BASE}/sync", headers=_token(esc["ids"]["analista_a"]),
                               json={"date_from": "2000-01-01", "date_to": "2000-12-31"})
    assert r.status_code == 200, r.text
    assert len(r.json()["jobs"]) == 14
    r = await http_client.post(f"{BASE}/sync", headers=_token(esc["ids"]["analista_a"]),
                               json={"date_from": "2000-01-01", "date_to": "2026-01-01"})
    assert r.status_code == 422, "ventana de años: rechazada antes de tocar HANA"


async def test_failed_sync_is_reported_not_raised(http_client, esc, hana):
    hana.fail_connect = FakeHanaError(10, f"authentication failed password={SECRETO}")
    cab = _token(esc["ids"]["analista_a"])
    r = await http_client.post(f"{BASE}/sync/plant", headers=cab, json={})
    assert r.status_code == 200, "el fallo de SAP es un resultado auditado, no un 500"
    job = r.json()["jobs"][0]
    assert (job["status"], job["error_code"]) == ("failed", "SAP_AUTH_ERROR")
    errores = (await http_client.get(f"{BASE}/errors", headers=cab)).json()
    assert errores["jobs"] and errores["jobs"][0]["error_code"] == "SAP_AUTH_ERROR"
    assert SECRETO not in r.text and SECRETO not in str(errores)
    assert "Traceback" not in r.text


async def test_objects_catalog_is_served_without_sql(http_client, esc, hana):
    r = await http_client.get(f"{BASE}/objects", headers=_token(esc["ids"]["lector_a"]))
    assert r.status_code == 200
    objetos = r.json()["objects"]
    assert len(objetos) == 14
    for o in objetos:
        assert {"object_type", "query_id", "tables", "source_status", "strategy",
                "promotes_to"} <= set(o)
        assert "sql" not in o and "sql_template" not in o
    assert "SELECT" not in r.text.upper()


# ── R-201 · aislamiento de contexto (`AC-HANA-39`) ───────────────────────────

async def test_r201_global_authority_without_context_sees_nothing(http_client, esc, hana):
    await http_client.post(f"{BASE}/sync/plant", headers=_token(esc["ids"]["analista_a"]), json={})
    abiertas = hana.connections_opened
    sin_contexto = _token(esc["ids"]["global"])

    for camino, clave in (("jobs", "jobs"), ("records", "records"), ("mappings", "mappings")):
        r = await http_client.get(f"{BASE}/{camino}", headers=sin_contexto)
        assert r.status_code == 200 and r.json()[clave] == [], f"{camino}: {r.text}"
    r = await http_client.get(f"{BASE}/errors", headers=sin_contexto)
    assert r.json() == {"records": [], "jobs": []}

    for camino in ("sync", "sync/plant"):
        r = await http_client.post(f"{BASE}/{camino}", headers=sin_contexto, json={})
        assert r.status_code == 400, f"{camino}: {r.status_code}"
    r = await http_client.put(f"{BASE}/mappings", headers=sin_contexto,
                              json={"entity_type": "COMPANY_CODE", "sap_key": "3000"})
    assert r.status_code == 400
    assert hana.connections_opened == abiertas, "sin contexto no se toca HANA"


async def test_r201_company_actor_only_sees_its_company(http_client, esc, hana):
    await http_client.post(f"{BASE}/sync/plant", headers=_token(esc["ids"]["analista_a"]), json={})
    de_b = _token(esc["ids"]["analista_b"])
    assert (await http_client.get(f"{BASE}/records", headers=de_b)).json()["records"] == []
    assert (await http_client.get(f"{BASE}/jobs", headers=de_b)).json()["jobs"] == []
    mappings = (await http_client.get(f"{BASE}/mappings", headers=de_b)).json()["mappings"]
    assert {m["sap_key"] for m in mappings} == {"2000", "2100"}

    situada = _token(esc["ids"]["global"], esc["a"])
    assert (await http_client.get(f"{BASE}/records", headers=situada)).json()["total"] == 2


# ── Mappings (`Q5`) ──────────────────────────────────────────────────────────

async def test_company_code_mapping_requires_global_authority(http_client, esc, hana):
    analista, situada = _token(esc["ids"]["analista_a"]), _token(esc["ids"]["global"], esc["a"])
    cuerpo = {"entity_type": "COMPANY_CODE", "sap_key": "3000"}

    r = await http_client.put(f"{BASE}/mappings", headers=analista, json=cuerpo)
    assert r.status_code == 403, "enlazar un inquilino con una sociedad no es tarea del analista"
    r = await http_client.put(f"{BASE}/mappings", headers=situada, json=cuerpo)
    assert r.status_code == 200, r.text
    assert r.json()["company_id"] == esc["a"] and r.json()["client"] == esc["client"]


async def test_plant_mapping_stays_inside_the_company(http_client, esc, hana):
    analista = _token(esc["ids"]["analista_a"])
    r = await http_client.put(f"{BASE}/mappings", headers=analista, json={
        "entity_type": "PLANT", "sap_key": "1200", "parent_sap_key": "1000"})
    assert r.status_code == 200, r.text
    propio = r.json()["id"]

    # Un centro bajo la sociedad de otra empresa, o ya asignado a otra: cerrado.
    r = await http_client.put(f"{BASE}/mappings", headers=analista, json={
        "entity_type": "PLANT", "sap_key": "2200", "parent_sap_key": "2000"})
    assert r.status_code == 409, r.text
    r = await http_client.put(f"{BASE}/mappings", headers=analista, json={
        "entity_type": "PLANT", "sap_key": "2100", "parent_sap_key": "1000"})
    assert r.status_code == 409, "2100 ya pertenece a la empresa B"
    r = await http_client.put(f"{BASE}/mappings", headers=analista, json={
        "entity_type": "PLANT", "sap_key": "1300", "parent_sap_key": "1000",
        "farm_id": 999_999_999})
    assert r.status_code in (400, 404), "la granja debe ser de la empresa"
    r = await http_client.put(f"{BASE}/mappings", headers=analista, json={
        "entity_type": "GALPON", "sap_key": "1"})
    assert r.status_code == 422

    ajeno = (await filas(esc, "SELECT id FROM sap_entity_mappings WHERE company_id = :c LIMIT 1",
                         c=esc["b"]))[0]["id"]
    assert (await http_client.delete(f"{BASE}/mappings/{ajeno}", headers=analista)).status_code == 404
    assert (await http_client.delete(f"{BASE}/mappings/{propio}", headers=analista)).status_code == 200
    assert await escalar(esc, "SELECT count(*) FROM sap_entity_mappings WHERE company_id = :c",
                         c=esc["b"]) == 2


# ── Readiness y connection-check (`AC-HANA-34`, `35`) ────────────────────────

async def test_readiness_works_without_credentials(http_client, esc, sin_credenciales):
    r = await http_client.get(f"{BASE}/readiness", headers=_token(esc["ids"]["lector_a"]))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["phase"] == "READ_ONLY_INBOUND"
    assert d["configured"] is False and d["connection_tested"] is False and d["connected"] is False
    assert set(VARIABLES) <= set(d["missing"])
    assert d["status"] == "PENDING_CREDENTIALS"
    assert d["outbound_enabled"] is False and d["write_operations_allowed"] is False
    assert d["tls"] == {"encrypt": True, "validate_certificate": True}
    assert isinstance(d["driver_available"], bool)


async def test_readiness_never_returns_secret_values(http_client, esc, hana):
    r = await http_client.get(f"{BASE}/readiness", headers=_token(esc["ids"]["lector_a"]))
    d = r.json()
    assert d["configured"] is True and d["missing"] == []
    assert d["simulated"] is True, "el fake se declara como tal"
    assert d["connected"] is False, "configurado no es conectado"
    for prohibido in (SECRETO, "GA_RO_TEST", "hana.invalid"):
        assert prohibido not in r.text


async def test_connection_check_does_not_fake_a_connection(http_client, esc, sin_credenciales):
    r = await http_client.get("/api/v1/sap/connection-check",
                              headers=_token(esc["ids"]["lector_a"]))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["inbound_hana"]["configured"] is False and d["inbound_hana"]["connected"] is False
    assert d["inbound_hana"]["status"] == "PENDING_CREDENTIALS"
    assert d["outbound"] == {"enabled": False, "delivers_to_sap": False,
                             "mode": "disabled_read_only_phase", "adapter": d["outbound"]["adapter"]}
    assert d["connected"] is False and d["delivers_to_sap"] is False


async def test_connection_check_with_fake_is_declared_simulated(http_client, esc, hana):
    r = await http_client.get("/api/v1/sap/connection-check",
                              headers=_token(esc["ids"]["lector_a"]))
    d = r.json()
    assert hana.executed[0][0] == 'SELECT 1 AS "ok" FROM DUMMY', "la primera consulta es la de humo"
    assert len(hana.executed) == 1, "y no dispara consultas de volumen"
    assert d["inbound_hana"]["connected"] is True and d["inbound_hana"]["simulated"] is True
    assert d["connected"] is False, "un simulador no es una conexión real a SAP"
    assert SECRETO not in r.text


async def test_connection_check_reports_auth_error(http_client, esc, hana):
    hana.fail_connect = FakeHanaError(10, f"authentication failed password={SECRETO}")
    r = await http_client.get("/api/v1/sap/connection-check",
                              headers=_token(esc["ids"]["lector_a"]))
    d = r.json()
    assert r.status_code == 200
    assert d["inbound_hana"]["connected"] is False
    assert d["inbound_hana"]["error_code"] == "SAP_AUTH_ERROR"
    assert SECRETO not in r.text


# ── Fase READ ONLY: outbound deshabilitado (`AC-HANA-05`) ────────────────────

def test_outbound_is_disabled_by_default():
    assert Settings.model_fields["SAP_OUTBOUND_ENABLED"].default is False
    assert settings.SAP_OUTBOUND_ENABLED is False
    assert Settings.model_fields["SAP_HANA_SYNC_ENABLED"].default is False
    assert Settings.model_fields["SAP_HANA_ENCRYPT"].default is True
    assert Settings.model_fields["SAP_HANA_SSL_VALIDATE_CERTIFICATE"].default is True
    for nombre in VARIABLES:
        assert Settings.model_fields[nombre].default == "", f"{nombre} no trae valor por defecto"


async def test_outbound_disabled(http_client, esc):
    cab = _token(esc["ids"]["analista_a"])
    for camino in ("export", "retry"):
        r = await http_client.post(f"/api/v1/sap/{camino}", headers=cab, json={})
        assert r.status_code == 409, f"{camino}: {r.status_code} {r.text}"
        assert r.json()["detail"]["code"] == "SAP_OUTBOUND_DISABLED_READ_ONLY_PHASE"
    assert await escalar(esc, "SELECT count(*) FROM sap_sync_jobs WHERE company_id = :c",
                         c=esc["a"]) == 0, "no se crea ni el job de exportación"
    assert await escalar(esc, "SELECT count(*) FROM sap_payloads WHERE company_id = :c",
                         c=esc["a"]) == 0


async def test_outbound_disabled_does_not_touch_failed_payloads(http_client, esc):
    async with esc["fabrica"]() as s:
        await s.execute(text(
            "INSERT INTO sap_payloads (company_id, idempotency_key, payload_data, status, "
            "retry_count, max_retries) VALUES (:c, :k, CAST('{}' AS jsonb), 'FAILED', 0, 3)"),
            {"c": esc["a"], "k": f"hana5-{esc['client']}-{esc['serie']}"})
        await s.commit()
    r = await http_client.post("/api/v1/sap/retry", headers=_token(esc["ids"]["analista_a"]), json={})
    assert r.status_code == 409
    assert await escalar(esc, "SELECT status::text || ':' || retry_count FROM sap_payloads "
                              "WHERE company_id = :c", c=esc["a"]) == "FAILED:0"
    async with esc["fabrica"]() as s:
        await s.execute(text("DELETE FROM sap_payloads WHERE company_id = :c"), {"c": esc["a"]})
        await s.commit()


async def test_delivers_to_sap_false(http_client, esc, sin_credenciales):
    from app.integrations.sap.adapter import ManualSapAdapter, MockSapAdapter
    from app.integrations.sap.inbound.adapter import HanaCloudReadOnlyAdapter

    assert ManualSapAdapter.delivers_to_sap is False and MockSapAdapter.delivers_to_sap is False
    assert getattr(HanaCloudReadOnlyAdapter, "delivers_to_sap", False) is False

    r = await http_client.get("/api/v1/sap/connection-check",
                              headers=_token(esc["ids"]["lector_a"]))
    assert r.json()["delivers_to_sap"] is False and r.json()["outbound"]["delivers_to_sap"] is False


async def test_real_outbound_adapter_stays_unimplemented(http_client, esc, monkeypatch):
    """`Q12`. Reabrir la ruta de artefacto no convierte nada en una entrega real."""
    monkeypatch.setattr(settings, "SAP_OUTBOUND_ENABLED", True)
    monkeypatch.setattr(settings, "SAP_ADAPTER", "real")
    r = await http_client.get("/api/v1/sap/connection-check",
                              headers=_token(esc["ids"]["analista_a"]))
    assert r.status_code in (200, 501)
    if r.status_code == 200:
        assert r.json()["delivers_to_sap"] is False


# ── Arranque sin credenciales (`FR-01`) ──────────────────────────────────────

async def test_app_starts_and_serves_health_without_sap_credentials(http_client, sin_credenciales):
    r = await http_client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
