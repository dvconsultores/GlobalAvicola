# `P-13` · INVENTARIO DEL FRONTEND

Fase de análisis · 2026-09-06

Comprobado por ruta, componente **y** cliente de API por separado (`§22` y `§23` del
encargo): una capacidad puede vivir en un modal sin pantalla propia, y una ruta puede existir
sin menú.

| Capacidad | Ruta | Página | Componente | Cliente de API | Navegación | Guarda | Prueba |
|---|---|---|---|---|:--:|---|:--:|
| acceder | `/login` | `LoginPage` | formulario + selector de idioma | `authService.login` | pública | — | `UI_E2E` |
| perfil y contraseña | `/profile` | `ProfilePage` | — | `changePassword` | sí | sesión | sí |
| **listar usuarios** | `/users` | `UsersPage` | tabla | `api.get('/users')` | sí | `WebOnlyRoute` | `UI_E2E` |
| **crear usuario** | `/users` | ídem | modal | `api.post('/users')` | — | ídem | sí |
| **editar usuario** | `/users` | ídem | modal | `api.put` | — | ídem | sí |
| **cambiar contraseña de otro** | `/users` | ídem | modal | `api.post('/users/{id}/password')` | — | ídem | sí |
| **activar / desactivar usuario** | `/users` | ídem | interruptor | `api.put` · `api.delete` | — | ídem | sí |
| **asignar rol a un usuario** | `/users` | ídem | desplegable alimentado por `/roles` | `api.get('/roles')` | — | ídem | sí |
| **listar roles** | **ninguna** | ❌ | ❌ | **`authService.listRoles` existe** | no | — | no |
| **crear rol con permisos** | **ninguna** | ❌ | ❌ | `createRole` existe pero **no envía permisos** | no | — | no |
| **editar rol** | **ninguna** | ❌ | ❌ | `updateRole` existe | no | — | no |
| **editar permisos de un rol** | **ninguna** | ❌ | ❌ | ❌ | no | — | no |
| **desactivar rol** | **ninguna** | ❌ | ❌ | vía `updateRole` | no | — | no |

## 1. La gestión de usuarios está completa

`audit/06` la daba por **rota** —«`limit=200` → 422 aborta el `Promise.all`»—. Verificado en
el código de hoy: `UsersPage:21` llama a `/users` **sin `limit`**, y la pantalla crea, edita,
cambia contraseña, activa, desactiva y asigna rol.

El hueco que el audit describía **ya no existe**.

## 2. La gestión de roles no existe, pero el cliente sí

`auth.service.ts:57-65` ya declara `listRoles`, `createRole` y `updateRole`. Lo que falta es
la **pantalla**: no hay ruta en `App.tsx`, no hay componente en `pages/`, y nada los invoca
salvo `UsersPage`, que usa `listRoles` únicamente para llenar un desplegable.

Y `createRole` está incompleto: su firma es `{ name, description }` — **no envía permisos**,
que es justo lo que `§3.1.3` pide administrar.

```
Clasificación · MISSING_PRODUCT_CAPABILITY
                (no «bug de frontend»: el backend cumple y la superficie no existe)
```

## 3. Verificado en los dos lados

| | Roles |
|---|---|
| ruta en `App.tsx` | **no** |
| componente en `pages/` | **no** |
| cliente de API | **sí**, parcial |
| endpoint backend | **sí** — listar, crear con permisos, editar |
| enlace de navegación | irrelevante sin ruta |

No es «no lo encontré»: es que `App.tsx` no declara ninguna ruta de roles y `pages/` no
contiene ningún componente que los gestione.
