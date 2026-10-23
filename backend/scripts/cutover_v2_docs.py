"""SPEC 006 · genera la documentación del contrato v2 desde el registry (`app/cutover/contracts.py`).

    uso:  .venv/bin/python scripts/cutover_v2_docs.py [directorio_de_salida]

Escribe `03…06_<BU>_TEMPLATE_CONTRACT.md`, `07_DATA_LINEAGE_MATRIX.md`, `08_XLSX_CSV_CONTRACT.md`,
`09_VALIDATION_CATALOG.md` y `10_APPLY_DESTINATION_MATRIX.md`. La fuente de verdad es el código:
estos documentos no se editan a mano.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cutover.contracts import CONTRACTS, FASES_POR_BU, TemplateContract, lineage  # noqa: E402
from app.cutover.parser import LIMITE_BYTES, LIMITE_COLUMNAS, LIMITE_FILAS  # noqa: E402
from app.cutover.service import PREVIEW_DESTACADAS  # noqa: E402

HOY = date.today().isoformat()
ORDEN = (("grandparent", "03"), ("breeder", "04"), ("hatchery", "05"), ("broiler", "06"))

CATALOGO_ERRORES = [
    ("INVALID_FILE", "archivo", "Archivo vacío, corrupto o ilegible (XLSX que no abre, CSV con codificación no UTF-8 o bytes nulos)."),
    ("FILE_TOO_LARGE", "archivo", f"Supera {LIMITE_BYTES // (1024 * 1024)} MB."),
    ("TOO_MANY_ROWS", "archivo", f"Más de {LIMITE_FILAS} filas de datos."),
    ("TOO_MANY_COLUMNS", "archivo", f"Más de {LIMITE_COLUMNAS} columnas en la cabecera."),
    ("UNSUPPORTED_EXTENSION", "archivo", "Extensión distinta de .xlsx / .csv."),
    ("MIME_MISMATCH", "archivo", "La extensión no coincide con el contenido (p. ej. .csv que es un ZIP, .xlsx que no es ZIP)."),
    ("MACRO_NOT_ALLOWED", "archivo", ".xlsm o libro con `vbaProject.bin`: la plantilla es solo datos."),
    ("FORMULA_NOT_ALLOWED", "archivo", "Celda con fórmula en `Datos` (fila y columna en el mensaje); no se evalúa."),
    ("SHEET_MISSING", "archivo", "Falta la hoja `Meta` o `Datos`."),
    ("TEMPLATE_VERSION_UNSUPPORTED", "archivo", "Versión ≠ v2. `v1` está retirada: el mensaje indica descargar la plantilla v2."),
    ("BUSINESS_UNIT_MISMATCH", "archivo", "La plantilla (Meta.business_unit / schema_id) no es la de la BU del batch; también al pedir una plantilla con `batch_id` de otra BU."),
    ("COMPANY_MISMATCH", "archivo", "`Meta.company` no es la empresa efectiva (el Excel nunca cambia el tenant)."),
    ("HEADER_MISSING", "archivo", "Faltan columnas del contrato (o no hay fila de cabecera)."),
    ("HEADER_DUPLICATE", "archivo", "Columnas repetidas en la cabecera."),
    ("HEADER_UNKNOWN", "archivo", "Columnas que no pertenecen al contrato."),
    ("NO_DATA_ROWS", "archivo", "La plantilla no trae filas de datos (una plantilla vacía nunca queda VALIDATED)."),
    ("REQUIRED_FIELD_MISSING", "fila", "Campo obligatorio vacío."),
    ("NOT_APPLICABLE_ON_REQUIRED", "fila", "N/A en un campo obligatorio (nunca se convierte en 0)."),
    ("NOT_APPLICABLE_NOT_ALLOWED", "fila", "N/A en un campo que no lo admite."),
    ("INVALID_INTEGER", "fila", "Entero esperado: sin separador de miles ni decimales (`1.200`, `12.5`, texto, booleano)."),
    ("INVALID_NUMBER", "fila", "Decimal esperado con punto; pesos > 0."),
    ("NEGATIVE_VALUE", "fila", "Valor negativo."),
    ("INVALID_DATE", "fila", "Fecha fuera de AAAA-MM-DD (`01/08/2026`)."),
    ("INVALID_ENUM", "fila", "Valor fuera de la lista permitida (sex, generation)."),
    ("INVALID_TEXT_LENGTH", "fila", "Texto más largo que el máximo del campo."),
    ("MASTER_NOT_FOUND", "fila", "Maestro inexistente, de otra empresa o que no coincide con el catálogo."),
    ("MASTER_INACTIVE", "fila", "Maestro inactivo para una referencia nueva (OD-21); la referencia histórica de un lote reutilizado se conserva."),
    ("MASTER_AMBIGUOUS", "fila", "Más de un maestro con ese código/nombre."),
    ("PARENT_MISMATCH", "fila", "Galpón de otra granja, incubadora/nacedora de otra planta, raza de otra línea o de otra BU, lote existente/fuente de otra BU o generación."),
    ("GENETIC_LINE_NOT_FOUND", "fila", "Línea genética inexistente, de otra empresa o inactiva (maestro interno de Global Avícola, no SAP)."),
    ("BREED_NOT_FOUND", "fila", "Raza inexistente en la empresa (maestro interno de Global Avícola, no SAP)."),
    ("BREED_NOT_IN_GENETIC_LINE", "fila", "La raza existe pero no pertenece a la línea genética indicada."),
    ("PHASE_INCOMPATIBLE", "fila", f"Fase fuera de las permitidas por BU: {dict(FASES_POR_BU)}."),
    ("METRIC_NOT_APPLICABLE_IN_PHASE", "fila", "Métrica de producción con valor KNOWN en fase CRIA (use N/A o vacío)."),
    ("LOT_DUPLICATE", "fila", "Código de lote repetido en el batch o ya usado por otra empresa."),
    ("LOT_EXISTS_REUSE_REJECTED", "fila", "El código ya existe en la empresa y la fila no declara `existing_lot_code`; o el lote existente ya tiene eventos."),
    ("OPENING_ALREADY_EXISTS", "fila / apply", "El lote ya tiene saldo de apertura."),
    ("CONSISTENCY_MISMATCH", "fila", "Ecuación de consistencia que no cuadra, evaluada solo con todas las piezas KNOWN (sin tolerancias)."),
    ("DATE_ORDER_INVALID", "fila", "Inicio > corte; fase antes del lote o después del corte; carga antes de la recepción o después del corte; nacimiento previsto antes de la carga."),
    ("DUPLICATE_UPLOAD", "batch (409)", "Mismo checksum ya cargado en otro batch del mismo corte."),
    ("BATCH_STATE_INVALID", "batch (409)", "Transición fuera de la máquina de estados (recargar tras enviar, aplicar sin aprobar, doble apply…)."),
    ("BU_DISABLED", "apply (403)", "La BU no está habilitada para la empresa (OD-16), incluso para un actor global."),
    ("BU_NOT_GRANTED", "apply (403)", "El actor no tiene concedida la BU del batch."),
    ("SEGREGATION_VIOLATION", "approve/reject (403)", "El creador no aprueba ni rechaza su propio batch."),
    ("PHASE_REQUIRED", "apply (422)", "No existe la fase productiva activa para anclar el opening (INCUB implícita en incubadora)."),
    ("APPLY_FAILED", "apply (422)", "Fallo inesperado: rollback total + rastro `FAILED_APPLY`."),
    ("CUT-GL-02", "operaciones (400)", "Evento con fecha ≤ fecha civil del corte en un lote con saldo de apertura por cutover."),
]


def _si(v: bool) -> str:
    return "sí" if v else "no"


def contrato_md(bu: str, numero: str, c: TemplateContract) -> str:
    filas = []
    for f in c.fields:
        filas.append(f"| `{f.name}` | {f.kind} | {f.unit or ''} | {_si(f.required)} | {_si(f.allow_unknown)} | {_si(f.allow_na)} | "
                     f"{f.master or ''} | {', '.join(f.values)} | {f.meaning} | {'<br>'.join(f'`{t}`' for t in f.targets)} |")
    destacadas = ", ".join(f"`{x}`" for x in PREVIEW_DESTACADAS[bu])
    return f"""# CUTOVER-INITIAL-BALANCES · {numero}_{bu.upper()}_TEMPLATE_CONTRACT

