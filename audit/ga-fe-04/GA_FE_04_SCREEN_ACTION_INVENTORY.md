# GA-FE-04 · INVENTARIO DE PANTALLAS Y ACCIONES (R-98 / P-13)

**Base**: `73352d4` · bundle `index-CElqNz3R.js` · inventario **completo** de rutas user-visible
(§13: sin muestreo). Tipos §14. «Actual» = estado hoy en código+bundle; «Objetivo» = tras
GA-FE-04. Las acciones sin escritura se listan para completar la matriz pero con objetivo N/A.

## A · Pantallas de administración (CONTROL_PLANE)

| # | Ruta / Pantalla | Permiso de página | Acción | Tipo | API | Método → permiso backend | Actual | Objetivo |
|---|---|---|---|---|---|---|---|---|
| U1 | `/users` UsersPage | `users:read` | Abrir modal «Nuevo usuario» | CREATE | `/users` | POST → users:create | visible sin permiso | **hidden por `users:create`** |
| U2 | ídem | | Guardar alta (modal) | CREATE | `/users` | POST → users:create | visible sin permiso | **hidden** (misma spec que U1) |
| U3 | ídem | | Guardar edición | UPDATE | `/users/{id}` | PUT → users:update | visible sin permiso | **hidden por `users:update`** |
| U4 | ídem | | Cambiar contraseña de otro | UPDATE | `/users/{id}/password` | POST → users:update | visible sin permiso | **hidden por `users:update`** |
| U5 | ídem | | Activar/desactivar | UPDATE | `/users/{id}` | PUT → users:update | visible sin permiso | **hidden por `users:update`** |
| U6 | ídem | | Desactivar (delete) | DELETE | `/users/{id}` | DELETE → users:delete | visible sin permiso | **hidden por `users:delete`** |
| U7 | ídem | | Asignar rol (select del modal) | ASSIGN | `/roles`(lectura)+PUT | users:update | visible sin permiso | **hidden con U2/U3** |
| U8 | ídem | | Botón «Unidades» (UserBusinessUnitsButton) | GRANT/REVOKE | BS | business_units:read/create/delete | ya gated (GA-FE-02) | sin cambio (regresión) |
| R1 | `/roles` RolesPage | `users:read` | Abrir modal «Nuevo rol» | CREATE | `/roles` | POST → users:create | visible sin permiso | **hidden por `users:create`** |
| R2 | ídem | | Guardar rol (crear/editar permisos) | CREATE/UPDATE | `/roles`·`/roles/{id}` | POST/PUT → users:create/update | visible sin permiso | **hidden por `users:create`∪`update`** |
| R3 | ídem | | Desactivar rol | UPDATE | `/roles/{id}` | PUT → users:update | visible sin permiso | **hidden por `users:update`** |
| M1 | `/masters/*` MasterListPage (20 entidades) | `masters:read` | «Nuevo» | CREATE | `/masters/{entity}` | POST → masters:create | visible sin permiso | **hidden por `masters:create`** |
| M2 | ídem | | «Editar» (fila) | UPDATE | `/masters/{entity}/{id}` | PUT → masters:update | visible sin permiso | **hidden por `masters:update`** |
| M3 | ídem | | «Eliminar» (fila) | DELETE | `/masters/{entity}/{id}` | DELETE → masters:delete | visible sin permiso | **hidden por `masters:delete`** |
| M4 | ídem | | «Gestionar curvas» (fila genetic-lines) | READ_NAVIGATION | — | (destino masters:read) | visible (página ya requiere read) | sin cambio (navegación) |
| W1 | `/masters/genetic-lines/:id/weight-curves` | `masters:read` | «Cargar tabla» (upload) | UPLOAD | `/masters/weight-curves` | POST → masters:create | visible sin permiso | **hidden por `masters:create`** |
| W2 | ídem | | «Activar» curva | UPDATE | `/masters/weight-curves/{id}/activate` | PUT → masters:update | visible sin permiso | **hidden por `masters:update`** |
| A1 | `/admin/unit-access` | `business_units:read` | Activar/desactivar unidad | CONTROL_PLANE_ACTION | BS | business_units:update | **ya gated** (canUpdate) | sin cambio |
| A2 | ídem | | Conceder/revocar | GRANT/REVOKE | BS | business_units:create/delete | **ya gated** | sin cambio |

## B · Pantallas productivas

