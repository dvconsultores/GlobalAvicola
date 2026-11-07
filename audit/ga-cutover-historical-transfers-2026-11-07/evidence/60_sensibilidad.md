# 60 — Sensibilidad / mutación (SPEC 014 · CUTOVER-HISTORICAL-TRANSFERS)

**IMPL SHA (restauración):** `347b478af59db13d1b26d7b724b731cb5fdcd2aa` · restauración tras cada mutación con `git restore --source=347b478 -- <archivo>` + `git diff --stat 347b478 -- <archivo>` vacío. Las ediciones las aplicó el ejecutor (DeepSeek, MCP) tras el commit de implementación; Claude revisó el informe y la restauración final (`git diff --stat 347b478 -- backend/app` vacío).
Suite objetivo: `test_cutover_historical_transfers_red` + `…_apply_red` + `test_cutover_v2_validation` + `test_cutover_v2_contracts` + `test_cutover_v2_continuity` (baseline **77 passed**).

| Mut. | Archivo · cambio | Resumen | Tests que la detectan | Veredicto |
|---|---|---|---|---|
| M1 | `validation.py` · se quita `+ entradas` de la ecuación | 5 failed · 72 passed | BR-T03, BR-T05, BR-T06, apply origen/receptor, reconciliación | **DETECTADA** |
| M2 | `validation.py` · se quita `− salidas` | 7 failed · 70 passed | BR-T02, T04, T06, T10, apply, reconciliación, sin doble conteo | **DETECTADA** |
| M3 | `validation.py` · UNKNOWN tratado como 0 | 2 failed · 75 passed | BR-T08, `test_ht_unknown_no_es_cero` | **DETECTADA** |
| M4 | `service.py` apply · `_opcional` → `_entero` (UNKNOWN→0) | 1 failed · 76 passed | `test_ht_unknown_no_es_cero` | **DETECTADA** |
| M5 | `service.py` reconciliación · `current_live` resta lo transferido (doble conteo) | 1 failed · 76 passed | `test_ht_sin_doble_conteo` | **DETECTADA** |
| M6 | `contracts.py` · `AVES_TEMPLATE_VERSION` v3→v2 (sin bump) | 39 failed · 38 passed | BR-T01…T06, contratos, validación, continuidad | **DETECTADA** |
| M7 | `parser.py` · CSV por defecto vuelve a `v2` | 1 failed · 76 passed | BR-T14 | **DETECTADA** |
| M8 | `parser.py` · se elimina el mensaje específico de negativo | 1 failed · 76 passed | BR-T09 | **DETECTADA** |
| M9 | `service.py` `_opening_engorde` · se quitan los `NOT_APPLICABLE` de transferencias | 77 passed (0 failed) | — | **SOBREVIVIÓ → brecha real** |
| M9′ | ídem, tras añadir `test_ht_engorde_no_aplica_transferencias` | 1 failed · 5 passed | `test_ht_engorde_no_aplica_transferencias` | **DETECTADA** (brecha cerrada) |

M9 no era un mutante equivalente: sin esos estados, Engorde/Incubadora mostrarían `UNKNOWN` en las métricas de transferencias (y hincharían el contador de métricas desconocidas). Se cerró con un test nuevo (Engorde ⇒ `NOT_APPLICABLE`, importes `None`) y se repitió la mutación.

**Resultado:** 9/9 mutaciones DETECTADAS (una tras cerrar brecha de cobertura), 0 sobrevivientes; `git diff --stat 347b478 -- backend/app` vacío; suite objetivo de nuevo verde.

```
SENSIBILIDAD=9/9_DETECTADAS (1 brecha cerrada) · DIFF_APP_VS_IMPL_SHA=0
```
