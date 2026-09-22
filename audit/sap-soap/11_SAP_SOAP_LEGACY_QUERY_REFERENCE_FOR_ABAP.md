# SAP-SOAP · 11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP

Fecha: 2026-09-22 · Auditoría de `dvconsultores/SapHanaLP/querysHana.py` y scripts asociados (§21) · Fuente: evidencia `LEGACY_CONFIRMED` de SAP-0/auditoría remota (lectura, sin ejecución)

> ## EXPRESO: **EL QUERY NO ES EL CONTRATO. EL SOAP CONTRACT ES EL CONTRATO.**
> Este anexo existe para que ABAP entienda **qué preguntaba el sistema histórico y con qué filtros**, y proponga el mejor mecanismo SAP para responderlo. Ningún filtro, tabla o código aquí es requisito técnico del servicio SOAP.

Clasificación por elemento: `LEGACY_QUERY_REFERENCE` (referencia funcional) · `LEGACY_FILTER_REFERENCE` (filtro histórico) · `BUSINESS_RULE_TO_VALIDATE` (regla de negocio a validar) · `DO_NOT_REUSE` (prohibido replicar tal cual).

---

## 1 · Queries auditadas

### Q-01 `query_farms` — Granjas
| Campo | Detalle |
|---|---|
| OLD_PURPOSE | Lista de centros/granjas para maestros locales |
| TABLES | `T001W` |
| FIELDS | WERKS, NAME1, NAME2, MANDT |
| FILTERS | `MANDT='120'`; `NAME1/NAME2 NOT LIKE '%NO USAR%'`; `WERKS NOT IN ('3000')` |
| BUSINESS_MEANING | catálogo de unidades operativas (no todas granjas: se excluía incubadora) |
| CURRENT_REQUIRED_DATA | PLANT maestra con clasificación explícita |
| CURRENT_CONTRACT_OPERATION | `GetPlants` |
| NOTES_FOR_ABAP | la exclusión de 3000 y el marcador «NO USAR» eran parches; el contrato pide `ACTIVE_STATUS` y clasificación (la hace GA) |
| CLAVE | `LEGACY_QUERY_REFERENCE` + `LEGACY_FILTER_REFERENCE` |

### Q-02 `query_warehouse` — Almacenes
| Campo | Detalle |
|---|---|
| TABLES | `T001L` JOIN `T001W` |
| FIELDS | LGORT, LGOBE, T001L.WERKS |
| FILTERS | `MANDT='120'`; NO USAR en NAME1/LGOBE |
| BUSINESS_MEANING | almacenes = «galpones» (sin validación de negocio) |
| CURRENT_REQUIRED_DATA | PLANT+STORAGE_LOCATION+NAME+estado |
| CURRENT_CONTRACT_OPERATION | `GetStorageLocations` |
| NOTES_FOR_ABAP | **LGORT ≠ GALPÓN no resuelto**; GA mantiene mapping configurable |
| CLAVE | `LEGACY_QUERY_REFERENCE` |

### Q-03 `query_purchase_orders` — OC aves por sexo
| Campo | Detalle |
|---|---|
| TABLES | `EKPO` (self-join EKPO2), `EKKO`, `T001W` |
| FIELDS | EBELN, UNIQUEID→id_sap, EKKO.LIFNR, WERKS, MENGE (machos/hembras), AEDAT |
| FILTERS | `MATNR='...110001'` machos; `...110000` hembras; `AEDAT>='20230301'`; NO USAR |
| BUSINESS_MEANING | OC de aves con cantidades por sexo |
| CURRENT_REQUIRED_DATA | documents: PO header+items con MATERIAL por ítem; **categoría de ave la resuelve GA** |
| CURRENT_CONTRACT_OPERATION | `GetPurchaseOrders` |
| NOTES_FOR_ABAP | el patrón macho/hembra por MATNR hardcodeado es **DO_NOT_REUSE**; entregar ítems con material y cantidades reales |
| CLAVE | `BUSINESS_RULE_TO_VALIDATE` + `DO_NOT_REUSE` (hardcodes) |

### Q-04 `query_purchase_orders_temp` / `query_purchase_orders_history`
| Campo | Detalle |
|---|---|
| TABLES | temp local (PostgreSQL) / `EKBE` |
| FIELDS | orden_compra, id_sap, cantidades, proveedor, granja / EKBE por EBELN |
| FILTERS | join local por proveedores/granjas |
| BUSINESS_MEANING | resolución de FKs locales / historial de pedidos |
| CURRENT_CONTRACT_OPERATION | `GetPurchaseOrderHistory` (historial) |
| NOTES_FOR_ABAP | el temp-join era **resolución de claves en GA**, no responsabilidad SAP; el contrato entrega claves crudas y GA resuelve |
| CLAVE | `LEGACY_QUERY_REFERENCE` |

