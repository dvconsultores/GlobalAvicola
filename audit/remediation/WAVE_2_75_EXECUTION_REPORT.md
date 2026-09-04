# WAVE 2.75 — EXECUTION REPORT

**Global Avícola** · Gate de migración en runtime · Certificación de autenticación
multiempresa · Preparación de activación productiva

**Fecha** 2026-09-04 · **Commit base** `bfccdfb` · **Estado** `COMPLETE`

---

# 1. Executive Summary

```
ARRANQUE REAL (4 escenarios) .......... 0 fallos
  fresh install ....................... el arranque crea el esquema
  existing upgrade .................... el arranque migra y reconcilia
  restart at head ..................... idempotente, sin duplicados
  migration failure ................... fail-closed: la aplicación NO arranca

Ciclo de negocio tras arranque real ... 14 PASS
Camino de actualización ............... 35 PASS
Suite completa ........................ 253 PASS · 0 FAIL   (2026 y 2028, idéntico)
Smoke post-despliegue ................. 10 PASS

GA-REM-024 ............................ CERTIFIED
R-40 / R-41 / R-44 en startup real .... CERTIFIED
R-48 switch-company ................... CERTIFIED
GA-REM-002 ............................ CERTIFIED
GA-REM-005 (umbral configurable) ...... CERTIFIED

Hallazgos nuevos ......................  4  (R-42 escalado, R-54, R-55…R-57)
Regresiones introducidas ..............  0
Bloqueantes de publicación abiertos ...  1  (GA-TD-040, capacidad de respaldo)

READY_FOR_E2E ......................... YES
READY_FOR_RELEASE ..................... NO — falta una copia de seguridad comprobada
```

**El hallazgo más grave de la Wave apareció probando el aislamiento multiempresa:** un
usuario de la empresa A podía **registrar operaciones contra un lote de la empresa B**.
No era una fuga de lectura —los filtros de listado funcionaban— sino una **escritura entre
inquilinos**: el evento quedaba archivado bajo A pero ligado a un lote de B, y como el
saldo de aves se calcula por `lot_id` sin filtro de compañía, contaminaba los balances de
B. Corregido y cubierto por test.

---

# 2. `GA-REM-024`

## Arquitectura verificada, no supuesta

Cinco ubicaciones inspeccionadas antes de la Wave 2.5; ninguna migraba. Ahora:

```
backend/Dockerfile:47   COPY docker-entrypoint.sh /usr/local/bin/
backend/Dockerfile:61   ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
backend/Dockerfile:62   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```sh
set -e
echo "[entrypoint] Starting database migrations"
echo "[entrypoint] target: <host>/<base>"      # sin credenciales
alembic upgrade head
echo "[entrypoint] Migration completed"
echo "[entrypoint] Starting application: $*"
exec "$@"
```

## Limitación declarada

Esta máquina **no tiene Docker**. Lo certificado es el **comportamiento del entrypoint**,
ejecutándolo tal cual contra PostgreSQL real. Lo que **no** se ha ejercitado es la capa de
imagen: el `COPY`, el cableado de `ENTRYPOINT`, y que el usuario `avicola` pueda ejecutar
el script y `alembic`.

Se declara como pendiente de un entorno con Docker (`R-58`, P2) y se incluye en el runbook
como comprobación del primer despliegue. **No se afirma más de lo que se probó.**

---

# 3. Arquitectura de migración en runtime

| Pregunta | Respuesta con evidencia |
|---|---|
| ¿Quién ejecuta las migraciones? | **El entrypoint del contenedor backend, y nadie más.** Documentado en el apéndice del runbook. Los workflows construyen y publican; no alcanzan la base. Un operador solo migra siguiendo el runbook, en incidente |
| ¿Se ejecutan antes de servir? | Sí, por construcción: `exec` solo se alcanza si `alembic upgrade head` retorna 0 |
| ¿Riesgo de concurrencia? | **Ninguno hoy.** `container_name: globalavicola-backend`, sin `deploy.replicas`, sin escalado: una única instancia. Alembic además bloquea `alembic_version`. Documentado como condición vigente, no como garantía permanente (`R-53`) |
| ¿El bot de Telegram interfiere? | No: comparte imagen y pasa por el mismo entrypoint, cuya migración es idempotente y por tanto inocua |

---

# 4. Comportamiento ante fallo de migración

Escenario 4 del arnés, con un DSN imposible:

```
✓ el arranque termino con codigo 1
✓ el servidor NO arranco: fail-closed correcto
✓ no se alcanzo el punto de cesion del control
```

La comprobación es doble: el código de salida **y** la ausencia de la marca que el
"servidor" deja al arrancar. No basta con que el proceso termine mal; hay que demostrar que
el siguiente eslabón nunca se ejecutó.

---

# 5. Instalación nueva — runtime

```
base vacía → entrypoint → alembic → esquema en l2m3n4o5p6q7 → servidor arranca
```

```
✓ el entrypoint cedio el control al servidor
✓ esquema creado por el arranque, no a mano
✓ registra el inicio de la migracion
✓ registra la migracion completada
```

---

# 6. Actualización de instalación existente — runtime

**El test más importante.** Nadie ejecuta `alembic` a mano: lo hace el arranque.

```
antes:   revision=i9j0k1l2m3n4  permisos=33
         (no se ejecuta alembic a mano: debe hacerlo el arranque)
