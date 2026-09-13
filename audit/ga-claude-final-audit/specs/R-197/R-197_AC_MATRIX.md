# R-197 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

Leyenda de nivel: `UNIT-BE` (pytest, PG de pruebas) · `UNIT-FE` (vitest/jsdom) · `E2E` (runtime local con semillas) · `UAT` (propietario, nube) · `CTRL` (control: verde hoy, protege regresión).

| AC | Criterio | Nivel | Prueba / paso | Estado hoy | Puerta de validez |
|---|---|---|---|---|---|
| AC01 | `GET /review/pending?status=in_review` ⇒ sólo `in_review` | UNIT-BE | `test_r197_01_status_in_review_devuelve_solo_in_review` | **RED** (devuelve `registered/pending_review`) | subconjunto exacto sobre un conjunto distinguible (≥1 evento por estado) |
| AC02 | sin `status` ⇒ `registered,pending_review` | CTRL | `test_r197_02_sin_status_conserva_el_defecto` | verde | ídem |
| AC03 | `status=foo` ⇒ 422 | UNIT-BE | `test_r197_03_status_invalido_es_422` | **RED** (200, parámetro ignorado) | código exacto |
| AC04 | `registered_by_id` filtra | UNIT-BE | `test_r197_04_registered_by_id_filtra` | **RED** | subconjunto exacto |
| AC05 | pestañas envían su `status` y muestran `total` del estado | UNIT-FE | `r197.reviewQueue.test.tsx › cada pestaña consulta su estado` | **RED** parcial (envía `status`, pero no las 7 y sin `corrected/rejected`) | URL capturada del mock |
| AC06 | evento `in_review` listado con Completar/Devolver | E2E | E2E-03 | **RED** (`R-12`, `H2-*`) | botones visibles + POST `/review/complete` 200 |
| AC07 | Devolver exige ≥ 10 en cliente y servidor | UNIT-FE + UNIT-BE | `r197.reviewQueue.test.tsx › devolver corto no envía`; `ReturnToOperatorRequest` (CTRL) | **RED** FE (usa `prompt`) | 0 POST con observación corta |
| AC08 | devuelto ⇒ «Devueltos»; reenviado ⇒ «Pendientes» | E2E | E2E-04, E2E-05 | **RED** | pestaña contiene el id |
| AC09 | `approved/consolidated/rejected/corrected` visibles en su pestaña | E2E | E2E-06 | **RED** | ídem |
| AC10 | acciones por evento: individuales + lote, `created_at asc` | UNIT-BE | `test_r197_05_acciones_por_evento_incluyen_las_individuales` | **RED** (404 ruta inexistente) | lista exacta de `action_type` |
| AC11 | evento ajeno ⇒ 404 | UNIT-BE | `test_r197_06_acciones_de_evento_ajeno_404` | **RED** (404 por ruta, no por alcance — se valida tras GREEN con sujeto B) | CONTROL/TRATAMIENTO mismo sujeto |
| AC12 | sin `review:read` ⇒ 403 | UNIT-BE | `test_r197_07_acciones_sin_review_read_403` | **RED** | código exacto |
| AC13 | `ReviewDetail` muestra el historial | UNIT-FE | `r197.reviewDetailHistory.test.tsx` | **RED** (llama `/review/batches`) | GET a `/review/events/{id}/actions` + render de `action_type` |
| AC14 | aprobar import sin lote ⇒ enlace a `/lots/{lot_id}` | UNIT-FE + UNIT-BE(CTRL) | `r197.approvalResult.test.tsx`; `test_r197_08_approve_devuelve_lot_id` | **RED** FE | `Link` con `href=/lots/N` |
| AC15 | detalle permanece y recarga | UNIT-FE | `r197.reviewDetailHistory.test.tsx › tras completar recarga` | **RED** (`navigate('/review')`) | 2.º GET `/operations/{id}` |
| AC16 | KPIs veraces | UNIT-FE | `r197.approvalResult.test.tsx › kpis` | **RED** | sin «Aprobados 0» ficticio |
| AC17 | doble clic ⇒ 1 POST | UNIT-FE | `r197.approvalResult.test.tsx › doble clic` | **RED** | `post` llamado 1 vez |
| AC18 | sin `users:read` ⇒ no `GET /users`, filtro oculto | UNIT-FE | `r197.reviewQueue.test.tsx › sin users:read` | **RED** (`ReviewCenter.tsx:109`) | 0 llamadas a `/users` |
| AC19 | 403 en carga ⇒ «sin permiso» | UNIT-FE | `r197.reviewQueue.test.tsx › 403` | **RED** («Sin resultados») | texto `review.noPermissionQueue` |
| AC20 | sin `prompt/alert` en revisión | UNIT-FE (guard) | grep en `pages/review/*.tsx` | **RED** (4 llamadas) | 0 coincidencias |
| AC21 | estados i18n en detalle | UNIT-FE | `r197.reviewDetailHistory.test.tsx › badge` | **RED** (`event.status` crudo) | `status.in_review` resuelto |
| AC22 | tenant/BU sin cambio | CTRL | `test_review_bu_enforcement`, `test_internal_reversal::test_s0*` | verde (salvo obsoletos GA-GOV-03) | suite |
| AC23 | guardianes exactos | UNIT-BE | `test_ac14_sin_migracion_ni_rutas_nuevas` (212), `test_rbac`, `test_las_rutas_nuevas_declaran…` | ajustar en C2 | igualdad exacta |
| AC24 | regresión motor | CTRL | `test_review_decision_concurrency`, `test_segregation_r143`, `test_full_workflow_audit` | verde | suite |
| AC25 | ES/EN + móvil | UNIT-FE + capturas | locales completas; 390×844 overflow 0 | — | capturas |
| AC26 | sin migración ni permiso | revisión de diff | — | — | `alembic heads` sin cambio |
| AC27 | E2E runtime 10/10 | E2E | `scripts_e2e_r197.mjs live` | — | `fatal_react 0`, `http5xx []` |
| AC28 | UAT | UAT | UAT-R197-01…06 | — | acta firmada |

Cobertura: 28 AC · RED válida esperable en 19 · control 5 · runtime/UAT 4.
