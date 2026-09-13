# GLOBAL AVÍCOLA — Auditoría final independiente pre-SAP · Compuerta de seguridad

| Campo | Valor |
|---|---|
| Repositorio | `/home/maria/Proyectos/GlobalAvicola` · rama `main` · HEAD `c0b4afc` (GA-F01 C3) |
| Runtime de referencia | `https://avicola.globaldv.net` (empresa 1) + pila local aislada (uvicorn con `lifespan`, base sembrada) |
| Fecha de auditoría | 2026-09-13 |
| Auditor | Claude (auditoría independiente; sin modificar código, tests ni documentación existente) |
| Alcance de este documento | Encargo §21–25 (auth/sesión, multiempresa/BU, OD-16, OD-23, administrador de accesos) y §59 (compuerta de seguridad). Transacciones, idempotencia y concurrencia se tratan en `GA_CLAUDE_DATA_INTEGRITY_AUDIT.md` (§38/§60) y aquí solo se referencian. |
| Método | Lectura directa de `backend/app` y `frontend/src`; grep transversal; cruce con `backend/tests`; ejecución de la suite completa en PostgreSQL de pruebas; sondas de runtime local y productivo por UI/API oficiales; deduplicación contra `audit/remediation/REMEDIATION_BACKLOG.md`. |
| Codificación de hallazgos | `GAP-xx` (seguridad, este documento) y `E-xx` (dominio, documento de integridad). **No se asignan R-numbers**: la asignación canónica corresponde al auditor líder. |

Rutas abreviadas: `app/…` = `backend/app/…`; `tests/…` = `backend/tests/…`; `alembic/…` = `backend/alembic/…`. Leyenda de veredicto: **PASS** · **PARTIAL** · **FAIL** · **UNKNOWN** (no verificable con la evidencia disponible).

---

## 0. Resumen ejecutivo

**Veredicto de la compuerta de seguridad: FAIL.**

La cadena canónica `TENANT → COMPANY BU ENABLED → USER BU GRANT → RBAC → PERTENENCIA/REGLA` está implementada, se evalúa contra base de datos en **cada petición** (nada de ella vive en el JWT) y está cubierta por tests y por certificaciones de runtime previas (GA-FE-02-D/E, 2026-09-11). La habilitación de empresa (OD-16), el ciclo de concesiones (OD-23) y el administrador de accesos (OD-15) son sólidos a nivel de fila.

La compuerta falla por cuatro defectos de **autoridad** y **sesión**, uno de ellos P1 y no registrado en ningún backlog, y por dos defectos que afectan específicamente a la fase SAP:

| Bloqueante | Sev. | Naturaleza | Registro |
|---|---|---|---|
| **GAP-01** | **P1** | Un actor de empresa con `users:create`/`users:update` fabrica un rol de inquilino con `("*", all)` y obtiene `is_super_admin` → `switch-company` a cualquier empresa. Contradice `OD-13.c`/`AC-R06`. | **NUEVO** (sin registro, sin test) |
| **GAP-03** | P2 | El refresh token (7 días) autentica cualquier ruta como Bearer: la expiración de 30 min del access token es ilusoria. | **NUEVO** |
| **GAP-09** | P1 (backlog `P1-4`) | Sin `POST /logout`, sin rotación del refresh, sin denylist; el cambio de contraseña no invalida sesiones. | **EXISTING** `GA-REM-003` (abierto; AC04 no certificado) |
| **GAP-06** | P2 | `POST/PUT /lots` aceptan `house_id`, `genetic_line_id`, `weight_curve_id` de otra empresa: escritura foránea aceptada con privilegios ordinarios (`lots:create`) y exposición de la curva ajena en `weight-evaluation`. | **NUEVO** |
| **GAP-02** | P2 (fase SAP) | La autoridad global **sin contexto** lee dato SAP de todas las empresas y **reintenta cargas** de todas (`retry_failed`), contra `OD-14.d`. | **NUEVO** |
| **GAP-14** | P3 (fase SAP) | Consolidación SAP sin bloqueo (dos consolidaciones concurrentes duplican `ConsolidatedMovement`) y re-enlace idempotente roto (500). Riesgo de duplicado en camino SAP (§38). | **NUEVO** |
| **GAP-07 · GAP-08** | P2 por impacto / **P1 por regla §23** | Dos superficies agregadas (`/reports/kpis/hatchery` sin lote y `dashboard/admin.active_alerts`) no aplican el predicado de unidad: exponen dato de una unidad **apagada** o no concedida. Por §23 del encargo («any violation: blocking P1 until evidence proves otherwise») quedan como bloqueantes hasta ratificación del propietario. | **NUEVO** |
| **GAP-05** | P2 → P1 condicional | `company_id` fijable por el cliente en 19 esquemas de maestros; mitigado hoy solo por la semilla RBAC. Bloquea si se delega `masters:*` a un rol de inquilino antes de corregirlo. | **EXISTING** `R-50` (**ausente** del backlog) |

Estado de la evidencia de tests en HEAD: **1201 passed · 25 failed · 49 skipped**. Los 25 fallos no revelan regresiones de seguridad: 17 son tests obsoletos frente a OD-16 (esperan 403 o visibilidad de control sobre unidad apagada y reciben 404/0 filas: fail-closed, coherente con la ratificación en `audit/ga-fe-02-d`), 5 son un defecto de fixture (`GET /me` 500 por correo con TLD reservado `.test`) y 3 son guardas obsoletas (cabeza Alembic y fechas literales). La CI (`.github/workflows/backend-ci.yml:7-10`) ejecuta pytest **solo en `pull_request`** y el historial es de commits directos a `main`: **la suite declarada a CI nunca se ejecuta en el flujo real**.

---

## 1. Método, fuentes y estado de la evidencia

### 1.1 Fuentes primarias

- Código: `backend/app/**` (auth, tenancy, business_units, masters, lots, operations, review, corrections, reversals, reports, dashboard, audit, notifications, integrations/sap), `frontend/src/stores/auth.store.ts`, `backend/Dockerfile`, `backend/docker-entrypoint.sh`, `docker-compose.yml`, `frontend/nginx.conf`.
- Tests: `backend/tests/*.py` (ejecutados en HEAD contra PostgreSQL de pruebas, 1210 s).
- Runtime: (a) producción-like `https://avicola.globaldv.net`, empresa 1, recorrido GP por UI/API oficiales (`evidence/runtime-gp-e2e.json`); (b) pila local aislada con `lifespan` activo y base sembrada (`evidence/ui-e2e-local.json`); (c) certificaciones previas de runtime `audit/ga-fe-02-d/GA_FE_02_D_OD16_GLOBAL_READ_RECONCILIATION.md` y `audit/ga-fe-02-e/GA_FE_02_E_FINAL_GENERATION_RECERTIFICATION.md` (2026-09-11).
- Backlog para deduplicación: `audit/remediation/REMEDIATION_BACKLOG.md`, `audit/remediation/UPDATE_SCHEMA_SECURITY_MATRIX.md`, `specs/remediation/GA-REM-003-AUTH-CONTEXT-AND-TOKEN-LIFECYCLE.md`.

### 1.2 Estado de la suite backend en HEAD (hecho verificado)

`25 failed, 1201 passed, 49 skipped, 16 warnings in 1210.23s`. Clasificación exacta de los 25 (detalle en Anexo B):

| Categoría | Nº | Tests | Causa | Naturaleza |
|---|---|---|---|---|
| Obsoletos frente a OD-16 (esperan `403`, reciben `404`) | 13 | `test_lots_bu_enforcement.py::test_l08_*` ×4, `test_operations_bu_enforcement.py::test_w13_*` ×4, `::test_a13_*`, `test_review_bu_enforcement.py::test_165_01_*`, `test_state_continuity.py::test_s07_*`, `test_internal_reversal.py::test_s03_s04_*`, `test_review_decision_concurrency.py::test_r166_12_*` | La autoridad global situada sobre una unidad apagada recibe «no encontrado» (404) en vez de 403: **fail-closed**, coherente con `OD-16.e` ratificado en `audit/ga-fe-02-d` («OFF→0/404/403») | TEST_STALE — actualizar aserciones |
| Obsoletos frente a OD-16 (esperan visibilidad de control de la unidad apagada) | 4 | `test_lots_bu_enforcement.py::test_l11_*`, `::test_e06_*`, `test_operations_bu_enforcement.py::test_a08_*`, `test_od14_productive_surfaces.py::test_s02_*` | La lectura de la autoridad global situada ya no incluye la unidad apagada (`business_units/service.py:143-144`) | TEST_STALE |
| `GET /me` → 500 en fixture R-188 | 5 | `test_r188_bu_lifecycle.py::test_r188_{apagar_termina…, reactivar_no_devuelve…, concesion_nueva…, zero_bu…, transferencia…}` | Fixture crea usuarios con `email=…@e.test` (`tests/test_r188_bu_lifecycle.py:79`); `UserRead.email: EmailStr` (`app/auth/schemas.py:30`) con `email-validator>=2.3.0` (`backend/requirements.txt:17`) rechaza el TLD reservado `.test` en `UserRead.model_validate(user)` (`app/auth/service.py:329`) → excepción no controlada → 500 | TEST_DEFECT **y nota de robustez**: una fila `users.email` que pydantic rechace hace fallar con 500 `GET /me` y `GET /users` para ese usuario (la validación de salida convierte un dato persistido en error de servidor). Recomendación: validar en entrada y serializar en salida sin `EmailStr`, o normalizar. |
| Guardas obsoletas | 3 | `test_company_catalog.py::test_t10_*` y `test_population_invariant.py::test_ac14_*` (esperan cabeza `x4y5z6a7b8c9`, la real es `y5z6a7b8c9d0`, `tests/test_population_invariant.py:398`); `test_time_determinism.py::test_t028_04_*` (fechas literales `2026-09-11` en docstrings de `test_r188_bu_lifecycle.py:3`, `test_r187_ipe_od22_scale.py:3`, `test_r184_ipe_date_semantics.py:4,50`) | Recuentos exactos no actualizados tras `y5z6a7b8c9d0`; docstrings con fechas | TEST_STALE |

