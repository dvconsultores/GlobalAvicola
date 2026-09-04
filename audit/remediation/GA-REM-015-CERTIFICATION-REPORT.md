# GA-REM-015 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-015` — Certificación de la suite backend |
| **Fecha** | 2026-09-03 · **Wave** 1.5 · **Track** C |
| **Naturaleza** | `CERTIFICATION / DIAGNOSIS` — **no** `FIX ALL TESTS` |
| **Estado final** | **`CERTIFIED`** |

## Finding
La suite backend —101 tests escritos entre el 23 y el 29 de junio de 2026— **nunca se había
ejecutado**. No existía ningún registro de una ejecución, ni en CI ni localmente. Los tests
eran, en el sentido estricto, código muerto: afirmaciones sobre el sistema que nadie había
comprobado.

## Spec
`specs/remediation/GA-REM-015-BACKEND-TEST-CERTIFICATION.md` · depende de `GA-REM-014` (`CERTIFIED`).

## Qué se hizo

1. Se ejecutó la suite por primera vez sobre PostgreSQL 16.2 real y aislado (**RUN 01**).
2. Se sanearon **cuatro capas de defectos de la infraestructura de pruebas**, sin tocar
   lógica de negocio, hasta que la suite midiera el producto y no a sí misma (**RUN 05**).
3. Se clasificó **cada uno** de los 26 fallos restantes con evidencia en ruta y línea.
4. Se trazó cada fallo a su `GA-REM` de destino.

## Resultados

| Run | Resultado | Qué medía |
|---|---|---|
| **RUN 01** | `29 passed · 6 failed · 66 errors` | la infraestructura de pruebas |
| **RUN 05** | `26 failed · 74 passed · 1 skipped in 22.78s` | **el producto** |

RUN 01 está congelado en `audit/remediation/BACKEND_TEST_BASELINE_RUN_01.md` y no debe
sobrescribirse. RUN 05 es la línea base contra la que se medirá la Wave 2.

Los 66 `ERROR` de RUN 01 eran `InterfaceError` por reutilización de conexiones `asyncpg`
entre *event loops*. Se resolvieron progresivamente: *fixture* de `dispose()` (66→23),
migración de `admin_client` a `pytest_asyncio.fixture` (23→0 errores, 41 fallos nuevos),
ámbitos explícitos de *loop* (sin efecto) y finalmente **`NullPool`**, que lo cerró.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | La suite se ejecuta completa contra una base real y aislada | ✅ RUN 01 … RUN 05, `run_tests.sh` |
| AC02 | Existe una línea base congelada e inmutable | ✅ `BACKEND_TEST_BASELINE_RUN_01.md` |
| AC03 | Cada FAIL/ERROR tiene clasificación de la taxonomía | ✅ 26/26, **cero `UNKNOWN`** |
| AC04 | Cada fallo tiene evidencia en ruta y línea | ✅ `BACKEND_TEST_FAILURE_MATRIX.md §2` |
| AC05 | Cada fallo tiene `GA-REM` de destino | ✅ 26/26 |
| AC06 | Ningún test se modificó para pasar | ✅ `git diff` sobre `backend/tests/**` no contiene cambios de aserciones de negocio |
| AC07 | Ningún código de aplicación se modificó para complacer un test | ✅ **cero cambios en `backend/app/**` en toda la Wave 1.5**. Los 8 ficheros de `backend/app` con cambios en el árbol de trabajo son entregables **de Wave 1** (`GA-REM-009`, `010`, `011`), ya certificados y documentados en `WAVE_1_EXECUTION_REPORT.md` |
| AC08 | El resultado es reproducible | ✅ dos ejecuciones idénticas |

## Tests ejecutados

| ID | Verificación | Resultado |
|---|---|---|
| `T-015-01` | Ejecución completa de los 101 tests | 26 F · 74 P · 1 S · **PASS** |
| `T-015-02` | Reproducibilidad | segunda ejecución idéntica · **PASS** |
| `T-015-03` | Clasificación exhaustiva | 26/26, 0 `UNKNOWN` · **PASS** |
| `T-015-04` | Sin cambios en `backend/app/**` atribuibles a Wave 1.5 | el diff de los 8 ficheros corresponde íntegramente a `GA-REM-009/010/011` de Wave 1 · **PASS** |
| `T-015-05` | Integridad de la cadena Alembic en cada ejecución | 1 head · 48 tablas · head sincronizado · **PASS** |

