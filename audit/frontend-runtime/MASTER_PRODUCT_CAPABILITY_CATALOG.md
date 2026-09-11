# MASTER PRODUCT CAPABILITY CATALOG

Capacidades **prometidas al usuario** de Global Avícola, inventariadas **desde la promesa** (SPEC/OD/requisitos), no desde el frontend. Cada fila: fuente, actor esperado, contexto esperado y estados por capa.

- **Fecha**: 2026-09-10 · **Base**: `3808ed5` · **Modo**: AUDIT ONLY
- **Universo**: capacidades que contractualmente requieren interacción humana. Las capacidades de backend interno (RBAC enforcement, aislamiento de inquilino, listeners de auditoría, adaptador SAP…) **no** cuentan como user-visible y se listan en el anexo.

## Leyenda de estados por capa

- `backend_state`: `IMPLEMENTED` · `PARTIAL` · `MISSING` · `DEFERRED` (SAP) · `OWNER_DECISION_BLOCKED`
- `frontend_repo_state`: `IMPLEMENTED` · `PARTIAL` · `MISSING` (a fecha `3808ed5`)
- `runtime_state`: `PRESENT` · `ABSENT` · `DIVERGENT` (artefacto del 2026-09-05) · `N/A`
- `primary`: uno de los 6 estados de producto (ver SPEC §5) o `BLOCKED_AUTH` (fila pendiente de la fase 7; contada aparte)

## Catálogo

### Sesión y contexto

| ID | Capacidad | Fuente | Actor | primary | backend | frontend repo | runtime | Evidencia |
|---|---|---|---|---|---|---|---|---|
| CAP-SES-01 | Iniciar sesión / sesión con token | `docs/02 §3.1` · `GA-REM-003` | todos | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | login renderizado en navegador; API 401 sin sesión |
| CAP-SES-02 | Cambio de contraseña | `GA-REM-012` | todos | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | bundle desplegado contiene `passwordMinLength` (sonda 2026-09-04) |
| CAP-SES-03 | Perfil de usuario (ver datos) | `docs/02 §3.1.4` | todos | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | `/profile` en ambos bundles |
| CAP-SES-04 | Contexto de empresa visible (indicadores) | `OD-11` · `docs/02 §3.1.4` | todos | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | `company_name` en Header/Dashboard/Perfil/SAP (código y bundle) |
| CAP-SES-05 | **Selector de empresa (actor global)** | `docs/02 §3.1.4` · `OD-14` · `PHASE_9_PREFLIGHT` | Super Admin | **IMPLEMENTED_BUT_NOT_EXPOSED** | IMPLEMENTED | IMPLEMENTED | PRESENT | `company.store.ts` + dropdown Header; secundarios: render condicionado a `company_name`, sólo `is_super_admin` (por diseño), carga con `catch{}` silencioso; funcionalidad pendiente de cuenta autorizada |

### Administración (multiempresa / unidades / usuarios / roles)

