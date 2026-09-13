# A · TRAZA FRONTEND ↔ BACKEND — GlobalAvicola (auditoría de solo lectura)

Fecha: 2026-09-13 · Repo: `/home/maria/Proyectos/GlobalAvicola` · Backend `backend/app` (FastAPI) · Frontend `frontend/src` (React+TS).
Método: lectura íntegra de los 15 routers, `main.py`, `route_scope.py`, `authorization_coverage.py`, esquemas Pydantic relevantes; lectura íntegra de `services/*`, `hooks/*`, `stores/*`, `App.tsx`, `navigationConfig.ts`, las 31 páginas y los componentes de layout/operaciones/notificaciones/`TraceabilityTree`/`DataTable`; greps de llamadores excluyendo `__tests__` y `*.test.*`. Todas las rutas del backend llevan prefijo `/api/v1` (`main.py:149-168`). El router SAP solo se monta si `FEATURE_SAP_ENABLED` (`main.py:146-147,167-168`; por defecto `False` en `config.py:111`; `true` en `.env:28` y `docker-compose.yml:26`).

Leyenda de clasificación: `USER_FACING` = tiene o debería tener superficie de usuario · `INTERNAL_ONLY` = infraestructura/sesión/plano de control sin pantalla por diseño · `API_ONLY_BY_DESIGN` = expuesto para clientes API/administración por API, documentado como tal · `SAP_FUTURE` = depende de `P-08`/SAP real.

Hallazgo transversal (condiciona las Partes 2 y 3): **ninguna página importa ningún hook de datos ni ningún servicio salvo `businessUnits.service`, `notifications`, `weightCurves` y `operationsService.submit`**. Las páginas llaman `api.get/post/...` directamente (grep «service imports outside services/hooks» y «hook imports» → 0 importadores de `hooks/use*`). Por tanto 11 de 14 servicios y 12 hooks de datos son código muerto (Parte 2).

---

## PARTE 1 — INVENTARIO DE RUTAS DEL BACKEND

Total de rutas montadas: **222** (211 sin SAP ni `/health`, coincide con el guardián «rutas 211» de `GA-REM-041 §5:191`). Columna «Permiso»: `require_permission(módulo, acción)` o exención declarada en `authorization_coverage.py` (`RUTAS_PUBLICAS:21-29`, `RUTAS_DE_TITULAR:42-59`). Columna «Alcance»: `route_scope.py` (`RUTAS:69-196`, `MAESTROS:44-66`).

### 1.1 Auth & Users — `auth/router.py`

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| POST | `/login` (:29-32) | PÚBLICA (`authorization_coverage.py:23`) · rate-limit 5/min | PUBLICA | `TokenResponse` | `AuthService.login` | Emitir tokens | USER_FACING |
| POST | `/refresh` (:35-37) | PÚBLICA (:24) | PUBLICA | `TokenResponse` | `AuthService.refresh_token` | Renovar sesión | INTERNAL_ONLY (interceptor) |
| GET | `/me` (:40-84) | titular (`get_current_user`) | CORE | `SessionRead` | `AuthService.get_user` + `business_units.service.unidades_*` | Sesión compuesta: empresa efectiva, permisos, BU | INTERNAL_ONLY (bootstrap) |
| POST | `/switch-company` (:87-94) | titular; el servicio valida super-admin | CORE | `TokenResponse` | `AuthService.switch_company` | Situarse en otra empresa (OD-11) | USER_FACING |
| GET | `/users` (:99-107) | `users:read` | CONTROL | `list[UserRead]` | `get_users` (skip/limit≤100/search) | Listar usuarios | USER_FACING |
| POST | `/users` (:110-116) | `users:create` | CONTROL | `UserRead` 201 | `create_user` | Alta de usuario | USER_FACING |
| GET | `/users/{user_id}` (:119-125) | `users:read` | CONTROL | `UserRead` | `get_user` | Detalle | API_ONLY_BY_DESIGN |
| PUT | `/users/{user_id}` (:128-135) | `users:update` | CONTROL | `UserRead` | `update_user` (`UserUpdate` extra=forbid, sin `username`/`company_id`/`password`: `auth/schemas.py:74-85`) | Editar usuario | USER_FACING |
| POST | `/users/{user_id}/password` (:138-150) | titular o admin (servicio) | CONTROL | 204 | `change_password` | Cambio/restablecimiento de contraseña (GA-REM-012) | USER_FACING |
| DELETE | `/users/{user_id}` (:153-159) | `users:delete` | CONTROL | 204 | `deactivate_user` | Baja lógica | USER_FACING |
| GET | `/roles/permissions-catalog` (:164-174) | `users:read` | CONTROL | NONE (dict) | `get_permission_catalog` | Módulos/acciones concedibles | USER_FACING |
| GET | `/roles` (:177-182) | `users:read` | CONTROL | `list[RoleRead]` | `get_roles` | Listar roles | USER_FACING |
| POST | `/roles` (:185-191) | `users:create` | CONTROL | `RoleRead` 201 | `create_role` | Crear rol con permisos | USER_FACING |
| PUT | `/roles/{role_id}` (:194-201) | `users:update` | CONTROL | `RoleRead` | `update_role` (`RoleUpdate` con `is_active`, `permissions`) | Editar/desactivar rol | USER_FACING |

No existe `DELETE /roles/{id}` ni ruta de logout en servidor (el logout es solo cliente: `auth.store.ts:133-139`).

### 1.2 Maestros — `masters/router.py` (`register_crud` :20-94)

22 entidades (:104-125): `companies, farms, houses, hatcheries, incubators, hatchers, areas, genetic-lines, breeds, productive-phases, suppliers, feed-types, vaccines, medications, mortality-causes, cull-causes, transports, processing-plants, rejection-reasons, correction-types` (20) + … total según `MAESTROS` (`route_scope.py:44-66`, 21 recursos + `weight-curves`). Por entidad `E`:

| Método | Ruta | Permiso | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|
| GET | `/masters/E` (:78) | `masters:read` | `list[ERead]` + cabecera `X-Total-Count` (:47-48) | `MasterService.get_all` | Listado paginado/búsqueda | USER_FACING |
| POST | `/masters/E` (:79) | `masters:create` | `ERead` 201 | `create` | Alta | USER_FACING |
| GET | `/masters/E/{id}` (:80) | `masters:read` | `ERead` | `get_by_id` | Detalle | USER_FACING (solo `genetic-lines` consumido) |
| PUT | `/masters/E/{id}` (:94) | `masters:update` | `ERead` | `update` | Edición | USER_FACING |
| DELETE | `/masters/E/{id}` (:81) | `masters:delete` | 204 | `deactivate` | Baja lógica | USER_FACING |

Especiales:

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| GET | `/masters/farms/{farm_id}/houses` (:132-152) | `masters:read` | MULTI_UNIDAD | `list[HouseRead]` | inline | Galpones de una granja | API_ONLY_BY_DESIGN (frontend filtra en cliente) |
| GET | `/masters/hatcheries/{id}/incubators` (:155-174) | `masters:read` | UNIDAD_UNICA hatchery | `list[IncubatorRead]` | inline | Incubadoras de una planta | API_ONLY_BY_DESIGN |
| GET | `/masters/genetic-lines/{id}/weight-curves` (:183-197) | `masters:read` | MULTI_UNIDAD | `list[WeightCurveRead]` | `curves._linea_del_usuario` | Versiones de curva | USER_FACING |
| POST | `/masters/weight-curves` (:200-208) | `masters:create` | MULTI_UNIDAD | `WeightCurveRead` 201 | `curves.crear_version` | Carga atómica de curva | USER_FACING |
| GET | `/masters/weight-curves/{id}` (:211-224) | `masters:read` | MULTI_UNIDAD | `WeightCurveRead` | inline | Detalle de curva | API_ONLY_BY_DESIGN |
| PUT | `/masters/weight-curves/{id}/activate` (:227-242) | `masters:update` | MULTI_UNIDAD | `WeightCurveRead` | `curves.activar` | Activar versión | USER_FACING |

### 1.3 Notificaciones — `notifications/router.py`

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| GET | `/notifications` (:26-43) | titular (`authorization_coverage.py:55`) | CORE | `list[NotificationRead]` + `X-Total-Count` | `service.listar` | Bandeja propia | USER_FACING |
| GET | `/notifications/unread-count` (:46-52) | titular | CORE | `UnreadCountRead` | `contar_sin_leer` | Contador | USER_FACING |
| GET | `/notifications/{id}` (:55-66) | titular | CORE | `NotificationRead` | `obtener` | Detalle (404 a terceros) | API_ONLY_BY_DESIGN |
| PATCH | `/notifications/{id}/read` (:69-80) | titular | CORE | `NotificationRead` | `marcar_leida` | Marcar leída | USER_FACING |

Sin ruta de creación, `read-all` ni borrado por diseño (`notifications/router.py:1-13`). Productores: `notifications/service.py:31 crear_notificacion`, invocado desde `review/service.py`, `operations/service.py`, `integrations/sap/service.py` y el vigilante SLA (`main.py:47-52`).

### 1.4 Lotes — `lots/router.py`

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| GET | `/lots` (:23-36) | `lots:read` | MULTI_UNIDAD | `list[LotRead]` | `LotService.get_lots` (search/farm_id/status; total descartado) | Listado | USER_FACING |
| POST | `/lots` (:39-46) | `lots:create` | MULTI_UNIDAD | `LotRead` 201 | `create_lot` | Alta | USER_FACING |
| GET | `/lots/{lot_id}` (:49-66) | `lots:read` | MULTI_UNIDAD | `LotDetailRead` (+phases, opening_balance) | `get_lot`, `get_lot_phases`, `get_opening_balance` | Detalle | USER_FACING |
| PUT | `/lots/{lot_id}` (:69-77) | `lots:update` | MULTI_UNIDAD | `LotRead` | `update_lot` (`LotUpdate` :50-74) | Edición | USER_FACING |
| POST | `/lots/{lot_id}/close` (:80-92) | `lots:create` | MULTI_UNIDAD | `LotClosureSummary` | `close_lot` (BR-05/G-09; GA-REM-029) | **Transición** active→closed | USER_FACING |
| POST | `/lots/activate-manual` (:99-106) | `lots:create` | MULTI_UNIDAD («P-11, las cuatro») | `OpeningBalanceRead` 201 | `activate_manual` (`OpeningBalanceCreate` :123-155) | **Transición** P-11: activación manual con saldo de apertura | USER_FACING |
| GET | `/lots/{lot_id}/opening-balance` (:109-119) | `lots:read` | MULTI_UNIDAD | `OpeningBalanceRead` | `get_opening_balance` | Saldo de apertura | USER_FACING |
| GET | `/lots/{lot_id}/phases` (:126-133) | `lots:read` | MULTI_UNIDAD | `list[LotPhaseRead]` | `get_lot_phases` | Fases | USER_FACING |
| POST | `/lots/{lot_id}/phases` (:136-147) | `lots:create` | MULTI_UNIDAD | `LotPhaseRead` 201 | `add_phase` (`LotPhaseCreate`: `lot_id:int`, `phase_id:int` obligatorios `lots/schemas.py:98-105`; guarda `lot_id mismatch` :143-145) | **Transición** cría→producción | USER_FACING |
| GET | `/lots/{lot_id}/traceability` (:154-200) | `lots:read` | CONTRATO | `TraceabilityNode` | inline + `_vinculos_efectivos` (R-178) | Árbol generacional | USER_FACING |
| POST | `/lots/egg-batches` (:239-268) | `lots:create` | CONTRATO | `EggBatchRead` 201 | inline + `verificar_vinculo_generacional`, `validar_flujo` | Vínculo huevos (`EggBatchCreate`: `hatchery_lot_id:int` obligatorio :219) | USER_FACING |
| POST | `/lots/chick-batches` (:271-300) | `lots:create` | CONTRATO | `ChickBatchRead` 201 | ídem | Vínculo pollitos | USER_FACING |

