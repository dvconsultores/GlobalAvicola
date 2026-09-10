# GA-FE-02 · CLARIFICATIONS

Respuestas verificadas contra código en `cb14523` (no supuestas). Fuentes citadas por archivo.

**C-01 · ¿Qué actor administra la habilitación de unidades de la empresa? ¿Con qué permiso?**
La autoridad es por permiso: `business_units:update` sobre la **empresa efectiva**
(`backend/app/business_units/router.py:104-144`). Hoy lo tienen el Super Administrador
(comodín) y el rol **Administrador de Accesos** (`backend/seeds/baseline_seeds.py:89-104`).
Que «habilitar sea acto comercial global y conceder acto operativo de empresa» (`BU-D07`) sigue
pendiente: **un mismo permiso gobierna ambos** y la UI no lo reinterpreta (`OD-16 §7`).

**C-02 · ¿Qué actor administra las concesiones de usuario? ¿Con qué permiso?**
`business_units:create` (conceder) y `business_units:delete` (revocar);
lectura de concesiones: `business_units:read` (`router.py:167-229`). Mismo conjunto del rol
Administrador de Accesos. Segregación: auto-concesión **403 en servidor** (`admin.py:299-345`);
revocación propia permitida (no eleva privilegio, `OD-15.b`).

**C-03 · ¿Qué endpoint lista las unidades de la empresa y su estado?**
`GET /api/v1/business-units` → `[{code, name_key, is_enabled}]`, las **cuatro** unidades
siempre presentes (nunca configurada → `is_enabled:false`) (`router.py:94-101`, `admin.py:114-135`).
**No acepta `company_id`**: la empresa sale del contexto efectivo; sin ella → **403**
(`router.py:58-73`).

**C-04 · ¿Qué endpoints activan/desactivan?**
`PATCH /api/v1/business-units/{code}/enable` y `…/disable`, **sin cuerpo**; código ∈
`grandparent|breeder|hatchery|broiler`; respuesta `HabilitacionRead`; idempotente; auditoría
`CONFIG_CHANGE`/`config` (`router.py:104-144`, `admin.py:137-186`).

**C-05 · ¿Qué endpoint devuelve las unidades (concesiones) de un usuario?**
`GET /api/v1/users/{user_id}/business-units` → `[{user_id, code, company_id, granted_at,
revoked_at, is_effective}]` — **incluye revocadas** (`revoked_at` ≠ null, `is_effective:false`).
Usuario de otra empresa → **404** (`router.py:167-184`, `admin.py:208-231`).

**C-06 · ¿Qué endpoint lista candidatos para conceder?**
`GET /api/v1/business-units/{code}/grant-candidates` → `[{user_id, username, display_name,
already_granted}]`; requiere **`business_units:create`** (deliberadamente **sin** `users:read`,
`R-129`/`OD-15 §6`); usuarios activos de la empresa efectiva, **excluyendo al actor**; unidad
desconocida → 404; unidad **apagada** → **409** (`router.py:146-163`, `admin.py:234-283`).

**C-07 · ¿Cómo se representa una unidad habilitada / una concesión viva / una histórica?**
Habilitada = `CompanyBusinessUnit.is_enabled` (y `BusinessUnit.is_active` a nivel plataforma).
Concesión viva = `user_business_units` con `revoked_at IS NULL`; histórica = `revoked_at` no nulo
(se conserva; puede volver a concederse — índice único parcial `models.py:120-121`).
**Efectiva** = concedida ∧ habilitada ∧ activa: `unidades_efectivas_por_id`
(`service.py:97-123`); `is_effective` en las lecturas de admin (`admin.py:190-206`).

**C-08 · ¿Qué hace el backend si la unidad de la empresa está OFF?**
La operación productiva se deniega para todos los actores (`AC-A05`, enmiendas G/H:
`test_operations_bu_enforcement.py`, `test_lots_bu_enforcement.py`); las concesiones **no se
borran**; las lecturas de control siguen funcionando (la página puede re-habilitar).

