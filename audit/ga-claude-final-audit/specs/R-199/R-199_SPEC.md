# R-199 · SPEC — LA AUTORIDAD GLOBAL NO SE FABRICA DESDE UN ROL DE INQUILINO

| Campo | Valor |
|---|---|
| **ID** | `R-199` · `SECURITY REMEDIATION SPEC` · P1 · `SPEC_READY` |
| **Decisiones que preserva** | `OD-13` (a…e) · `OD-14` (a…d) · `OD-15` · `OD-16` · `OD-23` |
| **AC que refuerza** | `OD-13 AC-R06` · `GA-REM-002 AC15` · `GA-REM-040 AC-F05` (nada por nombre de rol) |
| **Dependencias** | ninguna de código; `GA-GOV-03` para que la certificación sea reproducible |
| **Vecinos** | `R-200` (sesión) · `R-202` (contraseña) · `R-201` (SAP) — mismo bloque de seguridad, sin acoplamiento de código |
| **GA-REM** | sin asignar (siguiente libre `GA-REM-043`) |

---

## 1. Contexto

`OD-13.b`: un rol es **de sistema** (`company_id NULL`, plantilla de producto) o **de inquilino** (`company_id = X`). `OD-13.c`: el rol que confiere autoridad global es `("*", scope_type="all")` y **sólo la autoridad global lo asigna**; «se prohíbe fabricar autoridad global desde una superficie de empresa». `R-117` cerró la asignación de la plantilla global desde una empresa; la creación y edición de roles (`GA-REM-034`) quedaron sin la misma frontera. La capacidad `is_super_admin` se deriva de la tupla sin comprobar que el rol sea de sistema.

## 2. Evidencia

Ver `R-199_FINDING.md §2-3` (E1…E10). Resumen: `auth/service.py:585-619`, `:621-658` (sin validación de permisos), `:116-142` (`_rol_asignable` rama `:142`), `:225-239` (`_es_super_admin`), `:507-540` (`switch_company`); `auth/security.py:113-120` (`is_super_admin` sin `Role.company_id`); `auth/schemas.py:201-205` (`PermissionCreate` libre); `security.py:170-178` (`get_company_filter`, muerto). Sin test del camino (informe D §A.4).

## 3. Causa raíz

Tres omisiones de la misma regla, en tres capas:

1. **Escritura**: `create_role`/`update_role` aceptan cualquier tupla de permiso (`GAP-16`), incluida la que `docs/02 §3.1.4` define como autoridad global.
2. **Asignación**: `_rol_asignable` aplica `_es_autoridad_global` sólo a las plantillas; asume que un rol de inquilino no puede llevar el comodín, y nada lo garantiza.
3. **Resolución de sesión**: `get_current_user` y `_es_super_admin` calculan la capacidad global por el permiso, no por el permiso **en un rol de sistema**.

La invariante que falta es de **modelo**, no de actor: *un rol de inquilino nunca porta `("*", all)`*, y *la autoridad global sólo se computa desde un rol de sistema*.

## 4. Impacto de negocio

- Cruce total de inquilino por un actor administrativo ordinario (usuarios, lotes, eventos, maestros, revisión, SAP de cualquier empresa activa).
- Invalida las compuertas «Inquilino», «RBAC» y «Cruce de empresa» del informe final de seguridad y, con ellas, la certificación de acceso por unidad (`GA-REM-040 §23`).
- Sin rastro específico en `P-09`: el rol se audita como `PERMISSION_CHANGE` ordinario y el cambio de contexto como `CONTEXT_SWITCHED`, indistinguibles de un uso legítimo.

## 5. Comportamiento actual

| Paso | Actor de empresa (`users:create`/`users:update`) | Resultado |
|---|---|---|
| `POST /roles` con `("*","read","all")` | aceptado | `201`, `Role(company_id=A)` con el comodín |
| `PUT /roles/{propio}` con `("*",…,"all")` | aceptado | `200` |
| `PUT /users/{u}` `{"role_id": <envenenado>}` | aceptado | `200` (`_rol_asignable:142`) |
| `GET /me` (como `u`) | | `is_super_admin: true` |
| `POST /switch-company {B}` | | `200`, tokens en B |
| `POST /refresh` con `company_id=B` reclamado | | honrado (`_es_super_admin`) |
| `POST /roles` con `module="hacking"` | aceptado | `201` |
| `POST /roles` con `action="fly"` | `ValueError` | `500` |