### 1.5 Operaciones — `operations/router.py`

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| GET | `/operations/event-types` (:33-35) | listada como titular (`authorization_coverage.py:45`) **pero sin ninguna dependencia de sesión** → de hecho anónima | CORE | NONE (`ALL_EVENT_TYPES` :312) | — | Catálogo estático de tipos | API_ONLY_BY_DESIGN |
| GET | `/operations` (:42-67) | `operations:read` | MULTI_UNIDAD | `list[OperationalEventRead]` | `get_events` (lot_id/farm_id/event_type/status CSV/registered_by_me/fechas; total descartado) | Listado | USER_FACING |
| POST | `/operations` (:70-77) | `operations:create` | MULTI_UNIDAD | `OperationalEventRead` 201 | `create_event` (24 tipos, 23 reglas BR) | Registro | USER_FACING |
| GET | `/operations/alerts` (:86-98) | `operations:read` | MULTI_UNIDAD | `list[OperationalAlertRead]` | `get_alerts` | Alertas | USER_FACING |
| PATCH | `/operations/alerts/{id}/resolve` (:101-108) | `operations:update` | MULTI_UNIDAD | `OperationalAlertRead` | `resolve_alert` | **Transición** alerta→resuelta | USER_FACING |
| GET | `/operations/pending-classification` (:118-144) | `operations:read` | CONTROL | `list[OperationalEventRead]` | inline `predicado_de_pendientes` | Bandeja OD-10.c | USER_FACING (diferido, ver P4) |
| POST | `/operations/{id}/classify` (:147-193) | `masters:update` | CONTROL | `OperationalEventRead` | `classification.clasificar` | **Transición** pendiente→clasificado | USER_FACING (diferido) |
| POST | `/operations/{id}/reclassify` (:196-244) | `corrections:correct` | CONTROL | `OperationalEventRead` | `classification.reclasificar` (409 si tuvo efectos) | **Transición** reclasificación OD-10.d | USER_FACING (diferido) |
| GET | `/operations/{id}/weight-evaluation` (:247-266) | `operations:read` | MULTI_UNIDAD | `WeightEvaluationRead` | `evaluar_pesajes` | Evaluación contra curva | USER_FACING |
| GET | `/operations/{id}` (:269-292) | `operations:read` | MULTI_UNIDAD | `OperationalEventDetailRead` (incluye `evidences` :305) | `get_event` | Detalle | USER_FACING |
| PUT | `/operations/{id}` (:295-303) | `operations:update` | MULTI_UNIDAD | `OperationalEventRead` | `update_event` (solo DRAFT/REGISTERED/RETURNED/REJECTED; `service.py:1137-1138`; `OperationalEventUpdate` extra=forbid :195-234) | **Edición pre-revisión** | USER_FACING |
| POST | `/operations/{id}/submit` (:310-317) | `operations:create` | MULTI_UNIDAD | `OperationalEventRead` | `submit_to_review` (REGISTERED/RETURNED/REJECTED→PENDING_REVIEW `service.py:1314-1317`) | **Transición** enviar a revisión | USER_FACING |
| POST | `/operations/{id}/cancel` (:320-327) | `operations:create` | MULTI_UNIDAD | `OperationalEventRead` | `cancel_event` (∉ NO_CANCELABLES `service.py:1338-1339`) | **Transición** →CANCELLED | USER_FACING |
| GET | `/operations/{id}/evidences` (:334-341) | `operations:read` | MULTI_UNIDAD | `list[EvidenceRead]` | `get_evidences` | Adjuntos | API_ONLY_BY_DESIGN (redundante con detalle) |
| POST | `/operations/{id}/evidences` (:344-392) | `operations:create` | MULTI_UNIDAD | `EvidenceRead` 201 | `create_evidence` (multipart `file`, `description`, `evidence_type`) | Subir adjunto | USER_FACING |
| GET | `/operations/{id}/evidences/{eid}/download` (:395-409) | `operations:read` | MULTI_UNIDAD | `FileResponse` | `get_evidence_for_download` | Descargar | USER_FACING |
| DELETE | `/operations/{id}/evidences/{eid}` (:412-419) | `operations:delete` | MULTI_UNIDAD | 204 | `delete_evidence` | Borrar adjunto | USER_FACING |

### 1.6 Revisión / Aprobación / Pasos — `review/router.py`

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| GET | `/review/pending` (:22-40) | `review:read` | MULTI_UNIDAD | NONE (`{events,total}`, ORM) | `get_pending_review_events` — **solo REGISTERED+PENDING_REVIEW** (`review/service.py:168`); parámetros aceptados: farm_id, lot_id, event_type, date_from, date_to, limit, offset (**no** `status`, **no** `operator_id`) | Cola de revisión | USER_FACING |
| POST | `/review/batches` (:47-54) | `review:review` | MULTI_UNIDAD | `ReviewBatchRead` 201 | `create_review_batch` (marca eventos PENDING_REVIEW `service.py:227`) | **Transición** lote de revisión | USER_FACING |
| GET | `/review/batches` (:57-66) | `review:read` | MULTI_UNIDAD | NONE (`{batches,total}`, ORM sin `actions` en `ReviewBatchRead` :18-29) | `get_batches` | Listar lotes | USER_FACING |
| POST | `/review/start/{id}` (:73-80) | `review:review` | MULTI_UNIDAD | NONE | `start_review` (PENDING_REVIEW→IN_REVIEW `service.py:266`) | **Transición** | USER_FACING |
| POST | `/review/return` (:83-90) | `review:review` | MULTI_UNIDAD | NONE | `return_to_operator` (`observations` min 10 `schemas.py:101`) | **Transición** →RETURNED | USER_FACING |
| POST | `/review/complete` (:93-100) | `review:review` | MULTI_UNIDAD | NONE | `complete_review` (IN_REVIEW→APPROVED si 1 nivel, si no →CORRECTED `service.py:323-355`) | **Transición** | USER_FACING |
| GET | `/approvals/pending` (:107-120) | `approvals:approve` | MULTI_UNIDAD | NONE (`{events,total}`) | `get_pending_approvals` (**solo CORRECTED** `service.py:463`) | Cola de aprobación | USER_FACING |
| POST | `/approvals/approve` (:123-130) | `approvals:approve` | MULTI_UNIDAD | NONE | `approve` | **Transición** →APPROVED (+reverso compensatorio si aplica) | USER_FACING |
| POST | `/approvals/reject` (:133-140) | `approvals:reject` | MULTI_UNIDAD | NONE | `reject` (`observations` min 10) | **Transición** →REJECTED | USER_FACING |
| POST | `/approvals/batch-approve` (:143-150) | `review:review` | MULTI_UNIDAD | NONE | `batch_approve` | **Transición** masiva | USER_FACING |
| POST | `/approvals/batch-reject` (:153-160) | `review:review` | MULTI_UNIDAD | NONE | `batch_reject` | **Transición** masiva | USER_FACING |
| GET | `/approval-steps` (:167-173) | `review:read` | CONTROL | NONE | `ApprovalStepService.get_steps` | Configuración del flujo | API_ONLY_BY_DESIGN |
| POST | `/approval-steps` (:176-183) | `review:create` | CONTROL | `ApprovalStepRead` 201 | `create_step` | Configuración | API_ONLY_BY_DESIGN |
| PUT | `/approval-steps/{id}` (:186-194) | `review:update` | CONTROL | `ApprovalStepRead` | `update_step` | Configuración | API_ONLY_BY_DESIGN |
| DELETE | `/approval-steps/{id}` (:197-204) | `review:delete` | CONTROL | 204 | `delete_step` | Configuración | API_ONLY_BY_DESIGN |
| POST | `/approval-steps/seed-defaults` (:207-214) | `review:create` | CONTROL | NONE | `seed_default_steps` | Semilla 1/2/3 niveles (`GA-REM-025:38`) | INTERNAL_ONLY |

### 1.7 Correcciones — `corrections/router.py`

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| POST | `/corrections` (:16-23) | `corrections:correct` | MULTI_UNIDAD | `CorrectionRead` 201 | `create_correction` (`field_name`, `original/corrected_value`, `reason` min 5 `schemas.py:8-15`) | **Transición** →CORRECTED con bitácora | USER_FACING |
| GET | `/corrections/event/{id}` (:26-33) | `corrections:read` | MULTI_UNIDAD | `list[CorrectionRead]` | `get_corrections_for_event` | Historial por evento | USER_FACING |
| GET | `/corrections` (:36-48) | `corrections:read` | MULTI_UNIDAD | NONE (`{corrections,total}`) | `get_corrections` | Listado | API_ONLY_BY_DESIGN |

### 1.8 Reversos — `reversals/router.py` (GA-REM-041 / OD-19)

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| POST | `/reversals` (:16-23) | `reversals:create` | MULTI_UNIDAD | `ReversalRead` 201 | `ReversalService.solicitar` (`event_id`, `reason` min 5) | **Transición** solicitar reverso: crea contrapartida en cola de revisión | USER_FACING (diferido, P4) |
| GET | `/reversals` (:26-34) | `reversals:read` | MULTI_UNIDAD | `ReversalListResponse` | `listar` | Listado | USER_FACING (diferido) |
| GET | `/reversals/event/{id}` (:37-43) | `reversals:read` | MULTI_UNIDAD | `list[ReversalRead]` | `por_evento` | Reversos de un original | USER_FACING (diferido) |

La aprobación del reverso no tiene ruta propia: se aprueba por `POST /approvals/approve` (`review/service.py:346` `new_status="reversed"`; `GA-REM-041 §3.3`).

### 1.9 Auditoría — `audit/router.py`

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| GET | `/audit` (:16-41) | `audit:read` | CORE | NONE (`{logs,total}`) | `list_logs` (11 filtros) | Bitácora | USER_FACING |
| GET | `/audit/{log_id}` (:44-51) | `audit:read` | CORE | `AuditLogRead` | `get_log` | Detalle | API_ONLY_BY_DESIGN |
| GET | `/audit/timeline/{entity_type}/{entity_id}` (:54-63) | `audit:read` | CORE | NONE | `get_entity_timeline` | Línea de tiempo por entidad | USER_FACING (sin consumidor, P4) |

### 1.10 Reportes — `reports/router.py` (14 rutas)

| Método | Ruta | Permiso | Alcance | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|
| GET | `/reports/kpis?lot_id` (:15-22) | `reports:read` | MULTI_UNIDAD | `get_all_kpis` → claves `mortality, feed_conversion, egg_production, hatchery_yield, animal_welfare, vaccination_efficiency, transfer_efficiency` (`reports/service.py:425-432`) | Agregado | USER_FACING |
| GET | `/reports/kpis/mortality` (:25-32) | `reports:read` | MULTI_UNIDAD | `get_kpi_mortality` | Individual (redundante con agregado) | API_ONLY_BY_DESIGN |
| GET | `/reports/kpis/feed-conversion` (:35-42) | ídem | ídem | `get_kpi_feed_conversion` | ídem | API_ONLY_BY_DESIGN |
| GET | `/reports/kpis/egg-production` (:45-52) | ídem | ídem | `get_kpi_egg_production` | ídem | API_ONLY_BY_DESIGN |
| GET | `/reports/kpis/hatchery` (:55-63) | ídem | UNIDAD_UNICA hatchery | `get_kpi_hatchery` (`hatchery_id` se acepta y se ignora :63) | Incubación | USER_FACING |
| GET | `/reports/kpis/animal-welfare` (:66-73) | ídem | MULTI_UNIDAD | `get_kpi_animal_welfare` (G-01) | Individual (en agregado) | API_ONLY_BY_DESIGN |
| GET | `/reports/kpis/vaccination-efficiency` (:76-83) | ídem | ídem | G-02 | Individual | USER_FACING |
| GET | `/reports/kpis/transfer-efficiency` (:86-93) | ídem | CONTRATO | G-03 | Individual | USER_FACING |
| GET | `/reports/kpis/afcr` (:96-103) | ídem | MULTI_UNIDAD | G-04 | Individual | USER_FACING |
| GET | `/reports/kpis/production-index` (:106-113) | ídem | ídem | G-05 (**no está en el agregado**) | Índice de producción | USER_FACING (sin consumidor, P4) |
| GET | `/reports/kpi/ipe/{lot_id}` (:116-126) | ídem | ídem | G-06 (OD-22) | IPE | USER_FACING |
| GET | `/reports/kpi/weight-uniformity/{lot_id}` (:129-136) | ídem | ídem | G-07 | CV% | USER_FACING |
| GET | `/reports/lot/{lot_id}` (:139-146) | ídem | ídem | `get_lot_report` | Informe de lote | USER_FACING |
| GET | `/reports/sap-comparison` (:149-156) | ídem | CONTRATO | `get_sap_comparison` | Comparativo SAP | USER_FACING |

Ninguna ruta de reportes declara `response_model`.

### 1.11 Dashboard — `dashboard/router.py`

| Método | Ruta | Permiso | Alcance | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|
| GET | `/dashboard/mobile` (:13-19) | `dashboard:read` | MULTI_UNIDAD | `get_mobile_dashboard` (`today_events, pending_corrections, approved_today, quick_actions` `dashboard/service.py:76-79`) | KPIs móvil | USER_FACING |
| GET | `/dashboard/admin` (:22-28) | `dashboard:read` | MULTI_UNIDAD | `get_admin_dashboard` (`total_events, by_status, pending_review, pending_approval, top_event_types, lots_by_type, mortality_trend, active_alerts` :143-151) | KPIs web | USER_FACING |

### 1.12 Unidades de negocio — `business_units/router.py` (GA-REM-040 fase 7; lógica en `admin.py`)

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| GET | `/business-units` (:94-101) | `business_units:read` | CONTROL | `list[HabilitacionRead]` | `admin.listar_habilitaciones` (:115-135) | Las 4 unidades y su estado | USER_FACING |
| PATCH | `/business-units/{code}/enable` (:104-121) | `business_units:update` | CONTROL | `HabilitacionRead` | `admin.fijar_habilitacion(True)` (:138-216) | **Transición** habilitar | USER_FACING |
| PATCH | `/business-units/{code}/disable` (:124-143) | `business_units:update` | CONTROL | `HabilitacionRead` | `fijar_habilitacion(False)` — termina concesiones vivas (OD-23 :178-193) | **Transición** deshabilitar | USER_FACING |
| GET | `/business-units/{code}/grant-candidates` (:146-162) | `business_units:create` | CONTROL | `list[CandidatoRead]` | `admin.candidatos_de_concesion` (:265-314) | A quién conceder | USER_FACING |
| GET | `/users/{id}/business-units` (:167-184) | `business_units:read` | CONTROL | `list[ConcesionRead]` | `admin.listar_concesiones` (:239-262) | Concesiones del usuario | USER_FACING |
| POST | `/users/{id}/business-units` (:187-207) | `business_units:create` | CONTROL | `ConcesionRead` 201 | `admin.conceder` (:317-391; OD-15.a auto-concesión 403) | **Transición** conceder | USER_FACING |
| DELETE | `/users/{id}/business-units/{code}` (:210-229) | `business_units:delete` | CONTROL | `ConcesionRead` | `admin.revocar` (:394-429) | **Transición** revocar | USER_FACING |

### 1.13 SAP — `integrations/sap/router.py` (solo con `FEATURE_SAP_ENABLED`)

