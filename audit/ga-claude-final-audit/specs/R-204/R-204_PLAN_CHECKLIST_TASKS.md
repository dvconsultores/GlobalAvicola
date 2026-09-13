# R-204 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Solo lectura productiva tocada; sin migración/endpoint/permiso.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `test_r204_unit_scope_aggregates.py` (+ampliaciones); ejecución RED (3 rojos + controles) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Predicado en los 4 sumatorios + `get_all_kpis`; alertas del panel; decisión route_scope (aplicar/retirar); GREEN + regresión; sensibilidad tras commit | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación runtime (API + UI regresión)** | E2E API `R204-RT-01…06` (actores por unidad/apagada); `/reports` y `/dashboard/admin` en local (0 fatales) | C2 | `evidence/r204/runtime-c3.json` + certificación | ☐ |
| **C4 · Cierre** | Backlog: R-204 `CLOSED` con GA-REM; referencias R-216/R-214/route_scope | C3 | backlog actualizado | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita/ejecutada (AC01/02/04/05 rojos; controles verdes)
- ☐ C1.2 Commit C1 sin producto
- ☐ C2.1 `_filtro_de_lotes` aplicado en los sumatorios de incubadora (todos los caminos, incluido `get_all_kpis`)
- ☐ C2.2 `_get_active_alerts` acotado
- ☐ C2.3 route_scope decidido/aplicado (C-03)
- ☐ C2.4 GREEN + regresión KPI/OD-16 completa
- ☐ C2.5 Sensibilidad S1/S2
- ☐ C3.1 E2E API + UI regresión + certificación
- ☐ C4.1 Backlog + referencias

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED de alcance BU en agregados/alertas | `backend/tests/test_r204_unit_scope_aggregates.py` (nuevo) | M | — | C1 |
| T-02 | Ampliación de controles | `backend/tests/test_kpi_scope.py`, `test_kpi_hatchery.py` | S | — | C1 |
| T-03 | Predicado incubadora | `backend/app/reports/service.py:191-207,262-308,415-420` | S | T-01 | C2 |
| T-04 | Predicado alertas | `backend/app/dashboard/service.py:206-242` | S | T-01 | C2 |
| T-05 | route_scope (C-03) | `backend/app/business_units/route_scope.py`, `reports/router.py` | S | — | C2 |
| T-06 | GREEN + regresión + sensibilidad | — | S | T-03…T-05 | C2 |
| T-07 | E2E API + UI regresión + certificación | `specs/R-204/evidence/r204/` | M | T-06 | C3 |
| T-08 | Backlog/cierre | `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-07 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | predicado de los sumatorios de incubadora | AC-R204-01/02/04 |
| S2 | predicado de `active_alerts` | AC-R204-05 |

## Regresión obligatoria

`test_kpi_scope.py` (7 KPI por lote + panel) · `test_kpi_hatchery.py` · `test_od14_productive_surfaces.py` · `test_kpi_hatchery` control otra empresa · `test_dashboard*` (si existe) · suite completa por diferencia vs línea base GA-GOV-03 · UI: `/reports`, `/dashboard/admin`, `/kpi` en local.
