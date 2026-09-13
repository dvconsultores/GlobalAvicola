# R-210 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 `frontend/src/pages/operations/__tests__/r210.weightUnit.test.tsx` (jsdom)

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R210-01 · etiquetas de peso en gramos (ES)` | montar `weight_recording`, `bird_transfer`, `bird_exit`, `lot_closure`, `grandparent_import` | todos los rótulos contienen «(g)» — HEAD: fallbacks «(kg)» en algunos |
| `AC-R210-02 · step coherente en gramos` | inspeccionar inputs de peso | `step` ≠ `0.001` — HEAD: `0.001` |
| `AC-R210-03 · serialización sin conversión` | guardar pesaje 2150 | `payload.bird_movements[i].avg_weight == 2150` — HEAD: rojo si algún camino convierte |
| `AC-R210-04 · sin «(kg)» en recursos` | leer `translation.json` ES/EN | ninguna clave de peso contiene «kg» |

### 1.2 Control backend

`backend/tests/test_r210_weight_evaluation_grams.py`: pesaje 2150 con curva que espera ~2100 ⇒ estado positivo/`within` (verde en HEAD; guarda de no-regresión).

Ejecución: `npx vitest run …/r210.*` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

Runtime/local UI. Lote de prueba con curva.

| Caso | Pasos | Esperado |
|---|---|---|
| R210-RT-01 | pesaje por UI a 390×844 y escritorio | etiqueta «(g)»; guardado 201 |
| R210-RT-02 | ver evaluación de peso del evento | dentro de banda (curva) |
| R210-RT-03 | detalle de operación | peso mostrado en g |

Artefactos: `evidence/r210/runtime-{red,c3}.json` + capturas.

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R210-01 | Confirmación del propietario: «el pesaje se captura en gramos» (acta) | Respuesta registrada (C-01) |
| UAT-R210-02 (opcional) | Registrar pesaje ~2150 g y ver evaluación en banda | Coherente con la curva |

Criterio: C-01 registrada; caso 2 informativo.
