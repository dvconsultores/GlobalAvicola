# R-204 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · «RED en HEAD» = resultado esperado antes de implementar. Artefactos bajo `specs/R-204/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-R204-01 | `/reports/kpis` sin hatchery ⇒ bloque incubadora en cero | `test_r204_01` | rojo (datos de toda la empresa) | RT-01 | `runtime-c3.json` |
| AC-R204-02 | `/reports/kpis/hatchery` sin unidad ⇒ vacío/ceros | `test_r204_02` | rojo | RT-02 | ídem |
| AC-R204-03 | Con hatchery concedida: valores idénticos (control) | `test_r204_05` | verde | RT-03 | ídem |
| AC-R204-04 | Unidad apagada no aporta (OD-16) | `test_r204_04` | rojo | RT-04 | ídem |
| AC-R204-05 | alertas del panel acotadas por lotes alcanzables | `test_r204_03` | rojo | RT-05 | ídem |
| AC-R204-06 | Otra empresa sin cambio (control) | `test_r204_06` + `test_t_022_06` | verde | RT-06 | log |
| AC-R204-07 | Global situada con todas las unidades: control idéntico | `test_r204_05` variante | verde | RT-03 | ídem |
| AC-R204-08 | route_scope aplicado/retirado con nota | revisión | — | — | diff + nota |
| AC-R204-09 | Sin migración/endpoint/permiso | revisión diff | — | — | `git diff --stat` |
| AC-R204-10 | Regresión KPI/OD-16 verde | suites | verde (línea base) | — | log |

Cobertura: 10 AC · 4 con RED nueva · 4 controles · 6 casos E2E API/UI · UAT no requerida.

## Trazabilidad fuente → AC

| Fuente (informe D B.8/B.10; E-22/E-23) | AC |
|---|---|
| `get_kpi_hatchery(None)` sin `_filtro_de_lotes` | AC-01/02/04 |
| `_huevos_*`/`get_all_kpis` ídem | AC-01 |
| `_get_active_alerts` sin predicado | AC-05 |
| Excepción `get_sap_comparison` (BU-D04) | nota fuera de AC (C-02) |
| route_scope sin aplicación | AC-08 |
