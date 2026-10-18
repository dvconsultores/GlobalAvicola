# 07 · Evidencia de pruebas — Revisión QA 2026-10-17

**Documento**: suites ejecutadas, qué cubre cada una y qué se puede afirmar con la evidencia disponible
**Fecha**: 2026-10-18 · **Baseline de referencia**: `83c9cd8` · **SHA de implementación**: `{{IMPL_SHA}}`
**Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md`
**Carácter**: evidencia de pruebas automatizadas. **No** sustituye la verificación en runtime (`08_RUNTIME_VERIFICATION.md`)

Regla de la ronda: **ningún test se redujo, relajó ni eliminó para obtener verde.** Los ficheros de prueba
existentes que se tocaron solo cambiaron de rótulo esperado (`gaFe04.mastersGates.test.tsx`: «Eliminar» → «Desactivar»),
porque el texto visible de la acción cambió con QA-002. Las suites nuevas se añaden como ficheros completos.

**Sin reducción de tests:** 1731 → 1739 (+8), 542 → 557 (+15); ningún test existente eliminado ni marcado `skip`.

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
| Frontend — cifra certificada final | `npx vitest run` | **96 archivos · 557 pruebas PASS · tsc rc 0 · build rc 0** (Node v24.13.0) | `evidence/07_frontend_regression.log` |
| Sensibilidad | mutaciones S1/S5/S6/S7/S8 (plan.md §11) | **`{{SENSITIVITY}}`** | a añadir por el orquestador (T19) |

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

`{{SENSITIVITY}}`

Las mutaciones previstas en `plan.md` §11 son:

| Mutación | Qué debe ocurrir | Resultado |
|---|---|---|
| **S1** — permitir OC de otra cadena (desactivar BR-23) | `test_br23_sap_reference_business_unit.py` en ROJO | `{{SENSITIVITY}}` |
| **S5** — desactivar la segregación BR-14 | `test_segregation_r143` g01-g06 en ROJO (ya cubierta) | `{{SENSITIVITY}}` |
| **S6** — ocultar el filtro de empresa | pruebas de alcance en ROJO | `{{SENSITIVITY}}` |
| **S7** — reintroducir el bucle de revisión (quitar la memoización de `useCan`) | `qaYolinel.red.test.tsx` (QA-017) en ROJO | `{{SENSITIVITY}}` |
| **S8** — volver a etiquetar una columna de maestro con `common.edit` | guardián de `qaYolinel.red.test.tsx` / `qaYolinel.mastersList.test.tsx` en ROJO | `{{SENSITIVITY}}` |

Restauración obligatoria tras cada mutación y re-verificación del diff (`FINAL_DIFF=0`) antes de declarar el cierre.

---

## 4. Lo que estas suites NO prueban

| No cubierto | Motivo | Dónde se atiende |
|---|---|---|
| Comportamiento en UAT con datos reales | Base no alcanzable desde la estación | `08_RUNTIME_VERIFICATION.md` (checklist manual) |
| Carga del dataset QA-DEMO-V1 | Sigue sin cargarse en runtime (`BLOCKED_EXTERNAL`) | runbook `audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md` |
| Integración SAP real | 0 llamadas SAP por mandato | `SAP_PARA_QA.md` (cadena documentada; SAP real `PENDING 2026-10-20`) |
| Filtro por planta de incubación | Brecha funcional: no existe `hatchery_id` en endpoints | `05_FIX_PLAN.md` §3 · `09_RESPONSE_TO_QA.md` |
