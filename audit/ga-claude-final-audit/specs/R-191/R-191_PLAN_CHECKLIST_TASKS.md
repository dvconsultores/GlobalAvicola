# R-191 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla: RED antes que GREEN; producto sólo en C2.** Sensibilidad después del commit de implementación, desde la raíz del repo (el driver revierte con `git checkout`).

## PLAN por tranches

| Tranche | Contenido | Salida | Estado |
|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding, spec, clarificaciones (C-02 verificada en roles reales; C-03/C-05 ratificadas con dominio), matriz AC, diseño; pruebas RED frontend (`r191.phaseTransition.test.tsx`) y backend (`test_r191_lot_phase_transition.py`); ejecución y lectura de la RED | commit C1 sin producto + `evidence/red/` | ☐ |
| **C2 · Implementación** | Backend: `ProductivePhaseRef`, `LotPhaseRead.phase`, `add_phase` (cierre anterior, derivación, guardas, bloqueo), helper saldo por sexo. Frontend: carga de fases maestras, cuerpo real, toasts, refetch, código de fase, i18n. GREEN dirigido + suites completas + tsc + build; sensibilidad tras commit | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación runtime** | Deploy; E2E-R191-01…05 en nube; consulta de reconciliación C-06; certificación | `evidence/runtime-c3/` + `R-191_RUNTIME_CERTIFICATION.md` | ☐ |
| **C4 · UAT** | UAT-R191-01…04; ratificación C-05; acta; backlog | acta + backlog | ☐ |

## CHECKLIST

- ☐ C1.1 Dedup y finding registrados
- ☐ C1.2 C-02: roles reales con `lots:create` verificados respecto a `masters:read` (alternativa B activada sólo si falta)
- ☐ C1.3 RED frontend escrita (4 casos) y RED backend escrita (7 casos)
- ☐ C1.4 RED ejecutada y leída: frontend falla en AC-01/02/03/10; backend falla en AC-06/07/08/09/13 y pasa en AC-05 (control)
- ☐ C1.5 Commit C1 (diff limitado a `audit/**`, `frontend/src/**/__tests__/**`, `backend/tests/**`)
- ☐ C2.1 `lots/schemas.py`: `ProductivePhaseRef` + `LotPhaseRead.phase`
- ☐ C2.2 `lots/service.py::add_phase`: guardas, cierre anterior, derivación con bloqueo del lote
- ☐ C2.3 `LotDetailPage.tsx`: carga de fases maestras, cuerpo `{lot_id, phase_id, start_date, poblaciones?}`, `toast`, refetch de lote+fases, `activePhaseName` por código
- ☐ C2.4 i18n ES/EN (`lots.transitionSuccess`, `lots.phaseAlreadyActive`)
- ☐ C2.5 GREEN dirigido + backend completo (PG) + vitest completa + tsc + build
- ☐ C2.6 Commit C2; sensibilidad S1-S4 tras el commit
- ☐ C3.1 Deploy + paridad
- ☐ C3.2 E2E-R191-01…05; 0 fatales; 0 `5xx`
- ☐ C3.3 Consulta C-06 ejecutada y reportada
- ☐ C3.4 Certificación escrita
- ☐ C4.1 UAT 4/4 + ratificación C-05
- ☐ C4.2 Backlog: R-191 `CLOSED`; nota en P1-12 REAPERTURA (auditoría `PHASE_STARTED`)

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED frontend (jsdom, `LotDetailPage`) | `frontend/src/pages/lots/__tests__/r191.phaseTransition.test.tsx` (nuevo) | M | — | C1 |
| T-02 | RED backend (PG; escenario `esc` propio con lote breeder, recepción y mortalidad aprobadas) | `backend/tests/test_r191_lot_phase_transition.py` (nuevo) | M | — | C1 |
| T-03 | Verificación C-02 (roles reales) | `audit/ga-claude-final-audit/specs/R-191/evidence/red/roles-lots-create.md` | S | — | C1 |
| T-04 | `ProductivePhaseRef` + `LotPhaseRead.phase` | `backend/app/lots/schemas.py:112-116` | S | T-02 | C2 |
| T-05 | `add_phase`: guardas (activo, fase distinta, fecha), cierre de la anterior, derivación por sexo con `bloquear_saldo_del_lote` | `backend/app/lots/service.py:685-697` (+ helper `saldo_por_sexo`) | M | T-04 | C2 |
| T-06 | Frontend: carga `productive-phases`, cuerpo real, toasts, refetch, código de fase | `frontend/src/pages/lots/LotDetailPage.tsx:44-73,88-93,121-138` | M | T-01 | C2 |
| T-07 | i18n | `frontend/public/locales/{es,en}/translation.json` | S | T-06 | C2 |
| T-08 | GREEN + regresión completa | — | S | T-04…T-07 | C2 |
| T-09 | Sensibilidad tras commit | — | S | T-08 | C2 |
| T-10 | Runner E2E runtime (Playwright; journal; capturas) | `scripts_e2e_r191.mjs` (raíz) | S | T-08 | C3 |
| T-11 | Ejecución C3 + consulta C-06 + certificación | `specs/R-191/evidence/runtime-c3/`, `R-191_RUNTIME_CERTIFICATION.md` | M | T-10 | C3 |
| T-12 | UAT + acta + backlog | `R-191_UAT_ACTA.md`; `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-11 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | el cuerpo vuelve a `phase_code` (sin `phase_id`) | AC-R191-03 |
| S2 | `catch` vuelve a `console.error` sin toast | AC-R191-02 |
| S3 | `add_phase` no cierra la fase anterior | AC-R191-06 / AC-R191-13 |
| S4 | derivación de poblaciones desactivada (0/0) | AC-R191-07 |

## Regresión obligatoria

Backend: `test_lots_bu_enforcement.py` (l09 control; l08 según GA-GOV-03), `test_lot_closure.py`, `test_lot_close_approval.py`, `test_population_invariant.py`, `test_opening_balance.py`, suite completa PG. Frontend: `gaFe04.lotsGates`, `gaFe06.lotFormContract`, `gaFe07.inactiveAreaEligibility`, vitest completa, tsc, build.
