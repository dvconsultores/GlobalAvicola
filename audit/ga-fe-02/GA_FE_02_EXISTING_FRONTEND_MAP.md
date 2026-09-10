# GA-FE-02 · EXISTING FRONTEND MAP

Inventario verificado en `cb14523` (búsquedas por regex sobre `frontend/src/**`).
Clasificación: **REUSABLE · PARTIAL · DEAD · LEGACY · OUT_OF_SCOPE · MISSING**.

## 1. Contexto de empresa

| Elemento | Ubicación | Estado | Uso en GA-FE-02 |
|---|---|---|---|
| Tienda `company.store` (zustand) | `stores/company.store.ts` (58 líneas): `activeCompanyId/Name`, `companies`, `isSwitching`, `initFromUser`, `fetchCompanies`, `switchCompany` | **REUSABLE** | base directa: `switchCompany` ya hace POST→`setTokens`→`fetchMe` |
| Indicador de empresa (desktop) | `components/layout/Header.tsx:71-124` (dropdown super_admin L75-121; badge estático L90-96) | **REUSABLE** | se conserva; verificar copy empresa efectiva |
| Indicador de empresa (móvil) | `Header.tsx:170-174` | **REUSABLE** | ídem |
| Indicadores sueltos | `DashboardPage.tsx:187-190` · `ProcessStagePage.tsx:65-68` · `SapManagerPage.tsx:82-85` · `ProfilePage.tsx:52-55` | **OUT_OF_SCOPE** (no se tocan) | — |
| Lista de empresas para el selector | `company.store.fetchCompanies` → `GET /masters/companies?limit=100` filtra `is_active!==false` | **REUSABLE** | ídem |
| Sesión extendida (`permissions[]`, listas BU, `effective_company_id`) | `stores/auth.store.ts` `User` L29-43 — **no incluye** los campos de `/me` | **PARTIAL** | ampliar el tipo y `fetchMe` para guardar la sesión extendida |
| Helper de permisos | — (0 coincidencias `hasPermission|permissions.includes|can(`) | **MISSING** | helper mínimo GA-FE-02 (frontera R-98/GA-FE-03) |

## 2. Administración de usuarios

| Elemento | Ubicación | Estado | Uso |
|---|---|---|---|
| `UsersPage` (tabla + modal único; ES/EN; estados 5) | `pages/users/UsersPage.tsx` (modal L111-…; `company_id` select L120-121) | **PARTIAL** | añadir acción "Unidades de negocio" + modal de concesiones (S4) |
| Ruta de detalle de usuario | — (`App.tsx` solo `/users` L235) | **MISSING** | no se crea (modal in-page) |
| `RolesPage` (matriz de permisos con checkboxes; L49-56 `tiene/alternar`) | `pages/roles/RolesPage.tsx` | **OUT_OF_SCOPE** (patrón de checkbox REUSABLE conceptualmente) | no se toca |
| UI de concesiones de unidades | — (0 `business_unit*` en `frontend/src/**`) | **MISSING** | núcleo de GA-FE-02 |
| Duplicación conocida en el modal (bloques repetidos L113-116/L123-126) | `UsersPage.tsx` | **DEAD** (duplicado inocuo, misma binding) | no se refactoriza aquí (fuera de alcance); cambio quirúrgico solo para S4 |

## 3. Navegación y rutas

