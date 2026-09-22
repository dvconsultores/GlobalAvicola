# GLOBAL AVÍCOLA
# REUNIÓN TÉCNICA DE INTEGRACIÓN SOAP CON SAP

### Definición de contrato SOAP inbound — Global Avícola ↔ Lider Pollo / Proveedor SAP

---

## 1. PORTADA / IDENTIFICACIÓN

| Campo | Valor |
|---|---|
| **Documento** | Paquete técnico para reunión con proveedor SAP / ABAP |
| **Versión** | 1.0 — Reunión técnica de definición de contrato |
| **Fecha** | **[POR COMPLETAR]** |
| **Lugar / modalidad** | **[POR COMPLETAR]** |
| **Base documental** | SAP-SOAP-1 (CLOSED) · `audit/sap-soap/01…15` · `specs/003-sap-soap-inbound-contract/` · documento cliente-facing v1.0 |
| **Estado** | Documento de trabajo para decisión conjunta — las decisiones abiertas figuran como **PENDIENTE**, nunca como acordadas |

**Participantes**

| Parte | Nombre | Rol |
|---|---|---|
| Lider Pollo | Alexis Aguilar | Gerente de Sistemas |
| Lider Pollo | [otros] | [POR COMPLETAR] |
| Proveedor SAP / ABAP | [nombre] | [rol] |
| Global DV / Global Avícola | Javier Garate | [rol] |
| Global DV / Global Avícola | [otros] | [POR COMPLETAR] |

**Leyenda de estados usada en todo el documento**

| Tag | Significado |
|---|---|
| **ACORDADO** | Decisión ya tomada conjuntamente (reunión de arquitectura) |
| **PROPUESTO** | Propuesta de Global Avícola, sujeta a confirmación |
| **PENDIENTE_PROVEEDOR_SAP** | Requiere respuesta del proveedor SAP/ABAP |
| **PENDIENTE_GLOBAL_AVICOLA** | Requiere trabajo/decisión de Global Avícola |
| **PENDIENTE_DECISION_CONJUNTA** | Se decide en esta reunión |

---

## 2. OBJETIVO DE LA REUNIÓN

Cerrar el **contrato técnico** necesario para que el proveedor SAP construya y exponga los servicios SOAP requeridos por Global Avícola.

La reunión debe permitir acordar:

- operaciones y sus nombres técnicos;
- request / response / campos / tipos de datos / requeridos-opcionales;
- filtros, paginación y sincronización incremental;
- estados y tratamiento de **anulaciones / reversos**;
- seguridad y autenticación; manejo de errores; versionado; límites;
- ambiente de pruebas; WSDL / XSD.

**Salida esperada de la reunión:**

- ☐ `SOAP CONTRACT APPROVED FOR ABAP DEVELOPMENT`
- ☐ `SOAP CONTRACT APPROVED WITH OPEN ITEMS` (con lista residual)

---

## 3. CONTEXTO Y ARQUITECTURA ACORDADA

### 3.1 Modelo anterior (retirado como target)

```
Global Avícola → conexión directa a HANA → SQL/queries → tablas SAP
```
`DIRECT_HANA_TARGET = RETIRED` · los queries históricos (`SapHanaLP`) quedan **únicamente** como referencia funcional.

### 3.2 Modelo nuevo (ACORDADO)

```
SAP / ABAP → SOAP SERVER (WSDL/XSD)
→ Global Avícola SOAP CLIENT
→ RAW → VALIDATION → MAPPING → STAGING → PROMOTION → DOMAIN
```

Declaraciones expresas:

- El **proveedor SAP expone** el servicio (**SOAP SERVER**).
- **Global Avícola consume** el servicio (**SOAP CLIENT**), en modelo **PULL**.
- Global Avícola **NO** ejecutará queries HANA como mecanismo productivo.
- Los queries legacy se entregan solo como referencia para entender filtros y datos necesarios.

> **«EL QUERY NO ES EL CONTRATO.**
> **EL CONTRATO SOAP ES EL CONTRATO.»**

### 3.3 Principios retenidos (no se discuten en esta reunión)

RAW/STAGING (nunca escritura directa al dominio) · adapter pattern · fail-closed multiempresa · idempotencia · auditoría · separación estricta SAP source of truth.

---

## 4. AGENDA TÉCNICA (90 minutos)

| # | Tema | Responsable principal | Tiempo | Resultado esperado |
|---|---|---|---|---|
| 1 | Apertura y objetivo | Global DV | 5 min | Objetivo y salida esperada confirmados |
| 2 | Confirmación arquitectura SOAP PULL | Proveedor SAP | 5 min | SOC-01 registrada (ACORDADO) |
| 3 | Revisión de operaciones SOAP (12+1) | Proveedor SAP + GA | 10 min | Operaciones confirmadas (OI-05 si aplica) |
| 4 | Revisión de catálogo de campos (muestra empresas/plantas/almacenes) | Proveedor SAP + GA | 8 min | Campos validados o marcados TO_CONFIRM |
| 5 | Empresas / centros / almacenes | Proveedor SAP | 6 min | Mapping BUKRS/WERKS/LGORT confirmado |
| 6 | Materiales y proveedores | Proveedor SAP | 6 min | OI-09 (BP/CVI) + campos materiales |
| 7 | Órdenes de compra (header + items) | Proveedor SAP | 6 min | Estructura confirmada |
| 8 | Órdenes de producción | Proveedor SAP | 5 min | OI-10 resuelto |
| 9 | Órdenes de salida | Proveedor SAP | 5 min | OI-08 resuelto (semántica DTO) |
| 10 | Transferencias / movimientos | Proveedor SAP | 6 min | OI-16 (BWART) resuelto |
| 11 | Paginación y delta | Proveedor SAP | 6 min | OI-03 + OI-04 resueltos |
| 12 | Anulaciones / reversos | Proveedor SAP | 4 min | Semántica de reverso definida |
| 13 | Seguridad / autenticación | Proveedor SAP + Seguridad | 5 min | OI-06 resuelto |
| 14 | SOAP Fault / errores | Proveedor SAP | 4 min | OI-13 resuelto (8 códigos) |
| 15 | Versionado WSDL/XSD | Proveedor SAP | 3 min | OI-07 + checklist WSDL |
| 16 | Ambiente de pruebas | Proveedor SAP | 4 min | OI-01 + OI-15 encaminados |
| 17 | Open Items restantes | Ambos | 4 min | Cada OI con estado final |
| 18 | Acuerdos y próximos pasos | Global DV | 4 min | Tabla DEC completada + acta |