| ID | Capacidad | Fuente | Actor | primary | backend | frontend repo | runtime | Evidencia |
|---|---|---|---|---|---|---|---|---|
| CAP-ADM-01 | Catálogo de empresas (listado) | `OD-18` · `R-127` | Admin | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | `/masters/companies` desplegado (401); masters incluye `companies` |
| CAP-ADM-02 | **Administración de empresas (crear/editar metadatos)** | `docs/02 §3.2.1` · `R-124`/`AOD-06` · `OD-18.b` | Admin | **OWNER_DECISION_REQUIRED** | PARTIAL (escritura `sap_config` `DEFERRED`) | PARTIAL | — | expectativa de propiedad SAP vs local sin decidir (R-124 vigente; no se duplica) |
| CAP-ADM-03 | **Unidades por empresa — habilitar/deshabilitar** | `GA-REM-040 T-040-21` · `AC-H04` · `OD-16.b/e` | Adm. de Accesos / Super Admin | **FRONTEND_MISSING** | IMPLEMENTED (fase 7) | **MISSING** (0 referencias) | ABSENT | `/business-units` 401 desplegado; 0 ocurrencias en frontend local y desplegado; fase 9 `FROZEN` |
| CAP-ADM-04 | **Unidades por usuario — conceder/revocar** | `T-040-22` · `AC-H05` · `OD-15` · `R-129` | Adm. de Accesos | **FRONTEND_MISSING** | IMPLEMENTED (fase 7 + `grant-candidates`) | **MISSING** | ABSENT | `grant-candidates`/`users/{id}/business-units` 401 desplegados; 0 referencias frontend |
| CAP-ADM-05 | **Bandeja de clasificación pendiente** | `T-040-24` · `AC-H07` · `OD-10.c` | Adm. de Accesos | **FRONTEND_MISSING** | IMPLEMENTED (fase 6) | **MISSING** | ABSENT | `pending-classification` 401 desplegado; 0 referencias frontend |
| CAP-ADM-06 | **Navegación adaptada a permisos y unidades** | `T-040-23` · `AC-H02/03` · `R-119`/`H360-F01` · `docs/02 §3.1.3` | todos | **FRONTEND_MISSING** | IMPLEMENTED (fase 8: sesión entrega permisos y unidades) | **MISSING** (menú estático sin campos de permiso/unidad; 0 `hasPermission`) | ABSENT | `navigationConfig.ts`; R-98/R-119 vigentes |
| CAP-ADM-07 | **Estado «sin unidades» (zero-BU)** | `T-040-23` · `AC-H06` · `OD-09.c` | usuario sin unidades | **FRONTEND_MISSING** | IMPLEMENTED | **MISSING** | ABSENT | ninguna superficie distingue «sin unidades» de «sin datos» |
| CAP-ADM-08 | Gestión de usuarios (listar/crear/editar/desactivar) | `docs/02 §3.1.2` · `GA-REM-002 AC13–16` | Admin | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT (generación 09-05: patrón «denegación = tabla vacía» persiste) | `UsersPage` en ambos bundles; R-122 (columna Empresa) vigente |
| CAP-ADM-09 | **Roles y permisos (pantalla)** | `docs/02 §3.1.3` · `GA-REM-034` | Admin | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED | **ABSENT** (el bundle servido no contiene la ruta `/roles`) | `/roles` 1 ref (sólo el GET de UsersPage) vs 7 en local; sin `path:/roles` en el router desplegado; **y en local la página no tiene enlace de navegación (sólo URL)** |
| CAP-ADM-10 | Asignación de rol en formulario de usuario | `OD-13`/`OD-15` | Admin | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | formulario con selector de compañía/rol en ambos bundles |

### Unidades productivas (entradas y superficies)

| ID | Capacidad | Fuente | Actor | primary | backend | frontend repo | runtime | Evidencia |
|---|---|---|---|---|---|---|---|---|
| CAP-BU-01 | Entradas productivas de las 4 unidades (hub + etapas) | `OD-16.a` · `docs/02 §3.4` | operativos | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT (`/poultry` ×30 en ambos bundles) | clasificación funcional pendiente de cuenta |
| CAP-BU-02 | **Importación de abuelas — plan tipado (Progenitoras)** | `GA-REM-042` · `R-152` · `BR-22` | Supervisor | **DEPLOYMENT_STALE** | IMPLEMENTED (valida BR-22) | IMPLEMENTED (form + detalle + adjuntos + i18n) | **ABSENT/DIVERGENT** (`import_plan` 0) — **la UI antigua produce 400 BR-22** | bundle: `import_plan` 0→1; validador exige plan (`validators.validate_import_plan`) |
| CAP-BU-03 | Catálogo de incubadora (mortalidad/descarte en etapa) | `GA-REM-021-D` · `R-171` | operativos | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED (catálogo + i18n) | **ABSENT** (`chicks_healthy` 0→1 en la sección nueva) | commit `64dff76` (09-10) |
| CAP-BU-04 | **Creación automática del lote de abuelas** | `docs/02 §3.4.2` · `R-153` | sistema/producto | **OWNER_DECISION_REQUIRED** | MISSING (decisión pendiente) | MISSING | ABSENT | `AOD-25` vigente (qué es «completar», código, si puebla) |

