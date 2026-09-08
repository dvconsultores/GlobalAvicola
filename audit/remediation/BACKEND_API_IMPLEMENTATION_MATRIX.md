# API DE BACKEND — COBERTURA POR DIMENSIÓN

Auditoría maestra · 2026-09-08 · **solo lectura** · 207 rutas bajo `/api`

```
LAS TRES GUARDAS DE ARRANQUE, VERIFICADAS EN ESTA AUDITORÍA
authorization_coverage   207/207 declaran permiso        `GA-REM-002 AC08`
route_scope              207/207 declaran alcance de unidad  `GA-REM-040 AC-C15`
transaction              207/207 dentro de la frontera        `GA-REM-026 AC11`
```

Ninguna ruta se sirve sin permiso, sin clasificación de unidad ni fuera de transacción. Eso es
sólido y no está en cuestión. **Lo que ninguna guarda vigila es el filtro de empresa**, y ahí
están las dos fugas de esta auditoría.

---

## 1. Las superficies auditadas en profundidad

| Ruta | Spec | Permiso | Alcance de empresa | Módulo | Unidad | `response_model` | Consumidor | Estado |
|---|---|---|:--:|:--:|:--:|:--:|---|---|
| `GET /users` | `02 §3.1.2` | `users:read` | **NINGUNO** | — | — | sí | `UsersPage` | **`CONTRADICTED`** `F-A` `P0` |
| `GET /users/{id}` | `02 §3.1.2` | `users:read` | **ninguno** | — | — | sí | `UsersPage` | **`CONTRADICTED`** `F-A` |
| `POST /users` | `02 §3.1.2` | `users:create` | cliente elige `company_id` | — | — | sí | `UsersPage` | **`PARTIAL`** `F-G` |
| `PUT /users/{id}` | `02 §3.1.2` | `users:update` | **ninguno** | — | — | sí | `UsersPage` | **`CONTRADICTED`** `F-A` |
| `GET /masters/companies` | `02 §3.2.1` | `masters:read` | **no-op** — el modelo no tiene `company_id` | — | `CONTROL` | sí | `UsersPage` `MasterListPage` | **`CONTRADICTED`** `F-B` `P0` |
| `POST·PUT·DELETE /masters/companies` | `02 §3.2.1` | `masters:*` | no-op | — | `CONTROL` | sí | `MasterListPage` | `COMPLETE` según spec · ver `F-F` |
| `GET·POST·PUT·DELETE /masters/farms` | `02 §3.2.1` | `masters:*` | sí | — | `MULTI_UNIDAD` | sí | `MasterListPage` | `COMPLETE` según spec · ver `F-F` |
| resto de los 22 maestros | `02 §3.2.1` | `masters:*` | sí, salvo sin empresa | — | clasificado | sí | `MasterListPage` | `COMPLETE` · ver `F-C` |
| `/lots/*` | `02 §3.4` | `lots:*` | sí | — | fase 3 | sí | `Lot*Page` | `COMPLETE` |
| `/operations/*` | `02 §3.4` | `operations:*` | sí | — | fases 3 y 6 | sí | `Operation*Page` | `COMPLETE` |
| `/review/*` `/approvals/*` | `12` | `review:*` `approvals:*` | sí | — | fase 3 | sí | `Review*` `ApprovalPanel` | `COMPLETE` |
| `/reports/*` `/dashboard/*` | `02 §3.5-3.6` | `reports:read` `dashboard:read` | sí | — | fase 4 | sí | `Reports*` `Dashboard` | `COMPLETE` |
| `/audit/*` | `13` | `audit:read` | sí | — | `CORE` | sí | `AuditPage` | `COMPLETE` |
| `/sap/*` (10 rutas) | `10` | `sap:read` `sap:send_sap` | sí | — | excepción `OD-12` | **1 de 10** | `SapManagerPage` | `PARTIAL` · `R-112` |
| `/business-units` · `/users/{id}/business-units` (6) | `GA-REM-040` fase 7 | `business_units:*` | sí | — | `CONTROL` | sí | **ninguno** | **`BACKEND_ONLY`** — fase 9 |
| `/switch-company` | `OD-11` | autenticado | resuelve | — | `CORE` | sí | **ninguno** | **`BACKEND_ONLY`** — «(futuro)» en `02 §3.1.4` |

---

## 2. `F-A` · el listado de usuarios no filtra por empresa · `P0`

```python
async def get_users(self, skip=0, limit=20, search="") -> list[UserRead]:
    query = select(User)                     # ← sin filtro de empresa
    if search: ...
    query = query.offset(skip).limit(limit).order_by(User.id)
```

`docs/02 §3.1.4`, que la propia spec marca **CRÍTICO**, dice: *«Usuarios regulares SOLO ven
datos de su compañía (`WHERE company_id = ?` en **todas** las queries)»*.

`get_users`, `get_user` y `update_user` no lo aplican. Un actor con `users:read` que no sea
Super Administrador enumera a los usuarios de **todas** las empresas: nombre, apellido, correo,
teléfono, rol y empresa.

