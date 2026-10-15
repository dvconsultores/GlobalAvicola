# Implementation Plan: SPEC 006 — Cutover Initial Balances Remediation

**Feature**: `specs/006-cutover-initial-balances-remediation` · **Fecha**: 2026-10-15 · **Rama**: `main`
**Tipo**: remediación post-certificación con certificación local + verificación en runtime

## 1 · Technical Context

Backend FastAPI/SQLAlchemy async/openpyxl (+ `csv` stdlib) · PostgreSQL/Alembic · React/Vite/vitest · Playwright (openpyxl vía `execFileSync` para fixtures).

## 2 · Constitution / Safety Check

| Principio | Cumplimiento |
|---|---|
| NO SPEC/AC/TEST/E2E/EVIDENCE | spec + AC-CUT2-01…58; RED antes de implementar; E2E UI por BU; evidencia en `audit/cutover-initial-balances/` |
| Sin rama; stage explícito; AOD-29 | `main`; 3 commits; push + `REMOTE_SHA_MATCH` |
| OD-16, OD-09, OD-14, RBAC intactos | solo se reutilizan `unidades_habilitadas`/`unidades_concedidas` y `cutover:*` |
| Sin datos fabricados | UNKNOWN/N/A preservados; sin tolerancias |
| Mutation checkpoint | S1–S12 tras `IMPLEMENTATION_SHA`, restauración explícita, post-mutación |

## 3 · Diseño

```
backend/app/cutover/
  contracts.py   registry: FieldSpec (name, type, unit, required, allow_unknown, allow_na, master, target, rule) · CONTRACTS[bu] · versión v2
  parser.py      lectura XLSX (openpyxl, data_only + detección de fórmulas) y CSV (utf-8-sig, delimitador por cabecera) → filas crudas → normalización por contrato → {value,status}
  validation.py  maestros por empresa/BU, padre-hijo, fase/BU, lote existente, opening existente, consistencia, fechas
  templates.py   XLSX (Instrucciones/Meta/Datos/Catalogos) y CSV; `?format=` ; `?batch_id=` rellena corte
  service.py     ciclo de vida (igual) + listado/detalle + preview + errores descargables + apply por BU (builders) + reconciliación por BU
  models.py      HatcheryOpening
  reporting.py   post-corte: aves (igual) + huevos cargados/nacidos/despachados para hatchery
lots/models.py   OpeningBalance (+columnas)
operations/validators.py   saldos con mixto y opening de incubadora; CUT-GL-02 en validate_event_date
reports/service.py         población base con mixto; informe de lote con lifetime por métrica
frontend/src/pages/cutover/  CargasInicialesPage (wizard) + CutoverPreview por BU + i18n
```

Apply por BU (`builders`): `aves` (grandparent/breeder/broiler) y `hatchery`. Cada builder devuelve `Lot`, `LotPhase`, `OpeningBalance`(+`HatcheryOpening`) y la matriz de destino se genera desde el contrato (`10_APPLY_DESTINATION_MATRIX`).

Rutas nuevas: `GET /cutover-batches`, `GET /cutover-batches/{id}`, `GET /cutover-batches/{id}/errors?format=csv|xlsx`, `GET /cutover-batches/{id}/preview`; `GET /cutover-templates/{bu}?format=&batch_id=`. Alcance `MULTI_UNIDAD` (igual que las existentes).

## 4 · Fases

| Fase | Contenido | Commit |
|---|---|---|
| F0 | Reproducción, spec, research, data-model, template-contract, plan, tasks, quickstart; `01_LIVE_FAILURE_ROOT_CAUSE`, `02_CURRENT_GAP_ANALYSIS` | 1 |
| F1 | RED (`backend/tests/test_cutover_v2_red.py` + ajustes), evidencia | 1 |
| F2 | contracts, parser XLSX/CSV, validation, templates, migración, modelos | 2 |
| F3 | service (apply por BU, preview, errores, listado), saldos, CUT-GL-02, reconciliación, informe | 2 |
| F4 | frontend + i18n + tests; E2E UI 4 BU; fixtures golden | 2 |
| F5 | verde dirigido → regresión completa (backend, frontend, tsc, build, E2E P-16 + procesos afectados + navegación) | 2 |
| F6 | S1–S12, restauración explícita, post-mutación | 3 |
| F7 | docs 03–16, `CUTOVER_MASTER_SPEC` addendum, certificación, push, verificación remota y de runtime | 3 |

## 5 · Test plan

| Capa | Archivo | Cubre |
|---|---|---|
| RED | `backend/tests/test_cutover_v2_red.py` | 9 escenarios del mandato §34 |
| Unit | `test_cutover_v2_contracts.py` | registry cerrado, 4 contratos, destino por campo (0 sin destino), parser XLSX/CSV, paridad, UNKNOWN/0/N/A, límites, fórmulas |
| Integración | `test_cutover_v2_validation.py` | maestros, padre-hijo, fase, consistencia, negativas §33 |
| Integración | `test_cutover_v2_apply.py` | apply por BU, destino, REUSE/REJECT, idempotencia, segregación, BU/grant, cross-company |
| Integración | `test_cutover_v2_continuity.py` | CUT-GL-02, saldos con opening (aves/huevos/pollitos), primer evento por BU, reconciliación, informe lifetime |
| Existentes | `test_ga_req_061_cutover_c*` (fixture v2) | sin regresión de contrato |
| Frontend | `r061.cutoverFlow.test.tsx` (ajuste), `cutoverV2.test.tsx` | wizard, BU bloqueada, CSV/XLSX, errores descargables, preview, i18n |
| E2E | `e2e/proceso-p16-cutover-{grandparent,breeder,hatchery,broiler}.spec.ts` | UI completa + primer evento post-corte por BU; CSV en uno |

## 6 · Verificación y Git

Commits: (1) spec + RED + reproducción, (2) implementación + verde, (3) certificación + evidencia. Push `origin/main` (AOD-29). Runtime: el push despliega; verificación con credenciales UAT con `cutover:*` (pendiente del Owner).

## 7 · Criterios de parada

Mutación no detectada · regresión que exija cambiar una regla · credenciales de runtime ausentes ⇒ `LOCALLY_CERTIFIED_RUNTIME_VERIFICATION_PENDING` (no bloquea el resto).
