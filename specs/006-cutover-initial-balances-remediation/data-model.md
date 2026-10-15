# Data Model — SPEC 006

**Migración**: `e0f1a2b3c4d5_cutover_v2_openings` (revisa `d9e0f1a2b3c4`) · aditiva · `downgrade` funcional · sin enums PostgreSQL nuevos

## 1 · `opening_balances` — columnas nuevas

| Columna | Tipo | Nota |
|---|---|---|
| `initial_mixed_count` | Integer, default 0 | población viva sin sexo (engorde; pollitos disponibles en incubadora) |
| `accumulated_mortality_mixed` | Integer, default 0 | mortalidad histórica sin sexo |
| `accumulated_culls_mixed` | Integer, default 0 | descartes históricos sin sexo |
| `placed_male_count` / `placed_female_count` / `placed_mixed_count` | Integer, nullable | aves alojadas históricas (para la ecuación de consistencia) |
| `accumulated_outbound_birds` | Integer, nullable | salidas parciales históricas (engorde) |
| `placed_status`, `weight_status`, `eggs_to_hatchery_status`, `outbound_status`, `age_status`, `initial_mixed_status` | String(15), default `KNOWN` | estados que faltaban por métrica (`initial_mixed_status`: los pollitos disponibles en incubadora pueden ser UNKNOWN/N/A) |
| `template_version` | String(10), nullable | `v2` para openings de esta spec; nulo en manuales/v1 |

Columnas existentes que ahora se rellenan: `accumulated_feed_kg`, `current_avg_weight` (gramos), `accumulated_egg_production`, `accumulated_eggs_to_hatchery`, `accumulated_chicks_hatched`, `accumulated_broiler_received`, `age_days`, `phase_at_activation_id` (fase declarada), `cutover_datetime`, `source_system`, `source_reference`, `legacy_lot_code`.

## 2 · `hatchery_openings` (nueva)

| Columna | Tipo | Nota |
|---|---|---|
| `id` | PK | |
| `opening_id` | FK `opening_balances`, unique | 1:1 |
| `lot_id` | FK `lots`, unique | lote de incubadora |
| `hatchery_id` | FK `hatcheries` | |
| `incubator_id` / `hatcher_id` | FK, nullable | |
| `source_lot_id` | FK `lots`, nullable | lote origen (grandparent/breeder) |
| `source_lot_reference` | String(100), nullable | código escrito en la plantilla |
| `generation` | String(20), nullable | `grandparent` \| `breeder` |
| `reception_date` | Date | |
| `set_date` / `expected_hatch_date` | Date, nullable | |
| `eggs_received`, `eggs_set`, `eggs_transferred`, `eggs_discarded` | Integer, nullable | |
| `eggs_received_status`, `eggs_set_status`, `eggs_transferred_status`, `eggs_discarded_status`, `set_date_status`, `expected_hatch_date_status` | String(15) | KNOWN/UNKNOWN/NOT_APPLICABLE |
| `created_at` | timestamptz | |

Pollitos nacidos y disponibles viven en `opening_balances` (`accumulated_chicks_hatched` + `chicks_hatched_status`, `initial_mixed_count`).

## 3 · `lots` (sin cambio de esquema)

El apply rellena `house_id`, `area_id`, `genetic_line_id`, `breed_id`, `sex`, `hatchery_purpose`, `source_system`, `source_reference`, `origin=MIGRATED`, `legacy_lot_code`, `start_date`.

## 4 · `lot_phases` (sin cambio de esquema)

Una fila por lote migrado: `phase_id` declarado, `start_date = phase_start_date | real_start_date | reception_date`, `start_population_* = vivas al corte`, `is_active=True`.

## 5 · `cutover_batches` / `cutover_items` / `cutover_staging_rows` (sin cambio de esquema)

`source_type ∈ {XLSX, CSV}`, `template_version='v2'`. `normalized` y `opening_state` guardan `{campo: {value, status}}` + referencias resueltas (`farm_id`, `house_id`, …) + `derived` (edad, huevos en proceso, día de incubación).

## 6 · Guarda CUT-GL-02

Sin columna nueva: se evalúa con `opening_balances.cutover_datetime` del lote (`validators.validate_event_date`).
