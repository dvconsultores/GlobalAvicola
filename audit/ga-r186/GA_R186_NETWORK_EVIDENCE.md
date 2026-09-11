# GA-R186 · EVIDENCIA DE RED

Referencia cruda: `evidence/green/runtime-e2e.json` (`network_sample`), `evidence/red/typeerror-local.txt` y la captura RED heredada (`audit/ga-r184/evidence/red/runtime-red.json`).

## 1 · Muestreo de cabeceras (post-fix, `GET /reports/kpis/production-index?lot_id=11` → 200)

| Cabecera | Valor |
|---|---|
| Content-Type | `application/json` |
| Content-Length | 121 |
| Server | openresty |
| Fecha | capturada en el JSON |

## 2 · Matriz de códigos de la tranche

| Situación | Código |
|---|---|
| G-05 pre-fix (lote con `start_date`, captura heredada) | **500** (`prodindex35`) |
| G-05 post-fix | **200** (batería completa) |
| `lot_id` ausente | 422 (validación FastAPI) |
| Sin sesión | 401 (estándar) |
| Sin `reports:read` | **403** |
| Lote inexistente / ajeno / sin concesión / BU OFF (incl. global) | **404** «Lote no encontrado» |

## 3 · Higiene

Sin credenciales, tokens, cookies ni cabeceras `Authorization` en los artefactos (solo códigos, rutas y cuerpos ya presentes en la evidencia primaria).