---

## 5. PIEZA 1 — RESUMEN TÉCNICO PARA LIDER POLLO / PROVEEDOR SAP

### A. Propósito de la integración

SAP (Lider Pollo) es **source of truth** de maestros y documentos; Global Avícola consume vía SOAP los datos necesarios para operar y reconciliar sus procesos avícolas (empresas, centros, almacenes, materiales, proveedores, órdenes de compra/producción/salida, transferencias, movimientos y lotes), con trazabilidad, idempotencia e integridad end-to-end.

### B. Responsabilidades

**Lider Pollo / Proveedor SAP:**

- Desarrollar el **SOAP server** y la lógica ABAP interna.
- Aplicar los filtros/selección de SAP; exponer **WSDL/XSD**.
- Seguridad/autorización SAP; disponibilidad del endpoint; responder errores SAP.

**Global Avícola:**

- **SOAP client**; validación; **RAW/STAGING**; mapping; idempotencia; multiempresa; auditoría; reconciliación; promoción controlada al dominio.

### C. Objetos inbound de fase 1 (13) — `ACORDADO (prioridades) / PROPUESTO (contrato)`

| # | Objeto | Operación | Prioridad |
|---|---|---|---|
| 1 | SAP_COMPANY | `GetCompanies` | P1 |
| 2 | SAP_PLANT | `GetPlants` | P1 |
| 3 | SAP_STORAGE_LOCATION | `GetStorageLocations` | P1 |
| 4 | SAP_VENDOR | `GetVendors` | P1 |
| 5 | SAP_MATERIAL | `GetMaterials` | P1 |
| 6 | SAP_PURCHASE_ORDER | `GetPurchaseOrders` (header) | P1 |
| 7 | SAP_PURCHASE_ORDER_ITEM | (anidado en `GetPurchaseOrders`) | P1 |
| 8 | SAP_PURCHASE_ORDER_HISTORY | `GetPurchaseOrderHistory` | P1 |
| 9 | SAP_PRODUCTION_ORDER | `GetProductionOrders` | P1 |
| 10 | SAP_OUTBOUND_ORDER | `GetOutboundOrders` | P1 |
| 11 | SAP_TRANSFER_ORDER | `GetTransferOrders` | P1 |
| 12 | SAP_MATERIAL_MOVEMENT | `GetMaterialMovements` | P1 |
| 13 | SAP_BATCH | `GetBatches` | P2 |

*COST_CENTER: fuera de fase 1 (deferido) — `PENDIENTE_DECISION_CONJUNTA` (OI-11).*

### D. Principios de integridad

| Principio | Detalle |
|---|---|
| SAP source of truth | GA no altera datos SAP; solo consume |
| No escritura directa al dominio | `SOAP → RAW → … → PROMOTION → DOMAIN` |
| payload hash | mismo registro = mismo hash; clave+hash igual = no-op; clave igual + hash distinto = nueva versión |
| source key | cada objeto tiene clave estable reconstruible |
| request id | trazabilidad end-to-end (`RequestId` en request y response) |
| schema version | obligatorio (`SchemaVersion`, inicial 1.0) |
| idempotencia | reintentos seguros (solo operaciones read) |
| audit trail | cada job/lote promovido con contadores y errores saneados |
| fail closed | sin resolución de mapping → `PENDING_MAPPING`, sin promoción |
| tenant/company isolation | `MANDT → BUKRS → WERKS → GA COMPANY → BU` |

### E. Qué NO forma parte de esta fase

Global Avícola → SAP (outbound) · creación de documentos SAP · BAPI write · HANA directo · lógica productiva ABAP definida unilateralmente por GA.

---

## 6. PIEZA 2 — CATÁLOGO DE OPERACIONES SOAP Y CAMPOS

**Estados de campos**: `[REQ]` requerido · `[OPT]` opcional · `[TC]` TO_CONFIRM_WITH_SAP.
**Rol del campo**: `(B)` Business field · `(S)` Sap technical reference · `(M)` GA mapping field.

### 6.0 Resumen de operaciones — `PROPUESTO / PENDIENTE_PROVEEDOR_SAP`

| Operación | Objeto | Propósito | Tipo Sync | Prioridad | Estado |
|---|---|---|---|---|---|
| `GetCompanies` | Company | sociedades (BUKRS) | snapshot + delta | P1 | PROPUESTO |
| `GetPlants` | Plant | centros (WERKS) | snapshot + delta | P1 | PROPUESTO |
| `GetStorageLocations` | StorageLocation | almacenes (LGORT por centro) | snapshot | P1 | PROPUESTO |
| `GetVendors` | Vendor | proveedores/BP | snapshot + delta | P1 | PROPUESTO |
| `GetMaterials` | Material | materiales + metadata | snapshot + delta | P1 | PROPUESTO |
| `GetPurchaseOrders` | PO + Items | OC con ítems anidados | delta documental | P1 | PROPUESTO |
| `GetPurchaseOrderHistory` | PO History | pedidos/recepciones OC | delta documental | P1 | PROPUESTO |
| `GetProductionOrders` | ProductionOrder | órdenes de producción | delta documental | P1 | PROPUESTO |
| `GetOutboundOrders` | OutboundOrder | órdenes de salida (DTO) | delta documental | P1 | PROPUESTO |
| `GetTransferOrders` | TransferOrder | transferencias | delta documental | P1 | PROPUESTO |
| `GetMaterialMovements` | MaterialMovement | documentos de material (DTO) | delta + ventana | P1 | PROPUESTO |
| `GetBatches` | Batch | lotes | delta/snapshot | P2 | PROPUESTO |
| `GetIntegrationChanges` | multi-objeto | **opcional**: incremental común | cursor | — | OPCIONAL (OI-05) |

### 6.1 `GetCompanies`

**Propósito**: sociedades (BUKRS) para resolución multiempresa. **ACORDADO**: mapping SAP Company → GA Company (fuente: SAP).

**Request** (`PROPUESTO`):

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| RequestId | C(36) | [REQ] | trazabilidad |
| SchemaVersion | C(8) | [REQ] | versión del contrato |
| ClientSystem | C(16) | [REQ] | `GLOBAL_AVICOLA` |
| ChangedSince | TS | [OPT] | delta |
| PageNumber / PageSize / ContinuationToken | — | [OPT] | paginación |
| Language | C(2) | [OPT] | idioma textos |

