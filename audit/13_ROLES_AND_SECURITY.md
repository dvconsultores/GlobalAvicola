# 13 — ROLES, PERMISOS Y SEGURIDAD

## 1. Roles

### 1.1 Definidos en la especificación (`docs/02 §6.1`) — 11 roles

Super Administrador · Administrador de Empresa · Supervisor Avícola · Aprobador · Operador de Granja · Operador de Incubadora · Operador de Engorde · Veterinario · Analista SAP · Auditor · Consulta/Reportes.

### 1.2 Sembrados en el sistema

`backend/seeds/dev_seeds.py` crea **6 roles**: Super Administrador, Supervisor Avícola, Operador de Granja, Aprobador, Analista SAP, Auditor.
`backend/seeds/integration_seeds.py` crea **7 roles adicionales** para pruebas en vivo: Operador Progenitoras, Operador Reproductoras, Operador Incubadora, Operador Engorde, Operador Multi-Proceso, Supervisor General, Contralor Avícola.

Faltan respecto a la spec: Administrador de Empresa, Veterinario, Consulta/Reportes.
`Role.company_id` existe pero los seeds crean **roles globales** (sin compañía), y `ApprovalStepService._get_role_by_name` busca por nombre **sin filtrar por compañía**.

## 2. Matriz de permisos — DECLARADA vs APLICADA

| Rol | Módulos | Leer | Crear | Editar | Eliminar | Aprobar | Acciones especiales |
|---|---|---|---|---|---|---|---|
| Super Administrador | `*` | ✔ | ✔ | ✔ | ✔ | ✔ | `send_sap`, ve todas las compañías |
| Supervisor Avícola | operations, lots, review, approvals, reports | ✔ | — | — | — | — | `review`, `correct` |
| Operador de Granja | operations, lots | ✔ | ✔ (operations) | — | — | — | — |
| Aprobador | operations, review, approvals, reports | ✔ | — | — | — | ✔ | `reject`, `review`, `correct` |
| Analista SAP | sap, operations, reports | ✔ | ✔ (sap) | — | — | — | `send_sap` |
| Auditor | audit, reports, operations | ✔ | — | — | — | — | — |

**Esta matriz es puramente documental.**

## 3. Enforcement por capa

| Capa | Se aplica | Detalle |
|---|---|---|
| **1. UI (visibilidad)** | ⚠ Parcial | El sidebar/menú se construye desde `navigationConfig.ts` **sin filtrar por rol** |
| **2. Router (frontend)** | ⚠ Solo por `view_type` | `WebOnlyRoute` bloquea a los usuarios `view_type='mobile'`. `ProtectedRoute` acepta un prop `roles` cuya lógica es `const userRoleName = user?.role_id ? '' : 'super_admin'` —sin sentido— y **nunca recibe ese prop** (`frontend/src/App.tsx:35-60`) |
| **3. API (dependencias)** | ✘ **NO** | Los 165 endpoints autenticados usan `Depends(get_current_user)` sin ninguna comprobación de permiso |
| **4. Backend (servicios)** | ✘ **NO** | Solo `is_super_admin` (alcance) y `validate_segregation` (BR-14, únicamente en `ApprovalService.approve`) |
| **5. Capa de datos** | ⚠ Parcial | Filtro por `company_id` con dos patrones incompatibles (ver S-03) |

> **`spec.md §4.1` exige "Permisos por módulo, acción (CRUD + revisar, corregir, aprobar, rechazar, enviar SAP) y alcance (empresa/granja)".**
> **Ninguna de esas comprobaciones existe en el código.** El modelo `Permission` solo se consulta para deducir `is_super_admin` (`auth/security.py:107-118`).

**Conclusión: "permiso solo oculto en frontend = vulnerabilidad" se cumple, y de la forma más severa: aquí ni siquiera está oculto en el frontend.**

## 4. Autenticación

| Elemento | Estado | Evidencia |
|---|---|---|
| Login usuario/contraseña | ✔ | `auth/service.py:29-58` |
| Hash de contraseñas | ✔ bcrypt vía passlib | `auth/security.py:15` |
| JWT | ✔ HS256, `exp`, claim `type` (access/refresh) | `auth/security.py:34-63` |
| Expiración de access token | ✔ 30 min | `config.py:60` |
| Expiración de refresh token | ✔ 7 días | `config.py:61` |
| Validación de tipo de token en refresh | ✔ | `auth/service.py:60-63` |
| **Contenido del token tras refresh** | ✘ **degradado** | pierde `view_type`, `company_id`, `role_id` |
| **Logout / revocación** | ✘ **no existe** | ningún endpoint; sin denylist |
| Cuenta desactivada | ✔ 403 en login y 401 en `get_current_user` | `auth/service.py:39` |
| Bloqueo por intentos fallidos | ✘ | — |
| Registro de login / login fallido | ✘ | `AuditAction.LOGIN/LOGIN_FAILED` definidos y nunca usados |
| `last_login` | ✘ columna existe, nunca se escribe | `auth/models.py:25` |
| Recuperación de contraseña | ✘ | — |
| MFA | ✘ | — |
| Cambio de contraseña propia | ✘ **NO FUNCIONA** — `UserUpdate` no declara `password`, así que el backend lo descarta y la UI muestra igualmente "Contraseña actualizada" | `auth/schemas.py:42-49`; `auth/service.py:136-138`; `ProfilePage.tsx:24-26` |
| Almacenamiento del token | `sessionStorage` (web) / `localStorage` (Telegram Mini App) | `auth.store.ts:51-57` |
| Cookies | no se usan | — |
| CSRF | no aplica (Bearer, sin cookies) | — |