**CI**: `.github/workflows/backend-ci.yml:7-10` — `on: pull_request: branches: [main]` con el comentario explícito «Los tests corren SOLO en Pull Requests, NUNCA en push directo a main». Los commits recientes (`c0b4afc`, `91bd27a`, `df8977c`, …) son pushes directos a `main`. Consecuencia: las regresiones «declaradas a CI» en los informes de cierre se ejecutaron localmente por los agentes, nunca por la pipeline. Esto no es un hueco de seguridad del producto, pero sí de **gobernanza de la evidencia**: el estado rojo de 25 tests en HEAD no fue detectado por ningún mecanismo automático.

### 1.3 Evidencia de runtime relevante para seguridad

| Observación | Entorno | Resultado | Fuente |
|---|---|---|---|
| BR-14 segregación: el aprobador que rechazó no puede aprobar el mismo registro | producción-like, empresa 1 | `approve` → **403** con mensaje claro | `evidence/runtime-gp-e2e.json` (R-11) |
| Sin 5xx en 52 respuestas 4xx del recorrido | producción-like | `5xx 0 · 4xx 52 · pageerror 0` | `evidence/runtime-gp-e2e.json` (resumen) |
| OD-16 familia completa con todas las unidades OFF: `/lots` 0 · `/lots/1` 404 · `/operations` 0 · `/review/pending` 0 · `/dashboard/admin` 0 · `/reports/kpis/mortality?lot_id=1` 404; plano de control intacto | producción-like (2026-09-11) | 22/22 PASS | `audit/ga-fe-02-e/GA_FE_02_E_FINAL_GENERATION_RECERTIFICATION.md §13` |
| OD-23: apagar termina concesiones vivas; reactivar no las devuelve; concesión nueva restaura; auditoría 1:1 (`config_change`×5, `permission_change`×6) | producción-like (2026-09-11) | PASS | `audit/ga-fe-02-e/… §12-13`, `audit/ga-fe-02-b/GA_FE_02_B_ENV01_MUTATION_LEDGER.md` filas 11-12 |
| Auto-concesión → 403; concesión cross-company → 404; global OFF write → 403 | producción-like (2026-09-11) | PASS | `audit/ga-fe-02-e/… §2, §13` |
| `/reports/kpis` (sin lote) con unidades OFF | producción-like (2026-09-11) | 200 «valores nulos/vacíos en este fixture» — **no discriminante** para GAP-07 | `audit/ga-fe-02-d/GA_FE_02_D_OD16_GLOBAL_READ_RECONCILIATION.md:55` |
| `active_alerts` del panel con unidades OFF | — | **No probado** (fixture sin alertas: `ga-fe-02-d:52`) | GAP-08 queda CONFIRMED_IN_CODE, UNKNOWN en runtime |

---

## 2. Cadena canónica y punto de entrada común

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| JWT decodificado y **usuario recargado de BD** con `is_active` en cada petición | PASS | `app/auth/security.py:72-104` (`select(User)`; `if not user or not user.is_active → 401`) | `tests/test_rbac.py::test_ac06_*`, `tests/test_security_regression.py` | Usuarios dados de baja → login posterior 403 (`ga-fe-02-e §16`) |
| Permisos leídos de BD (no del JWT); `role_id` del token no autoriza | PASS | `security.py:111-121`; `auth/models.py:33,47` (`lazy="selectin"`); `tiene_permiso` `security.py:199-209`; claims `auth/service.py:24-41` | `tests/test_role_administration.py::test_t_092_05_*`, `tests/test_rbac.py` | — |
| Empresa efectiva (`OD-11`) resuelta por petición; usuario normal no reclama otra empresa | PASS | `app/tenancy.py:258-307` | `tests/test_multicompany_isolation.py::test_un_usuario_normal_no_desplaza_su_contexto`, `tests/test_session_payload.py::test_h13_*` | — |
| Cobertura de autorización en arranque (`AC08`): toda ruta declara permiso o exención | PASS | `app/authorization_coverage.py:94-115`; `app/main.py:174-176`; `RUTAS_PUBLICAS` 7 (`:21-29`), `RUTAS_DE_TITULAR` 8 (`:42-59`) | `tests/test_rbac.py::test_ac08_*`, `::test_ac08b_*` | — |
| Frontera transaccional verificada en arranque (`GA-REM-026 AC11`) | PASS | `app/transaction.py:76-104`; `main.py:181-183` | `tests/test_transaction_boundary.py::test_t_026_10/11` | — |
| Clasificación BU por ruta (`AC-C15`) | PASS (declarativo) | `app/business_units/route_scope.py:220-252`; `main.py:189-191` | `test_ac_c15_toda_ruta_esta_clasificada` | **Clasificar no protege**: `unidad_requerida()` (`route_scope.py:215-217`) no tiene llamadores (GAP-17). |

---

## 3. Compuertas

### 3.1 Aislamiento de inquilino (tenant) — **PARTIAL**

