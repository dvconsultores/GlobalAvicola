# 09 — AUDITORÍA DEL BACKEND

## 1. Stack y estructura

| Aspecto | Valor |
|---|---|
| Lenguaje / runtime | Python 3.11 |
| Framework | FastAPI (async), Uvicorn |
| ORM | SQLAlchemy 2.x async + asyncpg |
| Validación | Pydantic v2 + pydantic-settings |
| Migraciones | Alembic (21 revisiones, 1 head) |
| Patrón | Modular monolito por dominio: `router → service → models` |
| Repositorios | **No existen** (el README los anuncia) |
| Middleware | CORS, `SecurityHeadersMiddleware` propio, slowapi condicional |
| Auth | JWT HS256 (PyJWT) + bcrypt (passlib), `HTTPBearer` |
| Sesión de BD | `get_db()` con commit al final del request y rollback ante excepción |

Métricas: **11 módulos de dominio, 14 796 LOC** (app + seeds + tests + alembic). Servicio mayor: `operations/service.py` (575 LOC).

## 2. Inventario de endpoints

**167 operaciones bajo `/api/v1` + `GET /health`** (obtenidas del esquema OpenAPI instanciando la app; `FEATURE_SAP_ENABLED=true`).

| Módulo | Ops | Auth | Roles exigidos | Consumidos por FE | Huérfanos |
|---|---|---|---|---|---|
| Auth (login, refresh, me, switch-company) | 4 | 3 de 4 | ninguno | 4 | 0 |
| Users | 5 | sí | **ninguno** | 4 | 1 |
| Roles | 3 | sí | **ninguno** | 3 (vía servicio muerto) | 0 |
| Masters | 82 | sí | **ninguno** | 62 | **20** |
| Lots | 12 | sí | **ninguno** | 12 | 0 |
| Operations | 13 | sí | **ninguno** | 12 | 1 |
| Review | 6 | sí | **ninguno** | 6 | 0 |
| Approvals | 5 | sí | **ninguno** | 5 | 0 |
| Approval Steps | 5 | sí | **ninguno** | 0 | **5** |
| Corrections | 3 | sí | **ninguno** | 3 | 0 |
| Audit | 3 | sí | **ninguno** | 3 | 0 |
| Reports | 14 | sí | **ninguno** | 10 | **4** |
| Dashboard | 2 | sí | **ninguno** | 2 | 0 |
| SAP Integration | 10 | sí | **ninguno** | 10 | 0 |
| Health | 1 | no | — | 0 (Docker) | 0 |
| **TOTAL** | **168** | | | **133** | **34** |

Inventario completo: `11_API_INVENTORY.md`.

## 3. Hallazgos del backend

### BE-01 · `mortality_recording` lanza `NameError` (P0 — BLOQUEADOR)

```python
# backend/app/operations/service.py:242
balance = await get_current_bird_balance(self.db, event.lot_id, self.company_id)
```

- `get_current_bird_balance` **no está importado** en `service.py` (verificado por análisis del AST del módulo: no aparece en ningún `ImportFrom`, ni a nivel de módulo ni dentro de la función).
- Además la firma real es `get_current_bird_balance(db, lot_id)` — **2 parámetros**, no 3 (`validators.py:21`).

La ruta se ejecuta siempre que se crea un `mortality_recording` con cantidad > 0, es decir en **toda mortalidad diaria**. Resultado: excepción no capturada → HTTP 500 y **el evento no se persiste** (rollback de la sesión).

Introducido en `bdb5cde` (2026-06-27 03:12, "Phase 3: range indicators + auto alerts backend"). Ningún test lo cubre porque el CI nunca corrió.

### BE-02 · Las correcciones no modifican el dato (P0 — BLOQUEADOR)

`backend/app/corrections/service.py:37-58`: crea un `CorrectionLog` con `field_name`, `original_value`, `corrected_value` y `reason`, cambia `event.status = CORRECTED` y audita. **En ningún punto escribe el valor corregido sobre el evento ni sobre sus submovimientos.**

Consecuencias en cadena:
- El dato erróneo es el que se aprueba, se consolida y se envía a SAP.
- Los KPIs se calculan sobre el valor incorrecto.
- La spec BR-09 ("valor original + corregido siempre visibles") se cumple *documentalmente*, pero el sistema queda con dos verdades divergentes.

