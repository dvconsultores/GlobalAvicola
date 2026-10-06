# Tasks: SPEC 005 — SAP HANA Cloud READ ONLY Inbound

**Input**: `specs/005-sap-hana-cloud-readonly-inbound/{spec,plan,research,data-model}.md`
**Formato**: `ID · Capa · Archivo probable · Objetivo · AC · Depende · Test · Estado`
**Estados**: `PENDING` · `DONE`

---

## Fase A — Spec development

| ID | Capa | Archivo | Objetivo | AC | Depende | Test / evidencia | Estado |
|---|---|---|---|---|---|---|---|
| T001 | docs | `specs/005-…/spec.md` | /specify + /clarify (Q1–Q12) | 01–05 | — | revisión contra el mandato | DONE |
| T002 | docs | `plan.md`, `research.md`, `data-model.md`, `quickstart.md` | /plan | — | T001 | — | DONE |
| T003 | docs | `tasks.md` | /tasks | — | T002 | trazabilidad AC→tarea | DONE |
| T004 | docs | `audit/sap-hana-cloud/01`, `02`, `09`, `13 §3` | decisión, auditoría legacy, matriz de pruebas, /analyze | 01–03 | T003 | `OPEN_TECHNICAL_CONTRADICTIONS = 0` | DONE |
| T005 | docs | `docs/10`, addenda SOAP / SAP-0 / SAP-0P | punteros `SUPERSEDED` sin borrar | 02 | T004 | git diff | DONE |

## Fase B — RED

| ID | Capa | Archivo | Objetivo | AC | Depende | Test / evidencia | Estado |
|---|---|---|---|---|---|---|---|
| T010 | test | `backend/tests/test_sap_hana_guard.py` (guard + registry), `…_client.py` | RED unitario | 06–12, 40 | T003 | `evidence/red/` | DONE |
| T011 | test | `backend/tests/sap_hana_fixtures.py`, `test_sap_hana_sync.py`, `…_promotion.py`, `…_routes.py` | RED de integración | 13–39, 40 | T003 | `evidence/red/` | DONE |

## Fase C — Implementación backend

| ID | Capa | Archivo | Objetivo | AC | Depende | Test | Estado |
|---|---|---|---|---|---|---|---|
| T020 | config | `app/config.py`, `.env.example`, `pyproject.toml`, `requirements.txt` | variables `SAP_HANA_*`, `SAP_OUTBOUND_ENABLED`, `hdbcli` | 07, 34 | T010 | client | DONE |
| T021 | backend | `inbound/errors.py`, `settings.py` | errores cerrados, faltantes, política TLS | 08, 09, 34 | T020 | client | PENDING |
| T022 | backend | `inbound/sql_guard.py` | guard de solo lectura | 06, 11 | T010 | guard | DONE |
| T023 | backend | `inbound/registry.py` | 14 definiciones | 03, 12–24 | T022 | registry | PENDING |
| T024 | backend | `inbound/client.py`, `fake_hana.py`, `adapter.py` | cliente lazy fuera del event loop, fake, adaptador | 08–12, 35 | T023 | client | PENDING |
| T025 | bd | `inbound/models.py`, `alembic/versions/a7b8c9d0e1f2_…` | 4 tablas, `downgrade` | 25, 30 | T011 | migración + sync | DONE |
| T026 | backend | `inbound/staging.py`, `mapping.py` | validación, DTO, hash, mapping fail-closed | 26–29 | T025 | sync | PENDING |
| T027 | backend | `inbound/promotion.py` | upsert de referencias, OC con BR-18 | 31–33 | T026 | promotion | PENDING |
| T028 | backend | `inbound/service.py`, `schemas.py` | readiness, sync, watermark, auditoría, listados, mappings | 29, 30, 34, 35 | T027 | sync, routes | PENDING |
| T029 | backend | `inbound/router.py`, `main.py`, `route_scope.py`, `sap_contract.py` | rutas con RBAC, alcance y transacción | 04, 10, 36–39 | T028 | routes | PENDING |
| T030 | backend | `sap/router.py`, `sap/service.py` | outbound 409; `connection-check` inbound/outbound | 05, 35 | T029 | routes | PENDING |
| T031 | backend | `inbound/scheduler.py`, `main.py` | scheduler sin solape, apagado en tests | — | T028 | sync | PENDING |
| T032 | scripts | `scripts/run_tests.sh`, `scripts/data_classification.py` | 64 tablas; clasificación | 42 | T025 | suite | PENDING |
| T033 | test | suites existentes con `/sap/export` y `/sap/retry` | opt-in explícito de outbound para seguir probando la arquitectura de export | 42 | T030 | suite | PENDING |

