# RELEASE BLOCKERS

> ### OWNER CLARIFICATION / ENV-01
>
> The currently deployed environment was previously referred to as
> "production" in technical reports.
>
> It is not a real business production environment.
>
> It is a shared development, testing and certification environment
> containing only test/certification data.
>
> No real business production deployment currently exists.
>
> **Anotación añadida el 2026-09-04.** No se ha modificado la fecha, el hallazgo, la
> evidencia ni la decisión de este documento. Reclasificación de urgencia en
> [`ENVIRONMENT_NORMALIZATION_REPORT.md §6`](ENVIRONMENT_NORMALIZATION_REPORT.md).


**Fecha** 2026-09-04 · **Wave** 2.75

Un bloqueante de publicación cumple **al menos una** de estas condiciones: puede dejar la
aplicación sin iniciar, puede dejar la base incompatible, puede bloquear a usuarios
válidos, puede corromper o perder datos, puede romper el aislamiento multiempresa, deja
una operación crítica inutilizable, o exige una acción inexistente que no se ha preparado.

**No se incluyen P2 ni P3 ordinarios.** Viven en `GA-REM-019`.

---

## 1. Bloqueantes abiertos

| ID | Blocker | Reason | Resolution | Status |
|---|---|---|---|---|
| **`GA-TD-040`** | **No hay capacidad de respaldo comprobada** | Las tres migraciones son `FORWARD_ONLY`: la única vuelta atrás es restaurar la base. No existe script, ni programación, ni evidencia de una restauración exitosa. Publicar sin copia comprobada deja un fallo de migración sin remedio | Ejecutar y **verificar** un `pg_dump`/`pg_restore` contra la base real antes de publicar. El runbook lo exige como precondición | **ABIERTO** |

**Uno.** Y no es de código: es de capacidad operativa.

---

## 2. Resueltos durante las Waves 2.5 y 2.75

| ID | Blocker | Resolution | Status |
|---|---|---|---|
| `GA-TD-013` / `GA-REM-024` | El despliegue no ejecutaba migraciones: la aplicación arrancaba con código nuevo contra esquema viejo | *entrypoint* que migra antes de servir, con fallo cerrado. Certificado en 4 escenarios de arranque real | **RESUELTO** |
| `R-44` | Catálogo de permisos incompleto: usuarios legítimos con 403 en casi toda la aplicación | Migración de datos idempotente, verificada sobre el arranque real | **RESUELTO** |
| `R-48` | `switch-company` sin efecto: con RBAC activo nadie podía crear lotes | El claim se honra solo para quien ya opera entre compañías | **RESUELTO** |
| **`R-42`** | **Escritura entre inquilinos**: la empresa A podía registrar operaciones contra lotes de la empresa B, contaminando sus balances | `validate_lot_active` filtra por compañía; un lote ajeno se comporta como inexistente | **RESUELTO** |
| `R-54` | El contexto de empresa se perdía al renovar: un Super Admin volvía a su empresa en silencio a los 30 minutos | La renovación conserva el contexto desplazado, solo para quien puede tenerlo | **RESUELTO** |
| `R-51` | `LotUpdate` exponía `status`: se podía cerrar y reabrir un lote saltándose `close_lot` | El estado del lote cambia por su transición | **RESUELTO** |

---

## 3. Precondición operativa — no es bloqueante

| ID | Acción | Por qué no bloquea |
|---|---|---|
| `R-52` | `docker compose up -d backend` una vez en el servidor | El sistema arranca y funciona sin ella. Lo que no ocurre es que las evidencias persistan a la recreación del contenedor, de modo que `GA-REM-009` no surte efecto hasta ejecutarla. Procedimiento y verificación en el runbook |

Clasificación exigida:

```
CODE DEFECT ......... NO
RELEASE PRECONDITION  SÍ
ONE-TIME OPERATION .. SÍ
```

---

## 4. Riesgos anotados, fuera del umbral de bloqueo