### BE-03 · RBAC declarado y no aplicado (P0 — BLOQUEADOR)

Existen `Permission` (role_id, module, action, scope_type, scope_id), el enum `PermissionAction` con 9 acciones (READ, CREATE, UPDATE, DELETE, REVIEW, CORRECT, APPROVE, REJECT, SEND_SAP) y seeds que pueblan permisos para 6 roles.

**No existe ninguna dependencia `require_permission` ni ninguna comprobación de `action`/`module` en todo `backend/app/`.** El único uso de la tabla es derivar `is_super_admin` cuando existe un permiso con `module="*"` y `scope_type="all"` (`auth/security.py:107-118`).

Todos los endpoints usan `Depends(get_current_user)` a secas. Por tanto **cualquier usuario autenticado** puede:
`POST /approvals/approve`, `POST /approvals/batch-approve`, `DELETE /masters/{entidad}/{id}`, `POST /users`, `PUT /roles/{id}`, `POST /sap/export`, `GET /audit`.

### BE-04 · El refresh de token degrada la identidad (P0 — BLOQUEADOR)

```python
# backend/app/auth/service.py:72
token_data = {"sub": user.id, "username": user.username}
```

El login emite `sub`, `username`, `company_id`, `role_id`, `view_type`. El refresh emite **solo `sub` y `username`**. El backend recupera al usuario de la BD, así que no se ve afectado; **el frontend sí**: reconstruye el usuario desde los claims (`auth.store.ts:85-101`) y aplica `view_type: claims?.view_type || 'web'`, `company_id: null`, `role_id: null`, perdiendo además `is_super_admin`.

Como `fetchMe()` solo se invoca cuando `token && isLoading`, y `setTokens` no restaura `isLoading`, **el usuario degradado persiste hasta recargar la página**. Un operador móvil, tras 30 minutos, obtiene acceso a todas las rutas "solo web". Sin RBAC de servidor (BE-03), esas acciones se ejecutan.

### BE-05 · BR-14 (segregación) eludible (P0)

`ApprovalService.approve()` valida correctamente `validate_segregation(event.registered_by_id, current_user["id"])` (`review/service.py:301-309`).
`ReviewService.complete_review()` **no la valida** y, cuando `company.approval_levels <= 1`, hace `event.status = APPROVED; event.approved_by_id = current_user["id"]` (`review/service.py:196-234`).

Ruta de elusión completa, ejecutable por el propio autor del registro y sin permisos especiales:
`POST /operations` → `POST /review/batches` → `POST /review/start/{id}` → `POST /review/complete` → **aprobado por sí mismo**.

### BE-06 · Aislamiento multi-compañía inconsistente (P1)

Dos patrones conviven:

1. Con soporte de Super Admin: `MasterService._apply_company_filter` y `OperationsService` comprueban `is_super_admin` antes de filtrar.
2. **Sin soporte**: **61 filtros crudos** `X.company_id == self.company_id` en 7 servicios — `reports` (19), `review` (12), `dashboard` (11), `lots` (5), `operations` (5), `audit` (4), `corrections` (4).

Para un Super Admin con `company_id = NULL`, esos filtros se traducen a `company_id IS NULL` → **resultado vacío** en Reportes, Revisión, Aprobaciones, Auditoría, Dashboard y Correcciones. El commit `bfccdfb` (el último del repositorio) corrigió este patrón **solo en `SapService`**.

**Agujero inverso, más grave:** `MasterService._apply_company_filter` (`masters/service.py:35-41`):

```python
if self.is_super_admin: return query      # sin filtro
if not self.user_company_id: return query # ← SIN FILTRO
```

Un usuario **no** super admin cuyo `company_id` sea `NULL` recibe **todos los maestros y todos los lotes de todas las compañías**. `User.company_id` es nullable y no hay validación en el alta de usuarios.

### BE-07 · Doble mecanismo de auditoría activo (P1)

Ambos están operativos simultáneamente:
- `register_audit_listeners()` se invoca en el `lifespan` de FastAPI (`main.py:33-37`) y registra `@event.listens_for(Session, "after_flush")`, que crea `AuditLog` para cada `OperationalEvent` nuevo o modificado, cada `CorrectionLog` y cada `ApprovalAction` (`audit/listeners.py:71-113`).
- Los servicios llaman explícitamente a `audit_event_created`, `audit_state_transition` y `audit_correction` (9 llamadas en `operations`, `review` y `corrections`).

