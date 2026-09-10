# `R-169` · INVENTARIO Y CLASIFICACIÓN DE TODA TOLERANCIA «±10 %» SIN FUENTE

**WAVE B · tranche 8 · pre-flight** · 2026-09-10 · hallazgo del tranche 7 (P3, «±10 % del formulario sin fuente») · búsqueda en
`backend/app`, `frontend/src`, `e2e`, `docs`, `specs`, `backend/tests`, `backend/seeds`, `backend/alembic` de `10 %`, `±10`, `0.10`,
`1.10`, `0.90`, `toleran*`, `pctDiff`, `qtyOutOfRange`, `Math.abs(`.

**Corrección de título.** El tranche 7 lo llamó «±10 % de peso». La regla activa compara **cantidad recibida contra cantidad declarada
de la OC**, no pesos. La autoridad de pesos (`OD-06`/`GA-REM-037`) no tiene ningún ±10 % en ninguna capa (backend 0, frontend 0,
`WeightEvaluation.tsx` consume la evaluación del backend). La autoridad de cantidades recibidas contra la OC es `OD-04`/`GA-REM-035`
(`BR-18`: acumulado ≤ ordenado, **sin tolerancia**; entregas parciales **legítimas**).

## 1. Inventario

| # | Fichero:línea / símbolo | Capa | Comportamiento | ¿Visible? | ¿Bloquea guardar? | ¿Alerta? | ¿Colorea UI? | ¿Calcula rango? | ¿Testeado? | ¿Fuente citada? | ¿Activo? | Clasificación |
|---|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| 1 | `frontend/src/pages/operations/OperationFormPage.tsx:384-395` (`sapQtyAlert`) | frontend, envío | si `extra_data.declared_quantity` y \|recibido − declarado\| > 10 % **inyecta un texto «⚠️ ALERTA …»** en `observations` **persistido** | sí (queda en el registro) | no | texto, no `OperationalAlert` | no | sí (umbral) | no | no | **sí** | **ACTIVE_UI_CLASSIFICATION** que escribe un veredicto sin fuente en el dato |
| 2 | `OperationFormPage.tsx:613-614, 743-751` (`pctDiff`, `outOfRange`, `qtyOutOfRange*`) | frontend, formulario | recuadro ámbar «Diferencia superior al 10 %» recibido vs declarado | sí | no | no | sí (ámbar) | sí (umbral) | no | no | **sí** | **ACTIVE_UI_CLASSIFICATION** (presentacional) |
| 3 | `translation.json` es/en `sapQtyAlert`, `qtyOutOfRange`, `qtyOutOfRangeDetail` | i18n | textos de 1 y 2 | — | — | — | — | — | paridad | — | con 1 y 2 | acompaña a 1 y 2 |
| 4 | `frontend/src/data/thermalCurves.ts:93` (`humidityStatus`: ±10 puntos de humedad → «warn») | frontend | banda de aviso de humedad | sí | no | no | sí | sí | no | no | sí | **fuera de `R-169`**: umbral de T°/H° sin fuente = familia `R-147` (`H360-B07`, `AOD-19`), ya registrado |
| 5 | `docs/02-functional-spec.md:473` «Uniformidad: % de aves dentro de ±10 % del peso promedio» | documental (nivel 3) | definición de KPI | — | — | — | — | — | — | nivel 3 | no ejecutado (ola C, `KPI_FORMULA_AND_DATA_SOURCE_MATRIX:70`) | DOCUMENTARY (KPI, ola C) |
| 6 | `e2e/proceso-02-control-produccion-diario.spec.ts:121-136` (mortalidad 10 % > umbral crítico 8 %) | e2e | valor de fixture | — | — | — | — | — | — | umbral 8 % gobernado (`settings`) | fixture | TEST_FIXTURE_ONLY |
| 7 | `seeds/*` «Enrofloxacina 10%» | semilla | nombre de medicamento | — | — | — | — | — | — | — | — | DEAD_TEXT |
| 8 | `backend/app` (validadores, `weight_curve.py`) | backend | **0** tolerancias; los comentarios dicen «sin tolerancia» | — | — | — | — | — | — | `OD-04`, `OD-06` | — | conforme |

## 2. Autoridad

```
recibido vs ordenado ..... OD-04 (RESOLVED) · GA-REM-035 (CERTIFIED) · BR-18: acumulado + nueva ≤ ordenada, SIN tolerancia; entregas parciales legítimas
peso vs rango ............ OD-06 (RESOLVED) · GA-REM-037: min/max de la curva del lote, SIN tolerancia
±10 % del formulario ..... ninguna fuente de nivel 1-4; FUNCTIONAL_COVERAGE_MATRIX CV-F07 lo contaba como «validación ±10 %» (error documental)
```

Las ocurrencias 1 y 2 son una **segunda definición normativa** de «recepción fuera de rango» que contradice `OD-04` en los dos sentidos:
una entrega parcial legítima (−15 %) se marca como anomalía, y un exceso del +5 % se presenta sin aviso aunque el backend lo rechaza
(`BR-18`). No hay autoridad superior que la respalde: **no se consulta al propietario**; se retira.

## 3. Estado y acción

```
R-169 ............ ACTIVE_UI_CLASSIFICATION (2 ocurrencias) · sin efecto backend · sin bloqueo · sin OperationalAlert ·
                   la ocurrencia 1 PERSISTE un veredicto sin fuente en `observations`
severidad ........ P3 → P2 (familia R-147: umbral sin fuente; además contamina un dato persistido)
acción ........... retirar 1 y 2 (y sus textos); conservar la tarjeta informativa de la OC (cantidad declarada, fecha, pesos declarados)
                   SIN umbral; la verdad de cantidades sigue en BR-18 (backend). Spec: GA-REM-035 enmienda A. Prueba: contrato
                   estático del formulario (vitest) + BR-18 intacto (backend).
fuera ............ #4 (R-147/AOD-19) · #5 (ola C) · #6 · #7
```
