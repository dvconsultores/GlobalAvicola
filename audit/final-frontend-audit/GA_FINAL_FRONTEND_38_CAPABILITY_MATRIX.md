# FINAL FRONTEND AUDIT · MATRIZ 38 CAPACIDADES (RECONCILIADA)

Estado final por fila (2026-09-11, runtime `index-DtzHNDMG.js`). Leyenda estados: `F_C_OA` = FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTED · `VNC` = IMPLEMENTED_VISIBLE_NOT_CERTIFIED · `ODR` = OWNER_DECISION_REQUIRED · `OOS` = OUT_OF_CURRENT_PRODUCT_SCOPE · `BE` = BLOCKED_EXTERNAL.
Desktop/Mobile: `✓` PASS · `N/A(w)` = ruta web-only (redirect móvil por diseño) · Deep link `✓` probado/por contrato de guarda. ES/EN: `✓` clave traducida (paridad ES/EN en suite).

## A · Identidad · autoridad · entrega

| FVA | Capacidad (CAP) | Proceso | Estado históricо | Blocker histórico | Ruta actual | Componente | Backend/API | Dominio | Empresa req. | BU usuario req. | Permiso req. | Desktop | Mobile | Deep link | ES | EN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FVA-01 | Sesión con token (CAP-SES-01) | Sesión | BLOCKED_AUTH | sin cuentas | `/login` | LoginPage | POST /login · /me | CORE | — | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-02 | Cambio de contraseña (CAP-SES-02) | Sesión | BLOCKED_AUTH | sin cuentas | `/profile` | ProfilePage | POST /users/{id}/password | CORE | — | — | — | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-03 | Perfil (CAP-SES-03) | Sesión | BLOCKED_AUTH | sin cuentas | `/profile` | ProfilePage | /me | CORE | opcional | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-04 | Contexto de empresa (CAP-SES-04) | Sesión | BLOCKED_AUTH | sin cuentas | header/dashboard | Header/Dashboard | /me | CORE | sí | — | dashboard:read (home) | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-05 | Selector de empresa global (CAP-SES-05) | Sesión | IMPLEMENTED_BUT_NOT_EXPOSED | render cond. | header | Header dropdown | POST /switch-company | CORE | contexto | — | is_super_admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-06 | Catálogo de empresas (CAP-ADM-01) | Administración | BLOCKED_AUTH | sin cuentas | `/masters/companies` | MasterListPage | /masters/companies | CONTROL | sí | — | masters:read | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-07 | Admón. de empresas (CAP-ADM-02) | Administración | OWNER_DECISION_REQUIRED | R-124/AOD-06 | `/masters/companies` (alta/edición) | MasterListPage | masters CRUD | CONTROL | sí | — | masters:create/update | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-08 | Unidades por empresa (CAP-ADM-03) | Administración | FRONTEND_MISSING | fase 9 congelada | `/admin/unit-access` | UnitAccessPage | /business-units enable/disable | CONTROL | sí (admin) | — | business_units:* | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-09 | Unidades por usuario (CAP-ADM-04) | Administración | FRONTEND_MISSING | fase 9 congelada | `/admin/unit-access` + panel usuario | UnitAccessPage/UserBUButton | grants API | CONTROL | sí | — | business_units:* | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-10 | Bandeja de clasificación (CAP-ADM-05) | Administración | FRONTEND_MISSING | fase 9 congelada (condicional) | — (sin UI) | ausente | /operations/pending-classification | CONTROL | — | — | — | N/A | N/A | N/A | — | — |
| FVA-11 | Nav por permisos/unidades (CAP-ADM-06) | Navegación | FRONTEND_MISSING | menú estático | NAV_ITEMS+guardas | evaluador canónico | — | PRODUCTIVE/CTRL | sí | por ítem | por ítem | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-12 | Estado zero-BU (CAP-ADM-07) | Navegación | FRONTEND_MISSING | sin distinción | árbol/estados | evaluador | — | CORE/CTRL | sí | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-13 | Gestión de usuarios (CAP-ADM-08) | Administración | BLOCKED_AUTH | patrón R-122 | `/users` | UsersPage | users CRUD | CONTROL | sí | — | users:* | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-14 | Roles y permisos (CAP-ADM-09) | Administración | DEPLOYMENT_STALE | ruta ausente en bundle | `/roles` | RolesPage | roles CRUD | CONTROL | sí | — | users:read (+*:create/update) | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-15 | Rol en formulario de usuario (CAP-ADM-10) | Administración | BLOCKED_AUTH | sin cuentas | `/users` (form) | UsersPage form | users API | CONTROL | sí | — | users:create/update | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-16 | Entradas productivas 4 unidades (CAP-BU-01) | Producción | BLOCKED_AUTH | gating por unidad | `/menu/poultry` + `/poultry/*` | MenuHub/PoultryStage | operations API | PRODUCTIVE (4) | sí | sí | operations:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-17 | Importación abuelas plan (CAP-BU-02) | Progenitoras | DEPLOYMENT_STALE | UI antigua 400 BR-22 | wizard `grandparent_import` | OperationFormPage | validadores BR-22 | PRODUCTIVE gp | sí | sí | operations:create | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-18 | Catálogo incubadora (CAP-BU-03) | Incubadora | DEPLOYMENT_STALE | bundle sin sección | `/poultry/hatchery` + `birth_registration` | OperationFormPage | catálogo | PRODUCTIVE hat | sí | sí | operations:* | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-19 | Lote automático de abuelas (CAP-BU-04) | Progenitoras | OWNER_DECISION_REQUIRED | R-153/AOD-25 | — | — | — | PRODUCTIVE gp | sí | sí | — | N/A | N/A | N/A | — | — |
| FVA-20 | Recepción de aves P-01 (CAP-OPS-01) | Operaciones | BLOCKED_AUTH | sin cuentas | `/operations` + `bird_reception` | OperationList/Form | operations API | PRODUCTIVE | sí | sí | operations:read/create | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-21 | Recepción reproductoras B01/B02 (CAP-OPS-02) | Reproductoras | DEPLOYMENT_STALE | UI antigua 400 BR-20 | wizard `breeder_rearing` | OperationFormPage | BR-20 backend | PRODUCTIVE br | sí | sí | operations:* | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-22 | Control diario P-02 (CAP-OPS-03) | Operaciones | BLOCKED_AUTH | sin cuentas | `/operations` (feed/water/weight/mortality) | OperationList/Form | operations API | PRODUCTIVE | sí | sí | operations:* | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-23 | Nacimiento B13/R-170 (CAP-OPS-04) | Incubadora | DEPLOYMENT_STALE | UI antigua 400 BR-21 | `birth_registration` | OperationFormPage | BR-21 | PRODUCTIVE hat | sí | sí | operations:* | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-24 | Consumo de agua B05 (CAP-OPS-05) | Reproductoras/Engorde | DEPLOYMENT_STALE | captura ausente runtime | `water_consumption` | OperationFormPage | water_liters | PRODUCTIVE | sí | sí | operations:* | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-25 | Despacho fila fértil (CAP-OPS-06) | Incubadora | DEPLOYMENT_STALE | UI antigua divergente | `egg_dispatch` | OperationFormPage | R-172/174 | PRODUCTIVE hat | sí | sí | operations:* | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-26 | Ciclo P-07 (CAP-OPS-07) | Revisión | BLOCKED_AUTH | R-181 secundario | `/review` `/approvals` (+submit) | ReviewCenter/ApprovalPanel | review/approvals API | PRODUCTIVE | sí | sí | review:*/approvals:* | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-27 | Envío/reenvío a revisión (CAP-OPS-08) | Operaciones | FRONTEND_MISSING | submit sin llamadores (R-181) | detalle de operación (CTA) | OperationDetailPage | POST /operations/{id}/submit | PRODUCTIVE | sí | sí | operations:create+units | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-28 | Pantalla de reverso (CAP-OPS-09) | Operaciones | FRONTEND_MISSING | diferida a fase 9 | — (sin UI) | ausente | reversal interno (GA-REM-041) | PRODUCTIVE | — | — | — | N/A | N/A | N/A | — | — |
| FVA-29 | Lotes P-06 (CAP-OPS-10) | Engorde+ | BLOCKED_AUTH | sin entrada de menú | `/lots*` (hub Gestión Avícola) | LotList/Detail/Form | lots API | PRODUCTIVE | sí | sí | lots:read/create | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-30 | Evidencias (CAP-OPS-11) | Operaciones | BLOCKED_AUTH | volumen R-52 | detalle de operación | OperationDetailPage | upload/download | PRODUCTIVE | sí | sí | operations:create/delete | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-31 | Dashboard/KPI (CAP-OPS-12) | Reportes | BLOCKED_AUTH | sin cuentas | `/`, `/kpi`, `/lots/:id`, `/reports` | Dashboard/LotDetail/Reports | KPI APIs | PRODUCTIVE/REPORT | sí | sí | dashboard/reports:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-32 | SAP refs/envíos (CAP-OPS-13) | SAP | BLOCKED_AUTH | backend PARTIAL R-112 · P-08 | `/sap` | SapManagerPage | sap refs/consolidación | SAP_SPECIFIC | sí | — | sap:read | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-33 | Maestros 19+áreas (CAP-MAS-01) | Maestros | DEPLOYMENT_STALE | bundle sin novedades | `/masters/*` (20) | MasterListPage | masters API | SHARED | sí | — | masters:read | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-34 | Áreas maestro (CAP-MAS-02) | Maestros | DEPLOYMENT_STALE | bundle sin áreas | `/masters/areas` | MasterListPage | areas API | SHARED | sí | — | masters:* | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-35 | Curvas de peso (CAP-MAS-03) | Maestros | DEPLOYMENT_STALE | `/weight-curves` 0→6 | `/masters/genetic-lines/:id/weight-curves` | WeightCurvesPage | weight curves API | SHARED | sí | — | masters:* | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-36 | Auditoría filtros (CAP-AUD-01) | Auditoría | DEPLOYMENT_STALE | pestañas sin filtro | `/audit` | AuditPage | /audit API | TRANSVERSAL | sí | — | audit:read | ✓ | N/A(w) | ✓ | ✓ | ✓ |
| FVA-37 | Notificaciones (CAP-NOT-01) | Notificaciones | DEPLOYMENT_STALE | `/notifications` 0→3 | header (campana) | NotificationBell | notifications API | CORE/CTRL | sí | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| FVA-38 | Errores distinguibles (CAP-ERR-01) | Transversal | DEPLOYMENT_STALE | patrón antiguo | guardas/mensajes | CapabilityRoute et al. | — | TRANSVERSAL | — | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |

