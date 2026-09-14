# GA-CLAUDE · CERTIFICACIÓN T5 — CONTRATO DE CAPTURA (fases, vacíos, códigos SAP y unidad de peso)

Fecha: 2026-09-14 · Tranche **T5** del programa Pre-SAP (R-191 · R-206 · R-209 · R-210; R-146 condicionada a AOD-16) · Baseline de entrada: T4 CERRADA (`976201d`) · Cierre técnico: `921a3a0` → `0f587b1` (+ evidencia `full_suite_t5`).

## 1 · Alcance ejecutado

| Item | Espec | Estado | Certificación |
|---|---|---|---|
| **R-191** · transición de fase por UI (P1 · P-02/P-04) | `specs/R-191` | `CLOSED_TECHNICALLY` · C3 runtime pendiente | `GA_CLAUDE_R191_RUNTIME_CERTIFICATION.md` (C1 `921a3a0` · C2 `d330ae5` · C2s `1f8dfb6`; S1 1F/S2 1F/S3 3F/S4 1F) |
| **R-206** · vacíos del asistente (`''` ⇒ ausencia) (P2) | `specs/R-206` | `CLOSED_TECHNICALLY` · C3 runtime pendiente | `GA_CLAUDE_R206_RUNTIME_CERTIFICATION.md` (C1 `ce1ea7e` · C2 `da66344` · C2s `4fdd131`; S1 1F/S2 4F) |
| **R-209** · referencias SAP por código canónico (P2 · fase SAP) | `specs/R-209` | `CLOSED_TECHNICALLY` · C3 runtime pendiente | `GA_CLAUDE_R209_RUNTIME_CERTIFICATION.md` (C1 `3fc1b91` · C2 `ae85a4e` · C2s `0073d57`; S1 1F/S2 1F) |
| **R-210** · gramos como unidad única de peso (P2) | `specs/R-210` | `CLOSED_TECHNICALLY` · UAT C-01 confirmatoria + C3 runtime pendientes | `GA_CLAUDE_R210_RUNTIME_CERTIFICATION.md` (C1 `6da1b3c` · C2 `5c1b5af` · C2s `0f587b1`; S1 2F/S2 1F) |
| **R-146** | condicionada a **AOD-16** (captura offline móvil v1) | `SCHEDULED` (cola del propietario, antes de T5 completa) | — |

## 2 · Criterio de salida (ficha T5) — verificación

| Criterio | Estado |
|---|---|
| RED→GREEN→sensibilidad por spec | ✅ R-191 (7F/2P+4F/4 → 9/9+4/4; S1-S4) · R-206 (8F/8+4F/2P → 17/17+35/35; S1-S2) · R-209 (2F/1P → 3/3; S1-S2) · R-210 (3F/2P → 5/5; S1-S2) |
| Controles de frontera | ✅ `phase_id` explícito (BE 05) · 422 del cuerpo antiguo (BE 07) · tolerancia BE sin relajar requeridos · comparativo SAP verbatim · curvas en gramos (bordes inclusivos) |
| Suite completa BE con artefacto | ✅ **1316 passed / 0 failed / 49 skipped** (1167.72s; `evidence/t5/full_suite_t5.log`) — primera pasada 1F por el guard de determinismo (literales ISO en el test R-206), remediada en `0e60038` y suite re-ejecutada limpia |
| Suite FE + tipos + build | ✅ **380/380** (`specs/R-210/evidence/green/fe-suite-380.log`) · `tsc` 0 (por tranche) · build OK |
| Regresión obligatoria de planes | ✅ `gaFe04`/`gaFe06`/`f01d`/`f01.payloadContract`/importaciones (BE) verdes en los GREEN dirigidos y en las suites |
| Evidencia en el hogar del programa | ✅ certificaciones por spec + `specs/R-{191,206,209,210}/evidence/` + esta certificación |
| Runtime (EX-01) | ⏸ ventana de deploy (familia G-06); runners R191-RT-01…05, R206-RT-01/02, R209-RT-01…04, R210-RT-01/03 listos |
| UAT del propietario | ⏸ AOD-16 (R-146, si procede) y AOD-21 (R-210 C-01 confirmatoria) — ninguno bloquea |

## 3 · Riesgo residual y límites declarados

- **C3 runtime** de los cuatro paquetes pendiente de la ventana de deploy/credenciales (misma clase G-06) — incluida la transición irreversible de R-191 (lote de pruebas UAT-09) y la consulta de activas múltiples (C-06).
- **R-146** no ejecutada: condicionada a la decisión **AOD-16** (ya en cola, `SCHEDULED` antes de T5 completa); su ausencia no invalida el resto del contrato de captura.
- R-209 C-03: históricos con id no se reescriben (inventario de lectura en C3); R-210 C-05: sin saneamiento histórico.

## 4 · CI

- Pendiente de observación de los runs de los commits T5 (registro en `evidence/t5-ci-run.json` cuando se observe). Patrón: C1 RED rojos por diseño; cierres verdes.

## 5 · Veredicto

**T5 = `CLOSED_TECHNICALLY`** — el contrato de captura queda íntegro: fases con una sola activa y cierre transaccional (R-191), payload sin `''` (R-206), referencias SAP por código (R-209) y una unidad de peso (R-210). KPI de procesos sin cambio (0/17) hasta la certificación runtime/UAT del tramo. **T6 queda HABILITADA** (DAG: T6 ← T4+T5); **R-146 queda como rider condicionado a AOD-16**.
