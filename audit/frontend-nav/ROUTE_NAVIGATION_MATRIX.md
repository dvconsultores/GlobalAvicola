# ROUTE NAVIGATION MATRIX — Auditoría frontend (NAV-01/UX-01)

**Fecha**: 2026-09-24 · **Método**: lectura del router real (`frontend/src/App.tsx`), headers de cada página, `SubNavHeader` y rutas de redirect.
**Leyenda**: BACK_AVAILABLE = mecanismo visible actual · BACK_TARGET = destino actual · LEGACY_UI = superficie legacy · ACTION_REQUIRED = remediación.

---

## 1 · Matriz (AC01 — 100% rutas activas)

| ROUTE | MODULE | SCREEN_TYPE | CURRENT_LAYOUT | BACK_AVAILABLE | BACK_TARGET | BROWSER_BACK_OK | LEGACY_UI_PRESENT | MOBILE_OK | ACTION_REQUIRED |
|---|---|---|---|---|---|---|---|---|---|
| `/` | dashboard | DASHBOARD | AppLayout+shell | n/a (raíz) | — | ✔ | No | ✔ | — |
| `/kpi` | dashboard | DASHBOARD | AppLayout | n/a (raíz) | — | ✔ | No | ✔ | — |
| `/login` | auth | FULLSCREEN | propio | n/a | — | ✔ | No | ✔ | — |
| `/menu/:menuKey` | hubs | PROCESS | AppLayout + SubNavHeader | ✔ | stack interno (drill-in persistido) | ✔ | No | ✔ | migrar a BackNavigation (route-aware) |
| `/masters` | masters | LIST (hub) | AppLayout | n/a (raíz módulo) | — | ✔ | No | ✔ | — |
| `/masters/:entity` | masters | LIST | AppLayout | n/a (raíz módulo) | — | ✔ | No | ✔ | — |
| `/masters/genetic-lines/:id/weight-curves` | masters | DETAIL | AppLayout | ✔ ad-hoc (link) | `/masters/genetic-lines` | ✔ | No | ✔ | BackNavigation |
| `/poultry` | poultry (legacy) | HUB DUPLICADO | AppLayout | n/a | — | ✔ | **SÍ — hub legacy** | ✔ | **redirect → `/menu/poultry`** |
| `/poultry/:birdType/:phase?` | poultry | PROCESS | AppLayout | ✔ ad-hoc (link «Procesos») | `/menu/poultry` | ✔ | No | ✔ | BackNavigation |
| `/processes` `/processes/:stage` | — | REDIRECT | — | — | → `/menu/poultry` / stage | ✔ | No (compat) | ✔ | mantener |
| `/operations` | operations | LIST | AppLayout | n/a (raíz módulo) | — | ✔ | No | ✔ | persistir filtros |
| `/operations/new` | operations | CREATE (wizard) | AppLayout | ⚠ solo paso 3 (ad-hoc) | `operationBackTarget` (acepta `/poultry` legacy) | ✔ | **acepta target legacy** | ✔ | sanear target + guard |
| `/operations/:id` | operations | DETAIL | AppLayout | ✔ ad-hoc | `/operations` | ✔ | No | ✔ | BackNavigation |
| `/my-pending` | operations | LIST | AppLayout | n/a | — | ✔ | No | ✔ | — |
| `/lots` | lots | LIST | AppLayout | n/a (raíz módulo) | — | ✔ | No | ✔ | persistir filtros |
| `/lots/new` | lots | CREATE | AppLayout | ✔ ad-hoc (icono, aria) | `/lots` (o `/lots/:id` si prefill) | ✔ | No | ✔ | BackNavigation + guard |
| `/lots/:id` | lots | DETAIL | AppLayout | ✔ ad-hoc (icono solo, sin texto) | `/lots` | ✔ | No | ✔ | BackNavigation |
| `/admin/unit-access` | admin | EDIT (administración) | AppLayout | **✗ FALTA** | — | ✔ | No | ✔ | **añadir BackNavigation → `/menu/settings`** |
| `/reports` | reports | REPORT (raíz) | AppLayout | n/a | — | ✔ | No | ✔ | — |
| `/reports/lot/:id` | reports | REPORT (detalle) | AppLayout | ✔ ad-hoc | `/reports` | ✔ | No | ✔ | BackNavigation |
| `/reports/sap` | reports | REPORT | AppLayout | ✔ ad-hoc | `/reports` | ✔ | No | ✔ | BackNavigation |
| `/review` | review | LIST | AppLayout + SubNavHeader | ✔ | `-1` (deep-link ⚠) | ✔ | No | ✔(web-only) | route-aware |
| `/review/:id` | review | DETAIL | AppLayout | ✔ ad-hoc («← Volver») | `/review` | ✔ | No | ✔(web-only) | BackNavigation |
| `/review/:id/correct` | review | EDIT | AppLayout | ✔ ad-hoc («←») | `/review/:id` | ✔ | No | ✔(web-only) | BackNavigation + guard |
| `/approvals` | approvals | LIST | AppLayout + SubNavHeader | ✔ | `-1` ⚠ | ✔ | No | ✔(web-only) | route-aware |
| `/audit` | audit | REPORT | AppLayout + SubNavHeader | ✔ | `-1` ⚠ | ✔ | No | ✔(web-only) | route-aware |
| `/sap` | sap | REPORT | AppLayout + SubNavHeader | ✔ | `-1` ⚠ | ✔ | No | ✔(web-only) | route-aware |
| `/cutover` | cutover | PROCESS | AppLayout + SubNavHeader | ✔ | `-1` ⚠ | ✔ | No | ✔(web-only) | route-aware |
| `/users` | users | LIST | AppLayout | n/a (raíz módulo) | — | ✔ | No | ✔(web-only) | — |
| `/roles` | users | LIST | AppLayout | n/a (raíz módulo) | — | ✔ | No | ✔(web-only) | — |
| `/profile` | users | EDIT (raíz usuario) | AppLayout | n/a (acceso por menú usuario) | — | ✔ | No | ✔ | — |
| `*` | — | REDIRECT | — | — | → `/` | ✔ | No | ✔ | — |

