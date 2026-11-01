# GA-UAT-ADMIN-RBAC-2026-10-31 — Tabla de hallazgos (§29, previa a implementación)

**Baseline:** `main` @ `4aa0775` · **Fecha:** 2026-10-31 · Sin código de aplicación modificado hasta el Authorization Gate.
**Fuente funcional:** `SESION 1 – REVISION CONFIGURACION – USUARIOS – ROLES – 30-10-2026.pdf` (Yolinel, `qa.admin`, QA Avícola Integral) + sondas observacionales en HEAD (`evidence/01a|b|c_probe_head_observed.json` y `.py.txt`) + lectura de código + estado vigente de specs/decisiones.

Sigla `Y-x.y` = observación de Yolinel; `S#` = escenario de sonda; `N-#` = hallazgo propio.

## A. Lo que FUNCIONA como exige el mandato (demostrado en HEAD con el MISMO token)

| Control | Evidencia | Resultado |
|---|---|---|
| Permiso retirado del rol → DENY inmediato; restaurado → ALLOW; `/me` coherente | S12 (403 → 200, `/me` permisos [] → [audit:read]) | **PASS** |
| Cambio de rol de usuario: permisos del rol anterior desaparecen, sin unión | S13 (`/audit` 200→403, `/lots` 403→200, `/me` = solo `lots:read`) | **PASS** |
| Usuario inactivo: access 401, refresh 401, login 403, reactivación → login 200 | S14 | **PASS** |
| Revocar/re-conceder BU → `/me` granted/effective correctos; sin duplicados vivos | S10 (`/me`), índice parcial único | **PASS** |
| Rol sin permisos → usuario entra y recibe 403 en todo salvo perfil | S5 | **PASS** (comportamiento, ver AR-18) |
| Tenant isolation, wildcard global R-199, reset scope R-202, segregación OD-15 | suites existentes (`test_user_tenant_isolation`, `test_r199…`, `test_r202…`, `test_access_administration`) | **PASS** (reutilizado, §27) |
| Contraseña: actual obligatoria/correcta, <8 → 422, clave vieja → 401, nueva → 200 | S9 + `test_p013_password` | **PASS** |

## B. Hallazgos