### Operativo (procesos)

| ID | Capacidad | Fuente | Actor | primary | backend | frontend repo | runtime | Evidencia |
|---|---|---|---|---|---|---|---|---|
| CAP-OPS-01 | Recepción de aves (P-01, flujo general) | `spec.md §4.4` · `PROCESS-01` | Operador/Supervisor | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT (generación 09-05) | `/operations` en ambos bundles |
| CAP-OPS-02 | **Recepción de reproductoras — cuadre B01 y pesos B02** | `GA-REM-021-B` · `GA-REM-037-B` · `BR-20` | Supervisor | **DEPLOYMENT_STALE** | IMPLEMENTED (exige recibidas/mortalidad/rechazo) | IMPLEMENTED (form + evaluación) | **ABSENT** — **la UI antigua produce 400 BR-20** | `dead_on_arrival` 0→1 en bundles; validador obligatorio para `breeder` |
| CAP-OPS-03 | Control diario de producción (P-02: mortalidad, alimento, peso) | `PROCESS-02` · `GA-REM-005` | Operador | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | rutas en ambos bundles |
| CAP-OPS-04 | **Nacimiento en incubadora — sanos/débiles (B13) y conteo (R-170)** | `GA-REM-005-C` · `GA-REM-021-C` · `BR-21` | Encargado incubadora | **DEPLOYMENT_STALE** | IMPLEMENTED (exige sanos/débiles; prohíbe fila «total») | IMPLEMENTED | **ABSENT** — **la UI antigua produce 400 BR-21** | `chicks_healthy` 0→1; validador obligatorio vs fila total duplicada |
| CAP-OPS-05 | **Consumo de agua (B05)** | `GA-REM-021-A` · `R-13` · `RR-10/11` | Operador (Reproductoras/Engorde) | **DEPLOYMENT_STALE** | IMPLEMENTED (`water_consumption`) | IMPLEMENTED (catálogo + campo + reporte) | **PARCIAL** (reporte agregaba `water_liters`; captura ausente) | `water_liters` 1→2 en bundles; `72600f1` (09-09) con frontend |
| CAP-OPS-06 | **Despacho — una sola fila fértil / cantidad > 0 (R-172/R-174)** | `GA-REM-005-E/F` · `BR-02/BR-04` | Operador incubadora | **DEPLOYMENT_STALE** | IMPLEMENTED (solo fértil; 0 rechazado) | IMPLEMENTED (fila única) | **ABSENT/DIVERGENT** (la UI antigua permite tipos/cantidades hoy rechazadas) | `64dff76`; validador `cuenta_como_disponible` |
| CAP-OPS-07 | Ciclo Revisión→Corrección→Aprobación (P-07) | `docs/12` · `PROCESS-03` · `OD-17`/`OD-19` | Supervisor/Aprobador | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT (generación 09-05) | `/review` `/approvals` en ambos bundles; R-181 como secundario (envío explícito) |
| CAP-OPS-08 | **Envío/reenvío explícito a revisión (`submit`)** | `docs/12 §2/§4` · `OD-17.b` · `R-135` (backend) | Operador/Supervisor | **FRONTEND_MISSING** | IMPLEMENTED (desplegado) | **MISSING** (servicio sin llamadores; sin control UI) | ABSENT | `operationsService.submit` sin call sites en todo el historial; E2E invoca la API; **R-181 (nuevo)** |
| CAP-OPS-09 | **Pantalla de reverso (solicitar/consultar)** | `GA-REM-041` · `OD-19` · R-136 evidencia («frontend … fase 9») | Supervisor/Contraloría | **FRONTEND_MISSING** | IMPLEMENTED (desplegado; 401) | **MISSING** (0 referencias `reversal`) | ABSENT | 0 refs frontend; reverso aprobado por el plano de revisión |
| CAP-OPS-10 | Lotes (P-06: listar/crear/detalle/cerrar) | `PROCESS-06` · `GA-REM-029/036` | Admin/Supervisor | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | `/lots*` en ambos bundles |
| CAP-OPS-11 | Evidencias (subir/descargar) | `GA-REM-009` · `PROCESS-07` | operativos | BLOCKED_AUTH | IMPLEMENTED (volumen `R-52` pendiente) | IMPLEMENTED | PRESENT | ambos bundles; R-52 vigente (volumen no montado) |
| CAP-OPS-12 | Dashboard / KPI | `PROCESS-15` · `GA-REM-022` | todos | BLOCKED_AUTH | IMPLEMENTED | IMPLEMENTED | PRESENT | `/` `/kpi` en ambos bundles |
| CAP-OPS-13 | SAP — gestión de referencias/envíos | `docs/10` · `OD-12` · `P-08` parcial | Analista SAP | BLOCKED_AUTH | PARTIAL | IMPLEMENTED | PRESENT | `/sap` en ambos bundles |

