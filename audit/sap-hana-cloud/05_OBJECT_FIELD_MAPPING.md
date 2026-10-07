# SAP-HANA-CLOUD · 05_OBJECT_FIELD_MAPPING

Fecha: 2026-10-06 · SPEC 005 · **Generado desde** `registry.py` y `staging.py` (no se edita a mano)

Campo SAP (RAW, `payload_json`) → campo del DTO de negocio (STAGING, `staged_json`). «derivado» = se calcula a partir de otros campos; «bandera» = cualquier valor no vacío es verdadero.

---

## `company` (`company.v1`)

Destino: staging (`STAGED_ONLY`)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `company_code` | `BUKRS` | sí |
| `name` | `BUTXT` | sí |
| `city` | `ORT01` | no |
| `country` | `LAND1` | no |
| `currency` | `WAERS` | no |

`MANDT` va en `client` y en la clave de origen, no en el DTO.

## `plant` (`plant.v1`)

Destino: `sap_references` · `plant`

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `plant` | `WERKS` | sí |
| `name` | `NAME1` | sí |
| `name2` | `NAME2` | no |
| `city` | `ORT01` | no |
| `country` | `LAND1` | no |
| `company_code` | `BUKRS` | sí |

`MANDT` va en `client` y en la clave de origen, no en el DTO.

## `storage_location` (`storage_location.v1`)

Destino: `sap_references` · `storage_location`

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `plant` | `WERKS` | sí |
| `storage_location` | `LGORT` | sí |
| `name` | `LGOBE` | no |
| `company_code` | `BUKRS` | sí |

`MANDT` va en `client` y en la clave de origen, no en el DTO.

## `vendor` (`vendor.v1`)

Destino: `sap_references` · `vendor`

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `vendor` | `LIFNR` | sí |
| `name` | `NAME1` | sí |
| `tax_id` | `STCD1` | no |
| `country` | `LAND1` | no |
| `blocked` | derivado | — |
| `deleted` | derivado | — |
| `company_code` | `BUKRS` | sí |

Banderas que alimentan campos derivados: `SPERR`, `LOEVM`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## `material` (`material.v1`)

Destino: `sap_references` · `material`

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `material` | `MATNR` | sí |
| `description` | `MAKTX` | no |
| `material_type` | `MTART` | sí |
| `material_group` | `MATKL` | no |
| `base_unit` | `MEINS` | sí |
| `deleted` | derivado | — |
| `changed_at` | `LAEDA` | no |

Banderas que alimentan campos derivados: `LVORM`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## `batch` (`batch.v1`)

Destino: `sap_references` · `sap_batch`

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `material` | `MATNR` | sí |
| `plant` | `WERKS` | sí |
| `batch` | `CHARG` | sí |
| `production_date` | `HSDAT` | no |
| `expiry_date` | `VFDAT` | no |
| `created_at` | `ERSDA` | no |
| `changed_at` | `LAEDA` | no |
| `deleted` | derivado | — |
| `company_code` | `BUKRS` | sí |

Banderas que alimentan campos derivados: `LVORM`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## `movement_type` (`movement_type.v1`)

Destino: staging (`STAGED_ONLY`)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `movement_type` | `BWART` | sí |
| `description` | `BTEXT` | no |

`MANDT` va en `client` y en la clave de origen, no en el DTO.

## `purchase_order` (`purchase_order.v1`)

Destino: `sap_references` · `purchase_order` (compuesta con posiciones e historial)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `po_number` | `EBELN` | sí |
| `company_code` | `BUKRS` | sí |
| `document_category` | `BSTYP` | no |
| `document_type` | `BSART` | no |
| `vendor` | `LIFNR` | sí |
| `purchasing_org` | `EKORG` | no |
| `document_date` | `BEDAT` | sí |
| `created_at` | `AEDAT` | no |
| `currency` | `WAERS` | no |
| `deleted` | derivado | — |
| `status` | derivado | — |

