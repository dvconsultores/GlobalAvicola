# `R-178` · Matriz de integridad del linaje al anular o mover (`R178_LINEAGE_CANCEL_MOVE_INTEGRITY_MATRIX`)

**WAVE B · tranche 11 · pre-flight** · 2026-09-10 · hallazgo `R-178` (P3, registrado en el pre-flight del tranche 10) · **«linaje» = trazabilidad
generacional entre lotes (`egg_batches`, `chick_batches`), NO la línea genética** (`GeneticLine`/`WeightCurve`, `GA-REM-037`, intactas).

## 1. Hallazgo exacto

> `R-178` · P3 · «`egg_batches`/`chick_batches` (linaje) se materializan al casar despacho y recepción y no se neutralizan ni re-casan al cancelar
> o mover de lote un despacho/recepción; no es saldo» · `service.py:401-500` · `REMEDIATION_BACKLOG.md:1295`.

## 2. Qué es el linaje aquí (`§27`)

| Entidad | Tabla / campos | Relación | Fuente | Cuándo se crea | Para qué existe | ¿Histórico? | ¿Efectivo actual? | ¿Saldo? | ¿Auditoría? | ¿Traza de cadena? | ¿SAP futuro? | ¿UI? | ¿Varios vínculos? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `EggBatch` | `egg_batches`: `source_lot_id` → `hatchery_lot_id` · `dispatch_event_id` · `reception_event_id` · `quantity_dispatched` · `quantity_received` · `dispatch_date` · `reception_date` · `generation` · `notes` | lote de producción (abuelas/reproductoras) → lote de incubadora; par `egg_dispatch` ↔ `egg_reception_hatchery` | `spec.md §4.9` · `GA-REM-008` (`RC-04`: la misma remesa física, no el mismo `lot_id`) · `GA-REM-031` (exactamente uno por envío, cree quien cree) · `GA-REM-030` (los dos lotes de la misma empresa) · `OD-10 §2.4` («la fila es el traspaso») | al registrar el despacho si ya existe la recepción en el destino declarado, o al registrar la recepción si ya existe el despacho dirigido a su granja (`_auto_create_traceability_batches`); o manual (`POST /lots/egg-batches`, sin eventos) | «qué lote vino de qué lote, con fechas y cantidades» (`OD-10 §2.6`: categoría `B`, se ve entera) | **sí** (la fila no se borra: `BR-10`/`R10`, eliminación lógica) | **sí, a la vez**: el árbol (`GET /lots/{id}/traceability`) la devuelve tal cual, sin mirar el estado de sus eventos | **no** (ningún saldo la lee) | no (la auditoría es de los eventos) | **sí** (única fuente del árbol y del `TraceabilityTree.tsx`) | no hoy | sí (árbol) | sí: un despacho ↔ un vínculo (clave `dispatch_event_id`); una recepción puede quedar apuntada por más de uno si el despacho anterior se anuló y se registró otro |
| `ChickBatch` | `chick_batches`: `hatchery_lot_id` → `destination_lot_id` (`broiler_lot_id` legado) · `egg_batch_id` · mismos campos de par | lote de incubadora → lote de engorde/reproductoras; par `chick_dispatch` ↔ `bird_reception`; referencia al `EggBatch` del que procede | ídem | ídem | ídem (`data-model.md §118`: cadena generacional completa) | sí | sí | no | no | sí | no | sí | ídem |

**Consumidores efectivos** (búsqueda en `backend/app`): solo `lots/router.py` (`GET /lots/{id}/traceability`, `POST /lots/egg-batches`, `POST /lots/chick-batches`)
y `tenancy.py` (coherencia del par, `GA-REM-030`). Ningún informe, KPI, saldo ni traspaso pendiente (`handoff.py`) lee `egg_batches`/`chick_batches`.
El emparejamiento automático **ya excluye** eventos `CANCELLED` al buscar la contraparte (`_despacho_dirigido_a_este_lote`, `_recepcion_en_el_destino_declarado`).

## 3. Histórico ≠ efectivo (`§28`)

