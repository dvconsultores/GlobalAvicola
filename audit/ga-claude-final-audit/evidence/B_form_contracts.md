# Auditoría B · Paridad de contrato de petición (formularios UI ↔ API)

Fecha: 2026-09-13 · Repositorio: `/home/maria/Proyectos/GlobalAvicola` · Modo: solo lectura (análisis estático del código; sin ejecutar pruebas ni runtime).
Contexto: `R-189` (F-01/F-01d/F-01e) corrigió el asistente de operaciones **solo para importación/recepción**. Esta auditoría recorre los 26 tipos de evento y los demás formularios buscando las mismas clases de defecto.

Convención de líneas: `OFP` = `frontend/src/pages/operations/OperationFormPage.tsx`; `V` = `backend/app/operations/validators.py`; `S` = `backend/app/operations/schemas.py`; `SVC` = `backend/app/operations/service.py`; `M` = `backend/app/operations/models.py`.

---

## 0. Comportamientos globales que condicionan todo lo demás

| Pieza | Comportamiento | Evidencia | Consecuencia |
|---|---|---|---|
| `api.ts` (axios) | Sin `transformRequest`, sin serialización de fechas, sin limpieza de `undefined`/`''`. `JSON.stringify` descarta `undefined`, conserva `null` y `''`, y convierte **`NaN → null`**. Params: serializador por defecto de axios. | `frontend/src/services/api.ts:3-6` | Todo `''` de un `<input>` registrado sin `valueAsNumber` **viaja** al backend; todo `NaN` no limpiado viajaría como `null`. |
| `SearchSelect` | `onChange(String(item.id))` siempre; `value` se compara por `String(x.id)`. | `frontend/src/components/ui/SearchSelect.tsx:89-93, 103-104, 159` | Cualquier `setValue(campo, v)` sin mapear id→código escribe el **id** del catálogo. |
| `getErrorMessage` | Normaliza `detail` (lista/objeto de FastAPI) a texto renderizable. **Solo** lo usan el asistente, detalle de operación, revisión/aprobaciones, informes y SAP. | `frontend/src/components/Toast.tsx:95-140` | Los formularios que renderizan `err.response.data.detail` crudo reproducen React #31 en cualquier 422 (ver B-15). |
| Zod preprocess del asistente | `limpiarNumerosNoFinitos` convierte `NaN → undefined` (números) recursivamente; **no toca cadenas `''`**. | `OFP:189-207` | Un `<input type=number>` registrado **sin** `valueAsNumber` entrega `''` → `z.number()` rechaza → bloqueo silencioso (B-05); un `''` en `extra_data` (`z.any`) viaja tal cual (B-11). |
| Serializadores `R-189` | Filas de aves/alimento/incubadora/almacenamiento sin contenido ⇒ descartadas; `[{}]` de arranque nunca viaja. `week_number`/`sex` no cuentan como contenido. | `frontend/src/pages/operations/operationPayload.ts:14-70` | Correcto para el defecto original; efecto colateral: la ovoscopía pierde el «día» (B-20). `inspection_details` **no** se serializa (B-21). |
| `defaultValues` | `bird_movements: [{sex:'male'},{sex:'female'}]`, `feed_movements: [{}]`, `hatchery_params: [{}]`, `egg_storage_records: [{}]`. | `OFP:256-267` | Cubiertos por los serializadores (`OFP:429-449`). |
| Derivación de ubicación | `farm_id = data.farm_id ?? (!isHatcheryStage ? derivedFarmId : undefined)`; `house_id = data.house_id ?? derivedHouseId` (lote, o 1.ª fila solo en `bird_reception`/`farm_inspection`). `data.farm_id`/`data.house_id` **nunca se registran** en la UI. | `OFP:386-394, 438-439`; `HATCHERY_EVENTS` `OFP:274-278` | `BR-08` (`V:822-840`) exige granja **y** galpón en 10 tipos; la UI no puede satisfacerlo en varios (B-01, B-04). |
| Edición | Ninguna pantalla llama a `PUT /operations/{id}` (`operationsService.update` sin uso). | grep `api.put(\`/operations` = 0 resultados; `frontend/src/services/operations.service.ts:40-41` | `OperationalEventUpdate` (`S:195-253`, R-34) es inalcanzable desde la UI (B-31). |

---

## 1. Asistente de operaciones — campos comunes (aplican a los 26 tipos)

| Field | UI renders? | UI default | UI validation | Payload value/shape | BE schema type/required | BE validator requirement | MATCH | Defect class | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| `event_type` | sí (paso 2) | `prefillType \|\| ''` | `min(1)` | string enum | `str` req.; `EventType(...)` | — | MATCH | — | `OFP:89, 259, 320`; `SVC:222` |
| `event_date` | sí | hoy `YYYY-MM-DD` | `min(1)` | `'YYYY-MM-DD'` | `date` (default hoy) | BR-06/BR-19 | MATCH | — | `OFP:90, 257, 2098`; `S:140`; `V:488-499, 794-819` |
| `lot_id` | sí (salvo inspecciones) | `prefillLotId` | superRefine salvo `LOT_OPTIONAL_EVENTS` | `number` | `Optional[int]` | `LOT_OPTIONAL_EVENTS` idéntico (`farm_inspection`, `hatchery_inspection`, `grandparent_import`) | MATCH | — | `OFP:29-40, 178-187, 2079-2087`; `SVC:61-68, 828-830` |
| `farm_id` | **no** (derivado) | — | — | `derivedFarmId` o `undefined` en etapa incubadora | `Optional[int]` | BR-08 obligatorio en 10 tipos (`V:828-835`) | **MISMATCH** en `egg_reception_hatchery`, `chick_dispatch` | optional-vs-required / derivación errónea | `OFP:386, 438`; `V:828-836` → **B-01** |
| `house_id` | **no** (derivado) | — | — | `lot.house_id` (o 1.ª fila en recepción/inspección) | `Optional[int]` | BR-08 galpón obligatorio en 10 tipos | **MISMATCH** para lotes sin galpón | selector value lost | `OFP:387-394, 439`; `V:836-839` → **B-04** |
| `sap_document_ref` | sí (6 tipos, selector superior) | — | `string().optional()` | **código** (`identificadorDeOrdenSap`) | `Optional[str]` | BR-10/BR-18/BR-22 por `sap_code` | MATCH (selector superior) / **MISMATCH** selector interno de `bird_exit` | ID instead of code | `OFP:1936-2039` OK; `OFP:917-927` KO → **B-09** |
| `observations` | sí | `''` | opcional | `''` o texto | `Optional[str]` | — | MATCH (`''` persistido, no `null`) | hygiene | `OFP:425, 440, 2109` |
| `idempotency_key` | **no** | — | — | ausente | `Optional[str]` | dedupe si viene | MISMATCH (nunca poblado) | BE field never populated | `S:167`; `SVC:224-234`; **R-146** (conocido) |
| `event_time` | no | — | — | ausente | no está en `Create` | — | n/a (columna sin contrato) | — | `M:94` |
| `extra_data` | por tipo | — | `record(any)` | objeto con **cadenas** en numéricos sin `valueAsNumber` | `Optional[dict]` | solo `import_plan` tipado (BR-22) | MATCH salvo tipos | string/int mismatch | → **B-11**, **B-26** |
| `evidence` | no en el alta (en detalle) | — | — | multipart `file`, `description`, `evidence_type` | `File(...)`, `Form("")`, `Form("")` | clases cerradas; 10 MB; MIME | MATCH | — | `OperationDetailPage.tsx:20-21, 89-95`; `operations/router.py:344-366` |

---

## 2. Tablas por tipo de evento (26)

Solo se listan los campos que la UI renderiza para ese tipo más los que el backend exige y la UI no cubre.

### 2.1 `bird_reception` (corregido por R-189; se verifica cierre)
| Field | UI | Default | Validación UI | Payload | BE | Validador | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|---|---|
| `sap_document_ref` / `extra_data.sap_order_ref` | selector superior (compra o transferencia) | — | — | código | `Optional[str]` | BR-18 acumulado por `sap_code` | MATCH | — | `OFP:1972-1999, 2008-2035`; `V:753-791` |
| `received_total`,`dead_on_arrival`,`rejected_on_arrival`,`sample_size` | solo etapa `breeder_rearing` | — | int ≥1/≥0 | números o ausentes | `Optional[int]` | BR-20 los exige en breeder; los prohíbe en otras cadenas | MATCH | — | `OFP:666-697`; `V:536-574` |
| `supplier_id`, `bird_movements.0.breed_id` | SearchSelect → `Number(v)` | — | — | int | `Optional[int]` | tenencia (R-179) | MATCH | — | `OFP:703-722` |
| `bird_movements[i]` `{target_house_id, sex, quantity, avg_weight(g)}` | por galpón | 2 filas M/F | `quantity ≥ 0` | filas con `quantity>0`, `week_number: 0` forzado | `BirdMovementSchema` | BR-17 capacidad con **Σ total contra `house_id` del evento** | MATCH contrato · **MISMATCH regla** | BE rule vs UI structure | `OFP:725-772, 429-434, 441`; `SVC:900-902`; `V:712-725` → **B-16** |
| `house_id` | derivado: lote ⇒ 1.ª fila con `target_house_id` | — | — | int | `Optional[int]` | BR-08 | MATCH (F-01e) | — | `OFP:392-393` |
| `feed_movements`/`hatchery_params`/`egg_storage_records` | no | `[{}]` | — | `[]` | listas | escritura estricta (F-01d) | MATCH | — | `OFP:444-449`; `S:75-82, 112-119` |
**Veredicto: CORRECT** (contrato) — queda B-16 como discrepancia de regla.

