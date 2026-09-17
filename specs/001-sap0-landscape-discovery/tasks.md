# Tasks: SAP-0 — Landscape Discovery + Inbound Data Contract

**Input**: `specs/001-sap0-landscape-discovery/spec.md` + `plan.md`
**Prerrequisitos**: ninguno de código. **Regla**: `IMPLEMENTATION_REQUIRED = NO` para toda la fase SAP-0 (salvo verificación); las tareas futuras están `BLOCKED_BY_SAP0`.
**Formato**: `[ID] [P?] [Story] Descripción → evidencia/AC`

---

## Phase 1: Discovery (SAP-0) — ✅ COMPLETADA

**Goal**: Extraer y clasificar la evidencia legacy + estado actual del producto, sin conectarse a nada.

- [x] T001 [US5] Auditar repo legacy `dvconsultores/SapHanaLP` (read-only, sin clone): archivos, arquitectura, conexión, driver, tablas, procesos, hardcodes → `audit/sap0/SAP_LEGACY_REPOSITORY_AUDIT.md` (AC-01,02,03)
- [x] T002 [P] [US5] Inventariar SOAP/Z-services legacy (`ZwsTasaMortalidad`, endpoint/auth/TLS) → `SAP_LEGACY_REPOSITORY_AUDIT.md §7` (AC-01)
- [x] T003 [P] [US5] Inventariar hardcodes con `TARGET_TREATMENT` (18 filas) → `SAP_LEGACY_REPOSITORY_AUDIT.md §6` (AC-03)
- [x] T004 [US5] Separar `LEGACY_FACT` vs `CURRENT_SAP_FACT` (current=UNKNOWN) y mapear a GA actual → `SAP_LEGACY_TO_CURRENT_MAPPING_MATRIX.md` (AC-04,06)
- [x] T005 [P] [US5] Verificar arquitectura SAP actual del producto: `adapter.py` (base + manual + mock; **NO** `RealSapAdapter`), `sap_references`, `GA-REM-010/017` → citado en spec/plan/matriz (AC-16)
- [x] T006 [P] [US5] Verificar estado de decisiones y placeholders actuales (`SAP_INTEGRATION_READINESS_AUDIT`, `SAP_DEFERRED_LOCAL_PLACEHOLDERS`, `docs/10`, OD-12/OD-24) → citado en `SAP_OWNER_DECISIONS_REQUIRED.md` (AC-07,16)

## Phase 2: Contratos y diseño (SAP-0) — ✅ COMPLETADA

- [x] T007 [US2] Catálogo de 12 objetos inbound (14 campos c/u, `CURRENT_SAP_VALIDATION=PENDING`) → `SAP_INBOUND_DATA_CATALOG.md` (AC-05,09)
- [x] T008 [P] [US3] Comparación formal conectividad (8 opciones × 13 dimensiones) + recomendación condicionada → `SAP_CONNECTIVITY_OPTIONS_ANALYSIS.md` (AC-10)
- [x] T009 [P] [US3] Definir SAP Bridge (aislado, least privilege, NO implementado) → `SAP_BRIDGE_ARCHITECTURE_PROPOSAL.md` (AC-11)
- [x] T010 [US4] Contrato RAW (16 campos) + separación RAW/STAGING/CANÓNICO/AUDITORÍA + promoción → `SAP_RAW_STAGING_SPEC.md` (AC-12)
- [x] T011 [P] [US4] Estrategia snapshot/delta/watermark por objeto + reconciliación R1–R4 + cuarentena + fail-closed multi-compañía → `SAP_RAW_STAGING_SPEC.md §3–6` (AC-13,14,15)
- [x] T012 [P] [US3] Spec de convergencia empresas/granjas OD-24 (6 estados; sin heurísticas) → `SAP_COMPANY_FARM_CONVERGENCE_SPEC.md` (AC-07)
- [x] T013 [US1] Plan de discovery P0–P6 (allowed/forbidden/evidence/stop) + request SAP Basis (20 puntos, sin passwords) → `SAP_DISCOVERY_EXECUTION_PLAN.md` (AC-18)
- [x] T014 [P] [US1] Registro de gates Owner/Basis (12 gates clasificados; solo gates reales) → `SAP_OWNER_DECISIONS_REQUIRED.md` (AC-08)
- [x] T015 [P] [US5] Reevaluar `GA-REM-017` por clase de bloqueo → `SAP_GA_REM_017_RECLASSIFICATION.md` (AC-16,17)
- [x] T016 [US1] Determinar `GL-OD-06` (§38, solo dos valores) → `BLOCKED_EXTERNAL_SAP_INFORMATION` (AC-17)

