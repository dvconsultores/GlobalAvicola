# GA-FE-04 · TAREAS

| ID | Finding | SPEC | AC | Página/acción | Archivos esperados | Test | Runtime | Estado |
|---|---|---|---|---|---|---|---|---|
| T0 | R-98 | §2–10 | AC01–03 | docs | `audit/ga-fe-04/*` | — | — | ✅ |
| T1 | R-98 | §18 | AC06 | capa compartida | `src/auth/actionAuthority.ts` (nuevo) | `gaFe04.actionAuthority.test.ts` | — | pendiente |
| T2 | R-98 | §11 | AC15 | UsersPage | `pages/users/UsersPage.tsx` | usuarios: gates | R ve listado sin botones; API 403 |
| T3 | R-98 | §11 | AC15 | RolesPage | `pages/users/RolesPage.tsx` | roles: gates | R no ve alta/edición |
| T4 | R-98 | §11 | AC15/30 | MasterListPage | `pages/masters/MasterListPage.tsx` | maestros: gates + vacío | R sin Nuevo/Editar/Eliminar |
| T5 | R-98 | §11 | AC15 | WeightCurvesPage | `pages/masters/WeightCurvesPage.tsx` | curvas: gates | R sin cargar/activar |
| T6 | R-98 | §12 | AC09–13 | LotList/LotDetail/LotForm | `pages/lots/LotListPage.tsx`, `LotDetailPage.tsx` | lotes: gates | 3D + cerrar/fase |
| T7 | R-98 | §12 | AC09–13 | OperationList/Detail/Form | `pages/operations/OperationListPage.tsx`, `OperationDetailPage.tsx` | operaciones: gates | 3D + evidencia |
| T8 | R-98 | §12 | AC11–14 | Review×3/Approvals | `ReviewCenter.tsx`, `ReviewDetail.tsx`, `CorrectionForm.tsx`, `ApprovalPanel.tsx` | revisión: gates | matriz V1–V10 |
| T9 | R-98 | §14 | AC20/21 | SAP + verificación self/cross | `pages/sap/SapManagerPage.tsx` | sap: gates | §79/80 |
| T10 | R-98 | §15 | AC24–26 | Paridad de rutas | `src/App.tsx` (3 guardas) | `gaFe04.routeParity.test.tsx` | deep links |
| T11 | R-98 | §17 | AC31–33 | i18n | `public/locales/{es,en}` | `gaFe04.i18n.test.ts` | ES/EN |
| T12 | R-98 | §13 | AC09 | 3D navegación/acción BU | (sin código nuevo) | — | 3D 4/4 |
| T13 | R-98 | §19/20 | AC08 | negativas API | (sin código) | — | 403/404 |
| T14 | R-98 | §21 | AC28 | móvil | (sin código) | — | 390×844 |
| T15 | R-98 | §22 | AC37–40 | regresión | (sin código) | suite | spots |
| T16 | R-98 | §23–25 | cierre | evidencia+reconciliación | `audit/ga-fe-04/*` | — | informe |

**Prohibido**: tocar backend (esperado 0), LotForm (R-182), submit (R-181), SEMÁNTICA
GA-FE-02/03. `git add` explícito; secret-check por commit.
