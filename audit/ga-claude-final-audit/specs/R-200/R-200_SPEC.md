# R-200 · SPEC — SÓLO UN ACCESS TOKEN AUTENTICA UNA PETICIÓN

| Campo | Valor |
|---|---|
| **ID** | `R-200` · `SECURITY REMEDIATION SPEC` · P2 · `SPEC_READY` |
| **Decisiones que preserva** | `OD-11` (empresa efectiva por petición) · `OD-14` · `GA-REM-003 §Alcance 1` («el token transporta identidad, no autoridad») |
| **Dependencias** | ninguna; `GA-REM-003 AC04` (logout/denylist) sigue abierta y **no** es prerrequisito |
| **Vecinos** | `R-199` (sesión: `is_super_admin`), `R-202` (contraseña) |
| **GA-REM** | sin asignar (siguiente libre `GA-REM-043`) |

---

## 1. Contexto

`GA-REM-003` fijó que el contexto de autorización se resuelve por petición desde la base y que el token transporta identidad. Dejó abiertos logout y revocación (AC04). Lo que ninguna spec fijó es que **sólo el token de acceso** puede presentar esa identidad en una ruta protegida: hoy el refresh —siete días, almacenado en el cliente— vale lo mismo que el access.

## 2. Evidencia

`R-200_FINDING.md §2-3`: `security.py:59-65` (`decode_token` sin `type`), `:87-93` (`get_current_user` sólo `sub`), `:48-56` (refresh a 7 d con los mismos claims), `service.py:241-247` (la renovación sí discrimina). Sin test del cruce.

## 3. Causa raíz

La marca `type` se escribe al emitir (`security.py:44`, `:55`) y se lee en un solo consumidor (`service.py:243`). La dependencia de autenticación se escribió antes de que existieran dos tipos y nunca incorporó la comprobación. Es una omisión de simetría, no un defecto de diseño.

## 4. Impacto de negocio

- La expiración de 30 minutos del access es ilusoria: la ventana real de una credencial comprometida es de 7 días.
- Un cambio de contraseña tras sospecha de compromiso (`GA-REM-012`) no cierra la ventana (`test_t012_08` + esta brecha).
- Compromete la compuerta «Sesión» del informe final de seguridad y la condición 2 de re-evaluación (§6.3).

## 5. Comportamiento actual

| Petición | Token presentado | HEAD |
|---|---|---|
| cualquier ruta protegida | access válido | `200` |
| cualquier ruta protegida | **refresh** válido | **`200`** |
| cualquier ruta protegida | JWT firmado sin `type` | **`200`** |
| `POST /refresh` | access | `401` (`test_r43_un_refresco_invalido_se_rechaza`) |
| `POST /refresh` | refresh | `200` |

## 6. Comportamiento esperado

```
get_current_user   payload["type"] == "access"   → continúa
                   cualquier otro valor o ausente → 401 «Token inválido: no es un token de acceso»
refresh_token      sin cambio (exige "refresh")
Emisión            sin cambio: access 30 min · refresh 7 d · mismos claims
Cliente            sin cambio: el interceptor ya adjunta sólo el access
```

La comprobación va **antes** de tocar la base: un token del tipo equivocado no debe producir ninguna consulta ni fijar `set_current_audit_user`.

## 7. Alcance

1. Comprobación de `type == "access"` en `get_current_user` (o en `decode_token` con parámetro `tipo_esperado`, a elección del implementador, `C-02`).
2. Pruebas RED→GREEN del cruce y controles de no regresión del flujo de renovación.
3. Documentación de la interacción con `GA-REM-003` en el registro y en el backlog (nota de alcance, no cierre).
4. Sonda runtime no destructiva.

## 8. Fuera de alcance

- Logout, rotación del refresh, denylist/`jti`, revocación al cambiar contraseña: `GA-REM-003 AC04` (sigue abierta; se referencia).
- Reducir la vida del refresh (7 d) o mover su almacenamiento en el cliente: decisión de producto fuera de esta corrección (`C-04`).
- `iss`/`aud`: aceptable para un solo emisor (informe D §D.9).