Aislamiento sólido y fail-closed (sin empresa ⇒ cero filas) en auth, maestros, lotes, operaciones, revisión, auditoría y notificaciones. Cuatro residuos: SAP sin contexto (GAP-02), `company_id` de maestros fijable (GAP-05), estructurales del lote sin verificar (GAP-06) y restablecimiento de contraseña sin contexto (GAP-04).

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| `auth` · usuarios list/get/update/deactivate acotados a la empresa efectiva; fail-closed sin empresa | PASS | `app/auth/service.py:79-114` (`_acotar`, `_usuario_alcanzable`), `:291-335`, `:384-421`, `:491-505`; `UserUpdate` `extra=forbid` sin `company_id` (`auth/schemas.py:65-85`) | `tests/test_user_tenant_isolation.py`, `tests/test_od14_productive_surfaces.py`, `tests/test_role_tenancy.py::test_r05_*` | — |
| `auth` · alta de usuario: empresa del contexto, no del cuerpo | PASS | `auth/service.py:349-361` | `tests/test_user_tenant_isolation.py` (R-118) | — |
| `auth` · roles por inquilino; plantillas de sistema visibles y no editables | PASS | `auth/service.py:116-171`, `:562-658` | `tests/test_role_tenancy.py::test_r01…r07` | — |
| `auth` · **actor de empresa no puede fabricar/asignar autoridad global** (`OD-13.c`, `AC-R06`) | **FAIL** | `create_role` `auth/service.py:585-619` y `update_role` `:621-658` no validan el contenido de `permissions`; `_rol_asignable` `:116-142` solo consulta `_es_autoridad_global` para roles con `company_id IS NULL` (`:139-141`) y devuelve `rol.company_id == empresa` para roles de inquilino (`:142`); `get_current_user` `security.py:119-120` marca `is_super_admin` por el permiso `("*", all)` sin mirar `Role.company_id` | `tests/test_role_tenancy.py::test_r06_*` prueba solo la plantilla global. **NO TEST** del camino real | No probado en runtime (no se crean roles en el entorno certificado). **GAP-01** |
| `masters` · `_apply_company_filter`: `companies` por identidad, control global solo `_CONTROL_GLOBAL`, fail-closed | PASS | `app/masters/service.py:54-97` | `tests/test_master_tenant_isolation.py`, `tests/test_company_catalog.py` | — |
| `masters` · cadena granja→galpón, planta→incubadora | PASS | `masters/service.py:187-206`; `masters/router.py:132-174` | `tests/security/test_multitenant_isolation.py::test_no_se_puede_crear_un_galpon_en_una_granja_ajena`, `tests/test_od14_productive_surfaces.py::test_s07/s08_*` | — |
| `masters` · **`company_id` fijable desde el cliente** en Create/Update | **FAIL** (registrado) | `masters/schemas.py:64-65`, `:124-125`, `:188,249,268,286,306,324,341,358,377,394,412,632` (Create), `:436,446,465,474,485,493,503,651` (Update); `masters/service.py:232-234` (solo impone si llega nulo), `:248-254` (`setattr` de todo lo enviado) | **NO TEST** con `company_id` ajeno | **GAP-05 = R-50** (`UPDATE_SCHEMA_SECURITY_MATRIX.md:59,105`); mitigación: semilla `alembic/versions/l2m3n4o5p6q7:45-107` da `masters:create/update` solo al Super Admin |
| `masters` · curvas de peso: tenencia por la línea | PASS | `app/masters/curves.py:66-87` | `tests/test_od14_productive_surfaces.py::test_s06_*`, `tests/test_genetic_curves.py` | — |
| `lots` · list/get/update/close/phases/opening-balance por empresa (+unidad) | PASS | `app/lots/service.py:250-273`, `:411-436`, `:438-443`, `:661-697` | `tests/test_lot_row_scope.py`, `tests/test_multicompany_isolation.py::test_idor_*` | `/lots/1` 404 con unidad OFF (`ga-fe-02-e §13`) |
| `lots` · alta: pertenencia de `farm_id`, `area_id` | PASS | `lots/service.py:320-329` (granja → 403), `:341-347` (`verificar_catalogo_de_empresa`) | `tests/test_lot_area_ownership.py::test_ga06a_01/02` | — |
| `lots` · **alta/edición no verifican `house_id`, `genetic_line_id`, `weight_curve_id`** | **FAIL** | `lots/service.py:362-392` asigna sin `verificar_pertenencia`; `_curva_del_lote` `:275-307` solo comprueba `curva.genetic_line_id == genetic_line_id`; `update_lot` → `MasterService.update` con `_PADRES_TENANT = {farm_id, hatchery_id}` (`masters/service.py:187`); `LotUpdate` admite `house_id`, `genetic_line_id` (`lots/schemas.py:65-67`); exposición de `expected_min/max` ajenos en `GET /operations/{id}/weight-evaluation` (`operations/service.py:744-824`) | **NO TEST** | **GAP-06** |
| `lots` · egg-batches / chick-batches (traspaso) | PASS | `app/lots/router.py:239-331`; `app/tenancy.py:204-253` | `tests/test_handoff_contract.py`, `tests/test_traceability_ownership.py` | — |
| `operations` · create/list/get/update/cancel/submit acotados; fail-closed | PASS | `app/operations/service.py:93-102` (`_acotar_a_empresa` → `false()`), `:1052`, `:1109-1124`, `:1130-1174`, `:1307-1351`; `validators.py:501-529` | `tests/test_od14_productive_surfaces.py::test_s02_*`, `tests/test_multi_company.py`, `tests/security/test_multitenant_isolation.py` | `/operations/37` 404 con unidad OFF |
| `operations` · referencias estructurales (R-180) y catálogos (R-179) del submovimiento | PASS | `operations/service.py:841-877`, `:1209-1216`; `tenancy.py:73-186` | `tests/test_submovement_structural_tenancy.py`, `tests/test_master_reference_tenancy.py` | BR-08 aplicado en runtime (galpón exigido en eventos de ubicación) |
| `operations` · edición/corrección: destino verificado como un alta | PASS | `operations/service.py:1261-1305`; `app/corrections/service.py:70-81` | `tests/test_operations_bu_enforcement.py::test_w09_*`, `tests/test_edit_validation_parity.py` | — |
| `operations` · `sap_document_ref` (OC) buscada dentro de la empresa | PASS | `validators.py:757-764`, `:778-779` | `tests/test_purchase_order_receipt.py` | BR-18 aplicado en runtime (límite de OC) |
| `review/approvals/corrections/reversals` · pertenencia del evento | PASS | `app/review/service.py:387-402`, `:614-634`; `corrections/service.py:26-30`, `:116-127`; `app/reversals/service.py:88-96`, `:165-178` | `tests/security/test_multitenant_isolation.py::test_no_se_puede_{corregir,revisar,aprobar}_un_evento_ajeno`, `tests/test_internal_reversal.py::test_s01_s02_*` | — |
| `reports/dashboard` · filtros de lote por empresa | PASS | `app/reports/service.py:37-70`, `:314-318`, `:379-386`; `app/dashboard/service.py:17-36`, `:49-73`, `:96-140` | `tests/test_kpi_scope.py::test_el_kpi_de_otra_empresa_sigue_siendo_inalcanzable`, `tests/test_kpi_hatchery.py::test_t_022_06` | — |
| `audit` · `company_id == self.company_id` en list/get/timeline; escritura sin empresa descartada | PASS lectura / PARTIAL escritura | `app/audit/service.py:48-49`, `:104-108`, `:117-122`; `audit/models.py:78` (NOT NULL); `audit/helpers.py:250-252`; `audit/listeners.py:140` (`company_id or 0`) | `tests/test_audit_query.py`, `tests/test_audit_coverage.py::test_t_081_02` | **GAP-10 = R-83** |
| `notifications` · destinatario **y** empresa | PASS | `app/notifications/service.py:124-134`, `:159-164`; `router.py:55-80`; `recipients.py:54-98`, `:132-145` | `tests/test_notifications.py`, `tests/test_notification_recipients.py::test_t_038_25` | — |
| `business_units` admin · empresa del contexto, dirección por código | PASS | `app/business_units/router.py:58-73`; `admin.py:73-110` | `tests/test_business_unit_admin.py::test_el_listado_no_deja_ver_la_configuracion_de_otra_empresa` | — |
| `sap` · references/consolidated/payloads/jobs/errors por empresa **para el actor de empresa** | PASS (actor de empresa) / **FAIL** (autoridad global sin contexto) | `app/integrations/sap/service.py:76-81` (`_company_filter` → `true()` si `company_id is None`); `:128-135`, `:158-161`, `:239-242`, **`:404-408` (`retry_failed`, escritura)**, `:532-537`, `:547-551`, `:564-567`, `:582-583` | `tests/test_sap_transversal.py::test_ac_sap02_*` (solo actor de empresa). **NO TEST** global sin contexto | `FEATURE_SAP_ENABLED` por defecto `true` (`docker-compose.yml:26`). **GAP-02** |
| `auth` · **restablecimiento de contraseña por administrador** solo `is_super_admin`, **sin contexto** | **FAIL** | `auth/service.py:443-446` (`select(User).where(id)` global), `:449-455`; comentario `:434-436` reconoce la deuda | `tests/test_p013_password.py::test_t012_05/06` (parcial) | **GAP-04** |

### 3.2 Habilitación de empresa (Company BU) — **PASS**

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| Resolutor central: efectivas = misma empresa ∧ `is_enabled` ∧ concesión viva ∧ unidad activa; **leído de BD en cada llamada** | PASS | `app/business_units/service.py:97-123` (`unidades_efectivas_por_id`), `:126-147` (`unidades_de_alcance_productivo`); sin concesiones → `[]` → `false()` (`scope.py:48-49`) | `tests/test_business_units.py`, `tests/test_business_unit_guard.py`, `tests/test_session_payload.py::test_una_revocacion_se_ve_en_la_sesion_siguiente` | `ga-fe-02-e §13` OFF→0/404 |
| Concesión viva sobre unidad apagada **no** da acceso (`OD-16.e`) | PASS | `service.py:117-121` (`is_enabled` en la misma consulta) | `tests/test_operations_bu_enforcement.py::test_w02_*`, `tests/test_lots_bu_enforcement.py::test_l03_*` | `ga-fe-02-e §14` (`is_effective=false`) |
| Autoridad global y unidad apagada = inaccesible en lectura y escritura (`OD-16.e/f`) | PASS | `business_units/service.py:143-144`, `:278-284`; `masters/service.py:99-120` | `tests/test_od16_global_read_boundary.py`, `tests/test_lots_bu_enforcement.py::test_l07_*`, `tests/test_review_bu_enforcement.py::test_165_01` (obsoleto en aserción 403→404, ver §1.2) | `ga-fe-02-e §13`: GLOBAL OFF read DENY, OFF write DENY (403) |
| Escritura productiva exige `exigir_unidad_operativa` en operaciones, lotes, revisión, correcciones, reversos, evidencias, alertas | PASS | `operations/service.py:159-214`, `:242-246`, `:1290-1292`, `:1309`, `:1327`, `:1370`, `:1408`, `:1019`; `lots/service.py:223-243`, `:359-360`, `:418`, `:443`, `:580`, `:692`; `review/service.py:110-117`, `:387-402`, `:614-634`; `corrections/service.py:28-30`; `reversals/service.py:94-95`, `:175` | `tests/test_operations_bu_enforcement.py` (W02…W14), `tests/test_lots_bu_enforcement.py` (L03…L15), `tests/test_review_bu_enforcement.py::test_165_01…05`, `tests/test_internal_reversal.py::test_s03_s04_*` | — |
| Excepciones por diseño: plano de control (`business_units` admin), SAP (`CONTRATO`, `BU-D04`), auditoría (`BU-D03`) | PASS (decisión) | `admin.py:420`; `sap/service.py`; `audit/service.py:48` | `tests/test_business_unit_admin.py` L15 | Plano de control intacto con OFF (`ga-fe-02-e §13`) |

