# `P-13` · AUTENTICACIÓN Y GESTIÓN DE USUARIOS — CADENA COMPLETA

`docs/02 §3.1` · 2026-09-06 · fase de análisis

---

## 1. Nombre normativo

La matriz lo llamaba «Usuarios, roles y permisos». La spec lo llama:

```
MÓDULO 1 · Autenticación y Gestión de Usuarios      (docs/02 §3.1)
```

Es **más ancho** que roles y permisos: incluye el acceso, la gestión de usuarios, la de roles,
el aislamiento multiempresa y el perfil. Se usa el nombre normativo.

> `docs/02` numera **dos** apartados como `§3.1.4` —aislamiento y perfil—. Defecto documental
> menor, sin efecto funcional; se anota y no se corrige aquí.

## 2. Actores

| Actor | De dónde sale | Qué puede |
|---|---|---|
| Super Admin | `§3.1.4` — rol con `module="*"`, `scope_type="all"` | todas las compañías |
| Administrador | `§3.1.2` — «Permisos: **solo administradores**» | usuarios y roles, con `users:*` |
| Titular de la cuenta | `§3.1.4bis` | su propio perfil y contraseña |

## 3. La cadena

| # | Paso | Actor | Acción | Estado esperado | Requisito | Evidencia |
|:--:|---|---|---|---|---|:--:|
| 1 | Acceder | cualquiera | login con usuario y contraseña | sesión con `company_id` y `role_id` en el token | `§3.1.1` | **PASS** |
| 2 | Selector de idioma en el acceso | cualquiera | — | visible en la pantalla de login | `§3.1.1` | **PASS** |
| 3 | Freno al ensayo de contraseñas | — | N intentos | bloqueo temporal | `§3.1.1` | **PASS** — `@rate_limit("5/minute")` |
| 4 | Alta de usuario | administrador | crear con rol y empresa | usuario operativo | `§3.1.2` | **PASS** |
| 5 | Edición y estado del usuario | administrador | editar, activar, desactivar | estado nuevo | `§3.1.2` | **PASS** |
| 6 | Asignar rol a un usuario | administrador | elegir rol | usuario con el rol | `§3.1.2` | **PASS** |
| 7 | **Alta de rol con permisos granulares** | administrador | crear rol y sus permisos | rol utilizable | `§3.1.3` | **FAIL** — sin interfaz |
| 8 | **Editar los permisos de un rol** | administrador | añadir o quitar permisos | conjunto nuevo | `§3.1.3` | **FAIL** — el backend no lo admite |
| 9 | **Conocer los permisos disponibles** | administrador | consultar el catálogo | módulos y acciones | `§3.1.3` | **FAIL** — no hay endpoint |
| 10 | Desactivar un rol | administrador | baja lógica | rol inactivo | `§3.1.3` | **PASS** por API (`is_active` en `PUT`) · **FAIL** sin interfaz |
| 11 | Aislamiento multiempresa | usuario regular | consultar | solo su compañía | `§3.1.4` | **PASS** — `GA-REM-002` |
| 12 | Perfil y contraseña | titular | cambiar | contraseña nueva | `§3.1.4bis` | **PASS** — `GA-REM-012` |
| 13 | Las acciones administrativas se auditan | — | crear o editar rol | `PERMISSION_CHANGE` | `docs/02 §3.11` | **PASS** — `GA-REM-032` |
| 14 | El permiso concedido surte efecto | usuario destino | operar | puede lo concedido, no lo demás | `§3.1.3` + `GA-REM-002` | **PASS** por API |

```
14 pasos · PASS 10 · FAIL 4
```

## 4. Lo que ya estaba y `audit/06` daba por roto

| `audit/06` decía | Hoy |
|---|---|
| «Usuarios: pantalla **rota** (`limit=200` → 422)» | **obsoleto** — `UsersPage` llama a `/users` sin `limit` y crea, edita, cambia contraseña y desactiva |
| «Permisos: modelo completo, sin pantalla y **sin enforcement**» | el enforcement lo certificó `GA-REM-002`; lo que falta es la pantalla |
| «Roles: 3 endpoints, sin pantalla» | **confirmado**, y hay dos huecos más de backend (§8-9) |

Quinta vez que `audit/06` resulta obsoleto en parte. Se usa como pista, nunca como verdad.
