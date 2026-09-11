# GA-FE-02-A · AUTH PROVISIONING MAP (§3)

Investigación **completa** de mecanismos de provisioning dentro del repositorio y su
documentación canónica (baseline `fad6463`). Sin búsqueda de valores secretos; solo mecanismos.
Resultado global: **ningún mecanismo permite provisionar el runtime desplegado (ENV-01) desde
este entorno de ejecución sin una credencial bootstrap inyectada externamente.**

| MECHANISM | SOURCE FILE | PURPOSE | ENV | OFFICIAL? | REQUIRES EXISTING AUTH? | CREATES USER? | SETS PASSWORD? | ASSIGNS COMPANY? | ASSIGNS ROLE? | ASSIGNS PERMISSION? | SAFE FOR ENV-01? | USED? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 · UI administrativa `/users` | `frontend/src/pages/users/UsersPage.tsx` · `POST /api/v1/users` | alta/edición de usuarios por admin | runtime | SÍ | **SÍ** (`users:create`) | SÍ | SÍ (via API de admin) | SÍ | SÍ (`role_id`) | vía rol existente | SÍ (uso normal) | **NO — bloqueado por bootstrap** |
| M2 · API administrativa | `backend/app/auth/router.py` (`/users`, `/users/{id}/password`) | CRUD usuarios + password por admin | runtime | SÍ | **SÍ** | SÍ | SÍ | SÍ | SÍ | vía rol | SÍ | **NO — bloqueado por bootstrap** |
| M3 · Seeds de sistema (bootstrap admin) | `backend/seeds/baseline_seeds.py` (`sembrar_admin`, `_password_admin`) · `dev_seeds.py` (`_seed_password`) | crea el Super Administrador y roles base | server-side (deploy) | SÍ | **NO** | SÍ | SÍ — **password desde entorno** `GA_BASELINE_ADMIN_PASSWORD` / `GA_SEED_DEFAULT_PASSWORD` / `GA_SEED_PWD_<USER>`; ausente ⇒ aborta o genera aleatoria | SÍ (baseline) | SÍ | SÍ | solo en el servidor/DB local | **NO aplicable** (sin acceso server-side; variables AUSENTES en este entorno — 0) |
| M4 · CLI administrativa | `backend/scripts/environment_reset.py` · `first_flow_check.py` · `run_tests.sh` · `certify_baseline.sh` · `reset_guard.py` | reset/verificación de entorno; flujo inicial | local/servidor | SÍ | SÍ (flujo) o DB directa (reset) | indirecto | `GA_FLOW_PASSWORD` (ausente) | — | — | — | **NO desde aquí**: requieren `DATABASE_URL`/shell del servidor (ausentes — 0) y operarían sobre la DB compartida; prohibido por §2 | **NO** |
| M5 · Tooling oficial de fixtures/test | `backend/seeds/test_seeds.py` · `scenario_fixtures.py` · `scripts/test_db.py` · `run_tests.sh` | datos para la suite backend | **base de pruebas AISLADA local** (`GA-REM-014`: instancia PG propia) | SÍ | no | SÍ | sí (local) | sí (local) | sí (local) | sí (local) | SÍ para su propósito — **no puede tocar ENV-01** | **NO aplicable** (no alcanza el runtime desplegado) |
| M6 · Invitación/alta pública | — (`grep register|invite|signup|forgot` en `auth/router.py` = **0 resultados**) | auto-registro | — | **NO EXISTE** | — | — | — | — | — | — | — | **NO** |
| M7 · Credential store externo (canónico) | `GUIA_PRUEBAS_EN_VIVO.md §1.1` · `specs/remediation/GA-REM-004` (CERTIFIED) | entrega de credenciales "por el canal seguro acordado" | externo | SÍ (es LA vía diseñada) | — | — | — | — | — | — | SÍ | **NO — nada inyectado en este entorno** |

## Cadena de evidencia (§5) — por qué el bloqueo es de credencial bootstrap

```
A. Provisioning NO autenticado legítimo ......... NO EXISTE
   · auth/router.py sin register/invite/signup/forgot (0 coincidencias)
   · POST /users exige users:create autenticado (matriz de contrato B-cadena)

B. CLI bootstrap usable desde aquí .............. NO EXISTE
   · M3/M4 requieren entorno del servidor (DATABASE_URL=0) o credenciales inyectadas
     (GA_BASELINE_ADMIN_PASSWORD=0 · GA_FLOW_PASSWORD=0 · GA_SEED_*=0)
   · §2 prohíbe DB directa; sin shell del servidor; los scripts hablan con DB local/servidor

C. Fixture/test tooling oficial sobre ENV-01 .... NO EXISTE
   · M5 opera contra la base de pruebas AISLADA de GA-REM-014, nunca contra el desplegado

D. First-admin mechanism usable en ENV-01 ....... NO EXISTE (desde aquí)
   · el primer admin se sembró server-side en el despliegue con password inyectada
   · GA-REM-004 (CERTIFIED): "Ninguna credencial funcional reside en el repositorio";
     la entrega es por el canal seguro acordado (M7) — nada fue inyectado (0 variables)

E. Sesión autenticada explícitamente disponible ... NINGUNA
   · el navegador compartido está en /login; no se compartió ninguna página autenticada

F. Credenciales buscadas/adivinadas/bypass ....... NO / NO / NO
   · única comprobación: PRESENCIA (conteo) de las variables documentadas → todas 0
```

**Conclusión**: `BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED` — el mecanismo oficial **existe**
(M3/M7: inyección externa de la credencial bootstrap por el canal seguro), pero la credencial
**no está presente** en este entorno (§5). Remediación exacta: inyectar UNA credencial bootstrap
por la vía canónica (p. ej. exportar `GA_FLOW_PASSWORD` con la cuenta `admin` de ENV-01, o
`GA_BASELINE_ADMIN_PASSWORD` si corresponde al operador, o compartir una sesión autenticada de
ENV-01) — con ella, TODO el resto del plan es auto-ejecutable por este agente (provisionar A–D
por M1/M2 y correr los 31 escenarios).
