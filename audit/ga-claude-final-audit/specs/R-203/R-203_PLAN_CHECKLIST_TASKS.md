# R-203 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Sin migración, sin endpoint, sin permiso.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `test_r203_lot_reference_tenancy.py` (+ampliación `test_lot_area_ownership.py`); ejecución RED (3 rojos + controles); inventario §12 (solo lectura) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Verificación de tenencia en alta/edición + `_curva_del_lote`; GREEN dirigido + regresión; sensibilidad tras commit | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación runtime (API + UI regresión)** | E2E API `R203-RT-01…06`; alta de lote por UI en local (0 fatales); inventario final | C2 | `evidence/r203/runtime-c3.json` + certificación | ☐ |
| **C4 · Cierre** | Backlog: R-203 `CLOSED` con GA-REM; referencias R-50/R-164/R-179 | C3 | backlog actualizado | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita y ejecutada (AC01-04 rojos; AC05/06 controles verdes)
- ☐ C1.2 Inventario §12 ejecutado (consulta de solo lectura) y registrado
- ☐ C1.3 Commit C1 sin producto
- ☐ C2.1 `house_id` verificado (alta y edición)
- ☐ C2.2 `genetic_line_id` verificado (nulo compartido intacto)
- ☐ C2.3 Curva coherente con línea alcanzable
- ☐ C2.4 GREEN + regresión completa de lotes/tenencia/curvas
- ☐ C2.5 Sensibilidad S1/S2
- ☐ C3.1 E2E API con artefacto; regresión UI de alta de lote
- ☐ C3.2 Inventario final (0 esperadas)
- ☐ C4.1 Backlog + referencias cruzadas

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED tenencia de referencias | `backend/tests/test_r203_lot_reference_tenancy.py` (nuevo) | M | — | C1 |
| T-02 | Ampliación área→galpón/línea/curva | `backend/tests/test_lot_area_ownership.py` | S | — | C1 |
| T-03 | Verificación alta (`house_id`, `genetic_line_id`) | `backend/app/lots/service.py:362-392` | S | T-01 | C2 |
| T-04 | Verificación edición (`PUT`) | `lots/service.py:411-436` | S | T-03 | C2 |
| T-05 | `_curva_del_lote` endurecido | `lots/service.py:275-307` | S | T-03 | C2 |
| T-06 | GREEN + regresión + sensibilidad | — | S | T-03…T-05 | C2 |
| T-07 | E2E API + UI regresión + inventario | `specs/R-203/evidence/r203/` | M | T-06 | C3 |
| T-08 | Backlog/cierre | `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-07 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | verificación de `house_id` | AC-R203-01/04 |
| S2 | verificación de línea/curva | AC-R203-02/03 |

## Regresión obligatoria

`test_lot_row_scope.py` · `test_lot_area_ownership.py` · `test_multicompany_isolation.py::test_idor_*` · `test_master_reference_tenancy.py` · `test_submovement_structural_tenancy.py` · `test_genetic_curves.py` · `test_edit_validation_parity.py` · suite completa por diferencia vs línea base GA-GOV-03 · UI: alta de lote local (P-03/P-06) sin regresión.
