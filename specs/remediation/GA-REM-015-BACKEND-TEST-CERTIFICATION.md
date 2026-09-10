# GA-REM-015 — CERTIFICACIÓN DE LOS TESTS DE BACKEND

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-015` · **Tipo** `QA SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** `CERTIFIED` (2026-09-03, Wave 1.5) · **addendum `R-28` `SPEC_READY`** (Wave 2 · Stage 0) |
| **Dependencias** | **`GA-REM-014`** (bloqueante absoluto) · idealmente tras `GA-REM-005, 006, 007` |
| **Hallazgos** | `GA-TD-023` · `GA-TD-044` · `audit/15_TESTING_STATUS.md` |

## Problema
76 tests de backend nunca ejecutados. Su estado real es desconocido. Al menos uno está confirmado como roto por análisis estático.

## Evidencia
| Ítem | Detalle |
|---|---|
| Inventario | 76 tests en 8 archivos (`pytest --collect-only`, verificado) |
| Distribución | `test_full_workflow_audit` 23 · `test_operations` 12 · `test_sap` 9 · `test_auth` 7 · `test_masters` 7 · `test_review` 7 · `test_audit_reports` 6 · `test_multi_company` 5 |
| Test roto confirmado | `test_operations.py:19` — `assert len(data) == 24`; el endpoint devuelve **25** (verificado en runtime) |
| Buena trazabilidad existente | `test_full_workflow_audit.py` nombra flujos F1–F10 alineados con los AC del MVP |

## Comportamiento esperado
Los 76 tests se ejecutan, su resultado se clasifica y cada fallo se resuelve **decidiendo primero quién está equivocado**.

## Alcance
1. Ejecutar la suite completa en el entorno de `GA-REM-014`.
2. Clasificar cada resultado: `PASS` · `FAIL` · `SKIPPED` · `ERROR`.
3. Agrupar los fallos por causa: `test obsoleto` · `defecto de implementación` · `desajuste con la spec` · `fixture` · `migración` · `entorno` · `contrato` · `regla de negocio`.
4. Para cada fallo, aplicar el Art. 8.4 de la constitución: `SPEC → REGLA DE NEGOCIO → TEST → IMPLEMENTACIÓN`.
5. Corregir lo que corresponda **sin ocultar problemas**.
6. Medir cobertura y fijar el objetivo de la siguiente iteración.

## Fuera de alcance
Escribir tests nuevos para funcionalidad no cubierta (eso pertenece a cada `GA-REM` funcional) · tests E2E (`GA-REM-016`) · alcanzar el 80 % de cobertura de una sola vez.

## Prohibiciones explícitas (Art. 8.3 de la constitución)
```
NO borrar un test porque falla
NO marcar skip sin justificación escrita en esta spec
NO rebajar aserciones
NO alterar el resultado esperado para acomodarlo al defecto
NO mockear funcionalidad central para obtener verde
```

## Fallos ya previstos por análisis estático
| Test | Causa probable | Decisión anticipada |
|---|---|---|
| `test_operations.py::test_list_event_types` | espera 24 tipos, hay 25 | **el test está desactualizado**: se añadió `egg_reception_classification` en `076ca5e`. Se corrige el test, no el código. Debe registrarse además como parte de `GA-REM-020` (el tipo carece de spec) |
| Tests que dependen de `lot_id=2` | fixture acoplada a datos | corregido por `GA-REM-014` |
| Tests de SAP | el adaptador cambia con `GA-REM-010` | reevaluar tras esa spec |
| `test_f8c_business_rule_mortality_exceeds_balance` | debería detectar el defecto P0-1 | **debe fallar antes de `GA-REM-005` y pasar después** — es el test de regresión natural |

## Acceptance Criteria

