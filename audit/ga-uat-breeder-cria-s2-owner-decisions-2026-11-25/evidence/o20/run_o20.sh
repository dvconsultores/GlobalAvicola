#!/usr/bin/env bash
# O-20 · determinismo del test de tendencia de mortalidad (R-141).
# Desde la raíz del repo. Corre: (1) el test corregido solo; (2) el corregido con reloj controlado
# en domingo, lunes y martes; (3) la versión ANTERIOR (90a5fb7^) con el mismo reloj, para mostrar
# que el defecto era del test. Solo se guardan las líneas de resumen (sin DSN).
set -u
RAIZ=$(pwd)
EV="$RAIZ/audit/ga-uat-breeder-cria-s2-owner-decisions-2026-11-25/evidence/o20"
OUT="$EV/o20_resultados.txt"
PREVIO="backend/tests/test_o20_version_previa_tmp.py"
: > "$OUT"

resumen() { grep -E "GA reloj controlado|PASSED|FAILED|passed|failed|Δ=" | sed -E 's#postgres(ql)?(\+[a-z]+)?://[^ ]+#<DSN>#g' | tail -25; }

corre() {  # etiqueta, reloj ('' = real), archivo, filtro
  local etiqueta="$1" reloj="$2" archivo="$3" filtro="$4"
  echo "=== $etiqueta · reloj=${reloj:-real} · $archivo -k $filtro" >> "$OUT"
  ( cd "$RAIZ" && GA_RELOJ_CONTROLADO="$reloj" PYTHONPATH="$EV${PYTHONPATH:+:$PYTHONPATH}" \
      bash backend/scripts/run_tests.sh -p reloj_controlado -v "${archivo#backend/}" -k "$filtro" 2>&1 ) | resumen >> "$OUT"
  echo "RC=${PIPESTATUS[0]}" >> "$OUT"
}

corre "1 · corregido, solo" "" backend/tests/test_ga_rem_022_r131_r141.py "tendencia"
for dia in 2026-11-22 2026-11-23 2026-11-24; do
  corre "2 · corregido, reloj controlado" "$dia" backend/tests/test_ga_rem_022_r131_r141.py "tendencia"
done
git show 90a5fb7^:backend/tests/test_ga_rem_022_r131_r141.py > "$PREVIO"
for dia in 2026-11-22 2026-11-23 2026-11-24; do
  corre "3 · versión previa (90a5fb7^), reloj controlado" "$dia" "$PREVIO" "tendencia_mortalidad"
done
rm -f "$PREVIO"
git status --short -- backend/tests >> "$OUT"
echo "FIN" >> "$OUT"
