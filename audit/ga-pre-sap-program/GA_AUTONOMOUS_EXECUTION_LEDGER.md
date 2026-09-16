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
- **Pista OPS** (única línea con dependencia «—»; «arrancable ya»): sus ítems son acciones **owner/ops fuera del código**, no ejecutables sin acceso al host: R-52 volumen `avicola-media` · GA-REM-004 AC03 (rate limit runtime) · AC07 (rol BD mínimo + SSL) · P1-6 (respaldo). ⇒ **Encolada** en `GA_OWNER_GATE_QUEUE.md` (G-02…G-05); instrumentos entregados 2026-09-16 (`GA_T13_OPS_RUNBOOK.md`); no ejecutada por el agente.
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

## AE-13 · 2026-09-13 (noche-2) · R-199 C2s + C3 — SENSIBILIDAD 6/6 · DEPLOY OK · G-06

- **Sensibilidad (C2s)**: 6 mutaciones, cada una rompe ≥1 prueba — M1→RED-01/06a · M2→RED-02 · M3→RED-03 · M4→RED-04 · **M5 (renovación) inicialmente enmascarada** (defensa en profundidad: el resolutor de `/me` re-decide el contexto aunque el token estampe el claim) ⇒ **RED-05 reforzada** (afirma también `decode_token(access).company_id == A` en el token renovado; 12/12 con refuerzo, `green_r199_c2s.log`) ⇒ M5 rompe RED-05 · M6→RED-06b/06c. Logs en `evidence/r199/mutations/`; reversión `git checkout` verificada tras cada una.
- **C3 runtime — parcial**: `Docker Push — Backend` run 114 (`62cd0e1`) = **success** (imagen publicada ⇒ deploy EX-01). **Sondas E2E-01…07 bloqueadas por credenciales**: las UAT-09 disponibles (Operador/Aprobador R-153) no tienen `users:*` ni son super ⇒ se encola **G-06** (credencial efímera de admin/super, o ejecución del script de sondas por el propietario); inventario §12 (SQL a runtime) dentro de G-06. Sin fabricar evidencia.
- **Certificación**: `audit/ga-claude-final-audit/GA_CLAUDE_R199_RUNTIME_CERTIFICATION.md` — **R-199 = `CLOSED_TECHNICALLY` · `C3_PENDING_OWNER_CREDENTIALS` (G-06)**; AC01–15/17/18 ✅; AC16 pendiente del inventario runtime.
- **Hallazgo colateral → C8**: el workflow **`Quality Gates`** (GA-REM-013) está **ROJO** en HEAD (incl. `448b918` del cierre T1 y `62cd0e1`): backend job falla ~10s y frontend job falla — mismos root causes C3/C4 + pasos que invocan el `python` del sistema ⇒ AE-14.

## AE-14 · 2026-09-13 (noche-2) · C8 — WORKFLOW «QUALITY GATES» REPARADO (root cause C3/C4)

- **Evidencia del fallo**: run 208 (`62cd0e1`) — `Backend · compilación, Alembic y guarda` failed (10s; repro local de `pip install -e ".[dev]"` en venv limpio ⇒ setuptools flat-layout, exit 1) · `Frontend · typecheck, tests, lint e i18n` failed (vitest sin peer; patrón C4) · `scope-guard EX-01` ✅ verde.
- **Fix C8 (solo workflow)**: `quality-gates.yml` — backend: `uv sync --frozen --python 3.11` + `.venv/bin/python` en compileall/Alembic/guarda; frontend: peer `@testing-library/dom@10.4.1` explícito. EX-01 intacto (el workflow sigue siendo señal, no puerta; scope-guard preservado).
- **Equivalencia local verificada**: compileall OK · guarda de entorno **25/25** (env del workflow) · i18n `ES=1041 EN=1041 faltantes=0` · Alembic `heads=['y5z6a7b8c9d0'] bases=['0c661168cb12'] revisiones=37` exit 0 · YAML OK. Push ⇒ run 209 esperado VERDE.
- Nota: este workflow **no forma parte de AC-06** (que cubría `quality-suite.yml`); su rojo era preexistente a la sesión y se corrige aquí como higiene de compuertas (coherente con `QUALITY_GATES_READY=YES`).

## AE-15 · 2026-09-13 (noche-3) · R-200 C1 — RED ✅ (4 rojas por el defecto · 5 controles)

- **Nuevo** `backend/tests/test_r200_refresh_token_as_access.py` (login real con `test_credentials`; JWT firmado a mano para los casos sin `type`). **Verificado local: 4 rojas por el defecto** — RED-01/02: el refresh como `Bearer` autentica la ruta protegida y la de permiso (**200 con identidad completa, `is_super_admin: true`**); RED-03: un JWT firmado sin `type` autentica; RED-04: `type:"session"` autentica — **y 5 controles verdes** (CTL-05…08 + DOC-10 ventanas 30 min / 7 d). Evidencia: `audit/ga-claude-final-audit/evidence/r200/red_c1.log`.
- Contexto declarado: `GA-REM-003 AC04` (logout/rotación/revocación) **no** se cierra aquí — esta spec restaura la frontera de 30 minutos del access.
- **Siguiente**: C2 (una comprobación en `get_current_user`, antes de tocar la base) → GREEN 9/9 → suite completa → **C3 runtime ejecutable ya** con las credenciales UAT-09 (sondas no destructivas de refresh).

## AE-16 · 2026-09-13 (noche-4) · R-200 C2 — IMPLEMENTACIÓN ✅ (GREEN 9/9 · suite 1247/0/49)

- **C2 implementado** (`app/auth/security.py`): `get_current_user` rechaza con `401` («Token inválido: no es un token de acceso») cualquier token cuyo `payload["type"] != "access"`, **antes** de leer `sub` y de consultar la base (sin consulta; sin `set_current_audit_user`). `refresh_token` sin cambio (ya exigía `"refresh"`); emisión sin cambio (30 min / 7 d, mismos claims).
- **GREEN**: dirigido **21/21** (R-200 9/9 + R-199 12/12; `green_r200_c2.log`); **suite completa `1247 passed / 0 failed / 49 skipped`** (18m56s; `full_suite_c2.log`; +9 = la suite nueva). Sin cambios frontend.
- **Runtime pre-fix capturado** (`evidence/r200/runtime-prefix.json`, 2026-09-13 20:04:52 +0200): E2E-01/02 = **200** (el refresh autenticaba en producción); pendiente sondas post-deploy.
- **Siguiente**: push → deploy EX-01 → sondas post-fix (esperado `401` en E2E-01/02; `200` en E2E-03/04) → `GA_CLAUDE_R200_RUNTIME_CERTIFICATION.md` → R-202 C1.

## AE-17 · 2026-09-13 (noche-5) · R-202 C1 — RED ✅ (3 rojas por el defecto · 2 controles)

- **Nuevo** `backend/tests/test_r202_password_reset_scope.py` (fixture `esc202`, PREFIJO `R202-`; super sin contexto / super situado / admin de empresa × 2 empresas). **Verificado local: 3 rojas por el defecto** — RED-01: el super **sin contexto** restablece por API (**204**; debe ser 4xx fail-closed); RED-03: el admin de empresa con `users:update` **no puede** restablecer en su empresa (**403**; debe ser 204); RED-06: sin reset legítimo no hay asiento con la empresa efectiva del actor — **y 2 controles verdes** (CTL-02 super situado → 204; CTL-04 cross-company → 403). Evidencia: `evidence/r202/red_c1.log`.
- **Siguiente**: C2 (`_usuario_alcanzable` + `tiene_permiso(users: update)` en `change_password`; auditoría con empresa efectiva) → GREEN 5/5 → suite completa → C3 runtime (misma necesidad de actores que R-199: **G-06**) → certificación.

## AE-18 · 2026-09-13 (noche-5) · R-200 C3 — RUNTIME ✅ · R-200 CERRADA

- **Sondas post-fix (observadas, 20:20:41 +0200)**: E2E-01/02 = **401 «Token inválido: no es un token de acceso»** (pre-fix eran 200); E2E-03 access = 200; E2E-04a/b renovación = 200/200. Evidencia `evidence/r200/runtime-{prefix,c3}.json`; deploy `Docker Push — Backend` run 117 (`bf1746c`) success + Watchtower.
- **Sensibilidad M1**: neutralizar la comprobación ⇒ RED-01…04 rojas (`evidence/r200/mutations/M1_sin_comprobacion_tipo.log`); revertida; worktree limpio.
- **Certificación**: `audit/ga-claude-final-audit/GA_CLAUDE_R200_RUNTIME_CERTIFICATION.md` — **R-200 = `CLOSED_FUNCTIONALLY_CERTIFIED`** (AC01–14 ✅). Registro actualizado; nota AC13: **no** cierra `GA-REM-003 AC04`.
- **Siguiente**: **R-202 C2** (implementación de `change_password` contextual) → GREEN 5/5 → suite completa → certificación (C3 runtime = G-06) → R-208 → **GA-REM-003 AC04** → certificación T2.

## AE-19 · 2026-09-13 (noche-6) · R-202 C2 ✅ (CLOSED_TECHNICALLY) · arranca R-208 C1

- **R-202 C2 `fafd262`**: `change_password` — objetivo resuelto por `_usuario_alcanzable` (fail-closed sin contexto) + `tiene_permiso(users:update)`; auditoría con empresa efectiva del actor. Dirigidas **37/37**; **suite completa `1252 passed / 0 failed / 49 skipped`** (19:39); sensibilidad M1 (sin permiso ⇒ `test_t012_05` roja) y M2 (sin ámbito ⇒ RED-01/04 rojas).
- **Certificación**: `GA_CLAUDE_R202_RUNTIME_CERTIFICATION.md` — `CLOSED_TECHNICALLY`, **C3 runtime pendiente de G-06**.
- **Nota de proceso**: un `git checkout --` sin staging previo revirtió la implementación C2 al índice (pre-fix) — recuperada re-aplicando y **stageando antes** de mutar; lección en `/memories/repo/spec-dev-red-green-pitfalls.md`.
- **R-208 C1 (arrancado)**: tests RED — backend `test_r208_batch_approval_authority.py` (4: 01/03 rojos por puerta `review:review`; 02/04 controles) y FE `r208.batchGates.test.tsx` (RED R1 ve botones de lote; control A1). Pitfall FE documentado: mocks de `t`/`toast` **estables** o el refetch resetea la selección.
- **Siguiente**: RED backend R-208 (ejecutar + evidencia) → commit C1 → C2 (decoradores `approvals:*` en batch + gates del panel) → GREEN/regresión/sensibilidad → C3 runtime (actores UAT-09 aptos: operator sin approvals / aprobador con approvals) → **GA-REM-003 AC04** → regresión T2 → certificación T2.

