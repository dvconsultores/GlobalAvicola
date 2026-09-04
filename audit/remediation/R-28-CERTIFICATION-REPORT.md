# `R-28` — CERTIFICATION REPORT · DETERMINISMO TEMPORAL DE LA SUITE

| | |
|---|---|
| **Hallazgo** | `R-28` — la suite backend caduca por `BR-19` |
| **Spec destino** | `GA-REM-015` · addendum `R-28` (no se creó GA-REM nueva: ya existía destino) |
| **Wave** | 2 · **Stage 0** |
| **Fecha** | 2026-09-04 |
| **Estado final** | **`CERTIFIED`** |

## Original finding

`validate_period_open` (`backend/app/operations/validators.py:332-347`, `BR-19`/G-R12)
rechaza todo evento con más de 90 días de antigüedad respecto a `date.today()`. La suite
fijaba fechas literales de junio de 2026 en 31 lugares. A partir del **2026-09-21**
decenas de tests en verde habrían empezado a fallar solos, y la línea base `RUN 05` habría
dejado de ser reproducible.

## Evidence

Reproducción del defecto antes de intervenir, sondeando con una fecha ya fuera de plazo:

```
app/operations/validators.py:343: BusinessRuleViolation:
  La fecha del evento (2026-06-01) está en un período cerrado (+90 días).
```

Inventario completo de la dependencia temporal:

| Ámbito | Ocurrencias | Clasificación |
|---|---|---|
| `tests/test_full_workflow_audit.py` | 17 × `2026-06-29` | `ACCIDENTAL_TIME_DEPENDENCY` |
| `tests/test_operations.py` | 11 × `2026-06-23` | `ACCIDENTAL_TIME_DEPENDENCY` |
| `tests/run_e2e_audit.py` | 2 × `2026-06-29` | `ACCIDENTAL_TIME_DEPENDENCY` |
| `tests/test_multi_company.py` | 1 × `2026-06-27` | `ACCIDENTAL_TIME_DEPENDENCY` |
| `seeds/test_seeds.py` | `start_date=date(2026, 1, 1)` | `ACCIDENTAL_TIME_DEPENDENCY` |
| Tests frontend (4 ficheros) | 0 | — |
| Specs E2E Playwright (4 ficheros) | 0 | — |
| `seeds/integration_seeds.py`, `seeds/live_data_boost.py` | 14 | **fuera de alcance** — no los usa la suite |

**`INTENTIONALLY_FIXED_DATE`: 0.** Ninguna de las 31 fechas expresaba una intención
temporal; todas eran «una fecha cualquiera para un evento operativo». Ningún test
ejercitaba `BR-19`: la regla **no tenía cobertura**.

## Implementation

| Archivo | Acción | Contenido |
|---|---|---|
| `backend/tests/time_reference.py` | **nuevo** | Reloj de referencia único. `CLOSED_PERIOD_DAYS = 90` explícito. Fechas con nombre por intención: `recent_event_date`, `inside_open_period`, `at_open_period_boundary`, `beyond_open_period`, `lot_start_date` |
| `backend/tests/simulated_clock.py` | **nuevo** | Adelanta `datetime.date` **de todo el proceso** vía `GA_TEST_SIMULATED_TODAY`, de modo que aplicación y tests midan contra el mismo calendario. Context manager `simulating()` con save/restore |
| `backend/tests/conftest.py` | modificado | Engancha la simulación en `pytest_configure`; nueva *fixture* `http_client` con `raise_app_exceptions=False` para observar el código HTTP real |
| `backend/tests/test_time_determinism.py` | **nuevo** | `T-028-01` … `T-028-06` |
| 4 ficheros de test + `seeds/test_seeds.py` | modificados | 31 fechas literales → `recent_event_date()`; `start_date` → `lot_start_date()` |
| **`backend/app/**`** | **sin cambios** | `BR-19` intacta |

### Decisión de diseño revisada durante la ejecución

El primer intento expuso `GA_TEST_REFERENCE_DATE`, que desplazaba **solo** la fecha que
los tests escriben. Se descartó al comprobarlo empíricamente: con la referencia a
`hoy − 30`, `T-028-01` y `T-028-02` fallaban porque `BR-19` seguía midiendo contra el día
real. Un override así no prueba nada y permite ejecuciones engañosas.

Se sustituyó por la simulación consistente del calendario: se reemplaza `datetime.date` en
el proceso, y como `validate_period_open` hace `from datetime import date` **dentro** de la
función, resuelve la clase parcheada en el momento de la llamada. Aplicación y tests ven la
misma fecha. Es la única forma honesta de demostrar que el problema está resuelto.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| `AC09` | Reloj de referencia único | ✅ `tests/time_reference.py`; ningún test construye fechas por su cuenta |
| `AC10` | Cero fechas literales | ✅ 31 → **0**, verificado por `T-028-04` |
| `AC11` | Resultado idéntico con distintos calendarios | ✅ **5 calendarios, resultado idéntico** (tabla abajo) |
| `AC12` | `BR-19` cubierta en sus tres regiones | ✅ `T-028-01` (día 89), `T-028-02` (día 90), `T-028-03a` (día 91) |
| `AC13` | Umbral explícito y verificado contra producción | ✅ `CLOSED_PERIOD_DAYS = 90`; `T-028-02`/`03a` fallarían si producción cambiara el umbral |
| `AC14` | `backend/app/**` sin cambios | ✅ 0 |

