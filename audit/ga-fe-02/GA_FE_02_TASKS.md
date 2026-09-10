# GA-FE-02 · TASKS (atómicas)

Formato: ID · fuente · AC · archivos · dependencia · prueba · estado. `⏳` pendiente.

## Bloque A — Sesión y permisos (fundamento)

| ID | Tarea | Fuente | AC | Archivos | Dep | Prueba | Estado |
|---|---|---|---|---|---|---|---|
| T01 | Extender `User` de auth.store con sesión de `/me`: `effective_company_id`, `permissions[]`, `company_business_units[]`, `granted_business_units[]`, `effective_business_units[]` (opcionales, tolerantes a sesiones antiguas) y persistirlos en `fetchMe` | B03 | (base) | `stores/auth.store.ts` | — | unit store | ⏳ |
| T02 | Helper mínimo `hasPermission(pereza?)`: comodín `*` o `modulo:accion` presente; exportado como selector de auth.store o helper puro | spec §7 | AC-UI-06 · AC-NAV-03 | `stores/auth.store.ts` (+ selector) | T01 | unit helper | ⏳ |
| T03 | `company.store`: exponer `effectiveCompanyId/Name` derivados y refrescar `initFromUser` desde `/me` (sin romper switch) | B03/B02 | AC-COMP-01 | `stores/company.store.ts` | T01 | unit store | ⏳ |

## Bloque B — API tipada

| ID | Tarea | Fuente | AC | Archivos | Dep | Prueba | Estado |
|---|---|---|---|---|---|---|---|
| T04 | Servicio `businessUnits.service.ts` con tipos del contrato: `getCompanyBusinessUnits`, `enableCompanyBusinessUnit(code)`, `disableCompanyBusinessUnit(code)`, `getUserBusinessUnits(userId)`, `getGrantCandidates(code)`, `grantBusinessUnit(userId, code)`, `revokeBusinessUnit(userId, code)` | B04–B10 | AC-UBU-05/08 | `services/businessUnits.service.ts` (nuevo) | — | contract unit | ⏳ |

## Bloque C — Página `/admin/unit-access`

| ID | Tarea | Fuente | AC | Archivos | Dep | Prueba | Estado |
|---|---|---|---|---|---|---|---|
| T05 | Ruta `/admin/unit-access` + guard por permiso `business_units:read` (o comodín), envoltura `WebOnlyRoute` | spec S5 | AC-NAV-04 | `App.tsx` | T02 | router test | ⏳ |
| T06 | Página: encabezado contexto (empresa efectiva o "sin empresa"); sin empresa → estado fail-closed sin mutaciones | S3a | AC-COMP-01/06 | `pages/admin/UnitAccessPage.tsx` | T04/T05 | component | ⏳ |
| T07 | Cuatro tarjetas de unidad (código→nombre i18n central); estado Habilitada/Inactiva con texto+símbolo; loading/error; refetch | S3b | AC-CBU-02/03/07/15 | ídem | T06 | component | ⏳ |
| T08 | Acción habilitar/deshabilitar con confirmación (ConfirmDialog variante danger al apagar), gated por `business_units:update`; reconciliación ante fallo (refetch; sin falso éxito) | S3b | AC-CBU-04/05/12/13/15 | ídem | T07 | component + API assert | ⏳ |
| T09 | Sección de concesión por unidad: selector de unidad → candidatos (username/display_name/ya-concedido); gated por `business_units:create`; 409 unidad OFF → mensaje claro y sin ofrecer concesión | S3c | AC-UBU-05/07/19 | ídem | T06 | component | ⏳ |
| T10 | Acciones conceder/revocar (gated `business_units:create`/`:delete`); sin cambio de estado local optimista que mienta: refetch tras respuesta | S3c | AC-UBU-05/08/19 | ídem | T09 | component + API assert | ⏳ |
| T11 | Mostrar por usuario el efecto (concedida efectiva/no efectiva) sin fusionar con estado de empresa; auto-concesión no aparece (candidatos la excluyen) | S3c | AC-UBU-03/04/11 | ídem | T09/T10 | component | ⏳ |
| T12 | Responsive de la página (apilado móvil; acciones alcanzables) | AC-UI-02 | AC-UI-02 | ídem | T07–T11 | browser/visual | ⏳ |

## Bloque D — Panel por usuario en `/users`

| ID | Tarea | Fuente | AC | Archivos | Dep | Prueba | Estado |
|---|---|---|---|---|---|---|---|
| T13 | Acción "Unidades de negocio" por fila (visible con `business_units:read`; mutaciones según permisos) | S4 | AC-UBU-01 | `pages/users/UsersPage.tsx` | T04/T02 | component | ⏳ |
| T14 | Modal de concesiones: identidad del usuario + empresa efectiva; lista de las 4 unidades con (estado empresa | estado usuario | efectiva); conceder/revocar; incluye revocadas marcadas (histórico) | S4a | AC-UBU-02/03/04/17 | ídem | T13, T04 | component | ⏳ |

## Bloque E — Navegación e i18n

| ID | Tarea | Fuente | AC | Archivos | Dep | Prueba | Estado |
|---|---|---|---|---|---|---|---|
| T15 | Entrada en `navigationConfig` (sección Admin, `settings`) → `/admin/unit-access`; visibilidad condicionada a `business_units:read` SOLO para esta entrada; sin tocar el resto | S5 | AC-NAV-01/02/03/05 | `data/navigationConfig.ts` + consumidores si requieren prop | T02 | nav unit test | ⏳ |
| T16 | Claves i18n ES/EN de GA-FE-02 (títulos, estados, acciones, errores, vacíos) + mapeo central de nombres de unidad (`name_key` → fallback por código) | §54 | AC-UI-08/09 | `public/locales/es|en/translation.json` + `data/businessUnits.ts` (nuevo) | — | parity test | ⏳ |

## Bloque F — RED y verificación

| ID | Tarea | Fuente | AC | Archivos | Dep | Prueba | Estado |
|---|---|---|---|---|---|---|---|
| T17 | RED: suites nuevas escritas y **rojas** antes de implementar (ver TEST_MATRIX) | §78 | todas | `src/**/__tests__/gaFe02*.test.ts*` | — | vitest (rojo) | ✅ 58 rojos/3 preexistentes |
| T18 | Targeted green + tsc 0 + build + Vitest completo | §107–110 | AC-DEP-01/02/03 | — | T05–T16 | comandos | ✅ 90/90 · tsc 0 · build 0 · 198/198 |
| T19 | Verificación de no-relajación y no-producto-backend (diff acotado) | §118 | AC-NR-04 | — | T18 | git diff | ✅ (0 líneas backend/infra) |
| T20 | COMMIT 2 (implementación) | §116 | — | — | T18/T19 | git | ✅ `48ffdbb` |
| T21 | Push normal + verificación remota + fingerprint de egreso + marcadores | §119–121 | AC-DEP-05…10 | — | T20 | push/curl | push ✅ · egreso ⏳ |
| T22 | E2E autenticado (o paquete BLOCKED_AUTH) + persistencia/relogin + negativos | §125–135 | AC-COMP/CBU/UBU | — | T21 | browser/API | `BLOCKED_AUTH` (cuentas §122 no recibidas; doc de requerimientos emitido) |
| T23 | Evidencia + reconciliación + UAT + COMMIT 3 + informe final | §159/§166/§170 | — | `audit/ga-fe-02/*` | T22 | git | ⏳ |
