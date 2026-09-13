# GA-CLAUDE · R-204 — CERTIFICACIÓN (predicado de unidad en agregados y alertas)

Fecha: 2026-09-13 · Hallazgo **R-204** (P2 · bloquea fuga BU · GAP-07/08) · Paquete `specs/R-204/` · Clarificaciones C-01/C-03/C-06 · Commits: C1 `ca1fa39` · C2 `c1a21bd`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `red_c1.log` — **4F/2P**: `/reports/kpis` (bloque incubadora) y `/reports/kpis/hatchery` sumaban la unidad no concedida (800/1000/900); `dashboard/admin.active_alerts` incluía la alerta de un lote de hatchery; con la unidad **apagada** el agregado seguía sumando. Controles verdes (con unidad; otra empresa) |
| **C2 · Implementación** | ✅ | `green_c2.log` — **53/53** (R-204 6 + `test_kpi_hatchery` + `test_kpi_scope` + `test_business_unit_guard`); suite completa **1284 passed / 0 failed / 49 skipped** (1137.13s, `full_suite_c2.log`) · commit `c1a21bd` |
| **C2s · Sensibilidad** | ✅ S1·S2 | **S1** (sin predicado en agregados): 3F — RED-01/02/04 caen (`mutations/S1_sin_predicado.log`); **S2** (alertas sin filtro): 1F — RED-03 cae (`mutations/S2_alertas_sin_filtro.log`); mutaciones revertidas |
| **C3 · Runtime** | ⏸ **pendiente G-06** | Requiere actores con perfiles de concesión distintos en runtime — misma clase que R-199/201/202/203. Sondas `R204-RT-01…06` listas |

## 2 · Implementación

- `reports/service.py`: `get_kpi_hatchery` sin lote ⇒ `_filtro_de_lotes()` aplicado a **todos** los sumatorios (nacidos, cargados, fértiles, descartes) vía el nuevo parámetro `lotes` de los helpers. Subconjunto alcanzable; sin unidad ⇒ ceros (no 403 — `C-01`). `get_all_kpis` hereda.
- `dashboard/service.py::_get_active_alerts`: el `_ambito` que «se calculaba y no se aplicaba» ahora va **en la consulta** (`lot_id.in_(lotes)`); sin resolutor ⇒ lista vacía (fail-closed).
- `route_scope.py`: la declaración `UNIDAD_UNICA hatchery` de `/reports/kpis/hatchery` se **retira con nota razonada** (`C-03`, opción permitida): la lectura agregada devuelve subconjunto; aplicar `unidad_requerida` daría 404 y rompería el contrato de lectura uniforme.

## 3 · AC

| AC | Estado |
|---|---|
| AC-R204-01 (`/reports/kpis` sin hatchery ⇒ ceros) | ✅ RED-01 · S1 |
| AC-R204-02 (`/kpis/hatchery` sin unidad ⇒ vacío/ceros) | ✅ RED-02 · S1 |
| AC-R204-03 (alertas del panel acotadas) | ✅ RED-03 · S2 |
| AC-R204-04 (unidad apagada no agrega) | ✅ RED-04 · S1 |
| AC-R204-05 (control con unidad: valores idénticos) | ✅ 800/1000/900 verde |
| AC-R204-06 (control otra empresa: sin cruce) | ✅ verde |
| AC-R204-07 (contrato sin cambio de forma) | ✅ mismas claves |
| AC-R204-08 (sin migración/endpoint/permiso; diff de 3 ficheros) | ✅ diff |
| AC-R204-09 (regresión KPI/guarda) | ✅ 53/53 · suite completa 1284/0/49 |

## 4 · Veredicto

**R-204 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos; **C3 runtime pendiente de G-06**. La doctrina `OD-16` queda uniforme en la lectura agregada: mismo conjunto autorizado antes de sumar, nunca «sumar y descontar».
