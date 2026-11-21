# SPEC 018 §8 · O-15 — Campaña de sensibilidad (mutación)

Base: commit de implementación `19b547b` (HEAD al iniciar). Cada mutante se aplicó de uno en uno
sobre el árbol de trabajo, se ejecutó **solo** el set de tests designado y se restauró siempre con
`git restore --source=19b547b -- <archivo>`, comprobando `git diff --stat -- <archivo>` vacío antes
de aplicar el siguiente. Sin `git add/commit/push/stash/reset/checkout`. No se escribió ningún test nuevo.

## Baseline (verde, previo a la campaña)

| Suite | Comando | Resultado |
|---|---|---|
| Backend | `./scripts/run_tests.sh tests/test_cutover_hatchery_v4_o15.py tests/test_cutover_hatchery_v4_od01.py tests/test_cutover_hatchery_v4.py -q` | **59 passed** (14.32s) |
| Frontend | `npx vitest run src/__tests__/cutoverHatcheryV4.test.tsx src/__tests__/cutoverV2.test.tsx` | **23 passed / 2 files** (3.44s) |

## Resultado por mutante

| Mutante | Cambio | Tests que fallan | Veredicto |
|---|---|---|---|
| **B1** | `service.py` · `_agregar_con_unknown`: los `None` suman como 0 (suma parcial; total nunca `None`, `filas_unknown` sigue contando) | `test_o15_02_una_unknown_propaga_unknown` (`(900,1) != (None,1)`), `test_o15_03_unica_fila_unknown` (`(0,1) != (None,1)`), `test_o15_06_summary_de_incubadora_con_dos_filas` (`900 is None`), `test_o15_07_summary_chicks_available` (`0 is None`) → 4 failed / 55 passed | **DETECTADO** |
| **B2** | `service.py` · `_agregar_con_unknown`: lista vacía → `(None, 0)` en vez de `(0, 0)` | `test_o15_05_sin_filas` (`(None,0) != (0,0)`) → 1 failed / 58 passed | **DETECTADO** |
| **B3** | `service.py` · `preview` rama hatchery: `en_proceso_filas.append(derivados.get("eggs_in_process") or 0)` (None→0) | `test_o15_06_summary_de_incubadora_con_dos_filas` (`900 is None`) → 1 failed / 58 passed | **DETECTADO** |
| **B4** | `service.py` · `pollitos_filas.append(_entero(estado, "chicks_available"))` (None→0) | `test_o15_07_summary_chicks_available` (`0 is None`) → 1 failed / 58 passed | **DETECTADO** |
| **B5** | `service.py` · N/A de `chicks_available` propaga UNKNOWN (se quita la rama `0 if ... == NOT_APPLICABLE`) | ninguno → **59 passed** | **SUPERVIVIENTE** |
| **B6** | `service.py` · `eggs_in_process_status` siempre `KNOWN` | `test_o15_06_summary_de_incubadora_con_dos_filas` (`'KNOWN' != 'UNKNOWN'`) → 1 failed / 58 passed | **DETECTADO** |
| **F1** | `CargasInicialesPage.tsx` · chip `eggs_in_process` como `<b>{Number(resumen?.eggs_in_process ?? 0).toLocaleString()}</b>` | `chip de huevos en proceso UNKNOWN no pinta una suma parcial` (`'Huevos en proceso: 0'` sin `UNKNOWN`) → 1 failed / 22 passed | **DETECTADO** |
| **F2** | `CargasInicialesPage.tsx` · `enProcesoDerivado` → `{ value: bruto ?? 0, status: 'KNOWN' }` | `preview por fila: A = 900 y B = UNKNOWN en «Huevos en proceso (derivado)»` (`'0'` sin `UNKNOWN`) → 1 failed / 22 passed | **DETECTADO** |
| **F3** | `CargasInicialesPage.tsx` · chip `chicks_available` como `<b>{Number(resumen?.chicks_available ?? 0).toLocaleString()}</b>` | `chip de pollitos disponibles: UNKNOWN con null y numérico con KNOWN` → 1 failed / 22 passed | **DETECTADO** |

**Totales: 8 DETECTADOS / 1 SUPERVIVIENTE (B5).**

## Nota sobre B5 (superviviente)

El contrato D-18 declara «NOT_APPLICABLE no propaga: aporta 0» para `chicks_available`, pero en todo
el set designado (`test_cutover_hatchery_v4_o15.py`, `test_cutover_hatchery_v4_od01.py`,
`test_cutover_hatchery_v4.py`) **ningún test de summary de incubadora usa `chicks_available="N/A"`**
(solo `chicks_available=None`, que es UNKNOWN y por tanto el mutante no altera). Verificación
adicional **fuera del set designado**, solo informativa: con el mutante B5 aplicado,
`backend/tests/test_cutover_v2_apply.py` (que sí usa `chicks_available="N/A"`) sigue **9 passed** —
refuerza que la línea `0 if ... == NOT_APPLICABLE` no está cubierta por ningún test existente. No se
escribió test nuevo (regla de la delegación): hueco de cobertura a reportar como riesgo.

## Integridad final

- `git diff --stat -- <archivo>` vacío tras **cada** restauración (9/9).
- `git diff --quiet 19b547b -- backend frontend e2e` ⇒ **vacío** (exit 0) al terminar.

## Crudo

`50_mutation_raw.log` contiene la salida completa por mutante (comando, fallos y traza), en el mismo
orden B1→B6, F1→F3, más la sección EXTRA del chequeo informativo de B5.
