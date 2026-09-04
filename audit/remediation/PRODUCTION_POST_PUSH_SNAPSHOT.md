# PRODUCTION POST-PUSH SNAPSHOT

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


**Fecha de captura** 2026-09-04 · **Modo** solo lectura · **Mutaciones ejecutadas** ninguna

> Todo lo que sigue es observación. No se reinició ningún contenedor, no se ejecutó
> `docker compose up`, ni `alembic upgrade`, ni ninguna migración o reconciliación, ni se
> modificó dato alguno de producción.

---

## 1. Push que originó el despliegue

| Dato | Valor |
|---|---|
| Rama local y remota | `main` |
| Commit empujado | `4fcc9a6` (`4fcc9a673d7636f42c1e381967e7c6361e4242d1`) |
| Base anterior | `bfccdfb` |
| Commits publicados | 14 |
| Fecha del commit | 2026-09-04T18:52:34+02:00 |
| Ficheros bajo `backend/` | 72 |
| Ficheros bajo `frontend/` | 12 |

## 2. ¿Era una rama que despliega?

**Sí.** Ambas publicaciones de imagen se dispararon:

| Workflow | Ramas | Rutas | Publica |
|---|---|---|---|
| `docker-push-backend.yml` | `main` | `backend/**` | **sí** |
| `docker-push-frontend.yml` | `main` | `frontend/**` | **sí** |
| `backend-ci.yml` · `frontend-ci.yml` · `quality-gates.yml` | `main` | — | no |
| `docker-build-push.yml` | manual | — | no |

```
AUTO_DEPLOY_BRANCHES ...... main
NON_DEPLOY_BRANCHES ....... ninguna otra configurada
```

## 3. Acceso disponible desde esta sesión

| Vía | Estado | Motivo |
|---|---|---|
| SSH al servidor de producción | **`BLOCKED_BY_AUTH`** | No existe `~/.ssh/config` ni procedimiento de acceso documentado en el repositorio. **No se buscaron claves alternativas** (§6, §62) |
| Base de datos de producción | **`NOT_REACHABLE`** | El puerto 5432 acepta TCP pero el servidor corta el intercambio de PostgreSQL: `ConnectionDoesNotExistError` con SSL desactivado, `ConnectionResetError` con SSL. Compatible con un `pg_hba.conf` o cortafuegos que no admite esta IP de origen. **No se probaron credenciales alternativas** |
| API del backend por el proxy | **DISPONIBLE** | `https://avicola.globaldv.net/api/v1/…` responde `application/json` |

En consecuencia: `docker ps`, `docker logs`, `docker inspect` y las consultas directas a
`alembic_version`, `pg_enum` y `permissions` **no pudieron ejecutarse**.

## 4. Endpoint real del backend

`/health` y `/openapi.json` devuelven **`text/html`**: son la SPA. El backend vive tras
`location /api/` → `proxy_pass http://backend:8000` (`frontend/nginx.conf:41-42`).

| Ruta | Código | `Content-Type` |
|---|---|---|
| `/health` | 200 | `text/html` ← **falso positivo, es el frontend** |
| `/openapi.json` | 200 | `text/html` ← ídem |
| `/api/v1/operations/event-types` | 200 | **`application/json`** ← backend real |

**El `200` que esta sesión reportó tras el push era la SPA, no el backend.** Queda
corregido aquí.

## 5. Qué código está corriendo

Dos discriminadores independientes, ambos sin autenticar y sin cuerpo, por tanto sin
posibilidad de mutar nada:

| Sonda | Código anterior | Código nuevo | Observado |
|---|---|---|---|
| `POST /api/v1/users/{id}/password` — ruta creada en la Wave 2 (`GA-REM-012`) | `404` (no existe) | `401` (existe, exige sesión) | **`401`** |
| `GET /api/v1/operations/alerts` — reordenada en la Wave 2 (`R-38`) | `422` (la capturaba `/{event_id}`) | `401` (ruta propia con permiso) | **`401`** |
| Control: ruta inexistente | `404` | `404` | `404` |

```
NEW_IMAGE_RUNNING
```

Frontend, por un activo estático público:

```
profile.passwordMinLength = "Mínimo 8 caracteres"     (era «Mínimo 6», Wave 2.5)
profile.currentPasswordRequired: presente             (clave nueva de la Wave 2.5)
```

Ambas imágenes, backend y frontend, son las del push.

## 6. Watchtower

**`NOT_VERIFIED`** — sus registros requieren acceso al servidor.