## AE-20 · 2026-09-13 (noche-7) · R-208 CERRADA (CLOSED_FUNCTIONALLY_CERTIFIED) · arranca GA-REM-003 AC04

- **R-208 C1 `11b8f89`**: RED backend 2F/2P (01/03 rojos: la puerta del lote era `review:review`); RED FE (revisor veía botones de lote).
- **R-208 C2 `331ad83`**: `require_permission("approvals",…)` en `batch-approve/reject`; barra del panel gateada por `approvals:*` (botones por permiso). GREEN BE 17/17, FE 5/5, **suite FE 316/316**, **suite BE `1256/0/49`** (20:43). Sensibilidad S1 (revertir puerta ⇒ 01/03 rojas) documentada en `evidence/r208/mutations/S1_sin_puerta.log`.
- **Runtime (no destructivo)**: señales con ids inexistentes + detalle del 403 como prueba de la puerta desplegada — operador 403 «Permiso requerido: approvals:approve/reject»; aprobador 404 «Evento no encontrado». Deploy Docker #121 (`331ad83`). `runtime-c3.json`.
- **Lección FE registrada**: mocks `t`/`toast` deben ser identidad estable o el refetch resetea la selección (`/memories/repo/spec-dev-red-green-pitfalls.md`).
- **Siguiente**: **GA-REM-003 AC04** (logout + denylist `jti` + migración `revoked_tokens` + auditoría LOGOUT; test RED ya escrito `test_ga_rem_003_ac04_logout_revocation.py`) → C1 commit → C2 → regresión T2 (suite completa + FE) → runtime/E2E → **certificación T2** → T3.

## AE-21 · 2026-09-13 (noche-8) · GA-REM-003 AC04 CERRADA (logout revoca) · pines del harness actualizados