### 3.3 Concesión de usuario (User BU) — **PASS**

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| Concesión evaluada de BD por petición; revocación inmediata (no hay estado BU en el JWT) | PASS | `auth/service.py:24-41` (claims sin unidades); `business_units/service.py:97-123`; `/me` compone en cada llamada `auth/router.py:61-84` | `tests/test_session_payload.py::test_una_revocacion_se_ve_en_la_sesion_siguiente`, `tests/test_r188_bu_lifecycle.py` (5 rojos por fixture, ver §1.2) | `ga-fe-02-e §2`: revoke → acceso retirado en la petición siguiente |
| Lectura productiva acotada por lotes alcanzables (lotes, eventos, alertas de operaciones, KPI por lote, panel: contadores/tendencia/`lots_by_type`) | PASS | `operations/service.py:1058-1061`, `:1116-1119`, `:997-1009`; `lots/service.py:255-256`, `:271-272`; `reports/service.py:37-62`; `dashboard/service.py:17-36`, `:44-73`, `:93-140`, `:154-204` | `tests/test_kpi_scope.py` (7 por lote + panel), `tests/test_lots_bu_enforcement.py::test_e02/e03/e08_*`, `tests/test_pending_classification.py` | `ga-fe-02-e §13` ON(solo broiler) → solo `L-BO-2026-05/06` |
| Lectura agregada sin `lot_id` (`/reports/kpis/hatchery`, `/reports/kpis` → `hatchery_yield`) | **FAIL** | `reports/service.py:191-207`, `:262-308`, `:415-420` (`where(company_id)` sin `_filtro_de_lotes` `:64-70`) | `tests/test_kpi_hatchery.py::test_t_022_06` solo otra empresa. **NO TEST** | No discriminado en runtime (`ga-fe-02-d:55`). **GAP-07** |
| `dashboard/admin.active_alerts` sin predicado de unidad | **FAIL** | `dashboard/service.py:206-242` (calcula `_ambito` `:212-213`, no lo aplica `:224-227`; comentario `:208-211` afirma lo contrario) | **NO TEST** (grep `active_alerts` en `tests/`: vacío) | No probado (fixture sin alertas, `ga-fe-02-d:52`). **GAP-08** |
| Notificaciones: canal `CORE`; el aviso puede llevar `lot_id` de una unidad no concedida al destinatario | PASS (decisión `OD-08`) | `notifications/recipients.py:101-147` | `tests/test_notification_recipients.py` | — |

### 3.4 RBAC — **FAIL**

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| Toda ruta declara permiso; permisos por BD; cambio de rol surte efecto en la siguiente petición | PASS | `authorization_coverage.py:94-115`; `security.py:98-121` | `tests/test_rbac.py::test_ac08_*`, `tests/test_role_administration.py::test_t_092_05_*` | — |
| **Fabricación de autoridad global desde un rol de inquilino** | **FAIL (P1)** | ver §3.1 fila `auth · actor de empresa…`; `security.py:119-120`; `auth/service.py:507-540` (`switch_company` honra `is_super_admin`) | **NO TEST** | **GAP-01**. Requiere `users:create`+`users:update` en el inquilino: hoy solo Super Admin en la semilla, pero es la capacidad prevista para el administrador de empresa (`GA-REM-034`, `OD-13`). |
| `PermissionCreate.module/action/scope_type` sin validar contra catálogo | PARTIAL | `auth/schemas.py:201-205`; `auth/service.py:602` (`PermissionAction(...)` inválido → `ValueError` 500) | — | GAP-16 (raíz compartida con GAP-01: el servidor acepta cualquier tupla de permiso) |
| Permiso de lote de aprobación más débil que el unitario (`batch-approve/reject` exigen `review:review`; unitarios `approvals:approve/reject`) | **FAIL** (control interno) | `review/router.py:123-160`; semilla: «Supervisor Avícola» tiene `review:review` (`alembic/versions/l2m3n4o5p6q7:54-60`) y solo «Aprobador» `approvals:approve/reject` (`:68-74`) | **NO TEST** | Tratado como **E-09** en el documento de integridad (consistencia de aprobación); se referencia aquí porque es un defecto RBAC |
| Autoridad global es contextual en dato productivo y maestros (`OD-14`) | PASS (con dos excepciones) | inventario de atajos en Anexo A | `tests/test_od14_productive_surfaces.py` | GAP-02 (SAP), GAP-04 (contraseña) |

### 3.5 OD-16 (apagado de empresa prevalece) — **PARTIAL**

Absoluto en todas las superficies de fila (lotes, operaciones, revisión, correcciones, reversos, evidencias, alertas de operaciones, KPI por lote, maestros con predicado de unidad, panel: contadores/tendencia/`lots_by_type`), para todo actor incluida la autoridad global, y certificado en runtime (`ga-fe-02-d/e`). **Residuo**: dos superficies agregadas (GAP-07, GAP-08) filtran únicamente por empresa y por tanto incluyen dato de unidades apagadas. Bajo §23 del encargo («Company BU OFF is absolute for productive operation … reports … Any violation: blocking P1 until evidence proves otherwise») ambos son **bloqueantes hasta ratificación**; por impacto (lectura agregada intra-empresa, sin escritura) la severidad técnica es P2 y la corrección es un predicado `lot_id.in_(...)` en cada caso.

| Superficie | Veredicto | Código | Tests | Runtime |
|---|---|---|---|---|
| Navegación / formularios / deep links (frontend refleja `/me.effective_units`) | PASS | `auth/router.py:40-84`; `auth/schemas.py:100-140` | `tests/test_session_payload.py` (h11-h14) | `ga-fe-02-e` E2E-01…10 desktop+móvil |
| APIs de fila | PASS | §3.2 | §3.2 | `ga-fe-02-e §13` |
| Reportes por lote | PASS | `reports/service.py:37-62` | `tests/test_kpi_scope.py::test_apagar_la_unidad_retira_su_kpi` | `/reports/kpis/mortality?lot_id=1` → 404 |
| Reportes agregados sin lote | **FAIL** | `reports/service.py:191-207`, `:262-308`, `:415-420` | NO TEST | GAP-07 |
| Panel `active_alerts` | **FAIL** | `dashboard/service.py:206-242` | NO TEST | GAP-08 |
| Evidencias (descarga/borrado) | PASS | `operations/service.py:1387-1435` | `tests/test_lots_bu_enforcement.py::test_e01…e08`, `tests/test_od14_productive_surfaces.py::test_s03/s04_*` | — |
| Actor global no salta OFF | PASS | `business_units/service.py:143-144`, `:278-284` | `tests/test_od16_global_read_boundary.py` | `ga-fe-02-e §13` |

### 3.6 OD-23 (ciclo apagar / encender / concesión nueva) — **PASS**

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| `disable` marca `revoked_at` en todas las concesiones vivas y audita cada una con causa | PASS | `business_units/admin.py:178-193`, `:205-214` (`PERMISSION_CHANGE`, `cause: company_business_unit_disabled`), `:197-203` (`CONFIG_CHANGE`) | `tests/test_r188_bu_lifecycle.py::test_r188_apagar_termina_las_concesiones_vivas` (rojo por fixture `.test`, no por producto), `::test_r188_auditoria_de_terminacion_por_ciclo`, `::test_r188_apagado_idempotente_normaliza_estado_previo` | `ga-fe-02-e §12` auditoría 1:1 |
| `enable` **no** revive concesiones | PASS | `admin.py:170-176`; ningún camino pone `revoked_at = NULL` (grep) | `tests/test_business_unit_admin.py::test_r188_deshabilitar_termina_y_rehabilitar_no_devuelve` | `ga-fe-02-e §13` |
| Concesión nueva restaura y conserva historia (índice único parcial entre vivas) | PASS | `admin.py:368-391`; `business_units/models.py:121-122` | `tests/test_business_unit_admin.py::test_una_concesion_revocada_se_puede_volver_a_otorgar` | `ga-fe-02-e §2` grant C ×2 |
| Conceder con empresa OFF → 409; unidad inexistente/inactiva → 404 | PASS | `admin.py:356-366`; `router.py:76-89` | `tests/test_business_unit_admin.py::test_habilitar_una_unidad_inexistente_es_404` | `ga-fe-02/GA_FE_02_CLARIFICATIONS.md:38` |
| Revocar marca (no borra), efecto inmediato, 404 si no viva | PASS | `admin.py:394-429`; `service.py:353-377` | `tests/test_business_unit_admin.py::test_revocar_retira_el_acceso_de_inmediato_y_conserva_la_historia` | `ga-fe-02-e §2` |
| Sesión activa pierde acceso de inmediato (UI, API, refresh, relogin, navegación) | PASS | claims sin unidades `auth/service.py:24-41`; evaluación por petición `service.py:97-123` | `tests/test_session_payload.py::test_una_revocacion_se_ve_en_la_sesion_siguiente` | `ga-fe-02-a:300` refresh/relogin 22/22 |
| Cambio de empresa persistida revoca concesiones (`OD-09.e`) | PASS (por ausencia de camino) | `service.py:321-350` sin llamador; `UserUpdate` no admite `company_id` | `tests/test_r188_bu_lifecycle.py::test_r188_transferencia_de_empresa_intacta` (rojo por fixture) | — |