## 9. Impacto frontend

**Ninguno.** `api.ts:46-52` adjunta sólo el access; el refresh viaja exclusivamente a `/refresh` (`api.ts:37`, `auth.service.ts:39-40`). Si por cualquier defecto futuro el cliente presentara el refresh como Bearer, recibiría `401`, el interceptor intentaría renovar (`api.ts:55-66`) y continuaría con un access legítimo: degradación segura. Sin cambios de i18n ni de bundle.

## 10. Impacto backend

| Fichero | Cambio |
|---|---|
| `backend/app/auth/security.py:87-93` | tras `payload = decode_token(...)`: `if payload.get("type") != "access": raise HTTPException(401, "Token inválido: no es un token de acceso")`, **antes** de leer `sub` y de consultar la base |
| (alternativa `C-02`) `decode_token(token, *, tipo_esperado: str | None = None)` | comprobación centralizada; `refresh_token` pasaría `tipo_esperado="refresh"` y podría retirar su `if` propio |

Sin migración, sin endpoint, sin permiso nuevo, sin cambio de claims.

## 11. Contrato frontend↔backend

| Ruta | Token | Antes | Después |
|---|---|---|---|
| toda ruta autenticada | refresh como Bearer | `200` | `401` `{"detail": "Token inválido: no es un token de acceso"}` |
| toda ruta autenticada | JWT sin `type` | `200` | `401` |
| toda ruta autenticada | access | `200` | `200` (sin cambio) |
| `POST /api/v1/refresh` | refresh | `200` | `200` (sin cambio) |
| `POST /api/v1/login`, `/refresh`, `/switch-company` | emisión | sin cambio | sin cambio |

## 12. Impacto en datos

Ninguno. No hay tabla nueva; no se toca `audit_logs`.

## 13. Seguridad

Cierra `GAP-03`. Restaura la frontera temporal del access (30 min). No cierra `GAP-09`/`GA-REM-003 AC04`: un refresh robado sigue **renovando** durante 7 días; lo que deja de poder es **autenticar directamente**. Un token con `type` alterado exige re-firmar, imposible sin la clave (`JWT_SECRET_KEY` obligatoria, `config.py:46-58`).

## 14. Inquilino

Sin cambio: la empresa efectiva se sigue resolviendo en `resolver_empresa_efectiva` (`tenancy.py:258-307`) a partir del access.

## 15. Unidad de negocio

Sin cambio.

## 16. RBAC

Sin cambio: `require_permission` sigue apoyándose en `get_current_user`; un refresh como Bearer produce `401` (no autenticado), nunca `403`.

## 17. Transacciones

Sin cambio: el `401` se lanza antes de cualquier consulta; `RutaTransaccional` hace rollback de una transacción vacía.

## 18. Auditoría

Sin asiento nuevo: un intento con el tipo equivocado no identifica al usuario de forma fiable (`R-83`: sin empresa no hay asiento) y, siendo `401`, sigue la política de los tokens inválidos (no se auditan). Se registra en el log de aplicación a nivel `WARNING` sin volcar el token (`C-03`).

## 19. i18n

Sin claves nuevas; el `detail` es ES como el resto de mensajes de `security.py`.

## 20. Escritorio

Sin cambio visible. Sesión web: `sessionStorage`.

## 21. Móvil

Sin cambio visible. Telegram Mini App: `localStorage` (`auth.store.ts:62`); el flujo de renovación se conserva (`GA-REM-003 AC07`).

## 22. Manejo de errores (400/401/403/404/409/422)

| Código | Cuándo |
|---|---|
| `401` | token del tipo equivocado o sin `type` (nuevo); expirado / firma inválida / sin `sub` / usuario inactivo (existentes) |
| `400`, `403`, `404`, `409`, `422` | no aplican a esta corrección |

## 23. Impacto de migración

Ninguna.

## 24. Impacto SAP

Ninguno directo. Cierra una vía de sesión prolongada sobre `sap:*`.

## 25. Compatibilidad hacia atrás

