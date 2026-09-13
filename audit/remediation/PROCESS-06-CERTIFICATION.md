# `P-06` · POLLO DE ENGORDE — INFORME DE CERTIFICACIÓN

> **Vigencia — anotación `GA-GOV-03` (T1, 2026-09-13). Estado: `NOT_REPRODUCIBLE_EN_HEAD (pre-GA-GOV-03)`.**
> Este informe histórico no cita commit certificado ni artefacto de corrida (regla «no GREEN por declaración», §52) y varias suites de proceso (P-03/P-04/P-05/P-10/P-11/P-15) contenían TEST_DEFECT rojos hasta la T1 de GA-GOV-03. El contenido no se reescribe; la recertificación E2E de cada proceso corresponde a la T12 del programa pre-SAP (`audit/ga-pre-sap-program/GA_PRE_SAP_REMEDIATION_MASTER_ROADMAP.md`).

---

# REEVALUACIÓN tras `OD-04` y `GA-REM-035` (2026-09-06)

```
P-06 = PARTIAL — BLOCKED_BY_DEFECT (R-76)
```

Se reevalúan **uno a uno** los tres bloqueantes históricos, sin certificar por alcance:

| Bloqueante | Estado | Evidencia |
|---|---|---|
| **`GA-TD-014`** | **RESUELTO** | `OD-04` `RESOLVED` · `GA-REM-035` `CERTIFIED`. El paso `bird_reception` de `P-06` ya aplica el límite acumulado |
| **`GA-REQ-037`** | **no bloquea** | `§4.8` —la sección normativa de `P-06`— **no menciona alertas por desviación**. Las exige `§4.5`, que es `P-03`. Verificado leyendo ambas |
| **`R-76`** | **BLOQUEA** | `docs/12 R7`: «un lote no puede cerrarse si tiene registros sin aprobar». Sigue sin implementarse, y `§4.8` incluye «cierre de lote» en su cadena |

## Por qué `P-06` sigue `PARTIAL`

`R-76` es una regla de **cierre**, y el cierre es el paso terminal de `P-06`. Un lote puede
cerrarse hoy con eventos en `registered`, lo que contradice `docs/12 R7`.

**No se corrige aquí.** Es otra causa, con su propia spec de destino, y absorberla dentro de
`GA-TD-014` sería exactamente lo que el proceso de este programa prohíbe.

```
Lo que falta para certificar P-06:  R-76, y solo R-76.
```

Es la primera vez que `P-06` queda a un único hallazgo de la certificación.

---

# CERTIFICACIÓN · `P-06` (2026-09-06)

```
P-06 = CERTIFIED
```

## 1. Los tres bloqueantes históricos, cerrados uno a uno

| Bloqueante | Estado | Evidencia |
|---|---|---|
| `GA-TD-014` | **CERTIFIED** | `OD-04` resuelta · `GA-REM-035`. La recepción lleva la OC al campo tipado y aplica el límite acumulado |
| `GA-REQ-037` | **no aplica** | `§4.8` —la sección normativa de `P-06`— **no menciona alertas por desviación**. Las exige `§4.5`, que es `P-03`. Reverificado leyendo la sección completa, no por transitividad |
| **`R-76`** | **CERTIFIED** | `GA-REM-036` · `docs/12 R7` |

## 2. `§4.8`, releído entero

> - Recepción de pollitos de un día desde incubadora (trazados al lote origen)
> - Distribución a galpones por lote
> - Ciclo: alimento (diario), pesaje (semanal), mortalidad (diaria), vacunación
> - Descarte de aves fuera de condición
> - **Cierre de lote** y despacho a planta de beneficio
> - KPIs: ganancia diaria, conversión alimenticia, viabilidad, uniformidad, EPEF

Ninguna mención a alertas. Los KPI que enumera están cubiertos por `P-15`, certificado.

## 3. La cadena

| # | Paso | Estado |
|:--:|---|:--:|
| 1 | `farm_inspection` | **PASS** |
| 2 | `bird_reception` con límite acumulado de OC | **PASS** — `GA-REM-035` |
| 3 | `bird_distribution` | **PASS** |
| 4 | `feed_registration` | **PASS** |
| 5 | `weight_recording` | **PASS** |
| 6 | `mortality_recording` | **PASS** — `GA-REM-005` |
| 7 | `cull_recording` | **PASS** |
| 8 | `vaccination` · `medication` | **PASS** |
| 9 | `bird_exit` | **PASS** |
| 10 | Aprobación de los registros | **PASS** — ciclo real de `P-07` |
| 11 | **Cierre de lote** | **PASS** — `BR-05` + `R7` + resumen |

```
11 pasos · PASS 11 · FAIL 0
```

## 4. El cierre, ahora con sus tres guardas

| Guarda | Qué exige | Origen |
|---|---|---|
| lote activo | no cerrar dos veces | `GA-REM-029 AC06` |
| `BR-05` | pesaje y alimento | `spec.md:266` |
| **`R7`** | **ningún registro sin aprobar** | `docs/12 §6` |

Y el resumen final que `R-73` restauró, con la fecha que `R-75` corrigió.

## 5. Evidencia

`e2e/proceso-p06-pollo-de-engorde.spec.ts` · **6 casos** · `API_E2E`.

El happy path **aprueba los nueve eventos por el camino normativo** —enviar, tomar la
revisión, aprobar con el aprobador, porque `BR-14` impide que apruebe quien registró— y no
manipulando la base: `R7` es una regla de aprobación, y comprobarla saltándose la aprobación
no probaría el proceso.

Y queda una **evidencia negativa permanente**: la cadena entera registrada, `BR-05`
satisfecho, y un registro sin aprobar basta para impedir el cierre.

### Una prueba obsoleta, sustituida

El caso «`GA-TD-014` sigue sin llegar al campo tipado» se escribió para fallar el día que el
hueco se resolviera. Se resolvió — pero la prueba seguía pasando, porque su fixture no enviaba
el campo: ya no documentaba nada. Se sustituyó por el comportamiento certificado — entregas
parciales aceptadas y exceso rechazado con `BR-18`.

## 6. Veredicto

```
P-06 = CERTIFIED   ·   11 de 11 pasos
```