### Maestros, auditoría, notificaciones

| ID | Capacidad | Fuente | Actor | primary | backend | frontend repo | runtime | Evidencia |
|---|---|---|---|---|---|---|---|---|
| CAP-MAS-01 | **Gestión completa de maestros (19 + áreas)** | `GA-REM-033` · `R-90/91` | Admin | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED (20 entidades con alta/edición) | **PARCIAL/DIVERGENT** (`/masters` 30 refs vs 39) | `0a44706` (09-06); bundle desplegado sin los 7 nuevos ni áreas |
| CAP-MAS-02 | **Áreas (maestro administrable)** | `GA-REM-039` · `OD-08` | Admin | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED | **ABSENT** | `950bb21` (09-07) |
| CAP-MAS-03 | **Curvas de peso (carga de tabla + evaluación)** | `GA-REM-037` · `OD-06` · `R-96/97` | Admin | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED (`WeightCurvesPage`) | **ABSENT** (`/weight-curves` 0→6) | `99e874f` (09-06) |
| CAP-AUD-01 | **Auditoría — filtros reales y cobertura** | `GA-REM-032` · `R-81/82/84` | Auditor | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED | **ABSENT/DIVERGENT** (generación 09-05 con pestañas que no filtraban) | `4386f87` (09-06) — el mismo commit que rompió el build |
| CAP-NOT-01 | **Notificaciones internas (campana/bandeja)** | `GA-REM-038` · `OD-07` | todos | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED | **ABSENT** (`/notifications` 0→3) | `a2e21da`/`846b1bf` (09-07) |
| CAP-ERR-01 | **Estados de error distinguibles (denegación ≠ vacío)** | `R-120` · `H360-F02` | todos | **DEPLOYMENT_STALE** | IMPLEMENTED | IMPLEMENTED (p. ej. `/users` con 5 estados) | **ABSENT** (persiste el `Promise.all` + `catch{}`) | `e75f168` (09-08); bundle desplegado muestra el patrón antiguo |

## Anexo — backend interno (NO user-visible, fuera del conteo)

| Capacidad | Fuente | Estado backend | Nota |
|---|---|---|---|
| Enforcement RBAC en cada ruta | `GA-REM-002` | IMPLEMENTED (guardas de arranque) | autoridad del backend; no requiere UI |
| Aislamiento por inquilino/unidad en escritura | `R-139/160/162/163/165/179/180` | IMPLEMENTED | probado por API |
| Balance de población/huevos bajo bloqueo | `R-130/161/172/173` | IMPLEMENTED | probado por API |
| Trazabilidad generacional / linaje efectivo | `GA-REM-008/031` · `R-178` | IMPLEMENTED | árbol en UI (bloqueado auth) |
| Auditoría inmutable (aplicación) | `GA-REM-032` · `R-148` abierto (BD) | PARTIAL | deuda registrada |
| Reverso interno (servicio) | `GA-REM-041` | IMPLEMENTED | UI → fase 9 |
| Adaptador SAP (semántica, consolidación) | `GA-REM-010` · `P-08` | PARTIAL / `SAP_DEFERRED` | `BLOCKED_EXTERNAL` |

## Universo y conteo

