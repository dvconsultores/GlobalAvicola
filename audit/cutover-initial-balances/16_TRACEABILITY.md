# CUTOVER-INITIAL-BALANCES · 16_TRACEABILITY

Fecha: 2026-10-15 · SPEC 006 · `POST_CERTIFICATION_CUTOVER_INITIAL_LOAD_REMEDIATION` · Rama `main` · `NEW_BRANCH_CREATED = NO`

---

## 1 · Cadena

```text
DISCOVERY → /specify → /clarify → /plan → /tasks → /analyze → RED → IMPLEMENTATION → TARGETED GREEN
→ FULL REGRESSION → IMPLEMENTATION COMMIT → SENSITIVITY S1–S12 → EXPLICIT SHA RESTORE
→ POST-MUTATION REGRESSION → EVIDENCE → LOCAL CERTIFICATION → CERTIFICATION COMMIT → PUSH → REMOTE SHA VERIFY → RUNTIME
```

| Fase | Artefacto | Estado |
|---|---|---|
| Reproducción en vivo (HEAD `57a421a`, por UI) | `01_LIVE_FAILURE_ROOT_CAUSE.md`, `evidence/head-repro/` | DONE |
| DISCOVERY / brecha | `02_CURRENT_GAP_ANALYSIS.md`, `specs/006-…/research.md` | DONE |
| /specify + /clarify | `specs/006-…/spec.md` (FR-01…17, AC-CUT2-01…58, Q1–Q12) | DONE |
| /plan + data-model + template-contract + quickstart | `specs/006-…/{plan,data-model,template-contract,quickstart}.md` | DONE |
| /tasks | `specs/006-…/tasks.md` (T001…T055) | DONE |
| /analyze | §3 de este documento | DONE — `OPEN_TECHNICAL_CONTRADICTIONS = 0` |
| RED (9 escenarios, mandato §34) | `backend/tests/test_cutover_v2_red.py` · `evidence/red/red_on_head_57a421a.log` (9 failed sobre HEAD) | DONE |
| IMPLEMENTATION | `backend/app/cutover/{contracts,parser,validation,templates,service,reporting,models,schemas,router}.py`, `lots/models.py`, `operations/validators.py`, `reports/service.py`, migración `e0f1a2b3c4d5`, frontend `CargasInicialesPage` + servicio + i18n, E2E ×4 | DONE |
| TARGETED GREEN | `evidence/green/` (v2 76/76 · GA-REQ-061 + RED 48/48) | DONE |
| FULL REGRESSION | `evidence/regression/backend_full_pre_commit.log` · frontend 542/542 · tsc · build · E2E 12/12 | ver `14_LOCAL_CERTIFICATION.md` |
| IMPLEMENTATION COMMIT | `IMPLEMENTATION_SHA` en `14_LOCAL_CERTIFICATION.md §0` | ver §5 |
| SENSITIVITY S1–S12 + EXPLICIT SHA RESTORE | `13_MUTATION_EVIDENCE.md`, `evidence/mutations/` | ver `13_…` |
| POST-MUTATION REGRESSION | `evidence/post-mutation/` | ver `14_…` |
| LOCAL CERTIFICATION · CERT COMMIT · PUSH · REMOTE SHA | `14_LOCAL_CERTIFICATION.md`, §5 | ver §5 |
| RUNTIME | `15_RUNTIME_VERIFICATION.md` | ver `15_…` |

## 2 · Mandato → spec / evidencia

| Mandato § | Tema | Dónde queda resuelto |
|---|---|---|
| 1–3 | decisión, problema, reproducir primero | `01_LIVE_FAILURE_ROOT_CAUSE`, `spec.md §PROBLEM` |
| 4–5 | spec development, auditoría del proceso actual | `specs/006-…`, `02_CURRENT_GAP_ANALYSIS` |
| 6–8 | regla central, formatos, versionado | `spec.md §ARCHITECTURE_DECISION`, `08_XLSX_CSV_CONTRACT` |
| 9 | vacío/0/N/A por métrica | FR-04 · `parser.py` · `test_vacio_es_unknown…`, RED-07 |
| 10 | data lineage | `07_DATA_LINEAGE_MATRIX` (0 / 0) · RED-08 |
| 11–14 | plantillas por BU | `03…06_*_TEMPLATE_CONTRACT`, `template-contract.md` |
| 15–17 | catálogos, instrucciones, Meta | `templates.py` · `test_catalogos_de_la_plantilla…`, RED-02/03/06 |
| 18 | CSV | `parser.py` · RED-04 · paridad ×4 |
| 19–20 | validaciones estructurales y de dominio | `09_VALIDATION_CATALOG` · `test_cutover_v2_contracts/validation` |
| 21–23 | staging, preview, descarga de errores | `service.py` · RED-01/06 · `test_listado_detalle_errores_y_preview` |
| 24–27 | apply, lotes migrados, opening, incubadora | `10_APPLY_DESTINATION_MATRIX` · `test_cutover_v2_apply` · RED-05 |
| 28 | cutover date | CUT-GL-02 · `test_cut_gl_02…` · RED-09 · E2E ×4 |
| 29–30 | reconciliación, continuidad | `11_POST_CUTOVER_CONTINUITY` · `test_cutover_v2_continuity` |
| 31–32 | E2E por BU, XLSX+CSV | `e2e/proceso-p16-cutover-{grandparent,breeder,hatchery,broiler}.spec.ts` · 8 caminos + paridad |
| 33–34 | negativas, RED primero | `test_cutover_v2_contracts/validation/apply` · `evidence/red/` |
| 35–37 | UX, responsive, i18n | `CargasInicialesPage.tsx`, E2E (360/390/1280), `r061.cutoverFlow` + `cutoverV2` tests |
| 38 | no cambiar | SPEC 005 intacta; RBAC/OD-16/multiempresa reutilizados; GA-REQ-061 conservada (addendum en `CUTOVER_MASTER_SPEC`) |
| 39 | mutación S1–S12 | `13_MUTATION_EVIDENCE` |
| 40–41 | gates, certificación | `14_LOCAL_CERTIFICATION` |
| 42 | runtime | `15_RUNTIME_VERIFICATION` |
| 43 | git | §5 |
| 44 | documentos | este directorio (01…16) |

