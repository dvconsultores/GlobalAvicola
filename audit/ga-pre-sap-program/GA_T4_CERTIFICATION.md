# GA-CLAUDE · CERTIFICACIÓN T4 — EVENTOS Y RECEPCIÓN (FE): UBICACIÓN DEL EVENTO Y CUADRE ALCANZABLE

Fecha: 2026-09-14 · Tranche **T4** del programa Pre-SAP (R-190 · R-205) · Baseline de entrada: T3 CERRADA (`9cb075f`) · Cierre técnico: `a79fe0c` → `dbc782d` (+ evidencia `full_suite_t4`).

## 1 · Alcance ejecutado

| Item | Espec | Estado | Certificación |
|---|---|---|---|
| **R-190** · ubicación del evento en `location_events` sobre lotes sin galpón (P1 · BR-08) | `specs/R-190` | `CLOSED_TECHNICALLY` · **C3 runtime en ventana de deploy/credenciales** | `GA_CLAUDE_R190_RUNTIME_CERTIFICATION.md` (C1 `a79fe0c` · C2 `d1c16a7` · C2s `801d18c`: S1 2F/S2 9F/S3 2F/S4 2F) |
| **R-205** · cuadre BR-20 alcanzable por la navegación real (P1 · P-03) | `specs/R-205` | `CLOSED_TECHNICALLY` · **C3 runtime en ventana de deploy/credenciales** | `GA_CLAUDE_R205_RUNTIME_CERTIFICATION.md` (C1 `fe3bd3d` · C2 `72aa7f4` · C2s `dbc782d`: S1 4F/S2 3F/S3 1F) |

## 2 · Criterio de salida (ficha T4) — verificación

| Criterio | Estado |
|---|---|
| RED→GREEN→sensibilidad por spec | ✅ R-190 (26F/2P→32/32; S1-S4) · R-205 (12F/2P→29/29; S1-S3); mutaciones revertidas |
| Paridad y fronteras demostradas | ✅ F-01e **4/4** intacto; frontera incubadora unit-verde; **BR-08 4/4** y **BR-20 10/10** por API (controles BE) |
| Suite completa BE con artefacto | ✅ **1295 passed / 0 failed / 49 skipped** (1170.30s; `evidence/t4/full_suite_t4.log`) — incluye R-221 C2 y controles R-190 |
| Suite FE completa + tipos + build | ✅ **360/360** (`specs/R-205/evidence/green/fe-suite-360.log`) · `tsc --noEmit` 0 · `npm run build` OK |
| Regresión obligatoria de planes | ✅ `f01e`/`f01`-familia/`r153.importLotOptional`/`gaFe05`/`r190.*`/`r205.*` verdes; BE: `test_reception_reconciliation` (BR-20) y control R-190 verdes en suite |
| Evidencia en el hogar del programa | ✅ certificaciones por spec + `specs/R-190/evidence/` + `specs/R-205/evidence/` + esta certificación |
| Runtime (EX-01) | ⏸ ventana de deploy + credenciales (misma clase G-06); runners listos (E2E-R190-01…08, E2E-R205-01…06, retry R-189 7/7) |
| UAT del propietario | ⏸ opcional (R-190 C-03 alternativa B); sin bloqueo |

## 3 · Riesgo residual y límites declarados

- **C3 runtime de R-190/R-205** pendiente de la ventana de deploy (Watchtower) + credenciales UAT-09 — igual que el resto de la familia G-06. **Efecto**: `p03/p04/p11` (e2e) quedan reparadas en árbol pero su verde en nube se observa en C3.
- **R-190 C-03** (alternativa B: persistir `house_id` en el lote al aprobar) es decisión **opcional** del propietario (cola); la implementación A por defecto está certificada.
- R-205 C-06 (cuadre por `bird_type` también en producción) queda como nota de dominio; sin bloqueo.

## 4 · CI

- Pendiente de observación de los runs de los commits T4 (patrón habitual: C1 RED = rojos por diseño; cierres verdes). Registro en `evidence/t4-ci-run.json` cuando se observe.
- **Actualización (AOD-29, 2026-09-14)**: la observación de runs de GitHub Actions queda **NOT_APPLICABLE_BY_OWNER_DECISION** — el propietario retiró Actions del camino de certificación; la certificación se sostiene en los gates locales (RED/GREEN/regresión/sensibilidad/suites). Registro: `GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md`.

## 5 · Veredicto

**T4 = `CLOSED_TECHNICALLY`** — el primer eslabón visible de la cadena (eventos y recepción FE) queda reparado con contrato propio y fronteras intactas: la ubicación del evento se deriva de una sola fuente (R-190) y el cuadre de reproductoras es alcanzable y obligatorio por cualquier ruta (R-205). KPI de procesos sin cambio (0/17): la certificación funcional se completa en C3 runtime + UAT. **T5 queda HABILITADA** (DAG: T5 ← T4).
