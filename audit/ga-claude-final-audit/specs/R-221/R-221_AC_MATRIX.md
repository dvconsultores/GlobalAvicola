# R-221 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · «RED en HEAD» = resultado esperado antes de implementar. Artefactos bajo `specs/R-221/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-R221-01 | Global situada; hatchery OFF; `hatchery_inspection` ⇒ denegado | `test_r221_01` | rojo (201) | RT-01 | `runtime-c3.json` |
| AC-R221-02 | Actor solo broiler ⇒ denegado; 0 filas | `test_r221_02` | rojo (201) | RT-02 | ídem |
| AC-R221-03 | Con hatchery concedida/ON ⇒ 201 y `business_unit_id=hatchery` | `test_r221_03` | rojo (null) | RT-03 | ídem |
| AC-R221-04 | `farm_inspection` según C-02, sin regresión del flujo decidido | `test_r221_04` | según decisión | RT-04 | ídem |
| AC-R221-05 | `grandparent_import` intacto (R-153) | `test_r221_05` + regresión | verde (control) | RT-05 | log |
| AC-R221-06 | Eventos con lote intactos | `test_r221_06` | verde (control) | RT-06 | log |
| AC-R221-07 | Apagar revierte a denegado; re-encender no revive (OD-23) | `test_r221_01` + ciclo | rojo/verde | RT-01b | ídem |
| AC-R221-08 | Sin migración/endpoint/permiso; históricos intactos | revisión diff | — | — | `git diff --stat` |
| AC-R221-09 | Tipos inequívocos dejan de ir a bandeja pendiente | `test_r221_03` (bandeja) | rojo | RT-03 | ídem |
| AC-R221-10 | Regresión BU/clasificación/R-153 verde | suites | verde (línea base) | — | log |

Cobertura: 10 AC · 4 con RED nueva · 3 controles · 6 casos E2E · 1 micro-decisión del propietario (C-02).

## Trazabilidad fuente → AC

| Fuente (registro G-34; informe D B.13) | AC |
|---|---|
| `unidad_directa` solo para importación | AC-01/03 |
| `unidad=None` ⇒ «alguna unidad» | AC-01/02 |
| Runtime `OD16b-global-actor-bu-off-api` (201 con OFF) | AC-01/07 |
| `farm_inspection` tipo ambiguo | AC-04 (C-02) |
| R-153/OD-23/no-reglas-nuevas | AC-05/06/08/09/10 |
