# 05 · Tests del seed

`backend/tests/test_qa_integral_dataset.py` — ejecutados con `scripts/run_tests.sh tests/test_qa_integral_dataset.py tests/test_seed_email_domains.py` (pgserver aislado): **18 passed**.

| Test | Qué garantiza |
|---|---|
| `test_sin_contrasenas_literales_en_el_seed` | ninguna contraseña literal en `qa_integral_*.py` |
| `test_sin_dsn_ni_hosts_reales_en_el_seed` | sin DSN, sin IP, sin literal `"SAP_HANA_CLOUD"` |
| `test_marcadores_de_trazabilidad` | VERSION/MARKER/PREFIX/USER_PREFIX/SAP_SOURCE; 12 usuarios `qa.*` únicos; dominio válido; empresas `QA ` |
| `test_es_codigo_qa` | reconoce `QA-…`, `QAP1`, `QAP1-0001`; rechaza códigos no QA |
| `test_entorno_prohibido_aborta_antes_de_conectar[production/prod/staging/pre/preprod]` | abort por `SystemExit` antes de abrir conexión |
| `test_escritura_sin_confirm_target_aborta` | escritura sin `--confirm-target` o con nombre distinto ⇒ abort |
| `test_escritura_con_confirm_target_correcto_pasa` | con el nombre de la BD configurada pasa |
| `test_lectura_no_exige_confirmacion` | `--inventory`/`--verify` no exigen confirmación |
| `test_credenciales_desde_env_o_archivo_0600` | `GA_QA_SEED_PASSWORD` prevalece; archivo 0600 generado; relectura estable; usuarios nuevos completados |
| `test_cleanup_cubre_toda_tabla_que_referencia_a_las_que_borra` | toda tabla con FK hacia el plan está en el plan (metadata real) |
| `test_cleanup_fail_closed_ante_datos_no_marcados` | empresa QA con lote sin marca ⇒ `AMBIGUOUS_QA_DATA` y 0 borrados en dry-run y real |
| `test_cleanup_sin_empresas_qa_no_hace_nada` | `NOTHING_TO_CLEAN`; inventario vacío |
| `test_seed_email_domains.py` (2, existente) | el nuevo seed no usa dominios reservados |

Cobertura adicional por ejecución real (no unit test): `06_SEED_EXECUTION_ISOLATED.md` (idempotencia CREATED=0, verify PASS) y `07_CLEANUP_PROOF.md` (CREATE→CLEAN→RECREATE).
