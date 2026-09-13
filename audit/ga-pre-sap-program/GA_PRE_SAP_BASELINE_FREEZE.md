# GA · PRE-SAP REMEDIATION PROGRAM — BASELINE FREEZE (TRANCHE 0 · §7)

Fecha de congelación: 2026-09-13 · Congelado por: continuidad de auditoría (ejecución DeepSeek Flash 4.1) · Estado: **ACTIVO como línea base canónica del programa de remediación**.

## 1 · Repositorio y git

| Ítem | Valor verificado | Cómo |
|---|---|---|
| Repositorio | `https://github.com/dvconsultores/GlobalAvicola` (origin sin cambios) | `git remote -v` |
| Rama | `main` | `git branch --show-current` |
| HEAD congelado | `f270d0b0aa9be374aac4f5714d3b586da1cf6c15` («GA-CLAUDE FINAL AUDIT: nota de cierre…») | `git log -1` |
| Commit de auditoría | `6c090788161a8fd808441f71385818d9ae3eb1f8` (259 ficheros, +28 318; solo `audit/**`) | `git log` |
| Remoto | `origin/main == f270d0b` | `git ls-remote origin main` |
| Worktree | limpio al congelar (tras el commit de esta tranche) | `git status --porcelain` |
| Commits posteriores a `f270d0b` | ninguno al iniciar la tranche | `git log f270d0b..HEAD` |
| Drift de producto desde `c0b4afc` (HEAD auditado) | **NINGUNO** — `git diff --name-only c0b4afc..HEAD` sin rutas `backend/app/`, `frontend/src/` ni `backend/alembic/` | grep de rutas |

## 2 · Runtime congelado

| Ítem | Valor verificado | Cómo (solo lectura) |
|---|---|---|
| URL | `https://avicola.globaldv.net` | — |
| `GET /health` | **200** (servido con cuerpo HTML de la SPA — fallback de nginx; el 200 es la señal registrada por la auditoría) | `curl` |
| Frontend desplegado | `assets/index-DDCcWL76.js` — **idéntico** a la generación auditada (sha256 `d049408a…` == build local de `c0b4afc`) | `curl /` + grep |
| Backend vivo | `GET /api/v1/operations/event-types` → **200**; `GET /openapi.json` → **200** | `curl` |
| Generación backend | marcadores C2d de la auditoría (422 para `[{}]` de alimento/incubadora; lectura tolerante del detalle) — no re-sondeados con mutaciones en esta tranche | evidencia de auditoría `GA_CLAUDE_FINAL_AUDIT_CURRENT_STATE.md` |
| Paridad repo↔runtime | **PASS** en la congelación (bundle idéntico; backend respondiendo) | — |

## 3 · Base de datos / Alembic

| Ítem | Valor | Nota |
|---|---|---|
| Ficheros de revisión | **37** (`.py`) + 1 entrada de directorio (`__pycache__`) = 38 entradas de `ls` — la cifra «38 revisiones» de la auditoría contaba la entrada de directorio (**corrección D-03**) | `ls alembic/versions | wc -l` = 38; `ls *.py | wc -l` = 37 |
| Cabeza | **única `y5z6a7b8c9d0`** | `alembic heads` (venv del backend) → `y5z6a7b8c9d0 (head)` |
| Raíz | `0c661168cb12` | parseo del grafo |
| Guardas de test obsoletas | 2 casos fijados a `x4y5z6a7b8c9` (`test_company_catalog::test_t10`, `test_population_invariant::test_ac14`) | GA-GOV-03 grupo C |
| Drift de esquema | ninguno detectado | — |

## 4 · Paquete de auditoría (entrada del programa)

| Ítem | Valor | Fuente |
|---|---|---|
| Documentos maestros | **20/20 presentes** (14 completados por Claude + 6 completados en la continuidad `6c09078`) | `audit/ga-claude-final-audit/*.md` |
| Registro de brechas | 34 entradas (24 bloqueantes = 9 P1 + 15 P2; 10 no bloqueantes = 7 P2 + 3 P3) · correcciones D-01/D-02 aplicadas | `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` |
| Paquetes de especificación | **33 carpetas** en `specs/` (24 completas ×6 ficheros + 9 compactas ×2 = 162 ficheros); R-214 solo en backlog | `find … | wc -l` = 162 |
| Procesos | 18 entradas en inventario (P-01…P-15 + OD-19 + OD-25 + X-BU); **17 pre-SAP aplicables** + P-08 fuera de alcance | `GA_CLAUDE_PROCESS_INVENTORY.md` |
| Procesos certificados E2E | **0 / 17** | id. |
| Decisiones del propietario | 20/25 `OD` resueltas-implementadas; **14 pendientes/contradictorias de alcance actual** (lista §5) | `GA_CLAUDE_OWNER_DECISION_RECONCILIATION.md` |
| UAT del propietario | 11 registros aceptados (evidencia primaria no verificable), **4 pendientes** (GA-UAT-09; GA-F01/R-189; 19-VNC CERT-PATH C; OD-19/reverso) | `GA_CLAUDE_OWNER_ACCEPTANCE_GAP_MATRIX.md` |
| Suites | backend 1201✔/25✘(TEST_DEFECT)/49; Playwright 117✔/12✘; vitest 314/314; tsc 0; build OK | evidencia de la auditoría |
| Veredicto | `PRE_SAP_FUNCTIONAL_CERTIFICATION=FAIL` · `READY_TO_BEGIN_SAP_INTEGRATION=NO` · `NO_GO_SAP_FUNCTIONAL_GAPS` | `GA_CLAUDE_PRE_SAP_READINESS.md` |

## 5 · Decisiones pendientes de alcance actual (explicitadas, §25)

`OD-05`, `OD-13.c`, `OD-16` (contrato 403/404 con tests), `OD-19` (UI), `OD-10.c`, `OD-23` (suite certificada roja), `OD-25` (UAT) + `AOD-08`, `AOD-10`, `AOD-14`, `AOD-16`, `AOD-17`, `AOD-18`, `AOD-22`. Decisiones futuras solo-SAP documentadas aparte (`OD-02`, `AOD-01…05`, `AOD-07`, `AOD-11`, `OD-24` sin código).

## 6 · Congelación

- Esta línea base es **canónica** para el programa de remediación: toda tranche de implementación parte de `f270d0b` (más los commits de governance de esta Tranche 0).
- Cualquier cambio de producto posterior **exige** un chequeo de drift (`git diff c0b4afc..HEAD -- backend/app frontend/src backend/alembic`) antes de ejecutar una tranche; si aparece producto no autorizado: `TRANCHE_0_BLOCKED_BY_PRODUCT_DRIFT`.
- Correcciones documentales acumuladas: **D-01** (17 tests grupo A), **D-02** (recuentos del registro), **D-03** (revisiones Alembic 37; carpetas de specs 33 — la narrativa previa decía «34»).