## 5. Hallazgos de seguridad

### P0 — CRÍTICO

**S-01 · Ausencia total de control de autorización.**
Cualquier usuario autenticado —incluido el operador de campo con el rol más restringido— puede ejecutar `POST /approvals/approve`, `POST /approvals/batch-approve`, `POST /sap/export`, `POST /users`, `PUT /roles/{id}`, `DELETE /masters/{entidad}/{id}` y `GET /audit`.
*Evidencia:* ninguna dependencia de permiso en `backend/app/**`; `auth/security.py:107-118` es el único consumidor de la tabla `permissions`.
*Impacto:* violación directa de la spec §4.1 y de `docs/02 §6.2`; también de BR-13 en su espíritu (un operador puede aprobar y exportar a SAP).
*Clasificación:* `SPEC_SECURITY_VIOLATION`.

**S-02 · Escalada de privilegios por refresh de token.**
`refresh_token()` (`auth/service.py:72`) emite `{"sub", "username"}`. El frontend reconstruye el usuario desde los claims (`auth.store.ts:85-101`) con `view_type: claims?.view_type || 'web'`. A los 30 minutos, un usuario móvil pasa a ser tratado como web y accede a `/users`, `/approvals`, `/sap`, `/audit`, `/review`, `/masters` y `/lots/new`. `fetchMe()` no se re-ejecuta porque solo corre cuando `isLoading` es true. Combinado con S-01, las acciones se ejecutan realmente.

**S-03 · Fuga de aislamiento multi-compañía.**
`MasterService._apply_company_filter` (`masters/service.py:35-41`):
```python
if self.is_super_admin: return query
if not self.user_company_id: return query   # ← sin filtro
```
Un usuario **no** super admin con `company_id = NULL` (columna nullable, sin validación en el alta) obtiene **todos los maestros y todos los lotes de todas las compañías**.
El defecto simétrico: 61 filtros crudos `== self.company_id` en 7 servicios dejan al Super Admin (con `company_id` nulo) sin datos en Reportes, Revisión, Aprobaciones, Auditoría, Dashboard y Correcciones.

**S-04 · Credenciales conocidas contra un entorno público sin rate limiting.**
`GUIA_PRUEBAS_EN_VIVO.md` publica 15 pares usuario/contraseña, incluido `admin / admin123` (Super Administrador). Los mismos valores están en `backend/seeds/dev_seeds.py:154` e `integration_seeds.py:174-203`. El `docker-compose.yml` de producción **no define `FEATURE_RATE_LIMIT_ENABLED`**, cuyo valor por defecto es `False` (`config.py:96`), así que el decorador `@rate_limit("5/minute")` del login es un *no-op*. Si esos seeds se ejecutaron contra la base de datos que sirve `avicola.globaldv.net`, el sistema es accesible con credenciales públicas.

**S-05 · Elusión de la segregación de funciones (BR-14).**
Ruta: `POST /operations` → `POST /review/batches` → `POST /review/start/{id}` → `POST /review/complete`. Con `company.approval_levels <= 1`, `complete_review` marca `APPROVED` y `approved_by_id = current_user["id"]` **sin llamar a `validate_segregation`** (`review/service.py:196-234`). El propio autor aprueba su registro.

### P1 — ALTO

