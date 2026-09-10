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

---

## Addendum B — `R-176` (+ `R-45`) · paridad de validación en edición y corrección (2026-09-10 · WAVE B · tranche 11)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-023-B` · `DATA INTEGRITY` (contrato de validación) · **Estado** `SPEC_READY` (pre-flight 2026-09-10) |
| **Hallazgos** | **`R-176`** (P3 → **P2** normalizado) · **`R-45`** (Wave 2, P2: corregir `event_date` no revalida `BR-19`; abierto, `GA-REM-016`/`GA-REM-019`) — absorbido |
| **Matriz** | `audit/remediation/R176_CREATE_EDIT_CORRECTION_VALIDATION_PARITY_MATRIX.md` (reglas definidas, paridad, campo → reglas, frontera con `R-173`) |
| **Fuentes** | `§Reglas de negocio afectadas` de esta spec (`BR-06`, `BR-08`, `BR-10`, `BR-17`, `BR-19` se aplican en el alta) · addendum `R-30` (`AC13`) · `GA-REM-035 §3` (`BR-18`, `OD-04`) · `docs/02 §7 R6` · `spec.md §5 BR-08`, `BR-11` · `GA-REM-040-G AC-W09` y `RR-18` (`RC-15`): «el destino de una edición se verifica como el de un alta» · `tests/test_corrections.py` («corregir no es una puerta trasera», `R-45`) |
| **Principio** | **paridad de validación sin repetir el alta**: las seis reglas son lecturas puras; se evalúan sobre el **estado candidato** (fila persistida + cambio) en la guarda central existente (`verificar_destino_de_edicion`, `GA-REM-005-E`); `create_event` sigue siendo el único que persiste, audita `created`, crea alertas, notificaciones y vínculos |
| **Sin cambio** | estados editables/corregibles · permisos · rutas · cantidades inmutables · `R-173` (bloqueo, saldos, auditoría con valores) · etiqueta `BR-10` de la unicidad SAP (observación: `spec.md` la numera `BR-11`; el contrato de error no se altera) · `R-80` (zona horaria) · `R-140`/`R-154` residuales |
| **Migración** | ninguna |

### B.1 Contrato

1. **Estado candidato**: `cand[campo] = cambios[campo] si campo ∈ cambios, si no getattr(event, campo)` para `lot_id`, `farm_id`, `house_id`,
   `destination_farm_id`, `event_date`, `sap_document_ref`. `n` = Σ `bird_movements.quantity` persistidos (el cliente no aporta cantidades).
2. **Disparadores** (sin sobre-validación): `farm_id`/`house_id` → `BR-08`; `event_date` → `BR-06` (vs `lote_destino`) y `BR-19` (período cerrado y fecha
   futura); `sap_document_ref` o `lot_id` → `BR-11` (`validate_sap_document_unique`, `exclude_event_id = event.id`, tipo ≠ `bird_reception`);
   `house_id` en `bird_reception`/`bird_distribution` → `BR-17` (`validate_house_capacity(cand.house_id, n)` si `n > 0`); `sap_document_ref` en
   `bird_reception`/`bird_distribution` → `BR-18` (`validate_oc_limit(cand.sap_document_ref, n, company_id, exclude_event_id = event.id)`).
3. **Orden** (`§63`): autenticación → empresa → original (`get_event`) → inquilino/unidad/lote activo/fecha vs lote/ubicación (`R-173`, sin cambio) →
   **reglas puras del candidato** (`BR-08` → `BR-06`/`BR-19` → `BR-11` → `BR-17` → `BR-18`) → bloqueo de lotes y reglas de saldo (`R-173`) → aplicar →
   auditar → confirmar. Ninguna regla de negocio se evalúa antes de la cadena de inquilino (sin fuga de información).
4. **Dos superficies, una guarda**: `PUT /operations/{id}` (todos los campos del cambio) y `POST /corrections` (`field_name` ∈ {`lot_id`, `farm_id`,
   `house_id`, `destination_farm_id`, `event_date`, `sap_document_ref`}) pasan por `verificar_destino_de_edicion`; ambas se prueban.
5. **Error**: el de cada regla en el alta (`400 {detail, rule}`); ninguno nuevo.
6. **Cero efectos**: una denegación deja fila, saldo, auditoría, alertas, notificaciones y vínculos intactos; una edición/corrección válida produce
   exactamente su auditoría (`UPDATED` con valores / `CORRECTED`) y nada del alta.
7. **Estados**: sin cambio (`EDITABLES`; correcciones `REGISTERED…REJECTED`; aprobado inmutable).
8. **Fecha de negocio**: `validate_period_open` se reutiliza tal cual (`date.today()`); las pruebas usan `tests.time_reference`; `test_time_determinism` obligatoria.

