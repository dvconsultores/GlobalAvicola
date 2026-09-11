# GA-FE-03 · MATRIZ DE RUTAS Y CAPACIDADES

**Fecha**: 2026-09-11 · **Base**: `5a3acc9` · Universo: **todas** las rutas user-visible de
`App.tsx` (inventario completo, sin muestreo). Leyenda de clase: `CORE` · `CP`
(control-plane) · `PROD` (productivo) · `REP` (reporting) · `INT` (integración). «Guard actual»
= guardas en `App.tsx` antes de GA-FE-03.

| # | Ruta | Página | Fuente de navegación | Grupo | Guard actual | RBAC requerido (canónico backend) | Clase | Dep. BU | Dep. contexto empresa | Dep. concesión | Global sin contexto | Móvil | Estado actual | Objetivo GA-FE-03 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | `/login` | LoginPage | — | — | público | — | CORE | — | — | — | visible | sí | correcta | sin cambio |
| 02 | `/` | HomeRoute→DashboardPage (móvil→`/menu/poultry`) | Sidebar «Dashboard»; MobileNav «Home» | main | sesión | `dashboard:read` | CORE | — | — | — | visible (0 filas) | sí | entrada visible a todos; D-4 home fail-closed sin `dashboard:read` (documentado) | entrada gated `dashboard:read`; D-4 intacto |
| 03 | `/kpi` | DashboardPage | MobileNav «KPI» | main | sesión | `dashboard:read` | CORE | — | — | — | visible | sí | siempre visible | gated `dashboard:read` |
| 04 | `/menu/:menuKey` | MenuHubPage | Sidebar/Drawer (contenedores) | — | sesión | (según hub) | CORE-PROD | según hub | según hub | según hub | fail-closed | sí | **consume `NAV_ITEMS` SIN filtrar** (`D-2`) | evaluado con el mismo filtro; raíz ausente → home |
| 05 | `/masters` → `/masters/farms` | MasterListPage | Sidebar «Maestros» | administration | sesión+webOnly | `masters:read` | CP (INQUILINO) | — | sí (datos) | — | fail-closed datos | no | visible a todos | entrada+guarda `masters:read` |
| 06 | `/masters/:entity` (21 entidades) | MasterListPage | ídem | administration | sesión+webOnly | `masters:read` | CP | — | sí | — | fail-closed | no | ídem | ídem |
| 07 | `/masters/genetic-lines/:id/weight-curves` | WeightCurvesPage | desde fila de maestros (acción) | administration | sesión+webOnly | `masters:read` | CP | — | sí | — | fail-closed | no | accionable solo desde fila (dato ya autorizado) | igual (la fila implica superficie autorizada) |
| 08 | `/poultry` | ProcessHubPage | Sidebar «Gestión Avícola»→hub `/menu/poultry`; redirect móvil | operational | sesión (+móvil→`/menu/poultry`) | `operations:read` (decisión GA-FE-03, §9) | PROD | hija por unidad | sí | sí | fail-closed | redirige | visible a todos; sin chequeo BU | visible si ≥1 unidad visible |
| 09 | `/poultry/:birdType/:phase?` | ProcessStagePage | hijos de `poultry` (Sidebar/Drawer/hub/Dashboard) | operational | sesión | `operations:read` + BU de la URL | PROD | `birdType` | sí | sí | fail-closed | sí | visible a todos; BU en URL sin chequeo | gated permiso + BU efectiva/habilitada |
| 10 | `/processes` | → `/menu/poultry` | legacy | — | sesión | — | — | — | — | — | — | — | redirect activo | sin cambio (LEGACY_SUPPORTED) |
| 11 | `/processes/:stage` | ProcessStageRedirect | legacy (mapeo a `/poultry/...`) | — | sesión | — | — | — | — | — | — | — | redirect activo | sin cambio (LEGACY_SUPPORTED) |
| 12 | `/operations` | OperationListPage | (sin entrada; flujos) | — | sesión | `operations:read` | PROD | datos | sí | sí | fail-closed | sí | alcanzable por URL/links de flujo | guarda `operations:read`; sin entrada nueva |
| 13 | `/operations/new` | OperationFormPage | tiles de proceso (stage) | — | sesión | `operations:create` (backend) | PROD | datos | sí | sí | fail-closed | sí | ídem | igual (backend autoridad; sin guarda nueva) |
| 14 | `/operations/:id` | OperationDetailPage | listas/dashboard | — | sesión | `operations:read` | PROD | datos | sí | sí | fail-closed | sí | ídem | guarda `operations:read` |
| 15 | `/my-pending` | MyPendingPage | (sin entrada) | — | sesión | `operations:read` | PROD | datos | sí | sí | fail-closed | sí | ídem | igual |
| 16 | `/lots` | LotListPage | (sin entrada; links) | — | sesión | `lots:read` | PROD | datos | sí | sí | fail-closed | sí | ídem | guarda `lots:read` |
| 17 | `/lots/new` | LotFormPage | (sin entrada) | — | sesión+webOnly | `lots:create` (backend) | PROD | datos | sí | sí | fail-closed | no | ídem | igual |
| 18 | `/lots/:id` | LotDetailPage | alertas del Dashboard, listas | — | sesión | `lots:read` | PROD | datos | sí | sí | fail-closed | sí | ídem | guarda `lots:read` |
| 19 | `/admin/unit-access` | UnitAccessPage | Sidebar/Drawer «Acceso por unidad» | administration | sesión+webOnly+`business_units:read` | `business_units:read` | CP | — | **sí** (exige empresa efectiva) | — | fail-closed | no | correcta (GA-FE-02) | sin cambio (referencia de patrón) |
| 20 | `/reports` | ReportsPage | Sidebar «Reportes» | reports | sesión | `reports:read` | REP | «any» | sí | sí | fail-closed | sí | visible a todos | gated permiso + BU ≥1 |
| 21 | `/reports/lot/:id` | LotReportPage | desde lot/operations | — | sesión | `reports:read` | REP | lote | sí | sí | fail-closed | sí | ídem | guarda `reports:read` |
| 22 | `/reports/sap` | SapComparisonPage | hijo «Diferencias SAP vs App» | reports | sesión+webOnly | `reports:read` (+`sap:read` datos) | REP | — | sí | — | fail-closed | no | visible a todos | entrada gated `reports:read`; BU no exigida (comparación, no unidad) |
| 23 | `/review` | ReviewCenter | Sidebar «Centro de Revisión» | review | sesión+webOnly | `review:read` | PROD | «any» | sí | sí | fail-closed | no | visible a todos | gated permiso + BU ≥1 |
| 24 | `/review/:id` | ReviewDetail | listas del centro | — | sesión+webOnly | `review:read` | PROD | evento | sí | sí | fail-closed | no | ídem | guarda `review:read` |
| 25 | `/review/:id/correct` | CorrectionForm | detalle | — | sesión+webOnly | `review:update` (backend) | PROD | evento | sí | sí | fail-closed | no | ídem | igual (backend autoridad) |
| 26 | `/approvals` | ApprovalPanel | Sidebar «Aprobaciones» | review | sesión+webOnly | `approvals:approve` | PROD | «any» | sí | sí | fail-closed | no | visible a todos | gated permiso + BU ≥1 |
| 27 | `/audit` | AuditPage | Sidebar «Auditoría» | administration | sesión+webOnly | `audit:read` | CP | — | sí | — | fail-closed | no | visible a todos; `D-3` (filtro inválido 500) documentado | entrada+guarda `audit:read`; D-3 intacto |
| 28 | `/sap` | SapManagerPage | Sidebar «Integración SAP» | integration | sesión+webOnly | `sap:read` | INT | — | sí | — | fail-closed | no | visible a todos | gated `sap:read` |
| 29 | `/users` | UsersPage | «Usuarios y Roles» (settings) | administration | sesión+webOnly | `users:read` | CP | — | sí | — | fail-closed | no | visible a todos | gated `users:read` |
| 30 | `/roles` | RolesPage | **sin entrada (solo URL)** | — | sesión+webOnly | `users:read` | CP | — | sí | — | fail-closed | no | ruta activa sin descubribilidad | **entrada nueva `Roles`** gated `users:read` |
| 31 | `/profile` | ProfilePage | «Mi Perfil» (settings) | administration | sesión | — | CORE | — | — | — | visible | sí | visible a todos | sin cambio |
| 32 | `*` | → `/` | — | — | — | — | — | — | — | — | — | — | fallback | sin cambio |

**Conteo**: 32 filas (21 entidades de maestros agrupadas en la fila 06) · producto/operativo
`PROD`: 12 · `REP`: 3 · `CP`: 6 · `INT`: 1 · `CORE`: 5 · legacy/soporte: 2 (`/processes*`) ·
fallback: 1 · rutas sin entrada de menú: 12 (flujos alcanzables por enlaces contextuales o URL;
solo `/roles` exigía descubribilidad §80).

**Fuera de alcance detectado**: `R-181` (`POST /operations/{id}/submit`, sin ruta/entrada
frontend) → `OUT_OF_SCOPE_OPEN_FINDING` (UNCHANGED). Reverso (`GA-REM-041`) → sin ruta frontend
→ se clasifica aparte, **no** se implementa. `R-182` (`LotForm`) → sin cambio.
