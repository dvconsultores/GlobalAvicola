# 31 · Sensibilidad (mutación) FRONTEND — post-implementación 562c346

**Fecha:** 2026-11-10
**Rama / HEAD de referencia:** `main` · `562c346` (commit de implementación UAT S1)
**Alcance:** `frontend/` — 10 mutaciones mínimas de producción (F1…F10).
**Precondición verificada:** `git rev-parse --short HEAD` = `562c346`; `git status --short frontend` **vacío** al inicio.
**Método:** por mutación → [1] edición mínima con reemplazo exacto → [2] `vitest run <suites objetivo>` →
[3] registro DETECTADA/SOBREVIVE → [4] `git restore --source=562c346 -- <archivo>` + verificación
`git diff --stat 562c346 -- <archivo>` vacío antes de la siguiente. Sin `add/commit/push/checkout/stash`.
**Toolchain:** Node `v24.13.0`, `vitest 4.1.11`, jsdom.

**Baseline (antes y después, idéntico):** 14 archivos · **62/62 tests verdes**.

## Tabla de resultados

| Mut. | archivo · cambio aplicado (semántica) | test(s) que la DETECTAN | fallos observados | veredicto |
|------|----------------------------------------|--------------------------|-------------------|-----------|
| **F1** | `src/pages/lots/LotListPage.tsx` · `unidadesDisponibles = BIRD_TYPE_KEYS.filter(k => hasUnit(user,k))` → `BIRD_TYPE_KEYS` (todas las unidades/pestañas siempre visibles) | `src/pages/lots/__tests__/uatS1.lotTabs.test.tsx` · «unidad no concedida no ofrece pestaña» (`lot-filter-grandparent`, `-broiler`, `-hatchery`) | 1 failed / 4 passed (1 archivo) | **DETECTADA** |
| **F2** | `src/components/Toast.tsx` · contenedor `toast-container` renderizado inline (`{…&& (<div …>)}`) en vez de `createPortal(…, document.body)` | `src/components/__tests__/uatS1.toastPortal.test.tsx` · «fuera del árbol de la app / `parentElement === document.body`» | 1 failed / 0 passed | **DETECTADA** |
| **F3** | `src/pages/reports/ReportsPage.tsx` · `useState<number \| null>(null)` → `useState<number \| null>(2)` (lote fijo inicial, no espera al primer lote visible) | `src/pages/reports/__tests__/uatS1.reports.test.tsx` · estado «Sin lotes disponibles» + no pedir KPIs/serie sin lote | 2 failed / 3 passed | **DETECTADA** |
| **F4** | `src/pages/operations/operationPayload.ts` · `validarObligatoriosDeOperacion`: `if (total <= 0) return 'operations.quantityRequired'` → `return null` (regla cantidad>0 mortalidad/descarte/salida neutralizada) | `src/pages/operations/__tests__/uatS1.requiredRules.test.ts` + `…/uatS1.requiredFields.test.tsx` · `mortality`/`cull_recording`/`bird_exit` sin cantidad | 4 failed / 10 passed (2 archivos) | **DETECTADA** |
| **F5** | `src/utils/correctionFields.ts` · `describirCampoCorregido` devuelve siempre el `fieldName` crudo (`return String(fieldName ?? '')` como primera sentencia) | `src/utils/__tests__/correctionFields.test.ts` + `src/pages/review/__tests__/uatS1.correctionForm.test.tsx` + `…/uatS1.reviewDetailCorrections.test.tsx` · «campo traducido» (`Peso promedio`, sin `bird_movements[`) | 5 failed / 6 passed (3 archivos) | **DETECTADA** |
| **F6** | `src/hooks/useDebouncedValue.ts` · `setTimeout(…, delayMs)` → `setTimeout(…, 0)` (sin espera real) | `src/hooks/__tests__/useDebouncedValue.test.ts` · «aún no pasaron 400 ms, el valor sigue siendo el previo» | 1 failed / 10 passed (sólo falla la suite unitaria) | **DETECTADA** |
| **F7** | `src/pages/approvals/ApprovalPanel.tsx` · diálogo de rechazo sin `children`: se elimina `<textarea data-testid="reject-reason">` + ayuda + aviso de longitud | `src/pages/approvals/__tests__/uatS1.rejectReason.test.tsx` · el campo de motivo dentro del diálogo y su validación | 3 failed / 0 passed | **DETECTADA** |
| **F8** | `src/pages/review/ReviewDetail.tsx` · botón «Corregir» genérico sin `&& CORREGIBLES.includes(event.status)` (visible con permiso en cualquier estado) | `src/pages/review/__tests__/uatS1.reviewDetailCorrections.test.tsx` · «estado `approved` no ofrece enlace Corregir» | 1 failed / 2 passed | **DETECTADA** |
| **F9** | `src/components/Toast.tsx` · `textoDeItem`: `type === 'missing'` devuelve «Valor no válido…» en lugar de «Falta el dato obligatorio…» | `src/components/__tests__/f4.toastSpanishDetail.test.tsx` + `src/components/__tests__/f01.getErrorMessage.test.ts` · `missing` sin/con campo → «Falta (el) dato obligatorio» | 3 failed / 9 passed (2 archivos) | **DETECTADA** |
| **F10** | `src/pages/operations/OperationListPage.tsx` · filtro de Historial `params.lot_code = lotCodeDebounced` → `params.lot_id = …` (vuelve a enviar id numérico) | `src/pages/operations/__tests__/f4.historyLotCodeFilter.test.tsx` · petición a `/operations` con `lot_code` | 2 failed / 1 passed | **DETECTADA** |