### Q-05 `query_transport` — Proveedores
| Campo | Detalle |
|---|---|
| TABLES | `LFA1` |
| FIELDS | LIFNR, NAME1 |
| FILTERS | ninguna |
| BUSINESS_MEANING | proveedores **y** «transportes» desde la misma fuente |
| CURRENT_REQUIRED_DATA | VENDOR maestro (+ si BP/CVI) |
| CURRENT_CONTRACT_OPERATION | `GetVendors` |
| NOTES_FOR_ABAP | confirmar si el sistema actual usa Business Partner (OI-09); la ambigüedad proveedor/transporte se resuelve en GA |
| CLAVE | `LEGACY_QUERY_REFERENCE` |

### Q-06 `query_transfer_food_farms` (+`_temp`) — Transferencia de alimento
| Campo | Detalle |
|---|---|
| TABLES | `MATDOC` JOIN `MAKT`; temp local con categorías |
| FIELDS | BUDAT, MATNR, MAKTX, MENGE, WERKS, LGORT, BWART, BUKRS, MBLNR, EBELN; concat `MBLNR-EBELN-MATNR` |
| FILTERS | `BWART='641'`; MATNR list 105001…105028; `BUDAT>='20240301'` |
| BUSINESS_MEANING | entregas/transferencias de alimento (categoría CRIA/PROD/ENGORDE por lista de materiales) |
| CURRENT_REQUIRED_DATA | transferencias con material+plantas+almacenes+cantidades |
| CURRENT_CONTRACT_OPERATION | `GetTransferOrders` / `GetMaterialMovements` |
| NOTES_FOR_ABAP | categorizar alimento NO se hace por lista MATNR en el contrato; GA mapea por material |
| CLAVE | `BUSINESS_RULE_TO_VALIDATE` + `DO_NOT_REUSE` (categorías por hardcode) |

### Q-07 `query_trasnfer_incubator_fattening` (+`_temp`) — Pollitos incubadora→engorde
| Campo | Detalle |
|---|---|
| TABLES | `MATDOC`; temp local |
| FIELDS | AUFNR, WERKS, UMWRK, LGORT, BUDAT, ERFMG, MATNR; destino por join a incubadoras |
| FILTERS | MATNR 120000/120005; `BUDAT>='20250312'`; `UMWRK NOT IN ('2500')`; `SUBSTRING(AUFNR,1,1)='7'`; WERKS='3000' |
| BUSINESS_MEANING | salidas de pollitos BB de incubadora hacia granja |
| CURRENT_REQUIRED_DATA | documentos de salida (origen/destino/material/cantidad/lote) |
| CURRENT_CONTRACT_OPERATION | `GetOutboundOrders` (+`GetMaterialMovements`) |
| NOTES_FOR_ABAP | prefijo AUFNR='7' y exclusiones eran parches de filtrado; el contrato pide documentos identificables por tipo/ventana |
| CLAVE | `LEGACY_FILTER_REFERENCE` + `BUSINESS_RULE_TO_VALIDATE` |

### Q-08 `query_ordenes_salida_cria_produccion` (+`_temp`) — Cría→producción
| Campo | Detalle |
|---|---|
| TABLES | `MATDOC`; temp con joins a granjas/galpones |
| FIELDS | AUFNR(orden), WERKS(origen), UMWRK(destino), LGORT(almacén), BUDAT, ERFMG; FK fija `'000000000000'` transporte |
| BUSINESS_MEANING | salidas internas entre etapas productivas |
| CURRENT_REQUIRED_DATA | outbound con origen/destino/almacén/lote |
| CURRENT_CONTRACT_OPERATION | `GetOutboundOrders` |
| NOTES_FOR_ABAP | resoluciones de galpón por join eran de GA; la FK fija «transporte» es **DO_NOT_REUSE** |
| CLAVE | `LEGACY_QUERY_REFERENCE` + `DO_NOT_REUSE` |

### Q-09 `query_ordenes_salida_produccion_aves` (+`_temp`) — Producción→beneficio
| Campo | Detalle |
|---|---|
| TABLES | `MATDOC`; temp con FK fijas `'1'` granja destino, `'3730'` transporte, `'1001'` galpón |
| FIELDS | AUFNR, WERKS, UMWRK, LGORT, BUDAT, ERFMG, MATNR(110002) |
| FILTERS | `BUDAT>='20250312'`; `UMWRK NOT IN ('2500')`; AUFNR prefijo 7 |
| BUSINESS_MEANING | salida de gallinas de producción |
| CURRENT_CONTRACT_OPERATION | `GetOutboundOrders` |
| NOTES_FOR_ABAP | destinos fijos eran datos ficticios locales → **DO_NOT_REUSE**; el contrato lleva origen/destino reales |
| CLAVE | `DO_NOT_REUSE` + `LEGACY_QUERY_REFERENCE` |

