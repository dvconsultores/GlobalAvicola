# GA · PRE-SAP — T13 · RECONCILIACIÓN DE GATES DE HOST (Owner Decision final)

Fecha: 2026-09-16 · Autoridad: Owner Decision — Certificación final autónoma
(`GA_OWNER_DECISION_FINAL_AUTONOMOUS_CERTIFICATION.md`) · Topología declarada:
`DEPLOYMENT_TOPOLOGY = SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME` ·
`HOST_INSPECTION_GATE = NOT_APPLICABLE_BY_OWNER_DECISION`.

Estados permitidos: `PASS` · `NOT_APPLICABLE_BY_OWNER_DECISION` · `FAIL`.
Sin `BLOCKED_EXTERNAL` por ausencia de administrador.

## G-02 · Volumen `avicola-media` (persistencia de evidencias)

| Campo | Detalle |
|---|---|
| Requisito pretendido | Evidencias/productos persisten a través de recreaciones del contenedor (R-52 / GA-REM-009). |
| Demostrable desde | repositorio · compose · app · tests |
| Comprobaciones ejecutadas (16-sep-2026) | `docker-compose.yml:31-32` declara `MEDIA_DIR:${MEDIA_DIR:-/app/media}` y `SAP_EXPORT_DIR`; `:43` monta `avicola-media:/app/media`; `:114` declara el volumen. `backend/app/operations/router.py:20` usa `MEDIA_DIR` y escribe evidencias en `MEDIA_DIR/evidences/<empresa>/<evento>` (`:382`). Tests reales que ejercitan el contrato de evidencias con `MEDIA_DIR`: `test_grandparent_import.py`, `test_operations_bu_enforcement.py`, `test_od14_productive_surfaces.py`, `test_lots_bu_enforcement.py`. Docker: un volumen **nombrado** sobrevive a la recreación del contenedor por diseño. |
| Clasificación | **PASS** (contrato explícito + pruebas suficientes). |
| Parte administrativa | El «archivo testigo + recreación en servidor» (procedimiento manual de host) = `NOT_APPLICABLE_BY_OWNER_DECISION`: con la topología declarada el host sólo ejecuta el artefacto y no se exige evidencia administrativa. |

## G-03 · Rate limit del login (runtime)

| Campo | Detalle |
|---|---|
| Requisito | Con el artefacto desplegado y sin activación manual: intentos 1–5 = 401 y 6.º = 429 (`5/minute`) desde la misma IP. |
| Estado inicial (pre-fix) | `FAIL_OBSERVED` — 12×401 sin 429 (19:30Z y siguientes). |
| Causa raíz | El decorador `rate_limit()` es no-op si el flag no está activo; el contenedor desplegado heredaba del servidor `ENVIRONMENT=development` y `FEATURE_RATE_LIMIT_ENABLED=false` (clonados en cada recreación; Watchtower no relee el compose). |
| Resolución (sin intervención manual, en el artefacto) | 3 iteraciones: (1) `config.py` default `true` (`0b5cc46`); (2) entornos no-dev siempre ON (`8fb9a4f`); (3) **fuerza-en-contenedor determinista** (`d122e04`): dentro de un contenedor (`.dockerenv`) el limitador está **SIEMPRE activo**; `GA_TEST_ENV=1` conserva el control para suites locales; fuera de contenedor, dev/test respetan el flag. |
| Cadena ejecutada | SPEC 14.1 → RED (cause-exacto en cada iteración) → IMPL → GREEN (5/5) → sensibilidad con mutación + restauración desde SHA explícito → commit → push → workflow → imagen → runtime. |
| Trazabilidad del deploy final | `SOURCE_COMMIT = d122e04de36c0a45056b8811040c245e50037dc4` · `WORKFLOW_RUN = 35142848385` (`Docker Push — Backend`, push, `success`, 19:49:14Z) · `IMAGE_TAG = latest` (+ `sha-d122e04`) · `IMAGE_DIGEST = sha256:5c4824bd0c3d2bca887c77f561318e096762f0b520d70115fb45064de54cd219` (19:49:48Z) · `RUNTIME_EVIDENCE` = 19:52:55Z: `401,401,401,401,401,429` (7.º también 429). |
| Clasificación | **PASS** (runtime verificado). |

## G-04 · Rol PostgreSQL mínimo + SSL

| Campo | Detalle |
|---|---|
| Requisito pretendido | Sustituir rol superusuario por rol de aplicación con privilegios mínimos y transporte cifrado (GA-REM-004 AC07). |
| Demostrable desde el artefacto | Parcial: la app no exige privilegios peligrosos (sus operaciones son DML y DDL de migraciones). Rehearsal local real (16-sep): rol `avicola_app` con `USAGE` + DML funciona (`SELECT lots` OK, 78 filas) y no puede `CREATE ROLE` (`usesuper=f`). |
| Parte no demostrable desde el artefacto | El rol/SSL viven en el PostgreSQL externo al artefacto versionado (credencial en `.env` del servidor); su inspección es operación administrativa. |
| Clasificación | **NOT_APPLICABLE_BY_OWNER_DECISION** — justificación: control diseñado para inspección administrativa del servidor de BD; con `SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME` no forma parte del modelo certificado. El contrato del artefacto (no requerir superusuario) queda verificado por rehearsal. |

## G-05 · Respaldo comprobado + política de recuperación

| Campo | Detalle |
|---|---|
| Requisito | Mecanismo de respaldo + **restauración comprobada** + política de recuperación (P1-6). |
| Comprobaciones ejecutadas | Rehearsal real (16-sep, `g05-local-rehearsal.log`): `pg_dump -Fc` (328.748 bytes) → `pg_restore` a base scratch → conteos idénticos original/restaurada: `lots=78`, `operational_events=179`, `audit_logs=1269`. Mecanismo estándar PostgreSQL sobre el esquema certificado (migraciones, cabeza única). Política escrita: `GA_T13_BACKUP_POLICY.md`. |
| Clasificación | **PASS** (mecanismo y restauración demostrados; política documentada). La programación/ejecución periódica en el servidor = `NOT_APPLICABLE_BY_OWNER_DECISION` (operación administrativa fuera de la topología declarada). |

## Cierre

```
HOST_ADMIN_DEPENDENCY       = REMOVED_BY_OWNER_DECISION
HOST_INSPECTION_GATE        = NOT_APPLICABLE_BY_OWNER_DECISION
G-02 = PASS   G-03 = PASS   G-04 = N/A-BY-OWNER-DECISION   G-05 = PASS
DEPLOYMENT_GATE             = PASS
  (todos los requisitos que continúan aplicables están satisfechos; los
   controles exclusivos de administración quedan N/A con justificación)
HOST_DEPLOYMENT_EVIDENCE    = COMPLETE_UNDER_DECLARED_TOPOLOGY
  (runs, digests, bundle, probes de runtime y contratos de repositorio;
   no se exige evidencia administrativa del servidor)
```
