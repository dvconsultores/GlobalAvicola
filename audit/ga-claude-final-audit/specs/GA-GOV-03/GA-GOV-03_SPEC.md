# GA-GOV-03 · SPEC — GOBERNANZA DE PRUEBAS Y CERTIFICACIONES (SUITE VERDE REPRODUCIBLE · CI · REGLA DE EVIDENCIA)

| Campo | Valor |
|---|---|
| **ID** | `GA-GOV-03` · Tipo `PROCESS SPEC` (higiene de pruebas · CI · regla de certificación · reconciliación documental) · Prioridad **P1 (gobernanza)** · Estado `SPEC_READY` (sin código) |
| **Hallazgo** | `GA-GOV-03_FINDING.md` |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) · runtime `https://avicola.globaldv.net` (`index-DDCcWL76.js` == build local de HEAD) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Fuente normativa** | `GA-REM-013` (quality gates), `GA-REM-014` (entorno aislado), `GA-REM-016` (certificación E2E), `R-72` (validez de pruebas), `docs/02-functional-spec.md §3.11`, regla del programa «no GREEN por declaración» (auditoría independiente, encargo §51/§52) |
| **Decisiones intactas** | Ninguna decisión de negocio (OD/AOD/BU-D) se toca; no se relaja ninguna regla implementada (BR-20, BR-21, BR-03, R-118 u OD-16) para «poner verde» |
| **Decisión del propietario** | **no requerida** para el núcleo (higiene + CI + regla de evidencia); opcional para C-03 (¿exigir PR con CI verde en adelante o mantener push directo con suite informativa?) |
| **Migración** | ninguna · **Endpoint nuevo** ninguno · **Permiso nuevo** ninguno · **Producto** intacto |
| **Interdependencias** | Precondición de toda la cola (`GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §3`, orden 1); habilita la recertificación P-01…P-15; relaciona R-213 (hallazgo colateral del grupo B) y P1-12 (grupo C/reconciliación) |

## 1 · Contexto

El programa declara certificaciones (13 informes `PROCESS-*-CERTIFICATION.md`, suites «PG declaradas a CI», aceptaciones del propietario) que **no son reproducibles en HEAD**: la suite backend completa termina en `1201 passed · 25 failed · 49 skipped` (`evidence/backend_full_suite.log:624`), la suite Playwright de procesos en `117 passed · 12 failed` (`evidence/playwright_e2e.log:561-575`), y el CI que ejecuta pytest/vitest **solo se dispara en `pull_request`** (`.github/workflows/backend-ci.yml:4-12`, `frontend-ci.yml:8-15`) mientras los 466 commits del repositorio son pushes directos a `main` (`git log --merges | wc -l` = 0). `quality-gates.yml` sí corre en `push`, pero no ejecuta la suite (`:24-67`). Consecuencia: ninguna «suite declarada a CI» se ha ejecutado, y seis certificaciones de proceso (P-03, P-04, P-05, P-10, P-11, P-15) tienen hoy su suite roja. Los 37 fallos actuales son **TEST_DEFECT** (pruebas obsoletas frente a reglas posteriores, fixtures inválidos, guardas literales); **0 APP_DEFECT directo** — es un problema de **gobernanza**, no de producto.

## 2 · Evidencia

`GA-GOV-03_FINDING.md §2` (corrida completa, clasificación por grupos A/B/C, CI, certificaciones, aceptaciones, backlog). Resumen verificable:

| Ítem | Evidencia |
|---|---|
| Backend 25 failed | `evidence/backend_full_suite.log:73-537, 598-624`; reproducido en aislamiento 189/25 (`backend_targeted_failing.log:550-575`) |
| Playwright 12 failed | `evidence/playwright_e2e.log:202-559, 561-575` |
| CI solo PR | `backend-ci.yml:4-12`; `frontend-ci.yml:8-15`; `quality-gates.yml:17-67` |
| Certificaciones sin artefacto | 13 ficheros `audit/remediation/PROCESS-*-CERTIFICATION.md`; `grep -cE '\b[0-9a-f]{7,40}\b'` = 0 en 12 de 13 |
| Aceptaciones sin evidencia primaria | `audit/ga-uat-07/…RECORD.md`, `ga-uat-08/…`, `ga-fe-08/…` (walkthroughs del agente, capturas duplicadas md5, limpieza previa) |
| Deriva documental | `R-189`/`GA-UAT-09` ausentes del backlog (grep = 0); `OD-21…25` sin fichero en `specs/remediation/` |
| Verde de control | `evidence/frontend_checks.log`: vitest 314/314, tsc 0, build OK; paridad runtime PASS |

