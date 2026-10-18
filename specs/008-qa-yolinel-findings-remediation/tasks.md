# Tasks: SPEC 008 — QA Yolinel Findings Remediation

**Directorio**: `specs/008-qa-yolinel-findings-remediation` · **Rama**: `main` (sin rama nueva) · **Baseline**: `83c9cd8`
**Created**: 2026-10-18 · **Status**: `IMPLEMENTED_PENDING_CERTIFICATION` · **Prioridad**: P1
**Referencias**: `spec.md` (FR-01…FR-08, AC-xx), `plan.md` (§3 FASE R, §11 sensibilidad), `audit/qa-yolinel-2026-10-17/01…09`

Estados: `DONE` · `EN CURSO` · `PENDING` · `BLOCKED (Owner)` · `BLOCKED (externo)`.

SHA de implementación: `{{IMPL_SHA}}` · SHA de certificación: `{{CERT_SHA}}` · Regresión: **1739 passed · 0 failed · 49 skipped** / **96 archivos · 557 pruebas PASS**

---

## FASE 0 — Discovery y clasificación

| ID | Tarea | Salida | QA | Estado |
|---|---|---|---|---|
| T01 | Discovery: lectura de la fuente y del código citado (maestros, validadores, inbound, review, frontend) | `04_CODE_VALIDATION.md` (archivo:línea) | todos | **DONE** |
| T02 | Clasificación formal de los 18 hallazgos y conteos | `02_FINDINGS_CLASSIFICATION.md`, `03_REQUIREMENT_TRACEABILITY.md`, matriz de `spec.md` | QA-001…018 | **DONE** |

## FASE R — RED (tests que deben fallar antes de implementar)

| ID | Tarea | Test | QA / FR | Estado |
|---|---|---|---|---|
| T03 | RED BR-23: cadena de la OC (mismatch, conflicto, desconocida) y filtro de cadena en `/sap/references` | `backend/tests/test_br23_sap_reference_business_unit.py` (5 pruebas) + `frontend/src/pages/operations/__tests__/qaYolinel.sapOrderByUnit.test.tsx` (3) — notación RED→GREEN consolidada en un archivo por ámbito | QA-007 / FR-01 | **DONE** |
| T04 | RED etiquetas de maestros: guardián de claves de columna + campo↔valor | `frontend/src/__tests__/qaYolinel.red.test.tsx` (guardián de rótulos) + `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` | QA-013 / FR-02 | **DONE** |
| T05 | RED padre en hijos: Galpones/Incubadoras/Nacedoras muestran Granja/Planta | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` (caso (a): columna del padre) | QA-012 / FR-03 | **DONE** |
| T06 | RED estado y «Desactivar»: rótulo, columna Estado, fila atenuada, toast de error | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` (casos (b) y (c)) | QA-002 / FR-04 | **DONE** |
| T07 | RED bucle de revisión: conteo de peticiones estable (Centro de Revisión y `ApprovalPanel`) | `frontend/src/__tests__/qaYolinel.red.test.tsx` (QA-017: 1 `GET /review/pending` sin interacción) | QA-017 / FR-05 | **DONE** |
| T08 | RED fechas y listados: `max=hoy` en `event_date`; `farm_name`/`created_by`/`created_at`; filtro Granja | `frontend/src/__tests__/qaYolinel.red.test.tsx` (QA-016) · `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` (3) · `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` (2) · `backend/tests/test_qa_yolinel_list_enrichment.py` (3) | QA-016, QA-014, QA-015, QA-018 / FR-06, FR-07 | **DONE** |

## FASE 1 — Backend · BR-23

| ID | Tarea | Archivos | QA / FR | Estado |
|---|---|---|---|---|
| T09 | Implementar `derive_oc_chain` + validación BR-23 junto a `validate_oc_limit` (sin tocar BR-18) + `business_unit_code`/`chain_known` en el contrato + filtro de cadena en `/sap/references` | `backend/app/operations/validators.py` (`derive_oc_business_unit`, `derive_oc_business_units`, `validate_oc_business_unit`), `backend/app/operations/service.py`, `backend/app/integrations/sap/{service,router,schemas}.py` — cubierto por `backend/tests/test_br23_sap_reference_business_unit.py` | QA-007 / FR-01 | **DONE** |

## FASE 2 — Frontend · Maestros

