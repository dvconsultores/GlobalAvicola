# R-208 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · «RED en HEAD» = resultado esperado antes de implementar. Artefactos bajo `specs/R-208/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-R208-01 | Revisor sin `approvals:approve`: batch ⇒ 403, sin cambios | `test_r208_01` | rojo (200) | RT-01 | `runtime-c3.json` |
| AC-R208-02 | Aprobador: batch ⇒ 200 (control) | `test_r208_02` | verde | RT-02 | ídem |
| AC-R208-03 | `batch-reject` simétrico (`approvals:reject`) | `test_r208_03` | rojo | RT-03 | ídem |
| AC-R208-04 | BR-14 por evento intacta (control) | `test_r208_04` + r166 | verde | RT-04 | log |
| AC-R208-05 | Gate UI del panel por `approvals:*` | `r208.batchGates` | rojo (gatea por review) | RT-UI | captura |
| AC-R208-06 | Unitarias sin cambio (control) | `test_review.py` | verde | — | log |
| AC-R208-07 | Sin migración/endpoint/permiso nuevo | revisión diff | — | — | `git diff --stat` |
| AC-R208-08 | Regresión aprobación verde | suites | verde (línea base) | — | log |

Cobertura: 8 AC · 3 con RED nueva · 3 controles · 4 casos E2E + 1 UI · UAT no requerida.

## Trazabilidad fuente → AC

| Fuente (informe E E-09) | AC |
|---|---|
| `batch-*` con `review:review` vs unitarias `approvals:*` | AC-01/02/03/06 |
| Gate del panel por `review:review` | AC-05 |
| BR-14/R-143 intactas | AC-04 |
| Reglas de la casa | AC-07/08 |
