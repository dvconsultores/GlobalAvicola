# AUDIT TASKS — atómicas y verificables

Cada tarea: ID · capacidad · fuente · expectativa UX · actor · empresa · BU · dependencia backend · dependencia frontend · paso runtime · evidencia requerida · regla de clasificación · resultado.

Regla: sin tareas tipo "revisar frontend". Cada una es verificable y con resultado registrado.

---

## Grupo A — Multiempresa y contexto

### T-01 · Selector de empresa (actor global)
- **Capacidad**: cambiar de empresa efectiva · **Fuente**: `docs/02 §3.1.4` ((futuro)) · `OD-14` · `PHASE_9_DEPENDENCY_PREFLIGHT` §2 · **Actor**: Super Admin · **Empresa**: n/a (global) · **BU**: n/a
- **Backend**: `GET /masters/companies` (catálogo seguro, R-127/OD-18) + `POST /switch-company` — ambos **desplegados** (405/401) · **Frontend**: `company.store.ts` + dropdown `Header.tsx` — **en repo y en bundle desplegado**
- **Runtime**: dropdown visible solo si `is_super_admin` y `(activeCompanyName || company_name)`; carga con `catch {}` silencioso
- **Evidencia**: código (trazado), bundle (strings `company.selector`/`company.switching`), runtime sin sesión (401) · **Clasificación**: IMPLEMENTED_BUT_NOT_EXPOSED
- **Resultado**: ✅ clasificada · secundarios: render condicionado, solo super-admin (por diseño `OD-14`), fallo de carga indistinguible; verificación funcional pendiente de cuenta autorizada.

### T-02 · Contexto de empresa visible (actores de empresa)
- **Capacidad**: ver la empresa en la que se opera · **Fuente**: `OD-11`, `docs/02 §3.1.4` · **Actor**: todos
- **Frontend**: badge estático en Header + indicadores en Dashboard/Profile/Sap/Process (reutiliza `activeCompanyName || company_name`)
- **Runtime**: presente en bundle desplegado (strings verificados)
- **Clasificación**: BLOCKED_AUTHENTICATED_VERIFICATION (desplegado, sin defecto estático localizado)
- **Resultado**: ✅ registrada; pendiente prueba con sesión.

### T-03 · Administración de empresas (metadatos app-owned)
- **Capacidad**: editar metadatos de empresa desde la app · **Fuente**: `docs/02 §3.2.1` · `R-124`/`AOD-06` (origen SAP sin decidir) · `OD-18.b` (escritura `sap_config` diferida)
- **Estado**: la expectativa de propiedad (SAP vs local) sigue sin decidirse → **OWNER_DECISION_REQUIRED** (ya gobernado por `R-124`; no se duplica)
- **Resultado**: ✅ referenciada a R-124/AOD-06.

## Grupo B — Unidades de negocio

### T-04 · Habilitar/deshabilitar unidades por empresa
- **Capacidad**: administrar las 4 unidades de una empresa · **Fuente**: `GA-REM-040 T-040-21` · `AC-H04` · `OD-16.b/e` · **Actor**: Administrador de Accesos / Super Admin · **BU**: las 4
- **Backend**: `GET /business-units` · `PATCH /business-units/{code}/enable|disable` — **desplegado** (401) · **Frontend**: **0 referencias** (`business-units` 0 en bundle local y desplegado)
- **Runtime**: no existe pantalla · **Clasificación**: FRONTEND_MISSING
- **Resultado**: ✅ clasificada · fase 9 `FROZEN` (causa: autorización del propietario).

### T-05 · Conceder/revocar unidades a un usuario
- **Capacidad**: administrar acceso por unidad · **Fuente**: `T-040-22` · `AC-H05` · `OD-15/OD-16` · `R-129` (candidatos sin `users:read`)
- **Backend**: `GET /business-units/{code}/grant-candidates` · `POST/DELETE /users/{id}/business-units` — **desplegado** (401) · **Frontend**: **0 referencias** (`grant-candidates` 0 en ambos bundles)
- **Runtime**: no existe pantalla · **Clasificación**: FRONTEND_MISSING
- **Resultado**: ✅ clasificada.

