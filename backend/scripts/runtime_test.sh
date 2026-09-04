#!/usr/bin/env bash
# ============================================================
# WAVE 2.75 — ciclo de negocio sobre la base que migro EL ARRANQUE REAL.
#
# Deliberadamente **no** ejecuta `alembic`. Prepara el estado anterior a la Wave 2, invoca
# el entrypoint de la imagen y despues lanza los tests contra lo que ese arranque dejo.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"

$PY scripts/test_db.py start >/dev/null
DSN="$($PY scripts/test_db.py reset upgrade)"

export GA_TEST_ENV=1 ENVIRONMENT=test DEBUG=false
export GA_TEST_DATABASE_URL="$DSN" DATABASE_URL="$DSN"
export JWT_SECRET_KEY="$($PY -c 'import secrets;print(secrets.token_hex(32))')"
export GA_UPGRADE_TEST_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
GA_TEST_MEDIA_DIR="$(mktemp -d -t ga-runtime-media-XXXXXX)"
export MEDIA_DIR="$GA_TEST_MEDIA_DIR" SAP_EXPORT_DIR="$GA_TEST_MEDIA_DIR/sap_exports"
mkdir -p "$SAP_EXPORT_DIR"
trap 'rm -rf "$GA_TEST_MEDIA_DIR"' EXIT
export PATH="$PWD/.venv/bin:$PATH"

echo "── Estado anterior a la Wave 2 ──"
$PY -m alembic upgrade i9j0k1l2m3n4 >/dev/null 2>&1
$PY -m seeds.legacy_state_seeds | sed 's/^/   /'

echo
echo "── ARRANQUE REAL: el entrypoint de la imagen ──"
./docker-entrypoint.sh true | sed 's/^/   /'

echo
echo "── Ciclo de negocio sobre lo que el arranque dejo ──"
$PY -m pytest "${@:-tests/test_runtime_startup.py}" -q