**AC01 — Ejecución completa y clasificada**
```
Given el entorno aislado de GA-REM-014
When  se ejecuta la suite completa
Then  se obtiene el recuento de PASS, FAIL, SKIPPED y ERROR
And   cada FAIL tiene una causa asignada de la taxonomía de esta spec
```
**AC02 — Cada fallo tiene decisión documentada**
```
Given cada test en fallo
When  se consulta el registro de decisiones
Then  indica si el error está en el test, en la implementación o en la spec
And   cita la fuente que resuelve la duda
```
**AC03 — Sin ocultamiento**
```
Given el diff de cierre
When  se inspeccionan los cambios sobre tests
Then  ningún test ha sido borrado
And   ningún skip carece de justificación escrita
And   ninguna aserción ha sido rebajada
```
**AC04 — El test de regresión de mortalidad funciona**
```
Given el código anterior a GA-REM-005
When  se ejecuta test_f8c_business_rule_mortality_exceeds_balance
Then  falla
Given el código posterior a GA-REM-005
Then  pasa
```
**AC05 — La suite pasa en CI**
```
Given el workflow de backend con el entorno aislado
When  se ejecuta
Then  la suite termina en verde
```
**AC06 — Cobertura medida**
```
Given la suite ejecutada con medición de cobertura
When  se consulta el informe
Then  existe una cifra de cobertura y un objetivo documentado para la siguiente iteración
```

## Tests requeridos
La spec **es** sobre tests. Su verificación es la ejecución misma y el registro de decisiones.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Ante muchos fallos, la tentación de silenciarlos | AC03 lo verifica sobre el diff |
| Un test verde por una fixture mal construida | revisión de las fixtures como parte de `GA-REM-014` |
| Los tests de SAP quedan obsoletos tras `GA-REM-010` | secuenciar: `GA-REM-010` antes que esta spec, o reevaluar |

## Definition of Done
- [ ] Suite ejecutada · [ ] Cada fallo clasificado y decidido · [ ] AC01–AC06 verificados · [ ] Cobertura medida · [ ] Certification report con el detalle test a test


---

# ADDENDUM `R-28` — DETERMINISMO TEMPORAL DE LA SUITE

**Añadido** 2026-09-04 · **Wave 2 · Stage 0** · **Prioridad** P1 con **fecha límite dura**

## Problema

`validate_period_open` (`backend/app/operations/validators.py:332-347`, `BR-19`/G-R12) rechaza
todo evento con más de **90 días** de antigüedad respecto a `date.today()`. La suite fija
fechas literales de junio de 2026 en **31 lugares**:

```
2026-06-29  ×19    caduca el 2026-09-27
2026-06-23  ×11    caduca el 2026-09-21
2026-06-27  ×1     caduca el 2026-09-25
```

A partir del **2026-09-21** decenas de tests hoy en verde empezarán a fallar sin que nadie
cambie una línea de código. La línea base `RUN 05` dejaría de ser reproducible y
`GA-REM-016` heredaría el defecto.

Confirmado en ejecución al sondear `P0-1` con fecha `2026-06-01`, ya fuera de plazo:

```
app/operations/validators.py:343: BusinessRuleViolation:
  La fecha del evento (2026-06-01) está en un período cerrado (+90 días).
```

## Principio

**`BR-19` pertenece al dominio y no se toca.** El defecto está en los tests, que dependen
del calendario real en lugar de expresar la regla. Un test debe decir «dentro del período
abierto», no «29 de junio de 2026».

## Alcance

`backend/tests/**` · `backend/seeds/test_seeds.py`. **Nada en `backend/app/**`.**

`backend/seeds/integration_seeds.py` y `backend/seeds/live_data_boost.py` quedan **fuera**:
no los usa la suite (`run_tests.sh` siembra con `seeds.test_seeds`). Se registran como
deuda de Wave 3 si alguna vez alimentan tests.

## Acceptance Criteria

| ID | Criterio |
|---|---|
| `AC09` | Existe un reloj de referencia único para la suite; ningún test construye fechas de evento por su cuenta |
| `AC10` | Cero fechas literales `20\d\d-\d\d-\d\d` en `backend/tests/**` y en `backend/seeds/test_seeds.py` |
| `AC11` | El resultado de la suite es idéntico ejecutándola con distintas fechas de referencia dentro del período abierto |
| `AC12` | `BR-19` queda **cubierta por test** en sus tres regiones: antes del límite, en el límite y pasado el límite — cobertura que hoy no existe |
| `AC13` | El helper declara el umbral de 90 días de forma explícita y un test falla si el comportamiento de producción deja de coincidir con él |
| `AC14` | `backend/app/**` sin cambios |