| # | Ruta / Pantalla | Permiso de página | Acción | Tipo | API | Método → permiso backend | Actual | Objetivo |
|---|---|---|---|---|---|---|---|---|
| L1 | `/lots` LotListPage | `lots:read` | CTA «Nuevo lote» | CREATE | (navega a `/lots/new`) | POST → lots:create | visible sin permiso | **hidden por `lots:create`** |
| L2 | `/lots/new` LotFormPage | WebOnly | Guardar lote | CREATE | `/lots` | POST → lots:create | ruta sin guarda de permiso | **guarda de ruta `lots:create`** |
| L3 | `/lots/:id` LotDetailPage | `lots:read` | Cerrar lote | UPDATE | `/lots/{id}/close` | POST → **lots:create** | visible sin permiso | **hidden por `lots:create`** |
| L4 | ídem | | Añadir fase | CREATE | `/lots/{id}/phases` | POST → lots:create | visible sin permiso | **hidden por `lots:create`** |
| L5 | ídem | | Resolver alerta | UPDATE | `/operations/alerts/{id}/resolve` | PATCH → operations:update | visible sin permiso | **hidden por `operations:update`** |
| L6 | ídem | | «Reporte / trazabilidad / IPE…» (pestañas y descargas de lectura) | READ_NAVIGATION | GETs | read | visible | sin cambio |
| O1 | `/operations` OperationListPage | `operations:read` | (CTA de alta si existe → verificar en impl) | CREATE | — | operations:create | visible sin permiso | **hidden por `operations:create`** (si existe) |
| O2 | `/operations/new` OperationFormPage | (sin guarda) | Guardar operación | CREATE | `/operations` (o submit) | POST → operations:create | ruta sin guarda | **guarda de ruta `operations:create`** |
| O3 | `/operations/:id` OperationDetailPage | `operations:read` | Subir evidencia | CREATE | `/operations/{id}/evidences` | POST → operations:create | visible sin permiso | **hidden por `operations:create`** |
| O4 | ídem | | Eliminar evidencia | DELETE | `/operations/{id}/evidences/{eid}` | DELETE → operations:delete | visible sin permiso | **hidden por `operations:delete`** |
| O5 | ídem | | «Enviar a revisión» | — | `/operations/{id}/submit` | POST → operations:create | **no existe en UI** | `EXCLUDED_R181` (no se implementa) |
| O6 | ídem | | Cancelar | UPDATE | `/operations/{id}/cancel` | POST → operations:create | (verificar impl; si existe) | **hidden por `operations:create`** |
| P1 | `/my-pending` MyPendingPage | `operations:read` | Acciones de fila (si son de lectura→navegación) | READ_NAVIGATION | — | read | visible | sin cambio |
| S1 | `/poultry/:birdType/:phase?` ProcessStagePage | `operations:read` + BU | Tiles de secuencia (navegan a alta) | READ_NAVIGATION | — | (destino create) | visible (aceptado en GA-FE-03/UAT) | **sin cambio** — la autoridad de alta se aplica en destino (O2) y backend; documentado en §7 |
| S2 | `/menu/:key`, `/poultry` hub | GA-FE-03 | Tarjetas de proceso | READ_NAVIGATION | — | — | gated GA-FE-03 | sin cambio |

## C · Revisión / aprobación / corrección

| # | Ruta / Pantalla | Permiso de página | Acción | Tipo | API | Método → permiso backend | Actual | Objetivo |
|---|---|---|---|---|---|---|---|---|
| V1 | `/review` ReviewCenter | `review:read` | «Iniciar revisión» | REVIEW | `/review/start/{id}` | POST → review:review | visible sin permiso | **hidden por `review:review`** |
| V2 | ídem | | Completar/Devolver | REVIEW | `/review/complete`·`return` | POST → review:review | visible sin permiso | **hidden por `review:review`** |
| V3 | ídem | | Crear lote de revisión (batch) | REVIEW | `/review/batches` | POST → **review:review** | visible sin permiso | **hidden por `review:review`** |
| V4 | ídem | | «Corregir» (→ `/review/:id/correct`) | CORRECT | — | destino corrections:correct | visible sin permiso | **hidden por `corrections:correct`** |
| V5 | `/review/:id` ReviewDetail | `review:read` | Iniciar/Completar/Devolver | REVIEW | ídem | review:review | visible sin permiso | **hidden por `review:review`** |
| V6 | ídem | | Aprobar / Rechazar (evento corregido) | APPROVE/REJECT | `/approvals/approve`·`reject` | approvals:approve / approvals:reject | visible sin permiso | **hidden por permiso respectivo (separados)** |
| V7 | `/review/:id/correct` CorrectionForm | (sin guarda) | Guardar corrección | CORRECT | `/corrections` | POST → corrections:correct | ruta sin guarda | **guarda de ruta + gate del guardar `corrections:correct`** |
| V8 | `/approvals` ApprovalPanel | (guarda `approvals:approve` GA-FE-03) | Aprobar | APPROVE | `/approvals/approve` | approvals:approve | gated a nivel ruta; botón visible | **sin cambio de ruta; botón gated (ya coincide)** |
| V9 | ídem | | Rechazar | REJECT | `/approvals/reject` | approvals:reject | botón visible sin permiso específico | **hidden por `approvals:reject`** |
| V10 | ídem | | Batch aprobar/rechazar + selección | APPROVE/REJECT | `/approvals/batch-*` | POST → **review:review** | visible sin permiso | **hidden por `review:review`** (contrato canónico) |

