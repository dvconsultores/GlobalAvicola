# GA · PRE-SAP — T13 · RECON STATUS (estado verificado contra repositorio)

Fecha: 2026-09-16 · Mandato: ejecución autónoma de T13 hasta el siguiente
`OWNER_GATE_REAL` · Este documento **no modifica producto**.

## 1 · Estado de referencia (verificado hoy)

- `git status --short`: limpio · rama `main` · `HEAD = 93b4a91` (producto congelado en `be5453f`; commits posteriores solo documentación)
- `git ls-remote origin refs/heads/main` = `93b4a91` ⇒ **REMOTE_SHA_MATCH = PASS**
- Cadena reciente: `775448e` (gobernanza) → `b58136a` (decisión Wave C) →
  `3398dc4` (RED) → `9e76254` (IMPL) → `af1f1e2` (fixup guard) → `abfffeb`
  (cierre T12) → `47c77c0` (doc-fixup) → `be5453f` (arranque T13) → `93b4a91`
  (recon + rehersals OPS locales + prevalidación U1/U2).
- Gates de cierre T12 vigentes: BE full **1436/0F/49S** · FE **524/524** · E2E
  **111/111** · OD-22 **intacto** (r187) · Wave C certificada
  (`GA_REM_022_CERTIFICATION.md`).

## 2 · Inventario T13

| Elemento | Estado |
|---|---|
| `GA_T13_UAT_KIT.md` | Entregado (8 lotes U1–U8, regla §32, plantillas) |
| `GA_T13_OPS_RUNBOOK.md` | Entregado (G-02…G-05 comandos/criterios/evidencias) |
| `evidence/t13-ops/` | Rehersals locales G-03/04/05 + prevalidación U1/U2 (ver resultados) |
| `GA_T13_UAT_FICHAS_U1_U2.md` | Entregado (fichas de ejecución humana) |
| Plan UAT canónico | `GA_PRE_SAP_OWNER_UAT_RECERTIFICATION_PLAN.md` (§3 lotes, §32 regla) |
| Credenciales UAT-09 | `~/ga_uat09_credentials.txt` **presente** (600; se destruye en limpieza post-decisión) |
| Readiness | `backend/seeds/live_readiness_check.py` presente |

## 3 · Gates abiertos / decisiones (clasificación)

| Ref | Qué | Estado | ¿Bloquea Pre-SAP? |
|---|---|---|---|
| **OPS G-02…G-05** | Volumen media · rate limit runtime · BD rol mínimo+SSL · respaldo+política | `QUEUED/ BLOCKED_EXTERNAL` (host) + **rehersals locales PASS** (G-03/04/05) | **SÍ** (Pista OPS exigida en el cierre T13) |
| **GA-UAT-09** | Sesión del propietario (retry R-153/R-189, guía LISTA, retry de ingeniería 7/7 verde) | Sesión pendiente del propietario | **SÍ** (U2) |
| **U1–U8** | Aceptación owner por lote (U1/U2 **AUTORIZADAS** — U1 con `U1_SECURITY_RATE_LIMIT = PENDING_HOST_G03`; U3–U8 tras resultados) | Sesión humana pendiente del propietario | **SÍ** |
| **AOD-13** | `farm_inspection` sin lote: unidad (opciones A/B/C) | `ACCIONABLE` — R-221 **PARTIAL** (AC-04) | Condicional — **registrar decisión antes del GO** |
| **AOD-17 / R-142** | Semántica `CORRECTED` multinivel | `SCHEDULED` (diferida; no implementada) | NO (no exigida en Pre-SAP si queda registrada) |
| **AOD-18** | Cancelación: motivo obligatorio + solo admin | `SCHEDULED` | NO (rider opcional) |
| **OD-10.c / P1-15** | UI de activación manual | `SCHEDULED` (capacidad backend existe; UI opcional) | NO (no exigida; registrar) |
| **RES-07** | 19 filas VNC (8 requieren UAT) | Credo dentro de T13 (certificación de filas) | Condicional — resolver/difuminar en el cierre |
| **G-06** | Credenciales runtime para sondas C3 (R-199/201/202/203/204) | `QUEUED` (límite declarado, no bloqueante documentado) | NO (C1/C2 certificadas; C3 documentada) |
| **P-08 / SAP** | Integración real SAP | `BLOCKED_EXTERNAL` (fase posterior) | NO (fuera del alcance Pre-SAP por roadmap) |
| **DEPLOYMENT** | Mecanismo de despliegue del SHA certificado al entorno de UAT (`avicola.globaldv.net`) | Ejecutado (runs Actions `35122083759`/`35122083928`, imágenes `sha-f38350a`) · **`GOVERNANCE_DRIFT = RESOLVED_BY_OWNER_DECISION`** (`DEPLOYMENT_MECHANISM = B` — `GA_OWNER_DECISION_AOD29_DEPLOYMENT_MECHANISM_ADDENDUM.md`) · `RUNTIME_EXTERNAL_VERIFICATION = PASS` · `HOST_DEPLOYMENT_EVIDENCE = PENDING` · `DEPLOYMENT_GATE = PENDING` (ver §5) | **SÍ** (U1/U2 en HOLD hasta cerrar gates de host) |

