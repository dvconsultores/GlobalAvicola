# ÍNDICE DE SPECS DE REMEDIACIÓN

Todas creadas el 2026-09-03 como `POST-AUDIT REMEDIATION SPEC`. Ninguna pretende haber existido antes.

| ID | Título | Tipo | Prior. | Estado | Fase | Documento |
|---|---|---|---|---|---|---|
| `GA-REM-001` | Gobierno de Spec Development | GOVERNANCE | P0 | **`CERTIFIED`** | A | [GA-REM-001](GA-REM-001-SPEC-DEVELOPMENT-GOVERNANCE.md) |
| `GA-REM-014` | Entorno de test backend aislado | INFRASTRUCTURE | P0 | **`CERTIFIED`** | F→adelantada | [GA-REM-014](GA-REM-014-ISOLATED-TEST-ENVIRONMENT.md) |
| `GA-REM-004` | Credenciales y cuentas de prueba | SECURITY | P0 | **`CERTIFIED`** (informe 2026-09-03) | B | [GA-REM-004](GA-REM-004-CREDENTIALS-AND-TEST-ACCOUNTS.md) |
| `GA-REM-009` | Persistencia de evidencias y archivos | INFRASTRUCTURE | P0 | **`CERTIFIED`** (volumen `avicola-media`) | D | [GA-REM-009](GA-REM-009-EVIDENCE-PERSISTENCE.md) |
| `GA-REM-010` | Semántica de estados SAP | INTEGRATION SEMANTICS | P0 | **`CERTIFIED`** (AC01–AC06) | D | [GA-REM-010](GA-REM-010-SAP-STATE-SEMANTICS.md) |
| `GA-REM-005` | Mortalidad y balance de aves (+ enmienda `R-67` · **enmienda B: el saldo nunca es negativo, `R-130`**) | BUGFIX + BUSINESS RULE | P0 | **`CERTIFIED`** (+ enm. B **`CERTIFIED`** 2026-09-09, frontera técnica; E2E `BLOCKED_RUNTIME`) | C | [GA-REM-005](GA-REM-005-MORTALITY-AND-BIRD-BALANCE.md) |
| `GA-REM-007` | BR-14: segregación y centralización de reglas (+ **enm. A: corrector/rechazador ≠ aprobador, `R-143`**) | BUSINESS RULE | P0 | **`CERTIFIED`** · enm. A **`CERTIFIED`** (2026-09-09, frontera técnica) | C | [GA-REM-007](GA-REM-007-BR14-SEGREGATION-CENTRALIZATION.md) |
| `GA-REM-011` | Alineación de contratos FE ↔ BE | CONTRACT | P0 | **`PARTIALLY CERTIFIED`** (10/18; `H360-C01` → alcance restante) | E | [GA-REM-011](GA-REM-011-FE-BE-CONTRACT-ALIGNMENT.md) |
| `GA-REM-012` | Cambio de contraseña | SECURITY + BUGFIX | P0 | **`CERTIFIED`** | B | [GA-REM-012](GA-REM-012-PASSWORD-CHANGE.md) |
| `GA-REM-002` | RBAC: enforcement en backend (+ enm. A: `AC12` · enm. B: administración de usuarios de inquilino · **enm. C: `OD-14.c/d` en el dato productivo, `R-139`**) | SECURITY | P0 | **`CERTIFIED`** (+ enm. B 2026-09-08 · **enm. C `CERTIFIED` 2026-09-09**) | B | [GA-REM-002](GA-REM-002-RBAC-BACKEND-ENFORCEMENT.md) |
| `GA-REM-003` | Contexto de autorización y ciclo del token | SECURITY | P0 | **`CERTIFIED`** | B | [GA-REM-003](GA-REM-003-AUTH-CONTEXT-AND-TOKEN-LIFECYCLE.md) |
| `GA-REM-006` | Correcciones e integridad del dato (+ **enm. A: continuidad de estados de `P-07`, `R-135` · `R-140` A · `R-154` parte**) | DATA INTEGRITY | P0 | **`CERTIFIED`** · enm. A **`CERTIFIED`** (2026-09-09, frontera técnica) | C | [GA-REM-006](GA-REM-006-CORRECTIONS-DATA-INTEGRITY.md) |
| `GA-REM-008` | Trazabilidad generacional | DOMAIN + BUGFIX | P0 | **`CERTIFIED`** | C | [GA-REM-008](GA-REM-008-GENERATIONAL-TRACEABILITY.md) |
| `GA-REM-013` | Quality gates de CI (sin tocar deployment) | PROCESS | P1 | **`CERTIFIED`** (`H360-T01` → enmienda pendiente: CI sin `FEATURE_SAP_ENABLED`) | F | [GA-REM-013](GA-REM-013-QUALITY-GATES.md) |
| `GA-REM-021` | Brechas de captura exigidas por el cliente | REQUIREMENT GAP | P1 | `SPEC_READY` — alcance ampliado por `H360-B01…B04`, `B13`, `R-156` | C | [GA-REM-021](GA-REM-021-CLIENT-REQUIRED-DATA-GAPS.md) |
| `GA-REM-022` | Completitud de KPI | FUNCTIONAL GAP | P1 | `PARTIAL` — enm. A certificada (`P-15`); alcance base abierto + `R-131…R-134`, `R-141` | E | [GA-REM-022](GA-REM-022-KPI-COMPLETENESS.md) |
| `GA-REM-023` | Persistencia de campos de evento y contrato de error | DATA INTEGRITY + API CONTRACT | **P0** | **`CERTIFIED`** | — | [GA-REM-023](GA-REM-023-EVENT-FIELD-PERSISTENCE-AND-ERROR-CONTRACT.md) |
| `GA-REM-020` | Validación de cobertura funcional contra la documentación del cliente | VALIDATION | P1 | **`CERTIFIED`** | A | [GA-REM-020](GA-REM-020-FUNCTIONAL-COVERAGE-VALIDATION.md) |
| `GA-REM-015` | Certificación de tests de backend | QA | P1 | **`CERTIFIED`** | F | [GA-REM-015](GA-REM-015-BACKEND-TEST-CERTIFICATION.md) |
| `GA-REM-016` | Certificación E2E y de procesos | QA + CERTIFICATION | P1 | `SPEC_DRAFT` — **en uso** por 15 informes de certificación; pasar a `SPEC_READY` en `WAVE F` (`R-149`) | G | [GA-REM-016](GA-REM-016-E2E-AND-PROCESS-CERTIFICATION.md) |
| `GA-REM-018` | Recuperación de trazabilidad Spec Development | METHODOLOGY | P1 | `SPEC_READY` | I | [GA-REM-018](GA-REM-018-SPEC-TRACEABILITY-RECOVERY.md) |
| `GA-REM-017` | Integración SAP real | INTEGRATION | P1 | **`BLOCKED_EXTERNAL`** | H | [GA-REM-017](GA-REM-017-SAP-REAL-INTEGRATION.md) |
| `GA-REM-019` | Reevaluación de deuda P2/P3 | TECHNICAL DEBT | P2 | `DEFERRED` | J | [GA-REM-019](GA-REM-019-P2-P3-DEBT-REASSESSMENT.md) |
| `GA-REM-024` | Ejecución de migraciones antes de servir | INFRASTRUCTURE + RELEASE SAFETY | **P0** | **`CERTIFIED`** (arranque real; `R-58` sin rastro abierto en el backlog) | — | [GA-REM-024](GA-REM-024-MIGRATION-ON-DEPLOY.md) |
| `GA-REM-025` | Baseline limpio del entorno compartido | ENVIRONMENT + TEST DATA STRATEGY | P1 | **`CERTIFIED`** | — | [GA-REM-025](GA-REM-025-CLEAN-DEVELOPMENT-BASELINE.md) |
| `GA-REM-026` | Frontera transaccional de la petición | DATA INTEGRITY + REQUEST LIFECYCLE | **P0** | **`CERTIFIED`** | — | [GA-REM-026](GA-REM-026-TRANSACTION-BOUNDARY.md) |
| `GA-REM-027` | Resolución del upstream en el proxy | RUNTIME CONFIGURATION | **P0** | **`PARTIALLY CERTIFIED`** | — | [GA-REM-027](GA-REM-027-PROXY-UPSTREAM-RESOLUTION.md) |
| `GA-REM-028` | Fecha de inicio del lote | DOMAIN SEMANTICS + BUGFIX | P1 | **`CERTIFIED`** | — | [GA-REM-028](GA-REM-028-LOT-START-DATE.md) |
| `GA-REM-029` | Contrato de cierre de lote | CONTRACT + BUSINESS RULE | P1 | **`CERTIFIED`** | — | [GA-REM-029](GA-REM-029-LOT-CLOSURE-CONTRACT.md) |
| `GA-REM-030` | Pertenencia en los vínculos de trazabilidad | TENANCY HARDENING | P2 | **`CERTIFIED`** | — | [GA-REM-030](GA-REM-030-TRACEABILITY-LINK-OWNERSHIP.md) |
| `GA-REM-031` | Creación del vínculo generacional desde la recepción | DOMAIN DEFECT | P1 | **`CERTIFIED`** | — | [GA-REM-031](GA-REM-031-RECEPTION-LINEAGE-CREATION.md) |
| `GA-REM-032` | Cobertura de auditoría y contrato de consulta | DOMAIN + CONTRACT | P1 | **`CERTIFIED`** | — | [GA-REM-032](GA-REM-032-AUDIT-COVERAGE-AND-QUERY-CONTRACT.md) |
| `GA-REM-033` | Gestión de datos maestros (+ enmienda A: catálogo seguro de empresas, `R-127`) | CAPABILITY + CONTRACT | P1 | **`CERTIFIED`** (+ enm. A **`CERTIFIED`** 2026-09-09) | — | [GA-REM-033](GA-REM-033-MASTER-DATA-MANAGEMENT.md) |
| `GA-REM-034` | Administración de roles y permisos | CAPABILITY | P1 | **`CERTIFIED`** | — | [GA-REM-034](GA-REM-034-ROLE-ADMINISTRATION.md) |
| `GA-REM-035` | Recepción contra orden de compra | BUSINESS RULE ACTIVATION | P1 | **`CERTIFIED`** | — | [GA-REM-035](GA-REM-035-PURCHASE-ORDER-RECEIPT-LIMIT.md) |
| `GA-REM-036` | Aprobación obligatoria antes del cierre de lote | BUSINESS RULE | P1 | **`CERTIFIED`** | — | [GA-REM-036](GA-REM-036-LOT-CLOSE-APPROVAL-GUARD.md) |
| `GA-REM-037` | Curvas estándar de peso y alerta por desviación (+ enmienda A: capacidad de producto) | CAPABILITY | P1 | **`CERTIFIED`** | — | [GA-REM-037](GA-REM-037-GENETIC-WEIGHT-CURVES.md) |
| `GA-REM-038` | Notificaciones internas (+ enmiendas A y B) | CAPABILITY | P1 | **`CERTIFIED`** | — | [GA-REM-038](GA-REM-038-INTERNAL-NOTIFICATIONS.md) |
| `GA-REM-039` | Áreas funcionales | DOMAIN MODEL | P1 | **`CERTIFIED`** | — | [GA-REM-039](GA-REM-039-FUNCTIONAL-AREAS.md) |
| `GA-REM-040` | Acceso por unidad de negocio (+ enms. A–F · **enm. G: la unidad se exige al operar sobre `operations`, `R-160`/`R-159`** · **enm. H: la habilitación de la empresa es absoluta — `lots` y descarga, `R-163`/`R-162`**) | ACCESS CONTROL | P0 | `IN_PROGRESS` — fases 1–8 **`CERTIFIED`** · enms. G y H **`CERTIFIED`** (2026-09-09, frontera técnica) · fase 9 `TECHNICALLY READY · FROZEN` (`R-127` y `R-139` cerrados) · fases 10–11 pendientes · precisada por `OD-16` | — | [GA-REM-040](GA-REM-040-BUSINESS-UNIT-ACCESS-CONTROL.md) |

