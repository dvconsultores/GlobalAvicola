# R-199 · DISEÑO RED · E2E RUNTIME · UAT

## 1. Pruebas RED (backend) — `backend/tests/test_r199_global_authority_fabrication.py`

### 1.1 Fixture `esc199` (molde: `tests/test_role_tenancy.py::esc`, PREFIJO `R199-`)

```
Empresas      A, B (activas)
Roles         rol_admin_a   company_id=A   users:read/create/update/delete (scope_type="company")
              rol_a         company_id=A   operations:read
              rol_global    company_id=NULL  ("*", <todas las acciones>, "all")        — plantilla global
              rol_env       company_id=A   ("*", read/create/update/delete, "all")   — ROL DE INQUILINO ENVENENADO,
                                             insertado directamente (simula el resultado de RED-01 o datos heredados)
Usuarios      admin_a (A, rol_admin_a) · user_a (A, rol_a) · user_env (A, rol_env) · super (None, rol_global)
Token         _token(user_id, company_id=None) con create_access_token (como en test_role_tenancy)
Teardown      DELETE audit_logs/permissions/users/roles/companies por PREFIJO
Lecturas      _rol_en_base(id), _permisos_en_base(role_id) -> set[(module, action, scope_type)],
              _rol_de_usuario(user_id), _recuentos() -> (count roles, count permissions)
```

Cliente: `http_client` (`raise_app_exceptions=False`) para observar `500`→`422` en RED-06b.

### 1.2 Casos

| ID | Nombre exacto | Pasos | Aserción que **falla en HEAD** (valor actual) |
|---|---|---|---|
| RED-01 | `test_r199_01_crear_rol_de_inquilino_con_comodin_global_se_rechaza` | `antes=_recuentos()`; `POST /api/v1/roles` como `admin_a` con `{"name": "R199-X", "permissions": [{"module": "*", "action": "read", "scope_type": "all"}]}` | `r.status_code == 403` (HEAD: `201`); `_recuentos() == antes` (HEAD: +1 rol, +1 permiso); (AC12) existe `audit_logs` `action=permission_change` con `comments` que contiene `rechazado` |
| RED-02 | `test_r199_02_editar_rol_de_inquilino_para_inyectar_el_comodin_se_rechaza` | `antes=_permisos_en_base(rol_a)`; `PUT /api/v1/roles/{rol_a}` como `admin_a` con `{"permissions": [{"module": "*", "action": "update", "scope_type": "all"}]}` | `403` (HEAD: `200`); `_permisos_en_base(rol_a) == antes` (HEAD: `{("*","update","all")}`) |
| RED-03 | `test_r199_03_un_rol_de_inquilino_envenenado_no_es_asignable` | `PUT /api/v1/users/{user_a}` como `admin_a` con `{"role_id": rol_env}` | `403` (HEAD: `200`); `_rol_de_usuario(user_a) == rol_a` (HEAD: `rol_env`). Variante en el mismo test: `POST /api/v1/users` con `role_id=rol_env` → `403` (HEAD: `201`) |
| RED-04 | `test_r199_04_un_rol_de_inquilino_envenenado_no_confiere_autoridad_global` | como `user_env`: `GET /api/v1/me`; `POST /api/v1/switch-company {"company_id": B}`; `GET /api/v1/users` | `me["is_super_admin"] is False` (HEAD: `True`); `switch.status_code == 403` (HEAD: `200`); todos los `company_id` del listado `== A` |
| RED-05 | `test_r199_05_la_renovacion_no_honra_un_contexto_ajeno_con_rol_envenenado` | `refresh = create_refresh_token({"sub": str(user_env), "company_id": B})`; `POST /api/v1/refresh {"refresh_token": refresh}` → `access`; `GET /api/v1/me` con `access` | `me["effective_company_id"] == A` (HEAD: `B`, porque `_es_super_admin` devuelve `True` y `_claims_de(user, B)` emite `company_id=B`) |
| RED-06a | `test_r199_06_modulo_fuera_de_catalogo_es_422` | `POST /roles` como `admin_a` con `{"module": "hacking", "action": "read", "scope_type": "company"}` | `422` (HEAD: `201`); recuentos iguales |
| RED-06b | `test_r199_06_accion_invalida_es_422_y_no_500` | ídem con `{"module": "lots", "action": "fly", "scope_type": "company"}` | `422` (HEAD: `500` — `PermissionAction("fly")` `ValueError`, `service.py:602`) |
| RED-06c | `test_r199_06_alcance_invalido_es_422` | ídem con `{"module": "lots", "action": "read", "scope_type": "galaxy"}` | `422` (HEAD: `201`) |
| CTL-07 | `test_r199_07_la_autoridad_global_sigue_creando_plantillas_con_comodin` | `POST /roles` como `super` con el par global | `201`, `_rol_en_base(id)["company_id"] is None`; un usuario creado con ese rol → `/me.is_super_admin is True` |
| CTL-08 | `test_r199_08_el_rol_de_inquilino_ordinario_se_crea_asigna_y_no_es_global` | `POST /roles` como `admin_a` con `[{"module":"lots","action":"read","scope_type":"all"},{"module":"operations","action":"create","scope_type":"all"}]` (lo que envía `RolesPage`); `PUT /users/{user_a}` con ese rol; `/me` como `user_a` | `201`, `200`, `is_super_admin is False`, `"lots:read" in permissions` |
| CTL-09 | `test_r199_09_el_comodin_de_modulo_con_alcance_de_empresa_sigue_admitido` | `POST /roles` como `admin_a` con `[{"module":"*","action":"read","scope_type":"company"}]`; asignar; `/me` | `201`, `is_super_admin is False`, `GET /lots` → `200` (`tiene_permiso` por comodín de módulo) |
| CTL-10 | `test_r199_10_no_queda_atajo_legado_sin_filtro` | `import app.auth.security as s; import app.dependencies as d` | `not hasattr(s, "get_company_filter") and not hasattr(d, "get_company_filter")` (HEAD: falla; es la única «RED» de higiene y se acepta como tal) |

