# GA-FE-06-A · EVIDENCIA DE RED (sanitizada)

Frontera: `https://avicola.globaldv.net/api/v1` · backend verde `69d0c95` · bundle `index-DcqmSs-R.js` (sin cambio). Sin tokens ni PII en este documento.

## Peticiones y resultados observados (GREEN)

| Método | Ruta | Actor | Cuerpo (forma) | Estado | Cuerpo de respuesta (resumen) |
|---|---|---|---|---|---|
| POST | `/lots` | F | `{lot_code, bird_type:"broiler", farm_id:1, area_id:5}` | **400** | `{"detail":"Área no encontrado","rule":"BR-07"}` |
| GET | `/lots?search=GA6A-GREEN-FOREIGN-…` | F | — | 200 | `[]` (sin persistencia) |
| POST | `/lots` | F | `…, area_id:4, planned_close_date:"2026-09-12"` | **201** | lote 32 (área 4) |
| GET | `/lots/32` | F | — | 200 | `area_id:4`, `planned_close_date:"2026-09-12T00:00:00Z"` |
| POST | `/lots` | F | `…` sin área | **201** | lote 33 · `area_id:null` |
| POST | `/lots` | F | `…, area_id:999999` | **400** | íd. BR-07 (antes 500) |
| PUT | `/lots/{id}` | F | `{area_id:5}` | **400** | íd. BR-07 |
| GET | `/lots/{id}` (fresh) | F | — | 200 | `area_id:4` (sin mutación) |
| PUT | `/lots/{id}` | F | `{area_id:4}` | 200 | control de edición válida |
| POST | `/lots` | G (sin concesión) | `{lot_code,…}` | **403** | «sin acceso operativo a la unidad de negocio 'broiler'» |
| POST | `/lots` | H (sin `lots:create`) | íd. | **403** | «Permiso requerido: lots:create» |
| PATCH | `/business-units/broiler/disable` → POST → `enable` | admin | — | 200 / **403** / 200 | «sin empresa efectiva con unidades de negocio habilitadas» |
| GET | `/audit?module=lots&limit=100` | admin | — | 200 | 1 creación `GA6A-GREEN-OK-…`; **0** para el código ajeno |
| GET | `/masters/areas?limit=100` (implícito vía UI) | F | — | 200 | solo áreas de su empresa (selector) |

## Observación de despliegue (C6)

Sonda de comportamiento (`POST` con `area_id=999999`): `500` → `500` → `500` → `502` (reinicio del contenedor) → **`400` BR-07** ⇒ generación `69d0c95` en servicio. Sin intervención manual sobre Watchtower/CI.

## Notas

- Las respuestas de denegación no varían entre «no existe» y «es de otro inquilino» (anti-enumeración).
- El frontend no emitió ninguna petición nueva por este cambio (0 cambios de producto); el filtrado del selector es la misma llamada a `/masters/areas` ya existente.