### T-06 · Menú y rutas adaptados a unidad + RBAC (navegación dinámica)
- **Capacidad**: que la navegación refleje permisos, unidades de empresa y unidades concedidas; estado "sin unidades" · **Fuente**: `T-040-23` · `AC-H02/03/06` · `R-119/H360-F01` · `docs/02 §3.1.3`
- **Frontend**: `navigationConfig.ts` estático sin campo de permiso/módulo/unidad; 0 `hasPermission`; `ProtectedRoute.roles` muerto · **Runtime desplegado**: menú completo para todos
- **Clasificación**: FRONTEND_MISSING
- **Resultado**: ✅ clasificada · secundario: R-98/R-119 vigentes.

### T-07 · Bandeja de clasificación pendiente
- **Capacidad**: resolver eventos sin unidad clasificada · **Fuente**: `T-040-24` · `AC-H07` · `OD-10.c`
- **Backend**: `GET /operations/pending-classification` — **desplegado** (401) · **Frontend**: 0 referencias
- **Clasificación**: FRONTEND_MISSING · **Resultado**: ✅ (fase 9, ítem 4).

### T-08 · Diferenciación visible de las 4 unidades (entradas productivas)
- **Capacidad**: identificar y entrar a Progenitoras/Reproductoras/Incubadora/Engorde · **Fuente**: `OD-16.a` · `docs/02 §3.4` · **Actores**: operativos
- **Frontend/runtime**: hub `/poultry` con las 4 unidades y etapas — presente en local y **en bundle desplegado** (`/poultry` ×30)
- **Clasificación**: BLOCKED_AUTHENTICATED_VERIFICATION (estructura desplegada; sin defecto estático localizado; gating por unidad ausente = T-06)
- **Resultado**: ✅; secundarios: Progenitoras (T-30) e Incubadora (T-31) con capacidades nuevas sin desplegar.

## Grupo C — Usuarios, roles y permisos

### T-09 · Alta/edición/desactivación de usuarios
- **Fuente**: `docs/02 §3.1.2` · `GA-REM-002 AC13–16` · **Backend**: `/users` desplegado · **Frontend**: `UsersPage` en ambos bundles
- **Clasificación**: BLOCKED_AUTHENTICATED_VERIFICATION · secundarios: columna Empresa ausente (R-122, vigente); en el bundle desplegado persiste el patrón "denegación = tabla vacía" (R-120 corregido solo en local → parte de R-99)
- **Resultado**: ✅.

### T-10 · Administración de roles y permisos
- **Fuente**: `docs/02 §3.1.3` · `GA-REM-034` · **Backend**: `/roles` + catálogo de permisos desplegados · **Frontend**: `RolesPage` en repo local (sin enlace de navegación: sólo URL); **ausente del bundle desplegado** (`/roles` 1→7, sin ruta en el bundle servido)
- **Clasificación**: DEPLOYMENT_STALE · **Evidencia**: diff de bundles + pruebas de ruta del router en cada bundle
- **Resultado**: ✅.

### T-11 · Asignación de rol a usuario en su empresa
- **Fuente**: `OD-13/OD-15` · **Backend**: `/users` (rol) — desplegado · **Frontend**: formulario de usuario con selector (local y desplegado)
- **Clasificación**: BLOCKED_AUTHENTICATED_VERIFICATION · **Resultado**: ✅.

## Grupo D — Capacidades operativas (las cuatro unidades y núcleo)

