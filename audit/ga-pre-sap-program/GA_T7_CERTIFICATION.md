# GA-CLAUDE · CERTIFICACIÓN T7 — CIERRE Y REVERSOS (R-192 · R-193 · R-211)

Fecha: 2026-09-14 · Tranche **T7** del programa Pre-SAP · Baseline de entrada: T6 CERRADA (`82b250f`) · Cierre: `582f513`…`e30178b` + este cierre.

## 1 · Alcance ejecutado

| Item | Espec | Estado | Certificación |
|---|---|---|---|
| **R-192** · cierre de lote con reversos efectivos (P1 · P-06) | `specs/R-192` | `CLOSED_TECHNICALLY` · C3 runtime en ventana · AOD-27 | `GA_CLAUDE_R192_RUNTIME_CERTIFICATION.md` |
| **R-193** · acumulado BR-18 neto de reversos (P2 · P-01/02/03) | `specs/R-193` | `CLOSED_TECHNICALLY` · C3 runtime en ventana · OBS-01/02 al backlog | `GA_CLAUDE_R193_RUNTIME_CERTIFICATION.md` |
| **R-211** · capacidad del galpón por fila (P2 · P-01/02) | `specs/R-211` | `CLOSED_TECHNICALLY` · C3 runtime en ventana · **AOD-28** (C-02 A/B) | `GA_CLAUDE_R211_RUNTIME_CERTIFICATION.md` |

## 2 · Criterio de salida (ficha T7) — verificación

| Criterio | Estado |
|---|---|
| RED→GREEN→sensibilidad por spec | ✅ R-192 (BE 6F/13P → 19/19; FE 3F/1P → 4/4; S1 3F/S2 2F/S3 3F) · R-193 (5F → 5/5; S1 3F/S2 1F) · R-211 (2F/2P → 4/4; S1 2F) |
| Corazón de integridad: estado `REVERSED`, BR-18 neto, BR-17 | ✅ R7 trata `REVERSED` como decidido; resumen neto; OC recupera capacidad tras reverso; capacidad por galpón por fila |
| Suite completa BE con artefacto | ✅ **1349/0/49** (`evidence/t7/full_suite_t7.log`; 1 207 s) |
| Suite FE + tipos | ✅ **390/390** (`specs/R-192/evidence/green/fe-suite-390.log`) · `tsc` 0 |
| Regresión obligatoria del plan | ✅ R-192: 87/87 (close-approval · lot-closure · internal-reversal · population-invariant) · R-193: 86/86 (purchase-order-receipt · internal-reversal · reception-reconciliation · edit-validation-parity · population-invariant) · R-211: 140/140 (+ masters-tenancy · BU enforcement · R-190 contigua) |
| Evidencia en el hogar del programa | ✅ certificaciones por spec + `specs/R-{192,193,211}/evidence/` + esta certificación |
| Runtime (EX-01) | ⏸ ventana de deploy (familia G-06): H8b + UI toast/resumen (R-192) · `R193-RT-*` API (R-193) · `R211-RT-*` + captura multi-galpón (R-211) |
| UAT del propietario | ⏸ confirmatorias **AOD-27** (R-192 C-01/C-05) y **AOD-28** (R-211 C-02 A/B) — no bloquean (defaults implementados) |
| Backlog actualizado | ✅ OBS-R193-01/02 registradas (fuera de alcance) |

## 3 · Riesgo residual y límites declarados

- **C3 runtime** pendiente de ventana en los tres paquetes; el comportamiento está demostrado a nivel API-integrada (BE) y jsdom (FE) con las cadenas reales (par de reverso vía `POST /reversals` + motor de aprobación; OC con recepciones parciales; reparto multi-galpón).
- **R-192**: la actualización de `test_lot_closure::test_t_073_01` (anulado neutro) es deliberada — el escenario anterior codificaba la semántica previa; el resumen neto queda fijado por los tests de R-192.
- **R-211 C-02=B** (si el propietario decidiera acumular entre eventos) requeriría consulta agregada y prueba de acumulado; documentado en AOD-28.
- **R-193 OBS-R193-01** (distribución con ref de OC suma como recepción) documentada como deuda, sin corrección en este paquete.
- Los procesos **P-01, P-02, P-03, P-06** quedan **reparados técnicamente**; su `FUNCTIONALLY_CERTIFIED_E2E` sigue dependiendo de la pasada runtime/UAT (KPI de procesos sin cambio: 0/17).

## 4 · CI

- Pendiente de observación (registro `evidence/t7-ci-run.json` cuando se observe). Patrón: C1 RED rojos por diseño; cierres verdes.

## 5 · Veredicto

**T7 = `CLOSED_TECHNICALLY`** — el cierre de lote, el acumulado contra la OC y la capacidad por galpón quedan reparados de extremo a extremo (validadores + servicio + UI donde aplica), con paridad exacta entre los estados de `docs/12 §4` y `REVERSED` como estado terminal decidido. **T8 (P1-12-REOPEN · R-198 · R-219 — auditoría y evidencias: la trazabilidad única y fiable antes de certificar procesos) queda HABILITADA** según el DAG (T8 ← T7; gates T13 aparte).