```
Capacidades user-visible inventariadas ......... 38
  con estado primario de producto .............. 23
    IMPLEMENTED_AND_VISIBLE ..................... 0
    IMPLEMENTED_BUT_NOT_EXPOSED ................. 1   (CAP-SES-05)
    FRONTEND_MISSING ............................ 7   (CAP-ADM-03…07 · CAP-OPS-08/09)
    DEPLOYMENT_STALE ............................ 13  (CAP-ADM-09 · CAP-BU-02/03 · CAP-OPS-02/04/05/06 · CAP-MAS-01/02/03 · CAP-AUD-01 · CAP-NOT-01 · CAP-ERR-01)
    BROKEN_FLOW (primary) ....................... 0   (3 rupturas de contrato son SECUNDARIAS de filas DEPLOYMENT_STALE)
    OWNER_DECISION_REQUIRED ..................... 2   (CAP-ADM-02 → R-124 · CAP-BU-04 → R-153/AOD-25)
  bloqueadas por credenciales (sin estado) ...... 15  (fase 7 del plan — AUTHENTICATED_RUNTIME_BLOCKER)
Capacidades internas (anexo, no contadas) ....... 7
```

Invariante: `23 = 0 + 1 + 7 + 13 + 2` ✓. Las 15 bloqueadas no reciben estado inventado; quedan pendientes de la entrega de cuentas por el propietario (§38 del encargo). Fuente única del conteo: `generate_gap_matrix.py` (reproducible).

## Addendum GA-FE-02-B (2026-09-11)

`CAP-SES-05` — selector de empresa: fix mínimo entregado y **verificado en runtime autenticado**
(GA-FE-02-B F4, commit `716d175`; bundle `index-B2-tZnkI.js`). Estado primario revisado:
**IMPLEMENTED_AND_VISIBLE** (conteo revisado: IMPLEMENTED_AND_VISIBLE 1 ·
IMPLEMENTED_BUT_NOT_EXPOSED 0; los CSV/conteos generados se regeneran en la próxima pasada del
script con este addendum). Detalle y evidencia:
`audit/ga-fe-02-b/GA_FE_02_B_F4_SELECTOR_EVIDENCE.md` y
`audit/frontend-runtime/GA_FE_02_B_CAP_SES_05_ADDENDUM.md`. `R-98`/`R-119` sin cambio.

## Addendum GA-FE-02-C (2026-09-11)

La **corrida autenticada completa** (E2E-01…10 + matriz 3D, desktop y móvil) quedó **verde**
sobre `index-B2-tZnkI.js` — evidencia en
`audit/ga-fe-02-a/GA_FE_02_A_AUTHENTICATED_RUNTIME_CERTIFICATION_EVIDENCE.md` (adenda §41–46).
Las capacidades user-visible de GA-FE-02 (administración de unidades de empresa y de
concesiones de usuario, contexto de empresa, selector) pasan a **`IMPLEMENTED_AND_VISIBLE`**
**con evidencia runtime autenticada** — sin R-ID nuevo y sin tocar la clasificación de
capacidades ajenas a GA-FE-02. Conteo revisado del estado primario:

```
IMPLEMENTED_AND_VISIBLE ........ 1 → 5  (CAP-SES-05 + las 4 superficies GA-FE-02 certificadas:
                                        contexto de empresa · 4 unidades de empresa ·
                                        concesiones de usuario · selector global)
```

Las capacidades de GA-FE-03 **no** se reclasifican (siguen como están); la instantánea
original del catálogo **no se reescribe**. Incidencias documentadas de la corrida
(**D-1** lectura productiva del actor global con unidades OFF — reclasificada por GA-FE-02-D
como `SECURITY_DEFECT` y **corregida** en `9ffc5ec` con verificación runtime OFF→cero/404 y
ON→habilitadas · D-2 tarjeta hub R-119 · D-3 filtro `module` de `/audit` con valores fuera
del enum → 500 · D-4 fail-closed del home sin `dashboard:read`): registradas en la evidencia;
**R-98/R-119 permanecen UNCHANGED** y ninguna bloquea GA-FE-02.
