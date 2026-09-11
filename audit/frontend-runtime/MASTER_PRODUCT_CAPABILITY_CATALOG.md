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

## Addendum GA-FE-03 (2026-09-11)

Navegación dinámica certificada en runtime autenticado sobre `index-CElqNz3R.js`
(desktop 45/45 · móvil 13/13 · regresión+restauración 29/29). Conteo revisado del estado
primario:

```
IMPLEMENTED_AND_VISIBLE ........ 5 → 6  (CAP-ADM-06 «Navegación adaptada a permisos y
                                         unidades» pasa de FRONTEND_MISSING a
                                         IMPLEMENTED_AND_VISIBLE con evidencia runtime)
```

- `D-2` (tarjeta del hub para D) **CERRADO** (hub sobre árbol filtrado).
- Entrada `Roles` descubrible para `users:read` (CAP-ADM-09 deja de ser «solo URL» en lo
  relativo a descubribilidad; su estado de despliegue lo cubre GA-FE-01 R-99/158).
- **`R-119` → `CLOSED`** (individual, con su evidencia) · **`R-98` → `PARTIAL`** (navegación
  accionable cerrada; residuo de ocultado intra-pantalla pertenece a `P-13`, declarado sin
  cierre por asociación).
- `R-181`/`R-182`/SAP/`BU-D10`: **UNCHANGED**. Detalle:
  `audit/frontend-runtime/GA_FE_03_ADDENDUM_DYNAMIC_NAVIGATION.md` y
  `audit/ga-fe-03/GA_FE_03_CERTIFICATION_RECONCILIATION.md`.

## Addendum GA-FE-04 (2026-09-11) · `index-B66tpdeW.js` (`de40d36`)

- **`R-98` → `CLOSED`**: capa de autoridad de ACCIÓN (`auth/actionAuthority.tsx`) + gates en
  12 superficies (31 acciones de escritura) + paridad de rutas de alta. La interfaz muestra
  solo acciones permitidas; el backend permanece autoridad (403 verificados).
- `CAP-ADM-06` se mantiene IMPLEMENTED_AND_VISIBLE (sin cambio); se añade el nivel de acción
  intra-pantalla como parte del mismo evaluador canónico (sin segundo sistema).
- `R-119` sigue `CLOSED`; `R-181`/`R-182`/SAP/`BU-D10`: **UNCHANGED**. Detalle:
  `audit/frontend-runtime/GA_FE_04_ADDENDUM_INTRA_SCREEN_AUTHORITY.md` y
  `audit/ga-fe-04/GA_FE_04_R98_CLOSURE_RECONCILIATION.md`.

## Addendum GA-FE-05 (2026-09-11) · `index-WUv1-F9o.js` (`005a252`)

- **`R-181` → `CLOSED`**: el envío/reenvío explícito a revisión ya es descubrible por UI
  (`/operations/:id`, state-aware según `OD-17.a/b`), con estado localizado, refresh sin
  optimismo y seguridad de producto verificada (permiso ∧ unidad ∧ estado; API 404/403/400).
- `R-98`/`R-119`: CLOSED (sin regresión; se reutiliza su evaluador). `R-182`: **UNCHANGED / OPEN**.
  `BU-D10`: PENDING_RATIFICATION. Detalle: `GA_FE_05_ADDENDUM_R181_SUBMIT_RESUBMIT.md` y
  `audit/ga-fe-05/GA_FE_05_R181_CLOSURE_RECONCILIATION.md`.
- **Aceptación del propietario (GA-UAT-03, `90ceee4` + registro): `GA-FE-05 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTED` · `R-181 = CLOSED / OWNER_ACCEPTED`** (sin observaciones).

## Addendum GA-FE-06 (2026-09-11) · `index-DcqmSs-R.js` (`23ca59a`)

- **`R-182` → `CLOSED`**: el alta de lote pasa de **perder en silencio** la fecha prevista de
  cierre (y no capturar área) a enviar, persistir, releer y **mostrar** `planned_close_date`
  y `area_id`; el aviso SLA «lote próximo a cierre» recupera su fuente de datos (ventana
  0..3 días intacta, sin cambios backend/migración/permisos). Selector de área acotado a la
  empresa del actor (nombres, sin IDs crudos).
