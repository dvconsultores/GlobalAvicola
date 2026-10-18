# 10 · Regresión completa

Código de la aplicación **sin cambios** (el seed es aditivo); la regresión se ejecuta como control de no-regresión y para incorporar los 16 tests nuevos del seed.

## Backend — `scripts/run_tests.sh` (pgserver aislado, migraciones reales, guardas del arnés)

| Métrica | Valor |
|---|---|
| Resultado | **1722 passed · 0 failed · 49 skipped** · 32 warnings · 23 min 37 s |
| Delta vs. certificación SPEC 006 | 1706 → 1722 (+16: `tests/test_qa_integral_dataset.py`) · skipped 49 = 49 |
| Pines del arnés | cabeza `e0f1a2b3c4d5` · 65 tablas · recuento de rutas sin cambios (no se tocó la app) |
| Log | `evidence/10_backend_regression.log` (sin DSN, sin secretos) |

## Frontend — `frontend/`

| Comando | Resultado |
|---|---|
| `npx vitest run` | **542 passed / 542** (91 archivos) |
| `npx tsc -b` | PASS (rc 0) |
| `npx vite build` | PASS (rc 0) |
| Log | `evidence/10_frontend_regression.log` (Node v24.13.0) |

## Tests del seed en aislado

`run_tests.sh tests/test_qa_integral_dataset.py tests/test_seed_email_domains.py` ⇒ 18 passed (detalle en `05_TESTS.md`).

## Sin reducción de tests

Ningún test existente fue modificado, marcado como skip ni eliminado. Las guardas del arnés (Alembic, rutas, tablas) no se avanzaron porque no hubo cambios de esquema ni de API.
