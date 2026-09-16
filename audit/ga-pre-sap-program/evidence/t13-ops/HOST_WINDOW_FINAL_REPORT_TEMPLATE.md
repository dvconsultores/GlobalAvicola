# GA · T13 · REPORTE DE VENTANA FINAL DE HOST / OPS (plantilla única de entrega)

Ventana: `<fecha/hora inicio> – <fecha/hora fin>` · Operador: `<nombre>` ·
Entorno: `https://avicola.globaldv.net` (SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT).
**Sanitizado**: sin passwords, tokens, private keys ni contenido completo de `.env`.

## Resultado por gate

### G-02 = PASS | FAIL
- Comandos/timestamps/exit codes:
- Evidencia (salidas reales):
- Observaciones:

### G-03 = PASS | FAIL
- FEATURE_RATE_LIMIT_ENABLED antes: `...`
- FEATURE_RATE_LIMIT_ENABLED después: `...`
- RATE_LIMIT_LOGIN efectivo: `...`
- Secuencia HTTP (6 intentos <1 min, `POST /api/v1/login`):
  ```
  1: ...
  2: ...
  3: ...
  4: ...
  5: ...
  6: ...
  ```
- Clave del limiter documentada (GAP-11, X-Forwarded-For / IP real + config del proxy):
- Observaciones:

### G-04 = PASS | FAIL
- Rol efectivo (`current_user`, `usesuper`):
- Conexión SSL (`ssl=require`): resultado
- Evidencia:
- Observaciones:

### G-05 = PASS | FAIL
- BACKUP_REFERENCE / BACKUP_SIZE:
- Restauración demostrada (base scratch) + conteos original vs restaurada:
- Política documentada (frecuencia / retención / RPO-RTO / respaldo antes de upgrade):
- Observaciones:

## Evidencia de deployment

```
DEPLOY_START_TIME:              ...
DEPLOY_END_TIME:                ...
BACKUP_STATUS:                  ...
BACKUP_REFERENCE:               ...
ALEMBIC_BEFORE:                 ...
ALEMBIC_AFTER:                  ...        # esperado: c8d9e0f1a2b3
ENTRYPOINT_MIGRATION_EVIDENCE:  ...        # [entrypoint] Migration completed
CONTAINER_STATUS:               ...        # docker compose ps + RepoDigests
RUNNING_IMAGE_BACKEND_DIGEST:   ...        # contraste: sha256:6f0edbfa…
RUNNING_IMAGE_FRONTEND_DIGEST:  ...        # contraste: sha256:29cd2eff…
BACKEND_HEALTH:                 ...        # :8002/health {"status":"ok",...}
FRONTEND_STATUS:                ...        # / 200; bundle index-*.js servido

HOST_DEPLOYMENT_EVIDENCE = COMPLETE | INCOMPLETE

OBSERVACIONES: ...
```

## Adjuntos (logs sanitizados)
- `...`

---

**Reglas**: no redeploy completo · no tocar frontend · no limpiar/resetear BD · no
borrar volúmenes · no downgrade de Alembic · no imprimir secretos. Si cualquier
paso crítico falla: **DETENERSE y reportar** — no improvisar.