- Todos los access tokens emitidos por el producto llevan `type: "access"` desde su origen (`security.py:44`): ninguna sesión legítima viva se invalida.
- Tokens de pruebas: `create_access_token(data=...)` (usado en ~30 ficheros de `tests/`) emite `type` → compatibles.
- Un cliente que hubiera guardado el refresh en lugar del access (no ocurre en el bundle actual) recibiría `401` y reautenticaría.

## 26. Criterios de aceptación

| AC | Enunciado |
|---|---|
| **AC01** | Given un refresh token válido · When se presenta como `Bearer` en `GET /api/v1/me` · Then `401` con el `detail` acordado y sin consulta de usuario |
| **AC02** | Given un refresh token válido de un super admin · When `GET /api/v1/users` · Then `401` (no `200`, no `403`) |
| **AC03** | Given un JWT firmado con la clave del producto pero sin claim `type` · When cualquier ruta protegida · Then `401` |
| **AC04** | Given un JWT firmado con `type: "otro"` · Then `401` |
| **AC05** | CONTROL: el access token emitido por `login` sigue autenticando (`/me` `200`) |
| **AC06** | CONTROL: `POST /refresh` con refresh → nuevo par; el nuevo access autentica; el flujo de `test_r43_la_sesion_continua_con_el_acceso_caducado` sigue verde |
| **AC07** | CONTROL: `POST /refresh` con un access sigue siendo `401` (`test_r43_un_refresco_invalido_se_rechaza`) |
| **AC08** | CONTROL: `switch-company` emite un access que autentica y un refresh que renueva conservando el contexto (`test_el_contexto_sobrevive_a_la_renovacion`) |
| **AC09** | El `401` de AC01…AC04 no deja asiento en `audit_logs` ni fija el usuario de auditoría de la petición |
| **AC10** | Documental: `exp(access) − iat ≈ 30 min` y `exp(refresh) − iat ≈ 7 d` según `config.py:48-49` (prueba que fija la ventana para que un cambio futuro sea visible) |
| **AC11** | Regresión: `test_security_regression.py`, `test_rbac.py`, `test_auth.py`, `test_session_payload.py`, `test_multicompany_isolation.py` en verde; suite completa PG sin rojos nuevos |
| **AC12** | Sin migración, sin endpoint, sin permiso, 0 ficheros FE |
| **AC13** | Registro y backlog: nota explícita «`R-200` no cierra `GA-REM-003 AC04`» |
| **AC14** | Sensibilidad: quitar la comprobación rompe AC01…AC04 |

## 27. Pruebas RED→GREEN

`backend/tests/test_r200_refresh_token_as_access.py` (`R-200_RED_E2E_UAT_DESIGN.md §1`): RED-01…RED-04 rojas en HEAD; CTL-05…CTL-08 y DOC-10 verdes antes y después. Con `client` (login real vía `test_credentials`) y `http_client` para códigos.

## 28. E2E

Sonda runtime no destructiva (§2 del diseño): login con el actor UAT-09 → `GET /me` con el refresh como Bearer → `401`; con el access → `200`; renovación → `200`; Playwright: la suite `e2e/` existente de sesión (login → navegación) sin cambios.

## 29. UAT

**NO REQUERIDA.** Corrección backend-only; ningún flujo de usuario cambia (login, renovación automática, cambio de empresa y Mini App se conservan; AC05…AC08 lo demuestran).

## 30. Criterios de cierre

- [ ] C1: paquete + RED (4 rojas, 5 controles) sin producto.
- [ ] C2: implementación (una comprobación) · GREEN dirigido 10/10 · suite completa PG sin rojos nuevos · `vitest`/`tsc`/`build` sin cambios (0 FE).
- [ ] C2s: sensibilidad M1 rompe RED-01…04.
- [ ] C3: despliegue · E2E-01…04 · evidencia · `GA_CLAUDE_R200_RUNTIME_CERTIFICATION.md` · nota AC13 en registro y backlog.
- [ ] `C-02`…`C-04` resueltas o por defecto.