Fecha: {HOY} · SPEC 006 · `schema_id = {c.schema_id}` · versión `{c.version}` · generado desde `backend/app/cutover/contracts.py`

| Dato | Valor |
|---|---|
| Unidad de negocio | `{bu}` (`lots.bird_type = {c.bird_type}`) |
| Fases compatibles | {', '.join(f'`{p}`' for p in c.phases)}{' (implícita, no se declara en la plantilla)' if c.implicit_phase else ''} |
| Fecha que fija `lots.start_date` | `{c.lot_date_field}` |
| Columnas (`Datos`) | {len(c.fields)} |
| Obligatorias | {', '.join(f'`{x}`' for x in c.required_fields)} |
| Archivo | `{c.filename_stem}.xlsx` (Instrucciones · Meta · Datos · Catalogos) · `{c.filename_stem}.csv` (solo cabecera, `;`) |
| Preview destacado | {destacadas} |

Semántica de celda: **vacío = UNKNOWN · `0` = KNOWN cero · `N/A` = NOT_APPLICABLE**. Fechas `AAAA-MM-DD`; pesos en gramos; alimento en kg.

## Campos

| Campo | Tipo | Unidad | Obligatorio | UNKNOWN (vacío) | N/A | Maestro | Valores | Significado | Destino |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(filas)}

