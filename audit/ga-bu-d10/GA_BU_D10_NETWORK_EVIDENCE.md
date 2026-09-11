# GA-BU-D10 · EVIDENCIA DE RED (sanitizada)

Sin tokens, sin cabeceras `Authorization`, sin cookies. Fuente: `evidence/runtime-api.json` (paths/status/cuerpos) y `runtime-ui.json`.

## 1 · Generación

| Observación | Valor |
|---|---|
| Apagado marca concesiones (generación nueva) | 1.ª marca `2026-09-11T19:33:10.622154Z` (probe del ciclo) |
| Bundle frontend | `index-BUthrUt9.js` (sin cambio) |

## 2 · Peticiones representativas

```
PATCH /api/v1/business-units/broiler/disable        → 200 {"is_enabled": false}
PATCH /api/v1/business-units/broiler/enable         → 200 {"is_enabled": true}
POST  /api/v1/users/142/business-units {"code":"broiler"} → 201 (concesión viva)
GET   /api/v1/users/142/business-units              → 200 [ {code:"broiler", revoked_at: "<marca>", is_effective:false}, ... ]
GET   /api/v1/me (OP, tras OFF)                     → 200 {"effective_business_units": [], "granted_business_units": []}
GET   /api/v1/me (OP, tras re-encender · B)         → 200 {"effective_business_units": [], "granted_business_units": []}
GET   /api/v1/lots?limit=5 (OP sin acceso)          → 200 [] (alcance vacío; nunca error crudo)
GET   /api/v1/reports/kpi/ipe/54 (OP sin acceso)    → 404 {"detail":"Lote no encontrado"}
```

## 3 · Negativos gobernados

```
POST /api/v1/users/143/business-units {"code":"broiler"} (self-grant)      → 403
POST /api/v1/users/142/business-units {"code":"broiler"} (unidad OFF)      → 409 «la empresa no tiene habilitada…»
POST /users/{company1} con token de empresa 3 (cross-company)              → 404
GET  /reports/kpi/ipe/54 con sin reports:read pero con concesión           → 403 «Permiso requerido: reports:read»
GET  /reports/kpi/ipe/54 (global, BU OFF)                                  → 404
```

## 4 · Auditoría (muestra sanitizada)

```
GET /api/v1/audit → 200 · eventos user_business_unit: 23 · terminaciones con causa
cause="company_business_unit_disabled", previous_state="granted", new_state="revoked",
new_values={target_user_id, business_unit} (uno por concesión terminada y ciclo)
```
