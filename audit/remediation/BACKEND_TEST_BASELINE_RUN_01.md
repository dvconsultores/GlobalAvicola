# BACKEND TEST BASELINE — RUN 01 (CONGELADO)

> **DOCUMENTO INMUTABLE.** Registra la **primera ejecución de la suite backend en toda la
> historia del proyecto**, sobre una base de datos real y aislada. No debe sobrescribirse
> ni «actualizarse» con ejecuciones posteriores. Las ejecuciones siguientes viven en
> `BACKEND_TEST_FAILURE_MATRIX.md`.

**Fecha** 2026-09-03 · **Wave** 1.5 · **Track** C · **GA-REM-015**

---

## 1. Por qué RUN 01 importa

Antes de esta ejecución la suite **nunca se había ejecutado**. Existían 101 tests escritos
a lo largo de junio de 2026 y ningún registro de que alguno hubiera corrido contra una
base de datos. La auditoría (Wave 0) se negó explícitamente a ejecutarlos porque la única
base disponible era la de producción en la nube.

RUN 01 es, por tanto, la primera medición real del estado del backend. Su valor no está en
los números —son malos— sino en que a partir de aquí **existe un punto de comparación**.

---

## 2. Resultado literal

```
29 passed, 6 failed, 66 errors
```

| Métrica | Valor |
|---|---|
| Tests recolectados | 101 |
| PASS | 29 (28,7 %) |
| FAIL | 6 |
| ERROR | 66 |
| SKIPPED | 0 |

---

## 3. Naturaleza de los 66 errores

Los 66 `ERROR` **no eran fallos funcionales**: eran `sqlalchemy.exc.InterfaceError` por
reutilización de conexiones `asyncpg` entre distintos *event loops* de `pytest-asyncio`.
La suite no llegaba a ejercitar la lógica de negocio; se rompía en el arranque de cada
test.

En otras palabras: **RUN 01 no midió el backend. Midió la infraestructura de pruebas.**

---

## 4. Entorno de RUN 01

| Elemento | Valor |
|---|---|
| PostgreSQL | 16.2 (`pgserver` en espacio de usuario, sin privilegios de root) |
| `PGDATA` | `~/.local/share/global_avicola_test_pg` |
| Base | `global_avicola_test` · rol `global_avicola_test_user` |
| Cadena Alembic | 21 migraciones, 1 *head* (`i9j0k1l2m3n4`) |
| Tablas | 48 (47 + `alembic_version`) |
| Guarda de entorno | `GA-REM-014` activa — 5 señales, fail-closed |
| Producción | **no tocada** en ningún momento |

---

## 5. Cadena de saneamiento posterior a RUN 01

Las ejecuciones intermedias se documentan aquí porque explican cómo se pasó de 29 a 74
PASS **sin modificar una sola línea de lógica de negocio**:

| Run | Cambio aplicado | Resultado |
|---|---|---|
| **01** | — (línea base) | `29 passed · 6 failed · 66 errors` |
| 02 | *fixture* de `dispose()` del motor entre tests | `errors: 66 → 23` |
| 03 | migración de `admin_client` a `pytest_asyncio.fixture` | `errors: 23 → 0`, aparecen `41 failed` con `got Future attached to a different loop` |
| 04 | ámbitos explícitos de *event loop* en `pyproject.toml` | sin efecto |
| **05** | **`NullPool`** en el motor de pruebas | `26 failed · 74 passed · 1 skipped` |

Cada intervención tocó **exclusivamente** `backend/tests/**`, `backend/seeds/test_seeds.py`,
`backend/scripts/**` y la sección `[tool.pytest.ini_options]` de `pyproject.toml`.
**Ninguna tocó `backend/app/**`, `alembic/versions/**` ni el frontend.**

---

## 6. Línea base definitiva

RUN 05 es la línea base contra la que se medirá la Wave 2:

```
26 failed, 74 passed, 1 skipped in 22.78s
```

Reproducible con `bash backend/scripts/run_tests.sh`. Verificada dos veces con idéntico
resultado. La clasificación de los 26 fallos está en
`audit/remediation/BACKEND_TEST_FAILURE_MATRIX.md`.

---

## 7. Declaración de integridad

- Ningún test se modificó para que pasara.
- Ningún código de aplicación se modificó para complacer a un test.
- Ningún fallo se ocultó con `skip`, `xfail` ni filtros de selección.
- El único `skipped` es un `skip` preexistente en el repositorio, no introducido aquí.

**Congelado el 2026-09-03.**
