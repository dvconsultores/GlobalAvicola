# SAP-HANA-CLOUD · 09_TEST_MATRIX

Fecha: 2026-10-06 · SPEC 005 · Matriz AC → prueba. Ninguna prueba llama a SAP: el driver es `FakeHana`.

---

## 1 · Suites

| Suite | Archivo | Pruebas | Base de datos |
|---|---|---|---|
| Guard + registry | `backend/tests/test_sap_hana_guard.py` | 16 funciones (parametrizadas por sentencia y por objeto) | no |
| Cliente, configuración, adaptador | `backend/tests/test_sap_hana_client.py` | 23 | no |
| Sync, idempotencia, watermark, mapping | `backend/tests/test_sap_hana_sync.py` | 39 | PostgreSQL de pruebas |
| Promoción, BR-18 | `backend/tests/test_sap_hana_promotion.py` | 16 | PostgreSQL de pruebas |
| Rutas, RBAC, alcance, R-201, outbound | `backend/tests/test_sap_hana_routes.py` | 24 | PostgreSQL de pruebas |
| Escenario compartido | `backend/tests/sap_hana_fixtures.py` | — | — |
| Frontend | `frontend/src/pages/sap/__tests__/sapInbound.test.tsx` | ver `11_LOCAL_CERTIFICATION` | — |
| E2E | `e2e/sap-hana-inbound.spec.ts` | ver `11_LOCAL_CERTIFICATION` | pila local |

## 2 · Pruebas exigidas por el mandato (§45) → ubicación

| Prueba del mandato | Archivo |
|---|---|
| `test_hana_adapter_missing_credentials`, `test_hana_adapter_tls_required`, `test_hana_connection_fake_success`, `test_hana_connection_fake_auth_error`, `test_hana_secret_never_leaks` | `…_client.py` |
| `test_hana_adapter_uses_readonly_registry`, `test_hana_guard_rejects_update / insert / delete / merge / call / multiple_statements`, `test_hana_query_uses_bound_parameters` | `…_guard.py` |
| `test_hana_no_raw_sql_endpoint` | `…_routes.py` |
| `test_sync_company / plant / storage_location / vendor / material / purchase_order / purchase_order_history / production_order / transfer_order / outbound_order / material_movement / batch` | `…_sync.py` |
| `test_sync_duplicate_same_hash_noop`, `test_sync_changed_hash_versioned`, `test_sync_failed_batch_does_not_advance_watermark`, `test_unknown_company_pending_mapping`, `test_unknown_plant_pending_mapping` | `…_sync.py` |
| `test_purchase_order_promotes_quantity`, `test_purchase_order_br18_limit`, `test_purchase_order_cross_company_isolation` | `…_promotion.py` |
| `test_outbound_disabled`, `test_delivers_to_sap_false`, `test_sap_inbound_routes_rbac`, `test_sap_inbound_routes_scope_declared`, `test_sap_inbound_transaction_coverage` | `…_routes.py` |

## 3 · AC → pruebas

