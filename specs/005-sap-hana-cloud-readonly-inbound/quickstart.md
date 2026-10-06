# Quickstart — SPEC 005

## 1 · Arrancar sin credenciales (estado por defecto)

No hay que configurar nada. Con `FEATURE_SAP_ENABLED=true`:

```bash
curl -s -H "Authorization: Bearer $TOKEN" $API/sap/inbound/readiness
# → "configured": false, "missing": ["SAP_HANA_HOST", "SAP_HANA_USER", ...], "write_operations_allowed": false
```

El backend arranca, el scheduler no corre y ninguna ruta llama a HANA.

## 2 · Variables

```text
SAP_HANA_HOST=            SAP_HANA_PORT=443           SAP_HANA_USER=           SAP_HANA_PASSWORD=
SAP_HANA_SCHEMA=          SAP_HANA_CLIENT=            SAP_HANA_ENCRYPT=true    SAP_HANA_SSL_VALIDATE_CERTIFICATE=true
SAP_HANA_SSL_TRUST_STORE= SAP_HANA_CONNECT_TIMEOUT_SECONDS=10                  SAP_HANA_QUERY_TIMEOUT_SECONDS=60
SAP_HANA_PAGE_SIZE=500    SAP_HANA_MAX_ROWS_PER_SYNC=20000                     SAP_HANA_DEFAULT_LOOKBACK_DAYS=30
SAP_HANA_SYNC_ENABLED=false                           SAP_HANA_SYNC_INTERVAL_SECONDS=3600
SAP_HANA_COMPANY_CODES=   SAP_HANA_PLANTS=            SAP_HANA_LANGUAGE=S      SAP_HANA_DRIVER=hdbcli
SAP_OUTBOUND_ENABLED=false
```

Los valores reales van solo en el entorno del servidor, nunca en el repositorio.

## 3 · Desarrollo local con fake HANA

```bash
export SAP_HANA_DRIVER=fake SAP_HANA_HOST=fake.invalid SAP_HANA_USER=fake SAP_HANA_PASSWORD=fake \
       SAP_HANA_SCHEMA=SAPFAKE SAP_HANA_CLIENT=100
```

`fake` solo se acepta con `ENVIRONMENT` en `development` o `test`. Readiness lo declara `simulated: true`.

## 4 · Mapear y sincronizar

```bash
# 1) la autoridad global, situada en la empresa, enlaza la sociedad SAP
curl -X PUT $API/sap/inbound/mappings -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"entity_type":"COMPANY_CODE","sap_key":"1000"}'
# 2) el analista mapea los centros
curl -X PUT $API/sap/inbound/mappings ... -d '{"entity_type":"PLANT","sap_key":"1100","parent_sap_key":"1000"}'
# 3) sincronizar todo, o un objeto
curl -X POST $API/sap/inbound/sync ... -d '{}'
curl -X POST $API/sap/inbound/sync/purchase_order ... -d '{"date_from":"2026-09-01","date_to":"2026-10-06"}'
# 4) revisar
curl $API/sap/inbound/jobs ...; curl $API/sap/inbound/errors ...; curl "$API/sap/references?ref_type=purchase_order" ...
```

## 5 · Pruebas

```bash
cd backend && ./scripts/run_tests.sh tests/test_sap_hana_guard.py \
  tests/test_sap_hana_client.py tests/test_sap_hana_sync.py tests/test_sap_hana_promotion.py tests/test_sap_hana_routes.py
cd backend && ./scripts/run_tests.sh                       # regresión completa
cd frontend && npx vitest run && npx tsc -b && npx vite build
bash scripts_e2e.sh e2e/sap-hana-inbound.spec.ts e2e/navigation-consistency.spec.ts
```

## 6 · Activación real

Ver `audit/sap-hana-cloud/12_REAL_SAP_ACTIVATION_RUNBOOK.md`. Hasta ejecutar ese probe el estado es `SAP_HANA_REAL = PENDING_CREDENTIALS`.