**Response** — registro `Company`:

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| MANDT | C(3) | [REQ] | — | mandante (S) |
| COMPANY_CODE | C(4) | [REQ] | **KEY** | BUKRS (S) |
| NAME | C(60) | [REQ] | — | razón social (B) |
| COUNTRY | C(3) | [REQ] | — | país ISO (B) |
| CURRENCY | C(3) | [REQ] | — | moneda local (B) |
| ACTIVE_STATUS | C(1) | [REQ] | — | ACTIVE/INACTIVE (B) |
| CHANGED_AT | TS | [OPT] | — | si SAP lo expone |

**Filtros**: `ChangedSince`, paginación. **Delta**: `ChangedSince` (o snapshot). **Paginación**: estándar (±token). **Claves**: `COMPANY_CODE`. **Dependencias**: raíz de tenant. **OI**: OI-04, OI-07.

### 6.2 `GetPlants`

**Propósito**: centros (WERKS). **Nota expresa**: *Plant no significa automáticamente granja* — GA aplicará mapping/clasificación (`PLANT_CATEGORY_HINT` opcional como pista).

**Request**: igual patrón (RequestId, SchemaVersion, ClientSystem [REQ]; CompanyCode, ChangedSince, Status, paginación, Language [OPT]).

**Response** — registro `Plant`:

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| MANDT | C(3) | [REQ] | — | (S) |
| COMPANY_CODE | C(4) | [REQ] | — | (S) |
| PLANT | C(4) | [REQ] | **KEY** | WERKS (S) |
| NAME1 | C(40) | [REQ] | — | (B) |
| NAME2 | C(40) | [OPT] | — | (B) |
| ADDRESS | C(120) | [OPT] | — | concatenada (B) |
| ACTIVE_STATUS | C(1) | [REQ] | — | (B) |
| PLANT_CATEGORY_HINT | C(16) | [OPT] | — | pista; clasificación final en GA (M) |

**Delta**: snapshot/`ChangedSince`. **Claves**: `PLANT`. **Dependencias**: COMPANY. **OI**: OI-04.

### 6.3 `GetStorageLocations`

**Propósito**: almacenes por centro. **Nota expresa**: `LGORT ≠ GALPÓN` — la relación con galpón es **mapping funcional en GA**.

**Request**: `Plant` [OPT pero al menos uno de Plant/CompanyCode [REQ-lógico]]; resto estándar.

**Response** — registro `StorageLocation`:

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| MANDT | C(3) | [REQ] | — | (S) |
| PLANT | C(4) | [REQ] | **KEY** | (S) |
| STORAGE_LOCATION | C(4) | [REQ] | **KEY** | LGORT (S) |
| NAME | C(16) | [REQ] | — | LGOBE (B) |
| ACTIVE_STATUS | C(1) | [REQ] | — | (B) |

**Claves**: `WERKS+LGORT`. **OI**: ninguna específica (mapping es GA).

### 6.4 `GetVendors`

**Propósito**: proveedores (LIFNR / Business Partner). **PENDIENTE_PROVEEDOR_SAP**: si el sistema usa BP/CVI (OI-09).

**Request**: estándar + `Status` (blocked) [OPT].

**Response** — registro `Vendor`:

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| MANDT | C(3) | [REQ] | — | (S) |
| VENDOR | C(10) | [REQ] | **KEY** | LIFNR (S) |
| NAME1 | C(40) | [REQ] | — | (B) |
| TAX_ID | C(20) | [OPT] | — | (B) |
| COUNTRY | C(3) | [OPT] | — | (B) |
| BLOCKED_FLAG | BOOL | [OPT] | — | (B) |
| COMPANY_SCOPE | C(4)[] | [OPT] | — | si aplica por sociedad |
| ACTIVE_STATUS | C(1) | [REQ] | — | (B) |

**OI**: OI-09 (BP/CVI), OI-04.

### 6.5 `GetMaterials`

**Propósito**: materiales + metadata para interpretar documentos. **Regla**: `MATNR` **no** determina automáticamente categoría; **no** se usa `if MATNR == ...`; la clasificación `FOOD · MEDICINE · VACCINE · BIRD · EGG · CHICK · OTHER` se resuelve por **mapping en GA** (M).

**Request**: estándar + `ChangedSince`, `Status` [OPT].

**Response** — registro `Material`:

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| MANDT | C(3) | [REQ] | — | (S) |
| MATERIAL | C(18) | [REQ] | **KEY** | MATNR con ceros significativos (S) |
| DESCRIPTION | C(40) | [REQ] | — | MAKTX (B) |
| MATERIAL_TYPE | C(4) | [REQ] | — | tipo material (B) |
| MATERIAL_GROUP | C(9) | [OPT] | — | grupo (B) |
| BASE_UOM | C(3) | [REQ] | — | unidad base (B) |
| STATUS | C(2) | [REQ] | — | activo/bloqueado (B) |

**OI**: OI-04. **Dependencia dura** de todos los documentos.

### 6.6 `GetPurchaseOrders` (HEADER + ITEMS)

**HEADER** — registro `PurchaseOrder`:

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| PO_NUMBER | C(10) | [REQ] | **KEY** | EBELN (S) |
| COMPANY_CODE | C(4) | [REQ] | — | BUKRS (S) |
| VENDOR | C(10) | [REQ] | — | LIFNR (S) |
| DOCUMENT_TYPE | C(4) | [REQ] | — | BSART (B) |
| DOCUMENT_DATE | D | [REQ] | filtro | BEDAT (B) |
| CURRENCY | C(3) | [REQ] | — | (B) |
| STATUS | C(4) | [OPT] | filtro | si SAP lo expone (B) |

**ITEMS** — registro `Item` (anidado):

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| PO_ITEM | N(5) | [REQ] | **KEY2** | EBELP (S) |
| MATERIAL | C(18) | [REQ] | — | MATNR (S) |
| PLANT | C(4) | [REQ] | — | WERKS (S) |
| STORAGE_LOCATION | C(4) | [OPT] | — | LGORT si aplica (S) |
| QUANTITY | DEC(13,3) | [REQ] | — | MENGE (B) |
| UNIT | C(3) | [REQ] | — | MEINS (B) |
| DELIVERY_DATE | D | [OPT] | — | (B) |
| DELETED_FLAG | BOOL | [OPT] | — | (B) |

