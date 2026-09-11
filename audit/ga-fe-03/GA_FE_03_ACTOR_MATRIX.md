# GA-FE-03 · MATRIZ DE ACTORES

**Mecanismos oficiales** (`GA-REM-004`): usuarios sintéticos vía `POST /users`; roles
temporales vía `POST /roles` (solo permisos canónicos existentes); concesiones vía
`POST/DELETE /users/{id}/business-units`; habilitación de empresa vía
`PATCH /business-units/{code}/enable|disable`. Credenciales efímeras fuera del repo; baja al
cierre (`DELETE /users/{id}`, `PUT /roles/{id}`); rol canónico 35 intacto.

| Actor | Usuario sintético | id | Rol | Empresa | Permisos | Concesiones iniciales | Escenarios que cubre |
|---|---|---|---|---|---|---|---|
| `E` Global | bootstrap (`admin`) existente | 1 | Super Administrador (comodín) | — (sitúa por selector) | `("*", all)` | — | no-contexto, switch, BU OFF/ON, control-plane, 3D caso global, relogin |
| `A` CBU Admin | `ga-fe03-a` | nuevo | temporal `business_units:read`+`update`+`dashboard:read` | 1 | control-plane unidades | ninguna | NAV-AC25, hub propio, sin productivo |
| `B` Access Admin | `ga-fe03-b` | nuevo | **canónico 35** (4 permisos `business_units:*`) | 1 | read/update/create/delete | ninguna | NAV-AC26/27, self-grant sigue 403 |
| `C` Productivo | `ga-fe03-c` | nuevo | temporal `lots:read`+`operations:read`+`dashboard:read` | 1 | productivo | `broiler` (tras grant) | 3D completo, grant/revoke, BU enable/disable, relogin |
| `D` Sin autoridad | `ga-fe03-d` | nuevo | temporal `dashboard:read` | 1 | CORE mínimo | ninguna | NAV-AC28, deep links, hub `D-2` cerrado |
| `Z` Cero unidades | `ga-fe03-z` | nuevo | temporal `dashboard:read` | 1 | CORE mínimo | ninguna | NAV-AC16, sin grupos vacíos, sin error genérico |
| `P` RBAC-negativo | `ga-fe03-p` | nuevo | temporal `dashboard:read` | 1 | CORE mínimo | `broiler` (grant vivo) | NAV-AC14/73 — BU ON + concesión + RBAC NO ⇒ oculto/denegado |

**Roles temporales**: reutilizar si existen (36/37/38 inactivos de GA-FE-02: 36≈A, 37≈C,
38≈D/Z/P base) o crear nuevos `ga-fe03-*` **solo** con permisos canónicos existentes; se
desactivan al cierre. `D` y `Z` comparten forma de rol; se mantienen separados porque
certifican cosas distintas (negativas vs CORE mínimo con navegación usable).

**Separation checks** (§22): A-rol no ve `users`; B (35) no ve `users` (OD-15 §6: sin
`users:read`); ninguno gana productivo por su rol de control. Sin gating por nombre en el
código (grep de cierre: 0 `role.name`/`roleName` en componentes de navegación).

**Estados de empresa**: empresa 1 de certificación (`TEST COMPANY A`) con las 4 unidades del
catálogo; company 3 (`Avícola Del Sur C.A.`) disponible para X/aislamiento solo si un escenario
lo exige (no exigido por esta tranche: el aislamiento por empresa ya está certificado en
GA-FE-02 y los héroes de GA-FE-03 son dimensión BU, no multiempresa).
