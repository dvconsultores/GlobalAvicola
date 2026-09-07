# `P-14` · LOS SEIS EVENTOS NORMATIVOS

`docs/02 §3.14` · `docs/10 §6.2` · `OD-07` · `OD-08` · `GA-REM-038`

Los seis con sus **nombres literales**, transcritos de `docs/02 §3.14` y no de conversaciones
anteriores. Ninguna fila se rellena sin fuente.

---

## 1. La distinción que ordena esta matriz

```
ALERT         pertenece al LOTE        OperationalAlert     ya existe
NOTIFICATION  pertenece a UNA PERSONA  bandeja con lectura  es P-14
AUDIT         pertenece al SISTEMA     AuditLog · P-09      ni una ni otra
```

Que exista una alerta no implica notificación, y al revés tampoco. `OD-08` resolvió **a
quién**; no resolvió **cuándo**, que sigue saliendo de las fuentes de cada evento.

## 2. Los seis

| # | Nombre literal (`docs/02 §3.14`) | Disparador | Originador del dato | Área | Estado |
|:--:|---|---|---|---|:--:|
| 1 | **Registro pendiente de revisión > 24h** | `notifications/sla.py` · 24 h desde la transición, tomada de `AuditLog.new_state = 'pending_review'` | `OperationalEvent.registered_by_id` | `event.lot_id → Lot.area_id` | **CUBIERTO** |
| 2 | **Registro rechazado (notificar al operador)** | `review/service.py:409` — único punto que asigna `REJECTED` | `OperationalEvent.registered_by_id` | `event.lot_id → Lot.area_id` | **CUBIERTO** |
| 3 | **Mortalidad > umbral configurable** | `operations/service.py:397` — alerta `high_mortality`, umbral en `settings` | `OperationalEvent.registered_by_id` | `event.lot_id → Lot.area_id` | **CUBIERTO** |
| 4 | **Peso fuera de estándar** | `operations/service.py` — alerta `weight_deviation` (`GA-REM-037`) | `OperationalEvent.registered_by_id` | `event.lot_id → Lot.area_id` | **CUBIERTO** |
| 5 | **Error de envío SAP** | `sap/service.py:367,451` — `PayloadStatus.FAILED` | `ConsolidatedMovement.event_ids → registered_by_id` | `ConsolidatedMovement.lot_id → Lot.area_id` | **CUBIERTO** |
| 6 | **Lote próximo a cierre** | `notifications/sla.py` · `0 <= días hasta planned_close_date <= 3` | quien dio de alta el lote, según `AuditLog` | `Lot.area_id`, directo | **CUBIERTO** |

```
6 / 6 disparadores computables
6 / 6 reglas de destinatario resolubles
6 / 6 integraciones probadas
```

## 2 bis. Los dos que se desbloquearon, y en qué orden

```
1ª tanda de OD-08 (destinatarios)   →  1 · 3 · 4 pasan a cubiertos
2ª tanda de OD-08 (área + cierre)   →  6 pasa a cubierto
```

El evento 6 esperaba una definición que ninguna fuente daba. `OD-08` la dio —tres días antes
de la fecha prevista— y con ella dejó de ser adivinanza.

## 3. El evento 1 sí tiene umbral, y por eso deja de estar bloqueado

El informe anterior lo clasificó junto al 6 como «temporal sin definir». Al releer el nombre
**literal** la diferencia salta:

```
«Registro pendiente de revisión > 24h»      el umbral ESTÁ en el nombre
«Lote próximo a cierre»                     «próximo» no está en ninguna parte
```

Y la condición es computable con lo que ya existe:

```
evento.status == pending_review
  Y  ahora − (AuditLog más reciente del evento con new_state = 'pending_review').created_at  > 24 h
```

`updated_at` **no** sirve: cambia con cualquier edición posterior, de modo que un evento tocado
a las 23 h reiniciaría su cuenta. La marca exacta es la de la transición, y esa está en la
auditoría —leerla no es reutilizar `AuditLog` como bandeja: es consultar historia, que es para
lo que existe—.

**La frecuencia no está definida.** `docs/02 §3.14` no dice si el aviso se repite. Se implementa
**una sola vez** por evento y destinatario, con idempotencia, y se registra que la recurrencia
es un hueco de requisito. No se inventa una repetición diaria.

## 4. El evento 6, resuelto — y lo que hubo que añadir para poder resolverlo

Se buscó en toda la jerarquía documental una definición de «próximo»:

```
near close · closing soon · lot closure · expected close · planned close
end date · production age · cycle duration · días antes de cierre
```

Cuando se escribió la primera versión de esta matriz, la única aparición de la frase en el
repositorio era la línea de `docs/02 §3.14` que la enumera. **`OD-08` la definió**: faltan tres
días calendario para la fecha prevista de cierre.

Lo que el modelo seguía sin tener era la fecha prevista, y por eso se añadió `planned_close_date`
—nulable, distinta de `end_date`—. Lo que **no** se hizo fue derivarla:

| Campo | Qué es | ¿Sirve? |
|---|---|:--:|
| `Lot.end_date` | la fecha **real** de cierre, que fija `close_lot` | **no** — para cuando existe, el lote ya cerró |
| `Lot.start_date` | inicio del ciclo | por sí sola, no |
| `ProductivePhase.duration_days` | duración típica de una fase (140 d en Cría) | **no sin fuente** — usarla equivaldría a decidir que el cierre previsto es `start_date + duration_days`, que ninguna fuente dice |

La fecha la pone quien planifica. Y la ventana es `0..3` en vez de `== 3` porque con igualdad
el aviso solo saldría si el evaluador corriera exactamente ese día: con el sistema apagado, no
saldría nunca.

## 5. Recuento

```
6 eventos normativos · 6 CUBIERTOS
```

## 6. Lo que sigue sin decidirse

```
recurrencia del aviso de «> 24h»   ¿una vez o mientras siga pendiente?
```

Ninguna fuente lo dice, y mientras tanto se emite **una vez**, con idempotencia. Es un hueco de
requisito registrado, no una decisión nuestra. No bloquea `P-14`: el aviso existe y llega.
