# GA-CUTOVER-HISTORICAL-TRANSFERS — Evidencia y certificación

**Fecha:** 2026-11-07 · **Rama:** `main` · **Baseline HEAD:** `aa8d4c2` · **IMPL SHA:** `347b478af59db13d1b26d7b724b731cb5fdcd2aa` · **Spec:** `specs/014-cutover-historical-transfers/spec.md` (amendment de SPEC 006/009).
Hallazgo `CUTOVER-BALANCE-TRANSFER-01`. Los datos del usuario NO se modificaron: se amplió el modelo. Sin SAP, sin datos reales, sin cambio en lotes ya aplicados.

## 1. Causa raíz (BEFORE reproducido: `02_before_real_case.json`)
La validación de Progenitoras/Reproductoras era `alojadas − mortalidad − descartes = vivas` (solo con las cuatro piezas KNOWN). Contra HEAD, con los números del caso real:
- lote que **entregó** 300 machos: `1300 − 165 − 0 = 1135 ≠ 835` ⇒ `CONSISTENCY_MISMATCH`;
- lote que **recibió** 300: `1000 − 100 − 20 = 880 ≠ 1180` ⇒ `CONSISTENCY_MISMATCH`.
El modelo no tenía dónde representar las transferencias históricas. En el dominio operativo `bird_transfer` es un evento neutro intra-lote (RR-02) y `live_*` es saldo vivo (RC-08: el histórico no se resta), de modo que el acumulado es informativo + verificación y no puede duplicar saldo.

## 2. Alcance por BU
| BU | Transferencias posibles | Modelo previo | Cambio |
|---|---|---|---|
| Reproductoras | Sí (demostrado) | No | **Sí** |
| Progenitoras | Plausible; mismo contrato y validador | No | **Sí** (contrato compartido; campos opcionales) — *a confirmar con el usuario clave* |
| Engorde | Posible, no demostrado (ya tiene `accumulated_birds_received` y salidas a planta) | Parcial | **No** (delta propio con campos mixtos si se confirma) |
| Incubadora | No (balance de huevos) | n/a | No |

## 3. Modelo y versionado
Campos (v3, enteros ≥ 0, opcionales, sin N/A): `historical_transfers_in_males|females`, `historical_transfers_out_males|females`. Ecuación por sexo con los seis componentes KNOWN: `vivas = alojadas + entradas − mortalidad − descartes − salidas`. Veredicto `CONSISTENT / INCONSISTENT (error) / NOT_FULLY_VERIFIABLE (sin error; sin ceros inventados)` en `derived.balance_check` y `summary.balance_not_fully_verifiable_rows`. Plantilla `breeder`/`grandparent` **v2 → v3** (`CUTOVER_*_V3`); la v2 se rechaza («descargue la v3»); CSV sin Meta usa la versión del contrato. BD: migración aditiva `g2b3c4d5e6f7` (6 columnas en `opening_balances`; aperturas previas `UNKNOWN`, nunca «0 conocido»). Apply: `accumulated_transfers_*` + `transfers_in/out_status`; reconciliación expone `historical_transfers_in|out` y sus estados; `current_live` no re-suma el histórico. Alternativas rechazadas: campo neto «transferidos», sumar a `birds_placed`, inflar mortalidad/descartes, eventos históricos ficticios.

## 4. Pruebas
| Prueba | Resultado | Evidencia |
|---|---|---|
| RED contrato/parser/validación (14) y apply/reconciliación/migración (5) | RED → **19/19 GREEN** | `01_`, `03_`, `04_green_targeted.log` |
| Lote origen realista (835) y receptor (1 180) | FAIL BEFORE → PASS AFTER | `02_before_real_case.json`, `61_matriz_before_after.md` |
| Suite SPEC 006 migrada a v3 (7 tests ajustados por contrato, sin debilitar) | verde | `05_spec006_breakage_and_fix.md` |
| E2E `p16b` (UI completa: plantilla v3, 3 lotes ORI/REC/UNK, preview, aprobar, aplicar, opening, evento post-corte, refresh, relogin, persistencia, v2 rechazada) | **passed** | `20_`, `21_e2e_journal.json` |
| Frontend completo | 105 archivos · **634 passed**; `tsc` rc 0; `build` rc 0 | `31_`–`33_` |
| Backend completo (pre-mutación) | **1 845 passed · 0 failed · 49 skipped** | `30_backend_full_pre_mutation.log` |
| E2E regresión: cutover 4 BU + p16b | **5/5** | `40_` |
| E2E regresión: RBAC P-17 A–G + p17e | **10/10** | `41_` |
| E2E navegación | **8/8** | `42_` |
| Sensibilidad | **9/9 DETECTADAS** (M9 sobrevivió → brecha real, cerrada con un test y re-mutada) | `60_sensibilidad.md` |
| Post-mutación (`backend/app` = IMPL SHA, 0 diff) | backend **1 846 passed · 0 failed · 49 skipped**; frontend 634 passed; `tsc` rc 0 | `50_`, `51_` |

Casos del mandato: BR-T01…T10 y los dos lotes realistas cubiertos; lote receptor (`live > placed − mortalidad − descartes` explicado por entradas) y lote origen; UNKNOWN y 0 distinguidos (BR-T08, apply, E2E); no double-counting probado con evento posterior al corte (9 835 − 15 = 9 820; receptor 9 730); RBAC/tenant sin cambios (suites de cutover y de aislamiento de empresa en la regresión completa).

## 5. Observaciones no bloqueantes (sin P0/P1 abiertos)
1. **Inclusión de Progenitoras** por contrato compartido: pendiente de confirmar con el usuario clave (campos opcionales, reversible). Engorde diferido con criterio documentado.
2. **Pérdida de verificación si se dejan vacíos los cuatro campos nuevos:** un archivo v3 con transferencias vacías pasa como `NOT_FULLY_VERIFIABLE` (mandato: no inventar ceros). Mitigado con instrucciones («0 solo si se sabe que no hubo»), manual y `summary.balance_not_fully_verifiable_rows`/`derived.balance_check` en el preview. **La interfaz no muestra aún ese conteo** (solo la API); candidato a un delta de UX.
3. Los acumulados nuevos no son corregibles por la corrección formal de opening (tampoco lo son `placed_*`): decisión separada si se requiere.
4. Una transferencia **posterior** al corte entre lotes no tiene hoy un evento operativo propio (`BIRD_TRANSFER` es intra-lote): se registra con salida/recepción existentes; fuera de alcance.
5. Fixtures QA regenerados (los 4 XLSX; broiler/hatchery solo cambian por metadatos/fechas relativas y textos de instrucciones ya vigentes).
6. **Runtime UAT sin verificar** (despliegue por Watchtower, AOD-29): los usuarios deben descargar la plantilla **v3** y las aperturas anteriores quedan `UNKNOWN` en estos campos.

## 6. Estado
```
MIGRATION=g2b3c4d5e6f7 (aditiva) · REAL_SAP_WRITES=0 · SECRETS_IN_EVIDENCE=0 · DATA_CHANGES_TO_EXISTING_LOTS=0
BEFORE: origen/receptor = CONSISTENCY_MISMATCH · AFTER: ambos PASS · UNKNOWN != 0 preservado · sin doble conteo
backend 1845→1846/0/49 · frontend 634 · E2E 5+10+8 + p16b · sensibilidad 9/9 · P0/P1 abiertos=0
FINAL_STATUS=CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS
```
