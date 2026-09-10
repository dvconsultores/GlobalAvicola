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

---

# Enmienda B · la administración de usuarios es superficie de inquilino (2026-09-08)

`R-114` · `R-117` · `R-118`. Cuatro `P0` demostrados por la Auditoría Maestra de Spec/Producto.

## Por qué hubo que enmendar y no crear una `GA-REM` nueva

`AC05` ya lo exigía: *«un usuario de la compañía A que intenta operar sobre un recurso de la
compañía B recibe 403 o 404, nunca el recurso»*. Un usuario **es** un recurso de una compañía, de
modo que la `AC` cubría el caso desde el primer día.

Lo que falló no fue la norma, fue su traza. `TENANT_RESOURCE_CLASSIFICATION.md` —el documento que
convierte `AC05` en una lista de sitios donde aplicar el filtro— se construyó desde el modelo de
datos **operativo**: lotes, eventos, granjas, galpones, evidencias, revisiones. **`users` nunca
entró en esa lista**, y con él se quedó fuera toda la superficie de administración.

```
LA `AC` EXISTÍA          ·  LA TRAZA DE IMPLEMENTACIÓN, NO
```

Por eso esto es una enmienda: no hay requisito nuevo que decidir, hay un ámbito que la
implementación nunca alcanzó. Inventar `GA-REM-041` habría escondido que la regla llevaba
escrita desde `GA-REM-002` y que lo que falló fue el método de verificación.

## `AC13` — la administración de usuarios se acota a la empresa efectiva

```
Given un actor cuya compañía efectiva es A, con permiso de administración de usuarios
When  lista usuarios
Then  obtiene únicamente los de A
And   el filtro se aplica en la consulta, antes de paginar, contar u ordenar

When  consulta por identificador un usuario de la compañía B
Then  recibe 404, y la respuesta no revela su existencia
```

El `404` y no el `403` es la convención ya fijada por `AC05`: distinguir «no existe» de «no es
tuyo» ya filtra información.

## `AC14` — la mutación resuelve el objetivo antes de mutar

```
Given un actor cuya compañía efectiva es A
When  edita un usuario de la compañía B
Then  la operación se rechaza ANTES de tocar ninguna fila
And   el usuario ajeno queda idéntico en todos sus campos
And   no se registra auditoría de éxito
And   la transacción no deja estado parcial
```

El orden importa y es parte de la `AC`:

```
AUTENTICACIÓN → EMPRESA EFECTIVA → OBJETIVO EN ESA EMPRESA → RBAC →
VALIDACIÓN DE CAMPOS → VALIDACIÓN DE ROL → MUTACIÓN → AUDITORÍA → COMMIT
```

Nunca «buscar globalmente, mutar, y descubrir después la discrepancia».

Y la empresa **no se recibe del cliente**. Ni por cuerpo, ni por parámetro de consulta, ni por
reclamación del token: se resuelve con `OD-11`, igual que en `GA-REM-040` fase 7.

## `AC15` — asignar un rol es modificar autoridad

```
Given un actor acotado a una compañía
When  asigna a cualquier usuario un rol con `module="*"` y `scope_type="all"`
Then  la operación se rechaza con 403
```

`docs/02 §3.1.4` define al Super Administrador exactamente así y le da visibilidad sobre
**todas** las compañías. Conceder ese rol desde una superficie acotada a una empresa **fabrica
una autoridad global desde dentro de un inquilino**, y eso es escalada aunque el objetivo sea de
la misma casa.

Lo que esta `AC` **no** hace: inventar una regla de «solo se asignan roles más débiles que el
propio». Esa jerarquía no está especificada en ninguna parte y decidirla no corresponde aquí.
Se prohíbe exactamente lo que la spec ya describe como alcance global, y ni un milímetro más.

```
PENDIENTE Y REGISTRADO   qué roles ordinarios puede asignar un administrador de empresa
                         sigue sin especificar — `R-121` · `OWNER_DECISION_REQUIRED`
```

La autoridad global legítima —quien ya tiene `("*", …, all)`— conserva la capacidad: `AC15`
acota a los actores de empresa, no al Super Administrador.

## `AC16` — una denegación se ve como una denegación

```
Given una pantalla de administración cuya API responde 403
When  el usuario la abre
Then  ve un estado explícito de permiso insuficiente
And   NO ve una tabla vacía

Given la API responde 200 con lista vacía
Then  ve el estado «no hay usuarios», y solo entonces
```

