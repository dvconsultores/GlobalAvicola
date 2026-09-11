# GA-FE-03 · CLARIFICACIONES

**Método**: resueltas contra repositorio/specs/OD vigentes — sin interrupción al propietario
cuando la fuente canónica responde. Solo si el repositorio **no** responde se marca
`OWNER_QUESTION`.

| # | Pregunta | Respuesta | Fuente |
|---|---|---|---|
| C01 | ¿Qué gobierna `R-98` realmente? | «Ninguna pantalla oculta acciones de escritura por permiso; no hay modelo de permisos en el frontend» (P2, transversal, `P-13`). Residuo de `AC-FE16`: `/me` no exponía permisos — **hoy sí los expone** (fase 8). Su parte de **navegación accionable** entra en GA-FE-03; la de acciones intra-pantalla excede la tranche | `REMEDIATION_BACKLOG.md` §R-98; `MASTER_FRONTEND_RUNTIME_AUDIT_EVIDENCE §30` |
| C02 | ¿Qué gobierna `R-119`? | «El frontend no comprueba permisos en ninguna pantalla» (P1): `navigationConfig.ts` estático, 0 `hasPermission`, `docs/02 §3.1.3` pide módulos accesibles por rol. No es agujero de seguridad: el backend deniega. Depende de fase 8 para el contrato de capacidades — **ya entregado** | Backlog §R-119; `NAVIGATION_ROLE_BU_MATRIX` |
| C03 | Fuentes canónicas de navegación | `Sidebar` + `MobileDrawer` (misma `navigationConfig.ts`), `MobileNav` (barra inferior fija), `MenuHubPage` (`/menu/:key`), atajos del `DashboardPage` (tarjetas de procesos), y el selector de empresa (Header). Única fuente declarativa: `navigationConfig.ts` | Inventario §GA_FE_03_NAV_SOURCE_INVENTORY |
| C04 | Fuentes de guardas de ruta | `App.tsx`: `ProtectedRoute` (sesión + `webOnly`), `PoultryHubLegacyRoute`, `PermissionRoute` (solo `/admin/unit-access`, GA-FE-02), redirects legacy `/processes`. `ProtectedRoute.roles` es código muerto (jamás recibe `roles`) | `App.tsx` líneas 43–87 |
| C05 | Semántica del helper de permisos | `auth/permissions.ts` es espejo EXACTO de `tiene_permiso` (`backend/app/auth/security.py`): comodín del actor global (`is_super_admin`), permiso exacto, comodín de módulo `*:accion`. **Se reutiliza; no se crea otra gramática** | `permissions.ts`; `R-121` |
| C06 | ¿Productivo vs control? | Control: no depende de BU ni concesiones (usuarios, roles, maestros, auditoría, unidades-empresa). Productivo: exige BU efectiva (`OD-09.a/b`, `OD-16.f`). Reportes/review/aprobaciones son productivos aunque sean «lectura» (`D-1`) | `OD-09`, `OD-16`, GA-FE-02-D |
| C07 | Mapa dependencia BU | `poultry`→por unidad hija (`grandparent`/`breeder`/`hatchery`/`broiler`); `review`/`approvals`/`reports`→cualquiera (conjunto efectivo no vacío); control→ninguna | `OD-16.a/f`; servicios backend |
| C08 | Reglas del actor global | Sin contexto: selector visible, inquilino fail-closed. Situado: productivo visible solo para unidades **habilitadas** (`company_business_units`); jamás cruza BU OFF; nunca unión de inquilinos | `OD-14`; `D-1` fix `9ffc5ec` |
| C09 | Comportamiento zero-BU | Autenticado sin concesiones: login OK, CORE según RBAC visible, productivo oculto, sin grupos vacíos, sin pantalla de error genérica al entrar | `OD-09.c` (`BU-D09=B`), `AC-H06` |
| C10 | Grupos vacíos | Desaparecen (sección sin hijos visibles no renderiza; contenedor sin hijos visibles no renderiza) | Política §9F del encargo; práctica actual del Sidebar para secciones |
| C11 | Comportamiento móvil | Misma semántica; `view_type=mobile` conserva su recorte de presentación (drawer operativo; barra Inicio/KPI/Operativo). Productivo oculto también en móvil | `AppLayout`/`MobileNav`; encargo §35 |
| C12 | Invalidación al cambiar de empresa | `switchCompany` reemplaza ambos tokens y llama `fetchMe()`; el estado zustand actualiza `user` ⇒ la navegación se recalcula en el mismo render posterior. Hard refresh reconstruye idéntico (=`/me`) | `company.store.ts`; `auth.store.ts`; `GA-FE-02` E2E |
| C13 | Invalidación por grant/revoke | Semántica canónica de sesión: los cambios sobre **el propio** usuario son efectivos en el siguiente `/me` (refresh o relogin). La administración de otro usuario no se propaga a una pestaña ya abierta. Certificación: GET fresco + refresh + relogin del objetivo, con la semántica registrada | `GA-REM-040 §14`; GA-FE-02 §10 |
| C14 | Propagación de cambio de rol | Igual: RBAC se re-lee en `/me`; **no** se inventa propagación en tiempo real; relogin/refresh documentado | `GA-REM-003` (`R-118` familia); GA-FE-02 |
| C15 | Política de deep link | La guarda de ruta es independiente del menú; permiso ausente ⇒ denegación visual fail-closed **y** backend 403/404. BU ausente/OFF ⇒ ídem por unidad de URL donde aplica; datos productivos jamás servidos | `OD-14`, `OD-16.f`; encargo §36 |
| C16 | Rutas legacy | `/processes`, `/processes/:stage` → redirects activos (soporte); `/menu/:key` hubs (activos); sin eliminaciones en esta tranche. Clasificación completa en la matriz de rutas | `App.tsx`; encargo §32 |
| C17 | Clasificación reportes/KPI | `REPORTING` productivo: mismas dimensiones BU que el dato que exponen; `do not expose` con BU OFF | `D-1`; encargo §20 |
| C18 | Clasificación audit/masters/admin | `CONTROL_PLANE` de inquilino (`INQUILINO` OD-14): visibles con permiso real, **sin** concesiones BU; audit `audit:read`, masters `masters:read`, users/roles `users:read` | `OD-14.c`; routers backend |
| C19 | Contrato i18n | `public/locales/{es,en}/translation.json` (http backend); claves `nav.*`; se añade `nav.roles`; sin claves crudas | `i18n/index.ts` |
| C20 | Criterio de cierre | `GA-FE-03 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING` solo con la certificación runtime autenticada completa (actores + 3D + deep links + desktop/móvil + ES/EN); `R-98`/`R-119` según evidencia individual; `GA-FE-02` sigue `PENDING` hasta UAT del propietario | Encargo §94/§97/§96 |

**Preguntas al propietario**: NINGUNA. `OWNER_RATIFIED_POLICY: NONE` (BU-D10 pendiente, sin
cambio).
