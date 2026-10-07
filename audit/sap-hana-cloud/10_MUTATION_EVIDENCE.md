# SAP-HANA-CLOUD · 10_MUTATION_EVIDENCE

Fecha: 2026-10-07 · SPEC 005 · Sensibilidad S1–S8 (mandato §51) · `IMPLEMENTATION_COMMIT = b07d3044766f8955c9a9c1a7cf92a3207d55b053`

Protocolo (`audit/remediation/MUTATION_CHECKPOINT_GOVERNANCE.md`): la sensibilidad corre **después** del commit de implementación, con el árbol productivo limpio y bajo `backend/scripts/mutation_guard.py` (7 señales). Cada mutación se instala en el archivo productivo, se ejecuta la prueba que debe enrojecer y se restaura con `git restore --source=<IMPLEMENTATION_COMMIT> -- <archivo>`, comprobando byte a byte y `git diff --exit-code`. Las mutaciones no se commitean ni forman parte del producto. Logs: `evidence/mutations/S1..S8.log`, `SENSITIVITY_SUMMARY.log`, `driver_output.log`.

## 1 · Resultados

| ID | Mutación | Archivo | Prueba objetivo | Esperado | Observado | DETECTED | Restauración |
|---|---|---|---|---|---|---|---|
| S1 | el guard permite UPDATE (se retiran los tokens UPDATE y SET) | `backend/app/integrations/sap/inbound/sql_guard.py` | `test_hana_guard_rejects_update` | la prueba falla | `1 failed in 0.25s` | **YES** | `git restore --source=b07d304` · diff 0 |
| S2 | misma clave + mismo hash inserta en lugar de no-op | `backend/app/integrations/sap/inbound/service.py` | `test_sync_duplicate_same_hash_noop` | la prueba falla | `1 failed, 1 warning in 1.75s` | **YES** | `git restore --source=b07d304` · diff 0 |
| S3 | se acepta una sociedad sin mapping (promoción con empresa desconocida) | `backend/app/integrations/sap/inbound/mapping.py` | `test_unknown_company_pending_mapping` | la prueba falla | `1 failed, 1 warning in 1.74s` | **YES** | `git restore --source=b07d304` · diff 0 |
| S4 | el watermark avanza antes de persistir el batch (fuera del savepoint) | `backend/app/integrations/sap/inbound/service.py` | `test_sync_failed_batch_does_not_advance_watermark` | la prueba falla | `1 failed, 1 warning in 1.74s` | **YES** | `git restore --source=b07d304` · diff 0 |
| S5 | bypass: se ignora SAP_OUTBOUND_ENABLED=false | `backend/app/integrations/sap/service.py` | `test_outbound_disabled` | la prueba falla | `1 failed, 1 warning in 2.41s` | **YES** | `git restore --source=b07d304` · diff 0 |
| S6 | el filtro de sociedad se concatena al SQL en lugar de ir como bind | `backend/app/integrations/sap/inbound/client.py` | `test_hana_client_executes_registry_sql_with_bind_parameters` | la prueba falla | `1 failed in 0.27s` | **YES** | `git restore --source=b07d304` · diff 0 |
| S7 | validación de certificado desactivada | `backend/app/integrations/sap/inbound/settings.py` | `test_hana_adapter_tls_required` | la prueba falla | `1 failed in 0.26s` | **YES** | `git restore --source=b07d304` · diff 0 |
| S8 | delivers_to_sap = True en el adaptador manual | `backend/app/integrations/sap/adapter.py` | `test_delivers_to_sap_false` | la prueba falla | `1 failed, 1 warning in 2.13s` | **YES** | `git restore --source=b07d304` · diff 0 |

Correspondencia con el mandato §51: S1 guard/`UPDATE` · S2 same-hash → insert · S3 promoción con empresa desconocida · S4 watermark antes del commit · S5 bypass de `SAP_OUTBOUND_ENABLED` · S6 bind → concatenación · S7 validación de certificado · S8 `delivers_to_sap=true`.

## 2 · Notas de construcción

- **S1** retira los dos tokens de una sentencia `UPDATE` (`UPDATE` y `SET`): con solo `UPDATE` la segunda capa del guard (`SET`) seguía bloqueando y la mutación habría sido inválida (protocolo: reconstruir con las capas necesarias). Se registra como mutación de capa completa.
- **S3** es observable gracias a un refuerzo de `test_unknown_company_pending_mapping` hecho antes del commit de implementación: además del centro desconocido (que la capa de centros seguiría reteniendo), la prueba inyecta un proveedor —objeto sin centro— cuya única barrera es la sociedad.
- **S4** avanza el watermark fuera del savepoint y antes de extraer; la prueba observa que la marca cambió aunque el batch falló.
- **S8** muta `ManualSapAdapter.delivers_to_sap` (el adaptador outbound vigente); el inbound no declara entrega alguna.
- Primera corrida del driver: veredictos idénticos, pero el log guardaba la cola de `stderr` sin el resumen de pytest; se corrigió el driver y se repitió S1–S8 íntegra antes de la regresión post-mutación (sin commits intermedios; `FINAL_DIFF = 0` en ambas).

## 3 · Restauración explícita

```text
FINAL_RESTORE_SHA = b07d3044766f8955c9a9c1a7cf92a3207d55b053
FINAL_DIFF = 0   (git diff --exit-code <sha> -- backend/app frontend/src backend/alembic)
ÁRBOL PRODUCTIVO TRAS LA SENSIBILIDAD = LIMPIO
MUTATION = PASS
```

## 4 · Regresión post-mutación

Ver `11_LOCAL_CERTIFICATION.md §3` y `evidence/post-mutation/`.
