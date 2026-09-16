# GA · PRE-SAP — T13 · RUNBOOK OPS (G-02…G-05)

Fecha: 2026-09-16 · Para: propietario/operaciones (host de despliegue) ·
Estado: **instrumentos entregados** — ítems `QUEUED` en
`GA_OWNER_GATE_QUEUE.md`; este runbook los hace **ejecutables sin ambigüedad**.

Reglas: ventana operativa declarada; registrar fecha/hora y comandos exactos;
**sanitizar secretos** en toda evidencia (nunca pegar contraseñas ni DSN
completos; sustituir por `<oculto>`); adjuntar salidas reales, no reconstruidas.

## G-02 · R-52/RES-05 — Volumen `avicola-media` (durabilidad de evidencias)

**Objetivo**: backend recreado **con** el volumen y evidencia que sobrevive a la
recreación (cierra R-52; evita `GA-REM-009` activa).

```bash
# 1) Verificar la declaración en el compose del servidor
grep -n "avicola-media\|MEDIA_DIR" docker-compose.yml

# 2) Archivo testigo ANTES de recrear (dentro del contenedor)
docker compose exec backend sh -lc 'echo testigo-$(date -u +%s) > /app/media/_persistence_check.txt && cat /app/media/_persistence_check.txt'

# 3) Recrear el backend (Watchtower no relee el compose)
docker compose up -d --force-recreate backend

# 4) Verificar montaje y persistencia DESPUÉS
docker inspect -f '{{json .Mounts}}' $(docker compose ps -q backend)
docker compose exec backend sh -lc 'cat /app/media/_persistence_check.txt'
```

**PASS**: el archivo testigo conserva su contenido tras la recreación y el
mount `avicola-media → /app/media` aparece en `docker inspect`.
**Evidencia**: salida de (1), (2), (3), (4) fechada; limpieza del archivo testigo.

## G-03 · GA-REM-004 AC03 — Rate limit en runtime (6→429)

**Objetivo**: con `FEATURE_RATE_LIMIT_ENABLED=true` **efectivo en el
contenedor**, el 6.º intento de login en <1 min desde la misma IP responde 429.

```bash
# 1) Confirmar el flag efectivo del contenedor
docker compose exec backend printenv FEATURE_RATE_LIMIT_ENABLED   # ⇒ true
# (si falta: añadirlo al entorno del servicio, recrear y repetir)

# 2) Seis intentos <1 min (sustituir usuario; NUNCA usar la contraseña real en el registro)
for i in $(seq 1 6); do
  curl -s -o /dev/null -w "intento $i: %{http_code}\n" \
    -X POST https://<host>/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"<usuario-prueba>","password":"<incorrecta>"}'
done
```

**PASS**: intentos 1–5 con 401 y **6.º con 429** (o el umbral documentado si la
política vigente difiere, p. ej. `5/minute` + margen del proxy).
**Nota GAP-11 (clave por proxy)**: documentar con qué clave limita (`X-Forwarded-For`
/ IP real) y la configuración del proxy al respecto.
**Evidencia**: salida de (1) y del bucle fechada + nota GAP-11.

## G-04 · GA-REM-004 AC07 — BD: rol de privilegios mínimos + SSL

**Objetivo**: sustituir el rol superusuario por un rol de aplicación con
privilegios mínimos y exigir transporte cifrado.

```sql
-- 1) Crear el rol de aplicación (sin SUPERUSER/CREATEDB/CREATEROLE)
CREATE ROLE avicola_app LOGIN PASSWORD '<desde-gestor-de-secretos>';
GRANT USAGE ON SCHEMA public TO avicola_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO avicola_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO avicola_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO avicola_app;

-- 2) Verificación de privilegios efectivos (con el nuevo rol)
SELECT current_user, usesuper FROM pg_user WHERE usename = current_user;
-- ⇒ current_user = avicola_app, usesuper = f
```

```bash
# 3) Conexión con SSL obligatorio (añadir sslmode=require a la DSN y recrear)
#    DATABASE_URL=postgresql+asyncpg://avicola_app:<oculto>@<host>:5432/<db>
docker compose exec backend python3 -c \
  "import asyncio,asyncpg,os; \
   print(asyncio.run((lambda: asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg','postgresql'), ssl='require'))().get_server_version()))"
```

**PASS**: rol efectivo `avicola_app` sin `usesuper`; conexión establecida con
`sslmode=require` (el servidor rechaza sin SSL si está forzado en `pg_hba`).
**Evidencia**: consultas de (2) y salida de (3) fechadas (sin secretos).

## G-05 · P1-6 — Respaldo comprobado + política de migraciones

**Objetivo**: ciclo respaldo→restauración **ejecutado y comprobado** + política
escrita.

```bash
# 1) Respaldo comprimido
pg_dump -Fc -d "$DATABASE_URL_SAFE" -f /backups/avicola_$(date -u +%Y%m%d_%H%M).dump

# 2) Restauración en base scratch
createdb avicola_restore_check
pg_restore -d avicola_restore_check /backups/<archivo>.dump

# 3) Comparación de conteos clave (original vs restaurada)
psql -d avicola_restore_check -c "SELECT 'lots', count(*) FROM lots UNION ALL
  SELECT 'operational_events', count(*) FROM operational_events UNION ALL
  SELECT 'audit_logs', count(*) FROM audit_logs;"
```

**PASS**: restauración sin errores y conteos idénticos en las tablas clave.
**Política a documentar**: frecuencia (p. ej. diaria), retención (p. ej. 30 d
+ mensuales), RPO/RTO acordados, **respaldo obligatorio antes de cada
`alembic upgrade`**, y verificación de restauración periódica (trimestral).
**Evidencia**: log del ciclo fechado + conteos + política con firma/fecha.

## Registro de ejecución

| Ítem | Fecha/hora | Operador | Resultado (PASS/FAIL) | Artefactos (nombre + sha256) | Notas |
|---|---|---|---|---|---|
| G-02 | | | | | |
| G-03 | | | | | |
| G-04 | | | | | |
| G-05 | | | | | |

Al completarse los cuatro ítems con evidencia ⇒ Pista OPS **cerrada**;
inventario y veredicto se anexan a la certificación de T13.
