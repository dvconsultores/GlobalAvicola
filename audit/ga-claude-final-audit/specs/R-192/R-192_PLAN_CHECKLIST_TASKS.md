# R-192 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · Commits previstos: **C1** gobernanza + RED (sin producto) → **C2** implementación + GREEN → **C3** certificación runtime → **C4** UAT del propietario. Sensibilidad después del commit de implementación (se revierte con `git checkout` desde la raíz del repo).

## PLAN

| Fase | Contenido | Entregable | Estado |
|---|---|---|---|
| C1.1 | Preflight: HEAD limpio, suite backend PG local levantada (`backend/scripts/run_tests.sh`), pila local E2E (`scripts_e2e.sh` o arnés equivalente) | log de preflight | ☐ |
| C1.2 | Decisión C-01 solicitada al propietario (paquete `OWNER_DECISION`); resto de clarificaciones aplicadas por defecto | `R-192_CLARIFICATIONS.md` firmado | ☐ |
| C1.3 | RED backend: `backend/tests/test_r192_lot_close_after_reversal.py` (6 casos, §1 del diseño) — ejecutado en HEAD: 4 rojos esperados / 2 controles verdes | `evidence/r192/red/backend_red.log` | ☐ |
| C1.4 | RED frontend: `frontend/src/pages/lots/__tests__/r192.closeLotError.test.tsx` — rojo en HEAD | `evidence/r192/red/vitest_red.log` | ☐ |
| C1.5 | RED runtime: H8b (lotes gemelos) sobre HEAD ⇒ control 200 / con reverso 400 R7 «2 en «reversed»» + captura UI sin toast | `evidence/r192/red/runtime-red.json` + PNG | ☐ |
| C1.6 | Commit C1 (`GA-R192 C1: gobernanza + RED`) | hash | ☐ |
| C2.1 | T-03 R7 con `REVERSED`; T-04 resumen neto; T-05 BR-05 vigente | diff | ☐ |
| C2.2 | T-06 UI toast en `handleCloseLot` | diff | ☐ |
| C2.3 | GREEN dirigido (6+1) + suites completas (backend PG, vitest, tsc, build) | logs | ☐ |
| C2.4 | Commit C2 (`GA-R192 C2: implementación`) | hash | ☐ |
| C2.5 | Sensibilidad S1-S3 (tras C2, desde la raíz) | `evidence/r192/sensitivity.md` | ☐ |
| C3.1 | Runtime post-fix: H8b ⇒ 200/200; UI: toast (forzando R7 con contrapartida pendiente) + resumen; escritorio + móvil | `evidence/r192/runtime-c3.json` + PNG | ☐ |
| C3.2 | Certificación técnica `R192_RUNTIME_CERTIFICATION.md`; backlog actualizado | doc | ☐ |
| C4 | UAT del propietario (3 casos, §3 del diseño) + veredicto | acta UAT | ☐ |

## CHECKLIST (AC → tarea → archivo → test → evidencia)

| AC | Tarea | Archivo | Test | Evidencia | ☐ |
|---|---|---|---|---|---|
| AC01, AC02, AC03, AC04 | T-03 | `backend/app/operations/validators.py` (`validate_lot_records_approved`) | `test_r192_01`, `_02`, `_06` + `test_lot_close_approval.py` | `backend_green.log` | ☐ |
| AC05, AC06, AC07, AC08 | T-04 | `backend/app/lots/service.py` (`close_lot`) | `test_r192_03`, `_04` + `test_lot_closure.py` | ídem | ☐ |
| AC09 | T-05 | `backend/app/operations/validators.py` (`validate_lot_closure`) | `test_r192_05` | ídem | ☐ |
| AC10 | T-03 | — | `test_r192_02` (asserts de no mutación) | ídem | ☐ |
| AC11, AC12, AC13 | T-06 | `frontend/src/pages/lots/LotDetailPage.tsx` | `r192.closeLotError.test.tsx` | `vitest_green.log` + PNG | ☐ |
| AC14 | T-07 | — | `test_ac14_sin_migracion_ni_rutas_nuevas` (guardián existente) | log | ☐ |
| AC15 | T-07 | — | suites completas | logs | ☐ |
| AC16 | T-08 | — | runtime H8b + UI | `runtime-c3.json` | ☐ |
| AC17 | T-03b (condicional C-07) | `validators.py` | `test_r192_02` (detalle) | log | ☐ |

## TAREAS

| ID | Contenido | Archivos | Tamaño | Depende | ☐ |
|---|---|---|---|---|---|
| T-01 | Gobernanza: paquete R-192, solicitud de decisión C-01, dedup registrado | `audit/ga-claude-final-audit/specs/R-192/*` | S | — | ☐ |
| T-02 | RED: tests backend (6) + vitest (1) + runtime H8b RED; evidencia `evidence/r192/red/` | `backend/tests/test_r192_lot_close_after_reversal.py`, `frontend/src/pages/lots/__tests__/r192.closeLotError.test.tsx`, runner E2E | M | T-01 | ☐ |
| T-03 | R7: conjunto de no gobernados `ESTADOS_APROBADOS ∪ {CANCELLED, REVERSED}`; docstring con `OD-19`; (T-03b) mensaje «reverso pendiente de decisión» si C-07 | `backend/app/operations/validators.py:400-455` | S | T-02, C-01 | ☐ |
| T-04 | Resumen neto: `status.not_in([CANCELLED, REVERSED])` en mortalidad/alimento/huevos | `backend/app/lots/service.py:469-498` | S | T-02 | ☐ |
| T-05 | BR-05 vigente: `not_in([CANCELLED, REVERSED])` en pesaje y alimento | `backend/app/operations/validators.py:362-390` | S | T-02, C-05 | ☐ |
| T-06 | UI: `toast.error(getErrorMessage(err, t('lots.closeError')))` en `handleCloseLot`; (opcional C-06) `toast.success` | `frontend/src/pages/lots/LotDetailPage.tsx:107-118` | S | T-02 | ☐ |
| T-07 | GREEN dirigido + regresión completa (backend PG local; vitest; tsc; build); guardianes exactos sin cambio (rutas, Alembic) | — | M | T-03…T-06 | ☐ |
| T-08 | C3: runtime H8b post-fix + UI (escritorio/móvil) + certificación + backlog | `audit/ga-claude-final-audit/evidence/r192/`, `R192_RUNTIME_CERTIFICATION.md` | M | T-07 | ☐ |
| T-09 | Sensibilidad S1 (quitar `REVERSED` de R7 ⇒ AC01 roja), S2 (quitar filtro del resumen ⇒ AC05/AC06 rojas), S3 (quitar toast ⇒ AC11 roja); revertir con `git checkout` | — | S | T-07 | ☐ |
| T-10 | C4: UAT del propietario (3 casos) + acta | `audit/ga-claude-final-audit/specs/R-192/uat/` | S | T-08 | ☐ |

Riesgos: (a) C-01 negativa ⇒ rediseño; (b) suite backend en HEAD con 25 fallos preexistentes (`GA-GOV-03`) ⇒ la regresión se lee **por diferencia** contra la línea base documentada (`backend_full_suite.log`), no por «0 failed»; (c) H8b depende de que el rol aprobador de semillas tenga `review:review` (sí) y el solicitante `reversals:create` (`TEST Super Admin` sí).
