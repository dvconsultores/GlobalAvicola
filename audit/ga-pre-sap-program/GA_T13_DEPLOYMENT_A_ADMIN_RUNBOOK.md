# GA · PRE-SAP — T13 · RUNBOOK DE DESPLIEGUE A — ADMINISTRADOR DEL HOST

Fecha: 2026-09-16 · Autoridad: decisión del propietario **`DEPLOYMENT = A`**
(2026-09-16; registro `GA_T13_DEPLOYMENT_DECISION_A.md`) · Estado: **ejecutable
por el administrador del host** — el agente no dispone de acceso autorizado
(`DEPLOYMENT_EXECUTION = BLOCKED_EXTERNAL_ACCESS`).

Entorno objetivo: `https://avicola.globaldv.net` — clasificación
**SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT** (NO es producción real; no
usar terminología de producción comercial).

Objetivo: que el runtime sirva **exactamente el producto certificado**
`be5453f`, sin destruir datos, siguiendo el mecanismo canónico del proyecto
(`EX-01`; `audit/remediation/PRODUCTION_ACTIVATION_RUNBOOK.md`).

**Sanitización obligatoria**: nunca pegar DSN, contraseñas, tokens ni contenido
de `.env` en la evidencia (sustituir por `<oculto>`).

## 0 · Identificadores

| Campo | Valor |
|---|---|
| `PRODUCT_CERTIFIED_SHA` | `be5453f` (única revisión con contenido de producto; verificado 2026-09-16) |
| `TARGET_ALEMBIC_HEAD` | `c8d9e0f1a2b3` (cabeza única verificada en el checkout) |
| Entorno | `https://avicola.globaldv.net` (`84.247.161.106`) |
| Baseline actual (externo, 2026-09-16T02:56Z) | bundle `/assets/index-apu3WWcr.js` (`Last-Modified: Mon, 14 Sep 2026 12:47:04 GMT`) |
| Contenedores | `globalavicola-backend` · `globalavicola-frontend` · `globalavicola-telegram-bot` · `watchtower-avicola` |
| Imágenes | `<DOCKER_USERNAME>/globalavicola-backend:latest` · `<DOCKER_USERNAME>/globalavicola-frontend:latest` (valor efectivo del host; por defecto histórico `dvconsultores`) |
| Migraciones | las aplica el **entrypoint** de la imagen al arrancar (`alembic upgrade head`, GA-REM-024). **Nadie más las ejecuta** (ni CI ni operador — doc canónico del proyecto) |

## 1 · Precondiciones (checklist)

1. Acceso autorizado al host (SSH o equivalente) con permiso `docker compose`.
2. Checkout del repositorio disponible en el host (o clonado) para construir desde `be5453f`.
3. Si se usa la ruta canónica de registro (recomendada): credenciales autorizadas de Docker Hub para publicar `<DOCKER_USERNAME>/…`.
4. `docker-compose.yml` del host al día (contiene `avicola-media`, `MEDIA_DIR`, `SAP_EXPORT_DIR`, `MORTALITY_ALERT_*`):

   ```bash
   grep -n "avicola-media\|MEDIA_DIR\|SAP_EXPORT_DIR\|MORTALITY_ALERT" docker-compose.yml
   ```

5. Procedimiento de respaldo disponible y **verificable** (pg_dump en host o cliente equivalente).
6. Ventana acordada (la recreación del backend corta el servicio brevemente).

## 2 · Captura PRE-DEPLOY (ejecutar y guardar salida; sin secretos)

```bash
cd <directorio del docker-compose.yml en el servidor>
date -u +"%Y-%m-%dT%H:%M:%SZ"                            # ⇒ DEPLOY_START_TIME
git -C <checkout> rev-parse HEAD                          # checkout actual del host (si procede)
docker compose ps
docker inspect -f '{{.Image}}' globalavicola-backend globalavicola-frontend   # IDs de imagen ⇒ rollback
docker exec globalavicola-backend alembic current         # ⇒ PRE_DEPLOY_DB_REVISION
docker inspect -f '{{.State.Health.Status}} {{.State.StartedAt}}' globalavicola-backend
curl -s https://avicola.globaldv.net/ | grep -oE 'index-[A-Za-z0-9_-]+\.js' | sort -u
                                                          # ⇒ CURRENT_FRONTEND_BUNDLE (esperado: index-apu3WWcr.js)
curl -fsS http://localhost:8002/health                    # ⇒ CURRENT_HEALTH (esperado {"status":"ok",...})
```

