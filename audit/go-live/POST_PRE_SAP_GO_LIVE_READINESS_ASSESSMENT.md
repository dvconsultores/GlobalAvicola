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
| SAP real | **FUERA de esta fase** (boundary intacto: S/4HANA = fuente transaccional/logística futura; Global Avícola = captura/validación/evidencia/aprobación). |

## 1 · Estado de entrada verificado

- Suites del árbol certificado: BE **1441/0F/49S** · FE **524/524** · tsc 0 · build OK · E2E **133/133** · KPI **142/0/35** (`evidence/t13-final/`).
- Runtime: `https://avicola.globaldv.net` — **SHARED DEVELOPMENT/TEST/CERTIFICATION/UAT** (no producción; `ENV-01`), topología `SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME`, despliegue por `DEPLOYMENT_MECHANISM = B` (docker-push-* + Watchtower), política de respaldo `GA_T13_BACKUP_POLICY.md`.
- Capacidad de cutover **ya certificada**: GA-REQ-061 (T14) — lotes en marcha sin doble conteo, plantillas por BU, staging, apply atómico/idempotente, reconciliación Opening↔Post-Lifetime (golden 9.965/535, UNKNOWN≠0), correcciones gobernadas. Ver `CUTOVER_MASTER_SPEC.md`.

## 2 · Observaciones no bloqueantes del Pre-SAP — clasificación (§2 del mandato)

Las **3** filas `CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS` del certificado son P-13, P-15 y OD-19. **No se asume** que «no bloqueante para Pre‑SAP» = «no bloqueante para producción»:

| ID | Origen | Observación | Clasificación Go-Live | Acción requerida |
|---|---|---|---|---|
| **NBO-01** | P-13 · Roles y permisos | Subcasos admin-only `N/A-BY-OWNER-DECISION` (G-04: inspección administrativa del host) | **ACEPTADA PERMANENTEMENTE** (decisión Owner) — es una limitación de **ejecución de UAT**, no del producto; en operación real existirán cuentas admin reales | Ninguna de producto. En G2: provisionar y probar cuentas admin reales como parte del checklist operacional (§8) |
| **NBO-02** | P-15 · Reportes | `R-133` (cobertura de vacunación) y `R-134` (AFCR) `DEFERRED_FUNCTIONAL_DEFINITION` — fuera de superficies certificadas; datos primarios conservados; UNKNOWN≠0 | **RESOLVER DESPUÉS DE GO-LIVE** | Registrar en roadmap G4+: definición funcional con Owner cuando se priorice. No afecta operación diaria ni el cutover |
| **NBO-03** | OD-19 · Reverso interno | Diferidos declarados en la frontera técnica: consolidados, huevos/incubación (`BLOCKED_BY-R-161`), reverso SAP | **RESOLVER ANTES DE GO-LIVE — vía decisión Owner** | `GL-OD-08`: aceptar la limitación operacional para Go-Live (con procedimiento alternativo documentado) **o** incluir las porciones en G2. Es una decisión funcional real: impacta a los usuarios de planta |

**Backlog trazable**: NBO-01 → sección ops de `GO_LIVE_INFRASTRUCTURE_READINESS.md`; NBO-02 → `POST_PRE_SAP_GO_LIVE_ROADMAP.md` (G4+); NBO-03 → `GO_LIVE_OWNER_DECISIONS_REQUIRED.md` (GL-OD-08).

## 3 · Hallazgos de discovery (síntesis)

1. **La capacidad de cutover existe y está certificada** (GA-REQ-061): el proceso canónico del mandato puede construirse **reutilizándola** — no requiere reconstrucción. Gaps detectados son de **extensión** (firma/acta de cutover, coordinación de congelación, fuentes reales), no de capacidad base. Detalle: `CUTOVER_GAP_MATRIX.md`.
2. **El entorno desplegado es ficticio por diseño** (entorno compartido). Inventario real de hoy (`evidence/runtime-data-inventory.log`, solo lectura): 1 empresa (`Avícola Global C.A.`), 7 granjas (3 legacy demo + 4 fixtures), 34 galpones, 10 lotes (incl. `E2E-MAN-153-*`, `L-GP-2026-01…13`; lote 67 cerrado por UAT), 2 líneas genéticas, 5 proveedores, 4 transportes, 9 alimentos, 12 causas de mortalidad, 8 de descarte, 10 vacunas, 10 medicamentos, 4 fases productivas, **39 referencias SAP sintéticas**. Datos de usuarios/roles no enumerables con la cuenta del canal (403 por rol). Limpieza: `DATA_CLEANUP_PLAN.md` (nada se borra en esta fase).
3. **Infraestructura**: un solo host Docker compartido con backups locales; **no hay** observabilidad, correo saliente, rotación de secretos ni restore ensayado sobre copia productiva → decisiones Owner requeridas (`GO_LIVE_INFRASTRUCTURE_READINESS.md`, `GO_LIVE_OWNER_DECISIONS_REQUIRED.md`).
4. **Datos reales**: no hay acceso todavía a los datos reales del negocio (lotes vivos, poblaciones, mortalidad acumulada, alimento, pesos, usuarios). El `REAL_DATA_MIGRATION_PLAN.md` fija **qué se necesita exactamente** y en qué formato, sin inventar nada.

## 4 · Estados de esta fase (§12 del mandato)

| Área | Estado |
|---|---|
| Documentación G0 (este pack) | **COMPLETA** (10 entregables) |
| Gaps identificados | `CUTOVER_GAP_MATRIX.md` (bloqueantes pre‑Go‑Live marcados) |
| **GO_LIVE_READINESS** | **`NEEDS_OWNER_DECISIONS`** — el camino está especificado y es ejecutable; su arranque depende de las decisiones y accesos del Owner (`GO_LIVE_OWNER_DECISIONS_REQUIRED.md`) |
| Implementación | **NO INICIADA** (por mandato). SAP real: **NO INICIADO** (fuera de fase) |

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
