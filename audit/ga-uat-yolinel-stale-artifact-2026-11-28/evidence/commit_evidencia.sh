#!/usr/bin/env bash
set -euo pipefail
cd /home/maria/Proyectos/GlobalAvicola
# 1 · JSON crudos de vitest de O-28 (sin seguimiento; resumen/logs/rc ya commiteados en 28fa481)
find audit/ga-o28-fe02-user-bu-panel/evidence/runs -name 'run_*.json' -type f -delete
echo "json_restantes=$(find audit/ga-o28-fe02-user-bu-panel/evidence/runs -name '*.json' | wc -l)"
# 2 · evidencia del incidente de producción
git add -f -- audit/ga-uat-yolinel-stale-artifact-2026-11-28
if git diff --cached -- . ':(exclude)audit/ga-uat-yolinel-stale-artifact-2026-11-28/evidence/*.sh' | grep -nEi 'Bearer eyJ|postgres(ql)?(\+[a-z]+)?://[^ ]*:[^ ]*@|DEEPSEEK_API_KEY=|sk-[A-Za-z0-9]{20,}|"token"'; then echo SECRET_SCAN=FAIL; git reset -q; exit 2; fi
echo SECRET_SCAN=PASS
git diff --cached --name-only | grep -v '^audit/ga-uat-yolinel-stale-artifact-2026-11-28/' && { echo STAGE_FUERA_DE_ALCANCE; git reset -q; exit 3; } || true
git diff --cached --stat | tail -1
git commit -q -F - <<'MSG'
docs(deploy): incidente producción desactualizada - evidencia de diagnóstico

Yolinel revisa PRODUCCIÓN (avicola.liderpollo.online), que sirve 8531d95 (21-11)
aunque :latest = 0d17b21 está publicado desde el 27-11; no tomó PR #2 ni PR #3.
UAT (avicola.globaldv.net) correcto en 28fa481: versión, bundle, locales e imagen
verificados por contenido. Causa STALE_DOCKER_IMAGE en producción; requiere
redespliegue del administrador. Incidente ABIERTO.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
MSG
git log -1 --oneline
git status --short | grep -v '^??' || echo TREE_TRACKED=CLEAN