| Método | Ruta | Permiso | Alcance | response_model | Servicio | Significado | Clase |
|---|---|---|---|---|---|---|---|
| POST | `/sap/references/import` (:20-27) | `sap:send_sap` | CONTROL | NONE 201 | `import_references` (`SapReferenceImportRequest.references: list[SapReferenceCreate]` `schemas.py:45-47`) | Carga manual de referencias | USER_FACING (sin consumidor, P4) |
| GET | `/sap/references` (:30-42) | `sap:read` | CONTROL | NONE (`{references,total}`) | `list_references` | Referencias | USER_FACING |
| POST | `/sap/consolidate` (:49-61) | `sap:send_sap` | CONTRATO | NONE 201 (lista) | `consolidate_approved` | **Transición** APPROVED→CONSOLIDATED | USER_FACING |
| GET | `/sap/consolidated` (:64-85) | `sap:read` | CONTRATO | `{consolidated: list[ConsolidatedMovementRead], total}` | `list_consolidated` | Consolidados | USER_FACING (sin consumidor) |
| POST | `/sap/export` (:92-103) | `sap:send_sap` | CONTRATO | `SapExportResponse` (`sync_job_id, payloads_created, status, message`) | `export_to_sap` | **Transición** exportar (manual: «preparado», GA-REM-010) | USER_FACING |
| POST | `/sap/retry` (:106-117) | `sap:send_sap` | CONTRATO | NONE (`{retried,message}` `service.py:462`) | `retry_failed` | **Transición** reintentar fallidos | USER_FACING (sin consumidor) |
| GET | `/sap/sync/jobs` (:124-133) | `sap:read` | CONTRATO | NONE (`{jobs,total}`) | `list_sync_jobs` | Bitácora | USER_FACING |
| GET | `/sap/payloads` (:136-148) | `sap:read` | CONTRATO | NONE (`{payloads,total}`) | `list_payloads` (filtro `status`) | Documentos | USER_FACING |
| GET | `/sap/errors` (:151-159) | `sap:read` | CONTRATO | NONE (`list[SapErrorItem]`) | `list_errors` | Fallidos | USER_FACING (sin consumidor) |
| GET | `/sap/connection-check` (:166-184) | `sap:read` | CONTROL | NONE | `adapter.check_connection` | Diagnóstico (`delivers_to_sap`, `mode`) | USER_FACING |

### 1.14 Infra

| Método | Ruta | Permiso | Clase |
|---|---|---|---|
| GET | `/health` (`main.py:127-129`, sin prefijo) | PÚBLICA | INTERNAL_ONLY |

### 1.15 Rutas de transición de estado (lista explícita)

`POST /operations/{id}/submit` · `POST /operations/{id}/cancel` · `PUT /operations/{id}` (edición pre-revisión) · `POST /review/batches` · `POST /review/start/{id}` · `POST /review/return` · `POST /review/complete` · `POST /approvals/approve` · `POST /approvals/reject` · `POST /approvals/batch-approve` · `POST /approvals/batch-reject` · `POST /corrections` · `POST /reversals` (solicitud; aprobación vía `/approvals/approve`) · `GET /reversals`, `GET /reversals/event/{id}` (lectura) · `POST /lots/{id}/close` · `POST /lots/activate-manual` · `POST /lots/{id}/phases` · `GET /operations/pending-classification` · `POST /operations/{id}/classify` · `POST /operations/{id}/reclassify` · `PATCH /business-units/{code}/enable|disable` · `POST|DELETE /users/{id}/business-units[/{code}]` · `POST /sap/consolidate` · `POST /sap/export` · `POST /sap/retry` · `POST /sap/references/import` · `POST /operations/{id}/evidences` · `GET …/evidences/{eid}/download` · `DELETE …/evidences/{eid}` · `PATCH /notifications/{id}/read` · `PATCH /operations/alerts/{id}/resolve` · `PUT /roles/{id}` (`is_active=false`) · `DELETE /users/{id}`. Exportaciones Excel/PDF: **no existe ruta backend**; son 100 % cliente (`frontend/src/utils/export.ts`).

---

## PARTE 2 — INVENTARIO DE SERVICIOS DEL FRONTEND

Convención: «Llamadores» = ficheros fuera de `services/`, `hooks/` y tests. Los hooks se listan aparte; **ningún hook de datos tiene importadores**, de modo que «solo hook» ≡ muerto en producción.

### 2.1 `services/api.ts`
Cliente axios base `/api/v1`, adjunta Bearer desde memoria (:52-58), refresco automático en 401 con `POST /refresh` (:30-49) y `forceLogout` (:74-77). Registrado en `main.tsx:24-29`. **Vivo.**

### 2.2 `auth.service.ts` — **0 llamadores reales** (la única coincidencia `RolesPage.tsx:6` es un comentario)

| Método | HTTP | Ruta | Backend | Llamadores |
|---|---|---|---|---|
| `login` (:36-37) | POST | `/login` | ✓ | ninguno (`auth.store.ts:126` llama `api.post` directo) |
| `refresh` (:39-40) | POST | `/refresh` | ✓ | ninguno (`api.ts:37`) |
| `getMe` (:42-43) | GET | `/me` | ✓ (tipo `UserResponse` incompleto vs `SessionRead`) | ninguno (`auth.store.ts:143`) |
| `listUsers` (:45-46) | GET | `/users` | ✓ | ninguno (`UsersPage.tsx:40`, `ReviewCenter.tsx:109`) |
| `createUser` (:48-49) | POST | `/users` | ✓ | ninguno (`UsersPage.tsx:83`) |
| `updateUser` (:51-52) | PUT | `/users/{id}` | ✓ (pero tipa `password?` que el backend rechaza) | ninguno (`UsersPage.tsx:79,91`) |
| `deactivateUser` (:54-55) | DELETE | `/users/{id}` | ✓ | ninguno (`UsersPage.tsx:88`) |
| `listRoles` (:57-58) | GET | `/roles` | ✓ | ninguno (`RolesPage.tsx:37`, `UsersPage.tsx:55`) |
| `createRole` (:60-61) | POST | `/roles` | ✓ (sin `permissions`, contrato incompleto) | ninguno (`RolesPage.tsx:81`) |
| `updateRole` (:63-64) | PUT | `/roles/{id}` | ✓ | ninguno (`RolesPage.tsx:80,94`) |

### 2.3 `lots.service.ts` — solo consumido por `useLots.ts` (hook muerto)

| Método | HTTP | Ruta | Backend | Llamadores |
|---|---|---|---|---|
| `list` (:39-40) | GET | `/lots` | ✓ | `useLots.ts:20,50` (muerto) |
| `get` (:42-43) | GET | `/lots/{id}` | ✓ | `useLots.ts:49` (muerto) |
| `create` (:45-46) | POST | `/lots` | ✓ | ninguno (`LotFormPage.tsx:133` directo) |
| `update` (:48-49) | PUT | `/lots/{id}` | ✓ | **ninguno** — no hay edición de lote en UI |
| `close` (:51-52) | POST | `/lots/{id}/close` | ✓ | ninguno (`LotDetailPage.tsx:111` directo) |
| `activateManual` (:54-55) | POST | `/lots/activate-manual` | ✓ | **ninguno** — P-11 sin UI |
| `getPhases` (:57-58) | GET | `/lots/{id}/phases` | ✓ | `useLots.ts:51` (muerto) |
| `addPhase` (:60-61) | POST | `/lots/{id}/phases` | ✓ | ninguno (`LotDetailPage.tsx:125` directo, payload inválido) |
| `getOpeningBalance` (:63-64) | GET | `/lots/{id}/opening-balance` | ✓ | **ninguno** |
| `getTraceability` (:66-67) | GET | `/lots/{id}/traceability` | ✓ | ninguno (`TraceabilityTree.tsx:124` directo) |

### 2.4 `operations.service.ts`

| Método | HTTP | Ruta | Backend | Llamadores |
|---|---|---|---|---|
| `list` (:22-32) | GET | `/operations` | ✓ | `useOperations.ts:22,55,83` (muerto) |
| `get` (:34-35) | GET | `/operations/{id}` | ✓ | ninguno (`OperationDetailPage.tsx:64`, `ReviewDetail.tsx:35`, `CorrectionForm.tsx:30` directo) |
| `create` (:37-38) | POST | `/operations` | ✓ | ninguno (`OperationFormPage.tsx:452` directo) |
| `update` (:40-41) | PUT | `/operations/{id}` | ✓ | **ninguno** — sin UI de edición |
| `submit` (:43-44) | POST | `/operations/{id}/submit` | ✓ | **`OperationDetailPage.tsx:132`** (vivo) |
| `cancel` (:46-47) | POST | `/operations/{id}/cancel` | ✓ | **ninguno** — sin UI de anulación |
| `getEventTypes` (:49-50) | GET | `/operations/event-types` | ✓ | **ninguno** (catálogo duplicado en `data/processCatalog.ts:205-268`) |

### 2.5 `masters.service.ts` — solo `useMasters.ts` (muerto)

`list` (:11-12), `get` (:14-15), `create` (:17-18), `update` (:20-21), `deactivate` (:23-24) → `/masters/{entity}[/{id}]` ✓ — llamadores `useMasters.ts:13,27,33,39` (muerto). `listFarms/listHouses/listHatcheries/listGeneticLines/listBreeds/listFeedTypes` (:27-43) → `useMasters.ts:59-63` (muerto). `listCorrectionTypes` (:45-46), `getHousesByFarm` (:48-49), `getIncubatorsByHatchery` (:51-52) → **0 llamadores** (rutas backend `masters/router.py:132-174` sin consumidor).

### 2.6 `review.service.ts` — solo `useReview.ts` (muerto)

| Método | HTTP | Ruta | Backend | Nota | Llamadores |
|---|---|---|---|---|---|
| `getPending` (:24-35) | GET | `/review/pending` | ✓ | envía `status`, `operator_id` que el backend **no acepta** (`review/router.py:22-33`); tipa `events: ApprovalAction[]` (semánticamente incorrecto) | `useReview.ts:25` (muerto) |
| `createBatch` (:37-38) | POST | `/review/batches` | ✓ | | `useReview.ts:48` (muerto) |
| `listBatches` (:40-41) | GET | `/review/batches` | ✓ | tipa `ReviewBatch[]` pero el backend devuelve `{batches,total}` (`review/router.py:66`) → contrato desalineado | **ninguno** |
| `startReview` (:43-44) | POST | `/review/start/{id}` | ✓ | | `useReview.ts:36` (muerto) |
| `returnEvent` (:46-47) | POST | `/review/return` | ✓ | `observations?` opcional; backend exige ≥10 | `useReview.ts:40` (muerto) |
| `completeReview` (:49-50) | POST | `/review/complete` | ✓ | | `useReview.ts:44` (muerto) |

### 2.7 `approvals.service.ts` — solo `useApprovals.ts` (muerto)

`getPending` (:4-5) `/approvals/pending` ✓ · `approve` (:7-8) · `reject` (:10-11) · `batchApprove` (:13-14) · `batchReject` (:16-17) → todas ✓; llamadores `useApprovals.ts:15,26,30,34,38` (muerto). Las páginas usan `api.post` directo (`ApprovalPanel.tsx:40,54,70,100,119`; `ReviewDetail.tsx:72,75`).

### 2.8 `corrections.service.ts` — **0 llamadores**

`create` (:16-24) `/corrections` ✓ (`CorrectionForm.tsx:52` directo) · `getByEvent` (:26-27) `/corrections/event/{id}` ✓ (`ReviewDetail.tsx:40` directo) · `list` (:29-30) `/corrections` ✓ pero tipa `CorrectionLog[]` vs `{corrections,total}` (`corrections/router.py:48`) — **0 llamadores**.

### 2.9 `audit.service.ts` — **0 llamadores**

`list` (:18-28) `/audit` ✓ pero tipa `AuditLog[]` vs `{logs,total}` (`audit/router.py:41`); `AuditPage.tsx:72` directo · `get` (:30-31) `/audit/{id}` — **0** · `getTimeline` (:33-34) `/audit/timeline/{type}/{id}` — **0**.

### 2.10 `reports.service.ts` — solo `useReports.ts` (muerto)

`getKpis` (:24-25) `/reports/kpis` ✓ (`useReports.ts:16`) · `getMortalityKpi` (:27-28) · `getFeedConversionKpi` (:30-31) · `getEggProductionKpi` (:33-34) · `getHatcheryKpi` (:36-37) → **0** · `getLotReport` (:39-40) (`useReports.ts:37`) · `getSapComparison` (:42-43) → **0** (`SapComparisonPage.tsx:14` directo).

### 2.11 `dashboard.service.ts` — **0 llamadores** (`getMobile` :23-24, `getAdmin` :26-27; `DashboardPage.tsx:94-95` directo).

### 2.12 `sap.service.ts` — solo `useSap.ts` (muerto)

