# R-208 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Cambio mínimo (router + gate UI).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED backend `test_r208_batch_approval_authority.py` + unit de gate UI; ejecución RED | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Decoradores `approvals:*` en batch; gate `ApprovalPanel`; GREEN + regresión; sensibilidad tras commit | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación** | E2E API `R208-RT-01…04` + regresión UI del panel (2 actores); certificación | C2 | `evidence/r208/runtime-c3.json` | ☐ |
| **C4 · Cierre** | Backlog: R-208 `CLOSED`; nota a administración de roles | C3 | backlog actualizado | ☐ |

## CHECKLIST

- ☐ C1.1 RED backend + unit de gate escritos/ejecutados (AC-01/03/05 rojos; controles verdes)
- ☐ C1.2 Commit C1 sin producto
- ☐ C2.1 Decoradores actualizados (`approvals:approve|reject`)
- ☐ C2.2 Gate de `ApprovalPanel` alineado
- ☐ C2.3 GREEN + regresión aprobación/BR-14/R-166
- ☐ C2.4 Sensibilidad S1
- ☐ C3.1 E2E API + UI regresión + certificación
- ☐ C4.1 Backlog + nota de roles

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED autoridad por lote | `backend/tests/test_r208_batch_approval_authority.py` (nuevo) | M | — | C1 |
| T-02 | Unit de gate UI | `frontend/src/pages/review/__tests__/r208.batchGates.test.tsx` (o extensión del suite GA-FE-05) | S | — | C1 |
| T-03 | Permisos del router | `backend/app/review/router.py:143-160` | S | T-01 | C2 |
| T-04 | Gate del panel | `frontend/src/pages/review/ApprovalPanel.tsx:100,119,173` | S | T-02 | C2 |
| T-05 | GREEN + regresión + sensibilidad | — | S | T-03/T-04 | C2 |
| T-06 | E2E API + UI + certificación | `specs/R-208/evidence/r208/` | S | T-05 | C3 |
| T-07 | Backlog/cierre | `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-06 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | revertir el permiso del batch a `review:review` | AC-R208-01/03 |

## Regresión obligatoria

`test_review.py` · `test_review_bu_enforcement.py` · `test_review_decision_concurrency.py` (`test_r166_*`) · `test_r143*` (si existe) · suite frontend vitest (gates) · suite completa por diferencia vs línea base GA-GOV-03 · UI `/approvals` con actor aprobador y revisor.