| Dimensión | Qué dice la fuente | Consecuencia |
|---|---|---|
| **Procedencia histórica** | `BR-10` / `docs/02 R10` (nivel 3/4): «Toda eliminación debe ser lógica y conservar trazabilidad»; `GA-REM-008` (rollback): «los vínculos creados no se borran»; `OD-10 §4bis` (nivel 1): «la historia anterior se conserva» | la fila del vínculo **no se borra** al anular ni al mover; la auditoría del evento (`CANCELLED`, `UPDATED` con valores) conserva el rastro |
| **Linaje efectivo** | `OD-10 §2.5` (nivel 1): «Un traspaso anulado o rechazado **sigue el contrato**: el lado que lo veía **lo ve desaparecer con su motivo**, no evaporarse sin explicación» · `OD-10 §2.4`: «la fila es el traspaso» (= `egg_batches`/`chick_batches`) · `GA-REM-008 AC04`: despacho sin recepción → «cadena marcada como incompleta» | el árbol **no** presenta como efectivo un traspaso cuyo despacho está anulado (desaparece), y presenta como **incompleto** un despacho cuya recepción está anulada; el **motivo** de la anulación es el residual `R-140`/`AOD-18` (hoy el `cancel` no lleva motivo): fuera, frontera documentada |
| **Reasignación de lote** (`R-173`, `RR-18`) | `GA-REM-031 AC03` (nivel 4, certificado): «`source_lot_id` es el lote que despachó y `hatchery_lot_id` el que recibió» (orientación correcta: el vínculo refleja los eventos) · `OD-10 §4bis`: «**Sin cascada automática.** Cambiar la cadena de un padre no reasigna a sus hijos en bloque: eso reinterpretaría operaciones históricas sin que nadie las hubiera revisado» · `OD-10 §4bis.5`: «**Ante la duda, se deniega**: si no se puede demostrar que NO hay efectos aguas abajo → DENEGAR» | mover el lote (o el destino declarado) de un evento que **ya participa** en un vínculo efectivo tiene efectos aguas abajo (el vínculo, la cadena `egg_batch_id`, la procedencia del lote hijo) y no puede relincarse sin reinterpretar historia → **se deniega**; el camino operativo es anular (gobernado, `R-173`) y registrar de nuevo, con lo que el emparejamiento crea el vínculo correcto (`GA-REM-031`) |

## 4. Matriz semántica (`§29`)

| Tipo de evento | Entidad | Significado | Evento origen | Evento destino | Hist./efect. | Creado cuando | Usado por | **Anular hoy** | **Mover hoy** | Anular esperado | Mover esperado | ¿Borrar? | ¿Desactivar? | ¿Re-enlazar? | ¿Conservar historia? | Lote viejo | Lote nuevo | Auditoría | Saldo | ¿Decisión? | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `egg_dispatch` (con recepción casada) | `EggBatch` | huevo fértil que salió del lote de producción hacia la incubadora | este | `egg_reception_hatchery` | ambos | al casar | árbol de A (`sent`) y de B (`received`) | la fila sigue; el árbol de A y de B **la muestran como traspaso vigente** (camión que no llegó) | `PUT`/corrección de `lot_id` → `200` (R-173 valida saldo de huevos); `source_lot_id` del vínculo **queda viejo** (`AC03` roto); el árbol del lote viejo sigue mostrando el envío | fila intacta; **no efectiva**: desaparece del árbol de A y de B; auditoría `CANCELLED` | **denegado** (`400`) mientras exista vínculo efectivo; cambiar `destination_farm_id` ídem | **no** | por lectura (dinámico: estado del evento) | **no** (sin cascada) | **sí** | intacto | — | del evento | ninguno | **no** (§3) | `AC-R178-02/04/05/06` | `LINA-` |
| `egg_reception_hatchery` (casada) | `EggBatch` | huevo fértil recibido en incubadora | `egg_dispatch` | este | ambos | al casar | ídem | fila sigue con `reception_event_id` anulado; el árbol muestra **recibido** | `lot_id` → `200`; `hatchery_lot_id` viejo | fila intacta; el vínculo se presenta **incompleto** (sin recepción, `AC04`); si se registra otra recepción, el emparejamiento la re-casa (comportamiento existente, control) | denegado (`400`) | no | por lectura | no | sí | intacto | — | del evento | ninguno | no | `AC-R178-03/07` | `LINA-` |
| `chick_dispatch` (casado) | `ChickBatch` | pollitos enviados a engorde/reproductoras | este | `bird_reception` | ambos | al casar | árbol | ídem huevo | ídem | ídem | denegado | no | por lectura | no | sí | — | — | — | ninguno | no | `AC-R178-08` | `LINA-` |
| `bird_reception` (casada) | `ChickBatch` | pollitos recibidos | `chick_dispatch` | este | ambos | al casar | árbol | ídem | ídem | incompleto | denegado | no | por lectura | no | sí | — | — | — | ninguno | no | `AC-R178-08` | `LINA-` |
| despacho/recepción **sin** vínculo | — | — | — | — | — | — | — | sin efecto en linaje | `R-173` como hoy (`200` si válido) | sin cambio | **sin cambio**: solo se deniega si hay vínculo efectivo | — | — | — | — | — | — | — | — | no | `AC-R178-09` (control) | `LINA-` |
| vínculo **manual** (`POST /lots/egg-batches`, sin `dispatch_event_id`) | `EggBatch` | enlace de corrección (`spec.md §4.9`, `GA-REM-008 AC07`) | — | — | efectivo por definición | a mano | árbol | no aplica (no hay evento que anular) | no aplica | sin cambio | sin cambio | — | — | — | — | — | — | — | — | no | `AC-R178-10` (control) | `LINA-` |

## 5. Reproducción (`§30`, `§31`) — leída del código, antes del rojo

