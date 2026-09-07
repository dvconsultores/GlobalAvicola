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

| # | Nombre literal (`docs/02 §3.14`) | Disparador | Originador del dato | Condición | Estado |
|:--:|---|---|---|---|:--:|
| 1 | **Registro pendiente de revisión > 24h** | el paso del tiempo sobre un evento en `pending_review` | `OperationalEvent.registered_by_id` | **objetiva y normativa**: 24 h desde que entró en `pending_review`, momento que consta en `AuditLog.new_state = 'pending_review'` | **ACTIONABLE** |
| 2 | **Registro rechazado (notificar al operador)** | `review/service.py:409` — único punto que asigna `REJECTED` | `OperationalEvent.registered_by_id` | inmediata | **ACTIONABLE** |
| 3 | **Mortalidad > umbral configurable** | `operations/service.py:397` — alerta `high_mortality` | `OperationalEvent.registered_by_id` | umbral en `settings.MORTALITY_ALERT_WARNING_PCT` (**configurable**, como exige el nombre) | **ACTIONABLE** |
| 4 | **Peso fuera de estándar** | `operations/service.py` — alerta `weight_deviation` (`GA-REM-037`) | `OperationalEvent.registered_by_id` | fuera del rango de la curva; `WITHIN_STANDARD` y `NO_REFERENCE` **no** disparan | **ACTIONABLE** |
| 5 | **Error de envío SAP** | `sap/service.py:367,451` — `PayloadStatus.FAILED` | los `registered_by_id` de los eventos de `ConsolidatedMovement.event_ids` | inmediata | **ACTIONABLE** |
| 6 | **Lote próximo a cierre** | — | `Lot` no tiene originador; el lote no lo tiene | **«próximo» no está definido en ninguna fuente** | **BLOCKED_BY_OWNER_DECISION** |

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

## 4. El evento 6 sigue bloqueado, y por qué exactamente

Se buscó en toda la jerarquía documental una definición de «próximo»:

```
near close · closing soon · lot closure · expected close · planned close
end date · production age · cycle duration · días antes de cierre
```

La única aparición de la frase en el repositorio es la línea de `docs/02 §3.14` que la enumera.
No hay definición.

Y el modelo tampoco la deja derivar:

| Campo | Qué es | ¿Sirve? |
|---|---|:--:|
| `Lot.end_date` | la fecha **real** de cierre, que fija `close_lot` | **no** — para cuando existe, el lote ya cerró |
| `Lot.start_date` | inicio del ciclo | por sí sola, no |
| `ProductivePhase.duration_days` | duración típica de una fase (140 d en Cría) | **no sin fuente** — usarla equivaldría a decidir que el cierre previsto es `start_date + duration_days`, que ninguna fuente dice |

No existe `planned_end_date` ni equivalente. Elegir «7 días antes» o derivar la fecha de la
duración de fase sería inventar el requisito, que es justo lo que `§22` prohíbe.

## 5. Recuento

```
6 eventos normativos
  5 ACTIONABLE                      1 · 2 · 3 · 4 · 5
  1 BLOCKED_BY_OWNER_DECISION       6 · «lote próximo a cierre»
```

De los cinco accionables, dos ya estaban implementados (`2` y `5`) y les faltaba ampliar
destinatarios; tres se implementan ahora (`1`, `3`, `4`).

## 6. Lo que sigue sin decidirse

```
OD-08 · semántica temporal      ¿qué es «lote próximo a cierre»?  ABIERTA
OD-08 · recurrencia del aviso   ¿el de «> 24h» se repite?         ABIERTA (se implementa una vez)
```

Ambas son del propietario. La **tecnología** del disparador temporal no lo es: se resuelve con
la arquitectura existente, sin introducir `Celery`, `Redis` ni colas.
