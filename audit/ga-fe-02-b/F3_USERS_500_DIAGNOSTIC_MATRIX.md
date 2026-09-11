# F3 · USERS 500 — MATRIZ DIAGNÓSTICA

**2026-09-11 · ENV-01 · runtime `index--DbCa8Hk.js` · Sesión: `admin` (super) situado en empresa 1
(salvo donde se indique) · Sin borrado, sin cambios de credenciales.**

## 1 · Reproducción runtime (pre-reparación)

| Prueba | Resultado |
|---|---|
| `GET /users?skip=0&limit=5` | **200** (ids 2–6) |
| `GET /users?skip=0&limit=6..9` | **200** |
| `GET /users?skip=0&limit=10` (y 12/14/16/18/20/30/100) | **500 Internal Server Error** |
| `GET /users?skip=9&limit=1` (la 10.ª fila del scope) | **500** |
| `GET /users/{2..10}` | **200** |
| `GET /users/{11..56}` | 404 (fuera de la empresa efectiva) |
| `GET /users/{57..70}` | **500** (14 ids consecutivos) |
| `GET /users/{71..120}` | 404 |

Scope empresa 1 = ids 2–10 (9 legibles) + **57–70 (14 ilegibles)** = 23 filas; cualquier página
que incluya una fila 57–70 → 500. El listado por defecto (limit 20) siempre las incluye ⇒
`UsersPage` inutilizable.

## 2 · Locus de serialización — prueba local (venv del backend, mismo esquema desplegado)

```
LOCAL REJECTED(check_deliverability=False): The part after the @-sign is a special-use
                                           or reserved name that cannot be used with email.
REAL ACCEPTED(check_deliverability=False)
USERREAD_LOCAL FAIL: ValidationError 1 validation error for UserRead — email —
  value is not a valid email address: The part after the @-sign is a special-use or
  reserved name that cannot be used with email. [type=value_error,
  input_value='web.contralor@testing.local', input_type=str]
USERREAD_FIXED OK
```

- `UserRead.email: Optional[EmailStr]` (`backend/app/auth/schemas.py`) — `None` es válido; una
  cadena en dominio reservado **no**.
- pydantic valida con `check_deliverability=False` (sin DNS); el rechazo de dominios
  special-use ocurre siempre. Reproducido con `email-validator` + `UserRead.model_validate`
  exactamente como los usa el backend desplegado.

## 3 · Origen de las filas (fuente)

`backend/seeds/integration_seeds.py` → `USERS_DEF` (14 usuarios):

| # | username (según seed) | view_type | email generado (seed) |
|---|---|---|---|
| 1 | `movil.progenitoras` | mobile | `movil.progenitoras@testing.local` |
| 2 | `movil.reproductoras` | mobile | `movil.reproductoras@testing.local` |
| 3 | `movil.incubadora` | mobile | `movil.incubadora@testing.local` |
| 4 | `movil.engorde` | mobile | `movil.engorde@testing.local` |
| 5 | `movil.multiproceso` | mobile | `movil.multiproceso@testing.local` |
| 6 | `movil.supervisor` | mobile | `movil.supervisor@testing.local` |
| 7 | `movil.contralor` | mobile | `movil.contralor@testing.local` |
| 8 | `web.progenitoras` | web | `web.progenitoras@testing.local` |
| 9 | `web.reproductoras` | web | `web.reproductoras@testing.local` |
| 10 | `web.incubadora` | web | `web.incubadora@testing.local` |
| 11 | `web.engorde` | web | `web.engorde@testing.local` |
| 12 | `web.multiproceso` | web | `web.multiproceso@testing.local` |
| 13 | `web.supervisor` | web | `web.supervisor@testing.local` |
| 14 | `web.contralor` | web | `web.contralor@testing.local` |

**Correspondencia esperada** (a verificar fila a fila en la reparación, mediante la respuesta del
propio `PUT`): ids **57–63** = móviles (orden del seed) · ids **64–70** = web (orden del seed).

`baseline_seeds` documenta el invariante en el comentario de `ADMIN`: «Dominio real y no reservado:
`EmailStr` rechaza .test/.example/.local y el usuario resultaría ilegible por la API». Estas filas
violan ese invariante: **fixture malformada**, no dato de negocio válido.

## 4 · Clasificación (§19)

```
CLASIFICACIÓN ........ DATA (fixture malformada; seed drift)
¿CÓDIGO? ............. NO para el runtime de producto (el rechazo es el comportamiento correcto
                       del contrato); SÍ un endurecimiento en seeds (evitar recreación, §38)
¿BORRADO? ............ PROHIBIDO y no necesario — las filas son usuarios legítimos de prueba
REPARACIÓN ........... mínima: corregir SOLO el dominio del email (API oficial PUT /users/{id}),
                       conservando parte local (username); reversible
CREDENCIALES ......... intactas (el PUT solo transporta email)
```

## 5 · Plan de reparación por fila (trace §20)

Por cada id 57–70: **(a) BEFORE** = `GET /users/{id}` → 500 (registrado); **(b) EXPECTED** =
`{username}@globalavicola.com` (dominio válido, único, ya usado por otras cuentas ENV-01);
**(c) CHANGE** = `PUT /users/{id}` `{"email": "..."}` → `200` con `UserRead` (verifica además que el
`username` devuelto coincide con el esperado del seed — si no coincide: **STOP** y reconciliar la
correspondencia antes de seguir); **(d) AFTER** = `GET /users/{id}` → 200. Todo queda en
`GA_FE_02_B_ENV01_MUTATION_LEDGER.md`.

## 6 · Postcondición

`GET /users` default y `limit=100` → 200 sin 500 · cada 57–70 → 200 · tenant/rol sin cambio ·
ninguna credencial tocada · seed endurecido + regresión añadida.

## 7 · Reparación ejecutada (2026-09-11) — RESULTADO

| Fase | Resultado |
|---|---|
| BEFORE | 500 ×14 (ids 57–70; registrado en `/tmp/ga_f3_before.txt`) |
| Reparación | `PUT /users/{id}` `{"email":"<username>@globalavicola.com"}` ×14 → **200** en todas; `username` devuelto = esperado del seed en **14/14** (57–63 móviles · 64–70 web) |
| AFTER | `GET /users/{id}` → **200 ×14**; `GET /users?limit=100` → **200** (23 filas); default → **200** |
| Invariantes | company_id=1 y role_id originales intactos (spot 57: rol 28; spot 70: rol 33); `view_type` intacto; `is_active` intacto; 14 emails únicos; **cero** credenciales tocadas |
| Endurecimiento | `b83d908` — `integration_seeds` con dominio válido + `test_seed_email_domains.py` (guarda R-44); grep de dominios reservados en seeds: 0 |

Nota de ejecución: un primer barrido accidental usó un token **sin contexto de empresa** (403 fail-closed)
y el guard de correspondencia cortó sin ninguna mutación; la reparación se ejecutó de nuevo con la
sesión situada en la empresa 1 (`switch-company`).
