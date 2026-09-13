#!/usr/bin/env bash
# Arnés local de la auditoría Claude (NO forma parte del repositorio).
# Replica los pasos de scripts_e2e.sh (GA-REM-016) contra la base de pruebas AISLADA
# (pgserver en espacio de usuario) y deja backend (8099) y frontend (5199) en pie.
#   uso: bash local_stack.sh start | stop
set -uo pipefail
REPO=/home/maria/Proyectos/GlobalAvicola
SCRATCH="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.nvm/versions/node/v24.13.0/bin:$PATH"
PY="$REPO/backend/.venv/bin/python"
PIDFILE="$SCRATCH/local_stack.pids"
ENVFILE="$SCRATCH/local_creds.env"

stop() {
  if [ -f "$PIDFILE" ]; then
    while read -r pid; do kill "$pid" 2>/dev/null; done < "$PIDFILE"
    sleep 1
    while read -r pid; do kill -9 "$pid" 2>/dev/null; done < "$PIDFILE"
    rm -f "$PIDFILE"
  fi
  pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 8099" 2>/dev/null
  pkill -f "vite --port 5199" 2>/dev/null
  rm -rf "$SCRATCH/ga-e2e-media"
  echo "stack detenido"
}

if [ "${1:-start}" = "stop" ]; then stop; exit 0; fi

echo "── 1/5 · Base de pruebas ──"
DSN="$(cd "$REPO/backend" && .venv/bin/python scripts/test_db.py start >/dev/null; .venv/bin/python scripts/test_db.py reset)"
export GA_TEST_ENV=1 ENVIRONMENT=test DEBUG=false
export GA_TEST_DATABASE_URL="$DSN" DATABASE_URL="$DSN"
export JWT_SECRET_KEY="$($PY -c 'import secrets;print(secrets.token_hex(32))')"
export GA_TEST_ADMIN_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
export GA_TEST_OPERATOR_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
export GA_TEST_APPROVER_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
GA_MEDIA="$SCRATCH/ga-e2e-media"; rm -rf "$GA_MEDIA"; mkdir -p "$GA_MEDIA/sap_exports"
export MEDIA_DIR="$GA_MEDIA" SAP_EXPORT_DIR="$GA_MEDIA/sap_exports"
export FEATURE_SAP_ENABLED=true

umask 077
cat > "$ENVFILE" <<EOF
GA_TEST_ADMIN_PASSWORD=$GA_TEST_ADMIN_PASSWORD
GA_TEST_OPERATOR_PASSWORD=$GA_TEST_OPERATOR_PASSWORD
GA_TEST_APPROVER_PASSWORD=$GA_TEST_APPROVER_PASSWORD
EOF
umask 022

echo "── 2/5 · Esquema y datos (por el entrypoint real) ──"
( cd "$REPO/backend" && PATH="$PWD/.venv/bin:$PATH" ./docker-entrypoint.sh true ) 2>&1 | tail -3 | sed 's/^/   /'
( cd "$REPO/backend" && .venv/bin/python -m seeds.test_seeds >/dev/null ) && echo "   semillas aplicadas"

echo "── 3/5 · Backend 8099 ──"
( cd "$REPO/backend" && exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8099 --log-level warning > "$SCRATCH/backend_8099.log" 2>&1 ) &
echo $! > "$PIDFILE"
export VITE_API_PROXY_TARGET="http://127.0.0.1:8099"

echo "── 4/5 · Frontend 5199 ──"
( cd "$REPO/frontend" && exec npx vite --port 5199 --strictPort > "$SCRATCH/frontend_5199.log" 2>&1 ) &
echo $! >> "$PIDFILE"

for _ in $(seq 1 60); do curl -fsS http://127.0.0.1:8099/health >/dev/null 2>&1 && break; sleep 1; done
curl -fsS http://127.0.0.1:8099/health >/dev/null 2>&1 && echo "   backend en pie" || { echo "   backend NO responde"; exit 1; }
for _ in $(seq 1 60); do curl -fsS http://127.0.0.1:5199/ >/dev/null 2>&1 && break; sleep 1; done
curl -fsS http://127.0.0.1:5199/ >/dev/null 2>&1 && echo "   frontend en pie" || { echo "   frontend NO responde"; exit 1; }
echo "── 5/5 · listo · credenciales en $ENVFILE (0600) ──"
