# RETIRED BY AOD-29 — NOT EXECUTED · HISTORICAL REFERENCE ONLY

Estos workflows **no son ejecutados por GitHub**. Fueron retirados del directorio
activo `.github/workflows/` por la decisión del propietario **AOD-29**
(GitHub Actions fuera del camino de certificación PRE-SAP) y su aclaratoria
**AOD-29 Clarification 01** (GitHub sigue activo como repositorio remoto y los
commits certificados se pushean a `origin/main`; lo retirado es GitHub Actions).

- `ACTIVE_WORKFLOW_COUNT = 0` · `AUTOMATIC_ACTION_TRIGGER_COUNT = 0`
- La certificación es **local** (`LOCAL_CERTIFICATION = REQUIRED`); el push a
  `origin/main` es **requerido** y **no debe disparar Actions**.
- Se conservan aquí como **referencia histórica** (qué corría y cómo), sin
  borrar historia.

> Consecuencia auditada: el auto-deploy compartido (Docker Hub `:latest` +
> Watchtower) dependía exclusivamente de estos workflows ⇒
> `AUTO_DEPLOY = NOT_AVAILABLE_WITH_GITHUB_ACTIONS_RETIRED (AOD29-DEPLOY-IMPACT)`.
> No se implementa mecanismo sustituto sin Spec/Owner Decision.

Registro canónico:
`audit/ga-pre-sap-program/GA_OWNER_DECISION_AOD29_CLARIFICATION_01_PUSH_PRESERVED.md`
