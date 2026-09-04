# OPERATION FIELD PERSISTENCE MATRIX — `P0-14`

**Fecha** 2026-09-04 · **Wave** 2 · **Stage 1** · **Spec** `GA-REM-023`
**Método** introspección de SQLAlchemy y Pydantic sobre el código vigente, contrastada con
`information_schema` de la base real y con el *payload* que construye el frontend.

Todos los recuentos de esta matriz se obtuvieron por introspección, no por lectura: el
defecto que se investiga es precisamente el de una lista escrita a mano que se quedó corta.

---

## 1. Cifras verificadas

```
Columnas de operational_events (BD real) ...... 32
Campos de OperationalEventBase (request) ...... 22
Campos del request sin columna en BD ..........  0
Campos asignados por create_event ............. 11
Campos del request IGNORADOS en la creación ... 14   ← P0-14
Campos aceptados por OperationalEventUpdate ...  3   (event_date, observations, status)
```

**No hace falta ninguna migración**: los 14 campos ya existen en el modelo y en la base.
Verificado contra `information_schema.columns` de la instancia de pruebas.

---

## 2. Matriz completa — 22 campos del contrato de entrada

| Field | Request Schema | Service Create | Service Update | Model | DB | Response | Required By | Status |
|---|---|---|---|---|---|---|---|---|
| `lot_id` | ✅ | ✅ | ❌ | ✅ | `INTEGER` | ✅ | núcleo | `UPDATE_MISSING` |
| `farm_id` | ✅ | ✅ | ❌ | ✅ | `INTEGER` | ✅ | `BR-08` | `UPDATE_MISSING` |
| `house_id` | ✅ | ✅ | ❌ | ✅ | `INTEGER` | ✅ | `BR-08` | `UPDATE_MISSING` |
| `event_type` | ✅ | ✅ | ❌ | ✅ | `VARCHAR(28)` | ✅ | núcleo | `INTENTIONALLY_IMMUTABLE` |
| `event_date` | ✅ | ✅ | ✅ | ✅ | `DATE` | ✅ | `BR-06`, `BR-19` | `FULLY_PERSISTED` |
| `observations` | ✅ | ✅ | ✅ | ✅ | `TEXT` | ✅ | — | `FULLY_PERSISTED` |
| `sap_document_ref` | ✅ | ✅ | ❌ | ✅ | `VARCHAR(100)` | ✅ | `BR-10` | `UPDATE_MISSING` |
| **`supplier_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | `docs/02 §3.5` recepción | **`CREATE_MISSING`** |
| **`cause_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | **cliente §16: «Mortalidad — Cantidad, causa»** | **`CREATE_MISSING`** |
| **`cull_cause_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | descarte | **`CREATE_MISSING`** |
| **`vaccine_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | `docs/02 §3.5.6` · cliente §2 | **`CREATE_MISSING`** |
| **`vaccination_route`** | ✅ | ❌ | ❌ | ✅ | `VARCHAR(50)` | ✅ | `docs/02 §3.5.6` | **`CREATE_MISSING`** |
| **`vaccine_lot_number`** | ✅ | ❌ | ❌ | ✅ | `VARCHAR(100)` | ✅ | trazabilidad sanitaria | **`CREATE_MISSING`** |
| **`medication_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | `docs/02 §3.5.7` | **`CREATE_MISSING`** |
| **`dosage_per_bird`** | ✅ | ❌ | ❌ | ✅ | `FLOAT` | ✅ | `docs/02 §3.5.7` | **`CREATE_MISSING`** |
| **`treatment_days`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | `docs/02 §3.5.7` | **`CREATE_MISSING`** |
| **`destination_farm_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | `docs/02 §3.5.9` salida de aves | **`CREATE_MISSING`** |
| **`destination_plant_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | `docs/02 §3.5.9` | **`CREATE_MISSING`** |
| **`transport_id`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | `docs/02 §3.5.9` · cliente §11 | **`CREATE_MISSING`** |
| **`sample_size`** | ✅ | ❌ | ❌ | ✅ | `INTEGER` | ✅ | cliente §11 «Muestra tomada» | **`CREATE_MISSING`** |
| **`extra_data`** | ✅ | ❌ | ❌ | ✅ | `JSONB` | ✅ | `OperationFormPage.tsx:1129` | **`CREATE_MISSING`** |
| `idempotency_key` | ✅ | ✅ | ❌ | ✅ | `VARCHAR(64)` | ✅ | `BR-12` | `INTENTIONALLY_IMMUTABLE` |
| `status` | ❌ | ❌ | ✅ ⚠ | ✅ | enum | ✅ | flujo de aprobación | **`CONTRACT_DEFECT` → `R-32`** |

---

## 3. Verificación en ejecución

Petición con siete de los campos ignorados, contra la base aislada:

```
[CREATE] 201
  enviado=1                    devuelto=None      vaccine_id
  enviado='water'              devuelto=None      vaccination_route
  enviado='L-001'              devuelto=None      vaccine_lot_number
  enviado=0.5                  devuelto=None      dosage_per_bird
  enviado=1                    devuelto=None      supplier_id
  enviado=30                   devuelto=None      sample_size
  enviado={'nota': 'sonda'}    devuelto=None      extra_data
