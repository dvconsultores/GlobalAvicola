# `GA-REM-034` · ADMINISTRACIÓN DE ROLES Y PERMISOS

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-034` · `CAPABILITY SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Hallazgos** | `R-92` (sin superficie de administración) · `R-93` (los permisos de un rol no se pueden editar) · `R-94` (sin catálogo de permisos) |
| **Proceso** | `P-13` · Autenticación y Gestión de Usuarios — `docs/02 §3.1.3` |
| **Dependencias** | `GA-REM-002` `CERTIFIED` (enforcement) · `GA-REM-032` `CERTIFIED` (auditoría) |
| **Decisión abierta** | `OD-05` — no bloquea (§6) |
| **Antecedentes** | `P13_PROCESS_CHAIN_MATRIX.md` · `P13_BACKEND_CAPABILITY_MATRIX.md` · `P13_FRONTEND_CAPABILITY_MATRIX.md` · `P13_CAPABILITY_PARITY_MATRIX.md` |

> **No se expande `GA-REM-002`.** Aquella gobierna el **enforcement** —que el permiso se
> aplique— y está `CERTIFIED`. Esto es **administración** —que el permiso pueda concederse
> desde el producto—, que es otra cosa. El enforcement se reutiliza intacto.

---

## 1. Requisito

`docs/02 §3.1.3`, prioridad **Alta**:

> **Gestión de Roles.** CRUD de roles con permisos granulares.
> Permisos por rol: módulos accesibles · acciones por módulo (leer, crear, editar, eliminar)
> · acciones especiales (corregir, aprobar, rechazar, enviar a SAP) · alcance por
> granja/empresa.

## 2. Los tres huecos

**`R-92`.** No hay ninguna superficie: ni ruta en `App.tsx`, ni componente en `pages/`. El
cliente de API existe a medias —`authService.createRole` declara `{name, description}` y **no
envía permisos**, que es justo lo que hay que administrar—.

**`R-93`.** `RoleUpdate` solo admite `name`, `description` e `is_active`. Un rol nace con sus
permisos y **no puede cambiarlos nunca**. Sin esto, «CRUD con permisos granulares» se queda en
«alta con permisos granulares».

**`R-94`.** Ningún endpoint dice qué módulos y acciones existen. Una interfaz tendría que
repetirlos a mano y quedarían desincronizados al añadir un módulo.

## 3. Fuera de alcance

- El **enforcement**: `GA-REM-002`, certificado, intacto.
- La gestión de usuarios: `UsersPage` ya la cubre — el `422` de `audit/06` está obsoleto.
- `DELETE /roles/{id}`: la baja lógica va por `PUT` con `is_active`, coherente con todo el
  producto. **No se añade por simetría.**
- **`Role.company_id`**: existe, nunca se fija y `docs/02 §3.1.3` sitúa el alcance en el
  **permiso** (`scope_type`), no en el rol. Sin fuente que lo contradiga, los roles siguen
  siendo globales y **no se introduce filtrado por compañía por intuición**.
- `P-14`, `OD-04`, SAP real.

## 4. Actores

`docs/02 §3.1.2` — «Permisos: **solo administradores**». En términos del producto: quien
posee `users:read`, `users:create` y `users:update`, que es el permiso que ya protegen los
endpoints de roles. **No se crean permisos nuevos.**

## 5. Criterios de aceptación

### `AC01` · El catálogo de permisos es consultable
`GET /roles/permissions-catalog` devuelve los módulos y las acciones que el sistema reconoce,
tomados de las fuentes de verdad (`PermissionAction` y los módulos de `AuditModule` más los
que el enforcement usa). La interfaz **no** los repite a mano.

### `AC02` · Los permisos de un rol se pueden editar
`PUT /roles/{id}` acepta `permissions`. Cuando viaja, **sustituye** el conjunto del rol: se
crean los que faltan y se retiran los que sobran, exactamente los indicados.

**Puerta de validez.** Se comprueba el **conjunto exacto** resultante, no que el número haya
subido. Y se comprueba que retirar uno concreto retira ese y no otro.

> **Sustituir y no acumular.** Es la semántica que el alta ya tiene —`POST /roles` recibe la
> lista completa— y la única que permite **quitar** un permiso. Una operación que solo añadiera
> no podría revocar nada, que es la mitad de administrar permisos.

### `AC03` · El cambio de permisos se audita
Reutiliza `GA-REM-032`: `PERMISSION_CHANGE`, módulo `users`, con el rol afectado y el actor.
**No se duplica lógica de auditoría.**

### `AC04` · Existe la superficie de administración
Ruta `/roles` con listado, alta, edición y baja lógica, sobre el patrón administrativo
vigente. Cada rol muestra sus permisos y permite modificarlos.

### `AC05` · Lo que la interfaz envía llega al dominio
`R-47` / `P0-14`: los permisos elegidos en el formulario llegan al esquema y producen el
efecto. **Prohibido** un `2xx` con el campo descartado en silencio.

### `AC06` · Persistencia inmediata
`R-68`: tras crear o editar, una lectura posterior ve el conjunto nuevo. Sin esperas.

### `AC07` · El permiso concedido surte efecto
Es lo que une administración con enforcement: tras conceder un permiso a un rol, un usuario
con ese rol **puede** la acción; tras retirarlo, **no puede**.

**Puerta de validez.** CONTROL y TRATAMIENTO sobre el mismo usuario y la misma operación; lo
único que cambia es el permiso del rol. Un `403` genérico no basta: se comprueba que la misma
llamada pasaba antes.

### `AC08` · Sin permiso no se administra
Sin `users:create` / `users:update`, `403`.

### `AC09` · Baja lógica
Desactivar un rol lo saca del listado activo sin borrarlo, y sin romper a los usuarios que lo
tienen asignado.

### `AC10` · La evidencia puede fallar
`GA-REM-016 AC13`. Mutación controlada y revertida sobre la sustitución de permisos, sobre el
efecto del permiso concedido y sobre la superficie de administración.

## 6. `OD-05` no bloquea esta spec

```
OD-05 · ¿puede un administrador conceder permisos que él mismo no posee?
        OWNER_DECISION_REQUIRED — sin fuente normativa
```

Administrar roles hace falta en cualquiera de sus respuestas. **No se implementa ninguna
restricción de escalada**, porque inventarla sería inventar seguridad; si el propietario
decide que la haya, se añade sobre esta misma superficie sin rehacerla.

Queda declarado para que no se lea como un descuido.

## 7. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01` `AC02` `AC03` `AC06` `AC08` `AC09` | `backend/tests/test_role_administration.py` | integración HTTP |
| `AC07` | ídem, CONTROL + TRATAMIENTO | integración HTTP |
| `AC04` `AC05` | `e2e/proceso-p13-roles-y-permisos.spec.ts` | `UI_E2E` + `API_E2E` |
| `AC10` | informe de certificación | mutación |

## 8. Definición de terminado

- Los diez criterios pasan.
- Existe prueba que **falla contra el código actual** por la causa exacta.
- Sensibilidad demostrada y revertida.
- Los 14 pasos de `P13_PROCESS_CHAIN_MATRIX` se recorren.
- Paridad i18n preservada; ninguna cadena embebida.
- Regresión completa sin fallos nuevos.
