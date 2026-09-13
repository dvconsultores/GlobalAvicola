# GA-GOV-03 · BASELINE PRE-FIX DE LA SUITE (T1 · §9)

Corrida canónica **congelada**: primera ejecución completa de `backend/scripts/run_tests.sh` sobre `e828c3a`, sin modificaciones previas. No se sustituye por corridas posteriores.

## 1 · Resultado

| Métrica | Valor |
|---|---|
| Comando | `backend/scripts/run_tests.sh` (PG aislado vía pgserver) |
| Inicio / fin | 2026-09-13T04:42:10+02:00 → 2026-09-13T05:01:34+02:00 |
| Commit | `e828c3a0c1507aaae3a407432764f6df0757e414` (== `origin/main`) |
| Entorno | Python 3.11.2 · pytest 9.1.1 · pgserver 0.1.4 · `GA_TEST_ENV=1` |
| Alembic | cabeza única `y5z6a7b8c9d0` (código y BD) · 55 tablas |
| **Collected** | **1275** |
| **Passed** | **1201** |
| **Failed** | **25** |
| **Errors** | **0** |
| **Skipped** | **49** |
| Warnings | 16 (deprecations; sin impacto) |
| Duración | **1163.98 s (19:23)** |
| Log crudo | `evidence/backend_full_suite_pre_t1.log` (721 líneas) |
| JSON | `GA_GOV_03_PRE_FIX_TEST_BASELINE.json` |

## 2 · Los 25 fallos (25/25 = inventario canónico · 0 fuera de GA-GOV-03)

| # | Grupo | Test | Firma (resumen) |
|---|---|---|---|
| 1 | C | `test_company_catalog::test_t10` | `['y5z6a7b8c9d0'] == ['x4y5z6a7b8c9']` |
| 2 | A | `test_internal_reversal::test_s03_s04` | 404 == 403 «Evento no encontrado» |
| 3-6 | A | `test_lots_bu_enforcement::test_l08_{put,close,activate_manual,phases}` | 404 == 403 «Lot no encontrado» |
| 7 | A | `test_lots_bu_enforcement::test_l11…sigue_viendo_la_unidad_apagada` | fila de unidad apagada ya no visible |
| 8 | A | `test_lots_bu_enforcement::test_e06_control_la_autoridad_global` | 404 == 200 (evidencia de unidad apagada) |
| 9 | A | `test_od14_productive_surfaces::test_s02_situada_en_a…` | `{ev_a,ev_a_h} <= ids` — evento apagado invisible |
| 10-13 | A | `test_operations_bu_enforcement::test_w13_{submit,cancel,upload,delete}` | 404 == 403 «Evento no encontrado» |
| 14 | A | `test_operations_bu_enforcement::test_a08…ve_toda_la_empresa` | `{242,243,246} == {242,243,244,246}` |
| 15 | A | `test_operations_bu_enforcement::test_a13…no_resuelve_sobre_unidad_apagada` | 404 == 403 «Alerta no encontrada» |
| 16 | C | `test_population_invariant::test_ac14` | `['y5z6a7b8c9d0'] == ['x4y5z6a7b8c9']` |
| 17-21 | B | `test_r188_bu_lifecycle` ×5 | helper `:133` — `/me` **500** == 200 (correo `@e.test`) |
| 22 | A | `test_review_bu_enforcement::test_165_01` | 404 == 403 (acción `start`) |
| 23 | A | `test_review_decision_concurrency::test_r166_12` | 404 == 403 (unidad apagada) |
| 24 | A | `test_state_continuity::test_s07…` | 404 == 403 «Evento no encontrado» |
| 25 | C | `test_time_determinism::test_t028_04` | 4 fechas literales en 3 ficheros |

**Recuento**: A = 17 · B = 5 · C = 3 → **25**. Idéntico al inventario canónico de `GA_GOV_03_37_TEST_RECONCILIATION_MATRIX.md` y al histórico de la auditoría (`1201/25/49`). **OUTSIDE_GA_GOV_03: [] (ninguno).**

## 3 · Lectura

- Las 17 firmas del grupo A son **exactamente** el contrato OD-16 fail-closed (404/no-visibilidad) frente a aserciones obsoletas 403/visibilidad — sin ningún 500 ni excepción inesperada.
- Las 5 del grupo B fallan en el **helper** (`/me` 500 por `@e.test`), no en la lógica BU-D10.
- Las 3 del grupo C son guardas literales (cabeza Alembic + fechas en docstrings).
- No hay ningún fallo con sintomatología de defecto de producto (0 APP_DEFECT directo), coherente con la clasificación TEST_DEFECT ×25 de GA-GOV-03.

## 4 · Playwright (baseline PRE-T1)

El producto y los specs no han cambiado desde `c0b4afc` (auditoría) hasta `e828c3a` (solo `audit/**`). El baseline canónico Playwright es `audit/ga-claude-final-audit/evidence/playwright_e2e.log` (**117 passed · 12 failed**, 129 pruebas). El RED fresco dirigido de los 12 casos se ejecuta en esta tranche antes de tocar nada (log: `evidence/playwright_targeted_12_red_pre_t1.log`).
