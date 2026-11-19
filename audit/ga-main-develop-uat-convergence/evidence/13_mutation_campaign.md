# 13 · Campaña de sensibilidad (mutación) — bootstrap del primer superusuario + contrato de imágenes

**Repositorio:** `/home/maria/Proyectos/GlobalAvicola`
**Commit de implementación bajo análisis:** `acda6f8` (HEAD de `main`; contiene `a472c54` — fix O10 del bootstrap
GA-REM-043 y los tests T-043-07..12, y el contrato único de imágenes SPEC 017).
**Objetivo:** demostrar que la suite dirigida *mata* los mutantes del fix de bootstrap y del contrato de compose/docs,
y detectar huecos reales de cobertura (supervivientes) sin inventar pruebas.

## Método

1. Árbol de trabajo verificado idéntico a `acda6f8` (`git status --short` vacío) antes de empezar.
2. Cada mutante se aplicó **de uno en uno** (nunca en paralelo) sobre el fichero fuente.
3. Se ejecutó **solo** el test dirigido del área mutada.
4. Restauración con el comando exacto `git restore --source=acda6f8 -- <archivo>` desde la raíz del repo,
   comprobando después que `git diff --stat -- <archivo>` queda vacío.
5. Criterio: **DETECTADO** si al menos un test falla; **SUPERVIVIENTE** si la suite queda verde.
6. Sin `git add/commit/push`, sin ramas, sin `stash/reset/checkout`, sin tocar `.github/workflows`.

Comandos usados:

```bash
# backend (rutas relativas a backend/)
./scripts/run_tests.sh tests/test_first_superuser_bootstrap.py -q
# frontend (contrato)
PATH=$HOME/.nvm/versions/node/v24.13.0/bin:$PATH npx vitest run src/__tests__/spec016.buildProvenance.test.ts
```

**Línea base (sin mutar):** backend `18 passed`; vitest de contrato `21 passed | 1 skipped (22)`.

## Resultados — mutantes de backend (`backend/scripts/bootstrap_first_superuser.py`)

| # | Mutación aplicada | Tests que fallan | Veredicto |
|---|---|---|---|
| **M1** | Rechazo por correo revertido a `if existing_email is not None:` (sin la cláusula que compara con `existing_username`) | `test_t_043_02_second_run_is_idempotent_and_does_not_rotate_password`, `test_t_043_07_repeated_runs_over_canonical_admin_write_nothing` | **DETECTADO** (2 failed / 16 passed) |
| **M2** | Eliminado por completo el bloque `if existing_email is not None and (...): raise BootstrapError(...)` (correo de un tercero) | `test_t_043_09_refuses_reserved_email_owned_by_another_user` | **DETECTADO** (1 failed / 17 passed) |
| **M3** | Comprobación de compatibilidad del admin existente sin `and existing_role.name == ROLE_NAME` | `test_t_043_10_refuses_admin_with_non_global_role` | **DETECTADO** (1 failed / 17 passed) |
| **M4** | Comprobación de compatibilidad sin `and existing_username.is_active` | `test_t_043_12_never_degrades_an_inactive_canonical_admin` | **DETECTADO** (1 failed / 17 passed) |
| **M5** | Camino de creación sin `password = validate_password(password)` | `test_t_043_11_weak_password_fails_safely_and_leaves_no_records` | **DETECTADO** (1 failed / 17 passed) |
| **M6** | `return BootstrapResult(created=True, ...)` fijo en el retorno final | `test_t_043_02_second_run_is_idempotent_and_does_not_rotate_password`, `test_t_043_07_repeated_runs_over_canonical_admin_write_nothing` | **DETECTADO** (2 failed / 16 passed) |
| **M7** | Compatibilidad del admin existente: `existing_username.company_id is None` sustituido por `True` | — (ninguno) | **SUPERVIVIENTE** (18 passed) |

## Resultados — mutantes de contrato

| # | Mutación aplicada | Test que falla | Veredicto |
|---|---|---|---|
| **C1** | `docker-compose.develop.yml`: `globalavicola-frontend:dev` → `globalavicola-frontend:develop` | `AC-C-03 · docker-compose.develop.yml pide ':dev' en las tres imágenes` | **DETECTADO** (1 failed / 20 passed / 1 skipped) |
| **C2** | `docs/DEPLOYMENT_CONTRACT.md`: eliminada la mención `verify_runtime_sha.sh` (única ocurrencia, línea 45) | `AC-C-04 · docs/DEPLOYMENT_CONTRACT.md declara el contrato completo` | **DETECTADO** (1 failed / 20 passed / 1 skipped) |

Los mutantes de `.github/workflows` (AC-C-01/AC-C-02) quedan fuera de este alcance por instrucción explícita:
los ejecuta el orquestador.

## Tasa de mutación

- Backend: **6/7 detectados** (85,7 %), 1 superviviente.
- Contrato: **2/2 detectados** (100 %).
- Global: **8/9 detectados** (88,9 %).

## Superviviente M7 — análisis (sin inventar pruebas)

`M7` sustituye `and existing_username.company_id is None` por `and True` en la comprobación de compatibilidad
del `admin` ya existente, es decir **desactiva la garantía de que el superusuario preexistente sea de ámbito
global** (sin empresa). La suite dirigida queda verde: ningún test construye un `admin` canónico con
`company_id` no nulo.

Hueco concreto de cobertura (T-043): no existe un caso análogo a `test_t_043_10` (rol no global) pero para
**cuenta de empresa**, p. ej. crear/usar `admin` con `email=ADMIN_EMAIL`, `username=admin`, rol
`Super Administrador` global pero `company_id=<empresa X>`, y exigir `BootstrapError`
(«configuración incompatible») sin sobrescribir la cuenta. La aserción existente
`admin.company_id is None` de `test_t_043_01` solo cubre el camino de **creación**, no el de **compatibilidad
de cuenta preexistente**, y por eso el mutante sobrevive.

Se reporta como hallazgo; **no se añadió ningún test** en esta campaña (restricción de la delegación).

## Estado final del árbol

- `git diff --stat` vacío → árbol de trabajo idéntico a `acda6f8`.
- `git status --short` → sin cambios de seguimiento; solo los ficheros de evidencia nuevos bajo
  `audit/ga-main-develop-uat-convergence/evidence/` (`12_authority_regression.log`,
  `13_mutation_campaign.md`, `13_mutation_raw.log`, `13_contract_vitest_after_restore.log`).

## Regresión de autoridad dirigida (post-restauración)

Comando (desde `backend/`):

```bash
./scripts/run_tests.sh tests/test_first_superuser_bootstrap.py \
  tests/test_r199_global_authority_fabrication.py tests/test_uat_admin_escalation.py \
  tests/test_rbac.py tests/test_uat_admin_rbac_matrix.py tests/test_role_tenancy.py \
  tests/test_session_payload.py tests/test_access_administration.py \
  tests/test_role_administration.py tests/test_uat_admin_dynamic_authority.py -q
```

Resultado real: **128 passed** en 142,08 s (`exit 0`). Salida completa en `12_authority_regression.log`.

Contrato tras restaurar (`npx vitest run src/__tests__/spec016.buildProvenance.test.ts`):
**21 passed | 1 skipped (22)**, `exit 0` (`13_contract_vitest_after_restore.log`).

## Evidencia cruda

`13_mutation_raw.log` contiene, para cada mutante: el parche aplicado, el comando, la salida completa de la
ejecución (incluidos los `assert` fallidos) y la confirmación de restauración.
