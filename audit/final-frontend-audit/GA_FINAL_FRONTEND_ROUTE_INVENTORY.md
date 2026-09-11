# FINAL FRONTEND AUDIT · INVENTARIO DE RUTAS (actual)

Fecha: 2026-09-11 · Fuente: `frontend/src/App.tsx` (206-284) + 20 rutas generadas de maestros (230-250). Leyenda: `M` = descubrible por menú (hub/ítem) · `D` = profunda (por enlace contextual) · guardas: `C=CapabilityRoute`, `P=PermissionRoute`, `W=WebOnlyRoute`, `PR=ProtectedRoute`.

| # | Ruta | Página | Guarda (permiso) | Menú | Empresa | BU | Control/Prod | Desktop | Mobile | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `/login` | LoginPage | pública | — | — | — | CORE | ✓ | ✓ | OK |
| 2 | `/` | HomeRoute→Dashboard | PR | M | sí | — | PRODUCTIVE/CORE | ✓ | redirige hub | OK (N-1 home sin dashboard:read) |
| 3 | `/kpi` | DashboardPage | (ninguna) | — | sí | — | PRODUCTIVE | ✓ | ✓ | **ruta sin guarda de capacidad** (nota) |
| 4 | `/menu/:menuKey` | MenuHubPage | (ninguna) | M (hubs) | sí | por ítem | mixto | ✓ | ✓ (solo poultry) | OK |
| 5 | `/masters` → farms | redirect | W+C `masters:read` | M | sí | — | CONTROL | ✓ | N/A(w) | OK |
| 6 | `/masters/genetic-lines/:id/weight-curves` | WeightCurvesPage | W+C `masters:read` | D (acción de fila) | sí | — | CONTROL | ✓ | N/A(w) | OK (verificado S21) |
| 7 | `/masters/{20 entidades}` | MasterListPage | W+C `masters:read` | M (`/masters`) | sí | — | CONTROL | ✓ | N/A(w) | OK |
| 8 | `/poultry` | PoultryHubPage | PR+C `operations:read`+units | M | sí | 4 | PRODUCTIVE | ✓ | redirige | legacy tolerado |
| 9 | `/poultry/:birdType/:phase?` | PoultryStageRoute | C `operations:read`+unidad | M (hub) | sí | exacta | PRODUCTIVE | ✓ | ✓ | OK |
| 10 | `/processes(/…stage)` | redirects | — | — | — | — | — | ✓ | ✓ | legacy tolerado |
| 11 | `/operations` | OperationListPage | C `operations:read` | D | sí | datos | PRODUCTIVE | ✓ | ✓ | OK |
| 12 | `/operations/new` | OperationFormPage | C `operations:create` | D | sí | sí (form) | PRODUCTIVE | ✓ | ✓ | OK |
| 13 | `/operations/:id` | OperationDetailPage | C `operations:read` | D | sí | sí | PRODUCTIVE | ✓ | ✓ | OK |
| 14 | `/my-pending` | MyPendingPage | (solo sesión) | — | sí | datos | PRODUCTIVE | ✓ | ✓ | **ruta sin guarda de capacidad** (nota) |
| 15 | `/lots` | LotListPage | C `lots:read` | **M (hub Gestión Avícola — GA-FE-08)** | sí | datos | PRODUCTIVE | ✓ | ✓ | OK |
| 16 | `/lots/new` | LotFormPage | W+C `lots:create` | D | sí | sí | PRODUCTIVE | ✓ | N/A(w) | OK |
| 17 | `/lots/:id` | LotDetailPage | C `lots:read` | D | sí | sí | PRODUCTIVE | ✓ | ✓ | OK |
| 18 | `/admin/unit-access` | UnitAccessPage | W+**P** `business_units:read` | M (Configuración) | sí | — | CONTROL | ✓ | N/A(w) | OK (único uso de PermissionRoute — nota de consistencia) |
| 19 | `/reports` | ReportsPage | C `reports:read` | M | sí | datos | REPORTING | ✓ | ✓ | OK |
| 20 | `/reports/lot/:id` | LotReportPage | C `reports:read` | D | sí | sí | REPORTING | ✓ | ✓ | OK |
| 21 | `/reports/sap` | SapComparisonPage | W+C `reports:read` | M | sí | — | REPORTING | ✓ | N/A(w) | OK |
| 22 | `/review` `/review/:id` | ReviewCenter/Detail | W+C `review:read` | M | sí | sí | PRODUCTIVE | ✓ | N/A(w) | OK |
| 23 | `/review/:id/correct` | CorrectionForm | W+C `corrections:correct` | D | sí | sí | PRODUCTIVE | ✓ | N/A(w) | OK |
| 24 | `/approvals` | ApprovalPanel | W+C `approvals:approve` | M | sí | sí | PRODUCTIVE | ✓ | N/A(w) | OK |
| 25 | `/audit` | AuditPage | W+C `audit:read` | M | sí | — | CONTROL | ✓ | N/A(w) | OK (filtro fuera de enum → 500 registrado D-3 previo) |
| 26 | `/sap` | SapManagerPage | W+C `sap:read` | M | sí | — | INTEGRATION | ✓ | N/A(w) | OK |
| 27 | `/users` | UsersPage | W+C `users:read` | M (Configuración) | sí | — | CONTROL | ✓ | N/A(w) | OK |
| 28 | `/roles` | RolesPage | W+C `users:read` | M (Configuración) | sí | — | CONTROL | ✓ | N/A(w) | OK |
| 29 | `/profile` | ProfilePage | (solo sesión) | M | — | — | CORE | ✓ | ✓ | OK |
| 30 | `*` | → `/` | — | — | — | — | — | ✓ | ✓ | OK |

## Hallazgos de inventario (no se corrigen)

- **Huérfanas/legacy toleradas:** `/processes*`, `/poultry` (legacy hub) — redirects gobernados; sin acción.
- **Sin guarda de capacidad (solo sesión):** `/kpi`, `/menu/:menuKey` (evalúa internamente), `/my-pending`, `/profile` — comportamiento vigente; `/menu/:key` filtra su contenido; `/kpi` y `/my-pending` quedan registrados como nota (P3, sin finding nuevo; patrón histórico conocido).
- **Descubribilidad:** tras GA-FE-08, `/lots*` ya tiene fuente de menú. `/operations*` y `/my-pending` continúan como rutas profundas por diseño (acceso contextual), coherente con GA-FE-03 §34.
- **Cero rutas duplicadas del mismo recurso**; 20 entidades de maestros comparten patrón `/masters/{entity}` sin colisión.
