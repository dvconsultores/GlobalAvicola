# SAP-HANA-CLOUD · 02_LEGACY_QUERY_AUDIT

Fecha: 2026-10-06 · Fase: **SPEC 005 — SAP HANA Cloud READ ONLY Inbound Integration** · Alcance: queries de `dvconsultores/SapHanaLP/querysHana.py`
Fuente: evidencia documental `LEGACY_CONFIRMED` de `audit/sap-soap/11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP.md` y `audit/sap0/SAP_LEGACY_REPOSITORY_AUDIT.md` (lectura remota, sin ejecución)

> **El SQL legacy no está en este repositorio y no se copió.** Esta matriz describe qué preguntaba el sistema histórico; ninguna tabla, filtro o literal de aquí es contrato de la integración nueva.

---

## 1 · Regla

```text
LEGACY QUERY != CONTRACT
CURRENT HANA METADATA + APPROVED QUERY REGISTRY = CONTRACT
LEGACY_HANA_QUERIES = REFERENCE_ONLY
```

`NEW_QUERY_ID` = `<objeto>.v1` del registry cerrado (`backend/app/integrations/sap/inbound/registry.py`). Verificación: AC-HANA-03 (ninguna query legacy se ejecuta ni se copia literal; test anti-hardcode del registry).

## 2 · Matriz de queries legacy

| LEGACY_QUERY | BUSINESS_PURPOSE | CURRENT_OBJECT | LEGACY_TABLES | HARDCODES_FOUND | REUSE_SEMANTICS | DO_NOT_REUSE | NEW_QUERY_ID |
|---|---|---|---|---|---|---|---|
| `query_farms` | Lista de centros/granjas para maestros locales | `plant` | `T001W` | `MANDT='120'`; `NAME1/NAME2 NOT LIKE '%NO USAR%'`; `WERKS NOT IN ('3000')` | catálogo de centros (`WERKS`, nombres) | mandante literal; exclusión fija de 3000; marcador «NO USAR» como criterio de baja | `plant.v1` |
| `query_warehouse` | Almacenes (tratados como «galpones») | `storage_location` | `T001L` JOIN `T001W` | `MANDT='120'`; «NO USAR» en `NAME1`/`LGOBE` | centro + almacén + nombre | equivalencia `LGORT` = galpón (OD-24: `LGORT ≠ galpón`) | `storage_location.v1` |
| `query_purchase_orders` | OC de aves con cantidades por sexo | `purchase_order` + `purchase_order_item` | `EKPO` (self-join), `EKKO`, `T001W` | `MATNR='…110001'` machos / `'…110000'` hembras; `AEDAT>='20230301'`; «NO USAR» | cabecera e ítems con material y cantidad reales | patrón macho/hembra por material; `EKPO.UNIQUEID` como id de la OC; fecha fija | `purchase_order.v1` + `purchase_order_item.v1` |
| `query_purchase_orders_history` | Historial de pedidos | `purchase_order_history` | `EKBE` | `EBELN` literal de prueba + `LIMIT 100` | historial por documento de compra | documento literal y tope fijo | `purchase_order_history.v1` |
| `query_purchase_orders_temp` | Resolución de FKs locales (proveedor, granja) | — (no es objeto SAP) | tabla temporal local (PostgreSQL) | join local por proveedores/granjas | ninguna: la resolución de claves es de GA | tabla temporal + join; lo sustituyen `sap_entity_mappings` y la promoción | — (sin query HANA) |
| `query_transport` | Proveedores y «transportes» desde la misma fuente | `vendor` | `LFA1` | ninguno (sin filtros) | maestro de proveedor (`LIFNR`, nombre) | lectura de mandante completo; doble uso proveedor/transporte | `vendor.v1` |
| `query_transfer_food_farms` (+`_temp`) | Entregas/transferencias de alimento | `transfer_order` + `material_movement` | `MATDOC` JOIN `MAKT`; temp local con categorías | `BWART='641'`; `MATNR` 105001…105028; `BUDAT>='20240301'` | traslado con material, centros, almacenes y cantidades | categoría CRIA/PROD/ENGORDE por lista de materiales; `BWART` como filtro; clave concatenada `MBLNR-EBELN-MATNR` | `transfer_order.v1` + `material_movement.v1` |
| `query_trasnfer_incubator_fattening` (+`_temp`) | Salida de pollitos BB incubadora → engorde | `outbound_order` + `material_movement` | `MATDOC`; temp local | `MATNR` 120000/120005; `BUDAT>='20250312'`; `UMWRK NOT IN ('2500')`; `SUBSTRING(AUFNR,1,1)='7'`; `WERKS='3000'` | documento de salida con origen, destino, material, cantidad y lote | prefijo de orden, exclusiones y centro fijos; destino resuelto por join local | `outbound_order.v1` + `material_movement.v1` |
| `query_ordenes_salida_cria_produccion` (+`_temp`) | Salidas internas cría → producción | `outbound_order` + `material_movement` | `MATDOC`; temp con joins a granjas/galpones | FK fija de transporte `'000000000000'` | salida con origen, destino, almacén y lote | FK fija de transporte; resolución de galpón por join | `outbound_order.v1` + `material_movement.v1` |
| `query_ordenes_salida_produccion_aves` (+`_temp`) | Salida de gallinas producción → beneficio | `outbound_order` + `material_movement` | `MATDOC`; temp con FK fijas | `MATNR` 110002; `BUDAT>='20250312'`; `UMWRK NOT IN ('2500')`; prefijo `AUFNR` 7; FK fijas `'1'` granja, `'3730'` transporte, `'1001'` galpón | salida con origen y destino reales | destinos ficticios locales; exclusiones y fecha fijas | `outbound_order.v1` + `material_movement.v1` |
| `query_transfer_reproductoras_303` | Transferencia de gallinas/machos a reproductoras | `transfer_order` + `material_movement` | `MATDOC` | `BWART='303'`; `MATNR` 110002/110003; `AUFNR='121000000016'` (ej.); `WERKS IN ('2000','2002')` | traslado con tipo de movimiento real y material | 303 como regla de proceso; orden y centros literales | `transfer_order.v1` + `material_movement.v1` |
| `query_inventories` | Reporte de inventario anual (no flujo operativo) | `material_movement` (+ `movement_type` por `T156HT`) | `MATDOC` + `MAKT` + `T001W` + `T001L` + `T156HT` | `MJAHR='2024'`; `BUDAT` en rango anual | movimientos acotados por ventana; texto del tipo de movimiento | año fijo; lectura anual sin tope; uso como stock (`SAP_INVENTORY_SNAPSHOT` = `DEFERRED_PHASE_1`) | `material_movement.v1` + `movement_type.v1` |

