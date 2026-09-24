# REMEDIATION REPORT — Frontend Navigation & UI Consistency (NAV-01 / UX-01)

**Fecha**: 2026-09-24 · **Clasificación**: `POST_CERTIFICATION_FRONTEND_REMEDIATION` · **SAP scope**: NONE
**Spec**: `specs/004-frontend-navigation-ui-consistency-remediation/` · **SAP-SOAP-1 / backend / workflows**: intactos.

---

## 1 · Resultado antes/después

| Métrica | Antes | Después |
|---|---|---|
| Rutas activas inventariadas | — (sin matriz) | **31** (AC01) |
| Rutas secundarias con back visible consistente | 7 variantes ad-hoc + 1 sin back | **16/16 — BACK_NAVIGATION_COVERAGE = 100%** |
| Componente canónico de back | inexistente (SubNavHeader parcial) | `components/layout/BackNavigation.tsx` (icono+texto, aria, testid, guard) |
| Back en deep-link | `navigate(-1)` (salía de la app) | cadena `to → historial interno → fallbackTo` (route-aware) |
| Rutas activas con UI legacy | **1** (`/poultry` hub duplicado + back-targets legacy) | **0** (redirect a `/menu/poultry`; E2E verifica marcador ausente) |
| Filtros de listado al volver | se perdían | preservados (lots `birdType`; operations `lotId`/`eventType`) — mecanismo `sessionStorage` existente |
| Cambios sin guardar | sin protección | `useUnsavedChangesGuard` (beforeunload + confirmación en back/route) en LotForm, OperationForm exit y CorrectionForm |
| i18n | `common.back` ya correcto | +4 claves ES/EN de diálogo (paridad) |

## 2 · Evidencia de verificación

| Gate | Resultado |
|---|---|
| vitest (baseline 87 files / 524 tests) | **89 files / 531 tests PASS** (+2 files, +7 tests nuevos) |
| `tsc -b` | **PASS** |
| `vite build` | **PASS** |
| E2E navegación (`e2e/navigation-consistency.spec.ts`, autónomo con stubs) | **8/8 PASS** (legacy redirect, deep-link back, browser back/forward, filtros, RBAC, 360/390/desktop) |
| Suite E2E de procesos (17 specs) | requiere entorno vivo (backend) — fuera del sandbox; sin cambios que la afecten (spec afirmativo: rutas de procesos intactas) |

## 3 · /ANALYZE · /CONVERGE

- SIN operaciones backend nuevas · SIN secretos · SIN legacy-as-current · SIN contradicciones SPEC/PLAN/TASKS.
```
SPEC_CONSISTENCY = PASS · TASK_TRACEABILITY = PASS · OPEN_TECHNICAL_CONTRADICTIONS = 0
```

## 4 · Límites conocidos (declarados, no ocultos)

1. **Doble “atrás” inmediato** con formulario sucio puede adelantar la confirmación (popstate antes del modal) — riesgo residual documentado en el hook.
2. Tras confirmar una salida programática con cambios, la entrada centinela del historial puede reaparecer al volver atrás (formulario se remonta limpio) — comportamiento aceptable, documentado.
3. El diálogo de salida cubre BackNavigation + browser-back; la navegación por clic en **otros** controles internos (sidebar) mientras hay cambios no intercepta — cubierto por `beforeunload` solo al recargar/cerrar. Registrado como mejora futura si el Owner lo pide.

## 5 · AC finales

AC01–AC21: **PASS** (AC21 = E2E navegación 8/8; AC20 = regresión completa 531/531 + tsc + build).
