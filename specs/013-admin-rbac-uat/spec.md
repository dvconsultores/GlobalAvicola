# SPEC 013 — UAT Administración, Identidad, Roles, Unidades de Negocio y RBAC (GA-UAT-ADMIN-RBAC-2026-10-31)

**Estado:** DRAFT→IMPL · **Fecha:** 2026-10-31 · **Baseline HEAD:** `4aa0775` · **Rama:** `main`.
Amendment de **GA-REM-002** (RBAC backend), **GA-REM-003** (identidad/ciclo de token), **GA-REM-012** (cambio de contraseña), **GA-REM-032/034** (auditoría y administración de roles), **OD-05** (escalada), **OD-13/OD-15** (propiedad de roles / segregación del acceso) y **GA-FE-02** (administración en el frontend). No reabre nada certificado sin regresión demostrada (§27): las suites vigentes de tenant isolation, R-199, R-200, R-202 y OD-15 se **reutilizan** y se mantienen verdes.

Entradas: `SESION 1 – REVISION CONFIGURACION – USUARIOS – ROLES – 30-10-2026.pdf` (Yolinel); sondas observacionales en HEAD (`audit/ga-uat-admin-rbac-2026-10-31/evidence/01a|b|c_*`); tabla `audit/ga-uat-admin-rbac-2026-10-31/00_FINDINGS_TABLE.md` (AR-01…AR-20).

## 0. Decisiones del Owner (2026-10-31) — vinculantes para esta spec
| ID | Decisión adoptada |
|---|---|
| **DR-1** (AR-01/20) | **Bloquear la baja de un rol con usuarios activos asignados** (`409`). Un rol inactivo **nunca** confiere permisos (defensa en profundidad) ni es asignable, y es **reactivable** desde la UI. Sustituye GA-REM-034 AC09 únicamente para el caso «con usuarios asignados». |
| **DR-2** (AR-18) | Un rol exige **≥1 permiso** al **crear y al editar** (`422`), en API y UI. |
| **DR-3** (AR-02/08) | **Regla de subconjunto**: nadie asigna un rol ni concede permisos que él mismo no posea (la autoridad global queda exenta), y **nadie cambia su propio rol ni se desactiva a sí mismo** (tampoco la autoridad global). Resuelve `OD-05` para administración de acceso. |
| **DR-4** (AR-11) | **Se mantiene** el contrato vigente (GA-REM-012 AC08): cambiar la contraseña no revoca tokens previos. Se evidencia con test y se documenta como observación P2 no bloqueante (`OD-01` sigue abierta). |

## 1. Hallazgos y acciones (ver tabla completa en `00_FINDINGS_TABLE.md`)

