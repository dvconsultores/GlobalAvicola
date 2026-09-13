# R-207 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-207/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R207-01 | Gate de acción (visible/no; API 403) | `r207 › gate` | rojo (no existe) | RT-01 | UAT-01 | captura |
| AC-R207-02 | Solicitar ⇒ 201; contrapartida visible; enlace | `r207 › request` | rojo | RT-02 | UAT-02 | journal+PNG |
| AC-R207-03 | Aprobar contrapartida ⇒ `reversed` + badges | `r207 › badge` | rojo | RT-03 | UAT-03 | PNG |
| AC-R207-04 | Motivo <5 ⇒ validación | `r207 › reason` | rojo | RT-04 | UAT-04 | captura |
| AC-R207-05 | 409 ⇒ mensaje | `r207 › conflict` | rojo | RT-05 | — | captura |
| AC-R207-06 | Sin cancelar/editar para `reversed` | unit/gates | rojo | — | — | salida |
| AC-R207-07 | ES/EN + móvil | locales + viewport | rojo | RT-03m | UAT-04 | PNG |
| AC-R207-08 | Sin migración/endpoint/permiso | revisión | — | — | — | `git diff --stat` |
| AC-R207-09 | Regresión reverso (API) + R-192/R-193 verificados | suites | verde (línea base) | — | — | log |

Cobertura: 9 AC · 6 con RED nueva · 5 casos E2E · 4 UAT.

## Trazabilidad fuente → AC

| Fuente (GA-REM-041/RES-04; C-13/C-27; H8*) | AC |
|---|---|
| Sin superficie (grep 0) | AC-01/02 |
| Estado `reversed` sin badge | AC-03 |
| Motivo ≥5 / elegibilidad / 409 | AC-04/05/06 |
| i18n / móvil / integridad | AC-07/08/09 |
