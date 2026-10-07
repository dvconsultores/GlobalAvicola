# SAP-HANA-CLOUD · 13_TRACEABILITY

Fecha: 2026-10-06 (spec) · 2026-10-07 (cierre local) · SPEC 005 · Trazabilidad de spec development

---

## 1 · Cadena

```text
DISCOVERY → /specify → /clarify → /plan → /tasks → /analyze → RED → /implement → TARGETED GREEN
→ FULL REGRESSION → IMPLEMENTATION COMMIT → SENSITIVITY → EXPLICIT SHA RESTORE
→ POST-MUTATION REGRESSION → EVIDENCE → LOCAL CERTIFICATION → EVIDENCE COMMIT → PUSH → REMOTE SHA VERIFY
```

| Fase | Artefacto | Estado |
|---|---|---|
| DISCOVERY | `specs/005-…/research.md` | DONE |
| /specify + /clarify | `spec.md` (FR-01…18, AC-HANA-01…55, Q1–Q12) | DONE |
| /plan | `plan.md`, `data-model.md`, `quickstart.md` | DONE |
| /tasks | `tasks.md` (T001…T057, T101–T102) | DONE |
| /analyze | §3 de este documento | DONE — `OPEN_TECHNICAL_CONTRADICTIONS = 0` |
| RED | `evidence/red/` | DONE — commit `44785d7` |
| /implement → TARGETED GREEN | `evidence/green/targeted_after_fix.log` (263) | DONE |
| FULL REGRESSION | 1630 / 0 / 49 (`evidence/regression/`) | DONE |
| IMPLEMENTATION COMMIT | `b07d3044766f8955c9a9c1a7cf92a3207d55b053` | DONE |
| SENSITIVITY S1–S8 + EXPLICIT SHA RESTORE | 8/8 DETECTED · `FINAL_DIFF = 0` (`10_…`) | DONE |
| POST-MUTATION REGRESSION | backend 1630/0/49 · frontend 539 · tsc · build · E2E 14 · migración · arranque sin credenciales | DONE |
| LOCAL CERTIFICATION | `11_LOCAL_CERTIFICATION.md` → `READY_FOR_SAP_CREDENTIALS` | DONE |
| EVIDENCE COMMIT · PUSH · REMOTE SHA VERIFY | §5 | ver §5 |

## 2 · Mandato → spec

| Mandato § | Tema | Dónde queda resuelto |
|---|---|---|
| 0, 4 | decisión y reconciliación histórica | `01_ARCHITECTURE_DECISION`, addenda `docs/10`, SOAP, SAP-0, SAP-0P |
| 3, 15, 16 | prohibición de escritura, guard, binds | FR-02, FR-03 · `04_READONLY_SECURITY` |
| 7 | alcance de objetos | `spec.md §SCOPE` (14) · `COST_CENTER`, `INVENTORY_SNAPSHOT` = `DEFERRED_PHASE_1` |
| 8, 9, 43 | fuentes y hardcodes legacy | `02_LEGACY_QUERY_AUDIT`, `03_HANA_QUERY_CATALOG` |
| 10–13 | driver, async, variables, TLS | FR-01, FR-04, FR-05 · `plan.md §3` |
| 14, 17, 18 | registry, paginación, delta | FR-06 · Q7 |
| 19–24 | RAW, watermark, mapping, staging, idempotencia | `data-model.md` · FR-07…FR-10 |
| 25–32 | promoción y semántica por objeto | FR-11, FR-12 · Q3, Q4, Q8, Q9, Q11 |
| 33–37 | API, readiness, RBAC, alcance | `plan.md §3` · FR-15 |
| 38, 39 | outbound deshabilitado, frontend | FR-16 · T030, T040 |
| 40–42 | scheduler, errores, auditoría | FR-13, FR-14, FR-17 |
| 44 | migraciones | `data-model.md` · T025 |
| 45–51 | pruebas, E2E, regresión, mutación | `09_TEST_MATRIX` |
| 52, 53 | certificación local y real | `11_LOCAL_CERTIFICATION`, `12_REAL_SAP_ACTIVATION_RUNBOOK` |
| 57, 58 | Git y despliegue | `plan.md §6` · `spec.md §RISKS` |

## 3 · /analyze (mandato §59)

Cada categoría se revisó contra el diseño (`spec.md`, `plan.md`, `data-model.md`) y queda cubierta por una prueba de la suite RED.