## 6. Comportamiento esperado

```
ROL DE INQUILINO      nunca porta ("*", scope_type="all")            → 403 al crear o editar
CATÁLOGO              module ∈ MODULOS ∪ {"*"} · action ∈ PermissionAction
                      scope_type ∈ {all, company, farm}               → 422 fuera de catálogo
ASIGNAR               ningún rol que confiera autoridad global se asigna desde una empresa,
                      sea plantilla o rol de inquilino                → 403 (ya para plantilla)
SESIÓN                is_super_admin ⇔ ("*", all) EN UN ROL DE SISTEMA (Role.company_id IS NULL)
                      — en get_current_user y en la renovación
DENEGACIÓN            0 filas escritas · 0 auditoría de éxito · registro del intento (C-05)
```

El actor de empresa **no pierde nada**: sigue creando roles con cualquier combinación de módulos del catálogo y acciones, con `scope_type='all'` incluido (es lo que `RolesPage.tsx:57,70` envía hoy), y sigue asignando plantillas ordinarias (`test_r05_la_plantilla_de_sistema_ordinaria_si_se_asigna`).

## 7. Alcance

1. Validación del contenido de `permissions` en `create_role` y `update_role` (catálogo + prohibición del par global en rol de inquilino).
2. `_rol_asignable`: `_es_autoridad_global` aplicado también a roles de inquilino.
3. `get_current_user` y `_es_super_admin`: la capacidad global exige `Role.company_id IS NULL`.
4. Registro del intento denegado según `C-05`.
5. Inventario de solo lectura de roles de inquilino ya envenenados (C3) — `C-06`.
6. Higiene: retirada de `get_company_filter` (muerto, fail-open) — `C-07`.
7. Pruebas RED→GREEN, certificación runtime, actualización del registro.

## 8. Fuera de alcance

- Interfaz de gestión de Super Administradores (`OD-13 §6`).
- Reinterpretar `scope_type` (`company`/`farm`) como filtro de datos: hoy no lo usa nadie salvo la detección del comodín; queda como observación (`C-03`).
- `pending_classification.skip` sin `ge=0` (parte restante de `GAP-16`): `R-220`.
- Logout/rotación de refresh (`GA-REM-003`, `R-200`).
- Reclasificación de los seis roles sembrados (`OD-13 §6`).

## 9. Impacto frontend

**Sin cambio funcional.** `RolesPage.tsx` no puede emitir `module="*"` (el catálogo no lo contiene) y ya envía `scope_type:'all'` para permisos ordinarios, que siguen aceptándose. Los nuevos `403`/`422` llegan por el `catch` existente (`alert(detail)`); su rendering legible es de `R-215`. Sin cambios de i18n.

## 10. Impacto backend

| Fichero | Cambio |
|---|---|
| `backend/app/auth/service.py` | `_validar_permisos(permisos, *, rol_de_inquilino: bool)` (nuevo helper privado) invocado en `create_role` **antes** de `db.add` y en `update_role` **antes** de `sa_delete`; `_rol_asignable` rama `:142` → `rol.company_id == empresa and not await self._es_autoridad_global(role_id)`; `_es_super_admin` añade `Role.company_id.is_(None)`; registro del intento (`C-05`) |
| `backend/app/auth/security.py` | `get_current_user`: `is_super_admin` sólo si `user.role.company_id is None`; retirada de `get_company_filter` (`C-07`) |
| `backend/app/auth/schemas.py` | `PermissionCreate.action` validado contra `PermissionAction`, `scope_type` contra `Literal["all","company","farm"]` (422 en esquema); `module` se valida en el servicio contra `AuthService.MODULOS ∪ {"*"}` (evita import circular) |
| `backend/app/dependencies.py` | retirar la re-exportación de `get_company_filter` (`C-07`) |

