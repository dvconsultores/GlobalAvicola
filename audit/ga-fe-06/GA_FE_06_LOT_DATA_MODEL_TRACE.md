# GA-FE-06 · TRAZA DEL MODELO DE DATOS DEL LOTE

Fuente: `backend/app/masters/models.py::Lot` + migración `o5p6q7r8s9t0_areas_and_planned_close.py` + `tests/test_lot_planned_close.py`.

| Columna | Tipo SQL (ORM) | Nulable | FK / índice | Origen canónico | Uso |
|---|---|---|---|---|---|
| `id` | Integer PK | no | — | base | — |
| `company_id` | Integer | sí | FK `companies.id`, índice | fase 1/tenancy | inquilino (resuelto por servicio desde la sesión, no del cuerpo) |
| `farm_id` | Integer | sí | FK `farms.id` | — | validada por empresa (`La granja no pertenece a su compañía` ⇒ 403) |
| `house_id` | Integer | sí | FK `houses.id` | — | opcional |
| `genetic_line_id` | Integer | sí | FK `genetic_lines.id` | — | opcional |
| `weight_curve_id` | Integer | sí | FK `genetic_weight_curves.id` | `GA-REM-037`/`OD-06` (fijada al alta) | referencia histórica |
| `lot_code` | String(100) | no | único, índice | — | — |
| `bird_type` | Enum BirdTypeEnum | sí | — | `GA-REM-040-H` | fija cadena; guarda operativa por BU |
| `status` | Enum LotStatus | no (default `active`) | — | — | SLA exige `active` |
| `start_date` | DateTime(tz) | sí | — | `GA-REM-028`/`R-47` · `R-75` (medianoche UTC) | edad del lote |
| `end_date` | DateTime(tz) | sí | — | real, fijada por `close_lot` | — |
| **`planned_close_date`** | **DateTime(tz)** | **sí** | — | **`GA-REM-038` enmienda B / `OD-08`**, `docs/02 §3.14`, `R-75` | **base de la ventana SLA `0..3`** |
| **`area_id`** | **Integer** | **sí** | **FK `areas.id`, índice** | **`GA-REM-039`** | ámbito funcional del lote; destinatarios de avisos |
| `created_at` / `updated_at` | DateTime(tz) | no | — | — | — |

## Hechos de migración

- `o5p6q7r8s9t0_areas_and_planned_close.py`: `op.add_column("lots", planned_close_date …)` y `op.add_column("lots", area_id …)` — **ya aplicadas**.
- ⇒ **R-182 NO requiere migración** (§63 del encargo).

## Convención de fecha de negocio (`R-75`)

`_fecha_de_negocio(day)` = `datetime.combine(día, 00:00, tzinfo=UTC)`. Aplica a `start_date`, `end_date` y `planned_close_date`. El SLA compara **día natural del calendario**: `prevista.date()` (= el día UTC declarado, que en servidor CET corresponde al mismo día local al ser medianoche UTC = 02:00 CET) contra `date.today()` local. Sin desfase (±1) en la relectura.
