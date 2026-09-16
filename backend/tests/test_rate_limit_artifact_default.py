"""G-03 / T13 — el artefacto desplegado debe activar el rate limit del login por defecto.

Contexto: el contenedor desplegado no recibe `.env` (no se copia en la imagen) ni la
variable de entorno; su comportamiento lo fija el **default del código**. Un default
inseguro (`False`) dejaba `@rate_limit("5/minute")` como no-op en el runtime compartido
(evidencia G-03: 12×401 sin 429, 16 de septiembre de 2026). Este test fija el contrato:
el default es seguro (ON) y el compose de despliegue lo inyecta igualmente con
default `true`. `development` desactiva el flag explícitamente en su `.env`.
"""

from pathlib import Path

from app.config import Settings


def test_el_default_del_artefacto_activa_el_rate_limit(monkeypatch) -> None:
    """Sin override de entorno ni `.env`: el default del código debe ser ON."""
    monkeypatch.delenv("FEATURE_RATE_LIMIT_ENABLED", raising=False)
    s = Settings(
        _env_file=None,
        JWT_SECRET_KEY="x" * 64,
        DATABASE_URL="postgresql+asyncpg://usuario:clave@localhost:5432/base",
    )
    assert s.FEATURE_RATE_LIMIT_ENABLED is True


def test_el_compose_de_despliegue_inyecta_el_flag_con_default_true() -> None:
    """El compose versionado declara el flag con default `true` (fail-safe)."""
    compose = Path(__file__).resolve().parents[2] / "docker-compose.yml"
    texto = compose.read_text(encoding="utf-8")
    assert "FEATURE_RATE_LIMIT_ENABLED: ${FEATURE_RATE_LIMIT_ENABLED:-true}" in texto


def test_el_limitador_no_puede_desactivarse_por_un_false_heredado_en_produccion() -> None:
    """En entornos no-dev el limitador está SIEMPRE activo (G-03/T13): un `false`
    heredado en el runtime del contenedor no puede desactivar la protección
    anti fuerza bruta del login."""
    from types import SimpleNamespace

    from app.main import resolve_rate_limit_active

    cfg = SimpleNamespace(ENVIRONMENT="production", FEATURE_RATE_LIMIT_ENABLED=False)
    assert resolve_rate_limit_active(cfg, en_contenedor=False, test_env=False) is True


def test_el_artefacto_desplegado_en_contenedor_fuerza_el_limitador() -> None:
    """Dentro de un contenedor desplegado el limitador está SIEMPRE activo, aunque
    el contenedor herede `ENVIRONMENT=development` y `FEATURE_RATE_LIMIT_ENABLED=false`
    del `.env` del servidor (herencia de la recreación)."""
    from types import SimpleNamespace

    from app.main import resolve_rate_limit_active

    dev = SimpleNamespace(ENVIRONMENT="development", FEATURE_RATE_LIMIT_ENABLED=False)
    assert resolve_rate_limit_active(dev, en_contenedor=True, test_env=False) is True

    test = SimpleNamespace(ENVIRONMENT="test", FEATURE_RATE_LIMIT_ENABLED=False)
    assert resolve_rate_limit_active(test, en_contenedor=True, test_env=False) is True


def test_el_limitador_sigue_desactivable_en_desarrollo_y_pruebas() -> None:
    """`development`/`test` fuera de contenedor conservan el control explícito del flag;
    `GA_TEST_ENV=1` (guardas de suites locales) tiene precedencia incluso en contenedor."""
    from types import SimpleNamespace

    from app.main import resolve_rate_limit_active

    dev_off = SimpleNamespace(ENVIRONMENT="development", FEATURE_RATE_LIMIT_ENABLED=False)
    assert resolve_rate_limit_active(dev_off, en_contenedor=False, test_env=False) is False

    test_off = SimpleNamespace(ENVIRONMENT="test", FEATURE_RATE_LIMIT_ENABLED=False)
    assert resolve_rate_limit_active(test_off, en_contenedor=False, test_env=False) is False

    dev_on = SimpleNamespace(ENVIRONMENT="development", FEATURE_RATE_LIMIT_ENABLED=True)
    assert resolve_rate_limit_active(dev_on, en_contenedor=False, test_env=False) is True

    assert resolve_rate_limit_active(dev_off, en_contenedor=True, test_env=True) is False
