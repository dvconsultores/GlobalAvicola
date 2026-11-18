# 30 · Sensibilidad (mutación) del backend · S1

Fecha: 2026-11-18 · Rama `main` · HEAD `562c346`
Protocolo por mutación: cambio mínimo con `edit_file` → suite objetivo →
restauración con `git restore --source=562c346 -- <archivo>` → `git diff --stat 562c346 -- <archivo>` vacío.

Suite objetivo (una invocación por mutación, `-x` para cortar en el primer fallo):

```
cd backend && bash scripts/run_tests.sh \
  tests/test_uat_s1_corrections.py tests/test_uat_s1_required_data.py \
  tests/test_uat_s1_identity.py tests/test_uat_s1_inspection_trace.py -q -x
```

Línea base sobre `562c346` (sin mutación): **32 passed**.

## Tabla de resultados

| Mut. | archivo · cambio | test(s) que la detectan | veredicto |
|------|------------------|-------------------------|-----------|
| B1 | `app/corrections/service.py` · `_corregir_submovimiento`: `if delta > saldo:` → `if False and delta > saldo:` (la salida por encima del saldo ya no se rechaza) | `test_uat_s1_corrections.py::test_t2_cantidad_por_encima_del_saldo_no_cambia_nada` (201 ≠ 400; la corrección de 999999 quedó registrada) | **DETECTADA** |
| B2 | `app/operations/validators.py` · `validate_contenido_minimo`: RR-20 neutralizada (`if not any(...) and False:`) | `test_uat_s1_required_data.py::test_rr20_pesaje_sin_filas_es_400_en_espanol` (201 ≠ 400) | **DETECTADA** |
| B3 | `app/operations/validators.py` · `validate_contenido_minimo`: RR-23 neutralizada (`if not any(...) and False:`) | `test_uat_s1_required_data.py::test_rr23_alimento_sin_filas_es_400` | **DETECTADA** |
| B4 | `app/operations/validators.py` · `validate_contenido_minimo`: RR-21 neutralizada (`if vaccine_id is None and False:`) | `test_uat_s1_required_data.py::test_rr21_vacunacion_sin_vacuna_es_400` | **DETECTADA** |
| B5 | `app/operations/service.py` · `_unidad_de_la_granja`: `if len(tipos) != 1: return None` → `if len(tipos) < 1: return None` (granja multicadena deja de quedar pendiente) | `test_uat_s1_inspection_trace.py::test_t02_granja_multicadena_nace_pendiente` | **DETECTADA** |
| B6 | `app/operations/service.py` · `get_events`: `patron = lot_code.strip()` (sin escape de `%` y `_`) | `test_uat_s1_identity.py::test_comodin_porcentaje_no_devuelve_todo` | **DETECTADA** |
| B7 | `app/lots/router.py` · `get_lot`: eliminada `await anotar_nombres_de_lotes(db, [lot])` | `test_uat_s1_identity.py::test_detalle_de_lote_trae_nombres` | **DETECTADA** |
| B8 | `app/corrections/service.py` · `_traducir_estado`: `return str(crudo)` (sin `ESTADO_ES`) | `test_uat_s1_corrections.py::test_t7_evento_aprobado_no_es_corregible_y_el_mensaje_es_espanol` | **DETECTADA** |
| B9 | `app/corrections/service.py` · `_corregir_submovimiento`: neutralizado el rechazo `BR-20` de la cantidad de recepción breeder (`if False and ...`) | **1.ª pasada: ninguna** (32 passed → SOBREVIVE) · tras añadir `test_t9_cantidad_de_recepcion_breeder_no_se_corrige_aislada`: ese test | **DETECTADA** (con test nuevo) |

Detalle de B9: la mutación **sobrevivió** a la suite S1 (no había ningún test de corrección sobre
una recepción de reproductoras; la cobertura estaba solo en E2E P18A). Se añadió
`backend/tests/test_uat_s1_corrections.py::test_t9_cantidad_de_recepcion_breeder_no_se_corrige_aislada`
— crea un lote `bird_type="breeder"` por API, registra una `bird_reception` con cuadre
(`received_total=100`, `dead_on_arrival=0`, `rejected_on_arrival=0`), comprueba que
`GET /api/v1/corrections/events/{id}/correctable-fields` **no** ofrece `...quantity` y que un
`POST /api/v1/corrections` directo con `bird_movements[<id>].quantity` responde `400` con el
mensaje en español (`reproductoras` + `cuadre de recepción`), sin cambiar la fila — y con la
mutación B9 re-aplicada el test falla (201 en lugar de 400).

Estado final: `git status --short backend` → solo ` M backend/tests/test_uat_s1_corrections.py`;
los ocho archivos de producción restaurados con `git diff --stat 562c346` vacío.
Suite objetivo tras el test nuevo: **33 passed**.

SENSIBILIDAD_BACKEND=9/9_DETECTADAS · DIFF_VS_IMPL_SHA=0
