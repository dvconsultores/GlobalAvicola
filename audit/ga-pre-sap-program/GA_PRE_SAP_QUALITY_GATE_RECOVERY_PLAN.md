# GA · PRE-SAP — PLAN DE RECUPERACIÓN DE QUALITY GATES (TRANCHE 0 · §17/§52)

## 1 · Estado de partida (línea base congelada)

| Gate | Estado en HEAD | Evidencia |
|---|---|---|
| Suite backend (PG) | **25 failed · 1201 passed · 49 skipped** — 25 `TEST_DEFECT` | `evidence/backend_full_suite.log:624` |
| Suite Playwright procesos | **12 failed · 117 passed** — 12 `TEST_DEFECT` | `evidence/playwright_e2e.log:561-575` |
| Vitest | 314/314 | `evidence/frontend_checks.log:10-11` |
| `tsc` | exit 0 | id. |
| Build FE | OK | id. |
| CI de tests | **solo `pull_request`** (nunca disparado: 0 merges en 466 commits) | `.github/workflows/backend-ci.yml:4-12` |
| Certificaciones de proceso | sin commit/artefacto; 6 con suite hoy roja; contradicciones internas | GA-GOV-03 §2.4 |
| Guardas Alembic en tests | 2 fijadas a `x4y5z6a7b8c9` (cabeza real `y5z6a7b8c9d0`) | id. |

## 2 · Reglas (no negociables)

1. **Sin supresión**: prohibido `skip`/`xfail`/`only` para apagar fallos. Los 49 skips actuales se mantienen solo si son condicionales de entorno ya justificados (PG-only en local); en CI deben ejecutarse.
2. **Sin GREEN por declaración**: cada certificación (tranche, proceso, gate) cita **commit exacto + artefacto de corrida** materializado en `audit/.../evidence/`.
3. **RED antes de GREEN por spec**: cada spec añade sus tests primero (rojo), luego el fix, luego verde — patrón ya diseñado en los paquetes.
4. **Artefacto por tranche**: `backend_full_suite_<sha>.log`, `playwright_e2e_<sha>.log` (+ logs específicos del proceso tocado).
5. **Paridad runtime** en cada cierre de tranche cuando haya deploy: bundle desplegado == build del commit; endpoints sanos.

## 3 · Recuperación escalonada

| Etapa | Cuándo | Estado objetivo | Criterio de salida |
|---|---|---|---|
| **E0 · Línea base** | T0 (ahora) | Roja documentada (25+12), evidencia materializada | Este programa + commit de T0 |
| **E1 · Verde de gobernanza** | **T1 (GA-GOV-03) — EJECUTADA 2026-09-13 (commit `66be1c1`)** | **0 failed** en ambas suites + CI en `push` + regla de evidencia publicada + backlog reconciliado | ✔ Backend `1226/0/0/49` + JUnit (`evidence/backend-junit-post-t1.xml`); ✔ Playwright `129/0`; ✔ workflow `Quality Suite (push)` publicado SIN dependencia del deploy (EX-01 intacto); ✔ plantilla `CERTIFICATION_EVIDENCE_TEMPLATE.md`; ✔ backlog (`R-189`, `GA-UAT-09`, `OD-21…25`). Salvedad: primer run del workflow = `BLOCKED_EXTERNAL_CI_OBSERVATION` (sin credenciales GitHub en el entorno; el push lo disparó). |
| **E2 · Por tranche** | T2-T11 | Suites globales verdes + tests nuevos de la spec (RED→GREEN) + E2E del proceso afectado | Gate de tranche (§39 roadmap) |
| **E3 · Recertificación** | T12 | 17 procesos recorridos E2E con artefacto; suites verdes completas; runtime paridad; Wave C decidida | Matriz de procesos 17/17 en estado certificable |
| **E4 · Gate final** | T13 | Todo verde + Pista OPS cerrada + decisiones registradas + UAT del propietario con evidencia primaria | GO/NO-GO final defendible |

## 4 · Objetivos numéricos

- Backend: de `1201 passed / 25 failed` → **`1226 passed / 0 failed / 49 skipped`** (T1) y creciendo con tests nuevos por tranche (cada spec añade ≥1 test de contrato y ≥1 E2E del proceso).
- Playwright: de `117 / 12` → **`129 / 0`** (T1) + regresiones por tranche (T4-T11) + pasada integral T12.
- Vitest/tsc/build: mantener verdes en cada tranche.

## 5 · Riesgos de la recuperación y mitigación

| Riesgo | Mitigación |
|---|---|
| Los fixtures «corregidos» escondan defectos reales | Clasificación caso a caso ya hecha (37 TEST_DEFECT, 0 APP_DEFECT directo; R-213 rastreado aparte); los fixtures se corrigen **hacia la regla vigente**, no relajando la regla |
| El grupo B (R-213) tape el defecto de `/me` | En T1 el fixture usa dominio válido; el defecto de producto se corrige en T11 con test propio de lectura tolerante |
| CI en `push` ralentice deploys | `OD-23`: gate de tests en `push` **sin bloquear** `docker-push` (jobs separados), con notificación; decisión documentada |
| Cobertura de skips en CI | Los 49 skips se ejecutan en CI PG; si alguno falla en CI, entra al inventario como TEST_DEFECT con dueño |
