# R-221 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** C-02 (micro-decisión) debe resolverse antes de C2 para el caso `farm_inspection`; el resto puede implementarse sin ella.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `test_r221_unit_derivation_no_lot.py` + extensiones; ejecución RED (3 rojos + controles); C-02 elevada | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Derivación por tipo inequívoco + guarda estricta; regla `farm_inspection` según C-02; GREEN + regresión; sensibilidad tras commit | C1 (+C-02) | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación runtime (API + UI regresión)** | E2E API `R221-RT-01…06`; UI: registro legítimo 201 + denegado seguro | C2 | `evidence/r221/runtime-c3.json` + certificación | ☐ |
| **C4 · Cierre** | Backlog: R-221 `CLOSED` con GA-REM; referencias R-153/OD-16/OD-23; bandeja actualizada si C-02=A | C3 | backlog actualizado | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita/ejecutada (AC01/02 rojos; controles verdes)
- ☐ C1.2 C-02 enviada al propietario (formato opción A/B/C)
- ☐ C1.3 Commit C1 sin producto
- ☐ C2.1 Lista de tipos inequívocos declarada y `hatchery_inspection` derivada
- ☐ C2.2 Guarda estricta con unidad derivada (global incluida)
- ☐ C2.3 Regla `farm_inspection` según C-02
- ☐ C2.4 GREEN + regresión BU/clasificación/R-153
- ☐ C2.5 Sensibilidad S1/S2
- ☐ C3.1 E2E API + UI regresión + certificación
- ☐ C4.1 Backlog + referencias

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED derivación sin lote | `backend/tests/test_r221_unit_derivation_no_lot.py` (nuevo) | M | — | C1 |
| T-02 | Extensiones W-xx y bandeja | `test_operations_bu_enforcement.py`, `test_pending_classification.py` | S | — | C1 |
| T-03 | `unidad_directa` generalizado (lista de inequívocos) | `backend/app/operations/service.py:242-246` | S | T-01 | C2 |
| T-04 | Guarda estricta con unidad derivada (documentar semántica) | `service.py:185-197`; `business_units/service.py:278-290` (nota) | S | T-03 | C2 |
| T-05 | Regla `farm_inspection` (C-02) | `service.py` según decisión | S/M | C-02 | C2 |
| T-06 | GREEN + regresión + sensibilidad | — | S | T-03…T-05 | C2 |
| T-07 | E2E API + UI regresión + certificación | `specs/R-221/evidence/r221/` | M | T-06 | C3 |
| T-08 | Backlog/cierre | `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-07 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | derivación `hatchery_inspection ⇒ hatchery` | AC-R221-01/03/09 |
| S2 | exigencia estricta con unidad derivada | AC-R221-01/02 |

## Regresión obligatoria

`test_operations_bu_enforcement.py` (W02…W14) · `test_lots_bu_enforcement.py` (capturas OD-16) · `test_pending_classification.py` · `test_r153_import_lot_auto.py` · `test_od16_global_read_boundary.py` · `test_business_units.py`/`test_business_unit_guard.py` · suite completa por diferencia vs línea base GA-GOV-03 · UI: `hatchery_inspection` por el hub (201 legítimo; denegado seguro con OFF).
