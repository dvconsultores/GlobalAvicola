#!/usr/bin/env bash
# =============================================================================
# GA-REM-014 — Ejecución segura de la suite de backend
#
#   arrancar PostgreSQL de pruebas -> resetear base -> alembic upgrade head
#   -> verificar esquema -> sembrar -> pytest
#
# La guarda FAIL-CLOSED de tests/environment_guard.py se aplica dentro de
# pytest y de los seeds, antes de abrir cualquier conexión.
#
# Instancia de pruebas (espacio de usuario, sin privilegios, sin Docker):
#   PGDATA : ~/.local/share/global_avicola_test_pg
#   base   : global_avicola_test
#   rol    : global_avicola_test_user
#
# No comparte host, socket, rol ni base con ningún otro entorno.
#
# Uso:
#   ./scripts/run_tests.sh                    # suite completa
#   ./scripts/run_tests.sh tests/test_auth.py -v
#   GA_TEST_KEEP_DATA=1 ./scripts/run_tests.sh   # no resetear la base
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv/bin/python
KEEP_DATA="${GA_TEST_KEEP_DATA:-0}"

# --- 1 · Instancia de pruebas ------------------------------------------------
echo "── 1/5 · Arrancando PostgreSQL de pruebas (espacio de usuario) ──"
if ! $PY -c "import pgserver" >/dev/null 2>&1; then
  echo "ABORTADO: falta el paquete 'pgserver'." >&2
  echo "          Instálelo con:  uv pip install --python .venv/bin/python pgserver" >&2
  echo "          Alternativa: un PostgreSQL del sistema o un contenedor dedicado." >&2
  exit 4
fi
GA_TEST_DATABASE_URL="$($PY -m scripts.test_db start)"
export GA_TEST_DATABASE_URL

# --- 2 · Base limpia ---------------------------------------------------------
if [ "$KEEP_DATA" = "1" ]; then
  echo "── 2/5 · GA_TEST_KEEP_DATA=1: se conserva el contenido de la base ──"
else
  echo "── 2/5 · Reseteando la base de pruebas a un estado limpio ──"
  GA_TEST_DATABASE_URL="$($PY -m scripts.test_db reset)"
  export GA_TEST_DATABASE_URL
fi

# --- Entorno de ejecución ----------------------------------------------------
export GA_TEST_ENV=1
export ENVIRONMENT=test
export DEBUG=false
export DATABASE_URL="$GA_TEST_DATABASE_URL"

# Secretos efímeros, generados en cada ejecución. Nunca versionados (GA-REM-004).
export JWT_SECRET_KEY="$($PY -c 'import secrets;print(secrets.token_hex(32))')"
export GA_TEST_ADMIN_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
export GA_TEST_OPERATOR_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
export GA_TEST_APPROVER_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"

# Artefactos que la aplicacion escribe. Por defecto apuntan a /app/media, que solo existe
# dentro del contenedor: fuera, la exportacion manual a SAP fallaba con PermissionError.
# Solo se notaba en la corrida completa, cuando existia un movimiento consolidado que
# exportar; en aislamiento el fichero de tests pasaba.
GA_TEST_MEDIA_DIR="$(mktemp -d -t ga-avicola-media-XXXXXX)"
export MEDIA_DIR="$GA_TEST_MEDIA_DIR"
export SAP_EXPORT_DIR="$GA_TEST_MEDIA_DIR/sap_exports"
mkdir -p "$SAP_EXPORT_DIR"
trap 'rm -rf "$GA_TEST_MEDIA_DIR"' EXIT

# --- 3 · Migraciones ---------------------------------------------------------
echo "── 3/5 · Aplicando la cadena real de migraciones ──"
$PY -m alembic upgrade head >/dev/null
echo "   migraciones aplicadas"

# --- 4 · Verificación de esquema --------------------------------------------
echo "── 4/5 · Verificando esquema e integridad de la cadena ──"
$PY - <<'PY'
import asyncio, os, sys
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sd = ScriptDirectory.from_config(Config("alembic.ini"))
heads = sd.get_heads()
assert len(heads) == 1, f"Se esperaba 1 head de Alembic, hay {len(heads)}"

async def main():
    eng = create_async_engine(os.environ["DATABASE_URL"])
    async with eng.connect() as c:
        n = (await c.execute(text(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_type='BASE TABLE'"))).scalar()
        db_head = (await c.execute(text("SELECT version_num FROM alembic_version"))).scalar()
    await eng.dispose()
    print(f"   tablas={n} (47 + alembic_version) · head en BD={db_head} · head en código={heads[0]}")
    if db_head != heads[0]:
        sys.exit(f"   head desincronizado: BD={db_head} código={heads[0]}")
    if n != 55:  # 54 + alembic_version
        sys.exit(f"   recuento de tablas inesperado: {n} (esperado 55)")
asyncio.run(main())
PY

# --- 5 · Seeds y suite -------------------------------------------------------
echo "── 5/5 · Sembrando datos deterministas y ejecutando pytest ──"
$PY -m seeds.test_seeds >/dev/null
echo "   seeds aplicados"
echo
$PY -m pytest "$@"