- **Anular**: `cancel_event` (`R-173`: bloqueo, relectura, invariante del saldo) no toca `egg_batches`; `GET /lots/{id}/traceability` (`lots/router.py:150-197`)
  selecciona los vínculos por `lot_id` **sin** unir con `operational_events`; `EggBatchRead` ni siquiera expone `dispatch_event_id`. Resultado: el
  lote origen sigue viendo «enviado 100» y el de incubadora «recibido 100» tras anular el despacho. **Efecto de negocio activo**: la cadena de
  procedencia (categoría `B` de `OD-10`) afirma un traspaso que no ocurrió → violación de `OD-10 §2.5`. **CONFIRMADO**.
- **Mover**: `verificar_destino_de_edicion` valida el destino y el saldo (`R-173`) y no consulta vínculos; `source_lot_id` queda apuntando al lote que
  ya no tiene el evento → violación de `GA-REM-031 AC03` (orientación correcta) y reinterpretación de historia sin revisión (`OD-10 §4bis`). **CONFIRMADO**.

## 6. Bloqueos y concurrencia (`§36`)

Las mutaciones de evento ya se serializan por lote (`R-173`); la lectura del árbol es dinámica (no hay estado del vínculo que actualizar) → ninguna
capa de bloqueo nueva. Anular vs mover: el `cancel` relee el estado bajo el bloqueo; la guarda de linaje del `PUT` lee el vínculo dentro de la misma
transacción. **N/A** para carrera nueva (no hay escritura de linaje en estos caminos).

## 7. Clasificación y puerta

```
R-178 ............ CONFIRMADO · GOBERNADO · SIN DECISIÓN DEL PROPIETARIO · P3 → ejecutable · significado: linaje = trazabilidad generacional (no genética)
modelo ........... histórico conservado (fila + auditoría) + efectivo derivado del estado de los eventos (lectura) + reasignación denegada si hay vínculo efectivo
                   (OD-10 §2.5, §4bis, §4bis.5 · BR-10/R10 · GA-REM-008 AC04/AC06 · GA-REM-031 AC03) · sin borrar · sin re-enlazar · sin cascada
migración ........ ninguna (dinámico; sin bandera nueva) · sin cambio de esquema de respuesta (los campos de recepción ya son opcionales)
residual ......... «con su motivo» (OD-10 §2.5) depende del motivo obligatorio del cancel: R-140 / AOD-18 (fuera)
spec ............. GA-REM-031 enmienda A (linaje efectivo tras anular; reasignación denegada) · AC-R178-01…11
```

## 8. AC → prueba (contrato completo en `GA-REM-031-A`)

| AC | Qué | Prueba (`tests/test_lineage_cancel_move.py`, prefijo `LINA-`) |
|---|---|---|
| `AC-R178-01` | control: despacho con destino declarado + recepción → **un** vínculo, orientado; el árbol de A lo lista en `sent` y el de B en `received` | `_01` |
| `AC-R178-02` | anular el **despacho** → el vínculo desaparece de ambos árboles; la fila persiste; auditoría `CANCELLED`; saldos según `R-173` | `_02` |
| `AC-R178-03` | anular la **recepción** → el árbol de A lo muestra **incompleto** (sin cantidad ni fecha de recepción); el de B ya no lo recibe; fila persiste; registrar otra recepción vuelve a casar (control existente) | `_03` |
| `AC-R178-04` | mover (`PUT lot_id`) un despacho con vínculo efectivo → `400`; evento y vínculo intactos; saldos intactos | `_04` |
| `AC-R178-05` | corrección de `lot_id` / cambio de `destination_farm_id` de un despacho con vínculo → `400`; nada cambia | `_05` |
| `AC-R178-06` | mover una recepción con vínculo → `400` | `_06` |
| `AC-R178-07` | denegación por inquilino/unidad (`R-173`: otra empresa, unidad apagada) → vínculo intacto, ningún vínculo entre empresas | `_07` |
| `AC-R178-08` | cadena de pollitos (`chick_dispatch` ↔ `bird_reception`, `ChickBatch` con `egg_batch_id`): anular el despacho → desaparece; mover → `400` | `_08` |
| `AC-R178-09` | control: un despacho **sin** vínculo se mueve como hoy (`200`, `R-173`) | `_09` |
| `AC-R178-10` | control: el vínculo manual sigue visible y no depende de eventos | `_10` |
| `AC-R178-11` | segunda anulación → `400` sin segundo efecto; el árbol no cambia | dentro de `_02` |

Sensibilidad: `R178-S1` (el árbol vuelve a listar vínculos con despacho anulado) → `_02` roja · `R178-S2` (quitar la guarda de linaje en la reasignación)
→ `_04`/`_06` rojas · `R178-S3` (borrar la fila al anular) → `_02`/`_03` rojas (historia) · `R178-S4` N/A (linaje dinámico, sin escritura que pueda
quedar parcial).

## 9. Cierre (2026-09-10)

`R-178` CERRADO (técnico) · `GA-REM-031-A` certificada · `AC-R178-01…11` verdes · sensibilidad `R178-S1…S3` válidas (`S4` N/A: linaje dinámico) · evidencia `WAVE_B_TRANCHE_11_VALIDATION_PARITY_AND_LINEAGE_EVIDENCE.md`.
