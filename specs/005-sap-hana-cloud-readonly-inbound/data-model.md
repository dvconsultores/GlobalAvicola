# Data Model — SPEC 005

**Migración**: `d9e0f1a2b3c4_sap_hana_inbound` (revisa `c8d9e0f1a2b3`) · aditiva · `downgrade` funcional · sin enums PostgreSQL nuevos (estados `String`)

---

## 1 · `sap_inbound_sync_jobs` — un job por (petición, objeto)

| Columna | Tipo | Nota |
|---|---|---|
| `id` | PK | |
| `sync_request_id` | String(36) | agrupa los jobs de una misma petición |
| `company_id` | FK `companies` | empresa efectiva; nunca nula (R-201) |
| `source_system` | String(30) | `SAP_HANA_CLOUD` |
| `object_type` | String(40) | valor de `HanaObject` |
| `query_id` | String(60) | definición ejecutada |
| `trigger` | String(20) | `manual` \| `scheduled` |
| `status` | String(20) | `in_progress` \| `completed` \| `partial` \| `failed` \| `skipped` |
| `filters` | JSONB | filtros saneados (sin secretos) |
| `watermark_from` / `watermark_to` | String(40) | ventana aplicada |
| `rows_read, rows_raw, rows_noop, rows_valid, rows_invalid, rows_pending_mapping, rows_promoted, rows_rejected` | Integer | contadores |
| `error_code` / `error_message` | String(60) / Text | error saneado |
| `initiated_by_id` | FK `users`, nullable | nulo = scheduler |
| `started_at` / `completed_at` / `created_at` | timestamptz | |

## 2 · `sap_inbound_records` — RAW + capa STAGING

| Columna | Tipo | Nota |
|---|---|---|
| `id` | PK | |
| `sync_job_id` | FK `sap_inbound_sync_jobs` | job que produjo esta versión |
| `company_id` | FK `companies` | inquilino en cuyo contexto se extrajo |
| `source_system` | String(30) | |
| `object_type` | String(40) | |
| `source_key` | String(200) | campos clave unidos con `\|`, mandante primero |
| `client` / `company_code` / `plant_code` | String(3/4/4), nullable | desnormalizados para aislamiento y filtrado |
| `payload_json` | JSONB | fila original normalizada; **inmutable** |
| `payload_hash` | String(64) | SHA-256 del JSON canónico |
| `version` | Integer | 1, 2, … |
| `is_current` | Boolean | una sola versión vigente por clave |
| `source_changed_at` | timestamptz, nullable | si el origen lo expone |
| `extracted_at` | timestamptz | |
| `validation_status` | String(20) | `PENDING` \| `VALID` \| `INVALID` |
| `mapping_status` | String(20) | `PENDING` \| `MAPPED` \| `PENDING_MAPPING` |
| `promotion_status` | String(30) | `PENDING` \| `READY_FOR_PROMOTION` \| `PROMOTED` \| `STAGED_ONLY` \| `BLOCKED` \| `SUPERSEDED` |
| `staged_json` | JSONB, nullable | DTO de negocio tipado (STAGING) |
| `promoted_reference_id` | Integer, nullable | `sap_references.id` (referencia blanda) |
| `error_code` / `error_message` | String(60) / Text | |
| `created_at` / `updated_at` | timestamptz | |

Índices: único `(company_id, source_system, object_type, source_key, version)`; único parcial `(company_id, source_system, object_type, source_key) WHERE is_current`; `(company_id, object_type, promotion_status)`; `(company_id, object_type, mapping_status)`; `(sync_job_id)`; `(company_id, error_code)`.

**Idempotencia**: se compara con la versión vigente. Mismo hash ⇒ no-op (ni fila ni actualización). Hash distinto ⇒ la vigente pasa a `is_current=false` / `SUPERSEDED` y se inserta `version + 1`.

## 3 · `sap_inbound_watermarks`

| Columna | Tipo | Nota |
|---|---|---|
| `id` | PK | |
| `company_id` | FK `companies` | |
| `source_system` / `object_type` | String | |
| `scope_key` | String(120) | `client:<MANDT>\|bukrs:<BUKRS>` |
| `watermark_value` | String(40) | fecha `YYYYMMDD` (ventana) o instante ISO (snapshot) |
| `last_success_at` | timestamptz | |
| `last_record_count` | Integer | |
| `created_at` / `updated_at` | timestamptz | |

