# SPEC 014 · Tarea 4a — Rotura y reparación de la suite existente de SPEC 006

Motivo: breeder/grandparent pasan a contrato **v3** (`CUTOVER_GRANDPARENT_V3`, `CUTOVER_BREEDER_V3`) con las 4
columnas de transferencias históricas (`historical_transfers_in_males|females`,
`historical_transfers_out_males|females`; vacío = UNKNOWN, `0` = KNOWN) y la ecuación por sexo
`live = placed + in − mortality − culls − out`. Con algún componente UNKNOWN la ecuación **no se evalúa**
(`NOT_FULLY_VERIFIABLE`). Los tests de SPEC 006 que fijaban el contrato v2 fallaban por ese cambio.

Regla aplicada: se cambia el **mecanismo/versión**, nunca se debilita ni se elimina una aserción; cada ajuste
lleva un comentario `# SPEC 014: …` con la razón. No se tocó `backend/app`. No se introducen literales ISO
(guarda T-028) y no se añadió ni borró ningún test.

## Tabla «test → causa → ajuste»

| Test | Causa | Ajuste |
|---|---|---|
| `test_cutover_v2_validation.py::test_consistencia_sin_tolerancias` | La fila V-C1 (alojadas M 1100 / live M 1000, mort 50, culls 0) dejaba las transferencias vacías ⇒ UNKNOWN ⇒ veredicto `NOT_FULLY_VERIFIABLE` en vez de `CONSISTENCY_MISMATCH` | Se declaran explícitamente `historical_transfers_in_males=0, historical_transfers_in_females=0, historical_transfers_out_males=0, historical_transfers_out_females=0` en V-C1 (KNOWN) ⇒ `1100 + 0 − 50 − 0 − 0 = 1050 ≠ 1000` sigue siendo `CONSISTENCY_MISMATCH`; la aserción (`== [(2,"live_males","CONSISTENCY_MISMATCH"), (4,"accumulated_eggs_to_hatchery",…)]`) queda intacta y se conserva la intención «sin tolerancias». V-C2 se mantiene tal cual (una pieza UNKNOWN ⇒ no se evalúa) y su comentario ahora menciona que la ecuación incluye las transferencias |
| `test_cutover_v2_continuity.py::test_grandparent_primer_evento_de_su_fase` | El opening de grandparent se persiste con `template_version` del contrato vigente, ahora v3 | La aserción pasa a exigir `"v3"` (se mantienen los otros tres campos del tuple: 1000, 9000, `KNOWN`) |
| `test_cutover_v2_apply.py::test_apply_grandparent_destino_por_campo` | Ídem: `ob.template_version` de la apertura de grandparent | La aserción pasa a exigir `"v3"` conservando el resto de la condición (`cutover_datetime is not None`, `is_manual_activation is False`) |
| `test_cutover_v2_red.py::test_red_06_plantilla_descargada_rellenada_y_cargada` | La BU del test es **breeder** (no hatchery): la plantilla descargada con `batch_id` trae `Meta.template_version` del contrato vigente ⇒ v3 | `assert meta["template_version"] == "v3"` (breeder v3 por SPEC 014; hatchery v3 por SPEC 009; broiler sigue v2) |
| `test_ga_req_061_cutover_c2_lifecycle.py::test_c2_upload_validar_preview` | `_xlsx` construía la plantilla con `Meta.template_version="v2"` para `BU_FIXTURE="grandparent"`; el parser rechaza v2 para un contrato v3 (`TEMPLATE_VERSION_UNSUPPORTED`) | Default de `_xlsx` a `"v3"`. Las filas y las columnas ya venían de `cutover_v2_fixtures` (v3: `CUTOVER_GRANDPARENT_V3` + 4 columnas de transferencias vacías = UNKNOWN); las aserciones son idénticas |
| `test_ga_req_061_cutover_c2_lifecycle.py::test_c2_mismo_checksum_no_duplica` | Mismo motivo (usa `_xlsx` por defecto) | Cubierto por el default `v3` de `_xlsx`; sin cambios de aserciones (3 filas, no 6) |
| `test_ga_req_061_cutover_c2_lifecycle.py::test_c2_plantilla_descargable_y_cargable` | Afirmaba `template_version == ("v3" if bu == "hatchery" else "v2")` | Mapa explícito `{"grandparent": "v3", "breeder": "v3", "hatchery": "v3", "broiler": "v2"}` y la misma comparación por BU; el resto (hojas, `business_unit`, `NO_DATA_ROWS`, `BUSINESS_UNIT_INVALID`) intacto |