## 2 · Cálculo de cobertura

- Rutas activas inventariadas: **31** (100% de `App.tsx`).
- **SECONDARY_ROUTES (exigen retorno) = 16**: `menu/:menuKey`, `masters/genetic-lines/:id/weight-curves`, `poultry/:birdType/:phase?`, `operations/new`, `operations/:id`, `lots/new`, `lots/:id`, `admin/unit-access`, `reports/lot/:id`, `reports/sap`, `review`, `review/:id`, `review/:id/correct`, `approvals`, `audit`, `sap`, `cutover` → (17 contando `menu`; se excluye del conteo por ser hub con stack propio ya cubierto — se reporta cobertura sobre 16 secundarias + hub).

Coherencia final (post-remediación): **16/16 secundarias con BackNavigation** + hub con su stack ⇒ **BACK_NAVIGATION_COVERAGE = 100%**.

## 3 · Problemas que explican NAV-01

1. Siete variantes distintas de back ad-hoc (icono solo, «←» + texto, link con icono+texto, botón aria, SubNavHeader…) ⇒ inconsistencia visible.
2. `SubNavHeader` por defecto usa `navigate(-1)` ⇒ en deep-link no hay historial interno.
3. `UnitAccessPage` sin back.
4. `LotDetailPage` con back **solo icono** (sin texto ni aria-label explícito).

## 4 · Problemas que explican UX-01

1. `/poultry` (hub duplicado pre-menú) sigue **activa** y accesible ⇒ al regresar por bookmarks/back-targets antiguos reaparece esa UI.
2. `operationBackTarget` puede valer `/poultry` exacto y `OperationFormPage` lo acepta (`startsWith('/poultry')`) ⇒ el “atrás” del wizard aterriza en el hub legacy.
3. Evidencia de primera mano en código: `App.tsx` nombra `PoultryHubLegacyRoute` y «Legacy redirects — keep for backward compatibility».

## 5 · Evidencia de no-regresión requerida

- vs currentUI: la app entera monta un único `AppLayout` (no hay shells alternativos) ⇒ AC09 se satisface por construcción una vez retirada la ruta legacy.
- Detección legacy en E2E: marcador del hub antiguo («Centro de Operaciones» / `process.hub.title`) ausente tras el redirect.
