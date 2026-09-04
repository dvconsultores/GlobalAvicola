# GA-REM-023 — PERSISTENCIA DE CAMPOS DE EVENTO Y CONTRATO DE ERROR

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-023` · **Tipo** `DATA INTEGRITY + API CONTRACT SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** |
| **Estado** | `SPEC_READY` |
| **Origen** | Wave 1.5 · Track C — revelado por la primera ejecución real de la suite backend |
| **Dependencias** | `GA-REM-001` · `GA-REM-014` (base aislada, ya `CERTIFIED`) |
| **Hallazgos** | `P0-14` · `R-26` · `R-27` · **`R-32`** · **`R-34`** · `R-30` |
| **Detectado** | 2026-09-03 — `audit/remediation/BACKEND_TEST_FAILURE_MATRIX.md §4` |

## Problema

Dos defectos independientes, ambos en `OperationalEventService`, ambos con el mismo efecto:
**el sistema acepta algo y no hace lo que dice que hizo.**

### `P0-14` — 14 columnas se descartan en silencio

`create_event` construye el `OperationalEvent` asignando 11 campos
(`backend/app/operations/service.py:69-81`). El esquema de entrada declara 14 campos
específicos de operación más (`schemas.py:92-105`), las columnas existen en el modelo
(`models.py:104-117`) y en el esquema, y `OperationalEventRead` los devuelve. Ninguno se
persiste jamás. La API responde `201` y el cliente recibe `null`.

```
supplier_id  cause_id  cull_cause_id  vaccine_id  vaccination_route
vaccine_lot_number  medication_id  dosage_per_bird  treatment_days
destination_farm_id  destination_plant_id  transport_id  sample_size  extra_data
```

Consecuencias verificadas: la mortalidad **no puede registrar su causa** (`cause_id`),
exigida literalmente por el cliente (§16, «Mortalidad — Cantidad, causa»); la vacunación no
registra qué vacuna se aplicó ni por qué vía; la salida de aves no registra destino ni
transporte. El frontend **sí envía** estos campos (`OperationFormPage.tsx:404`, `:1129`).

### `R-26` — siete reglas de negocio devuelven 500 en lugar de 400

El bloque `try/except BusinessRuleViolation → HTTP 400` de `_apply_business_rules` abarca
solo `service.py:336-364`. Los siete validadores invocados antes lanzan la excepción fuera
del manejador, y no existe manejador global (`main.py:54` solo registra `RateLimitExceeded`).

| Regla | Validador | Línea | HTTP actual | HTTP correcto |
|---|---|---|---|---|
| `BR-07` | `validate_lot_active` | `:317` | 500 | 400 |
| `BR-06` | `validate_event_date` | `:318` | 500 | 400 |
| `BR-08` | `validate_farm_house` | `:320` | 500 | 400 |
| `BR-19` | `validate_period_open` | `:322` | 500 | 400 |
| `BR-10` | `validate_sap_document_unique` | `:325` | 500 | 400 |
| `BR-17` / G-R04 | `validate_house_capacity` | `:332` | 500 | 400 |
| G-R05 | `validate_oc_limit` | `:334` | 500 | 400 |

Verificado en ejecución contra la base aislada:

```
bird_reception sin farm_id      -> HTTP 500  Internal Server Error
mortality_recording sobre saldo -> HTTP 400  {"detail":"Mortalidad (999999) excede el saldo..."}
```

### `R-32` — `PUT /operations/{id}` aprueba sin flujo ni aprobador  **(P0, nuevo)**

`OperationalEventUpdate` declara `status` (`schemas.py:118-122`) y `update_event` lo aplica
con `setattr` (`service.py:493-494`). Verificado en ejecución:

```
[CREATE] status = registered
[PUT status=approved] -> 200
[READ ] status = approved
```

Cualquier usuario autenticado aprueba cualquier evento con un `PUT`, saltándose el flujo
`REGISTERED → PENDING_REVIEW → IN_REVIEW → APPROVED`, `BR-13` (el registro queda aprobado y
por tanto consolidable hacia SAP) y `BR-14` (quien registró aprueba lo suyo). `approved_by_id`
queda **nulo**: un evento aprobado sin aprobador. Tercera vía de elusión de `BR-14`, tras
`R-23` y la bandera `require_segregation` muerta.

### `R-34` — los campos operativos tampoco son editables antes de revisión  **(P1, nuevo)**

`update_event` solo permite editar en `DRAFT`, `REGISTERED` y `RETURNED` —exactamente los
estados en que `docs/12 §3` reconoce que el operador puede «Editar (antes de enviar)»— pero
`OperationalEventUpdate` acepta 3 campos. Un operador que erró la vacuna debe cancelar y
volver a registrar.

### `R-27` — configuración ausente reportada como error del servidor

`review/service.py:505-508` responde `500` cuando falta un rol del sistema. Un requisito de
configuración no satisfecho debe ser un 4xx accionable que nombre lo que falta.

## Evidencia

