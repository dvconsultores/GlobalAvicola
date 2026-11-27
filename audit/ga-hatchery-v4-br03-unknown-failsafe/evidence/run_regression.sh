#!/usr/bin/env bash
# BR-03 UNKNOWN FAIL-SAFE · regresión completa (desde la raíz del repo). Secuencial: backend y E2E no corren en paralelo.
# Uso: bash run_regression.sh <etiqueta>   (la etiqueta nombra los logs, p. ej. pre-commit o post-mutacion)
set -u -o pipefail
RAIZ=$(pwd)
EV="$RAIZ/audit/ga-hatchery-v4-br03-unknown-failsafe/evidence"
ET="${1:-regresion}"
export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"
sanea() { sed -E 's#postgres(ql)?(\+[a-z]+)?://[^ "]+#<DSN>#g; s#(password|PASSWORD|token|TOKEN)=[^ ]+#\1=<REDACTED>#g; s/Bearer eyJ[A-Za-z0-9._-]*/Bearer [REDACTADO]/g'; }
ST="$EV/status_$ET.txt"

echo "HEAD=$(git rev-parse --short HEAD) dirty=$(git status --short -- backend frontend e2e specs | wc -l) $(date -Iseconds)" > "$ST"

( cd frontend && npx vitest run 2>&1 | sanea > "$EV/frontend_vitest_$ET.log" ); echo "vitest rc=$?" >> "$ST"
( cd frontend && npx tsc -b 2>&1 | sanea > "$EV/frontend_tsc_$ET.log" ); echo "tsc rc=$?" >> "$ST"
( cd frontend && npx vite build 2>&1 | sanea | tail -15 > "$EV/frontend_build_$ET.log" ); echo "build rc=$?" >> "$ST"

bash backend/scripts/run_tests.sh tests 2>&1 | sanea > "$EV/backend_full_$ET.log"
echo "backend rc=${PIPESTATUS[0]}" >> "$ST"

bash scripts_e2e.sh --workers=1 2>&1 | sanea > "$EV/e2e_full_$ET.log"
echo "e2e rc=${PIPESTATUS[0]}" >> "$ST"
echo "FIN $(date -Iseconds)" >> "$ST"
