# `P-14` · QUÉ EVENTOS PRODUCEN NOTIFICACIÓN

`docs/02 §3.14` · `docs/10 §6.2` · `OD-07` · 2026-09-07

Ninguna fila se rellenó por intuición. Cada una cita la fuente que la exige, y las que no
tienen fuente se marcan como hueco en vez de completarse a ojo.

---

## 1. La distinción que ordena esta matriz

`§4` del encargo lo pide y conviene dejarlo escrito, porque es lo que evita convertir el
sistema en una máquina de ruido:

```
ALERT         pertenece al LOTE      OperationalAlert       ya existe
NOTIFICATION  pertenece a UNA PERSONA  con lectura y bandeja  es P-14
AUDIT         pertenece al SISTEMA   AuditLog · P-09         ni una cosa ni la otra
```

Una operación puede generar las tres, dos, una o ninguna. Que exista una alerta **no** implica
que deba existir una notificación: hace falta que `§3.14` —o una fuente normativa aplicable—
lo exija *y* que se sepa a quién.

## 2. Los seis tipos de `docs/02 §3.14`

| Event | Normative Source | Trigger | Recipient | Company | Related Entity | Required? |
|---|---|---|---|---|---|:--:|
| **`record_rejected`** · registro rechazado | `docs/02 §3.14` — «Registro rechazado (notificar al operador)» | `review/service.py:409` · `reject()`, único punto que asigna `REJECTED` | **`OperationalEvent.registered_by_id`** — «el operador», literal | `event.company_id` | `operational_event` / `event.id` | **SÍ** |
| **`sap_send_failed`** · error de envío SAP | `docs/02 §3.14` + `docs/10 §6.2` — «Notificar al rol Analista SAP» | `sap/service.py:367,451` · `PayloadStatus.FAILED` | **usuarios con rol `Analista SAP`** de esa empresa | `SapPayload.company_id` | `sap_payload` / `payload.id` | **SÍ** |
| `mortality_over_threshold` · mortalidad > umbral | `docs/02 §3.14` | existe: alerta `high_mortality`, umbral en `settings` | **sin definir** | — | — | **hueco** |
| `weight_out_of_standard` · peso fuera de estándar | `docs/02 §3.14` · `spec.md §4.5` | existe: alerta `weight_deviation` (`GA-REM-037`) | **sin definir** | — | — | **hueco** |
| `review_pending_24h` · pendiente de revisión > 24 h | `docs/02 §3.14` | **no existe** — disparador temporal, sin planificador | sin definir | — | — | **hueco** |
| `lot_near_closure` · lote próximo a cierre | `docs/02 §3.14` | **no existe** — temporal, y «próximo» no está definido | sin definir | — | — | **hueco** |

## 3. Por qué dos sí y cuatro no

**Los dos que sí** tienen las tres cosas que hacen falta para escribir código sin inventar:
un momento exacto en el que ocurren, una persona a quien nombrar, y una fuente que lo dice con
sus palabras. No se dedujeron: se leyeron.

**Los cuatro que no** fallan por motivos distintos, y conviene no mezclarlos:

```
mortalidad > umbral     tiene disparador · NO tiene destinatario
peso fuera de estándar  tiene disparador · NO tiene destinatario
pendiente > 24 h        NO tiene disparador (temporal, sin planificador) · NO tiene destinatario
lote próximo a cierre   NO tiene disparador · NO tiene destinatario · «próximo» sin definir
```

Para los dos primeros, el dato tampoco ayuda: `Lot` no tiene responsable ni supervisor
asignado —sus campos se enumeraron—, así que no hay persona derivable. Elegir «todos los
administradores» o «el Supervisor Avícola» sería exactamente lo que `§14` prohíbe.

Para los dos temporales haría falta además un planificador. No hay ninguno en el proyecto, y
`OD-07` decidió el **canal**, no autorizó introducir infraestructura de ejecución periódica.

## 4. Lo que esta matriz NO hace

**No convierte las alertas existentes en notificaciones.** `high_mortality`,
`weight_deviation`, `temperature_out_of_range` y `humidity_out_of_range` siguen siendo alertas
del lote. Las dos primeras están en `§3.14` y esperan destinatario; las dos últimas ni siquiera
figuran ahí, de modo que convertirlas sería inventar requisito.

**No toca la auditoría.** Los eventos que ya se auditan siguen auditándose igual. Rechazar un
registro seguirá dejando su `AuditLog` por `audit_state_transition`, y la notificación es otra
cosa que se añade, no que lo sustituye.

**No crea notificación cuando la operación falla.** Si el rechazo no llega a persistirse, no
hay notificación: la transacción es la misma y revierte junta. `§84` del encargo lo exige, y
`§29` advierte de no trasladar aquí la excepción de `LOGIN_FAILED`, que es de `P-09` y responde
a un requisito de seguridad distinto.

## 5. Consecuencia sobre el veredicto

```
6 tipos normativos · 2 implementables · 4 con hueco de requisito
```

`§117` del encargo no admite certificar por muestra si la spec exige todos. `docs/02 §3.14`
enumera seis. Por tanto:

```
P-14 = PARTIAL          el canal existe y funciona; faltan cuatro tipos por falta de requisito
OD-08 = REQUERIDA       destinatarios de las alertas operativas y definición de «próximo a cierre»
```

No se pide aquí esa decisión al propietario —`OD-07` acaba de tomarse y esto es su
consecuencia, no su continuación—: se deja registrada con lo que habría que preguntar y por
qué, para que la pregunta llegue completa.
