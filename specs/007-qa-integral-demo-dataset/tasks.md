# Tasks — SPEC 007

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| T01 | Discovery: modelo, servicios, seeds, navegación, reglas | DONE | `research.md`, `audit/qa-integral-dataset/01_DISCOVERY.md` |
| T02 | SPEC completa (spec, plan, tasks, research, data-model, dataset-contract, cleanup-contract, qa-test-matrix, quickstart) | DONE | este directorio |
| T03 | Constructores `qa_integral_builders.py` | DONE | código |
| T04 | CLI `qa_integral_dataset.py` (--inventory/--apply/--verify/--cleanup/--dry-run, guardas, credenciales, manifest) | DONE | código |
| T05 | Escenarios: lotes por BU y etapa, historia 4–8 semanas, 28 tipos de evento | DONE | `--verify` «event types coverage» |
| T06 | Workflow en todos los estados internos, correcciones, reverso, cancelación, consolidación | DONE | `--verify` «workflow states valid» |
| T07 | SAP sintético: 14 objetos staged + promoción + OC BR-18 + pendiente de mapeo + inválido | DONE | `--verify` |
| T08 | Cutover v2 aplicado por BU + fixtures XLSX | DONE | `fixtures/`, `--verify` |
| T09 | Empresa de aislamiento (BU apagadas, usuarios propios, lotes propios) | DONE | `--verify` «isolation BU on/off» |
| T10 | Cleanup FK-safe fail-closed + dry-run | DONE | `07_CLEANUP_PROOF.md` |
| T11 | Tests del seed (guardas, secretos, marcadores, fail-closed, cobertura FK) | DONE | `tests/test_qa_integral_dataset.py` |
| T12 | Ensayo aislado CREATE→VERIFY→APPLY(0)→CLEAN→RECREATE→VERIFY | DONE | `06`, `07` |
| T13 | Regresión completa backend + frontend | DONE (1722/0/49 · 542/542 · tsc+build) | `10_REGRESSION.md` |
| T14 | Commit de implementación (SPEC + seed + tests + evidencia) | DONE | `12_TRACEABILITY.md` |
| T15 | Push AOD-29 + REMOTE_SHA_MATCH | DONE (`b7942c7`, PASS) | `12_TRACEABILITY.md` |
| T16 | Ejecución en runtime compartido (`--inventory`, `--apply`, `--verify`) | BLOCKED_EXTERNAL (base no alcanzable desde la estación; runbook entregado) | `09_RUNTIME_VERIFICATION.md` |
| T17 | Verificación funcional en runtime por API (login 12 usuarios, menú por BU, lotes, revisión, SAP, reportes, cutover) | BLOCKED_EXTERNAL (checklist entregada) | `09` |
| T18 | Manual QA MD + DOCX + plantilla de resultados DOCX + matriz de cobertura | DONE | `docs/`, `QA_DATA_COVERAGE_MATRIX.md`, `11_QA_MANUAL_DELIVERY.md` |
| T19 | Manifest MD + JSON | DONE (aislado; runtime pendiente) | `QA_DATA_MANIFEST.*` |
| T20 | Commit de certificación + push + verificación remota | DONE (IMPL `9a5d11a` · CERT `b7942c7` · REMOTE_SHA_MATCH PASS) | `12` |
| T21 | Revisión independiente del entregable (ejecutor DeepSeek, solo lectura, 2 partes) | DONE | 13_INDEPENDENT_REVIEW_AND_REMEDIATION.md |
| T22 | Remediación R1 (seed, tests, manual, script de ciclo aislado) | DONE | remediation-r1.md · 13 |
| T23 | Regresión completa backend post-R1 | DONE (1731/0/49 pre y post-mutación) | 10_REGRESSION.md |
| T24 | Commit R1 + sensibilidad + push + verificación remota | DONE commit R1 `fda91a8` · sensibilidad S7–S9 3/3 · CERT en este commit · push 2510653..7e44a66 · REMOTE_SHA_MATCH PASS | 12_TRACEABILITY.md |
