# Especificación Técnica de Integración SOAP SAP ↔ Global Avícola (Lider Pollo)

**Documento**: `Especificacion_Tecnica_Integracion_SOAP_SAP_Global_Avicola_Lider_Pollo`
**Versión**: 1.0 (borrador para revisión conjunta) · **Fecha**: 2026-09-22
**Contrapartes**: Lider Pollo (SAP/ABAP) · Global Avícola / Global DV
**Base contractual**: `audit/sap-soap/01…15` + `specs/003-sap-soap-inbound-contract/` (este documento resume; **no introduce decisiones no cerradas como hechos**).

---

## 1 · Objetivo

Definir el contrato de integración **SAP → Global Avícola** vía **servicio SOAP** que el proveedor SAP construirá y expondrá. Global Avícola actúa como **consumidor (cliente SOAP)** en modelo **PULL**.

## 2 · Roles

| Parte | Rol |
|---|---|
| Lider Pollo / proveedor SAP | **SOAP server**: implementa y expone el servicio |
| Global Avícola | **SOAP client**: consulta, valida, mapea y promueve datos a su dominio |
| Global DV | Soporte técnico de Global Avícola |

## 3 · Flujo de datos

```
SAP → Servicio SOAP (proveedor) → GA (cliente SOAP) → RAW → Validación → Mapeo → Staging → Promoción → Dominio GA
```

## 4 · Operaciones (12 núcleo + 1 opcional)

| Operación | Contenido | Filtros principales |
|---|---|---|
| `GetCompanies` | sociedades | ChangedSince |
| `GetPlants` | centros | ChangedSince/estado |
| `GetStorageLocations` | almacenes (por centro) | Plant |
| `GetVendors` | proveedores | ChangedSince/estado |
| `GetMaterials` | materiales + descripción/UoM/estado | ChangedSince |
| `GetPurchaseOrders` | OC con **ítems anidados** | CompanyCode, fechas, documento |
| `GetPurchaseOrderHistory` | pedidos/recepciones OC | documento, fechas |
| `GetProductionOrders` | órdenes de producción | Plant, fechas |
| `GetOutboundOrders` | órdenes de salida | Plant, fechas |
| `GetTransferOrders` | transferencias (alimento/medicinas/vacunas/aves/huevos/pollitos) | CompanyCode, fechas |
| `GetMaterialMovements` | documentos de material (DTO, ventana obligatoria) | fechas, documento |
| `GetBatches` | lotes | material/centro |
| `GetIntegrationChanges` *(opcional)* | incremental común propuesto a ABAP | ChangedSince + cursor |

## 5 · Mensajes

**Request** (común): `RequestId`, `SchemaVersion`, `ClientSystem` (obligatorios) + `CompanyCode`, `Plant`, `FromDate/ToDate`, `ChangedSince`, `DocumentNumber`, `Status`, `PageNumber`, `PageSize`, `ContinuationToken`, `Language` según operación.

**Response** (común): `Header { RequestId, ResponseTimestamp, Success, ErrorCode, ErrorMessage, SchemaVersion, RecordCount, HasMore, ContinuationToken }` + `Records[]`.

**Ejemplos XML completos**: `audit/sap-soap/06_SAP_SOAP_REQUEST_RESPONSE_EXAMPLES.md` (6 operaciones + Fault).

## 6 · Campos por objeto

Catálogo campo a campo (tipo, obligatorio/opcional, clave, filtros, notas) en `audit/sap-soap/04_SAP_SOAP_FIELD_CATALOG.md`. Puntos clave para SAP:
- Todas las claves documentales incluyen su número de documento y posición.
- `MATNR` se entrega **con su metadata** (descripción, UoM, estado); la categorización funcional (alimento/medicina/vacuna/ave/huevo/pollito) la resuelve Global Avícola (no se hardcodea).
- `LGORT` no se asume equivalente a galpón; el mapeo es configurable en GA.
- No se requieren tablas SAP directas: el servicio entrega **DTO de negocio** (p. ej. movimientos de material; no `MATDOC` como tal).

## 7 · Paginación y delta

- **Paginación**: `ContinuationToken` preferido (fallback `PageNumber/PageSize`); máximo de página acordado: **500**; orden estable obligatorio; ventana temporal obligatoria en documentos.
- **Delta**: `ChangedSince` (maestros) y rangos de fecha documental / timestamp de cambio (documentos); reconciliación periódica por ventana. El campo exacto de delta por objeto se confirma con ABAP.

## 8 · Errores

Lista cerrada (8 códigos): `AUTHENTICATION_ERROR`, `AUTHORIZATION_ERROR`, `INVALID_FILTER`, `OBJECT_NOT_FOUND`, `SAP_INTERNAL_ERROR`, `TIMEOUT`, `SCHEMA_ERROR`, `TEMPORARY_UNAVAILABLE`. Errores funcionales en la respuesta (`Success=false`); técnicos por SOAP Fault; `CorrelationId` obligatorio. Detalle: `07_SAP_SOAP_ERROR_CONTRACT.md`.

## 9 · Seguridad

- **HTTPS/TLS 1.2+ obligatorio**, certificado válido.
- Autenticación a acordar: **WS-Security UsernameToken** (recomendada), **mTLS** (preferida si la infraestructura lo permite) o **Basic-over-TLS** (aceptable como mínimo) + allowlist de IP.
- Prohibido: validación TLS deshabilitada, contraseñas en XML/URL, credenciales en repositorios o logs.

## 10 · Versionado del contrato

`SchemaVersion` obligatorio (inicial **1.0**). Cambios incompatibles ⇒ **nueva versión**; nunca cambio silencioso de esquema en producción.

## 11 · Puntos abiertos a confirmar con SAP (reunión)

Lista corta (detalle en `13_SAP_SOAP_PROVIDER_OPEN_ITEMS.md`): publicación WSDL/sandbox · estilo/literal · paginación por token · campo delta por objeto · `GetIntegrationChanges` · autenticación definitiva · versionado · semántica de órdenes de salida · Business Partner/CVI · campos reales de órdenes de producción · cost centers (fase posterior) · volúmenes · errores · ejemplos adaptados · datos de prueba · tipos de movimiento actuales.

## 12 · Referencia histórica (no vinculante)

Los queries del sistema anterior (`SapHanaLP`) se adjuntan **solo como referencia funcional** para ABAP (`11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP.md`): documentan qué información se usaba históricamente y con qué filtros. **El contrato vigente es este documento y sus anexos; el legado no es especificación.**

## 13 · Estado del documento

`BORRADOR v1.0 — para revisión conjunta`. Las decisiones no cerradas figuran como puntos abiertos (§11) y **no** como hechos. Próxima iteración tras la reunión con el proveedor: v1.1 con WSDL/examples adaptados.
