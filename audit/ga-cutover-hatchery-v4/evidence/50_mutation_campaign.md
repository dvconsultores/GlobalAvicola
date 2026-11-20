# Campaña de sensibilidad — SPEC 018 (incubadora v4)

Commit de implementación `0d7b0cc`. Cada mutante se aplicó de uno en uno y se restauró con `git restore --source=0d7b0cc -- <archivo>` (árbol idéntico tras cada uno).
Crudos: `50_mutation_raw.log` (B1–B16, F1) y `50_mutation_raw_frontend_F2_F4.log` (F2–F4).

**20/20 detectados, 0 supervivientes.**

| # | Archivo | Mutación | Detectado por |
|---|---|---|---|
| B1 | validation.py | sin cota `set + Σ(no incubables KNOWN) ≤ received` | AC-V4-07; test_consistencia_sin_tolerancias |
| B2 | validation.py | total derivado como suma parcial (UNKNOWN=0) | AC-V4-06 |
| B3 | validation.py | igualdad forzada `set + total == received` | AC-V4-06/07/10, BR-03 operativo, RED-09, continuity |
| B4 | validation.py | sin `fosa ≤ received` | AC-V4-08; test_consistencia_sin_tolerancias |
| B5 | validation.py | `en_proceso = set − transferred − total` (doble conteo) | AC-V4-08 pipeline con fosa |
| B6 | operations/validators.py | BR-03 no resta no incubables | AC-V4-10; RED-05 |
| B7 | operations/validators.py | BR-03 resta dos veces | AC-V4-10; BR-03 operativo; RED-05 |
| B8 | service.py | `eggs_discarded` = suma de no incubables | AC-V4-09; RED-05 |
| B9 | service.py | oversized↔broken al persistir | AC-V4-09; RED-05 |
| B10 | service.py | fórmula V4 para V3 histórica | AC-V4-11 |
| B11 | service.py | total parcial en el detalle | AC-V4-06/10/11 |
| B12 | service.py | `eggs_in_process` aunque fosa > 0 | AC-V4-08 pipeline |
| B13 | contracts.py | `allow_na=True` en fosa | AC-V4-01/02/05; contracts |
| B14 | contracts.py | reintroduce campo `eggs_discarded` | 51 tests (AC-V4-01..12, validación, RED, contracts) |
| B15 | contracts.py | orden oversized/dirty permutado | AC-V4-01/02; RED-02/08; contracts |
| B16 | migración | `server_default` de estados `KNOWN` (no `UNKNOWN`) | AC-V4-12 |
| F1 | CargasInicialesPage | total null pintado como 0 | vitest UNKNOWN del total (d) |
| F2 | CargasInicialesPage | columna de descartados V3 siempre visible | vitest (a) V4 sin columna histórica |
| F3 | CargasInicialesPage | fosa 0 conocida pintada como vacío | vitest (c) fosa 0 |
| F4 | locales es | etiqueta «derivado» → «calculado» | vitest (a) cabecera «derivado» |

Regresión posterior (árbol == `0d7b0cc`): backend dirigido **299 passed** (`51_backend_postmutation.log`); frontend dirigido **38 passed + 1 skipped** (`52_frontend_postmutation.log`).