Sin migración, sin endpoint nuevo, sin permiso nuevo.

## 11. Contrato frontend↔backend

| Ruta | Antes | Después |
|---|---|---|
| `POST /api/v1/roles` (actor de empresa, par global) | `201` | `403` `{"detail": "La autoridad global no se concede desde la administración de una empresa"}` |
| `PUT /api/v1/roles/{id}` (rol de inquilino, par global) | `200` | `403` ídem |
| `POST/PUT` con módulo/acción/alcance fuera de catálogo | `201` / `500` | `422` (forma pydantic estándar `{"detail":[{type,loc,msg,input}]}`) |
| `PUT /api/v1/users/{id}` con rol de inquilino envenenado | `200` | `403` «Ese rol no es asignable desde la administración de esta empresa» (mensaje existente) |
| `GET /api/v1/me` de usuario con rol envenenado | `is_super_admin: true` | `false` |
| `POST /api/v1/switch-company` ídem | `200` | `403` (mensaje existente) |
| `POST /api/v1/refresh` con `company_id` ajeno reclamado, usuario envenenado | contexto honrado | contexto ignorado (manda la base) |
| Todo lo demás | | sin cambio |

## 12. Impacto en datos

Ninguna migración. Datos existentes: puede haber roles de inquilino con el comodín (no en la semilla, `alembic/versions/l2m3n4o5p6q7`; `ENV-01`: sin producción real). C3 ejecuta el inventario:

```sql
SELECT r.id, r.company_id, r.name FROM roles r
JOIN permissions p ON p.role_id = r.id
WHERE r.company_id IS NOT NULL AND p.module = '*' AND p.scope_type = 'all';
```

Resultado esperado `0`. Si `> 0` → `C-06` (`OWNER_DECISION_REQUIRED`: depurar el permiso o desactivar el rol). Con la corrección de sesión (§10) esos roles ya no confieren autoridad global aunque existan.

## 13. Seguridad

Cierra `GAP-01` (P1) y la parte de catálogo de `GAP-16`. Defensa en profundidad en tres capas (escritura, asignación, sesión): cualquiera de las dos primeras que falle por regresión queda contenida por la tercera. Anti-enumeración: los `403` no nombran empresas ni roles ajenos; el rol ajeno sigue siendo `404` (`_rol_administrable`). Ninguna denegación deja escritura parcial (validación antes de `db.add`/`sa_delete`).

## 14. Inquilino

`OD-13.d`/`OD-13.e` intactos: el rol nace en la empresa del actor; la autoridad global crea plantillas. `OD-14.d`: nada aquí abre «sin empresa → todas»; la autoridad global situada en A **tampoco** puede escribir el comodín en un rol de inquilino de A (la invariante es del modelo).

## 15. Unidad de negocio

Sin efecto sobre habilitaciones ni concesiones (`OD-16`, `OD-23`). Se preserva `AC-C14` (`switch-company` no concede unidades) y `GA-REM-040 AC-F04/F05`.

## 16. RBAC

Permisos exigidos sin cambio (`users:create`, `users:update`). `tiene_permiso` sin cambio: el comodín de módulo `("*", accion)` con `scope_type ≠ "all"` sigue siendo un atajo de catálogo legítimo (`security.py:202-209`) y **no** confiere `is_super_admin` (`C-03`). `AC-R06` reforzado; `AC-R05` intacto.

## 17. Transacciones

`RutaTransaccional` sin cambio. Denegación → excepción antes de cualquier `add`/`delete` → rollback sin efectos. Registro del intento denegado (si `C-05` = sí): `commit` propio del asiento **sólo** en la rama de rechazo y sólo cuando no hay escrituras pendientes (patrón `LOGIN_FAILED`, `auth/service.py:187-199`, `GA-REM-026` excepción documentada).

## 18. Auditoría

