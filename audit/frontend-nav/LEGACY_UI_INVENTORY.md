# LEGACY UI INVENTORY — Detección objetiva (UX-01)

**Fecha**: 2026-09-24 · Evidencia para AC07/AC08/AC09. Regla del repo: no ocultar legacy con CSS; retirar de la superficie activa o reportar.

---

## 1 · Identificadores legacy inventariados

| ID | Componente/Ruta | Evidencia en código | Estado pre-fix | Tratamiento |
|---|---|---|---|---|
| LEG-01 | Ruta `/poultry` → `PoultryHubPage` → `ProcessHubPage` (hub duplicado pre-menú) | `App.tsx:130` (`PoultryHubLegacyRoute`), `App.tsx:255`, wrapper «Legacy redirects» | **ACTIVA** | **Redirect a `/menu/poultry`**; archivos conservados como historia |
| LEG-02 | `PoultryHubLegacyRoute` (wrapper movil→menu) | `App.tsx:130-134` | activo | eliminado (la ruta ya no existe) |
| LEG-03 | Marcadores visuales del hub antiguo | `ProcessHubPage`: `process.hub.eyebrow` «Centro de Operaciones», `process.hub.title` «Elige un Proceso» | visibles en `/poultry` | usados como **marcadores de detección E2E** (deben estar AUSENTES tras el redirect) |
| LEG-04 | `operationBackTarget` aceptando `/poultry` exacto | `OperationFormPage.tsx:2024` (`target.startsWith('/poultry')`) | activo | restringido a `/poultry/<...>` (etapas) y `/menu/**`; fallback `/menu/poultry` |
| LEG-05 | Redirects `/processes(/:stage)` | `App.tsx:257-258` | backward-compat legítima | **mantener** (no es UI legacy; no renderiza) |
| LEG-06 | Back ad-hoc «←» / icono sin texto | ReviewDetail, CorrectionForm, LotDetailPage, etc. | activos | migrados a `BackNavigation` (consistencia, no legacy visual) |

## 2 · Detección objetiva (E2E)

El spec `e2e/navigation-consistency.spec.ts` verifica:
1. `GET /poultry` ⇒ URL final `/menu/poultry` y **ausencia** de «Centro de Operaciones»/«Elige un Proceso».
2. `data-testid="back-navigation"` presente en las pantallas secundarias auditadas.
3. Ninguna ruta activa monta un shell distinto de `AppLayout` (por construcción: único layout del árbol de rutas protegidas).

## 3 · Resultado objetivo

```
LEGACY_COMPONENTS_FOUND (surface activa)      = 1  (LEG-01/LEG-03 hub duplicado + su wrapper)
LEGACY_ACTIVE_ROUTES_BEFORE                    = 1  (/poultry)
LEGACY_ACTIVE_ROUTES_AFTER                     = 0  (redirect; marcador ausente — E2E)
LEGACY_SCREEN_REMAINING                        = none
LEGACY_FILES_KEPT_FOR_HISTORY                  = ProcessHubPage.tsx / PoultryHubPage.tsx (sin ruta)
```