## Decisiones normativas

No son specs de remediación y no cuentan en el total: fijan el marco en el que las specs
se interpretan.

| ID | Título | Estado | Documento |
|---|---|---|---|
| `ENV-01` | Clasificación de entorno — el desplegado es compartido de desarrollo/test/certificación, no producción | **VIGENTE** | [ENV-01](ENV-01-ENVIRONMENT-CLASSIFICATION.md) |
| `OD-09` | Plano de control frente a unidad de negocio — visibilidad de control y acceso operativo son capacidades distintas (+ enm. A: la concesión pertenece a usuario + empresa + unidad · enm. B: volver no reactiva) | **VIGENTE** | [OD-09](OD-09-CONTROL-PLANE-VS-BUSINESS-UNIT.md) |
| `OD-10` | Contrato de traspaso entre unidades y clasificación pendiente — entre unidades solo pasa el contrato | **VIGENTE** | [OD-10](OD-10-HANDOFF-CONTRACT-AND-PENDING-CLASSIFICATION.md) |
| `OD-11` | La empresa efectiva de una petición — una reclamación en el token no es autoridad | **VIGENTE** | [OD-11](OD-11-EFFECTIVE-COMPANY-CONTEXT.md) |
| `OD-12` | La transversalidad del contrato SAP — capacidad operativa explícita y acotada | **VIGENTE** | [OD-12](OD-12-SAP-TRANSVERSAL-CONTRACT.md) |
| `OD-13` | La propiedad de roles y permisos — el permiso es de producto, el rol tiene alcance | **VIGENTE** | [OD-13](OD-13-ROLE-AND-PERMISSION-TENANCY.md) |
| `OD-14` | Control global frente a contexto de inquilino — `switch-company` elige inquilino, no retira autoridad | **VIGENTE** | [OD-14](OD-14-GLOBAL-CONTROL-VS-TENANT-CONTEXT.md) |
| `OD-15` | Segregación en la administración de acceso — quien reparte no se sirve a sí mismo | **VIGENTE** | [OD-15](OD-15-ACCESS-ADMINISTRATION-SEGREGATION.md) |
| `OD-16` | Alcance productivo vigente y activación de unidades por empresa — cuatro unidades, cada razón social las enciende o apaga en Global Avícola; encender ≠ conceder | **VIGENTE** · requisito de producto | [OD-16](OD-16-PRODUCT-SCOPE-AND-COMPANY-BUSINESS-UNIT-ACTIVATION.md) |
| `OD-17` | Un rechazo corregible no es terminal — `RETURNED`/`REJECTED` se corrigen y reenvían; con SAP, reenvío explícito (alias `AOD-09`) | **VIGENTE** · implementación `WAVE B` | [OD-17](OD-17-CORRECTABLE-REJECTION-IS-NOT-TERMINAL.md) |
| `OD-18` | El catálogo general de empresas no contiene configuración SAP — `sap_config` fuera de `GET /masters/companies`; persistencia diferida (alias `AOD-12`) | **VIGENTE** · gobierna `R-127` | [OD-18](OD-18-COMPANY-CATALOG-EXCLUDES-SAP-CONFIGURATION.md) |

