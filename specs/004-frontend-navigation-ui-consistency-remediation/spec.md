# SPEC — Frontend Navigation & UI Consistency Remediation (NAV-01 / UX-01)

**Feature Branch**: `specs/004-frontend-navigation-ui-consistency-remediation`
**Fecha**: 2026-09-24 · **Clasificación**: `POST_CERTIFICATION_FRONTEND_REMEDIATION` · **SAP scope**: NONE
**No reabre PRE-SAP** · frontend-only · no toca SAP/SAP-SOAP-1/backend (salvo estrictamente necesario — no se requirió).

---

## PURPOSE

Eliminar los dos defectos transversales detectados por el Owner durante navegación manual:

- **NAV-01**: en múltiples pantallas internas no existe mecanismo visible, consistente y predecible para regresar.
- **UX-01**: al navegar y regresar, determinadas rutas vuelven a mostrar UI/UX legacy (la entrada duplicada `/poultry` y los back-targets que apuntan a ella) en lugar del estándar visual actual.

## CURRENT_UI_STANDARD (definido desde código, nombres reales)

| Elemento | Implementación canónica |
|---|---|
| Shell | `components/layout/AppLayout.tsx` + clases globales `app-content-shell-*` (sin `max-w-* mx-auto` locales) |
| Navegación | `data/navigationConfig.ts` (única fuente) → `Sidebar`/`MobileDrawer`/`MobileNav` |
| Menú por área | `pages/operations/MenuHubPage` (`/menu/:menuKey`, grilla `MenuCard`, stack persistido) |
| Sub-cabecera | `components/layout/SubNavHeader.tsx` (título + breadcrumbs + back) |
| Etapa operativa | `pages/operations/ProcessStagePage` (vista moderna, usada por `/poultry/:birdType/:phase?`) |
| UI kit | `components/ui/**` (Button, Card, ConfirmDialog, EmptyState…), `components/data-table/**` |
| i18n | `common.back` = «Volver» (ES) / «Back» (EN) |

## LEGACY_UI (inventario — detalle en `audit/frontend-nav/LEGACY_UI_INVENTORY.md`)

| Elemento | Estado detectado | Acción |
|---|---|---|
| Ruta `/poultry` → `ProcessHubPage` (hub duplicado de la era pre-menú) | **ACTIVA** — entra por bookmarks/back-targets antiguos ⇒ UX-01 | **Retirar de la superficie activa**: redirect a `/menu/poultry` (historia preservada) |
| `PoultryHubLegacyRoute` + import en `App.tsx` | wrapper legacy | eliminar |
| `OperationFormPage` step-3 acepta `operationBackTarget = '/poultry'` | back-target que aterriza en el hub legacy | restringir a `/poultry/<…>` profundas y `/menu/**`; fallback `/menu/poultry` |
| `/processes(/:stage)` → redirect | backward-compat legítima | mantener |
| `PoultryHubPage`/`ProcessHubPage` files | historia | conservar en repo, sin ruta |

**Objetivo**: `LEGACY_ACTIVE_ROUTES = 0`.

## NAVIGATION CONTRACT (nuevo, vinculante para pantallas secundarias)

Tipos de pantalla: `LIST · DETAIL · CREATE · EDIT · PROCESS · REPORT · DASHBOARD · FULLSCREEN`.
Reglas base: `LIST→DETAIL→LIST`, `DETAIL→EDIT→DETAIL`, `LIST→CREATE→(success) DETAIL|LIST · (cancel) LIST`, `PROCESS→origen`, `REPORT→parent`, `DASHBOARD/FULLSCREEN` sin back.

**Cadena de resolución del back (BackNavigation)** — nunca depende solo de `navigate(-1)`:
1. **preferred**: `to` explícito (parent route-aware declarado por la pantalla);
2. **fallback**: historial interno de la SPA si existe (no salió de la app);
3. **final fallback**: ruta canónica del módulo (`fallbackTo`, por defecto `/`).

**Componente**: `components/layout/BackNavigation.tsx` — icono + texto (nunca solo icono), i18n `common.back`, touch target ≥36px, `data-testid="back-navigation"`, posición uniforme al inicio del contenido, props `{ to?, fallbackTo?, label?, dirty?, onDiscard? }`. `SubNavHeader` lo reutiliza internamente (sin duplicar lógica).

## REQUIREMENTS