| ID | Tarea | Archivos | QA / FR | Estado |
|---|---|---|---|---|
| T10 | Claves i18n propias para las 20 columnas mal etiquetadas (ES/EN) + guardián | `frontend/src/App.tsx` (42 columnas revisadas), `frontend/public/locales/{es,en}/translation.json` (`masters.fields.*`) — cubierto por `qaYolinel.red.test.tsx` y `qaYolinel.mastersList.test.tsx` | QA-013 / FR-02 | **DONE** |
| T11 | Estado/«Desactivar»/«Reactivar», columna Estado, fila atenuada, toast de error, nota OD-24 para maestros SAP; columna Granja/Planta en Galpones, Incubadoras y Nacedoras | `frontend/src/pages/masters/MasterListPage.tsx`, `frontend/src/components/data-table/DataTable.tsx` (`rowClassName`, `RowAction.visible`) — cubierto por `qaYolinel.mastersList.test.tsx`; rótulo ajustado en `gaFe04.mastersGates.test.tsx` | QA-002, QA-012, QA-003 (UX columnas descriptivas) / FR-04, FR-03 | **DONE** |

## FASE 3 — Frontend · Revisión

| ID | Tarea | Archivos | QA / FR | Estado |
|---|---|---|---|---|
| T12 | Estabilizar `useCan`/`fetchEvents`/`toast`; eliminar el REQUEST_LOOP; guardia anti-respuesta obsoleta | `frontend/src/auth/actionAuthority.tsx` (`useCallback`), `frontend/src/pages/review/ReviewCenter.tsx` (`tRef`/`toastRef`, `canReadUsers`), `frontend/src/pages/approvals/ApprovalPanel.tsx` — cubierto por `qaYolinel.red.test.tsx` | QA-017 / FR-05 | **DONE** |
| T13 | Columnas «Registrado por» y «Fecha de registro» (`created_at`) distinguidas de la fecha del evento | `ReviewCenter.tsx`, `ApprovalPanel.tsx`, `OperationListPage.tsx`, `MyPendingPage.tsx` + `common.registeredBy|registeredAt|eventDate` — cubierto por `qaYolinel.reviewColumns.test.tsx` y `qaYolinel.listColumns.test.tsx` | QA-018 / FR-07 | **DONE** |

## FASE 4 — Frontend · Fechas

| ID | Tarea | Archivos | QA / FR | Estado |
|---|---|---|---|---|
| T14 | `max=hoy` en `input type=date` de fecha de evento (no en planificadas/cutover) + inventario `FIELD/ROUTE/ALLOW_FUTURE` | `frontend/src/utils/dates.ts` (`hoyISO`), `frontend/src/pages/operations/OperationFormPage.tsx` (fecha del evento + salida/llegada de importación) — cubierto por `qaYolinel.red.test.tsx`; inventario de fechas en `06_IMPLEMENTATION_EVIDENCE.md` §2.2 y `08_RUNTIME_VERIFICATION.md` §3.8 | QA-016 / FR-06 | **DONE** |

## FASE 5 — Backend + Frontend · Listados y filtro Granja

| ID | Tarea | Archivos | QA / FR | Estado |
|---|---|---|---|---|
| T15 | BE: `farm_name`/`hatchery_name`, `created_by`, `created_at` en contratos de lectura sin N+1; test de contrato de `farm_id`/`status`/`date_*` | `backend/app/operations/enrichment.py` (nuevo), `backend/app/lots/{schemas,service}.py`, `backend/app/operations/{schemas,service}.py`, `backend/app/review/service.py` — cubierto por `backend/tests/test_qa_yolinel_list_enrichment.py` (`farm_name`/`house_name`/`lot_code`/`registered_by_name`; `hatchery_name` no aplica: no existe `hatchery_id` en los endpoints, ver QA-015) | QA-014, QA-015, QA-018 / FR-07 | **DONE** |
| T16 | FE: columnas condicionales Granja/Planta + Registrado por + Fecha de registro en Lotes, Historial, Mis pendientes, Centro de Revisión y Aprobaciones; filtro **Granja**; documentar Planta como pendiente | `LotListPage.tsx`, `OperationListPage.tsx`, `MyPendingPage.tsx`, `ReviewCenter.tsx`, `ApprovalPanel.tsx`, `FilterPanel.tsx` — cubierto por `qaYolinel.listColumns.test.tsx` y `qaYolinel.reviewColumns.test.tsx`; brecha de Planta declarada en `05_FIX_PLAN.md` §3 y `09_RESPONSE_TO_QA.md` | QA-014, QA-015, QA-018 / FR-07 | **DONE** |

## FASE 6 — Regresión

