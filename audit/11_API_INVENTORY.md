# 11 — INVENTARIO DE API

> Generado instanciando la aplicación FastAPI y volcando su esquema OpenAPI (`app.openapi()`), con `FEATURE_SAP_ENABLED=true`.
> **168 operaciones** (167 bajo `/api/v1` + `GET /health`). Ninguna requiere rol ni permiso: todas usan `Depends(get_current_user)` sin más.

## Convenciones

`FE` = consumido por alguna pantalla · `FE(muerto)` = solo referenciado desde `services/*.service.ts` sin consumidor · `HUÉRFANO` = sin ninguna referencia.

| # | Método | Endpoint | Módulo | Auth | Permiso exigido | Consumo FE | Estado |
|---|---|---|---|---|---|---|---|
| 1 | GET | `/health` | Health | no | — | Docker healthcheck | OK |
| 2 | POST | `/api/v1/login` | Auth | **público** | **ninguno** | FE | OK |
| 3 | POST | `/api/v1/refresh` | Auth | **público** (valida el refresh token) | **ninguno** | FE | BE-04: token degradado sin view_type/company_id/role_id |
| 4 | GET | `/api/v1/me` | Auth | bearer | **ninguno** | FE | OK |
| 5 | POST | `/api/v1/switch-company` | Auth | bearer | **ninguno** | FE | OK |
| 6 | GET | `/api/v1/users` | Users | bearer | **ninguno** | FE | OK |
| 7 | POST | `/api/v1/users` | Users | bearer | **ninguno** | FE | OK |
| 8 | GET | `/api/v1/users/{user_id}` | Users | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 9 | PUT | `/api/v1/users/{user_id}` | Users | bearer | **ninguno** | FE | OK |
| 10 | DELETE | `/api/v1/users/{user_id}` | Users | bearer | **ninguno** | FE | OK |
| 11 | GET | `/api/v1/roles` | Roles | bearer | **ninguno** | FE | OK |
| 12 | POST | `/api/v1/roles` | Roles | bearer | **ninguno** | FE | OK |
| 13 | PUT | `/api/v1/roles/{role_id}` | Roles | bearer | **ninguno** | FE | OK |
| 14 | GET | `/api/v1/masters/companies` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 15 | POST | `/api/v1/masters/companies` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 16 | GET | `/api/v1/masters/companies/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 17 | DELETE | `/api/v1/masters/companies/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 18 | PUT | `/api/v1/masters/companies/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 19 | GET | `/api/v1/masters/farms` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 20 | POST | `/api/v1/masters/farms` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 21 | GET | `/api/v1/masters/farms/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 22 | DELETE | `/api/v1/masters/farms/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 23 | PUT | `/api/v1/masters/farms/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 24 | GET | `/api/v1/masters/houses` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 25 | POST | `/api/v1/masters/houses` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 26 | GET | `/api/v1/masters/houses/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 27 | DELETE | `/api/v1/masters/houses/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 28 | PUT | `/api/v1/masters/houses/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 29 | GET | `/api/v1/masters/hatcheries` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 30 | POST | `/api/v1/masters/hatcheries` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 31 | GET | `/api/v1/masters/hatcheries/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 32 | DELETE | `/api/v1/masters/hatcheries/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 33 | PUT | `/api/v1/masters/hatcheries/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 34 | GET | `/api/v1/masters/incubators` | Masters | bearer | **ninguno** | FE (formulario) | OK |
| 35 | POST | `/api/v1/masters/incubators` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 36 | GET | `/api/v1/masters/incubators/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 37 | DELETE | `/api/v1/masters/incubators/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 38 | GET | `/api/v1/masters/hatchers` | Masters | bearer | **ninguno** | FE (formulario) | OK |
| 39 | POST | `/api/v1/masters/hatchers` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 40 | GET | `/api/v1/masters/hatchers/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 41 | DELETE | `/api/v1/masters/hatchers/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 42 | GET | `/api/v1/masters/genetic-lines` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 43 | POST | `/api/v1/masters/genetic-lines` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 44 | GET | `/api/v1/masters/genetic-lines/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 45 | DELETE | `/api/v1/masters/genetic-lines/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 46 | GET | `/api/v1/masters/breeds` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 47 | POST | `/api/v1/masters/breeds` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 48 | GET | `/api/v1/masters/breeds/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 49 | DELETE | `/api/v1/masters/breeds/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 50 | GET | `/api/v1/masters/productive-phases` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 51 | POST | `/api/v1/masters/productive-phases` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 52 | GET | `/api/v1/masters/productive-phases/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 53 | DELETE | `/api/v1/masters/productive-phases/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 54 | GET | `/api/v1/masters/suppliers` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 55 | POST | `/api/v1/masters/suppliers` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 56 | GET | `/api/v1/masters/suppliers/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 57 | DELETE | `/api/v1/masters/suppliers/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 58 | GET | `/api/v1/masters/feed-types` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 59 | POST | `/api/v1/masters/feed-types` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 60 | GET | `/api/v1/masters/feed-types/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 61 | DELETE | `/api/v1/masters/feed-types/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 62 | GET | `/api/v1/masters/vaccines` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 63 | POST | `/api/v1/masters/vaccines` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 64 | GET | `/api/v1/masters/vaccines/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 65 | DELETE | `/api/v1/masters/vaccines/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 66 | GET | `/api/v1/masters/medications` | Masters | bearer | **ninguno** | FE (formulario) | OK |
| 67 | POST | `/api/v1/masters/medications` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 68 | GET | `/api/v1/masters/medications/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 69 | DELETE | `/api/v1/masters/medications/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 70 | GET | `/api/v1/masters/mortality-causes` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 71 | POST | `/api/v1/masters/mortality-causes` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 72 | GET | `/api/v1/masters/mortality-causes/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 73 | DELETE | `/api/v1/masters/mortality-causes/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 74 | GET | `/api/v1/masters/cull-causes` | Masters | bearer | **ninguno** | FE (formulario) | OK |
| 75 | POST | `/api/v1/masters/cull-causes` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 76 | GET | `/api/v1/masters/cull-causes/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 77 | DELETE | `/api/v1/masters/cull-causes/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 78 | GET | `/api/v1/masters/transports` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 79 | POST | `/api/v1/masters/transports` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 80 | GET | `/api/v1/masters/transports/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 81 | DELETE | `/api/v1/masters/transports/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 82 | GET | `/api/v1/masters/processing-plants` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 83 | POST | `/api/v1/masters/processing-plants` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 84 | GET | `/api/v1/masters/processing-plants/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 85 | DELETE | `/api/v1/masters/processing-plants/{item_id}` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 86 | GET | `/api/v1/masters/rejection-reasons` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 87 | POST | `/api/v1/masters/rejection-reasons` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 88 | GET | `/api/v1/masters/rejection-reasons/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 89 | DELETE | `/api/v1/masters/rejection-reasons/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 90 | GET | `/api/v1/masters/correction-types` | Masters | bearer | **ninguno** | FE (formulario) | OK |
| 91 | POST | `/api/v1/masters/correction-types` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 92 | GET | `/api/v1/masters/correction-types/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 93 | DELETE | `/api/v1/masters/correction-types/{item_id}` | Masters | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 94 | GET | `/api/v1/masters/farms/{farm_id}/houses` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 95 | GET | `/api/v1/masters/hatcheries/{hatchery_id}/incubators` | Masters | bearer | **ninguno** | FE (MasterListPage) | OK |
| 96 | GET | `/api/v1/lots` | Lots | bearer | **ninguno** | FE | OK |
| 97 | POST | `/api/v1/lots` | Lots | bearer | **ninguno** | FE | unicidad de lot_code global, no por compañía |
| 98 | GET | `/api/v1/lots/{lot_id}` | Lots | bearer | **ninguno** | FE(muerto) | OK |
| 99 | PUT | `/api/v1/lots/{lot_id}` | Lots | bearer | **ninguno** | FE | OK |
| 100 | POST | `/api/v1/lots/{lot_id}/close` | Lots | bearer | **ninguno** | FE | OK |
| 101 | POST | `/api/v1/lots/activate-manual` | Lots | bearer | **ninguno** | FE | OK |
| 102 | GET | `/api/v1/lots/{lot_id}/opening-balance` | Lots | bearer | **ninguno** | FE(muerto) | OK |
| 103 | GET | `/api/v1/lots/{lot_id}/phases` | Lots | bearer | **ninguno** | FE | OK |
| 104 | POST | `/api/v1/lots/{lot_id}/phases` | Lots | bearer | **ninguno** | FE | OK |
| 105 | GET | `/api/v1/lots/{lot_id}/traceability` | Lots | bearer | **ninguno** | FE | EggBatch/ChickBatch sin filtro de compañía |
| 106 | POST | `/api/v1/lots/egg-batches` | Lots | bearer | **ninguno** | FE | OK |
| 107 | POST | `/api/v1/lots/chick-batches` | Lots | bearer | **ninguno** | FE | OK |
| 108 | GET | `/api/v1/operations/event-types` | Operations | bearer | **ninguno** | FE(muerto) | 25 etiquetas en español fijo; test espera 24 |
| 109 | GET | `/api/v1/operations` | Operations | bearer | **ninguno** | FE | OK |
| 110 | POST | `/api/v1/operations` | Operations | bearer | **ninguno** | FE | BE-01: mortality_recording → 500. FE no envía sap_document_ref ni idempotency_key |
| 111 | GET | `/api/v1/operations/{event_id}` | Operations | bearer | **ninguno** | FE | OK |
| 112 | PUT | `/api/v1/operations/{event_id}` | Operations | bearer | **ninguno** | FE(muerto) | OK |
| 113 | POST | `/api/v1/operations/{event_id}/submit` | Operations | bearer | **ninguno** | FE | OK |
| 114 | POST | `/api/v1/operations/{event_id}/cancel` | Operations | bearer | **ninguno** | FE | OK |
| 115 | GET | `/api/v1/operations/{event_id}/evidences` | Operations | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 116 | POST | `/api/v1/operations/{event_id}/evidences` | Operations | bearer | **ninguno** | FE | OK |
| 117 | GET | `/api/v1/operations/{event_id}/evidences/{evidence_id}/download` | Operations | bearer | **ninguno** | FE | OK |
| 118 | DELETE | `/api/v1/operations/{event_id}/evidences/{evidence_id}` | Operations | bearer | **ninguno** | FE | OK |
| 119 | GET | `/api/v1/operations/alerts` | Operations | bearer | **ninguno** | FE | OK |
| 120 | PATCH | `/api/v1/operations/alerts/{alert_id}/resolve` | Operations | bearer | **ninguno** | FE | OK |
| 121 | GET | `/api/v1/review/pending` | Review | bearer | **ninguno** | FE | ignora status y operator_id que envía el FE |
| 122 | POST | `/api/v1/review/batches` | Review | bearer | **ninguno** | FE | OK |
| 123 | GET | `/api/v1/review/batches` | Review | bearer | **ninguno** | FE | OK |
| 124 | POST | `/api/v1/review/start/{event_id}` | Review | bearer | **ninguno** | FE | OK |
| 125 | POST | `/api/v1/review/return` | Review | bearer | **ninguno** | FE | OK |
| 126 | POST | `/api/v1/review/complete` | Review | bearer | **ninguno** | FE | BE-05: aprueba sin validar BR-14 |
| 127 | GET | `/api/v1/approvals/pending` | Approvals | bearer | **ninguno** | FE | OK |
| 128 | POST | `/api/v1/approvals/approve` | Approvals | bearer | **ninguno** | FE | OK |
| 129 | POST | `/api/v1/approvals/reject` | Approvals | bearer | **ninguno** | FE | OK |
| 130 | POST | `/api/v1/approvals/batch-approve` | Approvals | bearer | **ninguno** | FE | OK |
| 131 | POST | `/api/v1/approvals/batch-reject` | Approvals | bearer | **ninguno** | FE | OK |
| 132 | GET | `/api/v1/approval-steps` | ApprovalSteps | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 133 | POST | `/api/v1/approval-steps` | ApprovalSteps | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 134 | PUT | `/api/v1/approval-steps/{step_id}` | ApprovalSteps | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 135 | DELETE | `/api/v1/approval-steps/{step_id}` | ApprovalSteps | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 136 | POST | `/api/v1/approval-steps/seed-defaults` | ApprovalSteps | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 137 | POST | `/api/v1/corrections` | Corrections | bearer | **ninguno** | FE | BE-02: no aplica el valor corregido |
| 138 | GET | `/api/v1/corrections` | Corrections | bearer | **ninguno** | FE(muerto) | OK |
| 139 | GET | `/api/v1/corrections/event/{event_id}` | Corrections | bearer | **ninguno** | FE | OK |
| 140 | GET | `/api/v1/audit` | Audit | bearer | **ninguno** | FE | ignora search, action_contains y group_by que envía el FE |
| 141 | GET | `/api/v1/audit/{log_id}` | Audit | bearer | **ninguno** | FE(muerto) | OK |
| 142 | GET | `/api/v1/audit/timeline/{entity_type}/{entity_id}` | Audit | bearer | **ninguno** | FE(muerto) | OK |
| 143 | GET | `/api/v1/reports/kpis` | Reports | bearer | **ninguno** | FE | OK |
| 144 | GET | `/api/v1/reports/kpis/mortality` | Reports | bearer | **ninguno** | FE | OK |
| 145 | GET | `/api/v1/reports/kpis/feed-conversion` | Reports | bearer | **ninguno** | FE | OK |
| 146 | GET | `/api/v1/reports/kpis/egg-production` | Reports | bearer | **ninguno** | FE | OK |
| 147 | GET | `/api/v1/reports/kpis/hatchery` | Reports | bearer | **ninguno** | FE | OK |
| 148 | GET | `/api/v1/reports/kpis/animal-welfare` | Reports | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 149 | GET | `/api/v1/reports/kpis/vaccination-efficiency` | Reports | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 150 | GET | `/api/v1/reports/kpis/transfer-efficiency` | Reports | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 151 | GET | `/api/v1/reports/kpis/afcr` | Reports | bearer | **ninguno** | FE | OK |
| 152 | GET | `/api/v1/reports/kpis/production-index` | Reports | bearer | **ninguno** | **HUÉRFANO** | sin consumidor |
| 153 | GET | `/api/v1/reports/kpi/ipe/{lot_id}` | Reports | bearer | **ninguno** | FE | OK |
| 154 | GET | `/api/v1/reports/kpi/weight-uniformity/{lot_id}` | Reports | bearer | **ninguno** | FE | OK |
| 155 | GET | `/api/v1/reports/lot/{lot_id}` | Reports | bearer | **ninguno** | FE | OK |
| 156 | GET | `/api/v1/reports/sap-comparison` | Reports | bearer | **ninguno** | FE | siempre vacío (sap_document_ref nunca poblado) |
| 157 | GET | `/api/v1/dashboard/mobile` | Dashboard | bearer | **ninguno** | FE | quick_actions con texto español fijo y emojis |
| 158 | GET | `/api/v1/dashboard/admin` | Dashboard | bearer | **ninguno** | FE | OK |
| 159 | POST | `/api/v1/sap/references/import` | SAP | bearer | **ninguno** | FE | OK |
| 160 | GET | `/api/v1/sap/references` | SAP | bearer | **ninguno** | FE | OK |
| 161 | POST | `/api/v1/sap/consolidate` | SAP | bearer | **ninguno** | FE | OK |
| 162 | GET | `/api/v1/sap/consolidated` | SAP | bearer | **ninguno** | FE | OK |
| 163 | POST | `/api/v1/sap/export` | SAP | bearer | **ninguno** | FE | ManualSapAdapter: archivo efímero en /tmp, doc id ficticio |
| 164 | POST | `/api/v1/sap/retry` | SAP | bearer | **ninguno** | FE | backoff (min+n)%60 puede quedar en el pasado |
| 165 | GET | `/api/v1/sap/sync/jobs` | SAP | bearer | **ninguno** | FE | OK |
| 166 | GET | `/api/v1/sap/payloads` | SAP | bearer | **ninguno** | FE | OK |
| 167 | GET | `/api/v1/sap/errors` | SAP | bearer | **ninguno** | FE | OK |
| 168 | GET | `/api/v1/sap/connection-check` | SAP | bearer | **ninguno** | FE | siempre true (adaptador manual) |

