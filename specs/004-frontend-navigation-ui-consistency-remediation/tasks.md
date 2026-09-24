# Tasks — 004 Frontend Navigation & UI Consistency Remediation

**Input**: `specs/004-…/{spec,plan,research}.md` · **IMPLEMENTATION_REQUIRED = YES** (frontend-only, autorizado por el mandato tras analyze; sin SAP/backend/workflows).

| ID | Tarea | AC | Depende | Estado |
|---|---|---|---|---|
| T001 | Auditoría de rutas → matriz completa | AC01 | — | ✅ DONE |
| T002 | Inventario legacy objetivo (LEG-01…LEG-06) | AC07-09 | T001 | ✅ DONE |
| T003 | SPEC/CLARIFY/PLAN/TASKS (esta cadena) | — | T001 | ✅ DONE |
| T004 | `/analyze`: 11 categorías (escritura oculta, queries, secretos, legacy-as-current, inconsistencia) | — | T003 | ✅ DONE (0 contradicciones; ver §ANALYZE en spec) |
| T005 | `BackNavigation` + `backResolver` + hook `useUnsavedChangesGuard` | AC02-04, AC14 | T003 | ⏳ |
| T006 | i18n keys de diálogo (ES/EN paridad) | AC15 | T005 | ⏳ |
| T007 | `SubNavHeader` route-aware (deep-link) | AC19 | T005 | ⏳ |
| T008 | Migrar back en 10 páginas (LotDetail, LotForm, OperationDetail, ReviewDetail, CorrectionForm, WeightCurves, LotReport, SapComparison, UnitAccess+añadir, ProcessStage) | AC02-04 | T005 | ⏳ |
| T009 | UX-01: redirect `/poultry` + eliminar wrapper/import legacy | AC07-09 | T005 | ⏳ |
| T010 | Saneo `operationBackTarget` en wizard | AC08 | T009 | ⏳ |
| T011 | Persistencia filtros listados (lots/operations) | AC10 | T005 | ⏳ |
| T012 | Unit tests nuevos (BackNavigation, guard) | AC14 | T005 | ⏳ |
| T013 | Actualizar tests desactualizados de `/poultry` | AC20 | T009 | ⏳ |
| T014 | E2E `navigation-consistency.spec.ts` (stubs, autónomo) | AC05/06/08/10/16-19/21 | T008-T011 | ⏳ |
| T015 | Regresión completa: vitest + tsc -b + vite build | AC20 | T008-T013 | ⏳ |
| T016 | `/converge` + commit + push + REMOTE_SHA | — | T015 | ⏳ |

**ANALYZE (previo a T005)**: sin operaciones de escritura backend; sin queries; sin secretos; sin legacy-as-current en la spec (la ruta legacy se retira, no se asume correcta); todos los "back" resueltos por contrato; sin dependencia Owner innecesaria. **PASS**.
