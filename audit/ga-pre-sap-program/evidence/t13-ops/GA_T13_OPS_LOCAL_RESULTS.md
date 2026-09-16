# GA · PRE-SAP — T13 · RESULTADOS DE REHERSALS LOCALES DE OPS

Fecha: 2026-09-16 · Entorno local: **pgserver user-space (sin Docker, sin host)** ·
Runbook canónico: `GA_T13_OPS_RUNBOOK.md` (G-02…G-05) · Evidencia:
`evidence/t13-ops/{g03,g04,g05}-local-rehearsal.log`.

> Regla de honestidad: estos rehersals son **evidencia de ingeniería local**.
> **NO sustituyen** la ejecución de los gates en el host desplegado
> (G-02…G-05 siguen `QUEUED` / `BLOCKED_EXTERNAL` hasta la sesión owner/ops).

## Registro por gate

| GATE | COMANDO (resumen) | START (UTC) | END (UTC) | EXIT | RESULT | EVIDENCE | OBSERVATIONS |
|---|---|---|---|---|---|---|---|
| G-02 volumen `avicola-media` | `docker compose up -d --force-recreate backend` + archivo testigo | — | — | — | **BLOCKED_EXTERNAL** | — | No hay Docker ni acceso al host en la estación del agente. Acción exacta: ejecutar G-02 del runbook en el host (registro de recreación + persistencia del testigo). |
| G-03 rate limit 6→429 | 7× `POST /api/v1/login` con flag `FEATURE_RATE_LIMIT_ENABLED=true` + uvicorn local | 02:12:11 | 02:12:11 | 0 | **PASS (rehersal local)** · gate HOST: BLOCKED_EXTERNAL | `g03-local-rehearsal.log` | Salida observada: **401×5 → 429 en el 6.º** (límite `5/minute` efectivo). Calibración documentada: ruta real `/api/v1/login`; payload inválido (password <6) ⇒ 422 sin contar (la validación precede al limiter). Clave por proxy (GAP-11) sigue pendiente de documentar en host. |
| G-04 rol BD mínimo + SSL | `CREATE ROLE avicola_app` + `GRANT` + verificación efectiva | 02:13:03 | 02:13:47 | 0 | **PASS (rehersal local: rol mínimo)** · SSL: HOST-LEVEL · gate HOST: BLOCKED_EXTERNAL | `g04-local-rehearsal.log` | Verificado: `usesuper = f`; `SELECT lots` OK (78 filas); `CREATE ROLE` denegado («Only roles with CREATEROLE…»). Hallazgo de calibración: los `GRANT` deben ejecutarse **en la base de la aplicación** (como su dueño/admin), no en la base por defecto. `sslmode=require` no evaluable local (pgserver sin TLS compilado) ⇒ parte SSL del gate = host. |
| G-05 respaldo+restauración | `pg_dump -Fc` → `pg_restore` a base scratch → conteos | 02:13:03 | 02:13:05 | 0 | **PASS (rehersal local)** · gate HOST: BLOCKED_EXTERNAL | `g05-local-rehearsal.log` | Ciclo completo OK (dump 328.748 bytes); conteos idénticos original/restaurada: `lots=78`, `operational_events=179`, `audit_logs=1269`. Política de migraciones/backup sigue pendiente de redacción owner/ops. |

## Nota de entorno (transparencia)

- La shell persistente conservó `FEATURE_RATE_LIMIT_ENABLED=true` del rehersal
  G-03 e hizo fallar una primera corrida de prevalidación (17F/12E por límite en
  los fixtures de login). Re-ejecutada con entorno limpio ⇒ **82/82 passed**
  (`u1u2-prevalidation-tests.log`). Sin efecto en producto ni en la suite final
  (los runs de certificación usan procesos de shell nuevos).
- Roles/bases creados en la instancia local de pruebas: rol `avicola_app` (sin
  privilegios), base `restore_check_test`. No tocan producción ni el host.

## Estado consolidado

- **Rehersals locales**: G-03/G-04/G-05 = **PASS** (mecanismo reproducible);
  G-02 = **BLOCKED_EXTERNAL** (requiere host).
- **Gates de host (canónicos)**: G-02…G-05 = **QUEUED / BLOCKED_EXTERNAL** —
  ejecutables por el propietario/ops con el runbook; sin Docker/acceso a host no
  pueden cerrarse desde aquí.
