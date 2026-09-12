# GA-F01 · CONTRATO DE ALMACENAMIENTO DE HUEVOS (`egg_storage_records`)

Fecha: 2026-09-12.

## 1 · Estructura canónica (backend, sin cambios)

- Campo: **`egg_storage_records`**, lista de `EggStorageSchema` (`backend/app/operations/schemas.py`), default `[]` en `OperationalEventCreate` — propiedad **opcional**.
- `EggStorageSchema`: `arrival_date: date` **requerido**; `eggs_received`, temperaturas, humedad, fechas de almacenamiento, transporte, `lot_id`, `notes` opcionales.
- Modelo DB `egg_storage`: `lot_id` **NOT NULL** (relevante para la observación F-01c).

## 2 · Semántica (contrato observado, sin cambios)

| Entrada | Resultado |
|---|---|
| Propiedad ausente | válido → lista vacía |
| `[]` | **válido** → «sin registros» (canónico; mismo default del esquema) |
| `[{}]` | **inválido** → 422 (`arrival_date` requerido) |
| Objeto parcial (sin `arrival_date`) | inválido → 422 |
| Objeto completo (`arrival_date` + contenido) | válido a nivel esquema (ver §4 F-01c para matiz de servicio en eventos sin lote) |

## 3 · Contrato del frontend (a corregir — F-01)

- Hoy: `defaultValues` fija `[{}]` y `onSubmit` lo envía tal cual → **siempre inválido** cuando el usuario no captura almacenamiento (todas las altas del asistente salvo el caso de incubadora).
- Corrección (R-189): serializar solo **registros con contenido**; sin contenido → `[]`. El registro completo, si el usuario lo captura, viaja íntegro (sin alterar campos).
- Parcialidad: un registro parcial con contenido se envía y el rechazo gobernado del servidor se muestra de forma segura (normalizador de errores) — el formulario no inventa campos.
- El caso `egg_reception_hatchery` (única superficie que captura almacenamiento) conserva su captura actual; su brecha de `arrival_date` queda como observación **F-01b** (no se modifica en este tranche).

## 4 · Observaciones adyacentes registradas (no implementadas)

- **F-01b**: `egg_reception_hatchery` no ofrece campo `arrival_date` → un registro real de almacenamiento no puede completarse desde esa pantalla (latente, previo).
- **F-01c**: registro completo en un evento **sin lote** → 500 (`es_data.setdefault("lot_id", data.lot_id)` con `None` vs `egg_storage.lot_id` NOT NULL). Alcanzable solo por API/sonda; hallazgo propio si se prioriza.

## 5 · Evidencia

Controles de contrato (runtime real, sondas canceladas): importación canónica `[]` → **201**; `[{}]` → 422; recepción `[]` → 201 / `[{}]` → 422. Detalle completo en `GA_F01_IMPORT_CONTRACT_TRACE.md §4`.
