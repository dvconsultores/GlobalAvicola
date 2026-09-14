# GA-CLAUDE · CERTIFICACIÓN T3 — ALCANCE DE DATOS (PREDICADOS DE UNIDAD EN TODO LO AGREGADO Y REFERENCIADO)

Fecha: 2026-09-14 · Tranche **T3** del programa Pre-SAP (R-201 · R-203 · R-204 · R-216 · rider R-221) · Baseline de entrada: T2 CERRADA (`f5eb36e`) · Cierre técnico: `897edb9` → `b056ef1`.

## 1 · Alcance ejecutado

| Item | Espec | Estado | Certificación |
|---|---|---|---|
| **R-201** · SAP sin contexto de empresa (P1 escritura cross-tenant) | `specs/R-201` | `CLOSED_TECHNICALLY` · **C3 runtime pendiente G-06** | `GA_CLAUDE_R201_RUNTIME_CERTIFICATION.md` (C1 `8a442ec` · C2 `4050eef` · S1 3F/S2 1F) |
| **R-203** · referencias de lote cruzando tenencia (galpón/línea/curva) | `specs/R-203` | `CLOSED_TECHNICALLY` · **C3 runtime pendiente G-06** | `GA_CLAUDE_R203_RUNTIME_CERTIFICATION.md` (C1 `fc8f193` · C2 `a4b1bfd` · S1 2F/S2 2F) |
| **R-204** · agregados sin predicado de unidad (+ alertas del panel) | `specs/R-204` | `CLOSED_TECHNICALLY` · **C3 runtime pendiente G-06** | `GA_CLAUDE_R204_RUNTIME_CERTIFICATION.md` (C1 `ca1fa39` · C2 `c1a21bd` · S1 3F/S2 1F) |
| **R-216** · `lots_by_type` con claves de enum (panel en 0) | `specs/R-216` | `CLOSED_TECHNICALLY` · **C3 visual piggyback G-06** | `GA_CLAUDE_R216_RUNTIME_CERTIFICATION.md` (C1 `074ee0a` · C2 `1ba1b11` · S1 2F/S2 2F) |
| **R-221** · eventos sin lote sin unidad derivada (rider) | `specs/R-221` | **PARCIAL — AC-01/02/03/05 cerradas técnicamente; AC-04 bloqueado por AOD-13 (decisión del propietario)** | C1 `8126f97` (RED 3F/2P) · C2 `b056ef1` (GREEN dirigido 134/134; S1 1F/S2 2F) · `evidence/r221/` |

## 2 · Criterio de salida (ficha T3) — verificación

| Criterio | Estado |
|---|---|
| RED→GREEN por spec con sensibilidad | ✅ R-201 (`8a442ec`→`4050eef`), R-203 (`fc8f193`→`a4b1bfd`), R-204 (`ca1fa39`→`c1a21bd`), R-216 (`074ee0a`→`1ba1b11`); mutaciones S1/S2 documentadas por spec |
| Suite completa con artefacto | ✅ **BE 1286 passed / 0 failed / 49 skipped** (1171.11s, tip `1ba1b11`; `evidence/t3/full_suite_t3.log`) · FE sin cambios de producto en T3 (no aplica suite nueva) |
| Doctrina `OD-16` uniforme | ✅ lectura agregada = mismo conjunto autorizado antes de sumar (R-204); escritura SAP fail-closed sin contexto (R-201); referencias verificadas por tenencia (R-203); contrato de panel exacto (R-216) |
| Regresión OD-14/OD-16 obligatoria | ✅ incluidas en la suite completa (`test_od14_*`, `test_r165*`, `test_r160`-familia, `rbac`, guardas BU) |
| Evidencia en el hogar del programa | ✅ certificaciones por spec + `evidence/{r201,r203,r204,r216}/` + esta certificación |
| Runtime (EX-01) | ⏸ bloqueado por **G-06** (credenciales runtime con perfiles de concesión distintos — sondas R199/201/202/203/204/216 listas; misma sesión) |
| UAT del propietario | ⏸ AOD-13 (micro-decisión C-02 de R-221, opciones A/B/C en cola) — no bloquea R-201/203/204/216 |

## 3 · Riesgo residual y límites declarados

- **G-06**: C3 runtime de las cuatro specs (sondeos de concesión/apagado en producción — `https://avicola.globaldv.net`). Certificaciones `CLOSED_TECHNICALLY` con ruta de sondeo lista; ninguna fabrica el resultado.
- **R-221**: parcial — `hatchery_inspection` (tipo inequívoco) cerrado técnicamente (C1 `8126f97` · C2 `b056ef1`: guarda estricta + atribución al nacer; suite completa del tramo R-221 en el próximo lote T4); `farm_inspection` (AC-04) espera **AOD-13**. Si la decisión es (A)/(B), T-05 y su RED se añaden en la ventana de T4.
- R-221 cierra T3 como tranche **con un item rider activo**: la tranche T4 (R-190 + R-205) no depende de AOD-13.

## 4 · CI

- Pendiente de observación de los runs de los commits T3 (patrón habitual: commits C1 RED = rojos por diseño; cierres verdes). Registro en `evidence/t3-ci-run.json` cuando se observe.
- **Actualización (AOD-29, 2026-09-14)**: la observación de runs de GitHub Actions queda **NOT_APPLICABLE_BY_OWNER_DECISION** — el propietario retiró Actions del camino de certificación; la certificación se sostiene en los gates locales (RED/GREEN/regresión/sensibilidad/suites). Registro: `GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md`.

## 5 · Veredicto

**T3 = `CLOSED_TECHNICALLY / OWNER_GATE_PENDING_AOD13`** — alcance de datos cerrado en lectura agregada (R-204), contrato de panel (R-216), escritura cross-tenant (R-201) y referencias de tenencia (R-203). **R-221 = `PARTIAL`** (AC-01/02/03/05 cerradas técnicamente; **AC-04 ↔ AOD-13**, T-05 sin ejecutar) — todo lo técnicamente ejecutable de T3 terminó, pero el cierre funcional total queda condicionado a esa micro-decisión del propietario. `CLOSED_TECHNICALLY` ≠ proceso `FUNCTIONALLY_CERTIFIED_E2E`: KPI de procesos sin cambio (0/17). **T4 (R-190 + R-205) queda HABILITADA.**