## Resumen
```
Total ................. 40
CERTIFIED ............. 31
PARTIALLY CERTIFIED ... 2     (011 · 027)
PARTIAL ............... 1     (022)
SPEC_READY ............ 2     (018 · 021)
SPEC_DRAFT ............ 1     (016, en uso)
IN_PROGRESS ........... 1     (040: fases 1–8 certificadas · fase 9 bloqueada)
BLOCKED_EXTERNAL ...... 1     (017)
DEFERRED .............. 1     (019)
```

> **Reconciliación del 2026-09-09 (WAVE A0-G).** Diez estados de este índice contradecían los
> informes de certificación que enlazan (`DOCUMENT_AUTHORITY_AND_SUPERSESSION_MATRIX.md §2`):
> `004`, `009`, `010`, `011`, `013`, `020`, `022`, `002`, `024`, `040`. Se corrigen al estado que
> tienen, con la evidencia citada en la celda. Ningún estado se eleva sin informe.

> **Deriva de registro corregida el 2026-09-06.** Las specs `GA-REM-028`…`GA-REM-037` se
> crearon y certificaron entre el 2026-09-04 y el 2026-09-06 sin darse de alta aquí, de modo
> que este índice declaraba 27 specs cuando el repositorio tenía 37. Se añaden con el estado
> que tienen, no con el que habrían tenido al crearse.