### 2.2 `bird_distribution`
| Field | UI | Default | Val. UI | Payload | BE | Validador | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|---|---|
| `bird_movements[i].source_house_id/target_house_id` | SearchSelect por fila | — | — | int | `Optional[int]` | tenencia estructural (R-180) | MATCH | — | `OFP:792-810`; `SVC:863-867` |
| `bird_movements[i].sex/quantity/avg_weight` | sí | M/F + «Mixto» al añadir | ≥0 | filas `quantity>0` | ok | BR-17 Σ contra `house_id` evento | MATCH | — | `OFP:814-828` |
| `house_id` | **no** derivado de filas (solo `lot.house_id`) | — | — | `undefined` si el lote no tiene galpón | `Optional[int]` | **BR-08 galpón obligatorio** | **MISMATCH** | selector value lost (clase F-01e) | `OFP:394`; `V:829-839`; frontera declarada en `audit/ga-f01/GA_F01E_SUBSANACION_ANNEX.md:40` → **B-04** |
**Veredicto: WRONG-FIELD** (para lotes sin galpón: 400 BR-08 «requiere un galpón asignado»).

### 2.3 `bird_transfer`
| Field | UI | Payload | BE | Validador | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|
| `bird_movements.0.source_house_id/target_house_id` | SearchSelect | int | ok | tenencia | MATCH | — | `OFP:844-862` |
| `bird_movements` M/F con `avg_weight` etiqueta **«(kg)»** step 0.001 | `renderMFRows(true)` | float | `avg_weight` float (**gramos** en el sistema) | curva en gramos | **MISMATCH unidad** | unit mismatch | `OFP:470, 484, 865`; `audit/remediation/GA_REM_021_B02_WEIGHT_RANGE_MATRIX.md:19,45`; `OperationDetailPage.tsx:221` → **B-12** |
| `house_id` | derivado de lote | — | BR-08 galpón obligatorio | **MISMATCH** lotes sin galpón | | | → **B-04** |
**Veredicto: WRONG-FIELD.**

### 2.4 `bird_exit`
| Field | UI | Payload | BE | Validador | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|
| `destination_farm_id`, `destination_plant_id`, `transport_id` | SearchSelect → `Number(v)` | int | `Optional[int]` | tenencia | MATCH | — | `OFP:879-908` |
| `sap_document_ref` (selector **interno** «Ref. OC SAP») | `setValue('sap_document_ref', v)` con `v = String(o.id)` | **id** del `SapReference` | `Optional[str]` | BR-10 unicidad, comparativo SAP por `sap_code` | **MISMATCH** | ID instead of code (misma clase que F-01, no corregida aquí) | `OFP:917-927` vs selector superior correcto `OFP:2008-2035`; `V:471-474, 758` → **B-09** |
| `extra_data.transport_*` | inputs number **sin** `valueAsNumber` | `"22"` cadenas | `dict` | — | MATCH (tipos degradados) | string/int | `OFP:938-973` → **B-26** |
| `bird_movements` M/F (kg) | `renderMFRows(true)` | float | — | BR-01 salida ≤ saldo | MATCH · unidad **MISMATCH** | unit | `OFP:987` → **B-12** |
| `house_id` | lote | — | BR-08 | **MISMATCH** sin galpón | | | → **B-04** |
**Veredicto: WRONG-FIELD.**

### 2.5 `feed_registration`
| Field | UI | Payload | BE | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|
| `feed_movements.0.feed_type_id` | `<select>` `valueAsNumber` | int / ausente | `Optional[int]` + tenencia | MATCH | — | `OFP:1015`; `SVC:857-858` |
| `feed_movements.0.week_number/quantity_kg/sacks_count` | `valueAsNumber` | números | `quantity_kg > 0` (F-01d) | MATCH (fila sin cantidad ⇒ descartada) | — | `OFP:1019-1029`; `S:75-82` |
| `feed_movements.0.sap_order_id` | SearchSelect `setValue(..., v \|\| undefined)` | **`String(id)`** | `Optional[str]` «orden de transferencia SAP» | **MISMATCH** | ID instead of code | `OFP:1033-1040`; `M:225` → **B-10** |
| `extra_data.feed_phase` | select | string | dict | MATCH | — | `OFP:1005-1011` |
**Veredicto: WRONG-FIELD.**

### 2.6 `water_consumption`
| Field | UI | Payload | BE | Validador | MATCH | Evidencia |
|---|---|---|---|---|---|---|
| `water_liters` | `valueAsNumber`, `min 0.1` | float | `Optional[float]` | B05/RR-11: obligatorio, >0, cadena breeder/broiler | MATCH (catálogo solo lo ofrece en esas etapas) | `OFP:109, 995`; `V:670-689`; `processCatalog.ts:216-237` |
| — | — | — | `ALL_EVENT_TYPES` **no lo lista** | — | MISMATCH informativo | `S:312-338` → **B-24** |
**Veredicto: CORRECT.**

### 2.7 `weight_recording`
| Field | UI | Payload | BE | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|
| `sample_size` | `valueAsNumber` | int | `Optional[int]` | MATCH | — | `OFP:624` |
| `bird_movements.0.week_number` | solo fila 0 | se pierde si la fila «machos» va con `quantity` 0 | — | MATCH parcial | data loss | `OFP:620, 441` → **B-38** |
| `bird_movements[M/F].avg_weight` | etiqueta **«Peso prom. (kg)»** step 0.001 | float | evaluación de curva en **gramos** (`GA-REM-037`) | **MISMATCH unidad** | unit mismatch | `OFP:470, 484, 627`; B02 matrix `:19,:45` → **B-12** |
**Veredicto: WRONG-FIELD** (unidad).

### 2.8 `mortality_recording` · 2.9 `cull_recording`
| Field | UI | Payload | BE | Validador | MATCH | Evidencia |
|---|---|---|---|---|---|---|
| `cause_id` / `cull_cause_id` | SearchSelect → `Number(v)` | int | `Optional[int]` | tenencia (R-179) | MATCH | `OFP:509-516, 532-539`; `SVC:851-856` |
| `bird_movements.0.week_number` + M/F `quantity` | `valueAsNumber` | filas `quantity>0` | ok | BR-01 (Σ>0, ≤ saldo) | MATCH | `OFP:520, 523, 543, 546`; `SVC:931-946` |
**Veredicto: CORRECT** (ambos).

### 2.10 `vaccination` · 2.11 `medication`
| Field | UI | Payload | BE | MATCH | Evidencia |
|---|---|---|---|---|---|
| `vaccine_id`/`medication_id` | SearchSelect → `Number` | int | `Optional[int]` | MATCH | `OFP:555-562, 593-600` |
| `vaccination_route` | select `spray/water/injection/eye/gel` | string (`''` si no elige) | `String(50)` libre | MATCH (sin enum BE) | `OFP:566-573`; `M:116` |
| `vaccine_lot_number`, `dosage_per_bird` (valueAsNumber), `treatment_days` | sí | ok | ok | MATCH | `OFP:577-581, 604-608` |
| `bird_movements` M/F sin peso | `renderMFRows(false)` | filas `quantity>0` | sin regla | MATCH | `OFP:584, 611` |
**Veredicto: CORRECT** (ambos).

### 2.12 `farm_inspection` (lote opcional)
| Field | UI | Payload | BE | Validador | MATCH | Evidencia |
|---|---|---|---|---|---|---|
| `house_inspections[i]` (UI-only) → `inspection_details` `{house_id, parameter, value\|status}` | por galpón: T°, H%, cama, notas, equipos | filas solo con datos | `InspectionDetailSchema` | tenencia `house_id` | MATCH | `OFP:396-421, 448, 1249-1347`; `SVC:868-869` |
| `value_numeric` | no | ausente (T°/H% viajan como `value` string) | `Optional[float]` | — | BE field never populated | `OFP:400-402`; `S:127` → **B-21b** |
| `farm_id`/`house_id` | `selectedFarmId` / 1.ª fila con galpón | int | BR-08 exige ambos («al menos un galpón») | MATCH (si el usuario elige granja/lote y galpón) | `OFP:386-388`; `V:836-838` |
**Veredicto: CORRECT.**

