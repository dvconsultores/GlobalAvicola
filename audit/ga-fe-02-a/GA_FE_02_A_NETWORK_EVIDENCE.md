# GA-FE-02-A · NETWORK EVIDENCE (§61) — corrida autenticada 2026-09-11 (GA-FE-02-C)

**Sanitizado**: aquí no hay contraseñas, `Authorization`, cookies, tokens ni `storageState` —
solo actor, método, ruta, estado y el cuerpo **semántico** de la operación. Fuente: captura
automática `context.on('response')` del runner Playwright local (desktop 1440×900 y móvil
390×844) + llamadas API directas con sesiones propias de cada actor.

## Mutaciones observadas en la corrida (UI)

| Actor | Método | Ruta | Estado | Cuerpo semántico |
|---|---|---|---|---|
| E (bootstrap) | POST | `/login` | 200 | credenciales → sesión (valor no registrado) |
| E | POST | `/switch-company` | 200 | `{"company_id":1}` → contexto Avícola Global C.A. |
| E | POST | `/switch-company` | 200 | `{"company_id":3}` → contexto Avícola Del Sur C.A. |
| E | POST | `/switch-company` | 200 | vuelta a `{"company_id":1}` |
| A | POST | `/login` | 200 | sesión de fixture A |
| A | PATCH | `/business-units/broiler/enable` | 200 | UI «Activar» → Engorde habilitada |
| A | PATCH | `/business-units/broiler/disable` | 200 | UI «Desactivar» → Engorde apagada (1 sola por clic) |
| A | PATCH | `/business-units/broiler/enable` | 200 | UI «Activar» (rehabilitar; AC-A06) |
| B | POST | `/login` | 200 | sesión de fixture B |
| B | POST | `/users/73/business-units` | 201 | UI «Conceder» Engorde → C (concesión viva y efectiva) |
| B | DELETE | `/users/73/business-units/broiler` | 200 | UI «Revocar» → concesión con `revoked_at` |
| B | POST | `/users/72/business-units` | **403** | auto-concesión directa → `"administrar el acceso no autoriza a concedérselo a uno mismo"` (OD-15.a) |
| B | POST | `/users/75/business-units` | **404** | concesión a usuario de otra empresa → `usuario 75` (sin distinguir del que no existe) |
| D | POST | `/login` | 200 | sesión de fixture D |
| D | GET | `/admin/unit-access` (SPA) | 200 | superficie **no renderizada** (alerta de permiso; ver §E2E-08) |
| D | GET | `/business-units` | **403** | sin `business_units:read` |
| D | PATCH | `/business-units/broiler/enable` | **403** | sin `business_units:update` |
| D | POST | `/users/73/business-units` | **403** | sin `business_units:create` |
| D | DELETE | `/users/73/business-units/broiler` | **403** | sin `business_units:delete` |
| M-A (móvil) | PATCH | `/business-units/broiler/disable` | 200 | UI móvil «Desactivar» |
| M-A (móvil) | PATCH | `/business-units/broiler/enable` | 200 | UI móvil «Activar» |
| M-B (móvil) | DELETE | `/users/73/business-units/broiler` | 200 | UI móvil «Revocar» |
| E | POST | `/lots` | **403** | alta de lote del actor global sin concesión → `"sin empresa efectiva con unidades de negocio habilitadas"` (R-163 cierra escrituras) |
| E | PATCH | `/business-units/broiler/disable` | 200 | restauración de estado (control plane) |

## Inspecciones (lecturas) correlacionadas

| Actor | Método | Ruta | Estado | Lectura |
|---|---|---|---|---|
| A | GET | `/business-units` | 200 | 4 filas canónicas con estados (`breeder/broiler/grandparent/hatchery`) |
| B | GET | `/business-units/broiler/grant-candidates` | 200 | 26 candidatos; **sin** `ga-fe02-b` (el actor no se ofrece) y **sin** `ga-fe02-x` (otra empresa) |
| B | GET | `/users/73/business-units` | 200 | concesión viva `is_effective=true` tras conceder; `revoked_at` tras revocar |
| C | GET | `/me` | 200 | `effective_business_units` = `["broiler"]` con concesión efectiva; `[]` sin ella |
| C | GET | `/lots?limit=100` | 200 | **ALLOW** = 2 filas `L-BO-2026-05/06`; **DENY** = 0 filas (row-scope por unidad, `false()` sin unidades efectivas) |
| D | GET | `/lots?limit=100` | **403** | RBAC NO (`lots:read` ausente) — MX-3 |
| E | GET | `/lots?limit=100` | 200 | 8 filas — lecturas del actor global **sin row-scope** (excepción declarada GA-REM-002/GA-REM-040 fase 3; ver divergencia D-1) |
| E | GET | `/audit?module=config&entity_type=company_business_unit&limit=200` | 200 | 14 filas `config_change` (actor/empresa/objetivo/timestamp) |
| E | GET | `/audit?module=users&entity_type=user_business_unit&limit=200` | 200 | 15 filas `permission_change` |

## Correlación UI → API → estado fresco

Cada mutación de UI quedó correlacionada con: (1) la petición anterior, (2) el `toast` de
éxito, (3) un `GET` fresco contra el backend y (4) un hard-refresh — sin estados
optimistas falsos (las negativas del backend muestran el error y reconcilian por refetch,
`admin.units.saveError` / `admin.grants.saveError`). Detalle por paso en
`GA_FE_02_A_AUTHENTICATED_RUNTIME_CERTIFICATION_EVIDENCE.md` §5–6.

```
Secretos capturados ........ 0 (registro solo de método/ruta/estado/cuerpo semántico)
Cabeceras registradas ...... ninguna
Tokens en documentos ....... 0
```
