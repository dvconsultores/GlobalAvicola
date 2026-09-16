# GA · OWNER DECISION — **AOD-29**: RETIRO DE GITHUB ACTIONS DEL CAMINO DE CERTIFICACIÓN PRE-SAP

| Campo | Valor |
|---|---|
| **ID** | **AOD-29** (siguiente libre tras AOD-28; serie canónica de la cola del programa) |
| **Fecha de decisión** | **2026-09-14** |
| **Autoridad** | Propietario de Global Avícola |
| **Alcance** | Todas las tranches PRE-SAP **desde esta decisión en adelante** (T8+ en curso y siguientes) |
| **Estado** | **RESUELTA — POLÍTICA VIGENTE** (no es un gate pendiente; es una decisión informativa de gobernanza) |
| **Reemplaza a** | — (los requisitos históricos de CI **no se reescriben**; ver §4) |

## 0 · Addendum — AOD-29 **Clarification 01** (2026-09-14) — «GitHub Actions Retired · Git Push Preserved»

El propietario **aclara** el alcance de AOD-29: retirar GitHub Actions **no**
retira GitHub como repositorio remoto ni suspende `git push`. La interpretación
previa registrada en este documento (`PUSH = NOT_PERFORMED_BY_OWNER_POLICY`) era
**parcialmente incorrecta** y queda **corregida prospectivamente, sin reescribir
historia**. Política efectiva: `GITHUB_REPOSITORY = ACTIVE` · `GITHUB_ACTIONS =
RETIRED` · `LOCAL_CERTIFICATION = REQUIRED` · `PUSH_POLICY = REQUIRED` ·
`PUSH_TARGET = origin/main` · `REMOTE_SHA_VERIFICATION = REQUIRED`. Los workflows
activos fueron movidos a `.github/workflows-retired/` (`ACTIVE_WORKFLOW_COUNT =
0`). Registro canónico:
`GA_OWNER_DECISION_AOD29_CLARIFICATION_01_PUSH_PRESERVED.md` (incluye inventario
de workflows e impacto de deploy `AOD29-DEPLOY-IMPACT`).

### Addendum — Deployment Mechanism (2026-09-16)

**AOD-29 · Addendum de despliegue** (decisión del propietario, 2026-09-16): se
autoriza **únicamente** `docker-push-backend.yml` + `docker-push-frontend.yml`
(`DEPLOYMENT_WORKFLOWS = AUTHORIZED`; `AUTO_DEPLOY_SHARED_UAT =
AUTHORIZED_FOR_DEPLOYMENT_ONLY`). `GITHUB_ACTIONS_GENERAL_CI = RETIRED` — el resto
de workflows permanece retirado y la certificación sigue **local**
(`LOCAL_CERTIFICATION = MANDATORY`). Este addendum **sustituye prospectivamente
solo** la cláusula «los push no deben disparar Actions»; el resto de AOD-29 y la
Clar. 01 siguen vigentes. `GOVERNANCE_DRIFT = RESOLVED_BY_OWNER_DECISION`.
Registro: `GA_OWNER_DECISION_AOD29_DEPLOYMENT_MECHANISM_ADDENDUM.md`.

## 1 · Decisión (texto del propietario, verbatim)

> «A partir del 14-09-2026, GitHub Actions deja de formar parte del camino obligatorio de certificación de nuevas tranches PRE-SAP. La certificación técnica se ejecutará mediante gates locales reproducibles. Los requisitos históricos de GitHub Actions permanecen como evidencia histórica. Los AC futuros que dependan exclusivamente de GitHub Actions se clasifican `NOT_APPLICABLE_BY_OWNER_DECISION` y deben apuntar a esta Owner Decision.»

Motivo declarado: **consumo/coste de minutos de ejecución**. La decisión **no** reduce calidad, pruebas, RED→GREEN, sensibilidad, regresión, E2E, seguridad, Specs ni AC.

## 2 · Política operativa derivada

