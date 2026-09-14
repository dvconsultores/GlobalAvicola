# GA-CLAUDE · CERTIFICACIÓN T6 — CADENA DE INCUBADORA (R-194)

Fecha: 2026-09-14 · Tranche **T6** del programa Pre-SAP (R-194) · Baseline de entrada: T5 CERRADA (`a94ae25` + gobernanza `ea053b4`) · Cierre técnico: `c413fdb` → `cd33d23` (+ evidencia `full_suite_t6`).

## 1 · Alcance ejecutado

| Item | Espec | Estado | Certificación |
|---|---|---|---|
| **R-194** · cadena de incubadora por UI (P1 · P-04/P-05/X-BU) — 5 causas acopladas + hallazgo colateral de servidor | `specs/R-194` | `CLOSED_TECHNICALLY` · C3 runtime en ventana · UAT agrupable | `GA_CLAUDE_R194_RUNTIME_CERTIFICATION.md` (C1 `c413fdb` · C2 `0bfba2e` · C2s `cd33d23`; S1-S4 1F c/u) |

## 2 · Criterio de salida (ficha T6) — verificación

| Criterio | Estado |
|---|---|
| RED→GREEN→sensibilidad | ✅ FE 4F/1P → 6/6; BE 1F/4P → **5/5** (cadena real por API) |
| La prueba demuestra la **cadena real** (no pantallas aisladas) | ✅ `test_r194_01`: recepción 1000 fértiles → **saldo persiste** → carga 500 → BR-03 (>saldo) → nacimiento 300 → despacho 100 → BR-04 (>viables) → **recepción en destino** → `ChickBatch` persistente → `traceability.chick_batches_sent ≥ 1` (X-BU) |
| Tenant/BU | ✅ unidad `hatchery`+`broiler` con concesión; BR-08 con ubicación real; tenencia de `hatchery_id` verificada en servidor |
| Suite completa BE con artefacto | ✅ **1321 passed, 0 failed, 49 skipped** (`evidence/t6/full_suite_t6.log`) |
| Suite FE + tipos | ✅ **386/386** (`specs/R-194/evidence/green/fe-suite-386.log`) · `tsc` 0 |
| Regresión obligatoria del plan | ✅ `f01.*`/`f01d`/`f01e`/`eggDispatchFormContract`/`r190.*`/`r205.*` verdes; BE `test_egg_incubation_concurrency` verde |
| Evidencia en el hogar del programa | ✅ certificación del spec + `specs/R-194/evidence/` + esta certificación |
| Runtime (EX-01) | ⏸ ventana de deploy (familia G-06): E2E-R194-01…07 + `e2e/proceso-p05-incubacion.spec.ts` sobre fixtures corregidos |
| UAT del propietario | ⏸ agrupable (R-190/R-205); defaults C-01/C-02 encolados (no bloquean) |

## 3 · Riesgo residual y límites declarados

- **C3 runtime** pendiente de ventana; la cadena ya está demostrada a nivel API-integrada (BE 5/5 con X-BU). P-04/P-05: **REPARADO técnicamente** — su `FUNCTIONALLY_CERTIFIED_E2E` es el objetivo de la pasada runtime.
- **Hallazgo colateral B-03b** (500 en `egg_storage.lot_id`): remediado en `0bfba2e` con control propio en la cadena; sin migración.
- **C-01/C-02 de R-194** (A/B y capturar/derivar): defaults A implementados y encolados como confirmación; si el propietario eligiera B, se especifica como anexo.
- Trampa evitada y documentada: `valueAsNumber` + `min` nativo HTML impide que zod vea el valor — la validación de dosis es por schema con error visible.

## 4 · CI

- Pendiente de observación (registro `evidence/t6-ci-run.json` cuando se observe). Patrón: C1 RED rojos por diseño; cierres verdes.
- **Actualización (AOD-29, 2026-09-14)**: la observación de runs de GitHub Actions queda **NOT_APPLICABLE_BY_OWNER_DECISION** — el propietario retiró Actions del camino de certificación; la certificación se sostiene en los gates locales (RED/GREEN/regresión/sensibilidad/suites). Registro: `GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md`.

## 5 · Veredicto

**T6 = `CLOSED_TECHNICALLY`** — la cadena de incubadora queda reparada de extremo a extremo (UI + API) con handoff X-BU persistente. KPI de procesos sin cambio (0/17) hasta la pasada runtime/UAT. **T7 (R-192 · R-193 · R-211 — cierre y reversos, validadores) queda HABILITADA** (DAG: T7 ← T3+T6, satisfechos).
