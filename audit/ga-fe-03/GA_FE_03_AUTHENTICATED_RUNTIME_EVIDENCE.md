# GA-FE-03 · EVIDENCIA DE CERTIFICACIÓN RUNTIME AUTENTICADA

**Generación certificada**: bundle `index-CElqNz3R.js` (== build local byte a byte por hash) ·
backend `9ffc5ec` · `https://avicola.globaldv.net` · health 200 · **HEAD** `5608465` (C3).
**Sin transitividad**: corrida completa contra la generación final, después del último commit de
producto. **Actores sintéticos** por mecanismos oficiales (usuarios 82–91; `POST /roles` 39/40;
36 reactivado); credenciales efímeras en `/tmp` (600), destruidas al cierre.

```
GA_FE_03_DESKTOP_RUN ........ 45/45 PASS   (Playwright 1440×900, contexto aislado por actor)
GA_FE_03_MOBILE_RUN ......... 13/13 PASS   (Playwright 390×844, isMobile+hasTouch)
GA_FE_03_FIXTURES ........... 25/25 PASS   (altas + logins + /me + estado base)
GA_FE_03_REGRESION+RESTORE .. 29/29 PASS   (D-1 familia · F1/F2/F3 · R-163 · restauración)
CONSOLA ..................... desktop: 1 entrada no fatal (403 esperado en negativas);
                              móvil: 0 · pageerror: 0 · sin claves crudas
RED → GREEN ................. RED 17F/2P (5 archivos, 19 casos) → GREEN 241/241 (26 archivos)
```

## 1 · Escenarios desktop (45/45)

**E · Global** — sin contexto: selector visible, plano de control visible, **cero inquilino**
(producto/review/reports ocultos), deep link `/poultry/broiler` → fail-closed (`E1_*`).
Switch a empresa 1 por UI → todo OFF: producto oculto (`E2`). Habilitación de Engorde **por UI**
en `/admin/unit-access` → `E3`. **Refresh** → barra con Gestión Avícola + Review + Reports
(wildcard + anyBU) (`E4`); hub `/menu/poultry` **solo Engorde** (`E5`); hard refresh conserva
(`E6`). Switch c1→c3 (4 OFF) → producto oculto → vuelta c1 → visible (`E7`). ES→EN→ES con
etiquetas completas (`E8`). Deshabilitación por UI → `E9`.

**A · Company-BU Admin** — `Dashboard + Configuración` y nada más; hub `/menu/settings` con
**Acceso por unidad + Perfil** (sin Usuarios/Roles/Maestros); **descubribilidad completa por UI**
(hub → superficie, sin URL manual); deep link `/users` → denegado (`A_*`).

**C · Productivo** — BU ON sin concesión: sin operativo, deep link denegado, backend 0 filas
(`C1_*`). **B concede por UI** (candidatos: C visible, **actor B excluido** — `B3`; estado
«Concedida» `B4`). C **relogin** → Gestión Avícola visible (`C2`), hub **solo su unidad**
(`C3`), etapa permitida (`C4`), otra unidad denegada (`C5`), backend **solo `L-BO-2026-05/06`**
(`C6`), **refresh** conserva (`C7`). E deshabilita BU por UI (`E9`): C → operativo oculto,
deep link denegado, backend **0 filas con concesión viva** (`C8` — apagar prevalece).

**B · Access Admin** — sin Dashboard (D-4 documentado), solo Configuración (`B1`); hub mínimo
(`B2`); concede/revoca desde su superficie; `/users` denegado (`B5`).

**P · RBAC-negativo** — BU ON + concesión + **sin `operations:read`**: operativo oculto, deep
link denegado (`P1`) — tercera dimensión completa.

**D · Sin autoridad** — `Dashboard + Configuración`; hub settings **solo Perfil** (`D2` — **`D-2`
CERRADO**, sin tarjeta de unidad); **10/10 deep links denegados** (`D3`).

**Z · Cero unidades** — CORE sí, productivo no; **sin grupos vacíos** (secciones OPERATIVO/
REVISIÓN/REPORTES/INTEGRACIÓN ausentes); deep link denegado; home usable **sin error genérico**
(`Z_*`).

## 2 · Matriz 3D de navegación (§74) y ruta directa