**Filtros**: CompanyCode, FromDate/ToDate, DocumentNumber, Status, ChangedSince. **Delta**: fecha documento / `ChangedSince`. **Claves**: `PO_NUMBER (+PO_ITEM)`. **Nota**: se elimina el patrón legacy macho/hembra por MATNR hardcodeado (cada ítem trae su `MATERIAL`). **OI**: OI-04, OI-12.

### 6.7 `GetPurchaseOrderHistory`

**Propósito**: reconciliar `ordered / received / reversed / pending`.

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| EBELN | C(10) | [REQ] | **KEY** | (S) |
| EBELP | N(5) | [REQ] | **KEY** | (S) |
| MATERIAL_DOCUMENT | C(10) | [REQ] | **KEY** | BELNR (S) |
| DOCUMENT_ITEM | N(4) | [OPT] | KEY3 | ZEILE si existe (S) |
| TRANSACTION_TYPE | C(2) | [REQ] | — | BEWTP (S) |
| MOVEMENT_TYPE | C(3) | [OPT] | — | BWART (S) |
| QUANTITY | DEC(13,3) | [REQ] | — | (B) |
| UNIT | C(3) | [REQ] | — | (B) |
| POSTING_DATE | D | [REQ] | filtro | BUDAT (B) |
| REVERSAL_REFERENCE | C(10) | [OPT] | — | reverso (S) |

**OI**: OI-04, OI-16 (semántica movimiento), OI-13.

### 6.8 `GetProductionOrders`

**Propósito**: órdenes de producción. Campos **candidatos** — `PENDIENTE_PROVEEDOR_SAP` (OI-10): cuáles existen realmente por proceso GA.

| Campo | Tipo | Requerido | Clave |
|---|---|---|---|
| ORDER_NUMBER | C(12) | [REQ] | **KEY** (AUFNR) |
| PLANT | C(4) | [REQ] | — |
| MATERIAL | C(18) | [REQ] | — |
| BATCH | C(10) | [OPT] | — (CHARG) |
| START_DATE / END_DATE | D | [REQ/OPT] | — |
| PLANNED_QUANTITY | DEC(13,3) | [REQ] | — |
| UNIT | C(3) | [REQ] | — |
| STATUS | C(4) | [REQ] | — |
| SOURCE_STORAGE / DESTINATION_STORAGE | C(4) | [OPT] | — |

**OI**: OI-10 (obligatorio).

### 6.9 `GetOutboundOrders`

**Propósito**: órdenes de salida como **BUSINESS DTO** — el servicio **abstrae** la estructura interna SAP (puede originarse en production order, stock transport order, material document u otro objeto). **No** se exige que SAP exponga MATDOC tal cual.

| Campo | Tipo | Requerido | Clave | Descripción |
|---|---|---|---|---|
| ORDER_NUMBER | C(12) | [REQ] | **KEY** | abstracción (B) |
| DOCUMENT_TYPE | C(4) | [REQ] | — | (B) |
| SOURCE_PLANT | C(4) | [REQ] | — | (B) |
| DESTINATION_PLANT | C(4) | [OPT] | — | (B) |
| SOURCE_STORAGE / DESTINATION_STORAGE | C(4) | [OPT] | — | (B) |
| MATERIAL | C(18) | [REQ] | — | (S) |
| BATCH | C(10) | [OPT] | — | (S) |
| QUANTITY / UNIT | DEC, C(3) | [REQ] | — | (B) |
| DOCUMENT_DATE / POSTING_DATE | D | [REQ/OPT] | filtro | (B) |
| STATUS | C(4) | [REQ] | filtro | (B) |
| PRODUCTION_ORDER / PURCHASE_ORDER / TRANSFER_ORDER | C | [OPT] | — | origen si aplica (S) |

**OI**: OI-08 (obligatorio), OI-04.

### 6.10 `GetTransferOrders`

**Propósito**: transferencias de las categorías: **FOOD · MEDICINE · VACCINE · BIRDS · EGGS · CHICKS** (cobertura vía mapping de materiales GA — no por listas MATNR).

| Campo | Tipo | Requerido | Clave |
|---|---|---|---|
| TRANSFER_NUMBER | C(10) | [REQ] | **KEY** |
| DOCUMENT_NUMBER | C(10) | [REQ] | **KEY2** |
| MOVEMENT_TYPE | C(3) | [REQ] | — (BWART, referencia) |
| MATERIAL / MATERIAL_DESCRIPTION | C(18)/C(40) | [REQ]/[OPT] | — |
| BATCH | C(10) | [OPT] | — |
| SOURCE_COMPANY / SOURCE_PLANT / SOURCE_STORAGE | C | [REQ/REQ/OPT] | filtro |
| DESTINATION_COMPANY / DESTINATION_PLANT / DESTINATION_STORAGE | C | [REQ/REQ/OPT] | filtro |
| QUANTITY / UNIT | DEC, C(3) | [REQ] | — |
| DOCUMENT_DATE / POSTING_DATE | D | [REQ] | filtro |
| PRODUCTION_ORDER / PURCHASE_ORDER / TRANSFER_ORDER ref | C | [OPT] | — |
| STATUS | C(4) | [REQ] | filtro |

Referencias SAP disponibles pero **no obligatorias** si el DTO usa campos de negocio equivalentes: `BWART, MBLNR, MATNR, WERKS, LGORT, UMWRK, CHARG, BUDAT, AUFNR, EBELN`.
**OI**: OI-16 (BWART semántica), OI-04.

### 6.11 `GetMaterialMovements`

**Propósito**: documentos de material como **DTO de negocio** (no se exige exponer MATDOC). Ventana temporal **obligatoria**; prohibido full scan.

