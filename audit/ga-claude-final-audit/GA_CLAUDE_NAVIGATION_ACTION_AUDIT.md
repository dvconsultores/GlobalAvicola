# GA-CLAUDE · AUDITORÍA DE NAVEGACIÓN Y AUTORIDAD DE ACCIÓN (§19 · §20 · §66)

Auditoría independiente Claude · 2026-09-13 · HEAD `c0b4afc` · Fuente principal: informe `evidence/F_i18n_nav_responsive.md §2` (matriz de 37 rutas) + `GA_CLAUDE_FRONTEND_CAPABILITY_MATRIX.md §6` (huérfanas) + gates de acción (`evidence/C_response_error_state.md`, `B_form_contracts.md`, runtime `httpErrores`). Todos los códigos `G-nn`/`R-nn` remiten a los registros de esta auditoría.

## 1 · Navegación — hechos estructurales

- Sidebar **no despliega hijos**: todo contenedor es enlace a su hub `/menu/:key` (`Sidebar.tsx:23-35`); `SidebarSubmenu.tsx`/`MobileDrawer.tsx` **no importados** (código muerto; `ui.store.openDrawer` sin uso).
- `AppLayout.tsx:13-20`: `Sidebar` solo `view_type!=='mobile'` y visible `lg:`; `MobileNav` solo móvil `<lg`; sin hamburguesa/drawer montado.
- Guardas: `ProtectedRoute` (sesión), `WebOnlyRoute` (móvil → `/`), `CapabilityRoute` (permiso+unidad), `PermissionRoute` (permiso; otro texto de denegación). `ProtectedRoute.roles` muerto.
- Guardas nav↔ruta: `/reports*`, `/review*`, `/approvals` exigen `requiresUnits` en menú pero no en ruta; `/operations/new` exige `operations:create` en ruta pero los tiles/timeline no gatean; `/my-pending` **sin guarda** y sin entrada.

## 2 · Matriz de descubribilidad (extracto de F §2.a; rutas completas allí)

| Estado | Rutas | Nota |
|---|---|---|
| **DIRECT_URL_ONLY ilegítima** | `/my-pending` (funcional, sin vía); `/masters/{20 entidades ≠ farms}`; `/reports/lot/:id` (solo enlace fijo a 2); `/profile` **en móvil** | Gaps funcionales/de navegación (`G-01`, `G-05`, `G-18`, `G-04`) |
| Sin entrada de menú | `/operations` (historial; solo pie de etapa y tras guardar); sin activo | `G-19` |
| Huérfanas legítimas | `/poultry` (legado; móvil redirige), `/processes*` (redirects) | compatibilidad (F §2.b) |
| Redundantes/muertas | 4 tarjetas SAP → `/sap` sin tab; 2 tarjetas de reportes → `/reports`; `/review?status=` ignorado por backend | `AOD-21`, R-197 |
| Home sin `dashboard:read` | `/` = error «Permiso requerido» + Reintentar (destino de login/Atrás/migas/`*`) | `G-02` (N-1) |

## 3 · Auditoría móvil (`view_type='mobile'`, 390×844)

| Flujo | Estado | Evidencia |
|---|---|---|
| Registrar operación (6 etapas) | **Sí** (hub → etapa → tile → asistente → guardar) | F §2.c; E2E local M |
| Ver «mis pendientes» | **No** (`/my-pending` inalcanzable) | G-05 |
| Detalle de lote / enviar a revisión / evidencia | Sí (con las salvedades de R-198) | F §2.c |
| Descargar/ver evidencia | **Degradado** (botones `opacity-0 group-hover` invisibles táctil) | R3 → R-198 AC-07 |
| Logout / perfil | **No** en superficies `<lg` | G-04 (`R-220` lote B) |
| Web `<1024px` (tablet vertical) | **Sin navegación ni logout** (sidebar/`lg:flex` oculto; drawer no montado) | G-03 (R1) |
| Web-only por diseño | review, approvals, masters, users, roles, audit, sap, unit-access… | `WebOnlyRoute` → `/` sin mensaje |

## 4 · Rutas huérfanas y código muerto de navegación

