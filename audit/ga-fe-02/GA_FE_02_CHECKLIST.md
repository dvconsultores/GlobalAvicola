# GA-FE-02 · CHECKLIST PRE-IMPLEMENTACIÓN

`[x]` hecho · `[ ]` pendiente · marcado al ejecutar. **Ningún código de producto antes de
completar esta lista** (§70).

## Gobernanza

- [x] Owner Decision registrada (`OD-20`, registro canónico `specs/remediation/`)
- [x] Owner Decision `APPROVED` (fuente: autorización explícita del propietario, 2026-09-11)
- [x] Baseline verificado (`main` · `cb14523` · remoto==local · limpio)
- [x] `R-158` permanece cerrado (tsc exit 0 · build exit 0)
- [x] `R-99` permanece cerrado (runtime sirviendo `index-kzREeQp6.js`)
- [x] Runtime entry fingerprint capturado (`GA_FE_02_RUNTIME_ENTRY_FINGERPRINT.md`)

## Contratos

- [x] Rutas backend mapeadas (B01–B10 con method/path/permiso/errores)
- [x] Permisos mapeados (`business_units:read|update|create|delete`; rol de Accesos exacto)
- [x] Matriz de actores mapeada (`GA_FE_02_ACTOR_CAPABILITY_MATRIX.md`)
- [x] Contexto de empresa mapeado (`/me` campos, `switch-company`, re-validación por petición)
- [x] Endpoints de Company BU mapeados (list/enable/disable · 403 sin empresa · 404)
- [x] Endpoints de User BU mapeados (grants/candidates/grant/revoke · 404/409/403)
- [x] Regla de auto-concesión mapeada (403 servidor; actor excluido de candidatos)
- [x] Regla de candidatos mapeada (misma empresa, activos, sin actor, sin oráculo)
- [x] Regla zero-BU mapeada (`effective_business_units=[]`; UI muestra estado real)
- [x] `OD-16` mapeado (cuatro unidades; encender≠conceder; apagar prevalece; control plane
      administra OFF)
- [x] `OD-14` mapeado (clases de superficie; fail-closed sin contexto)
- [x] `OD-15` mapeado (segregación; sin excepción de arranque; rol de 4 permisos)
- [x] `BU-D10` preservado sin resolver (comportamiento provisional tal cual; copy neutral)
- [x] Ciclo de vida de transferencia de empresa leído (sin UI que lo viole; sin dropdown nuevo)

## Frontend

- [x] Inventario de frontend existente (`GA_FE_02_EXISTING_FRONTEND_MAP.md`)
- [x] Rutas seleccionadas: `/admin/unit-access` (nueva) + acción en `/users` (preexistente)
- [x] Estrategia de navegación definida: 1 entrada en sección Admin gated por
      `business_units:read`, guard de ruta propio, SIN navegación global (GA-FE-03)
- [x] Patrón i18n identificado (ES/EN paridad; `company.*` reusables; `businessUnits.*` nuevos)
- [x] Layout móvil planificado (tarjetas apiladas; acciones alcanzables; modal scrollable)
- [x] RED diseñado (`GA_FE_02_TEST_MATRIX.md`; fixtures de contratos REALES)
- [x] Requisito de cuentas autenticadas documentado (`§122`: A/B/C/D + global si aplica)
- [x] Plan de runtime E2E (`E2E-01…E2E-10` contra `avicola.globaldv.net`)
- [x] Plan de rollback/limpieza de datos: restaurar estado de unidad de prueba y concesiones
      creadas (`GA_FE_02_E2E_*`) al estado previo; sin tocar datos ajenos; sin reset global
- [x] Sin alcance GA-FE-03 · [x] Sin `R-181` · [x] Sin `R-182` · [x] Sin Wave B · [x] Sin
      cambios de infraestructura de despliegue

## Commit 1 (esta fase)

- [x] `git add` selectivo + verificar que NO contiene producto (solo `specs/remediation/OD-20…`, `INDEX.md`, `audit/ga-fe-02/`)
- [x] COMMIT 1 registrado y worktree limpio — `466f9d3` publicado

## Ejecución (addendum de la tranche)

- [x] RED construido y ROJO antes de implementar — 58 rojos / 3 verdes-preexistentes (razón por prueba)
- [x] Implementación completa (20 archivos; RED→GREEN trazado) — cazado y corregido un bucle de refetch en el propio ciclo
- [x] Targeted: 7 archivos · **90/90** verdes
- [x] `tsc -b --noEmit` → **0 errores** · `npm run build` → exit 0 · Vitest completo → **198/198**
- [x] Sin relajaciones (diff tsconfig/package/Dockerfile/.github = 0) · backend sin cambios (0 líneas)
- [x] COMMIT 2 `48ffdbb` creado tras gates verdes · worktree limpio
- [x] Push normal `466f9d3..48ffdbb` · remoto == implementación · origen intacto
- [x] Cuentas de prueba: NO recibidas → `AUTHENTICATED E2E: BLOCKED_AUTH` + `GA_FE_02_REQUIRED_TEST_ACCOUNTS.md`
- [x] Sensibilidad: N/A documentado (harness no disponible de forma segura; compensación: sensibilidad empírica RED→GREEN + guards backend certificados + negativos E2E pendientes)
- [ ] Observación de despliegue y marcadores GA-FE-02 → pendiente la ventana de CI+Watchtower
- [ ] Evidencia + addenda + COMMIT 3
