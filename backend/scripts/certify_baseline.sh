#!/usr/bin/env bash
# Certificación del ciclo completo del baseline limpio — GA-REM-025.
#
#   base vacía → migraciones → baseline → ensuciar → reset → verificar
#
# Demuestra AC01, AC02, AC11 y AC14 de extremo a extremo sobre la base aislada de
# GA-REM-014. No toca en ningún caso el entorno compartido.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv/bin/python
CERT_DB="${GA_CERT_DB:-global_avicola_baseline_cert}"

# Sin literales en el repositorio (GA-REM-004). Si el operador no las declara, se generan
# por ejecución: la base de certificación se destruye al principio de cada corrida, así que
# no hay nada que recordar de una a otra.
export GA_BASELINE_ADMIN_PASSWORD="${GA_BASELINE_ADMIN_PASSWORD:-$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')}"
export GA_SEED_DEFAULT_PASSWORD="${GA_SEED_DEFAULT_PASSWORD:-$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')}"

echo "══ 1. Instancia aislada ══"
$PY -m scripts.test_db start >/dev/null
DSN=$($PY -m scripts.test_db dsn)
SOCKET=$(printf '%s' "$DSN" | sed 's/.*host=//')
BASE_DSN="${DSN%%/global_avicola_test*}"

echo "══ 2. Base de certificación vacía: $CERT_DB ══"
$PY - "$CERT_DB" "$SOCKET" <<'PYEOF'
import sys, pgserver, pathlib, os
pgdata = pathlib.Path(os.environ.get("GA_TEST_PGDATA", pathlib.Path.home()/".local/share/global_avicola_test_pg"))
srv = pgserver.get_server(pgdata, cleanup_mode=None)
base = sys.argv[1]
srv.psql(f'DROP DATABASE IF EXISTS "{base}"')
srv.psql(f'CREATE DATABASE "{base}" OWNER global_avicola_test_user')
print(f"  base {base} recreada vacía")
PYEOF

CERT_DSN=$(printf '%s' "$DSN" | sed "s|/global_avicola_test?|/$CERT_DB?|")

echo "══ 3. alembic upgrade head sobre base vacía ══"
DATABASE_URL="$CERT_DSN" $PY -m alembic upgrade head 2>&1 | grep -E "R-44|Running upgrade" | tail -3
echo "  revisión:"
DATABASE_URL="$CERT_DSN" $PY -m alembic current 2>&1 | grep -v INFO | sed 's/^/    /'

echo "══ 4. Seed de baseline ══"
DATABASE_URL="$CERT_DSN"   $PY -c "
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from seeds.baseline_seeds import sembrar_baseline
async def main():
    m = create_async_engine(os.environ['DATABASE_URL']); S = async_sessionmaker(m, expire_on_commit=False)
    async with S() as s: await sembrar_baseline(s)
    await m.dispose()
asyncio.run(main())" 2>&1 | grep -v "bcrypt\|Traceback\|File \|  \^\|AttributeError\|    " || true

echo "══ 5. Inventario del baseline ══"
DATABASE_URL="$CERT_DSN" $PY -m scripts.environment_reset --inventory 2>&1 | grep -E "Inventario|Filas que|^  [A-Z]"

echo "══ 6. Ensuciar con datos de desarrollo ══"
DATABASE_URL="$CERT_DSN"   $PY -m seeds.dev_seeds >/dev/null 2>&1 || true
DATABASE_URL="$CERT_DSN" $PY -c "
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import app.audit.models, app.corrections.models, app.integrations.sap.models
import app.lots.models, app.operations.models, app.review.models
from seeds.scenario_fixtures import crear_par_multitenant
async def main():
    m = create_async_engine(os.environ['DATABASE_URL']); S = async_sessionmaker(m, expire_on_commit=False)
    async with S() as s:
        await crear_par_multitenant(s); await s.commit()
    await m.dispose()
asyncio.run(main())" 2>&1 | grep -v "bcrypt\|Traceback\|File \|  \^\|AttributeError\|    " || true
DATABASE_URL="$CERT_DSN" $PY -m scripts.environment_reset --inventory 2>&1 | grep -E "Filas que"

