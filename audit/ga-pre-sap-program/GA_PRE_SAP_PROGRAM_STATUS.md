# GA · PRE-SAP — ESTADO DEL PROGRAMA (TRANCHE 0 · cierre)

Fecha: 2026-09-13 · Baseline: `f270d0b` (+ commits de governance de T0) · Fase: **T1 CERRADA (AC-06 = PASS) · T2 CERRADA (certificación con CI run #26) · T3 CERRADA TÉCNICAMENTE (`9cb075f`) · T4 CERRADA TÉCNICAMENTE (`4a08382`) — T5 en arranque automático**.

## 1 · KPI del programa

| KPI | Valor | Meta de cierre |
|---|---|---|
| Procesos certificados E2E | **0 / 17** | 17/17 |
| Brechas bloqueantes abiertas | **24** (9 P1 + 15 P2) + GA-GOV-03 | 0 |
| Otras brechas abiertas | 10 (7 P2 no bloqueantes + 3 P3, incl. R-214) | cerradas o aceptadas |
| Heredados que bloquean/condicionan | 36 filas (incl. 4 sin spec: Wave C P1 + condicionales por decisión) | resueltos por decisión/rider |
| Suites | **0 rojos** — backend 1263/0/0/49 (JUnit CI T2: 1312 total) · Playwright 129/0 · vitest 318/318 | mantenido en cada tranche |
| CI de tests | `Quality Suite (push)` **VERDE observado** — run #26 `34778950665` (`5044788`): backend ✅ 24m25s + frontend ✅ 1m1s; artefactos descargados y sha256-verificados (1312/0/0/49 · 318/0); `evidence/t2-ci-run.json`. Historial honesto de T2: #21/#24 rojos **por diseño** (RED) y #25 rojo por pines del harness, remediado en `5044788` (#26 verde) | mantenido en cada push |
| Certificaciones con artefacto | informes históricos anotados `NOT_REPRODUCIBLE_EN_HEAD (pre-GA-GOV-03)`; plantilla de evidencia vigente | nuevas certificaciones con commit+artefacto (regla ya aplicada a T1) |
| UAT con evidencia primaria | 0 de 11 registros + 2 pendientes | 8 lotes finales completos |
| Decisiones del propietario pendientes (alcance actual) | 14 (+4 por tranche según roadmap) | registradas antes de su tranche |
| Tranches del programa | T0 **CERRADA** (`e828c3a`); **T1 = CLOSED** (AC-06 = PASS; run #10 `60e9d9d`); **T2 = CLOSED** (5 specs + rider AC04; run #26 `5044788`); **T3 = CLOSED_TECHNICALLY** (`9cb075f`; R-201 · R-203 · R-204(+R-216) · R-221 parcial — AC-04 en cola AOD-13); **T4 = CLOSED_TECHNICALLY** (`4a08382`; R-190 · R-205); **T5 = READY_FOR_EXECUTION**; T6-T13 + Pista OPS planificadas | todas cerradas |
| Veredicto pre-SAP | `NO_GO_SAP_FUNCTIONAL_GAPS` (sin cambios) | GO/NO-GO final en T13 |

## 2 · Estado por tranche

| Tranche | Estado | Nota |
|---|---|---|
| T0 · Cierre de auditoría + programa | **CERRADA** (`e828c3a`, 2026-09-13) | 15 documentos del programa + correcciones D-03 |
| T1 · GA-GOV-03 | **CERRADA** (2026-09-13) | 38/38 TEST_DEFECT (37 + nº38 hallado en CI); suites verdes en local **y en CI** (run #10 `34764423545`, `60e9d9d`); **AC-06 = PASS** (artefactos sha256-verificados) ⇒ `CLOSED_FUNCTIONALLY_CERTIFIED` |
| T2 · Fundación de seguridad | **CERRADA** (2026-09-13) | R-199 · R-200 · R-202 · R-208 · GA-REM-003 AC04 — certificaciones por spec; suite completa `1263/0/49` local y **CI run #26 verde** (`5044788`; artefactos sha256-verificados) ⇒ `GA_T2_CERTIFICATION.md`. Límites declarados: **G-06** (C3 runtime de R-199/R-202, cola del propietario); GA-REM-003 AC01/02/03/05/06-resto/07 siguen su recorrido |
| T3 · Alcance de datos | **CLOSED_TECHNICALLY** (`9cb075f`, 2026-09-14) | R-201 · R-203 · R-204(+R-216) cerradas — RED→GREEN→sensibilidad por spec; suite completa `1286/0/49` (`evidence/t3/full_suite_t3.log`) ⇒ `GA_T3_CERTIFICATION.md`. **R-221 parcial**: AC-01/02/03/05 cerradas (`8126f97`→`b056ef1`); AC-04 espera **AOD-13** (C-02, opciones A/B/C en cola). Límite declarado: **G-06** (C3 runtime de R-201/203/204/216) |
| T4 · Operación (R-190 + R-205) | **CLOSED_TECHNICALLY** (`4a08382`, 2026-09-14) | R-190 (ubicación del evento: `a79fe0c`→`d1c16a7`→`801d18c`; S1-S4) · R-205 (cuadre alcanzable: `fe3bd3d`→`72aa7f4`→`dbc782d`; S1-S3); F-01e 4/4 intacto; **suite BE 1295/0/49** (`evidence/t4/…`) · **FE 360/360** + tsc 0 + build ⇒ `GA_T4_CERTIFICATION.md`. Límite: C3 runtime (deploy/credenciales — familia G-06); C-03 de R-190 opcional del propietario |
| T5 · Contrato de captura (R-191 · R-206 · R-209 · R-210) | **READY_FOR_EXECUTION** | Arranque automático tras T4 (DAG: T5 ← T4, satisfecho); R-146 si AOD-16 |
| T6-T13 + OPS | PLANIFICADAS | Orden y gates en el roadmap maestro |

## 3 · NEXT_IMPLEMENTATION_TRANCHE (§52) — siguiente tras T1

**GATE SATISFECHO**: **AC-06 = PASS** (run #10 `34764423545`, `60e9d9d`: enlace + ambos jobs verdes + artefactos con sha256 verificado; `GA_GOV_03_CI_EVIDENCE.md §4.2`) ⇒ **T2 AUTORIZADA — arranca a continuación** (autorización autónoma vigente).

- **ID**: `T2` · **Nombre**: Fundación de seguridad y sesión (auth/roles/permisos).
- **Specs**: `R-199` · `R-200` · `R-202` · `R-208` (+ rider `GA-REM-003 AC04` — logout con revocación).
- **Findings**: R-199 (P1 — un rol de inquilino no puede fabricar autoridad global), R-200 (refresh aceptado como access), R-202 (reset de contraseña sin contexto), R-208 (permisos batch ≠ unitarios), P1-4/AC04 (no existe logout servidor; refresh robado vive 7 días).
- **Prioridad**: **P1 seguridad** — la fundación de seguridad se ejecuta primero (T2 del roadmap maestro).
- **Dependencias**: **T1 cerrada** ✔ (suites verdes). Decisión habilitante a registrar antes del merge de R-199: **`OD-13.c`** (¿puede existir `("*", all)` en roles de inquilino? propuesta del programa: NO).
- **Alcance**:
  1. R-199: validación de la forma de permisos en `create_role`/`update_role` (sin wildcard de inquilino).
  2. R-200: chequeo del `type` del token en la ruta de access (`decode_token`).
  3. GA-REM-003 AC04: `POST /logout` con denylist de `jti` + auditoría `LOGOUT` (mismo ciclo de tokens que R-200).
  4. R-202: reset de contraseña con contexto de empresa.
  5. R-208: dependencias de permiso de `batch-approve`/`batch-reject` alineadas con las rutas unitarias.
- **Fuera de alcance**: el resto de tranches (T3+); el fix de lectura de `/me` (R-213 → T11); decisiones de negocio.
- **Ficheros esperados**: `backend/app/auth/service.py`, `backend/app/auth/security.py`, `backend/app/auth/router.py`, `backend/app/review/router.py` (solo permisos), tests de seguridad nuevos por spec, evidencia en `audit/ga-pre-sap-program/evidence/`.
- **Tests**: ataques de cada spec bloqueados (RED→GREEN) + suites completas verdes con artefacto; regresión OD-14/OD-16 obligatoria.
- **Runtime**: deploy por el flujo vigente (EX-01); paridad bundle/marcadores al cierre de la tranche.
- **UAT del propietario**: lote **U1** de T13 (no bloquea el cierre técnico de T2).
- **Criterio de salida**: los 4 ataques bloqueados con test verde; suites verdes con artefacto; `OD-13.c` registrada; evidencia en el hogar del programa.

## 4 · Repositorio y siguiente paso

- Material del programa: `audit/ga-pre-sap-program/` (T0 + T1 + registros de ejecución autónoma) + correcciones D-03 en el paquete de auditoría; **producto diff acumulado = 0**.
- T1 cerrada con AC-06 = PASS observado. Con la autorización autónoma vigente (prompt maestro del propietario, 2026-09-13), **T2 arranca automáticamente** (criterio de salida definido arriba).

## 5 · Ejecución autónoma (2026-09-13 06:08 +0200) — `PROGRAM_EXECUTION_BLOCKED_BY_OWNER_GATE`

- **Intento final de AC-06 por vías legítimas**: SIN VÍA — navegador integrado sin sesión de GitHub (404 + «Sign in»), `gh`/`glab` ausentes, sin tokens, API anónima 404; sin búsqueda de credenciales. AC-06 sigue `BLOCKED_EXTERNAL_CI_OBSERVATION`; T1 `PARTIAL`.
- **DAG consultado (9 documentos canónicos)**: T2-T13 dependen de T1 (o transitivamente; GA-GOV-03 es el gate de arranque) ⇒ **ninguna tranche independiente ejecutable**; T2 NO iniciada. **Pista OPS** (única línea independiente, «arrancable ya»): declarada **owner/ops** (acciones fuera del código) ⇒ encolada en `GA_OWNER_GATE_QUEUE.md` (bloquea solo T13).
- **OD-13.c verificada**: **ya resuelta** en la gobernanza vigente (`specs/remediation/OD-13-ROLE-AND-PERMISSION-TENANCY.md §3`, 2026-09-08) — sin decisión redundante del propietario.
- **Único gate inmediato**: `AC-06 (evidencia externa de CI)`.
- **Registros**: `GA_AUTONOMOUS_EXECUTION_LEDGER.md` (AE-01…AE-05; AE-05 = continuación 06:19-06:21 sin sesión disponible) · `GA_OWNER_GATE_QUEUE.md` (G-01…G-05 + programados §25). Commit docs-only sobre `a3b53a8`.
- Sin cambios de producto/tests/CI/migraciones; KPI `0/17` sin cambio; veredicto `NO_GO_SAP_FUNCTIONAL_GAPS` sin cambio.
- **Actualización (2026-09-13 15:45 +0200) — AC-06 observado + remediación CI completa**: los runs están **ROJOS** (incl. `66be1c1`) ⇒ **AC-06 = FAIL observado**. Causas clasificadas y corregidas (solo `.github/workflows/quality-suite.yml`): backend — `pip install -e` flat-layout ⇒ **C3**; frontend — peer `@testing-library/dom` ausente por `--legacy-peer-deps` (27 fallos reales del run #1) ⇒ **C4** (**validado: run #8, `frontend-suite` VERDE**). Backend run #7: `25F/1192P/58S` — todos por flag SAP ausente ⇒ **C5** (`FEATURE_SAP_ENABLED=true`; A/B local 201→211) pusheado. Run #9: C5 ✓ (`1F/1225P/49S`; 24/25) · resto = **TEST_DEFECT nº38** (`r188`, orden de lectura) ⇒ **C6** (test determinista; local 10/10). Con el run #10 VERDE ⇒ AC-06 = PASS ⇒ T1 cierra. Producto/migraciones sin cambio (C6: solo test).
- **Cierre (2026-09-13 ~17:25 +0200) — RUN #10 VERDE ⇒ T1 CERRADA**: run #10 `34764423545` (`60e9d9d`, C6) = `Success` (backend ✅ 21m42s · frontend ✅ 1m22s); artefactos descargados y **sha256 recomputado == digest de GitHub** (backend JUnit `1275/0/0/49`; frontend `314/0`). **AC-06 = PASS** ⇒ GA-GOV-03 `CLOSED_FUNCTIONALLY_CERTIFIED` ⇒ **T1 CLOSED** ⇒ `QUALITY_GATES_READY = YES` ⇒ **T2 READY_FOR_EXECUTION (arranque automático)**. KPI de procesos sin cambio: **0/17**.