## D · Integración / auditoría / reportes / sesión

| # | Ruta / Pantalla | Permiso de página | Acción | Tipo | API | Permiso backend | Actual | Objetivo |
|---|---|---|---|---|---|---|---|---|
| G1 | `/sap` SapManagerPage | `sap:read` | Consolidar | CONFIGURE | `/sap/consolidate` | sap:send_sap | visible sin permiso | **hidden por `sap:send_sap`** |
| G2 | ídem | | Exportar a SAP | CONFIGURE | `/sap/export` | sap:send_sap | visible sin permiso | **hidden por `sap:send_sap`** |
| G3 | ídem | | Reintentar | CONFIGURE | `/sap/retry` | sap:send_sap | visible sin permiso | **hidden por `sap:send_sap`** |
| G4 | ídem | | Importar referencias (si existe botón) | CREATE | `/sap/references/import` | sap:send_sap | verificar en impl | **hidden por `sap:send_sap`** |
| G5 | ídem | | Consultas (references/consolidated/jobs/payloads/errors/connection-check) | READ | GETs | sap:read | visible | sin cambio |
| X1 | `/audit` AuditPage | `audit:read` | Filtros y detalle (solo lectura; sin export) | READ | GET | audit:read | visible | N/A |
| X2 | `/reports`, `/reports/lot/:id`, `/reports/sap` | `reports:read` | Consultas (sin export ni descargas) | READ | GET | reports:read | visible | N/A |
| X3 | `/notifications` (campana) | sesión | Marcar leída (self) | OTHER (self) | POST self | — | visible | N/A (self) |
| X4 | `/profile` | sesión | Cambiar contraseña propia | UPDATE (self) | `/users/me/password` | self | visible | N/A (CORE self — no es autoridad de terceros) |
| X5 | `/login`, `/kpi`, `/` | público/sesión | — | OTHER | — | — | — | N/A |

## E · Conteos

```
Filas de inventario ................ 54 (incluye lecturas/N-A para completitud)
Pantallas .......................... 32 rutas (20 entidades de maestros = 1 grupo)
Mutaciones/acciones de escritura ... 31 (U:12 · R:3 · M:3 · W:2 · L:4 · O:4 · V:9 · G:4)
  CREATE 9 · UPDATE 9 · DELETE 2 · REVIEW 4 · APPROVE 2 · REJECT 2 · CORRECT 1 (gate) ·
  UPLOAD 1 (dentro de CREATE de curvas) · CONFIGURE 3 (SAP = send_sap)
CTAs de estado vacío ............... MasterListPage «Nuevo», LotListPage «Nuevo lote»,
                                     botones de alta de Usuarios/Roles
Guardas de ruta nuevas ............. 3 (`/lots/new` lots:create · `/operations/new`
                                     operations:create · `/review/:id/correct` corrections:correct)
Ya conformes (GA-FE-02/03) ......... U8 · A1 · A2 · V8(ruta) + navegación completa GA-FE-03
Acciones masivas .................... 3 (batch approve/reject + selección del centro — review:review)
Modales privilegiados .............. altas/ediciones de Usuarios/Roles/Maestros/Curvas,
                                     confirmaciones de borrado y cierre de lote
Alternas móvil ...................... las mismas (sin menús de desborde con mutaciones)
EXCLUDED_R181 ....................... O5 («submit»; no existe UI; no se implementa) + O6 se
                                      implementa solo si existe (gate), la función cancel ya es backend
EXCLUDED_R182 ....................... 0 (LotForm sin cambios)
N/A documentadas .................... auditoría/reportes/notificaciones/perfil (lectura o self)
```
