# 10 — MATRIZ DE INTEGRACIÓN FRONTEND ↔ BACKEND

Método: enumeración del esquema OpenAPI instanciando la aplicación FastAPI (167 operaciones + `/health`) y extracción de todas las llamadas `api.*` del código del frontend (176 invocaciones, 99 URLs distintas normalizadas), con verificación manual de compatibilidad de parámetros y respuestas.

## 1. Resumen

```
Endpoints backend ......................... 167  (+1 /health)
Consumidos por el frontend ................ 133  (79,6 %)
Huérfanos (ningún consumidor) .............  34  (20,4 %)
Llamadas del frontend a rutas inexistentes    0
Llamadas con contrato INCOMPATIBLE ........  13
   · límite fuera de rango (HTTP 422) .....   6
   · parámetro inexistente (silencioso) ...   7
Campos del contrato nunca enviados ........   2  (sap_document_ref, idempotency_key)
```

**Ninguna pantalla llama a un endpoint que no exista.** Todos los fallos son de *forma* del contrato, no de ruta.

## 2. Matriz de acciones críticas

| Pantalla / acción | Cliente FE | Método | URL FE | Endpoint BE | Request compat. | Response compat. | Auth | Estado |
|---|---|---|---|---|---|---|---|---|
| Login | `auth.store:113` | POST | `/login` | `POST /api/v1/login` | ✔ | ✔ | público | **OK** |
| Refresh | `api.ts:39` | POST | `/refresh` | `POST /api/v1/refresh` | ✔ | ⚠ el token devuelto **pierde** `view_type`, `company_id`, `role_id` | bearer | **DEFECTUOSO (P0)** |
| Perfil actual | `auth.store:130` | GET | `/me` | `GET /api/v1/me` | ✔ | ✔ | bearer | OK |
| Cambiar compañía | `company.store:50` | POST | `/switch-company` | `POST /api/v1/switch-company` | ✔ | ✔ | bearer | OK |
| Cargar compañías (selector) | `company.store:38` | GET | `/masters/companies?limit=200` | `GET /masters/companies` (`le=100`) | ✘ **422** | — | bearer | **ROTO (P0)** |
| Listar usuarios | `UsersPage:21` | GET | `/users` + `/roles` + `/masters/companies?limit=200` en `Promise.all` | 3 endpoints | ✘ el 3.º da 422 y **aborta los tres** | — | bearer | **ROTO (P0)** |
| Crear/editar usuario | `UsersPage:32` | POST/PUT | `/users`, `/users/{id}` | ✔ | ✔ | ✔ | bearer | OK (inalcanzable: la pantalla no carga) |
| Listar lotes | `LotListPage:27` | GET | `/lots?limit=100` | `GET /lots` (`le=100`) | ✔ | ✔ | bearer | OK |
| Detalle de lote | `LotDetailPage:45` | GET | `/lots?limit=200` | `GET /lots` (`le=100`) | ✘ **422** | — | bearer | **ROTO (P0)** — aborta las 6 llamadas siguientes |
| KPIs del lote | `LotDetailPage:50` | GET | `/reports/kpis?lot_id=` | ✔ | ✔ | ✔ | bearer | inalcanzable |
| Fases del lote | `LotDetailPage:52` | GET | `/lots/{id}/phases` | ✔ | ✔ | ✔ | bearer | inalcanzable |
| Cerrar lote | `LotDetailPage:108` | POST | `/lots/{id}/close` | ✔ | ✔ | ✔ | bearer | inalcanzable |
| Transición de fase | `LotDetailPage:122` | POST | `/lots/{id}/phases` | ✔ | ✔ | ✔ | bearer | inalcanzable |
| Árbol de trazabilidad | `TraceabilityTree:124` | GET | `/lots/{id}/traceability` | ✔ | ✔ | ✔ | bearer | inalcanzable (vive en LotDetailPage) |
| Enlazar generaciones | `TraceabilityTree:86,105` | POST | `/lots/egg-batches`, `/lots/chick-batches` | ✔ | ✔ | ✔ | bearer | inalcanzable |
| Registrar operación | `OperationFormPage:415` | POST | `/operations` | `POST /api/v1/operations` | ⚠ **no envía `sap_document_ref` ni `idempotency_key`**; envía campos de UI que el backend ignora (`house_inspections`) | ✔ | bearer | **INCOMPLETO (P0)** |
| Registrar mortalidad | idem | POST | `/operations` | idem | ✔ | ✘ **HTTP 500** (`NameError` en el generador de alertas) | bearer | **ROTO (P0)** |
| Catálogos del formulario (14) | `OperationFormPage:317-330` | GET | `/masters/*?limit=100` | `le=100` | ✔ | ✔ | bearer | OK |
| Órdenes SAP del formulario | `OperationFormPage:314-315` | GET | `/sap/references?ref_type=…&limit=50` | `le=200` | ✔ | ✔ | bearer | OK |
| Listar operaciones | `OperationListPage:26` | GET | `/operations?limit=100` | `le=100` | ✔ | ✔ | bearer | OK |
| Mis pendientes | `MyPendingPage:33` | GET | `/operations?registered_by_me=true&status=draft,registered` | `GET /operations` | ✘ `registered_by_me` **no existe**; `status="draft,registered"` no es un valor del enum → error de conversión | ✘ | bearer | **ROTO (P0)** |
| Detalle de operación | `OperationDetailPage:54` | GET | `/operations/{id}` | ✔ | ✔ | ✔ | bearer | OK |
| Subir evidencia | `OperationDetailPage:80` | POST | `/operations/{id}/evidences` (multipart) | ✔ | ✔ | ✔ | bearer | ⚠ Nginx sin `client_max_body_size` → 413 por encima de 1 MB |
| Bandeja de revisión | `ReviewCenter:94` | GET | `/review/pending?limit&offset&status&operator_id&…` | `GET /review/pending` | ⚠ `status` y `operator_id` **no existen** → se ignoran | ✔ | bearer | **DEFECTUOSO (P1)** |
| Detalle de revisión | `ReviewDetail:32` | GET | `/operations?limit=200` | `le=100` | ✘ **422** | — | bearer | **ROTO (P0)** |
| Correcciones del evento | `ReviewDetail:38` | GET | `/corrections/event/{id}` | ✔ | ✔ | ✔ | bearer | OK |
| Registrar corrección | `CorrectionForm:50` | POST | `/corrections` | ✔ | ✔ | ⚠ el backend **no aplica el valor** | bearer | **DEFECTUOSO (P0)** |
| Cargar evento a corregir | `CorrectionForm:27` | GET | `/operations?limit=200` | `le=100` | ✘ **422** | — | bearer | **ROTO (P0)** |
| Aprobar / rechazar | `ApprovalPanel:52,68` | POST | `/approvals/approve`, `/reject` | ✔ | ✔ | ✔ | bearer | OK |
| Aprobar / rechazar masivo | `ApprovalPanel:98,117` | POST | `/approvals/batch-approve`, `/batch-reject` | ✔ | ✔ | ✔ | bearer | OK |
| Completar revisión | `ReviewCenter:126` | POST | `/review/complete` | ✔ | ✔ | ⚠ aprueba **sin validar BR-14** | bearer | **DEFECTUOSO (P0)** |
| Auditoría | `AuditPage:44-51` | GET | `/audit?limit=50&search&action_contains&group_by` | `GET /audit` | ⚠ `search`, `action_contains`, `group_by` **no existen** | ✔ | bearer | **DEFECTUOSO (P1)** |
| Maestros: listar | `MasterListPage:41` | GET | `/masters/{e}` | ✔ | ✔ | ⚠ lista plana sin total → paginación falsa | bearer | DEFECTUOSO (P2) |
| Maestros: crear | `MasterListPage:81` | POST | `/masters/{e}` | ✔ | ✔ | ✔ | bearer | OK |
| Maestros: editar | `MasterListPage:79` | PUT | `/masters/{e}/{id}` | **solo existe** para companies, farms, houses, hatcheries | ✘ **405** en las otras 8 pantallas | — | bearer | **ROTO (P1)** |
| Maestros: borrar | `MasterListPage:97` | DELETE | `/masters/{e}/{id}` | ✔ | ✔ | ✔ | bearer | OK |
| Reportes: KPIs | `ReportsPage:19` | GET | `/reports/kpis?lot_id=` | ✔ | ✔ | ✔ | bearer | OK |
| Reportes: gráficas | `ReportsPage:20` | GET | `/operations?lot_id=&limit=200` | `le=100` | ✘ **422** | — | bearer | **ROTO (P1)** |
| Comparativo SAP | `SapComparisonPage:14` | GET | `/reports/sap-comparison` | ✔ | ✔ | ⚠ filtra `sap_document_ref != NULL`, que el FE nunca puebla → **siempre vacío** | bearer | **DEFECTUOSO (P1)** |
| SAP: consolidar / exportar | `SapManagerPage:51,60` | POST | `/sap/consolidate`, `/sap/export` | ✔ | ✔ | ⚠ el "envío" escribe un archivo efímero | bearer | DEFECTUOSO (P0) |
| Dashboard | `DashboardPage:91` | GET | `/dashboard/mobile` \| `/admin` | ✔ | ✔ | ⚠ `quick_actions` con texto español fijo y emojis | bearer | DEFECTUOSO (P3) |

