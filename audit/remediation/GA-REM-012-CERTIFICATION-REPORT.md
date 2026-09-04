# GA-REM-012 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-012` — Cambio de contraseña |
| **Wave** | 2 · **Stage 3** · **Hallazgo** `P0-13` |
| **Fecha** | 2026-09-04 |
| **Estado final** | **`CERTIFIED`** |

## Original finding

`PUT /users/{id}` con `{password}` devolvía `200`, la interfaz mostraba «contraseña
actualizada» y **la contraseña no cambiaba**: la anterior seguía autenticando. `UserUpdate`
no declaraba el campo y Pydantic lo descartaba antes de llegar al servicio.

Severidad **P0**: toda rotación de credencial tras una sospecha de compromiso era ficticia.

## Evidence

```
[1] alta de usuario                        -> 201
[2] PUT /api/v1/users/4 {"password": ...}  -> 200   <- la API confirma
[3] login con la contraseña NUEVA          -> 401   <- la nueva no sirve
[4] login con la contraseña ORIGINAL       -> 200   <- la vieja sigue viva
```

## Matriz de flujos de contraseña

| Flow | Endpoint | Actor | Requires Current Password | Hash | Persistence | Token Impact | UI |
|---|---|---|---|---|---|---|---|
| Alta | `POST /users` | admin | no | bcrypt | ✅ | — | `UsersPage` |
| **Cambio propio** | `POST /users/{id}/password` | el titular | **sí** | bcrypt | ✅ | ninguno (ver `AC08`) | `ProfilePage` |
| **Restablecimiento** | `POST /users/{id}/password` | Super Admin | **no** | bcrypt | ✅ | ninguno | `UsersPage` |
| Edición de usuario | `PUT /users/{id}` | admin | — | — | **rechaza `password` con 422** | — | `UsersPage` |
| Siembra | `seeds/*.py` | — | no | bcrypt | ✅ | — | — |

**Recuperación de contraseña: no existe** en el backend. No se inventa un flujo que ninguna
fuente describe.

## Implementation

Endpoint dedicado, no un campo más de `UserUpdate`: admitirlo allí sin control abriría un
vector de toma de cuentas, y así lo advertía la propia spec.

`UserUpdate` declara `extra="forbid"`. Es la diferencia entre rechazar y descartar en
silencio: quien envíe `password` recibe un `422` explícito. La misma clase de fallo que
`P0-14`, cerrada por contrato.

Autorización: el titular con su contraseña actual, o un administrador sin ella. Hoy se apoya
en `is_super_admin`, la única señal disponible cuando se escribió; `GA-REM-002` la sustituye
por el permiso `users:update`.

Política `RR-05` (Wave 1.5): longitud mínima **8**, idéntica en alta, cambio y
restablecimiento. El `min_length=6` del login no es una política —restringe un intento de
autenticación, no la creación de un secreto— y se deja como está.

Frontend: `ProfilePage` usa el endpoint dedicado, **envía la contraseña actual que ya
recogía y no usaba**, aplica el mínimo de 8 y muestra el mensaje del servidor en lugar de un
texto fijo. `UsersPage` deja de enviar la contraseña en el cuerpo de edición.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| `AC01` | El cambio surte efecto | ✅ la nueva autentica, la anterior deja de servir |
| `AC02` | Se exige la contraseña actual | ✅ sin ella y con ella incorrecta: 400, y la contraseña no cambia |
| `AC03` | Sin falsos positivos en la interfaz | ✅ `PUT` con `password` da 422; la UI muestra el error del servidor |
| `AC04` | Política única | ✅ 7 caracteres se rechaza en alta **y** en cambio; 8 se acepta en ambos |
| `AC05` | Aislamiento entre usuarios | ✅ un operador que intenta cambiar la de otro recibe 403 |
| `AC06` | Restablecimiento por administrador | ✅ sin aportar la anterior; auditado con ambos usuarios |
| `AC07` | Auditoría sin secretos | ✅ entrada `user_password`; ni la contraseña ni el hash aparecen |
| `AC08` | Comportamiento de las sesiones | ✅ **documentado**: los JWT son sin estado y las sesiones previas siguen vivas hasta expirar |

### Sobre `AC08`

No hay lista de revocación: un token emitido antes del cambio sigue siendo válido hasta que
caduca. Se documenta porque **un usuario que rota su contraseña tras una sospecha de
compromiso espera lo contrario**. El test fija el comportamiento actual para que el cambio
sea visible cuando `GA-REM-003` aborde la revocación. No se simula una garantía que el
sistema no da.

## Tests

`tests/test_p013_password.py` — **11 PASS · 0 FAIL** (`T-012-01` … `T-012-08`).

## Files changed

```
backend/app/auth/schemas.py     PasswordChangeRequest; UserUpdate con extra="forbid"
backend/app/auth/service.py     change_password con auditoría
backend/app/auth/router.py      POST /users/{user_id}/password
backend/tests/test_p013_password.py   nuevo
frontend/src/pages/users/ProfilePage.tsx   endpoint dedicado, contraseña actual, mínimo 8
frontend/src/pages/users/UsersPage.tsx     deja de enviar password en la edición
frontend/public/locales/{es,en}/translation.json   mensajes actualizados
```

## Hallazgo anotado

`R-37`: `audit_logs.company_id` no admite nulos y varias ayudas de auditoría usan `0` como
relleno, que no existe como compañía. Un usuario sin compañía rompe la inserción. Destino
`GA-REM-019`.

## Final status

**`CERTIFIED`.** El cambio de contraseña cambia la contraseña, lo dice solo cuando es
cierto, y ningún camino puede volver a responder éxito sin haber hecho nada.
