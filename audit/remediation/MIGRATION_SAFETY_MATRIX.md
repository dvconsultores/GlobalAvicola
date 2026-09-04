# MIGRATION SAFETY MATRIX

**Fecha** 2026-09-04 · **Wave** 2.75 · **Alcance** las tres migraciones que el primer
despliegue con `GA-REM-024` aplicará sobre una instalación existente

---

## 1. Clasificación de reversibilidad

| Clase | Significado |
|---|---|
| `FULLY_REVERSIBLE` | `downgrade` devuelve el esquema y los datos a su estado anterior |
| `LOGICALLY_REVERSIBLE` | el esquema se puede revertir, pero algún dato no se recupera |
| `FORWARD_ONLY` | no se puede revertir con seguridad; el `downgrade` no lo intenta |
| `DATA_BACKUP_REQUIRED` | revertir exige restaurar desde copia |

---

## 2. Las tres migraciones

| Revisión | Cambio | Transaccional | Si falla a mitad | Reversibilidad |
|---|---|---|---|---|
| `j0k1l2m3n4o5` | `ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'EGG_RECEPTION_CLASSIFICATION'` | **sí** en PostgreSQL 12+ | la transacción revierte; el tipo queda como estaba | **`FORWARD_ONLY`** |
| `k1l2m3n4o5p6` | `ALTER TYPE birdtypeenum ADD VALUE IF NOT EXISTS 'HATCHERY'` | **sí** | ídem | **`FORWARD_ONLY`** |
| `l2m3n4o5p6q7` | `INSERT` de hasta 22 filas en `permissions` | **sí** | la transacción revierte; ninguna fila queda escrita a medias | **`FORWARD_ONLY`** por decisión, no por limitación |

---

## 3. `ALTER TYPE ADD VALUE` — la particularidad de PostgreSQL

Hasta PostgreSQL 11, `ALTER TYPE ... ADD VALUE` **no podía ejecutarse dentro de un bloque
de transacción**. Desde la 12 sí, con una condición: el valor nuevo no puede **usarse** en
la misma transacción que lo añade.

Las dos migraciones cumplen la condición —añaden el valor y no lo utilizan— y se ejecutan
dentro de la transacción de Alembic sin trucos.

### Comparación con la migración histórica

`a1b2c3d4e5f6` (junio de 2026, ya aplicada en producción) usa otro enfoque:

```python
op.execute("COMMIT")
op.execute("ALTER TYPE birdtypeenum ADD VALUE IF NOT EXISTS 'hatchery'")
op.execute("BEGIN")
```

Cerrar y reabrir la transacción a mano deja la migración fuera del control transaccional de
Alembic: si algo falla después del `COMMIT`, lo ya aplicado no se revierte y
`alembic_version` puede quedar desalineado. **No se replica ese patrón** en las
migraciones nuevas, y no se modifica la histórica: ya se ejecutó, y reescribir una
migración aplicada es peor que convivir con ella.

Se registra como **`R-55`** (P3, documental) en `GA-REM-019`.

### Versión de PostgreSQL

Verificado sobre **PostgreSQL 16.2**, la versión del entorno de certificación. Si la
instalación de producción corriera PostgreSQL 11 o anterior, las dos migraciones de enum
fallarían con `ALTER TYPE ... cannot run inside a transaction block` — y, por `GA-REM-024`,
**el contenedor no arrancaría**, que es el comportamiento correcto: fallo visible en lugar
de esquema incoherente.

El runbook incluye la comprobación de versión entre sus precondiciones.

---

## 4. Por qué `FORWARD_ONLY` y no otra cosa

| Migración | Motivo |
|---|---|
| Las dos de enum | PostgreSQL **no permite eliminar valores** de un tipo enumerado. Revertir exigiría recrear el tipo y reescribir cada columna que lo use, con riesgo sobre datos existentes, para retirar un valor aditivo e inocuo |
| La de permisos | Técnicamente se podrían borrar las filas, pero **no hay forma de distinguir** las que añadió la migración de las que un administrador configurara después. Y revertirla devolvería la instalación al estado que corrige: usuarios legítimos con 403 en casi toda la aplicación |

**No se finge reversibilidad.** Las tres declaran su `downgrade` como no operativo y
explican por qué en su propio encabezado.

---

## 5. Consecuencia para el despliegue

Como ninguna es reversible por migración, la única vuelta atrás real es **restaurar una
copia de la base**. De ahí que el runbook exija copia previa como precondición y no como
recomendación.

Ver `PRODUCTION_ACTIVATION_RUNBOOK.md §PRECONDITIONS`.

---

## 6. Comportamiento ante un bloqueo

Si una migración quedara esperando un bloqueo —por ejemplo, una transacción larga sobre
`permissions`— el arranque **se detendría ahí**, sin ceder el control a `uvicorn`.

| Síntoma | Diagnóstico |
|---|---|
| El contenedor no responde en `/health` y el registro se queda en `Starting database migrations` | migración bloqueada |
| Consulta | `SELECT pid, state, query, wait_event_type FROM pg_stat_activity WHERE datname = '<base>'` |
| Acción | identificar y resolver la transacción bloqueante; el reintento de `restart: unless-stopped` reanudará |

**No se implementa un tiempo límite.** Añadirlo abriría la posibilidad de abandonar una
migración a medias, que es peor que esperar: con `set -e` y sin límite, el peor caso es un
servicio caído y visible, no una base a medio migrar.

Se registra el riesgo como **`R-56`** (P3) y su procedimiento de diagnóstico queda en el
runbook.
