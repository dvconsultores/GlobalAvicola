# MASTER FRONTEND RUNTIME AUDIT · ADDENDUM GA-FE-03 (2026-09-11)

**Addendum — la instantánea histórica NO se reescribe.** Tranche GA-FE-03 (navegación
dinámica) sobre la generación final `index-CElqNz3R.js` · HEAD `5608465`.

## 1 · Cambios de estado (con evidencia runtime autenticada)

| Capacidad / hallazgo | Estado anterior | Estado GA-FE-03 | Evidencia |
|---|---|---|---|
| `CAP-ADM-06` Navegación adaptada a permisos y unidades | FRONTEND_MISSING (`R-119`) | **`IMPLEMENTED_AND_VISIBLE`** — evaluador canónico único (RBAC ∩ BU empresa/concesión ∩ contexto ∩ autoridad global) en Sidebar, móvil, hubs, atajos; 45/45 desktop + 13/13 móvil | `audit/ga-fe-03/GA_FE_03_AUTHENTICATED_RUNTIME_EVIDENCE.md` |
| `R-119` | OPEN (P1) | **CLOSED** (individual) | `GA_FE_03_R119_RECONCILIATION.md` |
| `R-98` | OPEN (P2) | **PARTIAL** — navegación accionable cerrada; residuo intra-pantalla `P-13` declarado | `GA_FE_03_R98_RECONCILIATION.md` |
| `NAVIGATION_ROLE_BU_MATRIX §1` (menú completo para todos) | exposición universal | **RESUELTO**: política completa por actor; matriz §3 reproducida en runtime (D: 10/10 denegados; Z sin grupos) | evidencia runtime |
| `NAVIGATION_ROLE_BU_MATRIX §3.7` (`/roles` solo por URL) | exposición incompleta | **RESUELTO**: entrada `Roles` descubrible (gate `users:read`) | `A1/A2`, hub, captura |
| `D-2` (tarjeta del hub para D) | observación aceptada | **CERRADO** — hub sobre árbol filtrado | `D_hub_settings.png` |
| CAP-ADM-07 estado «sin unidades» explícito | FRONTEND_MISSING | **sin cambio** (el zero-BU se resuelve ocultando, sin error — navegación correcta; el aviso explícito no era AC de esta tranche) | `Z_*` |

## 2 · Sin cambio (declarado)

`R-181` · `R-182` · `R-99` (cerrado en GA-FE-01) · `D-3` · `D-4` · SAP · Wave B/C ·
`BU-D10` (`PENDING_RATIFICATION`) · backend (0 archivos) · migraciones (0).

## 3 · Archivos clave

`frontend/src/auth/navigation.ts` (nuevo — evaluador único) · `data/navigationConfig.ts`
(metadatos) · `App.tsx` (`CapabilityRoute`) · `Sidebar/MobileNav/MobileDrawer/MenuHubPage/
ProcessHubPage/DashboardPage` (derivados) · `public/locales/{es,en}` (`nav.roles`,
`common.noPermission`). Commits: `524704e` (C1 gobernanza+RED) · `a3cd7eb` (C2) · `5608465` (C3) ·
evidencia (C4).
