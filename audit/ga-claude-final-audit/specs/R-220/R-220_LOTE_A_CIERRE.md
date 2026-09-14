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
| **A3** (C#25) | KPIs ficticios del panel de aprobaciones retirados (sobre pendientes, «Aprobados/Rechazados» siempre 0) | FE 2F del lote A2 | re-insertar el KPI ficticio ⇒ RED | `.../loteA2/fe-s3-*` |
| **A5** (C#28) | El `reason` del motor de evaluación se muestra (`WeightEvaluation`) | ídem | retirar el render ⇒ RED | `.../loteA2/fe-s5-*` |
| **A7** (C#32) | Destinos de avisos: `lot` ⇒ lote, `sap_payload` ⇒ gestor SAP; guardia de textos ES/EN | `83010fd` | quitar destino lote ⇒ RED | `.../loteA5/fe-a7-*` |
| **A8** (C#33) | `X-Total-Count` en `/lots` y `/operations`; «Cargar más» con `skip` acumulado | `f760ecf` | quitar header BE / ignorar cabecera FE ⇒ RED | `.../loteA6/*` |
| **A10** (B-18) | `sap_reference` retirado del formulario (el esquema lo descartaba — P0-14) | `ac26733` | devolver el campo al payload ⇒ RED | `.../loteA7/fe-m1-*` |
| **A11** (B-19) | `farm_id` opcional en UI, alineado al contrato `Optional` | ídem | restaurar `min(1)` ⇒ RED | `.../loteA7/fe-m2-*` |
| **A15** (B-25) | `egg_classification` retirada de los mapas del catálogo (inalcanzable; la real es `egg_reception_classification`) | `a359eea` | re-añadir el icono ⇒ RED | `.../loteA8/fe-a15-*` |

### Lecturas dirigidas (verificadas por código, sin cambio de producto)

- **A12 (B-20)** · «Ovoscopía pierde el día»: el formulario registra `bird_movements.0.week_number`
  como «Día de ovoscopía» (`OperationFormPage.tsx`, `case 'ovoscopy'`) y el backend expone
  `week_number` en modelo y esquema — el dato viaja. Verificado por lectura (29 sesión).
- **A13 (B-21)** · `value_numeric`: presente en `InspectionDetail` (modelo), en
  `schemas.py` y en las lecturas del detalle; el serializador `F-01d` (T5) ya lo contempla.
  Verificado por lectura.

### Pendiente honesto del lote A (tanda A-extra)

- **A16 (B-35)** mensajes/validación de `birth_registration` (dosis/mixed+sexadas) y
  **A17 (B-38/B-39)** `week_number`/`avg_weight` solo en la fila 0 — requieren rediseño
  de filas dinámicas del formulario y su harness de submit por filas; quedan
  **abiertos y documentados** para su tanda (no se cierran como «lectura» porque la
  lectura muestra el hueco vigente).

- Segunda tanda: commit `aa3e41e` (C2b) · **FE suite completa 454/454 · build 0** · post-mutación 2/2 (`evidence/{green,sensibilidad,post-mutation}/loteA2/`).

- **Nota de harness (honestidad RED)**: el primer RED A9 falló también por URL de mock
  desalineada (`/approvals/pending`); corregida en C2. La prueba de causa exacta es la
  **mutación de sensibilidad** (retirar la guarda ⇒ 2 POST), registrada en evidencia.
- Commits: C1 `a9132a6` (RED) · C2 `ddc225f` (fixes). Post-mutación: BE 1/1 · FE 2/2.

## Pendientes del lote A

- **A16 (B-35)** y **A17 (B-38/B-39)** — tanda A-extra (arriba).
- Todo lo demás del lote A está cerrado o verificado por lectura (arriba).

## Pendiente de lotes B/C/D

- **B**: B1–B10 (navegación <1024px/móvil, rutas huérfanas, responsive) — AC-R220-B.
- **C**: C1–C9 (i18n) — AC-R220-C.
- **D**: D1–D3/D5 (código muerto/contratos obsoletos).

La certificación final de R-220 y `GA_T11` se emitirán al completar las tandas.
