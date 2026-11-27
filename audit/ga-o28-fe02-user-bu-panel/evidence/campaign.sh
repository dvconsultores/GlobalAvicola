#!/usr/bin/env bash
# O-28 · campaña de repetición de vitest con reporter JSON por corrida (desde cualquier cwd).
# Uso: campaign.sh <etiqueta> <n> <modo: file|tests|suite|full|shuffle> [patrón -t]
set -uo pipefail
RAIZ=/home/maria/Proyectos/GlobalAvicola
EV="$RAIZ/audit/ga-o28-fe02-user-bu-panel/evidence"
export PATH=$HOME/.nvm/versions/node/v20.20.2/bin:$PATH
export DEBUG_PRINT_LIMIT=200000
ET=$1; N=$2; MODO=$3; PAT=${4:-}
OUT="$EV/runs/$ET"; mkdir -p "$OUT"
F1=src/pages/users/__tests__/gaFe02.userBuPanel.test.tsx
F2=src/pages/users/__tests__/uatAdminRbac.userBuPanel.test.tsx
cd "$RAIZ/frontend"
for i in $(seq 1 "$N"); do
  case $MODO in
    file)    ARGS=("$F1" "$F2") ;;
    tests)   ARGS=("$F1" "$F2" -t "$PAT") ;;
    suite)   ARGS=($(cd "$RAIZ/frontend" && grep -rlE 'SPEC 013|GA-FE-02' src --include='*.test.tsx' --include='*.test.ts' | sort)) ;;
    full)    ARGS=() ;;
    shuffle) ARGS=("$F1" "$F2" --sequence.shuffle --sequence.seed=$((1000+i))) ;;
  esac
  npx vitest run "${ARGS[@]}" --reporter=default --reporter=json --outputFile.json="$OUT/run_$i.json" > "$OUT/run_$i.log" 2>&1
  echo "run $i rc=$?" >> "$OUT/rc.txt"
done
python3 "$EV/summarize.py" "$OUT" | tee "$OUT/summary.txt"
