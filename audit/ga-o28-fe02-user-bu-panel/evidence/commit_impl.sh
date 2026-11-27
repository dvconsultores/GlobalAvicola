#!/usr/bin/env bash
set -euo pipefail
cd /home/maria/Proyectos/GlobalAvicola
git restore -- audit/ga-cutover-grandparent-v3 audit/ga-cutover-hatchery-v4/evidence audit/ga-hatchery-v4-br03-unknown-failsafe/evidence audit/ga-hatchery-v4-o15/evidence audit/ga-hatchery-v4-od02-pit-preload/evidence audit/ga-o3-classification-build-provenance audit/ga-uat-breeder-cria-s1-2026-11-10 audit/ga-uat-users-s2-01-2026-11-01
FILES=(frontend/src/pages/users/__tests__/gaFe02.userBuPanel.test.tsx frontend/src/pages/users/__tests__/uatAdminRbac.userBuPanel.test.tsx specs/013-admin-rbac-uat/spec.md)
git add -- "${FILES[@]}"
if git diff --cached | grep -nEi 'Bearer eyJ|postgres(ql)?(\+[a-z]+)?://[^ ]*:[^ ]*@|DEEPSEEK_API_KEY=|sk-[A-Za-z0-9]{20,}'; then echo SECRET_SCAN=FAIL; git reset -q; exit 2; fi
echo SECRET_SCAN=PASS
git diff --cached --name-only | grep -vxF -f <(printf '%s\n' "${FILES[@]}") && { echo STAGE_FUERA_DE_ALCANCE; git reset -q; exit 3; } || true
git diff --cached --stat | tail -1
git commit -q -F - <<'MSG'
test(users): SPEC 013 §8 O-28 - el panel de unidades se consulta cuando termina la carga

TEST_DEFECT: openPanel daba el panel por abierto al ver el título del Modal, que se
pinta junto al indicador «cargando»; las filas de unidades solo existen al resolver
load(). Las consultas síncronas siguientes dependían de esa carrera (4/4 fallos
reproducidos con el indicador en el DOM). Ahora se espera el hecho observable: el
indicador desaparece y las cabeceras de estado aparecen (waitFor sobre esa
condición). Componente sin cambios; sin pausas, skips ni aserciones relajadas.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
MSG
git log -1 --oneline
git status --short | grep -v '^??' || echo TREE_TRACKED=CLEAN
