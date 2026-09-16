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