---

## Resumen del inventario

| Métrica | Valor |
|---|---|
| Operaciones totales | **168** (167 en `/api/v1` + `/health`) |
| Endpoints públicos | 3 (`/health`, `POST /login`, `POST /refresh`) |
| Endpoints autenticados | 165 |
| **Endpoints con control de permisos** | **0** |
| Consumidos por el frontend | 133 |
| Solo referenciados desde código muerto | 8 |
| Huérfanos estrictos | **34** |
| Endpoints con defecto confirmado | 14 |

### Por módulo

| Módulo | Ops | Huérfanos |
|---|---|---|
| Masters | 82 | 20 |
| Reports | 14 | 4 |
| Operations | 13 | 1 |
| Lots | 12 | 0 |
| SAP Integration | 10 | 0 |
| Review | 6 | 0 |
| Approvals | 5 | 0 |
| Approval Steps | 5 | **5 (100 %)** |
| Users | 5 | 1 |
| Auth | 4 | 0 |
| Roles | 3 | 0 |
| Corrections | 3 | 0 |
| Audit | 3 | 0 |
| Dashboard | 2 | 0 |
| Health | 1 | 0 |

### Observaciones de contrato

1. **Sin versionado de contrato.** Existe `/openapi.json` generado por FastAPI, pero **no hay ningún artefacto OpenAPI versionado en el repositorio**, ni colección Postman/Insomnia. Los documentos `specs/global-avicola/contracts/api-contract.md` y `docs/06-api-contract.md` describen una fracción de los 167 endpoints y están desactualizados (`CRITICAL_DRIFT`).
2. **Límites de paginación heterogéneos:** `le=100` en operations, lots, masters, users, review/batches, sap/sync/jobs; `le=200` en review/pending, approvals/pending, audit, corrections, operations/alerts, sap/references, sap/consolidated, sap/payloads, sap/errors. Esa heterogeneidad es la causa raíz de los seis errores 422 del frontend.
3. **Respuestas sin envoltorio uniforme:** `masters`, `lots`, `operations` y `users` devuelven listas planas (sin `total`), mientras `review`, `approvals`, `audit` y `sap` devuelven `{items, total}`. El frontend paga esa inconsistencia con paginación falsa en maestros.
4. **Sin idempotencia efectiva:** el mecanismo existe (`idempotency_key` con índice único) pero ningún cliente lo usa.
5. **Sin `PUT` en 15 de 19 maestros**, mientras el frontend ofrece "Editar" en 12 → 405 en 8 pantallas.
