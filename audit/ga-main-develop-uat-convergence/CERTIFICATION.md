# CERTIFICACIÓN LOCAL — GA-MAIN-DEVELOP-UAT-EXACT-CONVERGENCE

Spec: `specs/017-main-develop-uat-convergence/spec.md` · Baseline `main` = `0363200`, `develop` = `424dda0`.
Sin migración (head `g2b3c4d5e6f7`). El árbol de **código** certificado es el de `152a8aa`; el commit de certificación solo añade esta carpeta de auditoría.

## 1. Topología Git
Antes: ver `evidence/01_git_topology_before.txt` (ni main→develop ni develop→main eran fast-forward).
Camino sin reescribir historia: merge de `develop` en `main` (`fa427c8`, develop pasa a ser ancestro), fix de O-10 y contrato de imágenes en `main`,
y **fast-forward de `develop` al SHA certificado de `main`** (sin merge adicional en develop).

## 2. O-10 — CERRADA
| | |
|---|---|
| Script (7610ece) | idempotente por diseño: una repetición con el `admin` canónico no valida contraseña ni crea usuario; reconcilia solo permisos comodín faltantes. |
| Test T-043-02 | segunda ejecución ⇒ `created=False`, mismo `user_id`/`role_id`, contraseña no rota. |
| Fallo observado | `BootstrapError: El correo reservado … ya pertenece a otro usuario` en la segunda ejecución. |
| Clasificación | **PRODUCT_DEFECT** (el test es correcto y coincide con GA-REM-043 AC04). |
| Causa raíz | el rechazo por correo no excluía al propio `admin` canónico (`existing_email` == `existing_username`). |
| Fix (`a472c54`) | rechazar solo si el correo es de OTRA cuenta (`existing_username is None or existing_email.id != existing_username.id`). Mismo mensaje; nada más cambia. |
| Tests | T-043-02 + T-043-07..12 (`a472c54`) y T-043-13 (`152a8aa`). 19 pasan en la corrida dirigida (`evidence/10`, `15`). |
| Revisión de seguridad §5 | solo crea si `admin` no existe; no promueve ni toca usuarios existentes (T-043-08); rehúsa correo ajeno (T-043-09), rol no global (T-043-10), admin inactivo (T-043-12), admin con empresa (T-043-13); sin contraseña literal ni impresión de secretos (T-043-04/05); falla seguro y no deja residuos (T-043-11); repetición sin escrituras (T-043-07). |
| Sensibilidad | M1–M7 + C1–C2 + W1–W4: ver `evidence/13_mutation_campaign.md`, `14_workflow_mutants.log`, `15_m7_closure.log`. 13 mutantes: 12 detectados a la primera; M7 sobrevivió y se cerró con T-043-13 (detectado después). |
| Nota | en la corrida backend **completa** los tests con fixture `pristine_superadmin` (T-043-01..03 y 07..13) se omiten por diseño (la base sembrada ya tiene Super Administrador): 52 → 59 omitidos. Se ejecutan en la corrida dirigida. |

Observación **O-12 (sin tocar)**: `create-pr.sh` (7610ece) pasó de un script con verificaciones y confirmación explícita a otro que crea y **fusiona automáticamente** `develop→main` sin pedir confirmación ni comprobar checks. No interviene en producto/CI. Riesgo de gobernanza: decisión de la Owner (restaurar el anterior o retirarlo).

## 3. Contrato de imágenes (hallazgo de infraestructura)
Evidencia: `evidence/02_registry_tags_before.txt`.
| Componente | Workflow tag (antes) | Compose repo (antes) | Registro | Runtime |
|---|---|---|---|---|
| backend | `dev` + `sha-<7>` (develop) / `latest` + `sha` (main) | `:develop` | existen `latest`, `dev`, `sha-*`; **no existe `develop`** | declara `424dda0` = digest de `dev` (= `sha-424dda0`), no el de `latest` (`39d8238`) |
| frontend | ídem | `:develop` | ídem | ídem |
Conclusión: UAT consume **`:dev`**; el compose del repo pedía un tag inexistente. Digest del contenedor en ejecución y tag vigilado por Watchtower: **NOT_ACCESSIBLE** desde fuera del servidor (el compose de UAT y Watchtower no están en el repo).
Normalización: `main → latest(+sha)`, `develop → dev(+sha)`; `docker-compose.develop.yml` → `:dev`; los 4 workflows **sin filtro `paths`** (todo push construye ⇒ el SHA de la rama es el del runtime); contrato en `docs/DEPLOYMENT_CONTRACT.md`; tests AC-C-01..04.

## 4. Regresión (HEAD de código = `152a8aa`)
| Gate | Resultado | Evidencia |
|---|---|---|
| Backend completo | **1906 passed, 0 failed, 59 skipped** (24:57) | `evidence/20_backend_full.log` |
| Regresión de autoridad dirigida (r199, escalada, rbac, matriz, tenancy, sesión, administración de accesos/roles, autoridad dinámica, bootstrap) | 128 passed | `evidence/12_authority_regression.log` |
| Bootstrap dirigido con T-043-13 | 19 passed | `evidence/15_m7_closure.log` |
| Frontend completo | **734 passed, 1 skipped** (123 archivos) | `evidence/21_frontend_full.log` |
| TSC | PASS | `evidence/22_tsc.log` |
| Build (con SHA inyectado) | PASS | `evidence/23_build.log` |
| E2E completa `--workers=1` | **207 passed, 0 failed, 0 skipped** (12,2 min) — incluye P18, P19 y O3-E2E-01..08 | `evidence/24_e2e_full.log` |
| O-3 | CLOSED: derivación, pendiente, clasificación, motivo y auditoría verdes (O3-E2E-01..08 y `test_o3_classification.py` en la corrida completa) | ídem |

## 5. O-11
Ver `O11_TRIAGE.md`: **P2 provisional · OWNER_DECISION_REQUIRED** (no consta el máximo operativo de granjas; QA tiene 5; solo la base de E2E superó 100).

## 6. Pendiente tras este commit
Push de `main`, fast-forward de `develop` y verificación del runtime. Esa evidencia posdespliegue **no se versiona**: commitearla movería el SHA que se acaba de certificar.
