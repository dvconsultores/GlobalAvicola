# GA-GOV-03 · HALLAZGO — GOBERNANZA DE PRUEBAS Y CERTIFICACIONES

| Campo | Valor |
|---|---|
| **ID** | `GA-GOV-03` · **Clase** `GOVERNANCE` · **Tipo** `PROCESS SPEC` (higiene de pruebas · CI · regla de certificación · reconciliación) |
| **Prioridad** | **P1 (gobernanza)** · **Bloquea SAP**: SÍ — sin suite verde reproducible en HEAD no hay certificación válida |
| **Estado** | `SPEC_READY` · sin código · sin GA-REM asignado (siguiente libre `GA-REM-043`, no se asigna aquí) |
| **Fecha / HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) · runtime `https://avicola.globaldv.net` (`index-DDCcWL76.js` == build local) |
| **Vecinos** | `GA-REM-013` (quality gates, `CERTIFIED` en `specs/remediation/INDEX.md:20`) · `GA-REM-014` (entorno aislado, `CERTIFIED` `:8`) · `GA-REM-016` (`SPEC_DRAFT` `:26`) · `P1-7` · `R-72` (validez de pruebas) · `R-213` (hallazgo colateral) |
| **Registro canónico** | `audit/ga-claude-final-audit/GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` G-33 (`:51`, ficha `:145-150`) |
| **Dedup (§48)** | Inspeccionados `REMEDIATION_BACKLOG.md` (R-001…R-189, GA-REM-001…042, GA-GOV-01…02, OD-01…25, GA-UAT-01…09, GA-FE-01…08), `specs/remediation/*`, `audit/ga-*/`. Ningún hallazgo previo cubre «suite roja en HEAD + CI sólo en PR + certificaciones sin artefacto»; `GA-REM-013`/`014` cubren la infraestructura, no la vigencia de las pruebas ni la regla de evidencia. **Nuevo.** |

## 1 · Enunciado

En HEAD `c0b4afc` la suite de backend ejecutada con el arnés canónico (`backend/scripts/run_tests.sh`, PostgreSQL aislado) termina **25 failed · 1201 passed · 49 skipped** (`evidence/backend_full_suite.log:624`), y la suite Playwright de procesos (`bash scripts_e2e.sh`) termina **12 failed · 117 passed** (`evidence/playwright_e2e.log:561-575`). Los 37 fallos son **TEST_DEFECT** (pruebas obsoletas frente a reglas posteriores, fixtures inválidos o guardas literales caducadas); **0 APP_DEFECT directo** (el 500 de `/me` que destapa la suite R-188 es un hallazgo colateral, `R-213`). Mientras tanto, la documentación afirma «suite PG declarada a CI» y «1139 passed · 49 skipped · 0 failed» (`audit/remediation/WAVE_B_TRANCHE_14_SUBMOVEMENT_STRUCTURAL_TENANCY_EVIDENCE.md:186`, 2026-09-10), pero **el CI que ejecuta pytest sólo se dispara en `pull_request`** (`.github/workflows/backend-ci.yml:4-12`) y el repositorio no tiene ningún merge en 466 commits (`git log --merges | wc -l` = 0): ninguna suite «declarada a CI» se ha ejecutado jamás. Las 13 certificaciones de proceso (`audit/remediation/PROCESS-*-CERTIFICATION.md`) no citan commit ni artefacto de corrida, cuatro contienen veredictos contradictorios en el mismo fichero, y seis (P-03, P-04, P-05, P-10, P-11, P-15) tienen hoy su suite roja en HEAD. Nueve registros de aceptación del propietario carecen de evidencia primaria del propietario. `R-189` y `GA-UAT-09` no están en el backlog; `OD-21…OD-25` no tienen fichero en `specs/remediation/`.

## 2 · Evidencia

### 2.1 Backend — 25 fallos en HEAD (todos TEST_DEFECT)