| AC / Hallazgo | Capa | Cambio |
|---|---|---|
| **AC-ID-01** AR-03 | backend | `POST /users` con `username` de un usuario y `email` de otro ⇒ `409` accionable (nunca excepción/500). Duplicado de username ⇒ `409 «El nombre de usuario ya está en uso»`; de email ⇒ `409 «El correo electrónico ya está en uso»`. |
| **AC-ID-02** AR-04 | backend | `PUT /users/{id}` con un email ya usado por otro usuario ⇒ `409`; ante carrera, `IntegrityError` ⇒ `409` (nunca 500). |
| **AC-ID-03** AR-05 | backend | `username`/`email` se normalizan con `strip()`; la unicidad se evalúa **insensible a mayúsculas** (`lower()`), sin migración. Un valor con espacios no se persiste con espacios. El login sigue exacto (sin cambio). |
| **AC-ID-04** AR-06 | backend | Nombre de rol único por empresa, insensible a mayúsculas y espacios; un rol de empresa tampoco puede repetir el nombre de una plantilla de sistema visible; incluye roles inactivos; `409 «Ya existe un rol con ese nombre»`. Aplica a alta y a renombrado. |
| **AC-ID-05** AR-07 | backend | `PUT /users/{id}` con `is_active=false` exige además `users:delete` (`403` si falta); reactivar sigue siendo `users:update`. |
| **AC-ID-06** AR-10 | backend | Cambio de contraseña (propio o restablecimiento) con la nueva igual a la vigente ⇒ `422`. |
| **AC-RL-01** AR-01 (DR-1) | backend | `PUT /roles/{id}` con `is_active=false` y ≥1 usuario **activo** asignado ⇒ `409` con el número de usuarios; sin usuarios activos ⇒ `200`. |
| **AC-RL-02** AR-01/01b | backend | Un rol inactivo no confiere permisos: `get_current_user` lo trata como **sin permisos** y sin autoridad global; `_es_super_admin` exige rol activo. |
| **AC-RL-03** AR-01b | backend | Asignar un rol **inactivo** (alta o cambio de `role_id`) ⇒ `409`. Re-guardar el mismo `role_id` ya asignado no se re-valida. |
| **AC-RL-04** AR-20 | backend/UI | `GET /roles?include_inactive=true` devuelve también los inactivos (mismo alcance de empresa); `PUT is_active=true` los reactiva. UI: filtro «Mostrar inactivos» y acción «Reactivar» (`users:update`). |
| **AC-RL-05** AR-18 (DR-2) | backend/UI | `POST /roles` y `PUT /roles` con `permissions` vacío ⇒ `422 «El rol debe tener al menos un permiso»`; la UI lo impide y lo explica. |
| **AC-RL-06** AR-09 | backend | Auditoría de edición de rol con `previous_values`/`new_values` de `nombre`, `descripcion`, `activo` y conjunto de `permisos` (añadidos/retirados). Nunca secretos. |
| **AC-ES-01** AR-02 (DR-3) | backend | Subconjunto en **asignación de rol** (alta y cambio): todos los `(módulo, acción)` del rol destino deben estar en poder del actor (`tiene_permiso`; el comodín exige comodín); si no ⇒ `403` + asiento de rechazo. Autoridad global exenta. |
| **AC-ES-02** AR-02 (DR-3) | backend | Subconjunto en **alta/edición de rol**: los permisos **añadidos** (nuevo conjunto − conjunto actual) deben estar en poder del actor; retirar siempre es posible. Autoridad global exenta. |
| **AC-ES-03** AR-02/08 (DR-3) | backend | `403` si el actor cambia su **propio** `role_id` o se desactiva (`PUT is_active=false` o `DELETE`) a sí mismo — incluida la autoridad global. |
| **AC-SS-01** AR-19 | frontend | Tras un refresh automático el store **conserva** `permissions`, `effective_business_units`, `is_super_admin`, nombre y correo y se **rehidrata desde `/me`**. |
| **AC-SS-02** AR-21 | frontend | Una respuesta `403` dispara una rehidratación acotada de `/me` (máx. 1 cada 30 s, nunca desde `/me` ni durante login) para que menús y acciones converjan con el backend sin recargar. |
| **AC-UI-01** AR-13 (Y-1.2) | frontend | `ConfirmDialog` se monta en portal sobre cualquier `Modal` (`z` superior): «Revocar» desde Usuarios revoca. |
| **AC-UI-02** AR-14 (Y-3.2) | frontend | El panel de unidades resuelve por unidad la concesión **viva**; si no hay, la revocada más reciente. Tras re-conceder muestra «Concedida» y «Efectiva». |
| **AC-UI-03** AR-15 (Y-1.1) | frontend | El panel muestra **Empresa** y **Usuario** (nombre + login); las cabeceras pasan a «Estado en la empresa» / «Estado del usuario». |
| **AC-UI-04** AR-16 (Y-3.1) | frontend | La confirmación de revocar nombra **usuario y unidad** (panel de Usuarios y página «Acceso por unidad»). |
| **AC-UI-05** AR-17 (Y-1.3) | frontend | La acción papelera de Usuarios se rotula **«Desactivar usuario»** (título, confirmación, `aria-label`) y explica que es reversible; se oculta/deshabilita sobre la propia fila (el backend decide). Permiso `users:delete` sin cambio. |
| **AC-UI-06** AR-20 | frontend | `RolesPage`: «Desactivar» gateado por `users:update` (coincide con el backend), `ConfirmDialog` y toasts en lugar de `confirm()/alert()`; el `409` por usuarios asignados se muestra legible. |
| **AC-UI-07** AR-22 | frontend | El listado de Usuarios pide `limit=100` y ofrece búsqueda (nombre/login/correo) sobre lo cargado; ya no queda truncado a 20. Observación: sin paginación completa por encima de 100. |
| **AC-UI-08** AR-23 | frontend | `HomeRoute` sin `dashboard:read` redirige a `/menu/poultry` **solo si ese hub existe** para la sesión (`filterNavItemsBySession`); si no, muestra un aviso neutro (`role="status"`, `home.noLanding`) y **no redirige** (sin bucle `/` ⇄ `/menu/poultry`). `AC-R212-02` se ajusta (sesión con unidad efectiva) porque su montaje con hub-stub ocultaba el bucle. Prueba: `uatAdminRbac.homeNoLoop.test.tsx` + E2E P-17-E/F estables. |
| **AC-UI-API-01** | E2E | Consistencia UI↔API para `test_admin/operator/approver` en 5 rutas (`/audit,/users,/roles,/lots,/cutover`): la UI abre la ruta ⇔ la API responde 200; si no, 403 exacto y la UI no consume el endpoint (P-17-G, `e2e_ui_api_consistency.json`). |
| **AC-PF-01** | frontend | `ProfilePage`: pruebas de campos obligatorios, desigualdad, longitud ≥8, éxito, error del servidor. Sin cambio funcional. |

