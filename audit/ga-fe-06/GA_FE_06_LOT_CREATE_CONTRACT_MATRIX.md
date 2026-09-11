# GA-FE-06 · MATRIZ CONTRATO DE ALTA DE LOTE (FORM → API → DB → FRESH GET → UI)

Contrato real verificado: `LotCreate(LotBase)` en `backend/app/lots/schemas.py`; servicio `create_lot` (empresa desde sesión; granja validada; BU por `bird_type`; `_fecha_de_negocio` para fechas).

| Campo | Fuente en form | Tipo zod | ¿Req.? | Validación | Campo DTO (payload) | Valor wire | Schema backend | Columna DB | Fresh GET | Display |
|---|---|---|---|---|---|---|---|---|---|---|
| `lot_code` | Input | string | sí | min2/max50 | `lot_code` | string | `lot_code: str` | `lot_code` | ✓ | lista/detalle |
| `bird_type` | select | enum | sí | enum BIRD_TYPES | `bird_type` | enum | `bird_type: str?` | `bird_type` | ✓ | detalle |
| `farm_id` | select granjas | coerce number | sí | min 1 | `farm_id` | int | `farm_id: int?` | `farm_id` | ✓ | detalle |
| `house_id` | select galpones | coerce number opt | no | — | `house_id` | int/null | `house_id` | `house_id` | ✓ | — |
| `genetic_line_id` | select líneas | coerce number opt | no | — | `genetic_line_id` | int/null | `genetic_line_id` | `genetic_line_id` | ✓ | — |
| `breed_id` | select razas | coerce number opt | no | — | `breed_id` | int/null | `breed_id` | `breed_id` | ✓ | — |
| `start_date` | Input date | string opt | no | — | `start_date` | `YYYY-MM-DD`/null | `start_date: datetime?` | `start_date` (medianoche UTC, R-75) | ✓ | detalle |
| **`planned_close_date`** | **Input date (existe)** | string opt | **no** | — | **FALTABA en payload** → GA-FE-06 lo envía | `YYYY-MM-DD`/null | `planned_close_date: datetime?` (aceptado) | `planned_close_date` (nullable, R-75) | ✓ (`LotRead`) | GA-FE-06: fila «Cierre previsto» en detalle |
| **`area_id`** | **sin control (zod muerto)** → GA-FE-06 añade selector `/masters/areas?limit=100` | coerce number opt | **no** | — | **FALTABA en payload** → GA-FE-06 lo envía | int/null | `area_id: int?` (aceptado) | `area_id` (nullable FK) | ✓ (`LotRead`) | selector (form); detalle N/A (ver clarificaciones) |
| `sap_reference` | Input | string opt | no | — | `sap_reference` (enviado) | string/null | **no declarado en `LotBase`** ⇒ ignorado por pydantic | — | — | — (observación no-R-182) |

## Regla resultante

**0 campos gobernados con pérdida silenciosa** tras GA-FE-06: `planned_close_date` y `area_id` viajan capturados → DTO → servicio → DB → fresh GET. `sap_reference` queda registrado como observación separada (no gobernado en el contrato de lote; no se toca en esta tranche).

## Serialización de fechas

`Input type="date"` ⇒ `YYYY-MM-DD` (wire). Backend parsea a datetime sin zona y normaliza a **medianoche UTC** (`_fecha_de_negocio`, `R-75`). Relectura: `planned_close_date` regresa como ISO UTC medianoche; el detalle muestra el **día del calendario** (`slice(0,10)` del ISO — determinista, sin conversión local ⇒ sin ±1).
