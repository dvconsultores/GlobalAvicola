# Feature Specification: SPEC 007 — QA Integral Synthetic Dataset and User Acceptance Pack

**Directorio**: `specs/007-qa-integral-demo-dataset` · **Rama**: `main` (sin rama nueva)
**Created**: 2026-10-18 · **Baseline**: `3e146ac` · **Status**: `LOCALLY_CERTIFIED · RUNTIME_PENDING_EXTERNAL` · R1 aplicada (2026-10-18)
**Tipo**: `QA_ENVIRONMENT_PREPARATION_SYNTHETIC_DATA_AND_UAT_GUIDE` (no modifica reglas de negocio ni arquitectura; no reabre SPEC 005/006) · **Prioridad**: P0 · **Dependencias**: SPEC 005 (inbound SAP sintetizable), SPEC 006 (Cargas Iniciales v2), GA-REM-040 (acceso por unidad), OD-16, OD-19, BR-14, BR-18, AOD-29
**Input**: Mandato Owner «PREPARACIÓN INTEGRAL DEL AMBIENTE QA CON DATA SINTÉTICA + GUÍA DE PRUEBA FUNCIONAL PARA QA — MODO AUTÓNOMO» (2026-10-18)
**Paquete de auditoría asociado**: `audit/qa-integral-dataset/01…12`
**Target**: `QA_DATA_READY=YES` · `REAL_SAP_CALLS=0` · `SAP_REAL_TEST=PENDING_2026_10_20`

---

## PURPOSE

Dejar el ambiente compartido QA/UAT **completamente poblado con datos sintéticos** —dos empresas, roles canónicos, usuarios por rol, las cuatro cadenas productivas con lotes en todas sus etapas, historia operativa de 4–8 semanas, flujo de revisión y aprobación en todos los estados, correcciones, reversos, notificaciones, cargas iniciales aplicadas y datos SAP **sintéticos**— para que una persona de QA pueda probar Global Avícola de punta a punta con una guía funcional, sin tocar SAP real y sin alterar la información existente del ambiente.

## PROBLEM / EVIDENCE

| Hecho | Evidencia |
|---|---|
| El runtime compartido solo tiene usuarios UAT sin `cutover:*`; el ciclo funcional de SPEC 006 quedó `BLOCKED_EXTERNAL` | `audit/cutover-initial-balances/16_RUNTIME_VERIFICATION.md`; commit `3e146ac` |
| Los seeds existentes son deterministas y mínimos (`baseline_seeds`, `test_seeds`, `dev_seeds`) o fixtures de escenario (`scenario_fixtures` `FX-`); ninguno cubre las 4 BU con historia, workflow completo, SAP sintético y cutover aplicado | `backend/seeds/*.py` (inventario en `research.md`) |
| No existe guía de prueba funcional para QA ni credenciales QA documentadas | `docs/` (solo `MANUAL_USUARIO.md` y `MANUAL_CARGAS_INICIALES.md`) |
| La prueba con usuario técnico SAP real está agendada para el **martes 2026-10-20**; hoy no puede ejecutarse | mandato Owner §0 |

## ARCHITECTURE_DECISION

```text
SEED_CANONICO        = backend/seeds/qa_integral_dataset.py  (CLI) + backend/seeds/qa_integral_builders.py (constructores)
DATASET_VERSION      = QA-DEMO-V1 · MARKER = QA_DEMO_V1 · PREFIX = QA- · USER_PREFIX = qa. · SAP_SOURCE = QA_SYNTHETIC
MOTOR                = servicios reales del dominio (OperationsService, ReviewService, ApprovalService, CorrectionService,
                       ReversalService, LotService, CutoverService, staging/promotion inbound). No INSERT crudo de eventos.
IDEMPOTENCIA         = claves naturales (tax_id, username, lot_code, idempotency_key=QA_DEMO_V1:<empresa>:<clave>, source_key SAP)
REMOVIBILIDAD        = --cleanup acotado a las 2 empresas QA, orden FK derivado del metadata, fail-closed (AMBIGUOUS_QA_DATA)
AISLAMIENTO          = 2 empresas propias; roles canónicos reutilizados, nunca alterados; catálogo global (fases, BU) intacto
SAP                  = inbound sintético (14 objetos HANA por staging real) con source_system=QA_SYNTHETIC; outbound no habilitado;
                       readiness real no modificado; 0 llamadas HANA
CREDENCIALES         = GA_QA_SEED_PASSWORD o archivo 0600 fuera del repo (/tmp/global_avicola_qa_credentials.txt); nunca versionadas
GUARDA DE ENTORNO    = ENVIRONMENT ∉ {development, dev, test, qa, uat, local} ⇒ ABORT; toda escritura exige --confirm-target <bd> por CLI
```

## OWNER DECISIONS (del mandato, registradas)