## Tests

| ID | Verificación | Resultado |
|---|---|---|
| `T-028-01` | `BR-19` antes del límite (día 89) → aceptado | **PASS** |
| `T-028-02` | `BR-19` en el límite exacto (día 90) → aceptado | **PASS** |
| `T-028-03a` | `BR-19` pasado el límite (día 91) → no persiste | **PASS** |
| `T-028-03b` | `BR-19` pasado el límite → responde **400** | **FAIL — por diseño** ⚠ |
| `T-028-04` | Cero fechas literales en el árbol de tests | **PASS** |
| `T-028-05` | Las fechas derivan de la referencia y conservan su orden | **PASS** |
| `T-028-06` | La simulación alcanza a la aplicación y no contamina | **PASS** |

**PASS 6 · FAIL 1 (declarado)**

### Sobre `T-028-03b`

Falla porque `validate_period_open` se invoca **fuera** del `try/except` de
`_apply_business_rules`, de modo que `BR-19` sale como **500** en lugar de 400. Es el
defecto **`R-26`**, cuyo destino es `GA-REM-023` y cuya corrección es el **Stage 2** de esta
Wave.

El test se escribe ahora, con la aserción correcta, deliberadamente: le da al Stage 2 un
criterio objetivo que satisfacer. No se relaja la aserción ni se marca `xfail` — eso sería
adaptar el test para esconder el defecto. Queda rojo, trazado y con fecha de resolución.

## Prueba de determinismo

Suite completa ejecutada con cinco calendarios distintos, incluido uno **posterior a la
fecha en que el defecto habría estallado**:

| Calendario | Resultado |
|---|---|
| hoy real (2026-09-04) | `27 failed · 80 passed · 1 skipped` |
| **2026-09-28** *(pasada la caducidad original)* | `27 failed · 80 passed · 1 skipped` |
| 2027-01-01 | `27 failed · 80 passed · 1 skipped` |
| 2028-06-15 | `27 failed · 80 passed · 1 skipped` |
| 2031-12-31 | `27 failed · 80 passed · 1 skipped` |

**Idéntico en los cinco.** La bomba de tiempo está desactivada.

## Regression

| Comprobación | Antes | Después |
|---|---|---|
| Suite backend | `26 failed · 74 passed · 1 skipped` | `27 failed · 80 passed · 1 skipped` |
| Tests recolectados | 101 | **107** (+6 de `R-28`) |

El delta se explica exactamente: +6 tests nuevos, de los cuales 5 pasan y 1 falla por
diseño (`T-028-03b`). **Ningún test que pasaba antes ha dejado de pasar.** Los 26 fallos
preexistentes siguen siendo los mismos 26 de `BACKEND_TEST_FAILURE_MATRIX.md`.

## Files changed

```
backend/tests/time_reference.py            nuevo
backend/tests/simulated_clock.py           nuevo
backend/tests/test_time_determinism.py     nuevo
backend/tests/conftest.py                  modificado (simulación + fixture http_client)
backend/tests/test_full_workflow_audit.py  17 fechas
backend/tests/test_operations.py           11 fechas
backend/tests/test_multi_company.py         1 fecha
backend/tests/run_e2e_audit.py              2 fechas
backend/seeds/test_seeds.py                 start_date
backend/app/**                             SIN CAMBIOS
alembic/versions/**                        SIN CAMBIOS
frontend/**                                SIN CAMBIOS
```

## DB changes

Ninguna. No se creó ni modificó ninguna migración.

## Hallazgos anotados, no corregidos

| ID | Observación | Destino |
|---|---|---|
| `R-30` | `BR-19` no acota fechas **futuras**: `days_ago` negativo pasa la validación, de modo que se admite registrar un evento con fecha de mañana | `GA-REM-023` (contrato de validación) |
| `R-31` | `tests/run_e2e_audit.py` es un script muerto: usa `admin/admin123`, credencial eliminada por `GA-REM-004`, y ningún flujo lo ejecuta | `GA-REM-019` (deuda) |
| — | `seeds/integration_seeds.py` y `live_data_boost.py` conservan 14 fechas fijas | fuera de alcance: no alimentan la suite. Deuda de Wave 3 si alguna vez lo hacen |

Ninguno se corrige aquí.

## Final status

**`CERTIFIED`.** La suite produce el mismo resultado con independencia de la fecha real de
ejecución, `BR-19` pasa de cero cobertura a tres tests de frontera, y `backend/app/**` no
se tocó. Queda un único test rojo, declarado y trazado a `R-26`, que el Stage 2 debe poner
en verde.
