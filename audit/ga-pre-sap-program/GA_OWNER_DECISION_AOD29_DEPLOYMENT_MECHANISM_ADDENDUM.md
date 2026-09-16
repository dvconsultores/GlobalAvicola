# GA · OWNER DECISION — **AOD-29 · ADDENDUM — DEPLOYMENT MECHANISM = B**

| Campo | Valor |
|---|---|
| **ID** | AOD-29 · **Addendum de despliegue** (familia AOD-29; sigue a Clarification 01) |
| **Fecha de decisión** | **2026-09-16** (canal chat; texto íntegro en el Anexo) |
| **Autoridad** | Propietario de Global Avícola |
| **Estado** | **RESUELTA — POLÍTICA VIGENTE** (modificación **prospectiva** de la parte de despliegue de AOD-29) |
| **Sustituye prospectivamente** | **Únicamente** la cláusula de AOD-29/Clar. 01 según la cual «los push no deben disparar Actions» |
| **No reescribe** | Historia, commits, evidencia ni las demás cláusulas de AOD-29/Clar. 01 |

## 1 · Decisión (texto del propietario, extracto verbatim)

> «Autorizo formalmente, de forma prospectiva, la reactivación y uso de SOLO estos
> dos workflows de despliegue: `docker-push-backend.yml`, `docker-push-frontend.yml`.
> Su función autorizada es exclusivamente: push elegible a main → build de imagen →
> push a Docker Hub → Watchtower actualiza el entorno compartido UAT/test/certificación.»
>
> «Esta decisión NO reactiva GitHub Actions como sistema general de CI/CD. […]
> La certificación técnica sigue siendo LOCAL.»
>
> «GOVERNANCE_DRIFT = RESOLVED_BY_OWNER_DECISION. La reactivación previa mediante
> f38350a queda registrada históricamente como reactivación ejecutada antes de esta
> formalización. No borrar ni reinterpretar esa evidencia.»

## 2 · Campos canónicos

```
GITHUB_ACTIONS_GENERAL_CI   = RETIRED
DEPLOYMENT_WORKFLOWS        = AUTHORIZED
AUTHORIZED_WORKFLOWS        = docker-push-backend.yml
                              docker-push-frontend.yml
LOCAL_CERTIFICATION         = MANDATORY
PUSH_POLICY                 = REQUIRED
REMOTE_SHA_VERIFICATION     = REQUIRED
AUTO_DEPLOY_SHARED_UAT      = AUTHORIZED_FOR_DEPLOYMENT_ONLY
GOVERNANCE_DRIFT            = RESOLVED_BY_OWNER_DECISION
```

## 3 · Alcance y límites

- **Solo** los dos workflows citados. El resto permanece **retirado** en
  `.github/workflows-retired/` (`backend-ci`, `frontend-ci`, `quality-gates`,
  `quality-suite`, `docker-build-push`).
- GitHub Actions **no** sustituye: tests locales, E2E, sensibilidad, evidencia,
  certificación técnica ni Owner UAT. `LOCAL_CERTIFICATION = MANDATORY`.
- **No** se añaden workflows, servicios CI/CD, Jenkins, Railway hooks, SSH
  automation, cron ni mecanismos equivalentes. **No** se amplían triggers sin
  nueva Spec/Owner Decision. Se mantiene el alcance mínimo actual
  (`push` a `main` con `backend/**` / `frontend/**` o el propio fichero +
  `workflow_dispatch` + `workflow_call`).
- Entorno aplicable: **SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT**
  (`https://avicola.globaldv.net`). **No** es producción real; no presentar este
  mecanismo como despliegue productivo comercial.
- **Trazabilidad obligatoria** por despliegue: `commit → workflow run (id) →
  image tag/digest → runtime desplegado` (se registra en el ledger cuando ocurra).

## 4 · Efecto sobre AOD-29 (prospectivo, sin reescribir historia)

- Se mantiene vigente todo AOD-29 y su Clar. 01 **salvo** la cláusula «los push
  no deben disparar Actions», que queda sustituida por este addendum
  **únicamente para los dos workflows de despliegue**.
- Nota añadida en `GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md` (§0,
  «Addendum — Deployment Mechanism (2026-09-16)») apuntando a este documento.
- `f38350a` (y los runs `35122083759`/`35122083928`) quedan como **evidencia
  histórica preservada**: reactivación ejecutada antes de esta formalización.

## 5 · Consecuencias operativas

- Todo push a `main` que toque `backend/**`, `frontend/**` o los ficheros de los
  dos workflows **reconstruye y despliega** al entorno compartido (Watchtower).
  Uso intencional; registrar run + tag/digest en el ledger de ejecución.
- Los commits documentales (`audit/**`) **no** disparan despliegues
  (paths-filtro verificado: último run sigue siendo `f38350a`).
- Coste: vigilar minutos de Actions (motivo original del retiro) — si crece sin
  control, es objeto de nueva decisión.

## 6 · Registro

- `GA_T13_GHA_AOD29_RECONCILIATION.md` §6 (resolución del drift).
- `GA_AUTONOMOUS_EXECUTION_LEDGER.md` AE-64.
- `GA_PRE_SAP_PROGRAM_STATUS.md` (fila T13) y `GA_T13_RECON_STATUS.md` §3/§5.

---

## Anexo · Texto íntegro de la decisión del propietario (2026-09-16, canal chat)

