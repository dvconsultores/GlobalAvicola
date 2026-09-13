# R-211 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** C-02 antes del cierre (no bloquea C1).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `test_r211_house_capacity_rows.py`; ejecución (AC-01/02 rojos; control verde) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Validación por fila (+ acumulado si C-02=B); mensaje; GREEN + regresión; sensibilidad | C1 (+C-02) | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación + UAT** | E2E multi-galpón (API/UI); decisión C-02 registrada | C2 | `evidence/r211/runtime-c3.json` + acta | ☐ |
| **C4 · Cierre** | Backlog: R-211 `CLOSED` con GA-REM | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita/ejecutada (AC-01/02 rojos)
- ☐ C1.2 C-02 elevada al propietario
- ☐ C1.3 Commit C1 sin producto
- ☐ C2.1 Agrupación por `target_house_id`
- ☐ C2.2 Mensaje con galpón/capacidad
- ☐ C2.3 Dependencia C-02 (acumulado) decidida/aplicada
- ☐ C2.4 GREEN + regresión + sensibilidad
- ☐ C3.1 E2E + acta C-02 + certificación
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED capacidad por fila | `backend/tests/test_r211_house_capacity_rows.py` | M | — | C1 |
| T-02 | Validación por fila + mensaje | `backend/app/operations/validators.py:712-725`; `service.py:900-906` | S | T-01 | C2 |
| T-03 | (Si C-02=B) acumulado por galpón | `validators.py` + consulta agregada | M | C-02 | C2 |
| T-04 | GREEN + regresión + sensibilidad | — | S | T-02/T-03 | C2 |
| T-05 | E2E + UAT + certificación | `specs/R-211/evidence/r211/` | S | T-04 | C3 |
| T-06 | Backlog/cierre | backlog | S | T-05 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | agrupación por fila (vuelve a Σ contra `house_id`) | AC-R211-01 |
| S2 | (C-02=B) agregado acumulado | AC-R211-04 |

## Regresión obligatoria

`test_population_invariant.py` · `test_reception_reconciliation.py` · `test_master_reference_tenancy.py` (galpones por fila) · suites `p03`/`p06` (tras GA-GOV-03) · `test_r190_br08_contract.py` (tranche contigua) · vitest/tsc/build si hubiera cambio FE (no previsto).
