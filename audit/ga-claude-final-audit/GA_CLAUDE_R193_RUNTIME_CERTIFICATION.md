# GA-CLAUDE · CERTIFICACIÓN RUNTIME — R-193 · ACUMULADO BR-18 NETO DE REVERSOS

Fecha: 2026-09-14 · Spec `specs/R-193` · Procesos: **P-01/P-02/P-03** (contrato de recepción contra OC) · Tranche T7 · Baseline: T6 CERRADA (`82b250f`).

## 1 · Ciclo ejecutado

| Fase | Commit(s) | Evidencia |
|---|---|---|
| **C1 · RED** | `c97b14e` | BE `5F` (`evidence/red/backend_red.log`): 01 «400 BR-18 ya recibidas: 800», 02 «400 tras aprobar el reverso», 03 «contrapartida rechazada cuenta», 04 «ya recibidas: 1600», 05 «ya recibidas: 1200» |
| **C2 · Implementación** | `0f61769` | `validate_oc_limit`: acumulado **neto** — `status.not_in([CANCELLED, REVERSED])` + `id.not_in(reversals.reversal_event_id)`; el original cuenta hasta que el reverso sea efectivo (`OD-19 §2`) |
| **C2s · Sensibilidad** | `0008541` | S1 (sin `REVERSED`) ⇒ 3F (02/04/05; `01` no cruza el límite) · S2 (sin excluir contrapartidas) ⇒ 1F (03) |
| **GREEN** | — | BE dirigido **5/5** · regresión (purchase-order-receipt, internal-reversal, reception-reconciliation, edit-validation-parity, population-invariant, R-192 contigua) **86/86** |
| **C3 · Runtime** | ⏸ ventana (G-06) | `R193-RT-00…05` sobre pila local (API): OC 1000 / 400 / reverso / 400 ⇒ 201 |

## 2 · Criterios de aceptación

| AC | Resultado | Dónde |
|---|---|---|
| AC01 tras reverso efectivo la OC recupera capacidad (201; neto en el mensaje) | ✅ | `test_r193_01`, `test_r193_05` |
| AC02 reverso pendiente no libera; al aprobar ⇒ 201 | ✅ | `test_r193_02` |
| AC03 contrapartida rechazada no cuenta (A cuenta); empresa gemela no influye | ✅ | `test_r193_03` |
| AC04 dos reversos ⇒ acumulado 0 (1000 ⇒ 201; +1 ⇒ 400) | ✅ | `test_r193_04` |
| AC05/AC06/AC07/AC08/AC09 sin reversos idéntico; edición paridad; empresa; sin migración; regresión | ✅ | suite 86/86 + guardianes |
| AC10 runtime API | ⏸ C3 en ventana | — |

## 3 · Observaciones al backlog (fuera de alcance, registradas)

- **OBS-R193-01**: `validate_oc_limit` invocada para `BIRD_DISTRIBUTION` suma su `total_qty` como recepción si lleva `sap_document_ref` de OC (sin evidencia de uso por UI; el asistente sólo ofrece OC en recepción/importación).
- **OBS-R193-02**: carrera preexistente entre dos recepciones concurrentes contra la misma OC (sin bloqueo del documento; no P1).

## 4 · Veredicto

**R-193 `CLOSED_TECHNICALLY`** — el acumulado contra la OC refleja lo realmente recibido (neto de reversos), preservando `exclude_event_id`, tenencia y empresa; sin migración. C3 runtime en ventana.