| ID | Origen | Reproducido | Esperado | Actual (HEAD) | Root cause | Sev | Spec dueña / decisión | Acción |
|---|---|---|---|---|---|---|---|---|
| **AR-01** | Y-2.2 · mandato §18 | ✅ S4 | Un rol desactivado no deja «autoridad fantasma» | Rol inactivo con usuario asignado: **mismo token** `/me`,`/lots`,`/audit` 200; login 200; refresh 200 | `get_current_user`/`login`/`refresh` nunca consultan `Role.is_active`; `update_role` no mira usuarios | **P1** (decisión) | GA-REM-034 AC09 dice «sin romper a los usuarios» ⇒ **conforme a spec pero contradice mandato §18 y Y-2.2** → `MATERIAL_DECISION_REQUIRED` (Q1) | Pendiente Owner |
| **AR-01b** | S4 | ✅ S4 | Un rol inactivo no es asignable | `POST /users` con rol inactivo → 201; `PUT /users` → 200 | `_rol_asignable` no filtra `is_active` | **P1** | GA-REM-034 / OD-13 (sin decisión necesaria: «baja lógica» ya lo saca del catálogo) | Fix (independiente de Q1) |
| **AR-02** | OD-05 · mandato §20/§26 | ✅ S7, S11 | Administrar acceso ≠ elevar el propio | Usuario con `users:read+update` se auto-asigna «TEST Operador» (6 permisos) y los obtiene; con `users:create` puede fabricar roles `(*,delete,company)` y asignarlos | Sin política de escalada (OD-05 PENDING desde Wave 2); R-199 solo cierra el comodín global | **P1** (decisión) | **OD-05** → `MATERIAL_DECISION_REQUIRED` (Q3) | Pendiente Owner |
| **AR-03** | mandato §5 | ✅ S1 | `409` determinista y accionable | Alta con `username` de A + `email` de B → **excepción `MultipleResultsFound` sin capturar (500)** | `create_user`: `scalar_one_or_none()` sobre un `OR` | **P2** | GA-REM-002 enm. B (usuarios) | Fix + RED |
| **AR-04** | mandato §5 | ✅ S3 | `409` accionable | `PUT /users/{B}` con email de A → **`IntegrityError` `ix_users_email` sin capturar (500)** | `update_user` no valida unicidad | **P2** | idem | Fix + RED |
| **AR-05** | mandato §5 «identidades ambiguas» | ✅ S2 | Sin duplicados ambiguos (capitalización/espacios) | `PA_…` y `pa_…` coexisten; email en MAYÚSCULAS distinto; `"  esp_  "` se guarda con espacios | Índices únicos sensibles a mayúsculas; sin `strip()`; sin decisión de normalización | **P2** | Mandato §5 (explícito) | Fix: `strip` + comparación `lower()` en servicio (sin migración) |
| **AR-06** | mandato §6 | ✅ S6 | Nombre de rol único por empresa | `POST /roles` ×3 mismo nombre (y `.upper()`) → 201 | Sin unicidad (modelo ni servicio) | **P2** | GA-REM-034 | Fix: 409 por (empresa, nombre) insensible a mayúsculas |
| **AR-07** | mandato §5 / Y-1.3 | ✅ S8 | Una sola autoridad para dar de baja | `PUT is_active=false` con solo `users:update` → 200; `DELETE` exige `users:delete` | Dos caminos con permisos distintos | **P2** | GA-REM-002 | Fix: `is_active=false` por PUT exige además `users:delete` |
| **AR-08** | mandato §5 | ✅ S7 | No auto-bloquearse | `PUT` propio `is_active=false` → 200 y token → 401 | Sin guarda de auto-acción | **P2** | agrupado con AR-02 (Q3) | Con Q3 |
| **AR-09** | mandato §24 | ✅ S15 | Auditoría con before/after | Edición de rol guarda `{nombre}`; sin diff de permisos ni de `is_active` | `update_role` audita `new_values={"nombre"}` | **P2** | GA-REM-032 AC03 | Fix + RED |
| **AR-10** | mandato §12 | ✅ S9 | Nueva clave igual a la actual → rechazo | `nueva == actual` → 204 | Edge case de GA-REM-012 (`:93`) no implementado | **P3** | GA-REM-012 | Fix menor |
| **AR-11** | mandato §12/§17 | ✅ S9 | (contrato vigente) | Access y refresh previos **siguen válidos** tras cambiar la clave | GA-REM-012 AC08 / GAP-09 / OD-01 (documentado y fijado por test `t012_08`) | **P2** (decisión) | OD-01 abierta → `MATERIAL_DECISION_REQUIRED` (Q4) | Pendiente Owner |
| **AR-12** | R-123 | ✅ código | `scope_type/scope_id` aplicados o declarados ignorados | `tiene_permiso` los ignora; UI siempre envía `all` | R-123 OPEN (nota de seguridad) | **P2** (conocido) | R-123 | Solo test que fije la política vigente; sin cambio |
| **AR-13** | **Y-1.2** | ✅ lectura (E2E RED en implementación) | «Revocar» desde Usuarios revoca | Solo oscurece la pantalla | `Modal` (portal, `z-50`) tapa a `ConfirmDialog` (inline, `z-50`) | **P2** | GA-FE-02 | Fix + RED (jsdom+E2E) |
| **AR-14** | **Y-3.2** | ✅ S10 (2 filas) + código | Estado actual por unidad | Muestra «Revocada (histórica)» tras re-conceder | `grants.find(x=>x.code===code)` toma la fila revocada más antigua; el API devuelve historia completa | **P2** | GA-FE-02 / GA-REM-040 | Fix: preferir la concesión viva |
| **AR-15** | **Y-1.1** | ✅ código | Mostrar empresa y usuario | Panel sin ellos; cabeceras «EMPRESA/USUARIO» son *estado empresa/usuario* | Falta cabecera; rótulos ambiguos | **P3** | GA-FE-02 | Fix UI |
| **AR-16** | **Y-3.1** | ✅ código | Confirmación con usuario y unidad | Mensaje genérico | `revokeConfirmMessage` sin interpolación | **P3** | GA-FE-02 | Fix UI |
| **AR-17** | **Y-1.3** | ✅ código | Etiqueta coherente con el efecto | Icono/etiqueta «Eliminar» ejecuta baja lógica reversible | i18n `users.deleteUser`="Eliminar" | **P3** | mandato §6 (UI coherente) | Renombrar a «Desactivar usuario» (mantiene `users:delete`) |
| **AR-18** | **Y-2.1** | ✅ S5 | Rol con ≥1 permiso (propuesta Yolinel) | Rol vacío se crea (201) | `RoleCreate.permissions=[]` válido; GA-REM-002 contempla «rol sin permisos → 403» | **P2** (decisión) | sin decisión escrita → `MATERIAL_DECISION_REQUIRED` (Q2) | Pendiente Owner |
| **AR-19** | N-1 (mandato §16/§17 B) | ✅ nivel store | Sesión conserva autoridad tras refresh | `permissions`, `effective_business_units`, nombre, email → **perdidos**; `canApprove true→false` | `setTokens` reemplaza `user` por uno derivado de claims; nadie vuelve a llamar `/me` | **P2** | GA-REM-003 (identidad tras refresh) | Fix + RED (jsdom + E2E navegador) |
| **AR-20** | Y-2.2 (rol inactivo) | ✅ código | Rol inactivo gestionable | Sin vía de reactivación en UI; `GET /roles` solo activos; botón de baja gateado por `users:delete` pero el backend exige `users:update`; `alert/confirm` nativos | `get_roles` filtra activos; desajuste de permisos UI/BE | **P3** | GA-REM-034 / R-212 | Con Q1 |

