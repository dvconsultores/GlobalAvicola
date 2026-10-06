"""SPEC 005 · Cliente HANA READ ONLY, configuración y adaptador — `AC-HANA-07…12`, `34`, `35`.

Ninguna prueba toca SAP: el driver es un doble (`FakeHana`) que imita `connect`, `cursor`,
`execute`, `description`, `fetchmany` y `close`, y resuelve las consultas contra el mismo
registry que usa el cliente real.
"""
from __future__ import annotations

import asyncio
import logging
import threading

import pytest

from app.integrations.sap.inbound.adapter import (
    HanaCloudReadOnlyAdapter,
    SapInboundAdapter,
    build_adapter,
)
from app.integrations.sap.inbound.client import SapHanaReadOnlyClient
from app.integrations.sap.inbound.errors import ErrorCode, SapInboundError
from app.integrations.sap.inbound.fake_hana import FakeHana, FakeHanaError, default_dataset
from app.integrations.sap.inbound.registry import HanaObject, get_definition, render_sql
from app.integrations.sap.inbound.settings import HanaSettings

SECRETO = "s3cr3t-P4ss!-no-debe-salir"


def _cfg(**cambios) -> HanaSettings:
    base = dict(host="hana.invalid", port=443, user="GA_RO_TEST", password=SECRETO,
                schema="SAPFAKE", client="100", environment="test")
    base.update(cambios)
    return HanaSettings(**base)


def _cliente(fake: FakeHana, **cambios) -> SapHanaReadOnlyClient:
    return SapHanaReadOnlyClient(_cfg(**cambios), connect_factory=fake.connect)


# ── Configuración ───────────────────────────────────────────────────────────

def test_hana_adapter_missing_credentials():
    """`AC-HANA-34`. Sin credenciales no hay excepción al construir: hay un estado legible."""
    cfg = HanaSettings(environment="test")
    assert cfg.configured is False
    assert {"SAP_HANA_HOST", "SAP_HANA_USER", "SAP_HANA_PASSWORD", "SAP_HANA_SCHEMA",
            "SAP_HANA_CLIENT"} <= set(cfg.missing())

    with pytest.raises(SapInboundError) as exc:
        cfg.connect_options()
    assert exc.value.code is ErrorCode.SAP_CONFIG_MISSING


async def test_hana_missing_credentials_never_reach_the_driver():
    fake = FakeHana()
    cliente = SapHanaReadOnlyClient(HanaSettings(environment="test"), connect_factory=fake.connect)
    with pytest.raises(SapInboundError) as exc:
        await cliente.ping()
    assert exc.value.code is ErrorCode.SAP_CONFIG_MISSING
    assert fake.connections_opened == 0, "sin configuración no se intenta conectar"


def test_hana_adapter_tls_required():
    """`AC-HANA-08`/`09`. Cifrado y validación de certificado, siempre y sin excepción."""
    opciones = _cfg().connect_options()
    assert opciones["encrypt"] is True
    assert opciones["sslValidateCertificate"] is True

    for cambio in ({"encrypt": False}, {"validate_certificate": False}):
        cfg = _cfg(**cambio)
        assert cfg.tls_violations(), cambio
        assert cfg.configured is False, "una configuración sin TLS no cuenta como configurada"
        with pytest.raises(SapInboundError) as exc:
            cfg.connect_options()
        assert exc.value.code is ErrorCode.SAP_TLS_ERROR


async def test_hana_tls_disabled_never_connects():
    fake = FakeHana()
    with pytest.raises(SapInboundError) as exc:
        await _cliente(fake, validate_certificate=False).ping()
    assert exc.value.code is ErrorCode.SAP_TLS_ERROR
    assert fake.connections_opened == 0


def test_hana_custom_ca_keeps_validation_on():
    opciones = _cfg(trust_store="/etc/ssl/certs/ga-sap-ca.pem").connect_options()
    assert opciones["sslTrustStore"] == "/etc/ssl/certs/ga-sap-ca.pem"
    assert opciones["sslValidateCertificate"] is True


def test_hana_timeouts_are_passed_to_the_driver():
    opciones = _cfg(connect_timeout=7, query_timeout=33).connect_options()
    assert opciones["connectTimeout"] == 7_000
    assert opciones["communicationTimeout"] == 33_000


# ── Conexión ────────────────────────────────────────────────────────────────

async def test_hana_connection_fake_success():
    fake = FakeHana()
    resultado = await _cliente(fake).ping()
    assert resultado == {"ok": 1}
    assert fake.executed[0][0] == 'SELECT 1 AS "ok" FROM DUMMY'
    assert fake.connect_kwargs[0]["encrypt"] is True
    assert fake.connect_kwargs[0]["sslValidateCertificate"] is True
    assert fake.connections_opened == fake.connections_closed == 1
    assert fake.cursors_opened == fake.cursors_closed == 1