Corrida completa: `evidence/backend_full_suite.log` (líneas 73-537 tracebacks; `:598-624` resumen). Reproducción en aislamiento de los 25 casos: `evidence/backend_targeted_failing.log:550-575` («25 failed, 189 passed»). Clasificación:

| Grupo | Casos | Causa | Regla/commit que los dejó obsoletos |
|---|---|---|---|
| **A · OD-16 fail-closed** | **17** (`test_lots_bu_enforcement` l08×4, l11, e06 · `test_operations_bu_enforcement` w13×4, a08, a13 · `test_review_bu_enforcement::test_165_01` · `test_state_continuity::test_s07` · `test_internal_reversal::test_s03_s04` · `test_od14_productive_surfaces::test_s02` · `test_review_decision_concurrency::test_r166_12`) | Esperan **403** o **visibilidad** de la autoridad global situada sobre una unidad **apagada**; el producto responde **404 «no encontrado» / fila invisible** (fail-closed) | `OD-16` (`specs/remediation/OD-16-…md:67-88`, «apagar prevalece», «no hay acceso productivo implícito») implementada en lectura por `9ffc5ec` («ga-fe-02-d IMPL (OD-16): borde de lectura productiva de la autoridad global — … remoción de los 8 atajos is_super_admin en lots/masters-filter/dashboard/review ×3/reports ×2/operations ×3», `backend/app/business_units/service.py:126-146` `unidades_de_alcance_productivo`); test canónico nuevo `backend/tests/test_od16_global_read_boundary.py:1-20` |
| **B · fixture R-188** | **5** (`test_r188_bu_lifecycle` ×5) | Fixture crea usuarios con correo `…@e.test` (`backend/tests/test_r188_bu_lifecycle.py:79`); el helper `_efectivas_y_concedidas` (`:131-133`) exige `/me` 200 y recibe **500** (`log:335-339, 366-370, 396-400, 419-423, 455-459`; `evidence/backend_r188_me500.log:81` «GET /api/v1/me → 500») | `pydantic 2.13.4` + `email_validator 2.3.0` rechazan dominios reservados (`.test`, `.invalid`, `.local`, `example.test`) en `UserRead.email: EmailStr` (`backend/app/auth/schemas.py:30`) → `auth/service.py:329` lanza `ValidationError` → 500 (**R-213**). La suite R-188 **nunca ha pasado**: su cabecera declara «en local… `skipped`… corre en CI» (`test_r188_bu_lifecycle.py:14-16`), `audit/ga-bu-d10/GA_BU_D10_CERTIFICATION.md:37` lo repite, y el CI no se ejecuta (§2.3) |
| **C · guardas literales** | **3** (`test_company_catalog::test_t10`, `test_population_invariant::test_ac14`, `test_time_determinism::test_t028_04`) | Cabeza Alembic fijada a `x4y5z6a7b8c9` (`test_company_catalog.py:267`, `test_population_invariant.py:398`; fijada en `c653ff8`) mientras la cadena avanzó a `y5z6a7b8c9d0` (`b4d8c3a`, `backend/alembic/versions/y5z6a7b8c9d0_seed_business_unit_catalog.py`; `log:88-96, 305-312`). Fechas ISO literales en comentarios/docstrings (`test_r188_bu_lifecycle.py:3`, `test_r184_ipe_date_semantics.py:4,50`, `test_r187_ipe_od22_scale.py:3`) detectadas por la guarda `T-028-04` (`test_time_determinism.py:95-115`; `log:530-537`) | Migración de datos F1 (`GA-FE-02-C §2`) y comentarios de OD-22/OD-23 escritos con fecha |

> **Corrección documental D-01 (aplicada en el registro)**: el registro canónico totalizaba el grupo A como «14 × TEST_DEFECT» y enumeraba 17 casos; corregido a **17 ×**, suma **17 + 5 + 3 = 25**, coherente con `backend_full_suite.log:624`. Recuento de paquetes del registro corregido en **D-02** (22 P2 · 24 bloqueantes · 24 completos · 9 compactos).

