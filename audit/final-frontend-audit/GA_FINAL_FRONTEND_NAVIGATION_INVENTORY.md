# FINAL FRONTEND AUDIT · INVENTARIO DE NAVEGACIÓN (actual)

Fecha: 2026-09-11 · Runtime `index-DtzHNDMG.js` · Comparado con GA-FE-03 y GA-FE-08.

## 1 · Desktop (Sidebar · `NAV_ITEMS` filtrado por sesión)

| Ítem (key) | Etiqueta ES/EN | Ruta/hub | Permiso | BU/empresa | Runtime hoy |
|---|---|---|---|---|---|
| dashboard | Dashboard | `/` | dashboard:read | — | ✓ (S01) |
| poultry (hub) | Gestión Avícola / Poultry Management | `/menu/poultry` | requiresUnits | unidad disponible | ✓ (5 tarjetas, S02) |
| └ lots (GA-FE-08) | Lotes / Lots | `/lots` | lots:read | requiresUnits | ✓ (C01-C04 FE-08 + S02) |
| └ grandparent | Progenitoras | `/poultry/grandparent/*` | operations:read | grandparent | ✓ (S04) |
| └ breeder | Reproductoras | `/poultry/breeder/*` | operations:read | breeder | ✓ |
| └ hatchery | Incubadora | `/poultry/hatchery` | operations:read | hatchery | ✓ |
| └ broiler | Pollo de Engorde | `/poultry/broiler` | operations:read | broiler | ✓ (S03) |
| review (hub) | Centro de Revisión | `/menu/review` | review:read | requiresUnits | ✓ (S12) |
| approvals | Aprobaciones | `/approvals` | approvals:approve | requiresUnits | ✓ |
| sap (hub) | Integración SAP | `/menu/sap` | sap:read | — | ✓ (S20) |
| reports (hub) | Reportes | `/menu/reports` | reports:read | requiresUnits | ✓ (S10) |
| audit | Auditoría | `/audit` | audit:read | — | ✓ (S14) |
| masters | Maestros | `/masters` | masters:read | — | ✓ (S13) |
| settings (hub) | Configuración | `/menu/settings` | — | — | ✓ |
| └ users / roles / profile / unit-access | Usuarios y Roles / Roles / Mi Perfil / Acceso por unidad | `/users` `/roles` `/profile` `/admin/unit-access` | users:read / users:read / — / business_units:read | — | ✓ (S15, S16, S19) |

## 2 · Móvil (`view_type=mobile`)

- Árbol móvil: **solo `poultry`** (`MOBILE_TOP_LEVEL_KEYS`) → hub con 5 tarjetas (4 unidades + **Lotes**) ✓ (S18).
- Barra inferior estática (misma política): `Gestión Avícola` (operations:read+units), `Inicio`/`KPI` (dashboard:read) ✓.
- `MobileDrawer`: presente en código pero **no montado** (sin cambio; nota histórica).

## 3 · Determinaciones

- **GA-FE-03: PRESERVADO** — un solo modelo + un solo evaluador; desktop 45-equivalente y móvil verificados hoy sin regresión (hub 5 tarjetas; zero-BU sin productivo; control sin productivo).
- **GA-FE-08: PRESERVADO** — `Lotes` bajo Gestión Avícola; OD-23 respetado (histórico oculto; fresca visible; re-verificado en FE-08 C01-C09).
- **Sin entradas duplicadas, sin entradas muertas, sin hardcode de rol/usuario** (invariantes de suite verde).
- **Faltantes/stale/desincronizadas: 0.** Nota: `/operations` y `/my-pending` siguen sin ítem de menú **por diseño inventariado** (acceso contextual), no como gap de descubribilidad.
- Tenant-aware ✓ (filtro por contexto/`company_business_units`), BU-aware ✓, permission-aware ✓, OD-23-aware ✓, zero-BU ✓, Access Admin ✓ (control-plane puro sin productivo — S16/C09).
