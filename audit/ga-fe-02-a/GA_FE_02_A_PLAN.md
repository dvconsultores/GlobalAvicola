# GA-FE-02-A · PLAN (28 fases)

Estado real de esta ejecución: fases 1–6 y 19–24 ejecutadas hasta donde es posible sin
autenticación; fases 7–18 y 20–23 **BLOCKED_AUTH**; 25–28 ejecutadas como cierre bloqueado.

| # | Fase | Contenido | Estado |
|---|---|---|---|
| 1 | Repo/runtime preflight | `main` · `d120fdd` == remoto · limpio · runtime = GA-FE-02 (`index-C_aR7TJ6.js`, hash `35ea38e2…`) | ✅ |
| 2 | Certification addendum | spec + clarify + plan + checklist + tasks en `audit/ga-fe-02-a/` | ✅ |
| 3 | Auth availability | 1.ª pasada: 0 credenciales → `MODE_C` · **resume 09-11: investigación de provisioning COMPLETA (mapa M1–M7)** → causa refinada `BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED` | ✅ |
| 4 | Test account matrix | `GA_FE_02_A_TEST_ACCOUNT_MATRIX.md` — todos `MISSING` (plan de creación congelado y auto-ejecutable con bootstrap) | ✅ (estado bloqueado) |
| 5 | Test Company state | no determinable sin actor; requisitos registrados | `BLOCKED_AUTH` |
| 6 | Pre-test snapshot | `GA_FE_02_A_PRETEST_STATE.md` — registro del estado no-autenticado | ✅ (bloqueado) |
| 7 | Company context | E2E-01 | `BLOCKED_AUTH` |
| 8 | Company switch | E2E-01b | `BLOCKED_AUTH` |
| 9 | Company BU enable | E2E-02 | `BLOCKED_AUTH` |
| 10 | Company BU disable | E2E-03 | `BLOCKED_AUTH` |
| 11 | Grant User BU | E2E-04 (+efecto) | `BLOCKED_AUTH` |
| 12 | Revoke User BU | E2E-05 | `BLOCKED_AUTH` |
| 13 | Self-grant negative | E2E-06 | `BLOCKED_AUTH` |
| 14 | Cross-company negative | E2E-07 | `BLOCKED_AUTH` |
| 15 | Unauthorized user | E2E-08 | `BLOCKED_AUTH` |
| 16 | BU ON + no grant | E2E-09 | `BLOCKED_AUTH` |
| 17 | Grant + BU OFF | E2E-10 | `BLOCKED_AUTH` |
| 18 | RBAC orthogonality | matriz 3D (4 casos) | `BLOCKED_AUTH` |
| 19 | Refresh/relogin | 5 puntos + objetivo ×2 | `BLOCKED_AUTH` |
| 20 | Mobile | 390×844 flujos críticos | `BLOCKED_AUTH` |
| 21 | Network evidence | artefacto de red | `BLOCKED_AUTH` (nada que capturar sin sesión) |
| 22 | Audit evidence | 4 mutaciones | `BLOCKED_AUTH` |
| 23 | State restoration | ledger vacío (no se creó dato) | ✅ trivially |
| 24 | Classification | `MODE_C · BLOCKED_AUTH` (§10) | ✅ |
| 25 | Certification | no emitible — `GA-FE-02` permanece `DEPLOYED_IMPLEMENTATION_COMPLETE_BLOCKED_AUTH` | ✅ (clasificado) |
| 26 | Owner UAT | `GA_FE_02_OWNER_UAT.md` existente; `UAT_READY = NO` (E2E no verde) | ✅ (estado) |
| 27 | Evidence | `GA_FE_02_A_AUTHENTICATED_RUNTIME_CERTIFICATION_EVIDENCE.md` (§117) | ✅ |
| 28 | STOP | commit de gobernanza + push + informe final | ✅ |

## Reglas de reanudación (cuando el propietario entregue cuentas)

```
1. Entrega de credenciales por mecanismo autorizado (no en el repo).
2. Verificar preflight + gates + runtime (fases 1–2).
3. Verificar login bootstrap + identidad + permisos (pasos 30–32 §133).
4. Ejecutar fases 5–23 en orden estricto §133 (50–160).
5. Solo entonces: fase 24–27 y certificación (§126).

## Reanudación 3 (autenticada — 2026-09-11, `ea26b2e`)

Fases 5–18: **`BLOCKED_FIXTURE_ENV01`** — el catálogo de unidades de negocio está vacío (F1) y el
rol «Administrador de Accesos» no existe (F2); sin ellos E2E-02…10 y la matriz 3D no son
ejecutables por ningún mecanismo oficial del cliente. Fase 19 (refresh): defecto **D1** detectado
y remediado (§7; verificado post-deploy). Re-ejecución completa pendiente tras resolver F1/F2.
Detalle y evidencia: `GA_FE_02_A_RESUME3_AUTHENTICATED_FINDINGS.md`.
```