- **FR-01** Inventario completo de rutas con la matriz `ROUTE…ACTION_REQUIRED` (AC01) → realizado.
- **FR-02** BackNavigation único y reutilizable; prohibido duplicar lógica ad-hoc (AC02–AC04).
- **FR-03** Migrar TODOS los back ad-hoc (7 variantes detectadas) al componente (cobertura 100% de secundarias).
- **FR-04** Rutas sin back ⇒ añadirlo (UnitAccessPage) / route-aware (SubNavHeader en deep-link).
- **FR-05** UX-01: `/poultry` fuera de la superficie activa; back-targets saneados (AC07–AC09).
- **FR-06** Preservar filtros de listado donde existan (LotListPage `birdType`; OperationListPage `lotId`/`eventType`) con persistencia de sesión ya empleada en el repo (`sessionStorage`) (AC10).
- **FR-07** Contexto company/BU intacto (stores globales; sin cambios) (AC11–AC12).
- **FR-08** RBAC: BackNavigation nunca elude guards (es navegación; guards siguen decidiendo) (AC13).
- **FR-09** Cambios sin guardar (CREATE/EDIT): `useUnsavedChangesGuard` (beforeunload) + confirmación en BackNavigation/salidas (AC14).
- **FR-10** i18n ES/EN (paridad; sin literales hardcodeados) (AC15).
- **FR-11** Mobile 360/390/desktop sin solapes ni overflow del back (AC16–AC18).
- **FR-12** Deep-link con back correcto y fallback canónico (AC19).
- **FR-13** Regresión: vitest completo + `tsc -b` + build (AC20) + E2E navegación nuevo spec (AC21).

## ACCEPTANCE CRITERIA

| AC | Criterio | Evidencia |
|---|---|---|
| AC01 | 100% rutas secundarias inventariadas | `audit/frontend-nav/ROUTE_NAVIGATION_MATRIX.md` |
| AC02 | Toda DETAIL tiene retorno visible | matrix + E2E |
| AC03 | Toda EDIT tiene retorno coherente | idem |
| AC04 | Toda CREATE tiene cancel/return coherente | idem |
| AC05 | Browser Back funciona en rutas auditadas | E2E |
| AC06 | Browser Forward funciona tras Back | E2E |
| AC07 | 0 rutas activas con layout legacy | matrix + E2E (redirect `/poultry`) |
| AC08 | No reaparece UI legacy al regresar | E2E (marcador ausente) |
| AC09 | Todas las rutas usan AppShell/layout actual | matrix (única `AppLayout`) |
| AC10 | Filtros/pagina listado preservados donde corresponde | E2E + unit |
| AC11 | Company context preservado | E2E |
| AC12 | BU context preservado | E2E |
| AC13 | RBAC no evadible vía Back | guards intactos (no se tocan) + E2E 403 |
| AC14 | Unsaved changes protegidos | unit hook + E2E/unit dialog |
| AC15 | i18n ES/EN completo | paridad + tests |
| AC16 | 360px PASS | E2E |
| AC17 | 390px PASS | E2E |
| AC18 | Desktop PASS | E2E |
| AC19 | Deep-link navigation PASS | E2E |
| AC20 | Frontend regression PASS | vitest + tsc + build |
| AC21 | E2E navigation regression PASS | `e2e/navigation-consistency.spec.ts` (spec nuevo, autónomo) |

## CLARIFICATIONS (resueltas por evidencia del repo)

1. **¿Hay un componente de back?** Sí: `SubNavHeader` (6 usos) + 7 variantes ad-hoc en el resto. No hay `BackNavigation` reutilizable como tal → se crea reutilizando el patrón visual existente (no se inventa un tercer estilo).
2. **¿Cuál es la “UI legacy” de UX-01?** La entrada duplicada `/poultry` (`ProcessHubPage`) conservada “for backward compatibility” junto al nuevo `/menu/poultry`, más back-targets antiguos que aterrizan en ella. Evidencia: `App.tsx` la envuelve como `PoultryHubLegacyRoute` y el comentario “Legacy redirects”.
3. **¿Se elimina `ProcessHubPage`?** No: se retira la **ruta** (redirect), el archivo queda como historia. Cero borrado de producto no necesario.
4. **¿navigate(-1) sirve?** No como base: falla en deep-link (el usuario llegó por URL). Se mantiene como *fallback* intermedio del contrato.
5. **¿Filtros con qué mecanismo?** El repo ya usa `sessionStorage` para stacks (`menuHubStack:*`, `operationBackTarget`); se extiende el mismo mecanismo (no se introduce uno nuevo).
6. **¿Unsaved-changes con `useBlocker`?** No aplicable: la app usa router declarativo (`<Routes>`), `useBlocker` exige data router. Se implementa guard propio: `beforeunload` + confirmación en salidas del componente (patrón sin `alert/prompt` nativos, conforme a la casa).
7. **¿Backend?** No se toca: el comportamiento es 100% frontend (guards/RBAC intactos).
