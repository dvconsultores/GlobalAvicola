# GA-FE-07 · EVIDENCIA DE RED (sanitizada)

Frontera: `https://avicola.globaldv.net/api/v1` · backend `5a5bb3f` · frontend `index-BUthrUt9.js`. Sin tokens ni PII.

| Método | Ruta | Actor | Cuerpo (forma) | Estado | Respuesta (resumen) |
|---|---|---|---|---|---|
| POST | `/lots` | C2 | `{…, area_id:11}` (activa) | **201** | lote 49 · `area_id:11` |
| POST | `/lots` | C2 | `{…, area_id:12}` (inactiva) | **400** | `{"detail":"Área inactiva","rule":"BR-07"}` |
| GET | `/lots?search=GA7-INACT-…` | C2 | — | 200 | `[]` (sin persistencia) |
| PUT | `/lots/{act}` | C2 | `{area_id:12}` (inactiva) | **400** | «Área inactiva» |
| GET | `/lots/{act}` | C2 | — | 200 | `area_id:11` (sin cambio) |
| GET | `/lots/48` (histórico) | C2 | — | 200 | `area_id:12` (inactiva, legible) |
| PUT | `/lots/48` | C2 | `{planned_close_date}` (sin área) | 200 | `area_id:12` intacta |
| PUT | `/lots/48` | C2 | `{area_id:12, planned_close_date}` (mismo id) | 200 | `area_id:12` (sin invalidación) |
| PUT | `/lots/48` | C2 | `{area_id:8}` (otra inactiva) | **400** | «Área inactiva» |
| PUT | `/lots/48` | C2 | `{area_id:11}` (activa) | 200 | `area_id:11` |
| POST/PUT | `/lots` · `/lots/{act}` | C2 | `area_id:5` (ajena) | **400** | «Área no encontrado» |
| POST | `/lots` | C2 | sin área | **201** | `area_id:null` |
| POST | `/lots` (carrera) | C2 | `area_id:10` (inactivada entre selección y envío) | **400** | «Área inactiva» · `search` = 0 |
| DELETE | `/masters/areas/{id}` | admin | baja oficial | 204 | usada para X, H, race, limpieza |
| GET | `/masters/areas?limit=100` | admin | — | 200 | inactivas **visibles** (control-plane) |
| GET | `/audit?module=lots&limit=100` | admin | — | 200 | creación activa 1 · inactiva 0 |
| POST | `/lots` (BU OFF / global / usuario sin BU / RBAC) | varios | — | **403** | los cuatro vectores |

Notas: el formulario realiza una única consulta a `/masters/areas` (misma ruta que antes; el filtro es local) — sin tormenta de peticiones. Las capturas crudas están en `evidence/green/runtime-green.json` y `evidence/red/`.
