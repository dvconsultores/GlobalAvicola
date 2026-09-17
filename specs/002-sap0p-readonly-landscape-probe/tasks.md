# Tasks: SAP-0P — Read-Only Landscape Probe

**Input**: `specs/002-sap0p-readonly-landscape-probe/{spec,plan,research}.md`
**Formato extendido exigido (§14)**: `ID · SOURCE_SPEC · AC · DEPENDENCIES · ALLOWED_ACTIONS · FORBIDDEN_ACTIONS · INPUT · OUTPUT · EVIDENCE · STOP_CONDITION · STATUS`
**Regla**: ninguna tarea de implementación de producto. Probe tasks read-only; hoy la mayoría `BLOCKED_EXTERNAL` por acceso no provisionado.

---

## Fase A — Formalización y Spec Development (ejecutadas)

| ID | SOURCE_SPEC | AC | DEPENDENCIES | ALLOWED | FORBIDDEN | INPUT | OUTPUT | EVIDENCE | STOP | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| T001 | §3 mandato | AC-01 | — | escribir doc | verificar técnicamente | mandato Owner | `SAP0P_OWNER_CONFIRMATION.md` | doc | — | **DONE** |
| T002 | §10. /specify | AC-26 | T001 | crear spec | implementar | mandato + SAP-0 | `spec.md` (21 secciones, AC-01…29) | spec | — | **DONE** |
| T003 | §12 /clarify | AC-26 | T002 | clasificar preguntas | convertir técnico en Owner gate | spec | Clarifications Q1–Q7 | spec §Clarifications | — | **DONE** |
| T004 | §13 /plan | AC-26 | T002 | plan P0–P10 | iniciar probe | spec | `plan.md` + `SAP0P_PROBE_PLAN.md` | docs | — | **DONE** |
| T005 | §14 /tasks | AC-26 | T004 | crear tareas | tareas de implementación | plan | este archivo | tasks | — | **DONE** |
| T006 | §15 /analyze | AC-27 | T005 | analizar spec/plan/tasks | ejecutar probe antes de PASS | artefactos | analyze PASS (sin escritura oculta, sin queries no acotadas, sin secretos) | traceability §4 | — | **DONE** |
| T007 | §16 /converge | AC-27 | T006 | resolver inconsistencias | — | artefactos | 0 contradicciones; READ_ONLY_SAFETY=PASS | traceability §5 | — | **DONE** |

## Fase B — P0/P1 (ejecutadas en modo local, sin SAP)

| ID | SOURCE_SPEC | AC | DEPENDENCIES | ALLOWED | FORBIDDEN | INPUT | OUTPUT | EVIDENCE | STOP | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| T010 | §17 P0 | AC-28 | T007 | git status/SHA/diff; conteos de config | imprimir valores/secretos | repo | preflight PASS; PRODUCT_FILES_CHANGED=0 | `evidence/P0_PREFLIGHT_CHECK.log` | privilegios dudosos | **DONE** |
| T011 | §18 P1 | AC-02 | T010 | presencia ifaces/VPN; DNS; **sin** conectar desde red no autorizada | reconfigurar red; túnel nuevo; PSK | entorno local | canal ausente demostrado → BLOCKED | `evidence/P1_NETWORK_LOCAL_CHECK.log` | cambio destructivo de red | **DONE (BLOCKED ≠ PASS)** |
| T012 | §9 | — | T011 | clasificar y emitir acción | inventar resultados | hallazgo P1 | `SAP0P_STATUS=BLOCKED_EXTERNAL` + `SAP_ADMIN_BASIS_ACTION_REQUIRED.md` (ÚNICA) | doc + logs | — | **DONE** |

## Fase C — Probe real P2–P7 (⛔ BLOCKED_EXTERNAL — no iniciar sin acceso)

