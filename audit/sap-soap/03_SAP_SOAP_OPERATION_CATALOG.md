# SAP-SOAP · 03_SAP_SOAP_OPERATION_CATALOG

Fecha: 2026-09-22 · Propuesta de operaciones tipadas (§7) · **Contrato externo únicamente — no impone arquitectura ABAP interna**

---

## 1 · Operaciones (12 núcleo + 1 opcional)

| # | Operación | Propósito | Objeto(s) | Clave de registros | Delta candidato | Prioridad |
|---|---|---|---|---|---|---|
| 1 | `GetCompanies` | Sociedades (BUKRS) | SAP_COMPANY | COMPANY_CODE | ChangedSince opt | P1 |
| 2 | `GetPlants` | Centros (WERKS) | SAP_PLANT | PLANT | ChangedSince opt | P1 |
| 3 | `GetStorageLocations` | Almacenes (LGORT) | SAP_STORAGE_LOCATION | PLANT+STORAGE_LOCATION | snapshot | P1 |
| 4 | `GetVendors` | Proveedores/BP | SAP_VENDOR | VENDOR | ChangedSince opt | P1 |
| 5 | `GetMaterials` | Materiales | SAP_MATERIAL | MATERIAL | ChangedSince opt | P1 |
| 6 | `GetPurchaseOrders` | OC con ítems anidados | SAP_PURCHASE_ORDER + ITEM | PO_NUMBER (+PO_ITEM) | ChangedSince/DocDate | P1 |
| 7 | `GetPurchaseOrderHistory` | Pedidos/recepciones OC | SAP_PURCHASE_ORDER_HISTORY | EBELN+EBELP+BELNR+item | PostingDate/ChangedSince | P1 |
| 8 | `GetProductionOrders` | Órdenes de producción | SAP_PRODUCTION_ORDER | ORDER_NUMBER | ChangedSince/DocDate | P1 |
| 9 | `GetOutboundOrders` | Órdenes de salida (DTO negocio) | SAP_OUTBOUND_ORDER | ORDER_NUMBER | ChangedSince/DocDate | P1 |
| 10 | `GetTransferOrders` | Transferencias (STO/OT) multiactivo | SAP_TRANSFER_ORDER | TRANSFER_NUMBER (+DOCUMENT_NUMBER) | ChangedSince/DocDate | P1 |
| 11 | `GetMaterialMovements` | Documentos de material (DTO) | SAP_MATERIAL_MOVEMENT | MBLNR+YEAR+ITEM | PostingDate/ChangedSince | P1 |
| 12 | `GetBatches` | Lotes | SAP_BATCH | MATERIAL+PLANT+BATCH | por documento/via movements | P2 |
| 13 | `GetIntegrationChanges` | **OPCIONAL**: endpoint incremental común | multi-objeto | por objeto | ChangedSince + cursor | Propuesta ABAP |

**Regla de diseño**: `GetIntegrationChanges` **puede** existir si SAP/ABAP lo considera más adecuado para incremental; si existe, **no reemplaza** las consultas puntuales por documento (se mantienen para reconciliación y recuperación).

## 2 · Contrato común de REQUEST (§8) — aplicabilidad por operación

Leyenda: **R**=requerido · **O**=opcional · **–**=no aplica

| Campo | Tipo | Companies | Plants | StorLoc | Vendors | Materials | PO | PO Hist | ProdOrd | OutbOrd | TransfOrd | MatMove | Batches |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RequestId | C(36) | R | R | R | R | R | R | R | R | R | R | R | R |
| SchemaVersion | C(8) | R | R | R | R | R | R | R | R | R | R | R | R |
| CompanyCode | C(4) | O | O | O* | O | – | O | O | O | O | O | O | O |
| Plant | C(4) | – | – | O* | – | – | O | O | O | O | O | O | O |
| FromDate / ToDate | D | – | – | – | – | – | O | O | O | O | O | O | – |
| ChangedSince | TS | O | O | O | O | O | O | O | O | O | O | O | O |
| DocumentNumber | C(10..12) | – | – | – | – | – | O | O | O | O | O | O | – |
| Status | C(4) | – | O | – | O | O | O | – | O | O | O | – | O |
| PageNumber | N(6) | O | O | O | O | O | O | O | O | O | O | O | O |
| PageSize | N(5) | O | O | O | O | O | O | O | O | O | O | O | O |
| ContinuationToken | C(512) | O | O | O | O | O | O | O | O | O | O | O | O |
| Language | C(2) | O | O | O | O | O | O | O | O | O | O | O | O |
| ClientSystem | C(16) | R | R | R | R | R | R | R | R | R | R | R | R |

`*` StorLoc: al menos uno de `Plant` o `CompanyCode` requerido (para acotar).

Reglas de filtrado (§8):
1. Toda operación debe evitar extracciones masivas: sin filtro temporal, el servicio debe limitar por `ChangedSince` por defecto o exigir ventana.
2. `DocumentNumber` acota a un documento puntual (reconciliación).
3. Los filtros son **acumulativos** (AND).

## 3 · Contrato común de RESPONSE (§9)

```
<OperationResponse>
  <Header>
    <RequestId/> <ResponseTimestamp/> <Success/> <ErrorCode/> <ErrorMessage/>
    <SchemaVersion/> <RecordCount/> <HasMore/> <ContinuationToken/>
  </Header>
  <Records> <!-- 0..N del tipo de la operación --> </Records>
</OperationResponse>
```

- Separación estricta: **errores funcionales** → `Success=false` + `ErrorCode/ErrorMessage` en Header (respuesta normal). **Errores técnicos/soap** → SOAP Fault (ver `07_SAP_SOAP_ERROR_CONTRACT.md`).
- `HasMore=true` ⇒ `ContinuationToken` presente. `RecordCount` = registros en este batch (no total global).

## 4 · Frecuencias objetivo (propuesta GA, confirmable con ABAP)

| Grupo | Operaciones | Frecuencia objetivo |
|---|---|---|
| Maestros | Companies, Plants, StorageLocations, Vendors, Materials | diaria + reconciliación semanal |
| Batches | Batches | diaria |
| Documentos | PO, PO History, Production, Outbound, Transfer | horaria/por turno (según disponibilidad SAP) |
| Movimientos | MaterialMovements | horaria/por turno, ventana acotada |

## 5 · Alineación con objetos §5 y prioridades §6

Cobertura 13/13 objetos (12 core + COST_CENTER fuera de fase 1, ver `02_…`). Toda operación P1 de la reunión (empresas, almacenes, OC, salidas, producción, transferencias) está cubierta. Nombres técnicos pueden ajustarse por ABAP **sin eliminar información requerida** (§33).
