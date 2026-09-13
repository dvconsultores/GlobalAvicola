# GA-CLAUDE · GA-REM-003 AC04 — CERTIFICACIÓN (logout revoca el refresh)

Fecha: 2026-09-13 · Alcance: **AC04** de `specs/remediation/GA-REM-003-AUTH-CONTEXT-AND-TOKEN-LIFECYCLE.md` («El logout revoca») · Commits: C1 `52d0077` · C2 `80ffd82`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | Backend `red_c1_backend.log` — **4F/3P**: sin `POST /logout` (404), sin idempotencia observable, sin asiento `LOGOUT`, sin `jti` en el refresh; controles verdes (refresh normal, sesiones aisladas, token inválido). FE `red_c1_frontend.log` — **1F/1P**: `logout()` no llamaba al servidor |
| **C2 · Implementación** | ✅ | `green_c2_backend.log` — **28/28** (AC04 7 + `test_rbac` 21) · `green_c2_frontend.log` — **8/8** (GA-REM-003 2 + `auth.store` 6) · **suite FE completa 46/46 archivos, 318/318** · **suite BE completa `1263 passed / 0 failed / 49 skipped`** (`full_suite_c2.log`, 23:43) · commit `80ffd82` + cierre
| **C2s · Sensibilidad** | ✅ S1 | Neutralizar la consulta de revocación en el refresh ⇒ RED-01/03 rojas (`mutations/S1_sin_consulta.log`, 2F/5P); mutación revertida |
| **C3 · Runtime** | ✅ | `runtime-c3.json` (21:23:04 +0200; deploy `Docker Push — Backend` #123 `80ffd82` + Watchtower): logout = **204**; refresh del revocado = **401 «Token revocado»**; control segunda sesión = **200**; control negativo sin sesión = **401 «Token de autenticación requerido»** |

## 2 · Implementación

- **`jti`** en el refresh emitido (`security.py:create_refresh_token`).
- **`revoked_tokens`** (migración `z6a7b8c9d0e1`): `jti` (único), `user_id`, `expires_at` (TTL = expiración del refresh) — denylist por token, purga oportunista en cada inserción. `downgrade()` funcional.
- **`POST /api/v1/logout`** (204, ruta **CORE/de titularidad**): exige sesión y el servicio exige que el `sub` del refresh sea el actor — cerrar sesiones ajenas no es una operación de usuario; además cierra el vector «refresh robado ⇒ logout a distancia». Idempotente y sin oráculo (token irrecuperable ⇒ 204 sin efecto). Auditoría `LOGOUT` con la empresa del dueño del token.
- **`/refresh`** rechaza `jti` revocado ⇒ `401 «Token revocado»`.
- **FE**: `logout()` del store revoca best-effort antes de limpiar (la limpieza local nunca depende de la red).
- **Guardas del repo puestas al día** (rutas nuevas): `authorization_coverage` (titular), `route_scope` (CORE), recuento de tablas del harness (56), cabezas Alembic pineadas (`test_company_catalog t10`, `test_population_invariant ac14` + recuento de rutas 212), clasificador de datos (`revoked_tokens` ⇒ `AUTH_REQUIRED`).

## 3 · AC04 (AC del encargo)

| Paso | Observado (runtime) |
|---|---|
| Sesión con access y refresh válidos | login 200 |
| `POST /api/v1/logout` | **204** |
| El refresh deja de emitir | **401 «Token revocado»** |
| Control: otra sesión del mismo usuario | refresh **200** (revocación por token, no por usuario) |
| Control negativo: sin sesión | **401** (superficie anónima = login/refresh, `AC08b`) |

## 4 · Alcance y límites

- Cierra **AC04** (y la parte LOGOUT de AC06: el asiento queda escrito). **No** cierra AC01/AC02/AC03/AC05/AC06-completo (LOGIN/LOGIN_FAILED/`last_login`) ni AC07: siguen su propio recorrido.
- La ventana del **access** vigente tras el logout sigue ≤ 30 min (documentada en la spec como caso de borde; el refresh —el de 7 días— ya no es canjeable).
- `R-200` sigue sin cubrir AC04 (su nota de alcance queda respondida por esta certificación).

## 5 · Veredicto

**GA-REM-003 AC04 = `CLOSED_FUNCTIONALLY_CERTIFIED`** — RED→GREEN→sensibilidad→runtime completos, con la frontera de titularidad verificada también en runtime.