| Elemento | Ubicación | Estado | Uso |
|---|---|---|---|
| `navigationConfig.ts` (`NAV_ITEMS`, sección admin: `audit`/`masters`/`settings` con hijos `settings_users`→`/users`, `settings_profile`) | `data/navigationConfig.ts:67-206` | **PARTIAL** | añadir UNA entrada hija GA-FE-02 en `settings`, condicionada a permiso |
| Filtrado por permiso de ítems | — (solo `getNavItemsForViewType`) | **MISSING** | mínimo para la entrada GA-FE-02 (no global) |
| `Sidebar`/`MobileDrawer` (consumen `getNavItemsForViewType`) | `Sidebar.tsx:57` · `MobileDrawer.tsx:46,48` | **REUSABLE** | recibir ítems filtrados sin cambiar su lógica |
| `ProtectedRoute` (+`roles?: string[]` **muerto**, sin call sites) | `App.tsx:37-63` | **PARTIAL/DEAD(roles)** | añadir guard por permiso para la ruta nueva (patrón existente; NO reactivar el prop muerto) |
| `WebOnlyRoute` | `App.tsx:65-68` | **REUSABLE** | envolver rutas admin nuevas |
| Ruta `/roles` sin entrada de menú | `App.tsx:238` | **OUT_OF_SCOPE** | no se toca |

## 4. Componentes UI reutilizables (`components/ui/`)

| Componente | Estado | Uso en GA-FE-02 |
|---|---|---|
| `Card/CardHeader/CardBody`, `Button` (variants/`loading`), `Badge`, `Modal` (portal/focus/scroll-lock), `ConfirmDialog` (`variant danger/primary`, `loading`), `EmptyState` (icon/title/action), `SubNavHeader` (título/breadcrumbs/acciones), `FormSection`, `FilterPanel`, `StatusTimeline` | **REUSABLE** | tarjetas de unidad, modal de concesiones, confirmación de apagado, estados vacío/carga |
| `DataTable` (genérico `{id:number}`) | **PARTIAL** | candidatos usan `user_id`; se usa lista propia o mapeo `id=user_id` |
| Toggle/switch estilizado | **MISSING** | usar `Button` (variants) o checkbox con label accesible; sin crear design system |
| `useToast` (`components/Toast.tsx:85`) | **REUSABLE** | feedback éxito/error en S3/S4 |
| `SearchSelect` / `SignaturePad` | **OUT_OF_SCOPE** | no aplican |

## 5. Patrón de datos

| Elemento | Estado | Uso |
|---|---|---|
| `services/api.ts` (axios, baseURL `/api/v1`, refresh single-flight) | **REUSABLE** | todas las llamadas nuevas |
| Patrón de página: `useState` + loader `useCallback` + refetch tras mutación (MasterListPage L44-111, UsersPage L33-87) | **REUSABLE** | convención a seguir en S3/S4 |
| `services/auth.service.ts` (CRUD usuarios tipado) | **PARTIAL** | añadir métodos tipados BU (nuevo `services/businessUnits.service.ts` o dentro de página — se elige servicio tipado) |
| `src/hooks/*` (useMasters etc.) | **DEAD** (definidos, sin importadores) | no usar |
| react-query | **MISSING** (no instalado) | no introducir |
| i18n claves `company.*` | **REUSABLE** | indicador/selector |
| i18n claves `businessUnits.*` | **MISSING** (backend emite `name_key` con esa forma) | añadir ES/EN + mapeo central por código |

## 6. Conclusión de reutilización

```
REUSABLE   company.store · Header indicador/selector · api.ts · Card/Button/Badge/Modal/
           ConfirmDialog/EmptyState/SubNavHeader/FormSection · useToast · Toast · i18n infra
PARTIAL    auth.store (extender sesión) · navigationConfig (1 entrada) · App.tsx (guard ruta) ·
           UsersPage (añadir sección) · DataTable
DEAD       ProtectedRoute.roles · src/hooks/* · duplicado del modal UsersPage
MISSING    página /admin/unit-access · panel concesiones · helper permisos · claves i18n BU ·
           toggle estilizado · método API BU tipado
OUT_OF_SCOPE  R-98/R-119 navegación global · RolesPage · SearchSelect/SignaturePad ·
              indicadores sueltos de empresa en otras páginas
```

**Nada se duplica**: la página nueva usa la arquitectura existente; el panel por usuario vive
dentro de `UsersPage`, no crea un segundo subsistema de usuarios (§36).
