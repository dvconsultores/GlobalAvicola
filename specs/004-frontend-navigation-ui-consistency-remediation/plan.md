# Plan — 004 Frontend Navigation & UI Consistency Remediation

**Feature**: `specs/004-frontend-navigation-ui-consistency-remediation` · Frontend-only · Sin backend, sin SAP, sin deploy.

---

## 1 · Alcance técnico

```
A. BackNavigation (componente único)  → B. Migración de 10 pantallas + SubNavHeader route-aware
C. UX-01: retirar /poultry (redirect) + sanear operationBackTarget
D. Contexto: persistir filtros de listados (sessionStorage, mecanismo existente)
E. Unsaved changes: hook + integración en CREATE/EDIT de alto riesgo
F. Tests: unit (componente/hook/páginas tocadas) + E2E autónomo + regresión completa
```

## 2 · Diseño de `BackNavigation`

```tsx
<BackNavigation to? fallbackTo? label? dirty? onDiscard? />
// resolución: 1) props.to  2) historial interno SPA  3) fallbackTo ?? '/'
// render: icono + texto (t('common.back')), aria-label, ≥36px, data-testid="back-navigation"
// dirty: intercepta click → ConfirmDialog (descartar / quedarse); onDiscard → limpia guard y navega
```

`useUnsavedChangesGuard(dirty)`:
- `beforeunload` cuando `dirty` (refresh/cierre).
- Sentinel + `popstate` para browser-back interno cuando `dirty` (volver a empujar y preguntar).
- Expone `confirmLeave()` para que `BackNavigation` resuelva la salida sin duplicar lógica.

## 3 · Fases de implementación

| Fase | Contenido | Archivos |
|---|---|---|
| F1 | Componente + hook + i18n keys | `components/layout/BackNavigation.tsx`, `hooks/useUnsavedChangesGuard.ts`, `locales/es|en/translation.json` |
| F2 | SubNavHeader route-aware (usa el componente) | `components/layout/SubNavHeader.tsx` |
| F3 | Migración back ad-hoc (10 páginas) | LotDetail, LotForm, OperationDetail, ReviewDetail, CorrectionForm, WeightCurves, LotReport, SapComparison, UnitAccess (añadir), ProcessStage |
| F4 | UX-01 legacy | `App.tsx` (redirect `/poultry`), `OperationFormPage.tsx` (target saneado) |
| F5 | Contexto | `LotListPage.tsx`, `OperationListPage.tsx` |
| F6 | Tests | unit nuevos + ajuste de tests afectados + `e2e/navigation-consistency.spec.ts` |
| F7 | Verificación | vitest completo, `tsc -b`, `vite build`, E2E nuevo (vite dev + stubs) |

## 4 · Test plan

| Capa | Qué cubre |
|---|---|
| Unit — `backNavigation.test.tsx` | label i18n, `to` explícito, fallback historial, fallback canónico, diálogo dirty (confirmar/descartar), a11y (aria/testid) |
| Unit — `useUnsavedChangesGuard.test.tsx` | beforeunload on/off, confirmLeave resuelve, popstate no rompe |
| Unit — páginas ajustadas | se re-ejecutan las 87 suites; se corrigen expectativas desactualizadas de `/poultry` |
| E2E — `navigation-consistency.spec.ts` (stubs) | legacy redirect + marcador ausente; menu→stage→back; deep-link fallback; browser back/forward; filtros preservados; mobile 360/390 (visible, sin overflow); desktop |
| Regresión | vitest 524+ (goal: all green), `npm run build` (tsc -b + vite) |

## 5 · Criterios de parada/rollback

- Si un cambio de página rompe su suite y el fix no es trivial ⇒ revertir edición de esa página y reportar `LEGACY_SCREEN_REMAINING` (no estaba el caso esperado).
- Sin cambios en backend/SAP/workflows.
