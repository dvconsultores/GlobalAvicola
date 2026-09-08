# GA-REM-002 — RBAC: ENFORCEMENT DE AUTORIZACIÓN EN BACKEND

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-002` · **Tipo** `SECURITY SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** |
| **Estado** | `SPEC_READY` |
| **Dependencias** | `GA-REM-001` |
| **Habilita** | `GA-REM-007`, `GA-REM-012`, cierre de seguridad, certificación de procesos |
| **Hallazgos** | P0-3 · S-01 · `GA-TD-003` · `GA-REQ-002` (`DOC_NO_IMPL`) |
| **Revalidado** | 2026-09-03 — `grep -rn "require_permission\|has_permission\|check_permission" backend/app` → **0 resultados** |

## Problema
El modelo de permisos existe completo (`Permission` con `module`, `action`, `scope_type`, `scope_id`; `PermissionAction` con 9 acciones; seeds que pueblan 6 roles) y **ningún endpoint lo consulta**. El único uso de la tabla es deducir `is_super_admin` cuando existe un permiso con `module="*"` y `scope_type="all"`.

## Evidencia
| Ítem | Ruta |
|---|---|
| Modelo de permisos | `backend/app/auth/models.py:46-69` |
| Único consumidor de la tabla | `backend/app/auth/security.py:107-118` |
| Seeds que pueblan permisos | `backend/seeds/dev_seeds.py:43-115`, `seeds/integration_seeds.py:66-143` |
| Endpoints con `Depends(get_current_user)` sin más | 10 routers: auth 10, lots 12, review 16, reports 14, operations 12, sap 10, masters 7, audit 3, corrections 3, dashboard 2 |
| Guard de frontend inservible | `frontend/src/App.tsx:53-58` — `const userRoleName = user?.role_id ? '' : 'super_admin'`, y el prop `roles` nunca se pasa |

## Comportamiento actual
Cualquier usuario autenticado —incluido un Operador de Granja— puede ejecutar `POST /approvals/approve`, `POST /approvals/batch-approve`, `POST /sap/export`, `POST /users`, `PUT /roles/{id}`, `DELETE /masters/{entidad}/{id}` y `GET /audit`. La única restricción del frontend es `view_type` (móvil/web), que además se pierde tras un refresh de token (`GA-REM-003`).

## Comportamiento esperado
```
REQUEST → AUTHENTICATION → AUTHORIZATION → PERMISSION CHECK → COMPANY SCOPE → BUSINESS ACTION
```
Con `403` cuando el permiso falta y `401` cuando la autenticación falta, de forma consistente en los 165 endpoints autenticados.

## Alcance
1. Dependencia `require_permission(module, action)` que resuelve contra la tabla `permissions` del rol del usuario.
2. Resolución de alcance: `all` · `company` · `farm` (`scope_type`/`scope_id`).
3. Aplicación a los 165 endpoints autenticados, agrupados por módulo.
4. Matriz endpoint → acción → permiso → rol → alcance, versionada en el repositorio.
5. Guard de rol en el frontend y menú filtrado por permisos efectivos (defensa en profundidad, **nunca** control único).
6. Eliminación del prop `roles` inservible de `ProtectedRoute`.
7. Endpoint `GET /me/permissions` para que el frontend construya la UI sin adivinar.

## Fuera de alcance
Rediseño del modelo de permisos · nuevos roles · UI de administración de roles y permisos (queda en `GA-REM-019`/backlog) · cambio del mecanismo de autenticación (es `GA-REM-003`).

## Reglas de negocio afectadas
`BR-13` (nada a SAP sin aprobación) y `BR-14` (segregación) dependen de que solo los roles autorizados alcancen esos endpoints. La spec **no** cambia las reglas; hace que sean exigibles.

## Arquitectura afectada
Nueva dependencia FastAPI en `backend/app/auth/`. Sin cambio de patrón: se añade una capa entre `Depends(get_current_user)` y el servicio.

## Backend afectado
`auth/security.py` (nueva dependencia), los 10 routers, `auth/router.py` (nuevo `GET /me/permissions`).

## Frontend afectado
`App.tsx` (guard de rol), `navigationConfig.ts` (filtrado de menú), `stores/auth.store.ts` (almacenar permisos efectivos).

## Base de datos afectada
**Ninguna.** El modelo ya existe y está poblado. Sin migraciones.

## Seguridad
Es el núcleo de la spec. Cierra `S-01` (P0) y reduce el impacto de `S-02`.

## Migraciones
Ninguna.