| ID | Riesgo | Sev. | Destino |
|---|---|---|---|
| `R-50` | `company_id` fijable desde el cliente en 19 esquemas de maestros | P2, mitigado por RBAC | `GA-REM-019` · **prerrequisito de `OD-04`** |
| `R-47` | `POST /lots` ignora el `start_date` recibido: impide registrar eventos retroactivos en un lote recién creado | P1 | `GA-REM-019` |
| `R-57` | La estrategia de despliegue no conserva rastro de la versión anterior (`:latest` sin digest) | P2 | mitigado anotando el digest en el runbook |
| `R-55` | La migración histórica `a1b2c3d4e5f6` usa `COMMIT`/`BEGIN` a mano | P3, documental | `GA-REM-019` |
| `R-56` | Sin límite de tiempo para una migración bloqueada | P3 | procedimiento de diagnóstico en el runbook |
| `R-45`, `R-46`, `R-49`, `R-53` | Deuda menor de Waves anteriores | P2/P3 | `GA-REM-019` |

---

## 5. `GA-TD-039` — observabilidad

**No es bloqueante para esta publicación**, pero su prioridad sube.

Con `GA-REM-024`, el arranque emite mensajes explícitos —`Starting database migrations`,
`Migration completed`, `Starting application`, y el recuento de la reconciliación— y
`docker logs` basta para diagnosticar el primer despliegue con migraciones automáticas.
Eso cubre el mínimo que el encargo exige.

Lo que no existe es alerta ni retención: si un despliegue futuro falla a las tres de la
madrugada, nadie se entera hasta que alguien lo mire. `GA-TD-013` es la demostración: el
despliegue llevaba meses sin aplicar migraciones y **nadie lo supo**.

Clasificación: **`PRE-PRODUCTION`**, no `RELEASE_BLOCKER`.

---

## 6. Estado tras el push de `4fcc9a6` (2026-09-04)

El despliegue automático se activó y el código está en producción. Eso **no** cierra
ningún bloqueante. Detalle en
[`POST_PUSH_PRODUCTION_STATE_REPORT.md`](POST_PUSH_PRODUCTION_STATE_REPORT.md).

```
DEPLOYMENT OCCURRED UNDER EX-01
FORMAL RELEASE GATE NOT YET CERTIFIED
READY_FOR_RELEASE = NO
```

| Pendiente | Estado | Cambio |
|---|---|---|
| `GA-TD-040` copia verificada | **ABIERTO** — único bloqueante formal | agravado: las migraciones ya corrieron **sin** copia previa; cualquier copia nueva es `CURRENT_STATE_BACKUP` |
| `R-44` efecto de la reconciliación | **`NOT_VERIFIED`** | la migración se ejecutó; su efecto exige entrar con una cuenta no Super Admin |
| `R-52` volumen `avicola-media` | **PENDING** | sin cambio; Watchtower no relee el compose, así que `GA-REM-009` sigue inactiva en producción |
| `R-58` entrypoint en Docker real | **`PASS_BY_INFERENCE`** | el backend sirve tras un entrypoint con `set -e`, luego migró; falta la lectura de `docker logs` |
| `GA-TD-013` despliegue sin migraciones | **CERRADO en la práctica** | el despliegue ya aplica migraciones |

---

## 7. Reclasificación por `ENV-01` (2026-09-04)

El entorno desplegado no es producción real. Los gates se separan en dos conjuntos; nada
se elimina, todo cambia de destino.

### `SHARED TEST GATES` — lo que debe cumplirse para desplegar al entorno compartido

| Gate | Estado |
|---|---|
| Regresión backend | **PASS** — 283 pasados, 49 omitidos, 0 fallos |
| Regresión frontend | **PASS** — tsc, 61/61 vitest, ESLint, i18n 866=866 |
| Migraciones sin deriva | **PASS** — esquema, tablas, columnas y enums en 0 |
| Baseline limpio reproducible | **PASS** — `GA-REM-025` |
| `R-58` entrypoint en Docker real | **`PASS_BY_INFERENCE`** — falta `docker logs`; `BLOCKED_BY_AUTH` |
| `R-52` volumen de evidencias | **PENDING** — `docker compose up -d backend`; `BLOCKED_BY_AUTH` |
| Salud del entorno compartido | backend y frontend sirviendo |
| E2E | 23 fallos heredados sin clasificar → `GA-REM-016` |

