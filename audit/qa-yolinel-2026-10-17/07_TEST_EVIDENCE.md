# 07 · Evidencia de pruebas — Revisión QA 2026-10-17

**Documento**: suites ejecutadas, qué cubre cada una y qué se puede afirmar con la evidencia disponible
**Fecha**: 2026-10-18 · **Baseline de referencia**: `83c9cd8` · **SHA de implementación**: `dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124` (IMPL) · **refuerzo de pruebas guardianas**: `9390afcad3ca57dcea17d8065054978abe1a0720` (IMPL-2)
**Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md`
**Carácter**: evidencia de pruebas automatizadas. **No** sustituye la verificación en runtime (`08_RUNTIME_VERIFICATION.md`)

Regla de la ronda: **ningún test se redujo, relajó ni eliminó para obtener verde.** Los ficheros de prueba
existentes que se tocaron solo cambiaron de rótulo esperado (`gaFe04.mastersGates.test.tsx`: «Eliminar» → «Desactivar»),
porque el texto visible de la acción cambió con QA-002. Las suites nuevas se añaden como ficheros completos.

**Sin reducción de tests:** 1731 → 1739 (+8), 542 → 557 (+15); ningún test existente eliminado ni marcado `skip`.
Tras el refuerzo **IMPL-2** (`9390afc`) el frontend pasa a **576 pruebas PASS** (`qaYolinel.red.test.tsx` 4 → 23 casos, +19):
cuatro pruebas guardianas **añadidas** para cerrar dos huecos de cobertura detectados por la sensibilidad (§3), no una
relajación. Backend sin cambios en IMPL-2.

---

## 1. Suites por hallazgo (RED → GREEN)

| ID | Comportamiento que fija la prueba | Archivo | Pruebas | Estado |
|---|---|---|---|---|
| **QA-007** | BR-23: cadena de la OC conocida ≠ cadena del lote ⇒ `400`; cadena desconocida ⇒ se acepta; conflicto entre centros ⇒ no derivable; `business_unit` en `/sap/references` no altera la consulta | `backend/tests/test_br23_sap_reference_business_unit.py` | 5 | **GREEN** |
| **QA-007** | El selector de OC pide `business_unit=<cadena del lote>`, espera al lote y rotula «sin cadena» | `frontend/src/pages/operations/__tests__/qaYolinel.sapOrderByUnit.test.tsx` | 3 | **GREEN** |
| **QA-013** | Guardián: ninguna cabecera de dato usa una clave de acción (`common.edit`/`common.save`) | `frontend/src/__tests__/qaYolinel.red.test.tsx` | (incluida en las 4) | **GREEN** |
| **QA-013 / QA-012 / QA-002** | Maestros: etiquetas propias, columna del padre con nombre, Estado, Desactivar/Reactivar por fila | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` | 3 | **GREEN** |
| **QA-017** | La carga inicial del Centro de Revisión se estabiliza en **1** `GET /review/pending` (sin bucle) | `frontend/src/__tests__/qaYolinel.red.test.tsx` | (incluida en las 4) | **GREEN** |
| **QA-016** | El `input type=date` de `event_date` lleva `max` = hoy (`YYYY-MM-DD`) | `frontend/src/__tests__/qaYolinel.red.test.tsx` | (incluida en las 4) | **GREEN** |
| **QA-014 / QA-018** | `/lots` anota `farm_name`/`house_name`; `/operations` y `/review/pending` anotan `lot_code`/`farm_name`/`registered_by_name` | `backend/tests/test_qa_yolinel_list_enrichment.py` | 3 | **GREEN** |
| **QA-014 / QA-015 / QA-018** | Lotes, Historial y Mis pendientes muestran granja/lote/registrador y envían `farm_id` al servidor | `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` | 3 | **GREEN** |
| **QA-014 / QA-015 / QA-018** | Centro de Revisión y Aprobaciones: columnas de contexto y filtro de granja | `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` | 2 | **GREEN** |
| **QA-002** (ajuste) | El diálogo de baja de maestros dice «Desactivar», no «Eliminar» | `frontend/src/pages/masters/__tests__/gaFe04.mastersGates.test.tsx` | (suite preexistente, rótulo corregido) | **GREEN** |

Total de pruebas nuevas: **20** (5 backend + 15 frontend) en **7** archivos.

---

## 2. Tabla de ejecuciones