| Método | Ruta | Backend | Nota | Llamadores |
|---|---|---|---|---|
| `importReferences` (:34-35) | POST `/sap/references/import` | ✓ | **cuerpo obsoleto**: envía `{ref_type, entries}`; el backend exige `{references:[{ref_type,sap_code,…}]}` (`sap/schemas.py:45-47`) → 422 si se usara | `useSap.ts:47` (muerto) |
| `listReferences` (:37-38) | GET `/sap/references` | ✓ | | `useSap.ts:18` (muerto); páginas directas (`SapManagerPage.tsx:39`, `OperationFormPage.tsx:352-353`) |
| `consolidate` (:40-41) | POST `/sap/consolidate` | ✓ | | `useSap.ts:35` (muerto) |
| `listConsolidated` (:43-44) | GET `/sap/consolidated` | ✓ | | **ninguno** |
| `exportToSap` (:46-47) | POST `/sap/export` | ✓ | | `useSap.ts:41` (muerto) |
| `retry` (:49-50) | POST `/sap/retry` | ✓ | | **ninguno** |
| `listSyncJobs` (:52-53) | GET `/sap/sync/jobs` | ✓ | | `useSap.ts:19` (muerto) |
| `listPayloads` (:55-56) | GET `/sap/payloads` | ✓ | | `useSap.ts:20` (muerto) |
| `listErrors` (:58-59) | GET `/sap/errors` | ✓ | | **ninguno** |
| `checkConnection` (:61-62) | GET `/sap/connection-check` | ✓ | | `useSap.ts:21` (muerto) |

### 2.13 `businessUnits.service.ts` — **vivo** (7/7 con llamadores)

`getCompanyBusinessUnits` (:34) → `UnitAccessPage.tsx:54`, `UserBusinessUnitsButton.tsx:57` · `enableCompanyBusinessUnit` (:40) → `UnitAccessPage.tsx:120` · `disableCompanyBusinessUnit` (:46) → `:121` · `getUserBusinessUnits` (:52) → `UserBusinessUnitsButton.tsx:58` · `getGrantCandidates` (:58) → `UnitAccessPage.tsx:86` · `grantBusinessUnit` (:64) → `UnitAccessPage.tsx:135`, `UserBusinessUnitsButton.tsx:82` · `revokeBusinessUnit` (:70) → `UnitAccessPage.tsx:150`, `UserBusinessUnitsButton.tsx:96`.

### 2.14 `notifications.ts` — **vivo**

`listNotifications` (:35-38) → `NotificationBell.tsx:76` · `getUnreadCount` (:40-43) → `:45` · `markRead` (:45-48) → `:90` · `destino` (:56-61) → `:98` (solo `operational_event`; `sap_payload` no navega por diseño :53-54).

### 2.15 `weightCurves.ts` — **vivo**

`listWeightCurves` (:46-50) → `WeightCurvesPage.tsx:65` · `getGeneticLine` (:52-55) → `:64` · `uploadWeightCurve` (:57-67) → `:111` · `activateWeightCurve` (:69-72) → `:131` · `parsearTabla` (:85-116) → `:94`.

### 2.16 Hooks (`hooks/*.ts`) — importadores en producción

| Hook | Servicio | Importadores | Observación |
|---|---|---|---|
| `useApprovals` (`useApprovals.ts:5-45`) | approvals | **0** | muerto |
| `useLots` (`useLots.ts:10-34`) / `useLotDetail` (:36-68) | lots | **0** | muerto; además `useLotDetail:50` pide `/lots` y lo guarda como «kpis» (defecto latente) |
| `useMasters` (:4-44) / `useMasterOptions` (:47-78) | masters | **0** | muerto; `:70` traga errores en silencio |
| `useOperations` (:12-42) / `useOperationDetail` (:44-72) / `useMyPending` (:74-98) | operations | **0** | muerto; `useOperationDetail:55-59` lista 100 y busca por id (patrón GA-REM-011 C-03 ya corregido en páginas) |
| `useKpis` (:5-26) / `useLotReport` (:28-47) | reports | **0** | muerto |
| `useReview` (:15-56) | review | **0** | muerto |
| `useSap` (:5-56) | sap | **0** | muerto (incluye `importReferences` con cuerpo obsoleto) |
| `useSidebar`, `useMediaQuery` | — | **0** | muertos (UI) |
| `useTelegram` / `useTelegramBackHandler` / `initTelegramEarly` | — | `App.tsx:7,173,202`, `main.tsx:7,12` | vivo |

### 2.17 Stores (`stores/*.ts`)

| Store | Acciones con red | Llamadores | Observación |
|---|---|---|---|
| `auth.store.ts` | `login` → POST `/login` (:126); `fetchMe` → GET `/me` (:143); `logout` cliente (:133-139) | `LoginPage.tsx:37`, `App.tsx:179`, `main.tsx:28`, `Header.tsx:148`, `Sidebar.tsx:154`, `MobileDrawer.tsx:203` | vivo; no hay revocación server-side de tokens |
| `company.store.ts` | `fetchCompanies` → GET `/masters/companies?limit=100` (:39); `switchCompany` → POST `/switch-company` (:51) + `fetchMe` | `Header.tsx:22,39`, `auth.store.ts:156` | vivo |
| `ui.store.ts` | — | **0** importadores fuera de sí mismo | muerto (duplica toasts de `components/Toast.tsx`) |
| `theme.store.ts` | — | solo `DarkModeToggle.tsx` (que a su vez tiene 0 importadores); `main.tsx:18-23` lee `theme-storage` | efectivamente muerto |
| `i18n.store.ts` | — | 0 | muerto (la i18n vive en `src/i18n`) |

### 2.18 Métodos con CERO llamadores y si representan funcionalidad prometida

| Método | ¿Funcionalidad prometida? | Evidencia |
|---|---|---|
| `lotsService.activateManual` | **Sí** — proceso P-11 «saldo de apertura / lotes ya en curso» | `GA-REM-005-…:390` (P-11), `GA-REM-028-…:7,39,82`, `GA-REM-002-…:518` (AC22 S05) |
| `lotsService.update` | **Sí** — `PUT /lots/{id}` con `planned_close_date`, `area_id`, etc. (`lots/schemas.py:50-74`) | `GA-REM-040:1440,1601,1612` |
| `lotsService.getOpeningBalance` | Parcial (el informe de lote ya muestra `opening_balance`: `LotReportPage.tsx:89-98`) | — |
| `operationsService.cancel` | **Sí** — anulación es acto de operador con `operations:create` | `GA-REM-042:51`, `GA-REM-005:633`, `GA-REM-006:211` |
| `operationsService.update` | **Sí** — edición en DRAFT/REGISTERED/RETURNED/REJECTED | `GA-REM-023:80,115` («docs/12 §3 le reconoce la edición»), `GA-REM-006:208`, `GA-REM-042:38,51` |
| `operationsService.getEventTypes` | No (catálogo estático) | duplicado en `processCatalog.ts` |
| `reviewService.listBatches` | Parcial (ReviewDetail lo llama directo y espera `actions` que nunca llegan) | ver P3 |
| `correctionsService.list` | No (AuditPage cubre con `?action=corrected`) | `AuditPage.tsx:70` |
| `auditService.get`, `getTimeline` | **Sí** (línea de tiempo por entidad, `docs/13`); sin superficie | — |
| `reportsService.getMortalityKpi/FeedConversion/EggProduction` | No (cubiertos por `/reports/kpis`) | `reports/service.py:425-432` |
| `sapService.retry` | **Sí** — reintento de fallidos; existe aviso `sap_send_failed` sin acción | `notifications.ts:16`, `sap/service.py:457` |
| `sapService.importReferences` | **Sí** en modo manual (`GA-REM-010:64,88`): sin UI no hay forma de cargar referencias salvo API | cuerpo del servicio además obsoleto |
| `sapService.listConsolidated`, `listErrors` | **Sí** (la página SAP tiene pestañas «Errores» que no usan `/sap/errors`) | `SapManagerPage.tsx:249-273` |
| `mastersService.getHousesByFarm/getIncubatorsByHatchery/listCorrectionTypes` | No (filtrado en cliente) | — |
| `authService.*`, `dashboardService.*` | No (duplicados por stores/páginas) | — |

---

## PARTE 3 — INVENTARIO DE ACCIONES DEL FRONTEND

Rutas de `App.tsx:207-283`. Columnas: Control (etiqueta/clave i18n) · Handler · HTTP · Consecuencia BD · Éxito · Error · Flags.

### 3.1 `/login` — `LoginPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Submit `auth.login` (:135-155) | `onSubmit` :33-47 → `useAuthStore.login` → `auth.store.ts:125-131` | POST `/login` + GET `/me` | `last_login`, auditoría login | toast + `navigate('/')` :38-39 | `setError` + toast :40-44 | — |
| Toggle idioma (:161-167) | `toggleLang` :49 | — | — | — | — | — |

### 3.2 Layout — `Header.tsx`, `Sidebar.tsx`, `MobileNav.tsx`, `AppLayout.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Selector de empresa (super-admin) `company.selector` (`Header.tsx:78-127`) | `handleSwitchCompany` :37-40 → `company.store.switchCompany` :47-61 | POST `/switch-company` + GET `/me` (+ GET `/masters/companies` :22) | auditoría P-09 | tokens nuevos, `initFromUser` | `set({isSwitching:false}); throw` :57-60 — **el Header no captura**: error silencioso (sin toast) | error no mostrado |
| `auth.logout` (`Header.tsx:147-152`, `Sidebar.tsx:153-162`) | `logout` cliente | ninguna | ninguna | limpia storage | — | no hay revocación en servidor |
| Campana (`Header.tsx:53,184`) | ver 3.19 | | | | | |
| Sidebar hubs → `/menu/:key` (`Sidebar.tsx:22-35`) | Link | — | — | — | — | — |
| MobileNav (`MobileNav.tsx:18-22`): `/menu/poultry`, `/`, `/kpi` | Link | — | — | — | — | — |
| `MobileDrawer.tsx` | — | — | — | — | — | **Componente no montado en ningún sitio** (`AppLayout.tsx:13-20` monta Sidebar/Header/MobileNav; único «importador» es un comentario en `navigationConfig.ts:8`). Huérfano. |

### 3.3 `/` y `/kpi` — `DashboardPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:93-106) | effect | GET `/dashboard/mobile` (móvil y no `/kpi`) o `/dashboard/admin` | — | render | `setError` + toast | — |
| «Reintentar» (:135-140) | `window.location.reload()` | — | — | — | — | recarga completa (tosco) |
| Resolver alerta ✕ `alerts.resolve` (:62-68) gate `operations:update` | `handleResolveAlert` :108-116 | PATCH `/operations/alerts/{id}/resolve` | `is_resolved` | filtro local + toast | toast | — |
| Atajos móviles a etapas (:390-427) | Link `stagePathForKey` | — | — | — | — | gate `stageVisibleForSession` ✓ |

### 3.4 `/lots` — `LotListPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:26-39) | `fetchLots` | GET `/lots?limit=100` | — | render | **`console.error` solo** (:33) — el usuario ve «sin lotes» | error indistinguible de vacío |
| Filtro tipo de ave (:61-72) | client-side `filter` :30 | — | — | — | — | `BIRD_TYPE_KEYS` (:9) omite `hatchery`; no usa `status/farm_id/search` del backend; sin paginación (>100 lotes invisibles) |
| «Nuevo lote» `lots.newLot` (:53-57) gate web + `lots:create` | Link `/lots/new` | — | — | — | — | — |
| Ver detalle (:79,119) | Link `/lots/{id}` | — | — | — | — | — |

### 3.5 `/lots/new` — `LotFormPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga maestros (:82-109) | effect | GET `/masters/{farms,houses,genetic-lines,breeds,areas}?limit=100` | — | selects | `allSettled` silencioso | sin aviso si falla un catálogo |
| Curva activa (:67-79) | effect | GET `/masters/genetic-lines/{id}/weight-curves` | — | aviso `curves.lotWillUse`/`noActiveCurve` | silencioso | — |
| Submit `lots.create` (:302-304) | `onSubmit` :116-139 | POST `/lots` | fila `lots` (+`weight_curve_id`, `area_id`, `planned_close_date`) | toast + `navigate('/lots/{id}')` :134-135 | toast `detail` :137 | — |
| Cancelar/Atrás (:147-153, :299) | `navigate('/lots')` | — | — | — | — | — |

### 3.6 `/lots/:id` — `LotDetailPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:44-73) | effect | GET `/lots/{id}`; `allSettled`: `/reports/kpis`, `/operations?lot_id&limit=50`, `/lots/{id}/phases`, `/reports/kpi/ipe/{id}`, `/reports/kpi/weight-uniformity/{id}`, `/operations/alerts?lot_id…` | — | render | `console.error` (:67) → «lote no encontrado» | error ≡ inexistente |
| **«Iniciar Producción»** `lots.transitionToProduction` (:174-182) gate `lots:create` + cría | `handleTransitionPhase` :121-138 | POST `/lots/{id}/phases` con `{phase_code, start_date, start_population_male, start_population_female}` (:125-130) | **ninguna**: `LotPhaseCreate` exige `lot_id:int` y `phase_id:int` y no conoce `phase_code` (`lots/schemas.py:98-105`) → **422 siempre** | refetch fases (:131) que nunca ocurre | **`console.error` solo** (:134) — el modal se cierra (:122) y el botón deja de cargar sin mensaje | **ACCIÓN MUERTA** (transición cría→producción imposible desde UI) |
| «Cerrar Lote» `lots.closeButton` (:185-195) gate `lots:create` | `handleCloseLot` :107-119 | POST `/lots/{id}/close` | `status=closed`, `end_date` | tarjeta resumen (:199-212) + estado local | **`console.error` solo** (:115) — sin toast (p.ej. BR de cierre con eventos pendientes se pierde) | error silencioso |
| Resolver alerta (:445-447) gate `operations:update` | `handleResolveAlert` :75-83 | PATCH `/operations/alerts/{id}/resolve` | `is_resolved` | filtro local + toast | toast | — |
| Atajos «Registrar operación» (:228-242) gate `operations:create` | Link `/operations/new?type&lot_id` | — | — | — | — | usa `STAGE_OPERATIONS` (catálogo estático) |
| Árbol de trazabilidad (:460) | ver 3.20 | | | | | |
| — | — | — | — | — | — | **No hay** enlace a `/reports/lot/{id}`, ni edición de lote (`PUT /lots`), ni activación manual, ni visualización del saldo de apertura |