### 2.13 `transport_inspection`
| Field | UI | Payload | BE | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|
| `transport_id` | SearchSelect | int | ok | MATCH | — | `OFP:1365-1372` |
| `inspection_details[0..5]` `{parameter, value \| status}` | 6 filas fijas (hidden `parameter`) | **siempre 6 filas**, con `value: ''` o `status: ''` si el usuario no las rellena (no hay serializador de cadenas) | `parameter: str` req.; `value/status Optional[str]` | MATCH esquema · **filas vacías persistidas** | malformed default (clase F-01d para cadenas) | `OFP:1374-1391, 448`; `operationPayload.ts` no cubre `inspection_details` → **B-21** |
| numéricos (`density`, `temperature`, `duration_min`) | `<input type=number>` sin `valueAsNumber` → `value` | `"1.5"` | `value` str; `value_numeric` nunca | MATCH degradado | BE field never populated | `OFP:1379`; `S:127` |
| `farm_id`/`house_id` | lote | — | BR-08 exige ambos | **MISMATCH** lotes sin galpón | | → **B-04** |
**Veredicto: MALFORMED-DEFAULT.**

### 2.14 `hatchery_inspection` (sin lote, sin granja)
| Field | UI | Payload | BE | MATCH | Evidencia |
|---|---|---|---|---|---|
| `hatchery_params[i]` `{incubator_id \| hatcher_id, temperature, humidity, co2}` (`machine_type` UI-only) | por máquina | filas con contenido; `machine_type` eliminado | `HatcheryParamsCreateSchema` (≥1 campo) | MATCH | `OFP:330-334, 445-447, 1399-1476` |
| `hatchery_id` | selector «Incubadora» = estado local `selectedHatcheryId` | **nunca viaja** (zod no lo declara) | `Optional[int]` + tenencia | BE field never populated | `OFP:139-149, 2044-2056`; `S:101`; `SVC:873-877` → **B-22** |
| `lot_id` | limpiado por efecto | ausente | opcional | MATCH | `OFP:336-340`; BR-08 exento `V:825-826` |
**Veredicto: CORRECT** (con B-22 P3).

### 2.15 `egg_collection`
| Field | UI | Payload | BE | Validador | MATCH | Evidencia |
|---|---|---|---|---|---|---|
| `egg_movements[i]` `{egg_type ∈ fertile,dirty,broken,infertile,discarded; quantity}` | hidden `egg_type` + cantidad | filas `quantity>0` | `egg_type: str` (sin enum BE) | saldo cuenta solo `fertile` (R-172) | MATCH | `OFP:1049-1071, 442`; `V:91-104` |
| `egg_movements.0.avg_weight` | solo fila 0 (`fertile`) | se pierde si fértiles = 0 | `Optional[float]` | — | data loss menor | `OFP:1076` → **B-39** |
| `house_id` | lote | — | BR-08 | **MISMATCH** sin galpón | → **B-04** |
**Veredicto: CORRECT** (contrato).

### 2.16 `egg_classification`
No aparece en ningún `STAGE_OPERATIONS` (`processCatalog.ts:205-238`) → **inalcanzable** desde la UI aunque el `switch` lo contemple (`OFP:1047`). **Veredicto: CORRECT (n/a)** → **B-25** (P3 informativo).

### 2.17 `egg_reception_classification`
Mismo bloque que 2.15 sin `avg_weight`; etapa incubadora ⇒ `farm_id` `undefined`, pero **no** está en `location_events` → sin BR-08. `egg_type` con 5 categorías de granja (no de recepción) — sin enum en BE. **Veredicto: CORRECT.**

### 2.18 `egg_dispatch`
| Field | UI | Payload | BE | Validador | MATCH | Evidencia |
|---|---|---|---|---|---|---|
| `sap_document_ref` (orden de traslado, selector superior) | código | `Optional[str]` | BR-10 unicidad lote+tipo | MATCH | `OFP:2004-2035`; `SVC:890-895` |
| `hatchery_params.0.incubator_id` («Incubadora destino») | SearchSelect | fila `HatcheryParams` en un evento de despacho | acepta (≥1 campo) | MATCH esquema · uso semántico dudoso | `OFP:1093-1100` → **B-33** |
| `transport_id` + `extra_data.transport_*` | sí | int + cadenas | ok | MATCH | `OFP:1104-1157` → B-26 |
| `egg_movements[fertile]` | única fila | `quantity>0` | BR-02 solo fértil (R-172) | MATCH (test `eggDispatchFormContract.test.ts`) | `OFP:1169-1181` |
| `farm_id`/`house_id` | lote | — | BR-08 exige ambos | **MISMATCH** sin galpón | → **B-04** |
**Veredicto: CORRECT** (contrato; B-04 condicional).

### 2.19 `egg_reception_hatchery` — **cadena de incubadora bloqueada por tres defectos**
| Field | UI | Payload | BE | Validador | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|
| `farm_id` | no (etapa incubadora ⇒ `undefined`) | ausente | `Optional[int]` | **BR-08 exige granja** (`egg_reception_hatchery` ∈ `location_events`) | **MISMATCH** → 400 siempre | optional-vs-required | `OFP:274-278, 438`; `V:828-835` → **B-01** |
| `house_id` | lote | `lot.house_id` | — | BR-08 exige galpón | MISMATCH si el lote de incubadora no tiene galpón | | `OFP:394` → B-04 |
| «Huevos recibidos» → `egg_storage_records.0.eggs_received` | sí | fila de almacenamiento | `EggStorageSchema.eggs_received` | **el saldo de incubadora lee `egg_movements[egg_type='fertile'].quantity`** | **MISMATCH** → `incubation_load` siempre BR-03 «disponibles (0)» | wrong nested structure | `OFP:1219`; `V:149-175, 156-164`; `SVC:956-960` → **B-02** |
| `egg_storage_records.0.arrival_date` | **no se captura** (zod tampoco) | ausente | `arrival_date: date` **requerido** | — | **MISMATCH** → 422 en cuanto se rellena cualquier campo de almacenamiento | optional-vs-required (**F-01b**) | `OFP:170-177, 1218-1236`; `S:87`; `audit/ga-f01/GA_F01_EGG_STORAGE_CONTRACT.md:30` → **B-03** |
| `egg_storage_records.0.transport_temp_c/transport_duration_min/storage_temp_c/storage_humidity_pct` | `valueAsNumber` | números | ok | — | MATCH | | `OFP:1223-1235` |
| `egg_storage_records.lot_id` | — | heredado del evento | `Optional[int]` en esquema, **NOT NULL** en modelo | — | MATCH vía UI (lote obligatorio); 500 solo por API sin lote (**F-01c**) | BE hardening | `SVC:281-284`; `M:273` → **B-40** |
| `extra_data.source_farm_id`, `extra_data.dispatch_order`, `transport_id` | sí | int/str | dict/`Optional[int]` | — | MATCH | | `OFP:1193-1215` |
| `egg_movements` | **no se renderiza** | `[]` | — | entrada de saldo BR-03 | ver B-02 | | |
**Veredicto: 422/RENDER** (B-03) + WRONG-FIELD (B-01, B-02).

### 2.20 `incubation_load`
| Field | UI | Payload | BE | Validador | MATCH | Evidencia |
|---|---|---|---|---|---|---|
| `hatchery_params.0` `{incubator_id, quantity_loaded, temperature, humidity, co2, turning}` | sí (`turning` checkbox → boolean) | fila con contenido | `HatcheryParamsCreateSchema` | BR-03 Σ `quantity_loaded` ≤ saldo incubadora | MATCH contrato · **bloqueado aguas arriba por B-02** | `OFP:1485-1513`; `SVC:956-960` |
**Veredicto: CORRECT** (contrato).

### 2.21 `ovoscopy`
| Field | UI | Payload | BE | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|
| «Día de ovoscopía» → `bird_movements.0.week_number` + hidden `sex='mixed'` | sí | fila `{sex:'mixed', week_number:n}` → **descartada** por `serializarMovimientosDeAves` (sin campo de contenido) y, antes de R-189, por `quantity>0` | — | **MISMATCH** → el día nunca se persiste | selector value lost / UI field without BE home | `OFP:1531-1532`; `operationPayload.ts:18-20, 40-43, 47-49`; `OFP:441` → **B-20** |
| `egg_movements[fertile, infertile, dead_early, dead_late, contaminated]` | sí | filas `quantity>0` | `egg_type` libre | MATCH (dominio pendiente **R-177** / AOD-24) | enum drift conocido | `OFP:1520-1543`; `REMEDIATION_BACKLOG.md:1295` |
**Veredicto: WRONG-FIELD.**

### 2.22 `transfer_to_hatcher`
`hatchery_params.0.{hatcher_id, quantity_transferred, temperature, humidity}` (`OFP:1554-1578`) → MATCH; `extra_data.incubation_day` sin `valueAsNumber` → `"18"` (B-26). **Veredicto: CORRECT.**