### 1.3 Verificación de que la RED es por el defecto

Antes del commit C1 se ejecuta el fichero: RED-01…06 y CTL-10 deben fallar **en la aserción indicada** (no en la fixture ni en el login); CTL-07…09 deben pasar. Se adjunta la salida a `evidence/r199/red_c1.log`.

## 2. E2E runtime (C3) — sondas API como actor de empresa

Entorno: `https://avicola.globaldv.net` tras desplegar C2. Actores: super admin de runtime (`UAT-09`) situado en empresa 1 crea un **actor desechable**:

```
rol   R199-AdminEmpresa  (users:read, users:create, users:update, scope_type company)   company_id=1
user  r199_admin         (empresa 1, rol R199-AdminEmpresa)
```

| ID | Sonda (como `r199_admin` salvo indicación) | Esperado post-fix | Valor pre-fix (RED runtime, opcional si se sonda antes del despliegue) |
|---|---|---|---|
| E2E-01 | `POST /api/v1/roles` con `("*","read","all")` | `403` + `GET /api/v1/roles` sin el rol; `GET /api/v1/audit?limit=50` (super) muestra el rechazo (`C-05`) | `201` |
| E2E-02 | crear rol ordinario `R199-Tmp` y `PUT /api/v1/roles/{id}` con el par | `403`, permisos intactos | `200` |
| E2E-03 | **condicional**: si `C-06` autoriza sembrar en runtime un rol envenenado (super situado en 1, por SQL de solo prueba, o se omite) → `PUT /users/{r199_admin}` con ese `role_id` | `403` | `200` |
| E2E-04 | `GET /api/v1/me` de `r199_admin`; `POST /api/v1/switch-company {"company_id": 2}` (si existe empresa 2) | `is_super_admin=false`, `403` | (ídem hoy para un actor sin comodín; la RED runtime real es E2E-01/02) |
| E2E-05a/b/c | `POST /roles` con módulo `hacking` / acción `fly` / alcance `galaxy` | `422` ×3 | `201` / `500` / `201` |
| E2E-06 | control: `POST /roles` ordinario con `scope_type:'all'` desde la **UI** (`/roles`, RolesPage) y por API; asignar a `r199_admin` | `201`/`200`; `/me.is_super_admin=false` | igual |
| E2E-07 | inventario §12 (SQL de solo lectura contra la base de runtime) | `0` filas (o `C-06`) | — |
| Limpieza | desactivar `r199_admin` (`DELETE /users/{id}`) y `R199-*` (`PUT /roles/{id} {"is_active": false}`) | | |

Evidencia: `audit/ga-claude-final-audit/evidence/r199/runtime-c3.json` (petición, código, cuerpo saneado, marca de tiempo) + `GA_CLAUDE_R199_RUNTIME_CERTIFICATION.md`.

## 3. UAT del propietario

**NO REQUERIDA.** Justificación: corrección backend-only de una escalada de privilegio; no cambia ninguna pantalla, ningún flujo legítimo ni ningún texto; el único comportamiento visible nuevo (un `403`/`422` ante una petición manipulada) no es alcanzable desde la interfaz. Se comunica en el ledger: resultado de E2E-07 y decisión `C-05`.

## 4. Sensibilidad (mutaciones que deben romper ≥1 prueba)

| # | Mutación | Prueba que debe romper |
|---|---|---|
| M1 | quitar la llamada a `_validar_permisos` en `create_role` | RED-01, RED-06a/b/c |
| M2 | quitar la llamada en `update_role` | RED-02 |
| M3 | restaurar `return rol.company_id == empresa` en `_rol_asignable` | RED-03 |
| M4 | quitar `user.role.company_id is None` en `get_current_user` | RED-04 |
| M5 | quitar `Role.company_id.is_(None)` en `_es_super_admin` | RED-05 |
| M6 | validar sólo `module` y no `action`/`scope_type` | RED-06b, RED-06c |
| M7 | comprobar por nombre de rol («Super Administrador») en vez de por `company_id` | CTL-07 con plantilla renombrada `R199-Global` (la fixture ya la nombra así) sigue pasando, y RED-04 rompe si M7 abre por nombre; se documenta como `AC-F05` |

Reversión: `git checkout -- backend/app/auth` desde la raíz del repo, después del commit C2 (regla de memoria «sensibilidad tras commit»).
