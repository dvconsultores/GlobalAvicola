# `P-13` · INVENTARIO DEL BACKEND

Fase de análisis · 2026-09-06

| Capacidad | Endpoint | Método | Esquema | Permiso | Inquilino | Auditoría | Pruebas |
|---|---|:--:|---|---|---|:--:|:--:|
| acceder | `/login` | `POST` | `LoginRequest` | — | — | **`LOGIN`** · **`LOGIN_FAILED`** | sí |
| renovar sesión | `/refresh` | `POST` | `RefreshRequest` | — | — | no exigida | sí |
| identidad actual | `/me` | `GET` | — | sesión | — | — | sí |
| cambiar de compañía | `/switch-company` | `POST` | `SwitchCompanyRequest` | Super Admin | — | — | sí |
| listar usuarios | `/users` | `GET` | — | `users:read` | filtrado | — | sí |
| crear usuario | `/users` | `POST` | `UserCreate` | `users:create` | hereda | — | sí |
| ver usuario | `/users/{id}` | `GET` | — | `users:read` | filtrado | — | sí |
| editar usuario | `/users/{id}` | `PUT` | `UserUpdate` | `users:update` | filtrado | — | sí |
| cambiar contraseña | `/users/{id}/password` | `POST` | `PasswordChangeRequest` | `users:update` | filtrado | — | sí (`GA-REM-012`) |
| desactivar usuario | `/users/{id}` | `DELETE` | — | `users:delete` | filtrado | — | sí |
| listar roles | `/roles` | `GET` | — | `users:read` | **global** | — | sí |
| crear rol **con permisos** | `/roles` | `POST` | `RoleCreate` + `PermissionCreate[]` | `users:create` | **global** | **`PERMISSION_CHANGE`** | sí |
| editar rol | `/roles/{id}` | `PUT` | `RoleUpdate` | `users:update` | **global** | **`PERMISSION_CHANGE`** | sí |
| **editar los permisos de un rol** | — | — | — | — | — | — | **no existe** |
| **catálogo de permisos** | — | — | — | — | — | — | **no existe** |
| **desactivar rol** | `/roles/{id}` | `PUT` | `RoleUpdate.is_active` | `users:update` | global | sí | existe **por `PUT`**, no por `DELETE` |

## 1. Lo que falta en el backend

**`RoleUpdate` no incluye permisos.**

```python
class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
```

Un rol nace con sus permisos y **no puede cambiarlos nunca**. `docs/02 §3.1.3` pide «CRUD de
roles **con permisos granulares**»: si los permisos no se pueden editar, el CRUD está a medias.

**No hay catálogo de permisos.** Ningún endpoint expone qué módulos y acciones existen, de
modo que una interfaz de roles tendría que adivinarlos o repetirlos a mano —y quedarían
desincronizados el día que se añada un módulo—.

## 2. La baja de rol existe, pero por otra puerta

No hay `DELETE /roles/{id}`, pero `RoleUpdate.is_active` permite la baja lógica por `PUT`. Es
coherente con el resto del producto, que nunca borra físicamente. **No es un hueco**; se anota
para que nadie añada un `DELETE` por simetría.

## 3. El enforcement no se toca

`GA-REM-002` está `CERTIFIED`: *«el enforcement es completo y el catálogo de roles es coherente
con él»*. `P-13` **reutiliza** esa infraestructura y no la reimplementa. Lo que falta es la
**administración**, que es otra cosa que la aplicación de la regla.

## 4. Dos políticas sin fuente normativa

**Alcance de los roles.** `Role.company_id` existe y es nulable, pero `create_role` nunca lo
fija y `get_roles` no filtra: en la práctica **todos los roles son globales**. `docs/02 §3.1.3`
sitúa el alcance en el **permiso** (`scope_type`: `all` · `company` · `farm`), no en el rol.

No hay fuente que diga que los roles deban ser por compañía. **No se introduce `company_id`
por intuición** (`§36` del encargo): se deja como está y se documenta.

**Escalada de privilegios.** Nada impide que quien tiene `users:create` cree un rol con
`module="*"`, `scope_type="all"` y se lo asigne. Buscada la regla en `docs/`, `specs/` y
`audit/`: **no existe**.

```
OD-05 · ¿puede un administrador conceder permisos que él mismo no posee?
        Sin fuente normativa. OWNER_DECISION_REQUIRED.
```

No se inventa una política de seguridad. En la práctica el permiso `users:create` solo lo
traen las semillas del Super Admin, así que hoy el camino no está abierto a nadie más — pero
eso es una propiedad de las semillas, no una garantía, como ya ocurrió en `R-60`.
