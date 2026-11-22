# SPEC 019 · Progenitoras V3 preventiva — Campana de MUTACION (sensibilidad de la suite)

- **Commit de implementacion (base):** `e161d16` (HEAD, rama `develop`)
- **Fecha:** 2026-11-22 · **Ejecucion:** secuencial, un mutante a la vez
- **Restauracion:** `git restore --source=e161d16 -- <archivo>` (nunca checkout/stash/reset/checkout de rama).
  En los **10/10** casos la comprobacion `git diff --stat -- <archivo>` quedo **vacia**.
- **Sin** `git add/commit/push`. **Sin** tests nuevos: los supervivientes se reportan tal cual.
- **Redaccion:** todos los logs de evidencia redactados (todo token JWT → `<JWT_REDACTED>`); la comprobacion de prefijo de token en ambos archivos da **0**.
- **Crudo por mutante:** [`50_mutation_raw.log`](./50_mutation_raw.log)

## Baseline (obligatorio, antes de mutar)

| Suite | Comando | Resultado |
|---|---|---|
| BACKEND | `./scripts/run_tests.sh tests/test_cutover_grandparent_v3.py tests/test_cutover_historical_transfers_red.py tests/test_cutover_historical_transfers_apply_red.py -q` | **40 passed**, 2 warnings (26.65s) — VERDE |
| FRONTEND | `npx vitest run src/__tests__/cutoverGrandparentV3.test.tsx src/__tests__/r061.cutoverFlow.test.tsx` | **2 files / 7 tests passed** — VERDE |

## Resultado

| # | Mutante | Cambio aplicado | Tests que fallan | Veredicto |
|---|---|---|---|---|
| B1 | `contracts.py` · `_gp_o_base` | `_gp_o_base` devuelve **siempre** `texto_base` (desaparece el texto refinado de Progenitoras) | `test_gp_v3_ac01_contrato_y_textos_refinados`, `test_gp_v3_ac01_plantilla_instrucciones_refinadas` (2 failed) | **DETECTADO** |
| B2 | `contracts.py` · `_gp_o_base` + `_con_nota_gp` | condicion `bu in ("grandparent","breeder")`: el texto de Progenitoras se aplica **tambien** a breeder | `test_gp_v3_ac01_contrato_y_textos_refinados` (guarda «breeder intacto», 1 failed) | **DETECTADO** |
| B3 | `contracts.py` · `_con_nota_gp` | no se anade `_GP_NOTA_FASE` (frase «NO es una transferencia» ausente) | `test_gp_v3_ac01_contrato_y_textos_refinados`, `test_gp_v3_ac01_plantilla_instrucciones_refinadas` (2 failed) | **DETECTADO** |
| B4 | `service.py` · `PREVIEW_DESTACADAS['grandparent']` | se quitan las 4 transferencias del final de la tupla | `test_gp_v3_preview_y_reconciliacion_por_sexo` — AC-GP-09 (1 failed) | **DETECTADO** |
| B5 | `service.py` · `_transferencia_por_sexo` | devuelve `0` cuando la columna es `None` (UNKNOWN → 0) | `test_gp_v3_t09_unknown_no_se_inventa_ni_se_aplica_como_cero`, `test_gp_v3_persistencia_por_sexo_con_known_y_unknown`, `test_gp_v3_preview_y_reconciliacion_por_sexo` (3 failed) | **DETECTADO** |
| B6 | `service.py` · detalle de reconciliacion | intercambiados los valores: `historical_transfers_in_males` lee `accumulated_transfers_out_male` (y viceversa) | `test_gp_v3_t09_…`, `test_gp_v3_conformation01_origenes_con_salida_y_destino_con_entrada`, `test_gp_v3_persistencia_por_sexo_con_known_y_unknown`, `test_gp_v3_post_corte_no_vuelve_a_restar_lo_historico`, `test_gp_v3_preview_y_reconciliacion_por_sexo` (5 failed) | **DETECTADO** |
| B7 | `validation.py` · `_consistencia_reproductoras` | la ecuacion **ignora** las transferencias de salida (`esperado = alojadas + entradas − mort − desc`) | GP-V3: T02, T04, T06, T07, T08, T09, conformation01, desalojo, persistencia, post-corte; breeder: BR-T02, T04, T06, T08, T10; apply: HT apply_origen_y_receptor, unknown_no_es_cero, reconciliacion_expone_transferencias, sin_doble_conteo (19 failed) | **DETECTADO** |
| B8 | `validation.py` · `_consistencia_reproductoras` | transferencias UNKNOWN tratadas como `0` (la ecuacion se calcula aun con componentes UNKNOWN) | `test_gp_v3_t01_sin_transferencias_y_transferencias_vacias`, `test_gp_v3_t09_…`, `test_br_t08_unknown_no_inventa_cero_y_queda_no_verificable`, `test_ht_unknown_no_es_cero` (4 failed) | **DETECTADO** |
| F1 | `es/translation.json` · `cutover.fields` | se elimina la clave `historical_transfers_out_females` | `cutoverGrandparentV3` › (a) etiquetas propias del preview, (b) paridad ES/EN; `r061.cutoverFlow` › AC84/85 claves del namespace cutover (3 failed / 7) | **DETECTADO** |
| F2 | `en/translation.json` · `cutover.fields` | `historical_transfers_in_males` pasa a valer el nombre tecnico (sin texto propio) | `cutoverGrandparentV3` › (b) paridad ES/EN «texto propio distinto del nombre tecnico» (1 failed / 7) | **DETECTADO** |

## Agregado

- Mutantes ejecutados: **10** (B1–B8 backend, F1–F2 frontend)
- **DETECTADOS: 10**
- **SUPERVIVIENTES: 0**
- Restauraciones verificadas (`git diff --stat -- <archivo>` vacio): **10/10**
- Integridad final: `git diff --quiet e161d16 -- backend frontend e2e` → **exit 0** (arbol de codigo identico al commit)
- Redaccion: comprobacion de prefijo de token JWT (`grep`) sobre `50_mutation_raw.log` y `50_mutation_campaign.md` → **0** ocurrencias en ambos
- Re-baseline POST-campana (arbol restaurado): BACKEND **40 passed** (32.53s) · FRONTEND **2 files / 7 tests passed** → mismo verde que el baseline previo

## Notas / observaciones

1. Ningun mutante sobrevivio: la suite dirigida de la SPEC 019 (40 tests backend + 7 frontend) tiene
   sensibilidad completa sobre los 10 puntos de mutacion propuestos del contrato, la validacion, el
   preview y las etiquetas i18n.
2. Efectos colaterales observados (esperados y utiles como red de seguridad): B7 rompe tambien la suite de
   breeder y de apply/reconciliacion por sexo; B8 rompe ademas `test_br_t08` y `test_ht_unknown_no_es_cero`
   (misma semantica «UNKNOWN no es 0» replicada en las tres BUs); B6 rompe T09 y post-corte porque el
   intercambio M/H se propaga a los totales por sexo del detalle.
3. B4 solo lo detecta el test de preview/reconciliacion (AC-GP-09): las transferencias existen en el contrato,
   por lo que los tests de contrato/plantilla no pueden verlo — cobertura correcta y sin redundancia inutil.
4. No se ejecutaron suites completas ni E2E en esta campana: la delegacion acota los tests por mutante.
   La evidencia E2E/agregada de la SPEC 019 vive en los logs `40_…`–`44_…` de esta misma carpeta.