## Specs nuevas respecto al índice propuesto en el encargo
| ID | Motivo |
|---|---|
| `GA-REM-020` | hallazgo **R-15**: la documentación funcional del cliente nunca se usó para validar la implementación. **Informa**, no bloquea: la taxonomía del proyecto se conserva |
| `GA-REM-021` | hallazgo **R-13**: el consumo de agua, exigido por el cliente en 3 etapas, no se captura |
| `GA-REM-022` | hallazgo **R-14**: la Tasa de Eclosión devuelve texto; 4 KPI implementados sin consumidor |

Ninguna spec del encargo se ha eliminado. `GA-REM-019` absorbe el bloque «P2/P3 posterior a estabilización».

## Hallazgos de auditoría → backlog oficial (2026-09-09)

| Origen | Reconciliación | IDs |
|---|---|---|
| Master 360 (`H360-*`, 65) + addendum (`H360A-*`, 10) | `audit/remediation/H360_AND_ADDENDUM_TO_OFFICIAL_BACKLOG_RECONCILIATION.md` · 0 sin disposición | 28 nuevos `R-130…R-157` · 20 mapeados a IDs existentes |
| Decisiones formalizadas | `OD-16` (requisito de producto) · `OD-17` (`AOD-09`) · `OD-18` (`AOD-12`) | pendientes: `AOD-01…08`, `10`, `11`, `13…16` · `BU-D10` `PENDING_RATIFICATION` |

