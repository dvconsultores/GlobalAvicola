# `R-129` · A QUIÉN CONCEDER, SIN `users:read`

`GA-REM-040` enmienda F · `T-040-38` · `AC-H15` · `AC-H16` · 2026-09-09

```
R-129  =  CERRADO
ROJO PREVIO      12 de 14 · los dos que pasaban eran los controles de la frontera real
VERDE            14 / 14  ·  backend 784 passed · 49 skipped  ·  frontend 87
SENSIBILIDAD     8 válidas · 8 detectadas · 0 intentos inválidos · 2 N/A con motivo
MIGRACIÓN        ninguna  ·  FRONTEND  0 ficheros  ·  users:read  NO
```

---

## 1. El requisito raíz, y de dónde viene

`OD-15 §6` negó `users:read` al `Administrador de Accesos` **a propósito**: `users:*` es el
conjunto que mantuvo cuatro `P0` latentes. La consecuencia funcional es que la pantalla de la
fase 9 (`T-040-22`, `AC-H05`) no tenía a quién ofrecerle. Eso es `R-129`.

```
DESCUBRIR A QUIÉN CONCEDER   ≠   ADMINISTRAR USUARIOS
```

Se enmendó `GA-REM-040` (enmienda F) y no se creó remediación nueva: la autoridad ya existía.
Faltaba la superficie.

## 2. La superficie

```
GET /business-units/{code}/grant-candidates
permiso      business_units:create      ← la autoridad de conceder ES la de saber a quién
alcance      INQUILINO · plano de control · `OD-14.c`
empresa      la efectiva, en la consulta — nunca del cliente
contrato     list[CandidatoRead] · user_id · username · display_name · already_granted
```

Sin parámetro de búsqueda ni de identificador **a propósito**. Lo único que se puede pedir es
«los de mi empresa para esta unidad», de modo que no hay oráculo que consultar: la prueba `C3`
envía el nombre y el identificador exactos de un usuario ajeno y no vuelve nada.

## 3. Elegibilidad: la del `POST`, no una nueva

La superficie **refleja** las puertas de `conceder` en vez de inventar otras:

| Puerta | En `conceder` | En candidatos |
|---|---|---|
| unidad desconocida | `404` | `404` |
| unidad apagada para la empresa | `409` | `409` — no hay a quién concederla |
| usuario de otra empresa | `404` | ausente |
| usuario inactivo | — | ausente: no puede recibir nada útil |
| el propio actor | `403` (`OD-15.a`) | ausente — **cortesía, no seguridad** |
| ya tiene la unidad | idempotente | presente, marcado `already_granted` |

**Por qué se incluye a quien ya la tiene.** Ocultarlo haría indistinguible «nunca se le dio» de
«ya la tiene» — la misma confusión que `AC-H11` separa entre concedidas y efectivas. Se devuelve
marcado y la interfaz decide.

**Por qué la exclusión del actor no es seguridad.** `C11` se envía a sí mismo al `POST` a mano y
recibe `403`; `C12` envía a un ajeno y recibe `404` con cero filas. Filtrar candidatos no es la
frontera. La frontera es la concesión, y existía antes que esta superficie — por eso `C11` y
`C12` ya pasaban en rojo.

## 4. `AC-H16` · el contraste obligatorio

```
mismo actor · misma sesión
GET …/grant-candidates    200
GET /users                403
/me → permissions         sin users:read
```

Sin este contraste la superficie sería `users:read` con otro nombre y habrían vuelto por la
puerta de atrás los cuatro `P0` que `OD-15 §6` cerró.

## 5. La autoridad global · `OD-14`

```
situada en A     candidatos de A · no de B
situada en B     candidatos de B · no de A
sin contexto     403 — no la unión
```

## 6. Sensibilidad · 8 válidas, 8 detectadas

Cada una con huella verificada antes de ejecutar, y dos con la aserción real inspeccionada.

| # | Mutación | Huella | Prueba | Resultado |
|:--:|---|:--:|---|:--:|
| `S1` | el rol sembrado recibe `users:read` | 1 | `s06` conjunto exacto (constante importada) | **1 failed** |
| `S2` | sin predicado de empresa en la consulta | 1 | `C1` · `C6` | **2 failed** |
| `S3` | confiar en parámetro de empresa | — | — | **N/A** — no existe tal parámetro |
| `S4` | contrato → `UserRead` y el servicio sirve la fila | 1 | `C8` proyección exacta | **1 failed** ✔ verificada |
| `S5` | quien tiene `lots:read` pasa a poder conceder | 1 | `C4/C5` | **1 failed** |
| `S6` | sin contexto → todos los candidatos (tres puertas) | 1 | `C7` | **1 failed** ✔ verificada |
| `S7` | el actor se ofrece a sí mismo | 1 | `C1` | **1 failed** |
| `S8` | filtrar después de paginar | — | — | **N/A** — no hay paginación |
| `S9` | la marca `already_granted` se invierte | 1 | `C9` | **1 failed** |
| `S10` | autoridad por nombre de rol | 1 | `C4/C5` | **1 failed** |

### `S4` y `S6`, inspeccionadas y no solo contadas

`§48` exige probar que la propiedad se retiró, no que el test falló. Un `500` habría producido
rojo igualmente y no habría probado nada. Se reinstalaron las dos y se leyó la aserción:

```
S4   200 · campos inesperados: email · phone · role_id · is_super_admin · last_login · …
     → la proyección mínima se retiró de verdad
S6   200 · diez candidatos: A, B y los usuarios sembrados de prueba
     → sin contexto devolvió la UNIÓN de inquilinos, que es exactamente el fail-open
```

```
VÁLIDAS FINALES          8
INTENTOS INVÁLIDOS       0
N/A CON MOTIVO           2
CONTADAS SIN SER VÁLIDAS 0
```

## 7. Lectura pura

`C13` cuenta filas de concesión y auditoría antes y después de pedir candidatos: iguales.

## 8. Lo que **no** se hizo, y por qué

```
NO  users:read al Administrador de Accesos — `OD-15 §6`, y `AC-H16` lo vigila
NO  paginación ni total — la empresa cabe entera; `S8` queda N/A y no fingida
NO  buscador — sin parámetro no hay oráculo; `S3` queda N/A y no fingida
NO  correo, teléfono, rol, permisos — cada campo de más es un pedazo de `users:read`
NO  capacidad de sesión `can_select_users` — `business_units:create` ya lo dice
NO  frontend — la fase 9 no ha empezado
```

## 9. Un error de esta tanda que conviene dejar escrito

El primer commit de `R-129` (`eb10739`) se hizo con la regresión en **rojo**: un conteo fijo de
rutas que yo mismo había escrito en la fase 7 seguía en seis, y `R-129` añadió la séptima. Leí
mal la cifra y el mensaje dice «784 passed» cuando la ejecución tenía 1 fallo. No se empujó
nada en rojo; se rectificó en `21e7423` en lugar de reescribir historia, y la regresión se
repitió entera antes de cualquier push: **784 passed · 0 failed**, esta vez de verdad.

El conteo fijo era correcto y se mantiene fijo: un `>=` habría dejado pasar una ruta colada sin
contrato. Lo que falló fue el orden — leer antes de escribir.