[READ ] vaccine_id = None
```

La API responde `201`, el recurso se crea, y **todo lo que distingue a una vacunación de
un registro vacío se ha perdido en silencio**.

---

## 4. Clasificación de cada campo ignorado

Ninguno de los 14 es derivado ni de solo lectura. Todos vienen del formulario, todos tienen
columna propia y todos se devuelven en la respuesta. La clasificación es uniforme:

| Clasificación | Campos |
|---|---|
| `BUG` (persistir) | los **14** |
| `DERIVED_FIELD` | ninguno |
| `READ_ONLY_FIELD` | ninguno |
| `DEPRECATED_FIELD` | ninguno |
| `SPEC_GAP` | ninguno |

`extra_data` merece una nota: es un `JSONB` libre. El frontend lo usa
(`OperationFormPage.tsx:1129`, `extra_data.source_farm_id`), así que persistirlo es correcto
y necesario. Acotar su forma por tipo de evento es una mejora aparte, registrada como
`R-33`, no un motivo para seguir descartándolo.

---

## 5. Causa raíz

`create_event` construye el modelo con una **lista escrita a mano**
(`app/operations/service.py:69-81`) que enumera 11 de los 22 campos del contrato. No hay
ningún mecanismo que relacione esa lista con el esquema: cuando la migración
`c1d2e3f4a5b6 add_operation_specific_fields` añadió las columnas y el esquema las expuso,
nadie actualizó el constructor, y **nada falló**.

El defecto no es que falten 14 asignaciones. Es que **es posible que falten**: cualquier
campo que se añada mañana al contrato se perderá igual y en silencio. La corrección tiene
que eliminar esa clase de fallo, no solo sus 14 instancias actuales.

---

## 6. Asimetría create / update

`OperationalEventUpdate` acepta 3 campos y `update_event` solo permite editar en
`DRAFT`, `REGISTERED` y `RETURNED` (`service.py:491`) — exactamente los estados en los que
`docs/12 §3` reconoce que el operador puede «Editar (antes de enviar)».

En esos estados, un operador que se equivocó de vacuna **no puede corregirla**: tiene que
cancelar y volver a registrar. La corrección de la asimetría consiste en admitir en la
actualización los mismos campos operativos que en la creación, **manteniendo intactas** las
restricciones de estado, que son las que hacen respetar `BR-15`, `BR-16` y `RR-01`.

`event_type` e `idempotency_key` quedan deliberadamente fuera: cambiar el tipo de un evento
ya registrado invalidaría las reglas que se le aplicaron al crearlo, y la clave de
idempotencia identifica el envío original.

---

## 7. `R-32` — hallazgo nuevo, P0

`status` está en `OperationalEventUpdate` y `update_event` lo aplica con `setattr`
(`service.py:493-494`). Verificado en ejecución:

```
[CREATE] status = registered
[PUT status=approved] -> 200
[READ ] status = approved
```

Cualquier usuario autenticado puede aprobar cualquier evento con un `PUT`, saltándose:

- el flujo completo `REGISTERED → PENDING_REVIEW → IN_REVIEW → APPROVED`;
- `BR-13` — nada llega a SAP sin aprobación: el registro **queda** aprobado;
- `BR-14` — quien registró acaba de aprobar su propio registro;
- la traza: `approved_by_id` queda **nulo**, de modo que existe un evento aprobado **sin aprobador**.

Es la tercera vía de elusión de `BR-14` encontrada, tras `R-23` (`complete_review`) y la
propia ausencia de lectura de `require_segregation`. Severidad **P0**: integridad del dato
y control de acceso. Destino `GA-REM-023` (es un defecto del contrato de entrada), con
referencia cruzada a `GA-REM-007` y `GA-REM-002`.

---

## 8. Hallazgos derivados de esta matriz

| ID | Hallazgo | Sev. | Destino |
|---|---|---|---|
| `P0-14` | 14 campos del contrato nunca se persisten en la creación | **P0** | `GA-REM-023` |
| **`R-32`** | `PUT /operations/{id}` permite fijar `status` y aprobar sin flujo ni aprobador | **P0** | `GA-REM-023` ✕ `GA-REM-007` ✕ `GA-REM-002` |
| `R-33` | `extra_data` es `JSONB` sin forma acotada por tipo de evento | P2 | `GA-REM-019` |
| `R-34` | Los 14 campos tampoco son editables antes de enviar a revisión | P1 | `GA-REM-023` |
