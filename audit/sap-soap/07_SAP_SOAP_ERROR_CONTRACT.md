# SAP-SOAP · 07_SAP_SOAP_ERROR_CONTRACT

Fecha: 2026-09-22 · Errores técnicos vs funcionales (§31) · Sin implementación

---

## 1 · Separación obligatoria

| Tipo | Canal | Uso |
|---|---|---|
| **Funcional** (filtro inválido, objeto no encontrado, sin permiso…) | Respuesta normal con `Success=false` + `ErrorCode/ErrorMessage` | Errores esperables del contrato |
| **Técnico** (servicio caído, fault SOAP, excepción no controlada) | **SOAP Fault** con `faultcode/faultstring` + `detail` | Errores de infraestructura/protocolo |

Nunca mezclar: un `OBJECT_NOT_FOUND` **no** es un Fault; un `TEMPORARY_UNAVAILABLE` **no** es una respuesta `Success=false` vacía (debe llegar como Fault **o** como funcional con código correspondiente — el proveedor elige **un** canal por código y debe documentarlo; la tabla §3 propone canal).

## 2 · Detalle funcional y técnico (estructura común)

```xml
<ErrorDetail>
  <ErrorCode>INVALID_FILTER</ErrorCode>
  <ErrorMessage>texto legible (sin datos sensibles)</ErrorMessage>
  <ObjectType>PurchaseOrder</ObjectType>        <!-- opcional -->
  <DocumentNumber>4500015040</DocumentNumber>   <!-- opcional -->
  <CorrelationId>...</CorrelationId>            <!-- SIEMPRE -->
</ErrorDetail>
```

`CorrelationId` obligatorio en todo error: es la llave de soporte entre GA y SAP/ABAP.

## 3 · Catálogo de errores (lista cerrada — §31)

| ErrorCode | Significado | Canal propuesto | Reintentable por GA | Acción GA |
|---|---|---|---|---|
| `AUTHENTICATION_ERROR` | credencial inválida/expirada | Fault `Client` | No (sin corregir) | alerta + detener job |
| `AUTHORIZATION_ERROR` | autenticado pero sin permiso al objeto | Fault `Client` | No | alerta + escalar |
| `INVALID_FILTER` | filtro inválido (fechas, claves, ventana) | Funcional | No | falla job; corregir parámetros |
| `OBJECT_NOT_FOUND` | documento/clave inexistente | Funcional | No | registrar; no es error de carga |
| `SAP_INTERNAL_ERROR` | error interno SAP | Fault `Server` | Sí (con backoff) | retry + alerta si persiste |
| `TIMEOUT` | el servicio excedió el tiempo | Fault/timeout de transporte | Sí (idempotente) | retry con backoff |
| `SCHEMA_ERROR` | payload/schema incompatible | Fault `Client` o Funcional | No | verificar SchemaVersion |
| `TEMPORARY_UNAVAILABLE` | mantenimiento/caída temporal | Fault `Server` | Sí (backoff) | retry + circuit breaker |

Reglas:
1. Códigos **fuera** de esta lista = defecto de contrato (reportar; no reintentar a ciegas).
2 `ErrorMessage` jamás contiene credenciales, datos personales ni SQL/detalles internos.
3. Todo error se registra en RAW/auditoría con `request_id` + `correlation_id` + `error_code` (saneado).

## 4 · Matriz de reintento (§30)

| ErrorCode | Retry | Backoff | ¿Rompe circuit breaker? |
|---|---|---|---|
| TIMEOUT | ✔ | exponencial | acumula |
| TEMPORARY_UNAVAILABLE | ✔ | exponencial | ✔ |
| SAP_INTERNAL_ERROR | ✔ | exponencial | ✔ si persiste |
| resto | ✗ | — | — |

Solo reintentan operaciones **read/idempotentes** (todas las de este contrato lo son). Cada intento se registra (intento, timestamp, resultado).

## 5 · Ejemplos

- Fault técnico: ver `06_…` §7 (`TEMPORARY_UNAVAILABLE` con `CorrelationId`).
- Error funcional: ver `06_…` §8 (`INVALID_FILTER` con `Success=false`).
