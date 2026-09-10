# `R-175` · Matriz de control de dependencia de orden (`R175_TEST_ORDER_DEPENDENCY_CONTROL`)

**WAVE B · tranche 10** · 2026-09-10 · hallazgo `R-175` (P3, higiene de pruebas; registrado en el cierre del tranche 9) · **solo control**: no se corrige
(prompt §49-§51) · propósito: distinguir regresión de producto de deuda del arnés; que ningún residuo conocido siga llamándose «ajeno» sin prueba
controlada (regla permanente D).

## 1. Qué se leyó

- `tests/test_clean_baseline.py:223-230` (`test_t_025_07_baseline_idempotente`): siembra dos veces y afirma `count(productive_phases) == 4` **en toda
  la base** (no filtra por prefijo).
- `tests/test_lot_start_date.py:235-251`: la prueba `test_…fecha_real…` crea `ProductivePhase(code="LSD-CRIA"…)` si no encuentra ninguna; el teardown
  (`:63`) borra `LotPhase`, **no** `ProductivePhase`.
- `tests/test_lots_bu_enforcement.py:132-136`: la fixture crea `ProductivePhase(code="BUL…")` si `select(ProductivePhase).limit(1)` devuelve `None`; el
  teardown (`:182-200`) no la borra.
- `tests/test_od14_productive_surfaces.py:135-140`: ídem, `code="OD14…"`; teardown (`:222-233`) sin `productive_phases`.
- `tests/test_opening_balance.py:70-93`: crea su fase y **sí** la borra (`delete(ProductivePhase).where(code LIKE prefijo)`): control positivo.
- `scripts/run_tests.sh`: cada invocación resetea la base (`scripts.test_db reset`, salvo `GA_TEST_KEEP_DATA=1`) → el residuo vive **dentro** de una
  invocación; la regresión completa es alfabética y `test_clean_baseline` corre antes que las tres suites → no se manifiesta en la regresión certificada.

Mecanismo: en una base sin fases (recién reseteada), la suite que corre **antes** que `test_clean_baseline` crea una fase y no la retira; la siembra del
baseline añade sus 4 → `5 ≠ 4`. Si `test_clean_baseline` corre **antes**, las suites encuentran una fase existente y no crean nada → sin residuo.

## 2. Matriz de control (ejecuciones de hoy, base reseteada en cada invocación)

| Suite | Prueba que deja el residuo | Recurso filtrado | Setup | Teardown | Aislada | A→B (suite → `test_clean_baseline`) | B→A (`test_clean_baseline` → suite) | ¿Afecta al tranche 10? | ¿Enmascara un defecto de producto? | ¿Corregir ahora? | Motivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `test_lot_start_date` | `test_…fecha_real_de_inicio…` (`:235-251`) | `productive_phases` (`LSD-CRIA`, `is_initial=True`) | crea la fase si no hay ninguna | borra `LotPhase`, no la fase | **6/6** | **1 failed, 23 passed** — `test_t_025_07`: «las fases se duplicaron: 5» | **24/24** | no (orden alfabético; las suites nuevas del tranche no crean fases) | no (residuo creado por la prueba; ningún camino de producto) | **no** | control, no objetivo; sin efecto en la certificación |
| `test_lots_bu_enforcement` | fixture `esc` (`:132-136`) | `productive_phases` (`BUL…`) | crea si `limit(1)` es `None` | 20 sentencias, sin `productive_phases` | **28/28** | **1 failed, 45 passed** — ídem «5» | **46/46** | no | no | **no** | ídem |
| `test_od14_productive_surfaces` | fixture `esc` (`:135-140`) | `productive_phases` (`OD14…`) | ídem | sin `productive_phases` | **35/35** | **1 failed, 52 passed** — ídem «5» | **53/53** | no | no | **no** | ídem |
| `test_clean_baseline` (víctima) | `test_t_025_07` (`:229-230`) | cuenta global de `productive_phases` | siembra ×2 | — | **18/18** | — | — | no | no | **no** | la afirmación global es la que hace visible el residuo; corregirla sería tocar un guardián sin spec |
| `test_opening_balance` (control) | — | crea y **borra** su fase | — | `delete(ProductivePhase)` por prefijo | (tranche 9: limpia) | — | — | — | — | — | patrón correcto de referencia |

Logs: `r175_iso_<suite>.txt`, `r175_ba_<suite>.txt`, `r175_ab_<suite>.txt`, `r175_iso_baseline.txt` (scratchpad de la sesión; resúmenes copiados en
la evidencia del tranche).

## 3. Clasificación

```
R-175 ............ NON-BLOCKING para el tranche 10 (prompt §51): no produce rojo falso ni verde falso en la regresión certificada (alfabética),
                   no impide aislar R-173/R-172/R-174/R-171 (sus suites nuevas no tocan productive_phases), no hay no-determinismo en la suite completa
residuo .......... IDENTIFICADO y REPRODUCIDO bajo control (3/3 pares A→B rojos por la misma afirmación; 3/3 B→A verdes; 4/4 aisladas verdes)
producto ......... ninguna regresión enmascarada: el residuo es una fila creada por las pruebas
estado ........... OPEN (P3) · sin limpieza oportunista · la corrección (teardown por prefijo, patrón de test_opening_balance) queda para un tranche de
                   higiene bajo la gobernanza de validez de pruebas
regla ............ mientras R-175 siga abierto, toda suite del tranche que toque productive_phases, lots o baseline corre AISLADA + A→B + B→A
```

## 4. Tranche 11 · control ampliado (`§48` del prompt)

Suites nuevas del tranche (`T11`): `tests/test_edit_validation_parity.py` (`PARI-`) y `tests/test_lineage_cancel_move.py` (`LINA-`). Ninguna toca
`productive_phases`. Matriz a ejecutar antes de la regresión completa (base reseteada en cada invocación):

| Par | Objetivo | Resultado |
|---|---|---|
| las tres suites aisladas · A→B · B→A | reconfirmar el residuo conocido | _pendiente de ejecución (se rellena en el cierre)_ |
| `T11 → A` (T11 antes de cada suite con residuo) | T11 no siembra nada que las altere | _pendiente_ |
| `A → T11` | el residuo de A no altera T11 | _pendiente_ |
| `T11 → B` (`test_clean_baseline`) | T11 no deja fases ni datos que el baseline cuente | _pendiente_ |
| `B → T11` | el baseline no altera T11 | _pendiente_ |

Criterio (`§49`): si algún par produce un rojo o verde falso atribuible al arnés, `R-175` pasa a BLOQUEANTE y se formaliza la remediación mínima bajo
gobernanza de validez de pruebas; si no, sigue OPEN · NON-BLOCKING.
