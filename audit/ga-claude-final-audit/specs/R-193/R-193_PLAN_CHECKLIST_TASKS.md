# R-193 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · C1 gobernanza + RED → C2 implementación → C3 certificación runtime (API) → C4 (sin UAT del propietario; acta técnica).

## PLAN

| Fase | Contenido | Entregable | ☐ |
|---|---|---|---|
| C1.1 | Preflight (HEAD, PG local de pruebas) | log | ☐ |
| C1.2 | RED backend `test_r193_oc_limit_after_reversal.py` (5 casos) ejecutado en HEAD: 4 rojos / controles verdes | `evidence/r193/red/backend_red.log` | ☐ |
| C1.3 | RED runtime API (pila local): `R193-RT-01` ⇒ 400 BR-18 «ya recibidas: 800» | `evidence/r193/red/runtime-red.json` | ☐ |
| C1.4 | Commit C1 | hash | ☐ |
| C2.1 | T-03 `validate_oc_limit` neto + docstring | diff | ☐ |
| C2.2 | GREEN dirigido + regresión (backend PG local por diferencia; frontend sin cambios: no se ejecuta salvo `tsc`/`build` de control) | logs | ☐ |
| C2.3 | Commit C2; sensibilidad S1/S2 (tras C2) | `evidence/r193/sensitivity.md` | ☐ |
| C3 | Runtime API post-fix `R193-RT-01…05` ⇒ 201/400 según AC; certificación técnica | `runtime-c3.json`, `R193_RUNTIME_CERTIFICATION.md` | ☐ |
| C4 | Acta técnica; backlog; (UAT opcional si el propietario lo solicita) | acta | ☐ |

## CHECKLIST

| AC | Tarea | Archivo | Test | Evidencia | ☐ |
|---|---|---|---|---|---|
| AC01, AC04, AC05 (mensaje) | T-03 | `backend/app/operations/validators.py:769-783` | `test_r193_01`, `_04`, `_05` | `backend_green.log` | ☐ |
| AC02, AC03 | T-03 | ídem | `test_r193_02`, `_03` | ídem | ☐ |
| AC05 | T-04 | — | `test_purchase_order_receipt.py` | ídem | ☐ |
| AC06 | T-04 | — | `test_edit_validation_parity.py` | ídem | ☐ |
| AC07 | T-02 | — | `test_r193_03` (variante empresa B) | ídem | ☐ |
| AC08 | T-04 | — | guardianes existentes | log | ☐ |
| AC09 | T-04 | — | suites listadas | logs | ☐ |
| AC10 | T-05 | — | runtime API | `runtime-c3.json` | ☐ |

## TAREAS

| ID | Contenido | Archivos | Tamaño | Depende | ☐ |
|---|---|---|---|---|---|
| T-01 | Gobernanza (paquete; OBS-R193-01/02 al backlog) | `specs/R-193/*` | S | — | ☐ |
| T-02 | RED: `backend/tests/test_r193_oc_limit_after_reversal.py` (fixture: `SapReference` OC 1000 prefijo `R193-`, lote broiler con galpón, actores solicitante/aprobador; teardown con `Reversal`, `ApprovalAction`, `SapReference`) + runner API `R193-RT-*` | tests, `evidence/r193/red/` | M | T-01 | ☐ |
| T-03 | `validate_oc_limit`: `status.not_in([CANCELLED, REVERSED])` + `id.not_in(select(Reversal.reversal_event_id))`; docstring `OD-19` | `backend/app/operations/validators.py` | S | T-02 | ☐ |
| T-04 | GREEN + regresión (`test_purchase_order_receipt`, `test_internal_reversal`, `test_reception_reconciliation`, `test_edit_validation_parity`, `test_population_invariant`; suite completa por diferencia) | — | M | T-03 | ☐ |
| T-05 | C3 runtime API + certificación + backlog | `evidence/r193/`, `R193_RUNTIME_CERTIFICATION.md` | S | T-04 | ☐ |
| T-06 | Sensibilidad S1 (quitar `REVERSED` de la exclusión ⇒ `test_r193_01/_04` rojos), S2 (quitar la exclusión de contrapartidas ⇒ `_02/_03` rojos); revertir con `git checkout` | — | S | T-04 | ☐ |

Riesgo: la fixture necesita un lote **con galpón** y capacidad ≥ 1000 (BR-17) y `SapReference` `purchase_order` de la empresa de pruebas (`sap/references/import` o inserción directa como `test_purchase_order_receipt.py`).
