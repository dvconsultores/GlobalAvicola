# GLOBAL AVÍCOLA — POST PRE-SAP · GO-LIVE READINESS ASSESSMENT

Fecha: 2026-09-17 · Fase: **G0 — Discovery / Gap Analysis / Spec (SIN implementación)**
Mandato: «Nueva fase post Pre-SAP — Cutover / Go-Live Readiness» (Owner, 2026-09-17).

---

## 0 · Congelación de baseline (§1 del mandato)

| Campo | Valor |
|---|---|
| **CERTIFIED_BASELINE_SHA** | **`fef7289`** (`fef7289f990a95348ac8e784e9d08f10938f5c05`) |
| **PRE_SAP_VERDICT** | `PRE_SAP_GO_WITH_NON_BLOCKING_OBSERVATIONS` |
| Baseline histórico | No se modifica. Toda evolución de esta fase parte de `fef7289` y debe ser trazable a él. |
| T13 | **CERRADO** — no se reabre; no se repiten UAT/suites/gates salvo evidencia de regresión (regla vigente). |
| **G0_DOCUMENTATION_SHA** | **`ea9478a`** — el pack G0 permanece **válido y cerrado**; la reconciliación pre-SAP-0 (2026-09-17) solo ajustó denominaciones de datos y estados de decisión, sin tocar producto. |
| SAP real (integración) | **FUERA de esta fase** (boundary intacto: S/4HANA = fuente transaccional/logística futura; Global Avícola = captura/validación/evidencia/aprobación). El **landscape actual** se auditará en **SAP-0** (descubrimiento, sin implementar). |

## 1 · Estado de entrada verificado

- Suites del árbol certificado: BE **1441/0F/49S** · FE **524/524** · tsc 0 · build OK · E2E **133/133** · KPI **142/0/35** (`evidence/t13-final/`).
- Runtime: `https://avicola.globaldv.net` — **SHARED DEVELOPMENT/TEST/CERTIFICATION/UAT** (no producción; `ENV-01`), topología `SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME`, despliegue por `DEPLOYMENT_MECHANISM = B` (docker-push-* + Watchtower), política de respaldo `GA_T13_BACKUP_POLICY.md`.
- Capacidad de cutover **ya certificada**: GA-REQ-061 (T14) — lotes en marcha sin doble conteo, plantillas por BU, staging, apply atómico/idempotente, reconciliación Opening↔Post-Lifetime (golden 9.965/535, UNKNOWN≠0), correcciones gobernadas. Ver `CUTOVER_MASTER_SPEC.md`.

## 2 · Observaciones no bloqueantes del Pre-SAP — clasificación (§2 del mandato)

Las **3** filas `CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS` del certificado son P-13, P-15 y OD-19. **No se asume** que «no bloqueante para Pre‑SAP» = «no bloqueante para producción».

> **Naturaleza**: las tres son `CERTIFIED_OBSERVATION` (observaciones del certificado Pre‑SAP) — **no** `OWNER_DECISION`. La columna «tratamiento propuesto» es `PROPOSED_GO_LIVE_TREATMENT` (propuesta técnica **no vinculante**): ninguna de las tres clasificaciones fue decidida explícitamente por el Owner todavía; las decisiones definitivas se registrarán en `GL-OD` cuando corresponda.

| ID | Origen | Observación (CERTIFIED_OBSERVATION) | Tratamiento propuesto (`PROPOSED_GO_LIVE_TREATMENT`) | Acción requerida |
|---|---|---|---|---|
| **NBO-01** | P-13 · Roles y permisos | Subcasos admin-only `N/A-BY-OWNER-DECISION` (G-04: inspección administrativa del host) | Propuesta: aceptar permanentemente (limitación de **ejecución de UAT**, no del producto; en operación real habrá cuentas admin) | En G2: provisionar y probar cuentas admin reales (checklist operacional). Decisión vinculante: `GL-OD-11` |
| **NBO-02** | P-15 · Reportes | `R-133` (cobertura de vacunación) y `R-134` (AFCR) `DEFERRED_FUNCTIONAL_DEFINITION` — fuera de superficies certificadas; datos primarios conservados; UNKNOWN≠0 | Propuesta: resolver después de Go-Live | Registrar en roadmap G4+ con definición funcional del Owner |
| **NBO-03** | OD-19 · Reverso interno | Diferidos declarados: consolidados, huevos/incubación (`BLOCKED_BY-R-161`), reverso SAP | Propuesta: decidir antes de Go-Live (aceptar limitación con workaround documentado **o** programar en G2) | Decisión vinculante: **`GL-OD-08`** (`PENDING_OWNER_DECISION`) |

