# Data Model — SPEC 007

Sin cambios de esquema (head `e0f1a2b3c4d5`, 65 tablas). Este documento describe **cómo el dataset ocupa** el modelo existente y qué columnas llevan el marcador de trazabilidad.

## 1 · Marcadores por entidad

| Entidad | Clave natural de idempotencia | Marcador |
|---|---|---|
| companies | `tax_id` | `tax_id = QA-DEMO-V1-INTEGRAL / -AISLAMIENTO`, nombre `QA …` |
| users | `username` | `qa.*`, email `@qa.globalavicola.com` |
| company_business_units / user_business_units | (company, bu) / (user, cbu) | pertenencia a empresa QA |
| approval_steps | (company, level) | pertenencia |
| farms / houses / hatcheries / incubators / hatchers / areas | `code` o `name` + empresa | `QA-…` / `QA …` |
| genetic_lines / breeds / genetic_weight_curves(+points) | `code` + empresa | `QA-LINE-…` |
| catálogos (suppliers, feed_types, vaccines, medications, mortality_causes, cull_causes, transports, processing_plants, rejection_reasons, correction_types) | `name` + empresa | nombre `QA …` |
| lots | `lot_code` | `QA-…`, `source_system=QA_DEMO_V1`, `source_reference=<run_id>` |
| lot_phases | (lot, phase) | vía lote |
| opening_balances / hatchery_openings | lot_id | `activation_reason`/`notes` con `QA_DEMO_V1` |
| operational_events | `idempotency_key = QA_DEMO_V1:<company_id>:<clave>` | `extra_data.qa_marker=QA_DEMO_V1` |
| bird/egg/feed_movements, hatchery_params, inspection_details | event_id | vía evento |
| approval_actions / correction_logs / reversals / operational_alerts | event_id | comentarios con `QA_DEMO_V1` |
| notifications | (company, recipient, type, `payload.qa_key`) | `payload.qa_key` |
| sap_entity_mappings | (company, entity, key) | `extra.source=QA_SYNTHETIC` |
| sap_inbound_sync_jobs / sap_inbound_records | `source_key` | `source_system=QA_SYNTHETIC` |
| sap_references | (company, ref_type, sap_code) | `QA-…`/`QAP…`, `extra_data.source=QA_SYNTHETIC` |
| consolidated_movements | (lot, type, period) | vía lote |
| cutover_batches / items / staging_rows | `legacy_lot_code` | `source_system=QA_DEMO_V1`, `source_reference=<run_id>` |
| audit_logs | — | `company_id` QA; usuario `qa.*` |
| egg_batches / chick_batches | derivados por el motor | vía lotes |

## 2 · Semántica de estados usados

- `operational_events.status`: draft, registered, pending_review, in_review, returned, corrected, approved, rejected, consolidated, reversed, cancelled (nunca sent_to_sap / sap_confirmed / sap_error).
- `opening_balances.*_status`: KNOWN, UNKNOWN (deliberado en alimento GP/BRO y descartados HAT), NOT_APPLICABLE (huevos en cría).
- `sap_inbound_records`: `V_VALID`/`M_MAPPED`/`P_PROMOTED` para los promovidos; `M_PENDING_MAPPING` (`QAP7`); `V_INVALID` (`QA-MAT-INVALIDO`).
- `lots.status`: active (mayoría), closed (`*-CLOSED-001`).
- `cutover_batches.status`: applied.

## 3 · Relaciones generacionales creadas

```
QA-GP-PROD-001 ─egg_dispatch→ QA-HAT-GPGEN-001 ─chick_dispatch→ QA-BR-CRIA-001
QA-BR-PROD-001 ─egg_dispatch→ QA-HAT-{REC,INC,OVO,NAC,BIRTH,CHICK}-001 ─chick_dispatch→ QA-BRO-001 (destino QA-EN-01)
```
`egg_batches` (7) y `chick_batches` (2) los crea el motor al despachar/recibir; el árbol de trazabilidad del lote los muestra.

## 4 · Volumen (corrida aislada 2026-10-18)

25 lotes · 364 eventos · 171 bird_movements · 171 egg_movements · 68 feed_movements · 10 hatchery_params · 12 inspection_details · 365 approval_actions · 2 correction_logs · 1 reversal · 18 operational_alerts · 41 notifications · 11 opening_balances · 1 hatchery_opening · 4 cutover_batches · 85 sap_inbound_records · 14 sync jobs · 13 mappings · 47 sap_references · 791 audit_logs.
