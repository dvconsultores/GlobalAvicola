# GA-FE-01 · CHECKLIST

`[x]` hecho · `[ ]` pendiente · `[n/a]` con causa. Marcado al ejecutar.

## Pre-implementación (bloquea escribir código)

- [x] baseline verificado (`main` · `42108b0` · limpio · local==remoto · HTTPS)
- [x] delta post-`42108b0` reconciliado (solo commits de auditoría, sin producto)
- [x] worktree limpio
- [x] entry runtime fingerprint capturado (21:33Z, asset+hash+LM+ETag)
- [x] origen stale vs caché de cliente distinguido (origen; sin SW)
- [x] historical green probado (`f46cb13`: tsc 0 · build produce `index-D5dwMXuP.js`)
- [x] historical first red probado (`4386f87`: exit 2, 2 errores)
- [x] segundo RED probado (`950bb21`: exit 2, 6 errores)
- [x] current red probado (tsc exit 2/6 · npm build FAIL · vite PASS)
- [x] 6-error matrix completa (`R158_TYPESCRIPT_ERROR_SEMANTIC_MATRIX.md`)
- [x] requirements trazados (GA-REM-032 AC11 · GA-REM-039/OD-08 · docs/02 sin área)
- [x] no feature deletion planificada (imports muertos + locals jamás ejecutados)
- [x] no tsconfig weakening planificado
- [x] no package build weakening planificado
- [x] no Dockerfile bypass planificado
- [x] AC completos (R-158 ×10 · R-99 ×10 · NR ×2)
- [x] tests planificados (sin suites dedicadas; sin cambio de comportamiento → Vitest completo)
- [x] build commands conocidos (tsc/vite/npm build/vitest exactos)
- [x] runtime markers seleccionados (M1–M7 + control negativo)
- [x] deployment proof method definido (fingerprint ENTRY vs EXIT + marcadores + smoke)
- [x] auth availability conocida (sin credenciales autorizadas → BLOCKED_AUTH esperado)
- [x] rollback plan (revert del commit; sin datos)
- [x] git plan (C1/C2/C3; sin add amplio; sin force)
- [x] out-of-scope verificado (fase 9 · R-181 · R-98/119 · Wave B/C · SAP · backend · deploy)
- [x] finding `R-182` identificado para registro (no se corrige)

## Implementación

- [ ] E1–E2: import de `AuditPage` sin `User`/`Database`
- [ ] E3–E4: estado `areas/setAreas` eliminado
- [ ] E5–E6: destructuring a 4 elementos
- [ ] cero `any`/casts/ts-ignore/renames falsos introducidos
- [ ] diff limitado a los loci justificados (2 archivos)

## Gates locales (TODOS antes del push de C2)

- [ ] `npx tsc -b --noEmit` → **exit 0 / 0 errores** (sin caché)
- [ ] `npx vite build` → exit 0
- [ ] `npm run build` → exit 0
- [ ] build repetido en limpio (`rm -rf dist` + tsbuildinfo) → exit 0
- [ ] `npx vitest run` → **0 failed**
- [ ] quality gates vigentes (typecheck + tests; ESLint solo para distinguir NEW vs PREEXISTING)
- [ ] docker build local **si** Docker disponible; si no → `DOCKER_BUILD_NOT_EXECUTED`
- [ ] local build fingerprint capturado (asset + hash + marcadores locales)
- [ ] verificación: ninguna feature eliminada (diff revisado contra AC-NR-01/02)
- [ ] `git status` limpio salvo loci + docs; sin dist commiteado; sin lockfile churn

## Push y despliegue

- [ ] pre-push safety: `git diff 42108b0..C2` solo `frontend/src` (2 archivos) + docs de auditoría
- [ ] push por el mecanismo normal; `origin` intacto
- [ ] `REMOTE_IMPLEMENTATION_HEAD` == commit de implementación
- [ ] observación acotada del runtime; change detection por asset/LM
- [ ] EXIT fingerprint: asset nuevo, LM posterior, stale no primario, M1–M7 presentes
- [ ] smoke público: root/login/JS/CSS 200; sin error fatal
- [ ] caché de cliente revalidada (contexto fresco)
- [ ] autenticado: ejecutado **si** hay credenciales autorizadas; si no → `BLOCKED_AUTH`

## Cierre

- [ ] R-158 clasificado (CLOSED solo si los 10 gates de §88 del encargo)
- [ ] R-99 clasificado (CLOSED solo si paridad desplegada demostrada)
- [ ] reconciliación de 13 capacidades **sin** auto-marcar IMPLEMENTED_AND_VISIBLE
- [ ] R-98/R-119 y R-181 sin cambio; fase 9 sin empezar; Wave B pausada
- [ ] `R-182` registrado (si ratificado por el programa)
- [ ] backend/Alembic/rutas/deployment config sin cambios (verificado por diff)
- [ ] evidencia final + COMMIT 3 + push + verificación remota
- [ ] informe final con el formato exacto
