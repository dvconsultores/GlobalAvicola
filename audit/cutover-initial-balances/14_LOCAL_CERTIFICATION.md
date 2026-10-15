# CUTOVER-INITIAL-BALANCES · 14_LOCAL_CERTIFICATION

Fecha: 2026-10-15 · SPEC 006 — Remediación de Cargas Iniciales / saldos de apertura (`POST_CERTIFICATION_CUTOVER_INITIAL_LOAD_REMEDIATION`) · Rama `main` (sin rama nueva)

> Certificación **local** emitida por el agente ejecutor con la evidencia de `evidence/`; el cierre formal corresponde al Owner (constitución Art. 9). Ninguna llamada a SAP; ningún workflow modificado; RBAC, OD-16 y multiempresa intactos; certificación GA-REQ-061 conservada (addendum en `audit/go-live/CUTOVER_MASTER_SPEC.md`).

---

## 0 · Commits

| Hito | SHA |
|---|---|
| Spec + RED + reproducción (`SPEC-006 (SPEC+RED)`) | `8edb777d11ad9a89ed3a6c3790bb231bf801be14` |
| Implementación (`IMPLEMENTATION_SHA`, fuente de restauración de S1–S12) | **`507d896ebed2ec163fe6e8b1e1b5bbf65c1a7a68`** |
| Certificación y evidencia (`CERTIFICATION_SHA`) | el commit que introduce este documento (`git log -1 -- audit/cutover-initial-balances/14_LOCAL_CERTIFICATION.md`); ver `15_RUNTIME_VERIFICATION.md` |

## 1 · Veredicto

```text
ROOT_CAUSE                                   = una plantilla genérica v1 para 4 BU + UX sin guía (ver 01_)
TEMPLATES                                    = GRANDPARENT V2 · BREEDER V2 · HATCHERY V2 · BROILER V2
XLSX = PASS · CSV = PASS (paridad XLSX_RESULT == CSV_RESULT ×4)
UNMAPPED_TEMPLATE_FIELDS                     = 0
REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE = 0
GRANDPARENT_APPLY = PASS · BREEDER_APPLY = PASS · HATCHERY_APPLY = PASS · BROILER_APPLY = PASS
GRANDPARENT_POST_CUTOVER = PASS · BREEDER_POST_CUTOVER = PASS · HATCHERY_POST_CUTOVER = PASS · BROILER_POST_CUTOVER = PASS
UNKNOWN_ZERO_NA = PASS · CROSS_COMPANY = PASS · BU_SCOPE = PASS · IDEMPOTENCY = PASS
LOCAL_IMPLEMENTATION                         = CERTIFIED
```

## 2 · Gates pre-commit (sobre el árbol que se convirtió en `507d896`)

| Gate | Resultado | Evidencia |
|---|---|---|
| RED sobre HEAD `57a421a` | 9 failed (comportamiento incorrecto demostrado) | `evidence/red/red_on_head_57a421a.log` |
| Verde dirigido v2 (RED 9 + contratos 33 + validación 11 + apply 9 + continuidad 6) | **76 passed / 0 failed** | `evidence/green/v2_suites_run2.log` |
| GA-REQ-061 C1–C7 con fixture v1→v2 (goldens 10.000 → 9.965, lifetime 535 intactos) | **48 passed** (39 + RED 9) | `evidence/green/targeted_run2.log` |
| Regresión completa backend | **1706 passed / 0 failed / 49 skipped** (22:54 min) | `evidence/regression/backend_full_pre_commit.log` |
| Frontend `vitest` | 91 archivos / **542 passed** (base 539) | `evidence/build/frontend_vitest_pre_commit.log` |
| `tsc -b` · `vite build` | PASS · PASS | `evidence/build/tsc_pre_commit.log`, `vite_build_pre_commit.log` |
| E2E UI por BU (4) + navegación (8) | **12 passed** | `evidence/e2e/e2e_run2.log`, `evidence/e2e/journals/e2e-{grandparent,breeder,hatchery}-xlsx.json`, `e2e-broiler-csv.json` |

Iteraciones previas conservadas y explicadas en `12_TEST_EVIDENCE.md §1` (fixtures de fechas, BR-08, zona horaria del `datetime-local`): ninguna exigió cambiar una regla de negocio.

## 3 · Sensibilidad y regresión post-mutación (sobre `507d896`)

| Gate | Resultado | Evidencia |
|---|---|---|
| S1–S12 | **12/12 DETECTED**; restauración `git restore --source=507d896` byte a byte; `FINAL_DIFF = 0` | `13_MUTATION_EVIDENCE.md`, `evidence/mutations/` |
| Regresión completa backend post-mutación | **1706 passed / 0 failed / 49 skipped** (22:48 min) | `evidence/post-mutation/backend_full_post_mutation.log` |
| Frontend `vitest` · `tsc -b` · `vite build` | **542 passed** · PASS · PASS | `evidence/post-mutation/frontend_vitest_post_mutation.log`, `tsc_post_mutation.log`, `vite_build_post_mutation.log` |
| E2E UI por BU + navegación | **12 passed** | `evidence/post-mutation/e2e_post_mutation.log` |
| Migración `e0f1a2b3c4d5` | upgrade fresh (65 tablas, `hatchery_openings` + 14 columnas v2, 6 índices/únicos) · `downgrade -1` (64 tablas, 0 columnas v2, tabla eliminada) · upgrade sobre esquema existente · 0 enums nuevos · ORM == BD | `evidence/post-mutation/migration_verification.log` |