### 3.7 `/masters/:entity` — `MasterListPage.tsx` (parametrizada, 20 entidades `App.tsx:135-166`)

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga/búsqueda/paginación (:46-66, :136-145, :164-174) | `fetchItems` | GET `/masters/{entity}?skip&limit=20&search` (+`X-Total-Count` :57-58) | — | tabla | `console.error` (:60) | error ≡ vacío |
| «Nuevo» `common.new` (:146-148) gate `masters:create`; «Editar» (`DataTable.tsx:91-98`) gate `masters:update` | `handleSave` :87-103 | POST/PUT `/masters/{entity}[/{id}]` con `formValues` (strings) | fila | cierra modal + refetch :96-97 | `formError` con `detail` :99 | campos = columnas de listado (`App.tsx:136-165`): p. ej. `houses` sin `farm_id`, `incubators` sin `hatchery_id`; `searchFields` prop ignorada (:25) — auditoría de formularios aparte |
| «Eliminar» (`DataTable.tsx:99-106`) gate `masters:delete` | `handleDelete` :106-118 | DELETE `/masters/{entity}/{id}` | baja lógica | refetch :112 | **`console.error` solo** (:114) — modal queda abierto sin mensaje | error silencioso |
| `genetic-lines` → «Gestionar curvas» (`App.tsx:242-245`) | `navigate` | — | — | — | — | — |

### 3.8 `/masters/genetic-lines/:id/weight-curves` — `WeightCurvesPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:59-76) | `refrescar` | GET `/masters/genetic-lines/{id}`, GET `…/weight-curves` | — | tabla | `errorCarga` visible | ✓ |
| «Subir curva» `curves.upload` (:161-163, modal :239-309) gate `masters:create` | `subir` :101-126 | POST `/masters/weight-curves` JSON (CSV parseado en cliente) | fila curva + puntos | cierra + refetch :117-118 | errores por fila `detail.errores` :120-122 | ✓ |
| «Activar» `curves.activate` (:219-227) gate `masters:update` | `activar` :128-138 | PUT `/masters/weight-curves/{id}/activate` | `is_active` exclusivo | refetch | `errorCarga` | ✓ |
| «Ver» (:213-218) | modal local | — | — | — | — | — |

### 3.9 `/menu/:menuKey`, `/poultry`, `/poultry/:birdType/:phase?` — `MenuHubPage`, `ProcessHubPage`, `ProcessStagePage`

| Control | Handler | HTTP | Flags |
|---|---|---|---|
| Tarjetas hub (`MenuHubPage.tsx:129-147`) | `handleSelect` :88-94 → drill-in o `navigate(item.to)` | — | árbol filtrado por sesión ✓ (:45) |
| Tiles de etapa (`ProcessHubPage.tsx:60-115`) | Link `stagePathForKey` | — | `/poultry` no enlazado desde ningún sitio (huérfano) |
| Tiles de operación (`OperationTile.tsx:60-73`) / Timeline «Registrar operación» (`StageTimeline.tsx:155-164` → `ProcessStagePage.tsx:47-50`) | Link/`navigate('/operations/new?type=…')` | — | `sessionStorage.operationBackTarget` |
| «Ver historial» (`ProcessStagePage.tsx:118-123`) | Link `/operations` | — | solo web; móvil no tiene acceso a `/operations` salvo tras guardar (`OperationFormPage.tsx:455`) |
| Toggle grid/secuencia (:82-96) | estado local | — | `completedStages=[]` fijo (:111-112): la línea de tiempo nunca marca completado |

### 3.10 `/operations` — `OperationListPage.tsx`

| Control | Handler | HTTP | Éxito | Error | Flags |
|---|---|---|---|---|---|
| Carga/filtros (:23-46, :61-73) | `fetchEvents` | GET `/operations?limit=100[&lot_id][&event_type]`; filtro de etapa en cliente (:36-40) | lista | **`catch { setEvents([]) }`** (:42) — error ≡ sin resultados | sin paginación (>100 invisibles) |
| «+ Crear» (:55-57) | Link `/menu/poultry` | — | — | — | — |
| Enlace por fila etiquetado **`common.edit`** (:89) | Link `/operations/{id}` (detalle, **no** edición) | — | — | — | **etiqueta engañosa**: no existe edición |

### 3.11 `/operations/new` — `OperationFormPage.tsx` (asistente de 3 pasos, 26 `case` de tipo)

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga catálogos (:342-379) | effect | GET `/lots?limit=100`; `/sap/references?ref_type=transfer_order|purchase_order&limit=50`; 14× `/masters/*?limit=100` | — | selects | `lotsLoadError` visible (:2088); resto silencioso | referencias SAP silenciosas si el router SAP no está montado |
| Paso 1 etapas (:1831-1845) | `goToStep2` | — | — | — | — | **no** aplica `stageVisibleForSession` (a diferencia de `ProcessHubPage.tsx:21`): permite elegir una unidad no concedida y falla en el POST |
| Paso 2 operación (:1877-1886) | `chooseOperation` | — | — | — | — | `categoriesForStage` estático |
| Selector orden SAP (:1937-2039) | `setValue('sap_document_ref')` | — | — | — | — | R-189 F-01 ✓ |
| Submit `common.save` (:2113-2116) | `onSubmit` :381-462 (serializadores `operationPayload.ts`) | POST `/operations` | evento + submodelos; `status` inicial | banner + toast + `navigate('/operations')` tras 1,5 s (:453-455) | banner + toast `getErrorMessage` (:456-460) | navega a `/operations` también para móviles (ruta sin entrada de menú móvil) |
| Indicadores de rango (`RangeIndicator` :63-80) | — | — | — | — | — | **datos codificados**: `thermalCurves.ts:20-78` (Ross/Cobb) y `INCUBATOR/HATCHER_*_RANGE` (:24-27) — referencia UI, no del backend |
| Atrás paso 3 (:1898-1915) | `navigate(operationBackTarget|'/menu/poultry')` | — | — | — | — | — |

### 3.12 `/operations/:id` — `OperationDetailPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:63-72) | `loadEvent` | GET `/operations/{id}` (`evidences` incluidas :66) | — | render | `setError` + toast | ✓ |
| «Enviar/Reenviar a revisión» (:183-194) gate `operations:create`+unidades, estados `registered|returned|rejected` (:26,120-121) | `handleSubmitToReview` :127-144 → `operationsService.submit` | POST `/operations/{id}/submit` | `status=pending_review` | toast + `loadEvent()` (:142) | toast + `loadEvent()` | ✓ (GA-FE-05) |
| Subir evidencia (:326-350) gate `operations:create` | `handleFileChange` :76-103 | POST `/operations/{id}/evidences` multipart | fila `evidences` + fichero | append local + toast (:96-99) | toast | — |
| Descargar/previsualizar (:288-295) | `handlePreview/handleDownload` :146-164 | GET `…/evidences/{eid}/download` blob | — | descarga/modal | toast | — |
| Borrar evidencia (:296-304) gate `operations:delete` | `handleDelete` :105-114 | DELETE `…/evidences/{eid}` | borrado | filtro local + toast | toast | — |
| Evaluación de peso (:230 → `WeightEvaluation.tsx:48-54`) | effect | GET `/operations/{id}/weight-evaluation` | — | render | `setDatos(null)` silencioso | — |
| — | — | — | — | — | — | **No hay** botón «Editar» (`PUT`), «Anular» (`cancel`), «Solicitar reverso», ni línea de tiempo de auditoría |

### 3.13 `/my-pending` — `MyPendingPage.tsx`

| Control | Handler | HTTP | Flags |
|---|---|---|---|
| Carga/refrescar (:29-44, :56-63) | `fetch` | GET `/operations?registered_by_me=true&status=draft,registered&limit=50` | **ruta sin entrada de menú ni enlace** (grep `my-pending` → solo `App.tsx:262`); filtra `draft,registered`: devueltos/rechazados **no** aparecen |
| Fila → detalle (:87-104) | `navigate('/operations/{id}')` | — | `op.lot?.name` (:101) — el backend no devuelve `lot` anidado (`OperationalEventRead`), siempre vacío |

### 3.14 `/review` — `ReviewCenter.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Pestañas de estado (:33-39, :181-202) y filtros (:205-273) | `fetchEvents` :82-104 | GET `/review/pending?limit&offset&status=…[&lot_id&event_type&date_from&date_to&farm_id&operator_id]` | — | tabla | toast | **`status` y `operator_id` no existen en el backend** (`review/router.py:22-33`) → ignorados: las 5 pestañas y las entradas de menú `/review?status=approved|returned` (`navigationConfig.ts:177-178`) muestran **siempre** REGISTERED+PENDING_REVIEW (`review/service.py:168`); filtro «Operador» inoperante |
| Catálogos filtros (:107-110) | effect | GET `/masters/farms?limit=100`, GET `/users?limit=100` | — | — | `.catch(() => {})` | — |
| «Iniciar» `review.start` (:317-322, :415-420) gate `review:review`, estado `pending_review` | `handleAction('start')` :122-135 | POST `/review/start/{id}` | `status=in_review` | toast + refetch | toast | tras el refetch el evento **desaparece** (ya no es pending) |
| «Completar» / «Devolver» (:323-334, :421-432) gate `review:review`, estado `in_review` | `handleAction` | POST `/review/complete` / `/review/return` (`prompt()` :123) | transición | toast + refetch | toast | **inalcanzables en la práctica**: la lista nunca contiene `in_review` (ver arriba) |
| «Crear lote» `review.createBatch` (:167-170) gate `review:review` | `handleCreateBatch` :137-152 (`prompt()` :143) | POST `/review/batches` | batch + eventos → pending_review | toast + refetch | toast | usa `window.prompt` |
| Detalle (:335-338, :433-436) | Link `/review/{id}` | — | — | — | — | — |
| «Aprobaciones» (:171-174) | Link `/approvals` | — | — | — | — | sin gate `approvals:approve` (la ruta sí lo tiene) |

### 3.15 `/review/:id` — `ReviewDetail.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:30-62) | effect | GET `/operations/{id}`; GET `/corrections/event/{id}`; GET `/review/batches?limit=50` | — | render | `console.error` (:56) | «Historial de acciones» (:190-204) lee `batches.batches[].actions` (:48-52) — **nunca existe** (`ReviewBatchRead` sin `actions` `review/schemas.py:18-29`; el router no declara `response_model`): sección muerta |
| «Iniciar» (:212-217) / «Completar» (:220-223) / «Devolver» (:227-231) gate `review:review` | `handleAction` :64-81 | POST `/review/start/{id}` · `/review/complete` · `/review/return` | transición | `navigate('/review')` (:77) sin toast | toast | `alert()` para observaciones vacías (:69,74); no valida los 10 caracteres mínimos del backend (`review/schemas.py:101`) → 422 mostrado como toast |
| «Aprobar» (:241-244) gate `approvals:approve` / «Rechazar» (:248-251) gate `approvals:reject`, estados `corrected|in_review` | `handleAction` | POST `/approvals/approve` · `/approvals/reject` | transición | `navigate('/review')` | toast | aprobación desde `in_review` la rechaza el backend (solo CORRECTED en `get_pending_approvals`; `approve` valida estado) — botón condicional optimista |
| «Corregir» (:232-236, :255-259) gate `corrections:correct` | Link `/review/{id}/correct` | — | — | — | — | duplicado dentro y fuera del bloque `in_review` |

### 3.16 `/review/:id/correct` — `CorrectionForm.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:26-45) | effect | GET `/operations/{id}`; GET `/masters/correction-types` | — | — | `console.error` (:39) | — |
| Submit `review.saveCorrection` (:139-142) gate `corrections:correct` | `handleSubmit` :47-67 | POST `/corrections` | `correction_logs` + `status=corrected` | toast + `navigate('/review/{id}')` | toast | `alert()` (:49); **solo corrige `observations`** (`fields` :72-74) aunque el backend admite `lot_id`, `farm_id`, cantidades… (`GA-REM-023:210`) |

### 3.17 `/approvals` — `ApprovalPanel.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:35-50) | `fetchEvents` | GET `/approvals/pending?limit&offset[&lot_id]` | — | tabla | toast | — |
| «Aprobar» (:238-241, :311-314) gate `approvals:approve` → `ConfirmDialog` (:355-364) | `handleApprove` :52-62 | POST `/approvals/approve` | `status=approved` (+reverso aplicado si contrapartida) | toast + refetch | toast | ✓ |
| «Rechazar» (:242-245, :315-318) gate `approvals:reject` → diálogo con motivo ≥10 (:64-79) | `handleRejectSingle` | POST `/approvals/reject` | `status=rejected` + notificación | toast + refetch | toast | ✓ |
| «Aprobar/Rechazar todos» (:177-184) gate `review:review` | `handleBatchApprove` :93-106 / `handleBatchReject` :108-127 | POST `/approvals/batch-approve` / `batch-reject` | masivo | toast + refetch | toast | ✓ |
| KPIs (:165-170) | derivados de la página actual (:145-146) | — | — | — | — | «Aprobados/Rechazados» siempre 0 (la cola solo trae `corrected`) — indicadores decorativos |

### 3.18 `/reports`, `/reports/lot/:id`, `/reports/sap` — `ReportsPage`, `LotReportPage`, `SapComparisonPage`

