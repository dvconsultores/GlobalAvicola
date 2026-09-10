# `GA-REM-021` · `B02` · MATRIZ DE CONTRATO DE «PESOS EN RANGO» EN LA RECEPCIÓN

**WAVE B · tranche 7 · pre-flight** · 2026-09-10 · `H360-B02` (P2) · fuente `Recomendación central.pdf` §6 (p.9-10) · contrato
existente `GA-REQ-037` · `OD-06` (`RESOLVED` 2026-09-06) · `GA-REM-037` (`CERTIFIED`, enmienda A incluida) · método
`REQUIREMENT_CONFLICT_RESOLUTION §1`.

## 1. Requisito exacto (nivel 2, textual)

§6, validación administrativa: «**Que los pesos estén dentro de rango esperado.**» Captura móvil del mismo §6: «**Peso promedio de
hembras** · **Peso promedio de machos** · **Muestra tomada** · Raza confirmada». Datos SAP de la OC (§6): «Cantidad · Raza/línea
genética · Sexo … Precio · Fecha estimada» — **sin peso**. §13 (engorde) captura «Peso semanal» y, en la salida a planta,
«Peso promedio»; no exige rango en la recepción. `Bases` p.2/12: «Peso de los pollitos/pollos: pesaje de una muestra representativa
para calcular el peso promedio diario» (dato diario, no de recepción). Ninguna fuente del cliente nombra el origen del «rango esperado».

## 2. Segundo gate — ¿qué significa «peso en rango»?

| Candidata | ¿Es `B02`? | Por qué |
|---|:--:|---|
| **Peso promedio por sexo de la muestra pesada al recibir** (g) | **sí** | es lo que §6 captura («Peso promedio de hembras/machos, Muestra tomada») y lo que el modelo persiste (`BirdMovement.avg_weight` por fila sexo/galpón, gramos) |
| peso individual de cada ave | no | §6 habla de «promedio» y «muestra» |
| peso de huevo | no | §11, otro proceso |
| peso semanal / diario | no | `weight_recording`, ya evaluado (`GA-REM-037`) |
| peso reportado por el proveedor vs peso en granja | no | es `H360-B11` → `R-156` (paridad con el legado, nivel 6, `AOD-20`); la reconciliación H360 lo separó de `B02` |

## 3. Traza del referente: ¿contra qué «rango esperado»?

| Candidato | Nivel que lo respalda | Evidencia | ¿Referente de `B02`? |
|---|---|---|---|
| **A. Curva estándar de la línea genética del lote, a la edad del lote el día de la recepción** (`min_weight`/`max_weight`, versión fijada al lote) | **nivel 1** (`OD-06`: «¿de dónde sale la curva estándar que `spec.md §4.5` exige comparar?» → tabla cargada por línea, edad en días, interpolación lineal, sin tolerancia, versionada, lote fijado) · **nivel 3** (`docs/02 §3.12.1` «Peso promedio vs estándar: comparación con curva estándar»; §3.14 «Peso fuera de estándar») · **nivel 4** (`spec.md §4.5` fase de cría de reproductoras — cuya lista de eventos incluye `bird_reception` «al inicio de cría»: «Alertas por desviaciones (peso fuera de curva estándar)») | `RC-07_BUSINESS_DECISION_DOSSIER.md:336-381` · `GA-REM-037 §1, §5, §6` | **sí** |
| B. Peso declarado por el proveedor en la OC / guía | nivel 6 (pantalla legada p.18 `peso_promedio_entrada`; `OperationFormPage.tsx:600-601` lo lee de `extra_data` y solo lo muestra) | `H360-B11` → `R-156` `OWNER_DECISION_REQUIRED` (`AOD-20`): «ninguna fuente de nivel 1-4 lo exige» | no: es otro ítem, pendiente del propietario |
| C. Estándar fijo de peso de pollito de un día | ninguno (0 definiciones en `docs/`, `specs/`, `audit/`; manuales Ross/Cobb no incorporados como requisito, `FUNCTIONAL_BASELINE_V1_1:62`) | — | no: inventarlo está prohibido |