## Reglas de consistencia y fechas

{REGLAS[bu]}
"""


REGLAS = {
    "grandparent": """- `real_start_date ≤ corte`; `real_start_date ≤ phase_start_date ≤ corte`.
- Por sexo, solo si alojadas, mortalidad, descartes y vivas son KNOWN: `alojadas − mortalidad − descartes = vivas`.
- `accumulated_eggs_to_hatchery ≤ accumulated_egg_production` si ambas KNOWN.
- En `CRIA`, `accumulated_egg_production` y `accumulated_eggs_to_hatchery` deben ser N/A o vacío (`METRIC_NOT_APPLICABLE_IN_PHASE`).
- Estado de una métrica con dos sexos: KNOWN solo si ambos lo son; N/A si ambos; si no, UNKNOWN.""",
    "hatchery": """- `reception_date ≤ corte`; `reception_date ≤ set_date ≤ corte`; `expected_hatch_date ≥ set_date`.
- `eggs_set ≤ eggs_received`; `eggs_transferred ≤ eggs_set`; `eggs_discarded ≤ eggs_set`; `eggs_transferred + eggs_discarded ≤ eggs_set`.
- `chicks_hatched ≤ eggs_transferred` (o `≤ eggs_set` si transferidos no es KNOWN); `chicks_available ≤ chicks_hatched`.
- Derivados: `eggs_in_process = eggs_set − eggs_transferred − eggs_discarded` (solo KNOWN), `incubation_day = corte − set_date`.
- `source_lot_code` debe ser un lote grandparent/breeder de la empresa (código actual o legado) compatible con `generation`.
- Saldos tras el apply: huevo disponible en planta = `eggs_received − eggs_set` (+ recepciones − cargas post-corte); pollitos viables = `chicks_available` + nacimientos − salidas.""",
    "broiler": """- `real_start_date ≤ corte`; fase obligatoriamente `ENGORDE`.
