# GA-FE-08 · TRAZA DE NAVEGACIÓN

Fecha: 2026-09-11 · Baseline: `30fe3dc`.

## 1 · Marco de navegación (GA-FE-03 certificado)

- **Modelo único:** `NAV_ITEMS` + `NAV_SECTIONS` — `frontend/src/data/navigationConfig.ts:77-248`; tipo `NavItem` (l.20-45) con `capability`, `permission`, `businessUnit`, `requiresUnits`.
- **Evaluador único:** `filterNavItemsBySession` (`frontend/src/auth/navigation.ts:137-155`) + `canAccessCapability` (l.91-98): permiso ∩ unidad ∩ conjunto; actor global ⇒ `company_business_units` + contexto (fail-closed sin él); sin sesión ⇒ árbol vacío.
- **Vistas:** `getNavItemsForViewType` (navigationConfig.ts:274-280) — web = árbol completo; **mobile = solo `poultry`** (`MOBILE_TOP_LEVEL_KEYS`, l.252).
- **Render:** `Sidebar` desktop (solo raíces; los contenedores enlazan a su hub `/menu/{key}`); `MenuHubPage` pinta la grilla de **hijos** del hub con la misma política (l.45-46); `MobileNav` barra inferior estática (poultry/home/kpi) evaluada con la misma capacidad; `MobileDrawer` existe pero **no está montado**.
- **Estado activo:** `SidebarItem` usa `isPathActive`; el contenedor se resalta con `isAnyChildActive` (navigationConfig.ts:329-340).
- **i18n:** bloque `nav.*` con paridad ES/EN (`frontend/public/locales/{es,en}/translation.json`).

## 2 · ¿Existe hoy una entrada «Lotes»? — NO (prueba)

1. `NAV_ITEMS` no contiene ninguna clave `lots` ni ningún `to: '/lots'` (lectura completa del archivo; las únicas referencias a `/lots` en `frontend/src` son intra-páginas de Lotes).
2. La clave **`nav.lots` existe** en ES («Lotes») y EN («Lots») — translation.json l.114 — y **no se usa** (grep `nav\.lots` en src ⇒ 0).
3. Runtime pre-fix: sidebar sin «Lotes», hub sin tarjeta, móvil sin entrada (`P01-P03`).

⇒ **OBS-UAT-01 presente; clase `MISSING_NAV_CONFIGURATION`.**

## 3 · Ubicación canónica (decisión §15)

Arquitectura real: el sidebar desktop muestra **raíces**; las opciones de área viven en su **hub** (`/menu/{key}`). Todas las superficies productivas se descubren así («Progenitoras…Pollo de Engorde», «Centro de Revisión», «Reportes», «Configuración»). En móvil la única raíz visible es «Gestión Avícola» (su hub).

**Decisión:** `lots` como **primera hija del contenedor `poultry`** («Gestión Avícola»):
- Descubrible en desktop (hub `/menu/poultry` → tarjeta «Lotes») y móvil (hub móvil) reutilizando **la MISMA composición** (NAV_ITEMS + filtro) — sin raíz nueva, sin tocar la barra inferior, sin motor nuevo.
- Reutiliza: sección `operational` existente · ruta existente `/lots` · permiso existente `lots:read` · clave i18n existente `nav.lots` · sistema de iconos lucide.

**Descartadas:** raíz nueva «Lotes» (rompe la arquitectura de hubs; en móvil exigiría tocar `MOBILE_TOP_LEVEL_KEYS`/barra inferior ⇒ cambio mayor del marco certificado); colgarla de otra sección (no existe grupo de «Operaciones» con entrada propia).

## 4 · Regla de autoridad de la entrada nueva

- `capability: PRODUCTIVE` · `permission: 'lots:read'` · `requiresUnits: true` (superficie **multi-unidad**, como `review`/`reports`/`approvals`).
- Dominio del lote `{grandparent, breeder, broiler}` (Clarificación C05): se usa «conjunto productivo no vacío»; la frontera incubadora-solo (lista vacía, sin cambio de autoridad) queda documentada — **sin** añadir dimensiones nuevas al evaluador certificado.
- Estado activo: `isPathActive('/lots')` cubierto por hijo directo; contenedor resaltado por `isAnyChildActive` en `/lots*`.