| Ámbito | Comando | Resultado | Evidencia |
|---|---|---|---|
| Backend — acotado a los hallazgos | `backend/scripts/run_tests.sh tests/test_qa_yolinel_list_enrichment.py tests/test_br23_sap_reference_business_unit.py tests/test_operations.py tests/test_review.py tests/test_r197_review_queue_contract.py tests/test_lot_row_scope.py tests/test_lots_bu_enforcement.py tests/test_lot_start_date.py tests/test_purchase_order_receipt.py tests/test_sap.py tests/test_r208_batch_approval_authority.py tests/test_segregation_r143.py` | **118 passed** (1 min 42 s) | `evidence/07_backend_targeted.log` |
| Frontend — regresión completa | `npx vitest run` | **96 archivos · 557 pruebas PASS · 0 fallos** | `evidence/07_frontend_regression.log` |
| Frontend — typecheck | `npx tsc -b` | **`tsc_rc=0`** (sin errores) | `evidence/07_frontend_regression.log` |
| Frontend — build | `npm run build` (`vite build`) | **`build_rc=0`** — «✓ built in 1.16s» | `evidence/07_frontend_regression.log` |
| Backend — regresión completa | `backend/scripts/run_tests.sh` | **1739 passed · 0 failed · 49 skipped (22 min 26 s)** | `evidence/07_backend_full.log` |
| Frontend — cifra certificada final | `npx vitest run` | **96 archivos · 557 pruebas PASS · tsc rc 0 · build rc 0** (Node v24.13.0) — **pre-mutación**; con IMPL-2 (`qaYolinel.red.test.tsx` 4 → 23 casos, +19) el total es **96 archivos · 576 pruebas PASS · tsc rc 0 · build rc 0** | `evidence/07_frontend_regression.log` · `evidence/07_frontend_regression_post_mutation.log` |
| Sensibilidad | mutaciones S1/S5/S6/S7/S8 (plan.md §11) | **5/5 DETECTED** (S7 y S8 tras el refuerzo IMPL-2) | `evidence/12_sensitivity_backend.log` · `evidence/12_sensitivity_frontend.log` |
| Backend — regresión post-mutación | `backend/scripts/run_tests.sh` | **1739 passed · 0 failed · 49 skipped (23 min 17 s; idéntica a la pre-mutación)** | `evidence/07_backend_full_post_mutation.log` |
| Frontend — regresión post-mutación | `npx vitest run` | **96 archivos · 576 pruebas PASS · tsc rc 0 · build rc 0** | `evidence/07_frontend_regression_post_mutation.log` |

### 2.1 Nota: una primera invocación de la suite acotada falló por una ruta inexistente (`tests/test_lots.py`) y no produjo ejecución; se corrigió la lista de archivos y se regeneró el log, que es el que figura en `evidence/`.

### 2.2 Qué sí queda acreditado con la evidencia existente

- `backend/scripts/run_tests.sh`: **1739 passed · 0 failed · 49 skipped** (22 min 26 s) en la regresión completa
  (`evidence/07_backend_full.log`) ⇒ GREEN backend acreditado.
- `backend/scripts/run_tests.sh` acotado: **118 passed** (1 min 42 s) sobre las suites de los hallazgos y las suites
  de contrato relacionadas (`evidence/07_backend_targeted.log`).
- `npx vitest run`: **96 archivos / 557 pruebas**, todas en verde, incluyendo los 5 archivos nuevos de frontend.
- `npx tsc -b` sin errores y `vite build` correcto ⇒ el tipo de los nuevos campos opcionales
  (`farm_name`, `lot_code`, `registered_by_name`, `business_unit_code`) y las nuevas props de `DataTable`
  (`rowClassName`, `RowAction.visible`) no rompen el contrato del frontend.
- Node usado: `v24.13.0`.

---

## 3. Sensibilidad

**Resultado final: 5/5 DETECTED.** Cinco mutaciones aplicadas sobre el árbol de `dbd6122`
(`dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124`); cada una se revirtió con
`git restore --source=<SHA> -- <archivo>` y se verificó `diff` final **0** antes de la siguiente.
Logs: `evidence/12_sensitivity_backend.log` (S1, S5) y `evidence/12_sensitivity_frontend.log` (S6, S7, S8).