Va en esta enmienda y no en otra parte porque es **la misma superficie y el mismo hallazgo**:
`/users` se veía vacía, y esa apariencia fue exactamente lo que mantuvo los cuatro `P0`
invisibles durante meses. Una fuga de inquilino que no se puede ver no se reporta.

Y porque el arreglo de `AC13` **aumenta** la frecuencia del `403`: donde antes un actor sin
empresa efectiva recibía la lista entera, ahora recibe una denegación. Dejar la denegación
indistinguible del vacío convertiría la corrección de seguridad en un fallo aparente del
producto.

El principio ya estaba escrito en la casa —`GA-REM-038 AC19`, para la campana de avisos:
«un fallo de `API` no se presenta como bandeja vacía»— y nunca se generalizó. Aquí se aplica
a la administración de usuarios; generalizarlo al resto de pantallas es trabajo aparte y
queda en `R-120`.

Cinco estados distinguibles: `cargando` · `datos` · `vacío real` · `403` · `error inesperado`.
Todo texto por `i18n`, con paridad `es`/`en` (`GA-REM-038 AC20`).

## Tareas

| Tarea | Qué |
|---|---|
| `T-002-13` | Localizador único de usuario dentro de la empresa efectiva |
| `T-002-14` | Listado, detalle y edición acotados en la consulta |
| `T-002-15` | Barrera de autoridad global en la asignación de rol |
| `T-002-16` | `users` incorporado a `TENANT_RESOURCE_CLASSIFICATION.md` |
| `T-002-17` | Cinco estados distinguibles en la pantalla de usuarios |

## Estado

Corregido y evidenciado en `USER_TENANT_ISOLATION_P0_EVIDENCE.md`. **Sin migración**: la
pertenencia ya existía en `users.company_id`; lo que faltaba era usarla.

---

# Enmienda C · el dato productivo declara su clase: `OD-14.c/d` en las ocho superficies no conformes (2026-09-09)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-002-C` · `SECURITY / SCOPE SPEC` · **Estado** `SPEC_READY` |
| **Hallazgo** | **`R-139`** · P1 · `REMEDIATION_BACKLOG.md` (alta 2026-09-09) · origen `H360-A01` = `H360A-08` · verificación `A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md` |
| **Autoridad** | **`OD-14.c`** (dato productivo y maestros = `INQUILINO`: global sin contexto → cero filas / deniega; situada en `A` → solo `A`) · **`OD-14.d`** («`PROHIBIDO sin empresa → todas`») · `OD-11` (empresa efectiva) · `OD-09.a` (visibilidad de unidad, se preserva) · `OD-16.f` |
| **Matriz previa** | `R139_PRODUCTIVE_SURFACE_AUTHORITY_MATRIX.md` — las ocho filas, con clase esperada y defecto |
| **Procesos** | `P-03`, `P-05`, `P-06`, `P-11`, `P-12`, `P-14` (superficies), sin re-certificación |
| **Dependencias** | `OD-14` implementado en `users`/roles/`masters/service` (`771b402`) · `GA-REM-040` fases 2-3 (predicados de unidad) · `RQ-03 COMPLETE` |
| **Fuera de alcance** | `WAVE B` (`R-130`, `R-135`, `R-136`, `R-140`, `R-142`, `R-143`, `R-144`, `R-147`, `R-148`, `R-152`, `R-153`, `R-154`, `R-156`, `GA-REM-021`) · `R-158` · KPI · agua · población · reproceso · reverso · SAP · fase 9 · `BU-D10` · **`R-159`** (alcance de unidad en `get_alerts`, registrado aquí, no remediado) |

## C.1 Hallazgo y causa raíz

Ocho superficies de dato productivo y maestros sustituyen el filtro de empresa por el indicador
de autoridad global (`if not is_super_admin: acotar`): `operations.get_alerts:762`,
`operations.get_events:810`, `operations.delete_evidence:978`,
`operations.get_evidence_for_download:997`, `lots.activate_manual:351`,
`masters/curves._linea_del_usuario:75`, `masters/router.get_houses_by_farm:139`,
`masters/router.get_incubators_by_hatchery:161`. Es la semántica que `OD-14 §6` retiró («antes
veía … de todas las empresas desde cualquier ruta; ahora tiene que elegir una empresa») y que
`771b402` propagó solo a `users`, roles y `masters/service`. Tres de ellas (S06, S07, S08) tienen
además la forma `and company_id` / `and company_id is not None`, de modo que **un actor sin
empresa** tampoco recibe filtro (`R-116` en otra piel). El primitivo compartido
`tenancy.verificar_pertenencia` conserva la regla anterior en su docstring y su código
(`company_id` nulo → sin filtro, `tenancy.py:44-48`).

