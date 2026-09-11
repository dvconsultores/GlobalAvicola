# GA-FE-03 · INVENTARIO DE FUENTES DE NAVEGACIÓN

**Base**: `5a3acc9`. Cada fuente con: archivo, componente, origen de rutas, consciencia de
permiso, de BU, de inquilino, duplicación y estatus.

| # | Fuente | Archivo(s) | Origen de las rutas | ¿Permiso? | ¿BU? | ¿Empresa? | Duplicación | Estatus |
|---|---|---|---|---|---|---|---|---|
| 01 | Sidebar (desktop) | `components/layout/Sidebar.tsx` (+`SidebarItem/Section`) | `getNavItemsForViewType(user.view_type)` + `filterNavItemsByPermissions` | **Parcial** — solo entradas con `permission` declarado (hoy 1) | No | No | Consume `NAV_ITEMS` | ACTIVA — paridad con drawer por fuente única |
| 02 | MobileDrawer | `components/layout/MobileDrawer.tsx` | ídem (recorte `view_type=mobile` ⇒ solo `poultry` top-level) | Parcial (misma función) | No | No | Misma fuente que Sidebar | ACTIVA |
| 03 | MobileNav (barra inferior) | `components/layout/MobileNav.tsx` | **Array local hardcodeado** (`poultry`, `home`, `kpi`) | No | No | No | Duplica rutas de `navigationConfig` | ACTIVA — divergirá si no se integra |
| 04 | MenuHub | `pages/operations/MenuHubPage.tsx` | `findNavItem(key, NAV_ITEMS)` — **RAWS** | **No** (no filtra hijos) | No | No | Consume `NAV_ITEMS` sin filtro | ACTIVA — `D-2` reproducido aquí |
| 05 | Atajos del Dashboard | `pages/dashboard/DashboardPage.tsx` (tarjetas «Procesos» por unidad + fases) | `PROCESS_STAGES` (`data/processCatalog.ts`) → `stagePathForKey` | No | No (la unidad va en la URL) | No | Duplica rutas de los hijos de `poultry` | ACTIVA — §33 obliga a misma política |
| 06 | Enlaces de alertas del Dashboard | `DashboardPage` (`/lots/:id`) | Dato del backend (ya acotado) | N/A (dato autorizado) | N/A | Sí (dato) | No | ACTIVA — enlace contextual, no menú |
| 07 | Selector de empresa | `components/layout/Header.tsx` + `stores/company.store.ts` | `is_super_admin` ('por diseño', `OD-14`) | Sí (autoridad global) | No | Sí | No | ACTIVA — permanece visible sin contexto (`F4`) |
| 08 | Breadcrumbs/SubNavHeader | `components/ui/Breadcrumbs.tsx`, `SubNavHeader.tsx` | Derivados de la ruta actual | No | No | No | No | Presentación — no accionable (excepto «Dashboard»→`/`) |
| 09 | Redirects legacy | `App.tsx` (`/processes`, `/processes/:stage`) | `STAGE_PATH_MAP` | No | Parcial (unidad en destino) | No | No | ACTIVA (soporte) — clasificada `LEGACY_SUPPORTED` |
| 10 | Cola de operaciones por evento (`MyPendingPage`, tiles) | páginas de operaciones | Rutas directas | No | Datos | Sí | No | ACTIVA — enlaces de flujo |
| 11 | Acciones de fila de maestros (`WeightCurvesPage`) | `App.tsx` `rowActions` | Derivadas del dato autorizado | Delegado (`masters:read` del listado) | No | Sí | No | ACTIVA |
| 12 | `PermissionRoute` (patrón GA-FE-02) | `App.tsx` | Única ruta: `/admin/unit-access` | Sí | No | No | — | ACTIVA — se reutiliza/extiende como `CapabilityRoute` |

## Duplicaciones declaradas (fuentes únicas tras GA-FE-03)

```
1. MobileNav (03)  → pasa a derivar de la MISMA evaluación que Sidebar/Drawer.
2. MenuHub (04)    → pasa a evaluar el árbol filtrado (no `NAV_ITEMS` crudos).
3. Dashboard (05)  → los atajos de unidad se filtran con el MISMO evaluador.
4. Sidebar/Drawer  → ya comparten fuente; reciben el evaluador único (RBAC + BU + contexto).
```

**Regla de arquitectura** (§23): una sola definición declarativa (`navigationConfig.ts`
extendida con metadatos) + un solo evaluador (`auth/navigation.ts`). Ningún componente
reimplementa política; ninguno usa `if role === …` ni `if username === …` (grep de cierre).

**Rutas sin fuente de menú** (12): `/operations*`, `/my-pending`, `/lots*`, `/reports/lot/:id`,
`/review/:id*`, y redirects. Se rigen por guardas de ruta y backend; sin entradas nuevas salvo
`Roles` (§21/§80).
