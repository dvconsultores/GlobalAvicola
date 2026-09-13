# R-205 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · «RED en HEAD» = resultado esperado antes de implementar. Artefactos bajo `specs/R-205/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Caso UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R205-01 | Hub `?type=` con lote breeder ⇒ cuadre+201 | `r205.breederReceptionParity › hub` | rojo (sin cuadre/400) | E2E-01 | UAT-01 | journal+PNG+payload |
| AC-R205-02 | Detalle de lote ⇒ paridad | `› detalle` | rojo | E2E-02 | UAT-02 | ídem |
| AC-R205-03 | URL directa sin regresión | `› directa` | verde (control) | E2E-03 | — | ídem |
| AC-R205-04 | Broiler/grandparent sin cuadre | `› otras cadenas` + backend | verde (control) | E2E-04 | — | payload |
| AC-R205-05 | Cuadre incompleto ⇒ sin POST + mensaje | `› validación` | rojo | E2E-05 | UAT-03 | captura mensaje |
| AC-R205-06 | API sin campos ⇒ 400 BR-20 | `test_r26_error_contract` + sonda | verde (control) | E2E-06 (sonda) | — | sonda JSON |
| AC-R205-07 | `?stage=` respetado | `r205.stageDerivation` (tabla) | rojo (helper no existe) | — | — | salida vitest |
| AC-R205-08 | i18n ES/EN | lectura locales | rojo si falta clave | — | UAT-04 (EN) | captura EN |
| AC-R205-09 | Móvil 390×844 | Playwright viewport | — | E2E-01m | UAT-01 (móvil) | PNG |
| AC-R205-10 | Sin migración/endpoint/permiso | diff | — | — | — | `git diff --stat` |
| AC-R205-11 | Runtime recepción breeder 201; p03/p04/p11 desbloqueadas | — | — | E2E-01…03 | — | certificación |
| AC-R205-12 | Regresión R-189/F-01e/R-190 | suites | verde (control) | E2E-03 | — | logs |

Cobertura: 12 AC · 5 con RED nueva · 4 controles · 6 casos E2E (+1 móvil) · 4 casos UAT.

## Trazabilidad fuente → AC

| Fuente (local BR2-*, B-16/B-41, C-3) | AC |
|---|---|
| Hub sin cuadre ⇒ 400 (`BR2-01`) | AC-01, 05 |
| Ruta directa muestra cuadre (`BR2-asistente`) | AC-03 |
| BR-20 backend | AC-04, 06 |
| `stage` como estado del paso 1 | AC-07 |
| Paridad de rutas + móvil/EN | AC-02, 08, 09 |
| Reglas de la casa + tranche conjunta R-190 | AC-10, 11, 12 |
