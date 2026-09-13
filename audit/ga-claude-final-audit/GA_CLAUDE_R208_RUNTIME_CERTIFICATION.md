# GA-CLAUDE · R-208 — CERTIFICACIÓN (C1 · C2 · C2s · C3 runtime)

Fecha: 2026-09-13 · Hallazgo **R-208** (P2 · bloquea control · E-09) · Paquete `specs/R-208/` · Commits: C1 `11b8f89` · C2 `331ad83`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | Backend `red_c1_backend.log` — **2F/2P**: `test_r208_01` (revisor con `review:review` sin `approvals:approve` **aprobaba** el lote ⇒ 200) y `test_r208_03` (batch-reject igual) rojos; controles 02/04 verdes. FE `red_c1_frontend.log` — **RED**: el revisor sin `approvals:*` **ve** los botones de lote (gate `review:review`); control A1 verde |
| **C2 · Implementación** | ✅ | Backend `green_c2_backend.log` — **17/17** (R-208 4/4 + `test_review_bu_enforcement` 5/5 + `test_review_decision_concurrency` 8/8=r166); FE `green_c2_frontend.log` — **5/5** panel (R-208 2 + GA-FE-04 3); **suite FE completa 45/45 archivos, 316/316**; **suite backend completa `1256 passed / 0 failed / 49 skipped`** (`full_suite_c2.log`, 20:43) · commit `331ad83` |
| **C2s · Sensibilidad** | ✅ S1 | Revertir la puerta del lote a `review:review` ⇒ 01/03 rojas de nuevo (`mutations/S1_sin_puerta.log`, 2F/2P); mutación revertida, worktree limpio |
| **C3 · Runtime** | ✅ | `runtime-c3.json` (20:52:24 +0200; deploy `Docker Push — Backend` #121 `331ad83` success + Watchtower): **operador** (sin `approvals:*`) ⇒ batch-approve/reject **403 «Permiso requerido: approvals:approve/reject»**; **aprobador** (`approvals:*`) ⇒ **404 «Evento no encontrado»** (puerta pasa, sin mutación de datos) |

## 2 · Implementación

- `review/router.py`: `batch-approve` ⇒ `require_permission("approvals","approve")`; `batch-reject` ⇒ `require_permission("approvals","reject")` — idénticas a las unitarias. Sin cambios en el servicio: BR-14/R-143 por evento intactas.
- `ApprovalPanel.tsx`: barra de lote gateada por `approvals:*` (aprobación y rechazo por separado); el revisor conserva el centro de revisión y los checkboxes de revisión (`review:review`).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R208-01 (revisor sin permiso ⇒ 403, cero cambios) | ✅ RED-01 (C1 rojo: 200) · Green C2 · S1 · runtime RT-01a |
| AC-R208-02 (aprobador ⇒ 200/según servicio, control) | ✅ C2 4/4 · runtime RT-02 (404 de servicio tras pasar la puerta — sin aprobar datos reales) |
| AC-R208-03 (reject simétrico) | ✅ RED-03 · S1 · runtime RT-03a/b |
| AC-R208-04 (BR-14/R-143 por evento intactas, control) | ✅ 04 verde + `test_review_bu_enforcement`/`r166` verdes |
| AC-R208-05 (gate UI por `approvals:*`) | ✅ FE 2/2 (RED R1 / control A1) |
| AC-R208-06 (unitarias sin cambio, control) | ✅ `GA-FE-04` 3/3 + suites unitarias backend |
| AC-R208-07 (sin migración/endpoint/permiso nuevo; diff router+panel+tests) | ✅ diff (`92+ / 7-` en 2 ficheros) |
| AC-R208-08 (regresión review/BR-14/r166) | ✅ 17/17 dirigidas · suite completa `1256/0/49` |

## 4 · Nota a administración de roles

Los roles que deban aprobar/rechazar **por lote** necesitan `approvals:approve`/`approvals:reject` — el flujo unitario ya los exigía; sin cambio efectivo de política para quien aprobaba de verdad. Los revisores (`review:review`) conservan revisión y pierden las acciones de aprobación en lote, como corresponde.

## 5 · Veredicto

**R-208 = `CLOSED_FUNCTIONALLY_CERTIFIED`** — C1/C2/C2s/C3 completos (local + runtime no destructivo). Frontera de autoridad uniforme entre unitario y lote; UAT del propietario no requerida (control interno).
