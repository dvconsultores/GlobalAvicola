# GA-R153 · EVIDENCIA BACKEND

Fecha: 2026-09-12 · Commits: `9651550` (C1) · `47ea484` (C2) · `db8ae21` (C2b) · Baseline previo: `9ad9b26`.

## 1 · Cambios y contrato

| Archivo | Cambio | Contrato que sostiene |
|---|---|---|
| `operations/service.py` | `LOT_OPTIONAL_EVENTS` incluye `GRANDPARENT_IMPORT` (gate 400 «El evento requiere lote» eliminado solo para este tipo) | `OD-25 (B)`: registrar sin lote; legado con lote intacto |
| `operations/service.py` | `exigir_unidad_operativa(..., unidad_directa)`: unidad `grandparent` (del **tipo**, nunca del cuerpo) cuando no hay lote; sin traducción `BR-07` (403 honesto) | fase 2/`R-160` preservada: sin lote no se inventa un «lote inexistente» |
| `operations/service.py` | `cadena_del_plan`: sin lote ⇒ `"grandparent"` para `validate_import_plan` (`BR-22`); con lote ⇒ la del lote | `R-152` intacto (lote pendiente sigue rechazando) |
| `review/service.py` | Hook en `approve()` y en `complete_review()` (nivel único), **misma transacción** tras el reverso | «Aprobar = único acto que crea el lote»; fallo del lote revierte la aprobación |
| `lots/service.py` | `crear_lote_de_importacion_si_procede`: no-op si hay lote o no es importación; lee plan (llegada), ♂/♀ (sexo), evento (granja/galpón); `L-GP-{año}-{nn}`; auditoría con `origin=grandparent_import_approval` | `R-153`/`OD-25 (B)`; **no puebla** |
| `lots/service.py` | `_siguiente_codigo_de_lote_gp` + `_bloquear_secuencia` (lock asesor xact por empresa/año; reintento ≤3 con lock global bajo colisión real de unicidad **global** de `lot_code`) | secuencia sin migración; unicidad global respetada |
| `business_units/classification.py` | Tercer origen de derivación: importación sin lote/clasificación ⇒ cadena `grandparent` (visible a esa cadena; fuera de la bandeja de pendientes) | **prerequisito técnico**: sin él la aprobación era inalcanzable (404) — ver certificación, Obs. 4 |

## 2 · Suite RED → contrato

`backend/tests/test_r153_import_lot_auto.py` — **11 casos**, recolección local correcta; ejecución PG **declarada** (PostgreSQL local no disponible; corre en CI vía `backend/scripts/run_tests.sh`):

- AC04/05 registrar sin lote · AC06-08/12-14 lote canónico · AC16-21 recepción puebla una vez · AC23/26 doble aprobación sin duplicar · AC27 legado sin duplicar · AC28/29 devuelto→aprobado · AC09/10 secuencia · AC31/32 fallo de lote revierte · AC45/46 falla cerrado · **AC58/59** derivación por tipo (visible a la cadena, fuera de bandeja, ajena a otras).

Regresión de vecindad: `test_grandparent_import.py` (documental, saldo 0), `test_population_invariant.py` (`R-130`), `test_pending_classification.py` (fase 6 — sus eventos siguen pendientes: la excepción es **nombrada**), `test_review*` (`P-07`).

## 3 · Verificación local

- `pytest --collect-only` → 11 tests; sintaxis/import OK.
- Los módulos tocados pasan el chequeo de tipos/errores del editor sin hallazgos.
- Diff: 6 archivos backend, **0 migraciones**, 0 endpoints nuevos, 0 permisos nuevos.
