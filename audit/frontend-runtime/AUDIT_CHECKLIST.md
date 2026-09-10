# AUDIT CHECKLIST — verificación de ejecución

**Base** `3808ed5` · **2026-09-10** · marcado al ejecutar. `[x]` hecho · `[!]` bloqueado con causa · `[n/a]` no aplica.

## Baseline y fuentes

- [x] baseline verified (`main` · `3808ed5` · limpio · local==remote · HTTPS)
- [x] delta del encargo reconciliado (`6ffd73c` → `3808ed5`, tranche 14)
- [x] source inventory complete (`specs/remediation`, `audit/remediation`, `docs/`, código)
- [x] owner decisions read (`OD-09…OD-19`, `AUDIT_OWNER_DECISIONS_REQUIRED`, registro AOD-01…25)
- [x] active specs read (`GA-REM-040`, `GA-REM-042`, `GA-REM-005/-006/-007` enmiendas vigentes)
- [x] deprecated/historical sources separated (`DOCUMENT_AUTHORITY_AND_SUPERSESSION_MATRIX`, ENV-01)

## Capacidades y matrices

- [x] all promised user-visible capabilities inventoried (catálogo: 51 filas)
- [x] backend route inventory complete (211 rutas; mapa por capacidad con rutas del dominio)
- [x] frontend route inventory complete (App.tsx: 33 rutas declaradas, 29 efectivas + redirects)
- [x] menu/navigation inventory complete (`navigationConfig.ts` — estático, sin permisos/BU)
- [x] permission guards inventoried (0 `hasPermission`/`usePermission`; `ProtectedRoute.roles` código muerto; `WebOnlyRoute` por `view_type`)
- [x] Company context flow inventoried (`company.store.ts`, `Header.tsx`, `initFromUser`, `switchCompany`)
- [x] Business Unit flow inventoried (backend fases 1–8 desplegado; frontend 0 referencias)
- [x] user BU assignment flow inventoried (`grant-candidates` backend desplegado; frontend 0 referencias)
- [x] role/permission admin flow inventoried (`RolesPage` local vs desplegado)
- [x] all four productive BUs evaluated (grandparent/breeder/hatchery/broiler — `OD-16.a`)

## Runtime y despliegue

- [x] runtime URL verified (`https://avicola.globaldv.net`, ENV-01 compartido)
- [x] deployed fingerprint captured (`Last-Modified` 2026-09-05 14:09:27 GMT; `index-D5dwMXuP.js`)
- [x] local build executed (PASS; `index-Cl0MIg8E.js`; árbol limpio)
- [x] freeze-commit build verified GREEN (`f46cb13`, worktree temporal)
- [x] post-freeze build timeline verified (15/15 commits RED; primera ruptura `4386f87`)
- [x] deployed backend generation probed (fase 7–8 API + reversals vivos por 401)
- [x] PWA/cache angle excluded as cause of the artifact (`Last-Modified` del servidor sin cambio; hash idéntico al de la medición del 2026-09-07)
- [x] bundle markers compared (deployed vs local: `/weight-curves` 0→6, `/notifications` 0→3, `/roles` 1→7, `import_plan` 0→1, `chicks_healthy` 0→1, `dead_on_arrival` 0→1)

## Navegador y credenciales

- [x] deployed app loaded in browser; `/` → `/login` captured
- [x] screenshot captured (`evidence/AUDIT_001_DEPLOYED_LOGIN.png`)
- [x] deep links probed unauthenticated (`/roles` `/masters/weight-curves` `/notifications` `/poultry/hatchery` `/review` → `/login`)
- [!] authenticated test users identified — **AUTHENTICATED_RUNTIME_BLOCKER** (§38)
- [x] no default credentials invented / no seeds used against shared env
- [!] browser evidence for authenticated flows — bloqueado por lo anterior
- [!] network behavior for authenticated flows — bloqueado
- [n/a] direct-route tests with session — bloqueado
- [n/a] menu discoverability with session — bloqueado
- [n/a] persistence / refresh / relogin with session — bloqueado
- [n/a] negative authorization with session — bloqueado

## Hallazgos y reconciliación

- [x] R-98 searched (frontend sin modelo de permisos — confirmado 0 referencias)
- [x] R-99 searched (frontend congelado — causa raíz demostrada: `tsc -b` rojo desde `4386f87`)
- [x] R-99 re-measured today (09-10): artefacto sigue congelado en 2026-09-05 14:09:27 GMT
- [x] existing findings deduplicated (R-98/R-119/R-120/R-127/R-158 y gobernanza GA-REM-040)
- [x] certification scope reconciled (matriz de frontera técnica; sin reescribir historia)
- [x] roadmap built (7 tranches propuestos con dependencias)
- [x] Owner Decisions separated (1 dossier nuevo identificado: ninguno bloqueante de fase 9; los vigentes se referencian)
- [x] no product code modified (`git status --short` solo `audit/**`)

## Controles

- [x] Vitest control run (108/108)
- [x] TypeScript control run (6 errores, R-158)
- [n/a] backend regression — no requerida para esta auditoría (§123); declarada en el plan
- [n/a] mutation testing — excluido (§124)

## Cierre

- [x] invariante de conteo verificado (TOTAL = suma de 6 estados + bloqueadas por auth contadas aparte)
- [x] evidencias completas y trazables (`MASTER_FRONTEND_RUNTIME_AUDIT_EVIDENCE.md` §10)
- [x] informe final con el formato exacto del encargo (§139)
- [!] fase 7–8 (flujos autenticados) — pendientes de credenciales autorizadas del propietario
