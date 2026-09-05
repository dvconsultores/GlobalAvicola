# ÍNDICE DE SPECS DE REMEDIACIÓN

Todas creadas el 2026-09-03 como `POST-AUDIT REMEDIATION SPEC`. Ninguna pretende haber existido antes.

| ID | Título | Tipo | Prior. | Estado | Fase | Documento |
|---|---|---|---|---|---|---|
| `GA-REM-001` | Gobierno de Spec Development | GOVERNANCE | P0 | **`CERTIFIED`** | A | [GA-REM-001](GA-REM-001-SPEC-DEVELOPMENT-GOVERNANCE.md) |
| `GA-REM-014` | Entorno de test backend aislado | INFRASTRUCTURE | P0 | **`CERTIFIED`** | F→adelantada | [GA-REM-014](GA-REM-014-ISOLATED-TEST-ENVIRONMENT.md) |
| `GA-REM-004` | Credenciales y cuentas de prueba | SECURITY | P0 | `SPEC_READY` | B | [GA-REM-004](GA-REM-004-CREDENTIALS-AND-TEST-ACCOUNTS.md) |
| `GA-REM-009` | Persistencia de evidencias y archivos | INFRASTRUCTURE | P0 | `SPEC_READY` | D | [GA-REM-009](GA-REM-009-EVIDENCE-PERSISTENCE.md) |
| `GA-REM-010` | Semántica de estados SAP | INTEGRATION SEMANTICS | P0 | `SPEC_READY` | D | [GA-REM-010](GA-REM-010-SAP-STATE-SEMANTICS.md) |
| `GA-REM-005` | Mortalidad y balance de aves (+ enmienda `R-67`) | BUGFIX + BUSINESS RULE | P0 | **`CERTIFIED`** | C | [GA-REM-005](GA-REM-005-MORTALITY-AND-BIRD-BALANCE.md) |
| `GA-REM-007` | BR-14: segregación y centralización de reglas | BUSINESS RULE | P0 | **`CERTIFIED`** | C | [GA-REM-007](GA-REM-007-BR14-SEGREGATION-CENTRALIZATION.md) |
| `GA-REM-011` | Alineación de contratos FE ↔ BE | CONTRACT | P0 | `SPEC_READY` | E | [GA-REM-011](GA-REM-011-FE-BE-CONTRACT-ALIGNMENT.md) |
| `GA-REM-012` | Cambio de contraseña | SECURITY + BUGFIX | P0 | **`CERTIFIED`** | B | [GA-REM-012](GA-REM-012-PASSWORD-CHANGE.md) |
| `GA-REM-002` | RBAC: enforcement en backend | SECURITY | P0 | **`IMPLEMENTED`** ⚠ R-44 | B | [GA-REM-002](GA-REM-002-RBAC-BACKEND-ENFORCEMENT.md) |
| `GA-REM-003` | Contexto de autorización y ciclo del token | SECURITY | P0 | **`CERTIFIED`** | B | [GA-REM-003](GA-REM-003-AUTH-CONTEXT-AND-TOKEN-LIFECYCLE.md) |
| `GA-REM-006` | Correcciones e integridad del dato | DATA INTEGRITY | P0 | **`CERTIFIED`** | C | [GA-REM-006](GA-REM-006-CORRECTIONS-DATA-INTEGRITY.md) |
| `GA-REM-008` | Trazabilidad generacional | DOMAIN + BUGFIX | P0 | **`CERTIFIED`** | C | [GA-REM-008](GA-REM-008-GENERATIONAL-TRACEABILITY.md) |
| `GA-REM-013` | Quality gates de CI (sin tocar deployment) | PROCESS | P1 | `SPEC_READY` | F | [GA-REM-013](GA-REM-013-QUALITY-GATES.md) |
| `GA-REM-021` | Brechas de captura exigidas por el cliente | REQUIREMENT GAP | P1 | `SPEC_READY` | C | [GA-REM-021](GA-REM-021-CLIENT-REQUIRED-DATA-GAPS.md) |
| `GA-REM-022` | Completitud de KPI | FUNCTIONAL GAP | P1 | `SPEC_READY` | E | [GA-REM-022](GA-REM-022-KPI-COMPLETENESS.md) |
| `GA-REM-023` | Persistencia de campos de evento y contrato de error | DATA INTEGRITY + API CONTRACT | **P0** | **`CERTIFIED`** | — | [GA-REM-023](GA-REM-023-EVENT-FIELD-PERSISTENCE-AND-ERROR-CONTRACT.md) |
| `GA-REM-020` | Validación de cobertura funcional contra la documentación del cliente | VALIDATION | P1 | `SPEC_READY` | A | [GA-REM-020](GA-REM-020-FUNCTIONAL-COVERAGE-VALIDATION.md) |
| `GA-REM-015` | Certificación de tests de backend | QA | P1 | **`CERTIFIED`** | F | [GA-REM-015](GA-REM-015-BACKEND-TEST-CERTIFICATION.md) |
| `GA-REM-016` | Certificación E2E y de procesos | QA + CERTIFICATION | P1 | `SPEC_DRAFT` | G | [GA-REM-016](GA-REM-016-E2E-AND-PROCESS-CERTIFICATION.md) |
| `GA-REM-018` | Recuperación de trazabilidad Spec Development | METHODOLOGY | P1 | `SPEC_READY` | I | [GA-REM-018](GA-REM-018-SPEC-TRACEABILITY-RECOVERY.md) |
| `GA-REM-017` | Integración SAP real | INTEGRATION | P1 | **`BLOCKED_EXTERNAL`** | H | [GA-REM-017](GA-REM-017-SAP-REAL-INTEGRATION.md) |
| `GA-REM-019` | Reevaluación de deuda P2/P3 | TECHNICAL DEBT | P2 | `DEFERRED` | J | [GA-REM-019](GA-REM-019-P2-P3-DEBT-REASSESSMENT.md) |
| `GA-REM-024` | Ejecución de migraciones antes de servir | INFRASTRUCTURE + RELEASE SAFETY | **P0** | **`IMPLEMENTED`** ⚠ `R-58` | — | [GA-REM-024](GA-REM-024-MIGRATION-ON-DEPLOY.md) |
| `GA-REM-025` | Baseline limpio del entorno compartido | ENVIRONMENT + TEST DATA STRATEGY | P1 | **`CERTIFIED`** | — | [GA-REM-025](GA-REM-025-CLEAN-DEVELOPMENT-BASELINE.md) |
| `GA-REM-026` | Frontera transaccional de la petición | DATA INTEGRITY + REQUEST LIFECYCLE | **P0** | **`CERTIFIED`** | — | [GA-REM-026](GA-REM-026-TRANSACTION-BOUNDARY.md) |
| `GA-REM-027` | Resolución del upstream en el proxy | RUNTIME CONFIGURATION | **P0** | **`PARTIALLY CERTIFIED`** | — | [GA-REM-027](GA-REM-027-PROXY-UPSTREAM-RESOLUTION.md) |