Registrar: `DEPLOY_START_TIME`, IDs de imagen previos (rollback), `PRE_DEPLOY_DB_REVISION`, bundle actual, salud.

> Nota: el `/health` **externo** devuelve el index del SPA (fallback del frontend);
> la salud real del backend se comprueba **en el host** (`:8002/health`).

## 3 · Obtener el código certificado

```bash
cd <checkout del repositorio>
git fetch origin
git checkout be5453f
git rev-parse HEAD        # ⇒ be5453f... (debe coincidir exactamente)
```

Nota: `93b4a91` (HEAD documental posterior) **no** cambia producto — verificado
(`git diff be5453f..93b4a91 -- backend frontend e2e` vacío). **No sustituir el SHA.**

## 4 · Validar migraciones (antes de tocar nada)

```bash
cd <checkout>/backend && <entorno/venv o imagen> alembic heads
# ⇒ una única cabeza: c8d9e0f1a2b3 (head)
```

Si aparece **más de una cabeza** ⇒ **STOP** (no improvisar merge migrations).
Registrar: `TARGET_ALEMBIC_HEAD = c8d9e0f1a2b3`.

## 5 · RESPALDO OBLIGATORIO (STOP si falla)

Antes de recrear el backend (su entrypoint aplicará migraciones), tomar copia y
**verificar que sirve**:

```bash
mkdir -p /backups
pg_dump --format=custom --file=/backups/avicola-preT13-$(date -u +%Y%m%d_%H%M).dump "<DSN>"
pg_restore --list /backups/avicola-preT13-*.dump | head
ls -l /backups/avicola-preT13-*.dump
```

Registrar: `BACKUP_STATUS`, `BACKUP_TIMESTAMP`, `BACKUP_REFERENCE`, `BACKUP_SIZE`.

Si no existe procedimiento autorizado o la copia falla ⇒ **STOP** ⇒
`DEPLOYMENT_STATUS = BLOCKED_BACKUP_SAFETY` (no ejecutar migraciones sin
respaldo verificable). No imprimir el DSN.

## 6 · Build y publicación — dos rutas

### Ruta 1 · Canónica (réplica del CI retirado; requiere credenciales de registro autorizadas)

```bash
cd <checkout>
docker build -t <DOCKER_USERNAME>/globalavicola-backend:be5453f  -t <DOCKER_USERNAME>/globalavicola-backend:latest  ./backend
docker build -t <DOCKER_USERNAME>/globalavicola-frontend:be5453f -t <DOCKER_USERNAME>/globalavicola-frontend:latest ./frontend
docker push <DOCKER_USERNAME>/globalavicola-backend:latest && docker push <DOCKER_USERNAME>/globalavicola-backend:be5453f
docker push <DOCKER_USERNAME>/globalavicola-frontend:latest && docker push <DOCKER_USERNAME>/globalavicola-frontend:be5453f
docker images --digests | grep -E 'globalavicola-(backend|frontend)'   # registrar IDs/digests
```

Los contextos (`./backend`, `./frontend`) y nombres de imagen replican
exactamente los workflows retirados (`docker-push-backend.yml` /
`docker-push-frontend.yml`). Después, **Watchtower detecta `:latest` (≤60 s) y
recrea los contenedores** (mecanismo EX-01); para acortar la ventana:

```bash
docker compose pull backend frontend
docker compose up -d backend frontend
```

> El `telegram-bot` comparte la imagen del backend; Watchtower puede recrearlo
> igualmente (la migración del entrypoint es idempotente). No es un error.

### Ruta 2 · Fallback local (sin publicar en registro)

