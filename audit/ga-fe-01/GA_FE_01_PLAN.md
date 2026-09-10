# GA-FE-01 · PLAN

**20 fases** (§20 del encargo). Estado marcado en el cierre; `[x]` al ejecutar.

| Fase | Contenido | Herramienta / evidencia | Estado |
|---|---|---|---|
| 1 | Repository truth | `git status/branch/HEAD/ls-remote`; delta post-`42108b0` reconciliado (ninguno: solo commits de auditoría) | ✅ |
| 2 | Runtime entry fingerprint | `GA_FE_01_RUNTIME_ENTRY_FINGERPRINT.md` (21:33Z: `index-D5dwMXuP.js`, sha `4eb822a5…`, LM 09-05 14:09:27 GMT) | ✅ |
| 3 | Historical build replay | `GA_FE_01_HISTORICAL_REPLAY.md` — worktrees f46cb13 (GREEN, produce `index-D5dwMXuP.js`) · 4386f87 (exit 2, 2 errores) · 950bb21 (exit 2, 6) · baseline (exit 2, 6) | ✅ |
| 4 | R-158 semantic analysis | `R158_TYPESCRIPT_ERROR_SEMANTIC_MATRIX.md` + `GA_FE_01_CLARIFICATIONS.md` (6 filas, 3 clases, 0 decisiones) | ✅ |
| 5 | Spec / AC | `GA_FE_01_R99_R158_…_SPEC.md` (AC-R158-01…10 · AC-R99-01…10 · AC-NR-01/02) | ✅ |
| 6 | Valid current RED | `tsc` exit 2/6 · `npm run build` exit 2 (muere en tsc) · `vite build` exit 0 — medidos en esta sesión sin caché | ✅ |
| 7 | Minimal implementation | 3 ediciones (import AuditPage · estado muerto LotForm · destructuring a 4) | ⏳ |
| 8 | Targeted component tests | No existen suites dedicadas ni cambio de comportamiento → regla «solo si cambia» → no aplica añadir; se ejecuta Vitest completo | ⏳ |
| 9 | TypeScript green | `npx tsc -b --noEmit` → exit 0 (sin allowance) | ⏳ |
| 10 | Vite green | `npx vite build` → exit 0 | ⏳ |
| 11 | Official npm build green | `npm run build` → exit 0 | ⏳ |
| 12 | Full Vitest | `npx vitest run` → 0 failed | ⏳ |
| 13 | Implementation checkpoint | COMMIT 2 solo con las ediciones mínimas | ⏳ |
| 14 | Push through normal mechanism | `git push origin main` (sin tocar origin) | ⏳ |
| 15 | Deployment observation | Observación acotada del runtime (root + asset + LM) | ⏳ |
| 16 | Runtime fingerprint parity | `GA_FE_01_RUNTIME_EXIT_FINGERPRINT.md` — ENTRY vs EXIT | ⏳ |
| 17 | Runtime smoke | Público: root/login/JS/CSS 200, sin error fatal; API viva | ⏳ |
| 18 | Certification reconciliation | Addendum fechado (13 capacidades stale → DEPLOYMENT_STALE RESOLVED; auth `BLOCKED_AUTH`) | ⏳ |
| 19 | Evidence | `GA_FE_01_…_EVIDENCE.md` (40 secciones §87) | ⏳ |
| 20 | Closure | COMMIT 3 + push + verificación remota + informe final | ⏳ |

## Reglas de ejecución

- Cero mutaciones/sensibilidad de product code: **N/A — BUILD/DELIVERY REMEDIATION** (§46),
  con justificación: RED reproducible + prueba causal histórica ejecutada; el mutation checkpoint
  guard permanece instalado y no se modifica.
- Backend: sin cambios. Alembic esperado `x4y5z6a7b8c9` (verificar). Rutas: 211 (verificar).
- Docker build local: se intentará **si Docker está disponible** (no se instala infraestructura);
  si no, se marca `DOCKER_BUILD_NOT_EXECUTED` y `npm run build` (el comando exacto del Dockerfile)
  es el gate obligatorio.
- Build repetido en limpio: sí — segunda corrida tras eliminar `dist/` y tsbuildinfo (sin tocar deps).
- Deployment: NINGUNA acción manual (sin `docker pull`, sin recrear contenedores, sin tocar
  Watchtower). El push es el único disparador.

## Estrategia de commits

| Commit | Contenido | Regla |
|---|---|---|
| C1 | este paquete (spec/clarify/plan/checklist/tasks/matriz/replay/fingerprint/markers) | sin código de producto; push permitido (no altera build) |
| C2 | implementación mínima (3 ediciones) | solo con TODOS los gates locales verdes; el push ES el evento de despliegue |
| C3 | evidencia/cierre + backlog + reconciliación | no necesario para que el fix llegue; push de documentación |
