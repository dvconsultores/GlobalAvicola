# GA-FE-02 · EVIDENCIA MAESTRA — ADMINISTRACIÓN MULTI-EMPRESA Y DE UNIDADES

**Baseline**: `cb14523` → **implementación**: `48ffdbb` · **Tranche**: GA-FE-02 · **OD**: `OD-20`
· **Fecha**: 2026-09-11 · **Entorno**: `avicola.globaldv.net` (ENV-01).

> Las secciones 19–24 (despliegue, egreso, marcadores, E2E, UAT) se completan al ejecutarse;
> `⏳` = pendiente en la redacción inicial.

---

## 1 · Baseline y gobernanza

- Preflight completo: `main` · `HEAD cb14523` == remoto · worktree limpio · origin HTTPS.
- GA-FE-01 verde re-verificado: tsc **0** · build **PASS** · Vitest **108/108**.
- Registro canónico leído (`specs/remediation/`): último `OD` = `OD-19` → **`NEXT_FREE = OD-20`**.
- `OD-20` formalizada **APPROVED** (autorización explícita del propietario, 2026-09-11) +
  alta en `INDEX.md` + `GA-REM-040` fase 9: `FROZEN → AUTHORIZED`.
- COMMIT 1 `466f9d3` (gobernanza/spec, sin producto) — publicado.

## 2 · Alcance y no-alcance

Alcance exacto: autorización de fase 9 para GA-FE-02 (`OD-20 §2`). No-alcance explícito
(`OD-20 §5`): GA-FE-03 · R-98/R-119 completos · navegación dinámica global · R-181 · R-182 ·
Wave B/C · SAP · BU-D10 · infraestructura de despliegue. **Verificado**: cero código de esos
ámbitos en el diff (`git diff --name-only` contra lista de exclusión → 0).

## 3 · Contrato backend (trazado, no asumido)

`GA_FE_02_BACKEND_CONTRACT_MATRIX.md` (B01–B11) — verificado contra código en `cb14523`:
`/masters/companies`, `/switch-company`, `/me` (SessionRead), `/business-units`,
`…/{code}/enable|disable`, `/users/{id}/business-units`, `…/{code}/grant-candidates` (POST/DELETE).
**MISSING deliberado** documentado (catálogo standalone, filtro por company, effective por
usuario arbitrario). **Backend READY — sin cambios** (diff backend = **0 líneas**).

## 4 · Estado de frontend previo

`GA_FE_02_EXISTING_FRONTEND_MAP.md` — REUSABLE (company.store, Header, ui, toast, i18n) ·
PARTIAL (auth.store, nav, UsersPage, App) · DEAD (`ProtectedRoute.roles`, `src/hooks/*`) ·
MISSING (páginas, helper de permisos, claves BU).

## 5 · Autoridad de actores

`GA_FE_02_ACTOR_CAPABILITY_MATRIX.md` — por PERMISO: Admin. de Accesos (4 permisos exactos,
sin `users:read`), Super Admin (comodín, switch), Contraloría (sin administración automática),
actor global sin contexto (fail-closed), zero-BU.

## 6 · Contexto de empresa (implementación)

Sesión extendida desde `/me` (`effective_company_id`, `permissions`, `company_business_units`,
`granted_business_units`, `effective_business_units`). Nombre de la empresa efectiva: directo si
persistida; resuelto por catálogo si desplazada (OD-11). Indicador en Header (existente, ahora
alimentado con la efectiva). Sin empresa: fail-closed en la página (sin peticiones).

## 7 · Cambio de empresa

Reutiliza `POST /switch-company` (super admin) vía `company.store.switchCompany` (existente):
POST → `setTokens` (ambos) → `fetchMe` → tienda de empresa actualizada. Las superficies GA-FE-02
refetchean por `effective_company_id` y **limpian la selección** (sin datos obsoletos). Formato
de contexto verificado en test (R-sw-1).

## 8 · Administración de unidades de la empresa

Página `/admin/unit-access` (nueva): las **cuatro** unidades con estado del backend
(`GET /business-units`), pill de estado con TEXTO (no solo color), acción habilitar/deshabilitar
gated por `business_units:update` con `ConfirmDialog` (danger + warning al apagar) y mensajes
íntegros; **refetch tras éxito Y tras fallo** (reconciliación; sin falso éxito). Habilidad:
"Habilitar NO concede" (test R-cbu-3: cero llamadas de concesión).

## 9 · Concesiones de usuario

Sección por unidad en la misma página (flujo por candidatos, apto para el Administrador de
Accesos **sin** `users:read`): selector de unidad → `grant-candidates` (solo si habilitada;
OFF muestra aviso y no provoca el 409) → conceder (`POST`) / revocar (`DELETE` con confirmación)
gated por `business_units:create|delete`; self excluido (UI) — servidor 403 (ya certificado).
Panel por usuario en `/users`: acción por fila (`business_units:read`), modal con EMPRESA vs
USUARIO separados, históricas (`revoked_at`) marcadas, `is_effective` como badge aparte,
conceder/revocar con los mismos gates; sobre uno mismo: sin concesión + nota. **Conceder/revocar
no tocan RBAC ni habilitación** (assert de llamadas: solo los endpoints exactos).

