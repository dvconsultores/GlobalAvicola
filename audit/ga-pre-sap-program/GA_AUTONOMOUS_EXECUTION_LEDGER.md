# GA · PRE-SAP — LEDGER DE EJECUCIÓN AUTÓNOMA

Programa autónomo autorizado por el propietario («AUTONOMOUS PRE-SAP COMPLETION PROGRAM», prompt maestro 2026-09-13).
**Estado de ejecución: `PROGRAM_EXECUTION_BLOCKED_BY_OWNER_GATE`** — único gate inmediato: **AC-06 (evidencia externa de CI)**.
Cada entrada registra SHA de inicio/fin, documentos consultados, resultado, evidencia y siguiente dependencia (§46). Sin fabricación de decisiones, UAT ni evidencia externa (§2/§58).

---

## AE-01 · 2026-09-13 · Arranque autónomo — PRE-FLIGHT (§55.1-2)

- **Start SHA**: `a3b53a8` (== `origin/main`; rama `main`; worktree limpio; drift `a3b53a8..HEAD` = 0; `ls-remote` coincide).
- **Estado inicial verificado** (coincide con el declarado): GA-GOV-03 = `CERTIFICATION_PENDING_AC06` · T1 = `PARTIAL / BLOCKED_EXTERNAL_CI_OBSERVATION` · QUALITY_GATES_READY = `PARTIAL` · T2-T13 + Pista OPS planificadas · procesos `0/17` · SAP `NOT_STARTED` · `NO_GO_SAP_FUNCTIONAL_GAPS`.
- **Specs/findings/tests/runtime**: sin nueva ejecución en este arranque (no requerida para los pasos 1-2).

## AE-02 · 2026-09-13 06:01-06:08 +0200 · AC-06 — INTENTO FINAL POR VÍAS LEGÍTIMAS (§10)

- **Vías probadas** (solo mecanismos legítimos ya disponibles; sin buscar credenciales, cookies, historial ni stores — §10/§31):
  1. **Navegador integrado** (pestaña compartida, recargada 06:08): `github.com/dvconsultores/GlobalAvicola/actions?query=branch%3Amain` → **404 «Page not found» + «Sign in»** (repo privado; sin sesión de GitHub en el navegador integrado ⇒ ninguna página de run observable).
  2. **CLI**: `gh` ABSENT · `glab` ABSENT.
  3. **Tokens de entorno**: `GITHUB_TOKEN` UNSET · `GH_TOKEN` UNSET.
  4. **API anónima** (06:01): `api.github.com/repos/dvconsultores/GlobalAvicola/actions/runs?head_sha=66be1c15…` → **404 Not Found**.
- **Resultado**: AC-06 continúa **`BLOCKED_EXTERNAL_CI_OBSERVATION`**; T1 sin cierre; **no se fabrica evidencia externa** (§9/§58).
- **End SHA**: `a3b53a8` (sin cambios). **Evidencia**: esta entrada + `GA_OWNER_GATE_QUEUE.md` §G-01.

## AE-03 · 2026-09-13 · CONSULTA DEL DAG CANÓNICO — ¿TRANCHES INDEPENDIENTES? (§11/§12)

