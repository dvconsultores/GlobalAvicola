# Feature Specification: SAP-SOAP-1 — SOAP Inbound Contract

**Feature Branch**: `specs/003-sap-soap-inbound-contract`
**Created**: 2026-09-22 · **Status**: Validated (SPEC ONLY — sin implementación)
**Input**: Mandato «SAP-SOAP-1 — SOAP INBOUND CONTRACT & IMPLEMENTATION READINESS» (Owner, 2026-09-22) + reunión técnica Lider Pollo / proveedor SAP / Global DV
**Paquete de auditoría asociado**: `audit/sap-soap/01…15`

---

## PURPOSE
Definir el **contrato exacto** que Global Avícola entrega al proveedor SAP para que construya el servicio SOAP inbound, y deixar diseñada (sin implementar) la ruta de consumo en GA: `SOAP → RAW → VALIDATION → MAPPING → STAGING → PROMOTION → DOMAIN`.

## BUSINESS_CONTEXT
- La reunión técnica cambió el mecanismo inbound: **SOAP** (pull), proveedor SAP = server, GA = consumer.
- Direct HANA queda retirado como target inbound; los queries de `SapHanaLP` son **referencia funcional** para ABAP, no contrato.
- Prioridades de cliente: empresas, almacenes, OC, órdenes de salida, órdenes de producción y transferencias (alimento, medicinas, vacunas, aves, huevos, pollitos) + maestros para interpretarlos.

## ARCHITECTURE_DECISION
Ver `audit/sap-soap/01_SAP_SOAP_ARCHITECTURE_DECISION.md`. Valores canónicos: `SAP_INBOUND_MECHANISM=SOAP` · `SAP_SOAP_PROVIDER=LIDER_POLLO_SAP_PROVIDER` · `GLOBAL_AVICOLA_ROLE=SOAP_CONSUMER` · `DIRECT_HANA_INBOUND=RETIRED_AS_TARGET_ARCHITECTURE` · `LEGACY_SQL=REFERENCE_ONLY` · `SAP_BRIDGE_DIRECT_HANA=SUPERSEDED_FOR_INBOUND`. Retenidos: RAW_STAGING, ADAPTER_PATTERN, FAIL_CLOSED, AUDIT, IDEMPOTENCY, MULTICOMPANY_ISOLATION.

## SCOPE
1. Contrato de **12 operaciones núcleo + 1 opcional** (`03_…`) y **13 objetos inbound** con field catalog R/O (`02_…`, `04_…`).
2. Request/Response comunes, paginación, delta, idempotencia, errores, seguridad, versionado, WSDL/XSD (`03_…`, `05_…`, `07_…`, `08_…`, `09_…`, `10_…`).
3. Ejemplos XML (`06_…`); anexo legacy para ABAP (`11_…`); spec de cambio del adaptador GA (`12_…`).
4. Open items con el proveedor y readiness (`13_…`, `14_…`).

## OUT_OF_SCOPE
Implementación (cualquier lado); SOAP/red calls; WSDL real; SAP conexión; HANA; deploy; G1/G2; `RealSapAdapter`; export GA→SAP (otra SPEC); PUSH sin decisión; cost centers fase 1 (deferido); acceso directo HANA.

## ACTORS
| Actor | Rol |
|---|---|
| Proveedor SAP/ABAP (Lider Pollo) | construye/expone el SOAP server contra este contrato |
| Global Avícola / Global DV | SOAP consumer (futuro `SoapSapAdapter`), RAW/STAGING/promoción |
| Owner | aprueba scope/deferrals; custodia de secretos (`AOD-12`) |
| SAP Basis/Seguridad | red, TLS, cuentas, allowlist |

## SOAP_OPERATIONS
12 núcleo: GetCompanies, GetPlants, GetStorageLocations, GetVendors, GetMaterials, GetPurchaseOrders (items anidados), GetPurchaseOrderHistory, GetProductionOrders, GetOutboundOrders, GetTransferOrders, GetMaterialMovements, GetBatches. +1 opcional: `GetIntegrationChanges`. Detalle: `03_…`.