echo "══ 7. Reset con guarda ══"
DATABASE_URL="$CERT_DSN" \
ENVIRONMENT=test \
GA_ALLOW_DESTRUCTIVE_RESET=1 \
GA_RESET_ALLOWED_TARGETS="local/$CERT_DB" \
  $PY -m scripts.environment_reset --reset --confirm-database "$CERT_DB" 2>&1 \
  | grep -E "Guarda|vaciadas|Baseline listo|Verificación|❌"

echo "══ 8. Segundo reset, retirando identidades obsoletas (AC11 · §26) ══"
DATABASE_URL="$CERT_DSN" \
ENVIRONMENT=test \
GA_ALLOW_DESTRUCTIVE_RESET=1 \
GA_RESET_ALLOWED_TARGETS="local/$CERT_DB" \
  $PY -m scripts.environment_reset --reset --confirm-database "$CERT_DB" --purge-identities 2>&1 \
  | grep -E "identidades retiradas|Baseline listo|Verificación"

echo "══ 9. Guarda: el mismo reset sin autorización ══"
# La salida se captura antes de filtrarla: con `pipefail`, el código 2 con que la
# herramienta señala el bloqueo haría fallar la tubería y se leería como lo contrario.
SALIDA=$(DATABASE_URL="$CERT_DSN" ENVIRONMENT=production GA_ALLOW_DESTRUCTIVE_RESET=1 \
   GA_RESET_ALLOWED_TARGETS="local/$CERT_DB" \
   $PY -m scripts.environment_reset --reset --confirm-database "$CERT_DB" 2>&1 || true)
if grep -q "RESET BLOQUEADO" <<<"$SALIDA"; then
  echo "  ✅ ENVIRONMENT=production rechazado:"
  grep "RESET BLOQUEADO" <<<"$SALIDA" | sed 's/^/     /'
else
  echo "  ❌ LA GUARDA NO BLOQUEÓ"; exit 1
fi

echo "══ 10. Arranque limpio: estados vacíos y primer flujo (AC13 · AC14) ══"
# Tercer reset: el paso 10 debe partir de un baseline intacto, y el backend arranca
# **después**. Resetear con la aplicación en marcha deja conexiones con datos que ya no
# existen y produce fallos que parecen del sistema y no lo son.
DATABASE_URL="$CERT_DSN" \
ENVIRONMENT=test \
GA_ALLOW_DESTRUCTIVE_RESET=1 \
GA_RESET_ALLOWED_TARGETS="local/$CERT_DB" \
  $PY -m scripts.environment_reset --reset --confirm-database "$CERT_DB" --purge-identities \
  >/dev/null 2>&1

PUERTO="${GA_FLOW_PORT:-8111}"
DATABASE_URL="$CERT_DSN" ENVIRONMENT=development SECRET_KEY=cert-only-key-not-a-secret \
  $PY -m uvicorn app.main:app --host 127.0.0.1 --port "$PUERTO" --log-level warning \
  >/tmp/ga_cert_uvicorn.log 2>&1 &
UVICORN_PID=$!
trap 'kill $UVICORN_PID 2>/dev/null || true' EXIT

for _ in $(seq 1 40); do
  curl -s -o /dev/null "http://127.0.0.1:$PUERTO/api/v1/operations/event-types" && break
  sleep 1
done

GA_FLOW_BASE_URL="http://127.0.0.1:$PUERTO" \
GA_FLOW_PASSWORD="$GA_BASELINE_ADMIN_PASSWORD" \
  $PY -m scripts.first_flow_check || FLOW_FALLO=1

kill $UVICORN_PID 2>/dev/null || true
trap - EXIT

echo
if [ "${FLOW_FALLO:-0}" = "1" ]; then
  echo "══ Certificación de ciclo completa · CON HALLAZGOS EN EL PRIMER FLUJO ══"
else
  echo "══ Certificación de ciclo completa ══"
fi
