# Research — 004 Frontend Navigation & UI Consistency Remediation

**Fecha**: 2026-09-24 · Fuentes: código real del frontend (router, pages, componentes, tests), auditorías UI previas (`GLOBAL_AVICOLA_UI_UX_NAVIGATION_AUDIT.md`), memoria de repo.

---

## 1 · Estado de partida (evidencia)

- Router declarativo (`<Routes>` en `App.tsx`; `BrowserRouter` en `main.tsx`). React Router 7.
- Back existente: `SubNavHeader` (6 páginas) con default `navigate(-1)`; 7 variantes ad-hoc en el resto (icono solo, «← texto», links con icono, botón aria).
- Pantalla sin back: `UnitAccessPage`. Pantalla con back solo-icono sin aria: `LotDetailPage`.
- UX-01: ruta `/poultry` (hub duplicado) activa + `operationBackTarget` puede apuntar a ella.
- Contexto: `MenuHubPage` persiste stack (`sessionStorage.menuHubStack:*`); `ProcessStagePage`/`OperationTile` persisten `operationBackTarget`; filtros de listados viven en estado React (se pierden al navegar).
- Unsaved-changes: **no existe** ningún mecanismo (`beforeunload`/blocker ausentes en todo `src/`).
- i18n: `common.back` ya es «Volver»/«Back»; paridad ES/EN verificada en tests del repo.
- Tests FE baseline: **87 files / 524 tests PASS** (2026-09-24).

## 2 · Mecanismos evaluados (antes de introducir nuevos)

| Mecanismo existente | Evaluación | Decisión |
|---|---|---|
| `SubNavHeader` | patrón visual correcto, pero `navigate(-1)` insegura en deep-link | **reutilizar como base** del nuevo `BackNavigation` (no crear un tercer estilo) |
| `sessionStorage` (`menuHubStack:*`, `operationBackTarget`) | ya usado para preservar contexto | extender al mismo mecanismo para filtros |
| `useBlocker` (RR7) | requiere data router; la app es declarativa ⇒ lanza | descartado; guard propio `beforeunload` + diálogo |
| `ConfirmDialog` (ui) | componente canónico, sin `alert/prompt` nativos | usar para confirmar salida con cambios |
| `window.confirm` | prohibido por convención del repo (R-197 AC20) | descartado |

## 3 · Matriz de rutas

Ver `audit/frontend-nav/ROUTE_NAVIGATION_MATRIX.md` (AC01) y `LEGACY_UI_INVENTORY.md` (AC07-09).

## 4 · Riesgos identificados

| Riesgo | Mitigación |
|---|---|
| Tests existentes que renderizan `/poultry` esperando el hub (`r220.loteB7`, `gaFe03.routeGuards`) | actualizar a la nueva verdad (redirect) — la spec es anterior; el comportamiento nuevo es el canónico |
| Cambios en páginas con lógica compleja (wizard, review) | edición mínima y quirúrgica: reemplazo del header/back, sin tocar lógica de negocio |
| Intercepción de browser-back con formularios sucios | sentinel `pushState` + popstate + ConfirmDialog; documentado en el hook |
| E2E depende de backend | spec nuevo **autónomo** con `page.route()` (stubs), ejecutable sin backend; la suite de procesos completa sigue requiriendo el entorno vivo |
