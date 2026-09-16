# GA · PRE-SAP — T13 · RECONCILIACIÓN GITHUB ACTIONS vs AOD-29

Fecha: 2026-09-16 (tarde) · Base del encargo: mandato de reconciliación §2 ·
Este documento **no modifica producto ni historia** · El agente **no ha
modificado** workflows, configuración ni revertido nada.

## 1 · Hechos verificados (2026-09-16)

| # | Hecho | Evidencia |
|---|---|---|
| 1 | `.github/workflows/` contiene **exactamente 2 ficheros**: `docker-push-backend.yml` (1685 B) y `docker-push-frontend.yml` (1697 B) | `ls -la .github/workflows/` |
| 2 | Ambos son **idénticos** a los de `.github/workflows-retired/` | `diff -q` = iguales (BE y FE) |
| 3 | **Triggers activos**: `push` a `main` con `paths: backend/**` o el propio fichero (BE) / `frontend/**` o el propio fichero (FE) + `workflow_dispatch` + `workflow_call` | lectura de los 2 ficheros |
| 4 | Commit **`f38350a`** — autor `dvconsultores <adominguez@dvconsultores.com>`; sello local 2026-09-16 12:28:26 −0400 (16:28:26Z, reloj local ~18 s adelantado respecto al servidor); mensaje EN «Add GitHub workflows…»; tocó **solo** esos 2 ficheros | `git show f38350a --format=fuller` + API commits |
| 5 | **GitHub Actions los reconoce ACTIVOS**: workflows API = 2 entradas, `state: active` | `api.github.com/.../actions/workflows` |
| 6 | **La reactivación disparó runs reales**: runs `35122083759` (BE) y `35122083928` (FE), evento `push`, creados **16:28:08Z**, `conclusion: success`; job BE `Build & Push Backend` 16:28:11Z→16:28:43Z | `api.github.com/.../actions/runs` + `/jobs` |
| 7 | **Imágenes publicadas en Docker Hub**: `sha-f38350a` + `latest` — BE 16:28:34Z (`sha256:6f0edbfa590b62f37e892509d35e6aa110519e99506800575cb37a1d81375817`), FE 16:28:52Z (`sha256:29cd2eff0d7d9c9772db432b44bc46efea06b37509eecbf7d6b07add77c2c6a2`) | Docker Hub API pública |
| 8 | El runtime sirve el build resultante (bundle `index-r36pBbNX.js`, Last-Modified 16:28:48Z) ⇒ **f38350a fue utilizado para desplegar** (Watchtower sobre `:latest`) | `evidence/t13-ops/deploy-a-runtime-verification.log` |
| 9 | Entre los runs del 2026-09-14T12:46Z (sha `571b4d5`) y hoy **no se observan runs** — coherente con el retiro AOD-29 (`75593f7`: «ACTIVE_WORKFLOW_COUNT=0; push no dispara Actions»); los pushes de T14/T12 posteriores no dispararon runs | lista de runs de Actions (752 históricos) |
| 10 | **No existe texto de decisión del Owner que autorice la reactivación**: búsqueda en docs (menciones de `f38350a` solo en los documentos del agente), ficheros modificados recientes, decisions registradas. El propio mandato de `DEPLOYMENT=A` (16-sep) instruía literalmente: «No modificar AOD-29. No reactivar GitHub Actions.» | grep + inventario de docs + Anexo de `GA_T13_DEPLOYMENT_DECISION_A.md` |

## 2 · Texto canónico vigente hasta hoy (AOD-29 + Clar. 01, 2026-09-14)

```
GITHUB_REPOSITORY            = ACTIVE
GITHUB_ACTIONS               = RETIRED
GITHUB_ACTIONS_STATUS        = NOT_APPLICABLE_BY_OWNER_DECISION
LOCAL_CERTIFICATION          = REQUIRED
PUSH_POLICY                  = REQUIRED  (push != CI != deploy)
ACTIVE_WORKFLOW_COUNT        = 0
AUTOMATIC_ACTION_TRIGGER_COUNT = 0
SHARED_RUNTIME_AUTO_DEPLOY   = NOT_AVAILABLE_WITH_GITHUB_ACTIONS_RETIRED
```

