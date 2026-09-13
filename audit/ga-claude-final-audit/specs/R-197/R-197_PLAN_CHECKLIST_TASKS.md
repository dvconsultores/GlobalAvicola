# R-197 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · Sin implementación en este paquete. Orden de la cola (registro §3): bloque 7 (R-197 · R-207), tras GA-GOV-03 y el bloque de contratos del asistente.

## PLAN

| Fase | Contenido | Entregable | Estado |
|---|---|---|---|
| **C1 · Gobernanza + RED** | Dedup (hecho), FINDING, SPEC, CLARIFICATIONS, AC_MATRIX, diseño RED/E2E/UAT; tests RED backend (`test_r197_review_queue_contract.py`) y frontend (`r197.*.test.tsx`) **fallando por la causa exacta**; captura de evidencia RED (salida de pytest/vitest); decisiones C-04/C-07 elevadas al propietario | commit C1 «R-197 C1: gobernanza + RED (sin producto)» | ☐ |
| **C2 · Implementación** | Backend (`status`/`registered_by_id`, ruta de acciones, `response_model`, guardianes exactos); frontend (`ReviewCenter`, `ReviewDetail`, `ApprovalPanel`, `review.service.ts`, i18n); GREEN dirigido + suite backend completa en PG local + vitest/tsc/build | commit C2 «R-197 C2: bandeja por estado, historial por evento, resultado de aprobación» | ☐ |
| **C3 · Certificación runtime** | Despliegue; `scripts_e2e_r197.mjs live` sobre pila local (semillas) y sonda de contrato en nube; journal `evidence/r197/`; `fatal_react 0`, `httpErrores` sin `/users` 403 para el aprobador; informe `R197_RUNTIME_CERTIFICATION.md` | commit C3 | ☐ |
| **C4 · UAT** | Guía UAT-R197-01…06 para el propietario; sesión; acta; cierre en backlog (asignación GA-REM al autorizar; siguiente libre GA-REM-043) | commit C4 | ☐ |

## CHECKLIST (AC → tarea → fichero → test → evidencia)

| AC | Tarea | Fichero(s) | Test | Evidencia | Estado |
|---|---|---|---|---|---|
| 01-04 | T-02 | `review/router.py`, `review/service.py`, `review/schemas.py` | `test_r197_01…04` | pytest GREEN + sonda API | ☐ |
| 05-09 | T-04 | `ReviewCenter.tsx`, `review.service.ts` | `r197.reviewQueue.test.tsx` | E2E-02…E2E-06 | ☐ |
| 10-12 | T-03 | `review/router.py`, `review/service.py` | `test_r197_05…07` | pytest | ☐ |
| 13 | T-05 | `ReviewDetail.tsx` | `r197.reviewDetailHistory.test.tsx` | E2E-07 | ☐ |
| 14-15 | T-05, T-06 | `ReviewDetail.tsx`, `ApprovalPanel.tsx` | `r197.approvalResult.test.tsx`, `test_r197_08` (control) | E2E-08 | ☐ |
| 16-17 | T-06 | `ApprovalPanel.tsx` | `r197.approvalResult.test.tsx` | E2E-08 | ☐ |
| 18-19 | T-04 | `ReviewCenter.tsx` | `r197.reviewQueue.test.tsx` (sesión sin `users:read`) | journal `httpErrores` | ☐ |
| 20-21 | T-04, T-05 | `ReviewCenter.tsx`, `ReviewDetail.tsx`, locales | grep guard + render | capturas ES/EN | ☐ |
| 22-24 | T-07 | — | suites existentes (`test_review_bu_enforcement`, `test_review_decision_concurrency`, `test_segregation_r143`, `test_rbac`, `test_population_invariant`) | log suite completa | ☐ |
| 25 | T-07 | locales | vitest + capturas 390×844 | capturas | ☐ |
| 26 | T-01 | — | revisión del diff (sin migración / permiso) | diff | ☐ |
| 27 | T-08 | `scripts_e2e_r197.mjs` | runtime | `evidence/r197/runtime-*.json` | ☐ |
| 28 | T-09 | guía UAT | — | acta | ☐ |

## TAREAS

| ID | Contenido | Ficheros | Tamaño | Depende | Estado |
|---|---|---|---|---|---|
| T-01 | Gobernanza: paquete C1, evidencia RED, elevación C-04/C-07 | `specs/R-197/**`, `evidence/r197/red/` | S | — | ☐ |
| T-02 | Backend bandeja: `status` (lista validada, `ESTADOS_DE_BANDEJA`), `registered_by_id`, default compatible, `response_model` `ReviewQueueResponse` en `/review/pending` y `/approvals/pending` | `review/router.py`, `review/service.py`, `review/schemas.py` | M | T-01 | ☐ |
| T-03 | Backend historial: `GET /review/events/{event_id}/actions`, `listar_acciones` (empresa + unidad, sin lock), guardianes exactos (211→212, contrato de respuesta, `test_rbac`) | `review/router.py`, `review/service.py`, `tests/test_population_invariant.py`, `tests/test_business_unit_admin.py` | S | T-01 | ☐ |
| T-04 | Frontend bandeja: 7 pestañas, `status` por pestaña, `registered_by_id`, filtro operador condicionado a `users:read`, modal de observación (≥ 10), modal de nombre de lote, 403 ⇒ «sin permiso», toast de lote creado tras Completar | `ReviewCenter.tsx`, `review.service.ts`, locales | M | T-02 | ☐ |
| T-05 | Frontend detalle: historial desde la ruta nueva, permanencia + recarga, enlace al lote, `Badge`+`status.*`, validación inline sin `alert` | `ReviewDetail.tsx`, locales | M | T-03 | ☐ |
| T-06 | Frontend aprobación: leer respuesta de `approve` (enlace al lote), KPIs veraces, guarda de doble clic | `ApprovalPanel.tsx`, locales | S | T-02 | ☐ |
| T-07 | GREEN + regresión: dirigido, suite backend completa (PG local), vitest ≥ 314, `tsc`, `build`, capturas ES/EN y móvil | — | S | T-02…T-06 | ☐ |
| T-08 | C3: runner `scripts_e2e_r197.mjs` (calibrate/live), journal, certificación | `scripts_e2e_r197.mjs`, `evidence/r197/`, `R197_RUNTIME_CERTIFICATION.md` | M | T-07 | ☐ |
| T-09 | C4: guía y sesión UAT, acta, backlog | `specs/R-197/uat/` | S | T-08 | ☐ |

Dependencias externas: **GA-GOV-03** (suite verde reproducible antes de certificar); **R-208** (barra de lote) y **R-207** (marcador de contrapartida) tocan `ApprovalPanel`/`ReviewCenter` — coordinar orden de merge para evitar conflictos (R-208 antes, R-207 después).