### 3.7 Administrador de accesos (OD-15) — **PASS**

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| Permisos propios de plano de control `business_units:read/update/create/delete` | PASS | `business_units/router.py:43-55`, `:98,109,129,151,172,193,216`; catálogo `auth/service.py:546-553` | `tests/test_access_administration.py`, `tests/test_business_unit_admin.py::test_llamarse_administrador_no_administra_nada` | — |
| Auto-concesión denegada en servidor antes de cualquier otra puerta (`OD-15.a/c`) | PASS | `admin.py:348-350` → 403 `router.py:85-88` | `tests/test_r188_bu_lifecycle.py::test_r188_self_grant_denegado`, `tests/test_grant_candidates.py::test_c11_*` | `ga-fe-02-e §2` auto-concesión 403 |
| Concesión cruzada entre empresas imposible (dos puertas) | PASS | `admin.py:98-110`, `:352-354`; `service.py:201-231` | `tests/test_r188_bu_lifecycle.py::test_r188_cross_company_denegado`, `tests/test_business_unit_admin.py::test_no_se_concede_a_un_usuario_de_otra_empresa` | cross-company 404 |
| Candidatos: proyección mínima, sin `users:read`, sin búsqueda por id | PASS | `router.py:146-162`; `admin.py:265-314` | `tests/test_grant_candidates.py::test_c2_*`, `::test_c3_*`, `::test_c4_c5_*`, `::test_c8_*` | — |
| Administrar no es acceder: el rol de accesos no gana alcance productivo | PASS | `admin.py:18-22`; `service.py:97-123` no consulta roles | `tests/test_business_unit_admin.py::test_administrar_no_cambia_el_alcance_operativo_del_administrador`, `tests/test_session_payload.py::test_h14_*` | `ga-fe-02-e` actor A (`dashboard:read` + BU admin) sin dato productivo |
| Frontend ofrece la superficie correcta de gestión de concesiones | PASS | `frontend/src` (consola de acceso por unidad; capturas `E03-unit-access.png`) | vitest `gaFe02.*` | `ga-fe-02-e` grant/revoke por UI y móvil |
| Escalada a autoridad global «por rol» | ver GAP-01 (RBAC) | — | — | — |

### 3.8 Actor global (OD-14) — **PARTIAL**

Contextual en todo el dato productivo y maestros (inventario completo de atajos `is_super_admin` en Anexo A). Dos superficies incumplen `OD-14.d` (fail-closed sin contexto):

| Superficie | Veredicto | Código | Tests | Notas |
|---|---|---|---|---|
| `switch-company`: solo autoridad global, empresa activa, auditado `CONTEXT_SWITCHED` | PASS | `auth/service.py:507-540`; `tenancy.py:294-307` | `tests/test_multicompany_isolation.py::test_el_super_admin_no_puede_situarse_en_una_empresa_inexistente` | — |
| Sin contexto → cero filas en auth/masters/lots/operations/reports/dashboard | PASS | `auth/service.py:91-96`; `masters/service.py:85-97`; `operations/service.py:93-102`; `business_units/service.py:143-147` | `tests/test_od14_productive_surfaces.py` | — |
| **SAP sin contexto: lectura de todas las empresas y `retry_failed` de todas** | **FAIL** | `sap/service.py:76-81`, `:404-413` | NO TEST | **GAP-02** |
| **Restablecimiento de contraseña sin contexto** (superficie `CONTROL` de inquilino `route_scope.py:81`) | **FAIL** | `auth/service.py:443-455` | parcial | **GAP-04** |
| `get_company_filter` legado fail-open, sin consumidores | nota | `security.py:170-178`; exportado en `dependencies.py:2` | — | GAP-16 (retirar) |

### 3.9 Cruce de empresa — **FAIL**

| Control | Veredicto | Código | Tests | Notas |
|---|---|---|---|---|
| Superficies certificadas (usuarios, roles, maestros por padre, lotes por empresa, eventos, revisión, evidencias, notificaciones, BU admin) | PASS | §3.1 | §3.1 | — |
| Escritura foránea aceptada en `POST/PUT /lots` (`house_id`, `genetic_line_id`, `weight_curve_id`) con `lots:create`/`lots:update` | **FAIL** | `lots/service.py:362-392`, `:275-307`, `:411-436` | NO TEST | **GAP-06**. IDs enteros secuenciales: no hace falta conocer nada de la otra empresa para acertar. |
| `company_id` de maestros fijable (mover un maestro propio a otra empresa o a `NULL`) | **FAIL** (mitigado por semilla) | `masters/service.py:232-234`, `:248-254` | NO TEST | **GAP-05 = R-50** |
| Oráculos de unicidad global (`lot_code`, `username`, `email`, `idempotency_key`) | PARTIAL | `masters/models.py:294`; `auth/models.py:18-19`; `operations/models.py:101` vs `service.py:224-231`; `lots/service.py:311-318`; `auth/service.py:345-347` | — | **GAP-15** (P3) |
| Política 404 vs 403 (ajeno = inexistente; excepciones documentadas: evidencias 403 R-139, unidad de lote 403, segregación 403) | PASS | `tenancy.py:39-70`; `admin.py:49-55` | `tests/test_submovement_structural_tenancy.py::test_r180_13_*`, `tests/test_grant_candidates.py::test_c3_*` | — |

### 3.10 Autenticación y sesión — **FAIL**

| Control | Veredicto | Código (file:line) | Tests | Runtime |
|---|---|---|---|---|
| Login: bcrypt; `LOGIN_FAILED` auditado con commit propio; cuenta desactivada → 403 | PASS | `auth/service.py:175-223`; `security.py:15-27` | `tests/test_auth.py`, `tests/test_audit_coverage.py::test_t_081_01/02` | login de usuario de baja → 403 (`ga-fe-02-e §16`) |
| Refresh: valida `type == "refresh"`, recarga usuario, conserva contexto solo a la autoridad global | PASS | `auth/service.py:241-287` | `tests/test_security_regression.py::test_r43_*`, `tests/test_rbac.py::test_ga_rem_003_*`, `tests/test_multicompany_isolation.py::test_el_contexto_sobrevive_a_la_renovacion` | — |
| **Access path no comprueba `type`: un refresh token (7 días) sirve como Bearer** | **FAIL** | `security.py:59-65` (`decode_token` no mira `type`), `:87-93`; `create_refresh_token` `:48-56`; `config.py:48-49` (30 min / 7 días) | **NO TEST** | Cliente web guarda ambos tokens en `sessionStorage` (`frontend/src/stores/auth.store.ts:60-69,106`) y en `localStorage` bajo Telegram Mini App (`:57-58`; `GA-REM-003:74`). **GAP-03** |
| Rotación del refresh / logout / revocación | **FAIL** (registrado) | no existe `POST /logout` (`auth/router.py`; `authorization_coverage.py:21-29`); `refresh_token` reemite sin invalidar (`:282-286`); sin `jti`/denylist | **NO TEST** | **GAP-09 = GA-REM-003** (`REMEDIATION_BACKLOG.md:90` P1-4; `:68` P0-4; `:21` `SPEC_READY`) |
| Cambio de contraseña: titular con la actual; política 8+; auditado sin secreto; sesiones previas siguen vivas (decisión `GA-REM-012`) | PASS con nota | `auth/service.py:423-489`; `auth/schemas.py:44-62` | `tests/test_p013_password.py::test_t012_01…08` | Con GAP-03/GAP-09 una credencial comprometida sigue válida hasta 7 días |
| Restablecimiento por administrador | **FAIL** | ver §3.8 | parcial | GAP-04 |
| Expiración; secreto obligatorio y no por defecto; algoritmo fijado | PASS | `config.py:46-67`; `security.py:34-45,61` | `tests/test_environment_guard.py`, `tests/test_runtime_startup.py` | — |
| Rate limit login `5/minute`, global `60/minute` | PARTIAL | `main.py:15-33`, `:70-73`; `auth/router.py:29-32`; clave `get_remote_address` (`main.py:17`); `backend/Dockerfile:62` sin `--forwarded-allow-ips`; `frontend/nginx.conf:67` `X-Forwarded-For` | **NO TEST** (grep `429`: vacío) | UNKNOWN en runtime. **GAP-11** |
| Sesión obsoleta: cambio de permisos/rol/BU surte efecto en la siguiente petición; `/me` informa y no decide | PASS | `security.py:98-121`; `auth/router.py:40-84` | `tests/test_role_administration.py::test_t_092_05_*`, `tests/test_session_payload.py` | `ga-fe-02-a:300` |
| `last_login` nunca se escribe | nota | grep: solo modelo/esquema | — | pendiente `GA-REM-003 §6` |

### 3.11 Endurecimiento de entrada / configuración — **PARTIAL**