**Corte:** el nivel 2 exige la validación en la recepción de reproductoras pero calla sobre el referente; el silencio desciende a los
niveles 3 y 4, que conocen **un solo** estándar de peso (la curva estándar), y a `OD-06`, decisión del propietario que fija de dónde
sale ese estándar para la fase §4.5, de la que la recepción es el primer evento. **`B02` está gobernado por `GA-REQ-037` + `OD-06`:
SÍ.** La cautela del pre-flight del tranche 6 («necesita fuente normativa del rango … `OWNER_DECISION_REQUIRED`») queda
**desestimada por esta traza**: la fuente existe. La fila `H360-B02` («¿decisión?: no») se confirma. Registro: `RC-11` / `RR-13`.

## 4. Cada semántica, con el nivel que la resuelve

| Semántica | Resuelto por | Resultado |
|---|---|---|
| Proceso / unidad | nivel 2 (§6 reproductoras) · nivel 4 (§4.5) · `PROCESS-06-CERTIFICATION:46` («`GA-REQ-037` no aplica a §4.8») | **`bird_reception` en lotes `breeder`**; engorde, progenitoras e incubadora **N/A** |
| Tipo de medida | nivel 2 + 5 | promedio de muestra por sexo/galpón, `BirdMovement.avg_weight` |
| Unidad de peso | `GA-REM-037 §3` (nivel 4) | **gramos**, sin conversión (`min_weight`/`max_weight` en gramos) |
| Línea genética | `OD-06` · `GA-REM-037 AC07/AC23` | **la del lote** (`Lot.genetic_line_id`), versión de curva **fijada al lote** (`Lot.weight_curve_id`); nunca del cuerpo (`breed_id` de `BirdMovement` es raza, no línea) |
| Fuente de edad | `GA-REM-028` (`age_days` desde `start_date`) · `GA-REM-037` (`service.py:750-753`: edad **el día del evento**) | `age_days = event_date − Lot.start_date`; recepción el día de inicio → 0; anterior al inicio → `NO_REFERENCE` (`event_before_lot_start`) |
| Unidad de edad | `OD-06` | **días** |
| min / target / max | `OD-06` · `GA-REM-037 §5` | de la tabla cargada; `target` no decide |
| Interpolación | `OD-06` · `GA-REM-037 AC12` | lineal entre puntos vecinos, los tres valores, en `app/operations/weight_curve.py` (**un solo motor**) |
| Fuera de la tabla (día 0 sin punto) | `GA-REM-037 §6`, `AC18` | **`NO_REFERENCE` declarado, nunca `WITHIN`**; sin extrapolación |
| Regla dentro / fuera | `GA-REM-037 §5`, `AC16` | `min ≤ peso ≤ max` inclusivo → `WITHIN_STANDARD`; `< min` → `BELOW`; `> max` → `ABOVE` |
| Tolerancia | `OD-06` | **ninguna** |
| Desviación % | `GA-REM-037 §4` («§4.5 no la pide») | **no se añade** |
| Consecuencia de fuera de rango | `GA-REM-037 §5`, `AC20`/`AC21` (nivel 4) · principio nivel 2 p.1 «la app debe capturar la realidad de granja» | **se persiste y se clasifica; se emite `OperationalAlert` (`weight_deviation`)**; **no bloquea** el alta ni la aprobación. §6 pide «validarse» en la administración web: el revisor ve la evaluación (`AC26`) y la alerta y decide («Que el responsable apruebe»); un bloqueo automático de la aprobación no está en ninguna fuente y no se inventa |
| Observabilidad | `GA-REM-037-A AC26`…`AC28` | `GET /operations/{id}/weight-evaluation` **ya acepta cualquier evento** (`router.py:247-266`); el detalle solo lo monta para `weight_recording` (`OperationDetailPage.tsx:163`) |
| Curvas históricas / versionado | `OD-06` · `AC08`/`AC23` | el lote queda fijado a su versión: la reevaluación es determinista; **no se necesita instantánea** |
| Evaluación por sexo | `OD-06` (estándar por línea, sin sexo) · `AC26` («una fila por muestra») | cada fila ♀/♂ se evalúa contra la misma curva del lote; un estándar por sexo sería otra decisión (no solicitada, no inventada) |
| Inquilino / unidad / RBAC | cadena certificada (`R-160`, `B05`, `AC28`) | `POST /operations` y la lectura de evaluación filtran por empresa; alerta con `company_id` del evento |
| Soporte actual | `service.py:586` (`if event_type == WEIGHT_RECORDING`) · `OperationDetailPage.tsx:163` | la recepción **no** se evalúa ni alerta; brecha = la puerta del gancho + el montaje del detalle |

