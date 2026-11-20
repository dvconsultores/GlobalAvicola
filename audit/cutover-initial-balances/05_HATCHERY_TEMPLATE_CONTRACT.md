# CUTOVER-INITIAL-BALANCES · 05_HATCHERY_TEMPLATE_CONTRACT

Fecha: 2026-11-20 · SPEC 006 · `schema_id = CUTOVER_HATCHERY_V4` · versión `v4` · generado desde `backend/app/cutover/contracts.py`

| Dato | Valor |
|---|---|
| Unidad de negocio | `hatchery` (`lots.bird_type = hatchery`) |
| Fases compatibles | `INCUB` (implícita, no se declara en la plantilla) |
| Fecha que fija `lots.start_date` | `reception_date` |
| Columnas (`Datos`) | 23 |
| Obligatorias | `legacy_lot_code`, `hatchery_code`, `egg_origin`, `reception_date`, `eggs_received`, `eggs_set` |
| Archivo | `cutover_template_hatchery_v4.xlsx` (Instrucciones · Meta · Datos · Catalogos) · `cutover_template_hatchery_v4.csv` (solo cabecera, `;`) |
| Preview destacado | `legacy_lot_code`, `hatchery_code`, `incubator_name`, `set_date`, `eggs_received`, `eggs_set`, `eggs_non_incubable_oversized`, `eggs_non_incubable_dirty`, `eggs_non_incubable_broken`, `eggs_transferred`, `fertile_eggs_to_pit`, `chicks_hatched`, `chicks_available`, `expected_hatch_date` |

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
| `eggs_non_incubable_oversized` | int | huevos | no | sí | no |  |  | Cantidad acumulada de huevos recibidos clasificados como no incubables por tamaño excesivo (extra grande), hasta la fecha de corte. Vacío = desconocido; 0 = cero conocido. | `hatchery_openings.eggs_non_incubable_oversized` |
| `eggs_non_incubable_dirty` | int | huevos | no | sí | no |  |  | Cantidad acumulada de huevos recibidos clasificados como no incubables por suciedad, hasta la fecha de corte. Vacío = desconocido; 0 = cero conocido. | `hatchery_openings.eggs_non_incubable_dirty` |
| `eggs_non_incubable_broken` | int | huevos | no | sí | no |  |  | Cantidad acumulada de huevos recibidos clasificados como no incubables por rotura, hasta la fecha de corte. Vacío = desconocido; 0 = cero conocido. | `hatchery_openings.eggs_non_incubable_broken` |
| `eggs_transferred` | int | huevos | no | sí | sí |  |  | Huevos ya transferidos a nacedora. ≤ cargados. | `hatchery_openings.eggs_transferred` |
| `fertile_eggs_to_pit` | int | huevos | no | sí | no |  |  | Cantidad acumulada de huevos fértiles enviados a fosa antes de la fecha de corte. Concepto separado de los no incubables. Vacío = desconocido; 0 = cero conocido. | `hatchery_openings.fertile_eggs_to_pit` |
| `chicks_hatched` | int | pollitos | no | sí | sí |  |  | Pollitos ya nacidos del proceso antes del corte. | `opening_balances.accumulated_chicks_hatched` |
| `chicks_available` | int | pollitos | no | sí | sí |  |  | Pollitos nacidos que siguen en planta sin despachar al corte. | `opening_balances.initial_mixed_count` |
| `source_system` | text |  | no | no | no |  |  | Sistema de origen del dato (p. ej. LEGACY, SAP, EXCEL). Vacío = el del batch. | `lots.source_system`<br>`opening_balances.source_system` |
| `source_reference` | text |  | no | no | no |  |  | Referencia en el sistema de origen (documento, planilla, lote). | `lots.source_reference`<br>`opening_balances.source_reference` |
| `notes` | text |  | no | no | no |  |  | Notas libres. Nunca sustituyen a un campo del contrato. | `cutover_items.opening_state.notes` |

## Reglas de consistencia y fechas

- `reception_date ≤ corte`; `reception_date ≤ set_date ≤ corte`; `expected_hatch_date ≥ set_date`.
- `eggs_set ≤ eggs_received`; `eggs_transferred ≤ eggs_set`.
- No incubables (SPEC 018, V4): cada componente KNOWN (`eggs_non_incubable_oversized`, `eggs_non_incubable_dirty`, `eggs_non_incubable_broken`) `≤ eggs_received`, y `eggs_set + Σ(no incubables KNOWN) ≤ eggs_received`. **Sin igualdad**: la suma conocida es cota inferior porque `eggs_received` puede incluir huevo aún no cargado.
- `fertile_eggs_to_pit ≤ eggs_received`. Su relación con `eggs_set`/`eggs_transferred` (resta en `eggs_in_process`, ecuación `transferred + fosa ≤ set`) queda pendiente de decisión de dominio: `OWNER_DOMAIN_DECISION_REQUIRED` · `OD-HATCH-V4-01`.
- `chicks_hatched ≤ eggs_transferred` (o `≤ eggs_set` si transferidos no es KNOWN); `chicks_available ≤ chicks_hatched`.
- Derivados: `eggs_non_incubable_total = oversized + dirty + broken` solo si los tres son KNOWN (si falta alguno, UNKNOWN: nunca suma parcial); `eggs_in_process = eggs_set − eggs_transferred` solo si `eggs_set` y `eggs_transferred` son KNOWN y `fertile_eggs_to_pit` es KNOWN `= 0` (en otro caso, desconocido); `incubation_day = corte − set_date`.
- `source_lot_code` debe ser un lote grandparent/breeder de la empresa (código actual o legado) compatible con `generation`.
- Saldos tras el apply: huevo por cargar = `eggs_received − eggs_set − Σ(no incubables KNOWN)` (un UNKNOWN no se resta: el saldo es entonces cota superior); huevo disponible en planta = ese saldo (+ recepciones − cargas post-corte); pollitos viables = `chicks_available` + nacimientos − salidas.
