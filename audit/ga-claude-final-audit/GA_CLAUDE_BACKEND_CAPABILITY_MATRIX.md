# GA · AUDITORÍA FINAL INDEPENDIENTE PRE-SAP (CLAUDE) · MATRIZ DE CAPACIDADES DEL BACKEND

**Fecha** 2026-09-13 · **Repositorio** `/home/maria/Proyectos/GlobalAvicola` · **HEAD** `c0b4afc` (`main`) · **Runtime** `https://avicola.globaldv.net` · **Modo** solo lectura.

## 0 · Fuentes y método

| Fuente | Uso |
|---|---|
| `backend_routes.json` de esta auditoría (volcado de la tabla de rutas de la app FastAPI: 212 rutas = 211 API + `/health`; las 10 de SAP solo con `FEATURE_SAP_ENABLED`, `main.py:146-147,167-168`) | Inventario canónico (coincide con el guardián «rutas 211» de `GA-REM-041 §5:191`) |
| `backend/app/*/router.py`, `authorization_coverage.py:21-59`, `business_units/route_scope.py:44-196` | Permiso, exenciones y alcance BU declarado |
| Informe A de esta auditoría (traza FE↔BE, partes 1, 4 y 5) | Consumidor de frontend por ruta, huérfanos |
| Informes B y C (contratos de petición/respuesta), D (seguridad `GAP-nn`), F (`G-nn`) | Brechas que condicionan la clasificación |
| `backend/tests/**` (104 ficheros): grep de la ruta literal (sin placeholders) y, para rutas con placeholder intermedio, del sufijo de segmento; contraste con las citas del informe D | Columna «Tests» — se nombran ficheros, no funciones, salvo cuando el informe D los individualiza |
| Suite en HEAD: **1201 ✔ / 25 ✘ / 49 omitidos** — fallos deterministas reproducidos en aislamiento: 14 tests desfasados frente a la frontera de lectura OD-16 (esperan 403; hoy 404), 5 de R-188 por `GET /me` 500 con correos de fixture con TLD reservado `.test` rechazados por `EmailStr`, 3 guardas desfasadas (cabeza alembic `y5z6a7b8c9d0`, fechas literales). Logs en `audit/ga-claude-final-audit/evidence/` (`backend_full_suite.log`, `backend_targeted_failing.log`, `backend_r188_me500.log`) | Estado de certificación automatizada |
| Evidencia runtime: `runtime_gp_e2e.log` **[RT]** y `ui_e2e_local.log` **[LOC]** en `audit/ga-claude-final-audit/evidence/` | Ejercicio real de rutas |

## 1 · Leyendas

- **Permiso**: `módulo:acción` de `require_permission`; `PUBLICA` (exenta, `authorization_coverage.py:21-29`); `titular` (solo sesión, `:42-59`).
- **Alcance BU** (`route_scope.py`): `PUBLICA` · `CORE` · `CONTROL` · `MULTI_UNIDAD` · `UNIDAD_UNICA` · `CONTRATO`. Nota del informe D §0: la clasificación es declarativa — `unidad_requerida()` (`route_scope.py:215-217`) no la invoca ninguna ruta; el acotamiento real lo hacen los servicios.
- **Consumidor FE**: componente:línea que llama la ruta en producción (excluidos `hooks/*` y `services/*` sin importadores, informe A §2).
- **Estado huérfano**: `CONSUMIDA` · `CONSUMIDA_CON_BRECHA` (hay llamador pero el contrato/estado no cuadra) · `BACKEND_ORPHAN` (sin llamador y es funcionalidad de usuario) · `PROMISED_ZERO_CALLER` (existe método en `services/*.ts` que nadie llama; se combina con el anterior) · `API_ONLY_BY_DESIGN` · `INTERNAL_ONLY` · `DEFERRED_BY_OWNER` (RES-02 / RES-04).
- **¿Req. pre-SAP?**: `Sí` / `No` / `Diferida` (decisión del propietario) / `P-08` (depende de SAP real).
- **Clasificación**: `CERTIFIED` = cubierta por tests de backend y, si es de usuario, consumida con paridad de contrato sin brecha material · `PARTIAL` = consumida con brecha de contrato/estado/feedback, o sin test directo, o con hueco de seguridad registrado · `MISSING` = requerida por el producto y sin consumidor (huérfana real) · `UNKNOWN` = sin test directo, sin ejercicio runtime y sin consumidor verificable.
- Códigos: `INT-nn` (registro de brechas de integración en `GA_CLAUDE_FRONTEND_BACKEND_INTEGRATION_MATRIX.md` §6), `B-nn` / `C#n` / `G-nn` / `GAP-nn` (informes compañeros), `R-nnn` / `GA-REM-nnn` / `OD-nn` (hallazgos y decisiones ya registrados).

## 2 · Conteos globales del inventario

| Módulo | Rutas | Sin `response_model` | Permiso `require_permission` | Solo sesión | Públicas |
|---|---|---|---|---|---|
| auth (`/login`, `/refresh`, `/me`, `/switch-company`) | 4 | 0 | 0 | 2 | 2 |
| users + roles (+3 de unidades por usuario) | 13 | 3 | 12 | 1 | 0 |
| business-units | 4 | 0 | 4 | 0 | 0 |
| notifications | 4 | 0 | 0 | 4 | 0 |
| lots | 12 | 0 | 12 | 0 | 0 |
| operations | 17 | 3 | 16 | 0 | 1 (`event-types`, de facto) |
| review | 6 | 5 | 6 | 0 | 0 |
| approvals | 5 | 5 | 5 | 0 | 0 |
| approval-steps | 5 | 3 | 5 | 0 | 0 |
| corrections | 3 | 1 | 3 | 0 | 0 |
| reversals | 3 | 0 | 3 | 0 | 0 |
| audit | 3 | 2 | 3 | 0 | 0 |
| reports | 14 | 14 | 14 | 0 | 0 |
| dashboard | 2 | 2 | 2 | 0 | 0 |
| sap | 10 | 9 | 10 | 0 | 0 |
| masters (20 entidades × 5 + 6 especiales) | 106 | 20 (los `DELETE` 204) | 106 | 0 | 0 |
| health | 1 | 1 | 0 | 0 | 1 |
| **Total** | **212** | **68** | **201** | **7** | **4** |

`GET /operations/event-types` figura en `RUTAS_DE_TITULAR` (`authorization_coverage.py:45`) pero no declara dependencia de sesión (`operations/router.py:33-35`): es anónima de facto (informe A, hallazgo 12).

## 3 · Matriz por módulo

Columnas: **Método · Ruta** · **Permiso** · **Alcance** · **response_model** · **Consumidor FE** · **Huérfano** · **¿Req.?** · **Tests (`backend/tests/`)** · **Clasificación** · **Nota**.

