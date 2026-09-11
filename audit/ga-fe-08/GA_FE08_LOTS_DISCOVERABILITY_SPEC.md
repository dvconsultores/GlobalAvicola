# GA-FE-08 · SPEC — DESCUBRIBILIDAD DE LOTES (OBS-UAT-01)

Fecha: 2026-09-11 · Baseline: `30fe3dc` · Autorización: propietario · Clase: `MISSING_NAV_CONFIGURATION`.

## 1 · Contexto

OBS-UAT-01 (GA-UAT-04, clasificada `UX_ENHANCEMENT_ONLY · P2 · sin R` en GA-GOV-01) señala que el módulo Lotes existe y funciona, pero no tiene **fuente de menú**: solo se alcanza por URL directa. Estado inventariado en GA-FE-03 §34 («rutas sin fuente de menú»), nunca implementado. Esta tranche lo resuelve con el **cambio mínimo de configuración de navegación**, reutilizando el marco certificado GA-FE-03/GA-FE-04.

## 2 · Historia OBS-UAT-01

Ver `GA_FE08_OBS_UAT01_SOURCE_RECONSTRUCTION.md` (primera observación, clasificación, dedup, dueño canónico).

## 3 · Superficie actual de Lotes

Ver `GA_FE08_LOTS_SURFACE_TRACE.md`: rutas `/lots` (lista), `/lots/:id` (detalle), `/lots/new` (alta web); guardas `lots:read`/`lots:create` vía `CapabilityRoute`; datos acotados por unidades efectivas; unidad del lote `bird_type ∈ {grandparent, breeder, broiler}`; tenant-scoped.

## 4 · Marco de navegación actual

Ver `GA_FE08_NAVIGATION_TRACE.md`: `NAV_ITEMS` + `filterNavItemsBySession`; web = árbol completo; móvil = solo raíz `poultry` (hub); sidebar desktop = raíces → hubs `/menu/{key}`; sin entrada `lots` hoy; `nav.lots` ES/EN existe sin uso.

## 5 · Alcance

- Añadir **una** entrada declarativa `lots` en `NAV_ITEMS` como primera hija de `poultry`.
- Reusar ruta, permiso, i18n, icono lucide, filtros y hubs existentes.
- Pruebas nuevas GA-FE-08 (contrato de la entrada + matriz de autoridad) y actualización **justificada** de una expectativa heredada (ver §12).
- Certificación técnica + paquete UAT del propietario.

## 6 · Fuera de alcance

Todo lo del prompt §4: sin cambios de reglas/API/esquema de Lotes; sin tocar `planned_close_date`, Áreas, R-182/R-185/R-188, OD-21/22/23, BU-D10, semántica BU/concesiones/RBAC; sin endpoints/migraciones/permisos nuevos; sin rediseño global de navegación; sin Wave B/C/SAP.

## 7 · Ruta

`/lots` (existente). Sin duplicar rutas; sin ruta nueva.

## 8 · Ubicación en el menú

`poultry` → hijos → **`lots` primera posición** (hub `/menu/poultry`). Desktop: tarjeta en el hub. Móvil: mismo hub (ruta móvil = barra inferior → Gestión Avícola → tarjeta). Reutiliza el patrón atenea certificado; sin raíz nueva.

## 9 · Etiqueta

Clave existente **`nav.lots`** (ES «Lotes» · EN «Lots») — reuso probado; fallback «Lotes»; sin copy nuevo; sin hardcode.

## 10 · Icono

`Layers` (lucide, sistema existente). Sin dependencia nueva.

## 11 · Reglas de autoridad

- **Permiso:** `lots:read` (espejo de `tiene_permiso`).
- **Empresa:** sesión con `effective_company_id`; global sin contexto ⇒ fail-closed.
- **BU del lote (dominio):** `{grandparent, breeder, broiler}`; la entrada exige **≥1 unidad disponible** (`requiresUnits: true`, superficie multi-unidad del marco GA-FE-03). Datos siempre acotados a unidades efectivas por el backend (frontera incubadora-solo documentada en C05; sin cambio de autoridad).
- **Empresa BU OFF:** entrada oculta (absoluto OD-16, global incluido); ruta directa sin datos (fail-closed).
- **Concesión de usuario:** sin unidades efectivas ⇒ oculta; **OD-23:** concesión histórica terminada NO revive la entrada; concesión nueva ⇒ vuelve.
- **RBAC:** sin `lots:read` ⇒ oculta y ruta visual denegada.
- **Zero-BU:** oculta.
- **Access Administrator:** control-plane puro ⇒ sin Lotes salvo que tenga, además, permiso y unidades.
- **Global:** contexto + unidad habilitada; BU OFF no se bypassa.
- **Autoridad:** la visibilidad del menú es representación UX; el backend sigue siendo la autoridad (nav ≠ autorización).

