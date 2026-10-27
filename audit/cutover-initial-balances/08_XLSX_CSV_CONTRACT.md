# CUTOVER-INITIAL-BALANCES · 08_XLSX_CSV_CONTRACT

Fecha: 2026-10-27 · SPEC 006 · parser: `backend/app/cutover/parser.py` · plantillas: `backend/app/cutover/templates.py`

## 1 · Descarga

`GET /api/v1/cutover-templates/{bu}?format=xlsx|csv&batch_id=` (permiso `cutover:create`). Con `batch_id`, el batch debe ser de la empresa efectiva **y de esa BU** (`BUSINESS_UNIT_MISMATCH` en caso contrario): la plantilla sigue al batch, nunca a un selector. `Meta.cutover_datetime` viaja rellena.

## 2 · XLSX (`cutover_template_{bu}_v2.xlsx`)

| Hoja | Contenido |
|---|---|
| `Instrucciones` | semántica vacío/0/N/A, formatos, unidades y una fila por campo: campo, significado, obligatorio, tipo, unidad, formato, ejemplo, valores permitidos, admite UNKNOWN, admite N/A, destino tras apply |
| `Meta` | `template_version = v2`, `schema_id`, `company` (empresa efectiva), `business_unit`, `generated_at`, `cutover_datetime` |
| `Datos` | cabecera exacta del contrato (orden libre al subir; nombres exactos) |
| `Catalogos` | `catalog, code, description, status, parent_code` — solo maestros **activos** de la empresa efectiva y de la BU (granjas/galpones(parent=granja)/áreas/fases/líneas/razas(parent=línea) · plantas/incubadoras/nacedoras(parent=planta)/lotes fuente · lotes existentes sin apertura) |

Lectura: `openpyxl` con `data_only=False` para detectar fórmulas (`FORMULA_NOT_ALLOWED`), rechazo de `vbaProject.bin` (`MACRO_NOT_ALLOWED`), firma `PK` obligatoria (`MIME_MISMATCH`).

## 3 · CSV (`cutover_template_{bu}_v2.csv`)

- Codificación UTF-8; BOM tolerado y emitido en la descarga.
- Delimitador detectado en la cabecera: `;` (preferido) o `,` (o tabulador). Decimales siempre con punto.
- Sin hojas: `business_unit`/`schema_id` vienen del batch y la versión del parámetro `?template_version=` del upload (por defecto `v2`); `Meta.company` no aplica.
- Fechas `AAAA-MM-DD`; `N/A`/`NA` literal para no aplica; celda vacía para desconocido.

## 4 · Un solo DTO

```text
{"source_type": "XLSX"|"CSV", "template_version": "v2", "business_unit", "schema_id", "company",
 "rows": [{"row_number", "raw": {col: str|null}, "normalized": {campo: {"value", "status"}}, "errors": [...]}]}
```

`XLSX_RESULT == CSV_RESULT` para cada BU (`test_paridad_xlsx_csv`, `test_red_04_csv_se_descarga_y_se_carga_como_xlsx`). La validación de dominio añade `_refs` (ids resueltos) y `_derived` (edad, huevos en proceso, día de incubación) al mismo diccionario normalizado antes del staging.

## 5 · Límites

| Límite | Valor | Error |
|---|---|---|
| Tamaño | 5 MB | `FILE_TOO_LARGE` |
| Filas de datos | 5000 | `TOO_MANY_ROWS` |
| Columnas | 60 | `TOO_MANY_COLUMNS` |
| Extensiones | `.xlsx`, `.csv` (`.xlsm` rechazado) | `UNSUPPORTED_EXTENSION` / `MACRO_NOT_ALLOWED` |

## 6 · Versionado

`v2` vigente · `v1 = RETIRED_WITH_CLEAR_ERROR` (Q6): un archivo v1 recibe `TEMPLATE_VERSION_UNSUPPORTED` con la indicación de descargar la plantilla v2; nunca se reinterpreta.

## 7 · Informe de errores

`GET /api/v1/cutover-batches/{id}/errors?format=csv|xlsx` (permiso `cutover:read`): columnas `row_number, field, error_code, message, received_value, column`; CSV `;` con BOM, XLSX hoja `Errores`.