- **Documentos consultados** (9 canónicos + registros): `GA_PRE_SAP_REMEDIATION_MASTER_ROADMAP.md` · `GA_PRE_SAP_TRANCHE_GROUPING_PROPOSAL.md` · `GA_PRE_SAP_PROGRAM_STATUS.md` · `GA_PRE_SAP_BLOCKING_FINDING_MATRIX.md` · `GA_PRE_SAP_SPEC_DEPENDENCY_GRAPH.md` · `GA_PRE_SAP_PROCESS_DEPENDENCY_GRAPH.md` · `GA_PRE_SAP_SPEC_READINESS_MATRIX.md` · `GA_PRE_SAP_SECURITY_DEPENDENCY_MATRIX.md` · `GA_PRE_SAP_SHARED_TOUCHPOINT_MATRIX.md` · `specs/remediation/OD-13-ROLE-AND-PERMISSION-TENANCY.md` · `specs/remediation/GA-REM-004-CREDENTIALS-AND-TEST-ACCOUNTS.md` · `audit/remediation/GA-REM-004-CERTIFICATION-REPORT.md`.
- **Dependencias (fuente autoritativa = roadmap maestro §1)**: T2 ← T1 · T3 ← T1 · T4 ← T2+T3 · T5…T13 en cadena; GA-GOV-03 es «el gate de arranque» (grafo de specs §1) y la fila T1 marca «**T2-T13 bloqueadas hasta AC-06 = PASS**» ⇒ **ninguna tranche T2-T13 es ejecutable hoy**. **T2 NO se inicia** (gate literal no satisfecho; §11).
- **Pista OPS** (única línea con dependencia «—»; «arrancable ya»): sus ítems son acciones **owner/ops fuera del código**, no ejecutables sin acceso al host: R-52 volumen `avicola-media` · GA-REM-004 AC03 (rate limit runtime) · AC07 (rol BD mínimo + SSL) · P1-6 (respaldo). ⇒ **Encolada** en `GA_OWNER_GATE_QUEUE.md` (G-02…G-05); no ejecutada por el agente.
- **OD-13.c (pre-check §15)**: **YA RESUELTA** en gobernanza canónica — `specs/remediation/OD-13-ROLE-AND-PERMISSION-TENANCY.md §3` (2026-09-08, VIGENTE): «se prohíbe fabricar autoridad global desde una superficie de empresa» · «ROL QUE CONFIERE AUTORIDAD GLOBAL (`module="*"` + `scope_type="all"`) → SOLO la autoridad global lo asigna». R-199 la implementa en T2. **No requiere decisión redundante del propietario** (§15; sin owner-gate falso, §7).
- **Conclusión**: no existe tranche independiente ejecutable por el agente.

## AE-04 · 2026-09-13 · ESTADO `PROGRAM_EXECUTION_BLOCKED_BY_OWNER_GATE` (§11)

- **Set**: estado de ejecución = **`PROGRAM_EXECUTION_BLOCKED_BY_OWNER_GATE`**; registro exacto: «**AC-06 (evidencia externa de CI) es el único gate inmediato**».
- **Calidad**: no se ejecutaron suites (cambio solo documental; última certificación técnica = T1 `66be1c1`, artefactos en `evidence/`). Producto/tests/CI/migraciones: diff 0.
- **Registros**: `GA_OWNER_GATE_QUEUE.md` · `GA_PRE_SAP_PROGRAM_STATUS.md §5`.
- **Auto-audit (§54)**: sin cambios fuera de spec ✔ · sin debilitar tests ✔ · sin bypass de tenencia ✔ · sin ocultar fallos ✔ · sin evidencia inventada ✔ · sin cambios de auto-deploy (§29/EX-01) ✔ · historial git intacto ✔ · local == remoto ✔ · worktree limpio ✔.
- **Git**: commit único docs-only sobre `a3b53a8` («GA pre-SAP autonomo: …»); push verificado (`local == remote`).
- **Parada**: §11/§56.A — sin trabajo seguro independiente restante. **STOP** (único gate inmediato: AC-06).
- **Siguiente dependencia**: AC-06 = PASS (acción del propietario — G-01) → T1 CLOSED → **T2 arranca automáticamente** (autorización autónoma vigente).

## AE-05 · 2026-09-13 06:19-06:21 +0200 · CONTINUACIÓN AUTORIZADA — VERIFICACIÓN DE LA SESIÓN PARA AC-06

