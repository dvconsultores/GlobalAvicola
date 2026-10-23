# CUTOVER-INITIAL-BALANCES · 10_APPLY_DESTINATION_MATRIX

Fecha: 2026-10-22 · SPEC 006 · generado desde `backend/app/cutover/contracts.py`; el apply vive en `CutoverService.aplicar` (`service.py`) con un builder por BU (`_opening_reproductoras`, `_opening_engorde`, `_opening_incubadora` + `_hatchery_opening`, `_lote`, `_lot_phase`).

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

### `grandparent` · `CUTOVER_GRANDPARENT_V2`

| Entidad | Columnas ← campo de plantilla |
|---|---|
| `lots` | `legacy_lot_code` ← `legacy_lot_code`<br>`lot_code` ← `legacy_lot_code`<br>`id` ← `existing_lot_code`<br>`farm_id` ← `farm_code`<br>`house_id` ← `house_name`<br>`area_id` ← `area_code`<br>`start_date` ← `real_start_date`<br>`genetic_line_id` ← `genetic_line_code`<br>`breed_id` ← `breed_name`<br>`sex` ← `sex`<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `opening_balances` | `legacy_lot_code` ← `legacy_lot_code`<br>`phase_at_activation_id` ← `productive_phase_code`<br>`activation_date` ← `real_start_date`<br>`age_days` ← `real_start_date`<br>`initial_male_count` ← `live_males`<br>`initial_female_count` ← `live_females`<br>`placed_male_count` ← `birds_placed_males` (+`placed_status`)<br>`placed_female_count` ← `birds_placed_females` (+`placed_status`)<br>`accumulated_mortality_male` ← `historical_mortality_males` (+`mortality_status`)<br>`accumulated_mortality_female` ← `historical_mortality_females` (+`mortality_status`)<br>`accumulated_culls_male` ← `historical_culls_males` (+`culls_status`)<br>`accumulated_culls_female` ← `historical_culls_females` (+`culls_status`)<br>`accumulated_feed_kg` ← `accumulated_feed_kg` (+`feed_status`)<br>`current_avg_weight` ← `current_avg_weight_g` (+`weight_status`)<br>`accumulated_egg_production` ← `accumulated_egg_production` (+`egg_production_status`)<br>`accumulated_eggs_to_hatchery` ← `accumulated_eggs_to_hatchery` (+`eggs_to_hatchery_status`)<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `lot_phases` | `phase_id` ← `productive_phase_code`<br>`start_date` ← `phase_start_date` |
| `cutover_items` | `opening_state.notes` ← `notes` |

### `breeder` · `CUTOVER_BREEDER_V2`

| Entidad | Columnas ← campo de plantilla |
|---|---|
| `lots` | `legacy_lot_code` ← `legacy_lot_code`<br>`lot_code` ← `legacy_lot_code`<br>`id` ← `existing_lot_code`<br>`farm_id` ← `farm_code`<br>`house_id` ← `house_name`<br>`area_id` ← `area_code`<br>`start_date` ← `real_start_date`<br>`genetic_line_id` ← `genetic_line_code`<br>`breed_id` ← `breed_name`<br>`sex` ← `sex`<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `opening_balances` | `legacy_lot_code` ← `legacy_lot_code`<br>`phase_at_activation_id` ← `productive_phase_code`<br>`activation_date` ← `real_start_date`<br>`age_days` ← `real_start_date`<br>`initial_male_count` ← `live_males`<br>`initial_female_count` ← `live_females`<br>`placed_male_count` ← `birds_placed_males` (+`placed_status`)<br>`placed_female_count` ← `birds_placed_females` (+`placed_status`)<br>`accumulated_mortality_male` ← `historical_mortality_males` (+`mortality_status`)<br>`accumulated_mortality_female` ← `historical_mortality_females` (+`mortality_status`)<br>`accumulated_culls_male` ← `historical_culls_males` (+`culls_status`)<br>`accumulated_culls_female` ← `historical_culls_females` (+`culls_status`)<br>`accumulated_feed_kg` ← `accumulated_feed_kg` (+`feed_status`)<br>`current_avg_weight` ← `current_avg_weight_g` (+`weight_status`)<br>`accumulated_egg_production` ← `accumulated_egg_production` (+`egg_production_status`)<br>`accumulated_eggs_to_hatchery` ← `accumulated_eggs_to_hatchery` (+`eggs_to_hatchery_status`)<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `lot_phases` | `phase_id` ← `productive_phase_code`<br>`start_date` ← `phase_start_date` |
| `cutover_items` | `opening_state.notes` ← `notes` |

