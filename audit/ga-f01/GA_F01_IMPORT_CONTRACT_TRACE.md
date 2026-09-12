# GA-F01 · TRAZA DEL CONTRATO DE IMPORTACIÓN (formulario → API)

Fecha: 2026-09-12 · Fuente: `OperationFormPage.tsx` (bundle `index-DNXomVaS.js`) + payload real capturado en `audit/ga-r153/uat/evidence/referencia-walkthrough.json` + esquema backend `backend/app/operations/schemas.py`.

## 1 · Ruta y capas

| Capa | Ubicación |
|---|---|
| Ruta | `/operations/new` (wizard) · `OperationFormPage.tsx` |
| Esquema de formulario (zod) | `operationSchema` (líneas ~85-186); `superRefine` solo exige lote a los tipos no opcionales (R-153) |
| Valores por omisión | `defaultValues` (línea ~242): incluye **`egg_storage_records: [{}]`** ← defecto S1 |
| Serializador | `onSubmit` (líneas 357-425): `payload = {...data, …}`; línea ~415 `egg_storage_records: data.egg_storage_records || []` ← defecto S1 |
| Servicio frontend | `api.post('/operations', payload)` (línea ~418) |
| Endpoint | `POST /api/v1/operations` → `OperationalEventCreate` (schemas.py:159) |
| Servicio backend | `OperationsService.create_event` (+ `_apply_business_rules` → `validate_import_plan` BR-22) |

## 2 · Campos del payload real (importación) → contrato backend

| JSON enviado (real) | Backend | Estado |
|---|---|---|
| `event_type='grandparent_import'`, `event_date` | `OperationalEventBase` requeridos | ✔ |
| `observations:''`, `supplier_id`, `transport_id` | opcionales/nullable | ✔ |
| `bird_movements` ♂40/♀60 (+`avg_weight`) | `list[BirdMovementSchema]` | ✔ |
| `egg_movements/feed_movements/hatchery_params/inspection_details: []` | defaults `[]` | ✔ |
| **`egg_storage_records: [{}]`** | `list[EggStorageSchema]`, `arrival_date` **requerido** | ✖ **422** |
| `extra_data.import_plan.*` (11 claves) | validado por `validate_import_plan` (BR-22) | ✔ |
| **`extra_data.sap_order_ref: '33'`** (id) | — (conveniencia de UI) | observado |
| **falta `sap_document_ref`** | `validate_import_plan` lo exige (OC) | ✖ **400 BR-22** |

## 3 · Bloque de OC compartido (origen de S2)

- Render: `eventType ∈ {grandparent_import, bird_reception, bird_exit, egg_dispatch, egg_reception_hatchery, chick_dispatch}` (líneas ~1903-1990), rama no-cría y rama cría (radio transferencia/compra ~1927-1952).
- `SearchSelect` entrega `onChange(String(item.id))` (el **id** del registro `sapReference`).
- El bloque hoy: `setValue('extra_data.sap_order_ref', v)` con `v = id` y busca la orden comparando **etiqueta** contra `v` → nunca encuentra → extras (vendor/declared) tampoco se fijan. **Nunca escribe `sap_document_ref`**.
- Precedente canónico **existente** en el propio archivo (`case 'bird_exit'`, bloque `GA-TD-014`/`GA-REM-035 AC13`): escribe **ambos** campos (`sap_document_ref` + `extra_data.sap_order_ref`). El bloque compartido no recibió ese arreglo.
- Identificador canónico esperado por backend: el **código** de la referencia SAP (p.ej. `PO-C001-GPR-0001`), como usan los flujos ya certificados (R-152, controles de contrato).

## 4 · Controles de contrato backend (runtime, admin, sondas canceladas)

| Caso | Resultado observado |
|---|---|
| OC tipada (`sap_document_ref`) + `egg_storage_records: []` | **201** (sonda 98, cancelada) — contrato canónico funcionando |
| `[{}]` + OC tipada | 422 `egg_storage_records[0].arrival_date` requerido |
| OC solo en `extra_data.sap_order_ref` + `[]` | 400 BR-22 «declara la orden de compra SAP» |
| `[{}]` en recepción / `[]` en recepción | 422 / 201 (misma semántica de lista vacía = sin registros) |
| Registro completo sintético en importación sin lote | **500** → observación F-01c (`egg_storage.lot_id` NOT NULL vs `lot_id=None`; no alcanzable por UI; fuera de alcance) |

## 5 · Recepción (misma capa de guardado)

- Mismo `onSubmit`/payload → misma carga `[{}]` → mismo 422 (verificado por control). 
- Contrato backend de recepción no exige almacenamiento; `[]` (lista vacía) es la representación canónica de «sin registros» (default del esquema). No se cambia semántica de recepción (BR-17/18/20 intactos).

## 6 · Presentación de error (S3)

- `onSubmit` catch (línea ~423): `err.response?.data?.detail || t('operations.saveError')` → el `detail` estructurado (array de objetos) se asigna a `result.message` y se renderiza → **React #31**.
- Helper existente: `getErrorMessage` (`components/Toast.tsx`) — devuelve `detail` **crudo** (mismo riesgo). Se extenderá como normalizador seguro compartido (reuso, no reescritura de arquitectura).
- `operationSchema`/RHF no producen este caso: el 422 viene del servidor (p.ej. cualquier residuo de schema). La corrección no enmascara validaciones: 4xx sigue rechazando, ahora legible.