despues: revision=l2m3n4o5p6q7  permisos=55

✓ el arranque migro la base (i9j0k1l2m3n4 -> l2m3n4o5p6q7)
✓ el arranque reconcilio permisos (33 -> 55)
✓ el servidor arranco despues de migrar
```

Sobre esa base, el ciclo completo que el encargo exige: **14 PASS** —login, refresh,
switch-company, leer maestros, crear lote, crear y leer operación, mortalidad con causa,
`R-40`, `R-41` y los accesos por rol—.

> **Corrección a la Wave 2.5.** Aquel informe cifró la reconciliación en 41 asociaciones
> (+17). La cifra real, medida sobre la base, es **46 (+22)**, o 55 con los comodines del
> Super Admin. Fue un error de estimación al redactar, no de la migración. Corregido en
> `RBAC_ROLE_PERMISSION_MATRIX.md`, `PRODUCTION_UPGRADE_COMPATIBILITY_MATRIX.md` y
> `WAVE_2_5_EXECUTION_REPORT.md`.

---

# 7. Reinicio con la base al día

Escenario de Watchtower: el entrypoint se ejecuta en **cada** recreación.

```
✓ segundo arranque: mismo numero de permisos (55)
✓ sin asociaciones duplicadas
✓ el servidor arranco de nuevo
```

Tres escenarios distintos, los tres certificados: instalación nueva, actualización y
reinicio en head.

---

# 8. `R-40` — el 25.º tipo de evento

Tras el arranque real sobre una base que tenía 24 valores: el tipo existe en el enum de
PostgreSQL, el evento se inserta y se relee.

# 9. `R-41` — `birdtypeenum`

Tras el arranque real: `HATCHERY` presente, `'hatchery'` histórico conservado, lote de
incubadora creado y releído, lotes históricos legibles.

# 10. `R-44` — permisos

Reconciliados **por el arranque**, no por un operador. Seis rutas por rol accesibles, tres
denegaciones verificadas. Mínimo privilegio conservado: 13 operaciones de administración
siguen siendo exclusivas del Super Admin, y el Auditor no tiene ninguna acción de escritura.

---

# 11. `R-48` — cambio de empresa

## Fuente de verdad, una sola

`get_current_user` resuelve el contexto efectivo. Un test lo fija sobre el código fuente:

- **usuario normal** → manda la base. Un token no puede reclamar una compañía ajena;
- **Super Admin** → se honra el claim que `switch-company` emitió, porque ya puede operar
  sobre cualquier compañía y lo único que el claim hace es **acotar dónde escribe**.

## `R-54` — hallazgo nuevo

El contexto **se perdía al renovar**: un Super Admin trabajando en la empresa B volvía a la
suya en silencio a los treinta minutos. La renovación reconstruía los claims desde la base
sin contemplar el desplazamiento.

Corregido: la renovación conserva el contexto, y solo para quien puede tenerlo. `login`,
`refresh` y `switch-company` comparten ahora un único constructor de claims.

## Matriz verificada

| Escenario | Resultado |
|---|---|
| Super Admin sin contexto | opera en su compañía de origen |
| `switch-company` a empresa válida | el contexto cambia |
| Lote creado tras el cambio | pertenece a la empresa seleccionada |
| Maestro creado tras el cambio | ídem |
| `switch-company` a empresa inexistente | 404 |
| Usuario normal intenta cambiar | 403 |
| Usuario normal reclama otra empresa en el token | ignorado; ve solo la suya |
| Renovación tras el cambio | el contexto se conserva |

---

# 12. Aislamiento multiempresa

## `R-42` — escritura entre inquilinos *(el hallazgo grave)*

`validate_lot_active` consultaba el lote **sin filtrar por compañía**. Como `create_event`
fija `company_id = self.company_id` —la de quien pide— y el `lot_id` no se comprobaba, la
empresa A podía registrar operaciones contra un lote de la empresa B.

El evento quedaba bajo A pero ligado a un lote de B; y como `get_current_bird_balance`
calcula por `lot_id` sin filtro de compañía, **contaminaba los balances de B**.

En la Wave 2 lo clasifiqué como P1 «no filtra por compañía». Era más que eso: los filtros
de listado protegían la lectura y **nadie comprobaba la referencia** en la escritura.

Corregido: un lote ajeno se comporta como inexistente, que es lo que debe parecerle a quien
no tiene derecho a verlo.

## Matriz e IDOR

`MULTICOMPANY_ISOLATION_MATRIX.md` recorre los servicios; **12 tests** cubren lectura,
escritura, registro contra recurso ajeno y barrido de listados. Todos pasan.

---

# 13. `GA-REM-005` — validación de `Settings`

| Pregunta (§26) | Respuesta |
|---|---|
| Fuente de configuración | `pydantic-settings`: variables de entorno y fichero `.env` |
| Valores por defecto | 3 % advertencia, 8 % crítico — los históricos |
| Validación | tipado `float`; un test comprueba `0 < warning < critical < 100` |
| Comportamiento en ejecución | el generador de alertas lee las constantes del módulo, alimentadas por `Settings` |
| Persistencia | el entorno del contenedor; sobrevive al reinicio porque `docker-compose.yml` lo declara |

**Se añadió a `docker-compose.yml`** con el mismo patrón que `FEATURE_RATE_LIMIT_ENABLED`:

```yaml
MORTALITY_ALERT_WARNING_PCT:  ${MORTALITY_ALERT_WARNING_PCT:-3.0}
MORTALITY_ALERT_CRITICAL_PCT: ${MORTALITY_ALERT_CRITICAL_PCT:-8.0}
```

Sin esto, «configurable» habría exigido editar código y reconstruir la imagen — que es
justamente lo que la palabra excluye.

**Prueba de efecto (§27):** con umbral al 3 %, una mortalidad del 4 % alerta; con umbral al
5 %, la misma proporción **no** alerta. La configuración cambia el comportamiento.

Alcance por empresa: sigue en `GA-REM-019` como mejora opcional. No se reabre.

---

# 14. `R-52` — volumen de evidencias

```
CODE DEFECT ......... NO
RELEASE PRECONDITION  SÍ
ONE-TIME OPERATION .. SÍ
```

Procedimiento exacto y verificación en el runbook: no basta con que `docker compose up -d`
devuelva 0. Hay que comprobar que el volumen existe, que está montado, y —el paso que
importa— que un fichero **sobrevive a la recreación del contenedor**.

**No se ejecutó en producción.**

# 15. Persistencia de evidencias

La suite de humo cubre el ciclo completo: subir, listar, descargar y comparar el contenido.
Verificado en entorno de pruebas. La persistencia tras recreación solo puede comprobarse
donde haya Docker: queda como paso 12 de las comprobaciones posteriores al arranque.

---

# 16. Preparación de respaldo

**`GA-TD-040` es un bloqueante de publicación.**

Las tres migraciones son `FORWARD_ONLY`: la única vuelta atrás es restaurar la base. Y el
proyecto **no tiene** un mecanismo de copia comprobado — ni script, ni programación, ni
evidencia de una restauración exitosa.

El runbook incluye la orden `pg_dump`/`pg_restore` que corresponde, pero **su viabilidad no
se ha verificado**: esta Wave tiene prohibido tocar producción, y afirmar que funciona sin
haberlo probado sería exactamente el tipo de suposición que esta serie de Waves viene
desmontando.

Publicar sin una copia comprobada significa que un fallo de migración no tendría remedio.

---

# 17. Seguridad de las migraciones

`MIGRATION_SAFETY_MATRIX.md`. Las tres son transaccionales en PostgreSQL 12+ y las tres son
**`FORWARD_ONLY`** — dos por limitación de PostgreSQL, la de permisos por decisión razonada.

Si una fallara a mitad, la transacción revierte: la base no queda a medias.

Se registra `R-55`: la migración histórica `a1b2c3d4e5f6` usa `COMMIT`/`BEGIN` a mano, un
patrón que las nuevas **no** replican. No se reescribe: ya se ejecutó, y reescribir una
migración aplicada es peor que convivir con ella.

---

# 18. Registro del arranque

```
[entrypoint] Starting database migrations
[entrypoint] target: local/global_avicola_upgrade_test
INFO  [alembic.runtime.migration] Running upgrade ...
[R-44] asociaciones rol-permiso añadidas: 22
[entrypoint] Migration completed
[entrypoint] Starting application: uvicorn app.main:app ...
```

Un test comprueba que el registro **no contiene credenciales**: solo host y base, nunca el
DSN completo ni el secreto JWT.

Cubre el mínimo que `GA-TD-039` exige para este despliegue: inicio, éxito o fallo,
arranque y salud. Lo que falta es alerta y retención — `PRE-PRODUCTION`, no bloqueante.

---

# 19. Regresión backend

| | Wave 2.5 | **Wave 2.75** |
|---|---:|---:|
| Suite principal | 229 | **253** |
| PASS | 229 | **253** |
| FAIL | 0 | **0** |
| Camino de actualización | 35 | 35 |
| Ciclo tras arranque real | — | **14** |
| Escenarios de arranque | — | **4** |

+24 tests: aislamiento multiempresa (12), arranque real (14, en su propia suite), humo (10),
`AC08` (2).

# 20. Regresión frontend

```
TypeScript ....... PASS
Vitest ........... PASS 61/61
Paridad i18n ..... PASS ES=866 EN=866
```

Sin cambios en el frontend esta Wave.

# 21. Integridad de base de datos

```
Deriva de tablas .... 0
Deriva de columnas .. 0
Deriva de enums ..... 0
Heads de Alembic .... 1   (l2m3n4o5p6q7)
```

Ninguna migración nueva en esta Wave: se certificaron las tres existentes sobre el arranque
real.

# 22. Release blockers

**Uno abierto:** `GA-TD-040`, capacidad de respaldo. Detalle en `RELEASE_BLOCKERS.md`.

Seis resueltos entre las Waves 2.5 y 2.75, incluidos `R-42` (escritura entre inquilinos) y
`R-54` (pérdida del contexto de empresa), ambos descubiertos aquí.

# 23. `READY_FOR_E2E`

```
READY_FOR_E2E = YES
```

Las operaciones críticas y la seguridad están estables y verificadas en el ciclo de
arranque real. `R-52` es una acción de activación en producción y no condiciona la
certificación E2E, que se ejecuta en entorno de pruebas.

`GA-REM-016` puede comenzar.

# 24. `READY_FOR_RELEASE`

```
READY_FOR_RELEASE = NO
```

**No por el código.** Trece de los catorce requisitos están cumplidos con evidencia runtime
independiente:

| Requisito | Estado |
|---|---|
| `GA-REM-024` | ✅ CERTIFIED |
| `R-40` / `R-41` / `R-44` en upgrade runtime | ✅ PASS |
| `GA-REM-002` · `R-48` · `GA-REM-005` | ✅ CERTIFIED |
| Configuración de `Settings` | ✅ VERIFIED |
| Instalación nueva · actualización · reinicio en head | ✅ PASS |
| Regresión backend | ✅ 253 GREEN |
| Guardas de producción | ✅ PASS |
| Procedimiento `R-52` | ✅ READY |
| **Copia de seguridad** | ❌ **MISSING** |

El decimocuarto —una copia comprobada— falta, y con tres migraciones irreversibles no es
una formalidad: es la diferencia entre un fallo recuperable y uno que no lo es.

**Es un bloqueante de una tarde**, no de una Wave: ejecutar y verificar un
`pg_dump`/`pg_restore` contra la base real. En cuanto exista esa evidencia,
`READY_FOR_RELEASE` pasa a `YES` sin más trabajo de ingeniería.

# 25. Recomendación para la Wave 3

| # | Trabajo | Motivo |
|---|---|---|
| 1 | **`GA-TD-040`** — copia comprobada | único bloqueante. Desbloquea la publicación |
| 2 | **Publicar**, con `R-52` en el mismo despliegue | la compatibilidad está certificada por tres caminos |
| 3 | `GA-REM-016` — certificación E2E y de procesos | desbloqueada; único camino al nivel de madurez 4. Puede solaparse con 1 y 2 |
| 4 | `GA-TD-039` — observabilidad | `PRE-PRODUCTION`. `GA-TD-013` demostró que un despliegue puede fallar meses sin que nadie lo note |
| 5 | `R-58` — certificar el arranque con Docker real | cierra la única limitación declarada de esta Wave |
| 6 | `GA-REM-011` · `GA-REM-021` · `GA-REM-022` | backlog funcional |
| 7 | `GA-REM-019` | acumula `R-45`…`R-57` |

# 26. Evidence index

| Documento / artefacto | Contenido |
|---|---|
| `backend/scripts/startup_test.sh` | 4 escenarios de arranque real, reproducible |
| `backend/scripts/runtime_test.sh` · `tests/test_runtime_startup.py` | ciclo de negocio sobre la base que migró el arranque |
| `backend/scripts/upgrade_test.sh` · `tests/test_upgrade_path.py` | camino de actualización |
| `tests/test_multicompany_isolation.py` | aislamiento e IDOR (12 tests) |
| `tests/test_smoke.py` | suite de humo posterior al despliegue (10 tests) |
| `MULTICOMPANY_ISOLATION_MATRIX.md` | contexto, filtrado y propiedad por servicio |
| `MIGRATION_SAFETY_MATRIX.md` | transaccionalidad y reversibilidad |
| `PRODUCTION_ACTIVATION_RUNBOOK.md` | procedimiento operativo verificable |
| `RELEASE_BLOCKERS.md` | el bloqueante abierto y los seis resueltos |
| `RBAC_ROLE_PERMISSION_MATRIX.md` | corregido: 46 asociaciones, no 41 |
| `BACKEND_TEST_BASELINE_RUN_01.md` | **congelado, no sobrescrito** |
