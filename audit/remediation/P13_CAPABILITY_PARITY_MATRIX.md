# `P-13` · PARIDAD DE CAPACIDADES

Fase de análisis · 2026-09-06 · **la matriz que decide la dimensión real**

---

| Capacidad exigida | Backend | Frontend | Contrato | Alcanzable operativamente | Clasificación |
|---|:--:|:--:|:--:|:--:|---|
| Acceder con JWT | ✅ | ✅ | ✅ | **sí** | `COMPLETE` |
| Selector de idioma en el acceso | — | ✅ | — | sí | `COMPLETE` |
| Freno al ensayo de contraseñas | ✅ | — | — | sí | `COMPLETE` |
| Gestión de usuarios (alta, edición, estado, contraseña) | ✅ | ✅ | ✅ | **sí** | `COMPLETE` |
| Asignar rol a un usuario | ✅ | ✅ | ✅ | sí | `COMPLETE` |
| Aislamiento multiempresa | ✅ | ✅ | ✅ | sí | `COMPLETE` — `GA-REM-002` |
| Perfil y contraseña propia | ✅ | ✅ | ✅ | sí | `COMPLETE` — `GA-REM-012` |
| Auditoría de las acciones administrativas | ✅ | — | ✅ | sí | `COMPLETE` — `GA-REM-032` |
| **Listar y crear roles con permisos** | ✅ | ❌ | parcial | **no** | **`BACKEND_COMPLETE_UI_MISSING`** |
| **Editar los permisos de un rol** | ❌ | ❌ | ❌ | **no** | **`MISSING_PRODUCT_CAPABILITY`** |
| **Conocer el catálogo de permisos** | ❌ | ❌ | ❌ | **no** | **`MISSING_PRODUCT_CAPABILITY`** |
| **Desactivar un rol** | ✅ vía `PUT` | ❌ | ✅ | **no** | `BACKEND_COMPLETE_UI_MISSING` |
| Roles por compañía | — | — | — | — | `SYSTEM_MANAGED` — globales, sin fuente que lo cambie |
| ¿Quién puede conceder qué permiso? | — | — | — | — | **`REQUIREMENT_GAP` → `OD-05`** |

## La dimensión real

```
14 pasos de la cadena · PASS 10 · FAIL 4
Capacidades ausentes: 3 (no «pantallas de roles y de permisos»)
```

| Hallazgo | Qué es | Sev. |
|---|---|:--:|
| **`R-92`** | no existe superficie para administrar roles: sin ruta, sin pantalla y con el cliente de API a medias | **P1** |
| **`R-93`** | `RoleUpdate` no incluye permisos: un rol nace con los suyos y no puede cambiarlos nunca | P2 |
| **`R-94`** | no hay catálogo de permisos: una interfaz de roles tendría que adivinarlos | P2 |

`R-92` es **P1** porque `§3.1.3` es un submódulo normativo de prioridad **Alta** sin ninguna
superficie: un administrador no puede crear un rol desde el producto. `R-93` y `R-94` son P2:
sostienen la capacidad pero no la agotan.

## Lo que **no** es un hueco

| | Por qué |
|---|---|
| `UsersPage` | **funciona**: el `422` de `audit/06` está obsoleto |
| enforcement de permisos | `GA-REM-002` `CERTIFIED`; no se reimplementa |
| ausencia de `DELETE /roles` | la baja lógica va por `PUT`, coherente con todo el producto |
| roles globales | `docs/02 §3.1.3` sitúa el alcance en el **permiso**, no en el rol |

## Lo que exige decisión y no desarrollo

```
OD-05 · ¿puede un administrador conceder permisos que él mismo no posee?
```

Sin fuente normativa en `docs/`, `specs/` ni `audit/`. **No se inventa una política de
seguridad.** Detalle en `P13_BACKEND_CAPABILITY_MATRIX §4`.

El desarrollo de `R-92`, `R-93` y `R-94` **no depende** de esa decisión: la administración de
roles es necesaria en cualquiera de sus respuestas, y la restricción —si el propietario decide
que la haya— se añadiría después sobre la misma superficie.
