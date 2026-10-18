# 07 · Prueba del cleanup (aislado) — `READY_NOT_EXECUTED` en runtime

Contrato: `specs/007-qa-integral-demo-dataset/cleanup-contract.md`. Log: `evidence/06_isolated_cycle.log` pasos 6–13. **En el runtime compartido no se ha ejecutado ni se ejecutará sin decisión Owner (OD-QA-04).**

## Secuencia probada

| Paso | Acción | Resultado |
|---|---|---|
| 6 | `--cleanup` sin confirmación | abort, 0 cambios |
| 7 | `--cleanup --dry-run` | `DRY_RUN`, `ambiguous=[]`, plan de 61 tablas, `total=2447` (conteo; `egg_batches`/`chick_batches` se cuentan por dos condiciones solapadas) |
| 8 | `--inventory` | sin cambios respecto al estado poblado |
| 9 | `--cleanup --confirm-target global_avicola_test` | **`CLEANED` · `total=2438`** en una transacción, orden FK derivado del metadata |
| 10 | `--inventory` | `qa_companies=[]`, usuarios/granjas/lotes/eventos/referencias/inbound/cutover = 0 |
| 11 | consultas de control | `users qa.*=0 · lots QA-=0 · companies QA-DEMO-V1*=0 · sap_references QA%=0 · operational_events=0` y **baseline intacto**: `companies=2 (certificación) · roles=7 · admin=1 · productive_phases=4 · business_units=4 · permissions=64` |
| 12 | `--apply` | `CREATED=719 · EXISTING=4` ⇒ recreación completa |
| 13 | `--verify` | `QA_DATA_VERIFY = PASS` |

## Fail-closed (tests)

`test_cleanup_fail_closed_ante_datos_no_marcados`: una empresa QA con un lote `LOTE-REAL-SIN-MARCA` ⇒ `AMBIGUOUS_QA_DATA`, lista `ambiguous=['lot:LOTE-REAL-SIN-MARCA']`, 0 borrados en dry-run y en modo real. `test_cleanup_cubre_toda_tabla_que_referencia_a_las_que_borra`: ninguna tabla con FK hacia el plan queda fuera del plan (incluye `sap_responses`, `opening_balance_corrections`, `hatchery_openings`, `revoked_tokens`).

## Plan de borrado (por tabla, condición acotada a las empresas QA)

opening_balance_corrections · hatchery_openings · chick_batches · egg_batches · approval_actions · correction_logs · evidences · bird/egg/feed_movements · hatchery_params · inspection_details · egg_storage · operational_alerts · reversals · consolidated_movements · notifications · sap_responses · sap_payloads · audit_logs · operational_events · cutover_items · cutover_staging_rows · cutover_batches · opening_balances · lot_phases · lots · review_batches · approval_steps · sap_inbound_records · sap_inbound_sync_jobs · sap_inbound_watermarks · sap_entity_mappings · sap_references · sap_sync_jobs · genetic_weight_curve_points · genetic_weight_curves · breeds · genetic_lines · houses · farms · incubators · hatchers · hatcheries · suppliers · feed_types · vaccines · medications · mortality_causes · cull_causes · transports · processing_plants · rejection_reasons · correction_types · user_business_units · company_business_units · revoked_tokens · users · areas · companies.

## Para ejecutarlo en el runtime (cuando el Owner lo decida)

```
.venv/bin/python -m seeds.qa_integral_dataset --inventory
.venv/bin/python -m seeds.qa_integral_dataset --cleanup --dry-run          # exige ambiguous=[]
.venv/bin/python -m seeds.qa_integral_dataset --cleanup --confirm-target avicolav2
.venv/bin/python -m seeds.qa_integral_dataset --inventory                  # debe quedar vacío
```