Se infiere que detectó y recreó el backend, porque la imagen en ejecución es la nueva y
`pull_policy: always` con Watchtower es el único mecanismo configurado para lograrlo. No
se dispone de la hora exacta ni de la traza de la actualización.

## 7. `R-58` — el entrypoint

**Evidencia indirecta, y es concluyente en un sentido:**

En la imagen nueva, `ENTRYPOINT` es `docker-entrypoint.sh`, y `uvicorn` solo se alcanza
por su `exec` final. Con `set -e`, ese `exec` es inalcanzable si `alembic upgrade head`
devuelve algo distinto de cero.

**El backend está sirviendo peticiones.** Por tanto:

| Eslabón | Estado | Base |
|---|---|---|
| La imagen contiene el entrypoint | **PASS** | necesario para que exista `ENTRYPOINT` |
| `ENTRYPOINT` cableado | **PASS** | ídem |
| El usuario `avicola` lo ejecuta | **PASS** | el contenedor corre como `avicola` y arrancó |
| Etapa de migración ejecutada | **PASS** | `set -e`: sin ella no hay `exec` |
| `uvicorn` arrancado | **PASS** | responde `401`/`200` en `/api/v1` |

Lo que **no** se tiene es la lectura directa de `docker logs`, que mostraría los mensajes
`Starting database migrations` / `Migration completed`. La inferencia es sólida pero no
sustituye a la evidencia de la capa Docker que `R-58` pide.

```
R-58 = PASS_BY_INFERENCE   (no PASS_BY_LOG_EVIDENCE)
```

## 8. Estado de la base de datos

```
Revisión Alembic leída directamente ... NO ACCESIBLE
Revisión inferida .................... l2m3n4o5p6q7
```

La inferencia se apoya en lo mismo que §7: la aplicación no estaría sirviendo si
`alembic upgrade head` hubiera fallado. Como la cadena termina en `l2m3n4o5p6q7`, las tres
migraciones se aplicaron:

| Revisión | Propósito | Estado inferido |
|---|---|---|
| `j0k1l2m3n4o5` | `EGG_RECEPTION_CLASSIFICATION` → `eventtype` (`R-40`) | aplicada |
| `k1l2m3n4o5p6` | `HATCHERY` → `birdtypeenum` (`R-41`) | aplicada |
| `l2m3n4o5p6q7` | reconciliación de permisos (`R-44`) | aplicada |

**Ninguna verificada por consulta.** `R-40` y `R-41` requerirían leer `pg_enum`; `R-44`,
leer `permissions`.

## 9. `R-44` — el riesgo residual principal

La migración se ejecutó (forma parte de la cadena). Lo que **no** puede comprobarse desde
aquí es su **efecto**: si los roles de producción se llaman exactamente como los que la
migración busca por nombre, las asociaciones se añadieron; si alguno fue renombrado, la
migración lo omite sin fallar —así está escrita, a propósito— y ese rol se quedaría sin
`masters:read`.

Comprobarlo exige entrar con una cuenta real que no sea Super Admin, y esta sesión no
dispone de credenciales de producción. Buscarlas sería exactamente lo que §6 prohíbe.

```
R-44 PRODUCTION STATE = NOT_VERIFIED
```

## 10. `R-52` — volumen de evidencias

```
R-52 CURRENT STATE = PENDING  (presunción fuerte, no verificada)
```

Watchtower recrea el contenedor a partir de la definición con la que se creó, y **no
vuelve a leer el fichero compose**. El volumen `avicola-media` se declaró en la Wave 1 y
nunca se aplicó con `docker compose up -d`. No hay motivo para que esté montado, y no
puede confirmarse sin `docker inspect`.

Consecuencia: **`GA-REM-009` no está productivamente activa.** Las evidencias que se
suban seguirán perdiéndose al recrear el contenedor.

## 11. Posición de la copia de seguridad

```
MIGRATIONS ALREADY EXECUTED ........... SÍ (inferido)
PRE-MIGRATION BACKUP OPPORTUNITY ...... PERDIDA
```

Las tres migraciones son `FORWARD_ONLY`. Se aplicaron durante el arranque automático que
siguió al push, **sin copia previa**, porque el gate de respaldo (`GA-TD-040`) sigue
abierto y esta sesión nunca tuvo capacidad de cerrarlo.

Cualquier copia que se haga a partir de ahora es una **`CURRENT_STATE_BACKUP`**, no un
punto de retorno anterior a la migración. No se la puede llamar de otro modo.

```
DEPLOYMENT OCCURRED UNDER EX-01 WITHOUT FORMAL BACKUP GATE
```

Es un hecho, y así queda registrado. No se han modificado informes anteriores para
sugerir que el gate se cumplió.
