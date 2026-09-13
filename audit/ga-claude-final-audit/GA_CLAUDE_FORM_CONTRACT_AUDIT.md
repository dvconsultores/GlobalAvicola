# GA-CLAUDE · AUDITORÍA DE CONTRATOS DE FORMULARIO (§12, §15)

**Fecha** 2026-09-13 · **Repositorio** `/home/maria/Proyectos/GlobalAvicola` · **HEAD** `c0b4afc` (`main`) · **Runtime** `https://avicola.globaldv.net` (bundle `index-DDCcWL76.js` = build local de HEAD) · **Modo** solo lectura.

## 0 · Alcance y método

Se compara, formulario por formulario, la cadena §12: valores por omisión del frontend → validación zod/cliente → serializador (`operationPayload.ts`, `JSON.stringify`) → **payload real observado** (cuando existe evidencia runtime) → esquema Pydantic → validador de negocio → restricción de BD. Se buscan las clases de defecto de F-01: `{}`, `[{}]`, `null` vs requerido, cadenas vacías, nombre de propiedad erróneo, estructura anidada errónea, valor de selector perdido, id en vez de código/objeto, cadena/entero, formato de fecha, opcional/obligatorio, DTO obsoleto, campo de backend nunca poblado.

Fuentes: `B_form_contracts.md` (análisis estático, códigos **B-01…B-41**; citas verificadas sobre HEAD en los puntos de carga), `C_response_error_state.md` (**C#n**), `A_fe_be_trace.md` (**A §n**), registro canónico `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` (ids **R-19x/R-2xx**), evidencia runtime **[RT]** `evidence/runtime-gp-e2e.json`, **[L1]** `evidence/ui-e2e-local-pass1.json`, **[L2]** `evidence/ui-e2e-local-pass2.json` (en generación al redactar; pasos en `ui_e2e_local_pass2.log`).

Convención: `OFP` = `frontend/src/pages/operations/OperationFormPage.tsx` · `V` = `backend/app/operations/validators.py` · `S` = `backend/app/operations/schemas.py` · `SVC` = `backend/app/operations/service.py` · `M` = `backend/app/operations/models.py`.

Veredictos por formulario: **CORRECT** (payload conforme al contrato; pueden quedar P3) · **MALFORMED-DEFAULT** (valores por omisión/filas vacías que viajan) · **WRONG-FIELD** (propiedad, valor, estructura, unidad o derivación errónea) · **422/RENDER** (rechazo de validación cliente/servidor o render de error roto).

---

## 1 · Comportamientos globales que condicionan todos los formularios

| Pieza | Comportamiento verificado | Evidencia | Consecuencia |
|---|---|---|---|
| `api.ts` (axios) | Sin `transformRequest`, sin limpieza de `''`/`undefined`; `JSON.stringify` descarta `undefined`, conserva `''`/`null`, convierte `NaN → null` | `frontend/src/services/api.ts:3-6` | Todo `''` de un `<input>` registrado sin `valueAsNumber` **viaja** |
| `SearchSelect` | `onChange(String(item.id))`; `value` comparado por `String(x.id)` | `components/ui/SearchSelect.tsx:89-93,103-104,159` | Cualquier `setValue(campo, v)` sin mapear id→código escribe el **id** del catálogo (B-09, B-10) |
| `getErrorMessage` | Normaliza `detail` string/lista/objeto a texto (R-189 F-01) | `components/Toast.tsx:95-140` | Solo lo usan asistente, detalle de operación, revisión/aprobaciones, informes, SAP, login, panel. El resto renderiza `detail` crudo (B-15) |
| Preprocesado zod del asistente | `limpiarNumerosNoFinitos` convierte `NaN → undefined`; **no toca `''`** | `OFP:189-207` | `<input type=number>` sin `valueAsNumber` entrega `''` → `z.number()` falla sin render (B-05); `''` en `extra_data` viaja (B-11, B-26) |
| Serializadores R-189 | Filas de aves/alimento/incubadora/almacenamiento sin contenido descartadas; `[{}]` de arranque nunca viaja | `pages/operations/operationPayload.ts:14-70`; `OFP:429-449` | Correcto para F-01/F-01d; efecto colateral en ovoscopía (B-20); `inspection_details` **no** se serializa (B-21) |
| `defaultValues` | `bird_movements: [{sex:'male'},{sex:'female'}]`, `feed_movements: [{}]`, `hatchery_params: [{}]`, `egg_storage_records: [{}]` | `OFP:256-267` | Cubiertos por los serializadores; [RT] payloads con listas hijas `[]` |
| Derivación de ubicación | `farm_id = selectedFarmId ?? lot.farm_id` (o `undefined` en etapa incubadora); `house_id` = 1.ª fila solo en `farm_inspection`/`bird_reception`, si no `lot.house_id` | `OFP:384-395,438-439`; `HATCHERY_EVENTS` `OFP:274-278` | BR-08 (`V:822-839`) exige granja **y** galpón en 10 tipos; la UI no puede satisfacerlo en lotes sin galpón ni en etapa incubadora (B-01, B-04) |
| Edición | Ninguna pantalla llama a `PUT /operations/{id}` | grep `api.put(\`/operations` = 0; `operations.service.ts:40-41` | `OperationalEventUpdate` (`S:195-253`) inalcanzable (B-31; CF-23) |
| Backend 400 de negocio | `{detail, rule}` | `backend/app/main.py:88-98` | `rule` nunca se lee en UI (C#28) |

---

## 2 · Asistente de operaciones (`OperationFormPage`) — 26 tipos de evento

Campos comunes (todos los tipos): `event_type` MATCH (`OFP:89,259,320`; `SVC:222`) · `event_date` MATCH (`OFP:90,257,2098`; `S:140`) · `lot_id` MATCH con `LOT_OPTIONAL_EVENTS` idéntico (`OFP:29-40,178-187`; `SVC:61-68`) · `observations` `''` persistido (B-37, higiene) · `idempotency_key` nunca poblado (B-23 = **R-146** conocido) · `farm_id`/`house_id` **no capturados, derivados** (ver §1) · `evidence` en el detalle, multipart MATCH (`OperationDetailPage.tsx:89-95`; `operations/router.py:344-366`).

| Tipo | Campos capturados vs exigidos por BE no capturados | Serializador / defaults | Mapeo erróneo | Fuente 422/400 | Render de error | Evidencia runtime | Veredicto | Id |
|---|---|---|---|---|---|---|---|---|
| `bird_reception` | Selector OC/traslado superior → código (`OFP:1972-2035`); `supplier_id`, `breed_id`, filas por galpón M/F; cuadre BR-20 **solo** con `stage==='breeder_rearing'` (`OFP:666-682`) | `[{}]` nunca viaja (`OFP:441-449`); `week_number:0` forzado | `house_id` = 1.ª fila si el lote no tiene galpón (F-01e, `OFP:392-393`) ✔ | BR-20 400 cuando el bloque de cuadre no se renderiza (navegación con `?type=`, `stage=null`, `OFP:316-319`) | `getErrorMessage` ✔ | [RT] `R-04: 201` (`sap_document_ref: PO-C001-GPR-0001`, `house_id:1`, `farm_id:1`, hijas `[]`); [L2] `BR2-01` hub **400 BR-20** vs `BR2-02` URL directa **201** | CORRECT (contrato) · **WRONG-FIELD** por navegación (cuadre inalcanzable) | **R-205**; regla BR-17 Σ vs un galpón → **R-211** (B-16, latente) |
| `bird_distribution` | filas `{source/target_house_id, sex, quantity, avg_weight}` | filas `quantity>0` | `house_id` solo `lot.house_id` (`OFP:394`) → ausente en lotes OD-25 | 400 BR-08 «requiere un galpón asignado» | ✔ | [RT] `R-08-bird_distribution: 400` (payload `farm_id:1`, sin `house_id`); [L1] `BO-bird_distribution: 201` con galpón | **WRONG-FIELD** | **R-190** (B-04) |
| `bird_transfer` | `source/target_house_id`, M/F con peso | ídem | `house_id` de lote (B-04); `step=0.001` con etiqueta i18n «(g)» (B-12) | 400 BR-08 sin galpón | ✔ | no ejercitado | **WRONG-FIELD** | R-190, R-210 |
| `bird_exit` | `destination_farm_id/plant_id`, `transport_id`, M/F, transporte | `extra_data.transport_*` sin `valueAsNumber` → cadenas `""` (`OFP:938-973`) | Selector interno «Ref. OC SAP» escribe **id** en `sap_document_ref` (`OFP:917-927`, `v=String(id)`) frente al selector superior correcto (`OFP:2008-2035`) (B-09); `house_id` de lote (B-04) | 400 BR-08 sin galpón; BR-10 no casa por id | ✔ | [RT] `R-08-bird_exit: 400` BR-08; [L1] `BO-bird_exit: 201` con `transport_density:""`… | **WRONG-FIELD** | **R-190**, **R-209**, R-206 (B-26) |
| `feed_registration` | `feed_type_id`, `week_number`, `quantity_kg`, `sacks_count` (`valueAsNumber`), `sap_order_id`, `feed_phase` | fila sin cantidad descartada (F-01d) | `feed_movements.0.sap_order_id ← String(id)` (`OFP:1033-1040`; `M:225` espera código) (B-10) | — | ✔ | [RT] `R-08-feed_registration: 201`; [RT] `backend-C2d-feed-vacio-422` ✔ | **WRONG-FIELD** | **R-209** |
| `water_consumption` | `water_liters` (`valueAsNumber`, min 0.1) | — | — (`ALL_EVENT_TYPES` omite el tipo, B-24 informativo) | — | ✔ | [L1] `BO-water_consumption: 201` | CORRECT | — |
| `weight_recording` | `sample_size`, M/F `avg_weight`, `week_number` solo fila 0 (B-38) | filas `quantity>0` | Unidad: etiqueta renderizada «Peso prom. (g)» (`operations.avgWeight` ES/EN verificado), `step=0.001` y fallback «(kg)» (`OFP:470,627`) | — | ✔ | [RT] `R-08-weight_recording: 201`; [L1] `avg_weight: 2400/2200` (gramos) | CORRECT (contrato) · riesgo de unidad | R-210 (**severidad a reevaluar**) |
| `mortality_recording` / `cull_recording` | `cause_id`/`cull_cause_id` (`Number`), `week_number`, M/F | filas `quantity>0` | — | BR-01 400 legítimo | ✔ (`R05-error-ux.png`) | [RT] 201 / `R-13: 400` BR-01 seguro; [L1] `BO-*: 201`; `MOB-mortality: 400` claro | CORRECT | — |
| `vaccination` / `medication` | `vaccine_id`/`medication_id`, `vaccination_route`, `dosage_per_bird` (`valueAsNumber` ✔ `OFP:581`), `treatment_days`, M/F sin peso | `vaccine_lot_number: ""` (B-37) | — | — | ✔ | [RT] `R-08-vaccination: 201` (`dosage_per_bird: 0.5`); [L1] `BO-medication: 201` | CORRECT | — |
| `farm_inspection` (lote opcional) | `house_inspections[]` UI-only → `inspection_details {house_id, parameter, value|status}` (`OFP:396-421,448`); granja por selector | filas solo con datos | `value_numeric` nunca poblado (B-21b); `farm_id` no exigido en cliente | 400 BR-08 «requiere una granja asignada» si el selector de granja queda vacío | ✔ | [RT] `R-08-farm_inspection: 400` (payload con `house_id:1`, **sin `farm_id`**); [L1] `BR-01/BO-01: 201` con granja | CORRECT (contrato) · **bloqueo por UI** sin exigir granja | **R-190** (AC04) |
| `transport_inspection` | `transport_id`; 6 filas fijas `inspection_details` | **6 filas siempre**, con `value:''`/`status:''` si no se rellenan (sin serializador de cadenas, `OFP:1374-1391`) | numéricos como `value` string; `farm_id/house_id` de lote (B-04) | 400 BR-08 sin galpón | ✔ | no ejercitado | **MALFORMED-DEFAULT** | R-206 (B-21), R-190 |
| `hatchery_inspection` (sin lote/granja) | `hatchery_params[]` por máquina `{incubator_id|hatcher_id, temperature, humidity, co2}` | filas con contenido; `machine_type` eliminado | `hatchery_id` (selector «Incubadora») **nunca viaja** (`OFP:139-149,2044-2056`; `S:101`) (B-22) | — | ✔ | [L2] `HAT2-01: 201` | CORRECT (B-22 P3) | R-194 (B-22) |
| `egg_collection` | `egg_movements[fertile,dirty,broken,infertile,discarded]` + `avg_weight` solo fila fértil (B-39) | filas `quantity>0` | `house_id` de lote (B-04) | 400 BR-08 sin galpón | ✔ | [RT] `R-10-egg_collection: 400` BR-08; [L2] `BR2-egg_collection: 201` con galpón | CORRECT (contrato) · bloqueado en lotes sin galpón | **R-190** |
| `egg_classification` | no está en ningún `STAGE_OPERATIONS` (`processCatalog.ts:205-238`) | — | inalcanzable (B-25) | — | — | — | CORRECT (n/a) | R-220 |
| `egg_reception_classification` | bloque de clasificación; etapa incubadora ⇒ `farm_id undefined` pero **no** está en `location_events` | — | — | — | ✔ | [L2] `HAT2-03: 201` | CORRECT | — |
| `egg_dispatch` | selector traslado superior → código; `hatchery_params.0.incubator_id` («incubadora destino», uso semántico dudoso B-33); `transport_*` | fila fértil única (test `eggDispatchFormContract.test.ts`) | `extra_data.transport_*` cadenas `""` (B-26); `house_id` de lote (B-04) | BR-02 400 legítimo; BR-08 sin galpón | ✔ | [L2] `BR2-egg_dispatch: 201` (`hp:[{incubator_id:1}]`, `ref: AUD-STO-EGG`, `transport_density:""`…); `BR2-egg_dispatch-exceso: 400` BR-02 seguro | CORRECT (contrato) | R-206, R-190 |
| `egg_reception_hatchery` | «Huevos recibidos» → `egg_storage_records.0.eggs_received` (`OFP:1218-1219`); temperaturas; `transport_id`; origen en `extra_data` | fila de almacenamiento con contenido | (1) `farm_id` forzado a `undefined` en etapa incubadora (`OFP:274-278,438`) vs BR-08 (B-01); (2) cantidad en `egg_storage_records` mientras BR-03 lee `egg_movements[fertile]` (`V:149-175`; `SVC:956-960`) (B-02); (3) `arrival_date` requerido no capturado (`S:87`) (B-03, F-01b) | 400 BR-08 «requiere una granja asignada»; 422 `egg_storage_records.0.arrival_date`; BR-03 «disponibles (0)» en la carga siguiente | ✔ (422 normalizado: banner `egg_storage_records.0.arrival_date: Field required`) | [L2] `HAT2-02: 422 arrival_date`; `HAT2-02b: 400` BR-08; `HAT2-02-sonda-sin-storage` (API con granja) 201 → `saldo-tras-recepcion-ui: 400 BR-03 (0)` | **422/RENDER** + WRONG-FIELD | **R-194** (B-01, B-02, B-03) |
| `incubation_load` | `hatchery_params.0 {incubator_id, quantity_loaded, temperature, humidity, co2, turning}` | fila con contenido | — | BR-03 aguas arriba (B-02) | ✔ | [L2] `HAT2-04: NO_REQUEST` (cascada: lote no seleccionado por el arnés) | CORRECT (contrato) · bloqueado aguas arriba | R-194 |
| `ovoscopy` | «Día» → `bird_movements.0.week_number` + `sex='mixed'` (`OFP:1531-1532`); `egg_movements[fertile, infertile, dead_early, dead_late, contaminated]` | fila `{sex:'mixed', week_number}` **descartada** por el serializador (sin campo de contenido, `operationPayload.ts:18-20,40-49`) | día nunca persiste (B-20); dominio `egg_type` pendiente (R-177) | — | ✔ | [L2] `HAT2-05: 201` con `bm: []` (día perdido, confirmado) | **WRONG-FIELD** | R-220 (B-20) |
| `transfer_to_hatcher` | `hatchery_params.0 {hatcher_id, quantity_transferred, temperature, humidity}`; `extra_data.incubation_day` sin `valueAsNumber` | — | `"18"` cadena (B-26) | — | ✔ | [L2] `HAT2-06: 201` | CORRECT | R-206 (B-26) |
| `birth_registration` | 3 filas `sex` hidden; `chicks_healthy/weak` (`valueAsNumber`, no obligatorios en UI vs BR-21 obligatorios, B-35); vacuna; `dosage_per_bird` **sin `valueAsNumber`** (`OFP:1651`; contraste `OFP:581`) | `''` → `z.number().optional()` rechaza → `handleSubmit` no invoca `onSubmit`; el error no se renderiza (B-05) | — | bloqueo **silencioso en cliente**; BR-21 400 si `mixed`+sexadas o sin sanos/débiles | sin mensaje | [L2] `HAT2-07 (sin dosis): NO_REQUEST`, `HAT2-07b (con dosis): NO_REQUEST` — B-05 confirmado parcialmente (sin petición); causa del bloqueo con dosis no aislada (UNKNOWN); `HAT2-07-sonda-api-nacimiento: 201` por API | **422/RENDER** (validación cliente sin render) | **R-194** (B-05, B-35) |
| `chick_dispatch` | `destination_farm_id`, `transport_id`, `sanitary_cert`, M/F | filas `quantity>0` | `farm_id` forzado a `undefined` en etapa incubadora (B-01) | 400 BR-08 «requiere una granja asignada» **siempre** | ✔ | [L2] `HAT2-08: 400` (payload `house_id:2`, `dest:2`, sin `farm_id`) | **WRONG-FIELD** | **R-194** (B-01) |
| `lot_closure` | `bird_movements.0 {sex:'mixed', quantity, avg_weight}`; `extra_data.fcr/mortality_pct` como cadenas | — | no cierra el lote (lo hace `POST /lots/{id}/close`, B-34); `step=0.001` (B-12) | — | ✔ | no ejercitado | CORRECT (contrato) | R-220 (B-34), R-206 (B-26), R-210 |
| `grandparent_import` | selector OC superior → código; `supplier_id`, `transport_id`; `import_plan` (`valueAsNumber` en enteros; fechas ISO); `reception_condition`, `initial_health_inspection`; M/F | `[{}]` nunca viaja ✔ (`storage: []` en [L1]/[L2]) | `quarantine_end_date` opcional en blanco → `''` (`OFP:1782`; `S:43` `Optional[date]` rechaza `''`) (B-11) | 400 BR-22 «Plan de importación inválido: quarantine_end_date: … input is too short» | ✔ (banner) | [L1] `GP-01: 400` (`quarantine_end_date_enviado: ""`); [L2] `GP2-01a: 400` / `GP2-01: 201` con fecha; [RT] evento 124 201 (`GP-01-payload-canonico` ✔ `ref: AUD-PO-GP`) | **422/RENDER** (campo opcional bloquea) | **R-206** (B-11) |

**Cierre de R-189 verificado en runtime**: `[{}]` de arranque → `[]` en todas las listas hijas ([RT] `R-04`, [L1] `GP-01-payload-canonico {storage:[]}`); `sap_document_ref` = código en el selector superior ([RT] `PO-C001-GPR-0001`, [L1]/[L2] `AUD-PO-GP`, `AUD-STO-EGG`); 4xx renderizados sin React #31 en el asistente ([RT] `pageerror: 0`); `house_id` derivado de la 1.ª fila en `bird_reception` ([RT] `house_id:1` con lote `house:null`); escritura estricta y lectura tolerante F-01d ([RT] `backend-C2d-feed-vacio-422: 422`, `backend-C2d-lectura-tolerante: 200`).

---

## 3 · Otros formularios

### 3.1 `LotFormPage` ↔ `LotCreate` (`lots/schemas.py:34-47`)
| Campo | UI / default | Payload | BE | MATCH | Evidencia |
|---|---|---|---|---|---|
| `lot_code` | `min(2).max(50)` | str | `str` 1..100; 409 duplicado (`lots/service.py:311-318`) | MATCH | `LotFormPage.tsx:21,119` |
| `bird_type` | select 4 valores | str | `BirdTypeEnum` | MATCH | `:18` |
| `farm_id` | **obligatorio** en zod (`min(1)`) | int | `Optional[int]` | UI más estricta (lotes de incubadora forzados a granja) — B-19 | `:23,121` |
| `house_id`, `genetic_line_id`, `breed_id`, `area_id` | `coerce.number` opcionales | int/`null` | `Optional[int]` | MATCH | `:24-28,122-129` |
| `planned_close_date`, `start_date` | `<input type=date>` | `'YYYY-MM-DD'`/`null` | `Optional[datetime]` | MATCH (vuelve como ISO completo → C#17) | `:127-130` |
| `sap_reference` | sí («Integración SAP») | str | **no existe** en `LotCreate` ni en `Lot` | **descartado en silencio** (B-18, patrón P0-14/R-47) | `:30,131`; `masters/models.py:278-320` |
| error | `toast.error(err.response.data.detail)` **crudo** | — | 422 lista | React #31 (B-15) | `:137` |
Veredicto **WRONG-FIELD** (B-18) + render (B-15 → **R-215**). Runtime: [L1] `BR-00-lote-ui: 201`, `HAT-00-lote-ui: 201`; mensajes zod fijos en español (`:21-23`, G-09).

### 3.2 `LotDetailPage` — acciones con cuerpo
| Acción | Payload UI | BE | MATCH | Evidencia |
|---|---|---|---|---|
| Cerrar lote | `POST /lots/{id}/close` sin cuerpo | `LotClosureSummary` | MATCH (error solo `console.error`, B-41 → R-192 AC04) | `LotDetailPage.tsx:107-119`; [L1] `BO-close-*: 400` sin feedback (`D01-bo-close-unapproved.png`) |
| Transición a producción | `{phase_code:'production', start_date, start_population_male, start_population_female}` | `LotPhaseCreate` exige **`lot_id`** y **`phase_id`** (`lots/schemas.py:98-109`); `phase_code` desconocido; router valida `lot_id == path` (`lots/router.py:143-145`) | **MISMATCH → 422 siempre**; `catch → console.error` | `LotDetailPage.tsx:121-138`; [RT] `R-09-transicion-ui: 422 lot_id/phase_id Field required, toasts:[]`; [L2] `BR2-transicion-ui: 422` → **R-191** (B-07) |
Veredicto **WRONG-FIELD** (transición).

### 3.3 `MasterListPage` (genérica; 20 entidades en `App.tsx:135-165`)
La pantalla renderiza **solo** las columnas de listado como `<Input>` de texto y envía `formValues: Record<string,string>` tal cual (`MasterListPage.tsx:87-103,193-200`); en edición rellena `item[key] ?? ''` (`:80`); `is_active` nunca se renderiza (B-36 → CF-63); `company_id` solo lo inyecta el servicio cuando el esquema lo declara opcional (`masters/service.py:227-235`).

| Entidad | Campos UI | Create exige | Alta desde UI | Edición desde UI | Veredicto | Evidencia |
|---|---|---|---|---|---|---|
| **farms** | name, code, location | `company_id: int` | **422** | ✔ | 422 | `masters/schemas.py:64-73` |
| **houses** | name, capacity | `farm_id: int`; `capacity Optional[int]` | **422** (`{}` real: [L1] `H4 → farm_id/name Field required` + `pageerror` React #31) | **422** si `capacity:''` (B-14) | 422 | `schemas.py:95-110`; `H04-masters-house-create.png` (en blanco) |
| **hatcheries** | name, code | `company_id: int` | **422** ([L1] `MAS-hatchery-create-ui: 422 company_id/name`, `req: {}`) | ✔ | 422 | `schemas.py:124-139` |
| **incubators** / **hatchers** | name, capacity | `hatchery_id: int`; `capacity` | **422** | **422** si en blanco | 422 | `schemas.py:149-173` |
| **productive-phases** | name, code, order | `order Optional[int]` | **422** si `order:''` | **422** si en blanco | 422 | `schemas.py:224-233` |
| companies, suppliers, areas, genetic-lines, breeds, feed-types, vaccines, mortality-causes, transports, processing-plants, medications, cull-causes, rejection-reasons, correction-types (14) | texto | opcionales / `company_id` inyectado | ✔ | ✔ | CORRECT | `schemas.py` (B §4) |
| (todas) | error | `setFormError(detail)` crudo → `<p>{formError}</p>` | React #31 en cualquier 422 lista (B-15) | | render | `MasterListPage.tsx:99,201-205` |

Nota de conteo: el informe B habla de «22 entidades / 16 CORRECT»; el recuento sobre `App.tsx:135-165` es **20 entidades: 14 CORRECT · 6 422** (las 22 corresponden a `register_crud` del backend, `masters/router.py:104-125`). Estas seis brechas (alta imposible por UI, `''` numérico, sin reactivación) son **R-196 (P1)**; el render roto es **R-215**. El campo `MAS-form-inputs: 2`/`MAS-form-fields: [null,null]` [L1] confirma que el modal de alta de `hatcheries` solo ofrece dos inputs sin `name`.

### 3.4 `WeightCurvesPage` ↔ `WeightCurveCreate` (`masters/schemas.py:575-609`)
`genetic_line_id`, `version_label`, `source`, `points[]` parseados de CSV en cliente (`weightCurves.ts:85-116`); celdas ilegibles → `NaN → null` → 422 lista no interpretada por fila (B-32, P3); `is_active` default; activar `PUT …/activate` sin cuerpo. Errores por fila (`detail.errores`) y `mensajeGeneral` seguro (`WeightCurvesPage.tsx:23-34,119-122`). **CORRECT** (referencia de buen manejo).

### 3.5 `UsersPage` ↔ `auth/schemas.py`
| Formulario | Payload UI | BE | MATCH | Evidencia |
|---|---|---|---|---|
| Crear | `{username, first_name, last_name, email, phone, role_id|null, area_id|null, company_id|null, view_type, is_active, password}` | `UserCreate`: `last_name min_length=1`, `EmailStr`, `password ≥8`; `company_id` resuelto en servidor (R-118) | `last_name` en blanco → 422 no prevenido; selector de empresa mostrado pero ignorado (B-28, P3) | `UsersPage.tsx:71,76-83`; `auth/schemas.py:27-41` |
| **Editar** | `PUT /users/{id}` con `{...datos}` = **incluye `username` y `company_id`** (`const { password, ...datos } = form`) | `UserUpdate` `extra="forbid"` **sin** `username` ni `company_id` (`auth/schemas.py:65-85`) | **MISMATCH → 422 «Extra inputs are not permitted» en toda edición**; `alert(detail)` → «[object Object]» (`:85`); el reset de contraseña posterior (`:80`) nunca se alcanza | `UsersPage.tsx:68-85` → **B-06 → R-195 (P1)**; [L1] `H3-users-edit-boton: no visible` (UNKNOWN) |
| Activar/desactivar | `PUT /users/{id} {is_active}` | ok | MATCH | `:91` |
| Reset contraseña | `POST /users/{id}/password {new_password}` | `PasswordChangeRequest` | MATCH | `:80`; `auth/schemas.py:44-62` |
Veredicto: crear CORRECT (P3) · **editar 422/RENDER** · toggle/reset CORRECT.

### 3.6 `RolesPage` — `{name, description, permissions:[{module, action, scope_type:'all'}]}`; desactivar `{is_active:false}` ↔ `RoleCreate`/`RoleUpdate`/`PermissionCreate` (`auth/schemas.py:149-172,201-205`) → **CORRECT** (`RolesPage.tsx:17-20,54-58,76-99`). Nota de seguridad: el backend no valida `permissions` contra el catálogo (R-199, entregable de seguridad). `alert()` genérico pierde el `detail` (C#30).

### 3.7 `ProfilePage` — `POST /users/{id}/password {current_password, new_password}` (≥8 en cliente) ↔ `PasswordChangeRequest` → MATCH; `setMessage(detail)` crudo (`ProfilePage.tsx:38,70`) → React #31 ante 422 estructurado (B-15 → R-215). **CORRECT** con render defectuoso.

### 3.8 `UnitAccessPage` / `UserBusinessUnitsButton` ↔ `business_units` — `GET /business-units`; `PATCH …/enable|disable` sin cuerpo; `GET …/grant-candidates` solo si `is_enabled` (evita 409); `POST /users/{id}/business-units {code}`; `DELETE …/{code}` → tipos exactos (`businessUnits.service.ts:10-73`; `business_units/schemas.py`) → **CORRECT** (contrato GA-FE-02). [L1] `OD23-grants-antes`.

### 3.9 Revisión / corrección / aprobación ↔ `review/schemas.py`, `corrections/schemas.py`
| Formulario | Payload UI | BE | MATCH | Id |
|---|---|---|---|---|
| `ReviewCenter` listado | `GET /review/pending?limit&offset&status&…&operator_id` | router acepta `farm_id, lot_id, event_type, date_from, date_to, limit, offset` (`review/router.py:22-33`); **`status` y `operator_id` no existen** | **WRONG-FIELD** (parámetros perdidos en silencio; B-13) — [RT] `R-12`, `R04-review-tabs.png` | **R-197** |
| `ReviewCenter` acciones | `POST /review/start/{id}`; `/review/complete {event_id}`; `/review/return {event_id, observations}` (prompt no vacío) | `observations min_length=10` (`review/schemas.py:98-107`) | MATCH salvo longitud (422 renderizable, B-29) | R-220 |
| `ReviewCenter` lote | `POST /review/batches {batch_name, event_ids}` | `ReviewBatchCreate` | MATCH | — |
| `ReviewDetail` | start/complete/return/approve/reject `{event_id, observations}` | return/reject `min_length=10` | MATCH salvo longitud (B-29) | R-220 |
| `ApprovalPanel` | approve `{event_id}`; reject `{event_id, observations≥10}`; batch `{event_ids[, observations]}`; `GET /approvals/pending?limit&offset&lot_id` | `ApproveRequest`, `RejectRequest`, `Batch*Request`; router `farm_id, lot_id, limit, offset` | MATCH ([RT] approve 200 ×2) | — |
| `CorrectionForm` | `POST /corrections {event_id, field_name:'observations', original_value, corrected_value, correction_type_id|null, reason≥5}` | `CorrectionCreate` (reason ≥5) | MATCH; UI limitada a `observations` frente a `campos_corregibles()` (`corrections/service.py:168-181`) (B-30) | R-220 |
| DTOs muertos `review.service.ts:46-47`, `approvals.service.ts:10,16` | `observations?` opcional | obligatorio ≥10 | stale DTO (informativo) | R-220 (C#34) |
Veredicto: listado **WRONG-FIELD**; acciones **CORRECT**.

### 3.10 SAP e informes
`SapManagerPage`: `GET /sap/references?limit=10`, `/sap/sync/jobs?limit=5`, `/sap/payloads?limit=5`, `/sap/connection-check`; `POST /sap/consolidate {}` / `POST /sap/export {}` ↔ cuerpos `Optional` → **CORRECT** de petición (`SapManagerPage.tsx:38-66`; `sap/router.py:30-42,49-61,92-103`); la lectura (`pending/draft/sent/error` vs `prepared/sending/confirmed/failed/retrying`) es defecto de respuesta → **R-217**. `sap.service.ts:34-35 importReferences` envía `{ref_type, entries}` frente a `SapReferenceImportRequest {references:[…]}` (`sap/schemas.py:45-47`) → **422 si se usara**; DTO muerto sin llamador de página (B-27; `useSap.ts:46-47`) — no existe formulario de importación de referencias (A §4). `ReportsPage` (`lot_id` por defecto 2), `LotReportPage`, `SapComparisonPage` → **CORRECT** de petición.

### 3.11 `TraceabilityTree` ↔ `EggBatchCreate` / `ChickBatchCreate` (`lots/schemas.py:209-248`)
`hatchery_lot_id` tecleado como número libre; `Number(x) || null` frente a `int` **requerido** (`:218-219`) → 422 si en blanco; `quantity_dispatched` `Number('') = 0` aceptado (B-17); `destination_lot_id || null` vs «uno obligatorio»; `setLinkError(detail)` crudo (`TraceabilityTree.tsx:95,114,347,389`) → React #31 (B-15). Veredicto **422/RENDER** (ambos modales) → **R-215**, R-220 (B-17).

### 3.12 Evidencias (`OperationDetailPage`) ↔ `POST /operations/{id}/evidences`
Multipart `file`, `description`, `evidence_type` ↔ `File(...)`, `Form("")`, `Form("")` (`OperationDetailPage.tsx:89-95`; `operations/router.py:344-366`); MIME y 10 MB coinciden; clases coinciden con `CLASES_DE_ADJUNTO` (`V:616-617`). **CORRECT** de petición; la respuesta del detalle descarta `evidences` (→ **R-198**, entregable de errores/estado).

---

## 4 · Familia F-01 / R-189 (§15) — reconciliación independiente

| Pregunta §15 | Hallazgo verificado |
|---|---|
| Id canónico | **R-189**; F-01 = alias de descubrimiento; F-01d y F-01e = extensiones del mismo hallazgo (`audit/ga-f01/GA_F01_RUNTIME_CERTIFICATION.md §2 D-01`; `GA_F01_DEDUP_RECONCILIATION.md §3`) |
| ¿Existe R-189? | Sí, en `audit/ga-f01/` (spec `R189_IMPORT_RECEPTION_FORM_CONTRACT_SPEC.md`, clarificaciones, plan, anexos F-01d/F-01e, certificación). **No figura** en `audit/remediation/REMEDIATION_BACKLOG.md` (deriva documental; `REMEDIATION_BACKLOG.md:2184`; registrada en el registro canónico §0) |
| Commits de implementación | `de79235` (C1 gobernanza) → `5992ddc` (C2: serializador, `sap_document_ref` = código, `getErrorMessage`) → `5dbb5d7` (C2c gobernanza F-01d) → `38d4647` (C2d: serializadores alimento/incubadora, escritura estricta 422, lectura tolerante, suite R-153 ejecutable) → `df8977c` (C2e gobernanza F-01e) → `91bd27a` (C2f: `derivedHouseId` de `bird_reception` cae a la 1.ª fila) → `c0b4afc` (C3 certificación) (`gitlog`) |
| Despliegue / generación vigente | Bundle servido `index-DDCcWL76.js` = C2f (`GA_F01_RUNTIME_CERTIFICATION.md:3-5`); [RT] `generacion-frontend: index-DDCcWL76.js` = build local de HEAD (`frontend/dist/assets/`) |
| Runtime E2E | Certificación C3: 35/35 asserts, 0 pageerror, 0×5xx; esta auditoría [RT]: import 124 → aprobación → `L-GP-2026-12` → recepción 125 → población exacta 50 (bracket 50/51) → devolver/reenviar/aprobar → 12 PASS · 1 FAIL (`R-11-aprobado` 403, causa no aislada) · 0 fatales · 0×5xx |
| Recertificación R-153 | Suite R-153 ejecutable desde C2d («11/11», commit `38d4647`); estado `CLOSED_FUNCTIONALLY_CERTIFIED` mantenido (`GA_F01_RUNTIME_CERTIFICATION.md:18`). Contexto GA-GOV-03: 25 fallos backend y 12 Playwright en HEAD por tests obsoletos (no de esta suite) |
| Retry GA-UAT-09 | ATTEMPT 1 = iniciado y bloqueado por F-01 (D-02); ATTEMPT 2 (retry) = 7/7 técnicos en verde (`c0b4afc`) |
| Aceptación del propietario | **PENDIENTE** (`GA_F01_RUNTIME_CERTIFICATION.md:17,107-108`: «Sin auto-aceptación») |
| Payload de almacenamiento de importación | `egg_storage_records: []` ([RT] `R-04`; [L1] `GP-01-payload-canonico {storage:[]}`) ✔ |
| Mapeo de la OC | Selector superior → **código** (`OFP:2008-2035`; [RT] `PO-C001-GPR-0001`) ✔ — **no propagado** a `bird_exit` interno (`OFP:917-927`) ni a `feed_movements.sap_order_id` (`OFP:1033-1040`) → **R-209** |
| Payload de recepción | `house_id` de la 1.ª fila si el lote no tiene galpón ([RT] `house_id:1`, lote `house:null`) ✔ — **no propagado** a los otros 9 tipos de `location_events` → **R-190** |
| Render de errores / React #31 | Asistente y consumidores de `getErrorMessage` ✔ ([RT] `fatal_react: 0`) — **no propagado** a maestros, lotes, trazabilidad, perfil, usuarios ([L1] `pageerror ×2`) → **R-215** |
| Importación / recepción por UI normal | Ambas alcanzables por hub/detalle de lote (`R01-import-form.png`; [RT] `R-04`) ✔ |

### 4.1 Hermanos de la misma clase de defecto que R-189 no resolvió (§15 «no asumir que una corrección cerró la familia»)
| Id | Clase F-01 | Formulario(s) | Qué queda | Evidencia |
|---|---|---|---|---|
| **R-190** (B-04) | selector value lost / optional-vs-required (`house_id`) | `bird_distribution`, `bird_transfer`, `bird_exit`, `egg_collection`, `egg_dispatch`, `transport_inspection`, `farm_inspection` (granja) | F-01e limitó la derivación a `bird_reception` (AC63-65 «demás tipos sin cambio») | [RT] 4 × 400 BR-08; `OFP:387-394` |
| **R-205** | campo requerido no renderizado (`received_total`…) | `bird_reception` reproductoras | Bloque de cuadre solo con `stage` del paso 1 | [L2] `BR2-01` 400 vs `BR2-02` 201 |
| **R-206** (B-11, B-26, B-37) | empty string (`''`) en fecha opcional / numéricos de `extra_data` / `''` persistido | `grandparent_import`, `bird_exit`, `egg_dispatch`, `transfer_to_hatcher`, `lot_closure`, `transport_inspection` (B-21) | `limpiarNumerosNoFinitos` solo cubre `NaN` | [L1]/[L2] `quarantine_end_date: ""` → 400 |
| **R-209** (B-09, B-10) | ID instead of code | `bird_exit` (selector interno), `feed_registration.sap_order_id` | F-01 §2 corrigió solo el bloque compartido | `OFP:917-927,1033-1040` |
| **R-210** (B-12) | unit mismatch (`step=0.001`, fallbacks «kg») | pesaje, traslado, salida, importación, cierre | Etiqueta i18n «(g)» correcta; restos «kg» y paso milesimal; **severidad a reevaluar** | `OFP:470,1703`; `translation.json` |
| **R-211** (B-16) | BE rule vs UI structure (BR-17 Σ contra un galpón) | `bird_reception`, `bird_distribution` | F-01e deriva un único `house_id` | `SVC:897-902`; `V:712-725` |
| **R-194** (B-01, B-02, B-03, B-05, B-22, B-33) | optional-vs-required (`farm_id`, `arrival_date`), wrong nested structure (`egg_storage_records` vs `egg_movements`), validation silently blocking (`dosage_per_bird` sin `valueAsNumber`), BE field never populated (`hatchery_id`) | `egg_reception_hatchery`, `incubation_load`, `birth_registration`, `chick_dispatch`, `hatchery_inspection` | F-01b solo documentó `arrival_date` | [L2] `HAT2-02/02b/04/07/08` |
| **R-196** (B-08, B-14, B-36) | `{}` / campos padre no capturados / `''` numérico / `is_active` | 6 maestros estructurales | Misma clase que F-01 (`[{}]`/`{}`) en otra pantalla | [L1] `{}` → 422 ×2 |
| **R-195** (B-06) | wrong property / stale DTO (`username`, `company_id` con `extra="forbid"`) | edición de usuario | — | `UsersPage.tsx:68-85` |
| **R-215** (B-15) | render de `detail` estructurado (React #31) | maestros, lotes, trazabilidad, perfil, usuarios | R-189 §3 solo cubrió el asistente | [L1] `pageerror ×2`, `H04.png` |
| **R-191** (B-07) | wrong property name / missing required (`phase_code`; sin `lot_id`/`phase_id`) | transición de fase | — | [RT] `R-09` 422 |

---

## 5 · Resumen

### 5.1 Por formulario (mi recuento explícito, reproducible)
| Grupo | Superficies | CORRECT | MALFORMED-DEFAULT | WRONG-FIELD | 422/RENDER |
|---|---|---|---|---|---|
| Asistente (26 tipos) | 26 | 15 (`bird_reception`, `water_consumption`, `mortality_recording`, `cull_recording`, `vaccination`, `medication`, `farm_inspection`, `hatchery_inspection`, `egg_collection`, `egg_classification` n/a, `egg_reception_classification`, `egg_dispatch`, `incubation_load`, `transfer_to_hatcher`, `lot_closure`) | 1 (`transport_inspection`) | 7 (`bird_distribution`, `bird_transfer`, `bird_exit`, `feed_registration`, `weight_recording`*, `ovoscopy`, `chick_dispatch`) | 3 (`egg_reception_hatchery`, `birth_registration`, `grandparent_import`) |
| Lotes (alta, cierre, transición) | 3 | 1 | 0 | 2 (`LotFormPage` B-18; transición B-07) | 0 |
| Maestros (20 entidades) | 20 | 14 | 0 | 0 | 6 |
| Curvas de peso | 1 | 1 | 0 | 0 | 0 |
| Usuarios (crear, editar, toggle, reset) | 4 | 3 | 0 | 0 | 1 (editar) |
| Roles · Perfil · Unidades | 3 | 3 | 0 | 0 | 0 |
| Revisión (listado, acciones), detalle de revisión, aprobaciones, corrección | 5 | 4 | 0 | 1 (listado B-13) | 0 |
| SAP (manager, importReferences muerto) · Reportes (3) | 5 | 5 | 0 | 0 | 0 |
| Trazabilidad (huevos, pollitos) | 2 | 0 | 0 | 0 | 2 |
| Evidencias | 1 | 1 | 0 | 0 | 0 |
| **Total** | **70** | **47** | **1** | **10** | **12** |

\* `weight_recording` se mantiene en WRONG-FIELD por herencia del informe B (unidad); con la etiqueta i18n verificada «(g)» el defecto se reduce a `step`/fallbacks y la fila es candidata a CORRECT con P3 si el propietario confirma la unidad de captura.

**FORMULARIOS AUDITADOS: 70 · CORRECTOS: 47 · DEFECTOS DE DEFAULT MALFORMADO (por formulario): 1 · MAPEOS ERRÓNEOS (por formulario): 10 · DEFECTOS 422/RENDER (por formulario): 12.**

### 5.2 Por defecto (registro B-01…B-41, 41 defectos)
Malformed default / cadena vacía: **5** (B-11, B-14, B-21, B-26, B-37) · Wrong-field mappings: **14** (B-01, B-02, B-04, B-06, B-07, B-09, B-10, B-12, B-13, B-18, B-20, B-22, B-27, B-33) · 422/render: **9** (B-03, B-05, B-08, B-15, B-17, B-28, B-29, B-32, B-35) · regla/semántica/hardening/informativos: **13** (B-16, B-19, B-23, B-24, B-25, B-30, B-31, B-34, B-36, B-38, B-39, B-40, B-41).

### 5.3 Bloqueantes (ids del registro canónico) — **10**
P1: **R-190**, **R-191**, **R-194**, **R-195**, **R-196**, **R-205** · P2 bloqueantes: **R-209**, **R-210** (severidad a reevaluar), **R-211**, **R-215**. No bloqueantes: R-206, R-220 (B-17…B-41 residuales). Conocido/referencia: R-146 (B-23).

### 5.4 UNKNOWN
- `birth_registration` con dosis rellena bloqueado en cliente ([L2] `HAT2-07b: NO_REQUEST`): causa no aislada.
- `bird_transfer`, `transport_inspection`, `lot_closure`, `feed_registration.sap_order_id` (selección de orden), `bird_exit` con OC interna: no ejercitados en runtime; veredicto por código.
- R-211 (dos galpones en una recepción): no ejercitado.
