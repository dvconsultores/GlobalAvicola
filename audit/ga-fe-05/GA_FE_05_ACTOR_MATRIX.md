# GA-FE-05 · MATRIZ DE ACTORES

Mecanismos oficiales · credenciales efímeras fuera del repo · sin mutación de cuentas humanas · rol canónico 35 intacto.

| Alias | Usuario (fixture) | Rol (fixture) | Autoridad | Concesión BU | Uso en GA-FE-05 |
|---|---|---|---|---|---|
| `C` Operador productivo | `ga05-c` | **nuevo «GA-FE05 TEST OPERATOR»** (`dashboard:read` · `operations:read+create` · `lots:read`) | productivo con escritura | `broiler` (ventana) | E2E-01 (submit), E2E-06 (return), E2E-07 (resubmit), E2E-09/10 |
| `P` RBAC-negativo productivo | `ga05-p` | **nuevo «GA-FE05 TEST CORE ONLY»** (`dashboard:read`) | CORE | `broiler` (ventana) | E2E-04 (sin RBAC ⇒ sin CTA, API 403) |
| `Z` Cero unidades | `ga05-z` | GA-FE05 TEST OPERATOR **sin concesión** | productivo sin unidad | — | E2E-03 (sin User BU ⇒ sin CTA, API 403) |
| `D` Autenticado sin autoridad | `ga05-d` | GA-FE05 TEST CORE ONLY | CORE | — | Control negativo general |
| `E` Global | cuenta habitual del propietario (Super Admin) | comodín | global situado | no exigida | E2E-02 variante global (CBU OFF ⇒ 403), AC28 |
| `V` Revisor | `ga05-v` | **nuevo «GA-FE05 TEST REVIEWER»** (`dashboard:read` · `operations:read` · `review:read+review` · `approvals:approve`) | revisor | — | E2E-06: devolver (crear estado `returned` por flujo oficial), E2E-08 (aprobar para estado final) |

Notas:
- Los estados `returned`/`approved` de fixtures se producen **solo por flujo oficial** (submit → review return; submit → review complete → approve), nunca por SQL/DB.
- Ventana controlada: `broiler` ON en Empresa 1 durante la preparación de fixtures productivos; restauración a **4×OFF** al cierre.
- Usuarios/roles sintéticos: baja/desactivación al cierre; auditoría conservada.
