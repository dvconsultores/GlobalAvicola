# Feature Specification: SAP-0 — Landscape Discovery + Inbound Data Contract

**Feature Branch**: `specs/001-sap0-landscape-discovery`
**Created**: 2026-09-17
**Status**: Draft → Validated (SPEC ONLY — no implementation)
**Input**: Mandato Owner «SAP-0 — LANDSCAPE DISCOVERY + INBOUND DATA CONTRACT» (2026-09-17)
**Alcance**: Especificación y documentación. **Prohibida toda implementación, conexión SAP, VPN, consulta HANA, llamada SOAP/OData/IDoc/RFC/BAPI, y todo cambio en `backend/**`, `frontend/**`, `e2e/**`, `.github/workflows/**`.**

---

## Propósito

Convertir el conocimiento disponible (repositorio legacy `SapHanaLP` como **evidencia de discovery**, arquitectura SAP actual del producto, specs previas) en:

1. Un **contrato de datos inbound** formal para los 12 objetos SAP que Global Avícola necesita consumir.
2. Un **marco de decisión de conectividad** (opciones formales comparadas) y la definición —sin implementación— de una **capa SAP Bridge** aislada.
3. Un **diseño de capas RAW/STAGING**, deltas y reconciliación, y de **convergencia** para empresas/granjas (OD-24).
4. Un **plan de discovery ejecutable** (probe read-only P0–P6) con el request formal a SAP Basis, listo para autorización del Owner.

## Contexto y estado actual (verificado en esta fase)

- Producto actual: adaptador SAP (`SapIntegrationAdapter`) con implementaciones `manual` y `mock` únicamente; `SAP_ADAPTER=real` → `NO IMPLEMENTADO (GA-REM-017)`; sin `RealSapAdapter` (verificado en `backend/app/integrations/sap/adapter.py`).
- `sap_references` espeja 8 tipos SAP (PO, STO, MATERIAL, VENDOR, PLANT, STORAGE_LOCATION, COST_CENTER, SAP_BATCH); solo `PURCHASE_ORDER` se consume (BR-18).
- Legacy `SapHanaLP`: conexión VPN L2TP/IPsec embebida + `hdbcli` directo a HANA (`SAPHANADB`, puerto 30241 hardcodeado), ETL por temp-tables a PostgreSQL, 1 servicio SOAP Z (`ZwsTasaMortalidad`), scheduling 06/10/14/18 h; múltiples hardcodes; `verify=False`. **Todo esto queda como evidencia, no como arquitectura.**
- Decisiones funcionales abiertas relevantes: `AOD-01…05` (export), `AOD-06`/`OD-24` (empresas/granjas), `AOD-12` (secretos), `GL-OD-06` (go-live).

## Escenarios de usuario (fases futuras habilitadas por esta spec)

- **US1 — Owner/Basis**: responder el request de información y autorizar el probe; a cambio recibe un plan acotado, seguro y auditable (P0–P6). (Prioridad P1)
- **US2 — Analista de integración**: usar el catálogo de 12 objetos para validar campos disponibles en SAP y cerrar el contrato por objeto. (P1)
- **US3 — Arquitectura**: decidir el mecanismo (SAP-CONN-01) con la matriz de 13 dimensiones y la propuesta del Bridge; sin exponer backend ni dominio. (P2)
- **US4 — Data/ETL**: implementar (fase posterior) extracción RAW, validación, staging y promoción conforme a contratos definidos aquí. (P2, bloqueada)
- **US5 — Auditoría/Certificación**: verificar trazabilidad COMPLETA de SAP-0 sin conexión SAP ni cambios de producto. (P1)

## Requirements