- RED 4 rojos + 1 control → **5/5 verdes**; suite **278/278**; runtime autenticado E2E-01…16
  (desktop/móvil/ES/EN; RBAC y CBU negativos; auditoría verificada).
- **Nuevos candidatos**: `R-183` (API de alta/edición acepta `area_id` de otra empresa — la
  UI filtra), `R-184` (`kpi/ipe` 500 en lote recién creado) + observaciones N-3/N-4.
- `R-98`/`R-119`/`R-181`: CLOSED sin regresión. `BU-D10`: PENDING_RATIFICATION. Wave B:
  PAUSED · Wave C/SAP: NOT STARTED. Detalle: `GA_FE_06_ADDENDUM_LOT_CONTRACT_SLA.md` y
  `audit/ga-fe-06/GA_FE_06_CERTIFICATION.md`.
- **Aceptación del propietario (GA-UAT-04, 2026-09-11): «A) ACEPTO GA-FE-06» ⇒ GA-FE-06 =
  FUNCTIONALLY_CERTIFIED · OWNER_ACCEPTED · OWNER_ACCEPTANCE = PASS · R-182 = CLOSED ·
  OWNER_ACCEPTED.** Observaciones aceptadas (no bloqueantes): descubrimiento de «Lotes»
  sin entrada de menú (candidato UX P2) · área no visible en el detalle · opción de área
  de baja lógica en el selector (P3). Registro: `audit/ga-uat-04/`

## Addendum GA-FE-06-A (2026-09-11) · backend `69d0c95` · bundle `index-DcqmSs-R.js`

- **Seguridad de área entre empresas (subhallazgo N-1/R-183) → CERRADA dentro de R-182**:
  alta y edición de lote validan la pertenencia del área (`verificar_catalogo_de_empresa`;
  `BR-07`; fail-closed). Runtime: ajena **DENY** (400) en alta y edición; inexistente 400
  (antes 500); positiva/NULL ALLOW; sin persistencia/auditoría de éxito/fuga.
- `R-183`: **ABSORBED_IN_R182** (sin entrada independiente). `R-184`: SEPARATE/UNCHANGED.
- **`R-182 = CLOSED` · `GA-FE-06 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING` ·
  `OWNER_UAT_READY = YES`** (Owner UAT no ejecutado). Detalle: `audit/ga-fe-06-a/`.

## Addendum GA-GOV-01 (2026-09-11) · triage post-UAT-04 (solo gobernanza)

- **CAP-OPS-10 (Lotes)**: estado sin cambio (IMPLEMENTED/PRESENT); se anota la mejora de
  descubrimiento **P2, sin R**: `/lots*` sin fuente de menú — estado inventariado y
  decidido en GA-FE-03 §34 («rutas sin fuente de menú»; «sin entradas nuevas salvo
  Roles»; aceptado en GA-UAT-01). No es regresión; no reabre R-119/GA-FE-03.
- **Elegibilidad por estado** (áreas/maestros en baja lógica para referencias nuevas):
  `OWNER_DECISION_REQUIRED` (P3, sin R) — silencio canónico verificado; opciones A/B/C
  con default neutro B en `audit/ga-gov-01/`.
- GA-FE-02..06 y R-98/R-119/R-181/R-182: **preservados** (sin reapertura). R-184:
  SEPARATE_OPEN sin relación con las observaciones.

## Addendum GA-FE-07 (2026-09-11) · `index-BUthrUt9.js` / backend `5a5bb3f`

- **OD-21** (elección del propietario «Option C»): un maestro dado de baja lógica no sirve
  para **referencias nuevas**; la historia se conserva. Implementación Área→Lote (R-185):
  alta/edición DENY con inactiva («Área inactiva», BR-07), **detección de cambio** en edición
  (H1–H5), selector transaccional solo activas, administración de maestros intacta.