| Control | Handler | HTTP | Éxito | Error | Flags |
|---|---|---|---|---|---|
| `ReportsPage` carga (:16-34) | effect | GET `/reports/kpis?lot_id={lotId}`; GET `/operations?lot_id&limit=100` | tarjetas + gráficas | **`.catch(() => {})`** (:17,:33) | **`lotId` por defecto = 2** (:13); enlace **codificado `/reports/lot/2`** (:193) |
| Excel/PDF (:74-91) | `handleExport` :39-65 → `utils/export.ts:10-27,31-66` (cliente) | ninguna | descarga | `console.error('Export failed')` (:61) | sin ruta backend; sin auditoría de exportación |
| `LotReportPage` carga (:25-42) | effect | GET `/reports/lot/{id}`; `allSettled`: `/reports/kpi/ipe/{id}`, `/reports/kpi/weight-uniformity/{id}`, `/reports/kpis/afcr`, `…/vaccination-efficiency`, `…/transfer-efficiency`, `…/hatchery` | render | toast solo para el informe | ruta solo alcanzable desde el enlace codificado o URL manual |
| `LotReportPage` Excel/PDF (:72-77) | `handleExport` :44-62 | ninguna | descarga | **sin catch** (`finally` solo :59) → rechazo no manejado | — |
| `SapComparisonPage` (:13-15) | effect | GET `/reports/sap-comparison` | render | toast | — |

### 3.19 Campana — `NotificationBell.tsx` (montada en `Header.tsx:53,184`)

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Contador (:43-55) | sondeo 60 s | GET `/notifications/unread-count` | — | badge | silencioso (:46-48) | — |
| Abrir (:68-85) | `abrir` | GET `/notifications?limit=20` | — | lista | `error` visible (AC19) | — |
| Pulsar aviso (:87-103) | `abrirAviso` | PATCH `/notifications/{id}/read` | `read_at` | estado local + `navigate(destino)` | `error` | `destino` solo para `operational_event` (:98) |

### 3.20 `TraceabilityTree.tsx` (en `LotDetailPage.tsx:460`)

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga/Actualizar (:120-133, :276-283) | `load` | GET `/lots/{id}/traceability` | — | árbol | texto + «Reintentar» | — |
| «Vincular huevos a incubadora» (:287-296, modal :310-349; solo breeder/grandparent) | `handleCreateEggBatch` :82-99 | POST `/lots/egg-batches` `{source_lot_id, hatchery_lot_id, quantity_dispatched, dispatch_date}` | fila `egg_batches` | cierra + `load()` | `linkError` con `detail` | `hatchery_lot_id: … || null` pero el backend exige `int` (`lots/schemas.py:219`) → 422 si vacío (mostrado); **sin gate** `lots:create` (backend deniega) |
| «Vincular pollitos a engorde» (:297-306, modal :352-391; solo hatchery) | `handleCreateChickBatch` :101-118 | POST `/lots/chick-batches` | fila `chick_batches` | cierra + `load()` | `linkError` | ídem; los botones solo se pintan si `hasData` (:160-166) → un lote **sin vínculos previos no puede crear el primero** desde UI |

### 3.21 `/sap` — `SapManagerPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:37-49) | effect | GET `/sap/references?limit=10`, `/sap/sync/jobs?limit=5`, `/sap/payloads?limit=5`, `/sap/connection-check` | — | KPIs/pestañas | `.catch(() => vacío)` — error ≡ sin actividad | **`limit=5`**: pestañas «Pendientes/Enviados/Errores» (:201-273) se derivan de 5 payloads → contadores falsos; `/sap/errors` y `/sap/consolidated` no se usan |
| «Consolidar» `sap.consolidate` (:135-138) gate `sap:send_sap` | `handleConsolidate` :51-58 | POST `/sap/consolidate` `{}` | eventos APPROVED→CONSOLIDATED + `consolidated_movements` | toast con `r.data.length` | toast | **sin refetch** de jobs/payloads |
| «Exportar a SAP» `sap.export` (:139-142) gate `sap:send_sap` | `handleExport` :60-67 | POST `/sap/export` `{}` | sync_job + payloads (manual: «preparado») | toast `sync_job_id`/`message` | toast | **sin refetch**; sin confirmación |
| Sub-entradas de menú `nav.sapPending/sapSent/sapErrors/sapLog` (`navigationConfig.ts:203-206`) | Link `/sap` | — | — | — | — | las 4 llevan a la misma página sin preseleccionar pestaña (diferenciación muerta) |
| — | — | — | — | — | — | **No hay** importación de referencias, reintento ni vista de consolidados |

### 3.22 `/audit` — `AuditPage.tsx`

| Control | Handler | HTTP | Flags |
|---|---|---|---|
| Pestañas/filtros (:59-76, :116-181) | effect | GET `/audit?limit=50[&action&module&date_from&date_to]`; pestaña «Correcciones» = `action=corrected` (:70) | **`.catch(() => {})`** (:74); sin paginación (50 máx.); `AUDIT_ACTIONS/AUDIT_MODULES` codificados (:23-32) duplican enums del backend; renderiza `log.user_name/old_value/new_value` (:90-96) — nombres no confirmados en `AuditLogRead` (probable detalle siempre vacío; no verificado en esta traza) |

### 3.23 `/users` — `UsersPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:37-65) | `fetchData` | GET `/users` (sin `limit` → **20 por defecto** `auth/router.py:101`); `allSettled` GET `/roles`, `/masters/companies?limit=100`, `/masters/areas?limit=100` | — | tabla; 403 → `users.forbidden` (AC16 ✓) | estado `error` + reintentar | **sin paginación**: >20 usuarios invisibles |
| «Crear» (:96) gate `users:create` → modal (:115-132) | `handleSave` :70-86 | POST `/users` `{…payload, password}` | fila | cierra + refetch | `alert(detail)` (:85) | `alert()` de validación (:71,:82) |
| «Editar» (:108,:110) gate `users:update` → mismo modal | `handleSave` :78-80 | **PUT `/users/{id}` con `{username, first_name, last_name, email, phone, role_id, area_id, company_id, view_type, is_active}`** (:76-79) | **ninguna**: `UserUpdate` tiene `extra="forbid"` y **no** declara `username` ni `company_id` (`auth/schemas.py:74-85`) → **422 en toda edición** | — | `alert(detail)` con el error Pydantic | **ACCIÓN MUERTA** (el cambio de empresa/nombre/rol desde el modal nunca se guarda); solo `handleToggleActive` (:91, envía `{is_active}`) funciona |
| Restablecer contraseña en edición (:80) | tras el PUT | POST `/users/{id}/password` `{new_password}` | hash | — | — | nunca se alcanza (el PUT anterior lanza 422) |
| Activar/Desactivar (chip :108,:110) gate `users:update` | `handleToggleActive` :91 | PUT `/users/{id}` `{is_active}` | `is_active` | refetch | `alert()` | ✓ |
| Eliminar (:108,:112) gate `users:delete` | `handleDelete` :88 | DELETE `/users/{id}` | baja lógica | refetch | `alert()` | `confirm()` nativo |
| Unidades por usuario (`UserBusinessUnitsButton.tsx`) | ver 3.25 | | | | | |
| Modal (:115-132) | — | — | — | — | — | campos nombre/apellido/email/teléfono/contraseña **duplicados** (:117-120 y :127-130) |

### 3.24 `/roles` — `RolesPage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:33-49) | `fetchData` | GET `/roles`, GET `/roles/permissions-catalog` | — | tabla/matriz | `console.error` (:43) | — |
| «Nuevo rol» (:107-112) gate `users:create` / «Editar» (:137-143) gate `users:update` | `guardar` :76-89 | POST `/roles` / PUT `/roles/{id}` `{name, description, permissions[{module,action,scope_type}]}` | rol + permisos (sustitución) | cierra + refetch | `alert()` (:85) | ✓ contrato `RoleCreate/RoleUpdate` |
| «Desactivar» (:144-150) gate `users:delete` | `desactivar` :91-99 | PUT `/roles/{id}` `{is_active:false}` | `is_active` | refetch | `alert()` | `confirm()` nativo; no hay DELETE en backend (coherente) |

### 3.25 `/admin/unit-access` — `UnitAccessPage.tsx` y `UserBusinessUnitsButton.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| Carga (:50-79) | `loadUnits` | GET `/business-units` | — | tarjetas | toast + reintentar | fail-closed sin empresa efectiva (:175-186) ✓ |
| Habilitar/Deshabilitar (:223-230) gate `business_units:update` → `ConfirmDialog` | `runToggle` :115-130 | PATCH `/business-units/{code}/enable|disable` | `company_business_units.is_enabled` (+ concesiones terminadas OD-23) | toast + refetch (:128) | toast + refetch | ✓ |
| Selector unidad → candidatos (:96-103) | `loadCandidates` | GET `/business-units/{code}/grant-candidates` | — | lista | toast | ✓ (evita 409 en OFF :101) |
| «Conceder» (:295-302) gate `business_units:create` | `runGrant` :132-143 | POST `/users/{id}/business-units` `{code}` | `user_business_units` | toast + recarga candidatos | toast | ✓ |
| «Revocar» (:305-312) gate `business_units:delete` → confirm | `runRevoke` :145-159 | DELETE `/users/{id}/business-units/{code}` | `revoked_at` | toast + recarga | toast | ✓ |
| Botón por usuario (`UserBusinessUnitsButton.tsx:116-123`, gate `business_units:read`) → modal | `load` :53-67; `grant` :79-90; `revoke` :92-105 | GET `/business-units`, GET `/users/{id}/business-units`; POST/DELETE | ídem | toast + `load()` | toast + `load()` | ✓ |

### 3.26 `/profile` — `ProfilePage.tsx`

| Control | Handler | HTTP | BD | Éxito | Error | Flags |
|---|---|---|---|---|---|---|
| «Actualizar contraseña» (:71-74) | `handleChangePassword` :18-40 | POST `/users/{id}/password` `{current_password, new_password}` | hash | mensaje verde | mensaje rojo con `detail` | ✓ (GA-REM-012) |

### 3.27 Resumen de FLAGS (Parte 3)

| Tipo | Ocurrencias (file:line) |
|---|---|
| **Acción muerta por contrato** | `LotDetailPage.tsx:125-130` (POST phases sin `lot_id`/`phase_id`, campo `phase_code` inexistente → 422; error solo en consola :134) · `UsersPage.tsx:76-79` (PUT users con `username`/`company_id` prohibidos → 422) |
| **Botón/sección inalcanzable** | `ReviewCenter.tsx:323-334,421-432` (Completar/Devolver: la lista nunca trae `in_review`) · `ReviewDetail.tsx:190-204` (historial de acciones: `actions` nunca viene) · `TraceabilityTree.tsx:286-307` (botones de vínculo solo si ya hay vínculos) · `ApprovalPanel.tsx:167-168` (KPIs siempre 0) · `ProcessStagePage.tsx:111-112` (`completedStages=[]`) |
| **Parámetros ignorados por el backend** | `ReviewCenter.tsx:88,95` (`status`, `operator_id`) y `navigationConfig.ts:177-178` (`/review?status=…`) |
| **Etiqueta engañosa** | `OperationListPage.tsx:89` (`common.edit` → detalle) · `navigationConfig.ts:203-206` (4 entradas SAP → misma página) · `:221-222` (2 entradas reportes → misma página) |
| **Datos codificados** | `ReportsPage.tsx:13,193` (lote 2) · `thermalCurves.ts:20-78` y `OperationFormPage.tsx:24-27` (rangos Ross/Cobb) · `processCatalog.ts:205-268` (catálogo de eventos duplicado del backend; `/operations/event-types` sin uso) · `AuditPage.tsx:23-32` (enums duplicados) · `LotListPage.tsx:9` (tipos sin `hatchery`) |
| **`alert()/confirm()/prompt()`** | `CorrectionForm.tsx:49` · `ReviewDetail.tsx:69,74` · `RolesPage.tsx:85,92,97` · `UsersPage.tsx:71,82,85,88,91` · `ReviewCenter.tsx:123,143` |
| **Errores tragados (consola o vacío)** | `LotListPage.tsx:33` · `LotDetailPage.tsx:67,115,134` · `MasterListPage.tsx:60,114` · `CorrectionForm.tsx:39` · `ReviewDetail.tsx:56` · `RolesPage.tsx:43` · `ReportsPage.tsx:17,33,61` · `AuditPage.tsx:74` · `OperationListPage.tsx:42` · `SapManagerPage.tsx:39-42` · `Header.tsx:37-40` (switchCompany sin catch) · `LotReportPage.tsx:44-62` (sin catch) |
| **Mutación sin refresco de lista** | `SapManagerPage.tsx:51-67` (consolidar/exportar) |
| **Éxito sin esperar** | ninguno (todas las mutaciones esperan la respuesta) |
| **Paths inexistentes** | ninguno en llamadas vivas; servicios muertos con contrato obsoleto: `sap.service.ts:34-35` (`entries`), `review.service.ts:40-41`, `audit.service.ts:18-28`, `corrections.service.ts:29-30` (tipos de lista) |
| **Sin paginación (datos ocultos)** | `UsersPage.tsx:40` (20) · `AuditPage.tsx:61` (50) · `LotListPage.tsx:29` / `OperationListPage.tsx:26` (100) |
| **Componentes/hook/stores huérfanos** | `MobileDrawer.tsx`, `SidebarSubmenu.tsx`, `OperationActionCard.tsx`, `ProcessCard.tsx`, `ProcessFlowVisualizer.tsx`, `DarkModeToggle.tsx`, `ui/SignaturePad.tsx`, `hooks/useSidebar.ts`, `hooks/useMediaQuery.ts`, `stores/ui.store.ts`, `stores/theme.store.ts`, `stores/i18n.store.ts` + 12 hooks de datos + 11 servicios (Parte 2) |
| **Gate de UI ausente** | `OperationFormPage.tsx:1831` (etapas sin `stageVisibleForSession`) · `TraceabilityTree.tsx:286-307` (sin `lots:create`) · `ReviewCenter.tsx:171` (enlace a `/approvals` sin gate) — el backend deniega en todos los casos |

