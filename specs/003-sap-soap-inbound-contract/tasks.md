# Tasks: SAP-SOAP-1 — SOAP Inbound Contract

**Input**: `specs/003-sap-soap-inbound-contract/{spec,plan,research}.md`
**Formato (§42)**: `ID · SPEC · AC · DEPENDENCY · OWNER · INPUT · OUTPUT · TEST · EVIDENCE · STATUS`
**Regla**: `IMPLEMENTATION_REQUIRED = NO` para toda esta ejecución (SPEC only).

---

## Fase A — Formalización y contrato (ejecutadas)

| ID | SPEC | AC | DEPENDENCY | OWNER | INPUT | OUTPUT | TEST | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| T001 | §2 | AC-01 | — | GA | decisión de reunión | `01_…ARCHITECTURE_DECISION` | revisión vs §2 del mandato | doc | **DONE** |
| T002 | §5–6 | AC-05 | T001 | GA | SAP-0 + REQ cliente | `02_…INBOUND_SCOPE` (13 objetos) | cobertura de prioridades §6 | doc | **DONE** |
| T003 | §7–8–9 | AC-07 | T002 | GA | objetos | `03_…OPERATION_CATALOG` (12+1) | request/response común + matriz | doc | **DONE** |
| T004 | §10–20 | AC-06 | T003 | GA | campos legacy + requisitos GA | `04_…FIELD_CATALOG` | R/O por campo; claves; delta | doc | **DONE** |
| T005 | §33 | AC-19 | T003 | GA | catálogo | `05_…WSDL_XSD_REQUIREMENTS` | criterios W-01…06 | doc | **DONE** |
| T006 | §34 | AC-08 | T004 | GA | campos | `06_…EXAMPLES` (6 ops + fault) | XML bien formado conceptual | doc | **DONE** |
| T007 | §31 | AC-09 | T003 | GA | escenarios error | `07_…ERROR_CONTRACT` | lista cerrada + retry | doc | **DONE** |
| T008 | §29 | — | T001 | GA | requisitos seguridad | `08_…SECURITY_CONTRACT` | S-01…S-07 + opciones auth | doc | **DONE** |
| T009 | §24–25–30 | AC-10/11 | T003 | GA | volúmenes | `09_…DELTA_PAGINATION_SPEC` | token/límite/ventana | doc | **DONE** |
| T010 | §26–27–28 | AC-12/13/14 | T004 | GA | SAP-0 RAW spec | `10_…RAW_STAGING_MAPPING` | idempotencia + fail-closed | doc | **DONE** |
| T011 | §21–23 | AC-15/16 | — | GA | `querysHana.py` (evidencia SAP-0) | `11_…LEGACY_QUERY_REFERENCE_FOR_ABAP` | clasificación + expreso «query≠contrato» | doc | **DONE** |
| T012 | §35–36 | AC-17/18 | T001 | GA | `adapter.py` actual | `12_…GA_ADAPTER_CHANGE_SPEC` | interfaz separada; export intacto | doc | **DONE** |
| T013 | §40 | — | T003 | GA | dudas técnicas | `13_…PROVIDER_OPEN_ITEMS` (16 OIs + OD) | separación por responsable | doc | **DONE** |
| T014 | §41 | — | T013 | GA | fases | `14_…IMPLEMENTATION_READINESS` | matriz SOAP-2…8 | doc | **DONE** |

## Fase B — Spec development (ejecutadas)

| ID | SPEC | AC | DEPENDENCY | OWNER | INPUT | OUTPUT | TEST | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| T020 | §38 | AC-01…20 | T014 | GA | paquete | `specs/003-…/spec.md` (24 secciones) | AC-SOAP-01…20 | spec | **DONE** |
| T021 | §40 | — | T020 | GA | preguntas | Clarifications Q1–Q8 | clasificación GA/Proveedor/Owner | spec | **DONE** |
| T022 | §41 | — | T020 | GA | fases | `plan.md` | fases y prerrequisitos | plan | **DONE** |
| T023 | §42 | — | T022 | GA | plan | este `tasks.md` | trazabilidad AC→tarea | tasks | **DONE** |
| T024 | §43 | — | T023 | GA | artefactos | analyze PASS (§15_… §3) | 11 categorías = 0 defectos | traceability | **DONE** |
| T025 | §44 | — | T024 | GA | analyze | converge PASS (§15_… §4) | 0 contradicciones abiertas | traceability | **DONE** |
| T026 | §46–47 | — | T020 | GA | spec final | doc cliente-facing + addendum `docs/10` + addenda SAP-0/0P | coherencia sin decisiones abiertas como hechos | docs | **DONE** |
| T027 | §49 | AC-20 | T026 | GA | repo | commit + push + SHA verify | `PRODUCT_FILES_CHANGED=0`; SHA match | git | **DONE** |

## Fase C — Futuras (PLANNED — NO iniciar)

| ID | Fase | AC futuro | DEPENDENCY | OWNER | OUTPUT | TEST | STATUS |
|---|---|---|---|---|---|---|---|
| T101 | SOAP-2 Mock contract | mock ACs | T027 | GA | fixtures XML + validador + cliente local | ejecución local sin SAP | **PLANNED** |
| T102 | SOAP-3 SoapSapAdapter | adapter ACs | T101 | GA | adaptador contra mock | suite de contrato | **PLANNED** |
| T103 | SOAP-4 RAW/STAGING | ingesta ACs | T102 | GA | jobs + RAW | idempotencia/duplicados | **PLANNED** |
| T104 | SOAP-5 Sandbox proveedor | sandbox ACs | T102 + OI-01/06/15 | Proveedor+GA | entorno integrado | handshake TLS/auth | **PLANNED** |
| T105 | SOAP-6 Prueba real RO | prueba ACs | T104 | GA+Proveedor | evidencia de lectura real | muestras acotadas | **PLANNED** |
| T106 | SOAP-7 Reconciliación | R1–R4 | T105 | GA | informes | discrepancias controladas | **PLANNED** |
| T107 | SOAP-8 Certificación | cert ACs | T106 | GA | certificado | — | **PLANNED** |

## Trazabilidad resumen AC→tarea

AC-01→T001 · 02→T001 · 03→T001 · 04→T001 · 05→T002 · 06→T004 · 07→T003 · 08→T006 · 09→T007 · 10→T009 · 11→T009 · 12→T010 · 13→T010 · 14→T010 · 15→T011 · 16→T011 · 17→T012 · 18→T012 · 19→T005 · 20→T027.