### 2.23 `birth_registration`
| Field | UI | Payload | BE | Validador | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|
| `bird_movements[male,female,mixed].quantity` | 3 filas hidden `sex` | filas `quantity>0` | ok | BR-21: 1 fila por sexo, `mixed` excluyente, Σ≥1 | MATCH (UI no impide mixed+sexadas → 400 legítimo) | UX | `OFP:1586-1605`; `V:593-602` → **B-35** |
| `chicks_healthy`, `chicks_weak` | `valueAsNumber`, **no obligatorios** en UI | int / ausente | `Optional[int] ≥0` | **obligatorios** en cadena hatchery (BR-21) | MISMATCH (400 si en blanco) | optional-vs-required | `OFP:1610-1614`; `V:607-610` → **B-35** |
| `vaccine_id`, `vaccination_route`, `vaccine_lot_number` | sí | ok | ok | — | MATCH | | `OFP:1625-1647` |
| `dosage_per_bird` | `register('dosage_per_bird')` **sin `valueAsNumber`** | `''` (o `"0.2"`) → `z.number().optional()` **rechaza** → `handleSubmit` no llama a `onSubmit`; no se renderiza `errors.dosage_per_bird` | `Optional[float]` | — | **MISMATCH → envío bloqueado en silencio** | validation silently blocking submit | `OFP:1651` vs `OFP:103, 189-207` (solo limpia `NaN`); compárese `OFP:581` (vacunación, correcto) → **B-05** |
**Veredicto: 422/RENDER** (bloqueo de validación cliente). *Inferencia estática; requiere confirmación runtime (la certificación R-189 no ejecutó este tipo).*

### 2.24 `chick_dispatch`
| Field | UI | Payload | BE | Validador | MATCH | Evidencia |
|---|---|---|---|---|---|---|
| `destination_farm_id`, `transport_id`, `extra_data.sanitary_cert` | sí | int/str | ok | tenencia | MATCH | `OFP:1665-1687` |
| `bird_movements` M/F | `renderMFRows(false)` | filas `quantity>0` | BR-04 Σ>0 ≤ viables | MATCH | `OFP:1690`; `SVC:961-966` |
| `farm_id` | no (etapa incubadora ⇒ `undefined`) | ausente | `Optional[int]` | **BR-08 exige granja y galpón** (`chick_dispatch` ∈ `location_events`) | **MISMATCH → 400 siempre** | `OFP:274-278, 438`; `V:831-836` → **B-01** |
**Veredicto: WRONG-FIELD.**

### 2.25 `lot_closure`
`bird_movements.0 {sex:'mixed', quantity, avg_weight «(kg)»}` + `extra_data.fcr/mortality_pct` como cadenas (`OFP:1698-1712`). BE: solo BR-05 (`SVC:967-970`); **no cierra el lote** (eso lo hace `POST /lots/{id}/close`, `lots/router.py:80-92`, usado por `LotDetailPage.tsx:111`). Contrato MATCH; duplicidad semántica → **B-34** (P3); unidad → B-12. **Veredicto: CORRECT.**

### 2.26 `grandparent_import` (R-152/R-153; corregido por R-189 F-01)
| Field | UI | Payload | BE | Validador | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|
| `sap_document_ref` | selector superior → código | str | `Optional[str]` | BR-22 obligatorio | MATCH | — | `OFP:2008-2035`; `V:650-651` |
| `supplier_id`, `transport_id` | SearchSelect | int | ok | BR-22 + tenencia | MATCH | — | `OFP:1726-1742`; `SVC:930` |
| `extra_data.import_plan.{origin_country, purchased_total, shipped_total, received_total, transit_mortality, departure_date, arrival_date}` | sí (`valueAsNumber` en enteros) | números/fechas ISO | `PlanDeImportacion` (`extra=forbid`) | BR-22 identidades | MATCH | — | `OFP:1746-1770`; `S:23-44` |
| `extra_data.import_plan.quarantine_end_date` | `<input type=date>` **opcional** | **`''` cuando se deja en blanco** (no hay limpieza de cadenas en `extra_data`) | `Optional[date]` — pydantic **rechaza `''`** | BR-22 → 400 «Plan de importación inválido: quarantine_end_date…» | **MISMATCH** | empty string for optional date | `OFP:1782`; `OFP:189-207`; `S:43`; `V:645-649`. El recorrido certificado **rellena** el campo (`scripts_e2e_f01_retry.mjs:176`), por eso no se observó → **B-11** |
| `reception_condition`, `initial_health_inspection` | texto | `''` | `Optional[str]` | — | MATCH (`''` aceptado) | | `OFP:1774, 1786` |
| `bird_movements` M/F con peso **«(kg)»** | `renderMFRows(true)` | filas | — | BR-22 Σ = `received_total` | MATCH · unidad **MISMATCH** | unit | `OFP:1790` → B-12 |
| `lot_id` | opcional (OD-25 B) | ausente/int | opcional | cadena `grandparent` | MATCH | | `OFP:37-40, 2090-2092`; `SVC:242-246, 927` |
**Veredicto: 422/RENDER** (B-11 con campo opcional en blanco).

### 2.27 Ruta de edición (`PUT /operations/{id}`)
Ninguna pantalla la invoca (grep sin resultados; `OperationDetailPage` solo `submit`/evidencias). `OperationalEventUpdate` (`S:195-253`, `extra="forbid"`, sin `status`) es coherente con `Create` pero **inalcanzable** desde la UI; la única mutación de campo es `CorrectionForm` (solo `observations`). → **B-31**, **B-30** (P3).

---

## 3. `LotFormPage` ↔ `LotCreate`
| Field | UI | Default | Val. UI | Payload | BE (`lots/schemas.py`) | Servicio | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|---|---|---|
| `lot_code` | sí | — | 2..50 | str | `str` 1..100 | 409 duplicado | MATCH | — | `LotFormPage.tsx:21, 119`; `schemas.py:29`; `service.py:311-318` |
| `bird_type` | select 4 valores | — | enum | str | `Optional[str]` → `BirdTypeEnum` | unidad operativa | MATCH (valores idénticos) | — | `LotFormPage.tsx:18`; `masters/models.py:34-38` |
| `farm_id` | select **obligatorio** (zod `min(1)`) | — | req. | int | `Optional[int]` | tenencia | UI más estricta que BE (lotes de incubadora forzados a granja) | optional-vs-required (inverso) | `LotFormPage.tsx:23, 121`; `schemas.py:14` → **B-19** |
| `house_id`, `genetic_line_id`, `breed_id` | select `coerce.number` | — | opc. | int/`null` | `Optional[int]` | — | MATCH | — | `LotFormPage.tsx:24-28, 122-129` |
| `area_id` | select (solo activas, OD-21) | — | opc. | int/`null` | `Optional[int]` | `exigir_activo=True` | MATCH | — | `LotFormPage.tsx:101-103, 126`; `service.py:341-347` |
| `planned_close_date`, `start_date` | `<input type=date>` | — | opc. | `'YYYY-MM-DD'`/`null` | `Optional[datetime]` (acepta fecha ISO) | medianoche UTC | MATCH | — | `LotFormPage.tsx:127-130`; `schemas.py:27, 47`; `service.py:372-375, 391` |
| `sap_reference` | sí («Integración SAP») | — | opc. | str/`null` | **no existe** en `LotCreate` ni en `Lot` | — | **MISMATCH → descartado en silencio** (patrón P0-14/R-47) | stale frontend DTO | `LotFormPage.tsx:30, 131, 288-293`; `schemas.py:12-47`; `masters/models.py:278-320` (sin columna); `lots.service.ts:16` → **B-18** |
| `sex`, `weight_curve_id` | no | — | — | ausentes | `Optional` | curva activa por línea | MATCH | — | `schemas.py:20, 31` |
| error | `toast.error(err.response.data.detail)` crudo | | | | | | React #31 en 422 | render | `LotFormPage.tsx:137` → **B-15** |
**Veredicto: WRONG-FIELD** (B-18).

### 3.1 `LotDetailPage` — cierre y transición de fase
| Acción | Payload UI | BE | MATCH | Evidencia |
|---|---|---|---|---|
| Cerrar lote | `POST /lots/{id}/close` sin cuerpo | `LotClosureSummary` | MATCH (error solo en consola) | `LotDetailPage.tsx:111-115`; `lots/router.py:80-92` |
| Transición a producción | `POST /lots/{id}/phases` `{phase_code:'production', start_date, start_population_male, start_population_female}` | `LotPhaseCreate` exige **`lot_id`** y **`phase_id`** (no `phase_code`); router verifica `data.lot_id == lot_id` | **MISMATCH → 422 siempre** (error solo `console.error`) | `LotDetailPage.tsx:125-134`; `lots/schemas.py:98-109`; `lots/router.py:136-147`; grep `phase_code` en backend = 0 → **B-07** |

---

## 4. `MasterListPage` (22 entidades de `App.tsx:135-166`)
La pantalla genérica renderiza **solo** las columnas configuradas como `<Input>` de texto y envía `formValues: Record<string,string>` tal cual en `POST`/`PUT` (`MasterListPage.tsx:40, 87-103, 193-200`); en edición rellena `item[key] ?? ''` (`:80`). `is_active` nunca se renderiza; `DELETE` = baja lógica. `company_id` solo lo inyecta el servicio cuando el esquema lo declara **opcional** y llega `None` (`masters/service.py:227-235`).

