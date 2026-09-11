# GA-FE-03 · PLAN

**Fases P1–P26** (encargo §40). Cada fase produce artefacto y gate. Estados al cierre de cada
una: DONE/state.

| # | Fase | Salida | Estado |
|---|---|---|---|
| P1 | Governance read (R-98, R-119, master audit, catálogo, OD-09/10/14/15/16, R-121/139/163, D-1, specs BU/RBAC, código de navegación/guards/stores/i18n) | Contexto leído y trazado en esta carpeta | ✅ |
| P2 | Baseline inventory (rama/HEAD/remoto/worktree/runtime/bundle; TSC/build/Vitest/backend) | §12–13 congelado: `5a3acc9` · TSC 0 · build ✓ · Vitest 205/205 · backend 7/7 | ✅ |
| P3 | Route matrix | `GA_FE_03_ROUTE_CAPABILITY_MATRIX.md` (32 filas) | ✅ |
| P4 | Nav inventory | `GA_FE_03_NAV_SOURCE_INVENTORY.md` (12 fuentes) | ✅ |
| P5 | Actor matrix | `GA_FE_03_ACTOR_MATRIX.md` (A–E, Z, P) | ✅ |
| P6 | RED proof + tests | `GA_FE_03_RED_EVIDENCE.md` + tests vitest que fallan hoy | PENDIENTE (tras C1) |
| P7 | Canonical capability model | `navigationConfig.ts` con metadatos (clase, permiso, BU, contexto, móvil) | PENDIENTE |
| P8 | Shared evaluator | `auth/navigation.ts` (`evaluateNavItem`, `filterNavItemsBySession`, `canAccessRoute`) | PENDIENTE |
| P9 | Desktop integration | Sidebar con evaluador único | PENDIENTE |
| P10 | MenuHub integration | Hub sobre árbol filtrado; raíz ausente → home; `D-2` cerrado | PENDIENTE |
| P11 | Dashboard shortcuts | Tarjetas de unidad/fases con el mismo evaluador | PENDIENTE |
| P12 | Mobile integration | Drawer + MobileNav derivados del mismo evaluador (sin duplicar arrays) | PENDIENTE |
| P13 | Context invalidation | Switch de empresa → recálculo (zustand) + refresh idéntico | PENDIENTE |
| P14 | Grant/revoke refresh | Semántica de propagación (refresh/relogin del objetivo) implementada de origen (estado de sesión) | PENDIENTE |
| P15 | Deep-link regression | Guardas `CapabilityRoute` para rutas con permiso inequívoco; rutas productivas de URL por unidad | PENDIENTE |
| P16 | i18n | `nav.roles` ES/EN; auditoría de claves crudas | PENDIENTE |
| P17 | Targeted tests | RED → GREEN (evaluador + navegación + hub + rutas) | PENDIENTE |
| P18 | Full frontend gates | TSC · build · Vitest completo · regresión GA-FE-02 | PENDIENTE |
| P19 | Deployment | Commit + push → pipeline → bundle nuevo verificado | PENDIENTE |
| P20 | Authenticated runtime actors | E, A, B, C, D, Z, P provisionados y logueados | PENDIENTE |
| P21 | Runtime matrix | Visibilidad por actor + 3D + switch/refresh/relogin + deep links | PENDIENTE |
| P22 | Mobile E2E | 390×844 para E, B, C, Z, D | PENDIENTE |
| P23 | Security regression | 403/404 backend en deep links + D-1/F1–F4 spots + BU OFF absoluto | PENDIENTE |
| P24 | Evidence | Documentos runtime/red/capturas/ledger | PENDIENTE |
| P25 | Certification | `GA_FE_03_CERTIFICATION_RECONCILIATION.md` + cierres R-98/R-119 | PENDIENTE |
| P26 | Converge | Limpieza, UAT del propietario, git final, informe §102 | PENDIENTE |

**Riesgos y mitigación**:
1. **Regresión GA-FE-02** por guardas demasiado estrictas → mitigación: guardas solo con
   permisos canónicos explícitos + suite completa + E2E de spots GA-FE-02 antes de publicar.
2. **Flash de permisos** durante hidratación → el layout solo se pinta tras `fetchMe`
   (`isLoading` de `ProtectedRoute`); el evaluador es síncrono sobre el `user` actual.
3. **Divergencia de semántica** con el backend → el evaluador es UX; jamás se usa para decidir
   datos; espejo del contrato `/me` (`AC-H11…H14`).
4. **BU-D10** (reactivación) → la navegación usa `effective_business_units` vigente; no decide
   política de ciclo de vida.

---

**ESTADO FINAL (2026-09-11 · HEAD `5608465` · evidencia C4)**: **P1–P26 DONE**. Preflight
verde; RED 17F/2P → GREEN 241/241; implementación C2 `a3cd7eb` + C3 `5608465` desplegada
(`index-CElqNz3R.js` == build local); certificación runtime **desktop 45/45 · móvil 13/13 ·
regresión+restauración 29/29**; evidencia y addenda publicadas; `GA-FE-03 = FUNCTIONALLY_
CERTIFIED / OWNER_ACCEPTANCE_PENDING`.
