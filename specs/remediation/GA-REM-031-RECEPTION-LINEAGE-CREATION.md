# `GA-REM-031` · CREACIÓN DEL VÍNCULO GENERACIONAL DESDE LA RECEPCIÓN

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-031` · `DOMAIN DEFECT SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Hallazgo** | `R-78` |
| **Proceso** | `P-10` · Trazabilidad generacional — pasos 3, 4, 7 y 8 |
| **Dependencias** | `GA-REM-008` `CERTIFIED` (rama de despacho) · `GA-REM-030` `CERTIFIED` (pertenencia) |
| **Antecedente** | `audit/remediation/P10_LINEAGE_BRANCH_MATRIX.md` |

> Spec propia y no enmienda de `GA-REM-008`. Aquella certificó la rama del **despacho**;
> ninguno de sus criterios habla de la recepción como origen del vínculo. `GA-REM-008` queda
> `CERTIFIED` y sin modificar, salvo la anotación de `AC01` que corresponde a `R-79`.

---

## 1. Requisito de negocio

`spec.md §4.9`:

> Un `EggBatch` se crea **automáticamente** al registrar `egg_dispatch` +
> `egg_reception_hatchery`.
> Un `ChickBatch` se crea **automáticamente** al registrar `chick_dispatch` +
> `bird_reception`.

La conjunción es simétrica. **La spec no impone orden**, y la operación real despacha antes
de recibir.

## 2. El defecto

La creación vive **solo** en la rama del despacho, que busca una recepción ya existente. Las
dos ramas de recepción se limitan a actualizar un vínculo previo:

```python
elif event.event_type == models.EventType.EGG_RECEPTION_HATCHERY:
    dispatch = await self._despacho_dirigido_a_este_lote(...)
    if dispatch:
        batch = ...where(EggBatch.dispatch_event_id == dispatch.id)...
        if batch:                      # ← si no existe, no crea: se ignora
            batch.quantity_received = ...
```

En el orden natural:

```
despacho  → busca recepción → todavía no existe → no crea
recepción → encuentra el despacho → busca el vínculo → no existe → no hace nada
RESULTADO: ningún vínculo, nunca
```

Medido en la pila real: la cadena de tres generaciones produce **0 vínculos**.

## 3. Invariante

```
CUANDO   una recepción válida establece una relación generacional
Y        el vínculo exigido no existe todavía
ENTONCES el sistema lo crea exactamente una vez
```

Con el mismo origen, destino y pertenencia que habría producido la rama del despacho — no
por parecido de código, sino porque `P10_LINEAGE_BRANCH_MATRIX §2` demuestra que las dos
ramas ya comparten filtros, semántica de pertenencia y señal de emparejamiento; la única
diferencia material es la acción.

## 4. Fuera de alcance

- La rama del despacho: certificada, intacta.
- El contrato de la API: ni esquema de petición, ni de respuesta, ni ruta.
- La señal de emparejamiento (`destination_farm_id`).
- El enlace manual y su guarda (`GA-REM-030`).
- `R-76`, `R-77`, `OD-04`, `GA-TD-014`.

## 5. Criterios de aceptación

### `AC01` · La recepción crea el vínculo ausente
Registrado el despacho con destino declarado y **después** la recepción en el lote destino,
existe un `EggBatch` — y su equivalente `ChickBatch` — con el origen y el destino correctos.

**Puerta de validez.** Antes de la recepción se comprueba que **no** hay vínculo; después,
que lo hay. Sin la comprobación previa, la aserción posterior no distingue creación de
preexistencia.

### `AC02` · Exactamente uno
Tras la pareja completa hay **un** vínculo, no dos. Ni la creación desde el despacho ni la
creación desde la recepción producen un duplicado del otro lado.

### `AC03` · Orientación correcta
`source_lot_id` es el lote que despachó y `hatchery_lot_id` el que recibió; análogamente
`hatchery_lot_id` → `destination_lot_id` para el pollito. **Un recuento de uno no basta**: el
vínculo debe apuntar a las entidades correctas.

### `AC04` · Cantidades y fechas de ambos lados
El vínculo creado desde la recepción registra la cantidad y la fecha **despachadas** —del
evento de despacho— y las **recibidas** —del evento de recepción—. Es el paso 4 de la cadena,
hoy sin cubrir.

### `AC05` · Referencia a la generación anterior
El `ChickBatch` creado desde la recepción referencia el `EggBatch` del que procede
(`egg_batch_id`), como ya hace el creado desde el despacho. Es el paso 7, hoy sin cubrir.

### `AC06` · Pertenencia
El vínculo queda bajo la compañía correcta. Un actor **con permiso** no produce vínculos que
alcancen lotes de otra compañía.