### Q-10 `query_transfer_reproductoras_303` — Aves a reproductoras
| Campo | Detalle |
|---|---|
| TABLES | `MATDOC` |
| FIELDS | AUFNR, WERKS, UMWRK, LGORT, BUDAT, SUM(ERFMG), MATNR |
| FILTERS | `BWART='303'`; MATNR 110002/110003; AUFNR='121000000016' (ej.); WERKS IN ('2000','2002') |
| BUSINESS_MEANING | transferencia de gallinas/machos a reproductoras |
| CURRENT_REQUIRED_DATA | transferencias con tipo de movimiento real y material |
| CURRENT_CONTRACT_OPERATION | `GetTransferOrders` |
| NOTES_FOR_ABAP | validar semántica actual de 303 con negocio/Basis |
| CLAVE | `BUSINESS_RULE_TO_VALIDATE` |

### Q-11 `query_inventories` — Inventarios anuales
| Campo | Detalle |
|---|---|
| TABLES | `MATDOC` + `MAKT` + `T001W` + `T001L` + `T156HT` |
| FIELDS | amplio (SHKZG, /CWM/*, MJAHR, CHARG, USNAM, TCODE2, …) |
| FILTERS | `MJAHR='2024'`; `BUDAT` rango anual |
| BUSINESS_MEANING | reporte de inventario (no flujo operativo) |
| CURRENT_CONTRACT_OPERATION | `GetMaterialMovements` acotado (fase posterior para reporting) |
| CLAVE | `LEGACY_QUERY_REFERENCE` (baja prioridad) |

### Q-12 `query_ordenes_salida_produccion_huevos` — (comentada, AFPO)
| Campo | Detalle |
|---|---|
| TABLES | `AFPO` (comentado; nunca activo) |
| BUSINESS_MEANING | salida de huevos (no implementado) |
| CURRENT_CONTRACT_OPERATION | posible `GetProductionOrders`/`GetOutboundOrders` futuro |
| CLAVE | `LEGACY_QUERY_REFERENCE` |

### Q-13 SOAP legacy `ZwsTasaMortalidad` (params de ejemplo)
| Campo | Detalle |
|---|---|
| FUENTE | `sap_integration.py` (BasicAuth, `verify=False` → **DO_NOT_REUSE** del modo TLS) |
| FIELDS | IBudat, ICharg, IErfmg, ILgort, IMatnr, IMblnr, IProceso, IWerks |
| BUSINESS_MEANING | notificación mortalidad (dirección **GA→SAP**) |
| NOTA | **fuera del alcance inbound** de esta SPEC; posible contrato outbound futuro (otra SPEC) |
| CLAVE | `LEGACY_QUERY_REFERENCE` (histórica) |

## 2 · BWART legacy (§22)

| BWART | LEGACY_USE | CURRENT_BUSINESS_EVENT (hipótesis) | SAP_PROVIDER_VALIDATION_REQUIRED |
|---|---|---|---|
| 641 | Transferencias entre centros/almacenes (alimento, aves, huevos, pollitos) | transferencia de material | **Sí** |
| 303 | Aves a reproductoras (gallinas/machos) | transferencia especial | **Sí** |

No se encontraron otros BWART usados como filtro operativo (AFPO/otros estaban comentados). **Ninguno se impone** como regla actual: el contrato usa `MOVEMENT_TYPE` informativo y GA clasifica por mapping.

## 3 · Filtros históricos (§23)

| Filtro legacy | Uso | Clasificación SAP-SOAP-1 |
|---|---|---|
| `MANDT='120'` | todas | `FILTER_REPLACED_BY_SOAP_CONTRACT` (MANDT va en datos, no en filtro fijo) |
| `WERKS NOT IN ('3000')`, exclusiones 2500 | granjas/salidas | `FILTER_NEEDS_SAP_VALIDATION` (clasificación real de plantas) |
| `'%NO USAR%'` en nombres | granjas/almacenes | `FILTER_NEEDS_SAP_VALIDATION` (¿estado real? ¿baja lógica?) |
| Listas `MATNR` (105xxx, 110xxx, 115000, 120000/120005) | categorización | `FILTER_REPLACED_BY_SOAP_CONTRACT` + `BUSINESS_RULE_TO_VALIDATE` (GA mapea categorías) |
| `BWART 641/303` | filtros de proceso | `FILTER_NEEDS_SAP_VALIDATION` |
| `BUDAT>=` 20230301/20240301/20250312; `MJAHR='2024'` | ventanas de carga | `OBSOLETE` (el contrato usa ventanas reales de operación/delta) |
| `AUFNR` prefijo `'7'` | filtrado de órdenes | `FILTER_NEEDS_SAP_VALIDATION` |
| Destinos fijos `'3730'`, `'1'`, `'1001'`, `'000000000000'` | relleno de FKs | `DO_NOT_REUSE` |
| LGORT como galpón | mapeo almacén | `BUSINESS_RULE_TO_VALIDATE` (SAP-STO-01) |

## 4 · Mensaje final para el proveedor

Este anexo documenta **qué necesitaba el sistema histórico**. El contrato vigente (`03_…`/`04_…`) define **qué necesita Global Avícola ahora**. Donde el legacy usaba hardcodes o parches, el contrato pide **datos maestros + clasificación en GA**. Cualquier divergencia se resuelve en la próxima reunión (ver `13_…`), nunca reinterpretando el SQL legacy como especificación.
