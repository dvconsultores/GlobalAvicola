"""
GA-REM-014 — Tests de la guarda FAIL-CLOSED del entorno de pruebas.

Estos tests NO requieren base de datos: verifican la decisión de la guarda
sobre entornos simulados. Son la red de seguridad de la propia guarda: si
alguien la desactiva o la debilita, estos tests fallan.
"""
from __future__ import annotations

import pytest

from tests.environment_guard import (
    UnsafeTestEnvironment,
    evaluate,
    require_safe_test_environment,
)

VALID_ENV = {
    "GA_TEST_ENV": "1",
    "ENVIRONMENT": "test",
    "GA_TEST_DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/test_global_avicola",
}


# ── AC01 · La guarda impide ejecutar contra producción ────────────────────────

def test_rechaza_entorno_vacio():
    """Sin ninguna señal, la guarda rechaza. Fail-closed por defecto."""
    assert evaluate({}).allowed is False


def test_rechaza_sin_marcador_explicito():
    env = dict(VALID_ENV)
    del env["GA_TEST_ENV"]
    d = evaluate(env)
    assert d.allowed is False
    assert "marcador" in d.reason.lower()


@pytest.mark.parametrize("environment", ["production", "PRODUCTION", "prod", "staging", "preprod"])
def test_rechaza_environments_no_aptos(environment):
    """AC02 · ENVIRONMENT productivo o similar aborta la sesión."""
    env = dict(VALID_ENV, ENVIRONMENT=environment)
    d = evaluate(env)
    assert d.allowed is False
    assert "entorno no apto" in d.reason.lower()


def test_rechaza_sin_url_de_test():
    env = dict(VALID_ENV)
    del env["GA_TEST_DATABASE_URL"]
    d = evaluate(env)
    assert d.allowed is False
    assert "GA_TEST_DATABASE_URL" in d.reason


@pytest.mark.parametrize("db_name", ["avicolav2", "avicola", "globalavicola", "postgres"])
def test_rechaza_bases_prohibidas(db_name):
    """La base real de la aplicación jamás puede usarse como base de pruebas."""
    env = dict(
        VALID_ENV,
        GA_TEST_DATABASE_URL=f"postgresql+asyncpg://u:p@64.225.104.69:5432/{db_name}",
    )
    d = evaluate(env)
    assert d.allowed is False
    assert "prohibidas" in d.reason


@pytest.mark.parametrize("db_name", ["midb", "avicola_dev", "produccion", "app"])
def test_rechaza_nombres_que_no_son_de_test(db_name):
    """El nombre debe declararse como de pruebas: test_* o *_test."""
    env = dict(VALID_ENV, GA_TEST_DATABASE_URL=f"postgresql+asyncpg://u:p@h:5432/{db_name}")
    d = evaluate(env)
    assert d.allowed is False
    assert "patrón" in d.reason


def test_rechaza_colision_con_la_base_declarada_por_la_aplicacion(monkeypatch):
    """La base de pruebas no puede ser la que el fichero .env declara para la app.

    La comparación se hace contra el FICHERO de configuración, no contra la
    variable de entorno: el flujo legítimo sobrescribe DATABASE_URL tras
    validar, y compararla produciría un falso positivo.
    """
    from tests import environment_guard as guard

    url_app = "postgresql+asyncpg://u:p@h:5432/test_colision"
    monkeypatch.setattr(guard, "_configured_app_database_url", lambda: url_app)
    d = guard.evaluate(dict(VALID_ENV, GA_TEST_DATABASE_URL=url_app))
    assert d.allowed is False
    assert "coincide" in d.reason


def test_no_hay_falso_positivo_al_sobrescribir_database_url():
    """Regresión: tras validar, el flujo asigna DATABASE_URL a la base de test.

    Una segunda evaluación en la misma sesión debe seguir permitiendo.
    """
    url = VALID_ENV["GA_TEST_DATABASE_URL"]
    d = evaluate(dict(VALID_ENV, DATABASE_URL=url))
    assert d.allowed is True


def test_rechaza_url_sin_nombre_de_base():
    """Ante la imposibilidad de determinar la base, se aborta. Fail-closed."""
    d = evaluate(dict(VALID_ENV, GA_TEST_DATABASE_URL="postgresql+asyncpg://u:p@h:5432"))
    assert d.allowed is False


# ── Camino favorable ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("db_name", ["test_global_avicola", "test_ga", "avicola_test"])
def test_acepta_entorno_de_pruebas_valido(db_name):
    env = dict(VALID_ENV, GA_TEST_DATABASE_URL=f"postgresql+asyncpg://u:p@localhost:5432/{db_name}")
    d = evaluate(env)
    assert d.allowed is True
    assert d.database_name == db_name


def test_require_lanza_excepcion_con_entorno_inseguro():
    with pytest.raises(UnsafeTestEnvironment) as exc:
        require_safe_test_environment({})
    assert "EJECUCIÓN ABORTADA" in str(exc.value)
    assert "No se ha abierto ninguna conexión" in str(exc.value)


def test_require_devuelve_decision_con_entorno_valido():
    d = require_safe_test_environment(VALID_ENV)
    assert d.allowed is True
    assert d.database_name == "test_global_avicola"


# ── Regresión: la guarda no puede debilitarse en silencio ─────────────────────

def test_las_cinco_senales_son_obligatorias():
    """Quitar cualquiera de las señales debe bastar para rechazar."""
    for clave in ("GA_TEST_ENV", "GA_TEST_DATABASE_URL"):
        env = dict(VALID_ENV)
        del env[clave]
        assert evaluate(env).allowed is False, f"Quitar {clave} debería rechazar"
