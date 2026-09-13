# R-211 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-211/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-R211-01 | 500+500 con filas 500/500 ⇒ 201 | `test_r211_01` | rojo (400) | RT-01 | `runtime-c3.json` |
| AC-R211-02 | Fila excedida ⇒ 400 con galpón/capacidad | `test_r211_02` | rojo (mensaje genérico) | RT-02 | ídem |
| AC-R211-03 | Mono-galpón excedido ⇒ 400 (control) | `test_r211_03` | verde | RT-03 | log |
| AC-R211-04 | Acumulado según C-02 | `test_r211_04` | según decisión | RT-04 | ídem |
| AC-R211-05 | Distribución multi-galpón sin regresión | regresión | verde | RT-05 | log |
| AC-R211-06 | Validación usa filas (documentado) | `test_r211_01` | rojo | — | salida |
| AC-R211-07 | Sin migración/endpoint/permiso | revisión | — | — | `git diff --stat` |
| AC-R211-08 | Regresión población/recepción verde | suites | verde (línea base) | — | log |

Cobertura: 8 AC · 3 con RED nueva · 2 controles · 5 casos E2E · 1 decisión del propietario (C-02).

## Trazabilidad fuente → AC

| Fuente (B-16; E-04) | AC |
|---|---|
| Σ contra `house_id` único | AC-01/02/06 |
| Galpones por fila (UI) | AC-01/05 |
| Capacidad no acumulada | AC-04 (C-02) |
| Reglas de la casa | AC-03/07/08 |
