# GA-FE-06 · EVIDENCIA DE RED (sanitizada)

Generación: `index-DcqmSs-R.js`. Capturado con Playwright (`request`/`response`) y `fetch` controlado. **Sin tokens, cookies ni PII** en este documento.

## Alta de lote (POST `/api/v1/lots`) — antes vs después

| Generación | Claves del payload | `planned_close_date` | `area_id` | Estado |
|---|---|---|---|---|
| Entrada `index-WUv1-F9o.js` (RED) | `bird_type, breed_id, farm_id, genetic_line_id, house_id, lot_code, sap_reference, start_date` (8) | **ausente** | **ausente** | 201 |
| GA-FE-06 `index-DcqmSs-R.js` (GREEN) | las 8 + `area_id`, `planned_close_date` (10) | `"2026-09-21"` (ej. lote 19) | `1` | 201 |

Frescura: `GET /api/v1/lots/{id}` devuelve `planned_close_date:"…T00:00:00Z"`/`area_id` idénticos a lo enviado (lotes 19–24).

## Rutas por flujo

| Flujo | Endpoints observados | Observación |
|---|---|---|
| `/lots/new` | `me` · `notifications/unread-count` · `masters/farms` · `masters/houses` · `masters/genetic-lines` · `masters/breeds` · **`masters/areas`** | **8 peticiones**, sin tormenta (una por maestro; la de áreas es la nueva y respeta el inquilino) |
| Alta (submit) | `POST /lots` → `GET /lots/{id}` (navegación a detalle) | 201/200 |
| Detalle | `GET /lots/{id}` · `reports/kpis?lot_id=` · `reports/kpi/ipe/{id}` · `reports/kpi/weight-uniformity/{id}` | Las 3 KPI: 403 sin `reports:read` (ruido preexistente N-3); con `reports:read`, `ipe` → 500 (N-2) |
| Refresh/relogin | `me` · `GET /lots/{id}` | Sin datos duplicados |
| RBAC (D) | `POST /lots` → **403** | Sin llamada previa del formulario (guard UI) |
| CBU (E) | `POST /lots` → **403** (detalle: «sin acceso operativo a la unidad de negocio 'broiler'») | Sin persistencia |

## Negativos dirigidos (fuera de UI)

| Caso | Petición | Resultado |
|---|---|---|
| Área ajena (empresa 3) vía API directa | `POST /lots` `area_id:3` como C | **201** + persistida (lote 18) → **N-1** |
| KPI IPE en lote sin datos (con `reports:read` temporal) | `GET /reports/kpi/ipe/19` | **500** → **N-2** |
| Lista de maestros de C | `GET /masters/areas?limit=100` | 200 · ids `[1,2]` (solo empresa 1) |

## Sanitización

- Se registran método, ruta, estado y (solo para `POST /lots`) la forma del payload sin credenciales.
- Cabeceras `Authorization` nunca capturadas; `sessionStorage` no volcado.
- Los JSON crudos residen en `evidence/green/` (`runtime-green.json`, `verify-focus.json`, `final-verify.json`) y en `evidence/red/runtime-red.json` — contienen datos de negocio de fixtures, ninguna credencial.
