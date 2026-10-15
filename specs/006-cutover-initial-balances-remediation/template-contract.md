# Template Contract — SPEC 006 (v2, por unidad de negocio)

**Fuente de verdad en código**: `backend/app/cutover/contracts.py` (registry cerrado). Este documento fija el contrato; `audit/cutover-initial-balances/03…06` se generan desde el código.

Semántica universal de cada celda de métrica: **vacío = UNKNOWN · `0` = KNOWN cero · `N/A` = NOT_APPLICABLE**. Fechas `AAAA-MM-DD`. Decimales con punto. Pesos en **gramos** (unidad canónica del sistema). Referencias por código/nombre, resueltas en la empresa efectiva.

Columnas comunes a los lotes de aves (grandparent · breeder · broiler):

| Campo | Tipo | Req. | UNKNOWN | N/A | Referencia / regla | Destino |
|---|---|---|---|---|---|---|
| `legacy_lot_code` | texto ≤60 | sí | no | no | único en el batch y en la empresa | `lots.legacy_lot_code`, `lots.lot_code` (si no hay `existing_lot_code`), `opening_balances.legacy_lot_code` |
| `existing_lot_code` | texto | no | — | — | lote GA existente, misma empresa, `ACTIVE`, mismo `bird_type`, sin eventos | REUSE del `Lot` |
| `farm_code` | texto | sí | no | no | `farms.code` de la empresa, activa | `lots.farm_id` |
| `house_name` | texto | no | — | — | `houses.name` dentro de la granja, activo, único | `lots.house_id` |
| `area_code` | texto | no | — | — | `areas.code` de la empresa | `lots.area_id` |
| `productive_phase_code` | texto | sí | no | no | `productive_phases.code` compatible con la BU | `lot_phases.phase_id`, `opening_balances.phase_at_activation_id` |
| `real_start_date` | fecha | sí | no | no | ≤ fecha del corte | `lots.start_date`, `opening_balances.age_days` |
| `phase_start_date` | fecha | no | sí | no | `real_start_date ≤ phase_start_date ≤ corte` | `lot_phases.start_date` (si falta: `real_start_date`) |
| `genetic_line_code` | texto | no | — | — | `genetic_lines.code` (empresa o global) | `lots.genetic_line_id` |
| `breed_name` | texto | no | — | — | `breeds.name` de la línea genética y del `bird_type` | `lots.breed_id` |
| `sex` | `male\|female\|mixed` | no | — | — | | `lots.sex` |
| `source_system` | texto | no | — | — | | `lots.source_system`, `opening_balances.source_system` |
| `source_reference` | texto | no | — | — | | `lots.source_reference`, `opening_balances.source_reference` |
| `notes` | texto | no | — | — | | `cutover_items.opening_state.notes` |

## CUTOVER_GRANDPARENT_V2 y CUTOVER_BREEDER_V2 (mismo contrato; fases `CRIA` o `PROD`)

| Campo | Tipo | Req. | UNKNOWN | N/A | Regla | Destino |
|---|---|---|---|---|---|---|
| `live_males` | entero ≥0 | sí (KNOWN) | no | no | | `initial_male_count` |
| `live_females` | entero ≥0 | sí (KNOWN) | no | no | | `initial_female_count` |
| `birds_placed_males` | entero | no | sí | no | consistencia por sexo si todo KNOWN: `placed − mortality − culls = live` | `opening_balances.placed_male_count` (+`placed_status`) |
| `birds_placed_females` | entero | no | sí | no | ídem | `placed_female_count` |
| `historical_mortality_males` | entero | no | sí | no | | `accumulated_mortality_male` (+`mortality_status`) |
| `historical_mortality_females` | entero | no | sí | no | | `accumulated_mortality_female` |
| `historical_culls_males` | entero | no | sí | no | | `accumulated_culls_male` (+`culls_status`) |
| `historical_culls_females` | entero | no | sí | no | | `accumulated_culls_female` |
| `accumulated_feed_kg` | decimal ≥0 | no | sí | no | | `accumulated_feed_kg` (+`feed_status`) |
| `current_avg_weight_g` | decimal >0 | no | sí | no | gramos | `current_avg_weight` (+`weight_status`) |
| `accumulated_egg_production` | entero | no | sí | sí | en `CRIA` debe ser N/A o vacío (`METRIC_NOT_APPLICABLE_IN_PHASE`) | `accumulated_egg_production` (+`egg_production_status`) |
| `accumulated_eggs_to_hatchery` | entero | no | sí | sí | ídem; ≤ producción si ambas KNOWN | `accumulated_eggs_to_hatchery` (+`eggs_to_hatchery_status`) |

Estado de una métrica con dos sexos: KNOWN solo si ambos son KNOWN; N/A si ambos N/A; en otro caso UNKNOWN (sin inventar el sexo que falta).

## CUTOVER_BROILER_V2 (fase `ENGORDE`; `sex` por defecto `mixed`)