`audit/helpers.py:1-10` justifica los helpers diciendo que los listeners "no se disparan de forma fiable con AsyncSession" — pero los listeners están registrados sobre la clase `Session` **síncrona** que `AsyncSession` envuelve, y sí se disparan.

Resultado: **cada acción genera dos o más entradas de auditoría**. La propia evidencia publicada en `AUDITORIA_FUNCIONAL_E2E.md` lo muestra: `created → updated → review_started → corrected` para un flujo en el que solo debería haber `created` y `review_started`.

### BE-08 · Reglas de negocio: estado real

| Regla | Implementación | Estado |
|---|---|---|
| BR-01 mortalidad ≤ saldo | `validate_mortality` correcto | ✔ **pero la ruta muere antes por BE-01** |
| BR-02 huevos ≤ disponible | `validate_egg_dispatch` | ✔ |
| BR-03 carga ≤ recibidos | `validate_incubation_load` | ✔ |
| BR-04 pollitos ≤ nacidos viables | `validate_chick_dispatch` | ✔ |
| BR-05 cierre con resumen | `validate_lot_closure` exige ≥1 pesaje y ≥1 alimento | ✔ |
| BR-06 fecha ≥ activación | **defectuosa** | ✘ |
| BR-07 lote activo | `validate_lot_active` | ✔ |
| BR-08 granja/galpón | `validate_farm_house` | ✔ |
| BR-09 corrección auditada | registra pero no aplica (BE-02) | ⚠ |
| BR-10 borrado lógico | maestros `is_active=False`; eventos `CANCELLED` | ✔ |
| BR-11 documento SAP único | `validate_sap_document_unique` correcto, **nunca se dispara** (FE no envía `sap_document_ref`) | ⚠ inerte |
| BR-12 idempotencia | implementada, **nunca se usa** (FE no envía `idempotency_key`) | ⚠ inerte |
| BR-13 nada a SAP sin aprobar | consolidación filtra `status == APPROVED` | ✔ |
| BR-14 segregación | eludible (BE-05) | ⚠ |
| BR-15 no editar enviados a SAP | `validate_sap_edit_lock` | ✔ |
| BR-16 reverso post-SAP | tabla `reversals` **huérfana**, 0 referencias | ✘ |
| BR-17/18/19 (solo código) | capacidad de galpón, cantidad ≤ OC, período >90 días | ✔ / ⚠ (BR-18 inerte) |

**BR-06 defectuosa** — `validators.py:250`:
```python
if lot and lot.start_date and event_date < lot.start_date.date() if hasattr(lot.start_date, 'date') else False:
```
Python evalúa esto como `(lot and lot.start_date and event_date < lot.start_date.date()) if hasattr(...) else False`. Con `lot` a `None`, `hasattr(None,'date')` es falso → la regla no se aplica; y aunque se cumpliera, la comprobación de `activation_type != "manual"` está anidada de forma que la regla nunca protege el caso general. **BR-06 no se aplica en la práctica.**

### BE-09 · Integración SAP simulada en producción (P0)

```python
def get_adapter(self) -> SapIntegrationAdapter:
    if self._adapter is None:
        # TODO: read from config/env which adapter to use
        self._adapter = ManualSapAdapter()
    return self._adapter
```
`backend/app/integrations/sap/service.py:34-38`.

`ManualSapAdapter.export_consolidated` escribe `/tmp/sap_exports/<idempotency_key>.json`, devuelve siempre `success=True` con `sap_document_id = "MANUAL-<12 hex>"`, y el servicio marca los eventos como `SENT_TO_SAP` con esa referencia ficticia. A partir de ahí BR-15 impide editarlos.

`RealSapAdapter` (tarea T-085, "🔴 Crítica, bloquea prod") **no existe**. `FEATURE_SAP_ENABLED=true` está activo en producción desde `bfccdfb` (2026-07-08).

### BE-10 · `mock_adapter.py` no compila (P2)

