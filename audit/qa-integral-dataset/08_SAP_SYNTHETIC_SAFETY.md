# 08 · Seguridad SAP — datos sintéticos, 0 llamadas reales

**REAL_SAP_CALLS = 0 · SAP_REAL_TEST = PENDING_2026_10_20 · OUTBOUND = NOT_ENABLED**

## Qué hace el seed con SAP

- Construye filas con la **forma** de los 14 objetos HANA del registry (BUKRS/WERKS/MATNR/LIFNR/EBELN/… con valores `QA…`) y las pasa por `staging.stage()` real ⇒ `sap_inbound_records` con `source_system = QA_SYNTHETIC`, `sap_inbound_sync_jobs` completados con `source_system = QA_SYNTHETIC`.
- Crea `sap_entity_mappings` (MANDT 100 → `QA01`/`QA02` → `QAP1…QAP5`,`QAP9`) y promueve con `upsert_reference` ⇒ `sap_references` con `extra_data.source = QA_SYNTHETIC`.
- Deja `QAP7` en `M_PENDING_MAPPING` y `QA-MAT-INVALIDO` en `V_INVALID` como ejemplos de la bandeja.
- Consolida (interno, pre-SAP) el alimento del lote cerrado de engorde ⇒ `consolidated_movements` sin `sap_payloads`.

## Qué NO hace

- No importa ni invoca `hana_client`/conector HANA; no lee `SAP_API_URL`, `SAP_USERNAME`, `SAP_PASSWORD`, `SAP_CLIENT`.
- No toca `sap_inbound_watermarks` (0 filas creadas), ni el readiness real, ni `SAP_ENABLED`/`SAP_INTEGRATION_MODE`.
- No crea `sap_payloads`/`sap_responses`/`sap_sync_jobs`; ningún evento queda en `sent_to_sap`, `sap_confirmed` ni `sap_error` (comprobación «workflow states valid»).
- No marca SAP como conectado: la UI de Integración muestra los registros sintéticos como lo que son (`QA_SYNTHETIC`).

## Verificación

- `--verify`: «SAP refs company-scoped & synthetic» (todas `QA…` y `source=QA_SYNTHETIC`), «inbound 14 objects staged, QA_SYNTHETIC», «real SAP calls = 0» (ningún inbound en empresas QA con `source_system ≠ QA_SYNTHETIC`).
- Test estático: sin literal `"SAP_HANA_CLOUD"` en el seed.
- Inspección de código: `grep -n "hana\|SAP_API_URL\|SAP_USERNAME" seeds/qa_integral_*.py` ⇒ sin coincidencias.