| Campo | Tipo | Requerido | Clave | Origen SAP ref. |
|---|---|---|---|---|
| MATERIAL_DOCUMENT | C(10) | [REQ] | **KEY** | MBLNR |
| YEAR | C(4) | [REQ] | **KEY** | MJAHR |
| DOCUMENT_ITEM | N(4) | [REQ] | **KEY** | ZEILE |
| MOVEMENT_TYPE | C(3) | [REQ] | — | BWART |
| MATERIAL | C(18) | [REQ] | — | MATNR |
| PLANT | C(4) | [REQ] | — | WERKS |
| STORAGE_LOCATION | C(4) | [REQ] | — | LGORT |
| DESTINATION_PLANT | C(4) | [OPT] | — | UMWRK |
| BATCH | C(10) | [OPT] | — | CHARG |
| QUANTITY / UNIT | DEC(13,3)/C(3) | [REQ] | — | ERFMG / ERFME |
| QUANTITY_BASE | DEC(13,3) | [OPT] | — | MENGE |
| DEBIT_CREDIT | C(1) | [REQ] | — | SHKZG |
| POSTING_DATE / DOCUMENT_DATE | D | [REQ] | filtro | BUDAT / BLDAT |
| ENTRY_DATE | D | [OPT] | — | CPUDT |
| PRODUCTION_ORDER | C(12) | [OPT] | — | AUFNR |
| PO_REFERENCE | C(10) | [OPT] | — | EBELN |
| COMPANY_CODE | C(4) | [REQ] | — | BUKRS |

**OI**: OI-04 (delta), OI-12 (volumen), OI-16.

### 6.12 `GetBatches`

| Campo | Tipo | Requerido | Clave |
|---|---|---|---|
| MATERIAL | C(18) | [REQ] | **KEY** |
| PLANT | C(4) | [REQ] | **KEY** |
| BATCH | C(10) | [REQ] | **KEY** (CHARG) |
| EXPIRY_DATE / PRODUCTION_DATE | D | [OPT] | — |
| STATUS | C(2) | [OPT] | — |
| CHANGED_AT | TS | [OPT] | — |

**OI**: OI-04.

### 6.13 `GetIntegrationChanges` (OPCIONAL — OI-05)

**Propósito**: endpoint incremental común propuesto a ABAP. **PENDIENTE_PROVEEDOR_SAP**: si lo ofrecen y con qué forma. No reemplaza las consultas puntuales por documento (reconciliación/recuperación).

### 6.14 Seguridad — bloque de decisión

| Elemento | Propuesta GA | Decisión reunión | Estado |
|---|---|---|---|
| TLS | HTTPS/TLS 1.2+ obligatorio, certificado válido | — | **PROPUESTO (no aprobado aún)** |
| BasicAuth sobre TLS | aceptable como mínimo | — | **PENDIENTE_DECISION_CONJUNTA** (OI-06) |
| WS-Security UsernameToken | recomendada si ABAP la soporta | — | **PENDIENTE_DECISION_CONJUNTA** (OI-06) |
| mTLS (certificado cliente) | preferida si la infraestructura lo permite | — | **PENDIENTE_DECISION_CONJUNTA** (OI-06) |
| IP allowlist | complemento recomendado | — | **PENDIENTE_DECISION_CONJUNTA** (OI-06) |

Prohibiciones permanentes (no negociables): validación TLS deshabilitada, password en XML custom/URL, credenciales en repo/logs. (Sin passwords en este documento.)

### 6.15 Paginación

- Opción preferida **PROPUESTO**: `ContinuationToken` (opaco, orden estable obligatorio, expiración ≥15 min).
- Fallback aceptado: `PageNumber/PageSize`.
- **`MaximumPageSize` a acordar** (propuesta: **500**).
- Razón: **no se permite respuesta sin límite (unbounded)**; documentos exigen ventana temporal.

### 6.16 Delta

```
INITIAL_SNAPSHOT → DELTA → RECONCILIATION
```
- Contrato funcional: `ChangedSince` (o equivalente propuesto por ABAP) + cursor/watermark.
- ABAP propone internamente **cómo** determina los cambios; GA **no depende** de estructura interna HANA.
- `PENDIENTE_PROVEEDOR_SAP`: campo exacto por objeto (OI-04).

### 6.17 Reversos y anulaciones — bloque de decisión

**Pregunta de reunión**: ¿cómo informa SAP que un documento previamente consultado fue **anulado/reversado**?
Necesidad de contrato (según SPEC): `status` · indicador de reverso · documento de reverso · documento original · timestamp de cambio. **No se inventa resolución** — se define en la reunión y se registra como DEC.

### 6.18 Errores (8 códigos — validar con proveedor, OI-13)

| ErrorCode | Canal | Reintentable |
|---|---|---|
| `AUTHENTICATION_ERROR` | Fault (Client) | No |
| `AUTHORIZATION_ERROR` | Fault (Client) | No |
| `INVALID_FILTER` | Funcional (`Success=false`) | No |
| `OBJECT_NOT_FOUND` | Funcional | No |
| `SAP_INTERNAL_ERROR` | Fault (Server) | Sí (backoff) |
| `TIMEOUT` | Fault / timeout transporte | Sí (idempotente) |
| `SCHEMA_ERROR` | Fault/Client o Funcional | No |
| `TEMPORARY_UNAVAILABLE` | Fault (Server) | Sí (backoff) |

`CorrelationId` **obligatorio** en todo error. Separación estricta: **SOAP Fault = técnico**; **funcional = respuesta normal**. Códigos fuera de lista = defecto de contrato.

### 6.19 WSDL / XSD — checklist de validación

- [ ] Namespace (`urn:globalavicola:sap:inbound:v1` propuesto)
- [ ] Service name
- [ ] PortType
- [ ] Operations (12+1)
- [ ] Request types
- [ ] Response types
- [ ] Simple types
- [ ] Enumerations (ACTIVE_STATUS, ErrorCode, Language)
- [ ] Cardinality
- [ ] Optional fields (ausentes, no vacíos)
- [ ] Fault
- [ ] SchemaVersion
- [ ] Endpoint TEST
- [ ] Endpoint PROD futuro

### 6.20 Ambiente de pruebas — puntos por definir