## B · Resultado actual · evidencia · certificación · cierre

| FVA | Resultado runtime (2026-09-11) | Nivel evidencia | Certificador técnico | ¿UAT req.? | Artefacto UAT | Aceptación | **Estado final** | Residual | Finding/Obs | Evidencia (archivo) | Captura |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FVA-01 | sesión real en todos los actores; relogin | L5 | GA-FE-02 | YES | GA-UAT-01 | ACCEPTED | **F_C_OA** | NONE | — | ga-uat-01 · runtime-uat.json | S01 |
| FVA-02 | 204 → relogin 200 → 204 (ida y vuelta) | L3 | — | NO cert | — | — | **VNC** | hygiene P3 | — | runtime-uat.json | S19 |
| FVA-03 | página de perfil carga | L2 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat.json | S19 |
| FVA-04 | nombre de empresa visible (header) | L5 | GA-FE-02 | YES | GA-UAT-01 | ACCEPTED | **F_C_OA** | NONE | — | ga-uat-01 | S01 |
| FVA-05 | selector alcanzable (F4 previo; sin regresión) | L5 | GA-FE-02-B | YES | GA-UAT-01 | ACCEPTED | **F_C_OA** | NONE | — | ga-fe-02-b | — |
| FVA-06 | 1 fila cargada | L2 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat (companiesRows=1) | S13 |
| FVA-07 | UI de alta/edición existente (régimen provisional ratificado `OD-24`) | L2 | — | — | — | — | **SUPERSEDED_BY_CANONICAL_DECISION** | OD-24: sin producto hoy; SPEC de convergencia pre-P-08 | R-124 RESUELTO | GA_OD_24_…DECISION.md | — |
| FVA-08 | 4 unidades listadas; ciclo ON/OFF certificado | L5 | GA-FE-02 + R-188 | YES | GA-UAT-01/08 | ACCEPTED | **F_C_OA** | NONE | — | ga-uat-08 | S16 |
| FVA-09 | revoke→regrant por UI verificado hoy | L5 | GA-FE-02 + R-188 | YES | GA-UAT-01/08 | ACCEPTED | **F_C_OA** | NONE | — | runtime-uat (regrantRow) | S16 |
| FVA-10 | no existe UI (0 refs; backend listo) | L0 | — | — | — | — | **OOS** | diseño-condicional (P2) | T-040-24 | orig inventory | — |
| FVA-11 | hub 5 tarjetas; menús evaluados | L5 | GA-FE-03 | YES | GA-UAT-01 | ACCEPTED | **F_C_OA** | NONE | — | ga-fe-03 | S02 |
| FVA-12 | zero-BU sin productivo; mensajes propios | L5 | GA-FE-03 | YES | GA-UAT-01 (c10) | ACCEPTED | **F_C_OA** | NONE | — | runtime (zbu) | S17 |
| FVA-13 | 20 filas + alta visible; acciones gateadas | L4/L5 | GA-FE-04 | YES | GA-UAT-02 | ACCEPTED | **F_C_OA** | NONE | — | runtime-uat | S15 |
| FVA-14 | página carga (bundle nuevo desplegado) | L4/L5 | GA-FE-03 + GA-FE-04 | YES | GA-UAT-01/02 | ACCEPTED | **F_C_OA** | NONE | — | runtime (rolesPage) | — |
| FVA-15 | 3 selects de rol en formulario | L4/L5 | GA-FE-04 | YES | GA-UAT-02 | ACCEPTED | **F_C_OA** | NONE | — | runtime | — |
| FVA-16 | 4 etapas cargan; gating por unidad certificado | L5 | GA-FE-03 (+GA-FE-02-D) | YES | GA-UAT-01 | ACCEPTED | **F_C_OA** | NONE | — | runtime | S02/S03/S04 |
| FVA-17 | campo `import_plan.*` presente (wizard) | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | S08 |
| FVA-18 | `chicks_healthy` presente | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | — |
| FVA-19 | sin decisión (R-153) | L0 | — | — | — | — | **ODR** | R-153/AOD-25 (P3) | R-153 | backlog:944 | — |
| FVA-20 | lista + formulario de recepción | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | — |
| FVA-21 | `dead_on_arrival`/`received_total` presentes | L3 | — | — | — | — | **VNC** | hygiene P3 | — | probe-b01-wizard | S07 |
| FVA-22 | superficies P-02 cargan | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | — |
| FVA-23 | `chicks_healthy` presente | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | — |
| FVA-24 | `water_liters` presente + reporte | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | S06 |
| FVA-25 | formulario renderiza | L2 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | — |
| FVA-26 | review+approvals cargan; submit certificado | L3/L5 | GA-FE-05/04 | YES (comp.) | GA-UAT-03/02 | ACCEPTED | **VNC** | hygiene P3 | — | runtime-uat | S12 |
| FVA-27 | CTA certificada R-181 | L5 | GA-FE-05 | YES | GA-UAT-03 | ACCEPTED | **F_C_OA** | NONE | R-181 CLOSED | ga-fe-05 | — |
| FVA-28 | sin UI (deferral fase 9) | L0 | — | — | — | — | **OOS** | fase 9 (P3) | — | orig inventory | — |
| FVA-29 | descubrible + 82-95 filas + detalle | L5 | GA-FE-06/07/08 | YES | GA-UAT-04/05 + FE-08 | ACCEPTED | **F_C_OA** | NONE | R-182/185/OD-21 | ga-fe-08 | S05/S09 |
| FVA-30 | acciones presentes; volumen R-52 | L3 | GA-FE-04 (acciones) | — | — | — | **VNC** | R-52 (P2 infra) | R-52 | release blockers | — |
| FVA-31 | IPE 333.3 · G-05 5.1 · reportes | L5 | R-184/186/187 | YES (R-184/187) | GA-UAT-06/07 | ACCEPTED | **F_C_OA** | NONE | OD-22 | ga-uat-06/07 | S01/S09/S10 |
| FVA-32 | UI carga; integración real bloqueada | L2 | — | — | — | — | **BLOCKED_EXTERNAL** | R-112 (P2) | P-08/R-112 | runtime-uat | S20 |
| FVA-33 | áreas (14) y empresas (1) cargan | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | S13 |
| FVA-34 | 14 filas; elegibilidad R-185 aceptada | L3/L5 | GA-FE-07 (elegibilidad) | YES (R-185) | GA-UAT-05 | ACCEPTED | **VNC** | hygiene P3 | OD-21 | ga-fe-07 | S13 |
| FVA-35 | página de curvas carga | L3 | — | — | — | — | **VNC** | hygiene P3 | — | probe-bell-pending-curves | S21 |
| FVA-36 | página + filtros cargan | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat | S14 |
| FVA-37 | campana abre bandeja | L3 | — | — | — | — | **VNC** | hygiene P3 | — | probe-bell-pending-curves | S11 |
| FVA-38 | denegado ≠ vacío (403 visual vs lista) | L3 | — | — | — | — | **VNC** | hygiene P3 | — | runtime-uat (admLotsDenied/zbu) | S17 |

## Conteo

- **F_C_OA: 14** (FVA-01,04,05,08,09,11,12,13,14,15,16,27,29,31) · **VNC: 19** · **ODR: 1** (FVA-19) · **SUPERSEDED: 1** (FVA-07/OD-24) · **OOS: 2** · **BE: 1** → **38/38 reconciliadas**.
- Residuales «hygiene P3» (19 filas VNC) se consolidan como **un** ítem de cola (certificación formal por AC si el programa la exige).
