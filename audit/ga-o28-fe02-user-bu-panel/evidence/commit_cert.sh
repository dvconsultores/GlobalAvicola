#!/usr/bin/env bash
set -euo pipefail
cd /home/maria/Proyectos/GlobalAvicola
git restore -- audit/ga-cutover-grandparent-v3 audit/ga-cutover-hatchery-v4/evidence audit/ga-hatchery-v4-br03-unknown-failsafe/evidence audit/ga-hatchery-v4-o15/evidence audit/ga-hatchery-v4-od02-pit-preload/evidence audit/ga-o3-classification-build-provenance audit/ga-uat-breeder-cria-s1-2026-11-10 audit/ga-uat-users-s2-01-2026-11-01
git add -f -- audit/ga-o28-fe02-user-bu-panel ':(exclude)audit/ga-o28-fe02-user-bu-panel/evidence/runs/*/*.json'
if git diff --cached -- . ':(exclude)audit/ga-o28-fe02-user-bu-panel/evidence/*.sh' | grep -nEi 'Bearer eyJ|postgres(ql)?(\+[a-z]+)?://[^ ]*:[^ ]*@|DEEPSEEK_API_KEY=|sk-[A-Za-z0-9]{20,}'; then echo SECRET_SCAN=FAIL; git reset -q; exit 2; fi
echo SECRET_SCAN=PASS
git diff --cached --name-only | grep -v '^audit/ga-o28-fe02-user-bu-panel/' && { echo STAGE_FUERA_DE_ALCANCE; git reset -q; exit 3; } || true
echo "json_staged=$(git diff --cached --name-only | grep -c '\.json$' || true)"
git diff --cached --stat | tail -1
git commit -q -F - <<'MSG'
docs(users): SPEC 013 §8 O-28 - certificación local del panel de unidades

Reproducción antes del fix (archivo 8/10, subsuite 1/3, fallos con el panel en
«cargando»), fix sobre 906e198, estabilidad pre y post sensibilidad (archivo 20/20,
SPEC 013 10/10, vitest completa 3/3 sin fallos, tsc/build OK), sensibilidad S1b/S2/S3
y falso verde S4 OK (S1 sin fallo natural en 20, documentado), E2E relevantes 14/14 y
completa 239/0. TEST_DEFECT; componente y backend sin cambios.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
MSG
git log -2 --oneline
git status --short | grep -v '^??' || echo TREE_TRACKED=CLEAN