## 4 · Gates funcionales

| Gate | Resultado | Pruebas |
|---|---|---|
| CONTRACT_PER_BU · V1_RETIRED | PASS | `test_registry_cerrado_cuatro_contratos_v2`, `test_version_retirada_y_desconocida`, RED-02/03 |
| XLSX_CSV_PARITY | PASS | `test_paridad_xlsx_csv[4]`, RED-04 |
| UNKNOWN_ZERO_NA | PASS | `test_vacio_es_unknown…`, RED-07, `test_unknown_se_propaga…` (S1, S2) |
| DATA_LINEAGE | PASS (0 / 0) | RED-08, `test_lineage…` |
| CATALOGS_BY_COMPANY_BU | PASS | `test_catalogos_de_la_plantilla_solo_empresa_y_bu` |
| DOMAIN_VALIDATION (maestros, padre-hijo, fase, consistencia, fechas) | PASS | `test_cutover_v2_validation.py` (S3, S6, S7) |
| STAGING_ONLY · ERRORS_DOWNLOAD · PREVIEW | PASS | C2, RED-01/06, `test_listado_detalle_errores_y_preview` |
| APPLY_DESTINATION (4 BU) | PASS | `test_apply_*` (S8) |
| HATCHERY_OPENING | PASS | RED-05, `test_apply_hatchery…`, `test_hatchery_siguiente_paso…` |
| CUT-GL-02 | PASS | `test_cut_gl_02…`, RED-09, E2E ×4 (S9) |
| RECONCILIATION_UNKNOWN_PROPAGATION | PASS | C5, `test_unknown_se_propaga…` |
| FIRST_OPERATION_AFTER_CUTOVER (4 BU) | PASS | `test_cutover_v2_continuity.py`, E2E ×4 |
| IDEMPOTENCY · DOUBLE_APPLY · SEGREGATION | PASS | `test_idempotencia_doble_apply_y_segregacion`, C3/C4/C7 (S5, S10) |
| CROSS_COMPANY · BU_DISABLED · BU_NOT_GRANTED | PASS | `test_multiempresa_bu_deshabilitada_y_sin_concesion`, C7 (S4) |
| TEMPLATE_WRONG_BU/COMPANY/VERSION · CSV_HEADER | PASS | `test_plantilla_de_otra_bu_rechazada`, `test_plantilla_de_otra_empresa…` (S11, S12) |
| RBAC_INTACT · OD16_INTACT · MULTIEMPRESA_INTACT | PASS | regresión completa (`test_rbac.py`, `test_business_unit_guard.py`, suites OD-16/R-201) |
| SPEC_005_INTACT | PASS | ningún archivo de `backend/app/integrations/sap` modificado; suites SAP en la regresión completa |
| RESPONSIVE 360/390/desktop · I18N ES/EN | PASS | E2E (desborde ≤ 1 px), `r061.cutoverFlow.test.tsx::AC84/85` |
| SECRETS | 0 | logs con JWT efímeros y DSN redactados; `local_creds.env` fuera del repo |

## 5 · Pruebas existentes adaptadas (sin cambio de regla)

- `test_ga_req_061_cutover_c2…c7`: la fixture `_xlsx` genera la plantilla **v2 de reproductoras** desde las mismas filas de 8 columnas; `_crear_batch` usa la BU de la fixture; el reuso de lote existente es explícito (`existing_lot_code`, AC20-21/AC53); los duplicados se detectan en el staging (CUT-RED-22, C4) y el apply conserva la guarda defensiva.
- `test_c2_plantilla_descargable_y_cargable`: versión v2 + hoja `Catalogos`; una plantilla vacía ya no queda VALIDATED (`NO_DATA_ROWS`).
- `r061.cutoverFlow.test.tsx`: etiquetas v2 («Crear carga», «Subir archivo (XLSX o CSV)»), preview desde el endpoint por BU.
- Pines del arnés: cabeza `e0f1a2b3c4d5`, 240 rutas, 65 tablas, `hatchery_openings` clasificada.
- E2E `proceso-p16-cutover-cargas-iniciales.spec.ts` (API-only, contrato v1) retirado del árbol y sustituido por cuatro specs de interfaz por BU (la historia queda en git).

## 6 · Deuda y límites

- Inventarios (alimento, vacunas, medicamentos, huevo comercial) como saldos de apertura: fuera de alcance (GL-OD-07).
- `post.feed_kg` de la reconciliación conserva la semántica certificada en GA-REQ-061 (`null` cuando la apertura de alimento es UNKNOWN); el post real viaja en `post.feed_kg_registered`.
- `LotPhase.start_population_*` no tiene columna mixta: para engorde/incubadora queda 0/0 y la población vive en `opening_balances.initial_mixed_count`.
- La verificación funcional en el runtime compartido depende de un usuario UAT con `cutover:*` (`15_RUNTIME_VERIFICATION.md`).