## C.2 Clasificación

Las ocho son **`INQUILINO`**. Ninguna es `CONTROL_GLOBAL`: `OD-14.c` reserva esa clase al
catálogo de empresas, al catálogo de capacidades y a las plantillas de sistema. La resolución de
la empresa efectiva no cambia (`get_current_user` → `resolver_empresa_efectiva`, `OD-11`): actor
de empresa → su `users.company_id`; autoridad global → la reclamación autorizada por
`switch-company` o **ninguna**.

| Situación | Listados (S01, S02) | Recurso por identificador (S05, S06, S07, S08) | Evidencias (S03, S04) |
|---|---|---|---|
| actor de empresa `A` | solo `A` | propio → `200`/`201`; ajeno → `404` (S06–S08) · `400 BR-07` (S05) | propia → `200`/`204`; ajena → `403` |
| autoridad global **sin contexto** | **cero filas** (`200 []`) | **`404`** (S06–S08) · **`400 BR-07`** (S05, convención `AC-R67-11`) | **`403`** |
| autoridad global situada en `A` | solo `A` | de `A` → `200`/`201`; de `B` → `404` | de `A` → ok; de `B` → `403` |
| autoridad global situada en `B` | solo `B` | inverso | inverso |
| actor sin empresa (`company_id NULL`, no global) | cero filas | `404` · `400 BR-07` (S05) | `403` |

Las convenciones de error son las **vigentes** de cada superficie: no se inventan.

## C.3 Interacción con unidad de negocio, RBAC y reglas de recurso

- **Unidad**: el actor de empresa sigue acotado por `unidades_efectivas` donde ya lo estaba (`predicado_de_evento` en S02; `get_lot` por `_apply_business_unit_filter` en S05). La autoridad global **conserva** la exención de visibilidad de unidad certificada en la fase 3 (`GA_REM_040_PHASE_3_EVIDENCE.md:88`, coherente con `OD-09.a`): situada en `A` ve todas las unidades de `A`. `R-139` **no** cambia `effective_business_units`, no concede unidades a nadie y no toca `BU-D10`. Las fixtures habilitan explícitamente la unidad que necesitan; ninguna prueba depende de rehabilitar.
- **RBAC**: los permisos de cada ruta no cambian (`operations:read/delete`, `lots:create`, `masters:read/create`). Ningún nombre de rol interviene.
- **Recurso**: `BR-07` (lote activo), `409` (saldo previo), `docs/02 §3.9.2` (sin historia) siguen en S05; S07/S08 mantienen la pertenencia por el padre (`AC12`).
- **Contraloría** (`OD-09.a`) y transversalidad SAP (`OD-12`) no intervienen: ninguna de las ocho es superficie de control transversal ni de contrato SAP.

## C.4 Criterios de aceptación

### `AC17` — invariantes globales (`AC-G01…G20` del encargo)

1. Las ocho superficies de `A01` quedan mapeadas a una clase `OD-14` explícita (`R139_PRODUCTIVE_SURFACE_AUTHORITY_MATRIX.md`).
2. Ninguna decisión de autoridad usa nombre de rol.
3. No queda ningún `if is_super_admin: todas las filas` en las ocho superficies; no se añade ninguno nuevo.
4. El aislamiento de inquilino para actores de empresa se mantiene (`R-115`, `R-116`, `RQ-03`).
5. La fuga entre empresas sigue siendo imposible para actores de empresa.
6. Las superficies `INQUILINO` exigen empresa efectiva a la autoridad global.
7. La autoridad global sin empresa seleccionada **falla cerrada** en ellas (cero filas · `404` · `403`, según la convención vigente).
8. Situada en `A`, solo obtiene dato de `A`.
9. No hay `CONTROL_GLOBAL` entre las ocho; el catálogo de empresas sigue global (`GA-REM-033-A AC18/AC19`, sin cambio).
10. La habilitación de unidad por empresa sigue aplicándose (`AC-A05`).
11. Las concesiones de unidad siguen aplicándose donde aplican (`predicado_de_evento`, `get_lot`).
12. El RBAC sigue aplicándose.
13. Las reglas de recurso/negocio siguen aplicándose.
14. Ninguna regla de empresa o unidad se elude como efecto colateral.
15. Sin cambios de contrato de respuesta ajenos (los cuerpos de `200` no cambian; solo cambia **quién** obtiene qué).
16. Sin rutas nuevas.
17. Sin migración (`alembic heads` = `s9t0u1v2w3x4`).
18. Sin frontend.
19. Sin SAP.
20. `BU-D10` sigue `PENDING_RATIFICATION`.

