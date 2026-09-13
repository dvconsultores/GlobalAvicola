# R-198 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-198/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R198-01 | Subir→F5 ⇒ visible | `test_r198_01` + UI | rojo (detalle `[]`) | RT-01 | UAT-01 | `runtime-c3.json` |
| AC-R198-02 | Relogin ⇒ visible | UI/manual+API | rojo | RT-02 | — | captura |
| AC-R198-03 | Estado no editable ⇒ denegado | `test_r198_02` | rojo | RT-03 | UAT-02 | ídem |
| AC-R198-04 | Alta/baja auditadas | `test_r198_03/04` | rojo | RT-04 | — | filas audit |
| AC-R198-05 | Borrado sin pérdida en fallo | `test_r198_05` | rojo (orden) | RT-05 | — | log |
| AC-R198-06 | Ruta de evidencias intacta (control) | `test_r198_06` | verde | — | — | log |
| AC-R198-07 | Táctil: botones visibles | UI móvil | rojo (hover) | RT-05m | — | PNG |
| AC-R198-08 | Sin migración/endpoint/permiso | revisión | — | — | — | `git diff --stat` |
| AC-R198-09 | Regresión evidencias/unidad verde | suites | verde (línea base) | — | — | log |

Cobertura: 9 AC · 5 con RED nueva · 1 control · 5 casos E2E · 2 UAT mínima.

## Trazabilidad fuente → AC

| Fuente (C#1/C#36; E-15/GAP-12) | AC |
|---|---|
| `pop("evidences")` en el detalle | AC-01/02 |
| UI local sin relectura | AC-01/02/06 |
| Sin gate | AC-03 |
| Sin auditoría | AC-04 |
| Borrado pre-commit | AC-05 |
| Hover en táctil (F R3) | AC-07 |
