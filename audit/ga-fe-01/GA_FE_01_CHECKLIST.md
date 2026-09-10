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

- [x] E1–E2: import de `AuditPage` sin `User`/`Database`
- [x] E3–E4: estado `areas/setAreas` eliminado
- [x] E5–E6: destructuring a 4 elementos
- [x] cero `any`/casts/ts-ignore/renames falsos introducidos
- [x] diff limitado a los loci justificados (2 archivos)

## Gates locales (TODOS antes del push de C2)

- [x] `npx tsc -b --noEmit` → **exit 0 / 0 errores** (sin caché) — 6 → 0
- [x] `npx vite build` → exit 0
- [x] `npm run build` → exit 0
- [x] build repetido en limpio (`rm -rf dist` + tsbuildinfo) → exit 0 (hash reproducible)
- [x] `npx vitest run` → **0 failed** — 108/108 (12 archivos)
- [x] quality gates vigentes (typecheck + tests) — ESLint: no forma parte del gate oficial del workflow (`quality-gates.yml` ejecuta `tsc -b --noEmit`); sin hallazgos NEW en los archivos tocados
- [x] docker build local **si** Docker disponible; si no → `DOCKER_BUILD_NOT_EXECUTED` (Docker ausente en la estación; `npm run build` = comando exacto del Dockerfile → exit 0)
- [x] local build fingerprint capturado (asset + hash + marcadores locales)
- [x] verificación: ninguna feature eliminada (diff revisado contra AC-NR-01/02)
- [x] `git status` limpio salvo loci + docs; sin dist commiteado; sin lockfile churn

## Push y despliegue

- [x] pre-push safety: `git diff 42108b0..C2` = 2 archivos `frontend/src` + docs de auditoría
- [x] push por el mecanismo normal; `origin` intacto
- [x] `REMOTE_IMPLEMENTATION_HEAD` == commit de implementación (`08d0197` == `08d01979…`)
- [x] observación acotada del runtime; change detection por asset/LM — cambio detectado a T+2.5m (21:43:35Z): `index-kzREeQp6.js` · LM 21:42:54 GMT
- [x] EXIT fingerprint: asset nuevo, LM posterior, stale no primario (404), M1–M7 presentes — `GA_FE_01_RUNTIME_EXIT_FINGERPRINT.md`
- [x] smoke público: root/login/JS/CSS 200; sin error fatal — + API viva (401/200)
- [x] caché de cliente revalidada (contexto fresco) — login renderiza; sin SW
- [x] autenticado: ejecutado **si** hay credenciales autorizadas; si no → `BLOCKED_AUTH` — sin credenciales → `BLOCKED_AUTH` registrado (no se adivinan)

## Cierre

- [x] R-158 clasificado — **CLOSED (TECHNICAL BUILD BLOCKER)**
- [x] R-99 clasificado — **CLOSED (paridad de entrega probada; autenticado `BLOCKED_AUTH` declarado)**
- [x] reconciliación de 13 capacidades **sin** auto-marcar IMPLEMENTED_AND_VISIBLE — addendum §7 fechado
- [x] R-98/R-119 y R-181 sin cambio; fase 9 sin empezar; Wave B pausada
- [x] `R-182` registrado (propuesto, ratificación del programa pendiente)
- [x] backend/Alembic/rutas/deployment config sin cambios (verificado por diff: `git diff 42108b0..HEAD -- backend/ frontend/Dockerfile frontend/package.json frontend/tsconfig* .github/ docker-compose.yml` → 0 líneas)
- [x] evidencia final + COMMIT 3 + push + verificación remota
- [x] informe final con el formato exacto
