# GA-FE-08 · EVIDENCIA DE REGRESIÓN BACKEND (focalizada, declarada)

Fecha: 2026-09-11 · C2 `a946cec`.

## 1 · Diff de backend

```
git diff --name-only 30fe3dc..HEAD -- backend/  →  0 archivos
```

**Sin cambios de contrato** (rutas, permisos, esquemas, migraciones). La autoridad sigue siendo backend; GA-FE-08 es solo representación UX de descubribilidad.

## 2 · Ejecución local declarada

Comando: `GA_TEST_ENV=1 GA_TEST_DATABASE_URL≈postgresql://127.0.0.1:5432/test_ga pytest tests/test_od16_global_read_boundary.py tests/test_r188_bu_lifecycle.py tests/test_business_units.py`

- Resultado local: `2 passed · 10 skipped · 30 failed · 33 errors` — **todos** por indisponibilidad de PostgreSQL local (misma línea base documentada desde GA-FE-02: los artefactos PG exigen servidor; fallan idéntico antes/después). El diff de backend es **0 líneas** ⇒ comportamiento pre/post idéntico por construcción.
- Suites PG ejecutadas por CI (PR) vía `backend/scripts/run_tests.sh` — sin cambios en este push.

## 3 · Cobertura canónica que protege esta tranche

- **OD-16 / OD-23** (preservados): `test_od16_global_read_boundary.py`, `test_r188_bu_lifecycle.py` (CI PG) — la entrada nueva no toca resolutores de alcance.
- **Contrato de ruta de Lotes**: sin cambios (App.tsx intacto; `CapabilityRoute` reusado) — protegido por `gaFe04.routeParity` y runtime E2E de esta tranche.
- **RBAC wildcard/espejo**: `gaFe02.permissions` (local) verde en la corrida completa.
