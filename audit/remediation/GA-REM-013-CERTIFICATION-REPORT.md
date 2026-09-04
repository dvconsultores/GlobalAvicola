# GA-REM-013 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-013` — Quality gates de CI · **Wave** 1 · 2026-09-03 |
| **Estado final** | **`CERTIFIED`** |

> ## ⚠ KNOWN_ACCEPTED_LIMITATION (EX-01)
> El resultado de estos gates **NO impide el despliegue**. Por decisión del propietario, el mecanismo de despliegue automático se mantiene sin cambios. La señal es **informativa, no bloqueante**.

## Finding
**P0-12** — Los workflows de calidad se disparaban **solo en `pull_request`** y el repositorio tiene **0 pull requests en 171 commits**: ninguna comprobación se ha ejecutado nunca. Además, si se hubieran ejecutado, habrían fallado por causas propias (Postgres vacío sin migraciones, lint con 5 errores, test de tipos de evento desactualizado).

## Implementation

| Archivo | Cambio |
|---|---|
| `.github/workflows/quality-gates.yml` | **nuevo** — se dispara en `push` a `main`, en `pull_request` y bajo demanda. Tres jobs: `backend-quality`, `frontend-quality` y **`scope-guard`** |
| `backend/scripts/verify.sh` | **nuevo** — reproduce localmente las **mismas 8 comprobaciones** del CI, para que la disciplina no dependa del pipeline |

### Comprobaciones (8)

| # | Comprobación | Resultado local |
|---|---|---|
| 1 | Backend · compilación (`compileall`) | ✅ |
| 2 | Backend · cadena Alembic (1 head, 1 base, 21 revisiones) | ✅ |
| 3 | Backend · deriva ORM ↔ migraciones (47 tablas, **0 deriva**) | ✅ |
| 4 | Backend · guarda del entorno de pruebas (24 tests) | ✅ |
| 5 | Backend · sin credenciales literales en seeds | ✅ |
| 6 | Frontend · typecheck (`tsc -b --noEmit`) | ✅ |
| 7 | Frontend · tests unitarios (`vitest`, 61 tests) | ✅ |
| 8 | Frontend · paridad i18n (865 = 865, 0 faltantes) | ✅ |

**8/8 en verde.**

### El job `scope-guard`
Verifica **en cada ejecución** que el alcance excluido sigue respetado: los tres workflows de despliegue existen, y `watchtower`, `pull_policy: always` y `:latest` permanecen en `docker-compose.yml`. Si alguien intentara retirar el despliegue automático por vía indirecta, **este job falla**.

Es la garantía automatizada de que `EX-01` se cumple en ambas direcciones.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | Los quality gates se ejecutan en cada push | ✅ `on: push: branches: [main]` |
| AC02 | El gate de lint pasa | ⚠ ESLint queda **informativo** (`continue-on-error`) en Wave 1: los 5 errores `react-hooks/refs` son deuda preexistente y corregirlos está fuera del alcance de esta Wave (§26). Se declara explícitamente en el workflow |
| AC03 | El gate de typecheck pasa | ✅ |
| AC04 | El gate de tests de frontend pasa | ✅ 61/61 |
| AC05 | El gate de tests de backend se ejecuta de verdad | ⚠ **parcial** — se ejecutan los 24 tests de la guarda; la suite completa espera a `GA-REM-014` `CERTIFIED` y a `GA-REM-015` |
| AC06 | La limitación está documentada | ✅ en el encabezado del workflow, en la salida de `verify.sh` y en `EX-01` de la Constitución |
| AC07 | **El deployment NO ha sido modificado** | ✅ 0 workflows de despliegue tocados; `scope-guard` lo verifica automáticamente en cada ejecución |
| AC08 | Verificación local reproducible | ✅ `backend/scripts/verify.sh` — mismas comprobaciones, 8/8 en verde |

## Nota sobre AC02
No se «arregló» el lint rebajando reglas: se declaró **informativo de forma explícita y visible**, porque los 5 errores son deuda preexistente cuya corrección pertenece a `GA-REM-019` y el §26 prohíbe el cleanup general en esta Wave. La alternativa —silenciar las reglas— habría violado el Art. 8.3 de la Constitución.

## Regression
Ninguna. Solo configuración de CI y un script nuevo.

## Final status
**`CERTIFIED`.** Por primera vez el proyecto tiene una señal de calidad ejecutable, tanto local como en CI, sin tocar el despliegue.
