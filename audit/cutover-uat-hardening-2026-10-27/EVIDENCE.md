# GA-CUTOVER-UAT-HARDENING-2026-10-27 — Evidencia

**Fecha:** 2026-10-27 · **Rama:** `main` · **Baseline HEAD:** `1436c27` · **IMPL HEAD:** `5f3a698` · **Spec:** `specs/011-cutover-uat-hardening/spec.md` (amendment de SPEC 006/009/010). SAP READ-ONLY, 0 escrituras; sin DB/migración. Dataset QA (QA-DEMO-V1), prefijos QA/UAT.

Entrada UAT (Yolinel, empresa `QA Avícola Integral`, usuarios `qa.admin`/`qa.approver`, 4 BU): `FUNCTIONAL_HAPPY_PATH_PASS / UAT_INCOMPLETE`. El módulo NO está roto.

## 1. Findings disposition

### CUTOVER-UX-01 — botones sin etiqueta · **NO_DEFECT_ON_HEAD (P3)**
- Root cause: en HEAD los botones usan `t('cutover.*')` con claves presentes (es/en) y los tests `getByRole({name:'...'} )` pasan ⇒ etiquetas renderizan. El blanco reportado = bundle/caché previo a SPEC 010.
- Fix: ninguno (sin defecto). Cobertura: aserciones `getByRole(name)` existentes + verificación visual UAT (`uat_cutover_*` de SPEC 010).
- Resultado: **NO_FIX_NEEDED / VERIFIED**.

### CUTOVER-UX-02 — filename sin versión · **FIXED (P2)**
- Root cause: `CargasInicialesPage.tsx` hardcodeaba `_v2`; ignoraba el `Content-Disposition` del servidor (que ya trae `cutover_template_<bu>_<version>`).
- Fix: helper `nombreDescarga(res, fallback)` usa el filename del header (versión real); fallback a `batch.template_version`; descarga temprana sin `_v2`.
- Tests: `cutoverV2.test.tsx` → `CUTOVER-UX-02: nombreDescarga ...` (Content-Disposition v3 + fallback). **PASS**.

### CUTOVER-DATA-01 — `Meta.cutover_datetime` vacío · **FIXED (P2, presentación — NO integridad)**
- Root cause: la descarga temprana (sin batch, SPEC 010) no enviaba el corte; el endpoint solo lo rellenaba desde el batch. **Autoridad del corte = batch**: `apply`/`reconciliación` usan `batch.cutover_datetime` (service.py); el **parser IGNORA** `Meta.cutover_datetime` (parser.py:306-309 solo lee template_version/business_unit/schema_id/company). Sin pérdida de semántica.
- Fix: param opcional `cutover_datetime` en `GET /cutover-templates/{bu}` (solo display en Meta); la descarga temprana envía el corte elegido. Meta nunca es autoridad.
- Tests: backend `test_cutover_uat_hardening_s011.py` (Meta refleja el corte / parser lo ignora) **2/2 PASS**; frontend `RC-010` envía `cutover_datetime`. **PASS**.

### CUTOVER-DOC-01 — `source_lot_code` poco claro · **FIXED (P2)**
- Root cause: `contracts.py` `meaning` no explicaba la relación con `egg_origin`.
- Fix: `meaning` ampliado (internal ⇒ lote interno compatible misma empresa/generación; purchased ⇒ no exige lote interno). Docs 03–10 regenerados; `05_HATCHERY` propaga el texto. `generation`/`egg_origin` se mantienen distintos (SPEC 009).
- Resultado: **FIXED** (verificado en 05_HATCHERY_TEMPLATE_CONTRACT.md).

## 2. UAT disposition (reutilización §16 + gaps)

| Bloque | Cobertura (suites vigentes) | Gap añadido | Estado |
|---|---|---|---|
| **UAT-02** negativas/mensajes | `test_cutover_v2_validation.py` (maestros inexistente/inactivo/otra empresa/otra BU, PARENT_MISMATCH, fase, lote duplicado, opening existente, orden fechas, consistencia), `test_cutover_v2_contracts.py` (obligatorio vacío, N/A en obligatorio, tipos/decimal/entero/negativo/fecha/enum, cabecera/Meta/archivo/version/fórmulas), `test_cutover_v2_keyuser_s01_red_*` (mortalidad breeder, egg_origin/generation, eggs_set>received, hatchery v2 rechazada, GENETIC_LINE/BREED codes). Errores con fila/campo/código/mensaje/valor en `/validation` + descarga de errores. | — (cubierto) | PASS (vía regresión) |
| **UAT-03** RBAC/segregación/tenant/BU | `security/test_multitenant_isolation.py`, `test_segregation_r143` (registrador≠aprobador), `_exigir_segregacion` (service), aislamiento por empresa en validación (maestro de otra empresa no resuelve), `require_permission` en routers (403), `test_ga_req_061_cutover_c7_controls/matrix`. | — (cubierto; se verifica en regresión) | PASS (vía regresión) |
| **UAT-04** apply+verify 4 BU | E2E `e2e/proceso-p16-cutover-{grandparent,breeder,hatchery,broiler}.spec.ts` (`flujoPorBu`: crear→plantilla→subir→validar→enviar→aprobar→aplicar→reconciliación→primer evento post-corte→verificación; CUT-GL-02). `test_cutover_v2_apply.py`, `test_ga_req_061_cutover_c4/c5`. | E2E 4 BU `--workers=1` **4 passed** | **PASS** (`07_e2e_cutover_4bu.log`) |
| **UAT-05** auditoría | `audit_accion` (create/apply/FAILED_APPLY) en service; `test_audit_coverage.py`. | — (cubierto) | PASS (vía regresión) |

