# GA-CLAUDE · CERTIFICACIÓN RUNTIME — R-192 · CIERRE DE LOTE CON REVERSOS EFECTIVOS

Fecha: 2026-09-14 · Spec `specs/R-192` · Proceso: **P-06** (ciclo de vida del lote) · Dependencia de tranche: T7 · Baseline de entrada: T6 CERRADA (`82b250f`).

## 1 · Ciclo ejecutado

| Fase | Commit(s) | Evidencia |
|---|---|---|
| **C1 · RED** | `582f513` (+ `69894ae` evidencia) | BE `6F/13P` (`evidence/red/backend_red.log`): 01 «400 R7 — 2 en reversed», 02 sin «reverso pendiente» (C-07), 03 «mortalidad 15 ≠ 5», 04 «400 R7», 05 «rule R7 ≠ BR-05», 06-reversed «400 ≠ 200»; controles 13/13 verdes · FE `3F/1P` (`evidence/red/vitest_red.log`): sin toast en 400/403/404/422 |
| **C2 · Implementación** | `f65a633` | R7 decide por **estado terminal** (`REVERSED` no bloquea) + `C-07` («1 reverso pendiente de decisión» en el detalle) · resumen neto (`status.not_in([CANCELLED, REVERSED])` en mortalidad/alimento/huevos) · BR-05 solo con pesaje/alimento **vigentes** · UI: `toast.error(getErrorMessage(err, t('lots.closeError')))` |
| **C2-fix** | `0e49add` | Restauración del `finally` de `handleCloseLot` consumido por la edición C2 (los tests no lo cubrían) |
| **C2s · Sensibilidad** | `929b2f6` | S1 (R7 sin `REVERSED`) ⇒ 3F (01/04/06) · S2 (sumas sin filtro) ⇒ 2F (03/04) · S3 (sin toast) ⇒ 3F (11/13/14) — `evidence/red/S{1,2,3}_*.log` |
| **GREEN** | — | BE dirigido **19/19** · regresión (close-approval, lot-closure, internal-reversal, population-invariant) **87/87** · FE dirigido 4/4 · **FE completa 390/390** (`evidence/green/fe-suite-390.log`) · `tsc` 0 |
| **C3 · Runtime** | ⏸ ventana (G-06) | H8b lotes gemelos + UI toast/resumen; capturas escritorio/móvil |

## 2 · Criterios de aceptación

| AC | Resultado | Dónde |
|---|---|---|
| AC01 lote con par revertido cierra 200 | ✅ | `test_r192_01` |
| AC03 contrapartida pendiente ⇒ 400 R7 + no-mutación | ✅ | `test_r192_02` |
| AC04 los 13 estados conservan veredicto; `REVERSED` por par real y por base no bloquea | ✅ | `test_r192_06*` |
| AC05/AC06/AC07 resumen neto (5/100/100) | ✅ | `test_r192_03`, `test_r192_04` |
| AC08 `approved_events` sin el par | ✅ | `test_r192_04` |
| AC09 BR-05 ignora pesaje revertido | ✅ | `test_r192_05` |
| AC11/AC13 UI toast con `detail` (400 R7/403/404) | ✅ | `r192.closeLotError.test.tsx` |
| AC12/AC14 UI resumen 200 / contrato sin forma nueva | ✅ | test control 02 |
| AC15 regresión | ✅ | 87/87 + FE 390/390 + tsc 0 |
| AC16/AC17 C3 runtime (H8b + capturas) y C-07 | ⏸ C3 en ventana · C-07 implementado | — |

## 3 · Decisión del propietario

`C-01` (¿`REVERSED` cuenta como decidido a efectos de R7?) y `C-05` (¿BR-05 ignora revertidos?): **implementado el defecto habilitante («sí»)** y elevado como **confirmatoria AOD-27** (no bloquea; el UAT de P-06 lo ratifica). Si el propietario eligiera «no», el paquete se rediseña (acción explícita para descargar el par).

## 4 · Nota de regresión

`test_lot_closure.py::test_t_073_01` anulaba **el evento de huevos** y aun así esperaba `total_eggs=250`: codificaba el comportamiento previo (contar anulados) que `AC07` corrige. Se actualizó el escenario (el anulado es una inspección —sin efecto en totales; conteos 6/5) preservando su intención: los dos contadores siguen siendo cuentas distintas.

## 5 · Veredicto

**R-192 `CLOSED_TECHNICALLY`** — P-06 reparado de extremo a extremo (backend + UI); impacto de lote verificado sobre datos reales de API y semántica neta alineada con `_suma_neta` (`OD-19`). C3 runtime y confirmatorias AOD-27 pendientes de ventana/propietario.