Todos los hardcodes de la columna `HARDCODES_FOUND` son evidencia histórica `DO_NOT_REUSE`.

## 3 · Notas

| Elemento legacy | Tratamiento |
|---|---|
| `query_ordenes_salida_produccion_huevos` (comentada, `AFPO`) | nunca estuvo activa; `LEGACY_QUERY_REFERENCE` sin `NEW_QUERY_ID` derivado. No sustenta ninguna definición. |
| SOAP legacy `ZwsTasaMortalidad` | dirección GA → SAP: **outbound, fuera de alcance** (`SAP_OUTBOUND_PHASE_1 = DISABLED`). Su `verify=False` es `DO_NOT_REUSE`. |
| Objetos de SPEC 005 sin query legacy propia (`company`, `material`, `batch`, `production_order`) | se apoyan en tablas candidatas no verificadas (`spec.md` §RISKS); `source_status` por definición, a validar en el probe P5. |
| Tablas confirmadas solo por uso histórico | `T001W, T001L, LFA1, EKKO, EKPO, EKBE, MATDOC, MAKT, T156HT` (`LEGACY_CONFIRMED`, no verificadas contra el landscape actual: SAP-0P = 0/12). |

Diferencias de fuente ya decididas en la SPEC (no heredadas del legacy):

- **Traslados**: se distinguen de una OC de forma estructural (`EKKO.RESWK` informado), sin listas de `BSART`/`BWART` (Q9).
- **Órdenes de salida**: fuente candidata `LIKP/LIPS`, separada de `MATDOC` como evidencia de movimiento; se valida en P5 y no se afirma como contrato final (Q8).
- **Proveedores**: acotados a la sociedad (`LFB1`) para no cruzar inquilinos que compartan mandante (Q11).
- **Delta**: maestros `SNAPSHOT`; documentos `BOUNDED_RECONCILIATION_WINDOW` (Q7).