## 3. Endpoints huérfanos (34)

Sin ninguna ruta de código en el frontend.

**Configuración de aprobación multinivel (5)** — la funcionalidad diferenciadora del producto (`docs/00 §6.2`) no tiene interfaz:
`GET /approval-steps` · `POST /approval-steps` · `PUT /approval-steps/{id}` · `DELETE /approval-steps/{id}` · `POST /approval-steps/seed-defaults`

**KPIs sin consumidor (4):**
`GET /reports/kpis/animal-welfare` · `/production-index` · `/transfer-efficiency` · `/vaccination-efficiency`

**Maestros sin pantalla (20):** CRUD completo de `productive-phases` y `rejection-reasons` (4+4) y las operaciones de escritura/lectura individual de `medications`, `cull-causes`, `incubators`, `hatchers`, `correction-types` (POST/GET-by-id/DELETE ×5 = 15, de los cuales 12 son huérfanos estrictos).

**Otros (5):** `GET /users/{id}` · `GET /operations/{id}/evidences` (el frontend lee las evidencias del detalle del evento).

**Nota:** otros 8 endpoints solo aparecen referenciados desde los módulos `services/*.service.ts` **muertos** (`GET /audit/{id}`, `GET /audit/timeline/...`, `GET /corrections`, `GET /lots/{id}`, `GET /lots/{id}/opening-balance`, `PUT /operations/{id}`, `GET /operations/event-types`, `GET /masters/{e}/{id}`). Son alcanzables en teoría e inalcanzables en la práctica.