| AC | Pruebas |
|---|---|
| 03 | `test_hana_registry_has_no_legacy_hardcodes`, `test_hana_document_objects_require_time_window` |
| 04, 10 | `test_hana_no_raw_sql_endpoint`, `test_hana_client_only_runs_registry_definitions`, `test_objects_catalog_is_served_without_sql` |
| 05 | `test_outbound_is_disabled_by_default`, `test_outbound_disabled`, `test_outbound_disabled_does_not_touch_failed_payloads`, `test_delivers_to_sap_false`, `test_real_outbound_adapter_stays_unimplemented` |
| 06, 11 | `test_hana_guard_*`, `test_hana_registry_is_closed`, `test_fake_hana_rejects_anything_outside_the_registry` |
| 07 | `test_hana_secret_never_leaks`, `test_job_error_message_is_sanitized`, `test_readiness_never_returns_secret_values` |
| 08, 09 | `test_hana_adapter_tls_required`, `test_hana_tls_disabled_never_connects`, `test_hana_custom_ca_keeps_validation_on` |
| 12 | `test_hana_query_uses_bound_parameters`, `test_hana_client_executes_registry_sql_with_bind_parameters`, `test_hana_schema_is_a_validated_identifier_never_request_input`, `test_sync_window_is_bound_and_bounded` |
| 13–24 | `test_sync_<objeto>` (14), `test_sync_all_objects_in_one_request` |
| 25 | `test_sync_company` (payload + hash), `test_hana_rows_are_json_serializable` |
| 26 | `test_invalid_row_is_kept_visible_and_not_promoted`, `test_schema_mismatch_fails_the_job_without_null_filling`, `test_hana_schema_mismatch_when_required_column_missing` |
| 27 | `test_unknown_company_pending_mapping`, `test_unknown_plant_pending_mapping`, `test_row_of_another_ga_company_is_not_persisted`, `test_company_without_mapping_makes_no_hana_call`, `test_company_code_outside_allowlist_is_not_queried`, `test_mapping_added_later_releases_pending_records` |
| 28 | `test_sync_*` (`staged_json`), `test_sync_production_order`, `test_sync_material_movement` |
| 29 | `test_sync_duplicate_same_hash_noop`, `test_sync_same_page_twice_no_duplicate`, `test_sync_changed_hash_versioned` |
| 30 | `test_sync_failed_batch_does_not_advance_watermark`, `test_sync_watermark_advances_after_success`, `test_sync_max_rows_cap_marks_partial_and_keeps_watermark` |
| 31 | `test_purchase_order_resync_updates_the_same_reference`, `test_purchase_order_adopts_existing_manual_reference`, `test_purchase_order_duplicate_manual_references_block_promotion` |
| 32 | `test_purchase_order_promotes_quantity`, `test_transfer_order_promotes_reference`, `test_synced_purchase_order_is_listed_for_the_reception_selector` |
| 33 | `test_purchase_order_br18_limit` + suites existentes `test_purchase_order_receipt.py`, `test_r193_oc_limit_after_reversal.py` |
| 34 | `test_hana_adapter_missing_credentials`, `test_readiness_works_without_credentials`, `test_sync_not_configured_reports_and_makes_no_hana_call`, `test_app_starts_and_serves_health_without_sap_credentials` |
| 35 | `test_connection_check_does_not_fake_a_connection`, `test_connection_check_with_fake_is_declared_simulated`, `test_connection_check_reports_auth_error` |
| 36, 37 | `test_sap_inbound_routes_rbac`, `test_sap_inbound_routes_exist_and_declare_authorization`, `test_company_code_mapping_requires_global_authority` |
| 38 | `test_sap_inbound_routes_scope_declared`, `test_sap_inbound_transaction_coverage`, suite existente `test_sap_transversal.py` |
| 39 | `test_r201_global_authority_without_context_sees_nothing`, `test_r201_company_actor_only_sees_its_company`, `test_sync_without_company_context_fails_closed`, `test_sync_is_scoped_to_the_effective_company`, suite existente `test_r201_sap_no_context.py` |

## 4 · Casos de OC exigidos (§26)

| Caso | Prueba |
|---|---|
| OC de aves macho/hembra, múltiples ítems | `test_purchase_order_promotes_quantity` |
| Recepción parcial, hasta el límite, intento de exceder | `test_purchase_order_br18_limit` |
| Reverso | `test_purchase_order_received_quantity_nets_reversals` |
| Otra empresa con el mismo `EBELN` | `test_purchase_order_cross_company_isolation` |
| Unidades incompatibles | `test_purchase_order_mixed_units_blocks_promotion` |
| Ítem borrado / OC anulada | `test_purchase_order_deleted_item_is_excluded`, `test_purchase_order_fully_deleted_becomes_inactive` |

## 5 · Mutaciones (§51) → prueba que debe fallar

| ID | Mutación | Prueba |
|---|---|---|
| S1 | el guard permite `UPDATE` | `test_hana_guard_rejects_update` |
| S2 | mismo hash inserta | `test_sync_duplicate_same_hash_noop` |
| S3 | se promueve con empresa desconocida | `test_unknown_company_pending_mapping` |
| S4 | el watermark avanza antes de persistir | `test_sync_failed_batch_does_not_advance_watermark` |
| S5 | outbound habilitado por bypass | `test_outbound_disabled` |
| S6 | filtro concatenado en vez de bind | `test_hana_client_executes_registry_sql_with_bind_parameters` |
| S7 | validación de certificado desactivada | `test_hana_adapter_tls_required` |
| S8 | `delivers_to_sap = true` | `test_delivers_to_sap_false` |

Resultados en `10_MUTATION_EVIDENCE.md`.