## 3 · Causa raíz

1. **Convención de CI desalineada con la operación real**: los workflows de test se restringieron a `pull_request` «para no bloquear el deploy» (`backend-ci.yml:4-9`), pero el flujo real es push directo a `main` ⇒ la red de seguridad nunca se activa. No existe ejecución programada ni informativa en `push`.
2. **Pruebas acopladas a reglas y fixtures antiguos sin actualización**: OD-16 cambió la frontera 403→404 fail-closed (`9ffc5ec`); BR-20 (`a759a17`), BR-21 (`c653ff8`) y la semántica de huevo fértil (`64dff76`) endurecieron validaciones; las suites no se actualizaron. La cabeza Alembic avanzó (`y5z6a7b8c9d0`, `b4d8c3a`) y dos guardas quedaron fijadas a `x4y5z6a7b8c9`.
3. **Fixtures con correo de dominio reservado** (`@e.test`): la lectura estricta de `EmailStr` en `/me` los hace inválidos (R-213 colateral); la suite R-188 dependía de un CI que nunca corrió.
4. **Falta de regla de evidencia**: certificaciones y aceptaciones se sostienen en declaraciones, sin artefacto de ejecución, commit certificado ni sesión del propietario en varios casos.

## 4 · Impacto de negocio

Sin una suite verde reproducible en HEAD no existe línea base fiable de certificación: la puerta §53 («todo proceso pre-SAP en `FUNCTIONALLY_CERTIFIED_E2E`») no puede abrirse, la cola de remediación no puede validar regresiones, y el veredicto GO/NO-GO no es defendible ante el propietario. El coste de subsanación es bajo y **no toca producto** (`backend/tests/`, `e2e/`, `.github/workflows/`, `backend/scripts/`, documentación).

## 5 · Comportamiento actual

- `run_tests.sh` (PG aislado): 25 rojos deterministas de tres grupos (A: 17 aserciones OD-16 obsoletas; B: 5 fixture `.test`; C: 3 guardas literales).
- `scripts_e2e.sh`: 12 rojos (11 fixtures obsoletos frente a BR-20/BR-21/BR-03/R-118 + 1 locator ambiguo).
- CI: ninguna ejecución de suite; `quality-gates.yml` solo `compileall` + integridad Alembic + `test_environment_guard` + grep de credenciales.

## 6 · Comportamiento esperado

1. **Suite backend completa verde en HEAD** tras actualizar los 25 casos a las reglas vigentes (o documentar su invalidez con reescritura), **sin tocar `backend/app`**.
2. **Suite Playwright verde en HEAD** tras actualizar los 12 casos (fixtures a BR-20/BR-21/R-118/R-172; locator de `p03-curvas-ui` desambiguado), **sin tocar `frontend/src`**.
3. **CI en `push` a `main` que ejecute ambas suites con PostgreSQL**, como job **independiente y no bloqueante del docker-push** (se preserva la invariante «los tests nunca bloquean el deploy»: job paralelo, sin `needs:` desde `docker-push-*`); resultado publicado como artefacto (`junit`/log) del run.
4. **Regla «no GREEN por declaración»**: toda certificación nueva cita (a) commit exacto, (b) comando ejecutado, (c) artefacto de corrida versionado, (d) enlace al run de CI. Plantilla en `audit/remediation/` + checklist de cierre.
5. **Reconciliación documental**: `R-189` y `GA-UAT-09` entran al `REMEDIATION_BACKLOG.md`; `OD-21…OD-25` ganan fichero índice en `specs/remediation/` (o constancia explícita de su hogar en `audit/`); `GA-REM-016` actualiza su estado.

