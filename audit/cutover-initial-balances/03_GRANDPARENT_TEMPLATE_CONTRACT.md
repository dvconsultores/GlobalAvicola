# CUTOVER-INITIAL-BALANCES · 03_GRANDPARENT_TEMPLATE_CONTRACT

Fecha: 2026-10-27 · SPEC 006 · `schema_id = CUTOVER_GRANDPARENT_V2` · versión `v2` · generado desde `backend/app/cutover/contracts.py`

| Dato | Valor |
|---|---|
| Unidad de negocio | `grandparent` (`lots.bird_type = grandparent`) |
| Fases compatibles | `CRIA`, `PROD` |
| Fecha que fija `lots.start_date` | `real_start_date` |
| Columnas (`Datos`) | 26 |
| Obligatorias | `legacy_lot_code`, `farm_code`, `productive_phase_code`, `real_start_date`, `live_males`, `live_females` |
| Archivo | `cutover_template_grandparent_v2.xlsx` (Instrucciones · Meta · Datos · Catalogos) · `cutover_template_grandparent_v2.csv` (solo cabecera, `;`) |
| Preview destacado | `legacy_lot_code`, `productive_phase_code`, `farm_code`, `house_name`, `live_males`, `live_females`, `historical_mortality_males`, `historical_mortality_females`, `accumulated_feed_kg`, `current_avg_weight_g`, `accumulated_egg_production` |

Semántica de celda: **vacío = UNKNOWN · `0` = KNOWN cero · `N/A` = NOT_APPLICABLE**. Fechas `AAAA-MM-DD`; pesos en gramos; alimento en kg.

## Campos

| Campo | Tipo | Unidad | Obligatorio | UNKNOWN (vacío) | N/A | Maestro | Valores | Significado | Destino |
|---|---|---|---|---|---|---|---|---|---|
| `legacy_lot_code` | text |  | sí | no | no |  |  | Código del lote en el sistema anterior. Único en el batch y en la empresa. | `lots.legacy_lot_code`<br>`lots.lot_code`<br>`opening_balances.legacy_lot_code` |
| `existing_lot_code` | text |  | no | no | no | lot |  | Código de un lote YA existente en Global Avícola para reutilizarlo (misma empresa, activo, sin eventos). | `lots.id` |
| `farm_code` | text |  | sí | no | no | farm |  | Código de la granja donde está el lote (hoja Catalogos → farm). | `lots.farm_id` |
| `house_name` | text |  | no | no | no | house |  | Nombre del galpón dentro de la granja (Catalogos → house, parent_code = granja). | `lots.house_id` |
| `area_code` | text |  | no | no | no | area |  | Código del área funcional (Catalogos → area). | `lots.area_id` |
| `productive_phase_code` | text |  | sí | no | no | productive_phase | CRIA, PROD | Fase productiva REAL del lote al corte. Valores para esta unidad: CRIA, PROD. | `lot_phases.phase_id`<br>`opening_balances.phase_at_activation_id` |
| `real_start_date` | date |  | sí | no | no |  |  | Fecha real de inicio del lote (alojamiento). AAAA-MM-DD, ≤ fecha del corte. | `lots.start_date`<br>`opening_balances.activation_date`<br>`opening_balances.age_days` |
| `phase_start_date` | date |  | no | sí | no |  |  | Fecha de inicio de la fase declarada. Vacío = se toma la fecha real de inicio. | `lot_phases.start_date` |
| `genetic_line_code` | text |  | no | no | no | genetic_line |  | Código de la línea genética (Catalogos → genetic_line). | `lots.genetic_line_id` |
| `breed_name` | text |  | no | no | no | breed |  | Nombre de la raza dentro de la línea genética (Catalogos → breed, parent_code = línea). | `lots.breed_id` |
| `sex` | enum |  | no | no | no |  | male, female, mixed | Sexo del lote. Vacío = mixto para engorde; vacío = sin declarar para reproductoras. | `lots.sex` |
| `live_males` | int | aves | sí | no | no |  |  | Machos vivos al momento del corte. | `opening_balances.initial_male_count` |
| `live_females` | int | aves | sí | no | no |  |  | Hembras vivas al momento del corte. | `opening_balances.initial_female_count` |
| `birds_placed_males` | int | aves | no | sí | no |  |  | Machos alojados originalmente (histórico). | `opening_balances.placed_male_count` |
| `birds_placed_females` | int | aves | no | sí | no |  |  | Hembras alojadas originalmente (histórico). | `opening_balances.placed_female_count` |
| `historical_mortality_males` | int | aves | no | sí | no |  |  | Mortalidad acumulada de machos ANTES del corte. | `opening_balances.accumulated_mortality_male` |
| `historical_mortality_females` | int | aves | no | sí | no |  |  | Mortalidad acumulada de hembras ANTES del corte. | `opening_balances.accumulated_mortality_female` |
| `historical_culls_males` | int | aves | no | sí | no |  |  | Descartes acumulados de machos antes del corte. | `opening_balances.accumulated_culls_male` |
| `historical_culls_females` | int | aves | no | sí | no |  |  | Descartes acumulados de hembras antes del corte. | `opening_balances.accumulated_culls_female` |
| `accumulated_feed_kg` | decimal | kg | no | sí | no |  |  | Alimento acumulado consumido antes del corte. | `opening_balances.accumulated_feed_kg` |
| `current_avg_weight_g` | decimal | g | no | sí | no |  |  | Peso promedio actual del ave al corte. | `opening_balances.current_avg_weight` |
| `accumulated_egg_production` | int | huevos | no | sí | sí |  |  | Huevos producidos acumulados antes del corte. N/A en cría. | `opening_balances.accumulated_egg_production` |
| `accumulated_eggs_to_hatchery` | int | huevos | no | sí | sí |  |  | Huevos enviados a incubadora acumulados antes del corte. N/A en cría. | `opening_balances.accumulated_eggs_to_hatchery` |
| `source_system` | text |  | no | no | no |  |  | Sistema de origen del dato (p. ej. LEGACY, SAP, EXCEL). Vacío = el del batch. | `lots.source_system`<br>`opening_balances.source_system` |
| `source_reference` | text |  | no | no | no |  |  | Referencia en el sistema de origen (documento, planilla, lote). | `lots.source_reference`<br>`opening_balances.source_reference` |
| `notes` | text |  | no | no | no |  |  | Notas libres. Nunca sustituyen a un campo del contrato. | `cutover_items.opening_state.notes` |

## Reglas de consistencia y fechas

- `real_start_date ≤ corte`; `real_start_date ≤ phase_start_date ≤ corte`.
- Por sexo, solo si alojadas, mortalidad, descartes y vivas son KNOWN: `alojadas − mortalidad − descartes = vivas`.
- `accumulated_eggs_to_hatchery ≤ accumulated_egg_production` si ambas KNOWN.
- En `CRIA`, `accumulated_egg_production` y `accumulated_eggs_to_hatchery` deben ser N/A o vacío (`METRIC_NOT_APPLICABLE_IN_PHASE`).
- Estado de una métrica con dos sexos: KNOWN solo si ambos lo son; N/A si ambos; si no, UNKNOWN.