```bash
cd <checkout>
docker compose config | grep 'image:.*globalavicola'     # ⇒ nombres efectivos (por defecto dvconsultores/...)
docker build -t <NOMBRE_BACKEND_EFECTIVO>  ./backend      # p. ej. dvconsultores/globalavicola-backend:latest
docker build -t <NOMBRE_FRONTEND_EFECTIVO> ./frontend
docker stop watchtower-avicola                            # evitar que un pull de :latest antiguo revierta
printf 'services:\n  backend:\n    pull_policy: never\n  frontend:\n    pull_policy: never\n' > docker-compose.manual.override.yml
docker compose -f docker-compose.yml -f docker-compose.manual.override.yml up -d --force-recreate backend frontend
```

Nota: `pull_policy: never` evita que `up` reponga la imagen antigua de Docker
Hub. Registrar la decisión sobre Watchtower al cierre de la ventana (reactivar
según indique ingeniería).

## 7 · Migración (canónica — entrypoint)

- La ejecución es **automática** al recrear el contenedor (GA-REM-024).
  **No ejecutar `alembic upgrade` manualmente** (el entrypoint es el único
  propietario de las migraciones — doc canónico).
- Verificar:

```bash
docker compose logs --since=15m backend | sed -n '1,60p'
# Esperado: [entrypoint] Starting database migrations → target: <host>/<base>
#           → Migration completed → Starting application: uvicorn ...
docker exec globalavicola-backend alembic current      # ⇒ ALEMBIC_AFTER == c8d9e0f1a2b3 (head)
docker compose ps                                      # ⇒ healthy
```

Si la migración falla: el contenedor **no sirve** (`set -e`;
`restart: unless-stopped` reintenta). No editar la BD manualmente; ir a §10
(rollback) y registrar el error.

## 8 · Health checks post-deploy (A–G)

```bash
# A · Contenedores/servicios activos
docker compose ps

# B · Salud del backend (interna del host)
curl -fsS http://localhost:8002/health          # esperado {"status":"ok",...}

# C · Frontend responde
curl -s -o /dev/null -w '%{http_code}\n' https://avicola.globaldv.net/          # ⇒ 200

# D · Sin errores críticos de arranque
docker compose logs --since=15m backend | grep -iE 'error|traceback' || echo NONE

# E · El bundle cambió respecto al baseline
curl -s https://avicola.globaldv.net/ | grep -oE 'index-[A-Za-z0-9_-]+\.js' | sort -u
# ⇒ distinto de index-apu3WWcr.js

# F · Esquema en cabeza
docker exec globalavicola-backend alembic current        # ⇒ c8d9e0f1a2b3 (head)

# G · Página de acceso
curl -s -o /dev/null -w '%{http_code}\n' https://avicola.globaldv.net/login     # ⇒ 200
```

Registrar: `DEPLOY_END_TIME`, `DEPLOYED_PRODUCT_SHA` (= `be5453f` del checkout),
`BACKEND_HEALTH`, `FRONTEND_STATUS`, `FRONTEND_BUNDLE_HASH` (nombre +
`sha256sum` del bundle), `ALEMBIC_HEAD`, `CONTAINER_STATUS`.
Resultado esperado: **`DEPLOYMENT_STATUS = PASS`**.

## 9 · Verificación de producto desplegado (evidencia combinada)

Sin endpoint de versión runtime: checkout `be5453f` + build desde ese checkout
(timestamps/logs) + bundle nuevo + salud + recreación. Refuerzo con
**marcadores estables GA-FE-01** (presencia ≥ 1 en el bundle servido):

```bash
NB=$(curl -s https://avicola.globaldv.net/ | grep -oE 'index-[A-Za-z0-9_-]+\.js' | head -1)
curl -s "https://avicola.globaldv.net/assets/$NB" -o /tmp/runtime-bundle.js
sha256sum /tmp/runtime-bundle.js
for m in permissions-catalog masters/areas notifications/unread-count weight-curves import_plan dead_on_arrival chicks_healthy switch-company; do
  printf "%-32s %s\n" "$m" "$(grep -c -- "$m" /tmp/runtime-bundle.js)"; done
```

