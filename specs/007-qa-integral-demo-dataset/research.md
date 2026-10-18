# Research — SPEC 007 (Discovery §4 del mandato)

Fecha: 2026-10-18 · HEAD `3e146ac` · árbol limpio salvo manuales/seeds nuevos.

## 1 · Modelo de datos relevante (65 tablas, head `e0f1a2b3c4d5`)

- **Tenancy**: `companies` (approval_levels), `users` (role_id, company_id, view_type), `roles`/`permissions` canónicos con `company_id NULL`, `business_units` (4 códigos canónicos, dato de despliegue), `company_business_units` (is_enabled), `user_business_units` (company_business_unit_id, revoked_at).
- **Maestros por empresa**: farms, houses, hatcheries/incubators/hatchers, areas, genetic_lines/breeds/genetic_weight_curves(+points), suppliers, feed_types, vaccines, medications, mortality_causes, cull_causes, transports, processing_plants, rejection_reasons, correction_types. `productive_phases` es global.
- **Lotes**: `lots` (bird_type enum = BU, status, start/end/planned_close, hatchery_purpose, origin, source_system/reference), `lot_phases`, `opening_balances` (+ `*_status` KNOWN/UNKNOWN/NOT_APPLICABLE), `hatchery_openings`, `egg_batches`/`chick_batches` (trazabilidad generacional).
- **Operación**: `operational_events` (28 tipos, 14 estados, idempotency_key, sap_document_ref) + bird/egg/feed_movements, hatchery_params, inspection_details, egg_storage, evidences, operational_alerts, reversals.
- **Revisión**: approval_steps (por empresa y nivel, require_segregation), approval_actions, review_batches, correction_logs.
- **SAP**: sap_references (ref_type, sap_code, quantity, extra_data), sap_payloads/responses, sap_sync_jobs, consolidated_movements; inbound: sap_inbound_records (source_system, object_type, estados V/M/P), sap_inbound_sync_jobs, sap_inbound_watermarks, sap_entity_mappings.
- **Transversal**: audit_logs, notifications, revoked_tokens, cutover_batches/items/staging_rows, opening_balance_corrections.

## 2 · Servicios reutilizados

| Servicio | Uso en el seed |
|---|---|
| `OperationsService.create_event / submit_to_review / cancel_event` | toda la historia operativa y el inicio del workflow |
| `ReviewService.start_review / return_to_operator / complete_review` | in_review, returned, corrected |
| `ApprovalService.approve / reject` | approved, rejected (BR-14 segregación) |
| `CorrectionService.create_correction` | corrected con CorrectionLog antes/después |
| `ReversalService.solicitar` + flujo de contrapartida | reversed (OD-19) |
| `LotService.activate_manual / close_lot` | aperturas manuales (BR-05 y R7 en el cierre) |
| `CutoverService` (SPEC 006) | batch v2 por BU: upload → validate → submit → approve → apply |
| `staging.stage` + `promotion.upsert_reference` | inbound SAP sintético por los 14 objetos del registry |
| `SapService.consolidate_approved` | estado `consolidated` (pre-SAP, sin envío) |
| `notifications.service.crear_notificacion` | `lot_near_close` leída/no leída |

## 3 · Seeds existentes (no se sustituyen)

| Seed | Alcance | Relación con 007 |
|---|---|---|
| `baseline_seeds` | roles+permisos, admin, fases, 2 empresas de certificación, BU | prerrequisito: 007 **lee** roles/fases/BU de aquí |
| `test_seeds` | dataset determinista del arnés | sin relación; 007 no corre dentro de pytest |
| `dev_seeds`, `integration_seeds`, `legacy_state_seeds` | desarrollo local | sin relación |
| `scenario_fixtures` (`FX-`) | fixtures de escenario con retiro | patrón de prefijo/retiro adoptado; alcance menor |
| `live_data_boost` (`BOOST_TAG`) | refuerzo de datos en vivo | patrón de marcador adoptado |

## 4 · Navegación (fuente única `frontend/src/data/navigationConfig.ts`)

`dashboard` · `poultry{lots, operations_history, my_pending, grandparent{gp_rearing, gp_production}, breeder{br_rearing, br_production}, hatchery, broiler}` · `review{review_pending, review_approved, review_returned}` · `approvals` · `sap{sap_pending, sap_sent, sap_errors, sap_log}` · `reports{rpt_production, rpt_mortality, rpt_sap}` · `cutover` · `audit` · `masters` · `settings{settings_users, settings_roles, settings_profile, settings_unit_access}`. Vista móvil: solo `poultry`.

## 5 · Reglas de negocio que el dataset debe respetar

BR-01/03/04 saldos (leen la apertura), BR-05 cierre con pesaje+alimento, BR-07 lote ajeno = 404, BR-08 farm/house en huevos, BR-14 segregación, BR-16 reverso único, BR-18 límite acumulado de OC, BR-20/21/22 recepción/nacimiento/importación, CUT-GL-02 fecha de corte, R7 cierre con todo aprobado, OD-16 alcance por BU, OD-19 reverso con contrapartida.

## 6 · Decisiones de diseño

1. **Fastpath de aprobación para el histórico** (justificado en `plan.md §1`); el workflow demostrativo usa servicios reales.
2. **SAP sintético por el mismo pipeline de staging** para que la UI de Integración muestre registros reales del modelo, con `source_system=QA_SYNTHETIC`.
3. **Códigos de centro SAP `QAP1…`** (WERKS es de 4 caracteres): se reconocen como QA por `es_codigo_qa`.
4. **Orden de borrado derivado del metadata**, no mantenido a mano.
5. **Empresa de aislamiento** con `grandparent`/`hatchery` apagadas para probar OD-16 y multiempresa.
