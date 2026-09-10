# NAVIGATION ↔ ROLE / COMPANY / BU MATRIX

**2026-09-10** · base `3808ed5` · auditoría de exposición (no de seguridad: el backend es la autoridad y ya está certificado como tal).

Fuente del menú: `frontend/src/data/navigationConfig.ts` — **array estático**, sin campo de permiso, módulo ni unidad. Única variación: `view_type` (móvil recorta a «Gestión Avícola»).

## 1. Estado de exposición por entrada de menú

| Entrada | Ruta | Capacidad | ¿Se muestra a autorizados? | ¿Se oculta a no autorizados? | URL directa protegida | Runtime (bundle 09-05) | Estado |
|---|---|---|---|:--:|---|---|---|
| Dashboard | `/` | CAP-OPS-12 | sí | **no** (todos) | solo sesión | ✅ | producto enseña puertas abiertas a todos |
| Gestión Avícola (Progenitoras/Reproductoras/Incubadora/Engorde) | `/poultry/*` | CAP-BU-01 | sí | **no** | solo sesión | ✅ | unidad en la URL sin chequeo de unidad |
| Centro de Revisión (Pendientes/Aprobados/Devueltos) | `/review*` | CAP-OPS-07 | sí | **no** (`WebOnly` sólo bloquea móvil) | solo sesión | ✅ | — |
| Aprobaciones | `/approvals` | CAP-OPS-07 | sí | **no** | solo sesión | ✅ | — |
| Integración SAP (4 entradas) | `/sap` | CAP-OPS-13 | sí | **no** | solo sesión | ✅ | — |
| Reportes (3 entradas) | `/reports*` | CAP-OPS-12 | sí | **no** | solo sesión | ✅ | — |
| Auditoría | `/audit` | CAP-AUD-01 | sí | **no** | solo sesión | ✅ (vieja) | — |
| Maestros | `/masters` | CAP-MAS-01 | sí | **no** | solo sesión | ✅ | — |
| Usuarios y Roles | `/users` | CAP-ADM-08 | sí | **no** | solo sesión | ✅ | — |
| Mi Perfil | `/profile` | CAP-SES-03 | sí | **no** | solo sesión | ✅ | — |
| *(no existe)* Unidades por empresa | — | CAP-ADM-03 | — | — | — | **ausente** | FRONTEND_MISSING |
| *(no existe)* Unidades por usuario | — | CAP-ADM-04 | — | — | — | **ausente** | FRONTEND_MISSING |
| *(no existe)* Notificaciones | — | CAP-NOT-01 | campana en Header (local) | — | — | **ausente** | DEPLOYMENT_STALE |
| *(no existe)* Reverso | — | CAP-OPS-09 | — | — | — | **ausente** | FRONTEND_MISSING |
| Selector de empresa | Header | CAP-SES-05 | sí (super_admin) | n/a | — | ✅ | IMPLEMENTED_BUT_NOT_EXPOSED |
| Rol en menú | — | — | — | — | — | — | **no hay noción de rol en el menú** |

## 2. La matriz prometida por `GA-REM-040 T-040-23` (fase 9) — objetivo

```
unidad apagada (empresa)          → entrada oculta
unidad encendida · sin concesión  → oculta
unidad encendida · con concesión  → visible
permiso ausente                   → oculta
sin unidades (zero-BU)            → estado explícito «sin unidades» (AC-H06)
```

Hoy: **ninguna de las cinco filas está implementada** (0 `hasPermission`; menú estático). El backend rechaza igual en los tres casos (probado en su programa); la interfaz no distingue.

## 3. Casos de exposición detectados (evidence-based)

| # | Hallazgo | Evidencia | Clase |
|---|---|---|---|
| 1 | El menú completo se dibuja para cualquier sesión; un Operador ve Auditoría/SAP/Usuarios/Roles y al pulsar recibe 403 con pantallas vacías o `alert` | `navigationConfig.ts` estático · F-D 360 · R-98/R-119 | producto (puertas cerradas visibles) |
| 2 | `/poultry/:birdType/:phase?` lleva la unidad en la URL; sin chequeo de cliente ni de API para "unidad no concedida" en esas pantallas (las listas sí filtran) | `FRONTEND_ROUTE_MODULE_MATRIX §2` · R-160/R-165 (backend) | exposición de la unidad |
| 3 | El selector de empresa: visible sólo si `is_super_admin` **y** existe nombre de empresa; si `fetchCompanies` falla, se queda en «Cargando…» sin error | `Header.tsx` 12/22/72 · `company.store.ts` 36-44 | exposición incompleta |
| 4 | Deep links sin sesión redirigen a `/login` (correcto) | probado hoy: `/roles` `/masters/weight-curves` `/notifications` `/poultry/hatchery` `/review` → `/login` | — |
| 5 | En el runtime 09-05, `/roles` no existe como ruta: escribirla lleva a `/login` (sin sesión) o a la home (con sesión) | bundle desplegado (router sin la ruta) | stale |
| 6 | El badge «Empresa» (no selector) usa `activeCompanyName || company_name`; sin empresa no se muestra nada | Header 72/93 | cosmético-informativo |
| 7 | **`/roles` no tiene ningún enlace de navegación** (ni menú ni páginas): la administración de roles sólo es alcanzable escribiendo la URL — y en el runtime servido ni la ruta existe | `App.tsx:238` es la única referencia; 0 enlaces `to="/roles"`; `nav.settings_users` apunta a `/users` | exposición incompleta (local) + stale (runtime) |

## 4. Roles sembrados vs entradas (contexto)

Roles vigentes (seeds + migraciones): Super Administrador (comodín), **Administrador de Accesos** (`OD-15 §6`), Supervisor Avícola (+`reversals:create/read`), Contralor Avícola (+`reversals:read`), Operador de Granja, Aprobador, Analista SAP, Auditor. `users:read` es exclusivo del Super Admin salvo Administrador de Accesos (parcial).

El menú no refleja ninguno: las únicas entradas "administrativas" (Usuarios y Roles) se muestran a todos.
