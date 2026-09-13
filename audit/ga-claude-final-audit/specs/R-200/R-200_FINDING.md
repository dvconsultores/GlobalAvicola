# R-200 · REGISTRO DE HALLAZGO — EL REFRESH TOKEN (7 DÍAS) AUTENTICA COMO ACCESS TOKEN

| Campo | Valor |
|---|---|
| **ID canónico** | `R-200` (registro §0; máximo previo `R-189`) |
| **Título** | `get_current_user` no comprueba `type == "access"`: un refresh token —válido 7 días y almacenado en el cliente— sirve como `Bearer` en cualquier ruta protegida, vaciando la expiración de 30 minutos del access token |
| **Clase (§9)** | `SECURITY` · sesión / ciclo de vida del token |
| **Prioridad** | **P2** (control de sesión débil; se agrava con la ausencia de logout/rotación de `GA-REM-003`) |
| **Origen** | `GAP-03` del informe `D_security_tx.md` (§D.4, tabla de candidatos); informe final de seguridad §3.10 «Autenticación y sesión — FAIL» |
| **Procesos** | transversal (toda ruta autenticada) |
| **Bloquea SAP** | **SÍ** (sesión: compuerta «Sesión» = PARTIAL; condición 2 de re-evaluación del informe final §6.3) |
| **Auditoría** | GA-CLAUDE final pre-SAP · 2026-09-13 · HEAD `c0b4afc` · runtime no sondado (sonda diseñada en C3, no destructiva) |
| **Estado** | `SPEC_READY` · sin código · sin `GA-REM` asignado (siguiente libre `GA-REM-043`) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-200/` (completo, 6 ficheros) |

## 1. Descripción

El producto emite dos tokens firmados con la misma clave y el mismo algoritmo: el **access** (`type: "access"`, 30 min, `config.py:48`) y el **refresh** (`type: "refresh"`, 7 días, `config.py:49`). La ruta de renovación sí exige `type == "refresh"` (`auth/service.py:243-247`), pero la dependencia de autenticación **no exige `type == "access"`**: `decode_token` (`security.py:59-65`) sólo verifica firma y expiración, y `get_current_user` (`:87-93`) sólo lee `sub`. Cualquier refresh token es, por tanto, un access token de siete días.

El cliente conserva el refresh en `sessionStorage` (web) o `localStorage` (Telegram Mini App) (`frontend/src/stores/auth.store.ts:60-69,104-106`). Combinado con la ausencia de logout, rotación y denylist (`GA-REM-003` AC04, abierta; `GAP-09`), una credencial exfiltrada autentica hasta siete días sin que el cambio de contraseña la invalide (`test_p013_password.py::test_t012_08`, comportamiento documentado).

## 2. Evidencia de código (HEAD `c0b4afc`)

| # | Sitio | Contenido | Hueco |
|---|---|---|---|
| E1 | `backend/app/auth/security.py:34-45` `create_access_token` | `to_encode.update({"exp": expire, "type": "access"})` | la marca de tipo **existe** desde el origen |
| E2 | `backend/app/auth/security.py:48-56` `create_refresh_token` | `{"exp": +7 d, "type": "refresh"}`; mismos claims (`sub`, `username`, `company_id`, `role_id`, `view_type`) que el access (`_claims_de`, `service.py:24-41`) | el refresh es, en contenido, un access de larga vida |
| E3 | `backend/app/auth/security.py:59-65` `decode_token` | `jwt.decode(token, key, algorithms=[…])`; sólo `ExpiredSignatureError`/`InvalidTokenError` | no discrimina `type` |
| E4 | `backend/app/auth/security.py:87-93` `get_current_user` | `payload = decode_token(...)`; `user_id_str = payload.get("sub")` | no lee `type`; cualquier token firmado con `sub` autentica |
| E5 | `backend/app/auth/service.py:241-247` `refresh_token` | `if payload.get("type") != "refresh": 401` | la asimetría existe sólo en un sentido |
| E6 | `backend/app/config.py:48-49` | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7` | ventana real = 7 días |
| E7 | `frontend/src/services/api.ts:46-52,55-73` | el interceptor de petición adjunta **sólo** el access; el refresh viaja únicamente a `POST /api/v1/refresh` | el cliente legítimo nunca usa el refresh como Bearer ⇒ la corrección es transparente |
| E8 | `frontend/src/stores/auth.store.ts:60-69,104-106,135-138` | `tokenStorage` = `sessionStorage` (web) / `localStorage` (TMA); `logout()` sólo borra el almacén local | sin revocación en servidor (`GA-REM-003`) |

## 3. Reproducción (fija la RED)

```
1. POST /api/v1/login {username, password}  → {access_token, refresh_token}
2. GET  /api/v1/me  Authorization: Bearer <refresh_token>
   HEAD: 200 (identidad completa)          esperado: 401 «Token inválido: no es un token de acceso»
3. GET  /api/v1/users (super admin) con el refresh como Bearer
   HEAD: 200                                esperado: 401
4. Token firmado sin claim `type` (jwt.encode({"sub": id, "exp": …}))
   HEAD: 200                                esperado: 401
```

## 4. Cobertura de pruebas existente

| Prueba | Cubre | No cubre |
|---|---|---|
| `tests/test_security_regression.py::test_r43_un_refresco_invalido_se_rechaza` | `POST /refresh` con un access token → `401` | el sentido inverso |
| `tests/test_security_regression.py::test_r43_la_sesion_continua_con_el_acceso_caducado` | flujo access caducado → refresh → nuevo access | — |
| `tests/test_rbac.py::test_ga_rem_003_el_refresco_conserva_el_contexto`, `test_ga_rem_003b_*` | claims tras renovar | — |
| `tests/test_multicompany_isolation.py::test_el_contexto_sobrevive_a_la_renovacion` | contexto del super admin tras renovar | — |
| grep `Bearer.*refresh` en `tests/` | — | **NO TEST** del cruce de tipos (informe D §D.4) |

## 5. Deduplicación (§48)

| Registro | Relación | Conclusión |
|---|---|---|
| `GA-REM-003` (`P1-4`, `S-02`, `S-06`; AC04 logout **abierta**) | logout/rotación/revocación; claims completos en la renovación (cerrado) | registra la **falta de revocación**, no el cruce de tipos; sigue abierta y **no se cierra aquí** |
| `R-43` (cerrado) | `sub` como cadena en la renovación | vecino de fichero, distinta regla |
| `R-54` (cerrado) | contexto de empresa conservado al renovar | sin relación |
| `GA-REM-012` / `P0-13` | cambio de contraseña; `test_t012_08` documenta que las sesiones previas viven | consecuencia agravada por esta brecha; no la duplica |
| `GAP-09` (informe D) | = `GA-REM-003` | vecino |
| backlog (grep `refresh.*access`, `type ==`) | vacío | **NUEVO** |

## 6. Veredicto

`NUEVO` · `P2` · `BLOQUEA` (sesión) · backend-only · corrección trivial (una comprobación) · sin migración · paquete completo. Interacción documentada con `GA-REM-003`: esta spec restaura la frontera de 30 minutos del **access**; la revocación del **refresh** sigue siendo `GA-REM-003 AC04`.
