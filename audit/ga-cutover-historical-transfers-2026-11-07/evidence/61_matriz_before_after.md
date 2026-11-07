# 61 — Matriz BEFORE / AFTER (SPEC 014)

| Caso | Modelo anterior (v2) | Modelo nuevo (v3) | Evidencia | Resultado |
|---|---|---|---|---|
| Sin transferencias (los 4 campos en 0) | cuadra | cuadra | `test_br_t01` | PASS |
| Salida histórica (origen: 1300 + 0 − 165 − 0 − 300 = 835) | `CONSISTENCY_MISMATCH` (1135 ≠ 835) — `02_before_real_case.json` | cuadra; apply 835/9000 | `test_br_t02`, `test_ht_apply_origen_y_receptor`, E2E p16b | PASS |
| Entrada histórica (receptor: 1000 + 300 − 100 − 20 − 0 = 1180) | `CONSISTENCY_MISMATCH` (880 ≠ 1180) — `02_before_real_case.json` | cuadra; apply 1180/8550 | `test_br_t03`, apply, E2E p16b | PASS |
| Hembras (salida y entrada), entradas y salidas a la vez | falla | cuadra | `test_br_t04/t05/t06` | PASS |
| Saldo realmente incorrecto (todo conocido) | error | error con la ecuación nueva | `test_br_t07`; sensibilidad M1/M2 | PASS |
| UNKNOWN (campo vacío) | no evalúa | `NOT_FULLY_VERIFIABLE`, sin error ni cero inventado; opening NULL + `UNKNOWN` | `test_br_t08`, `test_ht_unknown_no_es_cero`, E2E (lote UNK); M3/M4 | PASS |
| Negativo / decimal / N/A | n/a | error de campo con mensaje claro | `test_br_t09`, `test_br_t10` | PASS |
| Plantilla v2 de Progenitoras/Reproductoras | aceptada | `TEMPLATE_VERSION_UNSUPPORTED` («descargue la v3») | `test_br_t12`, E2E (422) | PASS |
| Evento posterior al corte | — | `current_live = live + entradas − salidas` (sin re-sumar el histórico: 9 835 − 15 = 9 820) | `test_ht_sin_doble_conteo`, E2E p16b; M5 | PASS |
