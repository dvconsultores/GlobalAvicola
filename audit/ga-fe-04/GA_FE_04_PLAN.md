# GA-FE-04 · PLAN (P1–P29)

| # | Fase | Estado |
|---|---|---|
| P1 | Governance read (R-98/P-13/AC-FE16/OD-14/15/16/R-121/139/163/R-181/182/audit) | ✅ |
| P2 | Reconciliación R-98 canónica | ✅ |
| P3/P4 | Inventario pantallas + acciones (32 rutas / 54 filas) | ✅ |
| P5 | Contrato acción↔API (mapa router extraído) | ✅ |
| P6 | Matriz de actores (E/A/B/C/D/Z/P/R) | ✅ |
| P7 | RED runtime (captura pre-fix con R real) | tras RED tests |
| P8 | RED automatizado (vitest sobre comportamiento actual) | tras RED tests |
| P9 | Diseño: `auth/actionAuthority.ts` (capa fina sobre GA-FE-03) | ✅ (SPEC §18) |
| P10 | Implementación de gates por página (12 pantallas) | pendiente |
| P11/P12 | Desktop + móvil (misma semántica) | pendiente |
| P13 | Invalidez por contexto (switch/BU/grant ya soportado por estado de sesión) | pendiente |
| P14 | Propagación grant/revoke (refresh/relogin canónico) | pendiente |
| P15 | Self/cross (verificar, no añadir reglas) | pendiente |
| P16 | i18n (`actions.readOnlyViewer` ES/EN) | pendiente |
| P17 | GREEN dirigido | pendiente |
| P18 | Gates completos frontend | pendiente |
| P19 | Regresiones backend relevantes (PG-libre local + familia en runtime) | pendiente |
| P20 | Deploy por pipeline | pendiente |
| P21/P22 | Actores runtime + matriz de acciones E2E | pendiente |
| P23 | Móvil E2E | pendiente |
| P24 | Negativas de API directas | pendiente |
| P25 | Restauración §100 | pendiente |
| P26 | Evidencia | pendiente |
| P27/P28 | Reconciliación por AC + certificación | pendiente |
| P29 | Converge (UAT + informe + git) | pendiente |

**Riesgos**: (1) gates demasiado estrictos → mitigado por contrato router 1:1 + regresiones +
UAT-09-replay; (2) flash → gating por `isLoading` de sesión; (3) deriva de conteos → el informe
final usa los conteos medidos en certificación.
