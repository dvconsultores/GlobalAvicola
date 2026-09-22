# SAP-SOAP · 09_SAP_SOAP_DELTA_PAGINATION_SPEC

Fecha: 2026-09-22 · Paginación (§24) y sincronización incremental (§25) · Sin implementación

---

## 1 · Paginación

**Preferencia GA**: `ContinuationToken` (opaco, server-side). **Fallback aceptado**: `PageNumber/PageSize`.

| Aspecto | Regla |
|---|---|
| Tamaño de página | `PageSize` ≤ **500** registros (límite máximo acordado; menor para MaterialMovements si SAP lo requiere) |
| Default | Si GA no envía `PageSize`, el servicio NO puede devolver más de 500 |
| Token | Opaco, no reutilizable en otro filtro; expira (propuesta: ≥15 min); su contenido no se interpreta en GA |
| Orden estable | El servicio garantiza orden determinista por clave de registro durante la paginación (requisito para token) |
| Consistencia | Cada página es consistente con el filtro; cambios concurrentes pueden aparecer como delta posterior (no se exige snapshot transaccional global) |
| Fin | `HasMore=false` y token vacío |
| Seguridad | Si el token es inválido/expirado → `INVALID_FILTER` (funcional) y GA reinicia la consulta |

**Prohibido por contrato**: responder “todo” en una llamada (MATDOC u órdenes completas). Ventana temporal obligatoria en operaciones documentales.

## 2 · Sincronización incremental

```
INITIAL_SNAPSHOT → DELTA → RECONCILIATION
```

| Fase | Mecánica | Uso |
|---|---|---|
| INITIAL_SNAPSHOT | paginación completa por objeto (ventana acotada) | primera carga |
| DELTA | `ChangedSince` (+ cursor/watermark) | periodicidad normal |
| RECONCILIATION | re-lectura por ventana + comparación de hashes (R1–R4 de SAP-0) | cierre de brechas |

### Mecanismos admitidos de delta (§25)
1. `ChangedSince` (timestamp de cambio del objeto) — **preferido para maestros**.
2. Rango `PostingDate/DocumentDate` — **preferido para documentos** (movimientos, OC).
3. Timestamp de cambio de documento (si SAP lo expone por tipo).
4. Secuencia/cursor (`ContinuationToken` incremental).

**No se fija un campo SAP específico**: ABAP propone el mejor campo disponible por objeto (OI-07); GA valida que cumpla: monotónico, actualizado en cada cambio, comparable por rango.

### Watermark por objeto (a confirmar con ABAP)

| Objeto | Delta propuesto | Fallback |
|---|---|---|
| Companies/Plants/StorageLocations/Vendors/Materials | `ChangedSince` (o snapshot) | snapshot semanal |
| Batches | `ChangedSince` o vía movimientos | snapshot |
| PO / PO History / Production / Outbound / Transfer | fecha documento + `ChangedSince` | ventana por `PostingDate` |
| MaterialMovements | `PostingDate` + `ChangedSince` (ventana obligatoria) | — |

### Semántica de borrado/desactivación
- Maestros: `ACTIVE_STATUS=INACTIVE` observable por delta o **barrido de reconciliación** (los borrados físicos no son fiables por delta).
- Documentos: no se borran; reversos aparecen como nuevos registros (`REVERSAL_REFERENCE`).

## 3 · Reconciliación (contrato de comportamiento)

| Regla | Detalle |
|---|---|
| R1 | conteo remoto vs RAW por ventana (si el servicio expone `RecordCount` global re-computable; si no, muestreo por clave) |
| R2 | re-lectura de claves detectadas como faltantes (`DocumentNumber` puntual) |
| R3 | comparación `payload_hash` (misma clave, distinto hash = cambio real) |
| R4 | informe de discrepancias → cuarentena (`PENDING_MAPPING`/`MANUAL_REVIEW`), nunca sobrescritura ciega |

## 4 · Timeout/retry (§30)

| Parámetro | Valor propuesto |
|---|---|
| Connect timeout | 10 s |
| Read timeout | 60 s (documentos grandes: hasta 120 s con acuerdo) |
| Retry | solo read/idempotentes; backoff exponencial (1, 5, 15, 60 min; máx 5 intentos/job) |
| Circuit breaker | abre tras 3 fallos consecutivos; cooldown 30 min; alerta |
| Registro | cada intento con `request_id`, duración, resultado |

## 5 · Criterios de aceptación (fase SOAP-2+)

| ID | Criterio |
|---|---|
| DP-01 | Paginación completa verificable de un dataset grande sin duplicados ni faltantes (por clave) |
| DP-02 | Token inválido/expirado manejado como `INVALID_FILTER` |
| DP-03 | Delta por `ChangedSince` reproducible (mismo filtro = mismo conjunto estable) |
| DP-04 | Ventana obligatoria funciona (sin filtro → error funcional claro) |
| DP-05 | Reconciliación por hash detecta un cambio real y un no-cambio |
