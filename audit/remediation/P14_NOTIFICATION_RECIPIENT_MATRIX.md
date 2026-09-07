# `P-14` · A QUIÉN LLEGA CADA NOTIFICACIÓN

`docs/02 §3.14` · `docs/10 §6.2` · `OD-07` · 2026-09-07

Existe aparte de la matriz de eventos porque el destinatario es donde más fácil resulta
inventar. `§14` del encargo lo dice sin rodeos: nada de «todos los administradores», «todos los
usuarios» ni «todos los aprobadores» salvo que una regla lo exija.

---

## 1. Quién causa el evento ≠ quién lo recibe

`§59` del encargo, y es la distinción que evita el error más común:

```
ACTOR      quien ejecuta la acción      p. ej. el aprobador que rechaza
RECIPIENT  quien necesita enterarse     p. ej. el operador cuyo registro fue rechazado
```

En el rechazo son **personas distintas por diseño**: `BR-14` exige segregación, de modo que
quien rechaza no puede ser quien registró. La prueba lo comprueba en los dos sentidos —que B
recibe y que A no—, porque si el destinatario se resolviera mal, notificar al propio actor
pasaría desapercibido.

## 2. Matriz

| Event | Actor | Recipient Rule | Role-based? | User-specific? | Company-scoped? |
|---|---|---|:--:|:--:|:--:|
| `record_rejected` | quien rechaza (`Aprobador` / `Supervisor Avícola`) | `OperationalEvent.registered_by_id` — «notificar al operador», `docs/02 §3.14` literal | no | **sí** | sí · `event.company_id` |
| `sap_send_failed` | el proceso de envío | todos los usuarios activos con rol **`Analista SAP`** en esa empresa — `docs/10 §6.2` literal | **sí** | no | sí · `payload.company_id` |
| `mortality_over_threshold` | quien registra la mortalidad | **SIN DEFINIR** | — | — | — |
| `weight_out_of_standard` | quien registra el pesaje | **SIN DEFINIR** | — | — | — |
| `review_pending_24h` | nadie (paso del tiempo) | **SIN DEFINIR** | — | — | — |
| `lot_near_closure` | nadie (paso del tiempo) | **SIN DEFINIR** | — | — | — |

## 3. Las dos reglas que sí están escritas

**`record_rejected` → el operador.** `docs/02 §3.14` dice literalmente «Registro rechazado
(notificar al operador)». En el modelo, el operador de un registro es
`OperationalEvent.registered_by_id`, que es obligatorio y nunca nulo. Un destinatario, una
persona, sin ambigüedad.

**`sap_send_failed` → el rol `Analista SAP`.** `docs/10 §6.2` dice «Notificar al rol "Analista
SAP"». Ese rol **existe**: lo crea la migración `l2m3n4o5p6q7` y `review/service.py:549` ya lo
busca por nombre para armar el tercer paso de aprobación. Es una regla por rol, no por persona,
de modo que produce **una notificación por cada usuario** de ese rol en la empresa: la bandeja
es personal y una fila compartida no podría marcarse leída por uno sin marcarla por todos.

Si en una empresa no hay nadie con ese rol, no se crea ninguna notificación y no se falla: el
envío SAP no puede depender de que la plantilla esté completa.

## 4. Las cuatro que no

`Lot` no tiene responsable, supervisor ni usuario asignado. Se enumeraron sus campos:

```
id · company_id · farm_id · house_id · genetic_line_id · breed_id · weight_curve_id
lot_code · bird_type · hatchery_purpose · sex · status · activation_type
start_date · end_date · created_at · updated_at
```

Ninguno apunta a una persona. Para «mortalidad > umbral» y «peso fuera de estándar» no hay, por
tanto, destinatario derivable del dato, y `docs/02 §3.14` no lo dice.

Las opciones que se descartaron, y por qué:

| Candidato | Por qué no |
|---|---|
| `registered_by_id` del evento | es quien acaba de registrar la mortalidad: ya lo sabe. Avisarle no informa a nadie |
| rol `Supervisor Avícola` | `docs/02 §6.1` le da «revisar, corregir, devolver registros» — el flujo de revisión, no las alertas operativas |
| todos los administradores de la empresa | exactamente lo que `§14` prohíbe |

Cualquiera de las tres sería una decisión nuestra vestida de requisito. Se deja el hueco.

## 5. Lo que habría que preguntar

Registrado como **`OD-08`**, sin plantear aquí:

```
1. ¿Quién debe recibir el aviso de mortalidad sobre umbral?
   ¿un rol, el responsable de la granja, alguien asignado al lote?
   Si es «el responsable del lote», el modelo no lo tiene y habría que añadirlo.

2. ¿Quién debe recibir el aviso de peso fuera de la curva estándar?
   ¿el mismo que el anterior u otro?

3. «Registro pendiente de revisión > 24 h»: ¿a quién, y con qué mecanismo?
   Hoy no hay planificador; introducirlo es una decisión de arquitectura, no de canal.

4. «Lote próximo a cierre»: ¿qué es «próximo»?
   ¿días antes de una fecha prevista de cierre —que el modelo tampoco tiene—,
   una edad, un porcentaje del ciclo? Y ¿a quién se avisa?
```