Banderas que alimentan campos derivados: `LOEKZ`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## `purchase_order_item` (`purchase_order_item.v1`)

Destino: anidada en la referencia de su OC (`extra_data.items`)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `po_number` | `EBELN` | sí |
| `item` | `EBELP` | sí |
| `material` | `MATNR` | sí |
| `description` | `TXZ01` | no |
| `plant` | `WERKS` | sí |
| `storage_location` | `LGORT` | no |
| `quantity` | `MENGE` | sí |
| `unit` | `MEINS` | sí |
| `delivery_date` | `EINDT` | no |
| `deleted` | derivado | — |
| `delivery_completed` | derivado | — |
| `company_code` | `BUKRS` | sí |

Banderas que alimentan campos derivados: `LOEKZ`, `ELIKZ`. Usados en campos derivados o solo en la clave: `AEDAT`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## `purchase_order_history` (`purchase_order_history.v1`)

Destino: staging (`STAGED_ONLY`); alimenta `received_quantity` de la OC

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `po_number` | `EBELN` | sí |
| `item` | `EBELP` | sí |
| `account_assignment` | `ZEKKN` | sí |
| `event_type` | `VGABE` | sí |
| `year` | `GJAHR` | sí |
| `document` | `BELNR` | sí |
| `document_item` | `BUZEI` | sí |
| `category` | `BEWTP` | no |
| `movement_type` | `BWART` | no |
| `posting_date` | `BUDAT` | sí |
| `quantity` | `MENGE` | sí |
| `debit_credit` | `SHKZG` | sí |
| `reversal` | derivado | — |
| `material` | `MATNR` | no |
| `plant` | `WERKS` | no |
| `reference_document` | `LFBNR` | no |
| `company_code` | `BUKRS` | sí |

`MANDT` va en `client` y en la clave de origen, no en el DTO.

## `production_order` (`production_order.v1`)

Destino: staging (`STAGED_ONLY`)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `order_number` | `AUFNR` | sí |
| `order_type` | `AUART` | no |
| `company_code` | `BUKRS` | sí |
| `plant` | `WERKS` | sí |
| `material` | `MATNR` | sí |
| `batch` | `CHARG` | no |
| `storage_location` | `LGORT` | no |
| `start_date` | `GSTRP` | no |
| `end_date` | `GLTRP` | no |
| `planned_quantity` | `GAMNG` | sí |
| `unit` | `GMEIN` | sí |
| `status` | derivado | — |
| `created_at` | `ERDAT` | sí |
| `changed_at` | `AEDAT` | no |

Banderas que alimentan campos derivados: `LOEKZ`, `PHAS1`, `PHAS2`, `PHAS3`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## `transfer_order` (`transfer_order.v1`)

Destino: `sap_references` · `transfer_order` (agrupada por documento)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `document` | `EBELN` | sí |
| `item` | `EBELP` | sí |
| `company_code` | `BUKRS` | sí |
| `document_type` | `BSART` | no |
| `source_plant` | `RESWK` | sí |
| `source_storage` | `RESLO` | no |
| `destination_plant` | `WERKS` | sí |
| `destination_storage` | `LGORT` | no |
| `material` | `MATNR` | sí |
| `description` | `TXZ01` | no |
| `quantity` | `MENGE` | sí |
| `unit` | `MEINS` | sí |
| `document_date` | `BEDAT` | no |
| `created_at` | `AEDAT` | no |
| `deleted` | derivado | — |
| `delivery_completed` | derivado | — |
| `status` | derivado | — |

Banderas que alimentan campos derivados: `LOEKZ`, `ELIKZ`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## `outbound_order` (`outbound_order.v1`)