## Fase D — Frontend y E2E

| ID | Capa | Archivo | Objetivo | AC | Depende | Test | Estado |
|---|---|---|---|---|---|---|---|
| T040 | frontend | `pages/sap/SapManagerPage.tsx`, `services/sap.service.ts` | panel inbound; export oculto | 05 | T030 | vitest | PENDING |
| T041 | frontend | `public/locales/{es,en}/translation.json` | i18n ES/EN | 43 | T040 | paridad | PENDING |
| T042 | test | `pages/sap/__tests__/sapInbound.test.tsx`, `gaFe04.sapGates.test.tsx` | gates y estado | 43 | T040 | vitest | PENDING |
| T043 | e2e | `e2e/sap-hana-inbound.spec.ts`, `scripts_e2e.sh` | flujo con fake HANA | 46 | T042 | playwright | PENDING |

## Fase E — Verificación y cierre

| ID | Capa | Objetivo | AC | Depende | Evidencia | Estado |
|---|---|---|---|---|---|---|
| T050 | test | verde dirigido | 41 | T033 | `evidence/green/` | PENDING |
| T051 | test | regresión completa backend | 42 | T050 | `evidence/regression/` | PENDING |
| T052 | test | vitest completo, `tsc -b`, `vite build` | 43–45 | T042 | `evidence/build/` | PENDING |
| T053 | test | E2E fake HANA + navegación 8/8 | 46 | T043 | `evidence/e2e/` | PENDING |
| T054 | git | commit de implementación | 51 | T051–T053 | SHA | PENDING |
| T055 | test | sensibilidad S1–S8 + restauración por SHA + post-mutación | 47, 48 | T054 | `10_MUTATION_EVIDENCE` | PENDING |
| T056 | docs | `audit/sap-hana-cloud/03…08, 10…13`, GA-REM-017 | catálogo, seguridad, mapping, runbook, certificación | 07, 55 | T055 | docs | PENDING |
| T057 | git | commit de certificación + push + SHA remoto | 49–54 | T056 | `REMOTE_SHA_MATCH` | PENDING |

## Fase F — Posterior a la credencial (NO iniciar)

| ID | Fase | Depende | Estado |
|---|---|---|---|
| T101 | `SAP-HANA-PROBE` P0–P9 (`12_REAL_SAP_ACTIVATION_RUNBOOK`) | credencial READ ONLY | PLANNED |
| T102 | Reconciliación funcional ⇒ `SAP_HANA_READONLY_CONNECTED_AND_RECONCILED` | T101 | PLANNED |

## Trazabilidad resumen AC→tarea

01–03→T001/T004 · 04→T029 · 05→T030/T040 · 06→T022 · 07→T020/T056 · 08–09→T021/T024 · 10→T029 · 11→T022 · 12→T023/T024 · 13–24→T023/T028 · 25→T025 · 26→T026 · 27→T026 · 28→T026 · 29→T028 · 30→T028 · 31–33→T027 · 34→T021/T028 · 35→T030 · 36–39→T029 · 40→T010/T011 · 41→T050 · 42→T051 · 43–45→T052 · 46→T053 · 47–48→T055 · 49–54→T054/T057 · 55→T056.