**Backlog trazable**: NBO-01 → sección ops de `GO_LIVE_INFRASTRUCTURE_READINESS.md` + `GL-OD-11`; NBO-02 → `POST_PRE_SAP_GO_LIVE_ROADMAP.md` (G4+); NBO-03 → `GO_LIVE_OWNER_DECISIONS_REQUIRED.md` (GL-OD-08).

## 3 · Hallazgos de discovery (síntesis)

1. **La capacidad de cutover existe y está certificada** (GA-REQ-061): el proceso canónico del mandato puede construirse **reutilizándola** — no requiere reconstrucción. Gaps detectados son de **extensión** (firma/acta de cutover, coordinación de congelación, fuentes reales), no de capacidad base. Detalle: `CUTOVER_GAP_MATRIX.md`.
2. **El entorno desplegado es ficticio por diseño** (entorno compartido). Inventario de hoy (`evidence/runtime-data-inventory.log`, solo lectura; **clasificado `TEST_UAT_CURRENT_RUNTIME_DATA` / `SYNTHETIC`** — NO es inventario productivo real ni fuente de verdad para el cutover; la fuente real se determinará vía `SAP-0 → GL-OD-06`): 1 empresa (`Avícola Global C.A.`, sintética), 7 granjas (demo+fixtures), 34 galpones, 10 lotes (fixtures `E2E-MAN-153-*`/`L-GP-2026-01/06` + UAT `L-GP-2026-07…13`; lote 67 cerrado por UAT), 2 líneas genéticas, 5 proveedores, 4 transportes, 9 alimentos, 12 causas de mortalidad, 8 de descarte, 10 vacunas, 10 medicamentos, 4 fases productivas, **39 referencias SAP sintéticas** (no provienen del landscape real). Datos de usuarios/roles no enumerables con la cuenta del canal (403 por rol). Limpieza: `DATA_CLEANUP_PLAN.md` (nada se borra en esta fase).
3. **Infraestructura**: un solo host Docker compartido con backups locales; **no hay** observabilidad, correo saliente, rotación de secretos ni restore ensayado sobre copia productiva → decisiones Owner requeridas (`GO_LIVE_INFRASTRUCTURE_READINESS.md`, `GO_LIVE_OWNER_DECISIONS_REQUIRED.md`).
4. **Datos reales**: no hay acceso todavía a los datos reales del negocio (lotes vivos, poblaciones, mortalidad acumulada, alimento, pesos, usuarios). El `REAL_DATA_MIGRATION_PLAN.md` fija **qué se necesita exactamente** y en qué formato, sin inventar nada.

## 4 · Estados de esta fase (§12 del mandato)

| Área | Estado |
|---|---|
| Documentación G0 (este pack) | **COMPLETA** (10 entregables; SHA documental `ea9478a`) |
| Gaps identificados | `CUTOVER_GAP_MATRIX.md` (bloqueantes pre‑Go‑Live marcados) |
| **SAP-0 · Landscape Discovery** | **⏳ NO INICIADA** — fase insertada en el DAG antes de G1; `GL-OD-06 = PENDING_SAP0_DISCOVERY` |
| **GO_LIVE_READINESS** | **`NEEDS_OWNER_DECISIONS`** — camino especificado y ejecutable; arranque de G1 condicionado a SAP-0 + decisiones/accesos del Owner |
| Implementación | **NO INICIADA** (por mandato). Integración SAP real: **NO INICIADA** (boundary intacto) |

## 5 · Índice del paquete

1. `POST_PRE_SAP_GO_LIVE_READINESS_ASSESSMENT.md` (este documento)
2. `CUTOVER_MASTER_SPEC.md`
3. `CUTOVER_GAP_MATRIX.md`
4. `REAL_DATA_MIGRATION_PLAN.md`
5. `DATA_CLEANUP_PLAN.md`
6. `GO_LIVE_INFRASTRUCTURE_READINESS.md`
7. `CUTOVER_REHEARSAL_PLAN.md`
8. `GO_LIVE_OWNER_GATE.md`
9. `POST_PRE_SAP_GO_LIVE_ROADMAP.md`
10. `GO_LIVE_OWNER_DECISIONS_REQUIRED.md`
· Evidencia: `evidence/runtime-data-inventory.log`