## 12 · Desktop / móvil

- Desktop: tarjeta «Lotes» en el hub de Gestión Avícola; contenedor resaltado en `/lots*` (`isAnyChildActive`).
- Móvil: mismo hub (barra inferior «Gestión Avícola» → «Lotes»); sin lógica especial; sin tocar la barra inferior.
- Cambio de expectativa heredada **justificado**: `frontend/src/data/__tests__/gaFe02.nav.test.ts` («el resto del menú también se evalúa») asumía que una sesión con solo `lots:read` no veía `poultry`; con la entrada nueva **la sesión autorizada SÍ ve Gestión Avícola con la única opción Lotes** — comportamiento objetivo de esta tranche; se actualiza la expectativa con anotación GA-FE-08.

## 13 · Deep link

Autorizado: URL directa funciona (contrato existente). Sin autoridad: mismo contrato de ruta certificado (visual `noPermission` sin `lots:read`; datos fail-closed por unidades — vacío/404/403 backend). **La entrada no cambia la autoridad.**

## 14 · Traducciones

`nav.lots` ya existe en ambos idiomas (reuso). Sin claves nuevas ⇒ sin cambios de translation.json.

## 15 · Accesibilidad / calidad

Sin overflow horizontal; sin errores fatales de consola; orden coherente del hub (Lotes primero, luego unidades en orden existente); sin duplicados.

## 16 · AC (contrato de esta tranche)

Descubribilidad: **FE08-AC01** descubrible por navegación normal · **02** sin URL directa · **03** usa la ruta existente · **04** sin ruta duplicada · **05** estado activo correcto.
Autoridad: **06** solo con contexto de empresa · **07** BU OFF oculta · **08** sin BU de usuario oculta · **09** concesión histórica OD-23 no muestra · **10** concesión fresca muestra · **11** sin RBAC oculta · **12** zero-BU sin entrada · **13** Access Admin sin Lotes por rol de control · **14** global no bypassa BU OFF.
Deep link: **15** autorizado funciona · **16** sin autoridad falla cerrado (contrato intacto) · **17** visibilidad no sustituye autoridad · **18** sin datos de otra empresa.
UX: **19** desktop hub · **20** móvil hub · **21/22/23** ES/EN sin hardcode (reuso `nav.lots`) · **24** sin overflow · **25** consola 0 · **26** orden coherente.
Regresión: **27–37** GA-FE-02/03/04/05/06/07, R-182/185/188, R-187/OD-22, sin contrato backend.

## 17 · Pruebas

- Unit/Vitest nuevo: `frontend/src/data/__tests__/gaFe08.lotsNav.test.ts` (contrato + matriz de autoridad + vistas + activo + i18n + unicidad).
- Suites existentes: Vitest completo (línea base 280/280 — total sube) · `tsc -b` · build.
- Backend: diff 0; regresión focalizada declarada (suites PG: skip local).

## 18 · Runtime

Actores: A `fe08op` (autorizado web) · B `fe08nob` (sin concesión) · C `fe08rbc` (sin RBAC de lotes) · D `fe08zbu` (zero-BU) · E `fe08adm` (Access Admin) · F `fe08mob` (móvil) · histórico OD-23 sobre A. E2E-01…10 según prompt.

## 19 · UAT del propietario

Required (cambio visible). 5 casos (§67): encontrar «Lotes» sin URL; abrir la superficie correcta; desaparece sin acceso; vuelve con concesión nueva; móvil. Guía `GA_OWNER_UAT_FE08_GUIDE.md`.

## 20 · Cierre

`OBS-UAT-01 → RESOLVED` + `GA-FE-08 FUNCTIONALLY_CERTIFIED` si todos los AC críticos pasan; UAT → aceptación del propietario; sin auto-aprobación.
