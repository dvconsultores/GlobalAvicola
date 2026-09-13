# R-217 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-217/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R217-01 | Pestañas usan los estados reales; un payload `failed` aparece en «Errores» | unit (rojo: 0) |
| AC-R217-02 | Jobs `failed` no se muestran como `pending` | unit (rojo) |
| AC-R217-03 | Tras consolidar/exportar ⇒ refetch de KPIs/listas | unit (rojo) |
| AC-R217-04 | Retry visible solo con `sap:send_sap`; ejecuta `POST /sap/retry` para `failed` | unit (rojo) |
| AC-R217-05 | `delivers_to_sap=false`/`mode=manual` se muestran explícitamente | unit (rojo) |
| AC-R217-06 | DTO de importación corregido o retirado (C-02 documentada) | revisión |
| AC-R217-07 | Sin migración/endpoint/permiso; diff FE (+tests) | revisión |
| AC-R217-08 | Regresión: vitest, tsc, build; `test_sap*.py` verdes | suites |

## 2 · Diseño RED

Unit jsdom `r217.sapManager.test.tsx` con mocks de payload/jobs en los estados reales (rojos por vocabulario/refetch/retry). Salida `evidence/red/`.

## 3 · E2E

`R217-RT-01…04` (local con `SAP_ADAPTER=mock`): consolidar→refetch; `failed` visible; retry gateado; modo manual visible. Artefacto `evidence/r217/runtime-{red,c3}.json`.

## 4 · UAT

**No requerida ahora.** En la fase SAP, verificación informativa del Analista (estados reales y reintento).
