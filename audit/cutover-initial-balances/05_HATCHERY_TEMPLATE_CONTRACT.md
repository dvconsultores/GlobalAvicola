# CUTOVER-INITIAL-BALANCES · 05_HATCHERY_TEMPLATE_CONTRACT

Fecha: 2026-10-27 · SPEC 006 · `schema_id = CUTOVER_HATCHERY_V3` · versión `v3` · generado desde `backend/app/cutover/contracts.py`

| Dato | Valor |
|---|---|
| Unidad de negocio | `hatchery` (`lots.bird_type = hatchery`) |
| Fases compatibles | `INCUB` (implícita, no se declara en la plantilla) |
| Fecha que fija `lots.start_date` | `reception_date` |
| Columnas (`Datos`) | 20 |
| Obligatorias | `legacy_lot_code`, `hatchery_code`, `egg_origin`, `reception_date`, `eggs_received`, `eggs_set` |
| Archivo | `cutover_template_hatchery_v3.xlsx` (Instrucciones · Meta · Datos · Catalogos) · `cutover_template_hatchery_v3.csv` (solo cabecera, `;`) |
| Preview destacado | `legacy_lot_code`, `hatchery_code`, `incubator_name`, `set_date`, `eggs_received`, `eggs_set`, `eggs_transferred`, `eggs_discarded`, `chicks_hatched`, `chicks_available`, `expected_hatch_date` |

Semántica de celda: **vacío = UNKNOWN · `0` = KNOWN cero · `N/A` = NOT_APPLICABLE**. Fechas `AAAA-MM-DD`; pesos en gramos; alimento en kg.

## Campos

| Campo | Tipo | Unidad | Obligatorio | UNKNOWN (vacío) | N/A | Maestro | Valores | Significado | Destino |
|---|---|---|---|---|---|---|---|---|---|
| `legacy_lot_code` | text |  | sí | no | no |  |  | Código del proceso/lote de incubación en el sistema anterior. | `lots.legacy_lot_code`<br>`lots.lot_code`<br>`opening_balances.legacy_lot_code` |
| `existing_lot_code` | text |  | no | no | no | lot |  | Código de un lote de incubadora YA existente para reutilizar (sin eventos). | `lots.id` |
| `hatchery_code` | text |  | sí | no | no | hatchery |  | Código de la planta de incubación (Catalogos → hatchery). | `hatchery_openings.hatchery_id` |
| `incubator_name` | text |  | no | no | no | incubator |  | Nombre de la incubadora dentro de la planta (Catalogos → incubator, parent_code = planta). | `hatchery_openings.incubator_id` |
| `hatcher_name` | text |  | no | no | no | hatcher |  | Nombre de la nacedora dentro de la planta (Catalogos → hatcher). | `hatchery_openings.hatcher_id` |
| `source_lot_code` | text |  | no | no | no | source_lot |  | Código (actual o legado) del lote interno de reproductoras/progenitoras que originó los huevos. Con egg_origin=internal, si se indica debe existir y ser compatible (misma empresa y generación); con egg_origin=purchased NO se exige lote interno (la procedencia externa va en source_system/source_reference). | `hatchery_openings.source_lot_id`<br>`hatchery_openings.source_lot_reference` |
| `generation` | enum |  | no | no | no |  | grandparent, breeder | Generación del huevo incubado: grandparent (huevo de progenitoras → pollito reproductor) o breeder (→ pollito de engorde). | `lots.hatchery_purpose`<br>`hatchery_openings.generation` |
| `egg_origin` | enum |  | sí | no | no |  | internal, purchased | Origen comercial del huevo: internal (propio de Global Avícola) o purchased (comprado a un tercero). No es la generación biológica. | `hatchery_openings.egg_origin` |
| `reception_date` | date |  | sí | no | no |  |  | Fecha de recepción del huevo en la planta. ≤ corte. | `lots.start_date`<br>`hatchery_openings.reception_date`<br>`opening_balances.activation_date` |
| `set_date` | date |  | no | sí | sí |  |  | Fecha de carga en incubadora. Vacío = desconocida; N/A = aún no cargado. | `hatchery_openings.set_date` |
| `expected_hatch_date` | date |  | no | sí | sí |  |  | Fecha prevista de nacimiento. ≥ fecha de carga. | `hatchery_openings.expected_hatch_date` |
| `eggs_received` | int | huevos | sí | no | no |  |  | Huevos fértiles recibidos en la planta. | `hatchery_openings.eggs_received` |
| `eggs_set` | int | huevos | sí | no | no |  |  | Huevos ya cargados en incubadora. ≤ recibidos. | `hatchery_openings.eggs_set` |
| `eggs_transferred` | int | huevos | no | sí | sí |  |  | Huevos ya transferidos a nacedora. ≤ cargados. | `hatchery_openings.eggs_transferred` |
| `eggs_discarded` | int | huevos | no | sí | sí |  |  | Huevos descartados (ovoscopia, rotos) del proceso. ≤ cargados. | `hatchery_openings.eggs_discarded` |
| `chicks_hatched` | int | pollitos | no | sí | sí |  |  | Pollitos ya nacidos del proceso antes del corte. | `opening_balances.accumulated_chicks_hatched` |
| `chicks_available` | int | pollitos | no | sí | sí |  |  | Pollitos nacidos que siguen en planta sin despachar al corte. | `opening_balances.initial_mixed_count` |
| `source_system` | text |  | no | no | no |  |  | Sistema de origen del dato (p. ej. LEGACY, SAP, EXCEL). Vacío = el del batch. | `lots.source_system`<br>`opening_balances.source_system` |
| `source_reference` | text |  | no | no | no |  |  | Referencia en el sistema de origen (documento, planilla, lote). | `lots.source_reference`<br>`opening_balances.source_reference` |
| `notes` | text |  | no | no | no |  |  | Notas libres. Nunca sustituyen a un campo del contrato. | `cutover_items.opening_state.notes` |

## Reglas de consistencia y fechas

- `reception_date ≤ corte`; `reception_date ≤ set_date ≤ corte`; `expected_hatch_date ≥ set_date`.
- `eggs_set ≤ eggs_received`; `eggs_transferred ≤ eggs_set`; `eggs_discarded ≤ eggs_set`; `eggs_transferred + eggs_discarded ≤ eggs_set`.
- `chicks_hatched ≤ eggs_transferred` (o `≤ eggs_set` si transferidos no es KNOWN); `chicks_available ≤ chicks_hatched`.
- Derivados: `eggs_in_process = eggs_set − eggs_transferred − eggs_discarded` (solo KNOWN), `incubation_day = corte − set_date`.
- `source_lot_code` debe ser un lote grandparent/breeder de la empresa (código actual o legado) compatible con `generation`.
- Saldos tras el apply: huevo disponible en planta = `eggs_received − eggs_set` (+ recepciones − cargas post-corte); pollitos viables = `chicks_available` + nacimientos − salidas.
