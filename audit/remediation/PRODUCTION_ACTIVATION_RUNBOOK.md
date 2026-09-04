# PRODUCTION ACTIVATION RUNBOOK

**Versión** Wave 2.75 · **Fecha** 2026-09-04
**Ámbito** primer despliegue que incluye `GA-REM-024` (migraciones en el arranque), las
migraciones de enum `R-40` / `R-41` y la reconciliación de permisos `R-44`.

> Este runbook **no se ejecuta** en esta Wave. Es el procedimiento verificable que hay que
> seguir cuando se decida publicar. Ninguno de sus comandos se ha ejecutado contra
> producción.

---

# PRECONDITIONS

| # | Condición | Cómo se comprueba | Bloqueante |
|---|---|---|---|
| 1 | Versión exacta a publicar identificada | `git rev-parse HEAD` sobre la rama que se publica; anotarlo | **sí** |
| 2 | Certificación de la Wave 2.75 vigente | `WAVE_2_75_EXECUTION_REPORT.md` con `READY_FOR_RELEASE = YES` | **sí** |
| 3 | **Copia de la base de datos**, tomada inmediatamente antes | ver §BACKUP | **sí** |
| 4 | PostgreSQL **12 o superior** | `SELECT version();` | **sí** — las migraciones de enum fallan por debajo |
| 5 | Credenciales del servidor disponibles | acceso SSH y permiso para `docker compose` | **sí** |
| 6 | El fichero `docker-compose.yml` del servidor está al día | contiene `avicola-media`, `MEDIA_DIR`, `SAP_EXPORT_DIR` y `MORTALITY_ALERT_*` | **sí** |
| 7 | Migraciones pendientes identificadas | ver §PRE-RELEASE CHECKS | **sí** |
| 8 | Ventana acordada | la aplicación no responde durante la migración | recomendable |

## BACKUP

Ninguna de las tres migraciones es reversible (`MIGRATION_SAFETY_MATRIX.md`). La única
vuelta atrás real es restaurar la base.

```
pg_dump --format=custom --file=avicola-pre-wave2-$(date +%Y%m%d-%H%M).dump "<DSN>"
```

**Verificar que la copia sirve, no solo que se creó:**

```
pg_restore --list avicola-pre-wave2-*.dump | head
```

> **`GA-TD-040` — capacidad de respaldo.** El proyecto **no tiene** un mecanismo de copia
> comprobado: no hay script, ni programación, ni evidencia de una restauración exitosa. La
> orden de arriba es la que corresponde a un PostgreSQL alcanzable, pero **su viabilidad
> no se ha verificado** en este entorno, y esta Wave tiene prohibido tocar producción.
>
> Clasificación: **`PRE-PRODUCTION BLOCKER`**. Publicar sin una copia comprobada significa
> que un fallo de migración no tendría vuelta atrás.

---

# PRE-RELEASE CHECKS

Ejecutar **antes** de tocar nada, y guardar la salida: es la referencia para comparar
después.

```bash
# 1 · Revisión actual del esquema
docker exec globalavicola-backend alembic current

# 2 · Salud y tiempo de vida del contenedor
docker inspect -f '{{.State.Health.Status}} {{.State.StartedAt}}' globalavicola-backend

# 3 · Estado del volumen de evidencias  (esperado ANTES de R-52: sin montaje)
docker inspect -f '{{json .Mounts}}' globalavicola-backend

# 4 · Fotografía de roles y permisos  (referencia para verificar la reconciliación)
docker exec globalavicola-backend python -c "
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def m():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.connect() as c:
        for fila in (await c.execute(text(
            'SELECT r.name, count(*) FROM permissions p JOIN roles r ON r.id=p.role_id '
            'GROUP BY 1 ORDER BY 1'))).all():
            print(fila)
    await e.dispose()
asyncio.run(m())"
```

Migraciones que se aplicarán:

```
j0k1l2m3n4o5   EGG_RECEPTION_CLASSIFICATION -> eventtype
k1l2m3n4o5p6   HATCHERY -> birdtypeenum
l2m3n4o5p6q7   reconciliación de permisos (R-44)
```

---

# ONE-TIME R-52 ACTION

**Qué es.** Watchtower recrea el contenedor con la imagen nueva pero **no vuelve a leer el
fichero compose**: conserva la definición de volúmenes con la que el contenedor se creó. El
volumen `avicola-media`, declarado desde la Wave 1 (`GA-REM-009`), no se monta hasta que
alguien recree el servicio desde el compose actual.

**No es un defecto de la aplicación.** Es una acción de activación, una sola vez.

```bash
cd <directorio del docker-compose.yml en el servidor>
docker compose up -d backend
```

**Verificación — no basta con que el comando devuelva 0:**

```bash
# 1 · El volumen existe
docker volume ls | grep avicola-media

# 2 · Está montado en /app/media
docker inspect -f '{{range .Mounts}}{{.Name}} -> {{.Destination}}{{"\n"}}{{end}}' \
  globalavicola-backend | grep avicola-media

# 3 · Sobrevive a la recreación: subir una evidencia por la interfaz,
#     recrear el contenedor y comprobar que se sigue descargando
docker exec globalavicola-backend ls -la /app/media
docker compose restart backend
docker exec globalavicola-backend ls -la /app/media   # el fichero debe seguir ahí
```

`R-52` solo puede darse por cumplido cuando el paso 3 pasa: el fichero sobrevive a la
recreación del contenedor.

---

# RELEASE

**No se ejecuta desde esta Wave.**

Con el mecanismo vigente (`EX-01`, sin cambios), publicar consiste en:

```
push a main
  → docker-push-backend.yml construye y publica :latest
  → Watchtower detecta la imagen nueva (pull_policy: always)
  → recrea globalavicola-backend
  → el ENTRYPOINT de la imagen ejecuta alembic upgrade head
  → si la migración falla, el contenedor NO sirve y restart: unless-stopped reintenta
  → si tiene éxito, arranca uvicorn
```

El orden `migración → servicio` está garantizado por el entrypoint, no por convención.

> **Orden recomendado:** ejecutar primero la acción `R-52` y después publicar. Así el
> volumen ya está montado cuando la imagen nueva arranca, y la evidencia persiste desde el
> primer minuto.

---

# STARTUP EXPECTATION

```
contenedor recreado
  → [entrypoint] Starting database migrations
  → [entrypoint] target: <host>/<base>
  → INFO [alembic] Running upgrade i9j0k1l2m3n4 -> j0k1l2m3n4o5
  → INFO [alembic] Running upgrade j0k1l2m3n4o5 -> k1l2m3n4o5p6
  → INFO [alembic] Running upgrade k1l2m3n4o5p6 -> l2m3n4o5p6q7
  → [R-44] asociaciones rol-permiso añadidas: N
  → [entrypoint] Migration completed
  → [entrypoint] Starting application: uvicorn app.main:app ...
  → healthcheck en verde
```

**Duración esperada:** segundos. Las tres migraciones son dos `ALTER TYPE` y hasta 22
`INSERT`.

**Si el registro se queda en `Starting database migrations`** más de un par de minutos,
véase `MIGRATION_SAFETY_MATRIX.md §6`: probablemente una migración esté esperando un
bloqueo.

```bash
docker logs -f globalavicola-backend
```

---

# POST-START CHECKS

En este orden. Cada uno tiene un resultado esperado concreto.