| Campo | Tipo | Req. | UNKNOWN | N/A | Regla | Destino |
|---|---|---|---|---|---|---|
| `live_birds` | entero ≥0 | sí (KNOWN) | no | no | | `initial_mixed_count` |
| `age_days` | entero | no | sí | no | si falta se deriva de `real_start_date` | `opening_balances.age_days` |
| `accumulated_birds_received` | entero | no | sí | no | | `accumulated_broiler_received` (+`broiler_received_status`) |
| `historical_mortality` | entero | no | sí | no | | `accumulated_mortality_mixed` (+`mortality_status`) |
| `historical_culls` | entero | no | sí | no | | `accumulated_culls_mixed` (+`culls_status`) |
| `partial_outbound_birds` | entero | no | sí | sí | | `accumulated_outbound_birds` (+`outbound_status`) |
| `accumulated_feed_kg` | decimal | no | sí | no | | `accumulated_feed_kg` |
| `current_avg_weight_g` | decimal | no | sí | no | | `current_avg_weight` |

Consistencia (solo si las cinco piezas son KNOWN): `accumulated_birds_received − historical_mortality − historical_culls − partial_outbound_birds = live_birds`. Si alguna pieza es UNKNOWN o N/A, la ecuación no se evalúa.

## CUTOVER_HATCHERY_V2 (una fila = un lote de incubadora con un proceso en curso; fase `INCUB` implícita)

| Campo | Tipo | Req. | UNKNOWN | N/A | Regla | Destino |
|---|---|---|---|---|---|---|
| `legacy_lot_code` | texto | sí | no | no | | `lots.legacy_lot_code` / `lot_code` |
| `existing_lot_code` | texto | no | — | — | lote hatchery existente sin eventos | REUSE |
| `hatchery_code` | texto | sí | no | no | `hatcheries.code` de la empresa, activa | `hatchery_openings.hatchery_id` |
| `incubator_name` | texto | no | — | — | `incubators.name` de la planta | `hatchery_openings.incubator_id` |
| `hatcher_name` | texto | no | — | — | `hatchers.name` de la planta | `hatchery_openings.hatcher_id` |
| `source_lot_code` | texto | no | — | — | lote GA (código o legado) grandparent/breeder de la empresa | `hatchery_openings.source_lot_id` (+`source_lot_reference` siempre) |
| `generation` | `grandparent\|breeder` | no | — | — | | `lots.hatchery_purpose`, `hatchery_openings.generation` |
| `reception_date` | fecha | sí | no | no | ≤ corte | `lots.start_date`, `hatchery_openings.reception_date` |
| `set_date` | fecha | no | sí | sí | `reception_date ≤ set_date ≤ corte` | `hatchery_openings.set_date` (+`set_date_status`) |
| `expected_hatch_date` | fecha | no | sí | sí | ≥ `set_date` | `hatchery_openings.expected_hatch_date` |
| `eggs_received` | entero ≥0 | sí (KNOWN) | no | no | huevo fértil recibido | `hatchery_openings.eggs_received` |
| `eggs_set` | entero ≥0 | sí (KNOWN) | no | no | ≤ `eggs_received` | `hatchery_openings.eggs_set` |
| `eggs_transferred` | entero | no | sí | sí | ≤ `eggs_set` | `hatchery_openings.eggs_transferred` (+status) |
| `eggs_discarded` | entero | no | sí | sí | ≤ `eggs_set` | `hatchery_openings.eggs_discarded` (+status) |
| `chicks_hatched` | entero | no | sí | sí | ≤ `eggs_transferred` si KNOWN, si no ≤ `eggs_set` | `opening_balances.accumulated_chicks_hatched` (+`chicks_hatched_status`) |
| `chicks_available` | entero | no | sí | sí | ≤ `chicks_hatched` | `opening_balances.initial_mixed_count` (pollitos vivos aún en planta) |
| `source_system`, `source_reference`, `notes` | texto | no | — | — | | como arriba |

Derivados (no se cargan): `eggs_in_process = eggs_set − eggs_transferred − eggs_discarded` (solo si KNOWN), `incubation_day = corte − set_date`.

Saldos tras el apply: huevos disponibles en planta = `eggs_received − eggs_set` + post; pollitos viables = `chicks_available` + nacimientos − salidas; aves del lote = `chicks_available` + post.

## Formatos

- **XLSX** `cutover_template_{bu}_v2.xlsx`: hojas `Instrucciones` (tabla por campo), `Meta` (`template_version=v2`, `schema_id`, `company`, `business_unit`, `generated_at`, `cutover_datetime` si se pidió con `batch_id`), `Datos` (cabecera = campos del contrato), `Catalogos` (`catalog, code, description, status, parent_code`).
- **CSV** `cutover_template_{bu}_v2.csv`: solo la cabecera de `Datos`; UTF-8 (BOM tolerado); delimitador `;` o `,` detectado por la cabecera; metadata desde el batch y `?template_version=v2`.
- Ambos → mismo DTO: `{row_number, raw, normalized: {campo: {value, status}}, errors}`.