### B.2 Criterios de aceptación

| AC | Criterio |
|---|---|
| `AC-R176-01` | `PUT house_id` de una recepción de 100 aves a un galpón de capacidad 50 → `400 BR-17`; `house_id`, saldo y auditoría intactos |
| `AC-R176-02` | corrección de `house_id` → ídem (`400 BR-17`, sin `correction_logs`) |
| `AC-R176-03` | OC-A (100) con 80 recibidas y OC-B (100) con 50: `PUT sap_document_ref` de la segunda → OC-A → `400 BR-18` (130 > 100); con cupo (OC-C de 200) → `200` |
| `AC-R176-04` | corrección de `sap_document_ref` → ídem |
| `AC-R176-05` | `PUT`/corrección de `event_date` → +91 días: `400 BR-19` · futura (+2 días): `400 BR-19` · anterior al inicio del lote: `400 BR-06` · dentro del período y posterior al inicio: `200`/`201` |
| `AC-R176-05b` | `PUT {"house_id": null}` en una recepción → `400 BR-08`; corrección `farm_id` = `""` en un despacho de huevos → `400 BR-08` |
| `AC-R176-05c` | vacunación con `DOC-1` en el lote; otra con `DOC-2`: `PUT`/corrección `sap_document_ref` → `DOC-1` → `400 BR-10`; mover a un lote donde `DOC-1` ya existe → `400 BR-10`; la recepción (OC repetible) no aplica |
| `AC-R176-06` | edición válida (galpón con capacidad, OC con cupo, fecha válida) → `200` y valor aplicado |
| `AC-R176-07` | corrección válida → `201`, estado `CORRECTED`, valor aplicado, `version + 1` |
| `AC-R176-08` | toda denegación: cero cambios en `operational_events`, saldo igual, cero `audit_logs` de éxito, cero `operational_alerts`, cero `notifications`, cero `egg_batches`/`chick_batches` nuevos |
| `AC-R176-09` | edición y corrección válidas: `audit_logs` +1 (`updated` / `corrected`), `operational_alerts` +0, `notifications` +0, `egg_batches`/`chick_batches` +0, saldos iguales — la paridad no repite el alta |
| `AC-R176-10` | `R-173` intacto (`tests/test_edit_cancel_balance.py` verde) |
| `AC-R176-11` | evento aprobado: `PUT` → `400` (sin cambio) |
| `AC-R176-12` | actor de otra empresa / unidad apagada / sin permiso → `400 BR-07` / `403`, antes de cualquier regla de negocio |

### B.3 Tareas

| Tarea | Descripción |
|---|---|
| `T-023-B1` | pruebas rojas `tests/test_edit_validation_parity.py` (prefijo `PARI-`; escenario propio: empresa A/B; galpón grande y galpón de capacidad 50; `sap_references` `PURCHASE_ORDER` OC-A/OC-B (100) y OC-C (200); lote con `start_date` futuro para `BR-06`; fechas de `tests.time_reference`) |
| `T-023-B2` | `operations/service.py::verificar_destino_de_edicion`: composición del candidato y reglas puras (B.1) antes del bloqueo |
| `T-023-B3` | `corrections/service.py`: la guarda también para `event_date` y `sap_document_ref` |
| `T-023-B4` | `tests/test_corrections.py::test_la_fecha_corregida_sigue_sujeta_a_las_reglas`: la aserción tolerante pasa a exigir el `400` (`R-45` cerrado por prueba, no por transitividad) |
| `T-023-B5` | sensibilidad B.4; regresiones `R-173`, `R-135`/`R-143`, `R-159`/`R-160`, `B01`/`B02`/`B05`, `R-161`, `R-130`; `test_time_determinism`; evidencia; cierre |

### B.4 Sensibilidad

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| `R176-S1` | `BR-17` de la guarda | `AC-R176-01` (y `_02`) |
| `R176-S2` | la llamada a la guarda desde la corrección para `event_date`/`sap_document_ref` (superficie de corrección) | `AC-R176-02/04/05` (corrección) |
| `R176-S3` | `BR-18` de la guarda | `AC-R176-03/04` |
| `R176-S4` | `BR-19`/`BR-06` del candidato | `AC-R176-05` |
| `R176-S5` | reproducir un efecto del alta en la edición válida (llamar a `_auto_create_traceability_batches`/alerta) | `AC-R176-09` |

### B.5 Definición de terminado

`AC-R176-01…12` verdes · rojo válido leído en `80cce71` · sensibilidad válida · `R-173` 16/16 · `test_time_determinism` · regresión completa leída ·
`R-176` y `R-45` cerrados (técnico).
