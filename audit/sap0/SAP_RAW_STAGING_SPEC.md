# SAP-0 · SAP_RAW_STAGING_SPEC

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY) · **Diseño de capas de datos de integración — no implementado**

---

## 1 · Separación obligatoria de capas (§20–22 del mandato)

| Capa | Qué contiene | Quién escribe | Quién lee |
|---|---|---|---|
| **RAW SAP** | Copia cruda normalizada de lo extraído (append-only, inmutable) | Job de extracción (o Bridge) | Validadores/mappers |
| **STAGING SAP** | Registros validados y mapeados a claves internas, **aún no promovidos** | Validadores/mappers | Job de promoción, analistas |
| **CANÓNICO (dominio GA)** | Tablas del producto (`companies`, `farms`, `houses`, `suppliers`, `sap_references`, …) | **Solo** job de promoción controlado + operación humana | Producto completo |
| **AUTITORÍA** | Bitácora de cada paso (job, lote, resultado, errores) | Todas las capas | Auditoría/Certificación |

**PROHIBIDO**: que una extracción escriba directo en tablas de dominio; que el Bridge conozca tablas del producto; que un fallo de validación mute el canónico.

## 2 · Contrato de registro RAW (campos canónicos, §21)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | PK técnica | secuencia del almacén RAW |
| `source_system` | string | `SAP` (fuente) |
| `sap_system_id` | string | SID/identificador del sistema SAP actual (UNKNOWN hasta discovery) |
| `mandant` | string | Mandante de origen (evidencia legacy `120`, NO asumido) |
| `company_code` | string | BUKRS de origen del registro |
| `object_type` | string | uno de los 12 inbound (`SAP_COMPANY`, `SAP_PLANT`, …) |
| `source_primary_key` | string | clave de origen exacta (ej. `WERKS`, `EBELN+EBELP`, `MBLNR+MJAHR+ZEILE`) |
| `source_version` | string | versión/etag/change-doc cuando exista; si no, hash de campos |
| `raw_payload` | jsonb | payload completo normalizado (sin transformar a dominio) |
| `payload_hash` | string | hash estable del payload → **idempotencia de ingesta** |
| `extracted_at` | timestamp | momento de extracción en origen |
| `ingested_at` | timestamp | momento de ingesta a RAW |
| `sync_job_id` | string | job que produjo el registro (trazabilidad) |
| `watermark` | string | marca de avance usada (BUDAT/CPUDT/offset) |
| `validation_status` | enum | `PENDING`/`VALID`/`INVALID`/`QUARANTINE` |
| `mapping_status` | enum | `PENDING`/`MAPPED`/`UNMAPPED`/`CONFLICT` |
| `error_code` / `error_detail` | string | error saneado (nunca secretos) |

Reglas RAW: **append-only**; re-ingesta del mismo `(object_type, source_primary_key, payload_hash)` = no-op (idempotente); nunca se actualiza un RAW válido (la corrección entra como nueva versión).

## 3 · Flujo de promoción (diseño)

```
EXTRACT ──► RAW (append, hash-idempotente)
             │ validación (tipos, dominios, obligatorios, multi-compañía)
             ▼
           STAGING (validado + mapped a claves internas, aún sin efecto)
             │ revisión de conflictos / cuarentena
             ▼
           PROMOCIÓN (upsert idempotente por clave canónica, transaccional por lote)
             ▼
           CANÓNICO + AUDITORÍA
```

- Toda promoción es **por lote** con `promotion_job_id`, contadores y rollback lógico (estado previo reconstruible desde RAW).
- Los registros `INVALID`/`CONFLICT` van a **cuarentena** y requieren resolución (manual u Owner), no se descartan en silencio (§30).
- Multi-compañía **fail-closed**: si un registro no permite resolver `company_code→tenant`, NO se promueve.

## 4 · Snapshot / Delta / Watermark (por objeto, §23)

| Objeto | Modo inicial | Delta candidate | Watermark propuesto |
|---|---|---|---|
| SAP_COMPANY | snapshot | — | `ingested_at` |
| SAP_PLANT | snapshot | por change docs si existen | snapshot completo |
| SAP_STORAGE_LOCATION | snapshot | por change docs si existen | snapshot completo |
| SAP_VENDOR | snapshot + delta | BP change docs | `changed_at`/snapshot |
| SAP_MATERIAL | snapshot + delta | material change docs | `changed_at`/snapshot |
| SAP_PURCHASE_ORDER / ITEM / HISTORY | delta | fecha de cambio de cabecera/posición | `AEDAT`/`CPUDT` si existen (validar) |
| SAP_TRANSFER_ORDER | delta | change docs | idem |
| SAP_MATERIAL_DOCUMENT | delta | **sí** | `CPUDT`/`BUDAT` + `MBLNR` (necesita validación current) |
| SAP_BATCH | snapshot + por documento | vía documentos | derivado de MATDOC |
| SAP_COST_CENTER | snapshot | — | snapshot completo |

Reglas de watermark: monotónico; solapamiento deliberado de ventana (p. ej. re-lectura de N horas) para cubrir escrituras tardías; re-proceso de ventana = idempotente por hash; si no hay columna de cambio fiable → **snapshot completo** con reconciliación por hash (nunca delta «ciego»).

## 5 · Reconciliación (§24)

| Nivel | Conciliación | Salida |
|---|---|---|
| R1 | SAP ↔ RAW (conteos y hashes por ventana) | faltantes por extraer / re-procesar |
| R2 | RAW ↔ STAGING (validación/mapping) | cuarentena explicada |
| R3 | STAGING ↔ CANÓNICO (promoción) | pendientes de promoción |
| R4 | CANÓNICO ↔ SAP (verdad funcional, muestreo) | informes de convergencia (`SAP_COMPANY_FARM_CONVERGENCE_SPEC.md`) |

Clases de discrepancia (permitidas): `MISSING_IN_RAW`, `MISSING_IN_STAGING`, `MISSING_IN_CANONICAL`, `HASH_DIVERGENT`, `MANUAL_REVIEW_REQUIRED`. Ninguna se resuelve por sobrescritura automática de datos GA-only sin aprobación del Owner.

## 6 · Semántica de errores y estados `UNKNOWN` (§30)

- `UNKNOWN_SAP_VALUE`: valor de SAP que el mapeo no entiende → **staging + decisión**, nunca falsa equivalencia.
- `UNKNOWN_GA_MAPPING`: clave interna ausente → cuarentena + reporte.
- `FAIL_CLOSED`: ante duda multi-compañía, no promoción.
- Los estados anteriores son **de integración**; no alteran los estados de negocio del producto.

## 7 · Definition of Done (para la futura SAP-1..SAP-5 — NO ahora)

1. Tablas RAW/STAGING con el contrato de §2. 2. Jobs con `sync_job_id`s auditables. 3. Promoción idempotente con rollback lógico. 4. Informes R1–R4. 5. Pruebas de idempotencia/duplicados/cuarentena. 6. Evidencia de que el dominio solo ve datos promovidos.
