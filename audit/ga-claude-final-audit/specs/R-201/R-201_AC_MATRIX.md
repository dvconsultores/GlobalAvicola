# R-201 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · «RED en HEAD» = resultado esperado de la prueba **antes** de implementar. Artefactos bajo `specs/R-201/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-R201-01 | Global sin contexto: `/sap/references` ⇒ `[]` | `test_r201_01` | rojo (filas de A+B) | RT-01 | `runtime-c3.json` |
| AC-R201-02 | Global sin contexto: jobs/consolidated/errors/payloads ⇒ `[]` | `test_r201_02` | rojo | RT-02 | ídem |
| AC-R201-03 | Consolidate/export sin contexto ⇒ 4xx sin leer (0 transiciones) | `test_r201_03` | rojo (transiciona) | RT-03 | ídem |
| AC-R201-04 | Retry sin contexto ⇒ 4xx; 0 reenvíos | `test_r201_04` | rojo (reenvía) | RT-04 | ídem |
| AC-R201-05 | Global situada en A: opera solo A | `test_r201_05` | verde (control) | RT-05 | ídem |
| AC-R201-06 | Actor de empresa intacto | `test_r201_06` + `test_sap_transversal` | verde (control) | RT-06 | log regresión |
| AC-R201-07 | Dos empresas: sin/con contexto no cruza | `test_r201_01/05` + fixture B | rojo/verde | RT-05 | ídem |
| AC-R201-08 | Sin migración/endpoint/permiso (diff) | revisión | — | — | `git diff --stat` |
| AC-R201-09 | `get_company_filter` retirado/obsoleto (C-05) | revisión | — | — | diff |
| AC-R201-10 | Regresión SAP verde (9+15) | suites | verde (línea base) | — | log |

Cobertura: 10 AC · 4 con RED nueva · 6 controles/verificaciones · 6 casos E2E API · UAT no requerida.

## Trazabilidad fuente → AC

| Fuente (informe D / GAP-02) | AC |
|---|---|
| `_company_filter` `true()` sin contexto | AC-01/02 |
| consolidate/export leen antes de fallar | AC-03 |
| `retry_failed` transversal sin guarda | AC-04 |
| Doctrina OD-14.d (global situada opera su empresa; actor de empresa intacto) | AC-05/06/07 |
| Regla de la casa: sin migración/endpoint/permiso | AC-08/09/10 |
