# R-200 · DISEÑO RED · E2E RUNTIME · UAT

## 1. Pruebas RED (backend) — `backend/tests/test_r200_refresh_token_as_access.py`

### 1.1 Fixtures y helpers

- `client`, `http_client`, `test_credentials`, `auth_headers`, `seeded_ids` de `conftest.py`.
- `_par(client, test_credentials) -> (access, refresh)`: `POST /api/v1/login` real.
- `_bearer(token) -> {"Authorization": f"Bearer {token}"}`.
- `_jwt(claims: dict) -> str`: `jwt.encode({**claims, "exp": now+5min}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)` (mismo mecanismo que `security.py`).
- Sin fixture de base propia: se usa el usuario sembrado (`test_admin`).

### 1.2 Casos

| ID | Nombre exacto | Pasos | Aserción que **falla en HEAD** (valor actual) |
|---|---|---|---|
| RED-01 | `test_r200_01_un_refresh_token_no_autentica_una_ruta_protegida` | `access, refresh = _par(...)`; `GET /api/v1/me` con `_bearer(refresh)` | `r.status_code == 401` (HEAD: `200`); `"acceso" in r.json()["detail"].lower()`; (AC09) recuento de `audit_logs` igual antes/después |
| RED-02 | `test_r200_02_un_refresh_token_no_autentica_una_ruta_con_permiso` | `GET /api/v1/users` con `_bearer(refresh)` | `401` (HEAD: `200`); explícitamente `!= 403` |
| RED-03 | `test_r200_03_un_token_firmado_sin_tipo_se_rechaza` | `t = _jwt({"sub": str(seeded_ids["user_admin_id"])})`; `GET /api/v1/me` | `401` (HEAD: `200`) |
| RED-04 | `test_r200_04_un_token_de_tipo_desconocido_se_rechaza` | `_jwt({"sub": ..., "type": "session"})` | `401` (HEAD: `200`) |
| CTL-05 | `test_r200_05_el_access_token_sigue_autenticando` | `GET /me` con `_bearer(access)` | `200`, `username == test_admin` |
| CTL-06 | `test_r200_06_el_flujo_de_renovacion_sigue_intacto` | `POST /refresh {"refresh_token": refresh}` → `nuevo`; `GET /me` con `nuevo["access_token"]` | `200`/`200`; `decode(nuevo["access_token"])["type"] == "access"` |
| CTL-07 | `test_r200_07_un_access_token_sigue_sin_servir_para_refrescar` | `POST /refresh {"refresh_token": access}` | `401` |
| CTL-08 | `test_r200_08_el_par_de_switch_company_sigue_siendo_valido` | super admin: `POST /switch-company {"company_id": seeded_ids["company_id"]}` → par; `/me` con access → `200`; `/refresh` con refresh → `200` | ambos verdes |
| DOC-10 | `test_r200_10_las_ventanas_de_los_dos_tokens_quedan_fijadas` | decodificar ambos sin verificar `exp`; `exp - now` | `≈ 30 min` (`±2`) y `≈ 7 d` (`±1 h`) según `settings` |

### 1.3 Verificación de la RED

Ejecutar antes del commit C1: RED-01…04 fallan en `status_code == 401` con `200` observado; CTL/DOC pasan. Salida a `evidence/r200/red_c1.log`.

## 2. E2E runtime (C3) — sondas no destructivas

Actor: UAT-09 (empresa 1). Ninguna sonda escribe.

| ID | Sonda | Esperado post-fix | Pre-fix |
|---|---|---|---|
| E2E-01 | `POST /api/v1/login` → par; `GET /api/v1/me` con `Bearer <refresh>` | `401` | `200` |
| E2E-02 | `GET /api/v1/lots?limit=1` con `Bearer <refresh>` | `401` | `200` |
| E2E-03 | `GET /api/v1/me` con `Bearer <access>` | `200` | `200` |
| E2E-04 | `POST /api/v1/refresh` con el refresh → `GET /api/v1/me` con el nuevo access | `200`/`200` | igual |
| E2E-05 (UI) | Playwright: login por la interfaz, navegar a `/lots`, forzar caducidad del access (borrar `access_token` del `sessionStorage` y recargar) → el interceptor renueva y la sesión continúa | sin logout inesperado | igual |

Evidencia: `evidence/r200/runtime-c3.json` + `GA_CLAUDE_R200_RUNTIME_CERTIFICATION.md`.

## 3. UAT del propietario

**NO REQUERIDA.** Backend-only; login, renovación automática, cambio de empresa y Mini App se conservan (CTL-05…08, E2E-04/05). Se informa en el ledger de que la revocación del refresh sigue pendiente en `GA-REM-003 AC04`.

## 4. Sensibilidad

| # | Mutación | Rompe |
|---|---|---|
| M1 | eliminar la comprobación de `type` en `get_current_user` | RED-01, RED-02, RED-03, RED-04 |
| M2 | aceptar `type in ("access", "refresh")` | RED-01, RED-02 |
| M3 | comprobar `type` **después** de consultar la base | AC09 (aserción de `get_current_audit_user()`), si la comprobación falla tras `set_current_audit_user`; en cualquier caso RED-01 sigue verde — se documenta como mutación no detectada por código de estado y detectada por la aserción de auditoría |