| Control | Veredicto | Código (file:line) | Tests | Notas |
|---|---|---|---|---|
| SQL crudo | PASS | única `text()`: `lots/service.py:107` con parámetro ligado | — | — |
| `ilike` parametrizado | PASS | `auth/service.py:304-309`; `masters/service.py:142-149` | — | comodines no escapados (solo resultado) |
| Topes de paginación | PASS | `auth/router.py:102`, `masters/router.py:33`, `audit/router.py:29`, `operations/router.py:122` (≤100/≤200) | — | `pending_classification.skip` sin `ge=0` → `offset(-1)` 500 (`operations/router.py:121`, GAP-16) |
| Asignación masiva vía `setattr` | PARTIAL | `auth/service.py:416-417` (`extra=forbid`), `:635-636`; `review/service.py:691-692`; `corrections/service.py:82` (lista blanca `:171-181`); `operations/service.py:1166-1167` (`extra=forbid`); **`masters/service.py:253-254`** (GAP-05) | `tests/test_security_regression.py::test_r32_*`, `::test_r51_*`, `tests/test_p014_persistence.py` | — |
| CORS | PASS | `main.py:100-107` (`allow_origins` explícito) | NO TEST | — |
| Cabeceras de seguridad | PASS | `main.py:110-124` (`nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, HSTS en `production`) | NO TEST | CSP corresponde a `frontend/nginx.conf` |
| Rate limiting: valor por defecto | PARTIAL | `docker-compose.yml:29` `true`; `.env.example:45` `false`; `config.py:115` `False` | NO TEST | GAP-11 |
| `DEBUG` / OpenAPI público | PASS/nota | `docker-compose.yml:19,87`; `authorization_coverage.py:25-28`; `main.py:64-66` | `tests/test_rbac.py::test_ac08b_*` | decisión declarada |
| Secretos por defecto rechazados en arranque | PASS | `config.py:46-67` | `tests/test_environment_guard.py`, `tests/test_runtime_startup.py` | — |
| Validación de salida convierte dato persistido en 500 (`EmailStr` en `UserRead`) | nota de robustez | `auth/schemas.py:30`; `auth/service.py:329` | 5 tests R-188 rojos por esta causa | ver §1.2 |

### 3.12 Acceso a evidencias (adjuntos) — **PASS** (con P3)

| Control | Veredicto | Código (file:line) | Tests | Notas |
|---|---|---|---|---|
| Path traversal en el nombre | PASS | `operations/router.py:374-378` (`os.path.basename`, prefijo `uuid4().hex`, directorio `MEDIA_DIR/evidences/{company_id}/{event_id}`) | NO TEST | — |
| Tipo y tamaño | PARTIAL | `router.py:21-22`, `:359-366` (`_ALLOWED_MIME`, 10 MB); tipo declarado por el cliente, sin inspección de firma; descarga sirve el `mime_type` guardado (`:405-409`); `nosniff` mitiga | NO TEST | GAP-12 (P3) |
| Descarga: empresa + evento al alcance de unidad (`R-162`) | PASS | `service.py:1416-1435` | `tests/test_lots_bu_enforcement.py::test_e01…e08`, `tests/test_od14_productive_surfaces.py::test_s04_*` | — |
| Borrado: empresa + unidad + guarda de escritura | PASS | `service.py:1387-1414` | `tests/test_operations_bu_enforcement.py::test_w06b_*`, `tests/test_od14_productive_surfaces.py::test_s03_*` | — |
| Persistencia del almacén (`R-52`) | PASS (config) | `docker-compose.yml:31-32,42-43,112-114`; `router.py:20` | — | EXISTING `R-52` |
| Auditoría de subida/borrado | **FAIL** (menor) | ni `create_evidence` ni `delete_evidence` llaman `audit_accion`; listeners solo cubren `OperationalEvent`, `CorrectionLog`, `ApprovalAction` (`audit/listeners.py:71-113`) | NO TEST | GAP-12 (P3); borrado físico antes del commit (`service.py:1409-1414`) |

---

## 4. Tabla consolidada de huecos de seguridad GAP-01 … GAP-17

Severidad: **P0** explotable ahora con privilegios ordinarios y cruce de inquilino · **P1** cruce de inquilino/escalada que requiere una capacidad administrativa prevista, o control de sesión que anula una garantía declarada · **P2** fuga de unidad o control de sesión débil · **P3** endurecimiento/robustez.

| ID | Sev. | Hallazgo | Evidencia (file:line) | Tests | Registro (dedup) | ¿Bloquea SAP? | Razonamiento |
|---|---|---|---|---|---|---|---|
| **GAP-01** | **P1** (P0 si un rol de inquilino ya tiene `users:create`+`users:update`) | Fabricación de autoridad global desde una empresa: `create_role`/`update_role` aceptan `{"module":"*","scope_type":"all"}` en un rol de inquilino; `_rol_asignable` lo considera asignable por ser de la propia empresa; `get_current_user` concede `is_super_admin` sin mirar `Role.company_id` → `switch-company` a cualquier empresa. Contradice `OD-13.c`, `AC-R06`. | `auth/service.py:585-619`, `:621-658`, `:116-142` (rama `:142`); `security.py:119-120`; `auth/service.py:507-540` | NO TEST (`test_r06_*` solo cubre la plantilla global) | **NUEVO** — no figura en `REMEDIATION_BACKLOG.md` ni en `UPDATE_SCHEMA_SECURITY_MATRIX.md`; `R-117` cubrió solo la asignación del rol global existente | **SÍ** | §59: «NO KNOWN P0/P1 SECURITY GAP»; defecto de autoridad material. Corrección: rechazar `("*", "all")` en `create_role`/`update_role` para actores no globales; aplicar `_es_autoridad_global` también a roles de inquilino en `_rol_asignable`; opcionalmente exigir `Role.company_id IS NULL` para computar `is_super_admin`. |
| **GAP-02** | P2 | Autoridad global **sin contexto** lee dato SAP de todas las empresas y **reintenta cargas** de todas (`retry_failed`), contra `OD-14.d`; `FEATURE_SAP_ENABLED=true` por defecto. | `sap/service.py:76-81`, `:128-135`, `:404-413`, `:532-537`, `:547-551`, `:564-567`, `:582-583`; `docker-compose.yml:26` | NO TEST | **NUEVO** (relacionado con `R-112`/`OD-12`, no cubierto por ellos) | **SÍ (fase SAP)** | Es la propia superficie SAP la que es fail-open para el actor global; `retry_failed` es escritura hacia SAP sin contexto. Corrección: `_company_filter` → `false()` si `company_id is None` (patrón `_acotar_a_empresa`). |
| **GAP-03** | P2 | Refresh token aceptado como access token: `get_current_user` no verifica `type == "access"`; el refresh (7 días) autentica cualquier ruta; expiración de 30 min ilusoria. | `security.py:59-65`, `:87-93`; `auth/service.py:48-56`; `config.py:48-49` | NO TEST | **NUEVO** (`GA-REM-003` registra la falta de logout/revocación, no este cruce de tipos) | **SÍ** | Anula la garantía de sesión declarada (30 min) y multiplica el impacto de GAP-09. Corrección de una línea: rechazar `payload.get("type") != "access"`. |
| **GAP-04** | P2 | Restablecimiento de contraseña por administrador: solo `is_super_admin`, **sin contexto de empresa** (viola `OD-14.d`); `users:update` de la empresa no puede restablecer. | `auth/service.py:434-436`, `:443-455` | `tests/test_p013_password.py::test_t012_05/06` (parcial) | **NUEVO** | NO | Superficie de control; el actor global ya tiene autoridad sobre toda empresa. Corregir antes de delegar `users:update` (misma tanda que GAP-01). |
| **GAP-05** | P2 → **P1 condicional** | `company_id` fijable por el cliente en 19 esquemas de maestros (`Farm`/`Hatchery` obligatorio) y 8 de actualización: quien tenga `masters:create/update` crea maestros en otra empresa o mueve los propios a otra o a `NULL` (compartido). | `masters/schemas.py:64-65,124-125,436-503,632-651`; `masters/service.py:232-234,248-254` | NO TEST | **EXISTING: `R-50`** (`UPDATE_SCHEMA_SECURITY_MATRIX.md:59,105`, «mitigado por RBAC», destino `GA-REM-019`); **ausente** de `REMEDIATION_BACKLOG.md` | **CONDICIONAL** | No bloquea con la semilla actual (`masters:*` solo Super Admin). Bloquea si se delega `masters:*` a un rol de inquilino antes de corregirlo (`GA-REM-034` lo permite). Corrección: eliminar `company_id` de Create/Update y resolver del contexto (`OD-14.c`), como `create_user`. |
| **GAP-06** | P2 | Lote con referencias estructurales/catálogo sin verificar: `house_id` (galpón de otra empresa), `genetic_line_id`, `weight_curve_id` (curva de otra empresa aplicada y **expuesta** en `weight-evaluation`). | `lots/service.py:362-392`, `:275-307`, `:411-436`; `masters/service.py:187`; `lots/schemas.py:14-20,65-67`; `operations/service.py:744-824` | NO TEST | **NUEVO** (grep backlog `house_id.*lot`, `línea genética ajena`: vacío) | **SÍ** | §22 «No backend may accept foreign writes» y §60 «foreign-reference integrity»: escritura foránea aceptada con `lots:create` (rol ordinario), sobre dato estructural (lote→galpón→granja) que es maestro SAP-bound. Corrección: `verificar_pertenencia(House)` vía granja y `verificar_catalogo_de_empresa(GeneticLine)` en alta y edición; exigir que `weight_curve_id` cuelgue de una línea de la empresa. |
| **GAP-07** | P2 (P1 por regla §23) | Agregado de incubadora sin `lot_id` (`/reports/kpis/hatchery`, `/reports/kpis`) no acotado por unidad: incluye dato de unidades apagadas/no concedidas. `_filtro_de_lotes` existe y no se usa; `UNIDAD_UNICA` declarado y no aplicado. | `reports/service.py:191-207`, `:262-308`, `:415-420`, `:64-70`; `route_scope.py:174-175,215-217` | NO TEST (solo otra empresa) | **NUEVO** (= E-23 en el documento de integridad) | **SÍ (regla §23, hasta ratificación)** | Runtime previo no discriminante (`ga-fe-02-d:55`). Corrección: `where(OperationalEvent.lot_id.in_(await self._filtro_de_lotes()))` en los cuatro sumatorios cuando `lot_id is None`. |
| **GAP-08** | P2 (P1 por regla §23) | `dashboard/admin.active_alerts` sin predicado de unidad: expone `lot_id`, mensaje (cifras de mortalidad/peso) y `actual_value` de alertas de unidades no concedidas o apagadas. | `dashboard/service.py:206-242` (comparar con `operations/service.py:997-1009`) | NO TEST (grep `active_alerts`: vacío) | **NUEVO** (= E-22) | **SÍ (regla §23, hasta ratificación)** | Runtime no probado (fixture sin alertas). Corrección: `OperationalAlert.lot_id.in_(_lotes)`. |
| **GAP-09** | P1 (backlog `P1-4`) | Sin rotación del refresh, sin `POST /logout`, sin denylist; cambio de contraseña no invalida sesiones. | `auth/service.py:241-287`, `:282-286`; `auth/router.py`; `tests/test_p013_password.py::test_t012_08` | NO TEST de logout (no existe) | **EXISTING: `GA-REM-003`** (`REMEDIATION_BACKLOG.md:90` P1-4, `:68` P0-4, `:21` `SPEC_READY`); `GA-REM-002-003-CERTIFICATION-REPORT.md` no cierra AC04 | **SÍ** | Hallazgo P1 registrado y abierto (§59). Con GAP-03, una credencial robada sigue válida hasta 7 días sin ningún mecanismo de revocación. |
| **GAP-10** | P2 | `audit_logs.company_id NOT NULL`: acciones sin empresa (autoridad global sin contexto, login fallido de usuario inexistente) no se auditan; listener escribe `company_id or 0` (FK inexistente). | `audit/helpers.py:244-252`; `audit/listeners.py:140`; `audit/models.py:78` | — | **EXISTING: `R-83`** (`REMEDIATION_BACKLOG.md:275`, P2 abierto) | NO | Hueco de auditoría, no de autorización; tratado en la compuerta de auditoría del documento de integridad. |
| **GAP-11** | P3 (P2 operativo) | Rate limiting por IP de origen tras proxy sin `--forwarded-allow-ips`: un solo cupo `5/min` login y `60/min` global para todos los usuarios (auto-DoS) o límite inefectivo; sin bloqueo por cuenta. | `main.py:17`; `backend/Dockerfile:62`; `frontend/nginx.conf:67`; `docker-compose.yml:29` | NO TEST | **NUEVO** (`S-05` no registra la clave tras proxy) | NO | UNKNOWN en runtime; endurecimiento operativo. |
| **GAP-12** | P3 | Subida y borrado físico de evidencias sin auditoría; borrado del fichero antes del commit; MIME solo declarado. | `operations/service.py:1363-1414`; `router.py:359-380` | NO TEST | **NUEVO** (relacionado `R-81`, `R-52`; = E-15) | NO | — |
| **GAP-13** | P3 | Inmutabilidad de `audit_logs` solo en aplicación (sin trigger/`REVOKE`). | `alembic/versions/ee30bd1aa374_add_audit_log.py`; grep `TRIGGER\|RULE\|REVOKE` en `alembic/versions`: vacío | NO TEST | **EXISTING: `R-148`** (`REMEDIATION_BACKLOG.md:940`, P2 abierto) | NO | Defensa en profundidad; la aplicación no expone `UPDATE/DELETE` (`audit/router.py:16-63`). Recomendado antes de SAP. |
| **GAP-14** | P3 | Idempotencia SAP: doble consumo del `Result` en el re-enlace idempotente (500); `consolidate_approved` sin bloqueo → dos consolidaciones concurrentes duplican `ConsolidatedMovement` (la 2.ª exportación cae por unicidad con 500). | `sap/service.py:283-293`, `:158-227` | — | **NUEVO** (relacionado `R-112`/`GA-REM-010`) | **SÍ (fase SAP)** | §38: «A critical transaction with known duplicate/split-state risk is NO-GO SAP». Debe cerrarse dentro de `GA-REM-010`/`R-112` antes de conectar un adaptador real. |
| **GAP-15** | P3 | Unicidades **globales** consultadas **por empresa**: `operational_events.idempotency_key` (colisión entre empresas → `IntegrityError` 500 + oráculo), `lots.lot_code` (409 revela código ajeno), `users.username/email` (409). | `operations/models.py:101` vs `service.py:224-231`; `lots/service.py:311-318`; `auth/service.py:345-347` | — | **NUEVO** (residuo de `R-146`, implementada en código pero abierta en `REMEDIATION_BACKLOG.md:938`) | NO | Oráculo de bajo impacto. |
| **GAP-16** | P3 | `PermissionCreate.module/action/scope_type` sin validación contra catálogo (acción inválida → 500; módulo arbitrario aceptado); `pending_classification.skip` sin `ge=0`; `get_company_filter` legado fail-open exportado. | `auth/schemas.py:201-205`; `auth/service.py:602`; `operations/router.py:121`; `security.py:170-178`; `dependencies.py:2` | — | **NUEVO** | NO | Endurecimiento; la primera parte comparte raíz con GAP-01. |
| GAP-17 | P3 | `route_scope.py` declara `UNIDAD_UNICA` para maestros de incubadora/planta y `kpis/hatchery`, pero nada aplica `unidad_requerida`. | `route_scope.py:50-53,174-175,215-217` | `test_ac_c15_*` (solo declaración) | **NUEVO** (documental; la parte productiva es GAP-07) | NO | — |

---

## 5. Deduplicación contra el backlog y hallazgos cerrados verificados

| Referencia | Estado verificado en código | Uso en este documento |
|---|---|---|
| `R-50` | Presente (GAP-05) | EXISTING; **ausente** de `REMEDIATION_BACKLOG.md` — debe reincorporarse |
| `R-83` | Presente (GAP-10) | EXISTING P2 abierto (`BACKLOG:275`) |
| `R-148` | Presente (GAP-13) | EXISTING P2 abierto (`BACKLOG:940`) |
| `GA-REM-003` (P0-4, P1-4) | Presente (GAP-09; GAP-03 es un cruce de tipos **no** descrito en la spec) | EXISTING abierto (`BACKLOG:21,68,90`) |
| `R-112` / `GA-REM-010` | SAP transversal | GAP-02 y GAP-14 son nuevos y no cubiertos por su alcance |
| `R-146` | **Implementada** (`operations/schemas.py:167,183`; `models.py:101`; `service.py:224-234`; `tests/test_multi_company.py::test_idempotency_key_prevents_duplicate:107`) | La fila `BACKLOG:938` sigue como hallazgo: verificar cierre documental; residuo GAP-15 |
| `R-117` | Cerrado (asignación de la plantilla global) | No cubre GAP-01 |
| `R-139` | Cerrado (atajos `is_super_admin`; Anexo A) | — |
| `R-161` | **Cerrado en código** (`validators.py:239-288`; `tests/test_egg_incubation_concurrency.py::test_r161_05/06_*`) | La fila `BACKLOG:1001` y recuentos `:1013,1045` conservan texto «OPEN» anterior a la evidencia `:1267` |
| `R-162`, `R-165`, `R-166`, `R-143` | Cerrados (`service.py:1434`; `review/service.py:110-117`, `:89-107`, `:48-67`) | — |
| `R-164` | Abierto (`masters/models.py:283` nulable; sin migración `NOT NULL`) | Tratado en la compuerta de base de datos del documento de integridad |

---

## 6. Veredicto de compuerta de seguridad: **FAIL**

Regla aplicada (§59): «Required: NO KNOWN P0/P1 SECURITY GAP. Any material cross-tenant or authority defect: NO-GO SAP.»

### 6.1 Huecos bloqueantes

| Orden | ID | Sev. | Por qué bloquea | Esfuerzo estimado de corrección |
|---|---|---|---|---|
| 1 | **GAP-01** | P1 | Escalada a autoridad global desde una empresa (autoridad); nuevo, sin test | Bajo: validación en `create_role`/`update_role` + `_rol_asignable` + test RED/GREEN |
| 2 | **GAP-09** | P1 (`P1-4`) | Registrado y abierto; sin logout/rotación/revocación | Medio: `GA-REM-003` AC04 (logout + denylist o `jti`) |
| 3 | **GAP-03** | P2 | Refresh usable como access: anula la expiración de 30 min; agrava GAP-09 | Trivial: comprobar `type == "access"` en `get_current_user` |
| 4 | **GAP-06** | P2 | Escritura foránea aceptada con privilegios ordinarios sobre estructura SAP-bound | Bajo: dos verificaciones de pertenencia + tests |
| 5 | **GAP-02** | P2 (fase SAP) | Superficie SAP fail-open para la autoridad global sin contexto, incluida escritura (`retry_failed`) | Trivial: `_company_filter` fail-closed |
| 6 | **GAP-14** | P3 (fase SAP) | Riesgo de duplicado en la consolidación SAP (§38) | Bajo: bloqueo de eventos en `consolidate_approved` + corrección del doble `Result` |
| 7 | **GAP-07**, **GAP-08** | P2 (P1 por §23) | Dato de unidad apagada en dos superficies agregadas; bloqueantes por regla del encargo hasta ratificación del propietario | Trivial: un predicado `in_` en cada uno |
| 8 | **GAP-05** | P2 → P1 condicional | Solo bloquea si se delega `masters:*` antes de corregirlo; se recomienda cerrarlo en la misma tanda que GAP-01/GAP-06 (misma clase: escritura acepta atributo de tenencia del cliente) | Bajo |

### 6.2 No bloqueantes (recomendados antes de SAP)

GAP-04 (contraseña sin contexto y sin `users:update`), GAP-10 (`R-83`), GAP-11 (rate limit tras proxy), GAP-12 (evidencias sin auditoría), GAP-13 (`R-148`), GAP-15 (oráculos), GAP-16 (validación de permisos/`skip`/código muerto), GAP-17 (documental).

### 6.3 Condiciones de re-evaluación

1. Corregir GAP-01, GAP-03, GAP-06, GAP-02 con tests RED→GREEN dirigidos (ninguno de los cuatro tiene test hoy).
2. Cerrar `GA-REM-003` AC04 (GAP-09) o, como mínimo, GAP-03 + rotación del refresh.
3. Ratificar con el propietario la clasificación de GAP-07/GAP-08 (P1 por §23 o P2 aceptado) y corregirlos en cualquier caso.
4. Actualizar los 17 tests obsoletos frente a OD-16 y las 3 guardas, y corregir el fixture `.test` (5 tests) para que la suite vuelva a 0 rojos: sin suite verde no hay evidencia de no regresión.
5. Ejecutar la suite en CI sobre `push` a `main` (o exigir PR), de modo que el estado de HEAD sea verificable por la pipeline.

---

## Anexo A — Inventario exhaustivo de atajos `is_super_admin` en `backend/app` (OD-14)

| # | Sitio | Efecto | ¿Contextual (exige empresa efectiva)? |
|---|---|---|---|
| 1 | `app/auth/security.py:107-120` | cálculo de la capacidad (`("*", all)`) | n/a (origen) — **sin mirar `Role.company_id`** (GAP-01) |
| 2 | `app/auth/security.py:145` → `tenancy.py:294-307` | honra `company_id` del token solo a la autoridad global; valida empresa activa | sí |
| 3 | `app/auth/security.py:170-178` `get_company_filter` → `None` | legado, sin consumidores | n/a — código muerto (GAP-16) |
| 4 | `app/auth/security.py:206` `tiene_permiso` | RBAC: pasa siempre | por diseño |
| 5 | `app/auth/service.py:77` `_contexto` | fail-closed sin empresa (`_acotar` `:91-96`) | sí |
| 6 | `app/auth/service.py:133,155` `_rol_asignable`/`_rol_administrable` | autoridad global asigna/edita cualquier rol | control global (`OD-14.c`) |
| 7 | **`app/auth/service.py:449` `change_password`** | restablece la contraseña de cualquier usuario de cualquier empresa sin contexto | **NO** (GAP-04) |
| 8 | `app/auth/service.py:510` `switch_company` | solo la autoridad global cambia de empresa | CORE (`OD-14.b`) |
| 9 | `app/auth/router.py:72` | proyección en `/me` | n/a |
| 10 | `app/business_units/service.py:143` | global → `unidades_habilitadas(company_id)`; sin empresa → `[]` | sí |
| 11 | `app/business_units/service.py:278-284` | global: `sin_empresa` si no situada; `no_habilitada` si apagada | sí (`OD-16.e/f`) |
| 12 | `app/lots/service.py:206` | asignación sin uso | n/a (código muerto) |
| 13 | `app/operations/service.py:1359,1368` | comparación redundante tras `get_event` | inocuo (`A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md` #8-9) |
| 14 | `app/masters/service.py:39,85` | sin filtro solo para `companies` | sí (`OD-14.c`) |
| 15 | `app/integrations/sap/service.py:76-81` (`company_id is None` → `true()`) | fail-open de lectura en 6 superficies y de escritura en `retry_failed` | **NO** (GAP-02) |

## Anexo B — Los 25 tests rojos en HEAD (evidencia `backend_full_suite.log`, 2026-09-13)

| Test | Aserción observada | Categoría |
|---|---|---|
| `test_lots_bu_enforcement.py::test_l08_put_sobre_unidad_apagada_es_403_para_la_autoridad_global` | `404 == 403` («Lot no encontrado») | OD-16 obsoleto |
| `…::test_l08_close_…` | `404 == 403` | OD-16 obsoleto |
| `…::test_l08_activate_manual_…` | `404 == 403` | OD-16 obsoleto |
| `…::test_l08_phases_…` | `404 == 403` | OD-16 obsoleto |
| `…::test_l11_frontera_de_lectura_la_autoridad_global_situada_sigue_viendo_la_unidad_apagada` | lote de unidad apagada ya no listado | OD-16 obsoleto (visibilidad) |
| `…::test_e06_control_la_autoridad_global` | `404 == 200` | OD-16 obsoleto (visibilidad) |
| `test_operations_bu_enforcement.py::test_w13_submit_…` | `404 == 403` («Evento no encontrado») | OD-16 obsoleto |
| `…::test_w13_cancel_…` | `404 == 403` | OD-16 obsoleto |
| `…::test_w13_upload_…` | `404 == 403` | OD-16 obsoleto |
| `…::test_w13_delete_…` | `404 == 403` | OD-16 obsoleto |
| `…::test_a08_control_la_autoridad_global_situada_ve_toda_la_empresa` | `{166,167,170} == {166,167,168,170}` | OD-16 obsoleto (visibilidad) |
| `…::test_a13_la_autoridad_global_no_resuelve_sobre_unidad_apagada` | `404 == 403` («Alerta no encontrada») | OD-16 obsoleto |
| `test_review_bu_enforcement.py::test_165_01_…` | `404 == 403` | OD-16 obsoleto |
| `test_state_continuity.py::test_s07_…` | `404 == 403` | OD-16 obsoleto |
| `test_internal_reversal.py::test_s03_s04_…` | `404 == 403` | OD-16 obsoleto |
| `test_od14_productive_surfaces.py::test_s02_situada_en_a_solo_ve_a_incluidas_todas_sus_unidades` | `{1210,1211} <= {1210}` | OD-16 obsoleto (visibilidad) |
| `test_review_decision_concurrency.py::test_r166_12_la_cadena_de_seguridad_se_mantiene` | `404 == 403` | OD-16 obsoleto |
| `test_r188_bu_lifecycle.py::test_r188_apagar_termina_las_concesiones_vivas` | `GET /me` `500 == 200` | fixture `.test` (TEST_DEFECT + nota de robustez) |
| `…::test_r188_reactivar_no_devuelve_la_concesion` | ídem | ídem |
| `…::test_r188_concesion_nueva_restaura_y_conserva_historia` | ídem | ídem |
| `…::test_r188_zero_bu_sin_dato_productivo` | ídem | ídem |
| `…::test_r188_transferencia_de_empresa_intacta` | ídem | ídem |
| `test_company_catalog.py::test_t10_ac20_ac21_sin_migracion_y_sin_conector` | `['y5z6a7b8c9d0'] == ['x4y5z6a7b8c9']` | guarda obsoleta |
| `test_population_invariant.py::test_ac14_sin_migracion_ni_rutas_nuevas` | ídem (`tests/test_population_invariant.py:398`) | guarda obsoleta |
| `test_time_determinism.py::test_t028_04_sin_fechas_literales_en_los_tests` | fechas `2026-09-11` en docstrings | guarda obsoleta |
