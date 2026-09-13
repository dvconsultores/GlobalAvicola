# R-218 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-218/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R218-01 | (A) `GET /reports/lot/{id}/weekly` ⇒ serie por semana (mortalidad/alimento/peso/agua) | `test_r218_01` (rojo: no existe) |
| AC-R218-02 | Alcance por lote/unidad (patrón `_exigir_lote`): ajeno ⇒ 404 (control) | `test_r218_02` |
| AC-R218-03 | FE: la vista semanal muestra filas reales | unit/E2E (rojo) |
| AC-R218-04 | FE: gráficos de reportes con series reales (no planas) | E2E (rojo) |
| AC-R218-05 | Sin migración; sin permiso nuevo; diff FE (+BE si A) | revisión |
| AC-R218-06 | Regresión: `reports` suite, `test_kpi_scope.py` verdes | suites |

## 2 · Diseño RED

(A) `backend/tests/test_r218_weekly_aggregate.py` (rojo). FE: unit de la tabla/gráficos con mock del agregado. Salida `evidence/red/`.

## 3 · E2E

`R218-RT-01…02`: lote con pesajes/mortalidad ⇒ vista semanal y gráficos con datos (capturas). Artefacto `evidence/r218/runtime-{red,c3}.json`.

## 4 · UAT

**No requerida.** Verificación informativa: mostrar la vista semanal con datos reales.