### `AC18` — S01 `GET /operations/alerts`
Actor `A` → solo alertas de `A` · global sin contexto → `200 []` · situada en `A` → solo `A`; en `B` → solo `B` · sin `operations:read` → `403`.

### `AC19` — S02 `GET /operations`
Actor `A` → solo eventos de `A` en sus unidades efectivas · global sin contexto → `200 []` y `X-Total-Count`/total sin filas ajenas · situada en `A` → solo `A` (todas sus unidades) · unidad deshabilitada para la empresa → el actor de empresa no la ve (`AC-A05`, control preservado) · sin `operations:read` → `403`.

### `AC20` — S03 `DELETE …/evidences/{id}`
Actor `A` sobre propia → `204` (fichero eliminado) · actor `B` sobre la de `A` → `403` y la evidencia y su fichero permanecen · global sin contexto → `403` · situada en `A` → `204`; situada en `B` → `403`.

### `AC21` — S04 `GET …/evidences/{id}/download`
Actor `A` propia → `200` con el contenido · actor `B` → `403` · global sin contexto → `403` · situada en `A` → `200`; en `B` → `403`.

### `AC22` — S05 `POST /lots/activate-manual`
Actor `A` con lote propio alcanzable → `201` · actor `B` con lote de `A` → **`400 BR-07`** («Lote no encontrado», convención vigente de `verificar_pertenencia` / `AC-R67-11`; el `404` queda para el lote de otra **unidad** de la misma empresa, `get_lot`) · global sin contexto → `400 BR-07` y **ningún** `opening_balances` creado · situada en `A` → `201`; situada en `B` con lote de `A` → `400 BR-07` · `409` con saldo previo se conserva.

> Corrección de redacción (2026-09-09, antes de implementar): la primera versión de este `AC` decía `404` para el lote ajeno; el rojo previo mostró que la convención vigente de la superficie es `400 BR-07` (`main.py:96`). Se ajusta el `AC` a la convención existente, no el código a un `AC` inventado.

### `AC23` — S06 curvas de una línea genética
`GET /masters/genetic-lines/{id}/weight-curves`: actor `A` propia → `200` · actor `B` → `404` · global sin contexto → `404` · situada en `A` → `200`; en `B` → `404` · actor **sin empresa** → `404`. `POST /masters/weight-curves` sobre línea de `A` por la global sin contexto → `404`.

### `AC24` — S07 `GET /masters/farms/{farm_id}/houses`
Actor `A` propia → `200` con sus galpones · actor `B` → `404` · global sin contexto → `404` · situada en `A` → `200`; en `B` → `404` · actor sin empresa → `404`.

### `AC25` — S08 `GET /masters/hatcheries/{hatchery_id}/incubators`
Ídem `AC24` con planta de incubación e incubadoras.

### `AC26` — el primitivo compartido falla cerrado
`tenancy.verificar_pertenencia(company_id=None)` con `recurso_id` no nulo → `BusinessRuleViolation BR-07` («no encontrado»), en lugar de devolver sin comprobar. Consecuencia verificada en sus llamadores: `masters/service:199` (crear un galpón sobre una granja siendo autoridad global sin contexto → `400 BR-07`, antes creaba) y `verificar_ubicacion` (evento con `farm_id` por la global sin contexto → `400 BR-07`). `BusinessRuleViolation` responde `400` (`main.py:96`). Su docstring deja de afirmar la regla anterior.

## C.5 Tareas