**Puerta de validez.** CONTROL y TRATAMIENTO con el mismo sujeto y la misma operación; lo
único que cambia es de quién es el lote. **Prohibido** un `!= 201`. **Prohibido** usar un
Super Admin como sujeto negativo: tiene exención por diseño.

### `AC07` · Sin efectos tras la denegación
Cero vínculos, cero mutación de saldos, cero avance de flujo.

### `AC08` · Lectura inmediata
`R-68`: tras la recepción, una consulta posterior del árbol ve el vínculo sin esperas.

### `AC09` · La rama del despacho no se altera
Las cuatro pruebas de `GA-REM-008` siguen en verde, y el orden inverso —recepción antes que
despacho— sigue produciendo un vínculo y solo uno.

## 6. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01`…`AC05` `AC08` | `backend/tests/test_reception_lineage.py` | integración HTTP |
| `AC06` `AC07` | ídem, CONTROL + TRATAMIENTO | integración HTTP |
| `AC09` | `backend/tests/test_traceability.py` | regresión |
| cadena de `P-10` | `e2e/proceso-p10-trazabilidad-generacional.spec.ts` | `API_E2E` |

## 7. Definición de terminado

- Los nueve criterios pasan.
- Existe una prueba que **falla contra el código actual** por la causa exacta —el vínculo no
  existe tras una recepción válida— y no por autenticación, permiso, fixture ni esquema.
- Sensibilidad demostrada por mutación controlada y revertida.
- La cadena de `P-10` se recorre entera y el `test.fail()` que documenta `R-78` se retira.
- Regresión completa sin fallos nuevos.

---

# Enmienda A · `R-178` · el linaje efectivo sigue el estado de sus eventos; la reasignación de un evento casado se deniega (2026-09-10 · WAVE B · tranche 11)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-031-A` · `TRACEABILITY INTEGRITY` · **Estado** `SPEC_READY` (pre-flight 2026-09-10) |
| **Hallazgo** | `R-178` (P3): los vínculos `egg_batches`/`chick_batches` no se neutralizan ni re-casan al anular o mover de lote un despacho/recepción; el árbol (`GET /lots/{id}/traceability`) los presenta como traspasos vigentes |
| **Matriz** | `audit/remediation/R178_LINEAGE_CANCEL_MOVE_INTEGRITY_MATRIX.md` (qué es el linaje, histórico ≠ efectivo, reproducción, AC) |
| **Fuentes** | `OD-10 §2.4` («la fila es el traspaso»), `§2.5` («un traspaso anulado … el lado que lo veía lo ve desaparecer con su motivo»), `§4bis` («sin cascada automática … la historia anterior se conserva»), `§4bis.5` («ante la duda, se deniega») · `BR-10`/`docs/02 R10` (eliminación lógica) · `GA-REM-008 AC04/AC06` · `GA-REM-031 AC02/AC03` (uno por envío; orientación correcta) · `GA-REM-030` (sin vínculos entre empresas) |
| **Modelo** | **histórico conservado** (la fila nunca se borra; auditoría de los eventos) + **efectivo derivado en lectura** del estado de los eventos del par + **reasignación denegada** mientras el evento participe en un vínculo efectivo (el camino es anular y registrar de nuevo: `R-173` + emparejamiento de esta spec). Sin decisión del propietario |
| **Sin cambio** | `_auto_create_traceability_batches` (creación y re-casado de una recepción nueva sobre un despacho existente) · vínculo manual (`POST /lots/egg-batches`, `/chick-batches`) · `GeneticLine`/`WeightCurve` · reversos (`OD-19`) · `R-140` (el **motivo** del `cancel`, `AOD-18`) · esquema de respuesta (`EggBatchRead`/`ChickBatchRead`: campos de recepción ya opcionales) |
| **Migración** | ninguna (sin bandera nueva: el estado efectivo se deriva de `operational_events.status`) |

## A.1 Contrato

1. **Linaje efectivo** (`GET /lots/{id}/traceability`): un vínculo con `dispatch_event_id` cuyo despacho está `CANCELLED` **no se lista** en ningún
   lado; un vínculo cuya recepción está `CANCELLED` se lista **incompleto** (`quantity_received`, `reception_date` = `null`) en el lado emisor y no se
   lista en el receptor. Los vínculos manuales (sin eventos) se listan siempre. La fila no cambia: es lectura.
2. **Historia**: `egg_batches`/`chick_batches` no se borran ni se reescriben al anular o mover; la auditoría `CANCELLED`/`UPDATED` del evento conserva el rastro.
   El motivo de la anulación pende de `R-140` (`AOD-18`): frontera documentada.
