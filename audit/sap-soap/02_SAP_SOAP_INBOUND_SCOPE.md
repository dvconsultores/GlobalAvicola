# SAP-SOAP · 02_SAP_SOAP_INBOUND_SCOPE

Fecha: 2026-09-22 · Alcance inbound fase 1 · **Sin implementación**

---

## 1 · Objetos inbound (13) — §5 del mandato

| # | Objeto | Operación SOAP | Prioridad | Dependencias |
|---|---|---|---|---|
| 1 | SAP_COMPANY | `GetCompanies` | **P1 (reunión)** | raíz de tenant |
| 2 | SAP_PLANT | `GetPlants` | P1 | requiere COMPANY |
| 3 | SAP_STORAGE_LOCATION | `GetStorageLocations` | **P1 (reunión)** | requiere PLANT |
| 4 | SAP_VENDOR | `GetVendors` | P1 | — |
| 5 | SAP_MATERIAL | `GetMaterials` | P1 (maestro de interpretación) | — |
| 6 | SAP_PURCHASE_ORDER | `GetPurchaseOrders` (header) | **P1 (reunión)** | VENDOR + MATERIAL(ítems) |
| 7 | SAP_PURCHASE_ORDER_ITEM | (anidado en `GetPurchaseOrders`) | P1 | MATNR/WERKS resoluble |
| 8 | SAP_PURCHASE_ORDER_HISTORY | `GetPurchaseOrderHistory` | P1 | PO + ITEM |
| 9 | SAP_PRODUCTION_ORDER | `GetProductionOrders` | **P1 (reunión)** | PLANT + MATERIAL + BATCH |
| 10 | SAP_OUTBOUND_ORDER | `GetOutboundOrders` | **P1 (reunión)** | PLANT + MATERIAL + BATCH |
| 11 | SAP_TRANSFER_ORDER | `GetTransferOrders` | **P1 (reunión)** | COMPANY/PLANT/STORAGE + MATERIAL |
| 12 | SAP_MATERIAL_MOVEMENT / MATERIAL_DOCUMENT | `GetMaterialMovements` | P1 | PLANT/STORAGE + MATERIAL |
| 13 | SAP_BATCH | `GetBatches` | P2 | MATERIAL + PLANT |

## 2 · Prioridades acordadas con cliente (§6 del mandato)

El mínimo de la reunión: **empresas, almacenes, órdenes de compra, órdenes de salida, órdenes de producción**, y **transferencias de**: medicinas, alimentos, vacunas/insumos sanitarios (si aplica), aves, huevos, pollitos — más los **maestros necesarios para interpretar** esos documentos.

**Principio de dependencia**: un documento con `MATNR` no es utilizable si GA no puede resolver el material → `GetMaterials` es dependencia dura de todo documento. Igualmente `GetCompanies/GetPlants/GetStorageLocations` son dependencias de resolución multiempresa.

## 3 · COST_CENTER — validación de scope (§5)

| Opción | Evaluación | Decisión propuesta |
|---|---|---|
| Entrar en fase 1 | Hoy no existe consumidor GA activo de cost centers (espejo `sap_references.COST_CENTER` sin uso, auditoría readiness §5) | ✗ |
| **Fase posterior** | Si el costeo/CO entra en el alcance operativo futuro | **✔ DEFER_TO_LATER_PHASE** |
| Eliminar del scope | — | ✗ (no eliminar; posponer) |

El servicio SOAP de fase 1 **no incluye** operación de cost centers. Revisable por Owner/Proveedor en la próxima reunión (`13_SAP_SOAP_PROVIDER_OPEN_ITEMS.md` ítem OI-11).

## 4 · Delimitación de fase 1 (qué NO entra)

- Outbound GA→SAP (otra SPEC si SAP lo requiere; §37).
- Extracción de reporting/inventarios históricos completos (a lo sumo `GetMaterialMovements` acotado).
- Cost centers (deferido).
- Cualquier acceso HANA directo, VPN embebida, OData como mecanismo principal.
- Implementación en cualquiera de los dos lados (el proveedor construye contra contrato; GA no implementa aún).

## 5 · Criterio de resolución de documentos (GA)

```
documento SOAP → RAW → validación → resolución de claves:
  COMPANY_CODE → GA company   (fail-closed si falta)
  WERKS        → GA plant/farm (clasificación, no automática)
  LGORT        → mapping configurable (NO asumir galpón)
  MATNR        → GA material mapping (categoría FEED/MEDICINE/VACCINE/BIRD/EGG/CHICK/OTHER)
  LIFNR        → vendor/supplier
sin resolución → PENDING_MAPPING (no promoción)
```

## 6 · Trazabilidad

Objetos ↔ operaciones ↔ campos: `03_SAP_SOAP_OPERATION_CATALOG.md` y `04_SAP_SOAP_FIELD_CATALOG.md`. Dependencias → orden de integración (fase 1 dentro de sí misma): maestros primero, documentos después, movimientos al final.
