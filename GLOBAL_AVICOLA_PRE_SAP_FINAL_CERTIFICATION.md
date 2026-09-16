# GLOBAL AVÍCOLA — CERTIFICACIÓN FINAL PRE-SAP

Documento de certificación de cierre del programa Pre-SAP · Fecha de emisión:
2026-09-16 · Autoridad de certificación: agente autónomo
(`TECHNICAL_FUNCTIONAL_UAT_AUTHORITY = DEEPSEEK_AGENT`) bajo mandato del
propietario del 2026-09-16 (`GA_OWNER_DECISION_FINAL_AUTONOMOUS_CERTIFICATION.md`).

> **Atribución.** `OWNER_UAT_HUMAN_EXECUTION = WAIVED_BY_OWNER_DECISION` ·
> `TECHNICAL_FUNCTIONAL_UAT_AUTHORITY = DEEPSEEK_AGENT` ·
> `OWNER_DID_NOT_EXECUTE_UAT = TRUE` · `AUTOMATED_TECHNICAL_UAT = TRUE`.
> Ninguna sección de este documento constituye ni implica aceptación del
> propietario; el veredicto es técnico-funcional.

---

## 1 · Objeto y alcance

Certificar el estado técnico-funcional del sistema Global Avícola en la frontera
Pre-SAP: procesos P-01…P-15 + OD-19 + OD-25 + X-BU (17 aplicables; P-08 fuera de
alcance por roadmap), con UAT técnica delegada, suites completas sobre el árbol
final, sensibilidad/mutación, reconciliación total de hallazgos y veredicto.

## 2 · Baseline y árbol final

- Baseline T12 certificada: `abfffeb` (BE full 1436/0F/49S · FE 524/524 · E2E procesos 111/111).
- Árbol final de certificación: `main` tras el **commit de cierre de esta fase**
  (el SHA exacto —con `LOCAL == REMOTE` y árbol limpio— consta en el informe de
  cierre §28 del mandato).
- Cambios de producto en T13: únicamente la corrección determinista de
  rate-limit (`config.py` default true; `main.py::resolve_rate_limit_active`),
  certificada por cadena completa (SPEC→AC→RED→IMPL→GREEN→sensibilidad→runtime).

## 3 · Arquitectura y topología

- Desplegado: `https://avicola.globaldv.net` (openresty; backend `:8002`) —
  entorno **compartido** de desarrollo/test/certificación/UAT (no producción;
  `ENV-01`).
- Topología declarada por el propietario: `SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME`.
- Despliegue: `DEPLOYMENT_MECHANISM = B` (AOD-29 Addendum): push a `main` que
  toque `backend/**`/`frontend/**` → GitHub Actions `docker-push-backend.yml` /
  `docker-push-frontend.yml` (únicos autorizados; CI general `RETIRED`) → Docker
  Hub (`:latest` + `sha-<corto>`) → Watchtower (60 s) → `alembic upgrade head`
  en entrypoint (GA-REM-024). Trazabilidad por despliegue:
  `SOURCE_COMMIT → WORKFLOW_RUN → IMAGE_TAG/DIGEST → RUNTIME_EVIDENCE`.
- Alembic head única: `c8d9e0f1a2b3`.

## 4 · Decisiones del propietario aplicadas (vigentes)

| Decisión | Estado | Documento |
|---|---|---|
| `DEPLOYMENT = A` (decisión original) | Superada operativamente por B | `GA_T13_DEPLOYMENT_DECISION_A.md` |
| `DEPLOYMENT_MECHANISM = B` (AOD-29 Addendum) | **VIGENTE** | `GA_OWNER_DECISION_AOD29_DEPLOYMENT_MECHANISM_ADDENDUM.md` |
| `T13_PARALLEL_CONTINUATION` | Aplicada (U1/U2 liberadas) | `GA_OWNER_DECISION_T13_PARALLEL_CONTINUATION.md` |
| Mandato final autónomo (`WAIVED` UAT humana) | **VIGENTE** | `GA_OWNER_DECISION_FINAL_AUTONOMOUS_CERTIFICATION.md` |
| Wave C (AOD-08/AOD-10) | Aplicada y certificada | `GA_OWNER_DECISION_WAVE_C_FORMAL.md` |
| AOD-29 retire GitHub Actions; Clar. 01 | Aplicada | docs homónimos |

## 5 · Gates G-02…G-05 (reconciliados)

