#!/usr/bin/env bash
# Regresión post-mutación (desde la raíz del repo). Secuencial: el arnés backend no corre en paralelo.
set -u
RAIZ=$(pwd)
EV="$RAIZ/audit/ga-uat-breeder-cria-s2-owner-decisions-2026-11-25/evidence"
SHA=$(git rev-parse --short HEAD)
export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"
sanea() { sed -E 's#postgres(ql)?(\+[a-z]+)?://[^ "]+#<DSN>#g; s#(password|PASSWORD|token|TOKEN)=[^ ]+#\1=<REDACTED>#g'; }

echo "HEAD=$SHA $(date -Iseconds)" > "$EV/post_mutation_status.txt"

bash "$EV/o20/run_o20.sh"; echo "o20 rc=$?" >> "$EV/post_mutation_status.txt"

( cd frontend && npx vitest run 2>&1 | sanea > "$EV/frontend_vitest_full_$SHA.log" ); echo "vitest rc=${PIPESTATUS[0]}" >> "$EV/post_mutation_status.txt"
( cd frontend && npx tsc -b 2>&1 | sanea > "$EV/frontend_tsc_$SHA.log"; echo "RC=${PIPESTATUS[0]}" >> "$EV/frontend_tsc_$SHA.log" )
( cd frontend && npx vite build 2>&1 | sanea | tail -15 > "$EV/frontend_build_$SHA.log"; echo "RC=${PIPESTATUS[0]}" >> "$EV/frontend_build_$SHA.log" )

bash backend/scripts/run_tests.sh tests 2>&1 | sanea > "$EV/backend_full_$SHA.log"
echo "backend rc=${PIPESTATUS[0]}" >> "$EV/post_mutation_status.txt"
echo "FIN $(date -Iseconds)" >> "$EV/post_mutation_status.txt"