## Clasificación exigida

Cada dependencia temporal encontrada se clasifica en `INTENTIONALLY_FIXED_DATE`,
`TIME_RELATIVE_TEST` o `ACCIDENTAL_TIME_DEPENDENCY`, y la clasificación se documenta.

## Tests requeridos

| ID | Verificación |
|---|---|
| `T-028-01` | `BR-19` antes del límite (día 89) → aceptado |
| `T-028-02` | `BR-19` en el límite exacto (día 90) → aceptado |
| `T-028-03` | `BR-19` pasado el límite (día 91) → rechazado con `400` y mención de la regla |
| `T-028-04` | Cero fechas literales en el árbol de tests |
| `T-028-05` | La suite da el mismo resultado con una fecha de referencia distinta |

## Definition of Done

- [ ] `AC09`–`AC14` verificados · [ ] `T-028-01`…`05` en verde · [ ] Clasificación documentada · [ ] Línea base reproducible tras el 2026-09-21 · [ ] Certification report

---

# ADDENDUM `R-175` — AISLAMIENTO DE LAS FASES PRODUCTIVAS QUE CREAN LAS SUITES (2026-09-10 · WAVE B · tranche 11)

| Campo | Valor |
|---|---|
| **Addendum** | `GA-REM-015-B` · `QA SPEC` (validez de pruebas) · **Estado** `SPEC_READY` (tranche 11) |
| **Hallazgo** | `R-175` (P3): `test_lot_start_date`, `test_lots_bu_enforcement` y `test_od14_productive_surfaces` crean una `ProductivePhase` cuando no existe ninguna y no la retiran; `test_clean_baseline::test_t_025_07` cuenta las fases de toda la base (`== 4`) y cae («las fases se duplicaron: 5») en cualquier invocación que ejecute una de esas suites antes que el baseline |
| **Por qué ahora** | prompt del tranche 11 §49: el residuo produjo un **rojo falso** en el verde dirigido de `R-176`/`R-178` (orden no alfabético: `test_lot_start_date` antes que `test_clean_baseline`) → `R-175` pasa a **BLOQUEANTE** y se formaliza la remediación mínima del arnés bajo esta spec (`R-28`: «el defecto está en los tests, `BR-19` no se toca» es el precedente) |
| **Principio** | cada suite retira en su teardown **exactamente** lo que creó, por prefijo propio (patrón ya certificado en `test_opening_balance.py:73`); ningún guardián se relaja (`test_t_025_07` sigue contando `== 4`); ninguna regla de dominio cambia |
| **Fuera** | reescritura del arnés · fixtures compartidas · aleatorización del orden · `R-166` |

## Criterios de aceptación

| AC | Criterio |
|---|---|
| `AC-R175-01` | las tres suites borran en su teardown la `ProductivePhase` que crearon (por `code`/`name` con su prefijo), después de los lotes que la referencian |
| `AC-R175-02` | A→B (`suite → test_clean_baseline`) verde para las tres suites (antes: `1 failed`, «5 fases») |
| `AC-R175-03` | aisladas y B→A siguen verdes (sin regresión) |
| `AC-R175-04` | pares con las suites del tranche 11: `T11 → A`, `A → T11`, `T11 → B`, `B → T11` verdes |
| `AC-R175-05` | `test_clean_baseline` no cambia; regresión completa verde |

## Tests requeridos

La matriz de control `R175_TEST_ORDER_DEPENDENCY_CONTROL.md §5` (ejecuciones con base reseteada) es la evidencia; no se añade un guardián estático.

## Definición de terminado

`AC-R175-01…05` · matriz §5 verde · regresión completa leída · `R-175` CERRADO (técnico) · la regla permanente C (`ISOLATED + A→B + B→A` para suites con
historial de residuo) deja de ser obligatoria para estas tres suites una vez cerrado, y sigue vigente para cualquier residuo nuevo.
