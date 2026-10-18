# 06 · Ejecución del seed en entorno aislado

Log completo: `evidence/06_isolated_cycle.log` (pgserver del arnés, base `global_avicola_test`, `ENVIRONMENT=test`, secretos efímeros no registrados). Guion: alembic head → `baseline_seeds.sembrar_baseline` (roles, admin, fases, 2 empresas de certificación, BU) → ciclo.

| Paso | Comando | Resultado |
|---|---|---|
| 1 | `--inventory` | base sin dataset: `qa_companies=[]`, 0 en todo |
| 2 | `--apply --confirm-target global_avicola_test --run-id QA-DEMO-V1-ISOLATED-20261018 --manifest …` | `CREATED=719 · EXISTING=4 (fases globales) · UPDATED=0 · SKIPPED=0` · **14 s** · fixtures XLSX ×4 · manifest escrito |
| 3 | `--verify` | 22/22 comprobaciones `PASS` · `QA_DATA_VERIFY = PASS` |
| 4 | `--apply` (segunda vez) | **`CREATED=0 · EXISTING=693`** ⇒ idempotente (AC-01) |
| 5 | `--verify` | `PASS` |
| 6 | `--cleanup` sin `--confirm-target` | `ABORTADO: la escritura exige --confirm-target 'global_avicola_test'` (AC-05) |
| 7 | `--cleanup --dry-run` | `status=DRY_RUN · ambiguous=[] · total=2447` (conteo por tabla; sin escrituras) |
| 8 | `--inventory` | idéntico al paso 3 ⇒ el dry-run no escribió |
| 9–13 | ver `07_CLEANUP_PROOF.md` | CLEANED → vacío → baseline intacto → recreación 719 → `PASS` |
| 14 | `ENVIRONMENT=production … --inventory` | `ABORTADO: ENVIRONMENT='production' no es un entorno autorizado` (AC-05) |

## Detalle de `--verify` (paso 3, idéntico en 5 y 13)

```
[PASS] 2 QA companies · 4 BU primary enabled · isolation BU on/off {grandparent: False, breeder: True, hatchery: False, broiler: True}
[PASS] users and roles correct (faltan=[]) · BU grants correct · qa.mobile view_type mobile
[PASS] farms/houses valid granjas=5 galpones=15 inactivos=1 · hatchery equipment plantas=1 incubadoras=4 nacedoras=2
[PASS] lots have company/BU lotes=25 · lots per BU {grandparent: 5, breeder: 5, hatchery: 8, broiler: 5}
[PASS] event details exist eventos=364 sin_detalle=0
[PASS] workflow states valid {approved: 333, reversed: 2, registered: 4, draft: 3, returned: 3, pending_review: 3, in_review: 2, corrected: 7, rejected: 1, cancelled: 1, consolidated: 5}
[PASS] event types coverage faltan=[]  (28/28)
[PASS] SAP refs company-scoped & synthetic refs=47 · PO quantities coherent (GP 5000 · BR 10000 · BRO 10000/12500 · BR18-TEST 1000)
[PASS] inbound 14 objects staged, QA_SYNTHETIC objetos=14 registros=85
[PASS] EggBatch/ChickBatch coherent egg_batches=7 chick_batches=2 · reports have source data aprobados=202
[PASS] UNKNOWN scenario present openings=11 · QA markers present · cutover applied per BU [grandparent, breeder, hatchery, broiler]
[PASS] real SAP calls = 0
```

## Contadores de la primera corrida (CREATED)

companies 2 · users 12 · company_business_units 8 · user_business_units 29 · approval_steps 3 · areas 5 · farms 6 · houses 17 · hatcheries 1 · incubators 4 · hatchers 2 · genetic_lines 3 · breeds 3 · genetic_weight_curves 3 · suppliers 7 · feed_types 5 · vaccines 5 · medications 4 · mortality_causes 5 · cull_causes 4 · transports 4 · processing_plants 3 · rejection_reasons 3 · correction_types 3 · sap_entity_mappings 13 · sap_inbound_sync_jobs 14 · sap_inbound_records 85 · sap_references 17 (+30 promovidas por documentos) · lots 21 (+4 por cutover) · lot_phases 19 · opening_balances 7 (+4 por cutover) · operational_events 363 (+1 contrapartida de reverso) · lots_closed 3 · notifications 3 (+38 del motor) · consolidated_movements 1 · cutover_batches 4.

Manifest de la corrida: `evidence/manifest_isolated.json`.