| # | Comprobación | Comando / acción | Esperado |
|---|---|---|---|
| 1 | Salud | `curl -fsS http://localhost:8002/health` | `{"status":"ok",...}` |
| 2 | Revisión del esquema | `docker exec globalavicola-backend alembic current` | `l2m3n4o5p6q7 (head)` |
| 3 | Estado de los enums | consulta de §ENUM abajo | `eventtype` 25 valores · `birdtypeenum` incluye `HATCHERY` |
| 4 | Permisos reconciliados | repetir la fotografía de §PRE-RELEASE CHECKS | cada rol con **más** asociaciones, ninguna perdida |
| 5 | Login | entrar con una cuenta real de cada rol | 200 |
| 6 | Renovación | dejar caducar el token o forzar `/refresh` | sesión continúa |
| 7 | Cambio de empresa | Super Admin cambia a una empresa | el contexto cambia y persiste al renovar |
| 8 | Maestros | abrir un formulario de operación con un usuario **no** Super Admin | los desplegables cargan |
| 9 | Alta de lote | crear un lote de prueba | 201 |
| 10 | Alta de operación | registrar una mortalidad con causa | 201 y la causa se conserva |
| 11 | Evidencia | subir un fichero y descargarlo | el contenido coincide |
| 12 | Persistencia de evidencia | recrear el contenedor y volver a descargar | el fichero sigue ahí |

### ENUM

```sql
SELECT t.typname, count(*) FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid
WHERE t.typname IN ('eventtype','birdtypeenum') GROUP BY 1;
-- eventtype 25 · birdtypeenum 5
```

El paso **8 es el más importante**: es el que `R-44` habría roto. Si un usuario que no es
Super Admin ve los desplegables vacíos o recibe 403, **detener y consultar §ROLLBACK**.

---

# ROLLBACK / INCIDENT

## Cuándo detener

| Síntoma | Gravedad | Acción |
|---|---|---|
| El contenedor no arranca y el registro muestra un fallo de Alembic | **alta** | no reintentar a ciegas: leer el error. La base **no** quedó a medias — la transacción revierte |
| Usuarios que no son Super Admin reciben 403 en maestros | **alta** | la reconciliación no se aplicó; comprobar `alembic current` |
| `alembic current` no es `l2m3n4o5p6q7` | **alta** | la migración no llegó a completarse |
| Las evidencias no persisten tras recrear | media | `R-52` no se ejecutó o el volumen no se montó |
| Un lote de incubadora no se crea | media | `k1l2m3n4o5p6` no se aplicó |

## Cómo volver atrás

**Las migraciones no son reversibles** (`MIGRATION_SAFETY_MATRIX.md`). La vuelta atrás es:

1. detener el contenedor: `docker stop globalavicola-backend`;
2. restaurar la copia tomada en §PRECONDITIONS;
3. desplegar la imagen anterior.

> El paso 3 exige conocer el *digest* de la imagen anterior. Con `:latest` y Watchtower,
> **ese dato no se conserva en ninguna parte**. Anotarlo en §PRE-RELEASE CHECKS antes de
> publicar:
>
> ```bash
> docker inspect -f '{{.Image}}' globalavicola-backend
> ```
>
> Se registra como `R-57` (P2): la estrategia de despliegue vigente no deja rastro de la
> versión anterior. No se corrige aquí —`EX-01` lo mantiene fuera de alcance— pero anotar
> el digest es una mitigación de coste cero.

## Qué NO hacer

- No ejecutar `alembic downgrade`: las tres migraciones lo tienen inoperativo a propósito.
- No borrar filas de `permissions` a mano: no hay forma de distinguir las que añadió la
  reconciliación de las que configurara un administrador.
- No desactivar Watchtower ni cambiar `:latest` para «controlar» el despliegue: `EX-01`
  sigue vigente y el problema no está ahí.

---

# APÉNDICE · Propiedad de las migraciones

**Quién ejecuta las migraciones: el entrypoint del contenedor backend. Nadie más.**

| Actor | ¿Migra? | Motivo |
|---|---|---|
| Entrypoint del contenedor | **sí** | única vía en el flujo normal |
| Workflows de CI | no | construyen y publican; no alcanzan la base |
| Operador por consola | **solo en incidente**, siguiendo este runbook | evita dos fuentes de verdad |

Una regla, sin ambigüedad. Antes de `GA-REM-024` no había ninguna, y esa es exactamente la
razón por la que `R-40` y `R-41` pudieron existir con sus migraciones en el repositorio.