| Entidad | Campos UI | Create schema exige | Create desde UI | Update schema | Edit desde UI | MATCH | Evidencia |
|---|---|---|---|---|---|---|---|
| companies | name, tax_id, country | `name` | ✔ | `CompanyUpdate` | ✔ | CORRECT | `schemas.py:14-34` |
| **farms** | name, code, location | **`company_id: int` requerido** | **422** (UI no lo captura; servicio no llega a inyectarlo) | `FarmUpdate` | ✔ | **422** | `App.tsx:137`; `masters/schemas.py:64-73` → **B-08** |
| **houses** | name, capacity | **`farm_id: int`** requerido; `capacity: Optional[int]` | **422** (`farm_id` ausente; `capacity:''` también 422) | `HouseUpdate.capacity Optional[int]` | **422 si capacidad en blanco** (`''`) | **422** | `App.tsx:138`; `schemas.py:95-110` → **B-08**, **B-14** |
| **hatcheries** | name, code | **`company_id: int`** | **422** | `HatcheryUpdate` | ✔ | **422** | `App.tsx:139`; `schemas.py:124-139` → **B-08** |
| suppliers | name, sap_code | `company_id` opcional (inyectado) | ✔ | `SupplierUpdate` (`Any`) | ✔ | CORRECT | `schemas.py:248-257, 434-441` |
| areas | name, code | opcional | ✔ | `AreaUpdate` | ✔ | CORRECT | `schemas.py:631-655` |
| genetic-lines | name, code | opcional | ✔ | `GeneticLineUpdate` | ✔ | CORRECT | `schemas.py:187-203, 444-451` |
| breeds | name | `genetic_line_id` opcional | ✔ (raza sin línea) | `BreedUpdate` | ✔ | CORRECT | `schemas.py:206-221` |
| feed-types | name, code | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:267-282` |
| vaccines | name, laboratory | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:285-302` |
| mortality-causes | name, category | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:323-337` |
| transports | name, plate | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:357-373` |
| processing-plants | name, location | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:376-390` |
| **incubators** | name, capacity | **`hatchery_id: int`** requerido; `capacity` `''` → 422 | **422** | `IncubatorUpdate.capacity Optional[int]` | **422 si en blanco** | **422** | `App.tsx:159`; `schemas.py:149-157, 523-526` → **B-08**, **B-14** |
| **hatchers** | name, capacity | **`hatchery_id: int`** | **422** | `HatcherUpdate.capacity Optional[int]` | **422 si en blanco** | **422** | `App.tsx:160`; `schemas.py:166-173, 529-532` → **B-08**, **B-14** |
| **productive-phases** | name, code, order | `order: Optional[int]` → `''` 422 | **422 si `order` en blanco** | `ProductivePhaseUpdate.order Optional[int]` | **422 si en blanco** | **422** | `App.tsx:161`; `schemas.py:224-233, 535-542` → **B-14** |
| medications | name, laboratory | opcional | ✔ | `MedicationUpdate` | ✔ | CORRECT | `schemas.py:305-320, 545-549` |
| cull-causes | name, category | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:340-354, 552-555` |
| rejection-reasons | name, category | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:393-408, 558-562` |
| correction-types | name, description | opcional | ✔ | ok | ✔ | CORRECT | `schemas.py:411-425, 565-568` |
| (todas) | error 422 | `setFormError(detail)` → `<p>{formError}</p>` | — | — | — | **React #31** en cualquier 422 (lista) | `MasterListPage.tsx:99, 201-205` → **B-15** |
| (todas) | `is_active` | no editable → no se puede **reactivar** desde la UI | — | todas las `*Update` lo admiten | — | gap | → **B-36** |

**Resumen maestros: 16 CORRECT · 6 422/RENDER** (farms, houses, hatcheries, incubators, hatchers, productive-phases). Nota: `FE_BE_CONTRACT_MATRIX.md:71` (C-17) cerró los `PUT` faltantes, no esta brecha de creación.

---

## 5. `WeightCurvesPage` ↔ `WeightCurveCreate`
| Field | UI | Payload | BE (`masters/schemas.py:575-609`) | MATCH | Evidencia |
|---|---|---|---|---|---|
| `genetic_line_id`, `version_label`, `source` | sí | int, str, str/`undefined` | req., 1..50, opc. | MATCH | `WeightCurvesPage.tsx:111-116`; `weightCurves.ts:57-67` |
| `points[]` `{age_days, min_weight, max_weight, target_weight}` | CSV parseado en cliente | números; celdas ilegibles → `NaN` → **`null`** en JSON | `int ≥0`, `float >0`, `Optional[float] >0` | MATCH cuando el CSV es correcto; con celdas ilegibles → 422 de pydantic (lista) que `mensajeGeneral` no interpreta (muestra genérico, sin fila) | `weightCurves.ts:101-115`; `WeightCurvesPage.tsx:23-34, 119-122` → **B-32** (P3) |
| `is_active` | no | ausente (default `False`) | `bool = False` | MATCH | |
| activar | `PUT /masters/weight-curves/{id}/activate` sin cuerpo | ruta sin cuerpo | MATCH | `weightCurves.ts:69-72`; `masters/router.py:227-242` |
**Veredicto: CORRECT.**

---

## 6. Usuarios / Roles / Perfil ↔ `auth/schemas.py`
| Formulario | Payload UI | BE | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|
| `UsersPage` **crear** | `{username, first_name, last_name, email, phone, role_id\|null, area_id\|null, company_id\|null, view_type, is_active, password}` | `UserCreate(UserBase)`: `last_name min_length=1`, `email EmailStr`, `password ≥8`; **`company_id` se resuelve en servidor** (R-118: ignorado para actor acotado) | `last_name` en blanco → 422 (UI solo exige username/first_name/email); selector de empresa mostrado pero **ignorado** | optional-vs-required · misleading UI | `UsersPage.tsx:71, 76-83, 124-126`; `auth/schemas.py:27-41`; `auth/service.py:340-357` → **B-28** |
| `UsersPage` **editar** | `PUT /users/{id}` con `{...datos}` = **incluye `username` y `company_id`** | `UserUpdate` `extra="forbid"` **sin `username` ni `company_id`** | **MISMATCH → 422 «Extra inputs are not permitted» en toda edición**; error mostrado como `alert(detail)` = `[object Object]` | wrong property / stale DTO | `UsersPage.tsx:76-79, 85`; `auth/schemas.py:65-85`; `auth/router.py:128-135` → **B-06** |
| `UsersPage` toggle activo | `PUT /users/{id}` `{is_active}` | ok | MATCH | | `UsersPage.tsx:91` |
| `UsersPage` reset contraseña | `POST /users/{id}/password` `{new_password}` | `PasswordChangeRequest` (`current_password` opcional para admin) | MATCH | | `UsersPage.tsx:80`; `auth/schemas.py:44-62` |
| `RolesPage` crear/editar | `{name, description, permissions:[{module, action, scope_type:'all'}]}`; desactivar `{is_active:false}` | `RoleCreate`/`RoleUpdate` con `PermissionCreate` | MATCH | | `RolesPage.tsx:17-20, 54-58, 76-99`; `auth/schemas.py:149-172, 201-205` |
| `ProfilePage` | `POST /users/{id}/password` `{current_password, new_password}` (≥8 en UI) | `PasswordChangeRequest` | MATCH; `setMessage(detail)` crudo → React #31 si 422 | render | `ProfilePage.tsx:29-38, 70` → **B-15** |

---

## 7. Acceso por unidad ↔ `business_units` (`admin.py`, `router.py`, `schemas.py`)
| Acción | UI | BE | MATCH | Evidencia |
|---|---|---|---|---|
| Listar | `GET /business-units` | `HabilitacionRead[]` | MATCH | `businessUnits.service.ts:34-37`; `business_units/router.py:94` |
| Habilitar/deshabilitar | `PATCH /business-units/{code}/enable|disable` sin cuerpo | rutas `PATCH` sin cuerpo | MATCH | `service.ts:40-49`; `router.py:104, 124`; `admin.py:138-216` |
| Candidatos | `GET /business-units/{code}/grant-candidates` (solo si `is_enabled`) | `CandidatoRead[]`; 409 si apagada | MATCH | `UnitAccessPage.tsx:96-103`; `router.py:146`; `admin.py:265-314` |
| Conceder | `POST /users/{id}/business-units` `{code}` (nunca `company_id`) | `ConcesionCreate{code}` | MATCH | `service.ts:64-67`; `schemas.py:54-62`; `admin.py:317-391` |
| Revocar | `DELETE /users/{id}/business-units/{code}` | `ConcesionRead` | MATCH | `service.ts:69-73`; `router.py:210` |
| Concesiones de usuario | `GET /users/{id}/business-units` → `{user_id, code, company_id, granted_at, revoked_at, is_effective}` | `ConcesionRead` idéntico | MATCH | `service.ts:16-23`; `schemas.py:33-51` |
**Veredicto: CORRECT** (UnitAccessPage y UserBusinessUnitsButton).

---

## 8. Revisión / Corrección / Aprobaciones ↔ `review/schemas.py`, `corrections/schemas.py`
| Formulario | Payload UI | BE | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|
| `ReviewCenter` listado | `GET /review/pending?limit&offset&status&lot_id&event_type&date_from&date_to&farm_id&operator_id` | router acepta `farm_id, lot_id, event_type, date_from, date_to, limit, offset`; **`status` y `operator_id` no existen** (el servicio devuelve siempre registered/pending_review) | **MISMATCH**: las pestañas «En revisión/Devueltos/Aprobados/Consolidados» y el filtro de operador se **pierden en silencio** | wrong query param / filter lost | `ReviewCenter.tsx:85-96`; `review/router.py:22-40`; `review/service.py:153-163` → **B-13** |
| `ReviewCenter` acciones | `POST /review/start/{id}`; `/review/complete {event_id}`; `/review/return {event_id, observations}` (prompt, no vacío) | `ReturnToOperatorRequest.observations min_length=10` | MATCH salvo longitud (<10 → 422, mostrado vía `getErrorMessage`) | optional-vs-required (longitud) | `ReviewCenter.tsx:122-135`; `review/schemas.py:98-107` → **B-29** |
| `ReviewCenter` lote de revisión | `POST /review/batches {batch_name, event_ids}` | `ReviewBatchCreate` | MATCH | | `ReviewCenter.tsx:146`; `schemas.py:12-15` |
| `ReviewDetail` | start/complete/return/approve/reject con `{event_id, observations}`; return/reject exigen solo «no vacío» | return/reject `min_length=10` | MATCH salvo longitud | | `ReviewDetail.tsx:64-81`; `schemas.py:98-101, 119-121` → **B-29** |
| `ApprovalPanel` | approve `{event_id}`; reject `{event_id, observations ≥10}`; batch-approve `{event_ids}`; batch-reject `{event_ids, observations ≥10}`; `GET /approvals/pending?limit&offset&lot_id` | `ApproveRequest`, `RejectRequest`, `Batch*Request`; router `farm_id, lot_id, limit, offset` | MATCH | | `ApprovalPanel.tsx:38-40, 54, 65-70, 100, 109-119`; `schemas.py:114-131`; `review/router.py:108-112` |
| `CorrectionForm` | `POST /corrections {event_id, field_name, original_value, corrected_value, correction_type_id\|null, reason ≥5}` | `CorrectionCreate` (reason ≥5 no en blanco) | MATCH; la UI solo ofrece `field_name='observations'` frente a `campos_corregibles()` (≈ todos los de `OperationalEventUpdate` menos identidad) | UI-limited | `CorrectionForm.tsx:49-59, 72-74`; `corrections/schemas.py:8-23`; `corrections/service.py:168-181` → **B-30** |
| `review.service.ts` / `approvals.service.ts` DTOs | `returnEvent.observations?` opcional; `reject.observations?` opcional | obligatorios (≥10) | DTO más laxo que el contrato | stale DTO | `review.service.ts:46-47`; `approvals.service.ts:10, 16` (informativo) |

---

## 9. SAP e informes ↔ `integrations/sap/router.py`, `reports/router.py`
| Pantalla | Petición | BE | MATCH | Evidencia |
|---|---|---|---|---|
| `SapManagerPage` | `GET /sap/references?limit=10`, `/sap/sync/jobs?limit=5`, `/sap/payloads?limit=5`, `/sap/connection-check`; `POST /sap/consolidate {}`; `POST /sap/export {}` | params `ref_type, limit, offset`; cuerpos `Optional[...]` → `{}` válido | MATCH | `SapManagerPage.tsx:38-66`; `sap/router.py:30-42, 49-61, 92-103` |
| `sap.service.ts.importReferences` | `POST /sap/references/import {ref_type, entries[]}` | `SapReferenceImportRequest{references:[{ref_type, sap_code, description, quantity, extra_data}]}` | **MISMATCH** (`references` requerido; `entries` desconocido) → 422. Solo lo usa `hooks/useSap.ts:46-47`; **ninguna página** lo invoca | wrong property / stale DTO | `sap.service.ts:34-35`; `sap/schemas.py:45-47` → **B-27** |
| `ReportsPage` | `GET /reports/kpis?lot_id=N`; `GET /operations?lot_id=N&limit=100` | `lot_id Optional[int]`; `skip/limit/lot_id` | MATCH (lote por defecto `2` hardcodeado) | `ReportsPage.tsx:13, 17-19`; `reports/router.py:15-22`; `operations/router.py:42-67` |
| `LotReportPage` | `/reports/lot/{id}`, `/reports/kpi/ipe/{id}`, `/reports/kpi/weight-uniformity/{id}`, `/reports/kpis/{afcr,vaccination-efficiency,transfer-efficiency,hatchery}?lot_id` | rutas idénticas | MATCH | `LotReportPage.tsx:26-33`; `reports/router.py:55-63, 76-103, 116-146` |
| `SapComparisonPage` | `GET /reports/sap-comparison` (sin `lot_id`) | `lot_id Optional` | MATCH (comparativo global; sin filtro por lote en UI) | `SapComparisonPage.tsx:14`; `reports/router.py:149-156` |
| `reportsService.getSapComparison` | sin params | ok | MATCH | `reports.service.ts:42-43` |
**Veredicto: CORRECT** (SapManagerPage, ReportsPage, LotReportPage, SapComparisonPage); B-27 es DTO muerto.

---

## 10. `TraceabilityTree` ↔ `EggBatchCreate` / `ChickBatchCreate`
| Field | UI | Payload | BE (`lots/schemas.py:209-248`) | MATCH | Clase | Evidencia |
|---|---|---|---|---|---|---|
| egg: `source_lot_id` | lote actual | int | req. | MATCH | | `TraceabilityTree.tsx:86-91` |
| egg: `hatchery_lot_id` | `<Input type=number>` libre (id numérico tecleado) | `Number(x) \|\| null` | **`int` requerido** (OD-10.b) | **MISMATCH** si se deja en blanco → 422 | null vs required | `TraceabilityTree.tsx:88`; `schemas.py:218-219` → **B-17** |
| egg: `quantity_dispatched` | number | `Number('')` = **0** | `int` sin `ge` → 0 aceptado | MATCH esquema (0 persistible) | BE hardening | `TraceabilityTree.tsx:89`; `schemas.py:222` → B-17 |
| egg: `dispatch_date` | date | `'YYYY-MM-DD'` | `date` | MATCH | | |
| chick: `hatchery_lot_id`, `destination_lot_id` (`\|\| null`), `quantity_dispatched`, `dispatch_date` | ídem | ídem | `destination_lot_id`/`broiler_lot_id` uno obligatorio (validador) | 422 si en blanco | null vs required | `TraceabilityTree.tsx:105-110`; `schemas.py:227-248` → B-17 |
| error | `setLinkError(err.response.data.detail)` → `<p>{linkError}</p>` | | | **React #31** en 422 | render | `TraceabilityTree.tsx:95, 114, 347, 389` → **B-15** |
| — | los lotes destino se teclean por **id numérico** sin selector | | | UX; no contrato | | `TraceabilityTree.tsx:326-333, 368-375` |
**Veredicto: 422/RENDER** (ambos modales).

---

## 11. Evidencias (`OperationDetailPage`) ↔ `POST /operations/{id}/evidences`
Campos multipart `file`, `description`, `evidence_type` (solo si se elige) (`OperationDetailPage.tsx:89-95`) ↔ `File(...)`, `Form("")`, `Form("")` (`operations/router.py:344-349`); MIME y 10 MB coinciden (`:20-21` ↔ `:22, 359-366`); clases de importación coinciden con `CLASES_DE_ADJUNTO` (`:320` ↔ `V:616-617`). Errores vía `getErrorMessage`. **Veredicto: CORRECT.**

---

## DEFECT REGISTER

| # | Form | Event/entity | Defect class | Sev. | Reproduction (payload) | Evidence file:line | Related finding |
|---|---|---|---|---|---|---|---|
| **B-01** | OperationFormPage | `egg_reception_hatchery`, `chick_dispatch` | optional-vs-required (BE exige `farm_id`; UI lo fuerza a `undefined` en etapa incubadora) | **P1** (bloquea la cadena de incubadora) | `POST /operations {event_type:'egg_reception_hatchery', lot_id:L, house_id:H?, farm_id:<ausente>, ...}` → 400 BR-08 «requiere una granja asignada»; ídem `chick_dispatch` | `OFP:274-278, 386, 438`; `V:828-836`; `SVC:879` | misma clase que F-01e (`GA_F01E_SUBSANACION_ANNEX.md:40` deja «demás tipos» fuera) |
| **B-02** | OperationFormPage | `egg_reception_hatchery` → `incubation_load` | wrong nested structure (cantidad recibida en `egg_storage_records`, saldo BR-03 lee `egg_movements[fertile]`) | **P1** | Recepción con `egg_storage_records:[{eggs_received:1000,...}]`, `egg_movements:[]` → luego `incubation_load {hatchery_params:[{quantity_loaded:500}]}` → 400 BR-03 «excede los huevos disponibles en incubadora (0)» | `OFP:1219`; `V:149-175`; `SVC:956-960` | F-01b (observación, sin hallazgo) |
| **B-03** | OperationFormPage | `egg_reception_hatchery` | optional-vs-required (`arrival_date` requerido, no capturado) | **P1** (con B-01/B-02) | `egg_storage_records:[{eggs_received:1000}]` → 422 `egg_storage_records.0.arrival_date: Field required` | `OFP:170-177, 1218-1236`; `S:85-87` | **F-01b** (`GA_F01_EGG_STORAGE_CONTRACT.md:30`; `GA_F01_DEDUP_RECONCILIATION.md:35`) |
| **B-04** | OperationFormPage | `bird_distribution`, `bird_transfer`, `bird_exit`, `egg_collection`, `egg_dispatch`, `transport_inspection` | selector value lost (galpón por fila no deriva `house_id`) / optional-vs-required (lotes sin galpón: OD-25 B autocreados, `LotFormPage` galpón opcional) | **P1** en cadena Progenitoras (lotes autocreados); P2 resto | Lote con `house_id=null`: `POST {event_type:'bird_distribution', bird_movements:[{target_house_id:7, sex:'female', quantity:100}]}` → `house_id` ausente → 400 BR-08 «requiere un galpón asignado» | `OFP:387-394, 439`; `V:829-839`; filas con galpón `OFP:741, 794, 805, 846, 857` | F-01e (AC63-65 limitan la corrección a `bird_reception`) |
| **B-05** | OperationFormPage | `birth_registration` | validation silently blocking submit (`dosage_per_bird` registrado sin `valueAsNumber` → `''` → `z.number()` falla; sin render del error) | **P1** *(inferencia estática; confirmar en runtime)* | Rellenar nacidos y pulsar Guardar sin tocar «Dosis por ave» → `handleSubmit` no llama `onSubmit`; ninguna petición; sin mensaje | `OFP:1651` vs `OFP:103, 189-207`; contraste correcto `OFP:581` | R-170 (cerrado en backend; el formulario no se certificó en runtime) |
| **B-06** | UsersPage | editar usuario | wrong property / stale DTO (`username`, `company_id` en `PUT` con `extra="forbid"`) | **P1** (ninguna edición de usuario funciona; error ilegible) | `PUT /users/5 {username:'x', company_id:1, first_name..., is_active:true}` → 422 «Extra inputs are not permitted» (`username`, `company_id`); UI: `alert('[object Object]')` | `UsersPage.tsx:76-79, 85`; `auth/schemas.py:65-85`; `auth/router.py:128-135` | R-118 (empresa resuelta en servidor) · P0-13 |
| **B-07** | LotDetailPage | transición de fase | wrong property name / missing required (`phase_code` vs `phase_id`; sin `lot_id`) | **P1** (transición cría→producción imposible; error solo en consola) | `POST /lots/12/phases {phase_code:'production', start_date:'2026-09-13', start_population_male:0, start_population_female:0}` → 422 `lot_id/phase_id Field required` | `LotDetailPage.tsx:125-134`; `lots/schemas.py:98-109`; `lots/router.py:136-147` | — (nuevo) |
| **B-08** | MasterListPage | `farms`, `houses`, `hatcheries`, `incubators`, `hatchers` | optional-vs-required (Create exige `company_id`/`farm_id`/`hatchery_id` que la UI no captura) → creación imposible desde UI | **P1** (5 maestros estructurales solo por API) | `POST /masters/houses {name:'G1', capacity:'1000'}` → 422 `farm_id Field required`; `POST /masters/farms {name, code, location}` → 422 `company_id` | `App.tsx:137-139, 159-160`; `MasterListPage.tsx:193-200`; `masters/schemas.py:64-73, 95-103, 124-132, 149-157, 166-173`; `masters/service.py:232-234` | C-17 (`FE_BE_CONTRACT_MATRIX.md:71`) cubrió solo `PUT` |
| **B-09** | OperationFormPage | `bird_exit` (selector interno «Ref. OC SAP») | ID instead of code (`setValue('sap_document_ref', String(id))`) | **P2** | Elegir OC en el bloque de salida → `sap_document_ref:"12"` (id) en vez de `"4500001234"`; BR-10/comparativo SAP no casan | `OFP:917-927` vs `OFP:2008-2035`; `V:471-474, 758` | R-189 F-01 (misma clase, no propagada) · GA-TD-014 |
| **B-10** | OperationFormPage | `feed_registration` | ID instead of code (`feed_movements.0.sap_order_id ← String(id)`) | **P2** | `feed_movements:[{feed_type_id:3, quantity_kg:500, sap_order_id:"9"}]` → persiste id de `SapReference`, no el código de la orden de transferencia | `OFP:1033-1040`; `M:225` | R-189 F-01 (clase) |
| **B-11** | OperationFormPage | `grandparent_import` | empty string for optional date (`quarantine_end_date:''` → `PlanDeImportacion` rechaza) | **P2** (campo opcional bloquea el alta) | Plan completo con «Cuarentena (fecha fin)» en blanco → `extra_data.import_plan.quarantine_end_date:''` → 400 BR-22 «Plan de importación inválido: quarantine_end_date: Input should be a valid date…» | `OFP:1782, 189-207`; `S:43`; `V:645-649`; e2e rellena el campo `scripts_e2e_f01_retry.mjs:176` | R-152 / R-189 |
| **B-12** | OperationFormPage | `weight_recording`, `bird_transfer`, `bird_exit`, `grandparent_import`, `lot_closure` | unit mismatch (etiqueta «(kg)» step 0.001; sistema y curva en **gramos**) | **P2** (evaluación de curva y KPI de uniformidad erróneos) | `weight_recording {bird_movements:[{sex:'male', quantity:50, avg_weight:2.15}]}` → evaluado contra curva en g → `below_standard` + alerta | `OFP:470, 484, 627, 865, 987, 1703, 1790` vs `OFP:762`; `GA_REM_021_B02_WEIGHT_RANGE_MATRIX.md:19,45`; `OperationDetailPage.tsx:221` | GA-REM-037 / B02 |
| **B-13** | ReviewCenter | listado por pestañas | wrong query param (filtro perdido en silencio: `status`, `operator_id`) | **P2** (pestañas muestran el mismo conjunto) | `GET /review/pending?status=approved&operator_id=3` → 200 con registered/pending_review | `ReviewCenter.tsx:85-96`; `review/router.py:22-40`; `review/service.py:153-163` | — |
| **B-14** | MasterListPage | `houses`, `incubators`, `hatchers`, `productive-phases` (edición y alta) | empty string sent for optional numeric (`capacity:''`, `order:''` → `Optional[int]` 422) | **P2** | `PUT /masters/houses/3 {name:'G1', capacity:''}` → 422 `capacity: Input should be a valid integer` | `MasterListPage.tsx:80, 92-94`; `masters/schemas.py:98, 108, 152, 169, 227, 525, 531, 538` | — |
| **B-15** | MasterListPage, LotFormPage, TraceabilityTree, ProfilePage, UsersPage | cualquier 422 | render de `detail` estructurado (React #31 / `[object Object]`) | **P2** (convierte cada 422 anterior en pantalla rota) | Cualquier 422 con `detail: [...]` → `<p>{detail}</p>` | `MasterListPage.tsx:99, 203`; `LotFormPage.tsx:137`; `TraceabilityTree.tsx:95, 114, 347, 389`; `ProfilePage.tsx:38, 70`; `UsersPage.tsx:85`; helper disponible `Toast.tsx:95-140` | R-189 F-01 (corrección limitada al asistente) |
| **B-16** | OperationFormPage ↔ service | `bird_reception` (y `bird_distribution`) | BE rule vs UI structure (BR-17 valida Σ total contra un solo `house_id`; la UI distribuye por galpón) | **P2** | Dos galpones de 500: filas `[{target_house_id:1, quantity:500},{target_house_id:2, quantity:500}]` → `house_id=1`, Σ=1000 → 400 BR-17 «excede la capacidad del galpón (500)» | `OFP:725-772, 392-393`; `SVC:897-902`; `V:712-725` | F-01e (deriva `house_id` de la 1.ª fila) |
| B-17 | TraceabilityTree | egg/chick batches | null vs required (`hatchery_lot_id`/`destination_lot_id` `null` si en blanco); `quantity_dispatched` 0 aceptado | P3 (422 legítimo; ver B-15 para el crash) | `POST /lots/egg-batches {source_lot_id:4, hatchery_lot_id:null, quantity_dispatched:0, dispatch_date:'…'}` → 422 | `TraceabilityTree.tsx:86-91, 105-110`; `lots/schemas.py:218-222, 238-243` | OD-10.b |
| B-18 | LotFormPage | alta de lote | stale frontend DTO (`sap_reference` sin contrato ni columna → descartado) | P3 | `POST /lots {..., sap_reference:'SAP-2024-1'}` → 201 sin persistir | `LotFormPage.tsx:30, 131, 288-293`; `lots/schemas.py:12-47`; `masters/models.py:278-320`; `lots.service.ts:16` | patrón P0-14 / R-47 |
| B-19 | LotFormPage | alta de lote | UI requires but backend optional (`farm_id`) | P3 | Lote `hatchery` sin granja imposible desde UI | `LotFormPage.tsx:23`; `lots/schemas.py:14` | — |
| B-20 | OperationFormPage | `ovoscopy` | UI field without BE home (día de ovoscopía descartado por serializador) | P3 (pérdida de dato) | `bird_movements:[{sex:'mixed', week_number:10}]` → fila descartada → dato perdido | `OFP:1531-1532`; `operationPayload.ts:18-20, 40-49` | R-177 (dominio `egg_type`) |
| B-21 | OperationFormPage | `transport_inspection`, `farm_inspection` | malformed default (6 filas `inspection_details` con `''` siempre persistidas); `value_numeric` nunca poblado | P3 | `inspection_details:[{parameter:'cage_condition', status:''}, {parameter:'density', value:''}, …]` → 201 con filas vacías | `OFP:1374-1391, 448, 400-402`; `S:122-129` | F-01d (clase, cadenas) |
| B-22 | OperationFormPage | `hatchery_inspection`, eventos de incubadora | BE field never populated (`hatchery_params.hatchery_id`; selector local no viaja) | P3 | Elegir incubadora en cabecera → `hatchery_id` ausente en todas las filas | `OFP:139-149, 2044-2056`; `S:101`; `reports/router.py:59` | — |
| B-23 | OperationFormPage | todos | BE field never populated (`idempotency_key`) | (P2 conocido) | — | `S:167`; `SVC:224-234` | **R-146** (abierto) |
| B-24 | backend | `water_consumption` | stale list (`ALL_EVENT_TYPES` sin `water_consumption`) | P3 | `GET /operations/event-types` omite el tipo | `S:312-338`; `M:55` | GA-REM-021-A |
| B-25 | processCatalog | `egg_classification` | unreachable event type (en enum y `switch`, en ninguna etapa) | P3 (informativo) | — | `processCatalog.ts:205-238`; `OFP:1047` | — |
| B-26 | OperationFormPage | `bird_exit`, `egg_dispatch`, `transfer_to_hatcher`, `lot_closure` | string/int mismatch en `extra_data` (numéricos sin `valueAsNumber`) | P3 | `extra_data:{transport_temperature:"22", incubation_day:"18", fcr:"2.000"}` | `OFP:947-973, 1131-1157, 1565, 1708-1712` | — |
| B-27 | sap.service.ts / useSap | importación de referencias | wrong property (`entries` vs `references`) — DTO muerto | P3 | `POST /sap/references/import {ref_type, entries:[…]}` → 422 `references Field required` | `sap.service.ts:34-35`; `hooks/useSap.ts:46-47`; `sap/schemas.py:45-47` | R-95 |
| B-28 | UsersPage | crear usuario | optional-vs-required (`last_name` ≥1 no exigido en UI); selector de empresa ignorado por servidor | P3 | `POST /users {last_name:'', …}` → 422 | `UsersPage.tsx:71`; `auth/schemas.py:29`; `auth/service.py:351-357` | R-118 |
| B-29 | ReviewDetail, ReviewCenter | devolver / rechazar | optional-vs-required (longitud ≥10 solo en BE) | P3 | `POST /review/return {event_id, observations:'ok'}` → 422 (mensaje renderizable) | `ReviewDetail.tsx:69, 74`; `ReviewCenter.tsx:123-129`; `review/schemas.py:101, 121` | — |
| B-30 | CorrectionForm | corrección de campo | UI-limited (solo `observations` frente a `campos_corregibles()`) | P3 | — | `CorrectionForm.tsx:72-74`; `corrections/service.py:168-181` | GA-REM-006 |
| B-31 | (ninguna) | `PUT /operations/{id}` | no UI edit path (`OperationalEventUpdate` inalcanzable) | P3 | — | grep FE = 0; `S:195-253` | R-34 / R-176 |
| B-32 | WeightCurvesPage | carga de curva | NaN→null en celdas ilegibles → 422 pydantic no interpretado (sin fila) | P3 | CSV con `"abc"` en peso → `points[i].min_weight:null` → 422 lista → mensaje genérico | `weightCurves.ts:101-115`; `WeightCurvesPage.tsx:23-34, 119-122` | R-96 |
| B-33 | OperationFormPage | `egg_dispatch`, `egg_reception_hatchery` | semantic misuse (`incubator_id` destino como fila `HatcheryParams`; granja origen en `extra_data`) | P3 | — | `OFP:1093-1100, 1194` | — |
| B-34 | OperationFormPage / LotDetailPage | `lot_closure` vs `POST /lots/{id}/close` | semantic duplication (el evento no cierra; datos de cierre como cadenas en `extra_data`) | P3 | — | `OFP:1694-1716`; `SVC:967-970`; `LotDetailPage.tsx:111` | BR-05 / R-73 |
| B-35 | OperationFormPage | `birth_registration` | optional-vs-required (`chicks_healthy/weak` obligatorios en incubadora; `mixed`+sexadas no impedido) | P3 (UX; 400 legítimo) | `{bird_movements:[{sex:'male',quantity:50},{sex:'mixed',quantity:10}]}` → 400 BR-21 | `OFP:1586-1614`; `V:593-613` | R-170 / B13 |
| B-36 | MasterListPage | todas | `is_active` no editable → imposible reactivar | P3 | — | `MasterListPage.tsx:193-200`; `masters/schemas.py` (`*Update.is_active`) | — |
| B-37 | OperationFormPage | `bird_reception` (radio origen) | `''` persistido en `sap_document_ref`/`vaccination_route` en lugar de `null` | P3 (higiene) | `sap_document_ref:''` | `OFP:1951, 1962, 566-567` | — |
| B-38 | OperationFormPage | `weight_recording`, `mortality`, `cull` | `week_number` solo en fila 0 → se pierde si esa fila va a 0 | P3 | — | `OFP:520, 543, 620, 441` | — |
| B-39 | OperationFormPage | `egg_collection` | `avg_weight` solo en fila `fertile` → se pierde si fértiles = 0 | P3 | — | `OFP:1076` | — |
| B-40 | backend service | `egg_storage_records` en evento sin lote | 500 (`lot_id` NOT NULL) — solo por API | P3 (hardening) | `POST {event_type:'farm_inspection', lot_id:null, egg_storage_records:[{arrival_date:'…', eggs_received:1}]}` → 500 | `SVC:281-284`; `M:273` | **F-01c** |
| B-41 | LotDetailPage | cierre / transición | errores solo en `console.error` (sin feedback) | P3 | — | `LotDetailPage.tsx:115, 134` | — |

### Verificación del cierre de R-189 (F-01 / F-01d / F-01e)
- `[{}]` de arranque: cubierto para `bird_movements`, `feed_movements`, `hatchery_params`, `egg_storage_records` (`OFP:441-449`; `operationPayload.ts`). **No** cubierto para `inspection_details` (cadenas `''`, B-21).
- `sap_document_ref` = código: cubierto en el **selector superior** (6 tipos). **No** propagado a los selectores internos de `bird_exit` (B-09) ni `feed_registration.sap_order_id` (B-10).
- React #31: cubierto en el asistente y en las pantallas que usan `getErrorMessage`. **No** propagado a maestros, lotes, trazabilidad, perfil, usuarios (B-15).
- `house_id` para lotes autocreados: cubierto solo en `bird_reception` (F-01e AC65 «otros tipos sin cambio»). Los seis tipos de B-04 siguen expuestos.
- `NaN` → ausencia: cubierto para números; **no** para `''` de `<input type=number>` sin `valueAsNumber` (B-05) ni para `''` en `extra_data` (B-11).

---

## Contadores

Clasificación: **CORRECT** = payload conforme al contrato del backend (pueden quedar P3); **MALFORMED-DEFAULT** = valores por omisión/filas vacías que viajan; **WRONG-FIELD** = propiedad, valor, estructura, unidad o derivación errónea; **422/RENDER** = rechazo de validación (cliente o servidor) o render de error roto.

Tipos de evento (26): CORRECT 15 (`bird_reception`, `water_consumption`, `mortality_recording`, `cull_recording`, `vaccination`, `medication`, `farm_inspection`, `hatchery_inspection`, `egg_collection`, `egg_classification` n/a, `egg_reception_classification`, `egg_dispatch`, `incubation_load`, `transfer_to_hatcher`, `lot_closure`) · MALFORMED-DEFAULT 1 (`transport_inspection`) · WRONG-FIELD 7 (`bird_distribution`, `bird_transfer`, `bird_exit`, `feed_registration`, `weight_recording`, `ovoscopy`, `chick_dispatch`) · 422/RENDER 3 (`egg_reception_hatchery`, `birth_registration`, `grandparent_import`).

Otras superficies (42): CORRECT 30 · WRONG-FIELD 3 (`LotFormPage`, `LotDetailPage` fase, `ReviewCenter`) · 422/RENDER 9 (maestros `farms`, `houses`, `hatcheries`, `incubators`, `hatchers`, `productive-phases`; `UsersPage`; `TraceabilityTree` huevos y pollitos).

**FORMS AUDITED: 68 · CORRECT: 45 · MALFORMED-DEFAULT: 1 · WRONG-FIELD: 10 · 422/RENDER: 12**

Registro: 41 defectos (P1: 8 · P2: 8 · P3: 24 · conocido/referencia: 1 [B-23/R-146]). Todo lo anterior es análisis estático; los P1 marcados como inferencia (B-05) requieren confirmación en runtime antes de la sensibilidad.