```
¿Hay test que lo cubra?      NO — cero pruebas de aislamiento sobre `/users`
¿Estaba registrado?          NO — sin entrada previa en el backlog
¿Lo detecta alguna guarda?   NO — ninguna guarda vigila el filtro de empresa
```

**Por qué no saltó antes.** `users:read` figura en `SOLO_SUPER_ADMIN`, así que en las semillas
solo el Super Administrador —que legítimamente ve todo— alcanza estas rutas. El defecto está
latente: se activa el día que un cliente cree un rol de administración con `users:read`, que es
exactamente lo que el producto invita a hacer desde `/roles`.

## 3. `F-B` · el listado de empresas no acota, y expone `sap_config` · `P0`

```python
if hasattr(self.model, "company_id"):
    query = query.where(self.model.company_id == self.user_company_id)
```

`Company` **no tiene** `company_id` —su clave es `id`—, de modo que la condición no se cumple
nunca y la consulta sale sin acotar. `masters:read` lo tienen los cinco roles sembrados, así que
**cualquier usuario autenticado lista todas las empresas** con `tax_id`, `country`, `currency`,
`approval_levels` y **`sap_config`**, que `CompanyRead` expone entero.

`docs/03-domain-model.md §686` decía «la mayoría de entidades tienen `company_id`». `Company` es
justamente la que no puede tenerlo, y el filtro se escribió asumiendo que sí.

No he podido inspeccionar qué guarda hoy `sap_config` en la base desplegada —no es alcanzable
desde aquí—, así que la severidad se declara por lo que el esquema permite: es un `JSON` libre
descrito en `02 §3.2.1` como «configuración SAP» de la empresa.

## 4. `F-C` · el usuario sin empresa no se filtra · `P0`

```python
if not self.user_company_id:
    return query        # No company assigned — return empty or filter by id
```

El propio comentario no sabe qué quería hacer. Un usuario **sin empresa y sin ser Super
Administrador** recibe la consulta **sin filtro**: ve los maestros de todas las empresas. Es un
`fail-open` en el mismo sitio donde `GA-REM-040` puso `fail-closed` para las unidades
(`unidades_efectivas` devuelve `[]`, nunca «toda la empresa»).

Hoy las semillas no crean usuarios así, salvo el Super Administrador. `POST /users` **sí**
permite crearlos: `company_id` es `Optional`.

## 5. `F-G` · el cliente elige la empresa al crear un usuario · `P1`

```python
# router
current_user: dict = Depends(require_permission("users", "create")),
):
    return await AuthService(db).create_user(data)      # ← current_user NO se pasa

# servicio
company_id=data.company_id,                             # ← tal cual viene del cliente
```

El router resuelve el actor y **lo descarta**. `create_user` no recibe con qué comparar, así que
`company_id` entra sin validar: un administrador de la empresa A crea usuarios en la B.

Contrasta con lo que `GA-REM-040` fase 7 hizo la semana pasada en la misma casa: allí la empresa
**no se recibe, se resuelve**, y «crear en otra empresa» no es expresable. La regla existe y
está probada — en el módulo de al lado.

## 6. `F-H` · `update_user` permite tomar cualquier cuenta de cualquier empresa · `P0`

```python
async def update_user(self, user_id: int, data: UserUpdate) -> UserRead:
    result = await self.db.execute(select(User).where(User.id == user_id))   # sin empresa
    ...
    for key, value in update_data.items():
        setattr(user, key, value)                                            # role_id incluido
```

Dos ausencias que se multiplican:

```
sin filtro de empresa    el objetivo puede ser de otro inquilino
`role_id` es editable    y `UserUpdate` lo acepta
```

Un actor con `users:update` puede asignarle a **cualquier** usuario de **cualquier** empresa el
rol que quiera, incluido uno con el comodín `("*", ...)` que otorga Super Administrador. Es
escalada de privilegios que cruza inquilinos, y no hace falta ningún truco: es la ruta
documentada de edición de usuario.

`GA-REM-034` cerró esto para los **roles** —un rol no podía cambiar sus permisos y se arregló—,
y `GA-REM-002 AC12` lo cerró para los sub-recursos de lote. La misma lección no llegó a
`/users`.

### Por qué ninguno de los tres saltó antes

`users:read`, `users:create` y `users:update` constan en `SOLO_SUPER_ADMIN`: **ningún rol
sembrado los concede**, y el Super Administrador ve y edita todo por definición. Los defectos son
por tanto **latentes en las semillas** y **activos en cuanto un cliente cree su rol de
administración**, que es justo lo que `docs/02 §3.1.2` describe («Permisos: solo
administradores») y lo que `/roles` invita a hacer.

Que estén latentes no los hace menores: `R-113` —abierto la semana pasada— pregunta precisamente
quién debe administrar en una avícola. La respuesta a `R-113` es lo que activa `F-A`, `F-G` y
`F-H` el mismo día.
