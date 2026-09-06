# `R-76` · QUÉ IMPIDE CERRAR UN LOTE

`docs/12 R7` · 2026-09-06 · antes de tocar código

---

## 1. La regla, literal

`docs/12 §6 · REGLAS DE APROBACIÓN`:

> **R7** — Un lote no puede cerrarse si tiene **registros sin aprobar**.

Dos palabras hay que acotar antes de programar: **qué registros** y **qué es sin aprobar**.

## 2. Qué es un «registro»

`docs/12 §4` se titula **«ESTADOS DEL REGISTRO OPERATIVO»** y describe el ciclo de vida de una
sola entidad. El documento entero trata de ella: `R6` habla de consolidar registros, `R5` de
no editarlos tras SAP, `R3` del motivo de rechazo.

```
«registro» = OperationalEvent del lote
```

**No** se generaliza a «nada puede estar pendiente en ningún sitio». Correcciones y acciones de
aprobación son artefactos del propio flujo del registro, no registros en el sentido de `R7`.

## 3. Qué es «sin aprobar»

`docs/12 §4` enumera **trece** estados. El flujo los ordena: la aprobación es el estado 7 y
todo lo posterior presupone haberla atravesado.

| # | Estado | Enum | ¿Bloquea el cierre? | Por qué |
|:--:|---|---|:--:|---|
| 1 | Borrador | `draft` | **sí** | ni siquiera se ha enviado |
| 2 | Registrado | `registered` | **sí** | esperando revisión |
| 3 | Enviado a Revisión | `pending_review` | **sí** | ídem |
| 4 | En Revisión | `in_review` | **sí** | en curso |
| 5 | Devuelto con Observaciones | `returned` | **sí** | el operador debe corregir |
| 6 | Corregido | `corrected` | **sí** | pendiente de aprobar |
| 7 | **Aprobado** | `approved` | no | es el estado que `R7` pide |
| 8 | Rechazado | `rejected` | **sí** | §4 |
| 9 | Consolidado | `consolidated` | no | posterior a la aprobación |
| 10 | Enviado a SAP | `sent_to_sap` | no | ídem |
| 11 | Confirmado por SAP | `sap_confirmed` | no | ídem |
| 12 | Error de Envío SAP | `sap_error` | no | §5 |
| 13 | Anulado | `cancelled` | no | §6 |

```
Bloquean 7 estados · no bloquean 6
```

## 4. `Rechazado` bloquea, y no atrapa el lote

`docs/12 §4` lo dice en la columna «¿Quién puede mover?»:

> **Rechazado** · Operador → **Reenvía (corregido)**

Y el diagrama de estados lo confirma: `Rechazado --> Registrado`. **No es terminal.** Un
registro rechazado no está aprobado y sigue esperando resolución, así que bloquea — y el lote
no queda atrapado, porque el operador puede reenviarlo.

## 5. `Error de Envío SAP` **no** bloquea

El estado 12 solo se alcanza desde `Enviado a SAP`, que solo se alcanza desde `Consolidado`,
que solo se alcanza desde `Aprobado`. **Un registro en error de SAP ya fue aprobado.**

`R7` es una regla de **aprobación** —está en la sección «Reglas de aprobación»—, no de
integración. Bloquear un cierre por un fallo de envío a SAP sería aplicar la regla a algo que
no gobierna.

> Se aparta aquí del conjunto que el código usa en otros sitios —`APPROVED`, `CONSOLIDATED`,
> `SENT_TO_SAP`, `SAP_CONFIRMED`, sin `SAP_ERROR`—, y a propósito: aquel cuenta eventos para
> **mostrar**, éste decide si algo **está aprobado**. Son preguntas distintas.

## 6. `Anulado` no bloquea

«Registro cancelado con auditoría». Un registro anulado no representa operación alguna, y los
**ocho** saldos de `operations/validators.py` lo excluyen sin excepción. Se sigue ese
precedente.

## 7. El universo, por tipo de registro

`R7` no distingue tipos de evento: habla de los registros del lote. Ninguno queda fuera.

| Entidad | ¿Ligada al lote? | ¿Tiene estado de aprobación? | ¿`R7` la gobierna? |
|---|:--:|:--:|:--:|
| `OperationalEvent` (los 25 tipos) | **sí** — `lot_id` | **sí** — `EventStatus` | **sí** |
| `CorrectionLog` | vía el evento | no propio | no — es un artefacto del flujo |
| `ApprovalAction` | vía el evento | no propio | no — ídem |
| `EggBatch` · `ChickBatch` | sí | **no** | no — sin estado que aprobar |
| `OpeningBalance` | sí | no | no |
| `LotPhase` | sí | no | no |
| `AuditLog` | sí | no | no — es el rastro, no el registro |

## 8. Lo que hoy ocurre

`close_lot` comprueba **dos** cosas: que el lote esté activo y `BR-05` —pesaje y alimento—.
Nada mira la aprobación.

El `API_E2E` de `P-06` cierra un lote con **nueve** eventos en `registered` y recibe `200`.

```
R-76 · P1 · docs/12 R7 no está implementado.
```

## 9. `BR-05` y `R7` son reglas distintas

Ambas se ejecutan en `close_lot`, y ahí acaba el parecido:

| | `BR-05` | `R7` |
|---|---|---|
| Fuente | `spec.md §266` · `docs/02 §545` | `docs/12 §6` |
| Pregunta | ¿hay base para el resumen final? | ¿está todo aprobado? |
| Comprueba | existe pesaje y existe alimento | ningún evento en los siete estados de §3 |

**No se fusionan bajo un mismo nombre** por compartir función. `R7` se cita como `R7`, que es
como la norma la llama; no se inventa un `BR-` nuevo ni se amplía `BR-05`.

## 10. Relación con `R-77`

`R-77` es la discrepancia de numeración entre `BR-10` (código) y `BR-11` (spec) en la regla de
no duplicar documentos SAP. **No afecta a `R7`**: esta regla no cita ningún `BR-` y su
trazabilidad es directa a `docs/12`.

`R-77` sigue abierto y fuera de esta implementación.
