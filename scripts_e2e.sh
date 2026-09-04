#!/usr/bin/env bash
# ============================================================
# WAVE 3 — arnés de certificación E2E de procesos (GA-REM-016).
#
# Levanta backend y frontend contra la base de pruebas AISLADA, ejecuta la suite de
# procesos y lo apaga todo. Producción no interviene: la guarda de entorno lo impide.
#
#   uso:  bash scripts_e2e.sh [rutas de test...]
#
# Puertos propios (8099 / 5199) para no interferir con nada que ya escuche en los
# habituales: el entorno de quien ejecuta esto puede tener sus propios servidores en pie,
# y apropiarse de ellos certificaria contra el sistema equivocado.
# ============================================================
set -uo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.nvm/versions/node/v24.13.0/bin:$PATH"
PY="backend/.venv/bin/python"

echo "── 1/5 · Base de pruebas ──"
DSN="$($PY backend/scripts/test_db.py start >/dev/null; cd backend && .venv/bin/python scripts/test_db.py reset)"
export GA_TEST_ENV=1 ENVIRONMENT=test DEBUG=false
export GA_TEST_DATABASE_URL="$DSN" DATABASE_URL="$DSN"
export JWT_SECRET_KEY="$($PY -c 'import secrets;print(secrets.token_hex(32))')"
export GA_TEST_ADMIN_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
export GA_TEST_OPERATOR_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
export GA_TEST_APPROVER_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
GA_MEDIA="$(mktemp -d -t ga-e2e-media-XXXXXX)"
export MEDIA_DIR="$GA_MEDIA" SAP_EXPORT_DIR="$GA_MEDIA/sap_exports"
mkdir -p "$SAP_EXPORT_DIR"

echo "── 2/5 · Esquema y datos (por el entrypoint real) ──"
( cd backend && PATH="$PWD/.venv/bin:$PATH" ./docker-entrypoint.sh true ) 2>&1 | sed 's/^/   /'
( cd backend && .venv/bin/python -m seeds.test_seeds >/dev/null ) && echo "   semillas aplicadas"

echo "── 3/5 · Backend ──"
( cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8099 --log-level warning ) &
BACKEND_PID=$!
export VITE_API_PROXY_TARGET="http://127.0.0.1:8099"

echo "── 4/5 · Frontend ──"
( cd frontend && npm run dev -- --port 5199 --strictPort >/dev/null 2>&1 ) &
FRONTEND_PID=$!

limpiar() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  rm -rf "$GA_MEDIA"
}
trap limpiar EXIT

for _ in $(seq 1 40); do
  curl -fsS http://127.0.0.1:8099/health >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS http://127.0.0.1:8099/health >/dev/null 2>&1 && echo "   backend en pie" || { echo "   backend NO responde"; exit 1; }
for _ in $(seq 1 40); do
  curl -fsS http://127.0.0.1:5199/ >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS http://127.0.0.1:5199/ >/dev/null 2>&1 && echo "   frontend en pie" || { echo "   frontend NO responde"; exit 1; }

echo
echo "── 5/5 · Certificación E2E ──"
GA_E2E_BASE_URL="http://127.0.0.1:5199" npx playwright test "$@"