## Compatibilidad
**Ruptura controlada e intencionada**: usuarios que hoy pueden hacer de todo dejarán de poder. Requiere verificar que los 6 roles sembrados tienen los permisos que su función exige **antes** de activar el enforcement, o los operadores quedarán bloqueados.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Usuario sin rol (`role_id = NULL`) | `403` en todo endpoint que exija permiso |
| Usuario con rol sin permisos | `403` |
| Super Admin (`module="*"`, `scope="all"`) | acceso completo, conservando el comportamiento actual |
| Permiso con `scope_type="company"` y compañía distinta | `403` |
| Permiso con `scope_type="farm"` y granja distinta | `403` |
| Rol modificado durante una sesión activa | el permiso se resuelve **por petición** contra la BD, no desde el token |
| Endpoint sin permiso declarado | falla el arranque de la aplicación (ver AC08) |

## Acceptance Criteria

**AC01 — Un operador no puede aprobar**
```
Given un usuario con rol "Operador de Granja" autenticado
When  hace POST /api/v1/approvals/approve
Then  recibe 403
And   el evento conserva su estado anterior
```
**AC02 — Un operador no puede borrar maestros**
```
Given un usuario con rol "Operador de Granja" autenticado
When  hace DELETE /api/v1/masters/farms/{id}
Then  recibe 403
And   la granja sigue con is_active = true
```
**AC03 — Un operador no puede exportar a SAP**
```
Given un usuario con rol "Operador de Granja" autenticado
When  hace POST /api/v1/sap/export
Then  recibe 403
```
**AC04 — Un aprobador sí puede aprobar**
```
Given un usuario con rol "Aprobador" y permiso approvals:approve
And   un evento en estado corrected registrado por otro usuario
When  hace POST /api/v1/approvals/approve
Then  recibe 200 y el evento queda approved
```
**AC05 — El alcance de compañía se valida**
```
Given un usuario de la compañía A con permiso scope_type="company"
When  intenta operar sobre un recurso de la compañía B
Then  recibe 403 o 404, nunca el recurso
```
**AC06 — Sin autenticación es 401, sin permiso es 403**
```
Given una petición sin cabecera Authorization
When  alcanza cualquier endpoint protegido
Then  recibe 401
Given una petición autenticada sin el permiso requerido
Then  recibe 403
```
**AC07 — El frontend no es el único control**
```
Given un usuario sin permiso approvals:approve
When  invoca el endpoint directamente con curl, sin pasar por la interfaz
Then  recibe 403
```
**AC08 — Ningún endpoint queda sin decisión de autorización**
```
Given la aplicación arrancando
When  se enumeran las rutas de /api/v1
Then  cada ruta autenticada declara explícitamente su permiso requerido
And   una ruta sin declaración impide el arranque
```
**AC09 — El Super Admin conserva su alcance**
```
Given un usuario Super Administrador
When  opera sobre cualquier módulo y cualquier compañía
Then  no recibe 403 por motivo de permiso
```
**AC10 — Los roles sembrados siguen pudiendo trabajar**
```
Given los 6 roles de dev_seeds y los 7 de integration_seeds
When  cada uno ejecuta el flujo propio de su función
Then  ninguno recibe 403 en una acción que su rol debe permitir
```

## Tests requeridos
| ID | Cubre | Tipo |
|---|---|---|
| `T-002-01..03` | AC01-AC03 — negativos por rol | integración |
| `T-002-04` | AC04 — positivo | integración |
| `T-002-05` | AC05 — alcance de compañía | integración |
| `T-002-06` | AC06 — 401 vs 403 | integración |
| `T-002-07` | AC07 — bypass de UI | integración |
| `T-002-08` | AC08 — cobertura total de rutas | test de arranque, paramétrico sobre `app.routes` |
| `T-002-09` | AC09 — super admin | integración |
| `T-002-10` | AC10 — matriz de 13 roles × acciones propias | integración, paramétrico |

Requiere `GA-REM-014` (entorno aislado) para ejecutarse.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Bloquear a operadores reales en producción al activar el enforcement | AC10 verifica los 13 roles antes de activar; despliegue tras validar la matriz |
| Un endpoint olvidado queda sin protección | AC08 lo convierte en fallo de arranque, no en agujero silencioso |
| Coste por petición al resolver permisos contra la BD | el usuario ya se carga en `get_current_user`; los permisos vienen con `lazy="selectin"` en el rol |

## Rollback lógico
La dependencia es aditiva y se puede desactivar con un feature flag (`FEATURE_RBAC_ENFORCED`) que en `false` conserva el comportamiento actual. **El flag es transitorio**: la spec no se cierra hasta que esté en `true` y el flag eliminado o documentado.

## Definition of Done
- [ ] AC01–AC10 verificados · [ ] Matriz de permisos versionada · [ ] `T-002-*` en verde · [ ] Control de regresiones §12 de la constitución · [ ] Certification report


---

# ADDENDUM — Wave 3 · `AC05` en su dimensión de escritura

## Por qué se activa esta spec desde `GA-REM-016`

El gate sistémico de aislamiento multiempresa que `GA-REM-016` exige antes de certificar
procesos encontró que **`AC05` estaba verificado solo a medias**.