## 4 · Findings P0/P1/P2 (estado de cierre)

- **P0 abiertos: 0** (GA-GOV-03 cerrada en T1; P1-12-REOPEN y familias cerradas
  en T8).
- **P1**: los 9 P1 del programa quedaron cerrados técnicamente en sus tranches
  (T2–T14); no hay P1 operativo bloqueante abierto a la fecha.
- **P2**: bloqueantes de programa cerrados en sus tranches; residuales
  registrados arriba (AOD-13, RES-07, G-06, OD-10.c, AOD-17/18) con su
  clasificación de bloqueo. La matriz final ID/SEVERITY/STATUS/BLOCKS/RATIONALE
  se emite en el cierre T13 con los resultados UAT/OPS.

## 5 · Deployment (estado 2026-09-16 tarde — reconciliación resuelta; gates de host pendientes)

- **Decisión del propietario**: `DEPLOYMENT = A` (`GA_T13_DEPLOYMENT_DECISION_A.md`).
- **Ejecución real**: `f38350a` (cuenta del propietario) restauró los 2 workflows de
  despliegue → push disparó runs de GitHub Actions (`35122083759` BE /
  `35122083928` FE, `success`) → imágenes `sha-f38350a`/`latest` en Docker Hub
  (BE `16:28:34Z` `sha256:6f0edbfa…`; FE `16:28:52Z` `sha256:29cd2eff…`) → Watchtower
  recreó contenedores.
- **Reconciliación de gobernanza**: reactivación sin decisión formal ⇒ `GOVERNANCE_DRIFT = TRUE`
  — **RESUELTO por decisión del propietario: `DEPLOYMENT_MECHANISM = B`**
  (`GA_OWNER_DECISION_AOD29_DEPLOYMENT_MECHANISM_ADDENDUM.md`): solo
  `docker-push-backend/frontend` autorizados; los otros 5 workflows siguen retirados;
  certificación local intacta; sin nuevos mecanismos.
- **Estados separados (mandato §3)**: `RUNTIME_EXTERNAL_VERIFICATION = PASS` ·
  `HOST_DEPLOYMENT_EVIDENCE = PENDING` · `DEPLOYMENT_GATE = PENDING` (rubric: KIT §3 +
  runbook §8/§12 — no se cierra sin evidencia de host y G-02…G-05).
- **Verificación externa**: bundle `index-r36pBbNX.js` (Last-Modified 16:28:48Z;
  sha256 `3047f5c…`); marcadores M1–M7 + control + `cutover-templates`; root/login 200;
  backend sirviendo (401 JSON). Evidencia: `evidence/t13-ops/deploy-a-runtime-verification.log`.