```text
GLOBAL AVÍCOLA — OWNER DECISION
T13 · DEPLOYMENT MECHANISM

DECISIÓN EXPLÍCITA DEL OWNER:

DEPLOYMENT_MECHANISM = B

============================================================
1. DECISIÓN
============================================================

Autorizo formalmente, de forma prospectiva, la reactivación y uso de SOLO estos
dos workflows de despliegue:

- docker-push-backend.yml
- docker-push-frontend.yml

Su función autorizada es exclusivamente:

push elegible a main
→ build de imagen
→ push a Docker Hub
→ Watchtower actualiza el entorno compartido UAT/test/certificación.

============================================================
2. ALCANCE
============================================================

Esta decisión NO reactiva GitHub Actions como sistema general de CI/CD.

Los workflows de:

- quality gates
- quality suite
- backend CI
- frontend CI
- otros workflows previamente retirados

deben permanecer RETIRED.

La certificación técnica sigue siendo LOCAL.

GitHub Actions NO puede:

- sustituir tests locales;
- sustituir E2E;
- sustituir sensibilidad;
- sustituir evidencia;
- sustituir certificación;
- sustituir Owner UAT.

============================================================
3. ENTORNO
============================================================

El mecanismo autorizado aplica al entorno:

SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT

No es producción real.

No presentar este mecanismo como despliegue productivo comercial.

============================================================
4. MODIFICACIÓN PROSPECTIVA DE AOD-29
============================================================

AOD-29 se mantiene vigente salvo en la parte relativa a los dos workflows de
despliegue.

Formalizar un addendum/Owner Decision que establezca:

GITHUB_ACTIONS_GENERAL_CI = RETIRED

DEPLOYMENT_WORKFLOWS =
AUTHORIZED

AUTHORIZED_WORKFLOWS =
docker-push-backend.yml
docker-push-frontend.yml

LOCAL_CERTIFICATION =
MANDATORY

PUSH_POLICY =
REQUIRED

REMOTE_SHA_VERIFICATION =
REQUIRED

AUTO_DEPLOY_SHARED_UAT =
AUTHORIZED_FOR_DEPLOYMENT_ONLY

Esta decisión sustituye prospectivamente únicamente la parte de AOD-29 que
declaraba que ningún push podía disparar Actions.

No reescribir historia.

No modificar commits anteriores.

============================================================
5. GOVERNANCE_DRIFT
============================================================

Registrar:

GOVERNANCE_DRIFT =
RESOLVED_BY_OWNER_DECISION

La reactivación previa mediante f38350a queda registrada históricamente como
reactivación ejecutada antes de esta formalización.

No borrar ni reinterpretar esa evidencia.

============================================================
6. REGLAS PARA LOS DOS WORKFLOWS
============================================================

Mantener el alcance mínimo.

No añadir nuevos workflows.

No añadir nuevos servicios CI/CD.

No montar Jenkins, Railway hooks, SSH automation, cron u otros mecanismos.

No ampliar triggers sin nueva Spec/Owner Decision.

Mantener trazabilidad entre:

commit
→ workflow run
→ image tag/digest
→ runtime desplegado.

============================================================
7. T13
============================================================

Esta decisión NO cierra T13 por sí sola.

Continuar resolviendo los gates técnicos pendientes:

G-03 =
FAIL OBSERVADO actualmente
(12×401 sin 429)

G-02 =
PENDING / HOST

G-04 =
PENDING / HOST

G-05 =
PENDING / HOST

HOST_DEPLOYMENT_EVIDENCE =
PENDING

U1/U2 =
PREPARED — EN HOLD

============================================================
8. G-03
============================================================

Resolver G-03 antes del Owner UAT.

Si la causa es configuración:

- documentar valor actual;
- corregir únicamente configuración necesaria;
- recrear solo backend;
- NO tocar BD;
- NO hacer redeploy completo;
- repetir prueba;
- exigir evidencia ANTES/DESPUÉS.

Resultado requerido:

G-03 = PASS

Si requiere cambio de producto:

SPEC
→ AC
→ RED
→ IMPL
→ GREEN
→ sensibilidad
→ regresión
→ evidencia
→ commit
→ push
→ remote verify.

============================================================
9. G-02 / G-04 / G-05
============================================================

Completar con evidencia real del host conforme al runbook.

No sustituirlos por rehearsal local.

Objetivo:

G-02 = PASS
G-03 = PASS
G-04 = PASS
G-05 = PASS

HOST_DEPLOYMENT_EVIDENCE = COMPLETE

============================================================
10. UAT
============================================================

NO abrir U1/U2 todavía.

Solo cuando:

AOD29_DEPLOYMENT_GOVERNANCE = RECONCILED
G-02 = PASS
G-03 = PASS
G-04 = PASS
G-05 = PASS
HOST_DEPLOYMENT_EVIDENCE = COMPLETE

entonces:

re-prevalidar U1/U2
→ U1 = READY_FOR_OWNER
→ U2 = READY_FOR_OWNER
→ STOP OWNER UAT.

No marcar PASS por el Owner.

============================================================
11. GIT
============================================================

Stage explícito.

NO:

git add .
git add -A
force push
reset
history rewrite

Commit de la formalización.

Push origin/main.

Verificar:

LOCAL_SHA == REMOTE_SHA

Registrar:

REMOTE_SHA_MATCH = PASS

============================================================
12. CONTINUIDAD
============================================================

Después de formalizar esta decisión:

continúa automáticamente con:

formalización B
→ cierre GOVERNANCE_DRIFT
→ resolución G-03
→ G-02/G-04/G-05
→ evidencia host
→ re-prevalidación U1/U2

y DETENTE únicamente cuando:

U1 = READY_FOR_OWNER
U2 = READY_FOR_OWNER

o aparezca un OWNER_GATE_REAL distinto.

No pedir micro-confirmaciones.

EJECUTA AHORA.
```