| ID | SOURCE_SPEC | AC | DEPENDENCIES | ALLOWED | FORBIDDEN | INPUT | OUTPUT | EVIDENCE | STOP | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| T020 | §19 P2 | AC-03..07 | T012 + acción Basis cumplida | metadata read-only | procedimientos desconocidos; elevar privilegios | canal + cuenta RO | identidad/versiones | `evidence/P2_*.log` | permisos no seguros | **BLOCKED_EXTERNAL** |
| T021 | §20 P3 | AC-08 | T020 | verificar SELECT-only por metadata | write test escribiendo | cuenta RO | `SAP0P_PERMISSION_ASSESSMENT` | idem | privilegios excesivos | **BLOCKED_EXTERNAL** |
| T022 | §21 P4 | AC-09..16 | T020 | metadata de 9 tablas | SELECT * alto volumen | catálogo | disponibilidad/estructura | `evidence/P4_*.log` | schema irreconciliable | **BLOCKED_EXTERNAL** |
| T023 | §22 P5 | AC-17 | T022 | muestras ≤10 filas filtradas | dumps; datos personales | tablas | muestras estructurales | `evidence/P5_*.log` | query no acotable | **BLOCKED_EXTERNAL** |
| T024 | §23 P6 | AC-21 | T023 | reconciliar 12 objetos | importar al dominio | muestras | `SAP0P_INBOUND_OBJECT_VERIFICATION` | idem | — | **BLOCKED_EXTERNAL** |
| T025 | §24–25 | AC-18 | T023 | verificar MANDT/BUKRS/WERKS/T001L | convergencia real; LGORT=GALPÓN automático | muestras | `SAP0P_OD24_*`, `SAP0P_STORAGE_LOCATION_FINDINGS` | idem | mapeo ambiguo → PENDING_MAPPING | **BLOCKED_EXTERNAL** |
| T026 | §26–29 | — | T022 | verificar MATNR/BWART/PO/MATDOC estructura | asumir vigencia de códigos; full scan MATDOC | catálogo | hallazgos clasificados | idem | — | **BLOCKED_EXTERNAL** |
| T027 | §30–31 P7 | AC-19,20 | T020 | discovery no mutante (WSDL/metadata/GET) | POST SOAP; invocación negocio | endpoints | estado OData/CDS/SOAP/Z-service | `evidence/P7_*.log` | efectos laterales | **BLOCKED_EXTERNAL** |
| T028 | §36–37 P8 | AC-24 | T020..T027 | registrar evidencia saneada | secretos/dumps | resultados | query register completo | `evidence/**` | fuga de secretos | **PARCIAL** (solo P0/P1) |
| T029 | §13 P9 | — | T028 | cerrar sesión/ruta | persistir credenciales | sesión | acta cierre | `evidence/P9_*.log` | residuos | **N/A** (sin sesión) |
| T030 | §42 P10 | AC-25,27 | T029 | certificar lo demostrado | redondear hacia arriba | todo | `SAP0P_READONLY_PROBE_CERTIFICATION.md` | doc | — | **DONE (certifica bloqueo)** |

## Fase D — Verificación / Git (ejecutadas)

| ID | SOURCE_SPEC | AC | DEPENDENCIES | ALLOWED | FORBIDDEN | INPUT | OUTPUT | EVIDENCE | STOP | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| T040 | §44 | AC-28 | T030 | verificaciones locales | modificar producto | repo | VERIFICATION_REPORT | doc | producto tocado → no commit | **DONE** |
| T041 | §46 | AC-29 | T040 | stage explícito + commit + push | `git add .`/`-A`/force | artefactos | commit `audit/sap0p` + `specs/002-*` | git log | — | **DONE** |
| T042 | §46 | AC-29 | T041 | `ls-remote` compare | reset/rewrite | remoto | `REMOTE_SHA_MATCH=PASS` | salida §49 | mismatch | **DONE** |

## Trazabilidad AC→Tarea (resumen)

AC-01→T001 · AC-02→T011,T012 · AC-03..07→T020 · AC-08→T021 · AC-09..16→T022 · AC-17→T023 · AC-18→T025 · AC-19,20→T027 · AC-21→T024 · AC-22..24→T010,T028 · AC-25→T030 · AC-26→T002..T005 · AC-27→T006,T007,T030 · AC-28→T040 · AC-29→T041,T042.

## SAP-1 scope proposal (NO iniciar — §41)
Propuesta a derivar de la evidencia futura: SAP-1 = inbound masters read-only (Company, Plant, Storage Location, Vendor, Material); SAP-2 = documentos (PO/PO items/history, STO, MATDOC, Batches, Cost Centers). **Estado: PROPOSED_NOT_STARTED** (bloqueada por acceso).