| Tarea | Contenido | `AC` |
|---|---|---|
| `T-002-18` | pruebas **rojas** `backend/tests/test_od14_productive_surfaces.py`: fixture con empresas `A`/`B`, unidad `breeder` habilitada explícitamente en ambas, lotes, eventos, alertas, evidencias con fichero real, líneas genéticas con curva, granja+galpón y planta+incubadora por empresa; actores `A`, `B`, sin empresa, global (autoridad comprobada por `("*", …, "all")`, no por nombre); tokens situados por reclamación autorizada (`OD-11`) | `AC18–AC26` |
| `T-002-18b` | ajuste documentado de fixtures existentes que dependían del atajo retirado: `test_genetic_curves.py::test_t_037_15` creaba la curva de la empresa 2 con la autoridad global situada en la 1; pasa a crearla **situada en la 2** (patrón de `771b402`). Ninguna aserción de esa prueba cambia | `AC17.15`, `AC23` |
| `T-002-19` | S01/S02: predicado de empresa **incondicional** (cero filas con empresa efectiva nula) antes de paginación y total; el predicado de unidad se mantiene solo para actores no globales | `AC18`, `AC19`, `AC17.7/8` |
| `T-002-20` | S03/S04: comparación `evidence.company_id == empresa efectiva` **incondicional** (`403` en caso contrario) | `AC20`, `AC21` |
| `T-002-21` | S05: `get_lot` siempre (acota empresa para todos y unidad para no globales); sin rama por `is_super_admin` | `AC22` |
| `T-002-22` | S06/S07/S08: filtro por empresa efectiva **incondicional**; empresa nula → `404` | `AC23–AC25` |
| `T-002-23` | `tenancy.verificar_pertenencia`: `company_id` nulo → `BR-07`; docstring actualizado | `AC26` |
| `T-002-24` | sensibilidad, regresión, evidencia `R-139-OD14-PRODUCTIVE-DATA-EVIDENCE.md`, cierre de `WAVE A`, preflight de la fase 9 | todos |

Implementación mínima: sin refactorizar la arquitectura de autorización, sin `is_global_actor`,
sin lógica paralela; se usan los predicados y ayudantes existentes.

## C.6 Sensibilidad

| Mutación | Superficie | Qué retira | Prueba que debe caer | Validez |
|---|---|---|---|---|
| `S1` | S01 | el predicado de empresa en `get_alerts` | actor `A` ve una alerta de `B` | observar dato ajeno |
| `S2` | S02 | restaurar `if not is_super_admin` en el predicado de empresa | global situada en `A` ve eventos de `A` **y** `B` (unión > 1 empresa) | observar la unión |
| `S3` | — | `N/A`: ninguna de las ocho es `CONTROL_GLOBAL` | — | — |
| `S4` | S02 | el predicado de unidad para actores de empresa | el actor ve el evento de la unidad **deshabilitada** | observar dato de unidad apagada |
| `S5` | S01 | `require_permission("operations","read")` → `get_current_user` | actor sin permiso obtiene `200` | RBAC retirado |
| `S6` | S07 | la comprobación del padre en `get_houses_by_farm` | actor `B` lista galpones de `A` | observar dato ajeno |
| `S7` | S03/S04 | la comparación de empresa en evidencias | actor `B` descarga/borra evidencia de `A` | observar contenido ajeno |
| `S8` | `AC26` | restaurar `company_id is None → return` | prueba del primitivo y galpón creado por la global sin contexto | escritura ajena consumada |
| `S9` | S06 | el filtro de empresa en `_linea_del_usuario` | actor `B` lee curvas de `A` | observar dato ajeno |

Contabilidad separada: intentadas · inválidas inicialmente · reconstruidas · válidas.

## C.7 Regresión exigida

`RQ-03` (`test_master_tenant_isolation`, `test_user_tenant_isolation`) · `OD-14`/`R-126` ·
`OD-15`/`R-128` · `R-113` · `R-129` · `R-121` · fases 7 y 8 · guardianes (`authorization_coverage`,
`route_scope`, `transaction`, `test_rbac`, `test_pending_classification`) · suite completa ·
vitest · `tsc` (6 errores preexistentes de `R-158`, sin cambio de número).

## C.8 Definición de terminado

`AC17–AC26` verdes · rojo previo por superficie documentado con causa · `S1–S9` válidas (o `N/A`
con motivo) y revertidas · regresión completa verde · sin migración · evidencia publicada ·
`R-139 CERRADO` · `WAVE A COMPLETE` · fase 9 `TECHNICALLY READY · FROZEN`.