Criterio: M1–M7 (`permissions-catalog` … `chicks_healthy`) presentes (≥1);
`switch-company` = control negativo (presente en ambas generaciones).

## 10 · Rollback (si fallo crítico)

Con lo capturado en §2 (IDs de imagen previos, bundle previo,
`PRE_DEPLOY_DB_REVISION`, respaldo de §5):

```bash
docker stop watchtower-avicola                                  # pausar auto-update durante la reversión
docker tag <PREV_BACKEND_IMAGE_ID>  <NOMBRE_BACKEND_EFECTIVO>
docker tag <PREV_FRONTEND_IMAGE_ID> <NOMBRE_FRONTEND_EFECTIVO>
docker compose up -d --force-recreate --pull never backend frontend
curl -fsS http://localhost:8002/health
curl -s https://avicola.globaldv.net/ | grep -oE 'index-[A-Za-z0-9_-]+\.js' | sort -u   # ⇒ bundle previo
```

- **BD**: no ejecutar `alembic downgrade` automáticamente; si hay que revertir
  esquema/datos ⇒ restaurar el respaldo de §5 (con ingeniería).
- Si se publicó en registro (Ruta 1): republicar/retaggear la imagen previa como
  `:latest` para que Watchtower converja.
- Registrar: hora, motivo, comandos, resultado; reactivar Watchtower según
  indicación de ingeniería.

## 11 · OPS G-02…G-05 (misma ventana si es posible)

Los cuatro gates del `GA_T13_OPS_RUNBOOK.md`, en el host. **Corrección
calibrada (2026-09-16)**: la ruta de login es **`/api/v1/login`** (el runbook
OPS cita `/api/auth/login`, que da 404). G-03:

```bash
for i in $(seq 1 6); do curl -s -o /dev/null -w "intento $i: %{http_code}\n" \
  -X POST https://avicola.globaldv.net/api/v1/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"<usuario-prueba>","password":"<incorrecta>"}'; done
# ⇒ 401 ×5 → 429 (con FEATURE_RATE_LIMIT_ENABLED=true efectivo en el contenedor)
```

- **G-02** (volumen `avicola-media`): puede aprovechar la recreación de este
  despliegue — secuencia del runbook OPS (testigo → recrear → verificar).
- **G-04** (rol mínimo + SSL) y **G-05** (ciclo respaldo/restauración en base
  scratch) según el runbook OPS.
- Registrar por gate: `GATE · COMMAND · RESULT · EXIT_CODE · EVIDENCE ·
  OBSERVATIONS`. No marcar PASS por inspección parcial.

## 12 · Evidencia que debe devolver el administrador

| Campo | Valor |
|---|---|
| `DEPLOY_START_TIME` / `DEPLOY_END_TIME` | |
| `CHECKOUT_SHA` (host) | `be5453f` |
| IDs/digests de imagen PRE y POST (backend/frontend) | |
| `BACKUP_STATUS` / `TIMESTAMP` / `REFERENCE` / `SIZE` | |
| `PRE_DEPLOY_DB_REVISION` / `ALEMBIC_AFTER` | |
| Log de arranque del backend (`[entrypoint] …`) | |
| Health A–G (salidas) | |
| `BUNDLE BEFORE` / `AFTER` + sha256 | |
| Marcadores GA-FE-01 (conteos) | |
| G-02…G-05 (salida por gate) | |
| Incidencias / rollback (si hubo) | |

Todo **sanitizado** (sin DSN, contraseñas ni tokens). Entrega por el canal
autorizado a ingeniería ⇒ verificación ⇒ prevalidación técnica U1/U2 ⇒ **solo
entonces** se abre la sesión del propietario (STOP gate §18 del mandato). El
agente **no** marca aceptaciones.

## 13 · PROHIBIDO

- `docker compose down -v` · borrar volúmenes · resetear/limpiar la BD · tocar datos.
- Ejecutar `alembic upgrade`/`downgrade` a mano (dueño exclusivo: entrypoint).
- Sustituir el SHA sin evidencia · imprimir o registrar secretos.
- Reactivar GitHub Actions por iniciativa del agente (la situación actual se
  reconcilia por decisión del propietario — ver `GA_T13_GHA_AOD29_RECONCILIATION.md`).

