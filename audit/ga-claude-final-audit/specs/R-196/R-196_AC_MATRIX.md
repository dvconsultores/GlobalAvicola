# R-196 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-196/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R196-01 | Crear farm ⇒ 201 | `r196.mastersCreate › farm` + backend | rojo (422/React#31) | RT-01 | UAT-01 | journal+PNG |
| AC-R196-02 | Crear house con padre ⇒ 201 | `› house` | rojo | RT-02 | UAT-02 | ídem |
| AC-R196-03 | hatchery/incubator/hatcher ⇒ 201 | `› hatchery/incubator/hatcher` | rojo | RT-03 | UAT-03 | ídem |
| AC-R196-04 | capacity/order vacíos ⇒ null | `› numerics` | rojo | RT-04 | — | payload |
| AC-R196-05 | Reactivar ⇒ activo | `› reactivar` | rojo (sin control) | RT-05 | UAT-04 | PNG |
| AC-R196-06 | 422 ⇒ mensaje texto | `› errors` | rojo (React #31) | RT-06 | UAT-04 | captura |
| AC-R196-07 | Navegación a todas las entidades | unit/E2E navegación | rojo (solo farms) | RT-07 | UAT-04 | PNG por entidad |
| AC-R196-08 | 409 legible | `› duplicate` | rojo/verde | RT-08 | — | captura |
| AC-R196-09 | Sin migración/endpoint/permiso | revisión | — | — | — | `git diff --stat` |
| AC-R196-10 | Regresión maestros verde | suites | verde (línea base) | — | — | log |

Cobertura: 10 AC · 8 con RED nueva · 8 casos E2E · 4 UAT.

## Trazabilidad fuente → AC

| Fuente (B-08/B-14/B-36; F G-01; runtime MAS/H4) | AC |
|---|---|
| Create sin padres ⇒ 422 | AC-01/02/03 |
| `capacity:''` ⇒ 422 | AC-04 |
| Sin reactivación | AC-05 |
| React #31 | AC-06 |
| Solo URL por entidad | AC-07 |
| Duplicados | AC-08 |
