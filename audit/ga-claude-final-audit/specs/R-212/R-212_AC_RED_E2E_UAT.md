# R-212 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-212/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R212-01 | Operador en detalle de lote: **0 peticiones** a `/reports/kpis|kpi/ipe|weight-uniformity` sin `reports:read` (o bloque «sin permiso» sin llamada) | unit gates (rojo: 12 llamadas) |
| AC-R212-02 | Home sin `dashboard:read` ⇒ landing útil (hub visible) sin error | unit + E2E (rojo: error) |
| AC-R212-03 | Aprobador en centro de revisión: no se pide `/users` sin `users:read` | unit (rojo: 7 llamadas) |
| AC-R212-04 | Listas: 403/500 ⇒ estado «prohibido»/«error» distinto de «vacío» (patrón `/users`) | unit por página (rojo) |
| AC-R212-05 | `LotReportPage`/`SapComparisonPage`: error ⇒ estado con reintento (no spinner eterno) | unit (rojo) |
| AC-R212-06 | Counts de consola `httpErrores` 403 = 0 en los recorridos de referencia | E2E |
| AC-R212-07 | Sin migración/endpoint/permiso; diff FE (+tests) | revisión |
| AC-R212-08 | Regresión: vitest completa, tsc, build; `gaFe03/04` gates intactos | suites |

## 2 · Diseño RED

Unit jsdom por superficie (mock api que rechaza con 403/500): aserciones de «no llamada» y de estado visible. Reproducción E2E local de los tres recorridos de `httpErrores` (operador/aprobador/home). Salida `evidence/red/`.

## 3 · E2E

`R212-RT-01…05`: operador (detalle lote, home), aprobador (revisión), listas con 403 forzado, reporte con error. Artefacto `evidence/r212/runtime-{red,c3}.json` + capturas; métrica: peticiones 403 = 0.

## 4 · UAT

**No requerida** (calidad interna; visible solo como mensajes más claros). Verificación informativa: mostrar el home de un rol operativo (landing útil) y una lista sin permiso (mensaje distinto de «vacío»).