| ID | Hallazgo | Evidencia |
|---|---|---|
| S-06 | **Sin revocación de sesión.** No hay logout de servidor ni denylist. Un refresh token robado sirve 7 días; desactivar al usuario solo corta el `access` en la siguiente validación de `get_current_user`, pero el atacante puede seguir usando el access token vigente hasta 30 minutos. | inventario de rutas; `auth/security.py:100-104` |
| S-07 | **El cambio de contraseña es un falso positivo.** `UserUpdate` (`auth/schemas.py:42-49`) **no declara el campo `password`**; Pydantic descarta las claves desconocidas, así que `update_user` recibe un diccionario vacío y no modifica nada. `ProfilePage` envía `{password}`, recibe 200 y muestra "Contraseña actualizada". **El usuario cree que cambió su contraseña y no cambió.** No existe ningún endpoint capaz de cambiar una contraseña tras el alta. | `auth/schemas.py:42-49`; `auth/service.py:130-142`; `ProfilePage.tsx:24-26` |
| S-08 | **Base de datos en IP pública con rol `postgres` y sin SSL obligatorio.** `backend/.env` conecta el entorno de desarrollo directamente al servidor de la nube; la variante `?ssl=require` está comentada en `.env.example`. | `backend/.env`; `.env.example:30` |
| S-09 | **Credenciales reales en `.env` locales**, incluidas SMTP de AWS SES en el `.env` de la raíz. No están versionadas (verificado: `git log --all -- '*.env'` vacío; `.gitignore:19,36`), pero circulan en las estaciones de trabajo. | `.env` raíz |
| S-10 | **CORS con `allow_credentials=True` y `allow_methods/headers=["*"]`.** Aceptable porque `allow_origins` está restringido por variable de entorno, pero el valor por defecto de `docker-compose.yml` incluye `http://localhost`. | `main.py:56-62`; `docker-compose.yml:27` |
| S-11 | **Auditoría incompleta en seguridad.** No se registran login, logout, login fallido, cambios de permisos ni cambios en maestros. `AuditAction` define esas acciones y ninguna se escribe. | `audit/models.py:24-45` |
| S-12 | **Enumeración de códigos de lote entre compañías.** `create_lot` valida `lot_code` de forma global; el error 409 revela que otra compañía ya usa ese código. | `lots/service.py:53-60` |
| S-13 | **`GET /lots/{id}/traceability` consulta `EggBatch`/`ChickBatch` sin filtro de compañía.** Solo se valida el lote raíz; los lotes enlazados podrían pertenecer a otra compañía. | `lots/router.py:157-176` |

### P2 — MEDIO

| ID | Hallazgo | Evidencia |
|---|---|---|
| S-14 | **Watchtower con el socket de Docker montado**, actualizando contenedores automáticamente desde `:latest`. Cualquiera con acceso de escritura al repositorio o al registro puede desplegar código en producción en 60 s. | `docker-compose.yml:87-99` |
| S-15 | **`client_max_body_size` no configurado en Nginx** → 413 para evidencias > 1 MB, pese a que el backend admite 10 MB. | `frontend/nginx.conf` |
| S-16 | **Errores verbosos en desarrollo.** `DEBUG=true` activa el echo de SQL; en producción `DEBUG=false` (correcto), pero el `.env` de desarrollo apunta a la base de datos de la nube. | `database.py:9`; `backend/.env` |
| S-17 | **Auditorías de dependencias no bloqueantes.** `pip-audit … \|\| true` y `npm audit … \|\| true`; además nunca se ejecutan (workflows solo en `pull_request`). | `.github/workflows/*-ci.yml` |
| S-18 | **Sin validación de `initData` de Telegram.** La Mini App usa login usuario/contraseña; no se aprovecha ni se valida la firma de Telegram. No introduce vulnerabilidad, pero el canal no está autenticado a nivel de plataforma. | `backend/app/integrations/telegram/bot.py` |

### P3 — BAJO

`S-19` `MockSapAdapter.check_connection` usa `random` sin importar → `NameError` potencial. · `S-20` mensajes de error de negocio en español fijo (no i18n) devueltos por la API. · `S-21` `X-Frame-Options: DENY` en el backend y `SAMEORIGIN` en Nginx (inconsistencia sin impacto real).

## 6. Vectores evaluados y NO encontrados (resultado positivo)

| Vector | Resultado |
|---|---|
| **Inyección SQL** | **No explotable.** 100 % SQLAlchemy ORM; cero `text()` o SQL concatenado en `backend/app/` |
| **XSS** | **Sin evidencia.** React escapa por defecto; **cero usos de `dangerouslySetInnerHTML`** y cero `eval`/`new Function` en `frontend/src` (las 3 apariciones de `innerHTML` son aserciones de lectura en tests) |
| **Mass assignment** | Mitigado: los servicios construyen las entidades campo a campo o mediante esquemas Pydantic explícitos |
| **Path traversal en subidas** | Mitigado: nombre generado con `uuid4().hex` + `os.path.basename`, y ruta bajo `MEDIA_DIR/evidences/{company}/{event}` |
| **Tipos de archivo peligrosos** | Mitigado: lista blanca de MIME (jpeg, png, gif, webp, pdf) y límite de 10 MB |
| **Secretos por defecto** | Mitigado activamente: `config.py.__init__` **aborta el arranque** si `JWT_SECRET_KEY` está vacío o empieza por `change_me`, o si falta `POSTGRES_PASSWORD` sin `DATABASE_URL` |
| **Secretos en el historial de Git** | **Ninguno.** `git log --all -- '*.env'` no devuelve nada; solo `.env.example` está versionado y usa marcadores |
| **SSRF** | No aplica: el backend no realiza peticiones salientes controladas por el usuario |
| **IDOR** | Mitigado parcialmente por el filtro de `company_id` en los servicios; **agravado** por S-01 y S-03 |
| **Cabeceras de seguridad** | Completas: `nosniff`, `X-Frame-Options`, `XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, HSTS en producción |

## 7. Resumen de severidad

```
P0 CRÍTICO ....  5   (S-01 RBAC, S-02 escalada por refresh, S-03 multi-tenant,
                      S-04 credenciales públicas sin rate limit, S-05 elusión BR-14)
P1 ALTO ....... 8
P2 MEDIO ...... 5
P3 BAJO ....... 3
```
