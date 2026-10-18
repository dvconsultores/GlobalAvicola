# 04 · Implementación

## Archivos versionados

| Archivo | Contenido |
|---|---|
| `backend/seeds/qa_integral_builders.py` | constantes del dataset, `USUARIOS`, `Contadores`, `Contexto`, `QaBuilder` (constructores idempotentes) |
| `backend/seeds/qa_integral_dataset.py` | CLI, guardas (`exigir_entorno_seguro`, `es_codigo_qa`), `credenciales`, `escenarios`, `fixtures_cutover`, `inventario`, `verificar`, `limpiar`, `aplicar`, manifest |
| `backend/tests/test_qa_integral_dataset.py` | 27 pruebas con `test_seed_email_domains.py` (25 propias; ver `05_TESTS.md`) |
| `specs/007-qa-integral-demo-dataset/*` | SPEC |
| `audit/qa-integral-dataset/*` | evidencia, manifest, matriz, fixtures |
| `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md` + `.docx`, `docs/QA_EXECUTION_RESULTS_TEMPLATE.docx` | guía QA |
| `backend/scripts/qa_dataset_isolated_cycle.sh` | ciclo de certificación aislada (apply #1 → apply #2 → cleanup → apply #3) |
| `tools/qa_docs/build_qa_docx.py` | generador DOCX de la guía QA |

## Código de la aplicación

**Sin cambios**: ni modelos, ni servicios, ni migraciones, ni frontend. El seed es aditivo y consume la API interna existente. Por eso la regresión completa (`10_REGRESSION.md`) se ejecuta como control, no por riesgo de cambio funcional.

## CLI

```
--inventory                 recuento de entidades QA (lectura)
--apply [--dry-run]         crea/reutiliza; exige --confirm-target <bd> (solo por CLI, sin variable de entorno);
                            --run-id, --fixtures-dir, --credentials-file, --reset-passwords, --manifest
--verify                    comprobaciones §49 → QA_DATA_VERIFY = PASS|FAIL (rc 1 si FAIL)
--cleanup [--dry-run]       borrado acotado FK-safe fail-closed; exige --confirm-target;
                            --force-unmarked <tax_id> (exige el tax_id exacto de una empresa QA)
```

## Puntos de implementación relevantes

- `QaBuilder.actor(username, company)` construye el `current_user` real (permisos del rol, `is_super_admin` solo para `*`) y fija el usuario de auditoría (`set_current_audit_user`) ⇒ los `audit_logs` llevan al usuario QA correcto.
- `QaBuilder.evento(...)` ⇒ `OperationsService.create_event` con `idempotency_key=QA_DEMO_V1:<company>:<clave>`; `aprobar=True` aplica el fastpath; `aprobar=False` deja `REGISTERED` para `flujo`.
- `QaBuilder.flujo(evento, destino)` ⇒ draft / pending_review / in_review / returned / corrected / approved / rejected por servicios reales; idempotente por estado (si ya no está `REGISTERED`, no repite).
- `QaBuilder.cerrar_lote` ⇒ `LotService.close_lot` (BR-05 + R7) y retrotrae `end_date` al histórico.
- `QaBuilder.cutover_aplicado(bu, filas)` ⇒ ciclo SPEC 006 completo (upload XLSX generado → validate → submit → approve por otro usuario → apply).
- `QaBuilder.sap_sintetico` ⇒ `stage()` real de los 14 objetos con `source_system=QA_SYNTHETIC`, mappings MANDT→BUKRS→WERKS, promoción con `upsert_reference`.
- `limpiar()` ⇒ auditoría de marcadores (fail-closed), plan por tabla con condición acotada, orden `reversed(Base.metadata.sorted_tables)`, una transacción.

## Correcciones durante el desarrollo (todas en código del seed)

1. Import de `Reversal` (vive en `app.operations.models`). 2. `cerrar_lote` faltante. 3. Prefijo `br-` vs `bro-` en la asignación de operador del lote de aprobación. 4. `sap_responses` en el plan de limpieza y orden FK derivado del metadata (`opening_balances.cutover_item_id`). 5. `es_codigo_qa` para `QAP…`. 6. Dominio de correo `.com`.

7. R1 (revisión independiente, 2026-10-18): allowlist de entornos, archivo de credenciales atómico 0600, `--force-unmarked <tax_id>`, predicados del cleanup ampliados, `sync_request_id` único, reanudación por estado en reversos y cutover; detalle en `13_INDEPENDENT_REVIEW_AND_REMEDIATION.md` y `specs/…/remediation-r1.md`.
