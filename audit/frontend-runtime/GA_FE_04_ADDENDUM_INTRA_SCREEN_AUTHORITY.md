# GA-FE-04 · ADDENDUM AL MASTER FRONTEND RUNTIME AUDIT — Autoridad intra-pantalla (P-13)

Complementa: `MASTER_FRONTEND_RUNTIME_GAP_MATRIX.md`, `MASTER_PRODUCT_CAPABILITY_CATALOG.md`, `GA_FE_03_ADDENDUM_DYNAMIC_NAVIGATION.md`.
Fecha: 2026-09-11 · Generación: `index-B66tpdeW.js` (`de40d36`) · Estado: FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING.

## 1 · Cambio estructural

| Antes (GA-FE-03) | Ahora (GA-FE-04) |
|---|---|
| Autoridad en navegación/rutas (`auth/navigation.ts`) | + capa de ACCIÓN `auth/actionAuthority.tsx` (`canPerformAction` ≡ `canAccessCapability`, `useCan`, `ActionGate`) |
| Pantallas legibles mostraban acciones sin permiso (R-98) | 12 superficies gatean 31 acciones por permiso canónico |
| Deep links de alta sin guarda | `/lots/new`=lots:create · `/operations/new`=operations:create · `/review/:id/correct`=corrections:correct |
| — | Aprobación ≠ rechazo (gates separados); lote=`review:review` |

## 2 · Superficies tocadas (12 + 3 rutas)

UsersPage · RolesPage · MasterListPage · WeightCurvesPage · LotListPage · LotDetailPage · OperationDetailPage · ReviewCenter · ReviewDetail · CorrectionForm · ApprovalPanel · SapManagerPage · DashboardPage(alerts) · App.tsx (3 guards) · i18n `actions.readOnlyViewer` (ES/EN).

## 3 · Cobertura de acciones

31 acciones de escritura: ver `audit/ga-fe-04/GA_FE_04_SCREEN_ACTION_INVENTORY.md` y `GA_FE_04_ACTION_API_CONTRACT.md`. Exclusión declarada: submit/cancel de operaciones (UI no existe → EXCLUDED_R181).

## 4 · Evidencia y gates

- RED→GREEN: 22/22 (8 archivos) · suite 263/263 · tsc 0 · build OK · backend PG-free 7/7.
- Runtime: R 0 controles (desktop+móvil, ES/EN) · D/Z negadas · P 3D caso 3 denegado · C 3D caso 4 permitido + propagación grant/revoke · A/B CBU sin regresión · E comodín.
- Backend autoridad: 403 directos (PUT/POST/DELETE masters; POST users).
- Red: solo GET 200, sin bucles; consola 0 errores.

## 5 · Efecto en roadmap

- **R-98: CLOSED** (P-13 residual cerrado). Ver `audit/ga-fe-04/GA_FE_04_R98_CLOSURE_RECONCILIATION.md`.
- R-119: sigue CLOSED. R-181/R-182: UNCHANGED. BU-D10: PENDING_RATIFICATION.
- Sin cambios de backend; sin cambios de contrato API; sin nuevas pantallas.

## 6 · Límites honestos

- La capa de acción es UX de descubribilidad; **la autorización sigue en el backend** (verificado).
- E sin empresa efectiva en sesión de navegador: listas vacías por alcance — control positivo de fila cubierto por pruebas y por actores con contexto.
- Rol duplicado 42 (reintento de provisión) desactivado en la misma sesión; IDs reales reconciliados en la matriz de actores.

## 7 · Addendum GA-FE-04-A (2026-09-11) · Self-action + Cross-company

- `P13-AC20` (self-grant) y `P13-AC21` (cross-company) ejecutados contra la generación final: **PASS** en frontend, backend (403 SOD / 404 sin fuga), persistencia, auditoría, desktop y móvil. Detalle: `audit/ga-fe-04/GA_FE_04_A_SELF_CROSS_RUNTIME_EVIDENCE.md`.
- Sin cambios de producto (tranche evidence-only).
- Observación registrada sin acción: `OBS-01` (hub desnudo `/menu` con rol 35 sin `dashboard:read` → redirección a home con «Permiso requerido»); preexistente y ajeno al alcance R-98.
- **R-98 = CLOSED** (AC originales + AC20/AC21).