| # | Categoría | Hallazgos abiertos | Cómo se cierra |
|---|---|---|---|
| 1 | Queries legacy copiadas literalmente | 0 | SQL nuevo y estático; el legacy no está en el repo |
| 2 | Hardcodes | 0 | `test_hana_registry_has_no_legacy_hardcodes` |
| 3 | DML posible | 0 | registry cerrado + guard; `test_hana_guard_*` |
| 4 | SQL injection | 0 | binds; schema validado desde `Settings` |
| 5 | TLS bypass | 0 | `connect_options` rechaza la configuración |
| 6 | Secretos | 0 | saneado de errores; `repr` sin contraseña |
| 7 | HANA bloqueando el event loop | 0 | `asyncio.to_thread`; `test_hana_calls_do_not_block_the_event_loop` |
| 8 | MATDOC sin acotar | 0 | ventana obligatoria, tope de filas |
| 9 | Mapping ambiguo | 0 | único por (sistema, mandante, tipo, clave) |
| 10 | Fuga entre empresas | 0 | sync por empresa efectiva; fila ajena no se persiste |
| 11 | Watermark prematuro | 0 | se escribe dentro del savepoint, tras persistir |
| 12 | Duplicados | 0 | índice único parcial `is_current` + comparación de hash |
| 13 | Cantidad de OC incorrecta | 0 | Σ de unidad homogénea; mezcla ⇒ `BLOCKED` |
| 14 | Colapso cabecera/ítem | 0 | objetos y claves separados |
| 15 | Confusión producción/traslado/salida/movimiento | 0 | cuatro objetos con fuentes distintas |
| 16 | Outbound accidental | 0 | 409 por defecto; `SAP_ADAPTER=real` en 501 |
| 17 | Supuestos SOAP aún activos | 0 | punteros `SUPERSEDED`; ningún código SOAP existía |
| 18 | Ruta sin RBAC / sin alcance / sin transacción | 0 | las tres coberturas de arranque |
| 19 | Migración no reversible | 0 | tablas nuevas, sin enums; `downgrade` las elimina |
| 20 | Frontend mostrando export en fase READ ONLY | 0 | T040: botón oculto mientras outbound esté deshabilitado |

Decisiones que el análisis obligó a explicitar (ya en `spec.md §CLARIFICATIONS`): Q2 (tabla de jobs propia), Q4 (unidades mixtas bloquean), Q5 (quién mapea sociedades), Q6 (alcance por empresa efectiva), Q10 (fake solo en development/test).

Hallazgo sobre el código existente, no sobre el diseño: `retry_failed` marca `CONFIRMED` sin comprobar `delivers_to_sap`. Queda inalcanzable por el 409 de outbound; se anota para la futura spec de export.

```text
SPEC_CONSISTENCY = PASS
TASK_TRACEABILITY = PASS
OPEN_TECHNICAL_CONTRADICTIONS = 0
```

## 4 · Límites declarados

- Ninguna tabla SAP está verificada contra el landscape real (SAP-0P = 0/12). Las definiciones declaran `LEGACY_CONFIRMED` o `CANDIDATE`; su validación es el paso P5 del runbook.
- La certificación local la emite el agente ejecutor; el cierre formal corresponde al Owner (constitución Art. 9).

## 5 · Commits y verificación remota

| Hito | SHA |
|---|---|
| Spec + RED | `44785d7` |
| Implementación (`IMPLEMENTATION_SHA`, fuente de restauración de S1–S8) | `b07d3044766f8955c9a9c1a7cf92a3207d55b053` |
| Certificación y evidencia (`CERTIFICATION_SHA`) | el commit que introduce `11_LOCAL_CERTIFICATION.md` y este §5 (`git log -1 -- audit/sap-hana-cloud/11_LOCAL_CERTIFICATION.md`) |

Push a `origin/main` según AOD-29; `REMOTE_SHA_MATCH` se verifica con `git rev-parse HEAD` frente a `git ls-remote origin refs/heads/main` y queda registrado en la salida final de la ejecución. Rama: `main`; `NEW_BRANCH_CREATED = NO`.

## 6 · Estado final

```text
LOCAL_IMPLEMENTATION = CERTIFIED
SAP_HANA_REAL        = PENDING_CREDENTIALS
READINESS            = READY_FOR_SAP_CREDENTIALS
NEXT_STEP            = LOAD_SAP_HANA_READONLY_CREDENTIALS_AND_RUN_REAL_PROBE (12_REAL_SAP_ACTIVATION_RUNBOOK.md)
```