## 4 · Hardcodes prohibidos en código productivo

| Hardcode legacy (`DO_NOT_REUSE`) | Evidencia | Sustituto en `SAP_HANA_CLOUD_READ_ONLY_V2` |
|---|---|---|
| `MANDT='120'` | SAP-0 T-07 | mandante por `SAP_HANA_CLIENT` (bind) |
| Puerto HANA legacy (valor legacy, ver SAP-0) | SAP-0 T-02 | configuración de entorno; ningún literal de conexión en código |
| Schema legacy (valor legacy, ver SAP-0) | SAP-0 T-06 | schema por `SAP_HANA_SCHEMA`, validado como identificador |
| `WERKS='3000'`, `NOT IN ('3000')`, `'2500'`, `('2000','2002')` | SAP-0 T-09, T-10 | sociedades y centros por `sap_entity_mappings` |
| Listas `MATNR` (105001…105028, 110000–110003, 115000, 120000/120005) | SAP-0 T-13 | materiales por maestro (`material`); la categoría la resuelve GA |
| Materiales macho/hembra (`…110001` / `…110000`) | `11_…` Q-03 | ítems reales de la OC con su material |
| `BWART` 641 / 303 | SAP-0 T-14 | tipo de movimiento como dato informativo (`movement_type`), nunca como filtro de proceso |
| Fechas `20230301` / `20240301` / `20250312`, `MJAHR='2024'` | SAP-0 T-15 | ventanas por parámetro (bind), con solape `SAP_HANA_DEFAULT_LOOKBACK_DAYS` |
| Destinos y transportes fijos (`'3730'`, `'1'`, `'1001'`, `'000000000000'`) | SAP-0 T-16 | origen y destino reales del documento; resolución por mapping |
| `'%NO USAR%'`, prefijo `AUFNR` `'7'` | SAP-0 T-10, T-17 | no se replican; `CURRENT_SAP_VALIDATION` (SAP-0 §6) |

Además: sin listas `IN` dinámicas (una consulta por cada `BUKRS` mapeado, Q6) y sin scan abierto del catálogo.

## 5 · Qué NO se copia

| Elemento legacy | Motivo | Reemplazo |
|---|---|---|
| SQL de `querysHana.py` | `LEGACY QUERY != CONTRACT` | definiciones nuevas del registry, con `source_status` |
| `inserts_thread.py` (`to_sql if_exists='replace'` + `sleep(3)`) | tablas temporales como puente de integración | RAW idempotente en `sap_inbound_records` |
| `operations.py` (funciones `store_*`) | escritura directa al dominio, sin idempotencia nativa | promoción controlada a `sap_references` |
| pandas | procesamiento en memoria sin contrato de columnas | validación por definición; columna obligatoria ausente ⇒ `SAP_SCHEMA_MISMATCH` |
| `app.py` (orquestación, VPN embebida, horario fijo) | `DO_NOT_REUSE` (SAP-0 §8) | servicio + scheduler propio, apagado por defecto |
| `schemas.py` (inventario de `SYS.TABLES`) | exploración abierta del catálogo | registry cerrado |
| `sap_integration.py` (`verify=False`) | TLS sin verificar; además es outbound | fuera de alcance; TLS obligatorio en inbound |

## 6 · Referencias

`audit/sap-soap/11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP.md` · `audit/sap0/SAP_LEGACY_REPOSITORY_AUDIT.md` §3–§8 · `specs/005-sap-hana-cloud-readonly-inbound/{spec,research,data-model}.md` · `01_ARCHITECTURE_DECISION.md`