Detalle caso a caso (aserción actual · respuesta real · cambio requerido) en `GA-GOV-03_SPEC.md §7.1` y en `GA-GOV-03_AC_MATRIX.md`.

### 2.2 Playwright — 12 fallos en HEAD (todos TEST_DEFECT)

`evidence/playwright_e2e.log` (129 pruebas, 2 workers; fallos `:202-559`; resumen `:561-575`):

| # | Prueba | Causa real (log) | Regla/commit posterior a la certificación |
|---|---|---|---|
| 1 | `e2e/proceso-p03-curvas-ui.spec.ts:374` cadena completa (`:439`) | `strict mode violation: getByText(/135/) resolved to 2 elements` — «Evento #135» (h1) y «135–165 g» (`log:204-226`) | Locator ambiguo por construcción (el id del evento coincidió con `MINIMO_A_LOS_15 = 135`, `:25`) |
| 2 | `e2e/proceso-p03-reproductoras-cria.spec.ts:107` (`:117,131`) | `bird_reception` → **400 BR-20** «declara recibidas, mortalidad al arribo y rechazo (falta: received_total, dead_on_arrival, rejected_on_arrival)» (`log:242-258`) | `BR-20` (`a759a17`; `backend/app/operations/validators.py:536-565`) — posterior a la certificación P-03 (2026-09-06) |
| 3 | `e2e/proceso-p04-reproductoras-huevo-fertil.spec.ts:71` (`:76-82`) | ídem BR-20 (`log:270-286`) | ídem — P-04 certificada 2026-09-05 |
| 4 | `e2e/proceso-p05-incubacion.spec.ts:60` (`:73`) | `birth_registration` → **400 BR-21** «declara los pollitos sanos y los débiles (falta: chicks_healthy, chicks_weak)» y en cascada `chick_dispatch` → **400 BR-04** «viables disponibles (0)» (`log:298-320`) | `BR-21` (`c653ff8`; `validators.py:577-613`) — P-05 certificada 2026-09-05 |
| 5-9 | `e2e/proceso-p10-trazabilidad-generacional.spec.ts:73,145,167,186,203` (helper `tresGeneraciones` `:56-61`) | **400 BR-21** en el nacimiento del helper (`log:332-475`) | ídem — P-10 certificada 2026-09-05 |
| 10 | `e2e/proceso-p11-activacion-manual-de-lotes.spec.ts:160` (`:165-170`) | **400 BR-20** (`crearLoteHistorico` crea `bird_type: 'breeder'`, `:71`) (`log:477-503`) | ídem BR-20 — P-11 certificada 2026-09-05 |
| 11 | `e2e/proceso-p11-…spec.ts:210` (`:255`) | «el sujeto debe estar en la empresa B» `Expected: 2 · Received: 1` (`log:505-531`) | `R-118`/`OD-14.c`: `POST /users` toma la empresa **del contexto del actor** e ignora `company_id` del cuerpo (`backend/app/auth/service.py:349-357`); el fixture crea rol y usuario con la cabecera del admin situado en A (`:224-248`) |
| 12 | `e2e/proceso-p15-reportes-e-indicadores.spec.ts:28` (`:33-41`) | `incubation_load` → **400 BR-03** «Carga (1000) excede los huevos disponibles en incubadora (800)» (`log:533-557`) | `R-172`/`RR-17` (`64dff76`): sólo el huevo **fértil** es disponibilidad (`validators.py` `cuenta_como_disponible`, `TIPO_DISPONIBLE = "fertile"`); el fixture recibe 800 fértiles + 200 infértiles y carga 1000 |