---

# Enmienda D · las referencias a **catálogos** de un evento son de su empresa — `R-179` (2026-09-10 · WAVE B tranche 13)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-002-D` · `TENANT ISOLATION` (escritura) · **Estado** `SPEC_READY` (pre-flight 2026-09-10) |
| **Hallazgo** | **`R-179`** (registrado P3 → **P1** normalizado, `R179_MASTER_REFERENCE_AUTHORITY_MATRIX §6`): un evento de la empresa A acepta, persiste y edita referencias a catálogos de la empresa B (`supplier_id`, `transport_id`, `cause_id`, `cull_cause_id`, `vaccine_id`, `medication_id`, `destination_plant_id`) en las **tres** superficies de mutación |
| **Reproducción** | 7 familias × `POST /operations` (`201`), `PUT` (`200`), `POST /corrections` (`201`); fila persistida `evento.company_id = A` con `suppliers.company_id = B` (matriz §3) |
| **Autoridad** | **este mismo ADDENDUM Wave 3**: «existir no basta»; «los catálogos maestros declaran `company_id` como anulable, lo que significa **global si es nulo, propio de la empresa si está fijado**, y bloquear una referencia a un catálogo compartido sería un error»; la ampliación de entonces cubrió solo las referencias **estructurales** (`lot_id`, `farm_id`, `house_id`). `R-179` extiende la misma regla, ya escrita, a los catálogos · `MASTER_DATA_BUSINESS_UNIT_SCOPE_MATRIX` (las seis familias: «compartido; `company_id`; transversal») · `MASTER_DATA_SOURCE_OF_TRUTH_MATRIX` · `RQ-03` (`TENANT` directo) |
| **Precedentes** | `R-42` (`lot_id` ajeno, P1) · `R-59` (`houses.farm_id` ajeno, P1) · `R-111` (sub-recurso por el padre) · `GA-REM-042` (proveedor y transporte en la importación de abuelas: mismo helper, alcance acotado a `grandparent_import`) |
| **Decisión del propietario** | **no requerida** (matriz §5) |
| **Migración** | **ninguna** (no se añade `company_id` a ninguna tabla; no se reclasifica ningún maestro) |
| **Fuera de alcance** | `R-180` (galpones origen/destino de los submovimientos: clase **estructural**, regla sin caso compartido) · limpieza de datos históricos (`§25` del método: prevención sin reescritura retrospectiva; si hiciera falta, remediación aparte) · estado activo del maestro (`§19`: ninguna fuente lo exige) · alcance de **unidad** de plantas e incubadoras («se deriva, no se declara») · `R-153`/`AOD-25` · `R-177`/`AOD-24` · `R-164` · `R-140`/`R-154` residuales · `R-136` SAP · `B03`/`B04`/`R-156` · `R-142` · `R-144` · `R-147` · `R-148` · ola C y KPI · fase 9 · SAP real (`P-08`) · `BU-D10` · `R-158` · rediseño de maestros |

## D.1 Regla

```
Para toda referencia de un evento (o de sus submovimientos) a un CATÁLOGO:

    master.company_id IS NULL        →  catálogo compartido        →  ACEPTADO desde cualquier empresa
    master.company_id IS NOT NULL    →  catálogo propio            →  master.company_id == empresa efectiva del evento
                                                                      si no:  400 BR-07 «<Etiqueta> no encontrado»

La empresa efectiva la deriva el SERVIDOR (sesión/contexto), nunca el cuerpo de la petición.
Catálogos derivados (incubadora-máquina, nacedora): la regla se aplica a su PADRE (`hatchery_id`).
Catálogos sin `company_id` (razas, fases productivas): PLATFORM_GLOBAL — no se convierten en tenant-owned.
```

Semántica de la denegación: la existente de `verificar_pertenencia` — el recurso ajeno **se comporta como inexistente** (`AC26`, anti-enumeración); no se
distingue «no existe» de «no es tuyo».

## D.2 Alcance (matriz §4)