| **AR-21** | N-2 (sesión, UI) | ✅ jsdom | Un 403 recibido con sesión abierta reconcilia permisos del store (menú coherente sin recargar) | El store conservaba permisos obsoletos hasta recarga manual; la UI seguía ofreciendo lo ya revocado | Ningún manejador reaccionaba a 403 | **P3** | GA-REM-003 / SPEC 013 `AC-SS-02` | Fix: `registerForbiddenHandler` + `/me` con throttle (E2E P-17-F) |
| **AR-22** | N-3 (Usuarios) | ✅ jsdom | El administrador ve y encuentra a todos sus usuarios | Listado limitado a 20 sin búsqueda ni paginación | `GET /users` sin `limit` explícito en el cliente | **P2** | GA-FE-02 | Fix: `limit=100` + búsqueda cliente (observación: sin paginación completa si >100) |
| **AR-23** | N-4 (hallado en E2E P-17-E/F) | ✅ E2E (3 ejecuciones: 1 atrapada, 2 convergen) + jsdom RED (21 navegaciones) | Un usuario con autoridad válida pero sin `dashboard:read` ni unidad productiva aterriza en una pantalla estable | Bucle infinito `/` ⇄ `/menu/poultry` (~300 navegaciones/s, `<main>` vacío, CPU alta); la ruta destino (`/audit`) solo se alcanza si el rebote converge por azar | `HomeRoute` (R-212 AC-02) redirige a `/menu/poultry` aunque el hub no sea alcanzable; `MenuHubPage` (GA-FE-03, fail-closed) devuelve a `/` cuando `poultry` no sobrevive a `filterNavItemsBySession` (exige `requiresUnits`) | **P2** (preexistente; no regresión de GA-REM-002/003/012) | R-212 AC-02 / GA-FE-03 | Fix: `HomeRoute` solo redirige si el hub existe; si no, aviso neutro `role="status"` (`home.noLanding`); AC-R212-02 ajustado (su sesión sin unidades montaba el hub como stub y ocultaba el bucle) |

**Severidad §26:** no se degrada ningún bypass por ocultamiento de UI. AR-01/AR-02 son P1 *pendientes de decisión Owner* porque el comportamiento actual está respaldado por texto de spec (GA-REM-034 AC09) y por una decisión nunca tomada (OD-05).

## C. Regresiones vs. remediaciones antiguas (§27)

- **GA-REM-002 / GA-REM-003 / GA-REM-012 / R-199 / R-200 / R-202:** sin regresión — todos sus contratos se sostienen en HEAD (secciones A y suites reutilizadas).
- **AR-19** es el residual de **GA-REM-003** en el *cliente* (la spec corrigió los claims del backend; el store sigue reconstruyendo desde claims).
- **AR-03/AR-04/AR-05** son hallazgos nuevos sobre `create_user`/`update_user` (no hay AC previo de «409 determinista»).

## D. Gate
- **Decision-independent (AR-01b, 03, 04, 05, 06, 07, 09, 10, 13, 14, 15, 16, 17, 19; tests de matriz/dinámicos/E2E):** bugs de semántica ya definida o mandato explícito ⇒ `AUTHORIZATION GATE = PASS`.
- **Decision-gated (AR-01, 02/08, 11, 18, 20):** `MATERIAL_DECISION_REQUIRED` — se consulta al Owner con recomendación.