**Consecuencia**: las certificaciones **P-03, P-04, P-05, P-10, P-11 y P-15 no son reproducibles en HEAD**. Desde 2026-09-05 hay **85 commits** que tocan `backend/app` o `frontend/src` (`git log --since=2026-09-05 -- backend/app frontend/src`).

### 2.3 CI — la suite «declarada a CI» nunca se ha ejecutado

- `.github/workflows/backend-ci.yml:4-12`: `on: pull_request` con comentario «Los tests corren SOLO en Pull Requests, NUNCA en push directo a main»; ídem `frontend-ci.yml:8-15`.
- `git log --merges --oneline | wc -l` = **0** de **466** commits: toda la historia son pushes directos a `main`.
- `.github/workflows/quality-gates.yml:17-21` sí corre en `push` a `main`, pero su job `backend-quality` (`:24-67`) sólo ejecuta `compileall`, la integridad Alembic, `tests/test_environment_guard.py` y un `grep` de credenciales: **no ejecuta la suite**. `GA-REM-013` figura `CERTIFIED` (`INDEX.md:20`) aunque su `AC05` («el gate de tests de backend se ejecuta de verdad… los 76 tests») sólo lo cubre `backend-ci.yml`, que no se dispara.
- Afirmaciones huérfanas: `test_r188_bu_lifecycle.py:14-16` («corre en CI con `backend/scripts/run_tests.sh`»), `GA_BU_D10_CERTIFICATION.md:37` («corren en CI»), `9ffc5ec` («frontera GET /lots para CI PG»), «1139 passed · 49 skipped · 0 failed (1028 s)» (`WAVE_B_TRANCHE_14_…EVIDENCE.md:186`, 2026-09-10) — desde entonces **125 commits** (`git log --since=2026-09-10 | wc -l`).
- Repositorio privado: la API de Actions responde 404 anónima; no verificable externamente y, por construcción, no ejecutado.

### 2.4 Certificaciones de proceso sin artefacto ni commit; veredictos contradictorios

- 13 ficheros: `audit/remediation/PROCESS-{01,02,03,04,05,06,09,10,11,12,13,14,15}-CERTIFICATION.md` (P-07 y P-08 sin fichero). `grep -cE '\b[0-9a-f]{7,40}\b'` = **0** en 12 de ellos; `grep -ciE '\.log|\.json|test-results|run_tests\.sh|scripts_e2e'` = **0** en los 13. P-14 cita `07e7410`, `a2e21da`, `846b1bf` (`:170,332`) como salvaguardas de reversión, no como HEAD certificado.
- Fechas: 2026-09-05 (P-02, P-04, P-05, P-10, P-11), 2026-09-06 (P-01, P-03, P-06, P-09, P-12, P-13, P-15), P-14 sin fecha.
- Contradicciones internas: **P-03** (`:6` `CERTIFIED`; `:10-13` «declaración prematura… volvió a PARTIAL… vuelve a CERTIFIED»; `:16-17` «sustituye… `PARTIAL — BLOCKED_BY_REQUIREMENT`»), **P-06** (`:8` `PARTIAL — BLOCKED_BY_DEFECT (R-76)`; `:38` y `:112` `CERTIFIED`), **P-10** (`:6` `CERTIFIED`; `:9` primera versión `PARTIAL — BLOCKED_BY_DEFECT`; `:50` tabla vigente «PASS 7 · FAIL 1 · BLOCKED 3»), **P-14** (`:6` `CERTIFIED 6 de los 6`; `:13` «cinco de seis sigue sin ser seis»; `:19` «no queda certificado»; `:247` `BLOCKED_BY_MODEL_GAP`; `:367,507` `CERTIFIED`).
- `GA-REM-016` (spec que ampara estas certificaciones): `INDEX.md:26` `SPEC_DRAFT` «en uso por 15 informes de certificación»; `REMEDIATION_BACKLOG.md:30` `SPEC_DRAFT`; el propio fichero `:7` `PARTIALLY CERTIFIED (Wave 3, 2026-09-04)`.

