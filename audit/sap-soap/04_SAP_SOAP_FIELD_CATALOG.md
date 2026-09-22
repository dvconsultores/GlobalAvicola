# SAP-SOAP · 04_SAP_SOAP_FIELD_CATALOG

Fecha: 2026-09-22 · Campos por objeto inbound (13) · Notación: `C(n)` char · `N(n)` numérico-texto · `D` fecha `YYYY-MM-DD` · `TS` timestamp ISO-8601 · `DEC(13,3)` · `BOOL`
**Obligatoriedad**: R=requerido · O=opcional. Columnas KEY/FILTRO indican clave de registro y campos usables como filtro (§8). Todo objeto lleva además la metadata de integración RAW (§26, ver `10_…`).

---

## 1 · SAP_COMPANY (`GetCompanies`)

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| MANDT | C(3) | R | filtro | mandante de origen |
| COMPANY_CODE | C(4) | R | **KEY**/filtro | BUKRS |
| NAME | C(60) | R | | razón social |
| COUNTRY | C(3) | R | | ISO país |
| CURRENCY | C(3) | R | | moneda local |
| ACTIVE_STATUS | C(1) | R | filtro | ACTIVE/INACTIVE |
| CHANGED_AT | TS | O | delta | si SAP lo expone |

Metadata: delta=`ChangedSince`; tenant=`MANDT/COMPANY_CODE`; GA target=`companies.sap_company_code`. SOURCE_OF_TRUTH=SAP (OD-24).

## 2 · SAP_PLANT (`GetPlants`)

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| MANDT | C(3) | R | filtro | |
| COMPANY_CODE | C(4) | R | filtro | |
| PLANT | C(4) | R | **KEY**/filtro | WERKS |
| NAME1 | C(40) | R | | |
| NAME2 | C(40) | O | | |
| ADDRESS | C(120) | O | | concatenada |
| ACTIVE_STATUS | C(1) | R | filtro | |
| PLANT_CATEGORY_HINT | C(16) | O | | pista de clasificación; **GA clasifica** (no asumir “todo WERKS = granja”) |

Metadata: delta=snapshot/ChangedSince; GA target=`farms.sap_plant_code`; clasificación en GA (`SAP-CLASS-01`).

## 3 · SAP_STORAGE_LOCATION (`GetStorageLocations`)

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| MANDT | C(3) | R | filtro | |
| PLANT | C(4) | R | **KEY**/filtro | |
| STORAGE_LOCATION | C(4) | R | **KEY**/filtro | LGORT |
| NAME | C(16) | R | | LGOBE |
| ACTIVE_STATUS | C(1) | R | | |

Metadata: clave `WERKS+LGORT`; **LGORT ≠ GALPÓN** — mapping configurable/funcional (SAP-STO-01; `SAP0P_STORAGE_LOCATION_FINDINGS` no resuelve semántica).

## 4 · SAP_VENDOR (`GetVendors`)

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| MANDT | C(3) | R | filtro | |
| VENDOR | C(10) | R | **KEY**/filtro | LIFNR / BP |
| NAME1 | C(40) | R | | |
| TAX_ID | C(20) | O | | |
| COUNTRY | C(3) | O | | |
| BLOCKED_FLAG | BOOL | O | filtro | |
| COMPANY_SCOPE | C(4)[] | O | filtro | si aplica por sociedad |
| ACTIVE_STATUS | C(1) | R | | |

Open item: si SAP usa **Business Partner/CVI** (OI-09). Histórico legacy mezclaba proveedor/transporte en `LFA1`.

## 5 · SAP_MATERIAL (`GetMaterials`)

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| MANDT | C(3) | R | filtro | |
| MATERIAL | C(18) | R | **KEY**/filtro | MATNR (con ceros significativos) |
| DESCRIPTION | C(40) | R | | MAKTX (idioma de `Language`) |
| MATERIAL_TYPE | C(4) | R | | tipo material |
| MATERIAL_GROUP | C(9) | O | | grupo |
| BASE_UOM | C(3) | R | | MEINS base |
| STATUS | C(2) | R | filtro | activo/bloqueado |

**No hardcodear MATNR** (§14). GA resuelve categorías por **mapping propio**: FEED · MEDICINE · VACCINE · BIRD · EGG · CHICK · OTHER.

## 6 · SAP_PURCHASE_ORDER (`GetPurchaseOrders`)

Header:

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| MANDT | C(3) | R | filtro | |
| PO_NUMBER | C(10) | R | **KEY**/filtro | EBELN |
| COMPANY_CODE | C(4) | R | filtro | BUKRS |
| VENDOR | C(10) | R | filtro | LIFNR |
| DOCUMENT_TYPE | C(4) | R | | BSART |
| DOCUMENT_DATE | D | R | filtro fechas | BEDAT |
| CURRENCY | C(3) | R | | |
| STATUS | C(4) | O | filtro | (si SAP lo expone) |

Items (anidados):

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| PO_ITEM | N(5) | R | **KEY2** | EBELP |
| MATERIAL | C(18) | R | filtro | MATNR |
| PLANT | C(4) | R | filtro | WERKS |
| STORAGE_LOCATION | C(4) | O | | LGORT si aplica |
| QUANTITY | DEC(13,3) | R | | MENGE |
| UNIT | C(3) | R | | MEINS |
| DELIVERY_DATE | D | O | | |
| DELETED_FLAG | BOOL | O | | |

**Prohibido** el patrón legacy macho/hembra por MATNR hardcodeado: cada ítem trae su `MATERIAL`; GA categoriza.