async def test_hana_connection_fake_auth_error():
    fake = FakeHana()
    fake.fail_connect = FakeHanaError(10, f"authentication failed for user GA_RO_TEST pwd={SECRETO}")
    with pytest.raises(SapInboundError) as exc:
        await _cliente(fake).ping()
    assert exc.value.code is ErrorCode.SAP_AUTH_ERROR
    assert SECRETO not in str(exc.value) and SECRETO not in exc.value.message


@pytest.mark.parametrize("codigo_driver, esperado", [
    (10, ErrorCode.SAP_AUTH_ERROR),
    (258, ErrorCode.SAP_AUTHORIZATION_ERROR),
    (259, ErrorCode.SAP_OBJECT_NOT_FOUND),
    (260, ErrorCode.SAP_QUERY_CONTRACT_ERROR),
    (613, ErrorCode.SAP_QUERY_TIMEOUT),
    (-10709, ErrorCode.SAP_TEMPORARY_UNAVAILABLE),
    (-10807, ErrorCode.SAP_TEMPORARY_UNAVAILABLE),
    (99999, ErrorCode.SAP_INTERNAL_ERROR),
])
async def test_hana_driver_errors_are_classified(codigo_driver, esperado):
    fake = FakeHana()
    fake.fail_query["plant.v1"] = FakeHanaError(codigo_driver, "fallo simulado")
    with pytest.raises(SapInboundError) as exc:
        await _cliente(fake).fetch_page(
            get_definition(HanaObject.PLANT), {"mandt": "100", "bukrs": "1000"},
            limit=10, offset=0)
    assert exc.value.code is esperado
    assert fake.connections_opened == fake.connections_closed, "la conexión se cierra también al fallar"
    assert fake.cursors_opened == fake.cursors_closed


@pytest.mark.parametrize("texto, esperado", [
    ("getaddrinfo failed: Name or service not known", ErrorCode.SAP_DNS_ERROR),
    ("SSL certificate validation failed: unable to get local issuer", ErrorCode.SAP_TLS_ERROR),
])
async def test_hana_network_errors_are_classified(texto, esperado):
    fake = FakeHana()
    fake.fail_connect = FakeHanaError(-10709, texto)
    with pytest.raises(SapInboundError) as exc:
        await _cliente(fake).ping()
    assert exc.value.code is esperado


async def test_hana_secret_never_leaks(caplog):
    """`AC-HANA-07`. Ni el error, ni el log, ni el `repr` llevan la contraseña."""
    fake = FakeHana()
    fake.fail_connect = FakeHanaError(
        -10709, f"connect failed hdbsql://GA_RO_TEST:{SECRETO}@hana.invalid:443 password={SECRETO}")
    cfg = _cfg()
    cliente = SapHanaReadOnlyClient(cfg, connect_factory=fake.connect)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(SapInboundError) as exc:
            await cliente.ping()

    assert SECRETO not in exc.value.message
    assert SECRETO not in repr(exc.value)
    assert SECRETO not in caplog.text
    assert SECRETO not in repr(cfg) and SECRETO not in str(cfg)
    assert SECRETO not in repr(cliente)


# ── Ejecución ───────────────────────────────────────────────────────────────

async def test_hana_client_executes_registry_sql_with_bind_parameters():
    """`AC-HANA-12`. Lo que llega al driver es el SQL del registry y los valores aparte."""
    fake = FakeHana()
    d = get_definition(HanaObject.PLANT)
    hostil = "1000' OR '1'='1"
    filas = await _cliente(fake).fetch_page(d, {"mandt": "100", "bukrs": hostil}, limit=5, offset=0)

    sql, parametros = fake.executed[-1]
    assert sql == render_sql(d, "SAPFAKE")
    assert hostil not in sql, "el valor no se concatena"
    assert parametros["bukrs"] == hostil and parametros["mandt"] == "100"
    assert parametros["page_limit"] == 5 and parametros["page_offset"] == 0
    assert filas == [], "el valor hostil no casa con ninguna sociedad: es un dato, no SQL"


async def test_hana_client_rejects_unknown_or_missing_parameters():
    fake = FakeHana()
    d = get_definition(HanaObject.PLANT)
    for malos in ({"mandt": "100"}, {"mandt": "100", "bukrs": "1000", "sql": "DROP TABLE X"}):
        with pytest.raises(SapInboundError) as exc:
            await _cliente(fake).fetch_page(d, malos, limit=5, offset=0)
        assert exc.value.code is ErrorCode.SAP_QUERY_CONTRACT_ERROR
    assert fake.executed == []


async def test_hana_client_caps_page_size():
    fake = FakeHana()
    d = get_definition(HanaObject.PLANT)
    await _cliente(fake).fetch_page(d, {"mandt": "100", "bukrs": "1000"}, limit=10_000_000, offset=0)
    assert fake.executed[-1][1]["page_limit"] == d.max_page_size


