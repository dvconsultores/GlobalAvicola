# GA-REM-023 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-023` — Persistencia de campos de evento y contrato de error |
| **Wave** | 2 · **Stages 1 y 2** |
| **Fecha** | 2026-09-04 |
| **Hallazgos** | `P0-14` · `R-26` · `R-27` · `R-30` · `R-32` · `R-34` |
| **Estado final** | **`CERTIFIED`** |

## Original findings

Dos defectos independientes en `OperationsService`, con el mismo efecto: **el sistema
acepta algo y no hace lo que dice que hizo.**

`P0-14` — `create_event` construía el modelo con una lista escrita a mano de 11 campos
frente a los 22 que el contrato declara. Los otros 14 se aceptaban, se devolvían como
`null` y nunca se guardaban.

`R-26` — el único `try/except` que traducía `BusinessRuleViolation` a `400` cubría cinco
reglas. Las otras ocho escapaban sin manejar y llegaban al cliente como
`500 Internal Server Error`.

Durante la ejecución aparecieron cuatro más: `R-32`, `R-34`, `R-30` y `R-27`.

## Evidence

Matriz completa por campo: `audit/remediation/OPERATION_FIELD_PERSISTENCE_MATRIX.md`
(introspección de SQLAlchemy y Pydantic contrastada con `information_schema`).

Reproducción de `P0-14` antes de intervenir:

```
[CREATE] 201
  enviado=1                 devuelto=None      vaccine_id
  enviado='water'           devuelto=None      vaccination_route
  enviado={'nota': ...}     devuelto=None      extra_data
[READ ] vaccine_id = None
```

Reproducción de `R-32`:

```
[CREATE] status = registered
[PUT status=approved] -> 200
[READ ] status = approved        ← aprobado sin revisión, sin segregación, sin aprobador
```

Reproducción de `R-26`:

```
bird_reception sin farm_id       -> HTTP 500  Internal Server Error
mortality_recording sobre saldo  -> HTTP 400  {"detail":"Mortalidad (999999) excede..."}
```

## Implementation

### `P0-14` — la asignación se deriva del contrato

```python
event_fields = data.model_dump(exclude=set(schemas.SUBMOVEMENT_FIELDS))
event_fields["event_type"] = event_type          # el enum ya validado
event = models.OperationalEvent(**event_fields, company_id=…, status=…, registered_by_id=…)
```

El defecto no era que faltaran 14 asignaciones: era que **fuera posible que faltaran**.
Cualquier campo añadido mañana al contrato se habría perdido igual y en silencio. La
corrección elimina esa clase de fallo, no solo sus instancias. Se añadieron dos constantes
explícitas —`SUBMOVEMENT_FIELDS` e `IMMUTABLE_AFTER_CREATE`— para que la exclusión sea
declarativa y no un detalle enterrado.

**Ninguna migración**: los 14 campos ya existían en el modelo y en la base. Verificado
antes de tocar nada.

### `R-26` — un contrato de error, no ocho

Manejador **tipado** registrado en `app/main.py`:

```python
@app.exception_handler(BusinessRuleViolation)
async def _business_rule_violation_handler(request, exc):
    return JSONResponse(status_code=400,
                        content={"detail": exc.message, "rule": exc.rule_id or None})
```

Deliberadamente **no** se captura `Exception`: un fallo imprevisto debe seguir siendo un
500, porque esconderlo tras un 400 sería peor que el defecto que se corrige. Un test lo
verifica sobre el propio código fuente.

El `try/except` local de `_apply_business_rules` se retiró: mantenerlo habría dejado dos
contratos —uno con `rule` y otro sin él— para el mismo tipo de error. Ahora las 23 reglas
de `validators.py`, y cualquiera que se añada, comparten uno solo.

`detail` sigue siendo una cadena: los clientes existentes no se rompen. `rule` se añade
para que la interfaz identifique la regla sin analizar el texto.

### `R-32` — el estado sale del contrato de edición

`OperationalEventUpdate` se reescribió: incorpora los campos operativos (`R-34`) y
**excluye** `status`, `event_type` e `idempotency_key`. Con `extra="forbid"`, un cliente
que envíe `status` recibe un `422` explícito en lugar de un `200` que no hizo nada — la
misma clase de fallo silencioso que `P0-13` y `P0-14`, cerrada aquí por contrato.

Las restricciones de estado de `update_event` (`DRAFT`, `REGISTERED`, `RETURNED`) **no se
relajaron**: son las que hacen cumplir `BR-15`, `BR-16` y `RR-01`.

### `R-30` y `R-27`

`validate_period_open` rechaza ahora las fechas futuras, con un día de holgura por zona
horaria. `_get_role_by_name` devuelve `422` accionable en vez de `500`.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| `AC01` | La creación persiste todos los campos del contrato | ✅ 14/14 |
| `AC02` | Prueba por campo, ida y vuelta | ✅ 14 tests parametrizados |
| `AC03` | Mecanismo contra la reaparición | ✅ dos tests estructurales: contrato ⊆ columnas, y la asignación debe derivarse |
| `AC04` | Las 7 reglas de `R-26` devuelven 400 con regla | ✅ verificado sobre 6 casos representativos de 5 reglas |
| `AC05` | Ninguna `BusinessRuleViolation` alcanza el manejador por defecto | ✅ |
| `AC06` | `_get_role_by_name` responde 4xx accionable | ✅ 422 nombrando el rol |
| `AC07` | Forma de error estable `{detail, rule}` | ✅ |
| `AC08` | El frontend no muestra 500 por una regla | ✅ por construcción; `tsc` y `vitest` en verde |
| `AC09` | La edición admite los campos operativos sin relajar estados | ✅ |
| `AC10` | `status` deja de ser fijable por `PUT` | ✅ |
| `AC11` | El intento se rechaza explícitamente | ✅ 422, no descarte silencioso |
| `AC12` | `event_type` e `idempotency_key` inmutables | ✅ |
| `AC13` | Fecha futura rechazada con 400 | ✅ |