- Solo si las cinco piezas son KNOWN: `accumulated_birds_received − historical_mortality − historical_culls − partial_outbound_birds = live_birds`.
- `age_days` vacío ⇒ se deriva de `real_start_date` (edad = corte − inicio) con estado KNOWN; declarado ⇒ se respeta.
- `sex` vacío ⇒ `mixed`.""",
}
REGLAS["breeder"] = REGLAS["grandparent"] + "\n- Un lote en producción (`PROD`) declara sus métricas de huevo; uno en cría (`CRIA`) las marca N/A."


def lineage_md() -> str:
    m = lineage()
    cab = ["BU", "TEMPLATE_FIELD", "BUSINESS_MEANING", "TYPE", "UNIT", "REQUIRED", "ALLOW_UNKNOWN", "ALLOW_NA", "VALIDATION",
           "MASTER_REFERENCE", "NORMALIZED_FIELD", "STAGING_FIELD", "TARGET_ENTITY", "TARGET_COLUMN", "PROMOTION_RULE",
           "FIRST_OPERATION_CONSUMER"]
    filas = []
    for r in m["rows"]:
        filas.append("| " + " | ".join(str(r[c]).replace("|", "\\|") for c in cab) + " |")
    return f"""# CUTOVER-INITIAL-BALANCES · 07_DATA_LINEAGE_MATRIX

Fecha: {HOY} · SPEC 006 · generado desde `backend/app/cutover/contracts.py` (`lineage()`); verificado por `test_red_08_registry_cerrado_sin_campos_sin_destino` y `test_lineage_sin_campos_sin_destino_ni_dominio_faltante`.

```text
UNMAPPED_TEMPLATE_FIELDS                    = {m["UNMAPPED_TEMPLATE_FIELDS"]}
REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE = {m["REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE"]}
FILAS                                        = {len(m["rows"])} (grandparent {len(CONTRACTS['grandparent'].fields)} · breeder {len(CONTRACTS['breeder'].fields)} · hatchery {len(CONTRACTS['hatchery'].fields)} · broiler {len(CONTRACTS['broiler'].fields)})
```

Recorrido de cada campo: `SOURCE FILE FIELD → RAW (cutover_staging_rows.raw) → NORMALIZED ({{value, status}}) → STAGING (cutover_staging_rows.normalized / cutover_items.opening_state) → DOMAIN ENTITY → DOMAIN FIELD`.

| {" | ".join(cab)} |
|{"---|" * len(cab)}
{chr(10).join(filas)}
"""


def xlsx_csv_md() -> str:
    return f"""# CUTOVER-INITIAL-BALANCES · 08_XLSX_CSV_CONTRACT

Fecha: {HOY} · SPEC 006 · parser: `backend/app/cutover/parser.py` · plantillas: `backend/app/cutover/templates.py`

## 1 · Descarga

`GET /api/v1/cutover-templates/{{bu}}?format=xlsx|csv&batch_id=` (permiso `cutover:create`). Con `batch_id`, el batch debe ser de la empresa efectiva **y de esa BU** (`BUSINESS_UNIT_MISMATCH` en caso contrario): la plantilla sigue al batch, nunca a un selector. `Meta.cutover_datetime` viaja rellena.

## 2 · XLSX (`cutover_template_{{bu}}_v2.xlsx`)

| Hoja | Contenido |
|---|---|
| `Instrucciones` | semántica vacío/0/N/A, formatos, unidades y una fila por campo: campo, significado, obligatorio, tipo, unidad, formato, ejemplo, valores permitidos, admite UNKNOWN, admite N/A, destino tras apply |
| `Meta` | `template_version = v2`, `schema_id`, `company` (empresa efectiva), `business_unit`, `generated_at`, `cutover_datetime` |
| `Datos` | cabecera exacta del contrato (orden libre al subir; nombres exactos) |
| `Catalogos` | `catalog, code, description, status, parent_code` — solo maestros **activos** de la empresa efectiva y de la BU (granjas/galpones(parent=granja)/áreas/fases/líneas/razas(parent=línea) · plantas/incubadoras/nacedoras(parent=planta)/lotes fuente · lotes existentes sin apertura) |

Lectura: `openpyxl` con `data_only=False` para detectar fórmulas (`FORMULA_NOT_ALLOWED`), rechazo de `vbaProject.bin` (`MACRO_NOT_ALLOWED`), firma `PK` obligatoria (`MIME_MISMATCH`).