### 2.5 Aceptaciones del propietario sin evidencia primaria

Registros: `audit/ga-uat-07/GA_OWNER_ACCEPTANCE_R187_RECORD.md`, `audit/ga-uat-08/GA_OWNER_ACCEPTANCE_R188_BU_D10_RECORD.md`, `audit/ga-fe-08/GA_OWNER_ACCEPTANCE_FE08_RECORD.md` (misma estructura en GA-UAT-01…06).

| Observación | Medición (esta sesión) |
|---|---|
| Walkthrough ejecutado por el agente, no por el propietario | `evidence/walkthrough-uat.json` con claves `pages`/`ui`/`steps`/`console` y un único `ts` (UAT-07 `2026-09-11T18:50:41Z`, UAT-08 `19:45:59Z`, FE-08 `e2e-uat.json` `20:07:20Z`); ningún artefacto producido por el propietario (mensaje, captura propia, grabación, `LOGIN` de su usuario en `audit_logs`) |
| Capturas duplicadas byte a byte (md5) | UAT-07: `UI-C03-reporte-lote-54` ≡ `UI-C04-tras-refresh` (`852ea1e5…`), `UI-C01-detalle-lote-54` ≡ `UI-C05-tras-relogin` (`e2a8d2f7…`). UAT-08: `C01-BUON-con-acceso` ≡ `C05-regrant-acceso-restaurado` (`63ef6768…`), `C02-BUOFF-sin-acceso` ≡ `C03-reenable-historico-sin-acceso` (`86e01223…`), y `C07-movil-con-acceso` ≡ `audit/ga-uat-07/evidence/UI-C06-movil-detalle-54.png` (`fe1aa38e…`, **mismo fichero en dos UAT distintos**). FE-08: `C01-hub-lotes-visible` ≡ `C07-fresh-grant-nav-restored` (`47dcc860…`), `C05-buoff-nav-absent` ≡ `C06-reenable-historical-absent` (`d3c02a5e…`). Las capturas de casos distintos no discriminan el caso |
| Ventanas de captura | mtime de los PNG: UAT-07 7 capturas en **34 s** (20:50:53→20:51:27), UAT-08 9 en **64 s** (21:46:12→21:47:15), FE-08 13 en **531 s** (la validación previa registró «17–173 s», `GA_CLAUDE_FINAL_AUDIT_CURRENT_STATE.md:63`) |
| Limpieza antes de la decisión | UAT-07: paquete C1 `d1f9829` 20:53:19 +0200 → `cleanup-uat.json ts` 21:01:19 → decisión C2 `8e91532` 21:02:12 (el registro `§5` y la evidencia `§G` dicen «ejecutada tras la decisión»). UAT-08: C1 `a2fe22a` 21:47:57 → limpieza 21:48:43 (**+46 s**) → C2 `30fe3dc` 21:50:10. FE-08: limpieza 22:10:15 **antes** de la evidencia C3 `a6d4afb` 22:11:24 y de la aceptación C4 `4b498dd` 22:14:09 (`GA_OWNER_ACCEPTANCE_FE08_RECORD.md:26` «Limpieza ya ejecutada y verificada»). Con usuarios de baja, roles desactivados y BU en OFF, el propietario no pudo recorrer los casos en el momento de decidir |
| PASS por caso derivado de una «A» global | UAT-07 `§3` «UAT-06 aceptación global → A» y «6/6 casos»; UAT-08 `§2` cinco `PASS` con «sin observaciones (opción sin texto libre)»; FE-08 `§2` 5/5 `PASS` con «sin observaciones» |

### 2.6 Backlog y decisiones sin hogar canónico

