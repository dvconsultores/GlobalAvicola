# AOD-29 Clarification 01 — GitHub Actions Retired · Git Push Preserved

Fecha: 2026-09-14 · Familia: Owner Decisions (`AOD-##`) · Base: **AOD-29**
(`GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md`) · Esta aclaratoria
**modifica únicamente la interpretación operativa** de AOD-29. No es una decisión
funcional nueva y **no reescribe historia**.

## Owner clarification

El Owner aclara que retirar GitHub Actions **NO** significa retirar GitHub como
repositorio remoto ni suspender `git push`. La interpretación previa
(`PUSH = NOT_PERFORMED_BY_OWNER_POLICY`) era **parcialmente incorrecta**:
GitHub sigue activo como repositorio oficial, respaldo, historial y referencia de
SHA; GitHub Actions deja de utilizarse y **los push no deben disparar Actions**.

## Canonical policy (efectiva desde 2026-09-14)

```
GITHUB_REPOSITORY            = ACTIVE
GITHUB_ACTIONS               = RETIRED
GITHUB_ACTIONS_STATUS        = NOT_APPLICABLE_BY_OWNER_DECISION
REMOTE_CI                    = NOT_APPLICABLE
LOCAL_QUALITY_GATES          = REQUIRED
LOCAL_CERTIFICATION          = REQUIRED
LOCAL_CERTIFIED_SHA          = REQUIRED
PUSH_POLICY                  = REQUIRED
PUSH_TARGET                  = origin/main
REMOTE_SHA_VERIFICATION      = REQUIRED
```

## Canonical flow

```
SPEC → AC → RED → IMPLEMENTATION → TARGETED GREEN → REGRESSION
→ IMPLEMENTATION COMMIT → SENSITIVITY
→ RESTORE FROM EXPLICIT IMPLEMENTATION SHA
→ POST-MUTATION REGRESSION → BE/FE/TS/BUILD GATES
→ EVIDENCE → LOCAL CERTIFICATION → EVIDENCE COMMIT
→ PUSH origin/main → VERIFY REMOTE SHA → CLOSED
```

## Explicit distinction

```
LOCAL CERTIFICATION != REMOTE CI
PUSH                != GITHUB ACTIONS
PUSH                != DEPLOY
GITHUB              != GITHUB ACTIONS
```

No convertir `NOT_APPLICABLE` en `PASS`. No convertir `PUSH REQUIRED` en
`CI REQUIRED`.

## Nota histórica

Este cambio es **prospectivo**: los documentos que reflejaron la interpretación
«AOD-29 también detenía los pushes» se corrigen con esta aclaratoria; los eventos
históricos (runs de Actions previos a AOD-29, AC-06/T1, artefactos) permanecen
exactamente como ocurrieron y no se reescriben.

---

## §A · Inventario de workflows (pre-retiro) — `HEAD 571b4d5`

| WORKFLOW | TRIGGER | PURPOSE | PUSH | PR | SCHED | MANUAL | DEPLOY | ACTION |
|---|---|---|---|---|---|---|---|---|
| `backend-ci.yml` | pull_request(main, backend/**) | Suite BE en PR | no | sí | no | no | no | RETIRADO |
| `frontend-ci.yml` | pull_request(main, frontend/**) | Suite FE en PR | no | sí | no | no | no | RETIRADO |
| `quality-gates.yml` | push(main) + pull_request | Gates (T1) | sí | sí | no | no | no | RETIRADO |
| `quality-suite.yml` | push(main) + workflow_dispatch | Suite pgserver + artefactos (T1) | sí | no | no | sí | no | RETIRADO |
| `docker-push-backend.yml` | push(main, backend/**) + workflow_dispatch | Build+push imagen BE a Docker Hub | sí | no | no | sí | **SÍ** | RETIRADO |
| `docker-push-frontend.yml` | push(main, frontend/**) + workflow_dispatch | Build+push imagen FE a Docker Hub | sí | no | no | sí | **SÍ** | RETIRADO |
| `docker-build-push.yml` | workflow_dispatch (reusable caller) | Invoca ambos pushes | no | no | no | sí | **SÍ** | RETIRADO |

Retiro: los 7 ficheros movidos a **`.github/workflows-retired/`** (con `README`
`RETIRED BY AOD-29 · NOT EXECUTED · HISTORICAL REFERENCE ONLY`). GitHub deja de
reconocerlos como workflows.

```
ACTIVE_WORKFLOW_COUNT          = 0
RETIRED_WORKFLOW_COUNT         = 7
AUTOMATIC_ACTION_TRIGGER_COUNT = 0
```

## §B · Impacto en auto-deploy (auditado, sin inventar sustituto)

| CAPABILITY | PRE-AOD29 MECHANISM | DEPENDS_ON_GITHUB_ACTIONS | STATUS_AFTER_RETIREMENT | ACTION |
|---|---|---|---|---|
| Build imagen backend | `docker-push-backend.yml` (push main, `backend/**`) → tag `latest` | **SÍ** | `NOT_AVAILABLE_WITH_GITHUB_ACTIONS_RETIRED` | ninguno (decisión aparte) |
| Build imagen frontend | `docker-push-frontend.yml` (push main, `frontend/**`) → tag `latest` | **SÍ** | `NOT_AVAILABLE_WITH_GITHUB_ACTIONS_RETIRED` | ninguno |
| Publicación `:latest` | Docker Hub vía workflows (`DOCKER_IMAGE=${{ secrets.DOCKER_USERNAME }}/globalavicola-*`) | **SÍ** | igual | ninguno |
| Pull/actualización en servidor | `watchtower` en `docker-compose.yml` (labels `watchtower.enable=true`) sobre `:latest` | Indirecto (la imagen no se publica sin Actions) | `AUTO_DEPLOY = DISABLED_AS_CONSEQUENCE_OF_AOD29` | ninguno |
| Mecanismos fuera de Actions | `docker-compose*` locales / Makefile (operación manual) | no | intactos | — |

Registro de consecuencia: **`AOD29-DEPLOY-IMPACT`** ·
`SHARED_RUNTIME_AUTO_DEPLOY = NOT_AVAILABLE_WITH_GITHUB_ACTIONS_RETIRED`.
**`GIT PUSH ≠ DEPLOY`** desde esta fecha: no se oculta; no se compensa con
CI/CD nuevo (Jenkins/Railway/hooks/SSH/cron prohibidos sin Spec/Owner Decision).

## §C · Commits locales certificados pendientes de sincronización

Tabla completada en el cierre de la micro-tranche (post-push) — ver
`GA_AUTONOMOUS_EXECUTION_LEDGER.md` (AE-47): incluye T8 (`0cefb68`, certificado
`8eb6e90`), R-215 (`4fc63b4`/`cd2e7bc`/`73a4fb9`), R-196 (`4c0f819`/`571b4d5`)
y los commits de gobernanza de esta aclaratoria.
