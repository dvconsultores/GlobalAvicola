# Quickstart — SPEC 006

## 1 · Flujo

1. `Cargas Iniciales` → elegir BU y fecha/hora de corte → **Crear carga** (la BU queda fija en el batch).
2. **Descargar plantilla Excel** (recomendado) o **CSV** para esa BU. La hoja `Instrucciones` explica cada campo; `Catalogos` trae los códigos válidos de la empresa.
3. Completar `Datos`: vacío = desconocido · `0` = cero real · `N/A` = no aplica. Fechas `AAAA-MM-DD`. Pesos en gramos.
4. **Subir archivo** (`.xlsx` o `.csv`) → ver leídas/válidas/inválidas/UNKNOWN, errores por fila (o **Descargar errores**), corregir y volver a subir.
5. **Preview** por BU → **Enviar a aprobación** → otro usuario **Aprueba** → **Aplicar** → **Reconciliación** → enlaces a los lotes creados.
6. Registrar el primer evento del lote con fecha **posterior** al día del corte (CUT-GL-02).

## 2 · API

```text
POST /api/v1/cutover-batches                       {business_unit, cutover_datetime}
GET  /api/v1/cutover-batches · GET /cutover-batches/{id}
GET  /api/v1/cutover-templates/{bu}?format=xlsx|csv&batch_id=
POST /api/v1/cutover-batches/{id}/upload           multipart file (.xlsx|.csv)
GET  /api/v1/cutover-batches/{id}/validation · /preview · /errors?format=csv|xlsx · /items · /reconciliation
POST /api/v1/cutover-batches/{id}/submit · /approve · /reject · /apply
```

## 3 · Pruebas

```bash
cd backend && ./scripts/run_tests.sh tests/test_cutover_v2_red.py tests/test_cutover_v2_contracts.py \
  tests/test_cutover_v2_validation.py tests/test_cutover_v2_apply.py tests/test_cutover_v2_continuity.py \
  tests/test_ga_req_061_cutover_c2_lifecycle.py tests/test_ga_req_061_cutover_c4_apply.py
cd frontend && npx vitest run && npx tsc -b && npx vite build
bash scripts_e2e.sh e2e/proceso-p16-cutover-grandparent.spec.ts e2e/proceso-p16-cutover-breeder.spec.ts \
  e2e/proceso-p16-cutover-hatchery.spec.ts e2e/proceso-p16-cutover-broiler.spec.ts
```
