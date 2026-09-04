# GA-REM-006 · GA-REM-007 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-006` (correcciones e integridad del dato) · `GA-REM-007` (`BR-14`, segregación) |
| **Wave** | 2 · **Stages 6 y 7** |
| **Fecha** | 2026-09-04 |
| **Hallazgos** | `P0-2` · `R-23` · `R-45` · `R-46` |
| **Estado final** | **`CERTIFIED`** |

---

## GA-REM-006 — `P0-2`

### Original finding

`create_correction` creaba el `CorrectionLog`, cambiaba el estado a `CORRECTED` y **no
escribía nada**. El dato erróneo era el que se aprobaba, el que alimentaba los KPI y el que
se consolidaba hacia SAP. El sistema quedaba con dos verdades divergentes, y la auditoría
respaldaba la que no era.

### Implementation

Regla vigente **`RR-01`** (Wave 1.5): la corrección escribe el valor en el acto, conserva el
original y deja el registro pendiente de aprobación.

| Decisión | Motivo |
|---|---|
| **Lista blanca** de campos corregibles, derivada de `OperationalEventUpdate` | `field_name` lo elige el cliente. Un `setattr` sobre lo que llegue permitiría corregir `status`, `company_id`, `registered_by_id` o `approved_by_id`: la misma escalada de privilegios que `R-32` |
| **`original_value` lo lee el servidor** del propio dato, ignorando el del *payload* | Si el valor original lo aporta quien corrige, la auditoría deja de ser evidencia y pasa a ser una declaración |
| **Conversión tipada** de `corrected_value` | Llega como texto; escribirlo tal cual en una columna numérica o de fecha daría un 500 en vez de un mensaje útil |
| `version` **avanza** | Una corrección produce una versión nueva, como exige `BR-16` |

20 campos corregibles: los operativos del contrato, sin `status`, `event_type` ni
`idempotency_key`.

### AC — verificación

| Criterio | Resultado |
|---|---|
| La corrección aplica el valor al dato | ✅ 5 campos parametrizados, ida y vuelta |
| Valor original y corregido, ambos conservados (`BR-09`) | ✅ |
| El original no lo puede falsear el cliente | ✅ test dedicado con una mentira deliberada |
| El evento corregido **no** queda aprobado (`RR-01`) | ✅ `status=corrected`, `approved_by_id=None` |
| No se corrige lo que no es un dato operativo | ✅ 6 campos sensibles rechazados con 400 |
| Un valor del tipo equivocado da 400, no 500 | ✅ |
| No se corrige un evento cancelado | ✅ |

`tests/test_corrections.py` — **18 PASS · 0 FAIL**

---

## GA-REM-007 — `BR-14`

### Original finding

Tres vías distintas de saltarse la segregación de funciones:

1. `complete_review` fijaba `APPROVED` y `approved_by_id` **sin comprobarla** cuando la
   empresa tenía un solo nivel de aprobación (`R-23`);
2. `approve` la aplicaba de forma **incondicional**, ignorando
   `ApprovalStep.require_segregation` — una columna que existía, se sembraba con cada paso
   y no se leía nunca;
3. `PUT /operations/{id}` permitía fijar el estado sin pasar por ninguna de las dos
   (`R-32`, corregido en el Stage 1).

### Implementation

Regla vigente **`RR-03`** (Wave 1.5): `BR-14` es **configurable por paso de aprobación**
mediante `ApprovalStep.require_segregation`, con valor por defecto `True`.

La comprobación se extrajo a `SegregacionMixin`, del que heredan `ReviewService` y
`ApprovalService`. **Una regla de control interno aplicada en un sitio y ausente en otro no
es un control: es una casualidad.** Por eso vive en un único lugar y no incrustada en cada
servicio.

Sin pasos configurados se exige segregación: el valor por defecto de la columna es `True`, y
una empresa que no ha configurado nada no puede haber renunciado a un control interno sin
saberlo.

### El test que verificaba lo contrario de lo que decía

`test_f4_approve_event` registraba y aprobaba con **el mismo cliente**. Al aplicarse
`BR-14`, empezó a fallar. La lectura correcta no es que la regla estorbe: es que el test,
tal como estaba escrito, **comprobaba que la regla no existiera**.

Se corrigió usando dos identidades reales —el operador registra, el aprobador aprueba—,
que es lo que el flujo describe en `docs/12 §3`. La regla se mantuvo intacta.

---

## Hallazgos anotados, no corregidos

| ID | Observación | Sev. | Destino |
|---|---|---|---|
| `R-45` | Una corrección de `event_date` se aplica **sin revalidar** `BR-19`, de modo que puede dejar el evento con fecha en período cerrado. El test documenta el comportamiento vigente y admite el deseable | P2 | `GA-REM-016` |
| `R-46` | No se puede corregir un submovimiento (`bird_movements[0].quantity`): el esquema no ofrece forma de identificarlo. Cuatro tests lo intentaban con una ruta anidada que el contrato nunca admitió | P2 | `GA-REM-019` |
| — | Una corrección desde `REGISTERED` deja el evento en `CORRECTED`, que es aprobable, saltando la revisión. `docs/12` solo contempla `EnRevision → Corregido`. No se cambia: alterar los estados corregibles excede el alcance y ninguna fuente lo pide de forma inequívoca | P2 | `GA-REM-016` |

---

## Regression

| Métrica | Tras Stage 5 | **Tras Stages 6-7** |
|---|---|---|
| Recolectados | 189 | **207** |
| PASS | 188 | **207** |
| FAIL | 1 | **0** |

**La suite backend está entera en verde por primera vez en la historia del proyecto.**

Corregido además un fallo dependiente del orden que solo aparecía en la corrida completa:
la exportación manual a SAP escribía en `/app/media/sap_exports`, que únicamente existe
dentro del contenedor. `run_tests.sh` crea ahora un directorio de artefactos por ejecución
y lo destruye al terminar. En aislamiento el fichero pasaba, de modo que el defecto solo era
visible ejecutando todo junto.

## Files changed

```
backend/app/corrections/service.py     P0-2: aplicación del valor, lista blanca, conversión tipada
backend/app/review/service.py          SegregacionMixin; R-23; RR-03
backend/tests/test_corrections.py      nuevo — 18 tests
backend/tests/test_full_workflow_audit.py  F4 con dos identidades; correcciones anidadas ajustadas
backend/scripts/run_tests.sh           directorio de artefactos por ejecución
frontend/**                            SIN CAMBIOS
alembic/versions/**                    SIN CAMBIOS
```

## Final status

**`CERTIFIED`** para ambas. La corrección corrige, la auditoría es evidencia y no
declaración, y la segregación de funciones se aplica en un único sitio por el que pasan
todas las rutas capaces de aprobar.
