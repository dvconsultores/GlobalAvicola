# GA-FE-06 · ADDENDUM AL MASTER FRONTEND RUNTIME AUDIT — R-182 resuelto

Complementa: `MASTER_FRONTEND_REMEDIATION_ROADMAP.md`, `MASTER_PRODUCT_CAPABILITY_CATALOG.md`, `GA_FE_05_ADDENDUM_R181_SUBMIT_RESUBMIT.md`.
Fecha: 2026-09-11 · Generación: `index-DcqmSs-R.js` (entrada `index-WUv1-F9o.js`; `23ca59a`) · Estado: **FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING**.

## 1 · R-182 · antes → después

| | Antes | Después |
|---|---|---|
| `planned_close_date` | capturada en UI, **ausente del payload** (8 claves) ⇒ perdida silenciosa; SLA sin datos | viaja (YYYY-MM-DD), se persiste (medianoche UTC, R-75), se relee exacta y se **muestra** («Fecha prevista de cierre») |
| `area_id` | en zod, sin control ni envío | **selector «Área»** por empresa (`/masters/areas` acotado al inquilino; nombres, sin IDs crudos) + `area_id` en payload |
| Opcionalidad | — | sin fecha/área ⇒ `null` explícito (el SLA excluye NULL por contrato) |
| SLA «lote próximo a cierre» | regla correcta, fuente de datos inexistente | fuente reparada y certificada en runtime; aviso por el escáner horario del producto (3 capas de evidencia) |

## 2 · Superficies tocadas

`frontend/src/pages/lots/LotFormPage.tsx` (selector + payload) · `frontend/src/pages/lots/LotDetailPage.tsx` (fila de lectura) · `public/locales/{es,en}/translation.json` (`lots.area`) · test `gaFe06.lotFormContract.test.tsx`.
**0 backend · 0 migración · 0 permisos.**

## 3 · Evidencia y gates

- RED→GREEN: 4 objetivos rojos + 1 control → **5/5 verdes**; suite **278/278** (36 archivos) · tsc 0 · build PASS · backend PG-libre 7/7.
- Runtime congelado: E2E-01 alta válida (payload/fresh exactos; fila en detalle) · E2E-05 sin ±1 (bordes +10/+3/+1/−1) · E2E-03/06 selector sin áreas ajenas · E2E-04 NULL · E2E-08 RBAC (fail-closed + 403) · E2E-09 CBU (403) · AC30 ventana OFF (403) · E2E-14 validación · E2E-15 auditoría (9 altas GA6 registradas) · móvil 390×844 · EN.
- RED pre-corrección: vitest (4 fallos objetivos) + runtime (lote 17: payload sin claves, fresh null).

## 4 · Efecto en roadmap y catálogo

- **R-182: CLOSED** (`audit/ga-fe-06/GA_FE_06_R182_CLOSURE_RECONCILIATION.md`).
- R-98/R-119/R-181: CLOSED (sin regresión). BU-D10: PENDING_RATIFICATION. Wave B: PAUSED · Wave C/SAP: NOT STARTED.
- **Nuevos candidatos registrados** (no corregidos aquí): **`R-183`** — el alta/edición de lote persiste `area_id` de otra empresa vía API directa (201; la UI filtra) · **`R-184`** — `GET /reports/kpi/ipe/{lot}` 500 con lote recién creado (date − datetime) · observaciones N-3 (KPIs del detalle sin permiso ⇒ 403) y N-4 (granularidad de `new_values` en auditoría de alta).

## 5 · Límites honestos

- El aviso real del SLA depende del ciclo horario del escáner; el cierre documenta `PENDING_SCAN_WINDOW` si no corrió (sin forzarlo ni reimplementar la regla).
- La suite canónica del SLA (`tests/test_lot_planned_close.py`) requiere PG: corre en CI, no en local (declarado).
- N-1/N-2 son defectos **preexistentes** de backend ajenos a R-182; se registran con evidencia viva para decisión del programa (disciplina de alcance).