- **Pre-flight (§2 del prompt de continuación)**: HEAD `4df4732` == `origin/main`; worktree limpio; 0 commits después de `4df4732`; sin drift de producto ⇒ no aplica `PROGRAM_BLOCKED_BY_PRODUCT_DRIFT`.
- **Autorización registrada**: el propietario autoriza la lectura directa del run `66be1c1` por el agente desde la «sesión autenticada del navegador integrado», con registro `AGENT_OBSERVED_GITHUB_EVIDENCE` — aplicable **solo si dicha sesión existe**.
- **Verificación de la sesión declarada (06:20 +0200)**: navegación fresca a `github.com/dvconsultores/GlobalAvicola/actions/workflows/quality-suite.yml` → **404 «Page not found» + «Sign in»** (repo privado; navegador integrado **sin sesión de GitHub**) ⇒ la sesión autenticada declarada **no está disponible** en el entorno del agente.
- **Vías adicionales (06:21 +0200)**: `gh` ABSENT · `glab` ABSENT · `GITHUB_TOKEN` UNSET · `GH_TOKEN` UNSET · propuesta de compartir otra página abierta: sin página compartida.
- **Resultado**: **AC-06 NO observable**; no se generó evidencia `AGENT_OBSERVED_GITHUB_EVIDENCE`; **sin fabricación** (§5/§75). AC-06 sigue `BLOCKED_EXTERNAL_CI_OBSERVATION`; T1 `PARTIAL`; T2 no iniciada; diffs de producto/tests/CI/migraciones = 0.
- **Acción mínima pendiente (G-01)**: (A) iniciar sesión el propietario en el navegador integrado (la pestaña ya apunta a la página de Actions; «Sign in» regresa a ella) — el agente lee el run y cierra AC-06 automáticamente; o (B) entregar los 5 valores (Run URL · Run ID · nombres exactos de artefactos · timestamp).
- **Parada**: §65-A/C — el gate humano (sesión o valores) bloquea todo el trabajo autónomo restante.
- **Re-verificación tras «LISTO» del propietario (06:25 +0200)**: HEAD `e2293fd` == `origin/main` (sin drift de producto; único commit tras `4df4732` = este registro). Navegación fresca a la página de runs del repo privado → **idéntico 404 «Page not found» + «Sign in»** (el contexto del agente sigue sin sesión). Segundo intento de compartir página abierta: sin página compartida. ⇒ **La sesión iniciada por el propietario no está en el contexto del navegador que las herramientas del agente pueden usar** (probable: iniciada en otra ventana/pestaña u otro navegador — no accesible al agente). **La pestaña controlada por el agente queda EN la página de inicio de sesión de GitHub** (`/login?return_to=…quality-suite.yml`): completar el inicio de sesión EN esa pestaña (o entregar los 5 valores) es la vía mínima pendiente. Sin fabricación; estados sin cambio (AC-06 pendiente · T1 `PARTIAL` · T2 no iniciada).

## AE-06 · 2026-09-13 (tarde) · AC-06 — OBSERVACIÓN DIRECTA: RUNS EN ROJO (REMEDIACIÓN EN CURSO)

- **Observación directa** (sesión autorizada del propietario; página de runs del workflow en el navegador integrado): los runs de `quality-suite.yml` figuran **ROJOS**; **Run #1 del SHA `66be1c1`**: job `backend-suite` **failed** (~1m24s) y `frontend-suite` **failed** (~58s); **artefacto backend AUSENTE** («No files were found… backend-junit.xml»); artefacto frontend presente (≈8,79 KB). ⇒ **AC-06 = FAIL observado**; la declaración previa `success`/`success`/`success` queda **contradicha** por la observación real (sin fabricación).
- **Causa raíz backend (clasificada + reproducida)**: el paso `pip install -e ".[dev]"` falla siempre — setuptools no puede auto-descubrir el paquete (flat-layout: `app`/`seeds`; `backend/pyproject.toml` sin `[tool.setuptools]`) ⇒ el job muere en el paso 1 y **la suite nunca corrió en CI**.
- **Corrección C3 (solo `.github/workflows/quality-suite.yml`; validada localmente extremo a extremo)**: `pip install uv==0.11.23` → `uv sync --frozen --python 3.11` → `uv pip install --python .venv/bin/python "pgserver==0.1.4"`. Detalle: sin `--python 3.11`, uv crea el venv con Python 3.14 y `pgserver` no tiene wheels cp314.
- **Pendiente**: clasificar `frontend-suite` (log requerido — navegador); re-captura de IDs/timestamps de runs; fix frontend; push; **observar runs VERDES** (solo entonces AC-06 = PASS ⇒ T1 cierra). Sin cambios de producto/tests/migraciones.

## AE-07 · 2026-09-13 (tarde) · FRONTEND CLASIFICADO + C4 — REMEDIACIÓN CI COMPLETA