| ID | Mutación aplicada | Test objetivo | Resultado | Restaurado desde |
|---|---|---|---|---|
| **S1** | BR-23 desactivada: `backend/app/operations/validators.py:1081` → `if True` | `backend/tests/test_br23_sap_reference_business_unit.py` | **DETECTED** — 1 failed / 4 passed | `dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124` |
| **S5** | BR-14 desactivada: `backend/app/review/service.py:94` → `return False` | `backend/tests/test_segregation_r143.py` | **DETECTED** — 3 failed / 3 passed (g02, g04, g06) | `dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124` |
| **S6** | Filtro de granja de Lotes eliminado (`LotListPage.tsx`, select `lot-filter-farm`) — ver nota de interpretación | `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` | **DETECTED** — 1 failed / 2 passed | `dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124` |
| **S7** | `useCan` sin `useCallback` (identidad de función nueva en cada render) | `frontend/src/__tests__/qaYolinel.red.test.tsx` + `src/pages/review` | **PRIMERA CORRIDA: NOT_DETECTED** (18 passed) ⇒ **DETECTED** tras IMPL-2: 1 failed / 22 passed | `9390afcad3ca57dcea17d8065054978abe1a0720` |
| **S8** | `companies.tax_id` vuelve a rotularse con `common.edit` | guardián de `frontend/src/__tests__/qaYolinel.red.test.tsx` | **PRIMERA CORRIDA: NOT_DETECTED** (el guardián solo cubría farms y houses) ⇒ **DETECTED** tras IMPL-2: 1 failed / 22 passed («/masters/companies: ningún th dice Editar ni Guardar») | `9390afcad3ca57dcea17d8065054978abe1a0720` |

### 3.1 Los dos `NOT_DETECTED` iniciales y el refuerzo IMPL-2

Siete y ocho (S7 y S8) **no** fueron detectadas en la primera pasada. No se relajó ningún test: se concluyó que la
cobertura era **insuficiente** y se reforzó.

- **S7 (bug de identidad de `useCan`).** Quitar el `useCallback` de `useCan` dejó en verde `qaYolinel.red.test.tsx` y
  `src/pages/review` (18 passed). Motivo: el Centro de Revisión ya no depende de la **función** `can` sino del booleano
  `canReadUsers`, así que mutar solo el hook no reintroduce el bucle en esa pantalla. Se añadió una prueba de
  **identidad estable** del hook (misma referencia entre renders sin cambio de dependencias) en `IMPL-2`; re-corrida:
  **1 failed / 22 passed** ⇒ DETECTED.
- **S8 (QA-013 reabierto).** Volver a poner `common.edit` en la columna `tax_id` de Empresas pasó desapercibido porque el
  guardián de rótulos solo enumeraba **farms** y **houses**. En `IMPL-2` el guardián se amplió a **los 20 maestros** de
  `masterEntities`; re-corrida: **1 failed / 22 passed**, con el mensaje
  «`/masters/companies`: ningún `th` dice Editar ni Guardar» ⇒ DETECTED.

Efecto neto: dos huecos de cobertura **reales** encontrados y cerrados (`qaYolinel.red.test.tsx` 4 → 23 casos, +19; total frontend 557 → 576). El
guardián ampliado y la prueba de identidad quedan como protección permanente contra la regresión silenciosa.

### 3.2 Nota de interpretación de S6

`plan.md` §11 describía S6 como «ocultar el filtro de empresa». El filtro de alcance que esta ronda **añade** a los
listados es el de **granja** (`farm_id`), porque el aislamiento por empresa se resuelve **en servidor** y ya está cubierto
por `backend/tests/test_lot_row_scope.py`; un filtro de empresa en la UI no existe ni se añadió. La mutación se aplicó por
tanto al filtro de granja de Lotes y quedó DETECTED. Se deja registrada la interpretación para que el revisor pueda
objetarla.

Restauración obligatoria tras cada mutación y re-verificación del diff (`FINAL_DIFF=0`) antes de declarar el cierre:
cumplido en las cinco (S1, S5, S6 restauradas desde `dbd6122`; S7 y S8 desde `9390afc`).

---

## 4. Lo que estas suites NO prueban

| No cubierto | Motivo | Dónde se atiende |
|---|---|---|
| Comportamiento en UAT con datos reales | Base no alcanzable desde la estación | `08_RUNTIME_VERIFICATION.md` (checklist manual) |
| Carga del dataset QA-DEMO-V1 | Sigue sin cargarse en runtime (`BLOCKED_EXTERNAL`) | runbook `audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md` |
| Integración SAP real | 0 llamadas SAP por mandato | `SAP_PARA_QA.md` (cadena documentada; SAP real `PENDING 2026-10-20`) |
| Filtro por planta de incubación | Brecha funcional: no existe `hatchery_id` en endpoints | `05_FIX_PLAN.md` §3 · `09_RESPONSE_TO_QA.md` |

---

## 5. E2E (2026-10-18)

| Suite | Resultado | Log |
|---|---|---|
| Specs E2E afectados por SPEC 008 (10 archivos) | 64 passed | `evidence/13_e2e_affected_raw.log` |
| Spec E2E nueva SPEC 008 (A lots · B operations · C review sin bucle · D approvals · E maestros Desactivar/Reactivar · F padre de galpón · G BR-23 por API · H selector OC espera lote) | 8 passed | `evidence/13_e2e_spec008_raw.log` |

Nota: la spec C mide el bucle en reposo (producción 1 petición; Vite+StrictMode 2).
