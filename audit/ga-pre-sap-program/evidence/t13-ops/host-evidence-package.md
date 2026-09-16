# GA · T13 · HOST EVIDENCE PACKAGE (deployment A) — estado por campo

Fecha: 2026-09-16 (tarde) · Fuente: verificación externa del agente (EXTERNO)
+ pendiente de la ventana de host (PENDIENTE_HOST). Sanitizado (sin secretos).

| Campo (§12 del runbook) | Estado | Valor / observación |
|---|---|---|
| DEPLOY_START_TIME | **EXTERNO** | 2026-09-16T16:28:08Z (runs creados al recibirse el push) |
| DEPLOY_END_TIME | **EXTERNO (aprox.)** | ≤ 16:29:27Z (bundle nuevo ya servido en la 1.ª verificación externa) |
| previous image / digest | **EXTERNO (tags)** | `sha-571b4d5` + `latest` (previas): BE publicada 2026-09-14T12:46Z; FE 2026-09-14T12:47Z |
| deployed image / digest | **EXTERNO** | `sha-f38350a` + `latest`: BE `sha256:6f0edbfa590b62f37e892509d35e6aa110519e99506800575cb37a1d81375817` (16:28:34Z); FE `sha256:29cd2eff0d7d9c9772db432b44bc46efea06b37509eecbf7d6b07add77c2c6a2` (16:28:52Z) |
| Runs (Actions) | **EXTERNO** | `35122083759` (BE) · `35122083928` (FE) — `push`, `success`, 16:28:08Z; job BE 16:28:11→16:28:43Z |
| BACKUP_STATUS / TIMESTAMP / REFERENCE / SIZE | PENDIENTE_HOST | — |
| ALEMBIC_BEFORE / ALEMBIC_AFTER | PENDIENTE_HOST | ALEMBIC_AFTER esperado = `c8d9e0f1a2b3` (head) |
| entrypoint migration evidence | PENDIENTE_HOST | `docker compose logs backend` ⇒ `[entrypoint] Migration completed` |
| container status | PENDIENTE_HOST | `docker compose ps` + `docker inspect` (imágenes/RepoDigests de ambos contenedores) |
| backend health | **EXTERNO (parcial)** | API responde 401 JSON (login); `/health` interno (`:8002`): PENDIENTE_HOST |
| frontend status | **EXTERNO** | `/` = 200; `/login` = 200; bundle `index-r36pBbNX.js` |
| bundle before / after / sha256 | **EXTERNO** | antes `index-apu3WWcr.js` (14-sep) → después `index-r36pBbNX.js`; sha256 `3047f5cdeb9cd9abf9310fd498755109f82e2f7a0e225e6bab1caf99ca9ab6f7` |
| Marcadores GA-FE-01 | **EXTERNO** | M1–M7 presentes (≥1) + control `switch-company` + `cutover-templates` |
| G-02 | PENDIENTE_HOST | runbook §11 (volumen `avicola-media`: testigo + recreación) |
| G-03 | **FAIL observado** | 12×401 sin 429; causa raíz en código documentada; corrección config-only (§14.1) + retest ANTES/DESPUÉS |
| G-04 | PENDIENTE_HOST | runbook §11 (rol mínimo + SSL) |
| G-05 | PENDIENTE_HOST | runbook §11 (respaldo + restauración + política) |

## Checklist mínimo de la ventana de host (para cerrar `DEPLOYMENT_GATE`)

1. **§14.1** — G-03: diagnóstico (`printenv`, compose, `.env`, Config.Env, Cmd),
   corrección config-only, `docker compose up -d backend`, retest ANTES/DESPUÉS
   (esperado `401×5 → 429`), documentar clave del limiter (GAP-11).
2. **§11** — G-02 (volumen), G-04 (rol mínimo + SSL), G-05 (respaldo+restauración+política).
3. **§12** — Campos `PENDIENTE_HOST` de esta tabla (digests de contenedor, entrypoint,
   alembic, health interno, backup) + los solicitados por cada gate.

Al completarse: `HOST_DEPLOYMENT_EVIDENCE = COMPLETE` ⇒ cierre `DEPLOYMENT_GATE`
⇒ re-prevalidación U1/U2 ⇒ `U1/U2 = READY_FOR_OWNER` (STOP OWNER UAT).