**C-09 · ¿Cómo selecciona empresa un actor global? ¿Qué contexto usa un actor normal?**
`POST /api/v1/switch-company {company_id}` — **solo super admin** (403 en otro caso); valida
existencia y `is_active` **en cada petición**; emite token nuevo con claim `company_id` **sin
tocar** `users.company_id` (`auth/service.py:507-541`, `tenancy.py:244-290`). Actor normal:
empresa persistida; una reclamación del token ajena **se ignora** (`OD-11`). El frontend, tras
el cambio, **reemplaza ambos tokens** y vuelve a pedir `/me` (`company.store.ts:47-58` ya lo
hace: `setTokens` + `fetchMe`).

**C-10 · ¿Qué endpoints requieren empresa efectiva?**
Todo `business_units/*` (403 sin ella). `/masters/companies` es **CONTROL_GLOBAL** (super admin
la ve entera sin contexto; actor de empresa solo la suya). `/users` es **INQUILINO** (OD-14.c).

**C-11 · ¿Qué ruta administra usuarios? ¿Existe ya un selector de empresa o UI parcial?**
`/users` (`UsersPage.tsx`, sin detalle por usuario; modal único). Selector de empresa: existe
**solo en el Header y solo para super_admin** (`Header.tsx:71-124`); tienda global
`company.store.ts` (REUSABLE). **Cero** referencias a `business_unit*` en todo `frontend/src`.

**C-12 · ¿Qué partes pertenecen a R-98/R-119 y quedan fuera?**
La ausencia de un helper de permisos global y el filtrado por permiso de toda la navegación son
`R-98`/`R-119`. GA-FE-02 introduce **solo** el helper mínimo y la condición de **sus propias**
entradas; no toca el resto del menú ni `ProtectedRoute.roles` (código muerto) salvo añadir el
guard nuevo de su ruta (patrón existente, `App.tsx:37-68`).

**C-13 · ¿Permite el contrato resolver la UI sin `users:read`?**
Sí: los candidatos llegan por `grant-candidates` (solo `business_units:create`). La pantalla
de concesiones no necesita listar usuarios por `/users`. Para el panel por usuario de
`UsersPage` (actores que **sí** tienen `users:read`) se usa `GET /users/{id}/business-units`.

**C-14 · ¿Qué claves i18n existen?**
`company.*` (selector/switch) ya existen en ES/EN (`public/locales/*/translation.json`).
**No existen** claves `businessUnits.*` en el frontend, pero el **backend ya devuelve**
`name_key` con la forma `businessUnits.*` (semillas `baseline_seeds.py:303-308`): la UI usará
`t(name_key)` con fallback localizado por código (un único mapeo central).

**C-15 · Autoridad de Contraloría en estas pantallas**
Contraloría **no** administra automáticamente unidades ni concesiones (`OD-09 §3`, `OD-16`).
Su visibilidad de control no llega a estas páginas salvo permiso explícito `business_units:*`.

**C-16 · ¿Existe endpoint de candidatos por búsqueda/ID?**
**No** — sin parámetros (sin oráculo de enumeración). La UI lista lo que el contrato da.

**C-17 · ¿El cambio de empresa puede revocarse en caliente?**
Sí: la resolución se re-valida por petición; si la empresa destino se desactiva, el contexto
deja de honrarse (`test_business_unit_guard.py:172`). La UI debe manejar el 401/403 subsecuente
con reconciliación (recargar `/me`).

**C-18 · ¿Qué NO hay que construir aunque parezca natural?**
CRUD de empresas (SAP es autoridad; `OD-18` excluye `sap_config` del catálogo) · gestión del
ciclo de vida de concesiones al apagar/encender (`BU-D10` intocable) · transferencia de empresa
de un usuario (`UserUpdate` no expone `company_id`; servicio sin caller documentado,
`service.py:298-328`) · navegación dinámica global (`GA-FE-03`) · cualquier superficie que
requiera `users:read` para el Administrador de Accesos.
