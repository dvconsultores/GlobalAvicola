# CUTOVER-INITIAL-BALANCES · 06_BROILER_TEMPLATE_CONTRACT

Fecha: 2026-10-15 · SPEC 006 · `schema_id = CUTOVER_BROILER_V2` · versión `v2` · generado desde `backend/app/cutover/contracts.py`

| Dato | Valor |
|---|---|
| Unidad de negocio | `broiler` (`lots.bird_type = broiler`) |
| Fases compatibles | `ENGORDE` |
| Fecha que fija `lots.start_date` | `real_start_date` |
| Columnas (`Datos`) | 22 |
| Obligatorias | `legacy_lot_code`, `farm_code`, `productive_phase_code`, `real_start_date`, `live_birds` |
| Archivo | `cutover_template_broiler_v2.xlsx` (Instrucciones · Meta · Datos · Catalogos) · `cutover_template_broiler_v2.csv` (solo cabecera, `;`) |
| Preview destacado | `legacy_lot_code`, `farm_code`, `house_name`, `real_start_date`, `age_days`, `live_birds`, `historical_mortality`, `historical_culls`, `accumulated_feed_kg`, `current_avg_weight_g` |

Semántica de celda: **vacío = UNKNOWN · `0` = KNOWN cero · `N/A` = NOT_APPLICABLE**. Fechas `AAAA-MM-DD`; pesos en gramos; alimento en kg.

## Campos

| Campo | Tipo | Unidad | Obligatorio | UNKNOWN (vacío) | N/A | Maestro | Valores | Significado | Destino |
|---|---|---|---|---|---|---|---|---|---|
| `legacy_lot_code` | text |  | sí | no | no |  |  | Código del lote en el sistema anterior. Único en el batch y en la empresa. | `lots.legacy_lot_code`<br>`lots.lot_code`<br>`opening_balances.legacy_lot_code` |
| `existing_lot_code` | text |  | no | no | no | lot |  | Código de un lote YA existente en Global Avícola para reutilizarlo (misma empresa, activo, sin eventos). | `lots.id` |
| `farm_code` | text |  | sí | no | no | farm |  | Código de la granja donde está el lote (hoja Catalogos → farm). | `lots.farm_id` |
| `house_name` | text |  | no | no | no | house |  | Nombre del galpón dentro de la granja (Catalogos → house, parent_code = granja). | `lots.house_id` |
| `area_code` | text |  | no | no | no | area |  | Código del área funcional (Catalogos → area). | `lots.area_id` |
| `productive_phase_code` | text |  | sí | no | no | productive_phase | ENGORDE | Fase productiva REAL del lote al corte. Valores para esta unidad: ENGORDE. | `lot_phases.phase_id`<br>`opening_balances.phase_at_activation_id` |
| `real_start_date` | date |  | sí | no | no |  |  | Fecha real de inicio del lote (alojamiento). AAAA-MM-DD, ≤ fecha del corte. | `lots.start_date`<br>`opening_balances.activation_date`<br>`opening_balances.age_days` |
| `phase_start_date` | date |  | no | sí | no |  |  | Fecha de inicio de la fase declarada. Vacío = se toma la fecha real de inicio. | `lot_phases.start_date` |
| `genetic_line_code` | text |  | no | no | no | genetic_line |  | Código de la línea genética (Catalogos → genetic_line). | `lots.genetic_line_id` |
| `breed_name` | text |  | no | no | no | breed |  | Nombre de la raza dentro de la línea genética (Catalogos → breed, parent_code = línea). | `lots.breed_id` |
| `sex` | enum |  | no | no | no |  | male, female, mixed | Sexo del lote. Vacío = mixto para engorde; vacío = sin declarar para reproductoras. | `lots.sex` |
| `live_birds` | int | aves | sí | no | no |  |  | Aves vivas (mixtas) al momento del corte. | `opening_balances.initial_mixed_count` |
| `age_days` | int | días | no | sí | no |  |  | Edad del lote en días al corte. Vacío = se deriva de la fecha de inicio. | `opening_balances.age_days` |
| `accumulated_birds_received` | int | aves | no | sí | no |  |  | Aves recibidas acumuladas (alojadas) antes del corte. | `opening_balances.accumulated_broiler_received` |
| `historical_mortality` | int | aves | no | sí | no |  |  | Mortalidad acumulada antes del corte. | `opening_balances.accumulated_mortality_mixed` |
| `historical_culls` | int | aves | no | sí | no |  |  | Descartes acumulados antes del corte. | `opening_balances.accumulated_culls_mixed` |
| `partial_outbound_birds` | int | aves | no | sí | sí |  |  | Aves salidas parcialmente a planta antes del corte. N/A si no hubo salidas parciales. | `opening_balances.accumulated_outbound_birds` |
| `accumulated_feed_kg` | decimal | kg | no | sí | no |  |  | Alimento acumulado consumido antes del corte. | `opening_balances.accumulated_feed_kg` |
| `current_avg_weight_g` | decimal | g | no | sí | no |  |  | Peso promedio actual del ave al corte. | `opening_balances.current_avg_weight` |
| `source_system` | text |  | no | no | no |  |  | Sistema de origen del dato (p. ej. LEGACY, SAP, EXCEL). Vacío = el del batch. | `lots.source_system`<br>`opening_balances.source_system` |
| `source_reference` | text |  | no | no | no |  |  | Referencia en el sistema de origen (documento, planilla, lote). | `lots.source_reference`<br>`opening_balances.source_reference` |
| `notes` | text |  | no | no | no |  |  | Notas libres. Nunca sustituyen a un campo del contrato. | `cutover_items.opening_state.notes` |

## Reglas de consistencia y fechas

- `real_start_date ≤ corte`; fase obligatoriamente `ENGORDE`.
- Solo si las cinco piezas son KNOWN: `accumulated_birds_received − historical_mortality − historical_culls − partial_outbound_birds = live_birds`.
- `age_days` vacío ⇒ se deriva de `real_start_date` (edad = corte − inicio) con estado KNOWN; declarado ⇒ se respeta.
- `sex` vacío ⇒ `mixed`.