| Ítem | Ruta |
|---|---|
| Constructor con 11 de 25 campos | `backend/app/operations/service.py:69-81` |
| Esquema de entrada con los 14 campos | `backend/app/operations/schemas.py:92-105` |
| Columnas existentes en el modelo | `backend/app/operations/models.py:104-117` |
| Frontera del `try/except` | `backend/app/operations/service.py:336-364` |
| Ausencia de manejador global | `backend/app/main.py:54` |
| 500 por configuración ausente | `backend/app/review/service.py:505-508` |
| Tests que lo revelan | `test_operations.py::test_vaccination_stores_vaccine_id`, `::test_medication_stores_medication_id`, `test_full_workflow_audit.py::test_f1_create_vaccination`, `::test_f8b_duplicate_sap_document_blocked` |

## Reglas de negocio afectadas

`BR-06`, `BR-07`, `BR-08`, `BR-10`, `BR-17`, `BR-19`, G-R04, G-R05 — todas **se aplican
correctamente**; lo que está mal es cómo se comunican. `P0-14` afecta a la integridad del
dato de mortalidad, vacunación, medicación, recepción y salida.

## Criterios de aceptación

| ID | Criterio |
|---|---|
| `AC01` | `create_event` persiste **todos** los campos operativos del contrato, no una lista escrita a mano |
| `AC02` | Existe una prueba por campo que verifica ida y vuelta: se envía, se guarda, se lee |
| `AC03` | Un mecanismo impide la reaparición del defecto: añadir un campo al contrato no puede volver a perderse en silencio. Un test falla si el conjunto persistido deja de cubrir el conjunto declarado |
| `AC09` | `update_event` admite los mismos campos operativos que la creación, **sin relajar** las restricciones de estado que hacen cumplir `BR-15`, `BR-16` y `RR-01` (`R-34`) |
| `AC10` | `status` deja de ser fijable por `PUT`: el estado solo cambia por las transiciones del flujo (`R-32`) |
| `AC11` | Un intento de fijar `status` por `PUT` se rechaza de forma explícita; no se ignora en silencio |
| `AC12` | `event_type` e `idempotency_key` permanecen inmutables tras la creación |
| `AC04` | Las 7 reglas de la tabla de `R-26` devuelven `400` con el mensaje y el código de regla |
| `AC05` | Ninguna `BusinessRuleViolation` puede alcanzar el manejador por defecto de FastAPI |
| `AC06` | `_get_role_by_name` responde 4xx nombrando el rol ausente, no `500` |
| `AC07` | La respuesta de error tiene forma estable y documentada: `{detail, rule}` |
| `AC08` | El frontend muestra el mensaje de la regla; ningún flujo enseña «Internal Server Error» por una regla de negocio |

## Escenarios

```gherkin
Given un evento de vacunación con vaccine_id, vaccination_route y vaccine_lot_number
When se crea mediante POST /api/v1/operations
Then la respuesta 201 devuelve esos tres valores
And una lectura posterior del evento los conserva

Given un evento de mortalidad con cause_id
When se crea
Then la causa queda persistida y es consultable en los informes

Given un bird_reception sin farm_id
When se crea mediante POST /api/v1/operations
Then la respuesta es 400
And el detalle nombra BR-08 y explica que se requiere una granja asignada
And la respuesta NO es 500

Given un sap_document_ref ya registrado para el mismo lote y tipo
When se intenta registrar de nuevo
Then la respuesta es 400 citando BR-10
```

## Backend afectado

`app/operations/service.py` (asignación de campos y frontera de manejo de errores),
`app/main.py` (manejador de `BusinessRuleViolation`), `app/review/service.py` (`R-27`).

## Frontend afectado

Ninguno funcionalmente: ya envía los campos. Sí conviene revisar que el mensaje de la regla
se muestre al operador una vez que llegue un 400 en lugar de un 500.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Persistir `extra_data` sin validar abre un vector de datos arbitrarios | acotar su esquema por tipo de evento antes de habilitarlo, o dejarlo fuera del alcance de esta spec y tratarlo aparte |
| Convertir 500 en 400 puede cambiar el comportamiento de clientes que hoy reintentan ante 5xx | es la corrección deseada; documentar el cambio de contrato |
| Un evento existente creado sin estos campos queda incompleto | no hay retroceso posible: los datos nunca se guardaron. Documentar el alcance temporal del defecto |

## Definition of Done

- [ ] `AC01`–`AC08` verificados · [ ] Tests por campo en verde · [ ] Sin `BusinessRuleViolation` sin manejar · [ ] Alcance temporal del dato perdido documentado · [ ] Certification report


---

## Addendum — `R-30` (Wave 2 · Stage 0)

`validate_period_open` no acota fechas **futuras**: `days_ago` negativo pasa la comparación
`> 90`, de modo que se admite registrar un evento con fecha de mañana. Se detectó al
escribir la cobertura de frontera de `BR-19` en `R-28`. Severidad P2.

| ID | Criterio |
|---|---|
| `AC13` | Un evento con fecha posterior al día en curso se rechaza con `400` citando la regla |

Se trata aquí por pertenecer al mismo contrato de validación, no por parche aparte.