| Caso | Empresa | Usuario | RBAC | Navegación | Ruta directa | Backend |
|---|---|---|---|---|---|---|
| OFF/YES/YES | OFF | grant viva | sí | **HIDDEN** (`C8`, `E2`) | **DENY** (`C8-DEEPLINK`) | **0 filas** (`C8-BACKEND-CERO`) |
| ON/NO/YES | ON | sin concesión | sí | **HIDDEN** (`C1`) | **DENY** (`C1-DEEPLINK`) | **0 filas** (`C1-BACKEND-VACIO`) |
| ON/YES/NO | ON | concesión | **no** | **HIDDEN** (`P1`) | **DENY** (`P1-DEEPLINK`) | 403 backend (GA-FE-02-E vigente) |
| ON/YES/YES | ON | concesión | sí | **VISIBLE** (`C2/C3`) | ALLOW (`C4`) | **solo habilitadas** (`C6`, `REG-ON-BROILER`) |

## 3 · Propagación de contexto (semántica real medida)

```
login ............... /me hidrata; nav correcta antes de pintar (sin flash — gating isLoading)
hard refresh ........ reconstruye idéntico (E6, C7)
switch de empresa ... recálculo inmediato en el mismo ciclo (E7) + refresh idéntico
CBU enable .......... REFRESH/RELOGIN (E4 con refresh; C2 con relogin) — no hay push
CBU disable ......... REFRESH/RELOGIN (C8) — sin entradas accionables residuales
grant (objetivo) .... REFRESH/RELOGIN del objetivo (C2/C7) — la sesión abierta de otro
                      usuario no se actualiza sola (semántica canónica /me, documentada)
revoke .............. tras revocar: navegación sin producto en sesión fresca (C1-SIN-GRANT
                      corre inmediatamente después del revoke de reset) + restauración §5
cambio de rol ....... se re-lee en /me (relogin/refresh) — no se inventa tiempo real
```

## 4 · Móvil 390×844 (13/13)

Cm (grant): barra **Operativo+Home+KPI**; hub solo Engorde; etapa permitida; otra unidad
denegada; **overflow 0**. Zm (cero-BU): barra Home+KPI; productivo denegado. Bm (control):
**barra ausente** (0 ítems accionables — fail-closed; las superficies de control son web por
recorte de `view_type`, preexistente). Dm: barra Home+KPI; admin **denegado/redirigido**
(`webOnly` móvil = denegación existente). **E-móvil = N/A por diseño**: el rol 1 es plantilla de
sistema y **no es asignable** desde la administración de empresa (intento real:
`POST /users` → **403 `_rol_asignable`**) — la no-proliferación de super admins es una
propiedad certificada del modelo (`OD-13`), no una carencia de la certificación; el bootstrap
global es web. `MobileDrawer` no está montado en ningún punto (huérfano preexistente):
la navegación móvil real es barra inferior + hubs — inventariado y certificado como tal.

## 5 · Regresión GA-FE-02 + seguridad + restauración (29/29)

D-1 familia: ON broiler → solo `L-BO-*`; **OFF → lots 0 · detalle 404 · ops 0 · dashboard 0 ·
review 0**; escritura global OFF → **403** (R-163). F1: 4 unidades canónicas. F2: rol 35 activo
con 4 permisos. F3: `/users` 200. Restauración: concesiones C/P/CM revocadas (0 vivas), CBU
4×OFF, **10 fixtures dados de baja** (login posterior 403), roles 36/39/40 desactivados, **rol
35 intacto** (activos = 14 canónicos), usuarios humanos sin tocar, auditoría conservada.

## 6 · Auditoría (1:1 con las operaciones)

- `company_business_unit`: **13 filas** `config_change` (broiler) en la ventana de la tranche —
  1 por toggle real (enable/disable UI E3/E9 + set-ups/reset/restore), última = OFF final.
- `user_business_unit`: **10 filas** para objetivos C(84)/P(87)/CM(88) = exactamente los cambios
  de estado reales (grant/revoke x2 cada uno + alta CM + revoke CM); el `POST` de concesión es
  **idempotente** (201 sin fila nueva cuando la concesión ya vive — observado en el re-setup de
  CM; sin duplicados de fila ni de auditoría).
- Denegaciones (auto-concesión, cross-company, D) → **0 filas de éxito** (GA-FE-02-E vigente,
  sin cambio).

## 7 · i18n / consola / red

ES→EN→ES verificado sobre etiquetas de navegación (incl. `nav.roles` nueva); 0 claves crudas;
0 literales nuevos hardcodeados. Consola desktop: **1 entrada no fatal** = `Failed to load
resource 403` durante la batería de negativas (esperada); `pageerror` 0; móvil 0. Red: 1
mutación por acción (sin duplicados de clic); sin bucles de `/me`; sin tormenta de fetches.
**Secretos capturados: 0** (ni passwords, ni Authorization, ni cookies, ni tokens).
