# GA-FE-05 · ADDENDUM AL MASTER FRONTEND RUNTIME AUDIT — R-181 resuelto

Complementa: `MASTER_FRONTEND_RUNTIME_GAP_MATRIX.md`, `MASTER_PRODUCT_CAPABILITY_CATALOG.md`, `GA_FE_03_ADDENDUM_DYNAMIC_NAVIGATION.md`, `GA_FE_04_ADDENDUM_INTRA_SCREEN_AUTHORITY.md`.
Fecha: 2026-09-11 · Generación: `index-WUv1-F9o.js` (`005a252`) · Estado: **FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTED** (GA-UAT-03: A) ACEPTO GA-FE-05, sin observaciones).

## 1 · R-181 · antes → después

| | Antes | Después |
|---|---|---|
| CTA envío/reenvío | inexistente (`operationsService.submit` con 0 llamadores) | «Enviar a revisión» / «Reenviar a revisión» en `/operations/:id`, state-aware |
| Estado visible | chip con valor crudo (`registered`) | chip localizado `t('status.*')` con fallback |
| Feedback | — | toast ES/EN + **GET fresco** (sin optimismo) |
| Seguridad | — | permiso de acción `operations:create` ∧ unidad (evaluador GA-FE-04) ∧ estado reenviable; backend autoridad (404/403/400 verificados) |
| Reenvío (`OD-17.a/b`) | solo por API | UI, mismo endpoint canónico |

## 2 · Superficies tocadas

`frontend/src/pages/operations/OperationDetailPage.tsx` · `services/operations.service.ts` (sin cambios; se cableó su uso) · `public/locales/{es,en}/translation.json` (5 claves nuevas + 3 `status.*`) · test `gaFe05.submitGates.test.tsx`.

## 3 · Evidencia y gates

- RED→GREEN: 10/10 (6 objetivos + 4 controles) · suite **273/273** · tsc 0 · build PASS · backend PG-free 7/7.
- Runtime (generación congelada): E2E-01 submit · E2E-07 resubmit · E2E-09 doble clic · E2E-10 fallo · E2E-05/08 estados · E2E-03/04 negativos · E2E-02 CBU OFF (C y global) · EN · móvil. Auditoría verificada.
- 0 cambios backend · 0 permisos nuevos · 0 migraciones.

## 4 · Efecto en roadmap

- **R-181: CLOSED** (`audit/ga-fe-05/GA_FE_05_R181_CLOSURE_RECONCILIATION.md`).
- R-98/R-119: CLOSED (sin regresión). R-182: **UNCHANGED / OPEN**. BU-D10: PENDING_RATIFICATION. Wave B: PAUSED · Wave C/SAP: NOT STARTED.

## 5 · Límites honestos

- La confirmación es toast + recomputo de estado (sin modal), decisión documentada en clarificaciones C12.
- Negativas de unidad usan `404` anti-enumeración (no 403) — semántica canónica ya existente; registrada tal cual.
- Fixtures de operación quedan en estados legítimos de producto como evidencia retenida (ledger).
