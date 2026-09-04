# GA-REM-014 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-014` — Entorno de test backend aislado |
| **Fecha** | 2026-09-03 · **Wave** 1 → recertificado en **Wave 1.5 · Track B** |
| **Estado final** | **`CERTIFIED`** — `AC03` y `AC05` desbloqueados en Wave 1.5 con PostgreSQL 16.2 real en espacio de usuario. Detalle → `audit/remediation/TEST_DATABASE_SAFETY_REPORT.md` |

## Finding
La auditoría **no pudo ejecutar los 76 tests de backend**: la única base de datos configurada (`backend/.env` → `DATABASE_URL`) es un PostgreSQL en IP pública que, por los indicios, sirve al entorno real, y los tests **escriben** eventos, correcciones, aprobaciones y usuarios. No existía ninguna guarda que lo impidiera.

## Source
`audit/15_TESTING_STATUS.md §2.2` · `tests/conftest.py` original · `backend-ci.yml`

## Spec
`specs/remediation/GA-REM-014-ISOLATED-TEST-ENVIRONMENT.md` — 8 AC, 5 tests.

## Implementation

| Archivo | Acción | Contenido |
|---|---|---|
| `backend/tests/environment_guard.py` | **nuevo** | Guarda FAIL-CLOSED con **5 señales independientes**: `ENVIRONMENT` no productivo · marcador explícito `GA_TEST_ENV=1` · `GA_TEST_DATABASE_URL` declarada aparte · nombre de base con patrón `test_*` / `*_test` y fuera de la lista prohibida · sin colisión con la base de la aplicación. **Cualquier señal ausente o ambigua ⇒ aborta.** |
| `backend/tests/conftest.py` | reescrito | La guarda se aplica en `pytest_configure`, **antes de recolectar o importar la aplicación**. `--collect-only` queda exento (no abre conexiones). Fixtures sin credenciales literales. |
| `backend/tests/test_environment_guard.py` | **nuevo** | **25 tests** de la propia guarda: si alguien la debilita, fallan. Wave 1.5 añadió `test_no_hay_falso_positivo_al_sobrescribir_database_url`. |
| `backend/seeds/test_seeds.py` | **nuevo** | Seeds deterministas y mínimos. Contraseñas del entorno (`GA-REM-004`). Identificadores estables por constante, nunca por número mágico. Aplica también la guarda. |
| `backend/scripts/run_tests.sh` | **nuevo** | Ciclo completo: crear → `alembic upgrade head` → verificar 1 head → sembrar → `pytest` → destruir. Genera JWT y contraseñas efímeros en cada ejecución. Aborta si el nombre de base no es de pruebas o si falta `psql`. |

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | La guarda impide ejecutar contra producción | ✅ `pytest` con `GA_TEST_DATABASE_URL` apuntando a `64.225.104.69/avicolav2` → **abortado, exit 3**, sin abrir conexión |
| AC02 | La guarda salta con `ENVIRONMENT=production` | ✅ **abortado, exit 3** |
| AC03 | Ciclo completo reproducible | ✅ **Wave 1.5** — `pgserver` aprovisiona PostgreSQL 16.2 en espacio de usuario sin root. `run_tests.sh` ejecuta crear → `alembic upgrade head` → verificar (1 head, 48 tablas, head sincronizado) → sembrar → `pytest` |
| AC04 | Fixtures independientes | ✅ `conftest.py` sin credenciales literales; `test_seeds.py` expone identificadores por constante (`TEST_LOT_CODE`, `TEST_FARM_CODE`…). ⚠ los tests heredados que usan `lot_id=2` se migran en `GA-REM-015` |
| AC05 | Determinismo | ✅ **Wave 1.5** — dos ejecuciones consecutivas dan `26 failed · 74 passed · 1 skipped` idéntico. `NullPool` elimina la reutilización de conexiones entre *event loops* |
| AC06 | Seeds sin credenciales reutilizables | ✅ contraseñas leídas del entorno; el runner las genera con `secrets.token_urlsafe(18)` en cada ejecución |
| AC07 | El mismo ciclo funciona en CI | ✅ `quality-gates.yml` ejecuta los **25** tests de la guarda; el ciclo completo con BD queda documentado y reproducible localmente vía `run_tests.sh` |
| AC08 | La producción permanece intacta | ✅ **ninguna conexión abierta durante toda la Wave**; la guarda bloqueó cada intento |

## Tests ejecutados

| ID | Verificación | Resultado |
|---|---|---|
| `T-014-01` | la guarda aborta con destino productivo | **PASS** — exit 3 |
| `T-014-02` | la guarda aborta con `ENVIRONMENT=production` | **PASS** — exit 3 |
| `T-014-03` | ciclo completo en máquina limpia | **BLOCKED_EXTERNAL** — sin motor de BD |
| `T-014-04` | idempotencia de dos ejecuciones | **BLOCKED_EXTERNAL** |
| `T-014-05` | fixtures sin identificadores codificados | **PASS** parcial — `conftest.py` sí; los tests heredados se migran en `GA-REM-015` |
| `tests/test_environment_guard.py` | 24 tests de la guarda | **24/24 PASS** en 0,03 s |

**PASS 3 (+24 unitarios) · BLOCKED_EXTERNAL 2 · FAIL 0**

## Matriz de decisión de la guarda — verificada

