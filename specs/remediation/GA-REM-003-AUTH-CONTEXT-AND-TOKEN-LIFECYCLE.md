# GA-REM-003 — CONTEXTO DE AUTORIZACIÓN Y CICLO DE VIDA DEL TOKEN

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-003` · **Tipo** `SECURITY SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · se recomienda coordinar con `GA-REM-002` |
| **Habilita** | `GA-REM-012` |
| **Hallazgos** | P0-4 · S-02 · S-06 · `GA-TD-004` · `GA-TD-022` |
| **Revalidado** | 2026-09-03 — `backend/app/auth/service.py:72` emite `{"sub","username"}`; login emite además `company_id`, `role_id`, `view_type` |

## Problema
El refresh de token **degrada la identidad del usuario**. `refresh_token()` emite un access token con solo `sub` y `username`. El frontend reconstruye el usuario desde los claims y aplica `view_type: claims?.view_type || 'web'`, `company_id: null`, `role_id: null`, perdiendo también `is_super_admin`. Como `fetchMe()` solo se ejecuta cuando `isLoading` es verdadero y `setTokens` no lo restaura, **el usuario degradado persiste hasta recargar la página**.

Efecto: a los 30 minutos, un operador móvil pasa a ser tratado como usuario web y accede a `/users`, `/approvals`, `/sap`, `/audit`, `/review`, `/masters` y `/lots/new`. Sin `GA-REM-002`, esas acciones se ejecutan realmente.

## Evidencia
| Ítem | Ruta |
|---|---|
| Login emite 5 claims | `backend/app/auth/service.py:47-57` |
| Refresh emite 2 claims | `backend/app/auth/service.py:72` |
| Reconstrucción degradada en el cliente | `frontend/src/stores/auth.store.ts:85-101` |
| `fetchMe` no se re-ejecuta | `frontend/src/App.tsx:117-121` |
| Único guard existente | `frontend/src/App.tsx:47-50` (`WebOnlyRoute` por `view_type`) |
| Sin logout ni revocación | inventario de rutas: no existe `POST /logout` |

## Comportamiento actual
- Refresh degrada `view_type` a `'web'`, `company_id` a `null`, `role_id` a `null`, `is_super_admin` a indefinido.
- No existe endpoint de logout ni lista de revocación; un refresh token robado sirve 7 días.
- Desactivar a un usuario corta el acceso en la siguiente validación de `get_current_user`, pero su access token vigente sigue funcionando hasta 30 minutos.
- `last_login` nunca se escribe; login, logout y login fallido **no se auditan** pese a existir `AuditAction.LOGIN/LOGOUT/LOGIN_FAILED`.

## Comportamiento esperado
El contexto de autorización se resuelve **siempre desde fuente confiable (la base de datos)**, no desde claims copiados. El token transporta identidad, no autoridad.

## Alcance
1. Definir la **fuente de verdad** del contexto de autorización: la base de datos por petición, vía `get_current_user`. Los claims son una optimización de presentación, nunca base de decisión.
2. Reponer los claims completos en el refresh, para que el cliente no degrade la sesión.
3. Forzar `fetchMe()` tras `setTokens` para que el estado del cliente se reconcilie con el servidor.
4. Endpoint de logout con revocación efectiva (denylist de `jti` con TTL).
5. Comportamiento ante usuario deshabilitado, rol cambiado y compañía cambiada durante una sesión viva.
6. Auditar `LOGIN`, `LOGOUT`, `LOGIN_FAILED` y escribir `last_login`.

## Fuera de alcance
MFA · recuperación de contraseña · política de complejidad (es `GA-REM-012`) · cambio del algoritmo JWT · SSO.

## Reglas de negocio afectadas
Ninguna del dominio avícola. Afecta al enforcement de todas.

## Backend afectado
`auth/service.py` (refresh, logout, `last_login`), `auth/security.py` (verificación de denylist), `auth/router.py` (`POST /logout`), `audit/helpers.py` (eventos de autenticación). Posible tabla o almacén de revocación.

## Frontend afectado
`stores/auth.store.ts` (reconciliación tras refresh), `services/api.ts` (interceptor), `App.tsx`.

