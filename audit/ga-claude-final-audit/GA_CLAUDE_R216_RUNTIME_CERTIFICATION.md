# GA-CLAUDE · R-216 — CERTIFICACIÓN (`lots_by_type` con el valor del enum)

Fecha: 2026-09-14 · Hallazgo **R-216** (P2 · panel) · Paquete `specs/R-216/` (compacto) · Commits: C1 `074ee0a` · C2 `1ba1b11`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `red_c1.log` — **1F/1P**: `test_r216_01` rojo (claves `'BirdTypeEnum.BROILER'`… en lugar de `'broiler'`…, patrón local `H5-dashboard-admin`); control de suma verde (el total era correcto: el defecto solo afectaba a las claves) |
| **C2 · Implementación** | ✅ | `green_c2.log` — **49/49** (contrato R-216 + `test_kpi_scope` + `test_kpi_hatchery` + `test_business_unit_guard`); suite completa T3 **1286 passed / 0 failed / 49 skipped** (1171.11s, tip `1ba1b11`; `evidence/t3/full_suite_t3.log`) · commit `1ba1b11` |
| **C2s · Sensibilidad** | ✅ S1·S2 | **S1** (restaurar `str(row.bird_type)`): 2F — contrato + panel caen (`mutations/S1_str_restaurado.log`); **S2** (`row.bird_type.name`): 2F — claves en mayúsculas (`mutations/S2_name_mutado.log`); mutaciones revertidas |
| **C3 · Runtime** | ⏸ **piggyback G-06** | Verificación visual de las cuatro tarjetas del panel con datos reales — misma sesión runtime que las sondas R-199/201/202/203/204 |

## 2 · Implementación

- `dashboard/service.py::_get_lots_by_type`: `{row.bird_type.value: row.cnt …}` — `str()` de un `(str, Enum)` producía `'BirdTypeEnum.BROILER'`; `DashboardPage.tsx:255,513` busca `'broiler'` ⇒ las cuatro tarjetas mostraban **0** mientras la suma era correcta.
- `test_kpi_scope.py`: las dos aserciones por substring (`"breeder" in etiquetas`) pasaban con el defecto (`'birdtypeenum.breeder'` contiene `'breeder'`) — **endurecidas a claves exactas** (`"breeder" in claves`). La prueba existía y no probaba.
- Sin migración, sin endpoint, sin permiso (diff de 2 ficheros de producto/test).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R216-01 (claves = valores del enum, exactas) | ✅ `test_r216_01` · S1 · S2 |
| AC-R216-02 (control: la suma por tipo no cambia) | ✅ `test_r216_02` (verde en RED y GREEN) |
| AC-R216-03 (contrato FE: las 4 claves esperadas por `DashboardPage`) | ✅ claves exactas `{grandparent, breeder, hatchery, broiler}` |
| AC-R216-04 (sin regresión de KPI/guardas) | ✅ 49/49 dirigidas · suite T3 1286/0/49 |
| AC-R216-05 (runtime: tarjetas con datos) | ⏸ G-06 (visual) |

## 4 · Veredicto

**R-216 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos; **C3 visual pendiente de G-06**. El contrato de `lots_by_type` queda fijado por test: claves = valores del enum, y la suma intacta.