**Pruebas de política sin cambio de comportamiento:** `AC-POL-01` R-123 (`scope_type/scope_id` no se evalúan) y `AC-POL-02` DR-4 (access/refresh previos siguen vivos tras cambiar la clave) quedan **fijados por test** para que ninguna regresión silenciosa los altere.

## 2. Matriz de autorización ejecutada (UAT-AUTH-05/06) — pruebas sin cambio de código de aplicación
- **AC-MX-01** Matriz generada por introspección de rutas: para **cada** ruta con `require_permission(m, a)` y para cada rol del producto (6 + Administrador de Accesos + rol vacío + rol con una sola acción), el resultado HTTP coincide con lo declarado en BD (ALLOW ⇔ `(m,a)`∈permisos o comodín; DENY = `403` exacto). Todo permiso con ≥1 prueba positiva y todo permiso crítico ausente con ≥1 negativa. Salida `evidence/matrix_*.json|md` (sin secretos).
- **AC-MX-02** Cambio dinámico con el **mismo token**: `ALLOW → retirar permiso → DENY → restaurar → ALLOW` (`/me` coherente), cambio de rol = reemplazo (sin unión), usuario `ACTIVE → INACTIVE → DENY` (access 401, refresh 401, login 403) y reactivación.
- **AC-MX-03** BU con el mismo token: concesión ⇒ lotes/eventos de la unidad accesibles; revocación ⇒ 404 inmediato en API operativa; re-concesión ⇒ restaura sin duplicar; revocar **una** entre varias no afecta a las demás; `GET /users/{id}/business-units` tras re-concesión devuelve historia + viva.
- **AC-MX-04** Huecos de cobertura de la tabla de cobertura (U1/U2/U3/U10/R5/R6/W3/W6/P5/B4/B10, auditoría con before/after y sin contraseña).
- **AC-E2E-01** E2E de navegador real: `ALLOW → REVOKE → DENY → RESTORE → ALLOW` para **permiso** y para **unidad de negocio**; `ACTIVE → INACTIVE → DENY` para usuario; cambio de contraseña (login con la nueva, la vieja falla); refresh automático conserva permisos; revocar desde Usuarios funciona.

## 3. Alcance
Dentro: `backend/app/auth/{service,router,security,schemas}.py`; `frontend/src/{components/ui/ConfirmDialog.tsx, pages/users/*, pages/admin/UnitAccessPage.tsx, stores/auth.store.ts, services/api.ts, main.tsx, i18n es/en}`; tests backend/frontend/E2E; evidencia. Fuera (§34): Cargas Iniciales, SAP real, KPIs, maestros no relacionados, rediseño visual, nuevo modelo de identidad/tokens, migraciones (no se prevé ninguna: head `f1a2b3c4d5e6` intacto).

## 4. Restricciones de diseño
1. **El backend decide**; la UI solo refleja (§4). Ningún AC se cierra con ocultar un botón.
2. Una sola fuente de autoridad: se reutiliza `get_current_user` (BD en cada petición); **no** se añade caché ni claims de permisos.
3. Sin migración: la unicidad insensible se resuelve en servicio (`lower()`); el `IntegrityError` es red de seguridad (`409`).
4. Los tests existentes que dependan del comportamiento previo (rol vacío, asignación de plantillas por actores sin esos permisos) se **actualizan con su razón explícita** (`DR-2`/`DR-3`), nunca se eliminan ni se debilitan.

## 5. Estrategia de pruebas
Backend: RED (los tests nuevos fallan en HEAD) → implementación → targeted GREEN → regresión completa → commit de implementación → sensibilidad (mutaciones por regla) → restauración por SHA → regresión post-mutación. Frontend: `vitest` (por componente), `tsc -b`, `vite build`. E2E: `scripts_e2e.sh` con `--workers=1`. Evidencia en `audit/ga-uat-admin-rbac-2026-10-31/`.

## 6. Constitution Gate
SPEC suficiente PASS · alcance acotado PASS · reglas de negocio (DR-1…DR-4 del Owner) PASS · API impact (códigos 409/422/403 nuevos; `GET /roles?include_inactive`) PASS · DB impact (ninguno) PASS · seguridad (backend decide, sin 2.ª fuente de autoridad, anti-enumeración 404 intacta) PASS · multiempresa PASS (suites reutilizadas) · regresión identificada PASS · AC verificables PASS · plan de pruebas PASS.
**AUTHORIZATION GATE: PASS** (decisiones materiales resueltas por el Owner el 2026-10-31).