- `grep -c "R-189" audit/remediation/REMEDIATION_BACKLOG.md` = **0**; `grep -c "GA-UAT-09"` = **0**. `R-189` vive en `audit/ga-f01/` (`R189_IMPORT_RECEPTION_FORM_CONTRACT_SPEC.md`, `R189_PLAN_CHECKLIST_TASKS.md`, `GA_F01_RUNTIME_CERTIFICATION.md`); `GA-UAT-09` en `audit/ga-r153/uat/GA_OWNER_UAT_R153_RETRY_REFERENCE.md`.
- `ls specs/remediation/ | grep ^OD-` termina en `OD-20`; `OD-21` (`audit/ga-uat-05/GA_OWNER_ACCEPTANCE_GA_FE_07_RECORD.md`, `audit/ga-fe-07/GA_FE_07_INACTIVE_AREA_REFERENCE_SPEC.md`), `OD-22` (`audit/ga-od-01/GA_OD_IPE_SCALE_OWNER_DECISION.md`), `OD-23` (`audit/ga-bu-d10/GA_BU_D10_LIFECYCLE_SPEC.md`), `OD-24` (`audit/final-frontend-audit/GA_OD_24_COMPANIES_FARMS_OWNERSHIP_DECISION.md`), `OD-25` (`audit/final-frontend-audit/GA_AOD25_OWNER_DECISION_PACKET.md`, `audit/ga-r153/`) no tienen fichero `specs/remediation/OD-2x-*.md` ni fila en `INDEX.md` (`grep -n "OD-2[1-5]" INDEX.md` = 0).
- Los artefactos de esta auditoría (`backend_full_suite.log`, `backend_targeted_failing.log`, `backend_r188_me500.log`, `playwright_e2e.log`, `frontend_checks.log`, `runtime-gp-e2e.json`, `ui-e2e-local-pass*.json`) están registrados como `audit/ga-claude-final-audit/evidence/` en el registro (`:11`), pero al redactar este paquete `ls evidence/` está **vacío**: su materialización es el primer criterio de cierre (regla «no GREEN por declaración» aplicada a la propia auditoría).

### 2.7 Lo que sí está verde

`evidence/frontend_checks.log`: Vitest **314/314** (44 ficheros, `:10-11`), `tsc` exit 0 (`:17`), build OK (`:33-34`). Paridad bundle/backend runtime PASS (registro `:149`).

## 3 · Clasificación (§51)

| Ítem | Clase |
|---|---|
| 25 fallos backend | `TEST_DEFECT` ×25 (A 17 · B 5 · C 3) — 0 `APP_DEFECT` directo; `R-213` es colateral y tiene paquete propio |
| 12 fallos Playwright | `TEST_DEFECT` ×12 (11 fixtures obsoletos frente a BR-20/BR-21/BR-03/R-118 + 1 locator ambiguo) |
| CI sólo en PR | `GOVERNANCE` — declaración sin ejecución |
| Certificaciones sin artefacto | `GOVERNANCE` — `STALE`/`NOT_REPRODUCIBLE` |
| Aceptaciones sin evidencia primaria | `GOVERNANCE` — `UNSUPPORTED` |
| Backlog/OD sin hogar | `GOVERNANCE` — deriva documental |

## 4 · Impacto

Sin una suite verde reproducible con artefacto y commit, ninguna de las certificaciones vigentes es una prueba de estado (§52 «final readiness must reflect current product»), la cola de remediación (registro `§3`, orden 1) no puede arrancar con una línea base fiable, y el veredicto GO/NO-GO pre-SAP no es defendible. El coste de subsanación es bajo (cambios sólo en `backend/tests/`, `e2e/`, `.github/workflows/`, `backend/scripts/`, documentación) y no toca producto.

## 5 · Paquete

`GA-GOV-03_SPEC.md` · `GA-GOV-03_CLARIFICATIONS.md` · `GA-GOV-03_PLAN_CHECKLIST_TASKS.md` · `GA-GOV-03_AC_MATRIX.md` · `GA-GOV-03_RED_E2E_UAT_DESIGN.md`.