| Ítem | Evidencia | Gap/Spec |
|---|---|---|
| `/my-pending` huérfana (hook `useMyPending` sin uso) | `App.tsx:262`; grep 0 enlaces | G-05 → R-220 B3 |
| 20 maestros solo por URL | `App.tsx:220`→`farms`; sin selector en `MasterListPage` | G-01 → **R-196** |
| `/reports/lot/:id` fijo a 2 | `ReportsPage.tsx:193` | G-18 → R-220 B4 |
| `/operations` sin menú/activo | `ProcessStagePage.tsx:120` | G-19 → R-220 B5 |
| `/profile` móvil sin enlace | `Header.tsx:158-198` | G-04 → R-220 B2 |
| Tarjetas duplicadas SAP/reportes | `navigationConfig.ts:203-206,221-222` | AOD-21/R-220 |
| `MobileDrawer`/`SidebarSubmenu`/drawer store muertos | F G-28 | R-220 D3 |

## 5 · Autoridad de acción (§20) — UI vs servidor

| Acción | Gate UI | Gate servidor | Veredicto |
|---|---|---|---|
| Crear operación | ruta `operations:create`; tiles **sin** gate (callejón) | `operations:create` | **UI incompleta** (G-20 → R-220 B6) |
| Enviar/reenviar | `OperationDetailPage` gate por permiso+unidad | idéntico | OK (GA-FE-05) |
| Aprobar/rechazar (unitario) | `approvals:*` | idéntico | OK |
| Aprobar/rechazar (**lote**) | `review:review` | `review:review` (más débil que unitario) | **Mismatch de política** → **R-208** |
| Editar/cancelar operación | sin UI | Backend permite en estados | **Backend-only** → INT-09/R-220 A20 |
| Cerrar lote | `lots:create`+estado | idéntico (BR-05/R7) | OK salvo feedback (R-192) |
| Transición de fase | botón siempre visible (etapa mal derivada) | `lot_id/phase_id` (422) | **Roto** → **R-191** |
| Solicitar reverso | **sin UI** | `reversals:create` | **Backend-only** → **R-207** |
| Unidades (conceder/revocar/habilitar) | `UnitAccessPage` gates | servidor autoridad (OD-15) | OK (GA-FE-02/08) |
| Maestros CRUD | gates de página | `masters:*` | OK salvo creación (R-196) |
| Usuarios/roles | gates | servidor (salvo R-195/R-199/R-202) | Parcial |
| Adjuntar/borrar evidencia | solo permiso, **cualquier estado** | solo unidad | **Sin gate de estado** → **R-198** |
| SAP consolidar/exportar | gates `sap:*` | idéntico | OK (UI desalineada en estados → R-217) |
| Exportar informes | cliente, sin auditoría | n/a | Residual (E-16/R-220) |

Principios verificados: **UI oculta ≠ seguridad** (el servidor deniega en las superficies certificadas; los huecos están registrados); **backend autoritativo** en RBAC/unidad/tenencia (con las excepciones R-199/R-203/R-204 ya con paquete).

## 6 · Registro de brechas (dedup con el registro central)

| Código | Brecha | Spec |
|---|---|---|
| `G-01` 20/21 maestros solo URL | R-196 |
| `G-02` home sin `dashboard:read` | R-212 |
| `G-03` web `<1024px` sin navegación/logout | R-220 (lote B) |
| `G-04` móvil sin logout/perfil | R-220 (lote B) |
| `G-05` `/my-pending` huérfana | R-220 (lote B) |
| `G-19` `/operations` sin menú | R-220 (lote B) |
| `G-20` tiles sin gate | R-220 (lote B) |
| `G-18` reporte de lote fijo | R-220 (lote A/B) |
| `G-26` paridad de guardas/`returnTo`/código muerto | R-220 (lotes B/D) |
| Lote de aprobación con permiso débil | R-208 |
| Reverso sin UI; edición/cancelación sin UI; activación manual sin UI | R-207 / R-220 A20 / P1-15 (registrado; UI de activación en R-220 A20 vía INT-10) |

**Veredicto de navegación**: no existe ningún flujo **requerido** sin entrada *legítimamente enlazada* salvo los listados arriba — `/my-pending`, navegación web intermedia, logout móvil y la selección de entidad de maestros. Los cuatro entran en paquetes (R-196/R-212/R-220). No se reproduce el patrón «solo por URL» en ningún otro flujo de proceso.
