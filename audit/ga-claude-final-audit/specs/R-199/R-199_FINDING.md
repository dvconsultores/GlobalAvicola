# R-199 · REGISTRO DE HALLAZGO — FABRICACIÓN DE AUTORIDAD GLOBAL DESDE UN ROL DE INQUILINO

| Campo | Valor |
|---|---|
| **ID canónico** | `R-199` (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo `R-189`) |
| **Título** | Un actor de empresa con `users:create`/`users:update` fabrica un rol de inquilino con `{"module":"*","scope_type":"all"}`, lo asigna, y el usuario resultante es `is_super_admin` con `switch-company` a cualquier empresa |
| **Clase (§9)** | `SECURITY` · subclase RBAC / escalada de privilegio / cruce de inquilino |
| **Prioridad** | **P1** (P0 condicional: si un rol de inquilino ya tiene `users:create` + `users:update`, que es exactamente el «Administrador de empresa» que `GA-REM-034`/`OD-13` prevé) |
| **Origen** | `GAP-01` del informe `D_security_tx.md` (§A.4, §E.6, tabla de candidatos); absorbe la parte de `GAP-16` que comparte causa raíz (`PermissionCreate` sin validación de catálogo) |
| **Procesos** | `P-13` (usuarios y roles); transversal a todo el producto por el efecto (`is_super_admin`) |
| **Bloquea SAP** | **SÍ** (escalada de autoridad desde una superficie de inquilino; contradice la compuerta RBAC = `FAIL` del informe final de seguridad §3.4) |
| **Auditoría** | GA-CLAUDE final pre-SAP · 2026-09-13 · HEAD `c0b4afc` · runtime `https://avicola.globaldv.net` (no sondado para este hallazgo: exigiría crear un rol envenenado en producción; se difiere a C3 con actores desechables) |
| **Estado** | `SPEC_READY` · sin código · sin `GA-REM` asignado (siguiente libre: `GA-REM-043`) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-199/` (completo, 6 ficheros) |

## 1. Descripción

`OD-13.c` fija que «se prohíbe fabricar autoridad global desde una superficie de empresa» y que el rol que confiere autoridad global es, literalmente, `module="*"` con `scope_type="all"` (`docs/02 §3.1.4`). `R-117` cerró **una** de las dos puertas: asignar la **plantilla global existente** (`Role.company_id IS NULL` con el comodín) desde una empresa responde `403` (`test_role_tenancy.py::test_r06_la_autoridad_global_no_se_reparte_desde_una_empresa`).

La otra puerta sigue abierta: el actor de empresa **crea su propio rol de inquilino** con el comodín. Nada valida el contenido de `permissions`; `_rol_asignable` considera el rol asignable por ser de su empresa; y `get_current_user` concede `is_super_admin` por el permiso **sin mirar `Role.company_id`**. El usuario así preparado obtiene `switch-company` a cualquier empresa activa y toda superficie de inquilino se le abre en la empresa elegida.

## 2. Evidencia de código (HEAD `c0b4afc`)

| # | Sitio | Qué hace hoy | Por qué es el hueco |
|---|---|---|---|
| E1 | `backend/app/auth/service.py:585-619` `create_role` | Crea `Role(company_id=empresa)` para el actor de empresa y persiste cada `perm_data` tal cual (`module`, `action`, `scope_type`, `scope_id`) | **No valida el contenido**: acepta `("*", "read", "all")` en un rol de inquilino |
| E2 | `backend/app/auth/service.py:621-658` `update_role` | Sustituye el conjunto entero de permisos cuando viaja (`sa_delete` + `add`) | Mismo defecto sobre un rol propio ya existente |
| E3 | `backend/app/auth/service.py:116-142` `_rol_asignable` | Para `rol.company_id IS NULL` consulta `_es_autoridad_global`; para rol de inquilino devuelve `rol.company_id == empresa` (línea `:142`) | La rama de inquilino **no** pregunta si el rol confiere autoridad global |
| E4 | `backend/app/auth/security.py:113-120` `get_current_user` | `if perm.module == "*" and perm.scope_type == "all": is_super_admin = True` | No exige `Role.company_id IS NULL`: un rol de inquilino con el comodín produce autoridad global |
| E5 | `backend/app/auth/service.py:225-239` `_es_super_admin` (camino de renovación) | Misma señal, sin condición sobre `Role.company_id` | La renovación honra un `company_id` reclamado ajeno para el usuario envenenado (`:276-280`) |
| E6 | `backend/app/auth/service.py:507-540` `switch_company` | `if not is_super_admin: 403`; con `is_super_admin` emite tokens con la empresa elegida | Es la superficie que convierte la escalada en cruce de inquilino |
| E7 | `backend/app/auth/schemas.py:201-205` `PermissionCreate` | `module: str`, `action: str`, `scope_type: str = "all"` sin validación | `GAP-16`: módulo arbitrario aceptado; acción inválida → `PermissionAction(...)` lanza `ValueError` → `500` (`service.py:602`, `:647`) |
| E8 | `backend/app/auth/router.py:185-201` | `POST /roles` exige `users:create`; `PUT /roles/{id}` exige `users:update` | Las capacidades necesarias son las del administrador de empresa previsto por `GA-REM-034` |
| E9 | `backend/app/auth/security.py:170-178` `get_company_filter` | Devuelve `None` («sin filtro») para `is_super_admin`; **sin consumidores** (grep) pero re-exportado en `dependencies.py:2` | Código muerto que documenta la doctrina anterior a `OD-14`; residuo de `GAP-16` |
| E10 | `frontend/src/pages/users/RolesPage.tsx:57,70` | Cada permiso marcado viaja con `scope_type: 'all'`; los módulos salen del catálogo (`/roles/permissions-catalog`) | La UI no puede emitir `"*"` (no está en `AuthService.MODULOS`), pero **sí** envía `scope_type='all'` para todo permiso ordinario: la corrección no puede rechazar `scope_type='all'` en general, sólo el par `("*", all)` |

## 3. Cadena de explotación (verificada por lectura; RED-01…05 la fijan como prueba)

```
Actor: usuario de la empresa A con rol de inquilino que tiene users:create + users:update
  1. POST /api/v1/roles {"name":"Coordinación","permissions":[{"module":"*","action":"read","scope_type":"all"}]}
       → 201 · Role(company_id=A) con Permission("*","read","all")                       (E1)
  2. PUT  /api/v1/users/{u}  {"role_id": <rol nuevo>}   (u = él mismo u otro usuario de A)
       → 200 · _rol_asignable: rol.company_id == A ⇒ asignable                              (E3)
  3. GET  /api/v1/me   (como u)
       → is_super_admin: true                                                               (E4)
  4. POST /api/v1/switch-company {"company_id": B}
       → 200 · tokens con company_id=B                                                       (E6)
  5. GET /api/v1/users · /lots · /operations · /masters/* … en B
       → la empresa efectiva es B y RBAC pasa siempre (tiene_permiso: is_super_admin ⇒ True)
```

Precondición real: sólo la capacidad `users:create` (paso 1) o `users:update` (pasos 2 y variante «editar rol propio», E2). En la semilla actual ambas son exclusivas del Super Admin; el actor `rol_admin_a` de `test_role_tenancy.py:67,74-77` (`users:read/create/update/delete`, `scope_type="company"`) es exactamente el administrador de empresa previsto, y con él la cadena completa es ejecutable hoy.

## 4. Cobertura de pruebas existente

| Prueba | Qué cubre | Qué no cubre |
|---|---|---|
| `tests/test_role_tenancy.py::test_r06_la_autoridad_global_no_se_reparte_desde_una_empresa` | asignar la **plantilla** global (`rol_global`, `company_id NULL`) → `403` | crear/editar un rol de **inquilino** con el comodín; asignarlo; efecto en `/me` y `switch-company` |
| `tests/test_role_tenancy.py::test_r02_*` | el rol nace en la empresa del actor | su contenido |
| `tests/test_rbac.py::test_los_permisos_de_super_admin_no_son_una_lista_creciente` | tope de permisos exclusivos de Super Admin en la semilla | el runtime del catálogo |
| `tests/test_session_payload.py` | `/me` compone `is_super_admin` de la capacidad | que la capacidad exija rol de sistema |

**Ningún test recorre el camino real.** El informe de seguridad lo marca `NO TEST` (§A.4, §E.6).

## 5. Deduplicación (§48)

| Registro | Relación | Conclusión |
|---|---|---|
| `R-117` (cerrado) | «un administrador de A convertía a un usuario de B en Super Administrador por `PUT /users`» — resolvió la **localización del objetivo** y la asignación de la plantilla global | no cubre la fabricación del rol |
| `R-121` / `OD-13` (cerrado, decisión vigente) | fija la norma (`OD-13.c`, `AC-R06`) | esta brecha la contradice; no la reabre |
| `GA-REM-002 AC15` | «asignar autoridad global exige autoridad global» | misma norma, distinto camino |
| `GA-REM-034` | CRUD de roles con permisos granulares; `AC01` catálogo; `AC02` sustitución de permisos | introdujo la superficie sin la validación |
| `R-93` / `R-94` (cerrados) | `RoleUpdate.permissions`; catálogo | ídem |
| `GAP-16` (informe D) | `PermissionCreate` sin validación | **se absorbe aquí** en su parte de catálogo de permisos (`skip ge=0` de `pending_classification` y `get_company_filter` quedan: el segundo se retira aquí como higiene, el primero pertenece a `R-220`) |
| `REMEDIATION_BACKLOG.md` (grep `fabricar autoridad`, `comodín`, `("*"`) | sólo la nota de `R-128` («no puede fabricar autoridad global») como **afirmación**, no como control | **NUEVO** |

## 6. Veredicto

`NUEVO` · `P1` · `BLOQUEA` · backend-only · sin migración · sin permiso nuevo · sin endpoint nuevo · paquete completo.
