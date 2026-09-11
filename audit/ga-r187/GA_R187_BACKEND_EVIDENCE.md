# GA-R187 · EVIDENCIA BACKEND (local + CI declarado)

Fecha: 2026-09-11 · Commits: gobernanza `5a32a6c` (C1) · implementación `f755baa` (C2).

## 1 · Diff de implementación (mínimo, verificado)

```
backend/app/reports/router.py                 |  5 ++++-
backend/app/reports/service.py                | 11 +++++++++--
backend/tests/test_r184_ipe_date_semantics.py | 16 +++++++++++-----
3 files changed, 24 insertions(+), 8 deletions(-)
```

- `service.py`: docstring OD-22 + **`ipe = (viabilidad * ganancia_diaria) / (fcr * 10) if fcr > 0 else 0.0`** (retirado `* 100`). Nada más.
- `router.py`: docstring G-06 alineado.
- `test_r184_…`: mismos insumos crudos, nuevo esperado OD-22 (333.3) + nota de régimen anterior (§31). Los documentos `audit/ga-r184/**` NO se reescriben.
- Grep de rastros `× 100` en producto/tests (excluyendo comentarios históricos de las suites): **ninguno**.

## 2 · Gates locales ejecutados

| Gate | Resultado |
|---|---|
| `compileall` service/router | **OK** |
| Gate canónico `test_od16_global_read_boundary` + `test_migration_bu_catalog` (subset) | **7 passed**, 2 deselected |
| Suites `r184` + `r186` + `r187` | **1 passed** (matemática independiente R-187) + **33 skipped** — PG requerido, **skip declarado** (mismo patrón que R-184/R-186; corre en CI con `backend/scripts/run_tests.sh`) |
| `test_audit_reports` + `test_kpi_hatchery` | 13 skipped (PG, declarado) |
| `test_kpi_scope` | 15 errors **pre-existentes en local** (fixtures PG ausentes; declarado; corre en CI) — **no atribuible a R-187** (verificado por nombre de archivo) |

Sin "fake green": lo no ejecutable en local (PG) queda declarado y se cubre por **runtime autenticado** (§ evidencia runtime), como en R-184/R-186.

## 3 · GREEN determinista (núcleo)

- `test_r187_ac25_matematica_independiente` (puro, local): `round((95.0 × (2000/19)) / 30, 1) == 333.3` **PASS**; nota histórica `×100 == 33333.3` documentada.
- La suite PG R-187 afirma los valores exactos 333.3 / 241.1 / 282.7 / 249.9 / 250.0 / 300.0 (corre en CI).

## 4 · Fuera de alcance confirmado

G-05/R-186 sin diff · bandas/labels sin diff · `_dia()` sin diff · sin migración · sin endpoints/permisos nuevos · frontend sin diff.