---

## PARTE 4 — TRAZA INVERSA (backend → superficie de usuario)

| Ruta backend | Superficie frontend (página + control) | Clasificación / justificación |
|---|---|---|
| POST `/login`, POST `/refresh`, GET `/me` | `LoginPage.tsx:135-155` · `api.ts:37` · `auth.store.ts:143` | Consumidas |
| POST `/switch-company` | `Header.tsx:78-127` selector de empresa (super-admin) | Consumida (FVA-05) |
| logout | Solo cliente (`auth.store.ts:133-139`). No existe ruta backend | INTERNAL_ONLY; nota: sin revocación server-side |
| GET/POST `/users`, DELETE `/users/{id}` | `UsersPage.tsx:40,83,88` | Consumidas |
| PUT `/users/{id}` | `UsersPage.tsx:79` (edición → **422**), `:91` (toggle activo ✓) | Consumida, pero la edición es un **FRONTEND_INTEGRATION_GAP** por contrato roto |
| GET `/users/{id}` | ninguna | API_ONLY_BY_DESIGN (la lista basta) |
| POST `/users/{id}/password` | `ProfilePage.tsx:29` (titular) · `UsersPage.tsx:80` (admin, inalcanzable hoy por el 422 previo) | Consumida (FVA-02) |
| GET/POST `/roles`, PUT `/roles/{id}`, GET `/roles/permissions-catalog` | `RolesPage.tsx:37-38,80-81,94` | Consumidas (FVA-14) |
| Maestros CRUD (22×5) | `MasterListPage.tsx:49,92,94,110` para las 20 entidades de `App.tsx:135-166` | Consumidas (FVA-33/34); `GET /masters/E/{id}` solo `genetic-lines` (`weightCurves.ts:52-55`) |
| GET `/masters/farms/{id}/houses`, `/masters/hatcheries/{id}/incubators`, GET `/masters/weight-curves/{id}` | ninguna | API_ONLY_BY_DESIGN (filtrado en cliente `OperationFormPage.tsx:291-298`, `LotFormPage.tsx:112-114`) |
| Curvas de peso (list/POST/activate) | `WeightCurvesPage.tsx:65,111,131` + `LotFormPage.tsx:71` | Consumidas (FVA-35, OD-06) |
| GET `/notifications`, `/unread-count`, PATCH `/read` | `NotificationBell.tsx:45,76,90` | Consumidas (FVA-37). GET `/notifications/{id}` sin consumidor → API_ONLY_BY_DESIGN |
| GET `/lots`, POST `/lots`, GET `/lots/{id}`, GET `/lots/{id}/phases`, GET `/lots/{id}/traceability` | `LotListPage.tsx:29` · `LotFormPage.tsx:133` · `LotDetailPage.tsx:49,55,131` · `TraceabilityTree.tsx:124` | Consumidas (FVA-29) |
| POST `/lots/{id}/close` | `LotDetailPage.tsx:185-195` «Cerrar Lote» | Consumida (error silencioso) |
| POST `/lots/{id}/phases` | `LotDetailPage.tsx:174-182` «Iniciar Producción» | **FRONTEND_INTEGRATION_GAP**: payload inválido (422) — la transición cría→producción no es ejecutable desde UI |
| **POST `/lots/activate-manual`**, GET `/lots/{id}/opening-balance` | **ninguna** (`lotsService.activateManual/getOpeningBalance` sin llamadores) | **FRONTEND_INTEGRATION_GAP** — proceso **P-11** (activación manual de lotes preexistentes con saldo de apertura) documentado en `GA-REM-005:390`, `GA-REM-028:7,39,82`, `GA-REM-002:518`, `route_scope.py:116` («P-11, las cuatro»); no aparece en la matriz de 38 capacidades (`GA_FINAL_FRONTEND_38_CAPABILITY_MATRIX.md`) → capacidad de negocio solo por API |
| PUT `/lots/{id}` | ninguna | **FRONTEND_INTEGRATION_GAP** (medio): no hay edición de lote (fecha prevista de cierre, área, galpón…); `GA-REM-040:1440,1612` la trata como mutación viva |
| POST `/lots/egg-batches`, `/lots/chick-batches` | `TraceabilityTree.tsx:82-118` modales «Vincular…» | Consumidas (solo visibles si ya hay vínculos; ver P3) |
| GET `/operations`, POST `/operations`, GET `/operations/{id}` | `OperationListPage.tsx:33` · `OperationFormPage.tsx:452` · `OperationDetailPage.tsx:64` | Consumidas |
| POST `/operations/{id}/submit` | `OperationDetailPage.tsx:183-194` CTA enviar/reenviar | Consumida (FVA-27, GA-FE-05) |
| **PUT `/operations/{id}`** | **ninguna** | **FRONTEND_INTEGRATION_GAP** — edición reconocida al operador en DRAFT/REGISTERED/RETURNED/REJECTED (`GA-REM-023:80,115`; `GA-REM-006:208`; `GA-REM-042:38,51`; `OD-17`). Un registro devuelto solo puede reenviarse **sin cambios** o «corregirse» en `observations` (`CorrectionForm.tsx:72-74`). `OperationListPage.tsx:89` etiqueta «Editar» un enlace a detalle |
| **POST `/operations/{id}/cancel`** | **ninguna** | **FRONTEND_INTEGRATION_GAP** — anulación es acto de operador (`GA-REM-042:51` «operations:create (alta, adjuntos, anulación)»; reglas `GA-REM-005:633`, `GA-REM-006:211`); sin superficie, el estado CANCELLED es inalcanzable |
| GET `/operations/{id}/weight-evaluation` | `WeightEvaluation.tsx:50` (en detalle) | Consumida |
| GET `/operations/alerts`, PATCH `/alerts/{id}/resolve` | `LotDetailPage.tsx:58,77` · `DashboardPage.tsx:98,110` | Consumidas |
| Evidencias POST/download/DELETE | `OperationDetailPage.tsx:93,148,161,108` | Consumidas (FVA-30). GET `/operations/{id}/evidences` sin consumidor → API_ONLY_BY_DESIGN (detalle ya las incluye `operations/schemas.py:305`) |
| GET `/operations/event-types` | ninguna | API_ONLY_BY_DESIGN (catálogo duplicado en `processCatalog.ts`); **sin dependencia de sesión** pese a figurar en `RUTAS_DE_TITULAR` (`authorization_coverage.py:45` vs `operations/router.py:33-35`) |
| **GET `/operations/pending-classification`, POST `/{id}/classify`, POST `/{id}/reclassify`** | **ninguna** | **API_ONLY (diferido por el propietario)** — FVA-10 `OOS` «diseño-condicional (T-040-24)» (`GA_FINAL_FRONTEND_38_CAPABILITY_MATRIX.md` fila FVA-10; `GA_FINAL_FRONTEND_RESIDUAL_GAPS.md:8` RES-02; `GA-REM-040:779` AC-H07 «La bandeja de clasificación existe si el diseño la requiere»; `OD-10:231,262`). Riesgo operativo: un registro sin cadena (`company_business_unit_id` nulo) es invisible en toda la UI |
| GET `/review/pending` | `ReviewCenter.tsx:96` | Consumida; filtros `status/operator_id` inexistentes (ver P3) |
| POST `/review/batches` | `ReviewCenter.tsx:146` «Crear lote» | Consumida |
| GET `/review/batches` | `ReviewDetail.tsx:46` (espera `actions`, nunca llegan) | Consumida de forma inútil → sección muerta |
| POST `/review/start/{id}` | `ReviewCenter.tsx:127`, `ReviewDetail.tsx:66` | Consumida |
| POST `/review/return` (return_to_operator), POST `/review/complete` | `ReviewDetail.tsx:70,67` (alcanzable solo por URL directa) · `ReviewCenter.tsx:128-129` (botones nunca visibles) | Consumidas nominalmente; **STATE ORPHAN in_review** (ver P5) |
| GET `/approvals/pending`, POST `/approvals/approve`, POST `/approvals/reject` | `ApprovalPanel.tsx:40,54,70` · `ReviewDetail.tsx:72,75` | Consumidas (FVA-26) |
| POST `/approvals/batch-approve`, `batch-reject` | `ApprovalPanel.tsx:100,119` | Consumidas |
| `/approval-steps` (GET/POST/PUT/DELETE/seed-defaults) | ninguna | API_ONLY_BY_DESIGN / INTERNAL_ONLY — configuración del flujo; `seed-defaults` es semilla (`GA-REM-025:38`); aprobación multinivel es backlog `GA-REM-019` (`GA-REM-007:52`). Nota: tampoco `Company.approval_levels` es editable en UI (`App.tsx:136` columnas de companies) |
| POST `/corrections`, GET `/corrections/event/{id}` | `CorrectionForm.tsx:52` · `ReviewDetail.tsx:40` | Consumidas (solo campo `observations`) |
| GET `/corrections` | ninguna | API_ONLY_BY_DESIGN (AuditPage cubre con `action=corrected`) |
| **POST `/reversals`, GET `/reversals`, GET `/reversals/event/{id}`** | **ninguna** (`grep -i revers` en `src` → 0 fuera de tests/servicios) | **API_ONLY (diferido por el propietario)** — FVA-28 `OOS` «diferral fase 9», RES-04, `GA-REM-041:10` («Fuera de alcance … frontend»), `:225` («sin frontend»), FIA-06 «UI diferida». Observación: `reversals:create/read` **se siembran a roles** (`GA-REM-041` Enmiendas A/B; `OD-19:65`) → titulares sin superficie |
| GET `/audit` | `AuditPage.tsx:72` | Consumida (FVA-36) |
| GET `/audit/{log_id}`, GET `/audit/timeline/{type}/{id}` | ninguna | **FRONTEND_INTEGRATION_GAP** (bajo): la línea de tiempo por entidad no se muestra en detalle de operación/lote; `auditService.getTimeline` muerto |
| GET `/reports/kpis` | `LotDetailPage.tsx:53`, `ReportsPage.tsx:17` | Consumida |
| GET `/reports/kpis/mortality`, `feed-conversion`, `egg-production`, `animal-welfare` | ninguna | API_ONLY_BY_DESIGN (incluidas en el agregado `reports/service.py:425-432`) |
| GET `/reports/kpis/hatchery`, `vaccination-efficiency`, `transfer-efficiency`, `afcr` | `LotReportPage.tsx:30-33` | Consumidas (GA-REM-022 AC07) |
| **GET `/reports/kpis/production-index` (G-05)** | **ninguna** (ni en agregado ni pedido) | **FRONTEND_INTEGRATION_GAP** (bajo): KPI calculado sin consumidor; FVA-31 lo cita («G-05 5.1») pero ninguna pantalla lo pinta |
| GET `/reports/kpi/ipe/{id}`, `/kpi/weight-uniformity/{id}` | `LotDetailPage.tsx:56-57`, `LotReportPage.tsx:28-29` | Consumidas |
| GET `/reports/lot/{id}` | `LotReportPage.tsx:26` (solo vía `/reports/lot/2` codificado) | Consumida; ruta casi huérfana |
| GET `/reports/sap-comparison` | `SapComparisonPage.tsx:14` | Consumida |
| GET `/dashboard/mobile`, `/dashboard/admin` | `DashboardPage.tsx:94-95` | Consumidas (FVA-31) |
| Business units (7 rutas) | `UnitAccessPage.tsx`, `UserBusinessUnitsButton.tsx` (P3.25) | Consumidas (FVA-08/09) |
| POST `/sap/consolidate`, POST `/sap/export`, GET `/sap/references`, `/sync/jobs`, `/payloads`, `/connection-check` | `SapManagerPage.tsx:53,62,39-42` · `OperationFormPage.tsx:352-353` | Consumidas (FVA-32, `BLOCKED_EXTERNAL` R-112/P-08) |
| **POST `/sap/references/import`** | ninguna (`useSap.importReferences` muerto y con cuerpo obsoleto) | **FRONTEND_INTEGRATION_GAP / SAP_FUTURE**: en modo manual (`GA-REM-010:64,88`) las referencias solo entran por API; el asistente depende de ellas (`OperationFormPage.tsx:352-353`) |
| **POST `/sap/retry`**, GET `/sap/errors`, GET `/sap/consolidated` | ninguna | **FRONTEND_INTEGRATION_GAP / SAP_FUTURE**: el aviso `sap_send_failed` (`notifications.ts:16`) no ofrece reintento; la pestaña «Errores» deriva de 5 payloads |
| GET `/health` | — | INTERNAL_ONLY |

---

## PARTE 5 — TABLAS DE HUÉRFANOS

### 5.1 BACKEND ORPHAN (rutas sin superficie)