`GA_T13_HOST_GATES_RECONCILIATION.md`: G-02 **PASS** (contrato + pruebas) ·
G-03 **PASS** (runtime `401×5→429`; trazado a `d122e04`/run `35142848385`/digest
`sha256:5c4824bd…`) · G-04 **N/A-BY-OWNER-DECISION** (inspección administrativa;
`HOST_INSPECTION_GATE`) · G-05 **PASS** (mecanismo de restauración + política
`GA_T13_BACKUP_POLICY.md`) ⇒ **`DEPLOYMENT_GATE = PASS`** ·
`HOST_ADMIN_DEPENDENCY = REMOVED_BY_OWNER_DECISION`.

## 6 · UAT técnica U1–U8 (agente)

Resumen (detalles por lote con los 14 campos exigidos en los documentos de
resultados):

| Lote | Proceso(s) | Resultado técnico | Evidencia |
|---|---|---|---|
| U1 · Plataforma/seguridad | P-13, X-BU | **PASS_WITH_OBSERVATIONS** (suite 82/82 + runtime login/logout/refresh/RBAC/rate-limit) | `GA_T13_UAT_RESULTS_U1_U2.md` + logs |
| U2 · Progenitoras (GA-UAT-09) | P-01, OD-25 | **PASS** (C1/C2/C3 en runtime; lote `L-GP-2026-13`; recepción 100; cierre BR-18) | id. + `gp-cierre-runtime.log` |
| U3 · Reproductoras | P-03 | **PASS_WITH_OBSERVATIONS** — funcional por suite (curvas §4.5, BR-17, BR-20); runtime degradado por alcance de la cuenta (X-BU) | `GA_T13_UAT_RESULTS_U3_U8.md` |
| U4 · Incubadora | P-04, P-05 | **PASS_WITH_OBSERVATIONS** — funcional por suite (BR-02/BR-03/BR-21); runtime degradado por alcance de la cuenta | id. |
| U5 · Engorde y cierre | P-06, OD-19 | **PASS_WITH_OBSERVATIONS** — cierre real ejercitado en runtime (GP BR-18); cadena broiler y R7 por suite | id. |
| U6 · Revisión y reverso | P-07 | **PASS** (runtime: bandejas, reverso con observaciones, reenvío, aprobación, notificación `record_rejected`; multinivel/cancelación no aplican hoy por decisión) | `u6-u7-runtime-flow.log` |
| U7 · Reportes/trazabilidad | P-15, P-10, P-09 | **PASS_WITH_OBSERVATIONS** — notificaciones/trazabilidad en runtime; KPIs/auditoría por suite (runtime limitado por rol) | id. |
| U8 · Maestros/usuarios | P-12, P-13, P-11, P-14 | **PASS_WITH_OBSERVATIONS** — funcional por suites P-11/P-12/P-13/P-14; runtime limitado por rol | id. |

**Restricción transversal documentada**: la cuenta del canal seguro (UAT-09) es
«Operador de abuelas» — BU `grandparent` única; sus permisos no incluyen
`masters:create`, `reports:read` ni `audit:read`, y el X-BU rechaza montar
escenarios breeder/hatchery/broiler (`403 «sin acceso operativo a la unidad de
negocio»`). Por ello las sondas runtime de U3/U4/U5/U8 quedan
`DEGRADED_BY_CERT_ACCOUNT_SCOPE` y su verificación funcional se toma de las
suites de pila completa (E2E + backend, fixtures multi-BU), ejecutadas sobre el
árbol final.

## 7 · Suites finales sobre el árbol final (§14)

- **Backend completo**: **1441 passed · 0 failed · 49 skipped** (1414.93 s) —
  `evidence/t13-final/backend-full-suite.log` (incluye los 5 nuevos tests del
  artefacto G-03, que quedaron verdes).
- **Frontend (vitest)**: **524/524** en 87 archivos (67.79 s) — `frontend-tests.log`.
- **Typecheck**: **0 errores** (`tsc -b`) · **Build**: **OK** (`tsc -b && vite build`,
  1.24 s) — `tsc.log`, `build.log`.
- **E2E completo (Playwright, `procesos` + `heredada`)**: **133/133** (3.1 min;
  111 `procesos` + 22 `heredada`) — `e2e-full.log`. Un locator frágil de la
  suite heredada se corrigió con evidencia rojo→verde (ver §14/§15).
- **Regresión KPI/reportes** (14 archivos canónicos GA-REM-022): **142 passed ·
  0 failed · 35 skipped** (105.52 s) — `kpi-regression.log`.
