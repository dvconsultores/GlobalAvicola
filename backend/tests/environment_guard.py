"""
Guarda FAIL-CLOSED del entorno de pruebas.

Entregable de GA-REM-014.

Principio (§16 del encargo de Wave 1):

    Si existe cualquier duda sobre la identidad de la base de datos,
    NO SE EJECUTAN LOS TESTS.

Nunca se emite un aviso y se continúa. Ante duda, se aborta.

La guarda evalúa cinco señales independientes y **todas** deben ser favorables:

    1. ENVIRONMENT no puede ser un entorno productivo.
    2. Debe existir un marcador explícito de test (GA_TEST_ENV=1).
    3. La URL de la base de datos debe estar definida en GA_TEST_DATABASE_URL.
    4. El nombre de la base debe coincidir con el patrón de test exigido.
    5. La base de pruebas no puede coincidir con la que declara el fichero de
       configuración de la aplicación (`backend/.env`), que apunta al entorno
       real. Se lee del fichero y no de la variable de entorno, porque el
       propio flujo de pruebas sobrescribe `DATABASE_URL` tras validar.

Cualquier señal ausente, ambigua o desconocida => ABORTA.
"""
from __future__ import annotations

import os
import pathlib
import re
from dataclasses import dataclass
from urllib.parse import urlparse

# ── Configuración de la guarda ────────────────────────────────────────────────

#: Marcador explícito que el ejecutor debe declarar de forma consciente.
TEST_MARKER_ENV = "GA_TEST_ENV"

#: Variable que transporta la URL de la base de datos desechable.
TEST_DB_URL_ENV = "GA_TEST_DATABASE_URL"

#: El nombre de la base de datos de pruebas DEBE casar con este patrón.
#: Evita que una base productiva o de desarrollo sea aceptada por descuido.
TEST_DB_NAME_PATTERN = re.compile(r"^(test_|.*_test$)", re.IGNORECASE)

#: Valores de ENVIRONMENT que impiden la ejecución de pruebas.
FORBIDDEN_ENVIRONMENTS = {"production", "prod", "staging", "pre", "preprod"}

#: Nombres de base de datos que jamás pueden usarse como base de pruebas.
FORBIDDEN_DB_NAMES = {"avicolav2", "avicola", "globalavicola", "postgres"}


def _configured_app_database_url() -> str:
    """DSN que el fichero `.env` de la aplicación declara, si existe.

    Es el destino real de la aplicación —el que jamás debe recibir escrituras
    de pruebas—, y no cambia aunque el proceso sobrescriba la variable.
    """
    env_file = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return ""
    try:
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        # Ante la imposibilidad de leer la configuración, no se relaja nada:
        # las señales 1-4 siguen aplicándose.
        return ""
    return ""


class UnsafeTestEnvironment(RuntimeError):
    """La guarda ha rechazado la ejecución. No se ha tocado ninguna base."""


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    reason: str
    database_url: str | None = None
    database_name: str | None = None


def _parse_db_name(url: str) -> str | None:
    """Extrae el nombre de la base de una URL de conexión, o None si no se puede."""
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    path = (parsed.path or "").lstrip("/")
    if not path:
        return None
    return path.split("?", 1)[0] or None


def _parse_host(url: str) -> str | None:
    try:
        return urlparse(url).hostname
    except Exception:
        return None


def evaluate(env: dict[str, str] | None = None) -> GuardDecision:
    """Evalúa el entorno y devuelve la decisión. No lanza excepciones."""
    env = dict(os.environ if env is None else env)

    # Señal 1 — ENVIRONMENT no puede ser productivo ni similar.
    environment = (env.get("ENVIRONMENT") or "").strip().lower()
    if environment in FORBIDDEN_ENVIRONMENTS:
        return GuardDecision(
            False,
            f"ENVIRONMENT='{environment}' es un entorno no apto para pruebas.",
        )

    # Señal 2 — marcador explícito de test.
    if env.get(TEST_MARKER_ENV) != "1":
        return GuardDecision(
            False,
            f"Falta el marcador explícito {TEST_MARKER_ENV}=1. "
            "La ejecución de pruebas debe declararse de forma consciente.",
        )

    # Señal 3 — URL de la base de pruebas declarada por separado.
    test_url = (env.get(TEST_DB_URL_ENV) or "").strip()
    if not test_url:
        return GuardDecision(
            False,
            f"{TEST_DB_URL_ENV} no está definida. "
            "Los tests nunca usan la DATABASE_URL de la aplicación.",
        )

    db_name = _parse_db_name(test_url)
    host = _parse_host(test_url)

    # Señal 4 — el nombre de la base debe declararse como de pruebas.
    if not db_name:
        return GuardDecision(
            False,
            f"No se pudo determinar el nombre de la base en {TEST_DB_URL_ENV}. "
            "Ante la duda, no se ejecutan pruebas.",
            test_url,
            db_name,
        )
    if db_name.lower() in FORBIDDEN_DB_NAMES:
        return GuardDecision(
            False,
            f"La base '{db_name}' está en la lista de bases prohibidas para pruebas.",
            test_url,
            db_name,
        )
    if not TEST_DB_NAME_PATTERN.match(db_name):
        return GuardDecision(
            False,
            f"La base '{db_name}' no cumple el patrón exigido "
            "(debe empezar por 'test_' o terminar en '_test').",
            test_url,
            db_name,
        )

    # Señal 5 — no puede coincidir con la base declarada por la aplicación.
    #
    # Se lee del FICHERO de configuración, no de la variable de entorno: el
    # flujo legítimo de pruebas (`conftest.pytest_configure`, `test_seeds.main`)
    # asigna `DATABASE_URL` a la base desechable **después** de validar, y
    # comparar contra la variable produciría un falso positivo en cualquier
    # invocación posterior dentro de la misma sesión.
    app_url = _configured_app_database_url()
    if app_url:
        app_db = _parse_db_name(app_url)
        app_host = _parse_host(app_url)
        if app_db and db_name and app_db == db_name and app_host == host:
            return GuardDecision(
                False,
                "La base de pruebas coincide con la que declara la configuración "
                f"de la aplicación ({host or 'sin-host'}/{db_name}).",
                test_url,
                db_name,
            )

    return GuardDecision(
        True,
        f"Entorno de pruebas validado: {host or 'sin-host'}/{db_name}",
        test_url,
        db_name,
    )


def require_safe_test_environment(env: dict[str, str] | None = None) -> GuardDecision:
    """Aplica la guarda. Aborta si el entorno no es inequívocamente de pruebas."""
    decision = evaluate(env)
    if not decision.allowed:
        raise UnsafeTestEnvironment(
            "\n"
            "══════════════════════════════════════════════════════════════\n"
            "  GA-REM-014 · GUARDA DE ENTORNO — EJECUCIÓN ABORTADA\n"
            "══════════════════════════════════════════════════════════════\n"
            f"  {decision.reason}\n"
            "\n"
            "  No se ha abierto ninguna conexión ni escrito ningún dato.\n"
            "\n"
            "  Para ejecutar pruebas de forma segura:\n"
            f"    export {TEST_MARKER_ENV}=1\n"
            f"    export {TEST_DB_URL_ENV}=postgresql+asyncpg://user:pass@host:5432/test_global_avicola\n"
            "    export ENVIRONMENT=test\n"
            "  o utilice  backend/scripts/run_tests.sh\n"
            "══════════════════════════════════════════════════════════════"
        )
    return decision
