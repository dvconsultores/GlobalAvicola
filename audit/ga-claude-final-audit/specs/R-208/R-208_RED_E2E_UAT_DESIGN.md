# R-208 · DISEÑO DE PRUEBAS RED · E2E API · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 Backend — `backend/tests/test_r208_batch_approval_authority.py` (nuevo)

Actores: R1 (rol con `review:review` y **sin** `approvals:*`), A1 (rol con `approvals:approve/reject`), ambos en la misma empresa; 2 eventos en `corrected` creados por terceros.

| Nombre exacto | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_r208_01_revisor_sin_permiso_no_aprueba_en_lote` | R1 → `POST /approvals/batch-approve {event_ids:[e1,e2]}` | `status == 403` y ambos eventos siguen `corrected` — HEAD: 200 y aprobados |
| `test_r208_02_aprobador_aprueba_en_lote` (control) | A1 → mismo POST | 200; aprobados (verde) |
| `test_r208_03_reject_simetrico` | R1 → `batch-reject` | 403 — HEAD: 200 |
| `test_r208_04_br14_por_evento` (control) | A1 que rechazó e1 intenta batch con e1 | denegación por evento (403/400 según servicio) sin afectar e2 — verde |

### 1.2 Frontend — unit de gate

`ApprovalPanel` con sesión R1: botones de lote **no** visibles; con A1: visibles. RED: hoy el gate usa `review:review` ⇒ con R1 aparecen (rojo).

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r208_batch_approval_authority.py` ⇒ 2-3 rojos exactos + controles; `npx vitest run src/pages/review/__tests__/r208.batchGates.test.tsx` ⇒ rojo; salidas a `evidence/red/`.

## 2 · Diseño E2E API (C3)

Pila local; actores R1/A1; eventos `corrected`.

| Caso | Llamadas | Esperado |
|---|---|---|
| R208-RT-01 | R1 batch-approve | 403; estados intactos |
| R208-RT-02 | A1 batch-approve | 200; aprobados |
| R208-RT-03 | R1 batch-reject / A1 batch-reject | 403 / 200 |
| R208-RT-04 | BR-14: A1 auto-rechazado intenta aprobar su evento | denegación por evento |
| R208-RT-UI | Panel con R1 y con A1 (capturas) | sin botones / con botones |

Artefactos: `evidence/r208/runtime-{red,c3}.json` + capturas. Invariantes: 0 `5xx`; estados de los eventos verificados antes/después.

## 3 · Plan UAT

**No requerida.** Nota para administración: los roles que deban aprobar en lote necesitan `approvals:approve/reject` (ya exigido en las unitarias); se incluye en el acta de la tranche.