- OD-QA-01: no crear branch; trabajar en `main`.
- OD-QA-02: ningún dato real del cliente; ninguna credencial, conexión, llamada o escritura SAP real; SAP no se marca conectado.
- OD-QA-03: no borrar información existente del ambiente compartido; sin DROP/TRUNCATE/reset.
- OD-QA-04: cleanup implementado, probado y documentado pero **NO ejecutado** en el runtime: los datos QA deben quedar cargados.
- OD-QA-05: contraseñas QA fuera del repositorio; el manual muestra usuario/rol/empresa/BU/propósito, no la contraseña.
- OD-QA-06: la prueba SAP real es el 2026-10-20; hoy `SAP_REAL_TEST=PENDING_2026_10_20`.

## FUNCTIONAL REQUIREMENTS

- FR-01 Dos empresas QA: principal con 4 BU habilitadas; aislamiento con `breeder`+`broiler` habilitadas y `grandparent`+`hatchery` apagadas.
- FR-02 Doce usuarios `qa.*` sobre los 6 roles canónicos (ver `dataset-contract.md §3`), con concesiones de BU por empresa y un usuario `view_type=mobile`.
- FR-03 Maestros completos por empresa (granjas, galpones con 1 inactivo, incubadora con 4 incubadoras y 2 nacedoras, áreas, líneas genéticas con curva de peso, razas, proveedores, alimentos, vacunas, medicamentos, causas, transportes, plantas de beneficio, motivos de rechazo, tipos de corrección).
- FR-04 Lotes por BU en todas las etapas (cría, producción, cercano a cierre, cerrado; incubadora en recepción, incubación, ovoscopia, nacedora, nacimiento y despacho) con cadena generacional GP → incubadora → reproductora y reproductora → incubadora → engorde.
- FR-05 Historia operativa de 4–8 semanas por los servicios reales: los **28 tipos de evento** del enum aparecen al menos una vez.
- FR-06 Workflow en todos los estados internos: draft, registered, pending_review, in_review, returned, corrected, approved, rejected, consolidated, reversed, cancelled; **ninguno** sent_to_sap / sap_confirmed.
- FR-07 Correcciones con antes/después y reverso efectivo con contrapartida aprobada (BR-14 respetada: creador ≠ revisor ≠ aprobador).
- FR-08 Notificaciones leídas y no leídas (`lot_near_close` y las que el motor genera automáticamente).
- FR-09 Cargas iniciales v2 **aplicadas** para las 4 BU con un `UNKNOWN` deliberado, más 4 plantillas XLSX listas para que QA ejecute su propio ciclo.
- FR-10 Datos SAP sintéticos: 14 objetos inbound staged con `QA_SYNTHETIC`, referencias promovidas por empresa, OC coherentes con BR-18 (incluida `QA-OC-BR18-TEST`=1000 para provocar el exceso), un objeto `M_PENDING_MAPPING` y un registro `V_INVALID` como ejemplos.
- FR-11 CLI `--inventory | --apply | --verify | --cleanup` con `--dry-run`, `--run-id`, `--confirm-target`, `--manifest`, `--fixtures-dir`, `--credentials-file`, `--reset-passwords`, `--force-unmarked`.
- FR-12 `--verify` ejecuta la lista de comprobaciones del mandato §49 y devuelve `QA_DATA_VERIFY=PASS|FAIL`.
- FR-13 Guía de prueba QA (`docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md` + `.docx`) y plantilla de resultados (`.docx`), sin código, SQL ni contraseñas.

## ACCEPTANCE CRITERIA

| AC | Criterio | Verificación |
|---|---|---|
| AC-01 | `--apply` dos veces consecutivas ⇒ segunda corrida `CREATED=0` | `audit/qa-integral-dataset/06_SEED_EXECUTION_ISOLATED.md` |
| AC-02 | `--verify` ⇒ todas las comprobaciones PASS en aislado y en runtime | `06`, `09` |
| AC-03 | `--cleanup --dry-run` no escribe; `--cleanup` elimina solo entidades de las 2 empresas QA; baseline (roles, admin, empresas de certificación, fases, BU) intacto | `07_CLEANUP_PROOF.md` |
| AC-04 | Tras cleanup, `--apply` recrea el dataset (`CREATE → CLEAN → RECREATE`) | `07` |
| AC-05 | ENVIRONMENT prohibido ⇒ abort antes de abrir conexión; escritura sin `--confirm-target` ⇒ abort | `tests/test_qa_integral_dataset.py` |
| AC-06 | Ninguna contraseña literal en `seeds/qa_integral_*.py`, evidencia ni manual | test estático + revisión de evidencia |
| AC-07 | 0 llamadas SAP reales; readiness real sin cambios; `sent_to_sap`/`sap_confirmed` = 0 | `08_SAP_SYNTHETIC_SAFETY.md`, `--verify` |
| AC-08 | Regresión completa backend/frontend sin reducción de tests | `10_REGRESSION.md` |
| AC-09 | Runtime: cada usuario QA inicia sesión, ve su menú por BU y los lotes de su empresa | `09_RUNTIME_VERIFICATION.md` |
| AC-10 | Manual QA cubre cada opción de `navigationConfig.ts` con datos de prueba y resultado esperado | `QA_DATA_COVERAGE_MATRIX.md` |

## OUT OF SCOPE

Conexión/credenciales/llamadas SAP reales (2026-10-20); cambios de reglas de negocio; nuevas migraciones; nuevos roles o permisos; ejecución del cleanup en el runtime compartido.
