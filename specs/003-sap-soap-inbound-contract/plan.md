# Implementation Plan: SAP-SOAP-1 — SOAP Inbound Contract

**Feature**: `specs/003-sap-soap-inbound-contract` · **Fecha**: 2026-09-22
**Tipo**: SPEC ONLY — sin implementación, sin conexiones, sin cambios de producto.

---

## 1 · Technical Context

- **Entregable**: contrato completo para el proveedor SAP (SOAP server) + diseño del consumo en GA (SOAP client).
- **Lado GA (futuro)**: Python/FastAPI; nuevo `SapInboundAdapter` + `SoapSapAdapter` (diseñados, no implementados); RAW/STAGING en PostgreSQL; jobs de extracción.
- **Lado SAP (proveedor)**: servicio SOAP ABAP contra `03_…`/`04_…`/`05_…`.
- **Restricciones de esta fase**: prohibido implementar, conectar SAP/HANA/SOAP, tocar `backend/frontend/e2e/.github`, deploy; solo `specs/**`, `audit/sap-soap/**` y docs SAP estrictamente necesarios.

## 2 · Constitution / Safety Check

| Principio | Cumplimiento |
|---|---|
| NO SPEC = NO DEVELOPMENT | ✔ contrato antes de cualquier código |
| Honestidad de estados | ✔ `REAL SAP INTEGRATION = NOT IMPLEMENTED` intacto; GA-REM-010 intacto |
| Fail-closed multiempresa | ✔ diseñado (`10_… §4`) |
| Sin secretos | ✔ ejemplos con placeholders; prohibiciones explícitas (`08_…`) |
| Anti-hardcode legacy | ✔ anexo con `DO_NOT_REUSE` (`11_…`) |
| PRODUCT_FILES_CHANGED=0 | ✔ verificación git |

## 3 · Fases (SOAP-1…SOAP-8 — §41 del mandato)

| Fase | Contenido | Esta ejecución | Prerrequisito |
|---|---|---|---|
| **SOAP-1** | Contrato delgado + SPEC + anexos | **COMPLETADA (docs)** | — |
| SOAP-2 | Mock del contrato (fixtures XML + validador + cliente local) | PLANNED | SOAP-1 (listo) |
| SOAP-3 | `SoapSapAdapter` implementado contra mock | PLANNED | SOAP-2 |
| SOAP-4 | RAW/STAGING + jobs de ingesta | PLANNED | SOAP-3 |
| SOAP-5 | Sandbox con proveedor SAP | PLANNED | OI-01/06/15 + SOAP-3 |
| SOAP-6 | Prueba read-only contra servicio real | PLANNED | SOAP-5 |
| SOAP-7 | Reconciliación end-to-end | PLANNED | SOAP-6 |
| SOAP-8 | Certificación | PLANNED | SOAP-7 |

## 4 · Estructura de entregables (esta fase)

```
audit/sap-soap/
  01_SAP_SOAP_ARCHITECTURE_DECISION.md     09_SAP_SOAP_DELTA_PAGINATION_SPEC.md
  02_SAP_SOAP_INBOUND_SCOPE.md             10_SAP_SOAP_RAW_STAGING_MAPPING.md
  03_SAP_SOAP_OPERATION_CATALOG.md         11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP.md
  04_SAP_SOAP_FIELD_CATALOG.md             12_SAP_SOAP_GA_ADAPTER_CHANGE_SPEC.md
  05_SAP_SOAP_WSDL_XSD_REQUIREMENTS.md     13_SAP_SOAP_PROVIDER_OPEN_ITEMS.md
  06_SAP_SOAP_REQUEST_RESPONSE_EXAMPLES.md 14_SAP_SOAP_IMPLEMENTATION_READINESS.md
  07_SAP_SOAP_ERROR_CONTRACT.md            15_SAP_SOAP_SPEC_TRACEABILITY.md
  08_SAP_SOAP_SECURITY_CONTRACT.md
specs/003-sap-soap-inbound-contract/  spec.md · plan.md · tasks.md · research.md
docs/  Especificacion_Tecnica_Integracion_SOAP_SAP_Global_Avicola_Lider_Pollo.md (cliente-facing)
       addendum en 10-sap-integration-strategy.md (OData → SUPERSEDED…)
audit/sap0|sap0p/  addenda de pointer (SOAP decision)
```

## 5 · Verificación (§49) y Git

1. `git diff` vacío en backend/frontend/e2e/.github; sin migraciones; sin deploy.
2. Sin secretos en artefactos (revisión por patrón).
3. Consistencia SPEC↔PLAN↔TASKS↔ACs (`15_… §2–4`).
4. Stage explícito de rutas acordadas; commit + push; `LOCAL_SHA == REMOTE_SHA`.

## 6 · Riesgos

| Riesgo | Mitigación |
|---|---|
| WSDL del proveedor difiere | diff obligatorio vs `04/05_…` antes de aceptar |
| Contaminación del enfoque legacy | anexo con clasificación y advertencia expresa |
| Scope creep (outbound/cost centers) | fuera de alcance explícito; otra SPEC |
| Rotura del export existente | interfaz inbound separada; garantías `12_… §4` |
