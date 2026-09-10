# FRONTEND ROUTE ↔ COMPONENT MAP (repositorio, HEAD `3808ed5`)

Fuente trazada por imports reales de `App.tsx`; no por nombres de fichero. Complementa (no sustituye) `FRONTEND_ROUTE_MODULE_MATRIX.md` y `FRONTEND_SCREEN_IMPLEMENTATION_MATRIX.md` de la auditoría 360.

## 1. Rutas declaradas (App.tsx — 245 líneas)

| Ruta | Componente | Guard | Menú | En bundle desplegado | Capacidad |
|---|---|:--:|:--:|:--:|---|
| `/login` | LoginPage | — (público) | no | ✅ | CAP-SES-01 |
| `/` | HomeRoute → DashboardPage (mobile → `/menu/poultry`) | Protected | sí | ✅ | CAP-OPS-12 |
| `/kpi` | DashboardPage | Protected | sí | ✅ | CAP-OPS-12 |
| `/menu/:menuKey` | MenuHubPage | Protected | sí | ✅ | CAP-BU-01 |
| `/masters` | → `/masters/farms` | WebOnly | sí | ✅ | CAP-MAS-01 |
| `/masters/genetic-lines/:id/weight-curves` | WeightCurvesPage | WebOnly | sí (local) | ❌ **ausente** | CAP-MAS-03 |
| `/masters/:entity` (20 entidades) | MasterListPage | WebOnly | sí | parcial (13 entidades) | CAP-MAS-01/02 |
| `/poultry` | PoultryHubPage (legacy) | view_type | sí | ✅ | CAP-BU-01 |
| `/poultry/:birdType/:phase?` | PoultryStagePage | view_type | sí | ✅ | CAP-BU-01/03 |
| `/processes` → redirect | Navigate | — | sí | ✅ | navegación |
| `/processes/:stage` | ProcessStageRedirect | — | sí | ✅ | navegación legacy |
| `/operations` | OperationListPage | Protected | sí | ✅ | CAP-OPS-01/03 |
| `/operations/new` | OperationFormPage (wizard 26 tipos) | Protected | sí | ✅ (generación vieja) | CAP-OPS-02/04/05/06 |
| `/operations/:id` | OperationDetailPage (evidencias) | Protected | sí | ✅ | CAP-OPS-11 |
| `/my-pending` | MyPendingPage (móvil; draft/registered) | Protected | móvil | ✅ | CAP-OPS-01 |
| `/lots`, `/lots/new`, `/lots/:id` | LotList/Form/Detail | Protected / WebOnly(new) | sí | ✅ | CAP-OPS-10 |
| `/reports`, `/reports/lot/:id`, `/reports/sap` | Reports/LotReport/SapComparison | Protected / WebOnly | sí | ✅ (vieja) | CAP-OPS-12 |
| `/review`, `/review/:id`, `/review/:id/correct` | ReviewCenter/Detail/CorrectionForm | WebOnly | sí | ✅ | CAP-OPS-07 |
| `/approvals` | ApprovalPanel | WebOnly | sí | ✅ | CAP-OPS-07 |
| `/audit` | AuditPage | WebOnly | sí | ✅ (filtros viejos) | CAP-AUD-01 |
| `/sap` | SapManagerPage | WebOnly | sí | ✅ | CAP-OPS-13 |
| `/users` | UsersPage | WebOnly | sí | ✅ (vieja) | CAP-ADM-08 |
| `/roles` | RolesPage | WebOnly | **no — sin enlace en menú ni en páginas; sólo URL directa** | ❌ **ruta ausente** | CAP-ADM-09 |
| `/profile` | ProfilePage | Protected | sí | ✅ | CAP-SES-03 |
| `*` | → `/` | — | — | ✅ | — |

**Rutas que NO existen en ninguna capa (fase 9 / faltantes):** `/business-units*`, `/users/:id/business-units*`, `/reversals*`, `/pending-classification`, `/notifications` (UI), `/admin/companies*`.

## 2. Guards inventariados

| Guard | Lógica | Cobertura | Problema |
|---|---|---|---|
| `ProtectedRoute` | `isAuthenticated` + `webOnly` (view_type) + rama `roles` | todas las privadas | La rama `roles` es **código muerto**: nunca se pasa `roles`; `userRoleName` se computa como `''` salvo usuarios sin rol. **No hay chequeo por permiso.** |
| `WebOnlyRoute` | `view_type === 'mobile' → /` | páginas de escritorio | Solo distingue móvil/web |
| `HomeRoute` | mobile → `/menu/poultry` | home | — |

```
grep "hasPermission|usePermission|can("  frontend/src → 0 resultados
grep "is_super_admin" frontend/src        → 3 (Header 1 · App.tsx 1 · tipo 1)
```

## 3. Contextos y stores

| Artefacto | Función | Consume |
|---|---|---|
| `auth.store.ts` | sesión, tokens, `/me` | `user`, `view_type`, `company_id`, `company_name`, `is_super_admin` |
| `company.store.ts` | empresas seleccionables + `switchCompany` | `GET /masters/companies` (limit 100) · `POST /switch-company` · re-`fetchMe` |
| `navigationConfig.ts` | menú | **estático**; sin permiso/módulo/unidad; solo `view_type` filtra (móvil) |
| `processCatalog.ts` | catálogo de etapas/operaciones de las 4 unidades | estático (70 referencias a unidades) |
| `statusColors.ts` | colores/labels de estado | estático; **sin `REVERSED`** |

**La sesión ya entrega** (fase 8): `is_super_admin`, `company_id`, `effective_company_id`, `permissions`, `company_business_units`, `granted_business_units`, `effective_business_units`.
**El frontend NO consume** ninguno salvo `company_id/company_name/is_super_admin/view_type` → toda la navegación dinámica de `T-040-23` está por construir.

## 4. Componentes muertos / sin ruta

| Artefacto | Estado | Lectura |
|---|---|---|
| `operationsService.submit` (`services/operations.service.ts:43`) | **sin llamadores en todo el historial** | R-181 (CAP-OPS-08) |
| `operationsService.cancel` | sin llamadores (el motivo obligatorio quedó pendiente → R-140) | R-140 |
| `hooks/useOperations.ts` | importado por ¿ninguna página? — **sin consumidores** | higiene; no clasifica por sí solo |
| `PoultryHubPage`/`PoultryStagePage` | re-export de compatibilidad (no muerto — documentado en 360) | navegación legacy |
| antiguas pestañas «por lote / por usuario» de `AuditPage` | retiradas por `4386f87` **dejando imports sin uso** → rompió `tsc -b` | R-99 causa raíz |

## 5. i18n

- Paridad ES/EN verificada por el programa (988+ claves; última medición P-14 940/931…).
- **Sin claves** para «enviar a revisión / reenvío» en ninguna de las dos lenguas (coherente con R-181).
- El bundle desplegado servía 866 claves frente a 940+ en local (medición 2026-09-07): el desfase de i18n es un síntoma de R-99, no un problema aparte.