- `CAP-OPS-10 (Lotes)`: contrato de alta/edición ampliado (elegibilidad por estado, sin
  migración/permisos/endpoints). **R-185 CLOSED_OWNER_ACCEPTED** (UAT corta GA-UAT-05, 2026-09-11, decisión A).
  OBS-UAT-04 (GA-GOV-01): **RESUELTA**. R-182/R-184/OBS-UAT-01/BU-D10: sin cambio.

## Addendum R-184 (2026-09-11) · `index-BUthrUt9.js` / backend `3f88f94`

- **KPI IPE (G-06)**: `GET /reports/kpi/ipe/{lot}` recuperado de un 500 sistemático
  (date − datetime en `age_days`; corrección con `_dia()` canónico, fórmula intacta).
  **R-184 CLOSED_OWNER_ACCEPTED** (UAT GA-UAT-06, 2026-09-11, decisión A; tarjeta IPE visible en detalle de lote).
- **GA-GOV-02 (2026-09-11)**: **R-186 CLOSED** — tranche homónima (2026-09-11): 500 temporal del
  `production-index` (G-05) resuelto con el helper `_dia()` canónico (C2 `0309225`);
  runtime E2E 14/14; **OWNER UAT NOT REQUIRED** (API-only, sin superficie de usuario).
  Observación de negocio de escala del IPE: **decisión de propietario pendiente**
  (paquete A/B/C en `audit/ga-gov-02/`). Detalle: `audit/ga-r186/`.
- R-181/R-182/R-185/R-184-OBS-UAT-01/BU-D10 sin cambio; Wave B/C/SAP igual.

## Addendum GA-OD-01 (2026-09-11) · OD-22 (escala del IPE G-06)

- **OD-22 RATIFICADA** (Opción A, decisión explícita del propietario): el IPE se alineará a la
  escala estándar/bandas (sin ×100); bandas y textos **sin cambios**; sin migración.
  Registro: `audit/ga-od-01/GA_OD_IPE_SCALE_OWNER_DECISION.md` (línea GA/OD, ≠ Wave B «AOD-22»).
- **R-187 · P2 · OPEN**: brecha de implementación (fórmula actual con ×100 vs regla OD-22).
  Tranche futura (spec → AC → implementación → UAT; cambia el número mostrado). Sin implementar.
- R-184/R-186 cerrados · GA-FE-02..07/OD-21 intactos · OBS-UAT-01 P2 · BU-D10 PENDING ·
  Wave B/C/SAP sin cambio. Detalle: `audit/ga-od-01/`.

## Addendum R-187 (2026-09-11) · OD-22 implementada — IPE a escala estándar

- **OD-22 RATIFIED_IMPLEMENTED** · **R-187 CLOSED · FUNCTIONALLY_CERTIFIED**: retirado el `×100`
  duplicado en G-06 (`ipe = viab% × gain / (fcr×10)`); bandas, labels, umbrales, fechas (R-184),
  FCR y esquema sin cambios; backend-only; sin migración. Frontend product diff: 0.
- Runtime E2E-01…14 PASS: 333.3 (DET, independiente exacto) · 241.1 🔴 · 282.7 🟡 · fronteras
  250.0/300.0/249.9 · lote 11: 556.6→5.6 · UI detalle/reporte/refresh/relogin/móvil OK ·
  seguridad OD-16/RBAC PASS · G-05 5.1 intacto · GA-FE-07 spot 400.
- Owner UAT REQUIRED/READY — acceptance PENDING. Detalle: `audit/ga-r187/`. C1 `5a32a6c` · C2 `f755baa`.

## Addendum GA-UAT-07 (2026-09-11) · R-187 CLOSED_OWNER_ACCEPTED

- **Decisión A) «ACEPTO R-187»** — UAT del propietario 6/6 (333.3 🟢 visible; clasificación
  coherente con bandas intactas; detalle=reporte; refresh/relogin estables; móvil usable).
- **OD-22 = RATIFIED_IMPLEMENTED_OWNER_ACCEPTED** · OWNER_ACCEPTANCE **PASS**.
- Sin cambios de producto · limpieza verificada (BU 4×OFF; actor UAT destruido).
  Detalle: `audit/ga-uat-07/`. C1 `d1f9829` · C2 decisión.
