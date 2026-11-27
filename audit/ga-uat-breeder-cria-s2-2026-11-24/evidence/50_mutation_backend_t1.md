# Campaña de sensibilidad — Tanda 1 (backend, 6 mutantes)

- Repo: rama `develop`, HEAD `3073ff6`; el código de producción de los dos ficheros mutados es
  idéntico al del commit `8366827` (verificado con `git diff --stat 8366827 HEAD -- <archivos>`).
- Suite de cada corrida (una sola vez por mutante):
  `backend/scripts/run_tests.sh tests/test_uat_s2_write_contract.py tests/test_uat_s2_corrections_masters.py
  tests/test_uat_s2_corrections_messages.py tests/test_uat_s2_review_filters.py
  tests/test_uat_s2_operations_pins.py -q --tb=line -p no:cacheprovider`
- Línea base sin mutar: **61 passed** (29,3 s). Ninguna corrida falló por infraestructura.
- Restauración tras cada mutante: `git restore --source=8366827 -- <archivo>` + `git diff --stat`
  vacío verificado antes del siguiente mutante.
- Abreviaturas: `WC` = `tests/test_uat_s2_write_contract.py`, `PINS` = `tests/test_uat_s2_operations_pins.py`.

| Mutante | Archivo | Mutación | Resultado | Tests que lo detectan |
|---|---|---|---|---|
| M1 | `app/operations/validators.py` · `validate_muestra` | `if sample_size < 1:` → `if False:` (neutraliza `RR-24`) | **DETECTADO** (6 fallos) | `WC::test_ops_s2_04a_muestra_negativa_es_400`, `WC::test_ops_s2_04a_muestra_cero_es_400`, `WC::test_ops_s2_04b_aves_pesadas_negativas_es_400`, `WC::test_ops_s2_04b_aves_pesadas_cero_es_400`, `WC::test_corr_s2_04_muestra_negativa_en_correccion_es_400`, `WC::test_corr_s2_04_muestra_cero_en_correccion_es_400` |
| M2 | `app/operations/validators.py` · `validate_muestra` | `if sample_size > poblacion:` → `if sample_size >= poblacion:` (`RR-25`) | **DETECTADO** (4 fallos) | `WC::test_ops_s2_04a_muestra_igual_a_lo_recibido_es_aceptada`, `WC::test_ops_s2_04c_editar_la_muestra_hasta_lo_recibido_es_200`, `WC::test_corr_s2_04_muestra_valida_en_correccion_se_aplica`, `PINS::test_ops_s2_11_muestra_igual_a_lo_alojado_es_201` |
| M3 | `app/operations/validators.py` · `validate_muestra` | `if tipo == EventType.BIRD_RECEPTION.value:` → `if False:` (desactiva la cota superior de la recepción) | **DETECTADO** (4 fallos) | `WC::test_ops_s2_04a_muestra_mayor_que_lo_recibido_es_400`, `WC::test_ops_s2_04c_editar_la_muestra_por_encima_de_lo_recibido_es_400`, `WC::test_corr_s2_04_muestra_por_encima_de_lo_recibido_en_correccion_es_400`, `PINS::test_ops_s2_11_muestra_mayor_que_lo_alojado_es_400` |
| M4 | `app/operations/validators.py` · `validate_cantidades_no_negativas` | `if valor is not None and valor < 0:` → `if False:` (`RR-26`) | **DETECTADO** (7 fallos) | `WC::test_ops_s2_dosis_dosis_negativa_en_el_alta_es_400`, `WC::test_ops_s2_dosis_dias_de_tratamiento_negativos_en_el_alta_es_400`, `WC::test_ops_s2_dosis_dosis_negativa_en_la_edicion_es_400`, `WC::test_ops_s2_dosis_dias_negativos_en_la_edicion_es_400`, `WC::test_ops_s2_dosis_dosis_negativa_en_la_correccion_es_400`, `WC::test_ops_s2_dosis_dias_negativos_en_la_correccion_es_400`, `WC::test_ops_s2_dosis_pollitos_sanos_negativos_en_la_correccion_es_400` |
| M5 | `app/corrections/service.py` · `create_correction` | se comenta `operaciones.validar_cantidades_del_candidato(event, {data.field_name: valor_aplicado})` | **DETECTADO** (6 fallos) | `WC::test_corr_s2_04_muestra_negativa_en_correccion_es_400`, `WC::test_corr_s2_04_muestra_cero_en_correccion_es_400`, `WC::test_corr_s2_04_muestra_por_encima_de_lo_recibido_en_correccion_es_400`, `WC::test_ops_s2_dosis_dosis_negativa_en_la_correccion_es_400`, `WC::test_ops_s2_dosis_dias_negativos_en_la_correccion_es_400`, `WC::test_ops_s2_dosis_pollitos_sanos_negativos_en_la_correccion_es_400` |
| M6 | `app/corrections/service.py` · `create_correction` | `if valor_aplicado is None and data.field_name in NO_VACIABLES:` → `if False and data.field_name in NO_VACIABLES:` (`event_date` no vaciable) | **DETECTADO** (1 fallo) | `WC::test_corr_s2_06_vaciar_la_fecha_del_evento_es_400_y_no_cambia_nada` |

## Conclusión

6/6 mutantes DETECTADOS; 0 supervivientes. La suite de la Sesión 2 cubre `RR-24`, `RR-25`, `RR-26`
—en alta, edición y corrección— y la guarda de campos no vaciables en la corrección, con detección
mínima de 1 test (M6) y máxima de 7 (M4). Las 6 restauraciones dejaron `git diff --stat` vacío; el
árbol queda sin cambios versionados y el único artefacto nuevo es este informe.