### T-12 · Recepción de aves (P-01) · T-13 · Control diario (P-02) · T-14 · Revisión/corrección/aprobación (P-07) · T-15 · Lotes (P-06) · T-16 · Reportes (P-15) · T-17 · Auditoría (P-09) · T-18 · SAP (P-08 parcial)
- **Fuente**: `docs/02`, procesos certificados `PROCESS-0x` · **Backend**: desplegado (sondas 401)
- **Frontend**: rutas y páginas existentes en ambos bundles
- **Clasificación**: BLOCKED_AUTHENTICATED_VERIFICATION (sin defecto nuevo localizado en esta auditoría; los defectos conocidos ya están gobernados por R-130…R-180)
- **Resultado**: ✅ registradas; la certificación de proceso sigue `BLOCKED_RUNTIME` (WAVE B) hasta ejecutar E2E.

### T-19 · Formulario de operación — contrato con backend
- **Fuente**: `FORM_API_CONTRACT_GAP_MATRIX.md` · **Hallazgo**: R-171 (catálogo incubadora, corregido en local, no desplegado), R-177 (ovoscopía, `AOD-24`), B01/B13 (campos nuevos locales)
- **Clasificación**: DEPLOYMENT_STALE (parcial: catálogo) + OWNER_DECISION_REQUIRED por R-177/AOD-24 (vigente, referenciado)
- **Resultado**: ✅.

## Grupo E — Despliegue

### T-20 · Verificar que el frontend desplegado sigue a `main`
- **Fuente**: `R-99` · **Prueba**: fingerprint (`Last-Modified` 2026-09-05 14:09:27 GMT re-medido hoy) + build local distinto + causa raíz reproducida (`tsc -b` rojo en HEAD; verde en `f46cb13`; rojo en los 15 commits posteriores)
- **Clasificación**: DEPLOYMENT_STALE (global, demostrado) · **Resultado**: ✅ causa raíz incorporada como addendum a R-99 (commit local).

### T-21 · Backend desplegado vs frontend desplegado
- **Prueba**: sondas 401 de `business-units`, `grant-candidates`/`users/{id}/business-units`, `pending-classification`, `reversals`, `notifications` → backend NUEVO; bundle → frontend VIEJO
- **Resultado**: ✅ "CURRENT BACKEND + STALE FRONTEND" demostrado.

### T-22 · PWA/caché como causa
- **Prueba**: el servidor sirve el mismo `index.html` (`Last-Modified` inmutable) y el mismo hash que la medición del 2026-09-07; la causa no es caché del cliente
- **Resultado**: ✅ excluida.

## Grupo F — Flujos autenticados (bloqueado)

### T-23 · Permutaciones rol×empresa×unidad (J02–J07) · T-24 · Zero-BU (J07) · T-25 · BU OFF / grant OFF (J03–J05) · T-26 · Persistencia/refresh/relogin (J03/J04) · T-27 · Direct-route autorizado/denegado (J06) · T-28 · Jornadas J08–J18
- **Estado**: ⛔ `AUTHENTICATED_RUNTIME_BLOCKER` — sin cuentas autorizadas del entorno compartido (§38). Cuentas necesarias: Super Admin, Administrador de Accesos, Supervisor Avícola, Operador, Contraloría, y un usuario multicompañía; empresas con las cuatro unidades en estados mixtos.
- **Resultado**: pendiente de la entrega de cuentas por el propietario; ninguna conclusión inventada.

## Grupo G — Despliegue específico por capacidad (nuevas capacidades locales)

### T-29 · Notificaciones internas (campana) · T-30 · Plan de importación de Progenitoras · T-31 · Catálogo de incubadora (mortalidad/descarte) · T-32 · Curvas de peso (administración) · T-33 · Áreas (maestro) · T-34 · Cuadre/pesos de recepción (B01/B02) · T-35 · Agua (B05) · T-36 · UX de denegación en `/users` (R-120)
- **Prueba por capacidad**: marcador en bundle local ausente del desplegado (`/notifications`, `import_plan`, `chicks_healthy`, `dead_on_arrival`, `weight-curves`…)
- **Clasificación**: DEPLOYMENT_STALE · **Resultado**: ✅
