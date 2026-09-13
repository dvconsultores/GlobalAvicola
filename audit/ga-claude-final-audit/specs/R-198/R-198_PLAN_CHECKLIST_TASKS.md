# R-198 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED backend (detalle/gate/auditoría/borrado); C-01 registrada | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Detalle/ruta (C-01), gate servidor, auditoría (⇒ P1-12 T-06), orden de borrado, carga/gate UI, táctil | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación + UAT mínima** | Subir→F5→visible; gate; borrar auditado; móvil | C2 | `evidence/r198/runtime-c3.json` + acta | ☐ |
| **C4 · Cierre** | Backlog: R-198 `CLOSED` | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED ejecutada (AC-01/03/04 rojos)
- ☐ C1.2 C-01/C-02/C-03 registradas
- ☐ C2.1 Detalle (o relectura UI) devuelve evidencias
- ☐ C2.2 Gate de servidor por estado
- ☐ C2.3 Auditoría alta/baja (coordina P1-12 T-06)
- ☐ C2.4 Orden de borrado seguro
- ☐ C2.5 Botones visibles en táctil (C-06)
- ☐ C2.6 GREEN + regresión
- ☐ C3.1 E2E + UAT mínima + certificación
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED contrato/gate/auditoría | `backend/tests/test_r198_evidences_contract.py` | M | — | C1 |
| T-02 | Detalle incluye evidencias (C-01) | `operations/router.py:277-292` | S | T-01 | C2 |
| T-03 | Gate por estado (servidor) | `operations/service.py:1363-1414` | S | T-01 | C2 |
| T-04 | Auditoría alta/baja | ídem (con P1-12 T-06) | S | T-01 | C2 |
| T-05 | Orden de borrado | `service.py:1409-1414` | S | T-01 | C2 |
| T-06 | UI carga del servidor + gate + táctil | `OperationDetailPage.tsx:66,76-114,297,327` | M | T-02 | C2 |
| T-07 | GREEN + regresión + sensibilidad | — | S | T-02…T-06 | C2 |
| T-08 | E2E + UAT + certificación | `specs/R-198/evidence/r198/` | M | T-07 | C3 |
| T-09 | Backlog | backlog | S | T-08 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | relectura/contrato de evidencias | AC-R198-01 |
| S2 | gate de servidor | AC-R198-03 |
| S3 | auditoría de baja | AC-R198-04 |

## Regresión obligatoria

`test_od14_productive_surfaces.py` (s03/s04) · `test_lots_bu_enforcement.py` (e01…e08) · `test_operations_bu_enforcement.py` (w06b) · `test_transaction_boundary.py` (t_026_09) · suite completa por diferencia vs línea base GA-GOV-03 · UI detalle de operación (subir/listar/borrar).