## REQUEST_CONTRACTS
Header común con `RequestId, SchemaVersion, ClientSystem` obligatorios y `CompanyCode, Plant, FromDate/ToDate, ChangedSince, DocumentNumber, Status, PageNumber, PageSize, ContinuationToken, Language` según matriz de aplicabilidad (`03_… §2`). Ventana temporal obligatoria en operaciones documentales.

## RESPONSE_CONTRACTS
`Header { RequestId, ResponseTimestamp, Success, ErrorCode, ErrorMessage, SchemaVersion, RecordCount, HasMore, ContinuationToken }` + `Records[]`. Errores funcionales en la respuesta; técnicos por SOAP Fault (`07_…`).

## FIELD_CATALOG
13 objetos campo a campo con tipo/obligatoriedad/clave/filtro (`04_…`). Claves: COMPANY_CODE · PLANT · PLANT+STORAGE_LOCATION · VENDOR · MATERIAL · PO_NUMBER(+ITEM) · EBELN+EBELP+BELNR · ORDER_NUMBER · TRANSFER_NUMBER(+DOCUMENT_NUMBER) · MBLNR+YEAR+ITEM · MATERIAL+PLANT+BATCH.

## SECURITY
TLS 1.2+ obligatorio; auth a acordar (WSS UsernameToken recomendada / mTLS preferida / Basic-over-TLS aceptable) + allowlist; prohibido `verify=False`, password en XML custom/URL, secretos en repo/logs; custodia `AOD-12` (`08_…`).

## PAGINATION
`ContinuationToken` preferido; `PageNumber/PageSize` fallback; PageSize ≤ 500; orden estable; sin respuestas masivas (`09_… §1`).

## DELTA
`INITIAL_SNAPSHOT → DELTA → RECONCILIATION`; mecanismos admitidos: `ChangedSince`, rangos de fecha de documento, timestamp de cambio, cursor incremental; campo exacto por objeto a confirmar con ABAP (`09_… §2`, OI-04).

## IDEMPOTENCY
Misma clave + mismo `payload_hash` → no-op; misma clave + hash distinto → nueva versión; reintentos seguros (`10_… §3`).

## RAW/STAGING
`SOAP → RAW → VALIDATION → MAPPING → STAGING → PROMOTION → DOMAIN`; RAW con `soap_operation, schema_version, request_id` + contrato SAP-0; nunca escritura directa a dominio; cuarentena; fail-closed (`10_…`).

## MULTICOMPANY
`SAP SYSTEM → MANDT → BUKRS → WERKS → GA COMPANY → BU`; sin resolución → `PENDING_MAPPING`, sin promoción (`10_… §4`).

## ERRORS
Lista cerrada de 8 códigos (AUTHENTICATION_ERROR, AUTHORIZATION_ERROR, INVALID_FILTER, OBJECT_NOT_FOUND, SAP_INTERNAL_ERROR, TIMEOUT, SCHEMA_ERROR, TEMPORARY_UNAVAILABLE) con canal y reintentabilidad (`07_…`).

## RETRIES
Solo read/idempotentes; backoff exponencial; circuit breaker; registro de intentos; timeouts 10/60 s (`09_… §4`).

## VERSIONING
`SchemaVersion` obligatorio (inicial 1.0); cambios breaking ⇒ nueva versión; prohibido cambio silencioso de XSD en producción (`05_… §3`).

## WSDL/XSD_REQUIREMENTS
WSDL document/literal wrapped con 12(+1) operaciones, XSD por operación y tipos comunes, ejemplos, catálogo de errores; el proveedor ajusta nombres sin eliminar información requerida (`05_…`).