## Phase 3: Spec development + verificación (SAP-0) — ✅ COMPLETADA

- [x] T017 [US5] `/specify` → `specs/001-sap0-landscape-discovery/spec.md` (FR-001…015, AC-01…21)
- [x] T018 [P] [US5] `/clarify` → sección Clarifications en `spec.md` (6 respuestas registradas)
- [x] T019 [P] [US5] `/plan` → `plan.md` (fases SAP-0…SAP-5 separadas; prohibiciones)
- [x] T020 [US5] `/tasks` → este documento (trazabilidad ID→doc→AC)
- [x] T021 [US5] `/analyze` → consistencia SPEC↔PLAN↔TASKS↔AC = PASS → `SAP0_SPEC_DEVELOPMENT_TRACEABILITY.md §4` (AC-20)
- [x] T022 [US5] `/converge` → 0 contradicciones técnicas abiertas → `SAP0_SPEC_DEVELOPMENT_TRACEABILITY.md §5` (AC-21)
- [x] T023 [US5] Verificación §33 (sin cambios de producto, sin secretos, 0 conexiones, árbol limpio, SHA remoto) → `SAP0_VERIFICATION_REPORT.md` (AC-18,19,21)
- [x] T024 [US5] Commit + push de documentación + verificación `LOCAL_SHA==REMOTE_SHA` (AC-21)

## Phase 4: Fases futuras — ⛔ NO INICIADAS (BLOCKED_BY_SAP0)

> Todas `IMPLEMENTATION_REQUIRED=YES` pero **fuera de SAP-0**. No ejecutar sin gates resueltos.

- [ ] T101 [US1] Obtener respuestas SAP Basis (SAP-BASIS-01) y autorización de probe (SAP0_PROBE_AUTHORIZATION) — `BLOCKED_BY_SAP0`
- [ ] T102 [US1] Ejecutar probe P0–P6 con evidencia saneada — `BLOCKED_BY_SAP0` (depende de T101)
- [ ] T103 [US3] Decidir SAP-CONN-01 (mecanismo/red) con resultados del probe — `BLOCKED_BY_SAP0`
- [ ] T104 [US4] Implementar SAP Bridge (SAP-2) — bloqueada por T103
- [ ] T105 [US4] Implementar RAW/STAGING y jobs de extracción (SAP-3) — bloqueada por T104
- [ ] T106 [US4] Implementar promoción + convergencia OD-24 (SAP-4) — bloqueada por T105
- [ ] T107 [US2] Cerrar decisiones funcionales LGORT/lote/scope con Owner — `BLOCKED_BY_SAP0`
- [ ] T108 [US3] Implementar servicios de operación continua (deltas/reconciliación) (SAP-5) — bloqueada por T106

## Trazabilidad resumida AC→Tarea

| AC | Tareas | AC | Tareas |
|---|---|---|---|
| 01 | T001,T002 | 12 | T010 |
| 02 | T001 | 13 | T011 |
| 03 | T001,T003 | 14 | T011 |
| 04 | T004 | 15 | T011 |
| 05 | T007 | 16 | T005,T006,T015 |
| 06 | T004 | 17 | T015,T016 |
| 07 | T006,T012 | 18 | T013,T023 |
| 08 | T014 | 19 | T023 |
| 09 | T007 | 20 | T021 |
| 10 | T008 | 21 | T022,T023,T024 |
| 11 | T009 | | |