Único `(company_id, source_system, object_type, scope_key)`. Solo se escribe dentro del savepoint del objeto, después de persistir sus filas.

## 4 · `sap_entity_mappings` — `MANDT → BUKRS → WERKS → empresa GA`

| Columna | Tipo | Nota |
|---|---|---|
| `id` | PK | |
| `source_system` | String(30) | |
| `client` | String(3) | mandante |
| `entity_type` | String(30) | `COMPANY_CODE` \| `PLANT` \| `STORAGE_LOCATION` |
| `sap_key` | String(40) | `BUKRS`; `WERKS`; `WERKS/LGORT` |
| `parent_sap_key` | String(40), nullable | `PLANT` → su `BUKRS` |
| `company_id` | FK `companies` | inquilino dueño |
| `farm_id` | FK `farms`, nullable | OD-24 `Plant ↔ Farm`, explícito |
| `house_id` | FK `houses`, nullable | solo por decisión expresa (`LGORT ≠ galpón`) |
| `business_unit_code` | String(30), nullable | informativo; no concede acceso (OD-16.c) |
| `is_active` | Boolean | |
| `created_by_id` | FK `users`, nullable | |
| `created_at` / `updated_at` | timestamptz | |

Único `(source_system, client, entity_type, sap_key)`: una sociedad o un centro SAP pertenece a **una sola** empresa GA.

## 5 · Claves de origen por objeto

| Objeto | `source_key` |
|---|---|
| `company` | `MANDT\|BUKRS` |
| `plant` | `MANDT\|WERKS` |
| `storage_location` | `MANDT\|WERKS\|LGORT` |
| `vendor` | `MANDT\|LIFNR` |
| `material` | `MANDT\|MATNR` |
| `batch` | `MANDT\|MATNR\|WERKS\|CHARG` |
| `movement_type` | `MANDT\|BWART` |
| `purchase_order` | `MANDT\|EBELN` |
| `purchase_order_item` | `MANDT\|EBELN\|EBELP` |
| `purchase_order_history` | `MANDT\|EBELN\|EBELP\|ZEKKN\|VGABE\|GJAHR\|BELNR\|BUZEI` |
| `production_order` | `MANDT\|AUFNR` |
| `transfer_order` | `MANDT\|EBELN\|EBELP` |
| `outbound_order` | `MANDT\|VBELN\|POSNR` |
| `material_movement` | `MANDT\|MBLNR\|MJAHR\|ZEILE` |

## 6 · Promoción a `sap_references` (tabla existente, sin cambios de esquema)

| Objeto(s) | `ref_type` | `sap_code` | `quantity` / `unit` |
|---|---|---|---|
| `purchase_order` + ítems + historial | `PURCHASE_ORDER` | `EBELN` | Σ ítems activos de unidad homogénea |
| `transfer_order` (agrupado por `EBELN`) | `TRANSFER_ORDER` | `EBELN` | Σ si la unidad es homogénea; si no, nulo |
| `material` | `MATERIAL` | `MATNR` | unidad base |
| `vendor` | `VENDOR` | `LIFNR` | — |
| `plant` | `PLANT` | `WERKS` | — |
| `storage_location` | `STORAGE_LOCATION` | `WERKS-LGORT` | — |
| `batch` | `SAP_BATCH` | `MATNR/WERKS/CHARG` | — |

`extra_data` siempre incluye `source = "SAP_HANA_CLOUD"`, `client`, `company_code`, `inbound_record_id`, `payload_hash` y `synced_at`. En OC añade `vendor`, `vendor_name`, `document_type`, `document_date`, `items[]`, `ordered_quantity`, `received_quantity` y `history_summary`.

## 7 · Tablas no modificadas

`sap_references`, `sap_sync_jobs`, `sap_payloads`, `sap_responses`, `consolidated_movements`, `companies`, `farms`, `houses`, `suppliers`. No se borra ni se converge ningún maestro local (OD-24).