| Punto | Valor | Estado |
|---|---|---|
| SAP environment (TEST) | [POR COMPLETAR] | PENDIENTE_PROVEEDOR_SAP |
| Endpoint | [POR COMPLETAR] | PENDIENTE_PROVEEDOR_SAP (OI-01) |
| Auth del sandbox | [POR COMPLETAR] | PENDIENTE_DECISION_CONJUNTA (OI-06) |
| Certificate | [POR COMPLETAR] | PENDIENTE_DECISION_CONJUNTA |
| Network (ruta/allowlist) | [POR COMPLETAR] | PENDIENTE_DECISION_CONJUNTA |
| Test user | (solo por canal seguro; **no en este documento**) | PENDIENTE_PROVEEDOR_SAP |
| Sample data | [POR COMPLETAR] | PENDIENTE_PROVEEDOR_SAP (OI-15) |
| Companies / Plants de prueba | [POR COMPLETAR] | PENDIENTE_PROVEEDOR_SAP |
| Fechas de prueba | [POR COMPLETAR] | PENDIENTE_PROVEEDOR_SAP |
| Expected results | a preparar por GA | PENDIENTE_GLOBAL_AVICOLA |
| Availability window | [POR COMPLETAR] | PENDIENTE_PROVEEDOR_SAP (OI-12) |

---

## 7. PIEZA 3 — MATRIZ DE OPEN ITEMS / DECISIONES

> **16 Open Items exactos de SAP-SOAP-1** (`13_SAP_SOAP_PROVIDER_OPEN_ITEMS.md`). Estado inicial de todos: **PENDING_MEETING**.

### 7.1 Matriz de reunión

| ID | Tema | Pregunta concreta | Propuesta GA | Decisión proveedor SAP | Responsable | Estado |
|---|---|---|---|---|---|---|
| OI-01 | WSDL / entorno | ¿Dónde publicarán WSDL y endpoint TEST (URL)? ¿Habrá PROD separado? | WSDL versionado + endpoint TEST por definir | — | Proveedor SAP | PENDING_MEETING |
| OI-02 | Estilo / binding | ¿document/literal wrapped + namespace propuesto (A) o proponen otro (B)? | A | — | Proveedor SAP | PENDING_MEETING |
| OI-03 | Paginación | ¿`ContinuationToken` factible (A) o solo PageNumber/PageSize (B)? ¿PageSize máx? | A con máx 500 | — | Proveedor SAP | PENDING_MEETING |
| OI-04 | Delta por objeto | ¿Qué campo de cambio existe por objeto (timestamp A / secuencia B / solo snapshot C)? | A o B; C aceptable en maestros | — | Proveedor SAP | PENDING_MEETING |
| OI-05 | `GetIntegrationChanges` | ¿Ofrecen endpoint incremental común (SÍ/NO)? ¿Forma? | Opcional, complementario | — | Proveedor SAP | PENDING_MEETING |
| OI-06 | Autenticación | ¿WS-Security UsernameToken (A) / mTLS (B) / Basic-over-TLS (C)? ¿Allowlist? | B > A > C (todas con TLS) | — | Proveedor + Seguridad | PENDING_MEETING |
| OI-07 | Versionado | ¿Confirman `SchemaVersion=1.0` y política «breaking = nueva versión» (SÍ/NO)? | SÍ | — | Proveedor SAP | PENDING_MEETING |
| OI-08 | Órdenes de salida | ¿De dónde salen realmente (prod order A / STO B / material doc C / otro D)? ¿Campos disponibles? | DTO de negocio único | — | Proveedor SAP | PENDING_MEETING |
| OI-09 | Vendors | ¿Business Partner/CVI activo (SÍ/NO)? ¿LIFNR = BP number? | lo que aplique | — | Proveedor SAP | PENDING_MEETING |
| OI-10 | Production orders | ¿Cuáles de los campos candidatos existen realmente en su sistema? | subconjunto candidato | — | Proveedor SAP | PENDING_MEETING |
| OI-11 | Cost centers | ¿Confirman exclusión de fase 1 (SÍ) o argumentan entrada (NO)? | Deferir | — | Proveedor + Owner | PENDING_MEETING |
| OI-12 | Volumen / frecuencia | Estimados de volumen por objeto y ventanas de mantenimiento | horaria/por turno | — | Proveedor SAP | PENDING_MEETING |
| OI-13 | Errores | ¿Implementan la lista cerrada de 8 códigos tal cual (SÍ/NO)? | SÍ | — | Proveedor SAP | PENDING_MEETING |
| OI-14 | Ejemplos / WSDL draft | ¿Devuelven WSDL preliminar + ejemplos adaptados? ¿Fecha? | SÍ + fecha | — | Proveedor SAP | PENDING_MEETING |
| OI-15 | Datos de prueba | ¿Dataset sandbox (sintético o enmascarado) disponible (SÍ/NO)? ¿Fecha? | SÍ | — | Proveedor SAP | PENDING_MEETING |
| OI-16 | BWART | ¿641/303 siguen siendo los tipos operativos relevantes (SÍ/NO)? ¿Otros? | validar semántica | — | Proveedor SAP | PENDING_MEETING |

### 7.2 Detalle por Open Item

**OI-01 — WSDL / entorno**
- *Contexto*: GA necesita WSDL para generar cliente y endpoint TEST para integración.
- *Pregunta cerrable*: URL de WSDL y endpoint TEST; ¿PROD separado? (responder con URLs).
- *Alternativas*: (A) publican WSDL accesible + endpoints TEST/PROD; (B) entregan archivos por otro medio.
- *Recomendación GA*: A, versionado en el tiempo.
- *Impacto si no se cierra*: bloquea generación de cliente real e integración (SOAP-5).
- *Afecta*: `05_…`, fase SOAP-5.

**OI-02 — Estilo / binding**
- *Pregunta*: ¿document/literal wrapped + `urn:globalavicola:sap:inbound:v1` (A) u otro estilo/namespace (B)?
- *Recomendación*: A (estándar, interoperable).
- *Impacto*: ajuste de ejemplos/cliente; no bloquea inicio de ABAP si aceptan A por defecto.
- *Afecta*: `05_…`, `06_…`. Clasificación: CAN_CLOSE_DURING_DEVELOPMENT.

**OI-03 — Paginación**
- *Pregunta*: ¿`ContinuationToken` factible (A) o solo `PageNumber/PageSize` (B)? ¿`MaximumPageSize`? (propuesta 500)
- *Impacto si no se cierra*: no puede cerrarse la interfaz de listados grandes (MATDOC).
- *Afecta*: `09_…`, todas las operaciones. Clasificación: **BLOCKS_ABAP**.

**OI-04 — Delta por objeto**
- *Pregunta*: por objeto, ¿campo de cambio timestamp (A) / secuencia (B) / solo snapshot (C)?
- *Recomendación*: A/B en documentos; C aceptable en maestros con reconciliación.
- *Impacto*: estrategia de sincronización y watermark.
- *Afecta*: `09_…`. Clasificación: **BLOCKS_ABAP**.

