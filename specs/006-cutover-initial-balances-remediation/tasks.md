# Tasks: SPEC 006 — Cutover Initial Balances Remediation

**Input**: `specs/006-…/{spec,plan,research,data-model,template-contract}.md`
**Formato**: ID · Capa · Archivo probable · Objetivo · AC · Depende · Test · Estado
**Estados**: PENDING · DONE

## Fase A — Reproducción y spec

| ID | Capa | Archivo | Objetivo | AC | Depende | Test / evidencia | Estado |
|---|---|---|---|---|---|---|---|
| T001 | repro | `audit/cutover-initial-balances/01_LIVE_FAILURE_ROOT_CAUSE.md`, `evidence/head-repro/` | reproducir en HEAD por UI; procedencia del runtime | 01, 02 | — | journal + capturas | DONE |
| T002 | docs | `spec.md`, `research.md`, `data-model.md`, `template-contract.md`, `plan.md`, `tasks.md`, `quickstart.md` | /specify /clarify /plan /tasks | — | T001 | — | DONE |
| T003 | docs | `02_CURRENT_GAP_ANALYSIS.md` | gap actual + OUT_OF_SCOPE inventarios | 27, 28 | T002 | — | DONE |

## Fase B — RED

| ID | Capa | Archivo | Objetivo | AC | Depende | Test | Estado |
|---|---|---|---|---|---|---|---|
| T010 | test | `backend/tests/test_cutover_v2_red.py` | 9 escenarios RED sobre HEAD | 04–09, 13–15, 27, 30–35 | T002 | `evidence/red/` | DONE |

## Fase C — Backend

| ID | Capa | Archivo | Objetivo | AC | Depende | Test | Estado |
|---|---|---|---|---|---|---|---|
| T020 | backend | `cutover/contracts.py` | registry v2 por BU | 04–07, 27, 28 | T010 | contracts | DONE |
| T021 | bd | `lots/models.py`, `cutover/models.py`, `alembic/versions/e0f1a2b3c4d5_…` | columnas de opening + `hatchery_openings` | 23–26 | T020 | migración | DONE |
| T022 | backend | `cutover/parser.py` | XLSX+CSV → DTO común; límites; fórmulas | 08, 09, 12–16 | T020 | contracts | DONE |
| T023 | backend | `cutover/validation.py` | maestros, padre-hijo, fase, consistencia, lote/opening | 16–18 | T022 | validation | DONE |
| T024 | backend | `cutover/templates.py` | XLSX 4 hojas + CSV + catálogos | 10, 11 | T020 | contracts | DONE |
| T025 | backend | `cutover/service.py`, `schemas.py`, `router.py`, `route_scope.py` | listado/detalle, preview, errores descargables, apply por BU, reconciliación | 19–26, 29, 36–41 | T023 | apply | DONE |
| T026 | backend | `operations/validators.py`, `cutover/reporting.py`, `reports/service.py` | saldos con opening, CUT-GL-02, lifetime | 30–35 | T025 | continuity | DONE |
| T027 | backend | `tests/test_ga_req_061_cutover_*`, pines de arnés | fixture v2; rutas | 46 | T025 | suite | DONE |

## Fase D — Frontend y E2E

| ID | Capa | Archivo | Objetivo | AC | Depende | Test | Estado |
|---|---|---|---|---|---|---|---|
| T040 | frontend | `pages/cutover/*`, `services/cutover.service.ts`, locales | wizard por BU, XLSX/CSV, preview, errores, enlaces | 42–45, 47–49 | T025 | vitest | DONE |
| T041 | e2e | `e2e/proceso-p16-cutover-*.spec.ts`, `test-support/cutover.ts` | 4 E2E UI + primer evento | 50, 51, 55 | T040 | playwright | DONE |

## Fase E — Verificación y cierre

| ID | Capa | Objetivo | AC | Depende | Evidencia | Estado |
|---|---|---|---|---|---|---|
| T050 | test | verde dirigido + regresión completa backend/frontend/tsc/build/E2E | 46–55 | T041 | `evidence/` | DONE |
| T051 | git | commit de implementación (`IMPLEMENTATION_SHA`) | — | T050 | SHA | DONE |
| T052 | test | S1–S12 + restauración explícita + post-mutación | 52, 53 | T051 | `13_MUTATION_EVIDENCE` | DONE |
| T053 | docs | `03…16`, addendum `CUTOVER_MASTER_SPEC` | — | T052 | docs | DONE |
| T054 | git | commit de certificación + push + `REMOTE_SHA_MATCH` | 57, 58 | T053 | git | DONE |
| T055 | runtime | verificación en runtime compartido (4 BU) | 56 | T054 + credenciales UAT | `15_RUNTIME_VERIFICATION` | PENDING |