`backend/app/integrations/sap/mock_adapter.py:17` hace `from .interface import SapAdapter`; el módulo `interface.py` **no existe**. Verificado: `python -c "import app.integrations.sap.mock_adapter"` → `ModuleNotFoundError`. El archivo no es importado por nadie, así que no rompe el arranque, pero es el entregable "mock SAP" del commit `0b8a6b7`, y por tanto una funcionalidad declarada e inexistente. Además coexiste con un `MockSapAdapter` distinto en `adapter.py`, también sin uso.

### BE-11 · Otros defectos confirmados

| ID | Hallazgo | Evidencia | Sev. |
|---|---|---|---|
| BE-11a | `MockSapAdapter.check_connection` usa `random` sin importarlo a nivel de módulo → `NameError` si `simulate_errors=True` | `adapter.py:157` | P3 |
| BE-11b | Backoff de reintento `(minute + n) % 60` produce una fecha **anterior** si el minuto actual es alto → reintento inmediato en bucle | `sap/service.py:317-319, 398-400` | P2 |
| BE-11c | `list_items` de maestros devuelve una lista plana sin total → el frontend no puede paginar | `masters/router.py:40` | P2 |
| BE-11d | 15 de 19 maestros carecen de `PUT` (solo `companies`, `farms`, `houses`, `hatcheries` reciben `update_schema`) mientras la UI ofrece "Editar" para 12 → **405** en 8 pantallas | `masters/router.py:88-107` | P1 |
| BE-11e | `ALL_EVENT_TYPES` con 25 etiquetas en español fijo en el backend | `operations/schemas.py:180-206` | P3 |
| BE-11f | `quick_actions` del dashboard móvil con texto español fijo y emojis | `dashboard/service.py:48-53` | P3 |
| BE-11g | `create_lot` comprueba unicidad de `lot_code` **global**, no por compañía → una compañía bloquea códigos de otra y se filtra su existencia | `lots/service.py:53-60`; sin `UniqueConstraint` en la tabla | P2 |
| BE-11h | `GET /lots/{id}/traceability` consulta `EggBatch`/`ChickBatch` sin filtro de compañía (solo valida el lote raíz) | `lots/router.py:157-176` | P2 |
| BE-11i | Ni `last_login` ni ningún evento de autenticación se registran; `AuditAction.LOGIN/LOGOUT/LOGIN_FAILED/PERMISSION_CHANGE/IMPORT/EXPORT/DELETED` están definidos y **jamás se escriben** | `auth/service.py`; `audit/models.py:24-45` | P2 |
| BE-11j | No existe endpoint de logout ni lista de revocación; los refresh tokens viven 7 días sin poder invalidarse | inventario de rutas | P1 |
| BE-11k | El evento `bird_transfer` está en el enum, en el catálogo y en el formulario, pero **no aparece en ninguna regla de balance**: no suma ni resta en `get_current_bird_balance` | `validators.py:26-33` | P2 |
| BE-11l | `_auto_create_traceability_batches` empareja despacho y recepción **por el mismo `lot_id`** → vínculos auto-referenciales o inexistentes | `operations/service.py:127-176` | P0 |

### BE-12 · Buenas prácticas verificadas (positivo)

- **Un solo `TODO` en todo el backend** (el de `get_adapter`), 0 `FIXME`, 0 `HACK`, 0 mocks de datos.
- `compileall` sobre `app/`, `seeds/` y `tests/` → sin errores.
- Modelo unificado `OperationalEvent` + 6 submodelos: diseño acertado que sustituye 12+ tablas del legacy.
- Adapter pattern de SAP correctamente aislado (ABC + DTOs sin acoplamiento a SAP).
- Cabeceras de seguridad completas (`X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, HSTS condicional en producción).
- `config.py` **rechaza el arranque** si `JWT_SECRET_KEY` está vacío o empieza por `change_me`, y si falta `POSTGRES_PASSWORD` cuando no hay `DATABASE_URL`. Es una defensa real contra despliegues con secretos por defecto.
- Contraseñas con bcrypt vía passlib; sin SQL crudo en ningún punto (100 % SQLAlchemy → sin superficie de inyección SQL).
- Subida de evidencias con lista blanca de MIME, límite de 10 MB y nombre de archivo aleatorio (`uuid4().hex`) — previene *path traversal* y ejecución.