| Materia | Política |
|---|---|
| GitHub Actions | **NO USAR** como gate de nuevas tranches (no esperar runs, no observar, no descargar artifacts, no `gh`). |
| Git | **COMMIT LOCAL = SÍ · PUSH = SÍ** (requerido tras la certificación local; **AOD-29 Clar. 01**). Sin force-push, sin reescribir historia publicada. *(La interpretación original «PUSH = NO» quedó corregida en §0.)* |
| Certificación | Gates **locales reproducibles**: SPEC→AC→BASELINE→RED→commit→IMPL→targeted GREEN→regresión dirigida→commit local→sensibilidad→**restauración por SHA explícito** (`git restore --source=$IMPL_COMMIT`)—>post-mutation GREEN→suite BE completa→suite FE completa→`tsc`→`build`→E2E local cuando sea posible→evidencia→certificación local→commit local→siguiente tranche. |
| Clasificación de evidencia | Lo que dependía de Actions se registra **`NOT_APPLICABLE_BY_OWNER_DECISION`** — nunca `PASS/GREEN/OBSERVED/VERIFIED` si no se ejecutó. |
| Publicación de cierre | `LOCAL_CERTIFIED_SHA=<sha>` · `REMOTE_SYNC_STATUS=NOT_REQUIRED_CURRENT_OWNER_POLICY` · `GITHUB_ACTIONS_STATUS=NOT_APPLICABLE_BY_OWNER_DECISION`. **No** se usa `HEAD == origin/main` como gate (el retraso de `origin` es esperado). |
| Mutaciones | `IMPLEMENTATION_COMMIT` registrado; HEAD verificado == ese commit; worktree limpio; restaurar **desde el SHA** (nunca `checkout` implícito); registrar `RESTORE_SOURCE` y `POST_RESTORE_RESULT`. |
| Evidencia local | Se sigue versionando localmente (`evidence/<tranche>/{red,green,regression,mutations,runtime,e2e,build,certification}`), logs sanitizados (sin credenciales; el DSN efímero de `run_tests.sh` se redacta). |

## 3 · Reconciliación (sin reescribir historia)

- `GA_PRE_SAP_REMEDIATION_MASTER_ROADMAP.md`: addendum de gobernanza; filas T1/T2 intactas.
- `GA_PRE_SAP_PROGRAM_STATUS.md`: política vigente + campos de publicación local.
- `GA_AUTONOMOUS_EXECUTION_LEDGER.md`: entradas históricas intactas; alta de `AE-45`.
- `GA_OWNER_GATE_QUEUE.md`: fila informativa AOD-29; G-01 (AC-06) permanece **cerrado con su evidencia histórica**.
- Certificaciones T3–T7: **addendum** por AOD-29 en su sección CI (la redacción original se conserva); T8 en adelante nacen con la clasificación N/A.
- `docs/07-qa-plan.md`: enmienda de política (los gates locales sustituyen al gate externo).
- Specs: los AC que exigieran literalmente Actions/CI externo/run URL/Run ID/artifact se anotarán `N/A — OWNER DECISION AOD-29` conservando su redacción (revisión realizada: sin pendientes en paquetes futuros T9–T13 a la fecha).

## 4 · Límites de la decisión

- **NO** autoriza SAP (sigue `NOT_STARTED`).
- **NO** modifica la conclusión histórica de T1 (AC-06, runs #10/#11) ni de los runs ya observados de T2 (#26) — permanecen como evidencia histórica válida.
- **NO** elimina gates locales; los endurece como única vía.
- **NO** convierte defaults autónomos en `OWNER_ACCEPTED`: los gates humanos (AOD-13, AOD-25…28, etc.) siguen vigentes en la cola.
- Los procesos P-01…P-17 siguen subiendo de estado solo con su evidencia E2E contractual (la tranche técnica cerrada ≠ proceso certificado).

## 5 · Efectos inmediatos aplicados con esta decisión

1. Runs de Actions **en curso de la sesión**: cancelados los cancelables (2 confirmados + los que la propia plataforma ya no permitía cancelar); **no habrá nuevos push** que disparen más.
2. Cierre local de **T8** (P1-12-REOPEN · R-198 · R-219) completado con evidencias locales; `GA_T8_CERTIFICATION.md` clasifica su CI como `NOT_APPLICABLE_BY_OWNER_DECISION`.
3. Tranches siguientes (T9…): flujo local completo por tranche, commits locales, sin push.
