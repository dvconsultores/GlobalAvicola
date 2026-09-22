# SAP-SOAP · 05_SAP_SOAP_WSDL_XSD_REQUIREMENTS

Fecha: 2026-09-22 · Qué debe poder generar el proveedor ABAP a partir de este paquete (§33)

---

## 1 · Entregable exigido al proveedor

| Entregable | Contenido mínimo |
|---|---|
| **WSDL** | 1 servicio, 12 operaciones núcleo (+1 opcional), binding **document/literal wrapped**, endpoint HTTPS |
| **XSD** | esquemas de request/response por operación + tipos comunes (Header, ErrorDetail, enumeraciones) |
| **Ejemplos** | los de `06_SAP_SOAP_REQUEST_RESPONSE_EXAMPLES.md` adaptados al naming final |
| **Catálogo de errores** | `07_SAP_SOAP_ERROR_CONTRACT.md` implementado tal cual (códigos y semántica) |
| **Versión** | `SchemaVersion` en servicio y mensajes; política §32 |

## 2 · Convenciones de contrato (propuestas GA — ajustables por ABAP sin perder información)

| Aspecto | Propuesta |
|---|---|
| Target namespace (ejemplo) | `urn:globalavicola:sap:inbound:v1` |
| Estilo | document/literal wrapped (estándar, interoperable) |
| OperationName | `Get<Object>` (nombres técnicos ajustables) |
| Tipos | `C,N,D,TS,DEC,BOOL` del field catalog (`04_…`) con longitudes SAP reales |
| Nulos | elementos opcionales **ausentes** (no vacíos) |
| Multi-valor | `Records[]` con contenedor por operación |
| Enumeraciones | `ACTIVE_STATUS`, `ErrorCode` (lista cerrada `07_…`), `Language` ISO-639-1 |
| Header común | request/response Header según `03_…` §2/§3 |
| Seguridad | WS-Security policy **declarada** en WSDL (ver `08_…`) — sin exponer detalles de red |

## 3 · Reglas de integridad del contrato (§27)

1. `source_primary_key` por objeto debe ser reconstruible desde los campos KEY del catálogo de campos.
2. `SchemaVersion` obligatorio en request y response; cambio breaking ⇒ **nueva versión** (§32) — nunca cambio silencioso de XSD en producción.
3. `RequestId` ecoado en response (trazabilidad).
4. `payload_hash`: lo calcula GA sobre el payload normalizado; el contrato no exige un hash de SAP, pero **sí** estabilidad de campos para que el hash sea estable entre llamadas idénticas.
5. Paginación y delta declarados por operación (`09_…`), no globales.

## 4 · Proceso de ajuste (§33 del mandato)

- El proveedor SAP **puede** ajustar nombres técnicos y detalles de serialización.
- El proveedor **no puede** eliminar información requerida (campos R, keys, filtros, semántica de errores) sin **nueva clarificación** registrada en `13_SAP_SOAP_PROVIDER_OPEN_ITEMS.md`.
- Toda diferencia entre WSDL real y este paquete debe volver a GA como diff documentado antes de aceptar.

## 5 · Criterios de aceptación del WSDL/XSD (para fase SOAP-2+)

| ID | Criterio |
|---|---|
| W-01 | El WSDL importa en un cliente estándar (p. ej. zeep) sin warnings de esquema |
| W-02 | 12 operaciones núcleo presentes (o 13 con incremental) |
| W-03 | Header común y Fault conformes a `03_…`/`07_…` |
| W-04 | Enumeraciones y longitudes conformes a `04_…` (o diff justificado) |
| W-05 | Endpoint HTTPS con TLS válido (ver `08_…`) |
| W-06 | Ejemplos del paquete ejecutables contra el sandbox (SOAP-5) |