- **FR-001**: Documentar la auditoría del repo legacy con evidencia por hallazgo (`SOURCE_FILE`, `LOCATION`, `VALUE`, `USE`, `PROCESS`, `CLASSIFICATION`, `CURRENT_VALIDITY`).
- **FR-002**: Separar explícitamente `LEGACY_FACT` vs `CURRENT_SAP_FACT` (hoy: sin evidencia current; todo `UNKNOWN`).
- **FR-003**: Inventariar tablas SAP, campos, procesos y **hardcodes** legacy con `TARGET_TREATMENT` (SAP_MASTER_DATA / CONFIGURATION / REFERENCE_MAPPING / OWNER_DECISION / CURRENT_SAP_VALIDATION / REMOVE).
- **FR-004**: Catálogo formal de los **12 objetos inbound** con los 14 campos del mandato §14.
- **FR-005**: Matriz SOURCE→CANONICAL (legacy→GA actual) y gaps.
- **FR-006**: Estrategia de convergencia empresas/granjas (OD-24) con estados `MATCH/CONFLICT/MISSING_IN_SAP/MISSING_IN_GA/DUPLICATE/MANUAL_REVIEW_REQUIRED`.
- **FR-007**: Comparación formal de opciones de conectividad (Direct HANA RO, OData, CDS, SOAP, IDoc, RFC/BAPI, SAP Cloud Connector, SFTP) sobre 13 dimensiones.
- **FR-008**: Definición de **SAP Bridge** (aislado, least privilege) — **sin implementar**.
- **FR-009**: Contrato RAW (16 campos canónicos) y separación RAW/STAGING/CANÓNICO/AUDITORÍA; prohibición de escritura directa a dominio.
- **FR-010**: Estrategia snapshot/delta/watermark por objeto; reconciliación R1–R4; cuarentena; política `UNKNOWN` y fail-closed multi-compañía.
- **FR-011**: Plan de discovery P0–P6 (allowed/forbidden/evidence/stop por fase) + request a SAP Basis (20 puntos, sin passwords).
- **FR-012**: Registro de decisiones Owner/Basis (solo gates reales) con clasificación.
- **FR-013**: Reevaluación de `GA-REM-017` por clase de bloqueo, preservando `REAL SAP INTEGRATION = NOT IMPLEMENTED`.
- **FR-014**: Resultado de `GL-OD-06` conforme §38: `READY_FOR_OWNER_DECISION` o `BLOCKED_EXTERNAL_SAP_INFORMATION`.
- **FR-015**: Trazabilidad de la cadena spec-development (specify→clarify→plan→tasks→analyze→converge) con PASS/FAIL por paso.

## Key Entities

- **Inbound Object Contract** (12): SAP_COMPANY, SAP_PLANT, SAP_STORAGE_LOCATION, SAP_VENDOR, SAP_MATERIAL, SAP_PURCHASE_ORDER, SAP_PURCHASE_ORDER_ITEM, SAP_PURCHASE_ORDER_HISTORY, SAP_TRANSFER_ORDER, SAP_MATERIAL_DOCUMENT, SAP_BATCH, SAP_COST_CENTER.
- **RAW Record** (16 campos: source_system, sap_system_id, mandant, company_code, object_type, source_primary_key, source_version, raw_payload, payload_hash, extracted_at, ingested_at, sync_job_id, watermark, validation_status, mapping_status, error_code/error_detail).
- **Convergence State** (6 estados) · **Owner/Basis Gate** (12 gates SAP-0) · **Probe Phase** (P0–P6).

## Out of Scope (prohibiciones del mandato, verificables)

Implementación de cualquier componente; conexión a SAP; VPN; consultas HANA reales; SOAP/OData/IDoc/RFC/BAPI; añadir `hdbcli`; crear `RealSapAdapter`; importación/limpieza/cutover de datos; tocar `backend/**`, `frontend/**`, `e2e/**`, `.github/workflows/**`; iniciar G1/G2; `/implement`.

## Acceptance Criteria (AC-SAP0-01…21)