`AC05` dice: *«un usuario de la compañía A intenta operar sobre un recurso de la compañía B
→ recibe 403 o 404, nunca el recurso»*. La certificación de la Wave 2 lo comprobó sobre
**lecturas** —listados y consultas por id— y sobre `lot_id` en escritura tras `R-42`.

No se comprobó sobre **las demás claves foráneas que el cliente puede enviar en una
escritura**. El gate lo probó y el resultado fue:

```
POST /operations {farm_id:  <granja de la empresa B>}  -> 201
POST /operations {house_id: <galpón de la empresa B>}  -> 201
POST /masters/houses {farm_id: <granja de la empresa B>} -> 201
```

Existir no basta. `R-42` enseñó exactamente esto para `lot_id`; la lección no se extendió
al resto.

## Alcance de la ampliación

Se descubrieron **22 claves foráneas tenant-scoped enviables por el cliente** en los
esquemas de escritura. No todas requieren la misma regla: los catálogos maestros declaran
`company_id` como anulable, lo que significa «global si es nulo, propio de la empresa si
está fijado», y bloquear una referencia a un catálogo compartido sería un error.

La ampliación cubre las referencias **estructurales**, aquellas cuya pertenencia define de
quién es el dato:

| Clave | Recurso | Por qué |
|---|---|---|
| `lot_id` | lote | ya cubierto por `R-42` |
| `farm_id` | granja | ubica el registro; una granja ajena lo asocia a otra empresa |
| `house_id` | galpón | ídem, y su capacidad participa en `BR-17` |
| `destination_farm_id` | granja destino | dirige un despacho a otra empresa |
| `event_id` | evento | corrección, revisión y aprobación sobre un registro ajeno |

Los catálogos con `company_id` anulable quedan **fuera**: su diseño admite el uso
compartido. Se documenta en `TENANT_RESOURCE_CLASSIFICATION.md` para que la exclusión sea
una decisión visible y no un olvido.

## `AC10` — pertenencia de las claves foráneas en escritura

```
Given un usuario cuya compañía efectiva es A
And   un recurso estructural que pertenece a la compañía B
When  envía ese identificador como clave foránea en una creación o edición
Then  la operación se rechaza
And   no se crea ni modifica ninguna fila
And   no se registra auditoría
And   ningún dato derivado de la compañía B cambia
```

## `AC12` — el sub-recurso hereda la pertenencia de su padre · **enmienda A** (2026-09-07)

```
Given  un recurso anidado que se alcanza por el identificador de su padre
       — las fases de un lote, su saldo de apertura —
When   el padre no pertenece a la compañía efectiva del usuario
Then   el sub-recurso es inalcanzable, con la misma respuesta que daría el padre
And    ninguna escritura contra ese padre ajeno deja fila
```

### Por qué se añade

`R-111`. `AC05` se verificó sobre **lecturas del recurso primario** —listados y consultas por
id— y `AC10` sobre **claves foráneas en escritura**. Entre las dos quedó un hueco: el
sub-recurso que se alcanza por el identificador del padre y consulta directamente por él.

```
GET /lots/{id}            comprobaba pertenencia
GET /lots/{id}/phases     NO comprobaba nada — ni compañía
GET /lots/{id}/opening-balance   ídem
POST /lots/{id}/phases    creaba la fila sin comprobar de quién era el lote
```

Es literalmente la frase que esta spec ya había escrito para las claves foráneas —*«existir no
basta»*, *«la lección no se extendió»*— aplicada un nivel más abajo:

```
DETALLE PROTEGIDO   ≠   SUB-RECURSO PROTEGIDO
```

Proteger el padre y dejar el hijo libre no protege nada: el recurso queda abierto por la puerta
de al lado.

### Estado

Corregido. Los tres caminos pasan por la comprobación del padre y devuelven `404`, que es lo que
`AC05` exige y lo que impide distinguir «no existe» de «no es tuyo». Las pruebas viven en
`backend/tests/test_lot_row_scope.py` y se enumeran en `GA_REM_040_PHASE_3_EVIDENCE.md §5`.

Se descubrió siguiendo la cadena de seguridad de `GA-REM-040` fase 3, y **no es un defecto de
aquella fase**: es anterior a las unidades de negocio y de otra naturaleza —pertenencia de
inquilino, no alcance de cadena productiva—.

---

## `AC11` — la comprobación es explícita y compartida

```
Given una escritura que referencia un recurso tenant-scoped
When  se inspecciona el código que la valida
Then  la comprobación de pertenencia es una función única y reutilizable
And   no está duplicada en cada servicio
```

Una regla de aislamiento aplicada en un sitio y ausente en otro no es una regla: es una
casualidad. Es la misma lección que `BR-14` dejó en `GA-REM-007`.