## 3 · /analyze (contradicciones técnicas)

| # | Riesgo analizado | Hallazgos abiertos | Cómo se cierra |
|---|---|---|---|
| 1 | Una plantilla genérica reaparece | 0 | registry cerrado con 4 contratos; RED-02 compara cabeceras |
| 2 | Campo de plantilla sin destino | 0 | `lineage()` = 0 / 0; RED-08 |
| 3 | UNKNOWN convertido en 0 | 0 | `{value,status}` por métrica; columnas NOT NULL heredadas llevan estado; S1 |
| 4 | N/A confundido con UNKNOWN | 0 | `NOT_APPLICABLE` explícito; `NOT_APPLICABLE_ON_REQUIRED`; S2 |
| 5 | Maestro de otra empresa resuelto | 0 | toda consulta filtra `company_id` (o global nulo); S3 |
| 6 | Galpón/incubadora de otro padre | 0 | `PARENT_MISMATCH`; S6 |
| 7 | Fase incompatible con la BU | 0 | `FASES_POR_BU`; `PHASE_INCOMPATIBLE`; INCUB implícita |
| 8 | Incubadora escondida en `notes` | 0 | `hatchery_openings` + saldos BR-03/BR-04 desde la apertura; S7/S8 |
| 9 | Doble conteo del histórico | 0 | CUT-GL-02 + `post = event_date > corte`; S9 |
| 10 | Duplicados de carga/lote | 0 | `DUPLICATE_UPLOAD`, `LOT_DUPLICATE`, `LOT_EXISTS_REUSE_REJECTED`, `OPENING_ALREADY_EXISTS`; S10 |
| 11 | Plantilla de otra BU/empresa/versión aceptada | 0 | `BUSINESS_UNIT_MISMATCH` (BU + schema_id), `COMPANY_MISMATCH`, v1 retirada; S11 |
| 12 | CSV con cabecera incompleta | 0 | `HEADER_MISSING`; S12 |
| 13 | Fórmulas/macros evaluadas | 0 | rechazo sin evaluar (`FORMULA_NOT_ALLOWED`, `MACRO_NOT_ALLOWED`) |
| 14 | Apply parcial | 0 | transacción única + `FAILED_APPLY` |
| 15 | RBAC/OD-16 alterados | 0 | mismos permisos `cutover:*`; `BU_DISABLED`/`BU_NOT_GRANTED`; S4 |
| 16 | Lectura de un opening v2 rompe `GET /lots/{id}` | 0 | validador movido a `OpeningBalanceCreate` |
| 17 | Pines del arnés | 0 | cabeza `e0f1a2b3c4d5`, 240 rutas, 65 tablas, clasificación `hatchery_openings` |
| 18 | Pantalla sin guía / batch perdido | 0 | wizard, listado, `?batch=`, errores con mensaje y descarga |
| 19 | Certificación GA-REQ-061 invalidada | 0 | suites conservadas con fixture migrada v1→v2; goldens 9.965/535 vigentes; addendum |
| 20 | SPEC 005 reabierta | 0 | ningún archivo de `integrations/sap` tocado |

```text
SPEC_CONSISTENCY = PASS
TASK_TRACEABILITY = PASS
OPEN_TECHNICAL_CONTRADICTIONS = 0
```

## 4 · Límites declarados

- Inventarios (alimento, vacunas, medicamentos, huevo comercial) como saldos de apertura: fuera de alcance (GL-OD-07).
- La certificación local la emite el agente ejecutor; el cierre formal corresponde al Owner.
- La verificación funcional en el runtime compartido depende de un usuario UAT con `cutover:*` (ver `15_…`).

## 5 · Commits y verificación remota

| Hito | SHA |
|---|---|
| Spec + RED + reproducción | `8edb777d11ad9a89ed3a6c3790bb231bf801be14` |
| Implementación (`IMPLEMENTATION_SHA`) | `507d896ebed2ec163fe6e8b1e1b5bbf65c1a7a68` |
| Certificación (`CERTIFICATION_SHA`) | `d1770ead73c3785a25ad365196b91104828b205c` (`REMOTE_SHA_MATCH = PASS`) |

Push a `origin/main` (AOD-29); `REMOTE_SHA_MATCH` y verificación del runtime en `15_RUNTIME_VERIFICATION.md`. Rama `main`; `NEW_BRANCH_CREATED = NO`; ningún workflow modificado.