- **G-03 (rate limit): FAIL observado** (12×401 sin 429) — **causa raíz en código**
  (`config.py:115` default `false`; decorador no-op `main.py:15-33`; el contenedor del
  host conserva env sin el flag — Watchtower no relee el compose al recrear) ⇒ corrección
  **config-only** en la ventana de host (adenda §14.1 del runbook: `docker compose up -d backend`
  + retest ANTES/DESPUÉS). **G-02/G-04/G-05**: `BLOCKED_EXTERNAL` (host).
- **Ventana final de host (emitida por el propietario, 2026-09-16)**: procedimiento
  consolidado — runbook §11 auto-contenido (G-02/G-04/G-05), §14.1 (G-03
  config-only), §15 (reporte único) y plantilla
  `evidence/t13-ops/HOST_WINDOW_FINAL_REPORT_TEMPLATE.md`; host
  `UNAVAILABLE_TEMPORARILY` ⇒ `HOST_GATES = BLOCKED_EXTERNAL_TEMPORARY` (T13
  continúa en paralelo — ver Owner Decision).
- **U1/U2**: **AUTORIZADAS por el propietario** (`T13_PARALLEL_CONTINUATION = AUTHORIZED`; `GA_OWNER_DECISION_T13_PARALLEL_CONTINUATION.md`) — U1 con `U1_SECURITY_RATE_LIMIT = PENDING_HOST_G03`; U2 completa. Sesión humana pendiente; sin aceptaciones marcadas.
- No se monta Jenkins/GHA/SSH/cron por iniciativa del agente (mandato §12). Sin cambios a
  workflows ni historia por el agente.

## 6 · Deferred verificados (sin reabrir)

- **R-133/R-134** = `DEFERRED_FUNCTIONAL_DEFINITION`: sin superficie certificada
  con fórmulas ambiguas (tarjetas FE retiradas; E2E p15 ajustado); datos
  primarios conservados en backend (no certificados como KPI).
- **R-142/AOD-17** y **AOD-18**: diferidos correctamente como `SCHEDULED`; no
  convertidos en blocking.

## 7 · U1/U2 — prevalidación técnica (autónoma)

- **U1**: tests dedicados vigentes y verdes sobre el árbol certificado:
  `test_ga_rem_003_ac04_logout_revocation.py` (revocación AC04 + LOGOUT en
  auditoría), `test_r199_global_authority_fabrication.py` (sin comodín),
  `test_r200_refresh_token_as_access.py` (refresh ≠ access),
  `test_security_regression.py`, `test_session_payload.py`, `test_auth.py`.
- **U2**: `test_r153_import_lot_auto.py` + `test_f01d_filas_vacias.py` verdes;
  guía del propietario `GA_OWNER_UAT_R153_GUIDE.md` (estado LISTA) + retry de
  ingeniería **7/7** (`GA_OWNER_UAT_R153_RETRY_REFERENCE.md`); fixture
  retenido (eventos 120–123, lotes 64/65) hasta la decisión.
- Corrida conjunta: **82 passed / 0 failed**
  (`evidence/t13-ops/u1u2-prevalidation-tests.log`).

## 8 · Conclusión del recon

U1/U2 están **técnicamente listos** para la sesión del propietario. El gate
**DEPLOYMENT** quedó **decidido por el propietario el 2026-09-16
(`DEPLOYMENT = A`)**: desplegar manualmente el build certificado `be5453f`; la
ejecución está en manos del administrador del host con
`GA_T13_DEPLOYMENT_A_ADMIN_RUNBOOK.md` (agente: `BLOCKED_EXTERNAL_ACCESS`).
U1/U2 permanecen **READY_FOR_OWNER** en espera del despliegue PASS + prevalidación
técnica; **no se ejecuta UAT contra el build anterior**.
