# GA-FE-04 · TAREAS

| ID | Finding | SPEC | AC | Página/acción | Archivos esperados | Test | Runtime | Estado |
|---|---|---|---|---|---|---|---|---|
| T0 | R-98 | §2–10 | AC01–03 | docs | `audit/ga-fe-04/*` | — | — | ✅ |
| T1 | R-98 | §18 | AC06 | capa compartida | `src/auth/actionAuthority.tsx` (nuevo) | `gaFe04.actionAuthority.test.tsx` 5/5 | — | ✅ |
| T2 | R-98 | §11 | AC15 | UsersPage | `pages/users/UsersPage.tsx` | usuarios 2/2 | R: Crear=0·pencil=0·trash=0; API 403 | ✅ |
| T3 | R-98 | §11 | AC15 | RolesPage | `pages/users/RolesPage.tsx` | roles (gates) | R sin alta/edición/desactivar | ✅ |
| T4 | R-98 | §11 | AC15/30 | MasterListPage | `pages/masters/MasterListPage.tsx` | maestros 2/2 + aviso | R sin Nuevo/Editar/Eliminar (pre 1/7/7 → 0/0/0) | ✅ |
| T5 | R-98 | §11 | AC15 | WeightCurvesPage | `pages/masters/WeightCurvesPage.tsx` | curvas (gates) | subir=create; activar=update | ✅ |
| T6 | R-98 | §12 | AC09–13 | LotList/LotDetail/LotForm | `pages/lots/LotListPage.tsx`, `LotDetailPage.tsx` | lotes 2/2 | CTA=lots:create; cerrar/fase/acciones=lots:create; alertas=operations:update; 3D caso 4 | ✅ |
| T7 | R-98 | §12 | AC09–13 | OperationList/Detail/Form | `pages/operations/OperationDetailPage.tsx` | operaciones (gates) | evidencia crear/borrar; ruta /operations/new=operations:create; 3D caso 3/4 | ✅ |
| T8 | R-98 | §12 | AC11–14 | Review×3/Approvals | `ReviewCenter.tsx`, `ReviewDetail.tsx`, `CorrectionForm.tsx`, `ApprovalPanel.tsx` | revisión 5/5 | iniciar/completar/devolver/lote=review:review; corregir=corrections:correct; approve≠reject | ✅ |
| T9 | R-98 | §14 | AC20/21 | SAP + verificación self/cross | `pages/sap/SapManagerPage.tsx` | sap 2/2 | consolidar/exportar=sap:send_sap | ✅ |
| T10 | R-98 | §15 | AC24–26 | Paridad de rutas | `src/App.tsx` (3 guardas) | `gaFe04.routeParity.test.tsx` 4/4 | R: 3/3 deep links negados en runtime | ✅ |
| T11 | R-98 | §17 | AC31–33 | i18n | `public/locales/{es,en}` | runtime ES/EN | `actions.readOnlyViewer` verificada en prod (ES y EN) | ✅ |
| T12 | R-98 | §13 | AC09 | 3D navegación/acción BU | (sin código nuevo) | runtime C/P/D | 3D: caso 3 (P denegado) + caso 4 (C permitido) + E control; casos 1–2 ya certificados GA-FE-03 | ✅ |
| T13 | R-98 | §19/20 | AC08 | negativas API | (sin código) | runtime | R: GET 200 / escrituras 403 (masters, users) | ✅ |
| T14 | R-98 | §21 | AC28 | móvil | (sin código) | runtime móvil | R 0/0/0+aviso; C CTA=1 | ✅ |
| T15 | R-98 | §22 | AC37–40 | regresión | (sin código) | suite 263/263 + spots runtime | sin regresión GA-FE-02/03 | ✅ |
| T16 | R-98 | §23–25 | cierre | evidencia+reconciliación | `audit/ga-fe-04/*` + addendum master | certificación + reconciliación R-98 CLOSED | ✅ |
| T17 | R-98 | GA-FE-04-A | **P13-AC20** | self-grant (UI+API+audit) | (sin código; evidencia) | runtime B: UI self excluido; `403` SOD; sin persistencia | PASS (desktop+móvil) | ✅ |
| T18 | R-98 | GA-FE-04-A | **P13-AC21** | cross-company (UI+API+fuga) | (sin código; evidencia) | runtime B: X ausente; `404` sin fuga; sin persistencia | PASS (desktop+móvil) | ✅ |

**Prohibido**: tocar backend (esperado 0), LotForm (R-182), submit (R-181), SEMÁNTICA
GA-FE-02/03. `git add` explícito; secret-check por commit.