## LEGACY_QUERY_REFERENCES
Anexo para ABAP con 13 queries/piezas, BWART y filtros históricos clasificados (`11_…`). **EL QUERY NO ES EL CONTRATO. EL SOAP CONTRACT ES EL CONTRATO.**

## GA_ADAPTER_CHANGES
Nuevo contrato inbound `SapInboundAdapter` + futuro `SoapSapAdapter` (diseñado, NO implementado); ABC export y Manual/Mock intactos; GA-REM-010 intacto (`12_…`).

## ACCEPTANCE_CRITERIA

| AC | Criterio | Estado |
|---|---|---|
| AC-SOAP-01 | Decisión SOAP formalizada | **PASS** (`01_…`) |
| AC-SOAP-02 | Direct HANA retirado como target inbound | **PASS** (`01_… §3` + addenda) |
| AC-SOAP-03 | SAP Provider = SOAP server | **PASS** |
| AC-SOAP-04 | Global Avícola = SOAP consumer (pull) | **PASS** |
| AC-SOAP-05 | Objetos inbound fase 1 definidos | **PASS** (13; `02_…`) |
| AC-SOAP-06 | Campos obligatorios/opcionales por objeto | **PASS** (`04_…`) |
| AC-SOAP-07 | Request/response por operación | **PASS** (`03_…`, `05_…`) |
| AC-SOAP-08 | Ejemplos XML | **PASS** (6 ops + fault; `06_…`) |
| AC-SOAP-09 | Catálogo de errores | **PASS** (`07_…`) |
| AC-SOAP-10 | Estrategia de paginación | **PASS** (`09_…`) |
| AC-SOAP-11 | Estrategia delta | **PASS** (`09_…`) |
| AC-SOAP-12 | RAW/STAGING preservado | **PASS** (`10_…`) |
| AC-SOAP-13 | SOAP nunca escribe directo al dominio | **PASS** (`10_… §1`) |
| AC-SOAP-14 | Multiempresa fail-closed | **PASS** (`10_… §4`) |
| AC-SOAP-15 | Queries legacy = referencia, no contrato | **PASS** (`11_…` expreso) |
| AC-SOAP-16 | Hardcodes legacy no pasan al producto | **PASS** (`11_… §2–3`) |
| AC-SOAP-17 | SoapSapAdapter diseñado, no implementado | **PASS** (`12_…`) |
| AC-SOAP-18 | Adapter Pattern preservado | **PASS** (`12_… §4`) |
| AC-SOAP-19 | Contrato convertible a WSDL/XSD | **PASS** (`05_…`) |
| AC-SOAP-20 | Producto no modificado | **PASS** (git; verificación §49) |

## Clarifications (schema §40 — GA_DECISION / SAP_PROVIDER_CLARIFICATION / OWNER_DECISION)

| # | Pregunta | Clase | Resolución |
|---|---|---|---|
| Q1 | ¿PUSH o PULL? | GA_DECISION | PULL asumido; PUSH solo si SAP lo exige (vuelve como decisión) |
| Q2 | ¿PO items como operación aparte? | GA_DECISION | Anidados en `GetPurchaseOrders` |
| Q3 | ¿Categorías de material en SAP? | GA_DECISION | NO: mapping en GA (anti-hardcode) |
| Q4 | ¿`GetIntegrationChanges` obligatorio? | SAP_PROVIDER_CLARIFICATION | Opcional (OI-05) |
| Q5 | ¿Campo de delta por objeto? | SAP_PROVIDER_CLARIFICATION | ABAP propone; GA valida propiedades (OI-04) |
| Q6 | ¿Auth definitiva? | SAP_PROVIDER_CLARIFICATION | Opciones aceptadas; decisión en reunión (OI-06) |
| Q7 | ¿COST_CENTER en fase 1? | OWNER_DECISION | Deferido propuesto; confirmar (OD-1) |
| Q8 | ¿Semántica BWART 641/303 actual? | SAP_PROVIDER_CLARIFICATION | Validación en reunión (OI-16); no regla |