**Total: 10/10 DETECTADAS · 0 SOBREVIVEN.** No fue necesario añadir tests nuevos (protocolo de supervivientes no activado).

## Restauración y estado final

Todas las mutaciones fueron revertidas con `git restore --source=562c346 -- <archivo>` y verificadas una a una
(`git diff --stat 562c346 -- <archivo>` vacío antes de la mutación siguiente).

```
$ git diff --stat 562c346 -- frontend/src
(sin salida)                      # diff de producción vs 562c346 = 0 archivos, 0 líneas

$ git status --short
 M audit/ga-uat-users-s2-01-2026-11-01/evidence/04_after_e2e.json   # pre-existente, ajeno
 M backend/tests/test_uat_s1_corrections.py                          # pre-existente, NO tocado
?? audit/ga-uat-breeder-cria-s1-2026-11-10/                         # pre-existente
?? screenshots/                                                     # pre-existente
```

No se añadieron tests nuevos ⇒ `git diff --stat 562c346 -- frontend/src` sólo podría contener tests nuevos; está
en cero, luego producción = 0 y tests nuevos = 0.

**Baseline final (suites objetivo, mismo conjunto que al inicio):**
`Test Files 14 passed (14) · Tests 62 passed (62)`.

## Observaciones (calidad de la red de seguridad)

- **F6 — sensibilidad concentrada:** sólo `useDebouncedValue.test.ts` detecta el cambio de retardo. Las suites de
  integración `f4.lotFilterDebounce.test.tsx` y `f4.historyLotCodeFilter.test.tsx` **no** fallan con retardo 0
  porque verifican *coalescencia de la ráfaga* y *valor final enviado* (los 3 `fireEvent.change` síncronos se
  agrupan igual con `setTimeout(…,0)`), no la **duración** del retardo. Cobertura funcional correcta; la
  granularidad temporal queda anclada únicamente en el test unitario. Mutación **detectada**, sin acción requerida.
- **F3 — doble red:** la mutación la detectan 2 tests (estado vacío sin lotes + ausencia de petición de KPIs),
  por lo que el comportamiento «no lote fijo / elegir primer lote visible» está bien protegido.
- **F4 / F5 / F9** afectan a utilidades compartidas: cada una hace fallar **2–3 suites distintas**, lo que
  confirma que las reglas están cubiertas tanto a nivel unitario como de integración de pantalla.
- Resto de mutaciones (F1, F2, F7, F8, F10): la suite objetivo designada las detecta de forma directa y
  específica (1–3 tests).

SENSIBILIDAD_FRONTEND=10/10_DETECTADAS · DIFF_PRODUCCION_VS_IMPL_SHA=0