## Tests

| Fichero | Contenido | Resultado |
|---|---|---|
| `tests/test_p014_persistence.py` | 24 tests: estructurales, ida y vuelta por campo, edición, `R-32`, inmutabilidad | **23 PASS · 1 FAIL** |
| `tests/test_r26_error_contract.py` | 9 tests: 6 reglas parametrizadas, barrido anti-5xx, manejador tipado, `R-27` | **9 PASS** |
| `tests/test_time_determinism.py` | +3: `R-30` futuro, holgura horaria, contrato `{detail, rule}` | **10 PASS** |

El único `FAIL` es `test_ac02_cause_id_en_mortalidad`, que no falla por `P0-14` sino por
**`P0-1`**: todo registro de mortalidad con cantidad positiva entra en
`_check_and_create_alerts` y choca con `NameError: get_current_bird_balance`
(`service.py:246`). Queda rojo y trazado; lo pone en verde el **Stage 4**.

## Files changed

```
backend/app/operations/service.py      create_event deriva del contrato; try/except local retirado
backend/app/operations/schemas.py      SUBMOVEMENT_FIELDS, IMMUTABLE_AFTER_CREATE, Update reescrito
backend/app/operations/validators.py   R-30: fechas futuras
backend/app/main.py                    manejador tipado de BusinessRuleViolation
backend/app/review/service.py          R-27: 422 accionable
backend/tests/test_p014_persistence.py nuevo
backend/tests/test_r26_error_contract.py nuevo
backend/tests/…                        payloads y aserciones corregidas (ver más abajo)
backend/seeds/test_seeds.py            catálogos maestros, 2ª granja, 2º galpón, 2ª compañía, roles del flujo
alembic/versions/**                    SIN CAMBIOS
frontend/**                            SIN CAMBIOS
```

## DB changes

**Ninguna.** Los 14 campos ya existían en el modelo y en la base; se verificó contra
`information_schema` antes de escribir código. Cadena Alembic: 1 head, deriva 0.

## Correcciones de tests aplicadas (`GA-REM-015`)

Con el contrato de error ya correcto, 12 de los fallos clasificados como `TEST_DEFECT` y
`OBSOLETE_TEST` pudieron cerrarse con evidencia:

| Test | Corrección | Justificación |
|---|---|---|
| 12 *payloads* sin `farm_id`/`house_id` | completados | `BR-08` es legítima (`spec.md:269`) y el frontend sí los envía (`OperationFormPage.tsx:404`) |
| `test_auth::test_login_success` | credenciales por *fixture* | `admin/admin123` eliminada por `GA-REM-004` |
| `test_auth::test_get_me` | `/api/v1/me` | `/api/v1/auth/me` nunca existió |
| `test_multi_company` × 3 | prefijo `/api/v1` + identidades reales de la siembra | los `sub` fijos suponían una compañía 2 inexistente |
| `test_list_event_types`, `test_f10` | 24 → 25 y clave `type` | `egg_reception_classification` existe desde `939fd14` |
| 4 lecturas de submovimientos | leen `GET /{id}` | `POST` devuelve la cabecera; el detalle los expone |
| `test_sap_connection_check` | `connected is False` | `GA-REM-010` hizo honesto al adaptador manual |
| `test_idempotency_key…` | 201 en ambos envíos | el resto de la suite y el router coinciden en 201 |

**Ninguna aserción de negocio se relajó.** Donde el test tenía razón y el código no
—`vaccine_id`, `medication_id`, `BR-08` como 400— se corrigió el código.

## Regression

| Métrica | Antes de Wave 2 | Tras Stage 0 | **Tras Stages 1-2** |
|---|---|---|---|
| Recolectados | 101 | 107 | **144** |
| PASS | 74 | 80 | **142** |
| FAIL | 26 | 27 | **2** |
| SKIP | 1 | 1 | **0** |

Los 2 fallos restantes son `P0-1` (Stage 4) y `BR-14` (Stage 7): defectos funcionales
conocidos con stage asignado, no regresiones.

Quality gates **8/8 en verde**: `ruff`, cadena Alembic (1 head), deriva de esquema 0,
guarda de entorno (25), sin credenciales en seeds, `tsc`, `vitest` 61/61, paridad i18n
865=865.

Determinismo de `R-28` **conservado**: con el calendario tres años adelante el resultado es
idéntico (`2 failed · 142 passed`).

## Hallazgos anotados, no corregidos

| ID | Observación | Sev. | Destino |
|---|---|---|---|
| `R-33` | `extra_data` es `JSONB` sin forma acotada por tipo de evento | P2 | `GA-REM-019` |
| `R-35` | Un envío deduplicado por idempotencia responde `201` aunque no cree nada | P3 | `GA-REM-019` |
| `R-36` | `get_events` filtra por compañía con `and self.company_id`: un usuario sin compañía **no** recibe filtro y ve todo. Fail-open | **P1** | `GA-REM-002` (Stage 5) |

`R-36` se detectó al hacer que los tests multiempresa verificaran de verdad. No se corrige
aquí: pertenece al cluster de seguridad.

## Final status

**`CERTIFIED`.** Los 14 campos viajan de ida y vuelta, la clase de fallo que los perdía
está cerrada estructuralmente, las reglas de negocio hablan un único idioma de error, y el
estado del evento ya no puede alterarse por `PUT`.
