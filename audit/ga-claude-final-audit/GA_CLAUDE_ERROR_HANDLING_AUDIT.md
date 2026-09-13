# GA-CLAUDE · AUDITORÍA DE MANEJO DE ERRORES (§14, §40, §11)

**Fecha** 2026-09-13 · **Repositorio** `/home/maria/Proyectos/GlobalAvicola` · **HEAD** `c0b4afc` (`main`) · **Runtime** `https://avicola.globaldv.net` (bundle `index-DDCcWL76.js`) · **Modo** solo lectura.

## 0 · Alcance, fuentes y criterio

§14 exige, para formularios y acciones críticas, manejo seguro de 400/401/403/404/409/422 y del error inesperado: **sin crash de React, sin pantalla en blanco, sin objeto crudo como hijo, sin traza, sin JSON como mensaje, sin pérdida evitable del formulario**; los errores deben seguir siendo fallos gobernados (no se «arregla» un 422 relajando el backend). §40: el rechazo del backend deja el frontend estable, el error es comprensible, el usuario puede corregir/reintentar, sin corrupción de estado ni consola fatal. §11: el estado persistido debe coincidir con la UI tras F5/relogin.

Fuentes: `C_response_error_state.md` (Audit 2 y 3, **C#n**), `B_form_contracts.md` (**B-15**), `A_fe_be_trace.md` (A §3.27 «errores tragados»), `F_i18n_nav_responsive.md` (G-11), registro canónico `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md`; evidencia **[RT]** `evidence/runtime-gp-e2e.json` (+PNG), **[L1]** `evidence/ui-e2e-local-pass1.json` (+PNG), **[L2]** `evidence/ui-e2e-local-pass2.json` (en generación al redactar; pasos en `ui_e2e_local_pass2.log`). Citas de carga verificadas sobre HEAD.

---

## 1 · Infraestructura

| Pieza | Comportamiento verificado | Evidencia | Valoración |
|---|---|---|---|
| Interceptor de petición | Adjunta `Bearer` desde memoria | `frontend/src/services/api.ts:52-58` | ✔ |
| Interceptor 401 | Un intento de refresh por petición (`_retry`), `axios.post('/api/v1/refresh')` fuera de la instancia, promesa compartida; si falla o ya se reintentó → `forceLogout()` → `auth.store.logout` → `ProtectedRoute` → `/login` | `api.ts:26-49,61-79`; `auth.store.ts:133-139`; `App.tsx:51` | Refresh implementado ✔. Cierre **silencioso**: sin toast ni «sesión expirada»; formulario abierto perdido (C#21). No hay 401 de negocio hoy (`auth/service.py:446-463` usa 400/403/404) |
| 403 / 404 / 409 / 422 / 5xx / red | **Sin manejo central**; cada pantalla decide | `api.ts` | Ver §2 y §3 |
| `getErrorMessage` | Normaliza `detail` string/lista/objeto a texto renderizable (R-189 F-01); fallback `err.message` de axios («Request failed with status code 403», inglés técnico) o el `fallback` | `components/Toast.tsx:95-140` | Correcto donde se usa: `OperationFormPage.tsx:456-461`, `OperationDetailPage.tsx:67-71,138`, `LoginPage.tsx:40-44`, `DashboardPage.tsx:101-104`, `SapComparisonPage.tsx:14`, revisión/aprobaciones/SAP |
| `Toast` | `fixed top-4 right-4 max-w-sm`; renderiza `{t.message}` tal cual | `Toast.tsx:67,74` | Si un consumidor pasa `detail` no normalizado (lista), el propio `ToastProvider` reproduce React #31 (`LotFormPage.tsx:137`) |
| `ErrorBoundary` | **No existe** (`grep -rn 'ErrorBoundary\|componentDidCatch' frontend/src` = 0; `main.tsx`, `App.tsx`) | — | Cualquier excepción de render deja la aplicación **en blanco sin recuperación** ([L1] `H04-masters-house-create.png`) |
| Backend 400 de negocio | `BusinessRuleViolation → {detail: str, rule: id}`; `Exception` genérica **no** se captura (500 deliberado) | `backend/app/main.py:80-98` | `rule` nunca se lee en UI (C#28) |
| Backend 403 | `HTTPException(403, "Permiso requerido: {modulo}:{accion}")` (20 usos de 403 en `backend/app`) | `auth/security.py:223-228` | Texto en español fijo (G-11) |
| Backend 404 / 409 / 422 | 37 usos de 404, 8 de 409 (p. ej. `lot_code` duplicado `lots/service.py:311-318`, candidatos con unidad apagada, reclasificación con efectos); 422 = lista Pydantic `[{type, loc, msg, input}]` | grep `status_code=` | Los 422 son la fuente de React #31 fuera del asistente |
| Diálogos nativos | `alert()` ×9, `confirm()` ×2, `prompt()` ×2, `window.location.reload()` ×1 | `UsersPage.tsx:71,82,85,88,91`; `RolesPage.tsx:85,92,97`; `ReviewDetail.tsx:69,74`; `CorrectionForm.tsx:49`; `ReviewCenter.tsx:123,143`; `DashboardPage.tsx:136` | `JSON.stringify` mostrado al usuario: ninguno ✔; `alert(detail)` coacciona listas a «[object Object]» (`UsersPage.tsx:85`) |

---

## 2 · Mapa por código de estado → render por pantalla

| Código | Origen backend | Render seguro (dónde) | Render inseguro / silencioso (dónde) | Evidencia runtime |
|---|---|---|---|---|
| **400** (regla de negocio) | `main.py:88-98` `{detail, rule}` | Asistente: banner + toast, formulario intacto (`OFP:456-461`; `R05-error-ux.png`); detalle de operación (toast + relectura); revisión/aprobaciones (toast); `LotFormPage`/`MasterListPage` cuando `detail` es cadena | **Cierre de lote**: `console.error` únicamente, modal ya cerrado (`LotDetailPage.tsx:107-119`) → sin ningún mensaje (`D01-bo-close-unapproved.png`, [L1] `BO-close-sin-aprobar {toasts:[]}`); **borrado de maestro**: `console.error` con el modal abierto (`MasterListPage.tsx:114`) | [RT] 5 × `POST /operations` 400 (BR-08 ×4, BR-01 ×1) todos con banner y `pageerrorDelta: 0`; [L1] `MOB-mortality 400` mensaje claro en móvil; [L2] `BR2-BR02-4xx-seguro` ✔ |
| **401** | Token vencido/ inválido | — | Interceptor: refresh → `forceLogout` **sin aviso**; `UsersPage` trata 401 como «prohibido» (`:37-63`) | No observado en runtime (sesiones válidas). Análisis por código (C#21) |
| **403** | `security.py:225-228`; OD-16 fail-closed (404 en lecturas de unidad apagada) | `DashboardPage` banner + «Reintentar» (`:130-143`); `UsersPage` estado `prohibido` con texto propio (`:37-63`); `UnitAccessPage` banner + reintento (`:57-60,198-205`); `CapabilityRoute`/`PermissionRoute` mensaje antes de pedir | **Denegación ≡ vacío** (C#19): `LotListPage.tsx:32-33` («No hay lotes»), `OperationListPage.tsx:42` (`setEvents([])`), `AuditPage.tsx:74` (`.catch(() => {})`), `ReportsPage.tsx:17,33`, `SapManagerPage.tsx:39-42`, `RolesPage.tsx:42-43`, `ReviewDetail.tsx:55-56` («Evento no encontrado»), `CorrectionForm.tsx:38-39`, `MasterListPage.tsx:59-61`; `LotDetailPage.tsx:66-67,86` («Lote no encontrado»); **carga eterna** (C#20): `LotReportPage.tsx:64`, `SapComparisonPage.tsx:17` («Cargando…» tras toast); sub-cargas `allSettled` mudas (`LotDetailPage.tsx:44-73`) | [RT] operador: `GET /reports/kpis?lot_id=66`, `/reports/kpi/ipe/66`, `/reports/kpi/weight-uniformity/66` **403 ×12 cada uno** sin ningún indicio en pantalla; `GET /dashboard/admin` 403 (op, ap) → pantalla de error como home; aprobador: `GET /users?limit=100` **403 ×7** silenciados (`ReviewCenter.tsx:110`); [L1] móvil: `/sap/references` 403 ×4 silenciados en el asistente (`OFP:352-353`); `POST /approvals/approve` 403 ×1 → toast (`R-11-aprobado`) |
| **404** | `HTTPException(404)` (37 usos) + OD-16 | `OperationDetailPage` (`setError` + toast, `:67-71`); `NotificationBell` (error explícito) | `LotDetailPage` «Lote no encontrado» (correcto para 404, pero idéntico para 403/500); `ReviewDetail` «Evento no encontrado» vía `console.error` | No provocado en runtime |
| **409** | `lot_code` duplicado; unidad apagada; reclasificación | `LotFormPage` (toast con cadena); `TraceabilityTree` (cadena) | `UnitAccessPage.tsx:124,138,153` / `UserBusinessUnitsButton.tsx:85,99`: `detail` descartado por mensaje genérico («Error al guardar») (C#30) | No provocado en runtime |
| **422** (Pydantic) | Lista `[{type, loc, msg, input}]` | Asistente (`textoDeDetalle` → «campo: msg», `Toast.tsx:97-133`; [L2] banner `egg_storage_records.0.arrival_date: Field required`); revisión/aprobaciones (observaciones <10); `WeightCurvesPage` (por fila + `mensajeGeneral` tipado, `:23-34,119-122`) | **React #31**: `MasterListPage.tsx:99,201-205` (`<p>{formError}</p>`), `LotFormPage.tsx:137` (`toast.error(detail)`), `TraceabilityTree.tsx:95,114,347,389`, `ProfilePage.tsx:38,70`; **`[object Object]`**: `UsersPage.tsx:85` (`alert(detail)`); **silencio total**: transición de fase (`LotDetailPage.tsx:134`) | [L1] `pageerror ×2` «Objects are not valid as a React child (found: object with keys {type, loc, msg, input})» en `POST /masters/hatcheries` y `/masters/houses` (`H04-masters-house-create.png` = pantalla en blanco); [RT] `R-09-transicion-ui: 422` con `toasts: []` (`R03-transition.png`) |
| **500 / red** | No capturados por diseño (`main.py:80-84`); `/me` 500 real por `EmailStr` (R-213, `me500_probe.log`) | `OperationDetailPage`, `DashboardPage`, `UnitAccessPage` (estado `error` + reintento) | `auth.store.fetchMe` traga (`:160-163`) → sesión sin permisos → «No tiene permiso» en toda sección (C#21, C#37); `Header.tsx:37-40` + `company.store.ts:57-60`: `switchCompany` relanza y el `Header` no captura → **unhandled rejection** sin feedback; `LotReportPage.tsx:44-62` exportación sin `catch`; el resto de pantallas de C#19 muestran «vacío» | [RT] `http5xx: []`; [L1] `http5xx: []` — ningún 5xx observado en los recorridos |

---

## 3 · Por pantalla (carga · mutación · `detail` crudo · estado del formulario · nativos)

| Pantalla | Carga (`catch`) | Mutaciones (`catch`) | `detail` crudo en JSX/toast | Formulario tras 4xx | Nativos / recarga | Veredicto |
|---|---|---|---|---|---|---|
| LoginPage | — | `getErrorMessage` + banner + toast (`:40-44`) | no | preservado ✔ | no | PASS (C#37 menor) |
| DashboardPage | banner + reintento por `reload()` (`:100-105,130-143`) | resolver alerta: toast ✔ | no | — | `window.location.reload()` | PARTIAL (home = error para roles sin `dashboard:read`, R-212) |
| LotListPage | `console.error` (`:32-33`) | — | — | — | no | FAIL (denegación ≡ vacío, C#19) |
| LotDetailPage | `console.error` (`:66-67`) → «Lote no encontrado»; `allSettled` mudo (`:44-73`) | cerrar (`:114-116`) y transición (`:133-135`): **solo `console.error`**; resolver alerta: toast ✔ | no | modal cerrado antes del POST (`:108,122`) | no | **FAIL** (R-191, R-192 C#8) |
| LotFormPage | `allSettled` mudo (selects vacíos) | `toast.error(detail)` (`:137`) | **sí** (React #31 en 422) | preservado ✔ | no | **FAIL** (R-215) |
| OperationFormPage | lotes: aviso (`:2088`) ✔; catálogos `allSettled` mudos (SAP 403 silenciados) | `getErrorMessage` + banner + toast (`:456-461`) ✔ | no | preservado ✔ | no | PASS (referencia R-189; `R05-error-ux.png`) |
| OperationListPage | `catch { setEvents([]) }` (`:42`) | — | — | — | no | FAIL (C#19) |
| MyPendingPage | mensaje genérico (`:37-38`) | — | no | — | no | PARTIAL |
| OperationDetailPage | `getErrorMessage` + estado `error` + toast (`:63-72`) ✔ | enviar/evidencias: toast ✔; relectura tras éxito **y** fallo (`:139-144`) ✔ | no | — | no | PASS (estado de evidencias tras F5: R-198) |
| ReviewCenter | toast (`:99-101`) + lista vacía «Sin resultados» | toast `getErrorMessage` ✔ | no | — | `prompt()` (`:123,143`) | PARTIAL (C#31; 403 de `/users` silenciado) |
| ReviewDetail | `console.error` (`:55-56`) → «Evento no encontrado» | toast ✔; `navigate('/review')` | no | — | `alert()` (`:69,74`) | PARTIAL |
| CorrectionForm | `console.error` (`:38-39`) | toast ✔ | no | preservado ✔ | `alert()` (`:49`) | PARTIAL |
| ApprovalPanel | toast (`:43-44`) | toast ✔ | no | — | no | PASS (sin guarda de doble clic, C#35) |
| AuditPage | `.catch(() => {})` (`:74`) | — | — | — | no | FAIL (C#19) |
| ReportsPage | `.catch(() => {})` (`:17,33`); export `console.error` (`:61`) | — | — | — | no | FAIL (C#18/C#19) |
| LotReportPage / SapComparisonPage | toast pero «Cargando…» eterno (`LotReportPage.tsx:64`, `SapComparisonPage.tsx:17`) | export sin `catch` (`LotReportPage.tsx:44-62`) | no | — | no | FAIL (C#20) |
| SapManagerPage | cada `catch` devuelve vacío (`:39-42`) | toast ✔ | no | — | no | FAIL (C#19; sin refetch C#22) |
| MasterListPage | `console.error` (`:59-61`) | guardar: `setFormError(detail)` **crudo** (`:99`); borrar: `console.error` (`:114`), modal abierto sin mensaje | **sí** (422 lista → React #31) | modal preservado ✔ | no | **FAIL** (R-215, R-196) |
| WeightCurvesPage | banner (`:69-70`) | filas rechazadas + mensaje seguro (`:24-34,119-122`) ✔ | no (`mensajeGeneral` comprueba tipo) | preservado ✔ | no | PASS (referencia) |
| UsersPage | estados `prohibido/error/ok` + reintento (`:37-63`) ✔ | `alert(detail || …)` (`:85`); `alert(t(...))` (`:88,91`) | `alert` → «[object Object]» si lista | modal preservado ✔ | `alert/confirm` ×5 | PARTIAL (carga ejemplar; R-195 en mutación) |
| RolesPage | `console.error` (`:42-43`) → «Sin roles» | `alert(t('common.error'))` (`:85,97`) | no | modal preservado ✔ | `alert/confirm` ×3 | PARTIAL (C#19, C#30) |
| ProfilePage | — | `setMessage(detail || …)` (`:38`) | **sí** (React #31 en 422 estructurado) | preservado ✔ | no | FAIL latente (R-215) |
| UnitAccessPage / UserBusinessUnitsButton | banner + reintento (`:57-60,198-205`) ✔ | toast genérico; `detail` descartado (`:124,138,153`; `Button:85,99`) | no | — | no | PARTIAL (C#30) |
| NotificationBell | error explícito ≠ bandeja vacía (`:78-82,151-153`) ✔ | marcar leída: error (`:93-96`) ✔ | no | — | no | PASS |
| TraceabilityTree | error + reintento (`:151-157`) ✔ | `setLinkError(detail)` **crudo** (`:95,114`) | **sí** (React #31 en 422) | modal preservado ✔ | no | FAIL (R-215) |
| Header / company.store | `fetchCompanies` traga (`company.store.ts:42-44`) → desplegable «Cargando…» eterno (`Header.tsx:106-107`) | `handleSwitchCompany` sin `catch` (`Header.tsx:37-40`) y `switchCompany` relanza (`company.store.ts:57-60`) → **unhandled rejection** | no | — | no | FAIL (C#20) |
| auth.store.fetchMe | traga (`:160-163`) → sesión degradada sin `permissions` | — | — | — | — | FAIL (C#21) |

---

## 4 · Fallos silenciosos (`console.error` / `catch` vacío únicamente)

| # | Acción / carga | Evidencia | Id |
|---|---|---|---|
| 1 | Cierre de lote (400 BR-05/BR pesaje, etc.) | `LotDetailPage.tsx:114-116`; [L1] `BO-close-*` 400 sin toast; `D01-bo-close-unapproved.png` | **R-192** (AC04), C#8 |
| 2 | Transición de fase (422 siempre) | `LotDetailPage.tsx:133-135`; [RT] `toasts: []`; `R03-transition.png` | **R-191** |
| 3 | Borrado de maestro | `MasterListPage.tsx:114` (modal abierto) | R-196 / R-220 |
| 4 | Cambio de empresa (super admin) | `Header.tsx:37-40`, `company.store.ts:57-60` | R-220 (C#20) |
| 5 | Exportación del informe de lote | `LotReportPage.tsx:44-62` (sin `catch`) | R-220 |
| 6 | Cargas: lotes, operaciones, auditoría, reportes, SAP, roles, detalle de revisión, corrección, maestros | `LotListPage.tsx:33`, `OperationListPage.tsx:42`, `AuditPage.tsx:74`, `ReportsPage.tsx:17,33`, `SapManagerPage.tsx:39-42`, `RolesPage.tsx:43`, `ReviewDetail.tsx:56`, `CorrectionForm.tsx:39`, `MasterListPage.tsx:60` | R-212 (C#19) |
| 7 | Sub-cargas del detalle de lote (KPIs/fases/alertas) y catálogos del asistente/alta de lote (`allSettled`) | `LotDetailPage.tsx:44-73`; `OFP:342-379`; `LotFormPage.tsx:82-109`; [RT] 403 ×36 sin indicio | R-212 |
| 8 | Filtro de operador en revisión (`/users` 403) | `ReviewCenter.tsx:107-110`; [RT] 403 ×7 | R-212 / R-197 |
| 9 | `/me` fallido tras login | `auth.store.ts:160-163`; `LoginPage.tsx:37-39` («Bienvenido») | R-212 (C#21), R-213 |
| 10 | Referencias SAP en el asistente (router SAP apagado o sin permiso) | `OFP:352-353`; [L1] móvil 403 ×4 | R-212 |

## 5 · Denegación mostrada como vacío / «no encontrado» (C#19) y carga infinita (C#20)

- **Denegación ≡ vacío / no encontrado (9 pantallas)**: LotListPage, OperationListPage, AuditPage, ReportsPage, SapManagerPage, RolesPage, ReviewDetail, CorrectionForm, MasterListPage; más `LotDetailPage` («Lote no encontrado» para 403/404/500) y `MyPendingPage` (genérico). Contraste correcto: `UsersPage.tsx:37-63` (403/401 → `prohibido`; otro → `error` con reintento), `UnitAccessPage`, `NotificationBell`, `DashboardPage`. → **R-212** (P3 en el registro; §14 lo eleva a ERROR_HANDLING_GAP material en las pantallas de proceso: lista de lotes/operaciones).
- **Carga infinita (2 + 1)**: `LotReportPage.tsx:64`, `SapComparisonPage.tsx:17` («Cargando…» tras el toast, sin estado de error ni reintento); `Header.tsx:106-107` (desplegable de empresas). → R-212 / R-220 (C#20).
- **Guardas de ruta**: `CapabilityRoute`/`PermissionRoute` muestran «No tiene permiso…» antes de pedir ([L1] `GUARD-approver-operations-new`, `GUARD-approver-unit-access`) ✔; pero `HomeRoute` y `/my-pending`/`/profile`/`/kpi` no tienen guarda (`App.tsx:110-114,216,262,282`), de ahí el 403 en el home.

## 6 · Sitios de React #31 (B-15 / C#6) y ausencia de `ErrorBoundary` (C#7)

| Sitio | Código | Disparador | Estado |
|---|---|---|---|
| `MasterListPage.tsx:99,201-205` | `setFormError(err.response.data.detail)` → `<p>{formError}</p>` | Cualquier 422 (alta de `farms/houses/hatcheries/incubators/hatchers`, `capacity:''`, `order:''`) | **Reproducido** [L1]: `pageerror ×2`, `fatal_react: 2`, `H04-masters-house-create.png` en blanco |
| `LotFormPage.tsx:137` | `toast.error(detail)` → `ToastProvider` renderiza lista | 422 en alta de lote (p. ej. `lot_code` >100, fecha inválida) | Por código (no reproducido) |
| `TraceabilityTree.tsx:95,114` → `:347,389` | `setLinkError(detail)` | «Vincular» con `hatchery_lot_id` vacío (`Number('')||null` vs `int`) | Por código |
| `ProfilePage.tsx:38,70` | `setMessage(detail)` | 422 estructurado en cambio de contraseña (`extra=forbid` u otros) | Por código (cliente valida ≥8, `:23`) |
| `UsersPage.tsx:85` | `alert(detail)` | 422 en edición (`username`/`company_id` prohibidos) → «[object Object]» | Sin crash, mensaje ilegible (R-195) |
| Global | Sin `ErrorBoundary` (`main.tsx`, `App.tsx`) | Cualquier excepción de render | Pantalla en blanco sin botón de recuperación |
→ **R-215** (P2, bloqueante en el registro). Nota §14: el helper `getErrorMessage` ya existe (`Toast.tsx:95-140`); la corrección es de consumo, no de backend.

## 7 · Comportamiento tras F5 / relogin (C#21, C §3.1)

| Aspecto | Comportamiento | Evidencia | Veredicto |
|---|---|---|---|
| Sesión | Tokens en `sessionStorage` (web) / `localStorage` (Telegram); `isLoading: !!token` fuerza `fetchMe` antes de las guardas | `auth.store.ts:60-69,100`; `App.tsx:177-181` | F5 conserva la sesión en la misma pestaña ✔; pestaña nueva → login (diseño) |
| Empresa activa | No se persiste; se deriva de `/me` en cada arranque | `auth.store.ts:146-159` | ✔ (OD-11) |
| Preferencias | `theme`, `i18n`, `useSidebar`, pila del hub (`sessionStorage`), `operationBackTarget` | `main.tsx:18-23`; `MenuHubPage.tsx:65-68`; `ProcessStagePage.tsx:48` | Solo UI ✔ |
| Datos cacheados | Ninguno (lotes/operaciones se releen) | grep stores | ✔ |
| Refresh vencido (7 d) / `/refresh` 401 a mitad de formulario | Salto a `/login` sin aviso; formulario perdido; sin `returnTo` | `api.ts:64-78`; `App.tsx:51`; G-26 | **FAIL** §14 «no lost form state where avoidable» (C#21) |
| `/me` 500 (R-213) | Sesión degradada: todas las `CapabilityRoute` → «No tiene permiso» sin explicar | `auth.store.ts:160-163` | FAIL |
| Evidencias tras F5 | Lista vacía aunque persistidas (`router.py:282-292` `pop("evidences")`; `OperationDetailPage.tsx:66`) | C#1 | **FAIL** §11 → **R-198** |
| SAP tras consolidar/exportar | Sin refetch hasta F5 (`SapManagerPage.tsx:51-67`) | C#22 | FAIL (R-217) |
| Mutaciones con relectura | enviar/reenviar (`loadEvent`), revisión/aprobación (`fetchEvents`), corrección, alta de lote (navega al detalle con GET), maestros (`fetchItems`), curvas, usuarios/roles (`fetchData`), unidades (tras éxito y fallo), vincular (`load()`) | C §3 | ✔ ([RT] estados releídos por GET en `R-05/R-06/R-11`) |
| Relogin explícito | No ejercitado | — | UNKNOWN (por diseño de almacenamiento no debería divergir) |

## 8 · Resumen de la evidencia runtime

| Métrica | [RT] runtime real | [L1] local pasa 1 | [L2] local pasa 2 (parcial) |
|---|---|---|---|
| `pageerror` (React fatal) | **0** | **2** (React #31, maestros) | pendiente de cierre |
| Respuestas 5xx | **0** | **0** | 0 en el log |
| 4xx totales | 52 (36 × 403 KPI operador · 7 × 403 `/users` aprobador · 2 × 403 `/dashboard/admin` · 5 × 400 `POST /operations` · 1 × 422 `/lots/66/phases` · 1 × 403 `/approvals/approve`) | 12 (2 × 403 home aprobador · 4 × 403 SAP móvil · 2 × 400 `/lots/1/close` · 2 × 422 maestros · 2 × 400 operaciones) | 400 BR-20/BR-08/BR-22/BR-02/BR-03 y 422 `arrival_date`/fase, todos con banner (asistente) o silencio (transición) |
| `consoleError` | 1 (`[Object, Object]`, actor op) | 4 (2 cierres de lote silenciosos + 2 avisos de anidamiento `<button>` en `<button>`) | — |

Todos los 400 del asistente dejaron `formVisible: true` y `pageerrorDelta: 0` ([RT] `posts[]`).

## 9 · Cumplimiento de los requisitos §14

| Requisito | Veredicto | Evidencia |
|---|---|---|
| Sin crash de React | **FAIL** | [L1] `fatal_react: 2` (maestros); mismo patrón en lotes, trazabilidad, perfil |
| Sin pantalla en blanco | **FAIL** | `H04-masters-house-create.png`; sin `ErrorBoundary` |
| Sin objeto crudo como hijo | **FAIL** (fuera del asistente) | §6 |
| Sin traza de pila | PASS | Ningún `stack`/traceback renderizado; 500 no observados |
| Sin JSON como mensaje | PASS (con salvedad) | `JSON.stringify` en UI: 0; `alert('[object Object]')` en usuarios es coacción, no JSON |
| Sin pérdida evitable del formulario | PARTIAL | Formularios preservados tras 4xx ✔ (`R05-error-ux.png`); perdidos en logout forzado por 401 (C#21) |
| Errores comprensibles | PARTIAL | Asistente ✔; cierre/transición mudos; `detail` en español para EN (G-11); `rule` no mostrado (C#28); 422 Pydantic en inglés dentro de toasts ES |
| Fallos gobernados (backend no relajado) | PASS | R-189 F-01d endureció (422 estricto) en lugar de relajar; ningún 422 «resuelto» en backend en esta cadena |
| §40: estable / comprensible / reintentable / sin corrupción / sin fatal | PARTIAL | Asistente cumple los 5; transición y cierre incumplen «comprensible» y «reintentable con información»; maestros incumplen «sin fatal» |

**Veredicto global de manejo de errores: FAIL.**

## 10 · Lista bloqueante y no bloqueante

| Id | Clase | Alcance | Bloquea (registro) |
|---|---|---|---|
| **R-215** | ERROR_HANDLING (React #31 fuera del asistente + sin `ErrorBoundary`) | `MasterListPage`, `LotFormPage`, `TraceabilityTree`, `ProfilePage`, `UsersPage` | **SÍ** |
| **R-191** | ERROR_HANDLING + contrato (422 silencioso en transición) | `LotDetailPage.tsx:121-138` | **SÍ** (P1) |
| **R-192** (AC04) | ERROR_HANDLING (400 de cierre invisible) | `LotDetailPage.tsx:107-119` | **SÍ** (P1) |
| **R-195** | ERROR_HANDLING (`alert('[object Object]')`) + contrato | `UsersPage.tsx:85` | **SÍ** (P1) |
| **R-197** | STATE_FEEDBACK (evento «desaparece» tras iniciar; 403 `/users` silenciado) | `ReviewCenter` | **SÍ** (P2) |
| **R-198** | STATE_REFRESH (§11: evidencias no persisten en la UI tras F5) | `OperationDetailPage.tsx:66`; `operations/router.py:282-292` | **SÍ** (P2) |
| R-212 | ERROR_HANDLING (denegación ≡ vacío ×9, carga eterna ×2, sesión degradada muda, home 403) | transversal | NO (P3) — recomendación: reclasificar a material para `LotListPage`/`OperationListPage` (pantallas de proceso) |
| R-213 | `/me` 500 por `EmailStr` → sesión muda | `auth/service.py:329` | NO (P3) |
| R-217 | STATE_REFRESH (SAP sin refetch) | `SapManagerPage.tsx:51-67` | NO ahora / SÍ fase SAP |
| R-220 | nativos (`alert/confirm/prompt` ×13, `reload()`), `detail` descartado (C#30), `rule` no leído (C#28), `switchCompany` sin `catch`, export sin `catch`, doble clic (C#35), «Bienvenido» con `/me` caído (C#37) | transversal | NO |

## 11 · UNKNOWN
- 401 real (token vencido) a mitad de formulario: no provocado; comportamiento derivado de `api.ts:61-79`.
- 404/409/500 de negocio por UI: no provocados en los recorridos; render deducido del código de cada `catch`.
- Reproducción runtime de React #31 en `LotFormPage`/`TraceabilityTree`/`ProfilePage` (solo `MasterListPage` fue ejercitado).
- Relogin explícito (logout → login) no ejercitado.
