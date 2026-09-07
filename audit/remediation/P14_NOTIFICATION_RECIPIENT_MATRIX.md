# `P-14` · A QUIÉN LLEGA CADA NOTIFICACIÓN

`docs/02 §3.14` · `docs/10 §6.2` · `OD-08` · `GA-REM-038`

---

## 1. La decisión

```
OD-08 · destinatarios de las notificaciones internas de P-14

  1. la persona que cargó/registró la data que originó el evento
  2. los usuarios administradores de la empresa correspondiente
  3. los usuarios con función de contraloría / contralor
  4. el gerente del área correspondiente
  5. el supervisor correspondiente

  ámbito: MISMA EMPRESA · y misma área cuando la arquitectura la tenga
```

## 2. La regla, en una línea

```
DESTINATARIOS = destinatarios explícitos de fuentes anteriores
              ∪ originador ∪ administradores ∪ contraloría ∪ gerente ∪ supervisor
              filtrado por  user.company_id == evento.company_id  y  user.is_active
              DISTINCT por user_id
```

**La unión no resta.** `OD-08` amplía; no retira lo que otra fuente exigía. «Notificar al
operador» de `docs/02 §3.14` y «Notificar al rol Analista SAP» de `docs/10 §6.2` siguen en pie
y se suman a los cinco términos nuevos.

**Una persona, un aviso.** Quien sea a la vez quien cargó el dato, administrador y supervisor
recibe **una** notificación, no tres. La deduplicación la impone el backend, no la pantalla.

## 3. La matriz

| Event | Explicit prior recipient | Uploader | Admin | Contralor | Area manager | Supervisor | Final rule |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| **Registro pendiente de revisión > 24h** | — | ✅ `registered_by_id` | ✅ | ✅ | ⛔ sin modelo | ✅ | unión `OD-08`, empresa del evento |
| **Registro rechazado (notificar al operador)** | **el operador** — `docs/02 §3.14` | ✅ (es el mismo) | ✅ | ✅ | ⛔ | ✅ | operador ∪ `OD-08` |
| **Mortalidad > umbral configurable** | — | ✅ | ✅ | ✅ | ⛔ | ✅ | unión `OD-08` |
| **Peso fuera de estándar** | — | ✅ | ✅ | ✅ | ⛔ | ✅ | unión `OD-08` |
| **Error de envío SAP** | **rol `Analista SAP`** — `docs/10 §6.2` | ✅ los que registraron los eventos consolidados | ✅ | ✅ | ⛔ | ✅ | `Analista SAP` ∪ `OD-08` |
| **Lote próximo a cierre** | — | — | — | — | — | — | **sin disparador** — `BLOCKED_BY_OWNER_DECISION` |

`⛔` = no hay modelo de área ni rol de gerencia. Detalle en `P14_OD08_ROLE_MAPPING_MATRIX.md §5`.

## 4. En el rechazo, actor y destinatario siguen sin ser el mismo

`BR-14` exige segregación: quien rechaza no puede ser quien registró. `OD-08` no cambia eso —el
operador sigue siendo destinatario por su papel de originador— pero sí añade a quien rechaza
**si además** es administrador, contralor o supervisor de esa empresa.

Es correcto y es lo que la decisión dice: un supervisor que rechaza un registro se entera de
que se rechazó. Lo que la prueba comprueba es que el operador **siempre** está, no que el actor
nunca esté.

## 5. El originador de cada evento, campo por campo

`§8` del encargo lo pide explícitamente: el destinatario sale del **dato persistido**, nunca de
quien esté autenticado cuando se genera el aviso —que puede ser otra persona, u otro momento—.

| Evento | Cómo se resuelve el originador |
|---|---|
| `> 24h`, rechazo, mortalidad, peso | `OperationalEvent.registered_by_id` — obligatorio, nunca nulo |
| error de envío SAP | `SapPayload → ConsolidatedMovement.event_ids → OperationalEvent.registered_by_id` de cada uno |

**No hace falta ningún campo nuevo.** No procede el hallazgo de `§9` («falta trazabilidad del
originador»): los cinco eventos accionables lo tienen.

## 6. `Super Administrador` no entra por ser administrador

`OD-08` dice «administradores **de la empresa correspondiente**». El Super Administrador se
siembra sin empresa (`company_id = None`), de modo que no pertenece a ninguna. Se le aplica la
misma condición que a todos: pertenecer a la empresa del evento.

Sin esa condición, un usuario de plataforma recibiría el detalle operativo de todas las
empresas — la fuga que `§6` del encargo advierte.

## 7. Lo que sigue sin resolverse

```
gerente del área    BLOCKED_BY_MODEL_GAP   no hay áreas, ni rol de gerencia
                                            (P14_OD08_ROLE_MAPPING_MATRIX §5)

lote próximo a cierre   BLOCKED_BY_OWNER_DECISION   «próximo» sin definir
                                                     (P14_NOTIFICATION_EVENT_MATRIX §4)

recurrencia del aviso de «> 24h»   sin definir   se implementa una sola vez
```

Los tres se declaran. Ninguno se completa a ojo.