## 3. Semántica UNKNOWN/0/N/A
Vinculante y cubierta: `test_cutover_v2_red.py::test_red_07_unknown_cero_y_na_se_distinguen` (staging→opening→reconciliación), `test_cutover_v2_contracts.py` (vacío=UNKNOWN, 0=KNOWN, N/A=NOT_APPLICABLE), reconciliación no convierte UNKNOWN en 0.

## 4. Resultados de verificación
- Frontend: `vitest` **577/577** (incl. `CUTOVER-UX-02` y `RC-010`+DATA-01), `tsc -b` PASS, `vite build` PASS — `evidence/01_frontend_tsc.log`, `02_frontend_vitest.log`, `03_frontend_build.log`.
- Backend cutover targeted: **102/102** — `evidence/04_backend_cutover.log`. DATA-01: **2/2** — `evidence/05_backend_data01.log`.
- Backend regresión completa (pre-mutación): **1767 passed · 0 failed · 49 skipped** (head BD/código `f1a2b3c4d5e6`) — `evidence/06b_backend_full_pre_mutation_rerun.log`. (La 1ª corrida `06_...` tuvo 1766/1/49; el único fallo `test_r141_tendencia_mortalidad_ignora_cancelados` es un flake de aislamiento preexistente: pasa aislado (1.63s) y el commit de implementación `5f3a698` no toca dashboard/operations/reports/mortalidad (diff solo cutover+frontend+docs). En la re-corrida no reaparece.)
- **E2E 4 BU** (`p16-cutover-{grandparent,breeder,hatchery,broiler}`, `--workers=1`): **4 passed (55.9s)** — ciclo completo por UI con aplicar + primer evento post-corte por unidad (CUT-GL-02 incluido) — `evidence/07_e2e_cutover_4bu.log`.
- **Mutación/sensibilidad** DATA-01 (`templates.py`, tras IMPL SHA `5f3a698`): **2/2 mutaciones DETECTADAS** — S1 (neutralizar condición `and False`) y S2 (anular asignación `corte = None`), ambas → `test_data01_meta_refleja_corte_sin_batch` FAILED; restauración `git restore --source=5f3a698 -- templates.py` con `git status` vacío y **0 diff** vs IMPL SHA; suite de nuevo 2/2 — `evidence/09_sensibilidad_data01.md`.
- Backend regresión completa (post-mutación, árbol = IMPL SHA, 0 diff): **1767 passed · 0 failed · 49 skipped** (head `f1a2b3c4d5e6`) — `evidence/08_backend_full_post_mutation.log`.

## 5. Matriz de trazabilidad (§22)
| Hallazgo/UAT | Spec | Código | Test | E2E | Evidencia | Resultado |
|---|---|---|---|---|---|---|
| CUTOVER-UX-01 | 011 | — | getByRole(name) (suite) | p16 | UAT caps SPEC 010 | NO_FIX/VERIFIED |
| CUTOVER-UX-02 | 011 | CargasInicialesPage.tsx, cutover.service.ts | cutoverV2 UX-02 | p16 (filename) | 02_frontend_vitest | PASS |
| CUTOVER-DATA-01 | 011 | templates.py, cutover.service.ts, CargasInicialesPage.tsx | s011 (2), RC-010 | p16 | 05_backend_data01 | PASS |
| CUTOVER-DOC-01 | 011/009 | contracts.py, docs 03-10 | lineage (counters) | — | 05_HATCHERY | PASS |
| CUTOVER-UAT-02 | 006/009 | — | validation/contracts/keyuser | p16 | 06b_backend_full | PASS |
| CUTOVER-UAT-03 | hardening waves | — | multitenant/segregation/c7 | p16 | 06b_backend_full | PASS |
| CUTOVER-UAT-04 | 006 | — | apply/c4/c5 | p16 4 BU | 07_e2e_cutover_4bu | PASS |
| CUTOVER-UAT-05 | audit | — | audit_coverage | — | 06b_backend_full | PASS |

## 6. Estado
```
REAL_SAP_WRITES=0 · DB_CHANGES=0 · MIGRATION=none
FINDINGS: UX-01 NO_FIX · UX-02 FIXED · DATA-01 FIXED(P2) · DOC-01 FIXED
GATES: frontend(vitest/tsc/build) PASS · cutover 102/102 · DATA-01 2/2
       regresión pre 1767/0/49 · E2E 4 BU 4/4 · sensibilidad 2/2 DETECTADAS · regresión post 1767/0/49
UAT: 02 PASS · 03 PASS · 04 PASS · 05 PASS · P0/P1 abiertos=0 · árbol limpio
FINAL_STATUS=CUTOVER_PROCESS_CERTIFIED
```
