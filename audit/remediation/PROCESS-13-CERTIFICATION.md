# `P-13` · AUTENTICACIÓN Y GESTIÓN DE USUARIOS — INFORME DE CERTIFICACIÓN

`docs/02 §3.1` · `GA-REM-034` · 2026-09-06

```
P-13 = CERTIFIED
R-92 = CERTIFIED   R-93 = CERTIFIED   R-94 = CERTIFIED
OD-05 = OWNER_DECISION_REQUIRED  (no bloquea — §6)
```

---

## 1. El nombre y el alcance, corregidos

La matriz llamaba a `P-13` «Usuarios, roles y permisos». `docs/02 §3.1` lo llama **Módulo 1 ·
Autenticación y Gestión de Usuarios**, y es más ancho: acceso, usuarios, roles, aislamiento
multiempresa y perfil. **14 pasos**, no dos pantallas.

## 2. La auditoría bidireccional, otra vez decisiva

`audit/06` resultó **obsoleto por quinta vez**:

| Decía | Hoy |
|---|---|
| «Usuarios: pantalla **rota** (`limit=200` → 422)» | `UsersPage` llama a `/users` sin `limit` y crea, edita, cambia contraseña, activa, desactiva y asigna rol. **El hueco no existe** |
| «Permisos: sin pantalla y **sin enforcement**» | el enforcement lo certificó `GA-REM-002`; faltaba la pantalla |
| «Roles: 3 endpoints, sin pantalla» | **confirmado**, y con dos huecos más de backend que el audit no veía |

Y una asimetría que solo aparece mirando los dos lados: **el cliente de API de roles ya
existía** (`authService.listRoles`, `createRole`, `updateRole`). Lo que faltaba era la
pantalla — y `createRole` declaraba `{name, description}`, **sin permisos**, que es justo lo
que hay que administrar.

## 3. Los tres huecos

**`R-92` (P1).** Ninguna superficie para administrar roles: ni ruta en `App.tsx` ni componente
en `pages/`. `§3.1.3` es un submódulo normativo de prioridad **Alta** sin forma de ejercerse
desde el producto.

**`R-93` (P2).** `RoleUpdate` admitía `name`, `description` e `is_active`. Un rol nacía con
sus permisos y **no podía cambiarlos nunca**: «CRUD con permisos granulares» se quedaba en
«alta con permisos granulares».

**`R-94` (P2).** Sin catálogo de permisos, una interfaz tendría que repetir módulos y acciones
a mano y quedarían desincronizados al añadir un módulo.

## 4. Sustituir, no acumular

`AC02` fija que `PUT /roles/{id}` **sustituye** el conjunto de permisos cuando viaja. Es la
semántica que el alta ya tenía, y la única que permite **quitar** uno — que es la mitad de
administrar permisos. Omitir el campo deja los permisos intactos, para que editar el nombre no
los borre.

Un detalle de implementación que costó un fallo: el asignador genérico
(`model_dump(exclude_unset=True)` + `setattr`) intentaba asignar una lista de diccionarios a
la relación. Se excluye `permissions` de ahí porque se trata aparte.

## 5. Lo que no se tocó, y por qué

| | Motivo |
|---|---|
| el **enforcement** | `GA-REM-002` `CERTIFIED`. Esto es **administración**, que es otra cosa. No se reimplementa |
| `UsersPage` | funciona; el `422` de `audit/06` está obsoleto |
| `DELETE /roles/{id}` | la baja lógica va por `PUT` con `is_active`, coherente con todo el producto. **No se añade por simetría** |
| `Role.company_id` | existe, nunca se fija, y `docs/02 §3.1.3` sitúa el alcance en el **permiso** (`scope_type`), no en el rol. Sin fuente que lo contradiga, **no se introduce filtrado por compañía por intuición** |

## 6. Una decisión que no me corresponde

```
OD-05 · ¿puede un administrador conceder permisos que él mismo no posee?
```

Nada impide que quien tiene `users:create` cree un rol con `module="*"`, `scope_type="all"` y
se lo asigne. Busqué la regla en `docs/`, `specs/` y `audit/`: **no existe**.

**No se implementó ninguna restricción de escalada**, porque inventarla sería inventar
seguridad. Administrar roles hace falta en cualquiera de las respuestas posibles, y la
restricción —si el propietario decide que la haya— se añade sobre esta misma superficie sin
rehacerla.

Hoy solo el Super Admin trae `users:create` en las semillas. Eso es una propiedad **de las
semillas**, no una garantía estructural: exactamente lo mismo que ya se dijo de `R-60`.

## 7. La cadena, paso a paso

| Mitad | Pasos | Estado |
|---|:--:|:--:|
| acceso y perfil (§3.1.1, §3.1.4bis) | 1-3, 12 | **PASS 4** |
| gestión de usuarios (§3.1.2) | 4-6 | **PASS 3** |
| gestión de roles (§3.1.3) | 7-10 | **PASS 4** |
| aislamiento y auditoría (§3.1.4, §3.11) | 11, 13-14 | **PASS 3** |

```
14 pasos · PASS 14 · FAIL 0
```

El paso 14 es el que une administración con enforcement: tras conceder `audit:read` a un rol,
un usuario con ese rol consulta la auditoría; tras retirarlo, recibe `403`. **La misma llamada
y el mismo usuario** — solo cambia el permiso.

## 8. Evidencia

### Fase roja

| Prueba | Con el código anterior |
|---|---|
| catálogo de permisos | **405 Method Not Allowed** |
| sustituir permisos | **200 con el campo descartado en silencio** — el patrón `R-47`/`P0-14` |
| retirar un permiso concreto | seguía presente |

### Puerta de sensibilidad

| Mutación | Fallan | Restaurado |
|---|:--:|:--:|
| la edición deja de sustituir permisos | **3** | 7/7 |
| el catálogo pierde las acciones | **1** | 7/7 |
| los permisos no se persisten | **2** | 7/7 |

`git diff` tras revertir: solo lo previsto.

### Modalidad

`UI_E2E` para la superficie (`AC04`, `AC05`) y `API_E2E` para la persistencia y el efecto. La
interfaz se prueba porque **la capacidad que faltaba era la interfaz**; la sustitución de
permisos se prueba por API, que es donde vive.

Las aserciones de interfaz usan `getByRole` con nombre accesible —`lots:read`,
`operations:approve`— y nunca `toBeTruthy` sobre un localizador.

### Regresión

| | Antes | Después |
|---|---|---|
| Backend | 370 · 49 omitidas | **377 · 49 omitidas · 0 fallos** |
| E2E | 99/99 | **102/102** |
| `tsc` · `vitest` | — | **PASS · 61/61** |
| Paridad i18n | 866 = 866 | **876 = 876** — diez claves nuevas en ambos idiomas |

## 9. Veredicto

```
P-13 = CERTIFIED   ·   14 de 14 pasos
```
