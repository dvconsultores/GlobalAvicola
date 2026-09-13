# P1-12-REOPEN · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 Arnés con listener

Los tests de este paquete registran el listener (`register_audit_listeners()` en el `lifespan` del arnés o llamada explícita) — **requisito para que la duplicación sea visible** (hoy `ASGITransport` sin `lifespan` la oculta).

### 1.2 `backend/tests/test_p112_audit_single_producer.py` (nuevo)

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_p112_01_alta_una_fila` | crear evento vía API | `count(created)==1` — HEAD: 2 |
| `test_p112_02_aprobacion_una_fila` | flujo submit→start→complete→approve | 1 `approved`, 0 `corrected` espuria — HEAD: 2 `approved` + `corrected` |
| `test_p112_03_cierre_auditado` | cerrar lote (`close`) | 1 fila de lote con resumen — HEAD: 0 |
| `test_p112_04_usuarios_auditados` | alta/edición/baja usuario | 1 fila cada una — HEAD: 0 |
| `test_p112_05_evidencias_curvas` | subir/borrar evidencia; crear/activar curva | 1 fila cada una — HEAD: 0 |
| `test_p112_06_batch_transicion` | `POST /review/batches` | 1 fila `new_state=pending_review` — HEAD: 0 |

### 1.3 Ajustes de aserciones existentes

`test_edit_cancel_balance.py:393` y `test_audit_coverage.py:171` pasan a ejecutarse con listener y siguen afirmando «exactamente 1» (ahora verdad en runtime).

Ejecución: `bash backend/scripts/run_tests.sh tests/test_p112_audit_single_producer.py` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

| Caso | Acción | Recuento esperado |
|---|---|---|
| RT-01 | alta de evento (API/UI) | 1 `created` |
| RT-02 | ciclo de revisión completo | 1 por acción; 0 espurias |
| RT-03 | cierre + activación + fase | 1 cada una |
| RT-04 | usuario alta/edición | 1 cada una |
| RT-05 | evidencia subir/borrar | 1 cada una |
| RT-06 | curva crear/activar | 1 cada una |
| RT-07 | batch de revisión | 1 transición |
| RT-08 | timeline del evento 1 | sin duplicados (antes 13 para 6 acciones) |

Artefacto: `evidence/p112/runtime-{red,c3}.json` (por acción: acción, entidad, nº filas, muestra).

## 3 · Plan UAT

**No requerida.** Verificación informativa: mostrar la línea de tiempo de un evento antes/después (conteo correcto).