### 3.1 · Autenticación y sesión — `auth/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| POST `/login` (`:29-32`) | PUBLICA (rate 5/min) | PUBLICA | `TokenResponse` | `auth.store.ts:126` (LoginPage) | CONSUMIDA (`authService.login` duplicado sin uso) | Sí | `test_auth.py`, `test_audit_coverage.py`, `test_security_regression.py` (14 ficheros) | CERTIFIED | [RT]/[LOC] login por UI 200. Rate limit por IP tras proxy sin `--forwarded-allow-ips` (`GAP-11`). |
| POST `/refresh` (`:35-37`) | PUBLICA | PUBLICA | `TokenResponse` | `api.ts:37` (interceptor 401) | CONSUMIDA (interno) | Sí | `test_security_regression.py`, `test_rbac.py`, `test_multicompany_isolation.py` | CERTIFIED | Sin rotación ni logout (`GA-REM-003`, `GAP-09`); el refresh sirve como Bearer (`GAP-03`). |
| GET `/me` (`:40-84`) | titular | CORE | `SessionRead` | `auth.store.ts:143` | CONSUMIDA | Sí | `test_session_payload.py`, `test_auth.py`, `test_grandparent_import.py` (13) | PARTIAL | 200 en runtime [RT me-op]; **500** cuando el correo del usuario tiene TLD reservado (`EmailStr`): 5 tests R-188 rojos en HEAD (`backend_r188_me500.log`). |
| POST `/switch-company` (`:87-94`) | titular (servicio exige autoridad global) | CORE | `TokenResponse` | `company.store.ts:51` (Header) | CONSUMIDA | Sí | `test_multicompany_isolation.py`, `test_lot_closure.py` (11) | PARTIAL | Backend correcto (D D.8); el frontend no captura el rechazo (C#20, INT-28). |

### 3.2 · Usuarios y roles — `auth/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/users` (`:99-107`) | `users:read` | CONTROL | `list[UserRead]` | `UsersPage.tsx:40` (sin `limit` → 20), `ReviewCenter.tsx:109` | CONSUMIDA_CON_BRECHA | Sí | `test_user_tenant_isolation.py`, `test_access_administration.py`, `test_od14_productive_surfaces.py` (18) | PARTIAL | Paginación no expuesta en UI (INT-31); 403 para aprobador desde ReviewCenter [RT]. |
| POST `/users` (`:110-116`) | `users:create` | CONTROL | `UserRead` 201 | `UsersPage.tsx:83` | CONSUMIDA | Sí | `test_user_tenant_isolation.py` (R-118), `test_auth.py`, `test_role_tenancy.py` | CERTIFIED | `last_name` obligatorio solo en BE (B-28, P3). |
| GET `/users/{user_id}` (`:119-125`) | `users:read` | CONTROL | `UserRead` | ninguno | API_ONLY_BY_DESIGN | No | `test_access_administration.py`, `test_p013_password.py`, `test_r188_bu_lifecycle.py` (9) | CERTIFIED | — |
| PUT `/users/{user_id}` (`:128-135`) | `users:update` | CONTROL | `UserRead` | `UsersPage.tsx:79` (edición → 422), `:91` (toggle ✔) | CONSUMIDA_CON_BRECHA | Sí | `test_user_tenant_isolation.py`, `test_role_tenancy.py`, `test_areas.py`, `test_access_administration.py` (6) | PARTIAL | `UserUpdate` `extra="forbid"` sin `username`/`company_id` (`auth/schemas.py:74-85`) vs modal que los envía → INT-02 (B-06). |
| POST `/users/{user_id}/password` (`:138-150`) | titular / administrador | CONTROL | 204 | `ProfilePage.tsx:29` (titular); `UsersPage.tsx:80` (admin, inalcanzable por INT-02) | CONSUMIDA / CONSUMIDA_CON_BRECHA | Sí | `test_p013_password.py` (`test_t012_01…08`) | PARTIAL | Restablecimiento solo para `is_super_admin` **sin contexto de empresa**; `users:update` no basta (`auth/service.py:443-455`, `GAP-04`). |
| DELETE `/users/{user_id}` (`:153-159`) | `users:delete` | CONTROL | 204 | `UsersPage.tsx:88` | CONSUMIDA | Sí | `test_access_administration.py`, `test_user_tenant_isolation.py`, `test_business_unit_admin.py` | CERTIFIED | Baja lógica. |
| GET `/roles/permissions-catalog` (`:164-174`) | `users:read` | CONTROL | — (dict) | `RolesPage.tsx:38` | CONSUMIDA | Sí | `test_role_administration.py`, `test_role_tenancy.py` | CERTIFIED | Enumerados sin i18n en UI (`G-08`). |
| GET `/roles` (`:177-182`) | `users:read` | CONTROL | `list[RoleRead]` | `RolesPage.tsx:37`, `UsersPage.tsx:55` | CONSUMIDA | Sí | `test_role_administration.py`, `test_role_tenancy.py`, `test_auth.py` (9) | CERTIFIED | — |
| POST `/roles` (`:185-191`) | `users:create` | CONTROL | `RoleRead` 201 | `RolesPage.tsx:81` | CONSUMIDA | Sí | `test_role_administration.py` | PARTIAL | **`GAP-01` (P1)**: `permissions` sin validar → rol de inquilino con `("*", all)` fabrica autoridad global (`auth/service.py:585-619`, `security.py:119-120`); sin test del camino. |
| PUT `/roles/{role_id}` (`:194-201`) | `users:update` | CONTROL | `RoleRead` | `RolesPage.tsx:80,94` | CONSUMIDA | Sí | `test_role_administration.py`, `test_role_tenancy.py` | PARTIAL | `GAP-01` (`:621-658`). No existe `DELETE /roles/{id}` (coherente con la UI: desactivación por `is_active`). |
| GET `/users/{id}/business-units` (`business_units/router.py:167-184`) | `business_units:read` | CONTROL | `list[ConcesionRead]` | `UserBusinessUnitsButton.tsx:58` | CONSUMIDA | Sí | `test_r188_bu_lifecycle.py`, `test_business_unit_admin.py`, `test_access_administration.py` (8) | CERTIFIED | Contrato GA-FE-02 exacto (`businessUnits.service.ts:16-23`). |
| POST `/users/{id}/business-units` (`:187-207`) | `business_units:create` | CONTROL | `ConcesionRead` 201 | `UnitAccessPage.tsx:135`, `UserBusinessUnitsButton.tsx:82` | CONSUMIDA | Sí | `test_r188_bu_lifecycle.py` (`self_grant_denegado`, `cross_company_denegado`), `test_grant_candidates.py` | CERTIFIED | OD-15.a en servidor (`admin.py:348-350`). |
| DELETE `/users/{id}/business-units/{code}` (`:210-229`) | `business_units:delete` | CONTROL | `ConcesionRead` | `UnitAccessPage.tsx:150`, `UserBusinessUnitsButton.tsx:96` | CONSUMIDA | Sí | `test_r188_bu_lifecycle.py`, `test_business_unit_admin.py` (7) | CERTIFIED | UAT-08 (revoke→regrant). |

### 3.3 · Unidades de negocio (plano de control) — `business_units/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/business-units` (`:94-101`) | `business_units:read` | CONTROL | `list[HabilitacionRead]` | `UnitAccessPage.tsx:54`, `UserBusinessUnitsButton.tsx:57` | CONSUMIDA | Sí | `test_business_unit_admin.py`, `test_access_administration.py`, `test_od16_global_read_boundary.py` (8) | CERTIFIED | Fail-closed sin empresa efectiva. |
| PATCH `/business-units/{code}/enable` (`:104-121`) | `business_units:update` | CONTROL | `HabilitacionRead` | `UnitAccessPage.tsx:120` | CONSUMIDA | Sí | `test_r188_bu_lifecycle.py`, `test_business_unit_admin.py`, `test_access_administration.py` | CERTIFIED | No revive concesiones (D C.2). |
| PATCH `/business-units/{code}/disable` (`:124-143`) | `business_units:update` | CONTROL | `HabilitacionRead` | `UnitAccessPage.tsx:121` | CONSUMIDA | Sí | `test_r188_bu_lifecycle.py`, `test_od16_global_read_boundary.py`, `test_lots_bu_enforcement.py` (6) | CERTIFIED | OD-23: termina concesiones vivas con auditoría por concesión (`admin.py:178-214`). |
| GET `/business-units/{code}/grant-candidates` (`:146-162`) | `business_units:create` | CONTROL | `list[CandidatoRead]` | `UnitAccessPage.tsx:86` | CONSUMIDA | Sí | `test_grant_candidates.py`, `test_business_unit_admin.py` | CERTIFIED | 409 con unidad apagada (la UI lo evita, `UnitAccessPage.tsx:101`). |

### 3.4 · Notificaciones — `notifications/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/notifications` (`:26-43`) | titular | CORE | `list[NotificationRead]` + `X-Total-Count` | `NotificationBell.tsx:76` | CONSUMIDA | Sí | `test_notifications.py`, `test_notification_recipients.py` | CERTIFIED | La UI solo compone texto para 2 de 6 tipos (C#32). |
| GET `/notifications/unread-count` (`:46-52`) | titular | CORE | `UnreadCountRead` | `NotificationBell.tsx:45` (sondeo 60 s) | CONSUMIDA | Sí | `test_notifications.py` | CERTIFIED | `unread:1` tras devolución [RT R-05]. |
| GET `/notifications/{id}` (`:55-66`) | titular | CORE | `NotificationRead` | ninguno | API_ONLY_BY_DESIGN | No | `test_notifications.py` | CERTIFIED | 404 a terceros. |
| PATCH `/notifications/{id}/read` (`:69-80`) | titular | CORE | `NotificationRead` | `NotificationBell.tsx:90` | CONSUMIDA | Sí | `test_notifications.py` | CERTIFIED | — |

### 3.5 · Lotes — `lots/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/lots` (`:23-36`) | `lots:read` | MULTI_UNIDAD | `list[LotRead]` | `LotListPage.tsx:29`, `OperationFormPage.tsx:343` | CONSUMIDA_CON_BRECHA | Sí | `test_lot_row_scope.py`, `test_lots_bu_enforcement.py`, `test_multicompany_isolation.py` (37) | PARTIAL | `total` descartado por el router; la UI pide 100 y filtra en cliente (C#33, INT-31). |
| POST `/lots` (`:39-46`) | `lots:create` | MULTI_UNIDAD | `LotRead` 201 | `LotFormPage.tsx:133` | CONSUMIDA_CON_BRECHA | Sí | `test_lot_area_ownership.py`, `test_lot_start_date.py`, `test_lots_bu_enforcement.py`, `test_lot_row_scope.py` | PARTIAL | `sap_reference` enviado y descartado en silencio (B-18, INT-27); `house_id`/`genetic_line_id`/`weight_curve_id` sin verificar pertenencia (`GAP-06`, `lots/service.py:362-392`). 201 por UI [LOC BR-00, HAT-00]. |
| GET `/lots/{lot_id}` (`:49-66`) | `lots:read` | MULTI_UNIDAD | `LotDetailRead` (+`phases`, `opening_balance`) | `LotDetailPage.tsx:49` | CONSUMIDA_CON_BRECHA | Sí | `test_lot_row_scope.py`, `test_multicompany_isolation.py` (`test_idor_*`) | PARTIAL | `opening_balance` ignorado por la UI; `LotPhaseRead` sin `phase` anidado (`lots/schemas.py:112-116`) → etapa irresoluble en UI (INT-18). |
| PUT `/lots/{lot_id}` (`:69-77`) | `lots:update` | MULTI_UNIDAD | `LotRead` | **ninguno** (`lots.service.ts:48-49`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí (`GA-REM-040:1440,1612`) | `test_lot_planned_close.py`, `test_lot_area_eligibility.py`, `test_lot_area_ownership.py`, `test_security_regression.py` (8) | MISSING | INT-10. `LotUpdate` (`schemas.py:50-74`) admite `house_id`/`genetic_line_id` sin verificar (`GAP-06`). |
| POST `/lots/{lot_id}/close` (`:80-92`) | `lots:create` | MULTI_UNIDAD | `LotClosureSummary` | `LotDetailPage.tsx:111` | CONSUMIDA_CON_BRECHA | Sí | `test_lot_closure.py`, `test_lot_close_approval.py`, `test_lots_bu_enforcement.py`, `test_lot_start_date.py` | PARTIAL | 400 BR-05 con pendientes [LOC BO-close]; la UI solo `console.error` (INT-19). |
| POST `/lots/activate-manual` (`:99-106`) | `lots:create` | MULTI_UNIDAD («P-11, las cuatro» `route_scope.py:116`) | `OpeningBalanceRead` 201 | **ninguno** (`lots.service.ts:54-55`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí (P-11: `GA-REM-005:390`, `GA-REM-028:7,39,82`) | `test_opening_balance.py`, `test_lot_start_date.py`, `test_lot_row_scope.py`, `test_lots_bu_enforcement.py`, `test_od14_productive_surfaces.py` | MISSING | INT-10. No figura en la matriz de 38 de DeepSeek. |
| GET `/lots/{lot_id}/opening-balance` (`:109-119`) | `lots:read` | MULTI_UNIDAD | `OpeningBalanceRead` | **ninguno** (`lots.service.ts:63-64`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Parcial (el dato viaja en `LotDetailRead` y en `/reports/lot/{id}`) | `test_lot_row_scope.py` | MISSING (bajo) | INT-18. |
| GET `/lots/{lot_id}/phases` (`:126-133`) | `lots:read` | MULTI_UNIDAD | `list[LotPhaseRead]` | `LotDetailPage.tsx:55,131` | CONSUMIDA_CON_BRECHA | Sí | `test_lot_row_scope.py`, `test_lots_bu_enforcement.py` | PARTIAL | Redundante con `LotDetailRead.phases`; sin `phase.name`/`code` la UI no puede resolver la etapa (INT-18). |
| POST `/lots/{lot_id}/phases` (`:136-147`) | `lots:create` | MULTI_UNIDAD | `LotPhaseRead` 201 | `LotDetailPage.tsx:125` (payload `{phase_code,…}`) | CONSUMIDA_CON_BRECHA | Sí | `test_lot_row_scope.py`, `test_lots_bu_enforcement.py` | PARTIAL | `LotPhaseCreate` exige `lot_id` y `phase_id` (`schemas.py:98-105`) → **422 siempre desde UI** [RT R-09] (INT-01). Además `productive-phases` no expone `phase_id` a la UI de forma usable. |
| GET `/lots/{lot_id}/traceability` (`:154-200`) | `lots:read` | CONTRATO | `TraceabilityNode` | `TraceabilityTree.tsx:124` | CONSUMIDA | Sí | `test_traceability.py`, `test_reception_lineage.py`, `test_handoff_contract.py`, `test_lineage_cancel_move.py`, `test_traceability_ownership.py` | CERTIFIED | R-178 (`_vinculos_efectivos`). |
| POST `/lots/egg-batches` (`:239-268`) | `lots:create` | CONTRATO | `EggBatchRead` 201 | `TraceabilityTree.tsx:91` | CONSUMIDA_CON_BRECHA | Sí (OD-10.b; secundario al vínculo automático `operations/service.py:433-541`) | `test_handoff_contract.py`, `test_traceability.py`, `test_traceability_ownership.py`, `test_lineage_cancel_move.py` | PARTIAL | `hatchery_lot_id: int` requerido vs `null` de la UI (B-17); botones ocultos hasta el primer vínculo (INT-23). |
| POST `/lots/chick-batches` (`:271-300`) | `lots:create` | CONTRATO | `ChickBatchRead` 201 | `TraceabilityTree.tsx:110` | CONSUMIDA_CON_BRECHA | Sí | `test_traceability_ownership.py` | PARTIAL | Ídem (INT-23). |

### 3.6 · Operaciones — `operations/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/operations/event-types` (`:33-35`) | **ninguno** (anónima de facto; listada como titular en `authorization_coverage.py:45`) | CORE | — | ninguno (catálogo duplicado en `processCatalog.ts:205-268`; `operationsService.getEventTypes` sin uso) | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No | `test_operations.py`, `test_mortality.py`, `test_full_workflow_audit.py` | PARTIAL | Superficie anónima no declarada en `RUTAS_PUBLICAS` (A hallazgo 12); `ALL_EVENT_TYPES` omite `water_consumption` (B-24). |
| GET `/operations` (`:42-67`) | `operations:read` | MULTI_UNIDAD | `list[OperationalEventRead]` | `OperationListPage.tsx:33`, `LotDetailPage.tsx:54`, `MyPendingPage.tsx:34`, `ReportsPage.tsx:33` | CONSUMIDA_CON_BRECHA | Sí | `test_operations.py`, `test_od14_productive_surfaces.py`, `test_operations_bu_enforcement.py` (54) | PARTIAL | La lista no incluye sublistas (`schemas.py:256-266`) y las pantallas las esperan (C#4, INT-18/INT-17); `total` descartado. |
| POST `/operations` (`:70-77`) | `operations:create` | MULTI_UNIDAD | `OperationalEventRead` 201 | `OperationFormPage.tsx:452` | CONSUMIDA (26 tipos) | Sí | `test_operations.py`, `test_reception_reconciliation.py`, `test_grandparent_import.py`, `test_f01d_filas_vacias.py` (11/11), `test_operations_bu_enforcement.py`, `test_population_invariant.py`, `test_water_capture.py`, `test_birth_classification.py`… | PARTIAL | Backend certificado; la paridad por tipo tiene brechas del cliente: INT-04 (BR-08 galpón/granja), INT-05 (incubadora), INT-06 (BR-20), INT-11, INT-12, INT-13, INT-26. Runtime: 9 tipos 201 [RT/LOC], 4 tipos 400 BR-08 [RT]. `idempotency_key` nunca enviado (`R-146`). |
| GET `/operations/alerts` (`:86-98`) | `operations:read` | MULTI_UNIDAD | `list[OperationalAlertRead]` | `LotDetailPage.tsx:58`, `DashboardPage.tsx:98` | CONSUMIDA | Sí | `test_mortality.py`, `test_weight_evaluation_endpoint.py`, `test_operations_bu_enforcement.py`, `test_od14_productive_surfaces.py` | CERTIFIED | Acotada por unidad (`service.py:997-1009`). |
| PATCH `/operations/alerts/{id}/resolve` (`:101-108`) | `operations:update` | MULTI_UNIDAD | `OperationalAlertRead` | `LotDetailPage.tsx:77`, `DashboardPage.tsx:110` | CONSUMIDA | Sí | `test_operations_bu_enforcement.py` | CERTIFIED | — |
| GET `/operations/pending-classification` (`:118-144`) | `operations:read` | CONTROL | `list[OperationalEventRead]` | ninguno | DEFERRED_BY_OWNER (RES-02) | Diferida | `test_pending_classification.py`, `test_r153_import_lot_auto.py` | PARTIAL | `skip` sin `ge=0` → 500 (`GAP-16`); registros sin cadena invisibles en toda la UI. |
| POST `/operations/{id}/classify` (`:147-193`) | `masters:update` | CONTROL | `OperationalEventRead` | ninguno | DEFERRED_BY_OWNER | Diferida | `test_pending_classification.py` | CERTIFIED (API) | Sin UI por decisión T-040-24. |
| POST `/operations/{id}/reclassify` (`:196-244`) | `corrections:correct` | CONTROL | `OperationalEventRead` | ninguno | DEFERRED_BY_OWNER | Diferida | `test_pending_classification.py` | CERTIFIED (API) | 409 si tuvo efectos. |
| GET `/operations/{id}/weight-evaluation` (`:247-266`) | `operations:read` | MULTI_UNIDAD | `WeightEvaluationRead` | `WeightEvaluation.tsx:50` | CONSUMIDA | Sí | `test_weight_evaluation_endpoint.py`, `test_reception_weight_range.py` | CERTIFIED | `reason` no mostrado (C#28, P3); curva de otra empresa podría exponerse (`GAP-06`). |
| GET `/operations/{id}` (`:269-292`) | `operations:read` | MULTI_UNIDAD | `OperationalEventDetailRead` | `OperationDetailPage.tsx:64`, `ReviewDetail.tsx:35`, `CorrectionForm.tsx:30` | CONSUMIDA_CON_BRECHA | Sí | `test_operations.py`, `test_corrections.py`, `test_edit_validation_parity.py` (54) | PARTIAL | El router hace `pop("evidences")`/`pop("egg_storage_records")` y **no los reasigna** (`router.py:282-291`) aunque el esquema los declara (`schemas.py:298-305`) → siempre `[]` (INT-08, C#1). |
| PUT `/operations/{id}` (`:295-303`) | `operations:update` | MULTI_UNIDAD | `OperationalEventRead` | **ninguno** (`operations.service.ts:40-41`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí (`GA-REM-023:80,115`, `GA-REM-042:38,51`, OD-17) | `test_edit_validation_parity.py`, `test_edit_cancel_balance.py`, `test_p014_persistence.py`, `test_master_reference_tenancy.py` (14) | MISSING | INT-09. `EDITABLES` incluye `returned/rejected` (`service.py:73-74`); `H7 {editar:0}` [LOC]. |
| POST `/operations/{id}/submit` (`:310-317`) | `operations:create` | MULTI_UNIDAD | `OperationalEventRead` | `OperationDetailPage.tsx:132` (`operationsService.submit`) | CONSUMIDA | Sí | `test_operations_bu_enforcement.py`, `test_notifications.py`, `test_full_workflow_audit.py`, `test_state_continuity.py` (12) | CERTIFIED | [RT R-05/R-06/R-11] 200; GA-FE-05/UAT-03. |
| POST `/operations/{id}/cancel` (`:320-327`) | `operations:create` | MULTI_UNIDAD | `OperationalEventRead` | **ninguno** (`operations.service.ts:46-47`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí (`GA-REM-042:51`) | `test_edit_cancel_balance.py`, `test_lineage_cancel_move.py`, `test_population_invariant.py`, `test_grandparent_import.py` (9) | MISSING | INT-09; `R-140` parcial (sin motivo/rol); `H7 {cancelar:0}` [LOC]; rechazo correcto sobre `reversed` [LOC H8]. |
| GET `/operations/{id}/evidences` (`:334-341`) | `operations:read` | MULTI_UNIDAD | `list[EvidenceRead]` | ninguno | API_ONLY_BY_DESIGN (pero es el **único** camino de lectura dado INT-08) | Sí (de facto) | `test_od14_productive_surfaces.py`, `test_operations_bu_enforcement.py`, `test_lots_bu_enforcement.py`, `test_smoke.py` | PARTIAL | Debería consumirla `OperationDetailPage` mientras el detalle descarte `evidences`. |
| POST `/operations/{id}/evidences` (`:344-392`) | `operations:create` | MULTI_UNIDAD | `EvidenceRead` 201 | `OperationDetailPage.tsx:93` (multipart) | CONSUMIDA | Sí | `test_lots_bu_enforcement.py`, `test_od14_productive_surfaces.py`, `test_smoke.py`, `test_grandparent_import.py` | PARTIAL | Sin auditoría de subida (`GAP-12`); MIME declarado por el cliente; almacén `R-52`; permitido en cualquier estado (C#36). |
| GET `/operations/{id}/evidences/{eid}/download` (`:395-409`) | `operations:read` | MULTI_UNIDAD | `FileResponse` | `OperationDetailPage.tsx:148,161` | CONSUMIDA | Sí | `test_lots_bu_enforcement.py` (`e01…e08`), `test_od14_productive_surfaces.py`, `test_smoke.py` | CERTIFIED | `R-162` cerrado. |
| DELETE `/operations/{id}/evidences/{eid}` (`:412-419`) | `operations:delete` | MULTI_UNIDAD | 204 | `OperationDetailPage.tsx:108` | CONSUMIDA | Sí | `test_od14_productive_surfaces.py`, `test_operations_bu_enforcement.py` | PARTIAL | `os.remove` antes del commit (estado partido, D F.13) y sin auditoría (`GAP-12`). |

### 3.7 · Revisión, aprobación y pasos — `review/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/review/pending` (`:22-40`) | `review:read` | MULTI_UNIDAD | — (`{events,total}`, ORM) | `ReviewCenter.tsx:96` | CONSUMIDA_CON_BRECHA | Sí | `test_review.py`, `test_pending_classification.py`, `test_full_workflow_audit.py`, `test_upgrade_path.py` | PARTIAL | Solo `registered+pending_review` (`service.py:168`); no acepta `status`/`operator_id` que la UI envía (INT-03, B-13); ORM crudo expone todas las relaciones (C §1.1). [RT R-12] `in_review` invisible. |
| POST `/review/batches` (`:47-54`) | `review:review` | MULTI_UNIDAD | `ReviewBatchRead` 201 | `ReviewCenter.tsx:146` | CONSUMIDA | Sí | `test_review.py` | CERTIFIED | — |
| GET `/review/batches` (`:57-66`) | `review:read` | MULTI_UNIDAD | — (`{batches,total}`) | `ReviewDetail.tsx:46` (espera `actions`) | CONSUMIDA_CON_BRECHA | Sí | `test_review.py` | PARTIAL | `ReviewBatchRead` sin `actions` (`schemas.py:18-29`) → historial de acciones muerto (INT-24, C#15). |
| POST `/review/start/{id}` (`:73-80`) | `review:review` | MULTI_UNIDAD | — | `ReviewCenter.tsx:127`, `ReviewDetail.tsx:66` | CONSUMIDA | Sí | `test_review_bu_enforcement.py` (`165_01…05`), `test_review_decision_concurrency.py`, `test_audit_coverage.py` (12) | CERTIFIED | [RT] 200 ×3. Tras iniciar, el evento sale de todas las listas (STATE ORPHAN `in_review`, INT-03). |
| POST `/review/return` (`:83-90`) | `review:review` | MULTI_UNIDAD | — | `ReviewDetail.tsx:70` (solo alcanzable por URL); `ReviewCenter.tsx:128` (botón nunca visible) | CONSUMIDA_CON_BRECHA | Sí | `test_review_bu_enforcement.py`, `test_r153_import_lot_auto.py` | PARTIAL | [RT R-05] 200 por `ReviewDetail`; `observations` ≥10 solo en BE (B-29, INT-29). |
| POST `/review/complete` (`:93-100`) | `review:review` | MULTI_UNIDAD | — | `ReviewDetail.tsx:67`; `ReviewCenter.tsx:129` (nunca visible) | CONSUMIDA_CON_BRECHA | Sí | `test_review_decision_concurrency.py` (`r166_01…13`), `test_segregation_r143.py`, `test_audit_coverage.py` | PARTIAL | Multinivel observado [RT]: `complete → corrected → approve`. INT-03. |
| GET `/approvals/pending` (`:107-120`) | `approvals:approve` | MULTI_UNIDAD | — (`{events,total}`) | `ApprovalPanel.tsx:40` | CONSUMIDA | Sí | `test_review.py`, `test_rbac.py`, `test_full_workflow_audit.py` | CERTIFIED | Solo `corrected` (`service.py:463`); KPIs de la UI siempre 0 (C#25). |
| POST `/approvals/approve` (`:123-130`) | `approvals:approve` | MULTI_UNIDAD | — | `ApprovalPanel.tsx:54`, `ReviewDetail.tsx:72` | CONSUMIDA | Sí | `test_r153_import_lot_auto.py`, `test_segregation_r143.py`, `test_internal_reversal.py`, `test_notification_recipients.py` (16) | CERTIFIED | [RT] 200 ×3 con creación de `L-GP-2026-12`; 403 BR-14 por segregación (mismo aprobador tras rechazo) — por diseño. Respuesta descartada por la UI (C#13, INT-24). |
| POST `/approvals/reject` (`:133-140`) | `approvals:reject` | MULTI_UNIDAD | — | `ApprovalPanel.tsx:70`, `ReviewDetail.tsx:75` | CONSUMIDA | Sí | `test_notifications.py`, `test_rbac.py`, `test_review_bu_enforcement.py`, `test_notification_recipients.py` (7) | CERTIFIED | [RT R-11] 200 + notificación. |
| POST `/approvals/batch-approve` (`:143-150`) | `review:review` | MULTI_UNIDAD | — | `ApprovalPanel.tsx:100` | CONSUMIDA | Sí | **ninguno** (grep `batch-approve` = 0) | UNKNOWN | Sin test ni ejercicio runtime. |
| POST `/approvals/batch-reject` (`:153-160`) | `review:review` | MULTI_UNIDAD | — | `ApprovalPanel.tsx:119` | CONSUMIDA | Sí | **ninguno** | UNKNOWN | Ídem. |
| GET `/approval-steps` (`:167-173`) | `review:read` | CONTROL | — | ninguno | API_ONLY_BY_DESIGN | No | `test_review.py`, `test_r26_error_contract.py` | CERTIFIED | Configuración del flujo; multinivel es backlog `GA-REM-019`. |
| POST `/approval-steps` (`:176-183`) | `review:create` | CONTROL | `ApprovalStepRead` 201 | ninguno | API_ONLY_BY_DESIGN | No | `test_review.py`, `test_r26_error_contract.py` | CERTIFIED | — |
| PUT `/approval-steps/{id}` (`:186-194`) | `review:update` | CONTROL | `ApprovalStepRead` | ninguno | API_ONLY_BY_DESIGN | No | ídem | CERTIFIED | — |
| DELETE `/approval-steps/{id}` (`:197-204`) | `review:delete` | CONTROL | 204 | ninguno | API_ONLY_BY_DESIGN | No | ídem | CERTIFIED | — |
| POST `/approval-steps/seed-defaults` (`:207-214`) | `review:create` | CONTROL | — | ninguno | INTERNAL_ONLY | No | ídem | CERTIFIED | Semilla 1/2/3 niveles (`GA-REM-025:38`). |

### 3.8 · Correcciones — `corrections/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| POST `/corrections` (`:16-23`) | `corrections:correct` | MULTI_UNIDAD | `CorrectionRead` 201 | `CorrectionForm.tsx:52` (solo `observations`) | CONSUMIDA_CON_BRECHA | Sí | `test_corrections.py`, `test_edit_validation_parity.py`, `test_birth_classification.py` (16) | PARTIAL | La UI corrige 1 campo de `campos_corregibles()` (`corrections/service.py:171-181`; B-30, `GA-REM-006`). |
| GET `/corrections/event/{id}` (`:26-33`) | `corrections:read` | MULTI_UNIDAD | `list[CorrectionRead]` | `ReviewDetail.tsx:40` | CONSUMIDA | Sí | `test_corrections.py`, `test_full_workflow_audit.py` | CERTIFIED | — |
| GET `/corrections` (`:36-48`) | `corrections:read` | MULTI_UNIDAD | — (`{corrections,total}`) | ninguno (`correctionsService.list` tipa `CorrectionLog[]`, desalineado) | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No (AuditPage cubre con `?action=corrected`) | `test_corrections.py` | CERTIFIED | — |

### 3.9 · Reversos — `reversals/router.py` (OD-19 / GA-REM-041)

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| POST `/reversals` (`:16-23`) | `reversals:create` | MULTI_UNIDAD | `ReversalRead` 201 | ninguno | DEFERRED_BY_OWNER (RES-04) | Diferida | `test_internal_reversal.py`, `test_reversal_role_matrix.py`, `test_water_capture.py` | CERTIFIED (API) | [LOC H8] solicitud 201 → contrapartida `pending_review` → `complete` → ambos `reversed`. Permisos ya sembrados a roles → titulares sin superficie. |
| GET `/reversals` (`:26-34`) | `reversals:read` | MULTI_UNIDAD | `ReversalListResponse` | ninguno | DEFERRED_BY_OWNER | Diferida | ídem | CERTIFIED (API) | — |
| GET `/reversals/event/{id}` (`:37-43`) | `reversals:read` | MULTI_UNIDAD | `list[ReversalRead]` | ninguno | DEFERRED_BY_OWNER | Diferida | `test_internal_reversal.py` | CERTIFIED (API) | — |

### 3.10 · Auditoría — `audit/router.py`

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/audit` (`:16-41`) | `audit:read` | CORE | — (`{logs,total}`) | `AuditPage.tsx:72` | CONSUMIDA_CON_BRECHA | Sí (P-09) | `test_audit_query.py`, `test_audit_reports.py`, `test_audit_coverage.py`, `test_p013_password.py` (11) | PARTIAL | UI lee `user_name/old_value/new_value` inexistentes (C#11); **filas duplicadas** por acción bajo uvicorn (listener `after_flush` + helper explícito: `audit/listeners.py:71-113`, `audit/helpers.py:73-92`, `operations/service.py:308`) [LOC H6/H8] — recurrencia de **`P1-12`** («auditoría duplicada e incompleta», `REMEDIATION_BACKLOG.md:98`); `R-148` sin trigger BD; `R-83` `company_id` NOT NULL (`GAP-10`). INT-15. |
| GET `/audit/{log_id}` (`:44-51`) | `audit:read` | CORE | `AuditLogRead` | ninguno (`auditService.get`) | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No | **ninguno directo** (grep) | UNKNOWN | — |
| GET `/audit/timeline/{entity_type}/{entity_id}` (`:54-63`) | `audit:read` | CORE | — | ninguno (`auditService.getTimeline`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí (docs/13; bajo) | `test_full_workflow_audit.py`, `run_e2e_audit.py` | MISSING (bajo) | API 200 [LOC H6-audit-timeline] con la misma duplicación. |

### 3.11 · Reportes — `reports/router.py` (ninguna declara `response_model`)

| Método · Ruta | Permiso | Alcance | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|
| GET `/reports/kpis?lot_id` (`:15-22`) | `reports:read` | MULTI_UNIDAD | `LotDetailPage.tsx:53`, `ReportsPage.tsx:17` | CONSUMIDA_CON_BRECHA | Sí | `test_kpi_scope.py`, `test_kpi_hatchery.py`, `test_audit_reports.py`, `test_r186_g05_date_semantics.py` (9) | PARTIAL | Agregado `hatchery_yield` sin filtro de unidad cuando no hay `lot_id` (`GAP-07`); 403 ×12 para `lots:read` sin `reports:read` desde el detalle de lote [RT] (INT-22); `ReportsPage` lo llama con lote 2 fijo (INT-17). |
| GET `/reports/kpis/mortality` (`:25-32`) | `reports:read` | MULTI_UNIDAD | ninguno (`reportsService.getMortalityKpi`) | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No (en agregado) | `test_kpi_scope.py`, `test_sap_transversal.py` | CERTIFIED | — |
| GET `/reports/kpis/feed-conversion` (`:35-42`) | `reports:read` | MULTI_UNIDAD | ninguno | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No | `test_kpi_scope.py` | CERTIFIED | — |
| GET `/reports/kpis/egg-production` (`:45-52`) | `reports:read` | MULTI_UNIDAD | ninguno | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No | `test_kpi_hatchery.py` | CERTIFIED | — |
| GET `/reports/kpis/hatchery` (`:55-63`) | `reports:read` | UNIDAD_UNICA hatchery (declarada; **no aplicada**) | `LotReportPage.tsx:33` | CONSUMIDA_CON_BRECHA | Sí | `test_kpi_hatchery.py`, `test_birth_classification.py` | PARTIAL | Sin `lot_id` suma toda la incubadora de la empresa (`reports/service.py:191-207,262-308`; `GAP-07`); `hatchery_id` aceptado e ignorado (`:63`). |
| GET `/reports/kpis/animal-welfare` (`:66-73`) | `reports:read` | MULTI_UNIDAD | ninguno | API_ONLY_BY_DESIGN | No | `test_kpi_scope.py` | CERTIFIED | G-01. |
| GET `/reports/kpis/vaccination-efficiency` (`:76-83`) | `reports:read` | MULTI_UNIDAD | `LotReportPage.tsx:31` | CONSUMIDA | Sí | `test_kpi_scope.py` | CERTIFIED | G-02. |
| GET `/reports/kpis/transfer-efficiency` (`:86-93`) | `reports:read` | CONTRATO | `LotReportPage.tsx:32` | CONSUMIDA | Sí | `test_kpi_scope.py` | CERTIFIED | G-03. |
| GET `/reports/kpis/afcr` (`:96-103`) | `reports:read` | MULTI_UNIDAD | `LotReportPage.tsx:30` | CONSUMIDA | Sí | **ninguno directo** (grep `/afcr` = 0) | PARTIAL | G-04 sin test HTTP. |
| GET `/reports/kpis/production-index` (`:106-113`) | `reports:read` | MULTI_UNIDAD | **ninguno** (ni en agregado) | BACKEND_ORPHAN | No (FVA-31 lo cita «G-05 5.1» sin pantalla) | `test_r186_g05_date_semantics.py` | MISSING (bajo) | Aceptado por el propietario en UAT-06/07 como cálculo; sin superficie. |
| GET `/reports/kpi/ipe/{lot_id}` (`:116-126`) | `reports:read` | MULTI_UNIDAD | `LotDetailPage.tsx:56`, `LotReportPage.tsx:28` | CONSUMIDA | Sí (OD-22) | `test_r184_ipe_date_semantics.py`, `test_r187_ipe_od22_scale.py` | CERTIFIED | [LOC BO-ipe] 200; UAT-06/07. |
| GET `/reports/kpi/weight-uniformity/{lot_id}` (`:129-136`) | `reports:read` | MULTI_UNIDAD | `LotDetailPage.tsx:57`, `LotReportPage.tsx:29` | CONSUMIDA | Sí (G-07) | `test_kpi_scope.py` | CERTIFIED | — |
| GET `/reports/lot/{lot_id}` (`:139-146`) | `reports:read` | MULTI_UNIDAD | `LotReportPage.tsx:26` | CONSUMIDA_CON_BRECHA | Sí | `test_audit_reports.py` | PARTIAL | Ruta FE casi huérfana (enlace fijo `lot/2`, `G-18`, INT-17). [LOC BO-reporte-lote] 200. |
| GET `/reports/sap-comparison` (`:149-156`) | `reports:read` | CONTRATO | `SapComparisonPage.tsx:14` | CONSUMIDA | P-08 | `test_audit_reports.py` | CERTIFIED | Sin filtro de unidad por diseño (BU-D04); carga eterna en error (C#20). |

### 3.12 · Dashboard — `dashboard/router.py`

| Método · Ruta | Permiso | Alcance | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|
| GET `/dashboard/mobile` (`:13-19`) | `dashboard:read` | MULTI_UNIDAD | `DashboardPage.tsx:94` | CONSUMIDA | Sí | `test_audit_reports.py`, `test_full_workflow_audit.py`, `test_upgrade_path.py` | CERTIFIED | Claves i18n de cabecera ausentes en UI (`G-10`). |
| GET `/dashboard/admin` (`:22-28`) | `dashboard:read` | MULTI_UNIDAD | `DashboardPage.tsx:95` | CONSUMIDA_CON_BRECHA | Sí | `test_kpi_scope.py` (`:286,342` comparan por substring y no detectan el defecto), `test_audit_reports.py` | PARTIAL | `lots_by_type` con claves `BirdTypeEnum.X` (`dashboard/service.py:171`) [LOC H5] → tarjetas en 0 (INT-14); `active_alerts` sin predicado de unidad (`GAP-08`); 403 para operador/aprobador convierte el home en error (`G-02`) [RT]. |

### 3.13 · SAP — `integrations/sap/router.py` (montado solo con `FEATURE_SAP_ENABLED`; `true` en `docker-compose.yml:26`)

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| POST `/sap/references/import` (`:20-27`) | `sap:send_sap` | CONTROL | — 201 | **ninguno** (`sapService.importReferences` con cuerpo obsoleto `{ref_type, entries}` vs `{references:[…]}` `sap/schemas.py:45-47`, B-27) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí en modo manual (`GA-REM-010:64,88`; el asistente depende de las referencias `OFP:352-353`) | `test_sap.py`, `test_sap_transversal.py`, `test_purchase_order_receipt.py`, `test_audit_coverage.py` | MISSING | INT-16. Usada como fixture por API [LOC fixture-sap-refs]. |
| GET `/sap/references` (`:30-42`) | `sap:read` | CONTROL | — (`{references,total}`) | `SapManagerPage.tsx:39`, `OperationFormPage.tsx:352-353` | CONSUMIDA_CON_BRECHA | Sí | `test_sap.py`, `test_purchase_order_receipt.py`, `test_sap_transversal.py` (6) | PARTIAL | `OFP:636` lee `quantity`, no declarado en `SapReferenceRead` (`sap/schemas.py:31-42`): funciona solo por ausencia de `response_model` (C §1.1); autoridad global sin contexto ve todas las empresas (`GAP-02`). |
| POST `/sap/consolidate` (`:49-61`) | `sap:send_sap` | CONTRATO | — 201 (lista) | `SapManagerPage.tsx:53` | CONSUMIDA_CON_BRECHA | Sí | `test_sap.py`, `test_sap_transversal.py`, `test_rbac.py`, `test_notifications.py` | PARTIAL | Sin refetch en UI (C#22, INT-16); sin bloqueo → consolidaciones concurrentes duplican (`GAP-14`). |
| GET `/sap/consolidated` (`:64-85`) | `sap:read` | CONTRATO | `{consolidated: list[ConsolidatedMovementRead], total}` | ninguno (`sapService.listConsolidated`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | P-08 | `test_sap.py`, `test_sap_transversal.py` | MISSING (bajo) | — |
| POST `/sap/export` (`:92-103`) | `sap:send_sap` | CONTRATO | `SapExportResponse` | `SapManagerPage.tsx:62` | CONSUMIDA_CON_BRECHA | Sí (modo manual «preparado») | `test_sap.py`, `test_sap_transversal.py`, `test_upgrade_path.py` | PARTIAL | Sin refetch ni confirmación (INT-16); `R-112` BLOCKED_EXTERNAL. |
| POST `/sap/retry` (`:106-117`) | `sap:send_sap` | CONTRATO | — (`{retried,message}`) | **ninguno** (`sapService.retry`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí (el aviso `sap_send_failed` no ofrece acción, `notifications.ts:16`) | `test_notifications.py` | MISSING | `retry_failed` sin `_require_company_id` (`GAP-02`); doble consumo de `Result` en re-enlace (`GAP-14`). |
| GET `/sap/sync/jobs` (`:124-133`) | `sap:read` | CONTRATO | — (`{jobs,total}`) | `SapManagerPage.tsx:40` (`limit=5`) | CONSUMIDA_CON_BRECHA | Sí | `test_sap.py` | PARTIAL | Vocabulario de estados distinto en UI (`pending/error` vs `failed`) (C#10). |
| GET `/sap/payloads` (`:136-148`) | `sap:read` | CONTRATO | — (`{payloads,total}`) | `SapManagerPage.tsx:41` (`limit=5`) | CONSUMIDA_CON_BRECHA | Sí | `test_sap.py` | PARTIAL | Pestañas derivadas de 5 filas; `failed` nunca visible (C#10). |
| GET `/sap/errors` (`:151-159`) | `sap:read` | CONTRATO | — (`list[SapErrorItem]`) | **ninguno** (`sapService.listErrors`; la pestaña «Errores» no lo usa `SapManagerPage.tsx:249-273`) | BACKEND_ORPHAN + PROMISED_ZERO_CALLER | Sí | `test_sap.py` | MISSING | INT-16. |
| GET `/sap/connection-check` (`:166-184`) | `sap:read` | CONTROL | — (`connected, adapter, delivers_to_sap, mode`) | `SapManagerPage.tsx:42` | CONSUMIDA_CON_BRECHA | Sí | `test_sap.py`, `test_sap_transversal.py` | PARTIAL | `delivers_to_sap`/`mode` ignorados → adaptador simulado mostrado como conectado (C#10). |

### 3.14 · Maestros — `masters/router.py` (`register_crud` `:20-94`; 20 entidades × {GET lista, POST, GET/{id}, PUT, DELETE})

Consumidores comunes: `MasterListPage.tsx:49` (lista), `:92`/`:94` (POST/PUT), `:110` (DELETE) para las 20 entidades; catálogos en `OperationFormPage.tsx:342-379` (14 entidades), `LotFormPage.tsx:82-109` (farms, houses, genetic-lines, breeds, areas), `UsersPage.tsx:37-65` (companies, areas), `CorrectionForm.tsx:26-45` (correction-types), `ReviewCenter.tsx:107-110` (farms), `company.store.ts:39` (companies). `GET /masters/E/{id}` solo lo consume `genetic-lines` (`weightCurves.ts:52-55`); para las otras 19 es `API_ONLY_BY_DESIGN`. Navegación: 19 entidades + empresas solo por URL escrita (`G-01`, INT-20). Permisos: `masters:read/create/read/update/delete`. Alcance: `companies` CONTROL; `farms`, `houses` y el resto MULTI_UNIDAD; `hatcheries/incubators/hatchers/processing-plants` declaradas `UNIDAD_UNICA` sin aplicación (D B.16). Seguridad transversal: `company_id` fijable por el cliente en Create/Update de 19 esquemas (`GAP-05` / `R-50`, `masters/schemas.py`, `masters/service.py:232-234,248-254`).

| Entidad (5 rutas) | `Create` exige | ¿Alta posible desde la UI genérica? | Tests (`/masters/<e>`) | Clasif. (5 rutas) | Nota |
|---|---|---|---|---|---|
| companies | `name` | ✔ (sin producto por OD-24) | `test_company_catalog.py`, `test_master_tenant_isolation.py`, `test_masters.py`, `test_user_tenant_isolation.py` | CERTIFIED | OD-24. |
| farms | **`company_id: int`** (`schemas.py:64-73`) | **✘ 422** (B-08) | `test_masters.py`, `test_master_tenant_isolation.py`, `test_multitenant_isolation.py`, `test_od14_productive_surfaces.py`, `test_lot_closure.py` (14) | PARTIAL | INT-07; `GAP-05`. |
| houses | **`farm_id: int`** (`:95-103`); `capacity` `''` → 422 | **✘ 422 + React #31** [LOC H4] | `test_masters.py`, `test_multitenant_isolation.py` (galpón en granja ajena), `test_od14_productive_surfaces.py`, `test_reception_lineage.py` (8) | PARTIAL | INT-07 (B-08, B-14, B-15). |
| hatcheries | **`company_id: int`** (`:124-132`) | **✘ 422** [LOC MAS-hatchery-create-ui] | `test_business_unit_guard.py`, `test_master_management.py`, `test_od14_productive_surfaces.py` | PARTIAL | INT-07. |
| incubators | **`hatchery_id: int`** (`:149-157`) | **✘ 422** | `test_business_unit_guard.py`, `test_master_management.py` | PARTIAL | INT-07. |
| hatchers | **`hatchery_id: int`** (`:166-173`) | **✘ 422** | `test_business_unit_guard.py` | PARTIAL | INT-07. |
| productive-phases | `order` `''` → 422 (`:224-233`) | parcial (422 con `order` en blanco) | `test_master_management.py` | PARTIAL | B-14; además la UI de transición no usa `phase_id` (INT-01). |
| suppliers | opcional (`company_id` inyectado) | ✔ | `test_masters.py`, `test_upgrade_path.py` | CERTIFIED | — |
| areas | opcional | ✔ | `test_areas.py`, `test_lot_area_eligibility.py`, `test_lot_area_ownership.py`, `test_business_unit_guard.py`, `test_notification_recipients.py` | CERTIFIED | GA-FE-07 / UAT-05 (elegibilidad OD-21). |
| genetic-lines | opcional | ✔ | `test_genetic_curves.py`, `test_od14_productive_surfaces.py`, `test_weight_alert.py`, `test_weight_evaluation_endpoint.py` | CERTIFIED | Único con `GET /{id}` consumido. |
| breeds | `genetic_line_id` opcional | ✔ | `test_masters.py` | CERTIFIED | — |
| feed-types | opcional | ✔ | **ninguno** | PARTIAL | Sin test directo. |
| vaccines | opcional | ✔ | `test_smoke.py`, `test_upgrade_path.py` | CERTIFIED | — |
| mortality-causes | opcional | ✔ | `test_runtime_startup.py`, `test_smoke.py` | CERTIFIED | — |
| transports | opcional | ✔ | **ninguno** | PARTIAL | Sin test directo. |
| processing-plants | opcional | ✔ | `test_business_unit_guard.py` | CERTIFIED | — |
| medications | opcional | ✔ | `test_master_management.py` | CERTIFIED | — |
| cull-causes | opcional | ✔ | `test_master_management.py` | CERTIFIED | — |
| rejection-reasons | opcional | ✔ | **ninguno** | PARTIAL | Sin test directo; sin consumidor de negocio más allá del CRUD. |
| correction-types | opcional | ✔ | **ninguno directo** (`CorrectionForm` lo consume) | PARTIAL | Sin test directo. |
| (las 20) `is_active` | — | reactivación **imposible** desde la UI (B-36) | — | — | CF-63 MISSING_UI. |

Rutas especiales de maestros:

| Método · Ruta | Permiso | Alcance | response_model | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|---|
| GET `/masters/farms/{farm_id}/houses` (`:132-152`) | `masters:read` | MULTI_UNIDAD | `list[HouseRead]` | ninguno (`mastersService.getHousesByFarm`; la UI filtra en cliente `OFP:291-298`, `LotFormPage.tsx:112-114`) | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No | `test_masters.py`, `test_multitenant_isolation.py`, `test_od14_productive_surfaces.py`, `test_smoke.py` (9) | CERTIFIED | 404 sin empresa (D A.6). |
| GET `/masters/hatcheries/{id}/incubators` (`:155-174`) | `masters:read` | UNIDAD_UNICA hatchery | `list[IncubatorRead]` | ninguno (`mastersService.getIncubatorsByHatchery`) | API_ONLY_BY_DESIGN + PROMISED_ZERO_CALLER | No | `test_business_unit_guard.py`, `test_master_management.py`, `test_od14_productive_surfaces.py` | CERTIFIED | — |
| GET `/masters/genetic-lines/{id}/weight-curves` (`:183-197`) | `masters:read` | MULTI_UNIDAD | `list[WeightCurveRead]` | `WeightCurvesPage.tsx:65`, `LotFormPage.tsx:71` | CONSUMIDA | Sí (OD-06) | `test_genetic_curves.py`, `test_od14_productive_surfaces.py` | CERTIFIED | Aviso de curva activa visto en alta de lote [LOC BR-00]. |
| POST `/masters/weight-curves` (`:200-208`) | `masters:create` | MULTI_UNIDAD | `WeightCurveRead` 201 | `WeightCurvesPage.tsx:111` | CONSUMIDA | Sí | `test_genetic_curves.py` (`t_037_01…15`), `test_weight_alert.py`, `test_weight_evaluation_endpoint.py`, `test_notification_recipients.py` | CERTIFIED | Celdas ilegibles → `null` → 422 genérico (B-32, P3). |
| GET `/masters/weight-curves/{id}` (`:211-224`) | `masters:read` | MULTI_UNIDAD | `WeightCurveRead` | ninguno | API_ONLY_BY_DESIGN | No | `test_genetic_curves.py`, `test_od14_productive_surfaces.py` | CERTIFIED | — |
| PUT `/masters/weight-curves/{id}/activate` (`:227-242`) | `masters:update` | MULTI_UNIDAD | `WeightCurveRead` | `WeightCurvesPage.tsx:131` | CONSUMIDA | Sí | **ninguno HTTP directo** (grep `weight-curves/…/activate` = 0; `test_genetic_curves.py` no contiene `activate`) | PARTIAL | Sin test de la ruta; UI no ejercitada. |

### 3.15 · Infraestructura

| Método · Ruta | Permiso | Alcance | Consumidor FE | Huérfano | ¿Req.? | Tests | Clasif. | Nota |
|---|---|---|---|---|---|---|---|---|
| GET `/health` (`main.py:127-129`, sin prefijo) | PUBLICA | PUBLICA | ninguno | INTERNAL_ONLY | No | `test_smoke.py`, `test_auth.py` | CERTIFIED | — |

## 4 · Conteos

### 4.1 · Por clasificación

| Clasificación | Rutas | Detalle |
|---|---|---|
| CERTIFIED | **107** | auth 2 · users/roles 8 · business-units 4 · notifications 4 · lots 1 · operations 7 · review 2 · approvals 3 · approval-steps 5 · corrections 2 · reversals 3 (API) · reports 9 · dashboard 1 · masters 55 (10 entidades × 5 + 5 especiales) · health 1 |
| PARTIAL | **91** | auth 2 (`/me`, `/switch-company`) · users/roles 5 · lots 8 · operations 8 · review 4 · corrections 1 · audit 1 · reports 4 · dashboard 1 · sap 6 · masters 51 (10 entidades × 5 + `activate`) |
| MISSING | **11** | `PUT /lots/{id}` · `POST /lots/activate-manual` · `GET /lots/{id}/opening-balance` · `PUT /operations/{id}` · `POST /operations/{id}/cancel` · `GET /audit/timeline/…` · `GET /reports/kpis/production-index` · `POST /sap/references/import` · `GET /sap/consolidated` · `POST /sap/retry` · `GET /sap/errors` |
| UNKNOWN | **3** | `POST /approvals/batch-approve` · `POST /approvals/batch-reject` · `GET /audit/{log_id}` |
| **Total** | **212** | |

### 4.2 · Por estado de consumo / huérfano

| Estado | Rutas | Detalle |
|---|---|---|
| CONSUMIDA (con o sin brecha) | **157** | de ellas **CONSUMIDA_CON_BRECHA** 36: `/users` GET/PUT/password, `/lots` GET/POST/{id}/close/phases×2/egg-batches/chick-batches, `/operations` GET/POST/{id}/evidences POST/DELETE, `/review/pending`, `/review/batches` GET, `/review/return`, `/review/complete`, `/corrections` POST, `/audit` GET, `/reports/kpis`, `/kpis/hatchery`, `/reports/lot/{id}`, `/dashboard/admin`, `/sap/references`, `/sap/consolidate`, `/sap/export`, `/sap/sync/jobs`, `/sap/payloads`, `/sap/connection-check`, masters POST de farms/houses/hatcheries/incubators/hatchers |
| BACKEND_ORPHAN (brecha real) | **11** | las 11 MISSING; 10 de ellas son además **PROMISED_ZERO_CALLER** (existe método en `services/*.ts` sin llamador: `lots.update/activateManual/getOpeningBalance`, `operations.update/cancel`, `audit.getTimeline`, `sap.importReferences/listConsolidated/retry/listErrors`); `production-index` no tiene método FE |
| PROMISED_ZERO_CALLER sobre rutas no requeridas | **9** | `operations.getEventTypes`, `corrections.list`, `audit.get`, `reports.getMortalityKpi/getFeedConversionKpi/getEggProductionKpi`, `masters.getHousesByFarm/getIncubatorsByHatchery/listCorrectionTypes` (informe A §2.18) |
| API_ONLY_BY_DESIGN | **36** | `GET /users/{id}`, `GET /notifications/{id}`, `GET /operations/event-types`, `GET /operations/{id}/evidences`, `/approval-steps` ×4, `GET /corrections`, `GET /audit/{id}`, 4 KPI individuales, `GET /masters/farms/{id}/houses`, `GET /masters/hatcheries/{id}/incubators`, `GET /masters/weight-curves/{id}`, `GET /masters/E/{id}` ×19 |
| INTERNAL_ONLY | **2** | `/health`, `POST /approval-steps/seed-defaults` |
| DEFERRED_BY_OWNER | **6** | `pending-classification`, `classify`, `reclassify` (RES-02) · `/reversals` ×3 (RES-04) |
| **Total** | **212** | |

### 4.3 · Requeridas pre-SAP sin frontend (FRONTEND_INTEGRATION_GAP, §5 del encargo)

| Ruta | Proceso | Referencia | Brecha |
|---|---|---|---|
| `POST /lots/activate-manual`, `GET /lots/{id}/opening-balance` | P-11 (lotes en curso con saldo de apertura) | `GA-REM-028`, `GA-REM-005:390` | INT-10 |
| `PUT /lots/{id}` | edición de lote | `GA-REM-040:1440,1612` | INT-10 |
| `PUT /operations/{id}` | edición pre-revisión (devueltos/rechazados) | `GA-REM-023:80,115`, OD-17 | INT-09 |
| `POST /operations/{id}/cancel` | anulación | `GA-REM-042:51` | INT-09 |
| `POST /sap/references/import`, `POST /sap/retry`, `GET /sap/errors` | SAP modo manual | `GA-REM-010:64,88` | INT-16 |
| `GET /audit/timeline/…` | línea de tiempo por entidad | docs/13 | INT-15 (bajo) |
| `GET /operations/{id}/evidences` | listado de adjuntos (único camino viable mientras INT-08 persista) | docs/02 §7 | INT-08 |

### 4.4 · Tests de backend: cobertura por ruta

- Rutas con ≥1 fichero de test que las ejercita por HTTP: **203 / 212**.
- Sin test HTTP directo (9): `POST /approvals/batch-approve`, `POST /approvals/batch-reject`, `GET /audit/{log_id}`, `GET /reports/kpis/afcr`, `PUT /masters/weight-curves/{id}/activate`, y las 5 rutas de `feed-types`/`transports`/`rejection-reasons`/`correction-types` contadas por entidad (20 rutas de 4 entidades sin test propio; cubiertas solo por el registro genérico `register_crud`).
- Suite en HEAD: 1201 ✔ / 25 ✘ / 49 omitidos; los 25 fallos no afectan a la semántica de producto de ninguna ruta de esta matriz salvo `GET /me` (500 con TLD reservado, fila 3.1).