---

## 7. Amendment S2-01 — `GA-UAT-USERS-S2-01` (2026-11-01, UAT SESIÓN 2)

**Entrada:** UAT SESIÓN 2 de Yolinel: `SESSION_1_UAT = PASS` (no se reabre). Hallazgo único: al editar un usuario y cambiar solo el **Rol**, «Guardar» muestra *«La nueva contraseña debe ser distinta de la actual»* sin que se haya tocado la clave.

**Clasificación:** *Caso B* (gap no cubierto, no regresión): `GA-REM-012` separó el cambio de clave en `POST /users/{id}/password` pero el modal de edición conservó un campo `type=password` siempre presente (R-195) y `handleSave` lo trataba como «clave nueva» si traía valor. **Severidad: P2 funcional/administración** (no se modifica credencial: la clave anterior sigue abriendo sesión; no se expone hash ni password; sin evasión de autorización).

**Reproducción BEFORE** (`evidence/01_before_repro.json`, sanitizado): `PUT /users/{id}` 200 (rol cambiado; el cuerpo NO lleva password) + `POST /users/{id}/password` 422 con la clave autocompletada = clave actual. Causa raíz: el navegador autocompleta el campo (captura del PDF: fondo azul de autofill, 9 puntos), `form.password` queda poblado, y el submit de «edición» dispara el flujo de cambio de clave. **Capa: frontend.** Backend correcto: `UserUpdate` es `extra=forbid` (sin password), el cambio de clave es endpoint dedicado, la regla «nueva ≠ actual» (AR-10) pertenece solo a ese endpoint.

**Contrato (único, sin valores mágicos):** edición administrativa y cambio de clave son operaciones distintas. En edición, la clave solo viaja si la persona activa **explícitamente** «Cambiar contraseña» (campos nueva + confirmación, `autocomplete="new-password"`); sin esa activación el submit no lee, valida ni envía clave y el formulario no contiene ningún campo de contraseña que el navegador pueda rellenar. Las reglas de clave (≥8, confirmación, ≠ actual, hash, auditoría `user_password`) no se debilitan.

| AC | Capa | Enunciado |
|---|---|---|
| **AC-S2-01** | frontend | Editar rol/nombre/apellido/email/estado/vista sin activar «Cambiar contraseña» ⇒ solo `PUT /users/{id}`; **ninguna** petición a `/password`; el cuerpo del PUT no contiene password. |
| **AC-S2-02** | frontend | En edición no existe `input[type=password]` hasta activar «Cambiar contraseña»; al desactivarla (o cerrar/reabrir) se descarta lo escrito. Los campos de clave llevan `autocomplete="new-password"` (también el alta). |
| **AC-S2-03** | frontend | Flujo explícito: nueva < 8 o confirmación distinta ⇒ error visible **antes** de cualquier petición (no se aplica un PUT a medias); válido ⇒ `PUT` y luego `POST /password {new_password}`; si el POST falla (p. ej. igual a la actual) el aviso indica que los datos se guardaron y la clave no cambió, con el detalle del servidor. |
| **AC-S2-04** | backend (pin) | `PUT /users/{id}` sin password conserva el hash; con clave `password` en el cuerpo ⇒ 422 (`extra=forbid`); cambiar solo el rol no toca hash, el rol nuevo es efectivo y la clave anterior autentica; el cambio explícito cambia el hash; nueva = actual ⇒ 422; sin `users:update` ⇒ 403; otra empresa ⇒ 404; la auditoría distingue `entity_type=user` (edición) de `user_password` (cambio de clave) y no registra password/hash. |
| **AC-S2-05** | E2E | Escenario de Yolinel: Rol A→B sin tocar clave (con el campo autocompletado simulado donde exista) ⇒ sin error de clave, rol B, clave anterior válida, `/me` del usuario con permisos de B, auditoría de edición y ninguna `user_password`; luego B→A (reversible). |

Fuera de alcance: política de clave, ciclo de vida de tokens (OD-01/DR-4), RBAC, SESIÓN 1.
**Constitution Gate:** spec suficiente PASS · alcance acotado PASS · sin decisión material nueva PASS · sin cambio de API/DB PASS · seguridad PASS (backend sin cambios, anti-IDOR intacto) · AC verificables PASS. **AUTHORIZATION GATE: PASS.**
