# SAP-0 · SAP_INBOUND_DATA_CATALOG

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY — catálogo formal de los 12 objetos inbound, §14 del mandato)
Ningún contrato se considera implementado ni acordado con SAP: **CURRENT_SAP_VALIDATION = PENDING** en todos.

Convenciones: clave canónica = clave estable en GA; `TENANT` = empresa multi-compañía GA (`companies`); `BU` = unidad de negocio (`business_units`, OD-09); todo objeto lleva además las columnas RAW (§`SAP_RAW_STAGING_SPEC.md`).

---

## 1 · SAP_COMPANY

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Sociedad/Compañía SAP (BUKRS / Company Code) |
| LEGACY_SOURCE | `MATDOC.BUKRS` (leído, mal etiquetado «Centro de Entrega»), inferido de mandante `120` |
| LEGACY_KEY | `BUKRS` |
| TARGET_CANONICAL_KEY | `companies.sap_company_code` (propuesta; hoy **no existe**) |
| FIELDS_REQUIRED | company_code, name, country, currency, mandant |
| CURRENT_GA_ENTITY/FIELD | `companies` (name, approval_levels; **sin clave SAP**) — PL-05 |
| SOURCE_OF_TRUTH | SAP (a definir en OD-24/AOD-06) |
| SYNC_MODE | snapshot (maestro) |
| DELTA_CANDIDATE | last-changed date si existe tabla CDS/BUKRS_T001; else snapshot completo |
| TENANT_MAPPING | `company_code → tenant(companies)` 1:1 |
| BU_MAPPING | por regla Owner (una compañía puede tener N BU) |
| VALIDATION_REQUIRED | alta/modificación/baja; colisiones de nombre; estado `NO USAR` legacy |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 2 · SAP_PLANT

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Centro (WERKS / Plant) — granjas, incubadora, plantas |
| LEGACY_SOURCE | `T001W` (WERKS, NAME1, NAME2; filtro `%NO USAR%`, exclusiones) |
| LEGACY_KEY | `WERKS` |
| TARGET_CANONICAL_KEY | `farms.sap_plant_code` (propuesta) |
| FIELDS_REQUIRED | plant, name1, name2, company_code, address, mandant, active_flag |
| CURRENT_GA_ENTITY/FIELD | `farms.code/name` (PL-06, sin clave SAP) |
| SOURCE_OF_TRUTH | SAP (OD-24 post-P-08) |
| SYNC_MODE | snapshot + delta |
| DELTA_CANDIDATE | campo cambio (`AEDAT` no existe en T001W estándar; usar snapshot en v0) |
| TENANT_MAPPING | vía company_code de la planta |
| BU_MAPPING | planta→granja→BU dueña del lote |
| VALIDATION_REQUIRED | clasificación granja vs planta productiva vs incubadora; `NO USAR` |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 3 · SAP_STORAGE_LOCATION

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Almacén (LGORT / Storage Location) — hipótesis legacy: galpón |
| LEGACY_SOURCE | `T001L` (LGORT, LGOBE, WERKS) |
| LEGACY_KEY | `WERKS+LGORT` |
| TARGET_CANONICAL_KEY | `houses.sap_storage_location` (propuesta) |
| FIELDS_REQUIRED | plant, storage_location, description, mandant, active_flag |
| CURRENT_GA_ENTITY/FIELD | `houses.code/name` (PL-07) |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot + delta |
| DELTA_CANDIDATE | snapshot v0 |
| TENANT_MAPPING | vía planta |
| BU_MAPPING | vía planta→granja |
| VALIDATION_REQUIRED | **decisión clave**: ¿LGORT = galpón? (SAP-STO-01 / AOD-02) |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 4 · SAP_VENDOR

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Proveedor / Business Partner (LIFNR) |
| LEGACY_SOURCE | `LFA1` (LIFNR, NAME1) — usado también como «transportes» |
| LEGACY_KEY | `LIFNR` |
| TARGET_CANONICAL_KEY | `suppliers.sap_code` (existe, opcional) |
| FIELDS_REQUIRED | vendor, name1, tax_id, country, mandant, blocked_flag |
| CURRENT_GA_ENTITY/FIELD | `suppliers.sap_code` (PL-04) + espejo `sap_references.VENDOR` |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot + delta |
| DELTA_CANDIDATE | campo de cambio BP si existe; snapshot v0 |
| TENANT_MAPPING | por company_code de compras |
| BU_MAPPING | compra asignada a BU según lote/granja destino |
| VALIDATION_REQUIRED | duplicidad LFA1/BP (CVI); legacy mezclaba proveedor/transporte |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 5 · SAP_MATERIAL

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Material (MATNR) — alimento, aves, huevo fértil, pollito, insumos sanitarios |
| LEGACY_SOURCE | Listas duras `MATNR` en `querysHana.py`; descripción `MAKT.MAKTX` |
| LEGACY_KEY | `MATNR` (18 díg., con ceros) |
| TARGET_CANONICAL_KEY | `feed_types.sap_material_code`, `vaccines.sap_material_code`, `medications.sap_material_code`, mapeo aves |
| FIELDS_REQUIRED | material, description, material_type, base_uom, material_group, mandant, status |
| CURRENT_GA_ENTITY/FIELD | PL-01/02/03 (sin clave SAP) |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot + delta |
| DELTA_CANDIDATE | MATERIAL master change docs / snapshot |
| TENANT_MAPPING | mandante→tenant |
| BU_MAPPING | por tipo/material |
| VALIDATION_REQUIRED | **NO crear reglas automáticas por `MATNR`** (mandato §13): el mapeo material↔dominio es decisión de negocio |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 6 · SAP_PURCHASE_ORDER

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Orden de compra (EKKO) |
| LEGACY_SOURCE | `EKKO` (EBELN, LIFNR) join `EKPO` |
| LEGACY_KEY | `EBELN` |
| TARGET_CANONICAL_KEY | `sap_references.sap_code` (PURCHASE_ORDER) |
| FIELDS_REQUIRED | ebeln, vendor, company_code, doc_date, doc_type, currency, status, mandant |
| CURRENT_GA_ENTITY/FIELD | `sap_references` tipo `PURCHASE_ORDER` (+`quantity`); consumido por BR-18 |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot + delta |
| DELTA_CANDIDATE | fecha de cambio de cabecera (EKKO no estándar: usar CDS/queues si existen) |
| TENANT_MAPPING | vía company_code |
| BU_MAPPING | vía centro de la posición |
| VALIDATION_REQUIRED | vigencia/estado, clase de documento |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 7 · SAP_PURCHASE_ORDER_ITEM

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Posición OC (EKPO) |
| LEGACY_SOURCE | `EKPO` (EBELN, UNIQUEID→id_sap, MATNR, WERKS, MENGE, AEDAT); autorrelación machos/hembras |
| LEGACY_KEY | `EBELN+EBELP` (legacy usaba `UNIQUEID`) |
| TARGET_CANONICAL_KEY | `sap_references.extra.sap_po_item_code` (espejo por definir) |
| FIELDS_REQUIRED | ebeln, ebelp, material, plant, quantity, uom, net_price, delivery_date |
| CURRENT_GA_ENTITY/FIELD | no existe a nivel posición (solo cabecera) |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot + delta |
| DELTA_CANDIDATE | junto con cabecera (v0: snapshot) |
| TENANT_MAPPING | vía cabecera |
| BU_MAPPING | vía plant |
| VALIDATION_REQUIRED | cantidades por sexo (machos/hembras) no se resuelven por reglas automáticas |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 8 · SAP_PURCHASE_ORDER_HISTORY

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Pedido (EKBE) / historial de OC |
| LEGACY_SOURCE | `EKBE` (prueba de lectura; `EBELN`) |
| LEGACY_KEY | `EBELN+EBELP+ZEKKN` (estándar) |
| TARGET_CANONICAL_KEY | por definir (reconciliación de recepciones, no maestro) |
| FIELDS_REQUIRED | ebeln, ebelp, bewtp, menge, budat, belnr, bwart |
| CURRENT_GA_ENTITY/FIELD | no existe |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | delta por documento |
| DELTA_CANDIDATE | sí (fecha del pedido) |
| TENANT_MAPPING | vía cabecera |
| BU_MAPPING | vía plant de la posición |
| VALIDATION_REQUIRED | uso exacto (reconciliación) a decidir |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 9 · SAP_TRANSFER_ORDER

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Orden de transferencia (STO / OT) |
| LEGACY_SOURCE | `MATDOC.EBELN` «la orden es Orden de Transferencia» (alimento) |
| LEGACY_KEY | `EBELN` (STO) |
| TARGET_CANONICAL_KEY | `sap_references` tipo `TRANSFER_ORDER` |
| FIELDS_REQUIRED | ebeln, supplying_plant, receiving_plant, material, quantity, status, doc_date |
| CURRENT_GA_ENTITY/FIELD | `sap_references.TRANSFER_ORDER` (listado, **no consumido** — H360 §5) |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot + delta |
| DELTA_CANDIDATE | por documento (si hay ChangeDocs/CDS) |
| TENANT_MAPPING | vía company_code |
| BU_MAPPING | vía plantas origen/destino |
| VALIDATION_REQUIRED | vínculo OT↔movimientos de material; no validado en legacy |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 10 · SAP_MATERIAL_DOCUMENT

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Documento de material (MATDOC: MBLNR/MJAHR/ZEILE) — corazón del flujo legacy |
| LEGACY_SOURCE | `MATDOC` completo (BWART 641/303, AUFNR, CHARG, UMWRK, ERFMG, SHKZG, BUDAT…) |
| LEGACY_KEY | `MBLNR+MJAHR+ZEILE` |
| TARGET_CANONICAL_KEY | `sap_references.extra` (documento) + reconciliación de eventos GA |
| FIELDS_REQUIRED | mblnr, mjahr, zeile, bwart, matnr, werks, lgort, erfmg, erfme, menge, shkzg, budat, bldat, cpudt, charg, aufnr, umwrk, ebelm/ebeln, usnam, mandt |
| CURRENT_GA_ENTITY/FIELD | **nada equivalente** (GA captura eventos operativos, no documentos SAP) |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | delta por rango (BUDAT/MBLNR watermark) |
| DELTA_CANDIDATE | sí — watermark sobre `CPUDT/BUDAT` |
| TENANT_MAPPING | vía WERKS→planta→compañía |
| BU_MAPPING | vía granja/planta |
| VALIDATION_REQUIRED | semántica de 641/303 y clasificación de negocio (no automática por lista MATNR) |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 11 · SAP_BATCH

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Lote/Batch SAP (`CHARG`, `SAP_BATCH`) |
| LEGACY_SOURCE | `MATDOC.CHARG` (leído, sin persistencias propias) |
| LEGACY_KEY | `MATNR+CHARG` (batch key estándar) |
| TARGET_CANONICAL_KEY | `lots.lot_code` / `sap_references.SAP_BATCH` |
| FIELDS_REQUIRED | material, batch, plant, expiry_date, production_date, status, mandant |
| CURRENT_GA_ENTITY/FIELD | `sap_references.SAP_BATCH` (no consumido); `lots.lot_code` sin clave SAP (H360-S05) |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot + delta por documento |
| DELTA_CANDIDATE | vía documentos (batch sin tabla de cambio directa) |
| TENANT_MAPPING | vía planta |
| BU_MAPPING | vía granja |
| VALIDATION_REQUIRED | lote productivo (AOD-03) vs batch SAP: **decisión de negocio**, no equivalencia automática |
| CURRENT_SAP_VALIDATION | **PENDING** |