### Asignación por olas (vigente tras la reconciliación)

| Ola | Contenido |
|---|---|
| **A** autoridad · seguridad · datos | ~~`R-127`~~ **CERRADO** (`WAVE A1`, `OD-18`) · ~~`R-139`~~ **CERRADO** (`GA-REM-002-C`, 2026-09-09) · `R-149` documental · `GA-REM-013` enm. (`H360-T01`, `R-158` tsc) — **WAVE A COMPLETE** en su alcance de seguridad/datos |
| **B** procesos faltantes | ~~`R-130`~~ **CERRADO** (tranche 1, `GA-REM-005-B`) · ~~`R-160`~~ ~~`R-159`~~ **CERRADOS** (tranche 2, `GA-REM-040-G`) · ~~`R-163`~~ ~~`R-162`~~ **CERRADOS** (tranche 3, `GA-REM-040-H`) · ~~`R-135`~~ ~~`R-143`~~ **CERRADOS** (tranche 4, `GA-REM-006-A`/`007-A`; `R-140`/`R-154` parciales; registrados `R-164` · `R-165` · `R-166`) · `R-135` (`OD-17`) · `R-161` · `R-136` · `R-140` · `R-142` · `R-143` · `R-144` · `R-147` · `R-148` · `R-152` · `R-153` · `R-154` · `R-156` · `GA-REM-021` (+ `H360-B01…B04`, `B13`) |
| **C** KPI · trazabilidad | `R-131` · `R-132` · `R-133` · `R-134` · `R-141` · `GA-REM-022` (`H360-K10`) · `R-80` (`H360-B09`) |
| **D** preparación SAP | `R-137` (`AOD-03`) · `R-138` · `R-145` · `R-155` (`AOD-15`) · `R-157` (`AOD-01…05`) · `R-124` (`AOD-06`) |
| **E** frontend · UX | fase 9 de `GA-REM-040` (tras `R-127` y `R-139`) · `R-98`/`R-119` · `R-146` · `R-150` · `R-151` · `R-122` · `R-123` · `GA-REM-011` (`H360-C01`) |
| **F** certificación | E2E en `main` · `GA-REM-016` → `SPEC_READY` · fases 10–11 de `GA-REM-040` (`H360A-05`, `BU 0/15`) · evidencia `P-01` (`H360A-04`) · `R-83` |
| **G** SAP real | `GA-REM-017` · `P-08` · `AOD-07` |
