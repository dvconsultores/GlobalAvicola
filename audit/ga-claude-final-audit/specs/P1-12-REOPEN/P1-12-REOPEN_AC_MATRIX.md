# P1-12-REOPEN · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/P1-12-REOPEN/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-P112-01 | Alta evento ⇒ 1 fila `created` | `test_p112_01` | rojo (2) | RT-01 | `runtime-c3.json` |
| AC-P112-02 | Review/approve/return/reject ⇒ 1 fila | `test_p112_02` | rojo (2-3) | RT-02 | ídem |
| AC-P112-03 | `complete_review` sin `corrected` espuria | `test_p112_02` | rojo | RT-02 | ídem |
| AC-P112-04 | Cierre/activación/fase ⇒ 1 fila | `test_p112_03` | rojo (0) | RT-03 | ídem |
| AC-P112-05 | Usuarios ⇒ 1 fila | `test_p112_04` | rojo (0) | RT-04 | ídem |
| AC-P112-06 | Evidencias ⇒ 1 fila | `test_p112_05` | rojo (0) | RT-05 | ídem |
| AC-P112-07 | Curvas ⇒ 1 fila | `test_p112_05` | rojo (0) | RT-06 | ídem |
| AC-P112-08 | Batch/contrapartida ⇒ transición | `test_p112_06` | rojo (0) | RT-07 | ídem |
| AC-P112-09 | Suite con listener verde | suite | mixto | RT-08 | log |
| AC-P112-10 | GA-REM-032 reconciliado | documental | — | — | nota |
| AC-P112-11 | Sin migración/endpoint/permiso | revisión | — | — | `git diff --stat` |

Cobertura: 11 AC · 8 con RED nueva · 1 documental · 8 casos E2E · UAT no requerida.

## Trazabilidad fuente → AC

| Fuente (E-11/E-10/E-12/E-13/E-15/E-16) | AC |
|---|---|
| Listener + helpers (duplicados) | AC-01/02/03 |
| Productores faltantes | AC-04/05/06/07 |
| Batch/contrapartida sin transición | AC-08 |
| Tests sin `lifespan` | AC-09 |
| GA-REM-032 | AC-10 |