## 10 · Navegación y descubribilidad

`navigationConfig`: entrada `nav.unitAccess` → `/admin/unit-access` con `permission:
'business_units:read'`; filtro `filterNavItemsByPermissions` aplicado en Sidebar y MobileDrawer
SOLO a entradas con `permission` (el resto del menú intacto — frontera R-98/GA-FE-03 verificada
por test). Ruta directa protegida por `PermissionRoute` (guard por permiso; mensaje
`admin.forbidden`, sin pantalla en blanco). **Sin** navegación productiva dinámica.

## 11 · RED y pruebas

`GA_FE_02_TEST_MATRIX.md`. RED inicial: **58 rojos / 3 verdes (de 61)** — los 3 verdes eran
comportamiento preexistente codificado (fetchMe spread, switchCompany, empresa persistida);
documentado en `GA_FE-02 C2`. RED válido = superficie ausente (módulos/página/claves
inexistentes), razón registrada por prueba.

Targeted GREEN (7 archivos · 90 pruebas): permisos 7/7 · nav 6/6 · i18n 44/44 · servicio 7/7 ·
sesión 5/5… (detalle en §107-style abajo) · página admin 15/15 · panel usuarios 6/6.

Cazado por el RED un defecto real de la implementación inicial: effect con dependencia inestable
(`loadUnits`) → bucle de refetch; corregido con dependencia única `[effectiveCompanyId]`
(crash de worker reproducido y eliminado).

## 12 · Gates de construcción

```
tsc -b --noEmit .......... exit 0 (0 errores; sin baseline allowance)
vite/npm run build ....... exit 0 (comando exacto del Dockerfile)
Vitest completo .......... 19 archivos · 198/198 (108 baseline + 90 nuevos) · 0 skipped nuevos
Sin relajaciones ......... diff de tsconfig/package/Dockerfile/.github = 0 líneas
Backend controls ......... NO EJECUTADOS LOCALMENTE — guard deliberado de entorno de test
                           (GA_TEST_ENV=1 + DATABASE_URL aislada requeridos; no hay PG local);
                           backend SIN CAMBIOS (diff 0) y guards OD-14/15/16 certificados en
                           WAVE B (tests citados en la matriz). Se compensará con control
                           negativo autenticado en el piso E2E cuando haya cuentas.
```

## 13 · Fingerprint LOCAL

```
LOCAL_BUILD_JS   assets/index-C_aR7TJ6.js   sha256 35ea38e2c3f41e783a7dc401962f61da0ae4010c34fd5da4dc1be3f9faa41bd8
LOCAL_BUILD_CSS  assets/index-NE-4BlmS.css
LOCAL_INDEX      sha256 b71a38cef5a17575bfbab20f24c164bacfc056b5c1ad846f8845d25f665c61ea
Marcadores locales: unit-access ×2 · business-units ×7 · grant-candidates ×1 · admin.forbidden ×1
(i18n vive en /locales/*.json servidos — no en el bundle; los name_key del backend llegan por API)
```

## 14 · Checkpoint de implementación

`COMMIT 2 = 48ffdbb` (20 archivos, +1700/−6) — solo gate tras gates verdes; worktree limpio.

## 15 · Push

`466f9d3..48ffdbb` exit 0 · remoto == `48ffdbb` (`48ffdbb629a3275d24055594ecb2fbf0141e6a58`)
· origen intacto · sin force. Push = evento de despliegue (EX-01 automático).

## 16 · Observación de despliegue