- **Auth/sesión/refresh**: suite dedicada **82/82** (`u1u2-dedicated-suite-FINAL.log`).
- **Rate-limit**: unitarios del artefacto (5/5 en la suite completa) + verificación
  runtime `401×5→429` (§5).
- **Contratos SAP sin SAP real**: `test_sap_transversal.py` (16/16) + `test_sap.py`
  (9/9) verdes; skips declarados OK.

## 8 · Seguridad y tenancy

- RBAC sin comodín (R-199) verificado; refresh no usable como access; AC04
  (revocación por denylist `jti`) verificado en runtime; rate-limit activo en
  contenedor (G-03, determinista por artefacto).
- X-BU: aislamiento por unidad de negocio activo (fail-closed, OD-16), verificado
  como barrera real en runtime (403 al montar escenarios fuera de la BU de la
  cuenta) y por suites (`test_business_unit*`, `test_lots_bu_enforcement.py`,
  GOV-03 37/37).
- Multitenancy: suites de aislamiento multiempresa verdes (T1-T5; T14).

## 9 · Cutover y aperturas (GA-REQ-061)

- Golden de apertura de engorde E2E p16 (10.000 − 35 = 9.965; 535 kg) y suites
  `test_ga_req_061_cutover_c2…c7` verdes en suites finales; `UNKNOWN ≠ 0`
  (Wave C) preservado; R-67 = `PARTIAL_REUSE` (extiende apertura existente, sin
  concepto paralelo).

## 10 · KPIs y reportes (Wave C)

- R-131 FCR = alimento/ganancia (UNKNOWN≠0; sin pesos ⇒ UNKNOWN) · edad de lote
  cerrado congelada en `end_date` · R-132 base = apertura + recepciones ·
  R-141 filtro de estados R-218 · R-133/R-134 `DEFERRED_FUNCTIONAL_DEFINITION`
  (fuera de superficies certificadas) · R-187/OD-22 IPE intacto.
- Evidencia: `test_ga_rem_022_*`, `test_r184/r186/r187`, regresión KPI (§7).

## 11 · Procesos — matriz de 17

Inventario canónico: 18 entradas (P-01…P-15 + OD-19 + OD-25 + X-BU); **17
aplicables pre-SAP** + P-08 fuera de alcance (frontera SAP, §12). **Sin
transitividad**: cada fila se sostiene en su propia ejecución/evidencia.

| # | Proceso | Estado | Evidencia principal | Notas |
|---|---|---|---|---|
| 1 | **P-01** · Progenitoras (cría/importación) | **CERTIFIED** | UAT U2 runtime (import 201→lote `L-GP-2026-13`→recepción 100→cierre BR-18 200) + E2E `proceso-p01-*` | Casos C1/C2/C3 GA-R153 cerrados en runtime |
| 2 | **P-02** · Progenitoras (producción) | **CERTIFIED** | E2E `proceso-p02-*`, `proceso-02-control-produccion-diario` + backend suites | Control diario (mortalidad/alimento/pesaje) verificado |
| 3 | **P-03** · Reproductoras — cría | **CERTIFIED** | E2E `proceso-p03-reproductoras-cria` (5) + `p03-curvas-ui` + `test_genetic_curves` | UAT runtime degradada por alcance de cuenta (§15) |
| 4 | **P-04** · Reproductoras — huevo fértil | **CERTIFIED** | E2E `proceso-p04-*` + `test_egg_*` | BR-02 negativo incluido |
| 5 | **P-05** · Incubación | **CERTIFIED** | E2E `proceso-p05-incubacion` + `test_birth_classification`, `test_egg_incubation_concurrency` | BR-03/BR-21 negativos incluidos |
| 6 | **P-06** · Engorde y cierre | **CERTIFIED** | E2E `proceso-p06-*` + `p16` + `test_lot_close_approval`/`test_lot_closure`/`test_lot_planned_close`/`test_r192_*` | Cierre real también ejercitado en runtime (GP, BR-18) · R7 verificado |
| 7 | **P-07** · Revisión/corrección/aprobación | **CERTIFIED** | UAT U6 runtime (bandejas/reverso/reenvío/aprobación/notificación) + E2E `proceso-03-*` + `test_internal_reversal`, `test_review_bu_enforcement` | Multinivel/cancelación `SCHEDULED` (AOD-17/18) — declarado |
| 8 | **P-09** · Auditoría interna | **CERTIFIED** | E2E `proceso-p09-*` + `test_audit_*` (patrón; runtime 403 por rol) | Vista/filtros verificados en suite |
| 9 | **P-10** · Trazabilidad generacional | **CERTIFIED** | E2E `proceso-p10-*` + runtime `/lots/67/traceability` 200 | Tres generaciones en suite |
| 10 | **P-11** · Activación manual de lotes | **CERTIFIED** | E2E `proceso-p11-*` (6 reglas, idempotencia, apertura) | UI `OD-10.c` `SCHEDULED` (no exigida) |
| 11 | **P-12** · Datos maestros | **CERTIFIED** | E2E `proceso-p12-datos-maestros` + `test_masters*`, `test_master_*` | Runtime 403 por rol (§15) |
| 12 | **P-13** · Roles y permisos | **CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS** | UAT U1 (suite 82/82 + runtime RBAC/AC04/rate-limit) + E2E `proceso-p13-*` + `test_rbac` | Subcasos admin-only `N/A-BY-OWNER-DECISION` (G-04) |
| 13 | **P-14** · Notificaciones | **CERTIFIED** | E2E `proceso-p14-*` + runtime (unread-count; `record_rejected`) + `test_notification*` | — |
| 14 | **P-15** · Reportes e indicadores | **CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS** | E2E `proceso-p15-*` + regresión KPI (Wave C) + `test_kpi_*`, `test_r184/186/187`, `test_r204` | `R-133`/`R-134` `DEFERRED_FUNCTIONAL_DEFINITION` (fuera de superficies); UNKNOWN≠0 |
| 15 | **OD-19** · Reverso interno pre-SAP | **CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS** | `GA-REM-041` + E2E `proceso-03-*` + `test_internal_reversal` | Consolidados/huevos/incubación/SAP diferidos (frontera declarada en OD-19) |
| 16 | **OD-25** · Lote de abuelas automático | **CERTIFIED** | UAT U2 runtime (C1/C2/C3 + cierre BR-18) + E2E `proceso-p01-*` + `test_r153_*` | `INDEX.md` reconciliado |
| 17 | **X-BU** · Aislamiento por unidad de negocio | **CERTIFIED** | GOV-03 (37/37) + `test_business_unit*`, `test_lots_bu_enforcement` + runtime 403 X-BU (barrera real) | Fail-closed `OD-16` |

