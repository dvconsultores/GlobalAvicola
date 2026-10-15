# CUTOVER-INITIAL-BALANCES · 12_TEST_EVIDENCE

Fecha: 2026-10-15 · SPEC 006 · Matriz de pruebas (AC → prueba) y resultados pre-commit. Logs en `evidence/` (saneados, sin DSN).

---

## 1 · Suites

| Suite | Archivo | Pruebas | BD | Resultado | Log |
|---|---|---|---|---|---|
| RED (mandato §34, 9 escenarios) | `backend/tests/test_cutover_v2_red.py` | 9 | sí | **9 failed sobre HEAD `57a421a`** → 9 passed con la implementación | `evidence/red/red_on_head_57a421a.log`, `evidence/green/v2_suites_run2.log` |
| Contratos y parser | `backend/tests/test_cutover_v2_contracts.py` | 33 (4 BU × 2 formatos + paridad ×4 + negativas §V + límites §W) | no | passed | `evidence/green/v2_suites_run2.log` |
| Validación de dominio | `backend/tests/test_cutover_v2_validation.py` | 11 | sí | passed | ídem |
| Apply por BU + negativas de batch | `backend/tests/test_cutover_v2_apply.py` | 9 | sí | passed | ídem |
| Continuidad post-corte + CUT-GL-02 | `backend/tests/test_cutover_v2_continuity.py` | 6 | sí | passed | ídem |
| **Total v2** | | **76** | | **76 passed / 0 failed** (21 s) | `evidence/green/v2_suites_run2.log` |
| GA-REQ-061 C1–C7 (fixture migrada v1→v2, goldens intactos) | `backend/tests/test_ga_req_061_cutover_c*.py` | 39 | sí | 39 passed (+ 9 RED = 48) | `evidence/green/targeted_run2.log` |
| Frontend | `frontend/src/__tests__/r061.cutoverFlow.test.tsx` (4), `cutoverV2.test.tsx` (3) + suite completa | 542 (base 539) | — | **542 passed / 0 failed** · `tsc -b` PASS · `vite build` PASS | `evidence/build/` |
| E2E UI por BU + navegación | `e2e/proceso-p16-cutover-{grandparent,breeder,hatchery,broiler}.spec.ts`, `navigation-consistency.spec.ts` | 4 + 8 | pila local | **12 passed** (1.0 min) | `evidence/e2e/e2e_run2.log`, `evidence/e2e/journals/` |
| Regresión completa backend (pre-commit) | toda la suite | ver §4 | sí | ver §4 | `evidence/regression/backend_full_pre_commit.log` |

Iteraciones previas (documentadas, no ocultas): `targeted_run1.log` (2 fallos de fechas/versión en C2 corregidos en la fixture), `v2_suites_run1.log` (6 fallos: BR-08 exige granja/galpón en recolección/despacho, fechas de fixture, grant de `cutover:create` para la sonda cross-company), `e2e_run1.log` (4 fallos en la sonda CUT-GL-02 por la zona horaria del `datetime-local`; la sonda usa ahora la fecha civil persistida).

## 2 · AC → pruebas