**Escalado:** no se requiere decisión del propietario. `GA-REM-037 §A.4` («no tocar el motor certificado, sus modelos, su migración
o sus alertas») acota la enmienda A (frontend); la extensión de la **puerta** de la alerta a la recepción se autoriza por **enmienda B
de `GA-REM-037`**, sin tocar el motor, los modelos ni la migración.

## 5. Matriz de aplicabilidad por unidad de negocio

| Unidad | `bird_reception` con `avg_weight` | Evaluación | Alerta | Fuente |
|---|---|:--:|:--:|---|
| Reproductoras (`breeder`) | sí | **sí** (motor `GA-REM-037`, curva del lote, edad del día) | **sí** si `BELOW`/`ABOVE` | Rec. §6 · `spec.md §4.5` · `OD-06` |
| Engorde (`broiler`) | sí (`spec.md:213` «peso promedio») | **no** | no | §4.8 sin alertas (`PROCESS-06-CERTIFICATION:46`); §13 sin rango en recepción |
| Progenitoras (`grandparent`) | `grandparent_import` (`R-152`) | no | no | sin fuente |
| Incubadora (`hatchery`) | no recibe aves | N/A | N/A | — |

## 6. Gap, criterios y pruebas

| Gap | Cambio | AC | Prueba |
|---|---|---|---|
| gancho de alerta solo para `weight_recording` | `service.py:586`: también `BIRD_RECEPTION` cuando el lote es `breeder` | `AC-B02-08/09/10/12/18/19` · `GA-REM-037-B AC29/AC30` | `tests/test_reception_weight_range.py` |
| detalle no muestra la evaluación de la recepción | `OperationDetailPage.tsx:163`: montar `WeightEvaluation` también para `bird_reception` | `AC-B02-21` · `GA-REM-037-B AC31` | inspección + `tsc` + `vitest` de catálogo (sin cambio) |
| ningún test de recepción afirma nada sobre peso | nuevas pruebas con curva de fixture (punto en día 0, día 10; curva que empieza en día 7) | `AC-B02-01…21` | ídem |

## 7. Frontera

Fuera: `R-156` (`AOD-20`); desviación %; estándar por sexo; instantánea de curva; bloqueo de aprobación; KPI de peso, uniformidad,
tendencia (ola C); pantalla nueva (fase 9); engorde/progenitoras/incubadora; motor, modelos y migración de `GA-REM-037`.

## Resultado (2026-09-10)

Cerrado (técnico) por `GA-REM-021-B` (commits `f878ab6` spec · `a759a17` código · commit de evidencia): 8/8 · sensibilidad válida ·
regresión 1016 passed · 49 skipped · 0 failed (935 s; 1000 previas + 16 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · evidencia `GA-REM-021-B01-B02-RECEPTION-EVIDENCE.md`. `GA-REM-021` sigue **PARTIAL**.