## Decisiones normativas

No son specs de remediación y no cuentan en el total: fijan el marco en el que las specs
se interpretan.

| ID | Título | Estado | Documento |
|---|---|---|---|
| `ENV-01` | Clasificación de entorno — el desplegado es compartido de desarrollo/test/certificación, no producción | **VIGENTE** | [ENV-01](ENV-01-ENVIRONMENT-CLASSIFICATION.md) |

## Resumen
```
Total ................. 27
CERTIFIED ............. 12
PARTIALLY CERTIFIED ... 1
IMPLEMENTED ........... 2
SPEC_READY ............ 9
SPEC_DRAFT ............ 1
BLOCKED_EXTERNAL ...... 1
DEFERRED .............. 1
```

## Specs nuevas respecto al índice propuesto en el encargo
| ID | Motivo |
|---|---|
| `GA-REM-020` | hallazgo **R-15**: la documentación funcional del cliente nunca se usó para validar la implementación. **Informa**, no bloquea: la taxonomía del proyecto se conserva |
| `GA-REM-021` | hallazgo **R-13**: el consumo de agua, exigido por el cliente en 3 etapas, no se captura |
| `GA-REM-022` | hallazgo **R-14**: la Tasa de Eclosión devuelve texto; 4 KPI implementados sin consumidor |

Ninguna spec del encargo se ha eliminado. `GA-REM-019` absorbe el bloque «P2/P3 posterior a estabilización».