**PASS 5 · FAIL 0**

## Composición de los 26 fallos

```
TEST_DEFECT ................ 14   defectos de los propios tests
OBSOLETE_TEST ..............  4   contratos que cambiaron legítimamente
IMPLEMENTATION_BUG .........  4   defectos reales del producto
FIXTURE_DEFECT .............  2   datos de siembra insuficientes
SPEC_MISMATCH ..............  1   sin árbitro documental
UNKNOWN ....................  0
```

**20 de 26 son problemas de los tests, no del producto.** Es la consecuencia previsible de
escribir 101 tests sin ejecutarlos nunca: codifican rutas equivocadas
(`/operations` sin prefijo), *payloads* incompletos (sin `farm_id`) y credenciales
eliminadas. No prueban lo que dicen probar.

Los 4 defectos reales son graves y **dos de ellos no los habría encontrado ninguna lectura
de código**: aparecieron porque la suite por fin corre.

## Defectos del producto revelados

| ID | Hallazgo | Sev. | Destino |
|---|---|---|---|
| `P0-14` | 14 columnas de datos operativos se descartan en silencio en la creación de eventos — incluida `cause_id`, la **causa de mortalidad** | **P0** | `GA-REM-023` |
| `R-26` | 7 reglas de negocio devuelven **500** en lugar de 400 porque sus validadores caen fuera del `try/except` | P1 | `GA-REM-023` |
| `R-27` | `_get_role_by_name` responde 500 ante configuración ausente | P2 | `GA-REM-023` |
| `R-28` | La suite **caduca** por `BR-19`: fechas literales de junio de 2026, plazo de 90 días | P1 | `GA-REM-015` (cierre) |
| `R-29` | `test_farm_inspection_without_house_id_still_accepted` contradice a `validators.py:365` sin árbitro | P2 | `GA-REM-018` |

Y la confirmación en ejecución de `P0-1`:

```
app/operations/service.py:244: in _check_and_create_alerts
    balance = await get_current_bird_balance(self.db, event.lot_id, self.company_id)
E   NameError: name 'get_current_bird_balance' is not defined
```

Estático desde la auditoría, **ahora confirmado en runtime**. Ningún test de los 101 recorre
esa ruta: `test_f8c` pasa porque usa `quantity: 999999`, que `validate_mortality` rechaza
antes de que el generador de alertas se ejecute.

## Advertencia de caducidad — `R-28`

`validate_period_open` (`BR-19`) rechaza eventos de más de 90 días. Los tests fijan fechas
literales:

```
test_full_workflow_audit.py   "2026-06-29"  ->  caduca ~2026-09-27
test_operations.py            "2026-06-23"  ->  caduca ~2026-09-21
```

**Decenas de tests hoy en verde fallarán solos a partir del 2026-09-21** sin que nadie
cambie una línea. Debe corregirse —fechas relativas a `date.today()`— **antes de esa fecha**,
o la línea base RUN 05 dejará de ser reproducible y `GA-REM-016` heredará el defecto.

## Regression
Ninguna sobre el producto. Todo lo que Wave 1.5 tocó vive en `backend/tests/**`,
`backend/seeds/**`, `backend/scripts/**`, la sección `[tool.pytest.ini_options]` de
`pyproject.toml`, `audit/**` y `specs/**`. **`backend/app/**`, `alembic/versions/**` y
`frontend/src/**` no se tocaron en esta Wave.**

## Files
| Archivo | Acción |
|---|---|
| `audit/remediation/BACKEND_TEST_BASELINE_RUN_01.md` | **creado y congelado** |
| `audit/remediation/BACKEND_TEST_FAILURE_MATRIX.md` | **creado** — 26 fallos clasificados |
| `specs/remediation/GA-REM-023-EVENT-FIELD-PERSISTENCE-AND-ERROR-CONTRACT.md` | **creada** — `P0-14`, `R-26`, `R-27` |
| `backend/app/**` | **sin cambios** |

## Final status
**`CERTIFIED`** — existe línea base, es reproducible, y cada fallo tiene diagnóstico,
evidencia y destino. La Wave 2 puede medirse contra ella.
