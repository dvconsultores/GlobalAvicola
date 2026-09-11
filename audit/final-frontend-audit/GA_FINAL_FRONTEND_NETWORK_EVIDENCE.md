# FINAL FRONTEND AUDIT · EVIDENCIA DE RED / SANEADA

Fecha: 2026-09-11 · Regla: sin `Authorization`, cookies, tokens ni credenciales. Todo dato crudo va en `evidence/*.json` sin secretos.

## 1 · Llamadas probatorias (por fila)

| FVA / fin | Llamada | Actor | Resultado | Fuente |
|---|---|---|---|---|
| Transversal (login) | `POST /login` | sintéticos | 200 (y 403 tras baja lógica) | runtime-uat.json · cleanup-uat.json |
| FVA-05 | `/me` · `POST /switch-company` | global | contexto efectivo | ga-uat-01 (histórico) |
| FVA-29 | `GET /lots?limit=100` | fdaop | 41 lotes de su alcance | runtime-uat.json |
| FVA-29 (tenant) | `GET /lots/999999` | fdaop | **404** (sin fuga) | FE-08 e2e-uat.json |
| FVA-13/14/15 | `GET /users` · `GET /roles` (página) | fdaadm | filas reales | runtime-uat.json |
| FVA-31 | KPI IPE lote (detalle) | fdaop | tarjeta real (333.3 en fixtures R-187/OD-22) | FE-08 + ga-uat-07 |
| FVA-08/09 | `DELETE/POST /users/{id}/business-units/{code}` | fdaacc (UI) + admin | 200/201; estado de fila «Concedida» | runtime-uat.json |
| FVA-02 | `POST /users/{id}/password` ×2 | fdaop | 204 → relogin 200 → 204 | runtime-uat.json |
| Fail-closed (FIA-01/37) | `GET /masters/*`, `/sap/references`, `/dashboard/admin` con rol mínimo | fdaop/fdaadm | **403** (denegado ≠ vacío) | probe-403-urls.json |
| BU OFF (OD-16/23) | `PATCH /business-units/{code}/disable` + lectura | admin/fdaop | 200; ceros/404 en producto | ga-bu-d10 · FE-08 |
| Limpieza | revokes/`DELETE /users`/roles/disable | admin | 200/204/200; catálogo 4×OFF | cleanup-uat.json |

## 2 · Semántica

- Los 403 observados en consola son **fail-closed esperado** de actores con rol mínimo (maestros/SAP/dashboard-admin): al añadir `masters:read` desaparecen (probe-b01-wizard.json); no son defectos.
- Ninguna respuesta probatoria se obtuvo por página de error/redirect/vacío no pedido: las filas afirman pantalla + estado (p. ej. contadores, tarjetas, filas de tabla).
- Saneado: los JSON de evidencia no contienen cabeceras de autorización ni tokens (verificado en el secret-check del commit).
