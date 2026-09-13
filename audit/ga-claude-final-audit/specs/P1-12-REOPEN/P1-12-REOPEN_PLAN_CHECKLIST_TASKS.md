# P1-12-REOPEN · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** C-01 se cierra en C1 (opción técnica registrada).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); arnés con listener; RED `test_p112_audit_single_producer.py`; ejecución (rojos: duplicados y 0-filas) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Productor único (C-01); fix `complete_review`; productores nuevos (lotes/usuarios/evidencias/curvas/batch); GREEN + regresión; sensibilidad | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación** | Recuento por acción en runtime (API/UI local + nube si aplica); artefactos; reconciliación GA-REM-032 | C2 | `evidence/p112/runtime-c3.json` | ☐ |
| **C4 · Cierre** | Backlog: P1-12 `CLOSED`; registro de la reapertura; referencias | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 Arnés con `lifespan` (o registro explícito) y RED ejecutada
- ☐ C1.2 C-01 registrada (opción)
- ☐ C1.3 Commit C1 sin producto
- ☐ C2.1 Duplicados retirados (una fila por acción)
- ☐ C2.2 `complete_review` sin `corrected` espuria
- ☐ C2.3 Productores nuevos (7 acciones)
- ☐ C2.4 Batch/contrapartida con transición
- ☐ C2.5 GREEN + regresión + sensibilidad
- ☐ C3.1 Recuentos exactos con artefacto; GA-REM-032 anotado
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | Arnés con listener + RED de recuentos | `backend/tests/conftest.py` (afectados), `test_p112_audit_single_producer.py` | L | — | C1 |
| T-02 | Productor único (retirada de duplicados / idempotencia) | `audit/listeners.py`, `audit/helpers.py`, llamadas en servicios | L | T-01 | C2 |
| T-03 | Fix acción `complete_review` | `review/service.py:363` | S | T-01 | C2 |
| T-04 | Productores lotes | `lots/service.py:438-549,555-659,685-697` | M | T-01 | C2 |
| T-05 | Productores usuarios | `auth/service.py:337-421,491-506` | M | T-01 | C2 |
| T-06 | Productores evidencias/curvas | `operations/service.py:1363-1414`; `masters/curves.py:90,143` | S | T-01 | C2 |
| T-07 | Batch/contrapartida transición | `review/service.py:206-243`; `reversals/service.py:131` | S | T-01 | C2 |
| T-08 | GREEN + regresión + sensibilidad | — | M | T-02…T-07 | C2 |
| T-09 | Certificación + GA-REM-032 | `specs/P1-12-REOPEN/evidence/p112/` | M | T-08 | C3 |
| T-10 | Backlog/cierre | backlog | S | T-09 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | reactivar una llamada helper duplicada | AC-P112-01/02 |
| S2 | retirar un productor nuevo (p. ej. cierre) | AC-P112-04 |

## Regresión obligatoria

`test_audit_coverage.py` · `test_full_workflow_audit.py` · `test_audit_query.py` · `test_edit_cancel_balance.py` (conteos) · `test_state_continuity.py` · suites SLA (`test_lot_planned_close.py`) · suite completa por diferencia vs línea base GA-GOV-03 · sin cambios FE.