Sin fallos adicionales: ninguna otra suite del conjunto cambió de veredicto.

## Comando ejecutado

```
cd backend && ./scripts/run_tests.sh tests/test_cutover_v2_validation.py tests/test_cutover_v2_contracts.py \
  tests/test_cutover_v2_continuity.py tests/test_cutover_v2_apply.py tests/test_cutover_v2_red.py \
  tests/test_cutover_v2_keyuser_s01_red_parse.py tests/test_cutover_v2_keyuser_s01_red_db.py \
  tests/test_ga_req_061_cutover_c1_schema.py tests/test_ga_req_061_cutover_c2_lifecycle.py \
  tests/test_ga_req_061_cutover_c3_lifecycle.py tests/test_ga_req_061_cutover_c4_apply.py \
  tests/test_ga_req_061_cutover_c5_reporting.py tests/test_ga_req_061_cutover_c6_corrections.py \
  tests/test_ga_req_061_cutover_c7_controls.py tests/test_ga_req_061_cutover_c7_matrix.py \
  tests/test_cutover_s3_timezone.py tests/test_cutover_uat_hardening_s011.py \
  tests/test_cutover_historical_transfers_red.py tests/test_cutover_historical_transfers_apply_red.py \
  tests/test_population_invariant.py tests/test_company_catalog.py 2>&1 | grep -E "^FAILED|passed|failed"
```

## Salida real (resumen)

```
================= 201 passed, 13 warnings in 84.31s (0:01:24) ==================
```

Salida por fichero (misma corrida):

```
tests/test_cutover_v2_validation.py ...........                          [  5%]
tests/test_cutover_v2_contracts.py ..................................... [ 23%]
tests/test_cutover_v2_continuity.py ......                               [ 28%]
tests/test_cutover_v2_apply.py .........                                 [ 33%]
tests/test_cutover_v2_red.py .........                                   [ 37%]
tests/test_cutover_v2_keyuser_s01_red_parse.py ...............           [ 45%]
tests/test_cutover_v2_keyuser_s01_red_db.py ...........                  [ 50%]
tests/test_ga_req_061_cutover_c1_schema.py ..                            [ 51%]
tests/test_ga_req_061_cutover_c2_lifecycle.py .....                      [ 54%]
tests/test_ga_req_061_cutover_c3_lifecycle.py ....                       [ 56%]
tests/test_ga_req_061_cutover_c4_apply.py ....                           [ 58%]
tests/test_ga_req_061_cutover_c5_reporting.py ....                        [ 60%]
tests/test_ga_req_061_cutover_c6_corrections.py .....                    [ 62%]
tests/test_ga_req_061_cutover_c7_controls.py ......                      [ 65%]
tests/test_ga_req_061_cutover_c7_matrix.py .........                     [ 70%]
tests/test_cutover_s3_timezone.py .......                                [ 73%]
tests/test_cutover_uat_hardening_s011.py ..                              [ 74%]
tests/test_cutover_historical_transfers_red.py ..............            [ 81%]
tests/test_cutover_historical_transfers_apply_red.py .....               [ 84%]
tests/test_population_invariant.py .....................                 [ 94%]
tests/test_company_catalog.py ...........                                [100%]
```

## Ficheros modificados en esta tarea

- `backend/tests/test_cutover_v2_validation.py`
- `backend/tests/test_cutover_v2_continuity.py`
- `backend/tests/test_cutover_v2_apply.py`
- `backend/tests/test_cutover_v2_red.py`
- `backend/tests/test_ga_req_061_cutover_c2_lifecycle.py`