| Ruta | ¿Interno legítimo? | ¿Legacy? | ¿Brecha real? | Evidencia |
|---|---|---|---|---|
| POST `/lots/activate-manual`, GET `/lots/{id}/opening-balance` | No | No | **Sí (P-11 sin UI)** | `lots/router.py:99-119`; `lots.service.ts:54-55,63-64` sin llamadores; `GA-REM-028:39` |
| PUT `/lots/{id}` | No | No | **Sí (edición de lote)** | `lots/router.py:69-77`; `lots.service.ts:48-49` |
| PUT `/operations/{id}` | No | No | **Sí (edición pre-revisión)** | `operations/router.py:295-303`; `GA-REM-023:80,115` |
| POST `/operations/{id}/cancel` | No | No | **Sí (anulación)** | `operations/router.py:320-327`; `GA-REM-042:51` |
| GET `/operations/pending-classification`, POST classify/reclassify | Diferido por propietario | No | Condicional (RES-02) | `operations/router.py:118-244`; matriz FVA-10 |
| POST/GET `/reversals*` | Diferido por propietario | No | Condicional (RES-04); permisos ya sembrados | `reversals/router.py`; `GA-REM-041:10,225` |
| `/approval-steps*` (5) | **Sí** (configuración/semilla) | No | No | `review/router.py:167-214`; `GA-REM-025:38` |
| GET `/corrections` | Sí (redundante) | No | No | `corrections/router.py:36-48` |
| GET `/audit/{id}`, GET `/audit/timeline/…` | No | No | Sí (bajo) | `audit/router.py:44-63` |
| GET `/reports/kpis/{mortality,feed-conversion,egg-production,animal-welfare}` | Sí (agregado) | No | No | `reports/service.py:425-432` |
| GET `/reports/kpis/production-index` | No | No | Sí (bajo) | `reports/router.py:106-113` |
| POST `/sap/references/import`, POST `/sap/retry`, GET `/sap/errors`, GET `/sap/consolidated` | Parcial (P-08) | No | Sí (modo manual) | `sap/router.py:20-27,106-117,151-159,64-85` |
| GET `/masters/farms/{id}/houses`, `/hatcheries/{id}/incubators`, `/masters/weight-curves/{id}`, `GET /masters/E/{id}` (salvo genetic-lines) | Sí | No | No | `masters/router.py:132-174,211-224` |
| GET `/operations/{id}/evidences`, GET `/notifications/{id}`, GET `/users/{id}`, GET `/operations/event-types` | Sí | No | No (event-types: sin auth, revisar) | ver P4 |

### 5.2 FRONTEND ORPHAN (código sin importadores en producción)

| Elemento | Tipo | ¿Legacy? | Evidencia |
|---|---|---|---|
| `services/{auth,lots,masters,review,approvals,corrections,audit,reports,dashboard,sap}.service.ts` (todos los métodos salvo `operationsService.submit`) | servicio | Capa abandonada (páginas usan `api` directo) | grep importadores: solo `hooks/*` |
| `hooks/{useApprovals,useLots,useMasters,useOperations,useReports,useReview,useSap,useSidebar,useMediaQuery}.ts` | hook | Sí | 0 importadores |
| `stores/{ui,theme,i18n}.store.ts` | store | Sí | 0 importadores (theme solo vía `DarkModeToggle`, también huérfano) |
| `components/layout/MobileDrawer.tsx`, `SidebarSubmenu.tsx` | componente | Sí (navegación anterior al hub) | `AppLayout.tsx:13-20` no los monta |
| `components/operations/{OperationActionCard,ProcessCard,ProcessFlowVisualizer}.tsx` | componente | Sí | exportados en `index.ts` pero no usados |
| `components/DarkModeToggle.tsx`, `components/ui/SignaturePad.tsx` | componente | Sí | 0 importadores |

### 5.3 ROUTE ORPHAN (rutas de `App.tsx` no alcanzables por nav/enlace)

| Ruta | Página | Alcanzable desde | Veredicto |
|---|---|---|---|
| `/my-pending` (`App.tsx:262`) | `MyPendingPage` | **nada** (grep `my-pending` → solo App) | Huérfana; además omite devueltos/rechazados |
| `/poultry` (`:253`) | `ProcessHubPage` | nada (nav usa `/menu/poultry` y `/poultry/<bu>`) | Legacy |
| `/processes`, `/processes/:stage` (`:256-257`) | redirects | nada | Legacy |
| `/reports/lot/:id` (`:268`) | `LotReportPage` | solo `ReportsPage.tsx:193` **codificado `/reports/lot/2`** | Casi huérfana (sin enlace desde el detalle de lote) |
| `/kpi` (`:216`) | `DashboardPage` | solo `MobileNav.tsx:21` | Web sin acceso (menor) |
| `/operations` (`:259`) | `OperationListPage` | `ProcessStagePage.tsx:120` (solo web), `OperationDetailPage.tsx:172`, post-guardado `OperationFormPage.tsx:455` | Sin entrada de menú; móvil solo tras guardar |
| `/review?status=approved|returned` (`navigationConfig.ts:177-178`) | `ReviewCenter` | menú | Semánticamente muertas (parámetro ignorado por backend) |
| `/sap` ×4 (`:203-206`), `/reports` ×2 (`:221-222`) | misma página | menú | Entradas redundantes sin efecto |

### 5.4 SERVICE ORPHAN — ver 2.18 (métodos con cero llamadores y evaluación de promesa).

### 5.5 ACTION ORPHAN (controles que no producen efecto o son inalcanzables)

| Control | Motivo | Evidencia |
|---|---|---|
| «Iniciar Producción» | 422 por contrato; error solo en consola | `LotDetailPage.tsx:125-134` vs `lots/schemas.py:98-105` |
| Guardar edición de usuario | 422 (`username`, `company_id` prohibidos) | `UsersPage.tsx:76-79` vs `auth/schemas.py:74-85` |
| «Completar»/«Devolver» en ReviewCenter | nunca se renderizan (lista sin `in_review`) | `ReviewCenter.tsx:323-334` vs `review/service.py:168` |
| Historial de acciones en ReviewDetail | `actions` nunca viene | `ReviewDetail.tsx:46-53` vs `review/schemas.py:18-29` |
| Pestañas de estado / filtro Operador en ReviewCenter | parámetros ignorados | `ReviewCenter.tsx:88,95` vs `review/router.py:22-33` |
| Enlace «Editar» en lista de operaciones | lleva al detalle | `OperationListPage.tsx:89` |
| KPIs «Aprobados/Rechazados» en ApprovalPanel | siempre 0 | `ApprovalPanel.tsx:145-146,167-168` |
| Sub-entradas SAP/Reportes del menú | misma página | `navigationConfig.ts:203-206,221-222` |
| Botones «Vincular…» en TraceabilityTree | ocultos hasta que exista un vínculo | `TraceabilityTree.tsx:160-166,286-307` |
| Línea de tiempo «completadas» | `completedStages=[]` | `ProcessStagePage.tsx:111-112` |

### 5.6 STATE ORPHAN (transiciones del backend sin camino normal de usuario)

| Estado / transición | Ruta backend | Camino UI | Veredicto |
|---|---|---|---|
| `IN_REVIEW` → `complete`/`return` | `/review/complete`, `/review/return` | Solo `ReviewDetail` por URL (`/review/{id}`); ninguna lista muestra `in_review` (`review/service.py:168`; `/approvals/pending` solo `corrected` `:463`) | **Huérfano funcional**: tras «Iniciar» el revisor pierde el registro de la vista |
| `→ CANCELLED` | `/operations/{id}/cancel` | ninguno | Huérfano |
| `RETURNED/REJECTED` → editar → reenviar | `PUT /operations/{id}` + `submit` | solo reenvío sin edición (`OperationDetailPage.tsx:183-194`) | Parcial |
| Reverso (solicitud → contrapartida → aprobación) | `/reversals` | ninguno (diferido) | Huérfano diferido |
| Clasificación pendiente → clasificado / reclasificado | `pending-classification`, `classify`, `reclassify` | ninguno (diferido) | Huérfano diferido; registros invisibles |
| Lote: activación manual (P-11) | `/lots/activate-manual` | ninguno | Huérfano |
| Lote: cría → producción | `/lots/{id}/phases` | botón con payload inválido | Huérfano de facto |
| Lote: edición | `PUT /lots/{id}` | ninguno | Huérfano |
| SAP: `error` → reintento | `/sap/retry` | ninguno | Huérfano |
| SAP: referencias (import) | `/sap/references/import` | ninguno | Huérfano |
| Flujo de aprobación (pasos) | `/approval-steps*` | ninguno | Interno legítimo |
| Lote active→closed · alerta→resuelta · BU enable/disable · grant/revoke · rol/usuario baja · notificación leída · submit · approve/reject · batch · corrección | — | existen (P3) | OK |

---

## TOP FINDINGS (brechas materiales, con evidencia)

1. **Transición cría→producción rota**: `LotDetailPage.tsx:125-130` envía `{phase_code,…}` sin `lot_id`/`phase_id`; `LotPhaseCreate` los exige (`lots/schemas.py:98-105`) → 422 siempre; el error solo va a consola (:134). El botón «Iniciar Producción» es una acción muerta.
2. **Edición de usuarios rota**: `UsersPage.tsx:76-79` envía `username` y `company_id` en `PUT /users/{id}`; `UserUpdate` es `extra="forbid"` sin esos campos (`auth/schemas.py:74-85`) → 422 en cada guardado del modal de edición (el restablecimiento de contraseña :80 nunca se alcanza).
3. **Centro de revisión: pestañas y filtros muertos + estado `in_review` huérfano**: `ReviewCenter.tsx:88,95` envía `status`/`operator_id` que `review/router.py:22-33` no acepta; el backend solo devuelve REGISTERED+PENDING_REVIEW (`review/service.py:168`). Las entradas de menú `/review?status=approved|returned` (`navigationConfig.ts:177-178`) muestran lo mismo, y los botones «Completar/Devolver» (:323-334) nunca aparecen: tras «Iniciar», el registro solo es alcanzable por URL.
4. **P-11 (activación manual con saldo de apertura) sin UI**: `POST /lots/activate-manual` y `GET …/opening-balance` (`lots/router.py:99-119`) no tienen consumidor; `lotsService.activateManual` muerto (`lots.service.ts:54-55`); no figura en la matriz de 38 capacidades.
5. **Edición y anulación de operaciones sin UI**: `PUT /operations/{id}` y `POST /operations/{id}/cancel` (`operations/router.py:295-327`) sin superficie; `operationsService.update/cancel` muertos; `OperationListPage.tsx:89` etiqueta «Editar» un enlace a detalle; `CorrectionForm.tsx:72-74` solo corrige `observations`. Especificado en `GA-REM-023:80,115`, `GA-REM-042:51`.
6. **Capa de servicios/hooks abandonada**: 11/14 servicios y 12 hooks de datos con 0 importadores (grep); contratos obsoletos en `sap.service.ts:34-35` (`entries` vs `references`), `review.service.ts:40-41`, `audit.service.ts:18-28`, `corrections.service.ts:29-30`. Riesgo de que alguien los reactive sin saber que están rotos.
7. **Historial de acciones de revisión nunca se muestra**: `ReviewDetail.tsx:46-53` espera `batches[].actions`; `ReviewBatchRead` no lo declara (`review/schemas.py:18-29`) y `GET /review/batches` no tiene `response_model` (`review/router.py:57-66`).
8. **Página SAP con datos parciales y sin refresco**: `SapManagerPage.tsx:40-41` pide 5 payloads/5 jobs y deriva de ahí las pestañas Pendientes/Enviados/Errores (:201-273); `/sap/errors` y `/sap/consolidated` sin uso; consolidar/exportar (:51-67) no refrescan. Sin UI para `POST /sap/references/import` ni `POST /sap/retry` (aviso `sap_send_failed` sin acción).
9. **Reportes con lote codificado**: `ReportsPage.tsx:13` (`lotId=2`) y `:193` (`/reports/lot/2`); `LotDetailPage` no enlaza a su informe → `/reports/lot/:id` casi huérfana.
10. **Ruta `/my-pending` huérfana** (`App.tsx:262`, sin enlace ni menú) y su filtro `draft,registered` (`MyPendingPage.tsx:34`) excluye devueltos/rechazados; `op.lot?.name` (:101) nunca existe en la respuesta.
11. **Errores silenciados en mutaciones críticas**: cierre de lote (`LotDetailPage.tsx:115`), borrado de maestro (`MasterListPage.tsx:114`), cambio de empresa (`Header.tsx:37-40` sin catch), exportación de informe (`LotReportPage.tsx:44-62` sin catch), cargas con `.catch(() => {})` (`ReportsPage.tsx:17,33`, `AuditPage.tsx:74`, `SapManagerPage.tsx:39-42`) → error indistinguible de «sin datos» (contradice FVA-38).
12. **`GET /operations/event-types` sin autenticación**: `operations/router.py:33-35` no declara dependencia de sesión pero `authorization_coverage.py:45` la lista como «exige sesión» → superficie anónima no declarada en `RUTAS_PUBLICAS`.
13. **Capacidades diferidas con permisos sembrados**: reversos (`/reversals*`) y clasificación pendiente (`pending-classification/classify/reclassify`) están certificados en backend y explícitamente sin UI (FVA-10/FVA-28, RES-02/RES-04, `GA-REM-041:10`); `reversals:*` ya se conceden a roles (`GA-REM-041` Enm. A/B) → titulares sin superficie, y registros sin cadena invisibles.
14. **Listados sin paginación ocultan datos**: `/users` (20 por defecto, `UsersPage.tsx:40`), `/audit` (50, `AuditPage.tsx:61`), `/lots` y `/operations` (100) — sin controles de página ni aviso.
15. **`MobileDrawer` y la navegación colapsable no están montados** (`AppLayout.tsx:13-20`; `MobileDrawer.tsx`, `SidebarSubmenu.tsx` con 0 importadores) junto con `OperationActionCard/ProcessCard/ProcessFlowVisualizer/DarkModeToggle/SignaturePad` y los stores `ui/theme/i18n`: código muerto que la matriz de capacidades no refleja.
