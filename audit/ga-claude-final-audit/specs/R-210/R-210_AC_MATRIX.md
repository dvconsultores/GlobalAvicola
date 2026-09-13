# R-210 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-210/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R210-01 | Etiquetas «(g)» en los 6 puntos ES/EN | `r210.weightUnit › labels` | rojo (fallbacks kg/step) | RT-01 | C-01 | salida vitest |
| AC-R210-02 | `step` coherente con g | `› steps` | rojo | RT-01 | — | ídem |
| AC-R210-03 | Serialización g + evaluación correcta | `› payload` + control backend | verde/rojo mixto | RT-02 | — | log + payload |
| AC-R210-04 | Sin «(kg)» en fallbacks | grep locales + unit | rojo | — | — | salida |
| AC-R210-05 | (Variante C-01=B) conversión explícita | unit de conversión | n/a | — | C-01 | salida |
| AC-R210-06 | Sin migración/endpoint/permiso | revisión | — | — | — | `git diff --stat` |
| AC-R210-07 | Regresión formularios | suites | verde (línea base) | RT-03 | — | log |
| AC-R210-08 | C-01 registrada | acta | — | — | sí | acta |

Cobertura: 8 AC · 3 con RED nueva · 1 control · 3 casos E2E · 1 confirmación UAT.

## Trazabilidad fuente → AC

| Fuente (B-12; FORM_CONTRACT §5.1; F) | AC |
|---|---|
| Step 0.001 + etiqueta (g) | AC-01/02 |
| Fallbacks «(kg)» | AC-04 |
| Curva/KPI en g | AC-03 |
| Decisión de unidad | AC-05/08 |
