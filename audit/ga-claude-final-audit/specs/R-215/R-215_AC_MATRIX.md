# R-215 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-215/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R215-01 | Maestros 422 ⇒ texto | `r215 › masters` | rojo (React #31) | RT-01 | UAT-01 | captura |
| AC-R215-02 | Lotes/trazabilidad/perfil ⇒ texto | `r215 › lots/trace/profile` | rojo | RT-02 | — | salida |
| AC-R215-03 | Usuarios sin `[object Object]` | `r215 › users` | rojo | RT-03 | — | captura |
| AC-R215-04 | Boundary con recuperación | `r215 › boundary` | rojo (no existe) | RT-04 | UAT-02 | PNG |
| AC-R215-05 | Sin stack / sin PII | revisión | — | — | — | — |
| AC-R215-06 | i18n boundary | lectura locales | rojo si falta | — | — | salida |
| AC-R215-07 | Sin migración/endpoint/permiso | revisión | — | — | — | `git diff --stat` |
| AC-R215-08 | Regresión | suites | verde (línea base) | — | — | log |

Cobertura: 8 AC · 4 con RED nueva · 4 casos E2E · 2 UAT.

## Trazabilidad fuente → AC

| Fuente (B-15; C#6/#7) | AC |
|---|---|
| `detail` crudo en 5 superficies | AC-01/02/03 |
| Sin `ErrorBoundary` | AC-04/05 |
| i18n | AC-06 |
