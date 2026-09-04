# GA-REM-004 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-004` — Credenciales y cuentas de prueba · **Wave** 1 · 2026-09-03 |
| **Estado final** | **`CERTIFIED` (alcance de Wave 1)** — con acciones operativas pendientes fuera del repositorio |

> Este informe **no transcribe ningún secreto**. Se refiere a ellos por ubicación.

## Finding
**P0-8 / S-04** — 15 pares usuario/contraseña publicados en `GUIA_PRUEBAS_EN_VIVO.md`, incluida una cuenta de Super Administrador, más contraseñas literales en dos módulos de seeds, contra un entorno accesible públicamente y con el limitador de intentos de login **desactivado por omisión** en producción.

## Implementation

| Archivo | Cambio |
|---|---|
| `backend/seeds/dev_seeds.py` | Helper `_seed_password(username)` que lee `GA_SEED_PWD_<USUARIO>` o `GA_SEED_DEFAULT_PASSWORD`. **Aborta** si falta, en lugar de crear usuarios con credenciales conocidas. 10 literales eliminados. |
| `backend/seeds/integration_seeds.py` | Mismo helper. 15 literales eliminados. El resumen que imprimía la contraseña en claro ahora muestra `<oculta>`. |
| `GUIA_PRUEBAS_EN_VIVO.md` | Las dos tablas de credenciales sustituidas por *(ver almacén de credenciales)* + nota explicativa. |
| `docker-compose.yml` | `FEATURE_RATE_LIMIT_ENABLED: ${FEATURE_RATE_LIMIT_ENABLED:-true}` — el limitador queda **activo por defecto en producción**. |

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | Sin credenciales funcionales en el repositorio | ✅ `grep -cE '\| \`(movil\|web)\.[a-z]+\` \| \`[a-z0-9]+\` \|'` → **0** pares en la documentación |
| AC02 | Contraseñas de seeds fuera del código | ✅ `grep -rnE '"password":\s*"[^"]' seeds/*.py` → **0 literales** |
| AC03 | Rate limiting activo en producción | ✅ variable inyectada con defecto `true`; ⚠ la verificación de los 6 intentos → 429 requiere entorno desplegado (`BLOCKED_EXTERNAL`) |
| AC04 | El deployment NO ha sido modificado | ✅ 0 archivos de `.github/workflows/docker-*.yml`; `watchtower`, `pull_policy: always` y `:latest` intactos (12 referencias) |
| AC05 | Inventario documentado sin transcribir secretos | ✅ ver §inventario; ningún secreto reproducido |
| AC06 | Separación de entornos | ✅ `test_seeds.py` usa identidades propias (`test_admin`, `test_operator`, `test_approver`) con contraseñas efímeras generadas por ejecución, distintas de las de demostración |
| AC07 | Acceso a BD con privilegios mínimos y SSL | ⚠ **`DEFERRED`** — acción de infraestructura fuera del repositorio |

## Inventario de credenciales (sin transcribir)

| Ubicación | Naturaleza | Clasificación | Acción |
|---|---|---|---|
| `GUIA_PRUEBAS_EN_VIVO.md` §1.1 | 15 pares de cuentas de prueba | **potencialmente válidas en producción** | **retiradas del repositorio**; rotación pendiente en el entorno |
| `backend/seeds/dev_seeds.py` | 10 contraseñas de desarrollo | seeds | **eliminadas del código** |
| `backend/seeds/integration_seeds.py` | 15 contraseñas de integración | seeds | **eliminadas del código** |
| `backend/.env`, `.env` raíz | credenciales de BD y SMTP reales | reales, **no versionadas** (verificado: `git log --all -- '*.env'` vacío) | rotación operativa pendiente |

## Acciones operativas pendientes (fuera del repositorio)

Estas **no** pueden ejecutarse desde el código y quedan como responsabilidad de operaciones:

1. **Rotar** las contraseñas de las cuentas que existan en el entorno desplegado, empezando por la cuenta de administración.
2. Verificar en el entorno que 6 intentos de login en un minuto devuelven **429** (AC03).
3. Rotar las credenciales de base de datos y SMTP presentes en los `.env` locales.
4. Sustituir el rol superusuario de base de datos por un rol de aplicación con privilegios mínimos y exigir SSL (AC07, `DEFERRED`).
5. Entregar las credenciales de prueba por el canal seguro acordado.

## Regression
`compileall` OK · sintaxis de ambos módulos de seeds validada · 176 operaciones OpenAPI · 0 deriva de esquema · `tsc` y `vitest` en verde.

## Final status
**`CERTIFIED`** en el alcance que el repositorio controla. Las cinco acciones operativas quedan registradas y son verificables externamente.
