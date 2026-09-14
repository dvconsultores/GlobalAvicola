# GA-REQ-061 · DISEÑO EXCEL + STAGING (PROPOSED)

## 1 · Flujo oficial

```
DESCARGAR PLANTILLA → COMPLETAR → SUBIR → PARSE → STAGING → VALIDAR
→ PREVIEW → CORREGIR ERRORES (re-subir) → SUBMIT → APPROVE → APPLY
```

Regla dura: **Excel nunca escribe tablas operacionales** (AC43/44). Tratamiento: Excel = **DATA**, jamás código (sin macros, sin fórmulas en ejecución; AC47/48).

## 2 · Plantillas — decisión

**PROPOSED: plantilla por BU, versionada** (`cutover_template_{grandparent|breeder|hatchery|broiler}_v1.xlsx`).
Justificación: los conjuntos de campos por BU difieren (aves vs producción vs incubación en curso vs engorde); una plantilla multi-BU única obligaría a columnas vacías masivas y validaciones condicionales frágiles. La versión (`template_version`) viaja en la hoja `Meta` y se valida al subir (AC45; error `TEMPLATE_VERSION_UNSUPPORTED`).

Contenido de cada plantilla:
- Hoja `Instrucciones` (unidades, obligatorios/opcionales, ejemplos, valores permitidos, semántica **UNKNOWN**: **celda vacía = UNKNOWN; `0` explícito = cero conocido**; `N/A` = NOT_APPLICABLE).
- Hoja `Meta`: `template_version`, `company`, `business_unit`, `cutover_datetime` (fecha-hora de corte).
- Hoja `Datos`: filas de lotes/procesos con `legacy_lot_code` o `lot_code` (si el lote ya existe), referencias maestras por **código** (farm_code, area_code, house_code…), fechas ISO, números sin formato local.
- Nunca se confía en formato/estilos como dato; el parser futuro leerá **valores** (p.ej. `openpyxl` `read_only+data_only`; dependencia nueva PROPOSED en la tranche).

## 3 · Staging (PROPOSED)

`CutoverStagingRow`: `id · batch_id · row_number · raw (JSON) · normalized (JSON tipado por regla) · validation_status · validation_errors[] · created_at`.
- El archivo original y su `source_checksum_sha256` se conservan como evidencia (archivo + registro), aunque el staging se archive/purge por política.
- Validación = sin efecto operacional; corregir archivo y re-validar es libre antes de SUBMIT.
- Idempotencia: mismo checksum ⇒ misma respuesta determinista, sin duplicar filas/saldos/lotes (AC50).

## 4 · Errores de validación (estructurados, AC46)

`{row_number, column, field, error_code, message, received_value}`.
Catálogo mínimo: `MASTER_NOT_FOUND` · `MASTER_INACTIVE` (solo referencia nueva, OD-21) · `INVALID_DATE` · `INVALID_NUMBER` · `INVALID_UNIT` · `LOT_DUPLICATE` · `OPENING_ALREADY_EXISTS` · `BU_DISABLED` (OD-16) · `CROSS_TENANT_REFERENCE` · `TEMPLATE_VERSION_UNSUPPORTED` · `REQUIRED_FIELD_MISSING` · `CONSISTENCY_MISMATCH` (invariante §21 del mandato, solo si TODOS los componentes son KNOWN).

Ejemplo de presentación:

```
Fila 18 · Campo: farm_code · Código: MASTER_NOT_FOUND
Mensaje: Granja no existe o no pertenece a la empresa.
Recibido: F-999
```

## 5 · Validaciones de consistencia

Si todos los componentes del balance son KNOWN:
`placed − mortality − culls − outbound_transfers + inbound_transfers = live_at_cutover` ⇒ si no cuadra ⇒ `CONSISTENCY_MISMATCH` (bloquea apply). Con UNKNOWN presentes: **no se exige** igualdad artificial (AC15-16). Tolerancias: prohibidas sin decisión de negocio (`OWNER_GATE_REAL` si se necesitan).

## 6 · Preview y reconciliación

- PREVIEW: resumen por fila (válida/errores) + totales (42 leídos / 38 válidos / 4 con errores / 0 aplicados) — sin efectos (AC26/80).
- RECONCILIACIÓN (doc 11/AC78-79): batch, company, BU, cutover, source, checksum, items, openings, acumulados conocidos, **conteo de métricas UNKNOWN**, errores, applied_by/at, correcciones.

## 7 · Seguridad del parsing

- No ejecutar macros/fórmulas/scripts embebidos; extensión y tipo MIME validados; límite de tamaño; errores de parseo ⇒ `INVALID_FILE` sin romper el batch.
- El archivo se guarda con acceso por company (mismo control que el batch).