## 3 · CSV (`cutover_template_{{bu}}_v2.csv`)

- Codificación UTF-8; BOM tolerado y emitido en la descarga.
- Delimitador detectado en la cabecera: `;` (preferido) o `,` (o tabulador). Decimales siempre con punto.
- Sin hojas: `business_unit`/`schema_id` vienen del batch y la versión del parámetro `?template_version=` del upload (por defecto `v2`); `Meta.company` no aplica.
- Fechas `AAAA-MM-DD`; `N/A`/`NA` literal para no aplica; celda vacía para desconocido.

## 4 · Un solo DTO

```text
{{"source_type": "XLSX"|"CSV", "template_version": "v2", "business_unit", "schema_id", "company",
 "rows": [{{"row_number", "raw": {{col: str|null}}, "normalized": {{campo: {{"value", "status"}}}}, "errors": [...]}}]}}
```

`XLSX_RESULT == CSV_RESULT` para cada BU (`test_paridad_xlsx_csv`, `test_red_04_csv_se_descarga_y_se_carga_como_xlsx`). La validación de dominio añade `_refs` (ids resueltos) y `_derived` (edad, huevos en proceso, día de incubación) al mismo diccionario normalizado antes del staging.

## 5 · Límites

| Límite | Valor | Error |
|---|---|---|
| Tamaño | {LIMITE_BYTES // (1024 * 1024)} MB | `FILE_TOO_LARGE` |
| Filas de datos | {LIMITE_FILAS} | `TOO_MANY_ROWS` |
| Columnas | {LIMITE_COLUMNAS} | `TOO_MANY_COLUMNS` |
| Extensiones | `.xlsx`, `.csv` (`.xlsm` rechazado) | `UNSUPPORTED_EXTENSION` / `MACRO_NOT_ALLOWED` |

## 6 · Versionado

`v2` vigente · `v1 = RETIRED_WITH_CLEAR_ERROR` (Q6): un archivo v1 recibe `TEMPLATE_VERSION_UNSUPPORTED` con la indicación de descargar la plantilla v2; nunca se reinterpreta.

## 7 · Informe de errores

`GET /api/v1/cutover-batches/{{id}}/errors?format=csv|xlsx` (permiso `cutover:read`): columnas `row_number, field, error_code, message, received_value, column`; CSV `;` con BOM, XLSX hoja `Errores`.
"""


def catalogo_md() -> str:
    filas = "\n".join(f"| `{c}` | {ambito} | {d} |" for c, ambito, d in CATALOGO_ERRORES)
    return f"""# CUTOVER-INITIAL-BALANCES · 09_VALIDATION_CATALOG

Fecha: {HOY} · SPEC 006 · catálogo cerrado de errores (`parser.py`, `validation.py`, `service.py`, `operations/validators.py`)

Todo error de fila viaja como `{{row_number, column, field, error_code, message, received_value}}` (AC46) y se descarga en CSV/XLSX. Los errores de archivo/batch viajan como `detail = "CODE: mensaje"` con el HTTP indicado.

| Código | Ámbito | Cuándo |
|---|---|---|
{filas}

## Orden de evaluación

1. Archivo: extensión → tamaño → contenido (MIME/corrupción/macros) → hojas → versión → BU/schema → cabecera → filas (fórmulas, límites) → `NO_DATA_ROWS`.
2. Fila (estructural, por campo): vacío/N/A según obligatoriedad → tipo → signo/rango → enum/longitud.
3. Fila (dominio, solo sobre valores KNOWN): lote existente → código legado (duplicado / existente) → maestros y relaciones → fase/BU → fechas → consistencia → derivados.
4. Batch: `DUPLICATE_UPLOAD`, `BATCH_STATE_INVALID`, segregación, OD-16 (`BU_DISABLED`, `BU_NOT_GRANTED`), guardas defensivas del apply.
5. Motor: `CUT-GL-02` en `validate_event_date` para todo evento de un lote con apertura por cutover.
"""


def destino_md() -> str:
    bloques = []
    for bu, c in CONTRACTS.items():
        por_entidad: dict[str, list[str]] = {}
        for f in c.fields:
            for t in f.targets:
                ent, _, col = t.partition(".")
                por_entidad.setdefault(ent, []).append(f"`{col}` ← `{f.name}`" + (f" (+`{f.status_column}`)" if f.status_column else ""))
        filas = "\n".join(f"| `{ent}` | {'<br>'.join(cols)} |" for ent, cols in por_entidad.items())
        bloques.append(f"### `{bu}` · `{c.schema_id}`\n\n| Entidad | Columnas ← campo de plantilla |\n|---|---|\n{filas}\n")
    return f"""# CUTOVER-INITIAL-BALANCES · 10_APPLY_DESTINATION_MATRIX

Fecha: {HOY} · SPEC 006 · generado desde `backend/app/cutover/contracts.py`; el apply vive en `CutoverService.aplicar` (`service.py`) con un builder por BU (`_opening_reproductoras`, `_opening_engorde`, `_opening_incubadora` + `_hatchery_opening`, `_lote`, `_lot_phase`).

## Constantes del apply (todas las BU)

| Entidad | Columna | Valor |
|---|---|---|
| `lots` | `origin` | `MIGRATED` (lote nuevo) · se conserva `NATIVE` si se reutiliza (`existing_lot_code`) |
| `lots` | `bird_type` | BU del batch |
| `lots` | `status` / `activation_type` | `active` / `normal` (BR-06 sigue aplicando) |
| `lots` | `source_system` | fila → batch.source_system → tipo de archivo (`XLSX`/`CSV`) |
| `opening_balances` | `activation_date` | fecha civil del corte |
| `opening_balances` | `cutover_datetime` / `cutover_item_id` / `template_version` | corte del batch / fila de staging / `v2` |
| `opening_balances` | `is_manual_activation` / `activation_reason` | `false` / «Cutover operacional v2 (SPEC 006)» |
| `opening_balances` | estados no cubiertos por la BU | `NOT_APPLICABLE` (p. ej. huevos en engorde, mortalidad en incubadora) |
| `lot_phases` | `phase_id` / `start_date` / `start_population_*` / `start_weight_avg` / `is_active` | fase declarada (INCUB implícita) / `phase_start_date` → fecha del lote / vivas por sexo (0 en mixto) / peso de apertura / `true` |

## Destino por campo

{chr(10).join(bloques)}
## Garantías

- Atómico: una fila que falla (`LOT_DUPLICATE`, `OPENING_ALREADY_EXISTS`, `PHASE_REQUIRED`, `MASTER_NOT_FOUND`) ⇒ rollback total + `FAILED_APPLY` auditado; el batch sigue `APPROVED`.
- Idempotente: `APPLIED` es terminal (doble apply ⇒ 409).
- Los valores UNKNOWN se guardan como `NULL` (columnas nulables) o `0` **acompañados del estado** en las columnas NOT NULL heredadas (`accumulated_mortality_*`, `accumulated_culls_*`); la lectura siempre consulta el estado.
"""


def main(salida: Path) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    for bu, numero in ORDEN:
        (salida / f"{numero}_{bu.upper()}_TEMPLATE_CONTRACT.md").write_text(contrato_md(bu, numero, CONTRACTS[bu]), encoding="utf-8")
    (salida / "07_DATA_LINEAGE_MATRIX.md").write_text(lineage_md(), encoding="utf-8")
    (salida / "08_XLSX_CSV_CONTRACT.md").write_text(xlsx_csv_md(), encoding="utf-8")
    (salida / "09_VALIDATION_CATALOG.md").write_text(catalogo_md(), encoding="utf-8")
    (salida / "10_APPLY_DESTINATION_MATRIX.md").write_text(destino_md(), encoding="utf-8")
    m = lineage()
    print(f"docs generados en {salida} · UNMAPPED_TEMPLATE_FIELDS={m['UNMAPPED_TEMPLATE_FIELDS']} "
          f"REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE={m['REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE']}")


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "audit" / "cutover-initial-balances"
    main(destino)