## 14 · Adenda (2026-09-16, tarde) — ventana de host: diagnóstico G-03 + evidencia cruda

**Regla**: el producto certificado **ya está desplegado** (verificado externamente).
**NO redeployar** para producir evidencia; solo recrear el servicio necesario para una
corrección real.

### 14.1 · G-03 — diagnóstico y corrección (configuración)

Observado (2026-09-16T16:30Z, 12 intentos externos a `POST /api/v1/login`): **401×12,
sin 429** (esperado 401×5 → 429). Pasos en el host, en el directorio del compose:

```bash
docker compose exec backend printenv FEATURE_RATE_LIMIT_ENABLED   # esperado: true
docker compose exec backend printenv RATE_LIMIT_LOGIN 2>/dev/null || true
grep -n "FEATURE_RATE_LIMIT_ENABLED\|RATE_LIMIT" docker-compose.yml
# (si existe .env del host) grep -n "FEATURE_RATE_LIMIT_ENABLED\|RATE_LIMIT" .env   # sin imprimir otros secretos
docker inspect -f '{{.Config.Env}}' globalavicola-backend | tr ',' '\n' | grep -i "RATE_LIMIT" || echo "sin vars de rate limit en el contenedor"
docker inspect -f '{{.Config.Cmd}}' globalavicola-backend          # confirmar 1 worker (sin --workers)
```

- Si `FEATURE_RATE_LIMIT_ENABLED` está ausente/false: **documentar el valor anterior**,
  añadir/ajustar a `true` **solo en el mecanismo autorizado** (compose o `.env` del host),
  `docker compose up -d --force-recreate backend` (solo backend; **NO tocar BD**), y
  repetir G-03 dos veces: desde el host (`curl localhost:8002`) y desde fuera.
- Evidencia exigida (causa-exacta): **ANTES** = `401×12 / sin 429`; **DESPUÉS** = patrón
  del AC (`401×5 → 429`); + configuración anterior/nueva, comando de recreación,
  timestamps y salidas reales.
- Documentar la **clave del limiter** (GAP-11): `X-Forwarded-For` vs IP real y la
  configuración del proxy.
- Si con `true` efectivo y 1 worker el límite sigue sin dispararse ⇒ **escalar como
  hallazgo técnico** (SPEC→AC→RED→IMPL→GREEN→sensibilidad→regresión): no tocar producto
  en esta ventana.

### 14.2 · Evidencia cruda del deploy (§12) — valores de contraste

| Campo | Valor esperado/observado externamente |
|---|---|
| Runs (Actions) | `35122083759` BE / `35122083928` FE — `push`, `success`, 16:28:08Z |
| Imagen BE `latest` (Docker Hub) | `sha256:6f0edbfa590b62f37e892509d35e6aa110519e99506800575cb37a1d81375817` (16:28:34Z) |
| Imagen FE `latest` (Docker Hub) | `sha256:29cd2eff0d7d9c9772db432b44bc46efea06b37509eecbf7d6b07add77c2c6a2` (16:28:52Z) |
| Contenedores (host) | `docker inspect -f '{{json .Image}}' globalavicola-backend globalavicola-frontend` + `RepoDigests` ⇒ deben corresponder a las imágenes `sha-f38350a` |
| `ALEMBIC_AFTER` | `c8d9e0f1a2b3` (head) — `docker exec globalavicola-backend alembic current` |
| Log entrypoint | `docker compose logs --since=15m backend` ⇒ `[entrypoint] Migration completed` |
| Resto de campos | tabla §12 (BACKUP_*, DEPLOY_START/END, health, digests, bundle before/after, etc.) |

### 14.3 · G-02 / G-04 / G-05

Ejecutar conforme al runbook (§11) en la misma ventana; registrar por gate:
`GATE · COMMAND · TIMESTAMP · EXIT_CODE · RESULT · EVIDENCE · OBSERVATIONS`
(estados: PASS / FAIL / BLOCKED_EXTERNAL).
