# R-212 · FINDING + SPEC (COMPACTO) — UI NO CONSCIENTE DEL PERMISO: 403 MOSTRADO COMO «VACÍO», CARGA ETERNA Y HOME INÚTIL

| Campo | Valor |
|---|---|
| **ID** | **R-212** · P3 · **no bloquea** (backend deniega; es calidad funcional de la UI) · Estado `SPEC_READY` |
| **Origen** | C#19/C#20 (informe C); F G-02/G-20/N-1; runtime `httpErrores` · Registro G-24 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración/endpoint/permiso · UAT: no |

## 1 · Contexto y evidencia

- Runtime (`runtime-gp-e2e.json` `httpErrores`): operador → `GET /reports/kpis`, `/reports/kpi/ipe/{id}`, `/reports/kpi/weight-uniformity/{id}` **403 ×12** en el detalle de lote; `/dashboard/admin` **403** en el home; aprobador → `/users` **403 ×7** en el centro de revisión.
- UI: **denegación ≡ vacío** en 9 páginas (`LotListPage.tsx:32`, `OperationListPage.tsx:42`, `AuditPage.tsx:74`, `ReportsPage.tsx:17,33`, `MasterListPage.tsx:59`, `RolesPage.tsx:42`, `SapManagerPage.tsx:39`, `CorrectionForm.tsx:38`… C#19); **carga eterna** en `LotReportPage.tsx:64` y `SapComparisonPage.tsx:17` (C#20); `HomeRoute` sin `dashboard:read` muestra «Permiso requerido» + Reintentar (F G-02, nota N-1, 403 [RT]).
- Contraste correcto: `UsersPage.tsx:37-63` distingue `prohibido/error/ok`.

## 2 · Causa raíz

Gates de cliente incompletos/heterogéneos: se piden recursos sin comprobar el permiso; los `catch` colapsan 403/500 en «vacío»; el home asume `dashboard:read`.

## 3 · Comportamiento actual → esperado

| Superficie | Hoy | Esperado |
|---|---|---|
| Detalle de lote (KPI) | 403 ×12 en consola | no pedir sin permiso; bloque «sin permiso» o sección oculta |
| Centro de revisión (`/users`) | 403 ×7 | no pedir la lista de usuarios sin `users:read` (filtro local o backend) |
| Home sin `dashboard:read` | error + Reintentar | landing útil (p. ej. `/menu/poultry` o primer hub visible) |
| Listas (lotes/operaciones/auditoría/reportes/maestros/roles/SAP/corrección) | 403 ≡ «vacío» | estados distinguidos (prohibido/error/vacío) como en `/users` |
| `LotReportPage`/`SapComparisonPage` | spinner infinito en error | estado de error con reintento |

## 4 · Secciones §47 (resumen)

- **Alcance FE**: gates con `useCan`/`filterNavItemsBySession` en las superficies listadas; patrón de estados de `UsersPage`; `HomeRoute` fallback; `ErrorState` reutilizable (nuevo componente o patrón).
- **Fuera**: backend (denegación correcta; sin cambios); R-150 completo (familia); permisos nuevos.
- **Contrato**: se dejan de emitir peticiones denegadas (menos ruido); sin cambios de esquema.
- **Seguridad**: UI sigue sin ser autoridad (backend intacto).
- **i18n**: claves de estado (`common.forbidden` existe; añadir 2-3 si faltan). **Móvil**: home móvil ya redirige a `/menu/poultry` (mantener).
- **Migración/SAP**: ninguna / indirecto (menos errores de consola).
- **AC/cierre**: ver `R-212_AC_RED_E2E_UAT.md`.

## 5 · Dedup

Familia R-119/R-120 (`GA-FE-03/04` cerraron casos puntuales; F/C documentan los residuales); N-1 (UAT-08) y N-3 (UAT-04) registradas como observaciones. **Nuevo** como paquete (G-24), sin duplicar R-150 (más amplio, sigue abierto).

## 6 · Interdependencias

R-197 (centro de revisión) · R-215 (estados de error/render) · R-216 (panel) · R-150/R-119/R-120 (familia).