Destino: staging (`STAGED_ONLY`)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `order_number` | `VBELN` | sí |
| `item` | `POSNR` | sí |
| `delivery_type` | `LFART` | no |
| `shipping_point` | `VSTEL` | no |
| `customer` | `KUNNR` | no |
| `planned_goods_issue_date` | `WADAT` | no |
| `actual_goods_issue_date` | `WADAT_IST` | no |
| `created_at` | `ERDAT` | sí |
| `material` | `MATNR` | sí |
| `description` | `ARKTX` | no |
| `plant` | `WERKS` | sí |
| `storage_location` | `LGORT` | no |
| `batch` | `CHARG` | no |
| `quantity` | `LFIMG` | sí |
| `unit` | `VRKME` | sí |
| `reference_document` | `VGBEL` | no |
| `reference_item` | `VGPOS` | no |
| `company_code` | `BUKRS` | sí |
| `status` | derivado | — |

`MANDT` va en `client` y en la clave de origen, no en el DTO.

## `material_movement` (`material_movement.v1`)

Destino: staging (`STAGED_ONLY`)

| Campo DTO | Origen SAP | Obligatorio en la respuesta |
|---|---|---|
| `material_document` | `MBLNR` | sí |
| `year` | `MJAHR` | sí |
| `item` | `ZEILE` | sí |
| `movement_type` | `BWART` | sí |
| `material` | `MATNR` | sí |
| `plant` | `WERKS` | sí |
| `storage_location` | `LGORT` | no |
| `destination_plant` | `UMWRK` | no |
| `destination_storage` | `UMLGO` | no |
| `batch` | `CHARG` | no |
| `quantity` | `ERFMG` | sí |
| `unit` | `ERFME` | sí |
| `quantity_base` | `MENGE` | no |
| `base_unit` | `MEINS` | no |
| `debit_credit` | `SHKZG` | sí |
| `posting_date` | `BUDAT` | sí |
| `document_date` | `BLDAT` | no |
| `entry_date` | `CPUDT` | no |
| `purchase_order` | `EBELN` | no |
| `purchase_order_item` | `EBELP` | no |
| `production_order` | `AUFNR` | no |
| `company_code` | `BUKRS` | sí |
| `reversal_flag` | derivado | — |
| `original_document` | `SMBLN` | no |
| `reversal_reference` | `SMBLN»/«SJAHR»/«SMBLP` | no |

Usados en campos derivados o solo en la clave: `SJAHR`, `SMBLP`. `MANDT` va en `client` y en la clave de origen, no en el DTO.

## Referencia promovida (`sap_references`)

| Objeto | `sap_code` | `description` | `quantity` / `unit` | `extra_data` (además de la traza) |
|---|---|---|---|---|
| `purchase_order` | `EBELN` | descripciones de las posiciones activas | Σ `MENGE` de posiciones no borradas si la unidad es homogénea | `vendor`, `vendor_name`, `document_type`, `document_date`, `purchasing_org`, `currency`, `status`, `ordered_quantity`, `received_quantity`, `history_summary`, `items[]` |
| `transfer_order` | `EBELN` | descripciones de las posiciones | Σ si la unidad es homogénea; si no, nulo y `quantity_status=MIXED_UNITS_NOT_AGGREGATED` | `document_type`, `document_date`, `source_plant`, `destination_plant`, `status`, `items[]` |
| `material` | `MATNR` (18, con ceros) | `MAKTX` | — / `MEINS` | `material_type`, `material_group`, `deleted` |
| `vendor` | `LIFNR` | `NAME1` | — | `tax_id`, `country`, `blocked`, `deleted`, `vendor_name` |
| `plant` | `WERKS` | `NAME1` | — | `name2`, `city`, `country`, `farm_id` y `business_unit_code` solo si el mapping los declara |
| `storage_location` | `WERKS-LGORT` | `LGOBE` | — | `plant`, `storage_location`, `house_id` solo por mapping expreso |
| `batch` | `MATNR/WERKS/CHARG` | `Lote <CHARG> · <WERKS>` | — | `material`, `plant`, `batch`, `production_date`, `expiry_date`, `deleted` |

Traza común en `extra_data`: `source = "SAP_HANA_CLOUD"`, `client`, `company_code`, `inbound_record_id`, `payload_hash`, `synced_at`.