3. **Reasignación denegada**: `PUT`/corrección que cambie `lot_id` o `destination_farm_id` de un evento que participa en un vínculo efectivo (como
   despacho o como recepción, con la contraparte no anulada) → `400` («El evento participa en un vínculo de trazabilidad; anúlelo y regístrelo de nuevo»),
   dentro de `verificar_destino_de_edicion`, tras la cadena de inquilino/unidad y antes del bloqueo de saldos; evento, vínculo y saldos intactos. Sin
   vínculo efectivo, la edición sigue el contrato de `R-173`.
4. **Re-casado natural**: anulada una recepción, una recepción nueva en el destino declarado vuelve a casarse con el despacho (comportamiento existente,
   `AC-R178-03` lo controla); anulado un despacho, un despacho nuevo crea su propio vínculo (`AC02`: uno por envío).
5. **Seguridad**: sin permiso ni ruta nuevos; `GA-REM-030` (ningún vínculo entre empresas) intacto; una denegación por inquilino/unidad no toca el linaje.
6. **Concurrencia**: N/A (sin escritura de linaje en estos caminos; las mutaciones de evento ya se serializan por lote, `R-173`).

## A.2 Criterios de aceptación

| AC | Criterio |
|---|---|
| `AC-R178-01` | control: `egg_dispatch` (destino declarado) + `egg_reception_hatchery` → un `EggBatch` orientado; el árbol de A lo lista en `egg_batches_sent` y el de B en `egg_batches_received` |
| `AC-R178-02` | anular el despacho → ambos árboles dejan de listarlo; `egg_batches` conserva la fila; auditoría `CANCELLED`; segunda anulación `400` sin cambio |
| `AC-R178-03` | anular la recepción → el árbol de A lo lista **incompleto** (`quantity_received`/`reception_date` nulos); el de B no lo lista; fila conservada; una recepción nueva vuelve a casarse y el árbol la refleja |
| `AC-R178-04` | `PUT lot_id` de un despacho casado → `400`; evento, vínculo y saldos intactos |
| `AC-R178-05` | corrección de `lot_id` y `PUT destination_farm_id` de un despacho casado → `400`; nada cambia |
| `AC-R178-06` | `PUT lot_id` de una recepción casada → `400` |
| `AC-R178-07` | denegación por inquilino/unidad (`R-173`: lote de otra empresa, unidad apagada) → vínculo intacto; ningún vínculo entre empresas |
| `AC-R178-08` | cadena de pollitos (`chick_dispatch` ↔ `bird_reception`, `ChickBatch` con `egg_batch_id`): anular el despacho → desaparece; mover → `400` |
| `AC-R178-09` | control: un despacho **sin** vínculo se mueve como hoy (`200`, `R-173`) |
| `AC-R178-10` | control: el vínculo manual sigue listado, sin depender de eventos |
| `AC-R178-11` | la auditoría del evento distingue el estado anterior y el nuevo (`CANCELLED`; `UPDATED` con valores) |

## A.3 Tareas

| Tarea | Descripción |
|---|---|
| `T-031-A1` | pruebas rojas `tests/test_lineage_cancel_move.py` (prefijo `LINA-`; escenario: empresa A con `breeder` + `hatchery` (+ `broiler` OFF) y empresa B; granja de producción y planta; lotes `lr`/`lr2` (breeder), `lh`/`lh2` (hatchery), `lr3` receptor de pollitos, `lb` (B); operador con `operations` + `corrections` + `lots:read`) |
| `T-031-A2` | `lots/router.py` (o servicio de lotes): filtro/presentación del linaje efectivo por estado de los eventos (A.1.1) |
| `T-031-A3` | `operations/service.py::verificar_destino_de_edicion`: guarda de vínculo efectivo (A.1.3) |
| `T-031-A4` | sensibilidad A.4; regresión `GA-REM-008`/`GA-REM-031` (`test_traceability`, `test_reception_lineage`), `R-173`, `OD-10` (`test_pending_classification`); evidencia; cierre |

## A.4 Sensibilidad

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| `R178-S1` | el filtro por estado del despacho en el árbol (vuelve a listar anulados) | `AC-R178-02` |
| `R178-S2` | la guarda de vínculo efectivo en la reasignación | `AC-R178-04/06` |
| `R178-S3` | borrar la fila del vínculo al anular (en vez de conservarla) | `AC-R178-02/03` (historia) |
| `R178-S4` | atomicidad parcial | **N/A**: linaje dinámico, sin escritura que pueda quedar parcial |

## A.5 Definición de terminado

`AC-R178-01…11` verdes · rojo válido leído en `80cce71` (árbol con traspaso anulado como vigente; evento casado movido con `200`) · sensibilidad válida ·
`test_traceability` + `test_reception_lineage` verdes · `R-173` 16/16 · regresión completa leída · `R-178` cerrado (técnico).