## 12 · SAP_COST_CENTER

| Campo | Valor |
|---|---|
| BUSINESS_OBJECT | Centro de costo (KOSTL / CSKS) |
| LEGACY_SOURCE | **nunca leído** en legacy |
| LEGACY_KEY | `KOSTL` (+ controlling area) |
| TARGET_CANONICAL_KEY | `sap_references.COST_CENTER` |
| FIELDS_REQUIRED | kostl, kokrs, name, company_code, valid_from/to, mandant |
| CURRENT_GA_ENTITY/FIELD | `sap_references.COST_CENTER` (no consumido) |
| SOURCE_OF_TRUTH | SAP |
| SYNC_MODE | snapshot |
| DELTA_CANDIDATE | snapshot v0 |
| TENANT_MAPPING | vía company_code |
| BU_MAPPING | por regla de control (futuro CO) |
| VALIDATION_REQUIRED | uso de cost center en envíos (WAVE D) |
| CURRENT_SAP_VALIDATION | **PENDING** |

---

## 13 · Trazabilidad AC-SAP0-03/04

- 12 objetos identificados y tipados: **AC-SAP0-04 ✔** (este documento).
- Matriz SOURCE→CANONICAL: **AC-SAP0-05 ✔** (`SAP_LEGACY_TO_CURRENT_MAPPING_MATRIX.md` + campos `LEGACY_SOURCE`/`TARGET_CANONICAL_KEY` aquí).
- `CURRENT_SAP_VALIDATION` uniforme `PENDING`: ninguna regla del legacy se eleva a contrato sin validación current (AC-SAP0-08/09).
