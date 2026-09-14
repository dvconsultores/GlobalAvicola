# R-220 · LOTE A (representativos) — CIERRE PARCIAL DOCUMENTADO

Fecha: 2026-09-14 · Programa: GA PRE-SAP (T11) · Política: **AOD-29 Clarification 01**.
El SPEC permite ejecución **por lotes independientes** (`§3`); este documento cierra el
lote A en su subconjunto ejecutado y deja el resto del lote documentado para su tanda.

## Ejecutado y certificado localmente

| Ítem | Fix | RED | Sensibilidad | Evidencia |
|---|---|---|---|---|
| **A14** (B-24) | `water_consumption` añadido a `ALL_EVENT_TYPES` (BE) | `a9132a6` (`test_r220_catalogo_eventos` 1F) | quitar la entrada ⇒ RED 1F | `evidence/{green,sensibilidad}/loteA/be-a14-*` |
| **A9** (C#35) | Guarda de vuelo en `handleApprove` (1 POST por gesto) | FE 2F del lote | quitar la guarda ⇒ doble POST RED | `.../loteA/fe-a9-*` |
| **A4** (C#26) | `lot_id` nulo ⇒ «Se creará al aprobar» (no «#null») en `OperationListPage` | ídem | revertir el texto ⇒ RED | `.../loteA/fe-a4-*` |
| **D4** | Clase activa inválida `bg-white[0.12]` ⇒ `bg-white/[0.12]` (`SidebarItem`) | — (revisión dirigida, diseño §2) | grep 0 coincidencias + línea válida | `.../loteA/d4-clase-invalida.txt` |

- **Nota de harness (honestidad RED)**: el primer RED A9 falló también por URL de mock
  desalineada (`/approvals/pending`); corregida en C2. La prueba de causa exacta es la
  **mutación de sensibilidad** (retirar la guarda ⇒ 2 POST), registrada en evidencia.
- Commits: C1 `a9132a6` (RED) · C2 `ddc225f` (fixes). Post-mutación: BE 1/1 · FE 2/2.

## Pendiente del lote A (tanda siguiente)

A1 (formateador de fechas único), A2 (selector real de lote en reportes), A3 (KPIs del
panel de aprobación), A5 (`rule`/`reason` visibles), A6 (campos omitidos del detalle),
A7 (textos/navegación de notificaciones), A8 (paginación de listados), A10–A13/A15–A17
(contratos de formulario), **A18 (egg_storage sin lote ⇒ 4xx, BE)** — con A18 entra la
próxima corrida completa BE de la tanda.

## Pendiente de lotes B/C/D

- **B**: B1–B10 (navegación <1024px/móvil, rutas huérfanas, responsive) — AC-R220-B.
- **C**: C1–C9 (i18n) — AC-R220-C.
- **D**: D1–D3/D5 (código muerto/contratos obsoletos).

La certificación final de R-220 y `GA_T11` se emitirán al completar las tandas.
