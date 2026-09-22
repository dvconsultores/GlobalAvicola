# SAP-SOAP · 10_SAP_SOAP_RAW_STAGING_MAPPING

Fecha: 2026-09-22 · RAW/STAGING bajo el mecanismo SOAP (§26) · Evoluciona el diseño de SAP-0 (`SAP_RAW_STAGING_SPEC.md`) sin romperlo

---

## 1 · Flujo obligatorio

```
SOAP RESPONSE → RAW → VALIDATION → MAPPING → STAGING → PROMOTION → DOMAIN
```

**Nunca**: `SOAP → DOMAIN DIRECTLY`. Ninguna operación SOAP escribe jamás en tablas de dominio; la promoción es un job separado, auditado e idempotente.

## 2 · Registro RAW (contrato actualizado para SOAP)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | PK | secuencia RAW |
| `source_system` | string | `SAP` |
| `soap_operation` | string | p. ej. `GetPurchaseOrders` |
| `schema_version` | string | del contrato (ej. `1.0`) |
| `request_id` | string | `RequestId` de GA (trazabilidad end-to-end) |
| `source_primary_key` | string | clave reconstruida del objeto (KEY del field catalog) |
| `raw_payload` | jsonb | registro completo normalizado (1 registro = 1 fila) |
| `payload_hash` | string | hash estable del payload |
| `received_at` | timestamp | recepción en GA |
| `sync_job_id` | string | job de extracción |
| `validation_status` | enum | `PENDING/VALID/INVALID/QUARANTINE` |
| `mapping_status` | enum | `PENDING/MAPPED/UNMAPPED/CONFLICT/PENDING_MAPPING` |
| `error` | string | error saneado (sin secretos) |

(Se conservan además `mandt/company_code` desnormalizados para aislamiento multiempresa y filtrado operativo.)

## 3 · Idempotencia e integridad (§27)

| Situación | Regla |
|---|---|
| misma clave + mismo `payload_hash` | **no duplicar** (no-op) |
| misma clave + hash distinto | nueva **versión** del registro (histórico conservado) |
| reintento tras TIMEOUT | seguro: la regla de hash absorbe duplicados |
| batch repetido | idempotente por (soap_operation, clave, hash) |

`payload_hash` se calcula en GA sobre el payload normalizado (orden canónico de campos) — el contrato exige estabilidad de campos, no de serialización XML.

## 4 · Validación → Mapeo → Staging

| Etapa | Contenido | Reglas |
|---|---|---|
| VALIDATION | tipos, obligatorios (R), longitudes, enumeraciones, coherencia fechas | registros inválidos → `QUARANTINE` (no se descartan en silencio) |
| MAPPING | resolución de claves GA: COMPANY_CODE→company; WERKS→plant/farm; LGORT→mapping configurable; MATNR→material+categoría GA; LIFNR→supplier | sin resolución → `PENDING_MAPPING`; **fail-closed**: no promoción |
| STAGING | registro listo con claves internas + referencia al RAW | inmutable hasta promoción |
| PROMOTION | upsert idempotente por clave canónica, por lote (`promotion_job_id`) | transaccional por lote; rollback lógico reconstruible desde RAW |

## 5 · Vínculo con el diseño SAP-0

- Se **mantienen**: capas RAW/STAGING/CANÓNICO/AUDITORÍA, cuarentena, fail-closed multiempresa, reconciliación R1–R4.
- Se **añaden** al RAW: `soap_operation`, `schema_version`, `request_id` (específicos del mecanismo SOAP).
- Se **retira** del flujo inbound: cualquier variante Direct HANA (SUPERSEDED_FOR_INBOUND).

## 6 · Auditoría

Cada promoción registra: `sync_job_id`, `promotion_job_id`, conteos por estado, errores saneados, ventana de origen. La cadena `RequestId → RAW → STAGING → dominio → auditoría` debe ser reconstruible (§27 del mandato).
