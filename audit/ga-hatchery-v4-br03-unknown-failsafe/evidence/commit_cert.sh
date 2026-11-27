#!/usr/bin/env bash
set -euo pipefail
cd /home/maria/Proyectos/GlobalAvicola
git restore -- audit/ga-cutover-grandparent-v3 audit/ga-cutover-hatchery-v4/evidence audit/ga-hatchery-v4-o15/evidence audit/ga-hatchery-v4-od02-pit-preload/evidence audit/ga-o3-classification-build-provenance audit/ga-uat-breeder-cria-s1-2026-11-10 audit/ga-uat-users-s2-01-2026-11-01
git add -f -- audit/ga-hatchery-v4-br03-unknown-failsafe
if git diff --cached -- . ':(exclude)audit/ga-hatchery-v4-br03-unknown-failsafe/evidence/*.sh' | grep -nEi 'Bearer eyJ|postgres(ql)?(\+[a-z]+)?://[^ ]*:[^ ]*@|DEEPSEEK_API_KEY=|sk-[A-Za-z0-9]{20,}|password *= *["'"'"'][^"'"'"']{6,}'; then echo "SECRET_SCAN=FAIL"; git reset -q; exit 2; fi
echo SECRET_SCAN=PASS
git diff --cached --name-only | grep -v '^audit/ga-hatchery-v4-br03-unknown-failsafe/' && { echo "STAGE_FUERA_DE_ALCANCE"; git reset -q; exit 3; } || true
git diff --cached --stat | tail -2
git commit -q -F - <<'MSG'
docs(cutover): SPEC 018 §10 BR-03 UNKNOWN fail-safe - certificación local

Evidencia: regresión completa pre-commit y post-mutación (backend 2152 passed,
tsc/build OK, E2E completa 239 passed; vitest 1 fallo intermitente O-28
preexistente, frontend sin cambios), mutación 9/9 sobre fd52b90 (M1..M5 del
mandato + retiro, cota de la corrección, KNOWN, V3), RED 10 failed / 1 passed,
E2E dirigida de incubadora 15/15 y E2E proceso-spec018e.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
MSG
git log -2 --oneline
git status --short | grep -v '^??' || echo TREE_TRACKED=CLEAN
