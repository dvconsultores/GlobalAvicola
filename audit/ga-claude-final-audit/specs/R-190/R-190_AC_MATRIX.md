# R-190 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Columna «RED en HEAD» = resultado esperado de la prueba **antes** de implementar. Artefactos bajo `audit/ga-claude-final-audit/specs/R-190/evidence/`.

| AC | Criterio (resumen) | Test unit / integración | RED en HEAD | Caso E2E | Caso UAT | Artefacto esperado |
|---|---|---|---|---|---|---|
| AC-R190-01 | distribución: lote sin galpón ⇒ `house_id` = galpón de fila ⇒ 201 | `r190.locationEventsHouse › AC-R190-01` | rojo (`house_id` undefined) | E2E-R190-01 | UAT-R190-01 | `runtime-c3/journal.json` paso `distribucion` + `R190-01.png` + payload |
| AC-R190-02 | salida: selector «Galpón del evento» ⇒ 201 | `r190.locationEventsHouse › AC-R190-02` | rojo (selector inexistente) | E2E-R190-02 | UAT-R190-02 | `R190-02.png` + payload |
| AC-R190-03 | recolección ⇒ 201 | `r190.locationEventsHouse › AC-R190-03` | rojo | E2E-R190-03 | UAT-R190-03 | `R190-03.png` + payload |
| AC-R190-04 | inspección sin granja ⇒ sin POST + mensaje; con granja ⇒ 201 | `r190.locationEventsHouse › AC-R190-04a/04b` | rojo (POST viaja; sin mensaje) | E2E-R190-04 | UAT-R190-04 | `R190-04a.png` (mensaje) · `R190-04b.png` (201) |
| AC-R190-05 | lote con galpón ⇒ galpón del lote (sin regresión) | `f01e.receptionHouse` (4/4) + `r190.locationEventsHouse › AC-R190-05` | verde (control) | E2E-R190-07 | — | journal paso `control-lote-con-galpon` |
| AC-R190-06 | API sin `house_id` ⇒ 400 BR-08 (backend intacto) | `test_r190_br08_contract.py::test_r190_01_*` + `test_r26_error_contract.py` BR-08 | verde (control) | E2E-R190-08 (sonda API) | — | `runtime-c3/sonda-br08.json` |
| AC-R190-07 | traslado ⇒ `house_id` = origen fila 0 | `r190.locationEventsHouse › AC-R190-07` | rojo | E2E-R190-05 | — | payload |
| AC-R190-08 | despacho huevo / inspección transporte ⇒ 201 | `r190.locationEventsHouse › AC-R190-08a/08b` | rojo | E2E-R190-06 | UAT-R190-05 | `R190-06.png` + payload |
| AC-R190-09 | sin fuente de galpón ⇒ sin POST + mensaje | `r190.locationEventsHouse › AC-R190-09` | rojo | E2E-R190-04 (variante) | UAT-R190-04 | captura del mensaje |
| AC-R190-10 | `farm_id` derivado del galpón | `r190.resolverUbicacion › farm desde galpón` | rojo (helper inexistente) | E2E-R190-04 | — | payload |
| AC-R190-11 | i18n ES/EN | `r190.locationEventsHouse › i18n` (lectura de `translation.json`) | rojo (claves ausentes) | — | UAT (EN) | captura EN |
| AC-R190-12 | móvil 390×844 | manual/Playwright viewport | — | E2E-R190-01m | UAT-R190-01 (móvil) | `R190-01m.png` |
| AC-R190-13 | sin migración/endpoint/permiso | revisión de diff | — | — | — | `git diff --stat c0b4afc..C2` |
| AC-R190-14 | helper cubierto por tabla | `r190.resolverUbicacion` (≥ 12 combinaciones) | rojo | — | — | salida vitest |
| AC-R190-15 | runtime completo sobre lote autocreado | — | — | E2E-R190-01…06 | — | `R-190_RUNTIME_CERTIFICATION.md` |
| AC-R190-16 | errores residuales renderizados como texto | `f01.errorRendering` | verde (control) | E2E-R190-08 | — | captura del toast |

Cobertura: 16 AC · 12 con RED nueva · 4 controles verdes · 8 casos E2E · 5 casos UAT.