## 7 · Alcance

- `backend/tests/` (25 casos + utilidades de fixture: helper de usuario con dominio válido `@example.com` y `/me` tolerante — R-213 se implementa con su propio paquete; aquí la **prueba** usa el fixture corregido).
- `e2e/` (12 casos), locator de `proceso-p03-curvas-ui.spec.ts`.
- `.github/workflows/` (nuevo job de suite en `push`, sin tocar los docker-push).
- `backend/scripts/run_tests.sh` (si requiere flag para CI), `scripts_e2e.sh`.
- `audit/remediation/REMEDIATION_BACKLOG.md` + `specs/remediation/INDEX.md` + plantilla de certificación.

### 7.1 · Detalle caso a caso — requisito de actualización

**Grupo A · OD-16 fail-closed (17):** actualizar aserción `403`/visibilidad → **`404` «no encontrado» / fila invisible** (contrato vigente `9ffc5ec`; test canónico nuevo `tests/test_od16_global_read_boundary.py`):

| Caso (`backend/tests/…`) | Aserción actual | Requerido |
|---|---|---|
| `test_lots_bu_enforcement.py` `test_l08_put/close/activate_manual/phases` (×4) | `404 == 403` | esperar `404` con `detail` «Lote no encontrado» |
| `test_lots_bu_enforcement.py` `test_l11…` | lote de unidad apagada visible | invisible (fail-closed) |
| `test_lots_bu_enforcement.py` `test_e06_control_la_autoridad_global` | `404 == 200` | `404` |
| `test_operations_bu_enforcement.py` `test_w13_submit/cancel/upload/delete` (×4) | `404 == 403` | `404` |
| `test_operations_bu_enforcement.py` `test_a08…` | `{166,167,170} == {166,167,168,170}` | conjunto fail-closed |
| `test_operations_bu_enforcement.py` `test_a13…` | `404 == 403` («Alerta») | `404` |
| `test_review_bu_enforcement.py::test_165_01` | `404 == 403` | `404` |
| `test_state_continuity.py::test_s07` | `404 == 403` | `404` |
| `test_internal_reversal.py::test_s03_s04` | `404 == 403` | `404` |
| `test_od14_productive_surfaces.py::test_s02` | `{1210,1211} <= {1210}` | visibilidad fail-closed |
| `test_review_decision_concurrency.py::test_r166_12` | `404 == 403` | `404` |

**Grupo B · fixture R-188 (5):** `test_r188_bu_lifecycle.py` `test_r188_apagar_termina_las_concesiones_vivas` · `reactivar_no_devuelve…` · `concesion_nueva_restaura…` · `zero_bu_sin_dato_productivo` · `transferencia_de_empresa_intacta` — el fixture `:79` crea `…@e.test` (`:131-133` exige `/me` 200 y recibe 500). **Requerido**: fixture con dominio válido (`@example.com`) + verificación de que la suite pasa en PG local y CI; la corrección de robustez de `/me` es **R-213** (paquete propio) y su test va allí.

**Grupo C · guardas literales (3):** `test_company_catalog::test_t10` y `test_population_invariant::test_ac14` — cabeza Alembic `x4y5z6a7b8c9` → `y5z6a7b8c9d0` (`b4d8c3a`); `test_time_determinism::test_t028_04` — retirar fechas literales `2026-09-11` de docstrings/comentarios (`test_r188_bu_lifecycle.py:3`, `test_r184_ipe_date_semantics.py:4,50`, `test_r187_ipe_od22_scale.py:3`) o parametrizar la guarda.

**Playwright (12):** p03 cadena (BR-20 fixture), p03 curvas (locator `getByText(/135/)` → selector por fila/`data-testid`), p04 (BR-20), p05 (BR-21 + cascada BR-04), p10 ×5 (BR-21 en helper `tresGeneraciones`), p11 ×2 (BR-20; aislamiento R-118 — el fixture debe crear rol/usuario **en la empresa del actor**), p15 (BR-03: disponibilidad = fértiles, `TIPO_DISPONIBLE="fertile"`).

## 8 · Fuera de alcance

