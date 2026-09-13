# R-194 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-194/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R194-01 | Recepción UI ⇒ 201 (sin BR-08/422) | `r194 › recepción` | rojo (422/400) | E2E-01 | UAT-01 | journal+PNG+payload |
| AC-R194-02 | Fértiles en payload; saldo BR-03 > 0 | `r194 › fértiles` + control backend | rojo | E2E-01/02 | UAT-01 | payload + sonda |
| AC-R194-03 | `incubation_load` con petición y 201 | `r194 › carga` | rojo (sin petición) | E2E-03 | UAT-02 | journal |
| AC-R194-04 | Nacimiento: dosis válida ⇒ 201; inválida ⇒ error visible | `r194 › dosis` | rojo (sin envío) | E2E-05 | UAT-03 | PNG+payload |
| AC-R194-05 | Despacho ⇒ 201 (BR-04 real) | `r194 › despacho` + control | rojo (400 BR-08) | E2E-06 | UAT-04 | journal |
| AC-R194-06 | `hatchery_id` viaja y tenencia | `r194 › hatchery_id` | rojo | E2E-02 | — | payload |
| AC-R194-07 | Cadena completa por UI, 0 fatales/0 5xx | — | — | E2E-01…07 | UAT-05 | certificación |
| AC-R194-08 | ES/EN + móvil usables | lectura locales + viewport | — | E2E-07m/07en | UAT-05 | PNG |
| AC-R194-09 | Sin migración/endpoint/permiso; BR-02/03/04/21 intactas | revisión + controles | verde (control) | — | — | `git diff --stat` |
| AC-R194-10 | EggBatch/ChickBatch completados (X-BU) | verificación cruzada | — | E2E-06 | — | ídem |

Cobertura: 10 AC · 6 con RED nueva · 2 controles · 8 casos E2E · 5 casos UAT.

## Trazabilidad fuente → AC

| Fuente (B-01/02/03/05/22; runtime HAT2) | AC |
|---|---|
| `farm_id` undefined ⇒ BR-08 | AC-01/05 |
| Saldo lee `egg_movements[fertile]` | AC-02/03 |
| `arrival_date` requerido | AC-01 |
| `dosage_per_bird` sin `valueAsNumber` | AC-04 |
| `hatchery_id` nunca viaja | AC-06 |
| Cadena/X-BU | AC-07/10 |
