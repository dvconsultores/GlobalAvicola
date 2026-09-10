# GA-FE-02-A · CLARIFICATIONS — MODELO DE AUTENTICACIÓN Y PROVISIONING

Respondido desde el código y las specs en el baseline `d120fdd` (no supuesto). Sin valores de
credenciales en ningún punto.

## C-01 · ¿Cómo se autentica un usuario?

`POST /api/v1/login` (usuario + contraseña) emite `access_token` + `refresh_token` (JWT; el
access expira a los 30 min). El frontend guarda ambos (`auth.store`), adjunta `Bearer` y refresca
single-flight con `POST /api/v1/refresh` ante 401. MFA: **no aplica** (no existe en el producto).

## C-02 · ¿Qué valida el servidor por petición?

`get_current_user` carga el usuario, compone permisos y resuelve la **empresa efectiva** por
`OD-11` (persistida, salvo contexto de switch autorizado y **re-validado en cada petición**).

## C-03 · ¿Existe confirmación por email / verificación?

No — el alta de usuario es administrativa; `is_active` controla el acceso. No hay flujo de
auto-registro.

## C-04 · ¿Cómo debe crearse legítimamente una cuenta de prueba?

Solo mediante los flujos oficiales:
1. Un actor con `users:create` (o el propio panel `/users`) crea el usuario →
   `POST /api/v1/users`; o el **Super Administrador** existente.
2. Se le asigna `company_id` (empresa de prueba), `role_id` existente y `view_type`.
3. Se activa (`is_active=true`).
4. Sus permisos provienen de su **rol existente** (no se crean permisos ni roles nuevos —
   prohibido por el encargo). Roles candidatos ya definidos: «Administrador de Accesos»
   (exactamente `business_units:read|update|create|delete`; sin `users:read` — por diseño `OD-15`)
   y los roles de usuario operativo existentes para el Target User.
5. La contraseña del usuario de prueba se establece por el mecanismo oficial
   (`POST /users/{id}/password` o el campo de creación).

**Requisito bloqueante de esta vía**: disponer de **una credencial bootstrap** (p. ej. el Super
Administrador o un admin con `users:create`) entregada por el propietario. Sin ella no hay forma
autorizada de provisionar (prohibido seed/DB/bypass).

## C-05 · ¿Qué permisos exactos necesita cada actor?

- **Company-BU Admin**: `business_units:read` + `business_units:update` (habilitar/apagar).
- **Access Admin**: `business_units:read|update|create|delete` y **nada más** (el rol sembrado
  «Administrador de Accesos» los tiene exactamente; NO tiene `users:read` — la superficie de
  candidatos de GA-FE-02 existe precisamente para eso).
- **Target User**: RBAC de la capacidad representativa elegida (p. ej. lectura productiva
  gobernada existente) + pertenencia a la empresa de prueba; **sin** la concesión de la BU
  objetivo al inicio.
- **Unauthorized Control**: sin ningún permiso `business_units:*`.
- **Global Actor (opcional)**: comodín existente; solo si su credencial está disponible
  legítimamente. Si no, se reporta `GLOBAL_RUNTIME_CONTROL BLOCKED_AUTH` (supuesto por §46) sin
  bloquear el resto.

## C-06 · ¿Qué empresa usar?

Una **empresa de prueba dedicada o ya existente en ENV-01** que no esté en uso productivo por
otros testers. **No** se inventa CRUD de empresas (SAP es autoridad del maestro, `OD-18`;
`OD-20 §14`). Si no existe una empresa segura, `BLOCKED_FIXTURE` para los flujos que muten estado.

## C-07 · ¿Qué estado inicial conviene? (fixture de alta información)

```
Company BU:   grandparent ON · breeder OFF · hatchery ON · broiler OFF
Target User:  concesiones iniciales: hatchery YES · grandparent/breeder/broiler NO
RBAC del Target: permiso productivo gobernado para la BU objetivo (para el experimento 3D)
```

Registrar el estado REAL encontrado; no forzar si el entorno no lo permite con seguridad.

## C-08 · ¿Cómo se concede/revoca por API oficial?

`POST /users/{id}/business-units {code}` y `DELETE /users/{id}/business-units/{code}`
(concesión viva/revocada por `revoked_at`; nunca borrado). Habilitar/apagar empresa:
`PATCH /business-units/{code}/enable|disable`. Auto-concesión: **403 en servidor**. Objetivo de
otra empresa: 404 según contrato. Empresa apagada: candidatos/concesión 409.

## C-09 · ¿La sesión del usuario objetivo se actualiza sola?

El acceso efectivo se resuelve **por petición** en el servidor (no en el token): un refresh de
sesión basta para que el nuevo conjunto efectivo se aplique; el relogin garantiza el escenario
completo. Se registrará IMMEDIATE / AFTER_REFRESH / AFTER_RELOGIN según lo observado (§49).

## C-10 · ¿Qué consideraba GA-FE-02 sobre `users:read`?

Que el Administrador de Accesos **no lo tiene** y no debe obtenerse: la administración de
concesiones para él ocurre en la superficie de candidatos de `/admin/unit-access` (contrato
`R-129`/`OD-15 §6`). El panel por usuario de `/users` es para actores que sí tienen `users:read`.

## C-11 · ¿Qué NO está disponible en esta ejecución? (determinación §26–29)

```
Credenciales autorizadas suministradas por mecanismo autorizado: NINGUNA (verificado: 0)
Sesión autenticada explícitamente disponible: NINGUNA (navegador compartido en /login)
Actor bootstrap autorizado disponible: NO EXISTE
Búsqueda de credenciales: NO REALIZADA · Adivinación: NO · Bypass/DB: NO
→ MODE_C BLOCKED_AUTH (§79): se emiten requerimientos y se detiene la certificación.
```