### `broiler` · `CUTOVER_BROILER_V2`

| Entidad | Columnas ← campo de plantilla |
|---|---|
| `lots` | `legacy_lot_code` ← `legacy_lot_code`<br>`lot_code` ← `legacy_lot_code`<br>`id` ← `existing_lot_code`<br>`farm_id` ← `farm_code`<br>`house_id` ← `house_name`<br>`area_id` ← `area_code`<br>`start_date` ← `real_start_date`<br>`genetic_line_id` ← `genetic_line_code`<br>`breed_id` ← `breed_name`<br>`sex` ← `sex`<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `opening_balances` | `legacy_lot_code` ← `legacy_lot_code`<br>`phase_at_activation_id` ← `productive_phase_code`<br>`activation_date` ← `real_start_date`<br>`age_days` ← `real_start_date`<br>`initial_mixed_count` ← `live_birds`<br>`age_days` ← `age_days` (+`age_status`)<br>`accumulated_broiler_received` ← `accumulated_birds_received` (+`broiler_received_status`)<br>`accumulated_mortality_mixed` ← `historical_mortality` (+`mortality_status`)<br>`accumulated_culls_mixed` ← `historical_culls` (+`culls_status`)<br>`accumulated_outbound_birds` ← `partial_outbound_birds` (+`outbound_status`)<br>`accumulated_feed_kg` ← `accumulated_feed_kg` (+`feed_status`)<br>`current_avg_weight` ← `current_avg_weight_g` (+`weight_status`)<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `lot_phases` | `phase_id` ← `productive_phase_code`<br>`start_date` ← `phase_start_date` |
| `cutover_items` | `opening_state.notes` ← `notes` |

### `hatchery` · `CUTOVER_HATCHERY_V3`

| Entidad | Columnas ← campo de plantilla |
|---|---|
| `lots` | `legacy_lot_code` ← `legacy_lot_code`<br>`lot_code` ← `legacy_lot_code`<br>`id` ← `existing_lot_code`<br>`hatchery_purpose` ← `generation`<br>`start_date` ← `reception_date`<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `opening_balances` | `legacy_lot_code` ← `legacy_lot_code`<br>`activation_date` ← `reception_date`<br>`accumulated_chicks_hatched` ← `chicks_hatched` (+`chicks_hatched_status`)<br>`initial_mixed_count` ← `chicks_available`<br>`source_system` ← `source_system`<br>`source_reference` ← `source_reference` |
| `hatchery_openings` | `hatchery_id` ← `hatchery_code`<br>`incubator_id` ← `incubator_name`<br>`hatcher_id` ← `hatcher_name`<br>`source_lot_id` ← `source_lot_code`<br>`source_lot_reference` ← `source_lot_code`<br>`generation` ← `generation`<br>`egg_origin` ← `egg_origin`<br>`reception_date` ← `reception_date`<br>`set_date` ← `set_date` (+`set_date_status`)<br>`expected_hatch_date` ← `expected_hatch_date` (+`expected_hatch_date_status`)<br>`eggs_received` ← `eggs_received` (+`eggs_received_status`)<br>`eggs_set` ← `eggs_set` (+`eggs_set_status`)<br>`eggs_transferred` ← `eggs_transferred` (+`eggs_transferred_status`)<br>`eggs_discarded` ← `eggs_discarded` (+`eggs_discarded_status`) |
| `cutover_items` | `opening_state.notes` ← `notes` |

## Garantías

- Atómico: una fila que falla (`LOT_DUPLICATE`, `OPENING_ALREADY_EXISTS`, `PHASE_REQUIRED`, `MASTER_NOT_FOUND`) ⇒ rollback total + `FAILED_APPLY` auditado; el batch sigue `APPROVED`.
- Idempotente: `APPLIED` es terminal (doble apply ⇒ 409).
- Los valores UNKNOWN se guardan como `NULL` (columnas nulables) o `0` **acompañados del estado** en las columnas NOT NULL heredadas (`accumulated_mortality_*`, `accumulated_culls_*`); la lectura siempre consulta el estado.
