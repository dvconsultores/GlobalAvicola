# R-191 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `audit/ga-claude-final-audit/specs/R-191/evidence/`.

| AC | Criterio (resumen) | Test unit / integración | RED en HEAD | Caso E2E | Caso UAT | Artefacto esperado |
|---|---|---|---|---|---|---|
| AC-R191-01 | transición por UI ⇒ 201; badge «Producción»; botón oculto; acciones de producción | `r191.phaseTransition › AC-R191-01` | rojo (POST 422 simulado / badge ausente) | E2E-R191-01 | UAT-R191-01 | `R191-01-antes.png`, `R191-01-despues.png`, payload |
| AC-R191-02 | error ⇒ toast legible | `r191.phaseTransition › AC-R191-02` | rojo (`toastError` no llamado) | E2E-R191-04 | UAT-R191-03 | `R191-04.png` |
| AC-R191-03 | cuerpo con `lot_id`+`phase_id`, sin `phase_code` | `r191.phaseTransition › AC-R191-03` | rojo (`phase_id` undefined) | E2E-R191-01 | — | payload |
| AC-R191-04 | regresión l09 control | `test_lots_bu_enforcement.py::test_l09_*` | verde | — | — | log backend |
| AC-R191-05 | contrato de entrada intacto | `test_r191 › test_r191_05_contrato_actual_phase_id_sigue_vigente` | verde (control) | — | — | log |
| AC-R191-06 | fase anterior cerrada; una activa | `test_r191 › test_r191_01_add_phase_cierra_la_fase_anterior` | rojo (2 activas) | E2E-R191-02 | UAT-R191-01 | `GET /lots/{id}/phases` guardado |
| AC-R191-07 | poblaciones derivadas del saldo por sexo | `test_r191 › test_r191_03_poblacion_por_sexo_derivada_del_saldo` | rojo (0/0) | E2E-R191-02 | UAT-R191-02 | respuesta 201 guardada |
| AC-R191-08 | `phase {id, code, name}` en POST y GET | `test_r191 › test_r191_02_lectura_incluye_codigo_de_fase` | rojo (`KeyError 'phase'`) | E2E-R191-02 | — | respuesta |
| AC-R191-09 | 400: no activo / ya activa / fecha anterior | `test_r191 › test_r191_04_*` (3 casos) | rojo (201 hoy) | E2E-R191-04 | UAT-R191-03 | respuestas |
| AC-R191-10 | i18n ES/EN | `r191.phaseTransition › i18n` | rojo (claves ausentes) | — | UAT-R191-04 | captura EN |
| AC-R191-11 | móvil | viewport 390×844 | — | E2E-R191-01m | UAT-R191-04 | `R191-01m.png` |
| AC-R191-12 | sin migración/endpoint/permiso | diff | — | — | — | `git diff --stat` |
| AC-R191-13 | concurrencia: una sola activa | `test_r191 › test_r191_06_dos_transiciones_concurrentes_una_sola_activa` | rojo | — | — | log |
| AC-R191-14 | runtime nube | — | — | E2E-R191-01…05 | — | `R-191_RUNTIME_CERTIFICATION.md` |

Cobertura: 14 AC · 10 con RED nueva · 2 controles verdes · 5 casos E2E · 4 casos UAT.
