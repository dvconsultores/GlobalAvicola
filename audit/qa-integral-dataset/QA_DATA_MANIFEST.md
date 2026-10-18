# QA Data Manifest — `QA-DEMO-V1`

| Campo | Valor |
|---|---|
| Versión del dataset | `QA-DEMO-V1` |
| Marcador | `QA_DEMO_V1` · prefijos `QA-` (códigos), `QAP…` (centros SAP), `qa.` (usuarios), `QA_SYNTHETIC` (SAP) |
| Seed canónico | `backend/seeds/qa_integral_dataset.py` (+ `qa_integral_builders.py`) |
| Última corrida certificada | aislado, `run_id=QA-DEMO-V1-ISOLATED-20261018`, SHA de código `3e146ac` (pre-commit; ver `12_TRACEABILITY.md`) · JSON: `QA_DATA_MANIFEST.json` |
| Corrida en runtime compartido | **PENDIENTE** (`09_RUNTIME_VERIFICATION.md`): al ejecutarse, adjuntar su manifest como `QA_DATA_MANIFEST_runtime.json` |
| Entidades creadas por `--apply` | **720 creadas** · 4 existentes (catálogos globales) en el ciclo aislado de R1 (`evidence/06_isolated_cycle.log`); el inventario de abajo no cambia |
| Cleanup | `READY_NOT_EXECUTED` |
| SAP real | 0 llamadas · `SAP_REAL_TEST=PENDING_2026_10_20` |

## Inventario (corrida aislada)

| Entidad | Cantidad |
|---|---|
| Empresas QA | 2 (QA Avícola Integral C.A. · QA Avícola Aislamiento C.A.) |
| Usuarios `qa.*` | 12 |
| Granjas | 6 (5 MAIN + 1 ISO) · galpones 17 (1 inactivo) |
| Incubadora / incubadoras / nacedoras | 1 / 4 / 2 |
| Lotes | 25 (21 del guion + 4 por cargas iniciales): GP 5 · BR 5 · HAT 8 · BRO 5 · ISO 2 |
| Eventos operativos | 364 (28/28 tipos; estados: approved 333 · consolidated 5 · corrected 7 · registered 4 · draft 3 · pending_review 3 · returned 3 · in_review 2 · reversed 2 · rejected 1 · cancelled 1) |
| Movimientos | aves 171 · huevo 171 · alimento 68 · parámetros de incubación 10 · inspecciones 12 |
| Aprobaciones / correcciones / reversos | 365 / 2 / 1 |
| Alertas / notificaciones | 18 / 41 |
| Saldos de apertura | 11 (+1 hatchery_opening) |
| Cargas iniciales aplicadas | 4 (una por BU) |
| SAP inbound sintético | 85 registros · 14 objetos · 14 jobs · 13 mappings · 47 referencias (OC: 7) |
| Trazabilidad | 7 egg_batches · 2 chick_batches |
| Auditoría | 791 entradas |

## Lotes

QA-GP-CRIA-001 · QA-GP-PROD-001 · QA-GP-CLOSE-001 · QA-GP-CLOSED-001 · QA-CUT-GP-001 · QA-BR-CRIA-001 · QA-BR-PROD-001 · QA-BR-PROD-002 · QA-BR-CLOSED-001 · QA-CUT-BR-001 · QA-HAT-GPGEN-001 · QA-HAT-REC-001 · QA-HAT-INC-001 · QA-HAT-OVO-001 · QA-HAT-NAC-001 · QA-HAT-BIRTH-001 · QA-HAT-CHICK-001 · QA-CUT-HAT-001 · QA-BRO-001 · QA-BRO-002 · QA-BRO-003 · QA-BRO-CLOSED-001 · QA-CUT-BRO-001 · QA-ISO-BR-001 · QA-ISO-BRO-001

## Credenciales

No versionadas. Mecanismo: `GA_QA_SEED_PASSWORD` (una contraseña temporal común para los 12 usuarios) o archivo `/tmp/global_avicola_qa_credentials.txt` (0600) generado por el seed. Entrega al Owner por canal separado.