- Corregir el producto (ningún defecto de producto se introduce aquí; R-213 va en su paquete).
- Reescribir los 13 informes históricos de certificación (se declaran `STALE`/`NOT_REPRODUCIBLE` en `GA_CLAUDE_PROCESS_INVENTORY.md §1` y se recertifican en la cola).
- Decidir la validez de las aceptaciones GA-UAT-01…08 (reconciliadas en `GA_CLAUDE_OWNER_ACCEPTANCE_GAP_MATRIX.md`).
- Ejecutar la recertificación de procesos (tranche posterior, con la suite ya verde).
- Auditoría de logout/`R-83`/`R-148` (paquetes propios ya existentes).

## 9 · Impacto frontend

Ninguno de producto. `e2e/*.spec.ts` (12 casos) y `scripts_e2e.sh`. Los 5 errores ESLint informativos (`GA-REM-013 AC02`) siguen diferidos.

## 10 · Impacto backend

Ninguno de producto. `backend/tests/` (25 casos + fixtures), `backend/scripts/run_tests.sh` (si aplica flag CI).

## 11 · Contrato frontend↔backend

Sin cambio (la tranche no toca contratos).

## 12 · Impacto en datos

Sin migración. La suite de tests usa PG aislado (`GA_TEST_ENV=1` + `GA_TEST_DATABASE_URL`, `test_environment_guard.py`); el job de CI levanta un servicio PostgreSQL efímero (patrón `services:`), nunca la base de un entorno real.

## 13 · Seguridad

No se debilita ninguna prueba de seguridad: las 17 actualizaciones del grupo A **endurecen** la aserción al contrato fail-closed vigente; el grep de credenciales de `quality-gates.yml` permanece; el job nuevo no expone secretos (PG efímero con credenciales del propio servicio; `JWT_SECRET_KEY` de test).

## 14 · Inquilino

N/A (no hay cambio de superficie). El caso `p11` de Playwright debe corregirse respetando R-118/OD-14.c (empresa del contexto, no del cuerpo).

## 15 · Unidad de negocio

N/A. Las 17 aserciones OD-16 actualizadas reflejan la doctrina vigente (apagado prevalece, también para la autoridad global).

## 16 · RBAC

N/A. (El caso `test_r166_12` pertenece a la cadena de seguridad de decisión concurrente; su actualización es de aserción, no de permiso.)

## 17 · Transacciones

N/A.

## 18 · Auditoría

La propia tranche produce artefactos de ejecución versionados (logs de corrida + resultado CI) que pasan a ser la evidencia de certificación de la línea base. Se archiva en `audit/ga-claude-final-audit/specs/GA-GOV-03/evidence/`.

## 19 · i18n

N/A.

## 20 · Escritorio · 21 · Móvil

N/A (las 12 Playwright corren en viewport de escritorio; no se alteran viewports).

## 22 · Manejo de errores

N/A.

## 23 · Impacto de migración

Ninguno. (Las guardas Alembic de los tests se actualizan a la cabeza vigente; no se crea migración.)

## 24 · Impacto SAP

Indirecto positivo: la matriz `GA_CLAUDE_SAP_EVENT_READINESS_MATRIX.md` apoya su fiabilidad de fuente en suites reproducibles; P-08 sigue fuera de alcance.

## 25 · Compatibilidad hacia atrás

