# R-195 · FINDING — EDICIÓN DE USUARIOS IMPOSIBLE (`PUT /users` CON `username`/`company_id` ⇒ 422) Y ERROR ILEGIBLE

| Campo | Valor |
|---|---|
| **ID canónico** | **R-195** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | `UsersPage` envía `username` y `company_id` en `PUT /users/{id}`; `UserUpdate` es `extra="forbid"` ⇒ **422 en toda edición**; el error se muestra con `alert(detail)` ⇒ «[object Object]» (detalle perdido) |
| **Severidad** | **P1** (§49: gestión de usuarios inoperante por UI; P-13) |
| **Clase** | `REQUEST_CONTRACT` (stale DTO) / `ERROR_HANDLING` |
| **Proceso** | P-13 (autenticación y gestión de usuarios) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Familia** | B-06/B-28 (informe B); C (mutaciones con `alert`); R-118 (empresa resuelta en servidor); `P0-13` |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-195/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (gestión de usuarios; roles/accesos base del sistema) |
| **UAT del propietario** | sí (flujo visible; agrupable con R-196/R-215) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `frontend/src/pages/users/UsersPage.tsx:76-79,85` — el guardado de edición envía `{...datos}` incluyendo `username` y `company_id`; `auth/schemas.py:65-85` (`UserUpdate`) es `extra="forbid"` y **no** declara `username`/`company_id` (empresa se resuelve por contexto, R-118) ⇒ **422 «Extra inputs are not permitted» en toda edición**.
- Error: `alert(detail || …)` (`:85`) ⇒ coacción a «[object Object]» sin mensaje útil.
- Creación: `last_name` con `min_length=1` en backend no se exige en UI (`B-28`); selector de empresa mostrado pero ignorado por el servidor para actores acotados.
- Baja: `confirm` + modal que queda abierto sin mensaje si falla (`C#30`).
- Evidencia local: `H3-users-edit-boton: no visible` (el arnés no localizó el control con el rol de prueba; la edición no llegó a ejercitarse por UI en la corrida local).

### 1.2 Contraste API

`PUT /users/{id}` con el subconjunto permitido (`first_name`, `last_name`, `email`, `phone`, `role_id`, `is_active`, `view_type`, `area_id`) funciona (200); con `username`/`company_id` ⇒ 422.

## 2 · Causa raíz

DTO del frontend obsoleto respecto a `UserUpdate` (quedó del contrato anterior a R-118/`extra=forbid`); manejo de error con `alert` en lugar del normalizador `getErrorMessage`.

## 3 · Impacto

- Ninguna edición de usuario (nombre, correo, rol, estado, vista, área) puede guardarse por UI — administración de personas bloqueada salvo alta/baja.
- Errores ilegibles («[object Object]») incluso cuando el usuario acierta a descubrir el problema.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-118` (empresa del contexto), `P0-13` (histórico de usuarios), `GA-REM-012` (contraseñas) — ninguno cubre el DTO de edición. |
| Informes B/C | B-06 + C (alert) coinciden; registro G-06. |

Conclusión: **nuevo**; ID asignado **R-195**.

## 5 · Propietario sugerido

Frontend (usuarios) + regresión backend de `UserUpdate`. Sin migración.

## 6 · Bloquea SAP y por qué

**SÍ**: la asignación de roles/áreas/estado de usuarios es prerrequisito operativo del sistema que alimentará SAP; hoy no es gestionable por UI.

## 7 · Interdependencias

- **R-202** (reset de contraseña por admin): misma pantalla; paquete aparte (backend), se agrupan en la UAT.
- **R-199** (autoridad global fabricable): mismo dominio de roles; seguridad, paquete propio.
- **R-215** (render seguro): `UsersPage` usa `alert` (no React #31), pero comparte el objetivo de errores legibles; fix mínimo aquí.
- **R-212** (UI consciente del permiso): gates de `/users`.