Cita (Clar. 01): «GitHub Actions deja de utilizarse y **los push no deben
disparar Actions**». Cita (AOD-29 §B): «Build imagen backend/frontend …
`NOT_AVAILABLE_WITH_GITHUB_ACTIONS_RETIRED`».

## 3 · Clasificación

**`GOVERNANCE_DRIFT = TRUE`.**

- Alcance del drift: **los 2 workflows de DESPLIEGUE** quedaron reactivados de
  hecho (ficheros activos, runs disparados por push, imágenes publicadas,
  auto-deploy efectivo). Los otros 5 workflows retirados
  (`backend-ci`, `frontend-ci`, `quality-gates`, `quality-suite`,
  `docker-build-push`) **permanecen retirados**.
- La reactivación contradice AOD-29 + Clar. 01 (`ACTIVE_WORKFLOW_COUNT=0`;
  «los push no deben disparar Actions»; `AUTO_DEPLOY = NOT_AVAILABLE…`).
- Fue ejecutada desde la cuenta del propietario (`f38350a`) pero **sin texto
  formal de decisión** ⇒ **no se atribuye Owner Decision**.
- **No se modifica ni borra historia**; el agente no revierte nada por
  iniciativa propia. La resolución es una decisión del propietario (§4).

## 4 · Decisión requerida del propietario (presentada — NO tomada)

### OPCIÓN A — Volver a retirar los workflows y mantener AOD-29

| Dimensión | Detalle |
|---|---|
| Qué requiere | Commit de gobernanza que mueve los 2 ficheros de vuelta a `.github/workflows-retired/` y restaura `ACTIVE_WORKFLOW_COUNT=0` (ejecutado por el agente **solo** tras decisión explícita). |
| Impacto | Coherente con AOD-29; los próximos despliegues vuelven a requerir build+push **manual** (runbook §6, ruta canónica/fallback). |
| Riesgo | Ninguno nuevo de gobernanza; riesgo operativo = cada despliegue exige ventana manual. |
| Mantenimiento | Cero. |
| Efecto sobre T13 | El despliegue ya verificado no cambia; el uso puntual de Actions queda registrado; `GOVERNANCE_DRIFT` queda cerrado por retiro + nota del incidente. Gates host (G-02…G-05) igual. |

### OPCIÓN B — Formalizar una nueva Owner Decision (sustitución prospectiva de esa parte de AOD-29)

| Dimensión | Detalle |
|---|---|
| Qué requiere | Documento de Owner Decision que autorice el mecanismo de despliegue vía `docker-push-*` → Docker Hub → Watchtower, manteniendo `LOCAL_CERTIFICATION = REQUIRED` (la certificación NO vuelve a depender de Actions). Registrar en la cola §25 y en la certificación T13. |
| Impacto | Auto-deploy activo: cada push a `main` que toque `backend/**` o `frontend/**` (o los ficheros de workflow) **reconstruye y despliega** al entorno compartido. |
| Riesgo | Despliegues no intencionales por pushes rutinarios; mitigación = disciplina (dispatch manual, ramas experimentales, congelación durante UAT) o ajuste de triggers, según fije la decisión. |
| Mantenimiento | Bajo (secretos DOCKER_* ya configurados; vigilar coste de minutos — motivo original del retiro). |
| Efecto sobre T13 | `GOVERNANCE_DRIFT` queda cerrado por decisión registered; el mecanismo usado para el despliegue A queda autorizado; gates host (G-02…G-05) igual. |

> En **ninguna** opción el agente decide ni ejecuta el cambio sin texto
> explícito del propietario. Ambas opciones pueden acompañarse de la nota de
> incidente (`GOVERNANCE_DRIFT`) sin reescribir historia.

## 5 · Registro de no-acción

- El agente **no** ha movido/creado/borrado workflows, no ha tocado `.env` ni
  configuración, y no ha revertido ningún commit con relación a esta
  reconciliación.
- Evidencia cruda de los hechos: ver §1 (consultas API reproducibles:
  workflows/runs/jobs de `dvconsultores/GlobalAvicola`; tags de Docker Hub
  `dvconsultores/globalavicola-*`).
