# GA-R153 · EVIDENCIA RED

Fecha: 2026-09-12 · Baseline `9ad9b26` · Runtime `index-DtzHNDMG.js`.

## 1 · RED runtime (pre-fix, autenticado)

Probe `evidence/red-runtime.json` (admin global, empresa 1; BU Grandparent habilitada solo durante el probe y restaurada OFF):

```
PATCH /business-units/grandparent/enable ......... 200
POST  /operations {grandparent_import, sin lote} . 400  "El evento requiere lote"
PATCH /business-units/grandparent/disable ........ 200   (catálogo restaurado 4×OFF)
```

⇒ Prueba viva del prerequisito de lote (lo que OD-25(B) ordena eliminar para el flujo nuevo).

## 2 · RED frontend (vitest estático)

`npx vitest run src/pages/operations/__tests__/r153.importLotOptional.test.ts` → **3 failed / 0 passed**:

1. ✗ AC04/36 — el esquema deja de exigir lote para `grandparent_import` (hoy lo exige: `superRefine` + `LOT_OPTIONAL_INSPECTION_EVENTS`).
2. ✗ AC36 — nota informativa `operations.importLotAutoNote` (no existe).
3. ✗ AC38 — enlace a `/lots/{id}` y estado pendiente en el detalle (no existen).

## 3 · RED backend (PG — CI; local declarado)

`backend/tests/test_r153_import_lot_auto.py` — 9 casos (AC04…AC46): importar sin lote; aprobación crea 1 lote canónico; doble aprobación sin duplicar; legado sin segundo lote; devuelto sin lote y aprobado después sí; secuencia `-01/-02`; recepción puebla una sola vez; fallo de lote revierte la aprobación; BU OFF/sin concesión cerrados.

- Local (sin PostgreSQL): corrida = **errores de conexión** (suite PG; misma línea base del repo — declarado; CI la ejecuta vía `backend/scripts/run_tests.sh`).
- Pre-fix en CI: los casos de import-sin-lote (AC04) y auto-creación (AC06) fallarían contra el contrato actual (400 «El evento requiere lote» / cero lotes).

## 4 · Controles ya verdes que la implementación no debe romper

- AC-R152-08 (importación documental: saldo 0) — suite `test_grandparent_import.py`.
- R-130 (saldo no negativo) — `test_population_invariant.py`.
- P-07 (aprobación, segregación, concurrencia) — `test_review*`, `test_segregation_r143.py`.