```
READY_FOR_SHARED_TEST = YES
```

### `FUTURE REAL PRODUCTION GATES` — lo que hará falta antes del primer cliente

| Gate | Estado |
|---|---|
| `GA-TD-040` copia y restauración verificadas | **`PRE-REAL-PRODUCTION`** — ya no bloquea el desarrollo |
| `GA-TD-039` observabilidad completa | **`PRE-REAL-PRODUCTION`** |
| `R-67` saldo de apertura → saldo de aves | **abierto**, P1 — rompe la incorporación de lotes en marcha |
| `R-68` visibilidad de escrituras | **abierto**, P0 — intermitente, afecta a todo endpoint de escritura |
| Certificación E2E completa | `GA-REM-016` |
| Cero P0 abiertos | no |
| Decisión sobre SAP real | `GA-REM-017` `BLOCKED_EXTERNAL` |
| Runbook de despliegue y estrategia de reversión | pendiente |

```
READY_FOR_REAL_PRODUCTION = NOT_YET_CERTIFIED
```

### Sobre `GA-TD-040` y `GA-TD-039`

**Ninguno se cierra.** `GA-TD-040` baja de bloqueante de publicación a
`PRE-REAL-PRODUCTION`: una copia verificada sigue siendo imprescindible antes de que
existan datos de un cliente, y deja de ser razón para detener el desarrollo sobre datos de
prueba. `GA-TD-039` mantiene la misma lectura: la observabilidad mínima del entorno
compartido ya es útil hoy; la completa es gate futuro.


---

## 8. Checkpoint `R-68` + `R-67` (2026-09-04)

| Hallazgo | Antes | Ahora |
|---|---|---|
| `R-68` respuesta antes de confirmar | **P0 sistémico, abierto** | **`CERTIFIED`** — `GA-REM-026` |
| `R-67` saldo de apertura ignorado | P1, abierto | **`CERTIFIED`** — `GA-REM-005` enmienda |

Ambos figuraban en `FUTURE REAL PRODUCTION GATES §6`. Quedan cerrados ahí.

`R-68` merece una nota: era el único hallazgo abierto capaz de **falsificar el resultado de
cualquier prueba E2E de escritura**. Cerrarlo no sólo elimina un defecto; devuelve
credibilidad a la medición que viene después.

### Estado de los gates

```
READY_FOR_SHARED_TEST      = YES
READY_FOR_REAL_PRODUCTION  = NOT_YET_CERTIFIED
```

Sigue pendiente para producción real: `GA-TD-040` (copia y restauración verificadas),
`GA-TD-039` (observabilidad), la certificación E2E completa de `GA-REM-016`, la ejecución
del reset en el entorno compartido (`PENDING_EXTERNAL_ACCESS`), y la decisión sobre SAP
real (`GA-REM-017`).


---

## 9. Incidente del 502 (2026-09-05) — `R-71`

`R-71` queda **`CERTIFIED`** por `GA-REM-027`. No añade bloqueante; sí deja una lección para
el gate de producción real.

**Ninguna prueba de este repositorio recorría el salto proxy → backend.** `startup_test.sh`
certifica el entrypoint y el arranque, y lo hace bien, pero llama al backend directamente:
por eso pasaba con 0 fallos mientras la API pública llevaba ocho horas caída. Entre «el
backend arranca» y «la API responde» hay un salto sin cobertura.

Anotado como hueco. Para producción real conviene una comprobación de extremo a extremo
posterior al despliegue que atraviese el proxy, no solo el arranque del contenedor.

```
READY_FOR_SHARED_TEST      = YES
READY_FOR_REAL_PRODUCTION  = NOT_YET_CERTIFIED
```