- **C1 `52d0077`**: RED BE 4F/3P (sin endpoint, sin jti, sin asiento, sin idempotencia) · FE 1F/1P (logout no llama al servidor).
- **C2 `80ffd82`**: `jti` en refresh · tabla `revoked_tokens` (migración `z6a7b8c9d0e1`, TTL 7d, purga oportunista) · `POST /logout` 204 **ruta de titularidad** (exige sesión + `sub` propio — `AC08b` limita la superficie anónima a login/refresh) · `/refresh` rechaza revocado ⇒ 401 «Token revocado» · FE logout best-effort. GREEN BE 28/28 · FE 8/8 · **suite FE 318/318** · **suite BE `1263/0/49`** (23:43).
- **Sensibilidad S1** (sin consulta de revocación ⇒ 01/03 rojas, 2F/5P).
- **Runtime** (`runtime-c3.json`, deploy Docker #123 + Watchtower): logout **204** → refresh revocado **401 «Token revocado»**; control segunda sesión 200; sin sesión 401. Auditoría LOGOUT escrita.
- **Pines del harness actualizados** (lección en `/memories/repo/spec-dev-red-green-pitfalls.md`): recuento de tablas 56 · cabezas `z6a7b8c9d0e1` (`test_company_catalog t10`, `test_population_invariant ac14`) · rutas `/api/` 212 · clasificador `revoked_tokens` ⇒ `AUTH_REQUIRED`.
- **Alcance**: AC04 (y parte LOGOUT de AC06) cerrados; AC01/02/03/05/06-resto/07 siguen su recorrido.
- **Siguiente**: **regresión final T2** (suites completas ya verdes; consolidar) + **certificación T2** → T3.

## AE-22 · 2026-09-13 (noche-9) · T2 CERRADA (CLOSED_FUNCTIONALLY_CERTIFIED) · arranca T3

- **T2 = `CLOSED_FUNCTIONALLY_CERTIFIED`** — 5 items (R-199 · R-200 · R-202 · R-208 · GA-REM-003 AC04) con certificación individual; `GA_T2_CERTIFICATION.md` consolida: criterios de salida ✅ (4+1 ataques bloqueados con test, suites verdes con artefacto, `OD-13.c` registrada, evidencia en el hogar del programa, deploy EX-01 observado).
- **CI de cierre**: Quality Suite **#26 `34778950665` (`5044788`) = Success** (backend 24m25s ✅ · frontend 1m1s ✅); artefactos descargados y **sha256 recomputado == digest**: backend `6f97466f…` (1312/0/0/49) · frontend `b919ac69…` (318/0); `evidence/t2-ci-run.json` + XML.
- **Historial CI honesto de T2**: #20/#22/#23 verdes; #21/#24 rojos por diseño (RED); #25 rojo por pines del harness — remediado en el commit de cierre (#26 verde). Lección permanente en memoria del repo (5 pines a actualizar al añadir ruta/migración/tabla).
- **Límites declarados**: G-06 (C3 runtime de R-199/R-202 — cola del propietario); GA-REM-003 AC01/02/03/05/06-resto/07 en su recorrido.
- **KPI**: procesos 0/17 (T2 es plataforma). Veredicto pre-SAP sin cambio: `NO_GO_SAP_FUNCTIONAL_GAPS`.
- **Siguiente**: **T3 · Alcance de datos** — R-201 C1 EN CURSO (RED ya ejecutado: 5F/18P; evidencia `evidence/r201/red_c1.log`) → C2/GREEN → R-203 → R-204+R-216 → R-221 (rider; **AOD-13** encolada al propietario) → certificación T3.

## AE-23 · 2026-09-13/14 (noche-10) · R-201 CERRADA (CLOSED_TECHNICALLY) · T3 en marcha

- **R-201** (SAP fail-closed): C1 `8a442ec` (RED 5F/18P — incluida la trampa: sin eventos aprobados `consolidate` respondía **201**) · C2 `4050eef` (`_company_filter`→`false()` + guardas de contexto tempranas; GREEN 32/32; S1/S2). C3 runtime pendiente **G-06**.
- **Guarda de determinismo**: la primera suite conjunta marcó 1F (`t028_04`) por una fecha ISO literal en el fixture R-201 — remediada con `iso_days_ago(1)` (guarda+R-201: 17/17).
- **Lección re-confirmada** (memoria del repo): `git checkout --` sin staging pierde la implementación — pasó de nuevo en el ciclo S1/S2 de R-203 y se recuperó re-aplicando con staging previo. La nota existía; ahora se aplica *siempre*.
- **T3 en marcha**: R-203 C1 `fc8f193` (RED 5F/7P; clarificación **C-07**: contrato canónico 400/`BR-07`, verificado contra `main.py:88` y el precedente del área) · C2 implementado (galpón vía granja; línea por catálogo; edición con semántica `OD-21`) · S1/S2 (2F/2F).

## AE-24 · 2026-09-14 · R-203 CERRADA (CLOSED_TECHNICALLY) — suite conjunta

- **R-203 C2**: `lots/service.py` — galpón verificado **por la granja**, línea por `verificar_catalogo_de_empresa`, edición solo cuando el valor cambia. GREEN dirigido 86/86 (R-203 7 + área 6 + curvas + tenencia maestros + submovimientos + row scope); sensibilidades S1 (sin galpón ⇒ 01/04 rojas) y S2 (sin línea ⇒ 02/03 rojas).
- **Extensión del fichero de clase** (`test_ga06a_06`): su primera versión usaba una `Connection` con `.add` (fallo de helper, no de producto); corregida con sesión ORM y **RED re-observado en la versión corregida** (log `red_c1_area_extension.log`).
- **Inventario §12**: house=0 · line=0 · curve=0 filas cruzadas en la BD de pruebas (solo lectura, tras la suite).
- **Suite completa conjunta** (fix de guarda R-201 + R-203 + todo lo anterior): **`1278 passed / 0 failed / 49 skipped`** (20:14; `evidence/r203/full_suite_c2.log`).
- **Siguiente**: R-204 (+R-216) C1 → luego R-221 (rider; **AOD-13** encolada) → certificación T3.

## AE-25 · 2026-09-14 · R-204 CERRADA (CLOSED_TECHNICALLY) — suite 1284/0/49

- **C1** `ca1fa39` (RED 4F/2P: agregados incubadora sumaban unidad no concedida; alertas con lote ajeno; unidad apagada seguía sumando) · **C2** `c1a21bd`: `_filtro_de_lotes()` aplicado a todos los sumatorios de `get_kpi_hatchery` (helpers con parámetro `lotes`) y `_get_active_alerts` con `lot_id.in_(_lotes)` + fail-closed; `route_scope` de `/reports/kpis/hatchery` retirado con nota razonada (C-03).
- **GREEN** dirigido 53/53 · **S1** (sin predicado ⇒ 3F) · **S2** (alertas sin filtro ⇒ 1F) · **suite completa** `1284 passed / 0 failed / 49 skipped` (1137.13s; `evidence/r204/full_suite_c2.log`).
- **Siguiente**: R-216 C1/C2 (mismo panel) — luego certificación T3.

## AE-26 · 2026-09-14 · R-216 CERRADA (CLOSED_TECHNICALLY) — contrato de claves

- **C1** `074ee0a` (RED 1F/1P: claves `BirdTypeEnum.*` vs valores; control de suma verde) · **C2** `1ba1b11`: `row.bird_type.value` en `_get_lots_by_type` (las cuatro tarjetas del panel volvían 0 con la suma correcta); `test_kpi_scope` endurecido de substring a claves exactas (el substring dejaba pasar el defecto).
- **GREEN** dirigido 49/49 · **S1** (restaurar `str()` ⇒ 2F) · **S2** (`.name` ⇒ 2F) · evidencia `evidence/r216/`.
- **T3**: R-201/R-203/R-204/R-216 cerradas técnicamente; **R-221** en curso (C1 RED escrito; AC-04 espera **AOD-13**); suite final T3 en ejecución al cierre de esta entrada.

## AE-27 · 2026-09-14 · T3 CERRADA TÉCNICAMENTE + R-221 parcial (rider)

- **Suite completa T3**: **`1286 passed / 0 failed / 49 skipped`** (1171.11s, tip `1ba1b11`; `evidence/t3/full_suite_t3.log`) — R-201/R-203/R-204/R-216 incluidos.
- **R-221 C1** `8126f97`: RED 3F/2P — con `hatchery` apagada la autoridad global registraba **201**; sin concesión, 201; con concesión, `business_unit_id` NULL. Controles verdes (statu quo C-02 fijado; evento con lote intacto).
- **R-221 C2** `b056ef1`: lista explícita `UNIDAD_POR_TIPO_INEQUIVOCO` (grandparent·hatchery) → guarda estricta (`OD-16.e`/`OD-09`) + atribución al nacer (`business_unit_id` = habilitación) para `hatchery_inspection` sin lote; importación intacta (R-153). GREEN 134/134 con regresión BU/clasificación/R-153; S1 (sin atribución) 1F · S2 (sin guarda) 2F.
- **Lecciones del ciclo**: (1) fixture de test de integración **exige `s.commit()`** antes del `yield` — su ausencia revirtió usuarios y dio 401 «Usuario no encontrado o inactivo» (diagnóstico por message-match, no por sospecha); (2) enum en SQL = **mayúsculas** (`'HATCHERY_INSPECTION'`), no el valor del miembro — mismo tropiezo que la lección de R-201, ahora aplicada a queries de conteo.
- **T3**: certificación `GA_T3_CERTIFICATION.md` (CLOSED_TECHNICALLY) · **AOD-13** único pendiente (AC-04 de R-221) · T4 (R-190 + R-205) habilitada sin dependencia.

## AE-28 · 2026-09-14 · R-190 CERRADA (CLOSED_TECHNICALLY) — ubicación del evento

- **C1** `a79fe0c`: RED 26F/2P FE (payload sin `house_id` en 7 tipos; sin bloqueo cliente; i18n ausente) + control BE BR-08 4/4 verde.
- **C2** `d1c16a7`: `resolverUbicacionDelEvento` (fuente única) + selector «Galpón del evento» ×4 + guardas cliente + i18n. GREEN 32/32; tsc 0; FE 360/360; build OK.
- **C2s** `801d18c`: S1 2F · S2 9F · S3 2F · S4 2F.
- **Lección**: el «tool» de edición difusa volvió a corromper JSX del formulario gigante (dos funciones comidas + fragmentos huérfanos) — remediado con hunks mínimos y verificación tras cada edición (memoria del repo ya lo advertía; ahora reforzada).

## AE-29 · 2026-09-14 · R-205 CERRADA (CLOSED_TECHNICALLY) — cuadre alcanzable

- **C1** `fe3bd3d`: RED 12F/2P (cuadre oculto en deep link; `?stage=` sin paridad; incompleto viaja) + control BR-20 10/10.
- **C2** `72aa7f4`: `resolverStageDelAsistente` + visibilidad por lote + guarda `cuadreRequired`. GREEN 29/29; tsc 0; FE 360/360; build OK.
- **C2s** `dbc782d`: S1 4F · S2 3F · S3 1F.

## AE-30 · 2026-09-14 · T4 CERRADA TÉCNICAMENTE — suite 1295/0/49

- **Suite completa**: `1295 passed / 0 failed / 49 skipped` (1170.30s; `evidence/t4/full_suite_t4.log`) = 1286 T3 + 5 R-221 + 4 control R-190.
- **Certificación**: `GA_T4_CERTIFICATION.md` (CLOSED_TECHNICALLY); C3 runtime de R-190/R-205 en ventana de deploy/credenciales (G-06 familia); C-03 de R-190 opcional del propietario.
- **Siguiente**: **T5** (DAG T5 ← T4) — arranque automático.

## AE-31 · 2026-09-14 · R-191 CERRADA (CLOSED_TECHNICALLY) — transición de fase

- **C1** `921a3a0` (BE 7F/2P · FE 4F/4) · **C2** `d330ae5` (bloqueo del lote + cierre de activa + saldo por sexo + `phase` en lectura + `BR-23`; FE por ids + toast; BE 9/9; FE 364/364; tsc 0) · **C2s** `1f8dfb6` (S1 1F/S2 1F/S3 3F/S4 1F).
- **Defecto de test detectado en GREEN**: `days_ago(40)` devuelve `date` — httpx exige ISO (`isoformat()`); corregido en el mismo ciclo (evidencia en log).

## AE-32 · 2026-09-14 · R-206 CERRADA (CLOSED_TECHNICALLY) — vacíos del asistente

- **C1** `ce1ea7e` (FE 8F/8 · BE 4F/2P) · **C2** `da66344` (`limpiarVacios` recursivo + `valueAsNumber` ×8 + tolerancia BE de opcionales C-02=A; FE 372/372; BE 35/35; tsc 0) · **C2s** `4fdd131` (S1 1F/S2 4F).

## AE-33 · 2026-09-14 · R-209 CERRADA (CLOSED_TECHNICALLY) — códigos SAP canónicos

- **C1** `3fc1b91` (FE 2F/1P; AC-01 control: R-189 ya canonicalizó el selector compartido; comparativo BE 2/2) · **C2** `ae85a4e` (helper sin fallback de id + OT de feed + selector interno de salida + barrido C-04; FE 375/375; tsc 0) · **C2s** `0073d57` (S1 1F/S2 1F).

## AE-34 · 2026-09-14 · R-210 CERRADA (CLOSED_TECHNICALLY) — gramos como unidad única

- **C1** `6da1b3c` (FE 3F/2P; control BE 4/4) · **C2** `5c1b5af` (rótulos g + step 1; FE 380/380; tsc 0) · **C2s** `0f587b1` (S1 2F/S2 1F).
- **Lección de mutación**: no inyectar marcadores `#` dentro de literales JS — rompe el transform (S1 inicial «no tests»); mutar el texto directo y detectar por contenido.

## AE-35 · 2026-09-14 · T5 CERRADA TÉCNICAMENTE — suite 1316/0/49

- **Suite completa**: `1316 passed / 0 failed / 49 skipped` (1167.72s; `evidence/t5/full_suite_t5.log`; re-ejecutada tras remediar el guard de determinismo — literales ISO en `test_r206_optional_tolerance.py`, fix `0e60038`).
- **Certificación**: `GA_T5_CERTIFICATION.md` (CLOSED_TECHNICALLY); FE 380/380 + tsc 0; riders: R-146 ↔ AOD-16 y AOD-21 (R-210 C-01); C3 runtime de R-191/206/209/210 en ventana (familia G-06).
- **Siguiente**: **T6 · Cadena de incubadora (R-194)** — arranque automático (DAG T6 ← T4+T5).

## AE-36 · 2026-09-14 · R-194 CERRADA (CLOSED_TECHNICALLY) — cadena de incubadora

- **C1** `c413fdb`: FE 4F/1P (BR-08 por ubicación, fértiles, dosis silenciosa, `hatchery_id`; carga = control) · BE 1F/4P — la cadena canónica destapó un **defecto real de servidor** (`egg_storage.lot_id` NULL ⇒ 500; `setdefault` inoperante con `lot_id: None` explícito).
- **C2** `0bfba2e`: fértiles + `arrival_date` (C-02=A) + ubicación de etapa (C-01=A) + `hatchery_id` + dosis `valueAsNumber` con error visible; fix B-03b en alta **y** verificación. **BE 5/5**: cadena real recepción→saldo→carga→BR-03→nacimiento→despacho→BR-04→recepción destino→`ChickBatch`→trazabilidad X-BU. FE 386/386; tsc 0.
- **C2s** `cd33d23`: S1-S4 1F c/u.
- **Lección de UI**: `min` nativo HTML bloquea el submit **sin** errores RHF — para errores visibles, validar por schema y sin constraint nativo.

## AE-37 · 2026-09-14 · T6 CERRADA TÉCNICAMENTE — suite 1321/0/49

- **Suite completa = 1321/0/49** (`evidence/t6/full_suite_t6.log`); FE 386/386 + tsc 0; certificación `GA_T6_CERTIFICATION.md` + `GA_CLAUDE_R194_RUNTIME_CERTIFICATION.md`.
- **Procesos**: P-04/P-05 **REPARADOS técnicamente** (E2E en ventana); X-BU demostrado a nivel API-integrada. KPI global sigue 0/17 hasta runtime/UAT.
- **Siguiente**: **T7 · Cierre y reversos (R-192 · R-193 · R-211)** — arranque automático (DAG T7 ← T3+T6).

## AE-38 · 2026-09-14 · R-192 CERRADA (CLOSED_TECHNICALLY) — cierre con reversos

- **C1** `582f513`: BE 6F/13P (R7 bloquea el par `REVERSED`; resumen sin filtro de estado; BR-05; C-07) + FE 3F/1P (toast ausente).
- **C2** `f65a633` + `0e49add`: R7 decide por estado terminal (`REVERSED` aceptable, C-07 nombra «reverso pendiente»); resumen neto excluye `CANCELLED`/`REVERSED`; BR-05 vigente (C-05); toast de cierre UI. BE 19/19 · regresión 87/87 · FE 390/390 · tsc 0. `test_t_073_01` actualizado a escenario neutro (codificaba la semántica previa).
- **C2s** `929b2f6`: S1 3F (R7 sin `REVERSED`) / S2 2F (resumen sin filtro) / S3 3F (sin toast).
- **Lección**: la edición de `handleCloseLot` consumió un `} finally {` (no lo cubrían los tests FE) — detectado y reparado en `0e49add`; verificar estructura tras ediciones en archivos grandes.

## AE-39 · 2026-09-14 · R-193 CERRADA (CLOSED_TECHNICALLY) — acumulado BR-18 neto

- **C1** `c97b14e`: BE 5F (reverso efectivo no libera la OC; contrapartida rechazada cuenta; mensaje inflado).
- **C2** `0f61769`: `validate_oc_limit` sobre Σ neta (excluye `REVERSED` y contrapartidas; el original cuenta hasta la efectividad). BE 5/5 · regresión 86/86.
- **C2s** `0008541`: S1 3F (02/04/05; 01 no cruza el límite) / S2 1F (03). OBS-R193-01/02 al backlog.

## AE-40 · 2026-09-14 · R-211 CERRADA (CLOSED_TECHNICALLY) — capacidad por fila

- **C1** `3dd397b`: BE 2F/2P (reparto 500+500 rechazado con 400; mensaje sin galpón).
- **C2** `b00a83b`: BR-17 por fila (`target_house_id`; fallback `house_id` del evento; C-02=A) con mensaje «galpón + capacidad». BE 4/4 · regresión 140/140 (incluye paridad de edición, tenencia, BU y R-190 contigua).
- **C2s** `e30178b`: S1 2F (01 reparto falso positivo; 02 mensaje). **AOD-28** (C-02 A/B) encolada.

## AE-41 · 2026-09-14 · T7 CERRADA TÉCNICAMENTE — suite 1349/0/49

- **Suite completa** `evidence/t7/full_suite_t7.log` (1349/0/49; 1 207 s) · FE 390/390 + `tsc` 0 · certificaciones `GA_T7_CERTIFICATION.md` + R-192/R-193/R-211.
- **Procesos**: P-01/P-02/P-03/P-06 **reparados técnicamente**; KPI 0/17 sin cambio (runtime/UAT pendientes; G-06 ampliada con R-192/R-193/R-211).
- **Owner gates nuevos**: AOD-27 (R-192 C-01/C-05), AOD-28 (R-211 C-02) — confirmatorias, no bloquean.
- **Siguiente**: **T8 · Auditoría y evidencias (P1-12-REOPEN · R-198 · R-219)** — arranque automático (T8 ← T7 satisfecho).

## AE-42 · 2026-09-14 · P1-12 (REAPERTURA) CERRADA (CLOSED_TECHNICALLY) — un productor por acción

- **C1** `d228eac` + **C1b** `ce363af`: arnés con listener (`tests/audit_harness.py`) y RED de 8 rojos exactos (created×2, review_started×3, approved×2+corrected espuria; cierre/activación/fase/usuarios/evidencias/curvas/batch = 0).
- **C2** `0bbad13`+`0de63c2`: **guarda de idempotencia compartida** listener↔helpers (`(entidad,id,acción)` en `session.info`) = un productor por acción en runtime y sin listener; ruta `ApprovalAction` retirada; mapa `pending_review→UPDATED`/`reversed→REVERSED`; productores nuevos (lotes/usuarios/evidencias/curvas/batch/contrapartida). BE 8/8 · regresión 207/207 · arnés runtime migrado en `test_audit_coverage`/`test_edit_cancel_balance`.
- **C2s** `5940f6a`: S1 2F / S2 1F.
- **Lección**: `git checkout --` restaura desde INDEX — en ciclos de mutación hay que **commitear C2 primero**; un checkout antes del commit del producto borra la implementación (ocurrió en R-219 y se reaplicó).

## AE-43 · 2026-09-14 · R-198 CERRADA (CLOSED_TECHNICALLY) — evidencias del detalle

- **C1** `dc69375` (BE 5F/2P + FE 3F/1P) · **C2** `244ab43`: detalle devuelve `evidences`+`egg_storage_records` (C-01=A/C-04); gate por estado en servidor (C-02); borrado físico **tras** commit (C-03); FE relee del servidor, gate espejo, acciones visibles en táctil; BE 7/7 + 122/122; FE 394/394 + tsc 0.
- **C2s** `5b8b865`: S1 3F / S2 1F / S3 1F.
- Nota: el test 05 instrumenta el **orden** `commit→remove` con un proxy de sesión — verifica la propiedad anti-pérdida sin simulacros frágiles.

## AE-44 · 2026-09-14 · R-219 CERRADA (CLOSED_TECHNICALLY) — AuditPage contra el contrato real

- **C1** `5b9bde5` (FE 5F) · **C2** `2f5d52f`: nombre de usuario (vía `/users` con permiso; `Usuario #id` sin él), diff `previous_values/new_values` + estados, `change_reason`+`comments`, paginador 50/página, i18n `audit.actions/modules` (22/11 ES/EN). FE 5/5 + 399/399 + tsc 0.
- **C2s** `45acbf8`: S1/S2/S3 1F c/u.

## AE-45 · 2026-09-14 · OWNER DECISION AOD-29 — GitHub Actions retirado del camino PRE-SAP

- **Decisión del propietario** (verbatim en `GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md`): Actions deja de ser gate obligatorio de nuevas tranches; certificación con **gates locales reproducibles**; evidencia dependiente de Actions ⇒ `NOT_APPLICABLE_BY_OWNER_DECISION`; **`PUSH = NO`** (`NOT_PERFORMED_BY_OWNER_POLICY`) mientras dispare Actions; históricos (T1/AC-06, T2 #26) intactos. → **CORREGIDO prospectivamente por AOD-29 Clar. 01 (AE-47): el push NO estaba retirado; `PUSH = REQUIRED`.**
- **Reconciliado sin reescribir historia**: roadmap (addendum), status (política + campos de publicación local), cola (fila AOD-29 + header), certificaciones T3-T8 (addendum CI), `docs/07-qa-plan.md` (enmienda), ledger.
- **Efecto inmediato**: runs de la sesión cancelados (los cancelables); sin nuevos push durante la aplicación *(corregido por AOD-29 Clar. 01 — ver AE-47: el push certificado continúa y es obligatorio)*; T8 (cierre) y T9+ pasan a flujo **local** con `LOCAL_CERTIFIED_SHA` + sincronización a `origin/main`.
- **Lección duradera**: mutaciones con restauración desde `IMPLEMENTATION_COMMIT` explícito (`git restore --source=<sha>`), nunca `checkout` implícito (ya ocurrió una vez en R-219).

## AE-46 · 2026-09-14 · T8 CERRADA TÉCNICAMENTE (LOCAL) — suite 1364/0/49

- **Suite completa BE (local)**: **1364 passed / 0 failed / 49 skipped** (21:16; `evidence/t8/full_suite_t8.log`; 1349 de T7 + 8 de P1-12 + 7 de R-198). FE **399/399** + `tsc -b`/`npm run build` verdes — el build detectó un defecto de tipos de `AuditPage` (`t()` no-string; `tsc --noEmit` no lo veía) corregido con `String(...)` **antes** del cierre.
- **Certificación**: `GA_T8_CERTIFICATION.md` + `GA_CLAUDE_P112/R198/R219_RUNTIME_CERTIFICATION.md`; CI = `NOT_APPLICABLE_BY_OWNER_DECISION` (AOD-29). **P-02/P-09 reparados técnicamente**; KPI de procesos 0/17 sin cambio.
- **Publicación local (AOD-29)**: `LOCAL_CERTIFIED_SHA` = commit de este cierre (registrado en AE-46b); `REMOTE_SYNC_STATUS` → **corregido por AE-47: sincronización a `origin/main` obligatoria**; `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`.
- **Siguiente**: **T9 · Maestros y usuarios (R-215 · R-196 · R-195)** — arranque automático en flujo local.

## AE-46b · 2026-09-14 · T8 — registro de publicación local (AOD-29)

- `LOCAL_CERTIFIED_SHA = 8eb6e90` · `WORKTREE_CLEAN = YES` · `LOCAL_CERTIFICATION = PASS (gates locales: BE 1364/0/49 · FE 399/399 · tsc -b · build)` · `REMOTE_SYNC_STATUS = NOT_REQUIRED_CURRENT_OWNER_POLICY` (origin en `45acbf8` — esperado) · `GITHUB_ACTIONS_STATUS = NOT_APPLICABLE_BY_OWNER_DECISION` · `PUSH = NOT_PERFORMED_BY_OWNER_POLICY`. → **CORREGIDO por AOD-29 Clar. 01 (AE-47): `PUSH = REQUIRED`; este checkpoint se sincroniza al remoto.**

## AE-47 · 2026-09-14 · AOD-29 CLARIFICATION 01 — GitHub Actions retirado · Git push preservado

- **Aclaratoria del propietario** (documento canónico `GA_OWNER_DECISION_AOD29_CLARIFICATION_01_PUSH_PRESERVED.md`): `GITHUB_REPOSITORY = ACTIVE`; `GITHUB_ACTIONS = RETIRED`; `LOCAL_QUALITY_GATES = REQUIRED`; `LOCAL_CERTIFICATION = REQUIRED`; `PUSH_POLICY = REQUIRED`; `PUSH_TARGET = origin/main`; `REMOTE_SHA_VERIFICATION = REQUIRED`. La interpretación previa «AOD-29 también detenía los pushes» queda **corregida prospectivamente, sin reescribir historia** (AE-45/46/46b llevan marca de corrección).
- **Retiro estructural de Actions**: 7 workflows movidos de `.github/workflows/` a `.github/workflows-retired/` (+ README «RETIRED BY AOD-29 · NOT EXECUTED · HISTORICAL REFERENCE ONLY»): `backend-ci`, `frontend-ci`, `quality-gates`, `quality-suite`, `docker-push-backend`, `docker-push-frontend`, `docker-build-push`. `ACTIVE_WORKFLOW_COUNT = 0` · `AUTOMATIC_ACTION_TRIGGER_COUNT = 0` ⇒ un push a `origin/main` **no puede** disparar Actions.
- **Impacto de deploy auditado** (`AOD29-DEPLOY-IMPACT`): el auto-deploy compartido (Docker Hub `:latest` + Watchtower) dependía exclusivamente de los workflows retirados ⇒ `SHARED_RUNTIME_AUTO_DEPLOY = NOT_AVAILABLE_WITH_GITHUB_ACTIONS_RETIRED`; `PUSH != DEPLOY`. Sin sustituto implementado (prohibido sin Spec/Owner Decision).
- **Commits locales certificados a sincronizar** (historia local desde `45acbf8`): `5d3a687` (AOD-29 governance) · `8eb6e90` (T8 C2 impl) · `0cefb68` (T8 registro) · `4fc63b4` (R-215 RED) · `cd2e7bc` (R-215 IMPL) · `73a4fb9` (R-215 evidencia) · `4c0f819` (R-196 RED) · `571b4d5` (R-196 C2 IMPL) · + commits de esta micro-tranche y C2b de R-196.
- **Estado real T9 (2026-09-14)**: R-215 cerrada local (FE 405/405; sensibilidad S1-S6); R-196: C1 `4c0f819` + C2 `571b4d5` (FE 414/414 + build; BE targeted 3/3 y 5/5 tras adaptar 5 setups que usaban creación cross-tenant; sensibilidad S1-S6 completa); siguiente: C2b (harness AC-04 + evidencia) y R-195.

## AE-48 · 2026-09-14 · AOD-29 CLARIFICATION 01 APLICADA — primer push bajo política corregida

- **Push**: `571b4d5..aa459ac` → `origin/main` (fast-forward; sin force; sin reescribir historia). `LOCAL_SHA = aa459acffe5e93fbff86d9e4c0e324b964c55af9` = `REMOTE_SHA` ⇒ `PUSH_STATUS = SUCCESS` · `REMOTE_SHA_VERIFICATION = PASS`.
- **Ancestría verificada**: 10/10 SHAs certificados presentes en `origin/main` (`5d3a687` · `8eb6e90` · `0cefb68` · `4fc63b4` · `cd2e7bc` · `73a4fb9` · `4c0f819` · `571b4d5` · `75593f7` · `aa459ac`).
- **Actions tras el push**: `ACTION_RUN_TRIGGERED_BY_PUSH = NO` (observación: sin runs nuevos en la ventana del push; estructural: `.github/workflows/` en el árbol remoto = **0 archivos**). Nota histórica: la sincronización externa previa de `571b4d5` (~25 min antes del retiro) sí produjo runs con los workflows aún activos — historia intacta, no reescrita.
- **R-196 cerrada local en este punto**: C2b `aa459ac` (harness AC-04 + evidencia completa); gates: FE **414/414** · build OK · BE full **1367/0/49** · sensibilidad S1-S6 con restore desde `571b4d5`.
- **Siguiente**: T9 continúa con **R-195** (C1 RED → C2 → gates → commit → push).

## AE-49 · 2026-09-14 · T9 CERRADA TÉCNICAMENTE — R-215 · R-196 · R-195

- **R-215** (render seguro): RED `4fc63b4` · IMPL `cd2e7bc` · evidencia `73a4fb9` — FE 405/405; sensibilidad S1-S6 quirúrgica; `ErrorBoundary` global + `getErrorMessage` ×5 + red de seguridad en `ToastProvider`.
- **R-196** (maestros): RED `4c0f819` · IMPL `571b4d5` · C2b `aa459ac` — FE 414/414 · build · **BE full 1367/0/49**; sensibilidad S1-S6; hallazgo: 5 setups cross-tenant adaptados a `switch-company`; `company_id` resuelto en servidor (fail-closed).
- **R-195** (usuarios): RED `7bde916` · IMPL `bcfdebd` · C2b `e515858` — FE final **419/419** · build; sensibilidad S1-S4 (S4 clúster de la guarda); modal duplicado deduplicado; sin `alert`/`confirm`; payload `UserUpdate` estricto (`username` inmutable, empresa por contexto).
- **Certificación**: `GA_T9_CERTIFICATION.md`; `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION`; `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION` con `REMOTE_SHA_MATCH = YES` en cada checkpoint (remoto final `e515858`).
- **UAT**: pendiente acumulable (R-215 2 · R-196 4 · R-195 3 casos) — no bloquea cierre técnico; se agrupa en el gate PRE-SAP. Procesos 0/17 sin cambio; SAP NOT_STARTED.
- **Siguiente**: **T10** (R-197 · R-207; +R-142 si AOD-17) — arranque automático.

## AE-50 · 2026-09-14 · GA-REQ-061 FORMALIZADO (SPEC_READY) — Cutover operacional / Opening Balance

- **Requerimiento transversal nuevo** (mandato del propietario 2026-09-14): operar con lotes ya iniciados desde un **estado operacional inicial certificado a fecha de corte**; prohibido reconstruir historia o fabricar movimientos/SAP; semántica `0 ≠ UNKNOWN`; saldo vivo ≠ acumulado (`10.000−35=9.965`; `lifetime=535`).
- **Paquete** `audit/ga-claude-final-audit/specs/GA-REQ-061/` (11 docs): SPEC · GAP analysis · **reconciliación R-67 = `PARTIAL_REUSE`** (se extiende `OpeningBalance`/`activate_manual`, sin concepto paralelo) · ACs **85** · arquitectura/modelo (`CutoverBatch`/`CutoverItem`/corrección; atomicidad/idempotencia/concurrencia; sin JSONB indiscriminado) · Excel/staging (plantilla por BU versionada; celda vacía=UNKNOWN) · seguridad (tenancy/BU OD-16/grants/RBAC `cutover:*` PROPOSED/segregación) · **plan RED 22+6 controles** · **sensibilidad S1-S10** · **E2E 4 BUs** (caso broiler obligatorio) · **placement**.
- **Placement**: **T14** con orden de ejecución T11 → **T14** → T12 → T13 (antes del E2E/GO); `T10_BLOCKED_BY_CUTOVER = NO`; `OWNER_GATE = NONE` en esta fase.
- **Estado**: `CUTOVER_SPEC_STATUS = SPEC_READY` · `CUTOVER_IMPLEMENTATION_STATUS = NOT_STARTED` · `PRODUCT_DIFF = 0`.
- **Siguiente**: reanudar **T10** (R-197 · R-207) automáticamente.

## AE-51 · 2026-09-14 · T10 EN CURSO — R-197 CERRADA TÉCNICAMENTE (bandeja por estado · historial por evento · resultado de aprobación)

- **R-197** (T10): RED `afea748` · IMPL `10f7b53` · C2b `e21629a` · CERT `f128218` · EV `6baf4ae`.
- **Gates**: BE targeted **10/10** · BE full **1373/0/49** · guardián de rutas 212→213 (213) · FE targeted **10/10** · FE full **429/429** · `npm run build` **EXIT 0**.
- **Sensibilidad** S1-S4 (BE) y F1-F6 (FE) con RED quirúrgica por test y restore desde `10f7b53`; post-mutación BE 10/10 · FE 10/10 · worktree limpio.
- **Push**: `afea748..6baf4ae` → `origin/main` (fast-forward; sin force). `LOCAL_SHA = 6baf4ae319403ef8d20eca38ef53b10ab6f83ce8 = REMOTE_SHA` ⇒ `REMOTE_SHA_MATCH = PASS`.
- **Política**: `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION`; `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`; `PUSH != DEPLOY`.
- **Siguiente**: **R-207** (reverso — superficie autorizada) en T10; después R-142 según AOD-17.

## AE-52 · 2026-09-14 · T10 CERRADA TÉCNICAMENTE — R-197 · R-207 (R-142 diferida por AOD-17)

- **R-197**: RED `afea748` · IMPL `10f7b53` · C2b `e21629a` · CERT `f128218`/`6baf4ae`. Bandeja por los 7 estados, historial real por evento, resultado de aprobación en el detalle. Gates: BE 10/10 + full 1373/0/49 + guardián rutas=213; FE 10/10 + 429/429; build 0; sensibilidad S1-S4/F1-F6 con restore `10f7b53`.
- **R-207**: RED `3eb1193` · IMPL `4e8d999` · CERT `00d4bea`. Superficie de reverso (botón gate `reversals:create`, modal sin diálogos nativos con motivo ≥5, contrapartida enlazada desde el 201, `reversed` con color propio en mapa central/listas/bandejas). Gates: FE 4/4 + 433/433; build 0; BE no requerida (diff 0); sensibilidad R1-R5 con restore `4e8d999`.
- **Push**: `c880cd5..00d4bea` → `origin/main` (fast-forward). `LOCAL_SHA = 00d4bea9c817541a687bebdf713c28ad7b4f3a5f = REMOTE_SHA` ⇒ `REMOTE_SHA_MATCH = PASS`.
- **Certificación de tranche**: `GA_T10_CERTIFICATION.md`.
- **R-142**: condición `AOD-17` (semántica `CORRECTED` multinivel) **no cumplida** — decisión del propietario `SCHEDULED` (lote §25); diferida y documentada en la cola; no bloquea el cierre de T10.
- **Siguiente**: **T11** (residuales FE `R-213` · `R-212` · `R-218` · `R-220`) — arranque automático.

## AE-53 · 2026-09-14 · T11 EN CURSO — R-213 CERRADA TÉCNICAMENTE (`/me` y `/users` toleran correos legacy)

- **R-213**: C1 RED `3bed31d` (BE 2F por causa exacta: `ValidationError` ⇒ 500 en `/me` y `/users`) · C2 `81de57f` (`UserBase.email: str` lectura tolerante · `UserCreate.email: EmailStr` escritura estricta).
- **Gates**: BE targeted **4/4** · guardianes de sesión/tenant/password/roles **52 passed** · BE full **1381/0/49**.
- **Sensibilidad** S1-S2 con RED quirúrgica y restore `81de57f`; post-mutación verde.
- **Push**: cierre `c32d873` → `origin/main` (fast-forward). `REMOTE_SHA_MATCH = PASS`.
- **Cert**: `specs/R-213/R-213_CERTIFICATION.md` (evidencia `c32d873`).
- **Siguiente**: **R-212** (conciencia de permisos) en T11.

## AE-54 · 2026-09-14 · R-212 CERRADA TÉCNICAMENTE (UI consciente del permiso — 403 ≠ «vacío»)

- **R-212**: C1 RED `0583426` (FE 13F: 10× «alert» ausente con 403/500; home sin landing; KPIs sin gate) · C2 `abf1888` (`ErrorState` reutilizable; `HomeRoute` cae a `/menu/poultry` sin `dashboard:read`; estados distinguidos en 8 pantallas; SAP deja de silenciar 403).
- **Gates**: FE targeted **15/15** · FE full **448/448** · `npm run build` **EXIT 0**.
- **Sensibilidad** M1-M5 con RED quirúrgica y restore `abf1888`; post-mutación verde.
- **Push**: cierre `a7a9087` → `origin/main`. `REMOTE_SHA_MATCH = PASS`.
- **Cert**: `specs/R-212/R-212_CERTIFICATION.md` (evidencia `a7a9087`).
- **Siguiente**: **R-218** (serie semanal del lote) en T11.

## AE-55 · 2026-09-14 · R-218 CERRADA TÉCNICAMENTE (serie semanal del lote — opción A)

- **R-218**: C1 RED `0376305` (BE 2F ruta inexistente `GET /reports/lot/{id}/weekly`; FE 2F tabla/gráficos leían la lista sin sublistas) · C2 `d5cc5fb` (agregado de solo lectura con `_exigir_lote`; agua atribuida una vez por (evento, semana); `route_scope` `MULTI_UNIDAD`; guardián de rutas **213→214**).
- **Gates**: BE targeted **24/24** (rutas = **214**) · BE full **1384/0/49** · FE targeted **2/2** · FE full **450/450** · build **EXIT 0**.
- **Sensibilidad** B1-B3 (BE) y N1-N3 (FE) con RED quirúrgica y restore `d5cc5fb`; post-mutación verde.
- **Push**: cierre `356de95` → `origin/main`. `REMOTE_SHA_MATCH = PASS`.
- **Cert**: `specs/R-218/R-218_CERTIFICATION.md` (evidencia `356de95`).
- **Siguiente**: **R-220** (residuales itemizados, por lotes) y cierre de T11.

## AE-56 · 2026-09-14 · T11 CERRADA TÉCNICAMENTE — R-220 (lotes A+extra/B/C/D) y cierre de la tranche de residuales FE

- **R-220** ejecutada **por lotes** con gobernanza completa por lote (SPEC→AC→RED→IMPL→GREEN→SENSIBILIDAD→POST-MUTACIÓN→EVIDENCIA→COMMIT→PUSH→VERIFY):
  - **Lote A** (A1–A18): contrato de lectura/UX (fechas civiles, lote dinámico en reportes, KPIs retirados, `Se creará al aprobar`, regla/motivo en 4xx, detalle completo, notificaciones con destino, `X-Total-Count`+«Cargar más», sin `sap_reference`, `farm_id` opcional, ovoscopía con día, serializador F-01d, `water_consumption` al catálogo (B-24), `egg_classification` retirado, `egg_storage` 4xx); commits `ddc225f`…`6c84895` (evidencias `loteA1…loteA8`).
  - **A-extra** (A16/A17): validador cliente BR-21 del nacimiento (mixed excluyente; sanos/débiles obligatorios) + anclaje de «Semana»/«Peso prom.» a la primera fila viva; RED `f11786c` · IMPL `30c1660` · add `ad9896e` · evidencia `2432ce7`.
  - **Lote B** (B1–B10): navegación <1024px (hamburguesa monta `MobileDrawer`; perfil/logout móvil), entradas de menú, reporte del lote dinámico, gate `operations:create` en tiles/timeline, contador de procesos dinámico, notificaciones a 390px, botón eliminar máquina con ancestro posicionado, cosméticos R7–R12/R14/R15; commits `2723b44`…`9451bf5`.
  - **Lote C** (C1–C9): enumerados traducidos, `roles.actions/modules` (9/13), claves engañosas corregidas, zod de lote por claves, +33 claves ES/EN, `formatFechaHora` con locale de la app, export con `locale` por parámetro, ES sin texto EN, `NotificationType.lot_near_close`; commits `1d9c131` · `efe6130`.
  - **Lote D** (D1–D5): 8 hooks muertos + `api.types.ts` retirados, tipos alineados (`UserResponse`=UserRead; sin `sap_reference`; `action_type` enumerado), `ProtectedRoute.roles` retirado; commit `da31f52`.
- **Gates finales**: **BE full 1389/0/49** (19:51, tras alineación `8604a60`; la primera corrida completa `1386/3F` capturó la **deriva de 3 tests de conteo 25→26** por `water_consumption` — alineados + presencia verificada; observada duplicación preexistente de `test_list_event_types`) · guardián de rutas `/api/` = **214** · **FE full 520/520** · `npm run build` **EXIT 0** · sensibilidades RED-1:1 por lote con restore desde SHA de implementación.
- **Certificación de paquete**: `specs/R-220/R-220_CERTIFICATION.md` (evidencia `evidence/{red,green,sensibilidad,post-mutation}/lote*`, `be-full-1389.log`).
- **Push**: `32f5d40..3c3ab3d` + cierre → `origin/main` (fast-forward); `REMOTE_SHA_MATCH = PASS` en cada checkpoint; política `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION`, `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`.
- **T11 = CLOSED_TECHNICALLY**: R-213 (`c32d873`) · R-212 (`a7a9087`) · R-218 (`356de95`) · R-220 (este cierre). **Certificación de tranche**: `GA_T11_CERTIFICATION.md`.
- **Siguiente**: **T14** (GA-REQ-061 · Cutover operacional — `SPEC_READY`) — orden T11 → **T14** → T12 → T13. R-142 permanece diferida por AOD-17.

## AE-57 · 2026-09-15 · T14 CERRADA TÉCNICAMENTE — GA-REQ-061 (Cutover operacional / Cargas Iniciales), por checkpoints C1–C9

- **C1 fundación** `cf03253` (RED `cad5e3c`): tablas `cutover_batches/items/staging_rows/opening_balance_corrections` + extensiones `OpeningBalance`/`Lot`; migraciones `b7c8d9e0f1a2` y `c8d9e0f1a2b3` (acciones RBAC/auditoría, **nombres de miembro en MAYÚSCULAS**); `AuditModule.CUTOVER`.
- **C2 parser+staging** `3e138a1` (RED `efb098d`): openpyxl v1, error codes estructurados, checksum idempotente, preview sin efectos.
- **C3 ciclo de aprobación** `3e3f2cb` (RED `b7f596f`): `submit/approve/reject`; segregación creador≠aprobador (también super admin); REJECTED terminal; 409 deterministas.
- **C4 apply atómico** `fe5fe98` (RED `b30a58a` · IMPL `782547b`): lotes MIGRATED con reuso (origen NATIVE intacto), snapshots de apertura = **saldo vivo al corte**, BU habilitada + alcance del actor, rollback total con `FAILED_APPLY` en transacción propia.
- **C5 reporting** `4b8bc74` (RED `81ea05f` · IMPL `3452117`): `GET /reconciliation` Opening/Post/Lifetime; golden **9.965** (nunca 9.465); UNKNOWN = `null` (jamás 0); post-cutover estricto `event_date > corte` con contrapartidas `GA-REM-041`.
- **C6 correcciones** `02e0632` (RED `bfadb41` · IMPL `f7819f1`): AC59-65 — lista blanca, razón ≥5, before/after/delta, auditoría `CORRECT`, tenancy 404, 9.900⇒9.865 sin borrar el post.
- **C7 matriz+controles** `69f5aa8` (RED `b3217ac` · IMPL `5f40842`): `CUT-RED-01..22` + `CUT-CTL-01..06`; **dos deficits reales cerrados**: `MASTER_INACTIVE` (OD-21/AC52; histórica AC53 se conserva) y **alcance BU del actor no-super-admin jamás resuelto** (leía claves de sesión inexistentes ⇒ resuelto en BD, patrón `/me`).
- **C8 FE** `a7ada1f`: «Cargas Iniciales» `/cutover` — flujo completo, status visible, preview, apply bloqueado con errores (AC81), UNKNOWN≠0 visual (AC77), i18n ES/EN; jsdom 4/4 · FE **524/524** · build 0.
- **C9 plantilla+E2E** `1976011` (RED `C9-RED`): `GET /cutover-templates/{bu}` v1 versionada (Instrucciones/Meta/Datos, semántica UNKNOWN impresa) + descarga en UI + **E2E 4/4 BUs** con journals (`evidence/e2e/`): golden broiler 9.965/535/UNKNOWN y negativas (cross-company 404, re-apply 409, submit bloqueado 409).
- **Gates**: BE targeted por checkpoint + guardias **67/67** · rutas `/api/` **214→226** · tablas **60** · cabeza única `c8d9e0f1a2b3` · **BE full 1428/0F/49S** · FE 524/524 · build 0 · E2E 4/4.
- **Sensibilidad S1–S10** completas con RED quirúrgica y restore desde SHA de implementación (S4 = clúster 4:4 del apply-path, documentado; S7 = mutación de oro 1:1/2:2); post-mutación en verde en cada checkpoint.
- **Push**: cada checkpoint empujado y verificado (`REMOTE_SHA_MATCH = PASS`). La primera corrida full detectó 9 fallos (gobernanza de matriz RBAC/purga/pin de cabeza + contaminación de fase/lote sembrado + literales de fecha en tests) — **todos resueltos** en `4b859b2`; doc-fixup final ancla el cierre `bed4b3f`.
- **Certificación**: `specs/GA-REQ-061/GA_REQ_061_CERTIFICATION.md` + `GA_T14_CERTIFICATION.md` (evidencia `specs/GA-REQ-061/evidence/{red,green,sensibilidad,post-mutation,fe,e2e}`).
- **Siguiente**: **T12** en el orden canónico; R-142 permanece diferida (AOD-17).

## AE-58 · 2026-09-16 · T12 CERRADA TÉCNICAMENTE — Wave C del propietario aplicada (GA-REM-022) + recertificación E2E

- **Decisión Owner** `b58136a` (fórmula a fórmula): R-131 corregir (FCR = alimento/ganancia; **OD-22 intacto**) · edad de lote cerrado congelada en `end_date` · R-132 aprobada (base = apertura + recepciones; `UNKNOWN ≠ 0`) · R-133/R-134 `DEFERRED_FUNCTIONAL_DEFINITION` (retiro de superficies certificadas; sin fórmulas inventadas) · R-141 corregir (mismo conjunto filtrado que R-218). Micro-confirmaciones: **NO** (mandato de ejecución autónoma).
- **RED** `3398dc4` — 5 fallos causa-exacta (FCR canónico: campos inexistentes + valor fabricado; R-141: 5250, 3 muestras, 510).
- **IMPL** `9e76254` — services `reports`/`dashboard`; fixtures `r184/r186/r187` con `current_avg_weight` (Δ=1000 g × base = 1000 kg ⇒ FCR canónico numéricamente idéntico al anterior ⇒ bandas OD-22 intactas, verificado por r187); FE retira AFCR/vacunación de `LotReportPage`/`ReportsPage`; E2E p15 ajustado; docs micro-tranca → OWNER_APPROVED_IMPLEMENTED; nota provisional → SUPERSEDED.
- **Gates**: GREEN dirigido 42/42 · regresión KPI/reportes **142/0/35** · sensibilidad **M1** (denominador `/1000` fabricado) 1F exacto y **M2** (filtro R-141 fuera de uniformidad) 1F exacto, con restauración tras cada mutación · FE **524/524** + `tsc` 0 + build 0 · E2E **111/111** · **BE full 1436/0F/49S** (supersede la corrida provisional 1431/0/49, clasificada SUPERSEDED). Preflight BE full = 1435/1F/49S: único fallo el guard `T-028-04` (fecha ISO en comentarios de tests R-131/R-184/R-186/R-187) — corregido en `af1f1e2` (solo texto; preflight conservado como evidencia) y re-corrida full limpia.
- **Certificación**: `audit/ga-claude-final-audit/specs/GA-REM-022/GA_REM_022_CERTIFICATION.md` + `GA_T12_CERTIFICATION.md`; evidencia final `specs/GA-REM-022/evidence/{red,green,sensibilidad,e2e}`.
- **Push**: pendiente de doc-fixup de cierre → `origin/main` (fast-forward, sin rewrite/reset/force); `REMOTE_SHA_MATCH = PASS`.
- **Siguiente**: **T13** (UAT del propietario, 8 lotes U1–U8 + decisiones §25 + Pista OPS). R-142 permanece diferida (AOD-17).

## AE-59 · 2026-09-16 · T13 EN CURSO — kit UAT (U1–U8) + runbook OPS (G-02…G-05) entregados

- **Arranque automático** tras el cierre de T12 (mandato del propietario).
- **Entregables**: `GA_T13_UAT_KIT.md` (8 lotes: casos núcleo, preparación, evidencia primaria admisible §32, plantilla de decisión por caso y reglas de cierre/limpieza) y `GA_T13_OPS_RUNBOOK.md` (G-02…G-05 con comandos exactos, criterios PASS y plantillas de evidencia; sanitización de secretos obligatoria).
- **Verificaciones locales**: `~/ga_uat09_credentials.txt` presente (retry GA-UAT-09 ejecutable por el propietario); `backend/seeds/live_readiness_check.py` presente; `GUIA_PRUEBAS_EN_VIVO.md` vigente como flujo de referencia.
- **Gates**: las sesiones UAT (U1–U8, prioridad U1/U2) y los ítems OPS son acciones del propietario/ops (G-02…G-05 `QUEUED` con instrumentos); decisiones §25 aplicables al cierre (GA-UAT-09 = registro de decisión del retry).
- **Siguiente**: ejecución de lotes por el propietario y de los ítems OPS; a su retorno, certificación de cierre de T13 con veredicto GO/NO-GO.

## AE-60 · 2026-09-16 · T13 — recon verificado + rehersals OPS locales + prevalidación U1/U2 (OWNER ACTION REQUIRED)

- **Recon contra repo**: `be5453f`, worktree limpio, `REMOTE_SHA_MATCH = PASS`; inventario T13, gates abiertos, findings P0/P1/P2, deferred y clasificación de despliegue → `GA_T13_RECON_STATUS.md`.
- **Rehersals locales OPS** (pgserver user-space, sin Docker; evidencia `evidence/t13-ops/`): **G-03 PASS** (401×5 → **429** en `/api/v1/login` con flag activa; calibración: payload inválido ⇒ 422 sin contar) · **G-04 PASS** (rol `avicola_app`: `usesuper=f`, `SELECT lots` OK, `CREATE ROLE` denegado; nota: GRANTs en la base de la app; SSL = host) · **G-05 PASS** (ciclo `pg_dump`/`pg_restore`: conteos idénticos 78/179/1269) · **G-02 `BLOCKED_EXTERNAL`** (sin Docker/acceso a host). Los gates canónicos en host siguen `QUEUED` para owner/ops con el runbook.
- **Prevalidación U1/U2**: **82/82 passed** en tests dedicados (logout/revocación AC04, R-199, R-200, R-153, F-01d, sesión/tenencia). Transparencia: el primer intento quedó contaminado por `FEATURE_RATE_LIMIT_ENABLED=true` persistida en la shell (17F/12E) — re-ejecutado limpio; los runs de certificación usan procesos nuevos.
- **Fichas U1/U2 entregadas** (`GA_T13_UAT_FICHAS_U1_U2.md`); sesión del propietario pendiente. **DEPLOYMENT_READINESS = BLOCKED_OWNER_DECISION**: no hay mecanismo autorizado de despliegue (workflows retirados) ⇒ decisión exacta: (A) autorizar/ejecutar despliegue manual de `be5453f` al host de UAT, o (B) declarar el entorno desplegado actual como objetivo con su SHA/limitación.
- **Siguiente**: respuesta del propietario a U1/U2 (+ decisión de despliegue); con PASS se preparan **U3–U8** automáticamente.

## AE-61 · 2026-09-16 · T13 — decisión del propietario `DEPLOYMENT=A` registrada; ejecución BLOCKED_EXTERNAL_ACCESS (runbook del administrador entregado)

- **Decisión del propietario (2026-09-16, canal chat)**: **`DEPLOYMENT = A`** — despliegue manual del producto certificado en el entorno compartido de UAT (`https://avicola.globaldv.net`), clasificado `SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT` (no producción). Registro con el texto íntegro del propietario como evidencia: `GA_T13_DEPLOYMENT_DECISION_A.md` (AOD-29 sin modificar; GitHub Actions no se reactiva).
- **SHA**: `PRODUCT_SHA = be5453f` único — `git diff be5453f..HEAD -- backend frontend e2e` **vacío** (el único commit posterior, `93b4a91`, es documental). Preflight registrado: HEAD `93b4a91`, worktree limpio, `REMOTE_SHA_MATCH = PASS`; `alembic heads` ⇒ única `c8d9e0f1a2b3`.
- **Precheck de acceso (§3)**: estación del agente sin Docker (`NOT_FOUND`) y host externo (`avicola.globaldv.net → 84.247.161.106`); sin acceso SSH/checkout/permisos Docker autorizados. No se buscaron credenciales (fuentes prohibidas intactas). ⇒ **`DEPLOYMENT_EXECUTION = BLOCKED_EXTERNAL_ACCESS`** (no se cambia a B).
- **Baseline pre-deploy externo** (2026-09-16T02:56Z; evidencia `evidence/t13-ops/deploy-a-preflight-baseline.log`): bundle `index-apu3WWcr.js` (Last-Modified 14-sep) ≠ producto certificado; `/login` 200; `/health` externo = fallback SPA (health real del backend: `:8002/health`).
- **Instrumento entregado**: `GA_T13_DEPLOYMENT_A_ADMIN_RUNBOOK.md` — comandos exactos para el administrador: preflight/captura, verificación de cabeza única, **respaldo obligatorio** (STOP si falla ⇒ `BLOCKED_BACKUP_SAFETY`), build+push canónico EX-01 (réplica del CI retirado) o fallback local con `pull_policy: never`, migración por **entrypoint** (GA-REM-024; nadie más), startup, health A–G, marcadores GA-FE-01, rollback con IDs de imagen previos, G-02…G-05 (G-03 corregido a `/api/v1/login`) y plantilla de evidencia a devolver.
- **Espera**: despliegue PASS por el administrador ⇒ verificación de evidencia ⇒ prevalidación técnica U1/U2 ⇒ **sesión Owner U1/U2**. No se ejecuta UAT contra el build anterior; no se marcan aceptaciones.

## AE-62 · 2026-09-16 · T13 — despliegue A ejecutado por el propietario (EX-01); verificación externa PASS; G-03 = FAIL observado en runtime

- **Mecanismo**: el propietario restauró los workflows `docker-push-backend/frontend` a `.github/workflows/` (`f38350a`, autor `dvconsultores`, 16:28:26Z) — **idénticos** a los de `workflows-retired/` (diff -q = iguales) ⇒ cadena EX-01 activa (push → build+push `:latest` → Watchtower → recreación → entrypoint migra). El agente no reactivó nada; la certificación sigue local (AOD-29 intacto).
- **Despliegue verificado externamente** (`evidence/t13-ops/deploy-a-runtime-verification.log`): bundle `index-apu3WWcr.js` (14-sep) → **`index-r36pBbNX.js`** (Last-Modified **16:28:48Z**; sha256 `3047f5c…`; 1.343.639 bytes); marcadores GA-FE-01 M1–M7 + control `switch-company` + `cutover-templates` (T14) presentes; root/login 200; backend sirviendo (401 JSON con cabeceras de seguridad) ⇒ GA-REM-024 implica migración completada. ⇒ **`DEPLOYMENT_STATUS = PASS` (verificación externa)**; evidencia cruda del host (digests/log/`alembic current`) pendiente como complemento.
- **G-03 ejecutado (runtime, externo)**: 12 intentos consecutivos `POST /api/v1/login` (credencial falsa) ⇒ **401 ×12, sin 429** (esperado 401×5 → 429). **`FAIL` observado** — no se marca PASS; diagnóstico host pendiente (flag efectivo en contenedor, umbral, clave del proxy GAP-11, compose del host actualizado). Referencia local: 401×5 → 429 (`g03-local-rehearsal.log`).
- **OPS**: G-02/G-04/G-05 siguen `BLOCKED_EXTERNAL` (requieren host). Nota: `/openapi.json` y `/docs` externos devuelven el fallback SPA (no exponen backend).
- **U1/U2**: `READY_FOR_OWNER` (fichas entregadas; prevalidación local 82/82; probes runtime OK). **Sin aceptaciones marcadas.**
- **Siguiente**: (1) host: G-02/G-04/G-05 + diagnóstico/re-ejecución G-03 + evidencia cruda del deploy; (2) sesión Owner U1/U2 contra el build desplegado; cierre T13 con veredicto GO/NO-GO.

## AE-63 · 2026-09-16 · T13 — reconciliación AOD-29 vs workflows (`GOVERNANCE_DRIFT=TRUE`) + estados separados de deployment + HOLD de U1/U2 + paquete de ventana host

- **Hechos verificados** (detalle en `GA_T13_GHA_AOD29_RECONCILIATION.md`): `.github/workflows/` = 2 ficheros (docker-push-backend/frontend; idénticos a los retirados; triggers push/dispatch/call; plataforma los reconoce `active`). Commit `f38350a` (autor `dvconsultores`; sello local 16:28:26Z) — **sin texto formal de decisión**. Runs **35122083759/35122083928** (`push`, `success`, 16:28:08Z) ⇒ **GitHub Actions reactivado de facto**; imágenes `sha-f38350a`/`latest` publicadas (BE `16:28:34Z` `sha256:6f0edbfa…`; FE `16:28:52Z` `sha256:29cd2eff…`) y desplegadas por Watchtower. Entre los runs del 2026-09-14T12:46Z (`571b4d5`) y hoy no hubo runs (retiro efectivo AOD-29 hasta `f38350a`).
- **Clasificación**: **`GOVERNANCE_DRIFT = TRUE`** (contradice AOD-29 + Clar. 01: «los push no deben disparar Actions»; `ACTIVE_WORKFLOW_COUNT=0`; `AUTO_DEPLOY = NOT_AVAILABLE…`). El agente no tocó workflows ni historia. **Decisión A/B requerida del propietario** (presentada, no tomada).
- **Estados de deployment separados (mandato §3)**: `RUNTIME_EXTERNAL_VERIFICATION = PASS` · `HOST_DEPLOYMENT_EVIDENCE = PENDING` · `DEPLOYMENT_GATE = PENDING` (rubric: KIT §3 + runbook §8/§12). No se usa `DEPLOYMENT_STATUS=PASS` plano.
- **G-03**: FAIL observado (12×401 sin 429). Paquete de ventana host (diagnóstico/corrección config-only con evidencia causa-exacta ANTES/DESPUÉS, evidencia cruda del deploy con digests de contraste, G-02/04/05) en la **adenda §14** del runbook. Sin redeploy innecesario.
- **U1/U2**: `PREPARED — EN HOLD` (mandato §8); no se piden sesiones al propietario todavía; fichas con banner de hold.
- **Siguiente**: (1) decisión A/B de gobernanza; (2) ventana host (G-03 PASS + G-02/G-04/G-05 + evidencia cruda); (3) con todo cerrado ⇒ re-prevalidar U1/U2 y volver al gate owner.

## AE-64 · 2026-09-16 · T13 — `DEPLOYMENT_MECHANISM = B` formalizado (AOD-29 Addendum); `GOVERNANCE_DRIFT` RESUELTO; G-03 con causa raíz en código + paquete config-only; cadena de host pendiente

- **Decisión del propietario**: `DEPLOYMENT_MECHANISM = B` (texto íntegro en el Anexo de `GA_OWNER_DECISION_AOD29_DEPLOYMENT_MECHANISM_ADDENDUM.md`): autoriza SOLO `docker-push-backend/frontend` (build→Docker Hub→Watchtower); `GITHUB_ACTIONS_GENERAL_CI = RETIRED`; `LOCAL_CERTIFICATION = MANDATORY`; sin nuevos workflows/servicios; sin ampliar triggers; trazabilidad commit→run→tag/digest→runtime; entorno SHARED UAT (no producción).
- **`GOVERNANCE_DRIFT = RESOLVED_BY_OWNER_DECISION`** (f38350a se preserva como reactivación previa a la formalización; sin reescribir historia; addendum de una línea en el doc AOD-29 original).
- **G-03 (causa raíz en código)**: `config.py:115` default `false`; `main.py:15-33` decorador no-op cuando el flag no está activo; `@rate_limit("5/minute")` en `auth/router.py:30`. El contenedor del host conserva env sin el flag (Watchtower no relee compose al recrear). El compose actual inyecta `${FEATURE_RATE_LIMIT_ENABLED:-true}` (línea 29); `.env.example` trae `false` (posible override del host). Corrección **config-only** en ventana host: asegurar línea/.env + `docker compose up -d backend` + retest ANTES(401×12)/DESPUÉS(401×5→429) — paquete en la adenda §14.1 del runbook; si no se corrige con `true` efectivo ⇒ hallazgo técnico por cadena completa (sin tocar producto en la ventana).
- **Evidencia**: `evidence/t13-ops/host-evidence-package.md` (campos externos completos; `PENDIENTE_HOST` marcados).
- **U1/U2**: `PREPARED — EN HOLD` (se mantiene). No se abre UAT.
- **Siguiente**: ventana de host (G-03 + G-02/G-04/G-05 + evidencia) ⇒ cierre `DEPLOYMENT_GATE` ⇒ re-prevalidación U1/U2 ⇒ `READY_FOR_OWNER` ⇒ STOP OWNER UAT.

## AE-65 · 2026-09-16 · T13 — ventana final de host/OPS emitida por el propietario; runbook auto-contenido + plantilla de reporte único (entrega host pendiente)

- **Mandato del propietario** (2026-09-16): ventana final host/OPS con reglas estrictas (sin redeploy completo, sin tocar frontend, sin BD/volúmenes, sin downgrade, sin secretos) y orden: G-03 (diagnóstico → corrección config-only → `docker compose up -d backend` → retest `401×5→429`; si persiste ⇒ DETENERSE y reportar, sin tocar código) → G-02 → G-04 → G-05 → evidencia de deployment; entrega = **reporte único** (secuencia HTTP 1–6, flag antes/después, ALEMBIC_AFTER, digests de contenedores, BACKUP_STATUS, observaciones + logs sanitizados).
- **Alineación**: `GA_T13_DEPLOYMENT_A_ADMIN_RUNBOOK.md` §11 ahora **auto-contenido** (G-02/G-04/G-05 con comandos exactos; G-03 → §14.1) + **§15** con el formato de reporte; plantilla `evidence/t13-ops/HOST_WINDOW_FINAL_REPORT_TEMPLATE.md`; contrastes de digests en §14.2.
- **Ejecución**: pertenece al host (agente: `BLOCKED_EXTERNAL`). Al volver el reporte: registro, validación del contrato (estados separados), cierre `DEPLOYMENT_GATE` si todo PASS ⇒ re-prevalidación U1/U2 ⇒ `READY_FOR_OWNER` ⇒ STOP OWNER UAT.
- **U1/U2**: `PREPARED — EN HOLD` (sin cambios).

## AE-66 · 2026-09-16 · T13 — `T13_PARALLEL_CONTINUATION = AUTHORIZED` (Owner): U1/U2 liberadas para sesión humana; host gates `BLOCKED_EXTERNAL_TEMPORARY`; T13 continúa sin cierre

- **Decisión del propietario** (texto íntegro en el Anexo de `GA_OWNER_DECISION_T13_PARALLEL_CONTINUATION.md`): `HOST_ADMIN_AVAILABILITY = UNAVAILABLE_TEMPORARILY`; `HOST_GATES = BLOCKED_EXTERNAL_TEMPORARY`; continuar todo lo que no dependa del host. **Estados conservados**: G-02/G-04/G-05 = `BLOCKED_EXTERNAL`; G-03 = `FAIL_OBSERVED / HOST_FIX_PENDING`; `HOST_DEPLOYMENT_EVIDENCE = INCOMPLETE`; `DEPLOYMENT_GATE = PENDING`.
- **U1**: autorizada con limitación explícita `U1_SECURITY_RATE_LIMIT = PENDING_HOST_G03` (si el cambio del host es solo config del flag, no se repite U1 completa). **U2**: autorizada completa (no depende de G-02/G-04/G-05).
- **U3–U8**: se preparan automáticamente tras resultados U1/U2; los casos que dependan de gate host se marcan `UAT_<ID> = BLOCKED_BY_HOST_GATE`.
- **No cierre**: `T13_FINAL_CERTIFICATION` y `PRE_SAP_GO` esperan a G-02…G-05 PASS + `HOST_DEPLOYMENT_EVIDENCE = COMPLETE`. El agente no marca PASS/OWNER_ACCEPTED (UAT humano).
- **Siguiente**: sesión humana U1/U2 (fichas presentadas); con PASS (o PASS con observaciones no bloqueantes) ⇒ registro de evidencia primaria ⇒ preparación automática U3–U8.
