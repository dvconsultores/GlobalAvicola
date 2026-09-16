# GA · PRE-SAP — T13 · RECON STATUS (estado verificado contra repositorio)

Fecha: 2026-09-16 · Mandato: ejecución autónoma de T13 hasta el siguiente
`OWNER_GATE_REAL` · Este documento **no modifica producto**.

## 1 · Estado de referencia (verificado hoy)

- `git status --short`: limpio · rama `main` · `HEAD = be5453f`
- `git ls-remote origin refs/heads/main` = `be5453f` ⇒ **REMOTE_SHA_MATCH = PASS**
- Cadena reciente: `775448e` (gobernanza) → `b58136a` (decisión Wave C) →
  `3398dc4` (RED) → `9e76254` (IMPL) → `af1f1e2` (fixup guard) → `abfffeb`
  (cierre T12) → `47c77c0` (doc-fixup) → `be5453f` (arranque T13).
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
| **DEPLOYMENT** | Mecanismo de despliegue del SHA certificado al entorno de UAT (`avicola.globaldv.net`) | **BLOCKED_OWNER_DECISION** (ver §5) | **SÍ** (para que UAT pruebe el producto certificado) |

## 4 · Findings P0/P1/P2 (estado de cierre)

- **P0 abiertos: 0** (GA-GOV-03 cerrada en T1; P1-12-REOPEN y familias cerradas
  en T8).
- **P1**: los 9 P1 del programa quedaron cerrados técnicamente en sus tranches
  (T2–T14); no hay P1 operativo bloqueante abierto a la fecha.
- **P2**: bloqueantes de programa cerrados en sus tranches; residuales
  registrados arriba (AOD-13, RES-07, G-06, OD-10.c, AOD-17/18) con su
  clasificación de bloqueo. La matriz final ID/SEVERITY/STATUS/BLOCKS/RATIONALE
  se emite en el cierre T13 con los resultados UAT/OPS.

## 5 · Deployment readiness (clasificación exacta)

- Los workflows de CI/CD están **retirados** (`.github/workflows-retired/`,
  incl. `docker-build-push`/`docker-push-*`) y no existe auto-deploy autorizado.
- Por tanto: **DEPLOYMENT_READINESS = BLOCKED_OWNER_DECISION**. Decisión
  necesaria (una de):
  - **(A)** Autorizar y ejecutar el despliegue **manual** del SHA certificado
    `be5453f` en el host (`docker compose build && up -d` o equivalente) antes
    de la UAT; o
  - **(B)** Declarar el **entorno desplegado actual** como entorno de UAT,
    registrando su SHA/limitación y las implicaciones (p. ej., U7 no podría
    validar Wave C si el build desplegado es anterior).
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

U1/U2 están **técnicamente listos** para la sesión del propietario. El único
gate que puede impedir una UAT válida es **DEPLOYMENT** (§5): sin el SHA
certificado desplegado (o sin declaración explícita del entorno objetivo), la
aceptación owner no representaría el producto certificado. Se presenta junto a
las fichas U1/U2 como `OWNER ACTION REQUIRED`.
