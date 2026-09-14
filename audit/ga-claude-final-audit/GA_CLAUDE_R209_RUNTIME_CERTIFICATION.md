# GA-CLAUDE · R-209 — CERTIFICACIÓN (las referencias SAP viajan por su código, nunca por id)

Fecha: 2026-09-14 · Hallazgo **R-209** (P2 · bloquea dato fuente SAP) · Paquete `specs/R-209/` · Commits: C1 `3fc1b91` · C2 `ae85a4e` · C2s `0073d57`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | FE `evidence/red/vitest-r209.log` — **2F/1P**: la OT de alimento guardaba `'9'` (id) y la referencia sin código guardaba `'5'`; **AC-01 control**: el selector compartido ya era canónico desde `R-189` (hallazgo de ejecución, no de spec). BE control `evidence/red/backend-r209-control.log` — comparativo **2/2** |
| **C2 · Implementación** | ✅ | `evidence/green/` — FE **12/12** dirigidas (R-209 + R-206 + contratos F-01); FE completa **375/375**; `tsc` 0 · commit `ae85a4e` |
| **C2s · Sensibilidad** | ✅ S1·S2 | S1 (fallback de id restaurado): 1F · S2 (OT de feed con id crudo): 1F — `evidence/sensibilidad/` |
| **C3 · Runtime** | ⏸ pendiente | R209-RT-01…04 (payloads reales + detalle + comparativo) — ventana de deploy |

## 2 · Implementación

- `identificadorDeOrdenSap` — **sin fallback de id** (`doc_number → ref_id → sap_code`; sin código ⇒ `''` ⇒ ausente).
- Selector de OC de `bird_exit` (interno) — `onChange` resuelve la orden y escribe el **código** en `sap_document_ref`/`extra_data.sap_order_ref` (con valor de control por id para la UI).
- OT de `feed_registration` (`feed_movements.0.sap_order_id`) — resuelve la orden y escribe código; nunca id de UI.
- Barrido `C-04`: expresión antigua `(doc||ref||sap||String(id)) === sapOrderRef` reemplazada por el helper.

## 3 · AC

| AC | Estado |
|---|---|
| AC-R209-01 (OC de salida = código) | ✅ control (R-189 ya canónico en el compartido) |
| AC-R209-02 (OT de alimento = código) | ✅ jsdom · S2 |
| AC-R209-03 (sin código ⇒ ausente) | ✅ jsdom · S1 |
| AC-R209-04 (comparativo por contrato — control) | ✅ BE 2/2 |
| AC-R209-05 (sin backend/migración) | ✅ diff FE-only |

## 4 · Veredicto

**R-209 = `CLOSED_TECHNICALLY`** — todo lo que el asistente escribe como referencia SAP es un **código canónico o ausencia**; los históricos con id no se tocan (C-03, inventario de lectura en C3). C3 runtime en ventana.