## 12 · Frontera SAP

`SAP_REAL_INTEGRATION = BLOCKED_EXTERNAL / FUTURE`.

- Alcance Pre-SAP certificado **sin SAP real**: `P-08` queda fuera de la matriz
  (§11) por roadmap; la frontera se gobierna por `OD-12` (contrato transversal
  SAP) y por las suites de contrato (`test_sap_transversal.py`; skips
  declarados OK) que corren en la suite completa sin depender del sistema
  externo.
- Diferidos SAP declarados: `R-144` (condicional a `AOD-08`), `R-136` SAP
  (frontera OD-19: reverso con contrapartida SAP diferido), `R-147`, `R-148`,
  `R-154`, `R-156`, `R-177` (aceptación o fase SAP), `OD-24` (empresas/granjas
  desde SAP, resuelto sin producto hoy), `OD-17.c` (reenvío SAP diferido).
- Referencias y snapshot SAP operativos en el entorno (39 referencias; import
  `POST /sap/references/import` operativo) — pero **ninguna certificación
  depende de un sistema SAP real**; la integración real es la fase siguiente.

## 13 · Reconciliación total (P0/P1/P2 + R-*/OD-*/AOD-*)

- **P0 abiertos: 0.** (GA-GOV-03 cerrada en T1: 37/37 + TEST_DEFECT 38; CI run
  `34764423545` verde.)
- **P1**: los 9 P1 del programa cerrados en sus tranches (T2–T14: R-194,
  R-197/R-207, R-153/R-189/GA-REM-042, GA-REQ-061, P1-12/13, Wave C
  R-131/R-132/R-141 + edad congelada, etc.). Residual: **R-221 `PARTIAL` /
  AOD-13 `ACCIONABLE`** — registro de decisión (unidad de `farm_inspection` sin
  lote) **antes del GO**; no bloquea técnicamente.
- **P2 residuales clasificados**: `R-133`/`R-134` = `DEFERRED_FUNCTIONAL_DEFINITION`
  (retirados de superficies certificadas; datos primarios intactos) ·
  `OD-10.c` UI de activación manual `SCHEDULED` (backend certificado; E2E p11) ·
  `AOD-17`/`R-142` (semántica `CORRECTED` multinivel) `SCHEDULED` · `AOD-18`
  (cancelación con motivo) `SCHEDULED` · `RES-07` (filas VNC con UAT) — nota
  administrativa de cierre · `G-06` límite declarado (sondas C3 con
  credenciales runtime; no bloqueante).
