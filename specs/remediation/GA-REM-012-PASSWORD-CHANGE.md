# GA-REM-012 — CAMBIO DE CONTRASEÑA

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-012` · **Tipo** `SECURITY + BUGFIX SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** — falso positivo de seguridad · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · `GA-REM-003` (política de sesión) · `GA-REM-002` (quién puede cambiar la contraseña de quién) |
| **Hallazgos** | P0-9 · S-07 · `GA-TD-012` |
| **Revalidado** | 2026-09-03 — `UserUpdate` (`auth/schemas.py:42-49`) **no declara `password`** |

## Problema
El cambio de contraseña **no funciona y anuncia éxito**. `ProfilePage` envía `PUT /users/{id}` con `{password}`; el esquema `UserUpdate` no declara ese campo, Pydantic lo descarta, `update_user` recibe un diccionario vacío por `exclude_unset=True` y no modifica nada. El servidor responde 200 y la interfaz muestra «Contraseña actualizada».

**Ningún usuario puede cambiar su contraseña después del alta, y cree que lo ha hecho.**

## Evidencia
| Ítem | Ruta |
|---|---|
| Esquema sin `password` | `backend/app/auth/schemas.py:42-49` |
| Servicio que aplica solo lo declarado | `backend/app/auth/service.py:136-138` — `data.model_dump(exclude_unset=True)` |
| Cliente que envía y celebra | `frontend/src/pages/users/ProfilePage.tsx:24-26` |
| El alta sí exige contraseña | `auth/schemas.py:38-39` — `UserCreate.password: str = Field(..., min_length=8)` |
| No se pide la contraseña actual | `ProfilePage.tsx` mantiene un campo `currentPassword` que **nunca se envía** |

## Comportamiento actual
```
PUT /users/{id} {password: "nueva"}
  → UserUpdate descarta el campo desconocido
  → update_data = {}  → ningún setattr
  → 200 OK
  ⇒ la contraseña NO cambia; la interfaz dice que sí
```

## Comportamiento esperado
```
usuario autenticado → contraseña actual → contraseña nueva → confirmación
  → backend valida la actual → aplica política → hashea → persiste
  → decide sobre la sesión activa y las sesiones abiertas
```

## Alcance
1. Endpoint dedicado para el cambio de contraseña propia, con verificación de la contraseña actual.
2. Política de complejidad **explícita y documentada**. Hoy el alta exige 8 caracteres (`UserCreate`) y el frontend exige 6 (`ProfilePage.tsx:20`): **incoherencia a resolver**.
3. Comportamiento sobre la sesión actual y sobre las demás sesiones tras el cambio (se apoya en `GA-REM-003`).
4. Diferenciar cambio propio de restablecimiento por un administrador, con permisos distintos.
5. Retroalimentación honesta en la interfaz: nunca declarar éxito sin confirmación del servidor.
6. Auditar el cambio de contraseña.

## Fuera de alcance
Recuperación de contraseña por correo (no hay canal de correo implementado; backlog) · MFA · política de expiración periódica · SSO.

## `RC-05` RESUELTO POR EVIDENCIA — regla `RR-05`
Resuelto el 2026-09-03 (`audit/remediation/REQUIREMENT_CONFLICT_RESOLUTION.md §6`). El conflicto era **aparente**: los números discrepantes se aplican a operaciones distintas que nunca compitieron. `auth/schemas.py:11` (`min_length=6`) y `LoginPage.tsx:14` restringen la **entrada de un intento de login**, no la creación de un secreto; `ProfilePage.tsx:21` valida una operación que no existe. La única declaración de política del sistema es `auth/schemas.py:39`, `min_length=8`. Ninguna fuente por encima de la implementación —cliente, `docs/**`, `specs/**`— enuncia política alguna de contraseñas.

> **`RR-05`.** Política única: longitud mínima de **8** caracteres, idéntica en el alta, en el cambio por el propio usuario y en el restablecimiento por un administrador. El *login* no impone longitud mínima: valida credenciales, no políticas. El cambio debe ser una operación explícita, con verificación de la contraseña actual cuando el usuario cambia la propia, y **no puede aceptarse en silencio**.

**Complejidad, caducidad e histórico** quedan como `OD-01` (`OWNER_DECISION_REQUIRED`) y **no bloquean esta spec**: ninguna fuente los exige y su ausencia es una oportunidad de endurecimiento, no un conflicto.

## `P0-13` — el cambio de contraseña se descarta en silencio
Confirmado **en ejecución** contra la base de pruebas aislada (Wave 1.5). `ProfilePage.tsx:24` envía `PUT /api/v1/users/{id}` con `{ password }`. `UserUpdate` (`auth/schemas.py:42-49`) **no declara `password`** y no fija `model_config`, por lo que rige `extra="ignore"` de Pydantic v2: el campo se descarta antes de llegar al servicio. `update_user` hace `data.model_dump(exclude_unset=True)` (`auth/service.py:136`) y nunca ve la clave. La API responde **`200 OK`** y la interfaz muestra `profile.passwordUpdated`.