## 7 · SAP_PURCHASE_ORDER_HISTORY (`GetPurchaseOrderHistory`)

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| EBELN | C(10) | R | **KEY**/filtro | |
| EBELP | N(5) | R | **KEY** | |
| MATERIAL_DOCUMENT | C(10) | R | **KEY** | BELNR |
| DOCUMENT_ITEM | N(4) | O | KEY3 | ZEILE si existe |
| TRANSACTION_TYPE | C(2) | R | | BEWTP |
| MOVEMENT_TYPE | C(3) | O | | BWART |
| QUANTITY | DEC(13,3) | R | | |
| UNIT | C(3) | R | | |
| POSTING_DATE | D | R | filtro fechas | BUDAT |
| REVERSAL_REFERENCE | C(10) | O | | reverso |
| **Objetivo** | | | | reconciliar ordered/received/reversed/pending (§16) |

## 8 · SAP_PRODUCTION_ORDER (`GetProductionOrders`)

Campos **candidatos** (§17 — validar con procesos GA antes de fijar): AUFNR (KEY), WERKS, MATERIAL, BATCH(O), START_DATE, END_DATE, PLANNED_QUANTITY, UNIT, STATUS, SOURCE_STORAGE(O), DESTINATION_STORAGE(O).
Nota: no asumir campos; el proveedor confirma disponibilidad real; GA fija los que sus procesos necesitan (huevo→incubación, pollito, etc.).

## 9 · SAP_OUTBOUND_ORDER (`GetOutboundOrders`)

| FIELD | TYPE | REQ | KEY/FILTRO | NOTES |
|---|---|---|---|---|
| ORDER_NUMBER | C(12) | R | **KEY**/filtro | abstracción (puede originarse en prod order/STO/doc material) |
| DOCUMENT_TYPE | C(4) | R | | |
| SOURCE_PLANT | C(4) | R | filtro | |
| DESTINATION_PLANT | C(4) | O | filtro | |
| SOURCE_STORAGE | C(4) | O | | |
| DESTINATION_STORAGE | C(4) | O | | |
| MATERIAL | C(18) | R | filtro | |
| BATCH | C(10) | O | | |
| QUANTITY | DEC(13,3) | R | | |
| UNIT | C(3) | R | | |
| DOCUMENT_DATE | D | R | filtro | |
| POSTING_DATE | D | O | filtro | |
| STATUS | C(4) | R | filtro | |
| PRODUCTION_ORDER | C(12) | O | | origen si aplica |
| PURCHASE_ORDER | C(10) | O | | origen si aplica |
| TRANSFER_ORDER | C(10) | O | | origen si aplica |

El servicio **abstrae** la tabla interna SAP (§18).

## 10 · SAP_TRANSFER_ORDER (`GetTransferOrders`)

Contrato común (§19): TransferNumber (KEY), DocumentNumber, MovementType, Material, MaterialDescription(O), Batch(O), SourceCompany, SourcePlant, SourceStorage(O), DestinationCompany, DestinationPlant, DestinationStorage(O), Quantity, Unit, DocumentDate, PostingDate, ProductionOrder(O), PurchaseOrder(O), TransferOrder ref, Status.
Cobertura por categoría (FOOD/MEDICINE/VACCINE/BIRDS/EGGS/CHICKS) vía **mapping de materiales GA**, nunca por listas MATNR.

## 11 · SAP_MATERIAL_MOVEMENT (`GetMaterialMovements`)

DTO de negocio (§20 — **no** exigir MATDOC directo). Campos requeridos por GA: MBLNR MATERIAL_DOCUMENT (KEY), YEAR (KEY), DOCUMENT_ITEM (KEY), MOVEMENT_TYPE, MATERIAL, PLANT, STORAGE_LOCATION, DESTINATION_PLANT(O), BATCH(O), QUANTITY(ERFMG), UNIT(ERFME), QUANTITY_BASE(O, MENGE), DEBIT_CREDIT(SHKZG), POSTING_DATE(BUDAT), DOCUMENT_DATE(BLDAT), ENTRY_DATE(O, CPUDT), PRODUCTION_ORDER(O), PO_REFERENCE(O), COMPANY_CODE.
Restricción (§29 del mandato): MATDOC masiva → **ventana obligatoria** + paginación; nunca full scan.

## 12 · SAP_BATCH (`GetBatches`)

MATERIAL (KEY), PLANT (KEY), BATCH (KEY), EXPIRY_DATE(O), PRODUCTION_DATE(O), STATUS(O), CHANGED_AT(O).
Delta: vía movimientos o `ChangedSince` si disponible.

## 13 · COST_CENTER (DEFERIDO — §5)

Campos si entra en fase posterior: KOSTL(KEY), KOKRS, NAME, COMPANY_CODE, VALID_FROM/TO, MANDT. **No incluido en fase 1** (decisión en `02_…` §3; confirmación Owner/Proveedor OI-11).

---

## Matriz campo→GA (resumen)

| SAP | GA target | Regla |
|---|---|---|
| COMPANY_CODE | `companies.sap_company_code` | fail-closed |
| PLANT | `farms.sap_plant_code` | clasificación GA |
| STORAGE_LOCATION | `houses.sap_storage_location` (propuesta) | mapping configurable |
| VENDOR | `suppliers.sap_code` / `sap_references.VENDOR` | una representación |
| MATERIAL | `*_type.sap_material_code` + categoría GA | mapping GA |
| PO/ITEM | `sap_references.PURCHASE_ORDER` (+extra) | — |
| TRANSFER | `sap_references.TRANSFER_ORDER` | — |
| BATCH | `sap_references.SAP_BATCH` / `lots` | decisión AOD-03 pendiente |
