# F-01d · Evidencia nube (runtime) — payload real y 500 del detalle

Fecha: 2026-09-12 · Entorno: `https://avicola.globaldv.net` (bundle `index-ygTuhjcs.js`, post-C2)

## Hechos

1. Payload real capturado del walkthrough (`/tmp/f01_e2e.json`, `payloads[1]`, importación de abuelas):
   - `"feed_movements": [{}]`
   - `"hatchery_params": [{}]`
   - `"egg_movements": []`, `"egg_storage_records": []`, `"inspection_details": []`

2. `GET /api/v1/operations/{id}` → **500** determinista en eventos creados con ese payload:
   - id 112 (`feed_movements: [{}]` sólo) → 500
   - ids 115 y 116 (repetición) → 500, 500
   - id 117 (`egg`+`feed`) → 500

3. Controles (mismo momento, mismo token):
   - id 111 (`egg_movements: [{}]`/vacío, sin feed) → 200
   - id 110 (todas las claves de submovimiento ausentes) → 200
   - `POST /operations/{id}/submit` y `GET /operations/{id}/evidences` del evento feed → 200
     (el defecto es exclusivo del **detalle**)

4. Mecanismo confirmado localmente (misma app, PostgreSQL de pruebas): `feed_movements:[{}]` ⇒ POST 201,
   GET detalle 500 por `ValidationError: FeedMovementSchema.quantity_kg gt=0 (0.0)`.
   Evidencia: `RED_local_traceback_exception.txt`, `RED_local_matriz.txt`.

Nota de exactitud: la inferencia inicial «clave `feed_movements` ⇒ 500» quedó corregida por el repro
local: el disparador es la **fila vacía `[{}]`**; `[]` es inocuo. Véase el anexo `GA_F01D_SUBSANACION_ANNEX.md`.