```
[1] alta de usuario                        -> 201
[2] PUT /api/v1/users/4 {"password": ...}  -> 200   <- la API confirma
[3] login con la contrasena NUEVA          -> 401   <- la nueva no sirve
[4] login con la contrasena ORIGINAL       -> 200   <- la vieja sigue viva
```

Alcanza también a `UsersPage.tsx:26`, que envía `password` al editar un usuario. Severidad **P0**: toda rotación de credencial tras una sospecha de compromiso es ficticia.

Colateral enlazado a `GA-REM-002`, no ampliado aquí: **`R-25`** — `PUT /api/v1/users/{id}` no comprueba autorización más allá de estar autenticado (`auth/router.py:88-95`), de modo que cualquier usuario válido puede modificar el registro de cualquier otro.

## Reglas de negocio afectadas
Ninguna del dominio avícola.

## Backend afectado
`auth/router.py` (nuevo endpoint), `auth/service.py` (verificación y hasheo), `auth/schemas.py` (esquema de cambio de contraseña), `audit/helpers.py` (registro).

## Frontend afectado
`pages/users/ProfilePage.tsx` — enviar `currentPassword`, alinear la política, no anunciar éxito sin confirmación. `pages/users/UsersPage.tsx` para el restablecimiento por administrador.

## Base de datos afectada
Ninguna. `users.hashed_password` ya existe.

## Seguridad
Cierra `S-07` (P1) y elimina un falso positivo que erosiona la confianza en el sistema. **Importante**: con `GA-REM-002` sin cerrar, hoy cualquier usuario autenticado podría cambiar la contraseña de cualquier otro a través de `PUT /users/{id}` si el campo llegara a añadirse sin control. Esta spec **no debe** añadir `password` a `UserUpdate` sin el permiso correspondiente.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Contraseña actual incorrecta | 400 o 403 sin cambiar nada; mensaje que no revele si el usuario existe |
| Nueva contraseña igual a la actual | rechazo con mensaje explícito |
| Nueva contraseña que incumple la política | rechazo indicando el requisito incumplido |
| Confirmación que no coincide | validación en cliente **y** en servidor |
| Cambio de contraseña de otro usuario sin permiso | 403 |
| Restablecimiento por administrador | permitido con permiso; **no** exige la contraseña actual del titular; queda auditado |
| Sesiones abiertas tras el cambio | comportamiento definido en la spec y coherente con `GA-REM-003` |
| Usuario inactivo | rechazo |

## Acceptance Criteria

**AC01 — El cambio surte efecto**
```
Given un usuario autenticado con contraseña conocida
When  cambia su contraseña aportando la actual y una nueva válida
Then  la respuesta es 200
And   puede autenticarse con la nueva contraseña
And   no puede autenticarse con la anterior
```
**AC02 — Se exige la contraseña actual**
```
Given un usuario autenticado
When  intenta cambiar su contraseña sin aportar la actual o aportándola incorrecta
Then  la operación se rechaza
And   la contraseña no cambia
```
**AC03 — Sin falsos positivos en la interfaz**
```
Given una petición de cambio de contraseña que el servidor rechaza
When  el usuario observa la interfaz
Then  ve un mensaje de error, nunca "Contraseña actualizada"
```
**AC04 — Política de complejidad única**
```
Given la política `RR-05` (longitud mínima 8, única para alta, cambio y restablecimiento)
When  se intenta una contraseña que la incumple, desde la interfaz o directamente contra el API
Then  ambas la rechazan con el mismo criterio
```
**AC05 — Aislamiento entre usuarios**
```
Given un usuario sin permiso de administración de usuarios
When  intenta cambiar la contraseña de otro usuario
Then  recibe 403
```
**AC06 — Restablecimiento por administrador**
```
Given un usuario con permiso users:update
When  restablece la contraseña de otro usuario
Then  la operación tiene éxito sin aportar la contraseña previa del titular
And   queda registrada en la auditoría con ambos usuarios identificados
```
**AC07 — Auditoría**
```
Given un cambio de contraseña realizado
When  se consulta la auditoría
Then  aparece una entrada con usuario, fecha y tipo de acción
And   no contiene la contraseña ni su hash
```
**AC08 — Comportamiento de las sesiones**
```
Given un usuario con dos sesiones activas
When  cambia su contraseña
Then  el comportamiento de ambas sesiones coincide con lo documentado en esta spec
```

## Tests requeridos
`T-012-01..08` para AC01–AC08 (integración) · `T-012-09` E2E: cambiar la contraseña, cerrar sesión y entrar con la nueva.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Añadir `password` a `UserUpdate` sin control abre un vector de toma de cuentas | endpoint dedicado, no reutilizar `UserUpdate`; AC05 lo verifica |
| Elevar la política deja fuera contraseñas existentes | la política aplica a contraseñas nuevas; se coordina con la rotación de `GA-REM-004` |

## Rollback lógico
Reversible por commit. Las contraseñas cambiadas **no** se revierten.

## Definition of Done
- [x] `RC-05` resuelto (`RR-05`) · [ ] `P0-13` corregido y cubierto por test · [ ] AC01–AC08 verificados · [ ] Tests en verde · [ ] Endpoint dedicado con permiso · [ ] Certification report
