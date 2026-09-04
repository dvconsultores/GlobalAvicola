# RELEASE BLOCKERS

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
