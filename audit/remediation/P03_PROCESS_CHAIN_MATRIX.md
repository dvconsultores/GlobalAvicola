# `P-03` · REPRODUCTORAS — CRÍA — CADENA COMPLETA

`spec.md §4.4` + `§4.5` · `docs/02 §3.5` · 2026-09-06

`audit/06_PROCESS_COVERAGE.md` describe `P-03` como «idéntico a `P-01` sin
`grandparent_import`». Es cierto para la cadena operativa, y **no** para lo normativo: `P-03`
se rige por `§4.5`, que exige un paso que `§4.4` no pide.

```
§4.4  (P-01)  · sin alertas por desviación
§4.5  (P-03)  · «Alertas por desviaciones (peso fuera de curva estándar, mortalidad > umbral)»
§4.8  (P-06)  · sin alertas por desviación
```

Ese renglón —y solo ese— era la diferencia entre `P-01`, certificado, y `P-03`, bloqueado.

---

## 1. La cadena operativa

| # | Paso | Actor | Entrada | Salida | Requisito | Estado |
|:--:|---|---|---|---|---|:--:|
| 1 | `farm_inspection` | operario | granja, galpón | parámetros de bioseguridad | `§4.4` | **PASS** |
| 2 | `transport_inspection` | operario | transporte | higiene del vehículo | `§4.4` | **PASS** |
| 3 | `bird_reception` | operario | OC de SAP, cantidad | aves en galpón | `§4.4` · `BR-18` | **PASS** — `GA-TD-014` |
| 4 | `bird_distribution` | operario | aves recibidas | reparto por galpón | `§4.4` | **PASS** |
| 5 | `feed_registration` | operario | kg y tipo | consumo del lote | `§4.4` | **PASS** |
| 6 | `weight_recording` | operario | muestra y peso medio | peso del lote | `§4.4` | **PASS** |
| 7 | `mortality_recording` | operario | bajas y causa | saldo actualizado | `§4.4` · `BR-01` | **PASS** — `P0-1` |
| 8 | `cull_recording` | operario | descartes y causa | saldo actualizado | `§4.4` | **PASS** |
| 9 | `vaccination` | operario | vacuna | registro sanitario | `§4.4` | **PASS** |
| 10 | `medication` | operario | medicamento | registro sanitario | `§4.4` | **PASS** |
| 11 | `bird_exit` | operario | aves y destino | salida del lote | `§4.4` | **PASS** |

## 2. El paso normativo de `§4.5`

| # | Paso | Actor | Entrada | Salida | Requisito | Estado |
|:--:|---|---|---|---|---|:--:|
| 12 | Alerta por **mortalidad sobre umbral** | sistema | `mortality_recording` | `high_mortality` | `§4.5` | **PASS** — ya existía |
| 13 | Alerta por **peso fuera de curva estándar** | sistema | `weight_recording` | `weight_deviation` | `§4.5` · `GA-REQ-037` | **PASS** — `GA-REM-037` |

El paso 13 no estaba «sin implementar»: era **inimplementable**. El generador de alertas
producía `high_mortality`, `temperature_out_of_range` y `humidity_out_of_range`, y no podía
producir la cuarta porque la *curva estándar* no existía como dato en ninguna parte del
producto —ni tabla, ni versión, ni referencia desde el lote—.

Cualquier umbral que el software hubiera aplicado habría sido inventado. Por eso el bloqueo se
elevó como decisión de propietario en lugar de resolverse en código, y por eso `OD-06` es la
pieza que lo desbloquea:

```
OD-06 = RESOLVED (2026-09-06)
  · curvas configurables por línea genética, versionadas
  · edad en días, rango del mínimo al máximo de la tabla cargada
  · interpolación lineal entre puntos, sin extrapolar fuera de la tabla
  · SIN tolerancia global: el rango sale de la tabla y de ningún otro sitio
```

## 3. Lo que la cadena necesita antes del paso 13

Cinco capacidades que no existían, ninguna de ellas una alerta:

| Capacidad | Dónde | Estado previo |
|---|---|:--:|
| Versión de curva por línea genética | `genetic_weight_curves` | **inexistente** |
| Puntos de la tabla | `genetic_weight_curve_points` | **inexistente** |
| Referencia del lote a una **versión** | `lots.weight_curve_id` | **inexistente** |
| Motor de evaluación | `app/operations/weight_curve.py` | **inexistente** |
| Tipo de alerta `weight_deviation` | `_alertas_de_peso` | **inexistente** |

Seis ya existían y no se rehicieron: `GeneticLine` como maestro con pantalla (`GA-REM-033`),
`Lot.genetic_line_id`, `OperationalAlert`, el generador de alertas, `age_days` (`R-47`) y el
peso medio en `BirdMovement.avg_weight`. El detalle está en `P03_GENETIC_CURVE_MODEL_MATRIX.md`.

## 4. Aislamiento entre empresas

| # | Comprobación | Control | Tratamiento | Estado |
|:--:|---|---|---|:--:|
| 14 | Las curvas heredan la tenencia de su línea | operador lee la curva de su empresa → `200` | el mismo operador lee la de otra → `404` | **PASS** |

El sujeto negativo es un operador con empresa propia, **no** el Super Administrador: su
exención de tenencia haría que la prueba pasara sin comprobar nada.

## 5. Recuento

```
14 pasos · PASS 14 · FAIL 0
   11 de la cadena operativa (§4.4)
    2 de alertas normativas   (§4.5)
    1 de tenencia             (spec.md §8.14)
```

## 6. Evidencia

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Cadena `API_E2E` | `e2e/proceso-p03-reproductoras-cria.spec.ts` | 5/5 |
| Modelo y carga | `backend/tests/test_genetic_curves.py` | 16/16 |
| Motor | `backend/tests/test_weight_curve_evaluation.py` | 14/14 |
| Alerta | `backend/tests/test_weight_alert.py` | 8/8 |