## 4. Criterio E2E (§21) aplicado a las acciones transaccionales

| Acción | UI | Validación | Request | API | Auth | Regla | Persistencia | Respuesta | Refresco UI | Error | E2E |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Registrar alimento | ✔ | ✔ zod | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ toast | **✅** |
| Registrar pesaje | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **✅** |
| Registrar mortalidad | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ 500 | ✘ | ⚠ toast genérico | **❌** |
| Recolectar huevos | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **✅** |
| Despachar huevos | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ BR-02 | ✔ | ✔ | ✔ | ✔ | **✅** |
| Enviar a revisión | ✔ | — | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **✅** |
| Devolver al operador | ✔ | ✔ obs. obligatoria | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **✅** |
| Corregir un valor | ✘ pantalla no carga | ✔ motivo ≥5 | ✔ | ✔ | ✔ | ✔ | ⚠ solo el log | ✔ | ✔ | ✔ | **❌** |
| Aprobar | ✔ | — | ✔ | ✔ | ✔ | ✔ BR-14 | ✔ | ✔ | ✔ | ✔ | **✅** |
| Rechazar | ✔ | ✔ motivo | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **✅** |
| Consolidar para SAP | ✔ | — | ✔ | ✔ | ✔ | ✔ BR-13 | ✔ | ✔ | ✔ | ✔ | **✅** |
| Exportar a SAP | ✔ | — | ✔ | ✔ | ✔ | ✔ BR-12 | ⚠ archivo efímero | ✔ | ✔ | ✔ | **⚠** |
| Cerrar lote | ✘ pantalla rota | — | ✔ | ✔ | ✔ | ✔ BR-05 | ✔ | ✔ | ✔ | ✔ | **❌** |
| Transición de fase | ✘ pantalla rota | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **❌** |
| Crear lote | ✔ | ✔ | ✔ | ✔ | ✔ | ⚠ unicidad global | ✔ | ✔ | ✔ | ✔ | **✅** |
| Crear usuario | ✘ pantalla rota | ✔ | ✔ | ✔ | ⚠ sin RBAC | — | ✔ | ✔ | ✔ | ✔ | **❌** |
| Editar maestro | ✔ | ✔ | ✔ | ✘ 405 en 8/12 | ✔ | — | ✘ | ✘ | ✘ | ✔ | **❌** |
| Subir evidencia | ✔ | ✔ tipo+tamaño | ✔ | ✔ | ✔ | ✔ | ⚠ efímera / 413 >1 MB | ✔ | ✔ | ✔ | **⚠** |
