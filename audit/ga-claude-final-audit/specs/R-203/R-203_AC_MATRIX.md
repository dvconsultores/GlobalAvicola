# R-203 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · «RED en HEAD» = resultado esperado antes de implementar. Artefactos bajo `specs/R-203/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-R203-01 | Galpón ajeno en alta ⇒ 404, 0 filas | `test_r203_01` | rojo (201) | RT-01 | `runtime-c3.json` |
| AC-R203-02 | Línea ajena ⇒ 404; nula ⇒ 201 | `test_r203_02` | rojo (201 ajeno) | RT-02 | ídem |
| AC-R203-03 | Curva de línea ajena rechazada | `test_r203_03` | rojo (aplica) | RT-03 | ídem |
| AC-R203-04 | PUT a ajenos ⇒ 404; propios ⇒ 200 | `test_r203_04` | rojo | RT-04 | ídem |
| AC-R203-05 | weight-evaluation sin fuga (rangos propios intactos) | `test_r203_05` (control) | verde | RT-05 | ídem |
| AC-R203-06 | Alta legítima UI/API intacta | `test_r203_06` + regresión | verde | RT-06 | log + captura UI |
| AC-R203-07 | A/B: ninguna puerta cruza | `test_r203_01…04` | rojo | RT-01…04 | ídem |
| AC-R203-08 | Sin migración/endpoint/permiso | revisión diff | — | — | `git diff --stat` |
| AC-R203-09 | Inventario §12 medido y registrado | consulta SQL lectura | — | — | `evidence/inventory.txt` |
| AC-R203-10 | Regresión tenencia/curvas verde | suites | verde (línea base) | — | log |

Cobertura: 10 AC · 4 con RED nueva · 2 controles · 1 medición · 6 casos E2E API/UI-regresión · UAT no requerida.

## Trazabilidad fuente → AC

| Fuente (informe D A.11 / GAP-06) | AC |
|---|---|
| `house_id` asignado sin `verificar_pertenencia` | AC-01/04/07 |
| `genetic_line_id` sin verificación de catálogo | AC-02/04/07 |
| `_curva_del_lote` sin empresa de la línea | AC-03/05 |
| Edición por `MasterService.update` sin `house_id` en `_PADRES_TENANT` | AC-04 |
| Reglas de la casa | AC-08/09/10 |