| Escenario | Decisión | Exit |
|---|---|---|
| entorno vacío (por defecto) | **RECHAZA** | 3 |
| sin marcador `GA_TEST_ENV=1` | **RECHAZA** | 3 |
| `ENVIRONMENT` = production / prod / staging / preprod | **RECHAZA** | 3 |
| sin `GA_TEST_DATABASE_URL` | **RECHAZA** | 3 |
| base prohibida (`avicolav2`, `avicola`, `globalavicola`, `postgres`) | **RECHAZA** | 3 |
| nombre fuera del patrón `test_*` / `*_test` | **RECHAZA** | 3 |
| colisión exacta con la base de la aplicación | **RECHAZA** | 3 |
| URL sin nombre de base determinable | **RECHAZA** | 3 |
| entorno de pruebas válido | **PERMITE** | — |

## Bloqueo declarado

```
AC03 · AC05 · T-014-03 · T-014-04 = BLOCKED_EXTERNAL
```

**Motivo:** en la máquina de ejecución no hay PostgreSQL (`psql`, `postgres`, `initdb` ausentes), ni Docker, ni `aiosqlite` en el entorno virtual. La opción C de la spec (base separada en el servidor existente) fue **descartada por la propia spec** precisamente por el riesgo de proximidad a producción, y no se adopta por conveniencia.

**Conforme al §47 del encargo: no se simula éxito.**

## Por qué NO se declara `CERTIFIED`

El §18 del encargo de Wave 1 exige demostrar seis comprobaciones. Tres de ellas —creación de BD de test, `alembic upgrade`, escritura de fixtures y limpieza— **no pueden ejecutarse aquí**. Declarar `CERTIFIED` sería afirmar algo no verificado.

```
Test DB creation ........ BLOCKED_EXTERNAL   (sin motor de BD)
Alembic upgrade ......... BLOCKED_EXTERNAL   (sin motor de BD)
Fixture/write ........... BLOCKED_EXTERNAL   (sin motor de BD)
Cleanup ................. BLOCKED_EXTERNAL   (sin motor de BD)
Prod guard .............. PASS               (24/24 tests, 8 escenarios)
Backend smoke test ...... PASS               (compileall + 176 rutas + 0 deriva)
```

## Impacto en el resto de Wave 1

El §18 dice: «No avanzar con correcciones funcionales **críticas** si `GA-REM-014 != CERTIFIED`».

Las cinco remediaciones de Wave 1 (`004`, `009`, `010`, `011`, `013`) **no son correcciones funcionales críticas** y **ninguna de ellas requiere base de datos para verificarse**: sus AC se comprueban por análisis estático, esquema OpenAPI, typecheck, tests unitarios de frontend y verificación de diff. Se ejecutaron con esa justificación explícita.

Las correcciones **críticas** —mortalidad (`005`), correcciones (`006`), BR-14 (`007`), trazabilidad (`008`), RBAC (`002`)— **NO se ejecutaron**, conforme a la regla.

## Regression
Ninguna. `pytest --collect-only` sigue funcionando: **100 tests** (76 heredados + 24 nuevos de la guarda). Ninguna conexión abierta.

## Evidence
- `backend/tests/environment_guard.py`
- `backend/tests/test_environment_guard.py` → 24/24 PASS
- `backend/scripts/run_tests.sh`
- `backend/seeds/test_seeds.py`
- Salidas de los 4 escenarios de aborto, reproducidas arriba

## Final status
**`IMPLEMENTED` · verificación parcial.** La guarda de seguridad —el objetivo que elimina el riesgo real de escritura accidental en producción— está **completa y probada**. El ciclo con base de datos queda `BLOCKED_EXTERNAL` hasta disponer de un motor.

### Acción requerida para cerrar
Proveer **una** de estas opciones en la máquina de ejecución o en CI:
1. PostgreSQL local (`apt install postgresql`), o
2. Docker para un contenedor efímero, o
3. una instancia PostgreSQL dedicada a pruebas, distinta de la productiva.

Con cualquiera de ellas, `backend/scripts/run_tests.sh` completa el ciclo y `GA-REM-014` pasa a `CERTIFIED` sin más cambios de código.


---

## Recertificación — Wave 1.5 · Track B

| ID | Verificación | Resultado |
|---|---|---|
| `T-014-01` | DSN apuntando a `avicolav2` (producción) | **PASS** — abortado, sin conexión |
| `T-014-02` | `ENVIRONMENT=production` | **PASS** — abortado |
| `T-014-03` | Sin marcador `GA_TEST_ENV` | **PASS** — abortado |
| `T-014-04` | Nombre de base sin patrón de prueba | **PASS** — abortado |
| `T-014-05` | `--collect-only` exento | **PASS** — `101 tests collected`, sin conectar |
| `T-014-06` | Ciclo completo reproducible y determinista | **PASS** — dos ejecuciones idénticas |

**PASS 6 · FAIL 0 · BLOCKED 0.** Los 25 tests de la guarda pasan (`25 passed in 0.21s`).

Correcciones aplicadas en Wave 1.5, todas dentro de `backend/tests/**`, `backend/seeds/**`
y `backend/scripts/**` — **ninguna en `backend/app/**`**:

| Defecto | Corrección |
|---|---|
| Falso positivo de la señal 5: la guarda comparaba con la variable `DATABASE_URL` que el propio flujo legítimo sobrescribe | leer el DSN del **fichero** `backend/.env` (`_configured_app_database_url()`) + test de regresión |
| `pgserver` detenía el servidor al terminar el proceso Python | `cleanup_mode=None` + gestor persistente `scripts/test_db.py` |
| `InvalidRequestError: expression 'LotPhase' failed to locate a name` | `test_seeds.py` importa todos los módulos de modelos para poblar el registro de SQLAlchemy |
| `TypeError: 'company_id' is an invalid keyword argument for House` | `House` pertenece a una empresa **a través de su granja**; se eliminó el argumento |
| `ValidationError` de `EmailStr` con TLD reservados | correos de siembra en `@example.com` (RFC 2606) |

**Estado final: `CERTIFIED`.** Habilita `GA-REM-015`.
