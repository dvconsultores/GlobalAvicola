# CUTOVER-INITIAL-BALANCES · 09_VALIDATION_CATALOG

Fecha: 2026-10-15 · SPEC 006 · catálogo cerrado de errores (`parser.py`, `validation.py`, `service.py`, `operations/validators.py`)

Todo error de fila viaja como `{row_number, column, field, error_code, message, received_value}` (AC46) y se descarga en CSV/XLSX. Los errores de archivo/batch viajan como `detail = "CODE: mensaje"` con el HTTP indicado.

| Código | Ámbito | Cuándo |
|---|---|---|
| `INVALID_FILE` | archivo | Archivo vacío, corrupto o ilegible (XLSX que no abre, CSV con codificación no UTF-8 o bytes nulos). |
| `FILE_TOO_LARGE` | archivo | Supera 5 MB. |
| `TOO_MANY_ROWS` | archivo | Más de 5000 filas de datos. |
| `TOO_MANY_COLUMNS` | archivo | Más de 60 columnas en la cabecera. |
| `UNSUPPORTED_EXTENSION` | archivo | Extensión distinta de .xlsx / .csv. |
| `MIME_MISMATCH` | archivo | La extensión no coincide con el contenido (p. ej. .csv que es un ZIP, .xlsx que no es ZIP). |
| `MACRO_NOT_ALLOWED` | archivo | .xlsm o libro con `vbaProject.bin`: la plantilla es solo datos. |
| `FORMULA_NOT_ALLOWED` | archivo | Celda con fórmula en `Datos` (fila y columna en el mensaje); no se evalúa. |
| `SHEET_MISSING` | archivo | Falta la hoja `Meta` o `Datos`. |
| `TEMPLATE_VERSION_UNSUPPORTED` | archivo | Versión ≠ v2. `v1` está retirada: el mensaje indica descargar la plantilla v2. |
| `BUSINESS_UNIT_MISMATCH` | archivo | La plantilla (Meta.business_unit / schema_id) no es la de la BU del batch; también al pedir una plantilla con `batch_id` de otra BU. |
| `COMPANY_MISMATCH` | archivo | `Meta.company` no es la empresa efectiva (el Excel nunca cambia el tenant). |
| `HEADER_MISSING` | archivo | Faltan columnas del contrato (o no hay fila de cabecera). |
| `HEADER_DUPLICATE` | archivo | Columnas repetidas en la cabecera. |
| `HEADER_UNKNOWN` | archivo | Columnas que no pertenecen al contrato. |
| `NO_DATA_ROWS` | archivo | La plantilla no trae filas de datos (una plantilla vacía nunca queda VALIDATED). |
| `REQUIRED_FIELD_MISSING` | fila | Campo obligatorio vacío. |
| `NOT_APPLICABLE_ON_REQUIRED` | fila | N/A en un campo obligatorio (nunca se convierte en 0). |
| `NOT_APPLICABLE_NOT_ALLOWED` | fila | N/A en un campo que no lo admite. |
| `INVALID_INTEGER` | fila | Entero esperado: sin separador de miles ni decimales (`1.200`, `12.5`, texto, booleano). |
| `INVALID_NUMBER` | fila | Decimal esperado con punto; pesos > 0. |
| `NEGATIVE_VALUE` | fila | Valor negativo. |
| `INVALID_DATE` | fila | Fecha fuera de AAAA-MM-DD (`01/08/2026`). |
| `INVALID_ENUM` | fila | Valor fuera de la lista permitida (sex, generation). |
| `INVALID_TEXT_LENGTH` | fila | Texto más largo que el máximo del campo. |
| `MASTER_NOT_FOUND` | fila | Maestro inexistente, de otra empresa o que no coincide con el catálogo. |
| `MASTER_INACTIVE` | fila | Maestro inactivo para una referencia nueva (OD-21); la referencia histórica de un lote reutilizado se conserva. |
| `MASTER_AMBIGUOUS` | fila | Más de un maestro con ese código/nombre. |
| `PARENT_MISMATCH` | fila | Galpón de otra granja, incubadora/nacedora de otra planta, raza de otra línea o de otra BU, lote existente/fuente de otra BU o generación. |
| `PHASE_INCOMPATIBLE` | fila | Fase fuera de las permitidas por BU: {'grandparent': ('CRIA', 'PROD'), 'breeder': ('CRIA', 'PROD'), 'broiler': ('ENGORDE',), 'hatchery': ('INCUB',)}. |
| `METRIC_NOT_APPLICABLE_IN_PHASE` | fila | Métrica de producción con valor KNOWN en fase CRIA (use N/A o vacío). |
| `LOT_DUPLICATE` | fila | Código de lote repetido en el batch o ya usado por otra empresa. |
| `LOT_EXISTS_REUSE_REJECTED` | fila | El código ya existe en la empresa y la fila no declara `existing_lot_code`; o el lote existente ya tiene eventos. |
| `OPENING_ALREADY_EXISTS` | fila / apply | El lote ya tiene saldo de apertura. |
| `CONSISTENCY_MISMATCH` | fila | Ecuación de consistencia que no cuadra, evaluada solo con todas las piezas KNOWN (sin tolerancias). |
| `DATE_ORDER_INVALID` | fila | Inicio > corte; fase antes del lote o después del corte; carga antes de la recepción o después del corte; nacimiento previsto antes de la carga. |
| `DUPLICATE_UPLOAD` | batch (409) | Mismo checksum ya cargado en otro batch del mismo corte. |
| `BATCH_STATE_INVALID` | batch (409) | Transición fuera de la máquina de estados (recargar tras enviar, aplicar sin aprobar, doble apply…). |
| `BU_DISABLED` | apply (403) | La BU no está habilitada para la empresa (OD-16), incluso para un actor global. |
| `BU_NOT_GRANTED` | apply (403) | El actor no tiene concedida la BU del batch. |
| `SEGREGATION_VIOLATION` | approve/reject (403) | El creador no aprueba ni rechaza su propio batch. |
| `PHASE_REQUIRED` | apply (422) | No existe la fase productiva activa para anclar el opening (INCUB implícita en incubadora). |
| `APPLY_FAILED` | apply (422) | Fallo inesperado: rollback total + rastro `FAILED_APPLY`. |
| `CUT-GL-02` | operaciones (400) | Evento con fecha ≤ fecha civil del corte en un lote con saldo de apertura por cutover. |

## Orden de evaluación

1. Archivo: extensión → tamaño → contenido (MIME/corrupción/macros) → hojas → versión → BU/schema → cabecera → filas (fórmulas, límites) → `NO_DATA_ROWS`.
2. Fila (estructural, por campo): vacío/N/A según obligatoriedad → tipo → signo/rango → enum/longitud.
3. Fila (dominio, solo sobre valores KNOWN): lote existente → código legado (duplicado / existente) → maestros y relaciones → fase/BU → fechas → consistencia → derivados.
4. Batch: `DUPLICATE_UPLOAD`, `BATCH_STATE_INVALID`, segregación, OD-16 (`BU_DISABLED`, `BU_NOT_GRANTED`), guardas defensivas del apply.
5. Motor: `CUT-GL-02` en `validate_event_date` para todo evento de un lote con apertura por cutover.