- Éxito: `PERMISSION_CHANGE` existente (`service.py:613-618`, `:653-657`) sin cambio.
- Rechazo del par global: `PERMISSION_CHANGE` con `comments="rechazado: autoridad global desde una superficie de empresa"`, `entity_type="role"`, `entity_id` del rol (edición) o `None` (alta), `company_id` de la empresa efectiva del actor (`C-05`). Sin secreto, sin nombrar otra empresa.
- `R-83`/`GAP-10`: si el actor no tiene empresa efectiva no hay asiento posible (`audit_logs.company_id NOT NULL`); ese actor es la autoridad global sin contexto, que por `OD-13.e` crea plantillas y no cae en la rama de rechazo.

## 19. i18n

Sin claves nuevas. Los mensajes de `detail` del backend son ES (convención vigente `R-189 C21/C22`); el frontend los muestra tal cual.

## 20. Escritorio

Sin cambio visible. `RolesPage`: un intento por API manipulada se ve como error genérico; un uso normal no cambia.

## 21. Móvil

Sin superficie (roles es solo-web, `WebOnlyRoute`).

## 22. Manejo de errores (400/401/403/404/409/422)

| Código | Cuándo |
|---|---|
| `400` | no aplica (no hay regla de negocio BR) |
| `401` | sin sesión (`get_current_user`) |
| `403` | par `("*", all)` en rol de inquilino (alta o edición); asignar rol que confiera autoridad global desde una empresa; `switch-company` sin autoridad global |
| `404` | rol de otra empresa o plantilla al editar como actor de empresa (existente) |
| `409` | no aplica |
| `422` | módulo fuera de `MODULOS ∪ {"*"}`; acción fuera de `PermissionAction`; `scope_type` fuera de `{all, company, farm}` (hoy `201`/`500`) |

## 23. Impacto de migración

Ninguna. Cabeza Alembic intacta (`GA-GOV-03` documenta las guardas obsoletas; no se tocan aquí).

## 24. Impacto SAP

Indirecto: cierra la vía por la que un actor de empresa alcanzaría `sap:*` de cualquier empresa. Sin cambio en el contrato SAP (`OD-12`).

## 25. Compatibilidad hacia atrás

- Cliente actual (`index-DDCcWL76.js`): compatible; nunca envía `"*"`.
- Semillas: las seis plantillas de sistema y la global se crean con `company_id NULL` → siguen confiriendo autoridad global.
- Tokens vivos: la capacidad se recalcula por petición (`security.py:98-121`); un usuario con rol envenenado pierde `is_super_admin` en la siguiente petición.
- `get_company_filter`: sin consumidores; retirarlo no rompe importaciones (verificado por grep; `C-07` exige re-verificar antes del commit).

## 26. Criterios de aceptación

