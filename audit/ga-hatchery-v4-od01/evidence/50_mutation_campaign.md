# 50 · Campaña de sensibilidad (mutación) — amendment OD-HATCH-V4-01

- **Alcance**: SPEC 018 §7 · `fertile_eggs_to_pit` es **POST-CARGA** (fosa ⊆ set, transferidos + fosa ≤ set,
  en proceso = set − transferidos − fosa, UNKNOWN si falta cualquiera de los tres).
- **Commit de implementación (baseline)**: `bee4832` (HEAD).
- **Método**: cada mutante se aplica de uno en uno sobre la implementación de `bee4832`; se ejecuta
  **solo** el subconjunto de tests indicado; se registra si algún test falla (**DETECTADO**) o no
  (**SUPERVIVIENTE**); y se restaura **siempre** con
  `git restore --source=bee4832 -- <archivo>` verificando `git diff --stat -- <archivo>` vacío
  (no se usó `checkout`, `stash` ni `reset`; sin `git add/commit/push`).
- **Comando (idéntico por mutante)**, desde `backend/`:
  ```
  ./scripts/run_tests.sh tests/test_cutover_hatchery_v4.py tests/test_cutover_hatchery_v4_od01.py \
      tests/test_cutover_v2_validation.py tests/test_cutover_v2_red.py tests/test_cutover_v2_continuity.py \
      -q 2>&1 | grep -E "^(FAILED|ERROR)|passed|failed" | tail -25
  ```
- **Baseline (sin mutar)**: `77 passed, 5 warnings in 25.92s` → verde, prerrequisito cumplido.
- **Salida cruda por mutante**: `50_mutation_raw.log` (misma carpeta).

## Tabla de resultados

| Mutante | Archivo · cambio aplicado | Tests que fallan | Veredicto |
|---|---|---|---|
| **M1** | `cutover/validation.py` `_consistencia_incubadora`: regla (a) vuelve a comparar la fosa con `eggs_received` (`fosa > recibidos`) en lugar de `eggs_set` — la cota `fosa ≤ cargados` queda anulada | `test_h4_fosa_04_fosa_mayor_que_cargados` (1 failed / 76 passed) | **DETECTADO** (H4-FOSA-04 · AC-V4-15) |
| **M2** | `validation.py`: se **elimina** la regla (b) `eggs_transferred + fosa ≤ eggs_set` | `test_h4_fosa_03_transferidos_mas_fosa_excede_los_cargados`, `test_ac_v4_08_fosa_acotada_por_lo_cargado` (2 failed / 75 passed) | **DETECTADO** (H4-FOSA-03 · AC-V4-16) |
| **M3** | `validation.py` `_derivados`: `eggs_in_process = set − transferred` (ignora la fosa) | `test_h4_fosa_01_en_proceso_resta_la_fosa`, `test_h4_fosa_02_transferidos_mas_fosa_igual_a_cargados`, `test_h4_fosa_05_fosa_unknown_no_inventa_en_proceso`, `test_ac_v4_08_pipeline_completo_con_fosa` (4 failed / 73 passed) | **DETECTADO** (H4-FOSA-01/02) |
| **M4** | `validation.py` `_derivados`: calcula `eggs_in_process` con solo `set` y `transferred` KNOWN, tratando la fosa **UNKNOWN como 0** | `test_h4_fosa_05_fosa_unknown_no_inventa_en_proceso` (1 failed / 76 passed) | **DETECTADO** (H4-FOSA-05 · AC-V4-17) |
| **M5** | `cutover/service.py` rama **V4** del detalle: `en_proceso = cargados − transferidos` (ignora la fosa) | `test_h4_fosa_01_en_proceso_resta_la_fosa`, `test_h4_fosa_07_sin_doble_conteo_entre_no_incubables_y_fosa`, `test_h4_fosa_02_…`, `test_h4_fosa_05_…`, `test_ac_v4_08_pipeline_completo_con_fosa` (5 failed / 72 passed) | **DETECTADO** (H4-FOSA-01/07 reconciliación) |
| **M6** | `service.py` rama V4: trata fosa `None` como 0 (calcula con `cargados`/`transferidos` KNOWN) | `test_h4_fosa_05_fosa_unknown_no_inventa_en_proceso` (1 failed / 76 passed) | **DETECTADO** (H4-FOSA-05 reconciliación) |
| **M7** | `service.py` rama **V3** (batch histórico): usa la fórmula V4 con la fosa en vez de `eggs_discarded` | `test_h4_fosa_v3_historica_no_cambia`, `test_ac_v4_11_registro_v3_historico_sigue_legible_sin_reparto` (2 failed / 75 passed) | **DETECTADO** (AC-V4-11 / AC-V4-19) |
| **M8** | `operations/validators.py` `get_hatchery_egg_balance`: al saldo de apertura le resta **también** la fosa (`fertile_eggs_to_pit_status == KNOWN`) | `test_h4_fosa_07_sin_doble_conteo_entre_no_incubables_y_fosa` (1 failed / 76 passed) | **DETECTADO** (H4-FOSA-07 · BR-03 no resta la fosa, D-14) |

## Resumen

- **Mutantes aplicados**: 8 · **DETECTADOS**: 8 · **SUPERVIVIENTES**: 0 → **sensibilidad 8/8 (100 %)**.
- Cada mutante fue detectado por su test objetivo; M2, M3 y M5 disparan además asserts de `AC-V4-08`
  (pipeline completo con fosa), lo que confirma cobertura redundante del mismo invariante.
- Restauración verificada mutante a mutante: `git diff --stat -- <archivo>` vacío en los 8 casos.
- Estado final del árbol: `git diff --stat -- backend/app` **vacío**; `git status --short` muestra solo
  la evidencia de esta campaña más lo preexistente (`audit/.../e2e_od01/*` modificado y las carpetas
  `postdeploy/` sin seguimiento). No se creó ni modificó ningún test.
- Nota de fidelidad de la campaña: no se añadieron tests nuevos; los supervivientes —si los hubiera—
  se habrían reportado tal cual.
