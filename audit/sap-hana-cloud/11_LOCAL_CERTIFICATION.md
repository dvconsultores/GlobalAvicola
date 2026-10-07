# SAP-HANA-CLOUD · 11_LOCAL_CERTIFICATION

Fecha: 2026-10-07 · SPEC 005 — SAP HANA Cloud READ ONLY Inbound · Rama `main` (sin rama nueva)
Commits: spec+RED `44785d7` · implementación **`b07d3044766f8955c9a9c1a7cf92a3207d55b053`** · certificación: ver `13_TRACEABILITY.md §5`

> Certificación **local**. Ninguna prueba tocó SAP: `REAL_SAP_CALLS = 0`, `REAL_SAP_WRITES = 0`. La certificación la emite el agente ejecutor con la evidencia de `evidence/`; el cierre formal corresponde al Owner (constitución Art. 9).

---

## 1 · Veredicto

```text
LOCAL_IMPLEMENTATION = CERTIFIED
SAP_HANA_REAL        = PENDING_CREDENTIALS
READINESS            = READY_FOR_SAP_CREDENTIALS
MISSING_EXTERNAL     = SAP_HANA_READONLY_CREDENTIALS (+ endpoint, schema, mandante y ventana de red/CA: 12_… §0)

NO DECLARADO (sin probe real): SAP_HANA_REAL_CONNECTION · SAP_HANA_REAL_RECONCILIATION
```

## 2 · Gates pre-commit (sobre el árbol que se convirtió en `b07d304`)

| Gate | Resultado | Evidencia |
|---|---|---|
| Regresión completa backend, 1.ª corrida | **3 failed / 1627 passed / 49 skipped** — guardas del arnés, no producto (ver §2.1) | `evidence/regression/backend_full_pre_commit_run1_3F_harness_guards.log` |
| FIX → verde dirigido (guardas + SPEC 005 + suites SAP) | 263 passed | `evidence/green/targeted_after_fix.log` |
| Regresión completa backend, 2.ª corrida | **1630 passed / 0 failed / 49 skipped** (22:07 min) | `evidence/regression/backend_full_pre_commit.log` |
| Frontend `vitest` | 90 archivos / **539 passed** (base 531) | `evidence/build/frontend_vitest_pre_commit.log` |
| `tsc -b` | PASS | `evidence/build/tsc_pre_commit.log` |
| `vite build` | PASS | `evidence/build/vite_build_pre_commit.log` |
| E2E fake HANA + navegación 8/8 | **14 passed** (6 + 8) | `evidence/e2e/e2e_sap_hana_inbound_pre_commit.log` |

### 2.1 · Las tres fallas de la 1.ª corrida

| Prueba | Causa | Corrección (sin cambiar reglas de negocio) |
|---|---|---|
| `test_company_catalog::test_t10_ac20_ac21_sin_migracion_y_sin_conector` | pin de la cabeza Alembic en `c8d9e0f1a2b3`; SPEC 005 añade `d9e0f1a2b3c4` | pin avanzado con nota (precedente GA-REQ-061, `4b859b2`); el resto de la prueba (`sap_config` String, `SAP_ADAPTER ∈ {manual, mock}`) intacto |
| `test_population_invariant::test_ac14_sin_migracion_ni_rutas_nuevas` | mismo pin + recuento exacto de rutas `/api` (226 → 236 por las 10 rutas inbound) | pin y recuento avanzados con nota |
| `test_time_determinism::test_t028_04_sin_fechas_literales_en_los_tests` | 7 fechas ISO literales en las pruebas nuevas de SPEC 005 | sustituidas por `tests.time_reference.iso_days_ago` (política R-28) |

`SPEC005_REGRESSION`: NO en producto; SÍ en higiene de pruebas, corregida antes del commit.

## 3 · Sensibilidad y regresión post-mutación (sobre `b07d304`)

| Gate | Resultado | Evidencia |
|---|---|---|
| S1–S8 | **8/8 DETECTED**, 1 failed exacto cada una; restauración `git restore --source=b07d304`; `FINAL_DIFF = 0` | `10_MUTATION_EVIDENCE.md`, `evidence/mutations/` |
| Regresión completa backend post-mutación | **1630 passed / 0 failed / 49 skipped** (incluye la suite dirigida de SPEC 005: 189) | `evidence/post-mutation/backend_full_post_mutation.log` |
| Frontend `vitest` | 90 / **539 passed** | `evidence/post-mutation/frontend_vitest_post_mutation.log` |
| `tsc -b` · `vite build` | PASS · PASS | `evidence/post-mutation/tsc_post_mutation.log`, `vite_build_post_mutation.log` |
| E2E fake HANA + navegación | **14 passed** | `evidence/post-mutation/e2e_post_mutation.log` |
| Migración `d9e0f1a2b3c4` | upgrade fresh (64 tablas) · `downgrade -1` (60 tablas, inbound 0, existentes intactas) · upgrade sobre esquema existente · índices y constraints presentes · 0 enums nuevos · ORM == BD | `evidence/post-mutation/migration_verification.log` |
| Arranque sin credenciales SAP | uvicorn con `env -i` (0 variables `SAP_HANA_*`): `/health` 200; readiness `PENDING_CREDENTIALS`, `configured=false`, `connection_tested=false`, `connected=false`, `outbound_enabled=false`, `write_operations_allowed=false`, `missing` = 5 nombres; sync → job `failed SAP_CONFIG_MISSING` (200, sin 500); export → 409; 0 intentos de conexión, 0 reintentos | `evidence/post-mutation/startup_without_sap_credentials.log` |
| Auditoría estática SQL | 14 `query_id` · `SAP_HANA_MUTATING_SQL = 0` · `ARBITRARY_SQL_ENDPOINTS = 0` · 19 rutas `/sap` | `evidence/green/sql_readonly_static_audit.log` |

