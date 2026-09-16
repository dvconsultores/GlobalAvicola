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
| **U1–U8** | Aceptación owner por lote (U1/U2 preparados; U3–U8 tras OK) | Pendiente del propietario | **SÍ** |
| **AOD-13** | `farm_inspection` sin lote: unidad (opciones A/B/C) | `ACCIONABLE` — R-221 **PARTIAL** (AC-04) | Condicional — **registrar decisión antes del GO** |
| **AOD-17 / R-142** | Semántica `CORRECTED` multinivel | `SCHEDULED` (diferida; no implementada) | NO (no exigida en Pre-SAP si queda registrada) |
| **AOD-18** | Cancelación: motivo obligatorio + solo admin | `SCHEDULED` | NO (rider opcional) |
| **OD-10.c / P1-15** | UI de activación manual | `SCHEDULED` (capacidad backend existe; UI opcional) | NO (no exigida; registrar) |
| **RES-07** | 19 filas VNC (8 requieren UAT) | Credo dentro de T13 (certificación de filas) | Condicional — resolver/difuminar en el cierre |
| **G-06** | Credenciales runtime para sondas C3 (R-199/201/202/203/204) | `QUEUED` (límite declarado, no bloqueante documentado) | NO (C1/C2 certificadas; C3 documentada) |
| **P-08 / SAP** | Integración real SAP | `BLOCKED_EXTERNAL` (fase posterior) | NO (fuera del alcance Pre-SAP por roadmap) |
| **DEPLOYMENT** | Mecanismo de despliegue del SHA certificado al entorno de UAT (`avicola.globaldv.net`) | **`DECIDED=A`** + **ejecutado** (EX-01 reactivado por el propietario, `f38350a`) · verificación externa **PASS** · G-03 `FAIL` observado (diagnóstico host) — ver §5 | **SÍ** (UAT ya puede probar el build certificado; cierre OPS en ventana host) |

## 4 · Findings P0/P1/P2 (estado de cierre)

- **P0 abiertos: 0** (GA-GOV-03 cerrada en T1; P1-12-REOPEN y familias cerradas
  en T8).
- **P1**: los 9 P1 del programa quedaron cerrados técnicamente en sus tranches
  (T2–T14); no hay P1 operativo bloqueante abierto a la fecha.
- **P2**: bloqueantes de programa cerrados en sus tranches; residuales
  registrados arriba (AOD-13, RES-07, G-06, OD-10.c, AOD-17/18) con su
  clasificación de bloqueo. La matriz final ID/SEVERITY/STATUS/BLOCKS/RATIONALE
  se emite en el cierre T13 con los resultados UAT/OPS.

## 5 · Deployment (estado actualizado 2026-09-16, tarde — desplegado y verificado)

- **Decisión del propietario**: **`DEPLOYMENT = A`** (2026-09-16; registro
  `GA_T13_DEPLOYMENT_DECISION_A.md`; entorno
  `SHARED DEVELOPMENT/TEST/CERTIFICATION/UAT`, no producción).
- `PRODUCT_SHA = be5453f` — producto congelado (`git diff be5453f..HEAD -- backend
  frontend e2e` vacío).
- **Ejecución (por el propietario, mecanismo EX-01)**: el propietario restauró los
  workflows `docker-push-backend/frontend` (`f38350a`; **idénticos** a los de
  `workflows-retired/`) y ejecutó el despliegue del build certificado; el agente no
  reactivó nada (certificación sigue local, AOD-29 intacto).
- **Verificación externa (PASS)**: bundle servido `index-apu3WWcr.js` (14-sep) →
  **`index-r36pBbNX.js`** (Last-Modified **16:28:48Z**; sha256 `3047f5c…`);
  marcadores GA-FE-01 M1–M7 (+ control `switch-company`, + `cutover-templates`)
  presentes; root/login 200; backend sirviendo (401 JSON) ⇒ según GA-REM-024 la
  migración del entrypoint completó. ⇒ **`DEPLOYMENT_STATUS = PASS` (verificación
  externa)**; evidencia cruda del host (digests, log `[entrypoint]`, `alembic
  current`) pendiente como complemento (runbook §12).
- **G-03 (rate limit) — FAIL observado en runtime**: 12 intentos consecutivos a
  `POST /api/v1/login` ⇒ **401×12, sin 429** (esperado 401×5 → 429). Diagnóstico
  host pendiente (flag efectivo en contenedor, umbral, clave del proxy GAP-11).
  Evidencia: `evidence/t13-ops/deploy-a-runtime-verification.log`.
- **Pendiente de host**: G-02 · G-04 · G-05 + diagnóstico/re-ejecución G-03 +
  evidencia cruda del despliegue (`GA_T13_DEPLOYMENT_A_ADMIN_RUNBOOK.md`).
- No se monta Jenkins/GHA/SSH/cron por iniciativa del agente (mandato §12).

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