```
T+0     23:38:14Z  push C2 aceptado (466f9d3..48ffdbb) — dispara docker-push-frontend.yml
                   (trigger `frontend/**` verificado en el workflow, .github/workflows/docker-push-frontend.yml:8-13)
T+1m    23:38:23Z  raíz aún GA-FE-01 (index-kzREeQp6.js · LM 21:42:54Z)
T+2m    23:39:20Z  idem
T+~53s  23:39:07Z  (LM nuevo) CAMBIO DETECTADO a las 23:40:25Z de observación:
                   index-C_aR7TJ6.js · Last-Modified 23:39:07 GMT · ETag "6aa33f9b-322" · CSS index-NE-4BlmS.css
CLASIFICACIÓN       RUNTIME_UPDATED
ACCIONES MANUALES   0 (sin docker pull, sin reinicios, sin tocar Watchtower/Nginx/CI/EX-01)
```

## 17 · Fingerprint de EGESO y marcadores

`GA_FE_02_RUNTIME_EXIT_FINGERPRINT.md`. Resumen:

| Señal | ENTRY | EXIT |
|---|---|---|
| Main JS | `index-kzREeQp6.js` | **`index-C_aR7TJ6.js`** |
| `Last-Modified` | 2026-09-10 21:42:54 GMT | **2026-09-10 23:39:07 GMT** |
| ETag | `"6aa3245e-322"` | `"6aa33f9b-322"` |
| Paridad con el build de `48ffdbb` | — | **byte a byte (HTML/JS/CSS)** |
| Asset anterior | primario | **404** |
| Marcadores | 0 | **unit-access ×2 · business-units ×7 · grant-candidates ×1 · admin.forbidden ×1 · users.businessUnits ×7** |

## 18 · Smoke público

`/` 200 · `/login` 200 · JS 200 · CSS 200 · `/api/v1/business-units` **401 (vivo y protegido)**
· `/api/v1/lots` 401. **Cliente fresco**: login renderiza sin error fatal (S-01); la ruta directa
`/admin/unit-access` sin sesión **redirige a `/login`** (guard de autenticación activo).

## 19 · E2E autenticado (E2E-01…E2E-10)

**`BLOCKED_AUTH`** — no se recibieron credenciales autorizadas en esta tranche
(`GA_FE_02_REQUIRED_TEST_ACCOUNTS.md` con los actores y sus permisos). No se buscaron, no se
usaron sembradas, no se adivinaron (§122). Consecuencia de clasificación: §144 →
`DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH` (no
`FUNCTIONALLY_CERTIFIED`).

## 20 · Persistencia / relogin / negativos

PENDIENTE por `BLOCKED_AUTH` (mismos actores). Los controles de UI equivalentes (visibilidad y
gating por permiso, self sin concesión, unidad OFF sin candidatos, reconciliación) están
cubiertos por la suite dirigida (90/90) — no sustituyen el control negativo de servidor, que ya
está certificado en backend (`test_access_administration.py::test_s01/s03/s04`).

## 21 · Responsive

Planificado y verificado a nivel de layout en la suite (apilado sin overflow estructural);
la verificación **visual en 390×844** queda en el piso E2E autenticado (pendiente).

## 22 · Auditoría (mutaciones)

Backend ya audita (`CONFIG_CHANGE` config · `PERMISSION_CHANGE` users · `CONTEXT_SWITCHED`);
la verificación de entradas reales por actor requiere la sesión autenticada (pendiente).

## 23 · Hallazgos

```
R-158 · R-99            permanecen CERRADOS (regresión §112 verificada abajo)
R-98 / R-119            SIN CAMBIO (la navegación global no se tocó; frontera probada por test)
R-181 / R-182           SIN CAMBIO (cero código en esos ámbitos)
BU-D10                  PENDING_RATIFICATION — ninguna semántica nueva en la UI; el copy se
                        limita a «Revocada (histórica)» descriptivo de `revoked_at`
Nuevos                  NINGUNO en esta tranche (el defecto del bucle de refetch fue cazado y
                        corregido ANTES del COMMIT 2 — no llega al producto)
```

## 24 · Regresión de tranches previas

```
R-158: tsc 0 y build verde en los tres puntos de control (preflight, pre-commit, post-fix)
R-99:  push normal desplegado (sección 16); paridad BYTE A BYTE con el build de `48ffdbb`
       (HTML/JS/CSS) y marcadores GA-FE-02 presentes (sección 17)
```

## 25 · UAT del propietario

`GA_FE_02_OWNER_UAT.md` entregado. **`OWNER_ACCEPTANCE: PENDING`** — no se auto-declara (§165).

## 26 · Estado final GA-FE-02

```
BACKEND CONTRACT        READY (sin cambios)
FRONTEND IMPLEMENTATION COMPLETE (gates verdes; RED→GREEN trazado)
DEPLOYMENT              CURRENT (byte a byte con el build local; marcadores presentes)
AUTHENTICATED E2E       BLOCKED_AUTH
OWNER UAT               PENDING
GA-FE-02                DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH
MULTI-COMPANY ADMIN     FUNCTIONAL (implementación) — certificación funcional pendiente de cuentas
```

## 27 · Git final

```
C1 466f9d3 (gobernanza) → C2 48ffdbb (implementación) → C3 (esta evidencia) — todos publicados
worktree limpio · origin HTTPS · sin force-push
SENSIBILIDAD  N/A — ver decisión en §28
```

## 28 · Sensibilidad (§117)

Decisión: **N/A documentado con causa**. La mutación destructiva del harness no está disponible
para frontend de forma segura en esta estación; se activan en su lugar: (a) mutaciones de
comportamiento cubiertas por la propia suite (RED original demuestra sensibilidad de las pruebas
a la ausencia de superficie; las suites fallan si se quitan guard/gating — verificado
empíricamente durante el ciclo RED→GREEN), (b) controles negativos de servidor certificados en
backend, (c) control negativo autenticado pendiente en el piso E2E. No se mutó backend. El
mutation checkpoint guard permanece instalado y sin uso.