| AC | Pruebas |
|---|---|
| 01–02 | reproducción por UI (`evidence/head-repro/`), `01_LIVE_FAILURE_ROOT_CAUSE` |
| 03 | `git branch --show-current = main` (§5 de `16_…`) |
| 04–07 | `test_red_02_plantilla_por_bu_no_generica`, `test_red_03_campos_especificos_por_bu_presentes`, `test_registry_cerrado_cuatro_contratos_v2` |
| 08–09 | `test_xlsx_positivo_por_bu[4]`, `test_csv_positivo_por_bu[4]`, `test_red_04_csv_se_descarga_y_se_carga_como_xlsx` |
| 10 | `test_red_03…` (Instrucciones por campo) |
| 11 | `test_catalogos_de_la_plantilla_solo_empresa_y_bu`, `test_red_06…` |
| 12 | `test_version_retirada_y_desconocida`, `test_plantilla_de_otra_empresa_otra_bu_y_otra_version`, `test_c2_template_version_no_soportada` |
| 13–15 | `test_vacio_es_unknown_cero_es_known_na_es_not_applicable`, `test_red_07_unknown_cero_y_na_se_distinguen`, `test_unknown_se_propaga_en_reconciliacion_e_informe` |
| 16 | `test_campo_obligatorio_vacio`, `test_na_en_obligatorio_y_na_donde_no_se_admite`, `test_campo_obligatorio_de_incubadora` |
| 17 | `test_maestros_inexistentes_e_inactivos`, `test_maestro_de_otra_empresa_no_resuelve`, `test_c7_red06_master_inactivo_referencia_nueva` |
| 18 | `test_relaciones_padre_hijo`, `test_fase_incompatible_y_metrica_no_aplicable_en_cria`, `test_lote_fuente_de_incubadora` |
| 19–20 | `test_c2_upload_validar_preview`, `test_c2_mismo_checksum_no_duplica`, `test_plantilla_de_otra_empresa_otra_bu_y_otra_version` (staging vacío tras rechazos) |
| 21 | `test_red_01…` (CSV), `test_listado_detalle_errores_y_preview` (CSV + XLSX) |
| 22 | `test_red_06…`, `test_listado_detalle_errores_y_preview`, `cutoverV2.test.tsx` |
| 23–26 | `test_apply_grandparent_destino_por_campo`, `test_apply_breeder_cria_y_produccion`, `test_apply_hatchery_con_lote_fuente_y_na`, `test_apply_broiler_mixto`, `test_red_05…` |
| 27–28 | `test_red_08_registry_cerrado_sin_campos_sin_destino`, `test_lineage_sin_campos_sin_destino_ni_dominio_faltante` |
| 29 | `test_apply_*` (LotPhase, fase real, origen/procedencia), `test_reuso_explicito_de_lote_existente`, `test_ctl01_lote_nativo_reusado_intacto` |
| 30–33 | `test_grandparent_primer_evento_de_su_fase`, `test_breeder_cria_y_produccion`, `test_hatchery_siguiente_paso_de_incubacion`, `test_broiler_mortalidad_alimento_y_peso`, `test_red_09…`, E2E ×4 |
| 34 | `test_unknown_se_propaga…`, `test_c5_golden_saldo_y_lifetime`, `test_c5_unknown_no_es_cero` |
| 35 | `test_cut_gl_02_rechaza_eventos_hasta_el_corte`, `test_red_09…`, E2E ×4 (sonda) |
| 36 | `test_idempotencia_doble_apply_y_segregacion`, `test_c2_mismo_checksum_no_duplica` |
| 37 | `test_idempotencia_doble_apply_y_segregacion`, `test_c4_apply_solo_desde_approved_y_una_vez`, `test_c7_red10_apply_concurrente_exactamente_uno` |
| 38 | `test_idempotencia_doble_apply_y_segregacion`, suite C3 |
| 39 | `test_multiempresa_bu_deshabilitada_y_sin_concesion`, `test_c7_red01/02/03` |
| 40 | `test_multiempresa_bu_deshabilitada_y_sin_concesion`, `test_c7_red04/05` |
| 41 | `test_ctl06_rbac_existente_intacto`, `test_rbac.py` (regresión completa) |
| 42–44 | E2E ×4: `scrollWidth − clientWidth ≤ 1` a 360/390/1280 px; `navigation-consistency` AC16–18 |
| 45 | `r061.cutoverFlow.test.tsx::AC84/85` (paridad ES/EN incl. `steps` y `fields`) |
| 46–49 | §1 (backend dirigido 76 + 48 · frontend 542 · tsc · build) |
| 50–51 | E2E 4/4 · 8 caminos + 4 paridades |
| 52–53 | `13_MUTATION_EVIDENCE.md` |
| 54–55 | §4 · E2E 12/12 |
| 56–58 | `15_RUNTIME_VERIFICATION.md`, `14_LOCAL_CERTIFICATION.md §0` |

## 3 · Negativas del mandato (§33) → prueba

template wrong BU/company/version → `test_plantilla_de_otra_bu_rechazada`, `test_plantilla_de_otra_empresa_otra_bu_y_otra_version` · missing/duplicate/unknown headers → `test_cabeceras_duplicadas_desconocidas_y_faltantes` · invalid/inactive/cross-company master → `test_maestros_inexistentes_e_inactivos`, `test_maestro_de_otra_empresa_no_resuelve` · wrong house/farm → `test_relaciones_padre_hijo` · invalid phase → `test_fase_incompatible…` · duplicate lot / existing opening → `test_lote_duplicado_existente_y_opening_existente` · negative values / invalid date / decimals where integer / text where number → `test_tipos_invalidos_por_celda` · corrupt XLSX/CSV / empty file / fake extension / MIME → `test_archivo_vacio`, `test_xlsx_corrupto_y_extension_falsa`, `test_csv_corrupto`, `test_extension_no_soportada_y_macros` · too large / too many rows / too many columns → `test_archivo_demasiado_grande`, `test_demasiadas_filas`, `test_demasiadas_columnas` · double upload / double apply / creator approves / BU disabled / no grant → `test_idempotencia_doble_apply_y_segregacion`, `test_multiempresa_bu_deshabilitada_y_sin_concesion` · formulas / macros → `test_formulas_rechazadas_sin_evaluar`, `test_extension_no_soportada_y_macros` · N/A on required → `test_na_en_obligatorio_y_na_donde_no_se_admite`.

## 4 · Regresión completa backend (pre-commit)

| Gate | Resultado |
|---|---|
| `backend/scripts/run_tests.sh` (suite completa, pgserver aislado, migración `e0f1a2b3c4d5` aplicada, 65 tablas) | **1706 passed / 0 failed / 49 skipped** en 22:54 min (base SPEC 005: 1630 / 0 / 49; +76 pruebas v2) |
| Guardas del arnés | cabeza Alembic `e0f1a2b3c4d5` (pines de `test_company_catalog` y `test_population_invariant`), 240 rutas `/api` (236 + listado, detalle, preview, errores), 65 tablas (+`hatchery_openings`), clasificación de datos completa, sin fechas ISO literales en los tests nuevos (`tests.time_reference`) |

`BACKEND_FULL_FAILED = 0` · log: `evidence/regression/backend_full_pre_commit.log` (JWT efímeros y DSN redactados).