- **Reconciliaciones puntuales**: `AOD-29` + Addendum (drift de gobernanza
  resuelto; solo `docker-push-*` autorizados; CI general `RETIRED`) ·
  `GA-REQ-061` certificado (T11; golden 9.965/535; suites c2–c7) · `R-67` =
  `PARTIAL_REUSE` (apertura extendida; sin concepto paralelo) ·
  `R-131/R-132/R-141` corregidos; `OD-22` intacto (`test_r187` verde) ·
  `OD-04` (entregas parciales → GA-REM-035 `CERTIFIED`) · `OD-06` (curvas →
  GA-REM-037 `CERTIFIED`) · `OD-09/OD-14/OD-15/OD-16` vigentes e implementados
  (fail-closed 17/17 en GOV-03) · `OD-21` (`CERTIFIED`, T14 — R-185) ·
  `OD-23` (ciclo BU `CERTIFIED`; su arista CI quedó superada por `AOD-29`) ·
  `OD-25` (UAT técnica ejecutada — U2 PASS; `INDEX.md` actualizado) ·
  **Wave C certificada** (`GA_REM_022_CERTIFICATION.md`).

## 14 · Defectos y diferidos

- **Defectos de producto abiertos: 0.** Durante las corridas finales apareció
  **1 defecto de test** en la suite heredada (`tests/operations.spec.ts`: locator
  `.first()` matcheando el span oculto del MobileDrawer) — corregido en el test
  con evidencia rojo→verde (`evidence/t13-final/e2e-heredada-locator-fix.md`);
  sin cambio de producto.
- **Diferidos declarados** (sin reabrir; registrados por decisión):
  `AOD-17`/`R-142` (multinivel) · `AOD-18` (cancelación con motivo) ·
  `OD-10.c` (UI activación manual) · `R-133`/`R-134` (definición funcional de
  KPIs) · familia SAP (`R-144`/AOD-08; `R-147`, `R-148`, `R-154`, `R-156`,
  `R-177` — aceptación o fase SAP) · `OD-19` consolidados/huevos/incubación
  (frontera técnica declarada) · `RES-07`/`G-06` (notas administrativas).

## 15 · Observaciones no bloqueantes

- Alcance de la cuenta UAT-09 (BU `grandparent`): sondas runtime de U3/U4/U5/U8
  degradadas por diseño X-BU; cobertura por suites (§6).
- Subcasos admin-only de U1 `N/A-BY-OWNER-DECISION` (G-04).
- Índice `specs/remediation/INDEX.md`: fila OD-25 actualizada con la UAT técnica;
  base GA-REM-040 fase 9 (`BLOCKED_AUTH` histórica por cuentas) permanece como
  frente administrativo separado (no Pre-SAP funcional).
- **Observación de arquitectura de datos UAT**: los datos creados durante la
  certificación (lote `L-GP-2026-13` cerrado, eventos 132/133, escenarios de
  suite) permanecen en el entorno **compartido** de UAT — es la política
  declarada (`ENV-01`); no se limpian como parte del cierre.

## 16 · Riesgos residuales

1. **Propagación del despliegue vía Watchtower** (60 s): verificada
   empíricamente en cada push de la fase (G-03 y previos); riesgo bajo.
2. **Entorno compartido**: datos y sesiones de UAT conviven con pruebas;
   mitigado por X-BU/RBAC y por el alcance de las cuentas.
3. **Alcance del canal de cuentas** (UAT-09 GP-only): verificación runtime de
   procesos no-GP depende de suites; riesgo informativo, no funcional.
4. **`G-06`**: sondas C3 con credenciales runtime del entorno — límite
   declarado, no bloqueante.
5. **Dependencia de `alembic head` única** (`c8d9e0f1a2b3`): verificada en
   entrypoint (GA-REM-024) y en suites (`test_upgrade_path` — skips declarados).

## 17 · Índice de evidencia

- **Decisión/alcance**: `GA_OWNER_DECISION_FINAL_AUTONOMOUS_CERTIFICATION.md`,
  `GA_OWNER_DECISION_AOD29_DEPLOYMENT_MECHANISM_ADDENDUM.md`,
  `GA_T13_HOST_GATES_RECONCILIATION.md`, `GA_T13_BACKUP_POLICY.md`,
  `GA_OWNER_DECISION_WAVE_C_FORMAL.md`.