## 4 · Objetos inbound (mandato §24)

| Objeto | Implementado | Probado | Destino |
|---|---|---|---|
| company | sí | `test_sync_company` | `STAGING_ONLY_BY_DESIGN` (Q3) |
| plant | sí | `test_sync_plant` | `PROMOTED` → `sap_references.plant` |
| storage_location | sí | `test_sync_storage_location` | `PROMOTED` → `storage_location` |
| vendor | sí | `test_sync_vendor` | `PROMOTED` → `vendor` |
| material | sí | `test_sync_material` | `PROMOTED` → `material` |
| batch | sí | `test_sync_batch` | `PROMOTED` → `sap_batch` |
| movement_type | sí | `test_sync_movement_type` | `STAGING_ONLY_BY_DESIGN` |
| purchase_order | sí | `test_sync_purchase_order`, `test_purchase_order_*` | `PROMOTED` → `purchase_order` (compuesta) |
| purchase_order_item | sí | `test_sync_purchase_order` | anidada en la OC |
| purchase_order_history | sí | `test_sync_purchase_order_history` | `STAGING_ONLY_BY_DESIGN`; alimenta `received_quantity` |
| production_order | sí | `test_sync_production_order` | `STAGING_ONLY_BY_DESIGN` |
| transfer_order | sí | `test_sync_transfer_order`, `test_transfer_order_promotes_reference` | `PROMOTED` → `transfer_order` |
| outbound_order | sí | `test_sync_outbound_order` | `STAGING_ONLY_BY_DESIGN` (fuente candidata, Q8) |
| material_movement | sí | `test_sync_material_movement` | `STAGING_ONLY_BY_DESIGN` |

## 5 · Gates funcionales

| Gate | Resultado | Pruebas |
|---|---|---|
| QUERY_REGISTRY | PASS | `test_hana_adapter_uses_readonly_registry` ×14, `test_hana_registry_is_closed` |
| SQL_READONLY_GUARD | PASS | `test_hana_guard_*` (S1) |
| TLS · CERTIFICATE_VALIDATION | PASS · PASS | `test_hana_adapter_tls_required`, `test_hana_tls_disabled_never_connects` (S7) |
| RAW · STAGING | PASS · PASS | `test_sync_*`, `test_hana_rows_are_json_serializable` |
| MAPPING_FAIL_CLOSED | PASS | `test_unknown_company_pending_mapping`, `test_unknown_plant_pending_mapping`, `test_row_of_another_ga_company_is_not_persisted` (S3) |
| IDEMPOTENCY | PASS | `test_sync_duplicate_same_hash_noop`, `test_sync_changed_hash_versioned`, `test_sync_same_page_twice_no_duplicate` (S2) |
| WATERMARK | PASS | `test_sync_failed_batch_does_not_advance_watermark`, `test_sync_watermark_advances_after_success` (S4) |
| PURCHASE_ORDER_PROMOTION | PASS | 12 pruebas en `test_sap_hana_promotion.py` |
| TRANSFER_ORDER_PROMOTION | PASS | `test_transfer_order_promotes_reference` |
| BR18_REGRESSION | PASS | `test_purchase_order_br18_limit` + `test_purchase_order_receipt.py` + `test_r193_oc_limit_after_reversal.py` (en la regresión completa) |
| RBAC | PASS | `test_sap_inbound_routes_rbac`, `…_declare_authorization`, `test_rbac.py` |
| BU_SCOPE · OD12 | PASS | `test_sap_inbound_routes_scope_declared`, `test_sap_transversal.py`, `test_business_unit_guard.py` |
| R201 | PASS | `test_r201_*` inbound + `test_r201_sap_no_context.py` |
| OD16 | PASS | `business_unit_code` informativo, sin concesión de acceso; suites OD-16 en la regresión completa |
| OUTBOUND DISABLED · DELIVERS_TO_SAP | PASS (409) · FALSE | `test_outbound_disabled`, `test_delivers_to_sap_false` (S5, S8) |
| SECRETS | 0 | escaneo del diff y de `evidence/` (DSN efímero de pgserver redactado) |

## 6 · Pruebas existentes adaptadas (sin cambio de regla)

`test_sap.py::test_export_to_sap`, `test_r201_sap_no_context.py` (04/05/06), `test_notifications.py` (09/10), `test_notification_recipients.py` (26): reabren explícitamente el outbound (`SAP_OUTBOUND_ENABLED=True` por monkeypatch) para seguir cubriendo la arquitectura de export, que el mandato apaga pero no borra. `gaFe04.sapGates.test.tsx`: «Exportar» exige `outbound.enabled`. Pines del arnés: ver §2.1.

## 7 · Deuda de código

Ninguna conocida que impida `READY_FOR_SAP_CREDENTIALS`. Límites declarados (no deuda): sync manual síncrono dentro de la petición (acotado); fuentes `CANDIDATE` a validar en P5 del runbook; UI de mappings por API (sin pantalla).

## 8 · Hallazgos laterales

- `backend/uv.lock` no incluía `openpyxl` (declarado en `pyproject.toml` desde septiembre); `uv lock` lo añadió junto con `hdbcli` (solo adiciones). La imagen Docker (`uv sync --frozen`) no instalaba `openpyxl`.
- `retry_failed` (export) marca `CONFIRMED` sin mirar `delivers_to_sap`; inalcanzable con el 409 de esta fase. Para la futura spec de outbound.
- `test_audit_coverage::test_t_081_03` busca el `audit_log` por `entity_id` sin `entity_type`: en subconjuntos de la suite colisiona con otra entidad del mismo id (pasa aislada y en la suite completa). Ajeno a SPEC 005.