- Los docker-push (`docker-push-backend.yml`, `docker-push-frontend.yml`) **no se tocan**; el job de suite no puede bloquearlos (sin `needs:`, workflows separados o job paralelo sin dependencia).
- `run_tests.sh` mantiene su interfaz; el comportamiento local no cambia.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| **AC-GOV03-01** | `backend/scripts/run_tests.sh` en HEAD con solo `backend/tests/**` actualizado ⇒ **0 failed** (≥1201 passed; los 25 actualizados/reclasificados); log versionado |
| **AC-GOV03-02** | `bash scripts_e2e.sh` ⇒ **0 failed** (129 passed); log versionado |
| **AC-GOV03-03** | Los 25 casos del grupo A/B/C quedan verdes **sin** diff en `backend/app/**` (guard: `git diff --stat` limitado a `backend/tests/**`) |
| **AC-GOV03-04** | Los 12 Playwright verdes **sin** diff en `frontend/src/**` |
| **AC-GOV03-05** | Workflow de suite en `push` a `main` ejecuta pytest (PG efímero) + vitest y publica artefacto; **no** es dependencia de los docker-push |
| **AC-GOV03-06** | Verificación operativa de CI: run del workflow sobre el commit de cierre con ambas suites verdes (enlace de run + artefacto) |
| **AC-GOV03-07** | Regla «no GREEN por declaración» publicada (plantilla + checklist) en `audit/remediation/`; el cierre de esta spec la aplica a sí misma |
| **AC-GOV03-08** | `R-189` y `GA-UAT-09` con entrada en `REMEDIATION_BACKLOG.md` (con `CLOSED_TECH_UAT_PENDING` y referencias); `specs/remediation/INDEX.md` con `OD-21…OD-25` y `GA-REM-016` actualizado |
| **AC-GOV03-09** | Suite de guardas (`test_time_determinism`, cabezas Alembic) verde sin fechas literales nuevas |
| **AC-GOV03-10** | Ninguna regla de producto relajada: `git diff` de la tranche no toca `backend/app/**` ni `frontend/src/**` salvo `**/__tests__/**` si aplica |
| **AC-GOV03-11** | El caso `p11` de aislamiento de empresa pasa con la empresa del **contexto** (R-118), sin cambio de código de `auth` |
| **AC-GOV03-12** | Certificación de cierre cita commit + comandos + logs + run de CI (aplica la regla a sí misma) |

## 27 · Pruebas (RED → GREEN del paquete)

No hay producto nuevo; la «RED» es de **estado de la suite**:

1. **RED documentada**: corrida en HEAD captura 25+12 fallos (`evidence/backend_full_suite.log`, `evidence/playwright_e2e.log` — ya en este paquete).
2. **GREEN de pruebas**: cada caso actualizado pasa en PG local (`GA_TEST_ENV=1` + `GA_TEST_DATABASE_URL` a PG efímero/CI) — criterio de aceptación individual por caso (tabla §7.1).
3. **GREEN de CI**: workflow nuevo ejecutado en el push de cierre; artefacto del run.
4. **Guardas de no-regresión del propio paquete**: (a) `git diff --stat` de producto vacío; (b) los 13 informes históricos no se reescriben; (c) las aserciones nuevas referencian la regla vigente en comentario (commit+regla) para evitar re-obsolecencia.

Diseño detallado: `GA-GOV-03_RED_E2E_UAT_DESIGN.md`.

## 28 · E2E

No aplica E2E de producto. La «ejecución de extremo a extremo» de este paquete es: `run_tests.sh` completa (PG), `scripts_e2e.sh` completa (Playwright), y el run de CI del commit de cierre. Criterio de duración: la suite backend tarda ~1210 s en local (aceptable para CI con timeout ≥ 40 min o `-n auto` si se decide paralelizar en la propia tranche — decisión C-02).

## 29 · UAT

**No requiere UAT del propietario** (sin cambio de comportamiento visible). Se informa en el acta de certificación. Si el propietario exige verificación independiente, el guion mínimo es: (1) mostrar run de CI en `push` con suite verde; (2) mostrar los dos logs de corrida local; (3) confirmar que ningún docker-push quedó bloqueado.

## 30 · Criterios de cierre

AC-GOV03-01…12 verdes · logs + run CI versionados en `specs/GA-GOV-03/evidence/` · diff de producto = 0 · backlog/index reconciliados (AC-08) · plantilla de certificación publicada · recertificación de procesos **habilitada** (no ejecutada aquí) · GA-GOV-03 → `CLOSED_TECH` en backlog al autorizar la ejecución.

> **Corrección documental D-01 (aplicada):** el registro (`GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md`) totalizaba el grupo A como «14 × TEST_DEFECT»; corregido a **17** (17+5+3 = 25, coherente con `backend_full_suite.log:624`). Recuento de paquetes del registro corregido en D-02 (22 P2 · 24 paquetes completos · 9 compactos).
