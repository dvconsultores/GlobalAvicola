# FINAL FRONTEND AUDIT · AUDITORÍA DE AUTORIDAD DE ACCIÓN

Fecha: 2026-09-11 · Capa canónica: `auth/actionAuthority.tsx` (`canPerformAction`/`useCan`/`ActionGate`) sobre el evaluador GA-FE-03. GA-FE-04 certificó 31 acciones; `ActionGate` no se usa en páginas (patrón exclusivo `useCan`).

## 1 · Cola de acciones (evidencia de código + runtime)

| Acción | Superficies (archivo:línea) | Spec usada | Visible autorizado | Oculto sin permiso | Backend autoridad | Runtime hoy |
|---|---|---|---|---|---|---|
| Crear | UsersPage:96/108 · RolesPage:107 · MasterListPage:131/146 · WeightCurves:161/180 · LotListPage:53 | `users:create` · `masters:create` · `lots:create` | ✓ | ✓ | 403 real | ✓ (alta visible S15; CTA lotes FE-04/05) |
| Editar | UsersPage:108/110/112 · MasterListPage:157 · WeightCurves:219 | `users:update` · `masters:update` | ✓ | ✓ | 403 | ✓ |
| Eliminar | UsersPage:108 · MasterListPage:158 · OperationDetailPage:285 (evidencia) | `users:delete` · `masters:delete` · `operations:delete` | ✓ | ✓ | 403 | ✓ |
| Aprobar / Rechazar | ApprovalPanel:238/242/311/315 · ReviewDetail:241/248 | `approvals:approve/reject` | ✓ | ✓ | 403 | ✓ (panel carga S12) |
| Revisar (selección) | ReviewCenter:167-421 · ReviewDetail:212/218 · ApprovalPanel:173… | `review:review` | ✓ | ✓ | 403 | ✓ |
| Enviar / Reenviar a revisión | OperationDetailPage:121-122 | `operations:create` ∧ `requiresUnits` ∧ estado | ✓ | ✓ | 409/403 | ✓ (R-181 certificado UAT-03) |
| Corregir | CorrectionForm:139 · ReviewDetail:232/255 | `corrections:correct` | ✓ | ✓ | 403 | ✓ |
| Conceder / Revocar (control) | UnitAccessPage:294/304/329 (hasPermission legacy) · UserBusinessUnitsButton:169/174 | `business_units:create/delete` (+read) | ✓ | ✓ | 403/409 | ✓ (revoke→regrant verificado hoy) |
| Consolidar/Exportar SAP | SapManagerPage:135/139 | `sap:send_sap` | ✓ | ✓ | 403 | UI carga (integración P-08 externa) |
| Resolver alerta / acciones de lote | LotDetailPage:174/185/228/445 | `lots:create` · `operations:create/update` | ✓ | ✓ | 403 | ✓ |
| Reclasificar | **no existe en UI** (backend pending-classification — ver FVA-10) | — | — | — | — | N/A |

## 2 · Notas de consistencia (sin corrección en esta auditoría)

- **Grant/Revoke** usan `hasPermission` directo (capa antigua) en lugar de `actionAuthority` — mismo resultado funcional (control-plane); registrado como nota (P3; GA-FE-04 lo cubrió funcionalmente).
- **Exports de reportes** (`ReportsPage:77-88`, `LotReportPage:72-75`) y **descarga de evidencia** (`OperationDetailPage` ~278) sin `can()`: la exportación/descarga es lectura derivada del permiso de la ruta (`reports:read`/`operations:read`); comportamiento vigente documentado (nota P3, sin finding nuevo).
- **OperationFormPage** envía sin gate local (guarda de ruta `operations:create`); consistente con patrón general.
- `ActionGate` sin uso en páginas = API disponible, no deuda (la cobertura real está en `useCan`, cubierta por suite GA-FE-04).

**Resultado: autoridad de acción PRESERVADA (GA-FE-04); 0 regresiones; notas P3 registradas sin reabrir findings.**
