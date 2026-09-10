# GA-FE-02 · BACKEND CONTRACT MATRIX

Verificado contra código en `cb14523` (no supuesto). Prefijo global `/api/v1` (`main.py:149-165`).
**Ningún endpoint de unidades acepta `company_id`**: la empresa efectiva la resuelve el servidor
(`router.py:58-73`; sin ella → 403).

| # | CAPABILITY | METHOD | ROUTE | REQUEST | RESPONSE | PERMISSION | TENANT RULE | COMPANY CONTEXT | COMPANY BU RULE | USER BU RULE | ACTOR EXCEPTION | AUDIT | ERRORS | TEST COVERAGE | SPEC | READY |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B01 | Catálogo de empresas (selector) | GET | `/masters/companies` | `skip/limit(≤100)/search` | `CompanyCatalogRead[]`: `id,name,tax_id,country,currency,approval_levels,is_active,created_at,updated_at` (+`X-Total-Count`) | `masters:read` | SUPER_ADMIN: todas (CONTROL_GLOBAL); actor de empresa: solo la suya; sin empresa: 0 filas | — | — | — | — | — | 403 sin permiso | `test_company_catalog.py:50,202-250` | `GA-REM-033` enm. A · `OD-14.c` · `OD-18` | **YES** |
| B02 | Cambiar empresa efectiva | POST | `/switch-company` | `{company_id:int>0}` | `TokenResponse{access_token,refresh_token,token_type,expires_in:1800}` | titular + **super_admin** | No toca `users.company_id`; contexto re-validado por petición (`tenancy.py:244-290`) | Emite claim `company_id` nuevo en ambos tokens | — | — | super_admin sin empresa puede seleccionar; usuario normal 403 | `CONTEXT_SWITCHED` (`auth` module, prev/new state) | 403 no-super · 404 inexistente/inactiva | `test_multicompany_isolation.py:65,72,83,105` · `test_business_unit_guard.py:151-206` | `OD-11` · `OD-14.b` | **YES** |
| B03 | Sesión y contexto efectivo | GET | `/me` | — | `SessionRead` = `UserRead` + `effective_company_id` · `permissions[]` · `company_business_units[]` · `granted_business_units[]` · `effective_business_units[]` (+`company_id` persistida, `company_name`, `is_super_admin`) | titular | `effective_company_id:None` = ninguna elegida (no «todas») | `company_business_units` = habilitadas de la efectiva | `granted_business_units` = concesiones vivas (puede incluir apagadas) | `effective_business_units` = concedida∩habilitada∧activa (la única que autoriza) | — | — | 401 sin token | `test_session_payload.py:197-260,312-350` | `GA-REM-040` fase 8 enm. E · `AC-H11…H14` | **YES** |
| B04 | Listar unidades de la empresa | GET | `/business-units` | — | `HabilitacionRead[]{code,name_key,is_enabled}` — 4 canónicas siempre | `business_units:read` | Empresa efectiva obligatoria (403 sin ella); estado de otra empresa invisible | Resuelve habilitación de la efectiva | Nunca configurada → `false` (`§7.4` lo desconocido deniega) | — | — | 403 sin empresa | 403 sin permiso | `test_business_unit_admin.py:269`; catálogo `test_business_units.py` | `GA-REM-040` fase 7 · `OD-16.b` · `AC-A02/A07` | **YES** |
| B05 | Habilitar unidad | PATCH | `/business-units/{code}/enable` | path `{code∈4}` | `HabilitacionRead` | `business_units:update` | Igual que B04 | Escribe fila de la efectiva (crea si no existía); idempotente | **CERO concesiones creadas** (`test_habilitar_no_concede…`) | No afecta concesiones | — | `CONFIG_CHANGE`/`config`, entity `company_business_unit` | 403/404 | `test_business_unit_admin.py:285,295,310` | `OD-16.d` · `AC-A03` | **YES** |
| B06 | Deshabilitar unidad | PATCH | `/business-units/{code}/disable` | path `{code∈4}` | `HabilitacionRead` | `business_units:update` | Igual | Igual; apagar **no borra** concesiones; re-encender las devuelve (provisional, `BU-D10` pendiente) | Concesiones quedan no-efectivas, se conservan | — | — | `CONFIG_CHANGE`/`config` | 403/404 | `test_business_unit_admin.py:318,339,368` · `test_business_units.py:491,521` | `OD-16.e` · `AC-A04/A05/A06` | **YES** |
| B07 | Concesiones de un usuario | GET | `/users/{user_id}/business-units` | — | `ConcesionRead[]{user_id,code,company_id,granted_at,revoked_at,is_effective}` — **incluye revocadas** | `business_units:read` | Usuario fuera de la efectiva → **404** | `company_id` de la concesión = efectiva | `is_effective` = viva∧habilitada∧activa | Histórica = `revoked_at≠null` | — | — | 403/404 | `test_business_unit_admin.py:475,557` | `GA-REM-040` fase 8 · `AC-H11` | **YES** |
| B08 | Candidatos para conceder | GET | `/business-units/{code}/grant-candidates` | — | `CandidatoRead[]{user_id,username,display_name,already_granted}` | **`business_units:create`** (sin `users:read` por diseño) | Activos **de la efectiva**, excluyendo al actor | — | Código desconocido/inactivo → 404; **apagada → 409** | `already_granted` = concesión viva | Sin búsqueda/ID (sin oráculo) | — | 403/404/409 | `test_grant_candidates.py:195-300` | `R-129` · `OD-15 §6` | **YES** |
| B09 | Conceder unidad | POST | `/users/{user_id}/business-units` | `{code}` | 201 `ConcesionRead` | `business_units:create` | Objetivo debe pertenecer a la efectiva (404) | — | Unidad debe estar **habilitada** (si OFF → 409); conceder **no habilita** | Auto-concesión → **403** `SegregacionDeFunciones`; duplicado vivo → idempotente sin auditoría de éxito | sin excepción «admin único» | `PERMISSION_CHANGE`/`users` (solo alta real) | 403/404/409 | `test_access_administration.py:215,226,240` · `test_business_unit_admin.py:549,654` | `OD-15.a/c` · `AC-S01…S04` · `AC-B10` | **YES** |
| B10 | Revocar unidad | DELETE | `/users/{user_id}/business-units/{code}` | — | 200 `ConcesionRead` (`revoked_at`, `is_effective:false`) | `business_units:delete` | Objetivo y unidad de la efectiva | — | Revocar **no deshabilita** la unidad | Marca (`revoked_at`), nunca borra; sin concesión viva → 404 | — | `PERMISSION_CHANGE`/`users` | 403/404 | `test_business_unit_admin.py:415,432,442` | `AC-B11` · `OD-09.e` | **YES** |
| B11 | Resolución efectiva (servicio) | — | `service.unidades_efectivas_por_id` 97-123 | — | códigos | (interna) | Empresa = parámetro del contexto | ∧ `is_enabled` | ∧ concesión viva | Sin concesiones → `[]` (nunca «toda la empresa») | — | — | — | `test_business_units.py:290` · `test_operations_bu_enforcement.py:306` · `test_lots_bu_enforcement.py:300` | `OD-16.f` · `AC-B04` | **YES** |

## Dependencias de permisos (del catálogo canónico)

```
business_units:read    · ver unidades de la empresa y concesiones        (ACL §7 OD-16)
business_units:update  · habilitar/deshabilitar unidades de la empresa
business_units:create  · conceder unidad a un usuario
business_units:delete  · revocar unidad de un usuario
Rol "Administrador de Accesos": exactamente estos 4, SIN users:* y SIN comodín (OD-15 §6)
Super Administrador: comodín ("*", acción, scope all)
```

## Elementos ausentes (MISSING — no inventar)

```
- GET /business-units/catalog o /masters/business-units        → no existe (solo lectura por empresa)
- parámetro company_id en cualquier ruta de unidades           → no existe por diseño
- endpoint de unidades EFECTIVAS de un usuario arbitrario      → solo /users/{id}/business-units (con is_effective)
- superficie HTTP de cambio de empresa de un usuario           → no existe (servicio sin caller)
- búsqueda/ID en grant-candidates                              → no existe (anti-oráculo)
```