| ID | Tarea | Comando | Estado |
|---|---|---|---|
| T17 | Regresión completa (backend + frontend + typecheck) sin fallos nuevos vs `83c9cd8` | `backend/scripts/run_tests.sh` · `npx vitest run` · `npx tsc -b` | **DONE** — backend **1739 passed · 0 failed · 49 skipped** (22 min 26 s); frontend **96 archivos · 557 pruebas PASS** (`557/557`), `tsc_rc=0`, `build_rc=0`. Delta vs certificación SPEC 007 (1731/0/49 y 542): +8 y +15, ningún test eliminado ni marcado `skip`. Acotada: 118 passed. Ver `audit/qa-yolinel-2026-10-17/07_TEST_EVIDENCE.md` §2 |

## FASE 7 — Commit

| ID | Tarea | Resultado | Estado |
|---|---|---|---|
| T18 | Commit en `main` con referencia QA-ID/FR (sin push, sin rama) | mensaje `SPEC-008: ...` | PENDING |

## FASE 8–9 — Sensibilidad y restore

| ID | Tarea | Mutaciones | Estado |
|---|---|---|---|
| T19 | Mutaciones S1 (permitir OC cross-BU), S5 (desactivar BR-14 — ya cubierta por `test_segregation_r143`), S6 (ocultar filtro empresa), S7 (bucle de revisión), S8 (etiqueta de maestro); restaurar y re-verificar | plan.md §11 | PENDING (`{{SENSITIVITY}}`) |

## FASE 10 — Documentación DOCX, certificación y push

| ID | Tarea | Salida | Estado |
|---|---|---|---|
| T20 | `OPERATION_STATE_MACHINE.md`, «Cómo Global Avícola recibe información de SAP», `lots.origin`, segregación, `PROCESS_PREDECESSOR_MATRIX` propuesta, matriz de autocompletado, inventario de fechas → DOCX; certificado `LOCALLY_CERTIFIED`; push autorizado | docs + certificado | PENDING — los `.md` están entregados (`OPERATION_STATE_MACHINE.md`, `SAP_PARA_QA.md`, `LOT_ORIGIN_AND_MASTERS_FOR_QA.md`, `PROCESS_PREDECESSOR_MATRIX.md`); faltan DOCX, certificado y verificación en runtime (`08_RUNTIME_VERIFICATION.md` = `NOT_VERIFIED_FROM_WORKSTATION`) |

---

## Bloqueos por decisión del Owner

| Task | Depende de | Efecto |
|---|---|---|
| Unicidad de vacunas/medicamentos/causas | **OD-QA2-01** | Sin implementación; estado actual documentado |
| Zona/área de planta de incubación | **OD-QA2-02** | Sin implementación; `location` texto se documenta |
| Autocompletado adicional de Recepción de Aves | **OD-QA2-03** | Sin implementación; matriz entregada |
| Reglas de predecesor en backend | **OD-QA2-04** | Matriz propuesta entregada; **no** se implementa en SPEC 008 |
| Fechas planificadas/cutover con futuro | **OD-QA2-05** | Solo `event_date` recibe `max=hoy` |

## Progreso

| Fase | Total | DONE | EN CURSO | PENDING |
|---|---|---|---|---|
| FASE 0 | 2 | 2 | 0 | 0 |
| FASE R | 6 | 6 | 0 | 0 |
| FASE 1 | 1 | 1 | 0 | 0 |
| FASE 2 | 2 | 2 | 0 | 0 |
| FASE 3 | 2 | 2 | 0 | 0 |
| FASE 4 | 1 | 1 | 0 | 0 |
| FASE 5 | 2 | 2 | 0 | 0 |
| FASE 6 | 1 | 1 | 0 | 0 |
| FASE 7–10 | 3 | 0 | 0 | 3 |
| **Total** | **20** | **17** | **0** | **3** |

### Qué falta para cerrar

1. **T17** — CERRADA: regresión backend completa **1739 passed · 0 failed · 49 skipped** (22 min 26 s) y frontend
   **96 archivos · 557 pruebas PASS** con `tsc_rc=0` y `build_rc=0`. Suite acotada: **118 passed** (1 min 42 s), con el
   log `evidence/07_backend_targeted.log` regenerado tras corregir la lista de archivos.
2. **T18** — commit en `main` con `{{IMPL_SHA}}` y referencia a los QA-ID.
3. **T19** — sensibilidad S1/S5/S6/S7/S8 con restauración verificada (`FINAL_DIFF=0`).
4. **T20** — DOCX, certificado `LOCALLY_CERTIFIED` y verificación en UAT (`08_RUNTIME_VERIFICATION.md`;
   dataset QA-DEMO-V1 sigue `BLOCKED_EXTERNAL`).
5. **Contraste con el PDF original de QA**: no disponible en la estación; los 18 hallazgos se trabajaron desde el
   mandato del Owner y quedan «pendiente de contraste con el PDF».