## Base de datos afectada
**Posible**: tabla de tokens revocados (`revoked_tokens`) con `jti`, `user_id`, `expires_at`. Alternativa sin esquema: almacén en memoria con TTL — se descarta por multi-instancia. **Decisión requerida en revisión de spec.** Si se opta por tabla → migración Alembic con docstring citando `GA-REM-003` (Art. 19 de la constitución).

## Seguridad
Cierra `S-02` (P0) y `S-06` (P1). Reduce la ventana de un token comprometido.

## Compatibilidad
Las sesiones activas en el momento del despliegue se degradarán a la nueva lógica en su próximo refresh. Aceptable.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Usuario desactivado con access token vigente | la siguiente petición falla con 401 (ya ocurre); documentar la ventana ≤ 30 min o reducirla |
| Rol cambiado durante la sesión | el permiso se resuelve por petición contra la BD → efecto inmediato |
| Compañía cambiada vía `switch-company` | el nuevo token refleja la compañía; `fetchMe` reconcilia |
| Refresh token reutilizado tras logout | `401`, no emite token nuevo |
| Dos pestañas refrescando a la vez | el interceptor ya protege con `isRefreshing`/`refreshPromise`; verificar que sigue |
| Mini App de Telegram (token en `localStorage`) | mismo comportamiento; la persistencia no cambia la revocación |

## Acceptance Criteria

**AC01 — El refresh conserva la identidad**
```
Given un usuario con view_type="mobile", company_id=2, role_id=3
When  se refresca el token
Then  el nuevo access token contiene view_type="mobile", company_id=2, role_id=3
```
**AC02 — El cliente no degrada la sesión**
```
Given una sesión móvil activa
When  transcurre la expiración y el interceptor refresca automáticamente
Then  el estado del cliente conserva view_type="mobile"
And   las rutas solo-web siguen inaccesibles sin recargar la página
```
**AC03 — La autorización no depende del token**
```
Given un access token manipulado con role_id de un rol superior
When  se usa contra un endpoint protegido
Then  la autorización se resuelve contra la BD y la petición se rechaza
```
**AC04 — El logout revoca**
```
Given una sesión con access token y refresh token válidos
When  el usuario hace POST /api/v1/logout
Then  el refresh token deja de emitir tokens nuevos (401)
```
**Estado (2026-09-13)**: ✅ **CERRADO — `CLOSED_FUNCTIONALLY_CERTIFIED`** — C1 `52d0077` (RED 4F/3P) · C2 `80ffd82` (denylist `jti` + `revoked_tokens` + endpoint de titularidad; sensibilidad S1; runtime: logout 204 → refresh revocado **401 «Token revocado»**; controles 200/401). Certificación: `audit/ga-claude-final-audit/GA_CLAUDE_GA_REM_003_AC04_CERTIFICATION.md`.
**AC05 — Usuario desactivado**
```
Given un usuario desactivado por un administrador
When  intenta refrescar su token
Then  recibe 401 y no obtiene token nuevo
```
**AC06 — Auditoría de autenticación**
```
Given un intento de login correcto, uno fallido y un logout
When  se consulta /api/v1/audit
Then  existe una entrada LOGIN, una LOGIN_FAILED y una LOGOUT
And   el usuario tiene last_login actualizado tras el login correcto
```
**AC07 — Sin regresión en Telegram**
```
Given la aplicación abierta como Telegram Mini App
When  se cierra y se reabre la mini app dentro de la validez del token
Then  la sesión se conserva con su view_type original
```

## Tests requeridos
`T-003-01` claims tras refresh · `T-003-02` estado del cliente tras refresh (vitest sobre `auth.store`) · `T-003-03` token manipulado · `T-003-04` logout revoca · `T-003-05` usuario desactivado · `T-003-06` auditoría de autenticación · `T-003-07` E2E de sesión móvil tras expiración.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| La denylist crece sin control | TTL = expiración del refresh (7 d) + purga programada |
| Multi-instancia con denylist en memoria | se descarta esa opción; decisión explícita en revisión |
| Romper el flujo de la Mini App | AC07 lo cubre con E2E |

## Rollback lógico
Los cambios de claims y de reconciliación son reversibles por commit. Si se introduce tabla de revocación, la migración debe tener `downgrade()` funcional.

## Definition of Done
- [ ] Decisión documentada sobre el almacén de revocación · [ ] AC01–AC07 verificados · [ ] Tests en verde · [ ] Control de regresiones · [ ] Certification report