| AC | Criterio | Evidencia en |
|---|---|---|
| AC-SAP0-01 | Mecánicas de conexión del legacy identificadas y documentadas | `SAP_LEGACY_REPOSITORY_AUDIT.md §3` (T-01…T-05) |
| AC-SAP0-02 | Tablas SAP legacy inventariadas con campos/uso | `SAP_LEGACY_REPOSITORY_AUDIT.md §4` |
| AC-SAP0-03 | Hardcodes legacy inventariados con tratamiento destino | `SAP_LEGACY_REPOSITORY_AUDIT.md §6` |
| AC-SAP0-04 | Separación LEGACY vs CURRENT-SAP explicitada (current=UNKNOWN) | `SAP_LEGACY_TO_CURRENT_MAPPING_MATRIX.md §1–2` |
| AC-SAP0-05 | 12 objetos inbound catalogados (14 campos cada uno) | `SAP_INBOUND_DATA_CATALOG.md` |
| AC-SAP0-06 | Matriz SOURCE→CANONICAL producida | `SAP_LEGACY_TO_CURRENT_MAPPING_MATRIX.md` |
| AC-SAP0-07 | Estrategia de convergencia OD-24 especificada | `SAP_COMPANY_FARM_CONVERGENCE_SPEC.md` |
| AC-SAP0-08 | Cuestión LGORT↔galpón registrada como decisión pendiente | `SAP_OWNER_DECISIONS_REQUIRED.md` (SAP-STO-01) |
| AC-SAP0-09 | Materiales/BWART NO convertidos en reglas automáticas | `SAP_INBOUND_DATA_CATALOG.md` (ob.5, ob.10) |
| AC-SAP0-10 | Comparación formal de conectividad (8 opciones × 13 dims) | `SAP_CONNECTIVITY_OPTIONS_ANALYSIS.md` |
| AC-SAP0-11 | SAP Bridge definido y NO implementado | `SAP_BRIDGE_ARCHITECTURE_PROPOSAL.md` (status DEFINED_NOT_IMPLEMENTED) |
| AC-SAP0-12 | RAW/STAGING separados con contrato de 16 campos | `SAP_RAW_STAGING_SPEC.md §1–2` |
| AC-SAP0-13 | Snapshot/delta/watermark por objeto especificado | `SAP_RAW_STAGING_SPEC.md §4` |
| AC-SAP0-14 | Reconciliación R1–R4 y cuarentena especificadas | `SAP_RAW_STAGING_SPEC.md §5–6` |
| AC-SAP0-15 | Multi-compañía fail-closed especificado | RAW §3 + Convergencia §5 |
| AC-SAP0-16 | GA-REM-017 reevaluado por bloqueo; `NOT IMPLEMENTED` preservado | `SAP_GA_REM_017_RECLASSIFICATION.md` |
| AC-SAP0-17 | GL-OD-06 con estado resultante y trazable | `SAP0_SPEC_DEVELOPMENT_TRACEABILITY.md` + `SAP_GA_REM_017_RECLASSIFICATION.md` |
| AC-SAP0-18 | Cero intentos de conexión SAP/VPN/consultas | `SAP0_VERIFICATION_REPORT.md §2` |
| AC-SAP0-19 | Cero archivos de producto modificados | `SAP0_VERIFICATION_REPORT.md §3` (`git diff` backend/frontend/e2e/workflows vacío) |
| AC-SAP0-20 | SPEC/PLAN/TASKS consistentes tras analyze | `SAP0_SPEC_DEVELOPMENT_TRACEABILITY.md §4` (SPEC_CONSISTENCY=PASS) |
| AC-SAP0-21 | Converge sin contradicciones técnicas + commit remoto verificado | `SAP0_SPEC_DEVELOPMENT_TRACEABILITY.md §5` + `SAP0_VERIFICATION_REPORT.md §6` (LOCAL_SHA==REMOTE_SHA) |

## Clarifications (sesión 2026-09-17 — respuestas registradas)

- **Q: ¿El probe P0–P6 se ejecuta en SAP-0?** A: No. Solo se especifica; requiere `SAP0_PROBE_AUTHORIZATION` + `SAP-BASIS-01`. Impacto: AC-SAP0-18 verificable hoy (0 intentos).
- **Q: ¿Se documentan credenciales/valores de `.env` del legacy?** A: No; jamás. Se citan nombres de variables como patrón, nunca valores. Impacto: verificación de secretos = PASS.
- **Q: ¿Los hallazgos legacy se asumen vigentes en SAP actual?** A: No; `CURRENT_VALIDITY=UNKNOWN` salvo evidencia current (que no existe). Impacto: FR-002, `GL-OD-06=BLOCKED_EXTERNAL_SAP_INFORMATION`.
- **Q: ¿Se toma ya la decisión de mecanismo de conexión?** A: No; depende de SAP-BASIS-01/probe; se registra matriz + recomendación condicionada. Impacto: `SAP-CONN-01 PENDING`.
- **Q: ¿Se implementa el SAP Bridge o el contrato RAW?** A: No; solo se definen (prohibición de implementación). Impacto: AC-SAP0-11/12.
- **Q: ¿Número de feature?** A: `001` (primera feature numerada del repo; `specs/` no contiene features numeradas). Directorio único `specs/001-sap0-landscape-discovery/`.