async def test_hana_client_only_runs_registry_definitions():
    """No existe un método para ejecutar SQL libre."""
    cliente = _cliente(FakeHana())
    publicos = {n for n in dir(cliente) if not n.startswith("_")}
    assert publicos == {"ping", "fetch_page"}
    with pytest.raises((SapInboundError, TypeError, AttributeError)):
        await cliente.fetch_page("SELECT * FROM MATDOC", {}, limit=1, offset=0)  # type: ignore[arg-type]


async def test_hana_schema_mismatch_when_required_column_missing():
    """`§47`. Una columna obligatoria ausente es un error de contrato, no un `NULL`."""
    fake = FakeHana()
    fake.drop_columns["plant.v1"] = {"NAME1"}
    with pytest.raises(SapInboundError) as exc:
        await _cliente(fake).fetch_page(
            get_definition(HanaObject.PLANT), {"mandt": "100", "bukrs": "1000"}, limit=5, offset=0)
    assert exc.value.code is ErrorCode.SAP_SCHEMA_MISMATCH
    assert "NAME1" in exc.value.message


async def test_hana_optional_column_may_be_null():
    datos = default_dataset()
    datos["plant"][0]["NAME2"] = None
    fake = FakeHana(datos)
    filas = await _cliente(fake).fetch_page(
        get_definition(HanaObject.PLANT), {"mandt": "100", "bukrs": "1000"}, limit=50, offset=0)
    assert filas and filas[0]["NAME2"] is None


async def test_hana_rows_are_json_serializable():
    """RAW conserva la respuesta normalizada: fechas y decimales no llegan como objetos."""
    import json

    fake = FakeHana()
    filas = await _cliente(fake).fetch_page(
        get_definition(HanaObject.PURCHASE_ORDER_ITEM),
        {"mandt": "100", "bukrs": "1000", "doc_category": "F",
         "date_from": "20000101", "date_to": "20991231"}, limit=50, offset=0)
    assert filas
    json.dumps(filas)


async def test_hana_calls_do_not_block_the_event_loop():
    """`§11`. `hdbcli` es síncrono: se ejecuta fuera del bucle de eventos."""
    fake = FakeHana()
    fake.latency_seconds = 0.25
    hilo_del_bucle = threading.get_ident()
    latidos = 0

    async def latir():
        nonlocal latidos
        while True:
            await asyncio.sleep(0.01)
            latidos += 1

    tarea = asyncio.create_task(latir())
    await _cliente(fake).ping()
    tarea.cancel()

    assert latidos >= 5, "el bucle siguió atendiendo mientras HANA respondía"
    assert fake.threads_used and hilo_del_bucle not in fake.threads_used


async def test_hana_concurrency_is_bounded():
    fake = FakeHana()
    fake.latency_seconds = 0.05
    cliente = _cliente(fake, max_concurrency=2)
    await asyncio.gather(*[cliente.ping() for _ in range(8)])
    assert fake.max_concurrent_connections <= 2
    assert fake.connections_opened == fake.connections_closed == 8


# ── Adaptador ───────────────────────────────────────────────────────────────

async def test_hana_adapter_is_inbound_only_and_never_delivers():
    """El inbound es una interfaz aparte: no hereda ni imita la semántica de export."""
    from app.integrations.sap.adapter import SapIntegrationAdapter

    adaptador = HanaCloudReadOnlyAdapter(_cfg(), client=_cliente(FakeHana()))
    assert isinstance(adaptador, SapInboundAdapter)
    assert not isinstance(adaptador, SapIntegrationAdapter)
    assert not hasattr(adaptador, "export_consolidated")
    assert not hasattr(adaptador, "execute_sql")

    filas = await adaptador.fetch_page(
        HanaObject.COMPANY, {"mandt": "100", "bukrs": "1000"}, limit=10, offset=0)
    assert [f["BUKRS"] for f in filas] == ["1000"]


def test_fake_driver_is_refused_outside_development_and_test():
    """`Q10`. El doble no puede acabar atendiendo un entorno real."""
    for entorno in ("production", "staging", "uat"):
        with pytest.raises(SapInboundError) as exc:
            build_adapter(_cfg(driver="fake", environment=entorno))
        assert exc.value.code is ErrorCode.SAP_CONFIG_MISSING

    simulado = build_adapter(_cfg(driver="fake", environment="test"))
    assert simulado.simulated is True
    real = build_adapter(_cfg(driver="hdbcli", environment="production"))
    assert real.simulated is False


async def test_fake_hana_rejects_anything_outside_the_registry():
    """El doble es estricto: si el cliente enviara otra cosa, la prueba lo vería."""
    fake = FakeHana()
    conexion = fake.connect(**_cfg().connect_options())
    cursor = conexion.cursor()
    with pytest.raises(FakeHanaError):
        cursor.execute("UPDATE T001W SET NAME1 = 'x'", {})
    with pytest.raises(FakeHanaError):
        cursor.execute("SELECT * FROM MATDOC", {})