**OI-05 — GetIntegrationChanges**
- *Pregunta*: ¿ofrecen endpoint incremental común (SÍ/NO)? ¿Forma?
- *Recomendación*: opcional complementario, no sustituto.
- *Impacto*: ninguno crítico; alternativa de eficiencia.
- *Afecta*: `03_…`. Clasificación: CAN_CLOSE_DURING_DEVELOPMENT.

**OI-06 — Autenticación**
- *Pregunta*: ¿WSS UsernameToken (A) / mTLS (B) / Basic-over-TLS (C)? ¿Allowlist de IP?
- *Recomendación*: B > A > C (todas con TLS obligatorio).
- *Impacto si no se cierra*: bloquea handshake real e integración.
- *Afecta*: `08_…`. Clasificación: **BLOCKS_ABAP** (binding) + **BLOCKS_GA_IMPLEMENTATION** (config cliente).

**OI-07 — Versionado**
- *Pregunta*: ¿confirman `SchemaVersion=1.0` + «breaking = nueva versión» (SÍ/NO)?
- *Impacto*: gobernanza del contrato; bajo.
- *Afecta*: `05_…`. Clasificación: CAN_CLOSE_DURING_DEVELOPMENT.

**OI-08 — Órdenes de salida**
- *Pregunta*: ¿origen real (A producción / B STO / C material doc / D combinación)? ¿qué campos pueden exponer?
- *Impacto si no se cierra*: no puede cerrarse el DTO de `GetOutboundOrders`.
- *Afecta*: `04_…` obj.9. Clasificación: **BLOCKS_ABAP**.

**OI-09 — Vendors (BP/CVI)**
- *Pregunta*: ¿Business Partner/CVI activo (SÍ/NO)? ¿LIFNR = BP number?
- *Impacto*: semántica del maestro proveedor y posibles duplicados CVI.
- *Afecta*: `04_…` obj.4. Clasificación: **BLOCKS_ABAP**.

**OI-10 — Production orders (campos reales)**
- *Pregunta*: ¿cuáles de los campos candidatos existen realmente? (responder lista sí/no por campo)
- *Impacto*: contrato final de `GetProductionOrders` (campos hoy candidatos).
- *Afecta*: `04_…` obj.8. Clasificación: **BLOCKS_ABAP**.

**OI-11 — Cost centers (scope)**
- *Pregunta*: ¿confirman exclusión de fase 1 (SÍ) o argumentan entrada (NO)?
- *Recomendación*: deferir (sin consumidor GA hoy).
- *Impacto*: alcance de la fase; work planning.
- *Afecta*: `02_…`. Clasificación: **BLOCKS_ABAP** (scope freeze). Requiere también confirmación Owner (OD-1).

**OI-12 — Volumen / frecuencia**
- *Pregunta*: estimados de volumen por objeto y ventanas de mantenimiento.
- *Impacto*: sizing, límites, agenda de jobs; no bloquea el contrato.
- *Afecta*: `09_…`, `14_…`. Clasificación: CAN_CLOSE_DURING_DEVELOPMENT.

**OI-13 — Errores**
- *Pregunta*: ¿implementan la lista cerrada de 8 códigos tal cual (SÍ/NO)?
- *Impacto*: manejo de errores/reintentos en GA.
- *Afecta*: `07_…`. Clasificación: **BLOCKS_ABAP**.

**OI-14 — Ejemplos / WSDL draft**
- *Pregunta*: ¿devuelven WSDL preliminar + ejemplos adaptados? ¿fecha?
- *Impacto*: velocidad de SOAP-2/3 en GA; alineación de nombres.
- *Afecta*: `05_…`, `06_…`. Clasificación: **BLOCKS_GA_IMPLEMENTATION**.

**OI-15 — Datos de prueba**
- *Pregunta*: ¿dataset sandbox disponible (SÍ/NO)? ¿fecha?
- *Impacto*: pruebas de integración/reconciliación (SOAP-5/7).
- *Afecta*: `14_…`. Clasificación: CAN_CLOSE_DURING_DEVELOPMENT.

**OI-16 — BWART**
- *Pregunta*: ¿641/303 siguen siendo relevantes (SÍ/NO)? ¿otros tipos operativos?
- *Impacto*: filtros/semántica de transferencias y movimientos.
- *Afecta*: `11_…`, `04_…`. Clasificación: **BLOCKS_ABAP**.

### 7.3 Clasificación de prioridad (§22)

| Clase | Open Items | Conteo |
|---|---|---|
| **BLOCKS_ABAP** (cerrar antes de que ABAP programe) | OI-03, OI-04, OI-06, OI-08, OI-09, OI-10, OI-11, OI-13, OI-16 | **9** |
| **BLOCKS_GA_IMPLEMENTATION** | OI-01, OI-14 | **2** |
| **CAN_CLOSE_DURING_DEVELOPMENT** | OI-02, OI-05, OI-07, OI-12, OI-15 | **5** |
| **NON_BLOCKING** | — | 0 |

---

## 8. ACUERDOS A REGISTRAR DURANTE LA REUNIÓN

| ID | Tema | Decisión acordada | Responsable | Fecha compromiso |
|---|---|---|---|---|
| DEC-01 | | | | |
| DEC-02 | | | | |
| DEC-03 | | | | |
| DEC-04 | | | | |
| DEC-05 | | | | |
| DEC-06 | | | | |
| DEC-07 | | | | |
| DEC-08 | | | | |
| DEC-09 | | | | |
| DEC-10 | | | | |
| DEC-11 | | | | |
| DEC-12 | | | | |
| DEC-13 | | | | |
| DEC-14 | | | | |
| DEC-15 | | | | |
| DEC-16 | | | | |

*(Estructura preparada para completar durante la reunión; una fila por acuerdo efectivo.)*

---

## 9. ENTREGABLES ESPERADOS DEL PROVEEDOR SAP

