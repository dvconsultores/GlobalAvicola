#!/usr/bin/env bash
set -euo pipefail
cd /home/maria/Proyectos/GlobalAvicola
git restore -- audit/ga-cutover-grandparent-v3 audit/ga-cutover-hatchery-v4/evidence audit/ga-hatchery-v4-o15/evidence audit/ga-hatchery-v4-od02-pit-preload/evidence audit/ga-o3-classification-build-provenance audit/ga-uat-breeder-cria-s1-2026-11-10 audit/ga-uat-users-s2-01-2026-11-01
FILES=(backend/app/cutover/saldo_incubadora.py backend/app/cutover/opening_corrections.py backend/app/cutover/schemas.py backend/app/cutover/service.py backend/app/cutover/validation.py backend/app/operations/validators.py backend/scripts/cutover_v2_docs.py backend/tests/test_cutover_hatchery_v4_br03_unknown.py backend/tests/test_cutover_hatchery_v4.py backend/tests/test_cutover_hatchery_v4_od02.py e2e/proceso-spec018e-hatchery-v4-br03-unknown.spec.ts specs/018-cutover-hatchery-v4-non-incubables/spec.md docs/MANUAL_CARGAS_INICIALES.md audit/cutover-initial-balances/05_HATCHERY_TEMPLATE_CONTRACT.md)
git add -- "${FILES[@]}"
if git diff --cached | grep -nEi 'Bearer eyJ|postgres(ql)?(\+[a-z]+)?://[^ ]*:[^ ]*@|DEEPSEEK_API_KEY=|password *= *["'"'"'][^"'"'"']{6,}'; then echo "SECRET_SCAN=FAIL"; git reset -q; exit 2; fi
echo SECRET_SCAN=PASS
git diff --cached --stat | tail -3
git commit -q -F - <<'MSG'
fix(cutover): SPEC 018 §10 BR-03 UNKNOWN fail-safe - el saldo para cargar es exacto o no autoriza

- saldo_incubadora.py: semántica canónica única (preview, reconciliación, BR-03):
  recibidos - cargados - extra grande - sucios - rotos - fosa solo si los seis son KNOWN;
  con un UNKNOWN el saldo es UNKNOWN (la suma conocida es cota, no saldo).
- BR-03 / retiro de entrada: saldo UNKNOWN + cantidad > 0 => 400 CUTOVER_BALANCE_INCOMPLETE
  con mensaje funcional; un 0 conocido se computa normal; V3 conserva recibidos - cargados.
- Corrección gobernada de la apertura V4 (POST /opening-balances/{id}/corrections) para los
  cuatro componentes PRE-CARGA: motivo, auditoría, original conservado, cota <= recibidos.
- Reconciliación expone opening_id; spec 018 §10 (D-28..D-31, AC-V4-30..36), manual y contrato 05.
- Tests BR03-U01..U07 + E2E proceso-spec018e.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
MSG
git log -1 --oneline
git status --short | grep -v '^??' || echo "TREE_TRACKED=CLEAN"