- **Evidencia directa (run #1, `runs/34736026774`)**: job `frontend-suite` failed (58s); artefacto `frontend-suite-66be1c15d8c299e2746faf6b5f90fec77b9bc758` (8,79 KB) — único artefacto del run (el backend no generó). Artefacto leído (vía URL firmada obtenida en la sesión autorizada): su `vitest-junit.xml` reporta **27 fallos — todos `Cannot find module '@testing-library/dom'`** (require stack: `@testing-library/react/dist/pure.js`).
- **Causa raíz frontend**: `npm install --legacy-peer-deps` **no instala peer dependencies**; `@testing-library/dom` es peer de `@testing-library/react@16.3.2` (`^10.0.0`) y **no figura en `package.json`** — local existía (10.4.1) por instalaciones previas; en CI nunca se instaló ⇒ 27 archivos de test no pudieron cargar.
- **Corrección C4 (solo workflow; validada local)**: `npm install --legacy-peer-deps --no-save "@testing-library/dom@10.4.1"` (exit 0; worktree limpio; misma versión local que satisface el peer).
- **Inventario de runs (URLs/IDs, lectura directa)**: #1 `34736026774` failed 1m28s (`66be1c1`) · #2 `34736137140` 1m15s · #3 `34736367334` 1m9s · #4 `34737396643` 1m14s · #5 `34737731264` 1m0s · #6 `34737937732` 1m11s · **#7 `34759922772` (C3) en progreso**. Repro local del paso vitest (TZ=UTC): PASA 314/314 ⇒ confirma que el fallo era de instalación de dependencias, no de tests.
- **Pendiente**: observar #7 (valida C3 backend en CI) y #8 (C4, tras push) hasta **runs VERDES** ⇒ AC-06 = PASS ⇒ T1 cierra. Sin cambios de producto/tests/migraciones.

## AE-08 · 2026-09-13 (tarde-2) · BACKEND CLASIFICADO (FLAG SAP) + C5 · FRONTEND C4 VALIDADO EN CI

- **Run #8 (C4, `b5e39db`) — FRONTEND VERDE EN CI**: job `frontend-suite` **completed successfully** (1m 28s) — primera suite verde en CI (C4 validado; solo warning cosmético Node-20 de las actions). El backend del #8 seguía corriendo (fallará: C5 aún no estaba).
- **Run #7 (C3, `runs/34759922772`) — backend clasificado con evidencia real**: la instalación pasó (C3 ✓) y la suite completa corrió ~19m43s: **`25 failed, 1192 passed, 58 skipped`** (artefacto `backend-suite-f965e9c…`, JUnit + log). Los 25 fallos: `test_sap_transversal.py` (10), `test_purchase_order_receipt.py` (7), `test_rbac.py` (3), `test_notifications.py` (2), `test_notification_recipients.py` (1), `test_audit_coverage.py` (1), `test_population_invariant.py` (1: `assert 201 == 211`) — **todos por rutas `/api/v1/sap/*` ausentes (404)**; skips 58 = 49 + 9 (`test_sap.py`).
- **Causa raíz**: `FEATURE_SAP_ENABLED` no existe en CI. El router SAP se registra **solo** si el flag está activo (`app/main.py:145-147,167-168`; default `False` en `config.py:111`); local pasa porque `backend/.env:28` trae `true`; `run_tests.sh` no lo exporta. Aritmética exacta: 1192+25+9 = **1226** y 58−9 = **49** (idéntico a la certificación local).
- **Validación local A/B (enumerador canónico de la app)**: `FEATURE_SAP_ENABLED=false` ⇒ **201 rutas `/api/`** (reproduce `assert 201 == 211`) y **0 rutas SAP**; `=true` ⇒ **211 rutas** con las 10 rutas SAP (references/import, references, consolidate, consolidated, export, retry, sync/jobs, payloads, errors, connection-check). Flags audit/review/rate-limit coherentes (defaults `True/True/False` = `.env`).
- **Corrección C5 (solo workflow)**: `env: FEATURE_SAP_ENABLED: "true"` en el paso «Suite canónica» — CI reproduce la configuración certificada. Push ⇒ run #9.
- **Pendiente**: observar run #9 hasta **dos suites verdes** ⇒ AC-06 = PASS ⇒ cierre T1 (documentos §7 del prompt maestro). Sin cambios de producto/tests/migraciones; EX-01/deploy intactos.

## AE-09 · 2026-09-13 (tarde-3) · RUN #9 (C5 ✓ 24/25) + TEST_DEFECT 38 (r188) + C6

- **Run #9 (`runs/34761309595`, `e52cad3`, C5)**: `backend-suite` failed 22m10s · `frontend-suite` **verde** 1m21s · 2 artefactos (backend 31,3 KB · sha256 `9818e06f…`; frontend 16,9 KB). JUnit backend real: **`1 failed, 1225 passed, 49 skipped`** (1275 total = local exacto; skips 49 ✓). **C5 validado: 24 de 25 fallos resueltos** (211 rutas SAP presentes).
- **Fallo restante — `test_r188_bu_lifecycle.py::test_r188_auditoria_de_terminacion_por_ciclo`** (`assert 'none' == 'granted'`): el test lee los eventos de auditoría de la concesión **sin `ORDER BY`** (línea 226) y se queda con el último mediante `{e.action: e for e in eventos}` (línea 232), reteniendo el evento de concesión (`none→granted`) en lugar del de terminación (`granted→revoked`). PostgreSQL **no garantiza** el orden de lectura sin `ORDER BY`; el mismo test pasó en local (1226/0) y en el run #7 y falló en #9 con código idéntico ⇒ **TEST_DEFECT (nº38)**, no defecto de producto: `admin.py:205-217` emite la terminación con `previous_state="granted"`/`new_state="revoked"` y causa declarada. Patrón frágil **único** en la suite (grep).
- **Corrección C6 (solo test)**: selección determinista por semántica (`new_state == "revoked"`), afirmación de unicidad y asserts de contrato (POST 201 · PATCH disable 200). Validado local: `tests/test_r188_bu_lifecycle.py` → **10 passed** (12,48 s).
- **Pendiente**: push C6 ⇒ run #10 hasta **dos suites verdes** ⇒ AC-06 = PASS ⇒ cierre T1. Producto/migraciones sin cambio.

## AE-10 · 2026-09-13 (tarde-4) · RUN #10 VERDE — AC-06 = PASS · T1 CERRADA

- **Run #10 (`runs/34764423545`, `60e9d9d`, C6) — `Success`** (21m 46s; push 17:02 +0200): `backend-suite` **completed successfully** (21m 42s) · `frontend-suite` **completed successfully** (1m 22s). **Ambas suites verdes — run de cierre.**
- **Artefactos verificados criptográficamente (descargados; sha256 recomputado == digest publicado por GitHub)**: `backend-suite-60e9d9d…` (id `10321140011`, 29,6 KB, `bae675f2…`): JUnit `tests=1275 failures=0 errors=0 skipped=49` · log `1226 passed, 49 skipped in 1275.94s`. `frontend-suite-60e9d9d…` (id `10319729148`, 17 KB, `46dff85b…`): JUnit `tests=314 failures=0` · log `Test Files 44 passed (44)`. **Idéntico a la certificación local.**
- **Historia honesta (observada)**: runs #1-#6 rojos ⇒ C3 `f965e9c`; #7 `25F/1192P/58S` (flag SAP) ⇒ C5 `e52cad3`; #8 frontend verde (C4 `b5e39db`); #9 `1F/1225P/49S` ⇒ TEST_DEFECT nº38 ⇒ C6 `60e9d9d`; #10 **VERDE**.
- **Cierre de programa**: **AC-06 = PASS** ⇒ GA-GOV-03 `CLOSED_FUNCTIONALLY_CERTIFIED` ⇒ **T1 CLOSED** ⇒ `QUALITY_GATES_READY = YES` ⇒ **T2 = READY_FOR_EXECUTION**. Documentos actualizados: CI_EVIDENCE §4 · CERTIFICATION §5-§7 · T1_CLOSURE_RECONCILIATION · FINAL_TEST_RESULTS.json · RECOVERY_PLAN E1 · BLOCKING_FINDING_MATRIX · MASTER_ROADMAP T1 · PROGRAM_STATUS · OWNER_GATE_QUEUE G-01.
- Producto/migraciones: 0. KPI de procesos: **0/17** (T1 gobernanza; recertificación E2E = T12). G-01 de la cola de gates: **CLOSED** (G-02…G-05 OPS siguen `QUEUED`, bloquean solo T13).

## AE-11 · 2026-09-13 (tarde-5) · T2 INICIADA — R-199 · C1 (Gobernanza + RED) ✅

- **Run #11 (`34765778836`, `448b918`, C7 docs-only) = `Success`** (15m37s) — el HEAD de cierre también quedó verde en CI (además del run #10).
- **T2 arrancada** (fundación de seguridad): paquetes leídos en `audit/ga-claude-final-audit/specs/` (`R-199` 6f · `R-200` 6f · `R-202` compacto · `R-208` 6f — todos `SPEC_READY`). Ejecución iniciada por **R-199** (P1: fabricación de autoridad global desde un rol de inquilino; `GAP-01`).
- **R-199 · C1 (RED)** — nuevo `backend/tests/test_r199_global_authority_fabrication.py` (fixture `esc199`, PREFIJO `R199-`; `RED-01…06` + controles). **Verificado local: 9 rojas por el defecto** (01/02/03/04/05/06a/06b/06c + higiene CTL-10) **y 3 controles verdes** (CTL-07/08/09); cada roja falla en la aserción prevista (auditoría línea a línea del log). Evidencia: `audit/ga-claude-final-audit/evidence/r199/red_c1.log`.
- Nota de diseño: CTL-07 se corrigió durante C1 — el actor global **sin contexto** no crea usuarios por API («No hay empresa efectiva…»); el usuario del control se inserta directo (se prueba la capacidad del rol, no el alta).
- **El push de C1 deja el run de CI rojo por diseño** (ciclo canónico RED→GREEN); **C2 (implementación) restaura GREEN**. Criterio de cierre de T2: suites verdes + E2E runtime + sensibilidad + certificación.

## AE-12 · 2026-09-13 (noche) · R-199 C2 — IMPLEMENTACIÓN ✅ (GREEN 12/12 · suite 1238/0/49)

- **C2 implementado** (producto): `auth/service.py` (`_validar_permisos` antes de `db.add`/`sa_delete`; `_rol_asignable` exige `not _es_autoridad_global` también en la rama de inquilino; `_es_super_admin` añade `Role.company_id IS NULL`; asiento de rechazo `C-05` con `commit` propio, patrón `LOGIN_FAILED`) · `auth/security.py` (`get_current_user`: la capacidad global exige rol de sistema; `get_company_filter` retirado) · `auth/schemas.py` (`action: PermissionAction`; `scope_type: Literal[all,company,farm]`; `module` validado en servicio contra `MODULOS ∪ {"*"}`) · `dependencies.py` (re-export retirada).
- **GREEN dirigido: 12/12** (`green_r199_c2.log`); controles CTL-07/08/09 intactos; higiene CTL-10 pasa (grep de consumidores de `get_company_filter` = 0, solo bytecode).
- **Reconciliación de regresión (honesta)**: la primera corrida completa detectó **2 dependientes del contrato antiguo** — `test_r184_ac26_actor_global_no_bypassa_bu_off` y `test_r186_global_no_bypassa_bu_off` fabricaban su «actor global» con un rol de inquilino + comodín (el propio loophole que R-199 elimina). Barrido de clase (grep de los ~25 fixtures con `module="*"`): **solo esos 2** usaban `company_id=a.id`; el resto ya usaba plantilla de sistema (`NULL`). Adaptados ambos: `rol_global` ahora `company_id=None` con comentario `R-199`; propósito del test intacto. Logs: `full_suite_c2.log` (2F, registro de la detección) · `full_suite_c2b.log` (**1238/0/49**, verde).
- **Suite completa final: `1238 passed, 0 failed, 49 skipped` (20m59s)** — +12 = la suite R-199 nueva. **vitest 314/314** (`vitest_c2.log`; 0 ficheros FE).
- **Incidente de edición resuelto**: un reemplazo con indentación desplazada corrompió un bloque de `security.py` (`IndentationError` en seeds) — detectado por parseo AST inmediato, reparado y re-verificado (`AST OK` ×4).
- **Siguiente**: push C2 (run #13) → sensibilidad (6 mutaciones) → certificación R-199 (+ C3 runtime: deploy EX-01 → E2E-01…07 API + inventario) → R-200 C1.
- **Evidencia saneada**: los logs de pytest incluyen la URL del PostgreSQL efímero de test con su contraseña **de un solo uso** (generada por `run_tests.sh`, destruida con el run); sanitizados (`:***@`) antes del commit — incluida la versión HEAD de `red_c1.log` (la original en la historia de C1 contiene esa credencial efímera, ya rotada; riesgo nulo, corregido hacia delante).