| # | Entregable | Clase |
|---|---|---|
| 1 | Confirmación de operaciones SOAP (12+1) | **REQUIRED_BEFORE_ABAP_BUILD** |
| 2 | Validación de campos (por objeto) | **REQUIRED_BEFORE_ABAP_BUILD** |
| 3 | Resolución de los OI técnicos (OI-03…OI-16 según clasificación §7.3) | **REQUIRED_BEFORE_ABAP_BUILD** |
| 4 | Nombre técnico de servicios | **REQUIRED_BEFORE_ABAP_BUILD** |
| 5 | WSDL draft | REQUIRED_BEFORE_INTEGRATION_TEST |
| 6 | XSD draft | REQUIRED_BEFORE_INTEGRATION_TEST |
| 7 | Endpoint TEST | REQUIRED_BEFORE_INTEGRATION_TEST |
| 8 | Esquema de autenticación (implementado en TEST) | **REQUIRED_BEFORE_ABAP_BUILD** (decisión) / REQUIRED_BEFORE_INTEGRATION_TEST (implementación) |
| 9 | Definición de Fault (8 códigos) | **REQUIRED_BEFORE_ABAP_BUILD** |
| 10 | Estrategia de delta | **REQUIRED_BEFORE_ABAP_BUILD** |
| 11 | Estrategia de paginación | **REQUIRED_BEFORE_ABAP_BUILD** |
| 12 | Datos de prueba acordados | REQUIRED_BEFORE_INTEGRATION_TEST |
| 13 | Fecha estimada de disponibilidad del servicio | REQUIRED_BEFORE_INTEGRATION_TEST (planificación) |

---

## 10. SIGUIENTE PASO DESPUÉS DE LA REUNIÓN

1. Registrar el acta (§11) y volcar los acuerdos DEC-xx al contrato.
2. Si aplica: actualizar el contrato a **v1.1** con los ajustes acordados (documentación, sin implementación).
3. Global Avícola prepara la fase **SOAP-2 (mock del contrato)** — habilitable sin dependencias del proveedor.
4. Con WSDL draft + endpoint TEST → fase **SOAP-5 (sandbox)**; luego pruebas y reconciliación.
5. Ninguna implementación de integración real se inicia sin las confirmaciones clasificadas como bloqueantes (§7.3).

---

## 11. ACTA RÁPIDA DE CIERRE

**Resultado de la reunión:**

- [ ] `SOAP CONTRACT APPROVED FOR ABAP DEVELOPMENT`
- [ ] `SOAP CONTRACT APPROVED WITH OPEN ITEMS`
- [ ] `REQUIRES SECOND TECHNICAL REVIEW`

**Open items restantes:** ………………………………………………………

**Proveedor SAP responsable:** …………………………………………………

**Global Avícola responsable:** …………………………………………………

**Próxima reunión:** ……………………………………………………………

**Fecha objetivo WSDL draft:** …………………………………………………

**Fecha objetivo endpoint TEST:** ……………………………………………

---

## 12. ANEXO — REFERENCIA LEGACY PARA ABAP

> **Regla visible:**
> **LOS QUERIES LEGACY AYUDAN A IDENTIFICAR FILTROS Y RELACIONES HISTÓRICAS.**
> **NO DEFINEN EL CONTRATO ACTUAL.**

| Query | Proceso histórico | Tablas | Filtros importantes | Servicio SOAP relacionado |
|---|---|---|---|---|
| Q-01 `query_farms` | granjas | T001W | MANDT 120; NO USAR; WERKS≠3000 | `GetPlants` |
| Q-02 `query_warehouse` | almacenes/galpones | T001L+T001W | MANDT; NO USAR | `GetStorageLocations` |
| Q-03 `query_purchase_orders` | OC aves (macho/hembra) | EKPO+EKKO+T001W | MATNR 110001/110000; AEDAT | `GetPurchaseOrders` |
| Q-04 `…_temp` / `…_history` | resolución local / historial | temp local / EKBE | joins locales | `GetPurchaseOrderHistory` |
| Q-05 `query_transport` | proveedores/transportes | LFA1 | — | `GetVendors` |
| Q-06 `query_transfer_food_farms` | transferencia alimento | MATDOC+MAKT | BWART 641; MATNR 105xxx; BUDAT | `GetTransferOrders`/`GetMaterialMovements` |
| Q-07 `query_trasnfer_incubator_fattening` | pollitos incubadora→engorde | MATDOC | 120000/120005; UMWRK≠2500; AUFNR '7'; WERKS 3000 | `GetOutboundOrders` |
| Q-08 `query_ordenes_salida_cria_produccion` | cría→producción | MATDOC | prefijo AUFNR; FK fija temporal | `GetOutboundOrders` |
| Q-09 `query_ordenes_salida_produccion_aves` | producción→beneficio | MATDOC | 110002; UMWRK≠2500; destinos fijos | `GetOutboundOrders` |
| Q-10 `query_transfer_reproductoras_303` | aves a reproductoras | MATDOC | BWART 303; 110002/110003; WERKS 2000/2002 | `GetTransferOrders` |
| Q-11 `query_inventories` | inventarios anuales | MATDOC+MAKT+T001W+T001L+T156HT | MJAHR; rango BUDAT | `GetMaterialMovements` (fase posterior) |
| Q-12 `…_huevos` (comentada) | salida de huevos | AFPO | (nunca activo) | posible futuro |
| Q-13 `ZwsTasaMortalidad` | mortalidad (GA→SAP) | — | — | fuera de esta fase (outbound futuro) |

**BWART de referencia histórica:** `641` (transferencias entre centros: alimento/aves/huevos/pollitos) y `303` (aves a reproductoras) — **validación obligatoria** con el proveedor (OI-16); no constituyen reglas actuales.

**Clasificación aplicada a cada elemento legacy**: `LEGACY_QUERY_REFERENCE` · `LEGACY_FILTER_REFERENCE` · `BUSINESS_RULE_TO_VALIDATE` · `DO_NOT_REUSE` (hardcodes y destinos fijos **nunca** pasan al producto).

“Los queries completos permanecen disponibles como anexo técnico de referencia” en `audit/sap-soap/11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP.md`.

---

### Trazabilidad interna (no para el proveedor)

| Dato | Valor |
|---|---|
| Base documental | SAP-SOAP-1 (cerrada) · commit `b078d07` |
| Documentos fuente | `audit/sap-soap/01…15` · `specs/003-sap-soap-inbound-contract/` |
| Este documento | `audit/sap-soap/SAP_SOAP_REUNION_TECNICA_PROVEEDOR.md` v1.0 |
| Regla de contenido | sin decisiones abiertas presentadas como hechos; SPEC como fuente canónica |
