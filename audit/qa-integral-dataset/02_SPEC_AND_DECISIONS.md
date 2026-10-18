# 02 · SPEC y decisiones — SPEC 007

SPEC: `specs/007-qa-integral-demo-dataset/` (spec, plan, tasks, research, data-model, dataset-contract, cleanup-contract, qa-test-matrix, quickstart). Sin rama nueva.

## Decisiones Owner registradas (del mandato 2026-10-18)

| ID | Decisión | Cumplimiento |
|---|---|---|
| OD-QA-01 | No crear branch | trabajo en `main` |
| OD-QA-02 | Sin datos reales, sin credenciales/conexión/llamadas/escrituras SAP reales; SAP no se marca conectado | `source_system=QA_SYNTHETIC`; `REAL_SAP_CALLS=0`; readiness/outbound intactos |
| OD-QA-03 | No borrar información existente; sin DROP/TRUNCATE/reset | el seed es aditivo; el cleanup está acotado a las empresas QA y no se ejecuta en runtime |
| OD-QA-04 | Cleanup implementado+probado+documentado, NO ejecutado en runtime | `07_CLEANUP_PROOF.md` (aislado) · estado `READY_NOT_EXECUTED` |
| OD-QA-05 | Contraseñas fuera del repo; el manual no las muestra | `GA_QA_SEED_PASSWORD` / archivo 0600; test estático |
| OD-QA-06 | Prueba SAP real el 2026-10-20 | `SAP_REAL_TEST=PENDING_2026_10_20` |

## Decisiones técnicas del orquestador (sin alterar reglas de negocio)

1. **Un seed canónico** (`qa_integral_dataset.py` + `qa_integral_builders.py`) sobre la arquitectura existente; nada de INSERT crudo de eventos.
2. **Fastpath auditado** solo para la historia aprobada (`QA_HISTORY_FASTPATH`): `APPROVED` + `ApprovalAction` + transición auditada; el workflow demostrativo recorre `OperationsService → ReviewService → ApprovalService` reales con BR-14.
3. **«Operador» ⇒ `Operador de Granja`** (único rol operador canónico). `Administrador de Accesos` sin usuario QA (no tiene alcance productivo); los 6 roles restantes tienen al menos un usuario.
4. **Empresa de aislamiento** con `grandparent` y `hatchery` apagadas para probar OD-16 y multiempresa.
5. **Centros SAP `QAP1…`** (WERKS de 4 caracteres) reconocidos como QA por `es_codigo_qa`.
6. **Confirmación de destino** obligatoria en toda escritura (`--confirm-target <bd>`): no hay override silencioso.
7. **Orden de borrado derivado del metadata** y test de cobertura FK, en vez de una lista mantenida a mano.
8. **Dominio de correo** `qa.globalavicola.com` (la guarda F3/GA-FE-02-B rechaza `.local`).