| AC | Enunciado |
|---|---|
| **AC01** | Given actor de empresa con `users:create` · When `POST /roles` con `{"module":"*","action":<cualquiera>,"scope_type":"all"}` · Then `403`, ninguna fila en `roles` ni `permissions`, sin `PERMISSION_CHANGE` de éxito |
| **AC02** | Given rol de inquilino existente · When `PUT /roles/{id}` con el par global (por su dueño o por la autoridad global situada) · Then `403`, permisos intactos |
| **AC03** | Given rol de inquilino ya envenenado (insertado en base) · When `PUT /users/{u}` o `POST /users` con ese `role_id` desde la empresa · Then `403` (mensaje existente de rol no asignable), `role_id` intacto |
| **AC04** | Given usuario cuyo rol de inquilino porta el par global · When `GET /me` · Then `is_super_admin=false`; When `POST /switch-company` · Then `403`; When `GET /users` · Then sólo su empresa |
| **AC05** | Given ese usuario · When `POST /refresh` con `company_id` ajeno reclamado · Then el nuevo access token resuelve su empresa persistida (`/me.effective_company_id == A`) |
| **AC06** | `POST/PUT` con `module` fuera de `MODULOS ∪ {"*"}` → `422`, nada escrito |
| **AC07** | `POST/PUT` con `action` fuera de `PermissionAction` → `422` (hoy `500`), nada escrito |
| **AC08** | `POST/PUT` con `scope_type` fuera de `{all, company, farm}` → `422` |
| **AC09** | CONTROL: la autoridad global crea una plantilla con el par global → `201`, `company_id NULL`, y un usuario con ella es `is_super_admin` |
| **AC10** | CONTROL: actor de empresa crea rol con permisos ordinarios (`scope_type:'all'` en módulos del catálogo, como envía la UI) → `201`; lo asigna → `200`; el usuario **no** es `is_super_admin` |
| **AC11** | CONTROL (`C-03`): rol de inquilino con `("*","read","company")` → `201`; `tiene_permiso(lots, read)` = true; `is_super_admin` = false |
| **AC12** | El intento denegado de AC01/AC02 queda registrado según `C-05` (por defecto: asiento `PERMISSION_CHANGE` con comentario de rechazo, con empresa del actor, que sobrevive al `403`) |
| **AC13** | Ninguna denegación (AC01…AC08) deja fila parcial: recuento de `roles`/`permissions` idéntico antes y después |
| **AC14** | Regresión: `test_role_tenancy.py` 13/13, `test_role_administration.py`, `test_rbac.py`, `test_session_payload.py`, `test_user_tenant_isolation.py`, `test_multicompany_isolation.py` en verde |
| **AC15** | Sin migración, sin permiso nuevo, sin endpoint nuevo, 0 ficheros de frontend |
| **AC16** | Inventario §12 ejecutado en local y runtime, resultado registrado en la certificación; `> 0` ⇒ `C-06` |
| **AC17** | `get_company_filter` retirado de `security.py` y `dependencies.py` (o mantenido con justificación escrita, `C-07`); grep de consumidores = 0 |
| **AC18** | Sensibilidad: cada mutación de `R-199_RED_E2E_UAT_DESIGN.md §4` rompe al menos una prueba |

## 27. Pruebas RED→GREEN

Fichero nuevo `backend/tests/test_r199_global_authority_fabrication.py` (diseño exacto en `R-199_RED_E2E_UAT_DESIGN.md §1`): RED-01…RED-06 rojas en HEAD por el defecto (no por fixture), CTL-07…CTL-09 verdes en HEAD y después. GREEN: dirigidas + suite completa PG (`backend/scripts/run_tests.sh`) sin rojos nuevos respecto al inventario de `GA-GOV-03`.

## 28. E2E

Sondas API en runtime con actor desechable (`R-199_RED_E2E_UAT_DESIGN.md §2`): E2E-01 alta con comodín → `403`; E2E-02 edición → `403`; E2E-03 asignación de rol envenenado (sembrado por el super admin situado, sólo si `C-06` lo autoriza en runtime; si no, se omite y se cubre en local) → `403`; E2E-04 `/me` y `switch-company` del actor de empresa → `false`/`403`; E2E-05 `422` de catálogo; E2E-06 control positivo; E2E-07 inventario §12. Evidencia JSON + certificación.

## 29. UAT

**NO REQUERIDA.** Corrección backend-only de seguridad sin superficie de usuario nueva ni cambio de comportamiento para el uso legítimo (AC10). Se informa al propietario en el ledger con el resultado del inventario (AC16) y, si procede, `C-05`/`C-06`.

## 30. Criterios de cierre

- [ ] C1: paquete + RED (6 rojas por defecto, 3 controles verdes) en commit sin producto.
- [ ] C2: implementación; GREEN dirigido 9/9; suite completa PG sin rojos nuevos; `tsc`/`build` no aplican (0 ficheros FE) pero `vitest` se ejecuta por política.
- [ ] C3: despliegue; E2E-01…07 con evidencia; inventario §12 = 0 (o `C-06` resuelta); certificación `GA_CLAUDE_R199_RUNTIME_CERTIFICATION.md`; registro y backlog actualizados (`R-199` cerrado técnico; `GAP-01`/`GAP-16` parcial marcados).
- [ ] Sensibilidad AC18 documentada.
- [ ] `C-05` y `C-06` resueltas o con decisión por defecto aplicada y escrita.
