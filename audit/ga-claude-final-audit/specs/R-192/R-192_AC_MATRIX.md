# R-192 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

Fecha: 2026-09-13. Columnas: AC → prueba unitaria/integración (RED en HEAD salvo «control») → E2E runtime → UAT → artefacto de evidencia.

| AC | Criterio (resumen) | Unit / integración (fichero::test) | RED en HEAD | E2E runtime (paso) | UAT | Evidencia |
|---|---|---|---|---|---|---|
| AC01 | Par revertido + resto aprobado ⇒ `close` 200 | `backend/tests/test_r192_lot_close_after_reversal.py::test_r192_01_un_par_revertido_no_impide_el_cierre` | **rojo** (400 R7) | `H8b-cierre-con-reverso` ⇒ 200 | UAT-R192-01 | `evidence/r192/{red,green}/backend_*.log`, `runtime-c3.json` |
| AC02 | Control gemelo sin reverso ⇒ 200 | `test_lot_close_approval.py::test_t_076_01` (existente) | verde (control) | `H8b-control-cierra-200` | UAT-R192-01 | ídem |
| AC03 | Contrapartida pendiente ⇒ 400 R7, sin mutación | `::test_r192_02_la_contrapartida_pendiente_si_impide_el_cierre` | verde (control) | `R192-UI-02` (toast R7 con contrapartida pendiente) | UAT-R192-02 | ídem + PNG |
| AC04 | 13 estados conservan veredicto; `REVERSED` no bloquea | `::test_r192_06_ningun_estado_cambia_de_veredicto` (parametrizado sobre `BLOQUEAN`/`NO_BLOQUEAN` + `REVERSED`) | verde/rojo (sólo `REVERSED` rojo) | — | — | `backend_green.log` |
| AC05 | `total_mortality` excluye cancelados | `::test_r192_03_el_resumen_excluye_cancelados` | **rojo** (15 ≠ 5) | `R192-RT-03` (resumen del gemelo) | UAT-R192-03 | `runtime-c3.json` |
| AC06 | `total_feed_kg` excluye el par revertido | `::test_r192_04_el_resumen_excluye_el_par_revertido` | **rojo** (14.0 ≠ 3.0) | `H8b-cierre-con-reverso.resumen.total_feed_kg` | UAT-R192-03 | ídem |
| AC07 | `total_eggs` excluye cancelados | `::test_r192_03_…` (segundo aserto) | **rojo** | — | — | log |
| AC08 | `total_events`/`approved_events` sin cambio | `test_lot_closure.py::test_t_073_01` (existente) + aserto en `test_r192_04` | verde | `H8b` resumen | — | log |
| AC09 | BR-05 ignora pesaje revertido | `::test_r192_05_br05_ignora_el_pesaje_revertido` | **rojo** (200 ≠ 400) | — | — | log |
| AC10 | 400 no muta `status`/`end_date` | `::test_r192_02` (asertos finales) | verde | `H8b` (lote sigue `active`) | — | log |
| AC11 | UI: 400 ⇒ toast con `detail`; sin React #31 | `frontend/src/pages/lots/__tests__/r192.closeLotError.test.tsx::«un 400 R7 al cerrar se muestra como toast»` | **rojo** (sin toast) | `R192-UI-02` | UAT-R192-02 | `vitest_*.log`, `R192-UI-02.png` |
| AC12 | UI: 200 ⇒ tarjeta de resumen neto | `r192.closeLotError.test.tsx::«un 200 pinta el resumen»` (control) | verde | `R192-UI-01` | UAT-R192-01 | PNG |
| AC13 | UI: 403/404 ⇒ toast legible | `r192.closeLotError.test.tsx::«403 y 404 se muestran»` | **rojo** | `R192-UI-04` (aprobador sin `lots:create`: botón oculto; sonda API 403) | — | PNG/JSON |
| AC14 | Sin migración/endpoint/permiso nuevo | guardianes existentes (`test_ac14_sin_migracion_ni_rutas_nuevas`, cabeza Alembic) | verde | — | — | log |
| AC15 | Regresión completa | suites backend PG local (por diferencia vs línea base `GA-GOV-03`), vitest ≥ 314, `tsc`, `build` | — | — | — | logs |
| AC16 | Runtime C3 post-fix | — | — | H8b completo + UI escritorio/móvil | — | `runtime-c3.json`, PNG |
| AC17 | Mensaje R7 «reverso pendiente de decisión» (C-07) | `::test_r192_02` (aserto de texto, condicional) | rojo si C-07 | `R192-UI-02` | UAT-R192-02 | PNG |

Sensibilidad (tras C2): S1 retira `REVERSED` del conjunto de R7 ⇒ AC01/AC04(`REVERSED`) rojas · S2 retira el filtro de estado del resumen ⇒ AC05/AC06/AC07 rojas · S3 retira el `toast.error` ⇒ AC11/AC13 rojas · S4 retira `REVERSED` de BR-05 ⇒ AC09 roja.