| Campo | Recurso | Clase | Regla |
|---|---|---|---|
| `supplier_id` · `transport_id` · `cause_id` · `cull_cause_id` · `vaccine_id` · `medication_id` · `destination_plant_id` | `suppliers` · `transports` · `mortality_causes` · `cull_causes` · `vaccines` · `medications` · `processing_plants` | `TENANT_OWNED_NULLABLE` | D.1 |
| `feed_movements[].feed_type_id` · `hatchery_params[].hatchery_id` | `feed_types` · `hatcheries` | ídem | D.1 |
| `hatchery_params[].incubator_id` · `hatcher_id` | `incubators` · `hatchers` | `TENANT_DERIVED` | D.1 sobre `hatchery_id` del padre |
| `bird_movements[].breed_id` | `breeds` | `PLATFORM_GLOBAL` (sin `company_id`) | **ninguna** (control negativo) |
| `lot_id` · `farm_id` · `house_id` · `destination_farm_id` · `sap_document_ref` | — | estructural / SAP | **sin cambio** (ya cubiertos: `R-42`, addendum Wave 3, `R-173`, `GA-REM-035`) |

## D.3 Superficies

1. **Alta** (`POST /operations`): en `_apply_business_rules`, junto a `verificar_ubicacion`, antes de las reglas de saldo.
2. **Edición** (`PUT /operations/{id}`): en `verificar_destino_de_edicion` → `_reglas_puras_del_candidato`, sobre el **estado candidato** (`R-176`): solo se
   valida la FK que cambia; una FK no mencionada no se revalida ni se arrastra como defecto (`§24`: sin limpieza retrospectiva inventada).
3. **Corrección** (`POST /corrections`): por la misma guarda central (los campos de FK ya pasan por ella desde `GA-REM-042`).
4. Submovimientos: solo en el alta (no son editables ni corregibles, `GA-REM-005-B`).

## D.4 Criterios de aceptación

| AC | Criterio |
|---|---|
| `AC-R179-01` | control: las siete familias con maestro **de la propia empresa** → `201`, FK persistida |
| `AC-R179-02` | alta con maestro de otra empresa, familia por familia → `400 BR-07`; cero filas, cero auditoría de alta |
| `AC-R179-03` | `PUT` de la FK a un maestro ajeno → `400 BR-07`; FK y evento intactos |
| `AC-R179-04` | `POST /corrections` de la FK a un maestro ajeno → `400 BR-07`; cero `correction_logs` |
| `AC-R179-05` | toda denegación: evento intacto (FK, estado, versión), sin auditoría de éxito, sin efecto |
| `AC-R179-06` | **control positivo**: catálogo compartido (`company_id IS NULL`) aceptado desde cualquier empresa |
| `AC-R179-07` | suplantación: declarar otra empresa en el contexto no autoriza el maestro ajeno |
| `AC-R179-08` | `feed_type_id` y `hatchery_id` ajenos → `400 BR-07` |
| `AC-R179-09` | `incubator_id`/`hatcher_id` cuya incubadora es ajena → `400 BR-07` |
| `AC-R179-10` | control negativo: `breed_id` (global) sigue aceptándose |
| `AC-R179-11` | `GA-REM-042` intacto: la importación exige proveedor y transporte de la empresa |
| `AC-R179-12` | autoridad global situada en A: mismo contrato |

## D.5 Tareas

| Tarea | Descripción |
|---|---|
| `T-002-D1` | pruebas rojas `tests/test_master_reference_tenancy.py` (prefijo `MAES-`; empresas A y B con las siete familias + un catálogo compartido `company_id NULL` + raza global; actor de A, actor de B, autoridad global) |
| `T-002-D2` | `tenancy.py`: `verificar_catalogo_de_empresa(db, modelo, recurso_id, company_id, etiqueta)` — acepta `company_id IS NULL`, exige igualdad si está fijado; y `verificar_catalogos_del_evento(...)` que aplica el mapa campo → modelo |
| `T-002-D3` | `operations/service.py`: llamada en `_apply_business_rules` (alta, incluidos submovimientos) y en `_reglas_puras_del_candidato` (edición y corrección) |
| `T-002-D4` | sensibilidad `R179-S1…S6`; regresión `GA-REM-042`, `R-173`, `R-176`, `R-178`, `R-42`/`R-59`/`RQ-03`, maestros, operaciones; evidencia; cierre |

## D.6 Definición de terminado

`AC-R179-01…12` verdes · rojo válido leído en `a93d4d1` · sensibilidad válida (incluido el sobre-bloqueo `S5`) · regresión completa **leída** · sin migración ·
`R-179` cerrado (técnico) · `R-180` registrado.