- **UAT técnica**: `GA_T13_UAT_RESULTS_U1_U2.md`,
  `GA_T13_UAT_RESULTS_U3_U8.md`; logs `evidence/t13-uat/`
  (`u1-runtime-probes.log`, `u2-runtime-flow.log`, `u6-u7-runtime-flow.log`,
  `gp-cierre-runtime.log`, `u3-u8-runtime-flow.log`,
  `u3-u8-data-inventory.log`, `u1u2-dedicated-suite-FINAL.log`).
- **Gates/OPS**: `evidence/t13-ops/g03-fix-red-green-sensitivity.log`,
  `deploy-a-runtime-verification.log`, `host-evidence-package.md`.
- **Suites finales**: `evidence/t13-final/` (`backend-full-suite.log`,
  `frontend-tests.log`, `tsc.log`, `build.log`, `e2e-full.log`,
  `kpi-regression.log`).
- **Certificaciones previas**: `GA_T1…GA_T14_CERTIFICATION.md`,
  `GA_REM_022_CERTIFICATION.md`, `GA_GOV_03_CERTIFICATION.md`.
- **Estado/ledger**: `GA_AUTONOMOUS_EXECUTION_LEDGER.md` (AE-61…AE-69),
  `GA_T13_RECON_STATUS.md` §9, `GA_PRE_SAP_PROGRAM_STATUS.md`.

## 18 · Verificación remota

`REMOTE_SHA_MATCH = PASS` — verificado tras el push del commit de cierre de esta
fase (`LOCAL == REMOTE`, árbol limpio). El SHA exacto consta en el informe de
cierre §28 del mandato.

## 19 · Sensibilidad/mutación

- G-03/rate-limit: mutación con restauración por SHA explícito
  (`git restore --source=$IMPL_COMMIT`), rojo causa-exacto reproducible —
  `evidence/t13-ops/g03-fix-red-green-sensitivity.log`.
- Wave C: M1/M2 sensibilidad 1:1 con restauración (T12; `GA_REM_022_CERTIFICATION.md`).
- **Fase final T13**: no se introdujeron cambios de producto adicionales tras
  G-03; la sensibilidad exigible quedó cubierta por las mutaciones M1/M2 de
  Wave C y por la mutación del artefacto de rate-limit (restauración por SHA
  explícito en ambos casos). Si la corrida final revelara un defecto, la cadena
  completa incluiría su sensibilidad correspondiente antes del cierre.

## 20 · Métricas de cierre

- **Hallazgos**: P0 abiertos **0** · P1 abiertos operativos **0** (residual
  `R-221`/`AOD-13`: registro de decisión antes del GO, no bloqueante) · P2
  residuales declarados y clasificados (§13/§14).
- **Procesos (17 aplicables)**: `14 CERTIFIED` ·
  `3 CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS` (P-13, P-15, OD-19) ·
  `0 PARTIAL` · `0 BLOCKED` · `0 NOT_APPLICABLE`.
- **UAT técnica**: U1–U8 con resultado propio por lote (§6); sin aceptación
  humana (`WAIVED_BY_OWNER_DECISION`).
- **Suites finales**: BE **1441/0F/49S** · FE **524/524** (tsc 0 · build OK) ·
  E2E **133/133** · KPI **142/0/35** · UAT dedicada **82/82** · runtime rate-limit
  **401×5→429**.

## 21 · Veredicto

**`PRE_SAP_GO_WITH_NON_BLOCKING_OBSERVATIONS`**

Justificación: todos los gates técnicos en verde sobre el árbol final — suites
§7 (BE 1441/0F/49S · FE 524/524 · tsc 0 · build OK · E2E 133/133 · KPI 142/0/35),
UAT U1–U8 §6, gates G-02…G-05 §5, reconciliación §13 — sin defectos de producto
abiertos (P0 = 0; P1 operativos = 0).

Observaciones **no bloqueantes**: (1) el alcance de la cuenta del canal UAT-09
(BU `grandparent`) limita las sondas runtime de U3/U4/U5/U8 — cobertura funcional
por suites de pila completa; (2) subcasos admin-only de U1
`N/A-BY-OWNER-DECISION` (G-04); (3) `R-221`/`AOD-13` — registrar la decisión de
la unidad de `farm_inspection` **antes del GO** (registro administrativo, no
técnico); (4) diferidos declarados (§14) permanecen como están.

Mantenimiento de la certificación: cualquier cambio de producto posterior a
este árbol invalida la certificación y exige repetir la cadena §14.
