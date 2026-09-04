# GA-REM-024 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-024` — Ejecución de migraciones antes de servir |
| **Wave** | 2.5 · **Paso 1** · **Origen** `GA-TD-013` (auditoría) |
| **Fecha** | 2026-09-04 |
| **Prioridad** | **P0 · RELEASE BLOCKER** |
| **Estado final** | **`CERTIFIED`** |

## Original finding

El despliegue era:

```
push a main → build → :latest → Watchtower → uvicorn
```

**Sin ningún paso de migración.** Comprobado en las cinco ubicaciones posibles:

| Ubicación | ¿Migra? |
|---|---|
| `backend/Dockerfile:56` — `CMD ["uvicorn", …]` | no |
| `docker-compose.yml` servicio `backend` — sin `command` ni `entrypoint` | no |
| `app/main.py` `lifespan` — solo registra *listeners* de auditoría | no |
| `.github/workflows/docker-push-backend.yml` — construye y publica | no |
| `entrypoint.sh` / script de despliegue | **no existe** |

La auditoría lo había registrado como `GA-TD-013`: *«cada release con cambio de esquema
rompe producción»*. Nunca recibió spec de remediación.

## Por qué bloqueaba la Wave 2.5

Las tres migraciones que la compatibilidad de producción necesita —`R-40`, `R-41` y la
reconciliación de `R-44`— **no habrían llegado a producción**. El contenedor nuevo habría
arrancado con el código nuevo contra el esquema viejo: exactamente el escenario que `R-44`
describe, agravado por un esquema al que le faltan valores de enum que el código usa.

Explica además, retrospectivamente, `R-40` y `R-41`: si las migraciones se aplican a mano y
de forma desigual, la deriva entre el enum de Python y el de PostgreSQL es el resultado
esperable.

## Implementation

`backend/docker-entrypoint.sh`, invocado como `ENTRYPOINT` de la imagen:

```sh
set -e
alembic upgrade head
exec "$@"
```

Tres decisiones, cada una con motivo:

| Decisión | Motivo |
|---|---|
| `set -e` | si la migración falla, el contenedor **no sirve**. Servir con el esquema equivocado corrompe datos; caerse ruidosamente y dejar que `restart: unless-stopped` reintente es preferible y visible |
| `exec "$@"` | el servidor hereda el PID 1 y recibe `SIGTERM` directamente: `docker stop` sigue siendo un apagado limpio |
| `ENTRYPOINT` y no `CMD` | los servicios que declaran su propio `command` —el bot de Telegram, que comparte imagen— pasan igualmente por la migración, que es idempotente y por tanto inocua |

## `EX-01` — por qué esto no toca el despliegue automático

La restricción prohíbe modificar Watchtower, `:latest`, `pull_policy`, los *triggers* y la
estrategia de publicación. **Ninguno se toca.** Watchtower sigue vigilando `:latest` con
`pull_policy: always` y recreando el contenedor igual que antes.

Lo único que cambia es lo que el contenedor hace en su primer segundo de vida, que es
responsabilidad de la imagen y no de la estrategia de despliegue.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| `AC01` | Migra antes de aceptar la primera petición | ✅ por construcción: `exec` solo se alcanza si `alembic upgrade head` retorna 0 |
| `AC02` | Si la migración falla, no sirve tráfico | ✅ `set -e` + `restart: unless-stopped` |
| `AC03` | Arrancar dos veces no produce efectos distintos | ✅ Alembic es idempotente por diseño; verificado en `PATH B` |
| `AC04` | Señales y apagado limpio | ✅ `exec` cede el PID 1 |
| `AC05` | Sin retraso perceptible sin migraciones pendientes | ✅ `alembic upgrade head` sobre una base al día es una consulta a `alembic_version` |
| `AC06` | `EX-01` intacto | ✅ watchtower 6 · `pull_policy` 3 · `:latest` 3 · 5 workflows, sin cambios |
| `AC07` | Mecanismo y ventana documentados | ✅ este informe y `RELEASE_COMPATIBILITY_REPORT.md §10` |

## Condición vigente, no garantía permanente

Hoy hay **un** contenedor de API (`container_name: globalavicola-backend`), sin réplicas, de
modo que no hay carrera de migraciones. Alembic además toma un bloqueo sobre
`alembic_version`.

Se documenta como **condición del despliegue actual**: el día que se introduzcan réplicas,
el arranque simultáneo exigirá revisarlo. Registrado como `R-53` (P3, condicional).

## Ventana de indisponibilidad

El *entrypoint* introduce una pausa entre el arranque del contenedor y la primera respuesta,
igual a la duración de las migraciones pendientes. Con las tres de esta Wave es
despreciable. Una migración pesada exigiría ventana planificada; `start_period: 15s` del
*healthcheck* absorbe lo razonable.

Es una pausa que **ya existía de hecho**, solo que ocupada sirviendo peticiones contra un
esquema equivocado.

## Files changed

```
backend/docker-entrypoint.sh   nuevo
backend/Dockerfile             COPY del entrypoint + ENTRYPOINT
docker-compose.yml             SIN CAMBIOS
.github/workflows/**           SIN CAMBIOS
```

## Final status

**`CERTIFIED`.** El orden `migración → servicio` queda garantizado por construcción, dentro
de las restricciones de `EX-01` y sin tocar la estrategia de despliegue.
